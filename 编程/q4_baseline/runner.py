from __future__ import annotations

import csv
import importlib.metadata
import json
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from q1_baseline.run_manifest import environment_snapshot, git_snapshot, sha256_file
from q1_baseline.solver_backend import HighsPyBackend, backend_by_name
from q2_baseline.config import load_config as load_q2_config
from q2_baseline.data import read_q2_inputs
from q2_baseline.time_axis import date_range, target_day

from .config import PREDICTORS, Q4Config, TRACKS, load_config
from .forecast import PriceForecastDay, build_price_forecast_day
from .metrics import economic_metrics, prediction_metrics, value_decomposition
from .exporter import export_result4_2_candidate
from .export_validation import validate_result4_2_candidate
from .integrity import verify_q4_inputs
from .planner import solve_price_plan
from .price import PriceHistory, read_price_records
from .reference import FrozenQ2Reference
from .settlement import Q4ReplayDay, replay_actual_price
from .validation import validate_price_records, validate_replays


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def structured_solver_audit(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return stable, JSON-serializable per-day solver audit records."""
    fields = ("template_date", "baseline", "predictor", "status", "termination_condition", "solver_invoked", "mip_gap", "runtime_seconds", "level_bound_hit_count")
    return [{field: row.get(field, "") for field in fields} for row in rows]


def aggregate_solver_metrics(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    statuses = [str(row.get("status", "")) for row in rows]
    return {
        "solver_days": len(rows),
        "optimal_count": sum(status in {"OPTIMAL", "OPTIMAL_CLOSED_FORM"} for status in statuses),
        "infeasible_count": sum("INFEASIBLE" in status.upper() for status in statuses),
        "failure_count": sum(status.startswith("FAILED") or status.startswith("ERROR") for status in statuses),
        "reference_only_count": sum(status == "REFERENCE_ONLY_NO_SOLVE" for status in statuses),
        "runtime_seconds": float(sum(float(row.get("runtime_seconds") or 0.0) for row in rows)),
        "level_bound_hit_count": int(sum(int(row.get("level_bound_hit_count") or 0) for row in rows)),
    }


def _q4_code_hashes() -> dict[str, str]:
    root = Path(__file__).resolve().parent
    return {path.name: sha256_file(path) for path in sorted(root.glob("*.py"))}


def _identity_snapshot(config: Q4Config, config_path: Path, input_identity: dict[str, Any], initial_soc: float | None = None) -> dict[str, Any]:
    try:
        highs_version = importlib.metadata.version("highspy")
    except importlib.metadata.PackageNotFoundError:
        highs_version = "NOT_INSTALLED"
    return {
        "config_sha256": sha256_file(config_path),
        "q4_core_python_sha256": _q4_code_hashes(),
        "input_sha256": dict(input_identity["sha256"]),
        "visibility_rule": config.parameters.visibility_rule,
        "formal_dates": [config.output_start.isoformat(), config.output_end.isoformat()],
        "initial_soc_feb1": initial_soc,
        "initial_soc_feb1_identity": {"source": str(config.q2_reference_run / "dispatch_timeseries.csv"), "sha256": input_identity["sha256"]["q2_reference_dispatch"]},
        "python_version": environment_snapshot().get("python", "UNKNOWN"),
        "highs_version": highs_version,
    }


def _assert_identity_unchanged(config: Q4Config, config_path: Path, initial: dict[str, Any], input_identity: dict[str, Any]) -> None:
    current_input = verify_q4_inputs(config)
    current = _identity_snapshot(config, config_path, current_input, initial.get("initial_soc_feb1"))
    if current["config_sha256"] != initial["config_sha256"] or current["q4_core_python_sha256"] != initial["q4_core_python_sha256"]:
        raise RuntimeError("Q4_IDENTITY_HARD_FAIL: code or config changed during run")
    if current["input_sha256"] != initial["input_sha256"]:
        raise RuntimeError("Q4_IDENTITY_HARD_FAIL: input changed during run")


def _actual_prices(history: PriceHistory, day: date) -> np.ndarray:
    return np.asarray([history.by_start[target.interval_start].price for target in target_day(day)], dtype=float)


def _price_rows(days: list[PriceForecastDay]) -> list[dict[str, Any]]:
    output = []
    for day in days:
        for row in day.rows:
            output.append({k: (v.isoformat(sep=" ") if isinstance(v, datetime) else v) for k, v in row.items()})
    return output


def _dispatch_rows(replays: list[Q4ReplayDay], price_days: list[PriceForecastDay]) -> list[dict[str, Any]]:
    by_day = {day.template_date: day for day in price_days}
    rows: list[dict[str, Any]] = []
    for replay in replays:
        price_day = by_day.get(replay.plan.template_date)
        for index, actual in enumerate(replay.actual):
            price_row = None if price_day is None else price_day.rows[index]
            rows.append({
                "period": "formal_output", "baseline": replay.plan.baseline,
                "template_date": replay.plan.template_date.isoformat(), "template_slot": index + 1,
                "interval_start": actual.interval_start.isoformat(sep=" "), "interval_end": actual.interval_end.isoformat(sep=" "),
                "decision_time": "" if price_row is None else price_row["decision_time"].isoformat(sep=" "),
                "level_bound_hit_count": 0 if price_row is None else price_row["level_bound_hit_count"],
                "load_actual_kwh": actual.load_kwh, "pv_actual_kwh": actual.pv_kwh,
                "price_actual": replay.price_actual[index], "price_pred": "" if price_row is None else price_row["price_pred"],
                "grid_plan_kwh": replay.plan.G[index], "grid_emergency_kwh": replay.emergency_kwh[index],
                "charge_bus_kwh": replay.plan.C[index], "discharge_bus_kwh": replay.plan.D[index],
                "spill_kwh": replay.surplus_kwh[index], "soc_before_kwh": replay.plan.S[index], "soc_after_kwh": replay.plan.S[index + 1],
                "regular_purchase_cost": replay.regular_cost[index], "emergency_purchase_cost": replay.emergency_cost[index],
                "realized_total_cost": replay.regular_cost[index] + replay.emergency_cost[index],
            })
    return rows


def _daily_rows(replays: list[Q4ReplayDay], price_days: list[PriceForecastDay]) -> list[dict[str, Any]]:
    price_by_day = {item.template_date: item for item in price_days}
    rows = []
    for replay in replays:
        price_day = price_by_day.get(replay.plan.template_date)
        level_hits = 0 if price_day is None else sum(int(row["level_bound_hit_count"]) for row in price_day.rows)
        rows.append({"template_date": replay.plan.template_date.isoformat(), "level_bound_hit_count": level_hits, **economic_metrics([replay])})
    return rows


def _run_reference_anchor(config_path: Path, config: Q4Config, destination: Path, input_identity: dict[str, Any]) -> Path:
    """Materialize the frozen Q2 cost anchor without invoking a solver."""
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    frozen_manifest_path = config.q2_reference_run / "run_manifest.json"
    frozen_manifest = json.loads(frozen_manifest_path.read_text(encoding="utf-8"))
    cost = float(frozen_manifest["formal_q2_total_cost_yuan"])
    identity = _identity_snapshot(config, config_path, input_identity)
    manifest = {
        "run_id": destination.name, "question_id": "Q4-2", "stage": 5,
        "status": "REFERENCE_ONLY_NO_SOLVE", "track": "REF_Q2_FIXED_PRICE_FROZEN",
        "model_version": config.model_version, "q2_frozen_model_version": config.q2_frozen_model_version,
        "reference_cost_yuan": cost, "reference_manifest": str(frozen_manifest_path),
        "identity": identity, "input_sha256": input_identity["sha256"],
        "solver_invoked": False, "candidate_generated": False,
    }
    (destination / "config_snapshot.json").write_text(json.dumps(config.snapshot(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (destination / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_csv(destination / "metrics_summary.csv", [{"metric": "REF_Q2_FIXED_PRICE_FROZEN", "value": cost, "unit": "yuan", "status": "HISTORICAL_ANCHOR_ONLY"}])
    _write_csv(destination / "solver_days.csv", [{"template_date": "2025-02-01..2025-12-31", "status": "REFERENCE_ONLY_NO_SOLVE", "solver_invoked": False, "runtime_seconds": 0.0, "level_bound_hit_count": 0}])
    (destination / "solver_audit.log").write_text(json.dumps({"schema": "q4-2-solver-audit-v1", "track": "REF_Q2_FIXED_PRICE_FROZEN", "solver_invoked": False}, ensure_ascii=False) + "\n", encoding="utf-8")
    (destination / "warnings_and_failures.log").write_text("REFERENCE-Q4-2-001: fixed-price Q2 value is a historical anchor, not an algorithm-gain baseline.\n", encoding="utf-8")
    (destination / "assertions.json").write_text(json.dumps({"passed": True, "solver_invoked": False, "official_template_untouched": True, "source_manifest": str(frozen_manifest_path)}, ensure_ascii=False, indent=2), encoding="utf-8")
    (destination / "human_feedback.md").write_text("# Q4-2 固定价格历史锚点反馈\n\n该轨道只读取冻结 Q2 manifest，不求解、不生成 result4-2 候选，不得用于价格感知收益计算。\n", encoding="utf-8")
    _assert_identity_unchanged(config, config_path, identity, input_identity)
    return destination


def prepare_price_forecast(config_path: str | Path, predictor_id: str, day: date) -> PriceForecastDay:
    config = load_config(Path(config_path).resolve())
    if predictor_id not in PREDICTORS:
        raise ValueError(predictor_id)
    return build_price_forecast_day(day, predictor_id, PriceHistory(read_price_records(config.normalized_price_input), config.parameters))


def price_unaware_resettlement(reference: FrozenQ2Reference, history: PriceHistory, day: date, config: Q4Config) -> Q4ReplayDay:
    """Resettle an unchanged frozen-Q2 dispatch day at actual Attachment4 prices."""
    return replay_actual_price(reference.plan(day), reference.actual(day), _actual_prices(history, day), config.parameters)


def run_q4_2(config_path: str | Path, output_dir: str | Path, track: str, *, allow_formal_run: bool = False, predictor_override: str | None = None) -> Path:
    """Human-run entry point. Full-year execution is opt-in and never automatic."""
    if not allow_formal_run:
        raise PermissionError("Q4-2 formal Solver/candidate generation requires explicit human authorization")
    config_path_resolved = Path(config_path).resolve()
    config = load_config(config_path_resolved)
    if track not in TRACKS:
        raise ValueError(f"unsupported Q4-2 track: {track}")
    if track == "Q4_2_NOSTORAGE" and predictor_override is None:
        raise ValueError("Q4_2_NOSTORAGE requires explicit --predictor matching the selected storage candidate")
    destination = Path(output_dir).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    identity = verify_q4_inputs(config)
    if track == "REF_Q2_FIXED_PRICE_FROZEN":
        return _run_reference_anchor(config_path_resolved, config, destination, identity)
    destination.mkdir(parents=True)
    q2_config = load_q2_config(config.q2_config)
    data = read_q2_inputs(q2_config.normalized_price_input, config.normalized_actual_input, q2_config.parameters)
    history = PriceHistory(read_price_records(config.normalized_price_input), config.parameters)
    reference = FrozenQ2Reference(config.q2_reference_run / "dispatch_timeseries.csv", data)
    initial_soc = reference.initial_soc_feb1()
    identity_snapshot = _identity_snapshot(config, config_path_resolved, identity, initial_soc)
    manifest = {"run_id": destination.name, "question_id": "Q4-2", "stage": 5, "status": "HUMAN_RUN_UNREVIEWED_CANDIDATE", "track": track, "model_version": config.model_version, "q2_frozen_model_version": config.q2_frozen_model_version, "visibility_rule": config.parameters.visibility_rule, "formal_dates": [config.output_start.isoformat(), config.output_end.isoformat()], "q2_reference_run": str(config.q2_reference_run), "environment": environment_snapshot(), "git": git_snapshot(config_path_resolved.parents[2]), "input_sha256": identity["sha256"], "identity": identity_snapshot, "warnings": ["Q4-2 formal run is human-controlled", "Q4-2-PLAN-SURPLUS-001"], "failures": [], "required_outputs": ["run_manifest.json", "config_snapshot.json", "model_selection_price.csv", "predictions_price.csv", "dispatch_timeseries.csv", "daily_metrics.csv", "monthly_metrics.csv", "metrics_summary.csv", "assertions.json", "solver_days.csv", "solver_audit.log", "warnings_and_failures.log", "result4-2_candidate.xlsx", "export_validation.json", "human_feedback.md"]}
    (destination / "config_snapshot.json").write_text(json.dumps(config.snapshot(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (destination / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (destination / "warnings_and_failures.log").write_text("WARNING-Q4-2-PLAN-SURPLUS-001: free predicted spill may permit multiple optimal storage paths.\n", encoding="utf-8")

    predictor_id = predictor_override or {
        "Q4_2_PRICE_BASELINE_P0": "P0_RECENT_SAME_CLOCK",
        "Q4_2_PRICE_CANDIDATE_P1": "P1_WEEKDAY_SAME_CLOCK",
        "Q4_2_PRICE_CANDIDATE_P2": "P2_EWMA",
        "Q4_2_PRICE_CANDIDATE_P3": "P3_SHAPE_LEVEL",
    }.get(track, "P1_WEEKDAY_SAME_CLOCK")
    if predictor_id not in PREDICTORS:
        raise ValueError(f"unsupported predictor: {predictor_id}")
    days = list(date_range(config.output_start, config.output_end))
    backend = backend_by_name(config.solver_name)
    if track not in {"Q4_2_PRICE_UNAWARE_RESETTLEMENT", "Q4_2_NOSTORAGE"} and isinstance(backend, HighsPyBackend):
        backend.require_available()
    plans: dict[date, Any] = {}; replays: list[Q4ReplayDay] = []; price_days: list[PriceForecastDay] = []
    for day in days:
        actual = reference.actual(day)
        actual_price = _actual_prices(history, day)
        if track == "Q4_2_PRICE_UNAWARE_RESETTLEMENT":
            plan = reference.plan(day); price_day = build_price_forecast_day(day, predictor_id, history)
        else:
            forecast = reference.forecast(day)
            price_day = build_price_forecast_day(day, predictor_id, history)
            plan = solve_price_plan(forecast, price_day, config.parameters, initial_soc, backend, destination / f"solver_{day.isoformat()}.log", no_storage=track == "Q4_2_NOSTORAGE")
            plan = replace(plan, baseline=track)
        replay = price_unaware_resettlement(reference, history, day, config) if track == "Q4_2_PRICE_UNAWARE_RESETTLEMENT" else replay_actual_price(plan, actual, actual_price, config.parameters)
        plans[day] = plan; price_days.append(price_day); replays.append(replay); initial_soc = float(plan.S[-1])
    formal_price_rows = _price_rows(price_days)
    _write_csv(destination / "predictions_price.csv", formal_price_rows)
    formal_dispatch_rows = _dispatch_rows(replays, price_days)
    _write_csv(destination / "dispatch_timeseries.csv", formal_dispatch_rows)
    daily = _daily_rows(replays, price_days)
    _write_csv(destination / "daily_metrics.csv", daily)
    monthly: dict[str, list[Q4ReplayDay]] = {}
    for replay in replays:
        monthly.setdefault(replay.plan.template_date.strftime("%Y-%m"), []).append(replay)
    price_by_day = {item.template_date: item for item in price_days}
    monthly_rows = []
    for month, items in sorted(monthly.items()):
        level_hits = sum(sum(int(row["level_bound_hit_count"]) for row in price_by_day[item.plan.template_date].rows) for item in items)
        monthly_rows.append({"month": month, "level_bound_hit_count": level_hits, **economic_metrics(items, config.parameters.soc_min, config.parameters.soc_max, config.parameters.feasibility_tolerance)})
    _write_csv(destination / "monthly_metrics.csv", monthly_rows)
    econ = economic_metrics(replays, config.parameters.soc_min, config.parameters.soc_max, config.parameters.feasibility_tolerance)
    pred = prediction_metrics(formal_price_rows)
    solver_rows = [{"template_date": day.isoformat(), "baseline": plans[day].baseline, "predictor": predictor_id, "status": plans[day].status, "termination_condition": plans[day].termination_condition, "solver_invoked": plans[day].solver_name not in {"ANALYTIC", "FROZEN_Q2"}, "mip_gap": plans[day].mip_gap, "runtime_seconds": plans[day].runtime_seconds, "level_bound_hit_count": sum(int(row["level_bound_hit_count"]) for row in price_by_day[day].rows)} for day in days]
    solver_summary = aggregate_solver_metrics(solver_rows)
    summary = {**econ, **{f"price_{key}": value for key, value in pred.items()}, **solver_summary}
    _write_csv(destination / "metrics_summary.csv", [{"metric": key, "value": value} for key, value in summary.items()])
    _write_csv(destination / "model_selection_price.csv", [{"track": track, "predictor": predictor_id, "selection_status": "EXPLORATORY_IF_FORMAL_COST_USED", "visibility_rule": config.parameters.visibility_rule}])
    _write_csv(destination / "solver_days.csv", solver_rows)
    replay_validation = validate_replays(replays, config.parameters)
    price_validation = validate_price_records(history.records)
    assertions = {"passed": bool(replay_validation["passed"] and price_validation["passed"]), "price": price_validation, "replay": replay_validation, "frozen_q2_warmup": {"initial_soc_feb1": reference.initial_soc_feb1(), "jan_actions_source": "FROZEN_Q2_STATE_CHAIN"}}
    (destination / "assertions.json").write_text(json.dumps(assertions, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    audit_lines = [{"schema": "q4-2-solver-audit-v1", "track": track, "predictor": predictor_id}] + structured_solver_audit(solver_rows)
    (destination / "solver_audit.log").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in audit_lines) + "\n", encoding="utf-8")
    (destination / "solver.log").write_text("Native solver logs are retained only when physically generated.\n", encoding="utf-8")
    warmup_replays = [replay_actual_price(reference.plan(day), reference.actual(day), _actual_prices(history, day), config.parameters) for day in date_range(config.warmup_start, config.output_start - timedelta(days=1))]
    all_replays = tuple(warmup_replays + replays)
    candidate = destination / "result4-2_candidate.xlsx"
    export_info = export_result4_2_candidate(config, candidate, all_replays)
    export_check = validate_result4_2_candidate(config, candidate, all_replays)
    (destination / "export_validation.json").write_text(json.dumps(export_check, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (destination / "human_feedback.md").write_text(f"# Q4-2 人工运行反馈（待填写）\n\n- 轨道：{track}\n- 预测器：{predictor_id}\n- 可见性：{config.parameters.visibility_rule}\n- Jan 冻结 Q2 状态链：待人工确认\n- Feb-1 初始 SOC：{reference.initial_soc_feb1()} kWh\n- 断言：待人工确认\n- Excel 回读：待人工确认\n- 正式结论：不得在人工确认前标记 ACCEPTED\n", encoding="utf-8")
    _assert_identity_unchanged(config, config_path_resolved, identity_snapshot, identity)
    manifest.update({"finished_at": datetime.now().isoformat(), "formal_days": len(days), "metrics": summary, "price_prediction_metrics": pred, "initial_soc_feb1": reference.initial_soc_feb1(), "price_hash": sha256_file(config.normalized_price_input), "predictor_id": predictor_id, "export": export_info, "export_validation_passed": export_check.get("passed", False)})
    (destination / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return destination


def build_value_decomposition(costs: dict[str, float], selected_predictor: str) -> dict[str, Any]:
    return value_decomposition(costs, selected_predictor)
