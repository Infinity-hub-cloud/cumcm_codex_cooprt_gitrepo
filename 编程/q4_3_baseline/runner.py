from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from q1_baseline.solver_backend import HighsPyBackend, backend_by_name
from q2_baseline.candidate_forecast import CandidatePredictor
from q2_baseline.data import read_q2_inputs
from q2_baseline.time_axis import date_range, target_day
from q3_baseline.attachment3 import read_attachment3_mapped, validate_point_mapped_consistency
from q3_baseline.forecast import initial_planning_day, pv_for_unexecuted
from q3_baseline.metrics import economic_metrics as q3_economic_metrics
from q3_baseline.planner import RollingPlan
from q3_baseline.state_machine import CausalActualView, ExecutedInterval, plan_version_rows, soc_after_action

from .config import REFERENCE_TRACKS, TRACKS, TRACK_TO_PREDICTOR, Q43Config, load_config
from .export_validation import validate_result4_3_candidate
from .exporter import export_result4_3_candidate
from .forecast_adapter import build_rolling_price_forecast
from .integrity import assert_identity_unchanged, identity_snapshot, verify_inputs
from .metrics import economic_metrics, price_prediction_metrics
from .planner import solve_price_aware_initial, solve_price_aware_suffix
from .price import PriceHistory, read_price_records
from .reference import feb1_initial_soc, plans_from_executed, read_frozen_q3_dispatch
from .settlement import execute_with_actual_price, resettle_frozen_q3
from .validation import validate_formal_run


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    material = list(rows)
    if fieldnames is None:
        # Initial planning rows and rolling-update rows intentionally expose
        # different audit fields.  Preserve first-seen order while accepting
        # the union, instead of deriving the schema from only the first row.
        names: list[str] = []
        seen: set[str] = set()
        for row in material:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    names.append(key)
    else:
        names = list(fieldnames)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names)
        writer.writeheader(); writer.writerows(material)


def _dispatch_rows(rows: Iterable[ExecutedInterval]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        item = asdict(row)
        item.update({
            "grid_plan_kwh": item.pop("G"), "grid_final_kwh": item.pop("Q"),
            "charge_bus_kwh": item.pop("C"), "discharge_bus_kwh": item.pop("D"),
            "grid_emergency_kwh": item.pop("E"), "spill_kwh": item.pop("W"),
            "adjust_down_kwh": max(row.G-row.Q, 0.0), "adjust_up_kwh": max(row.Q-row.G, 0.0),
        })
        output.append(item)
    return output


def validate_input_only(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    inputs = verify_inputs(config)
    q3_rows = read_frozen_q3_dispatch(config.frozen_q3_run)
    soc, source = feb1_initial_soc(q3_rows, config.frozen_q3_run / "dispatch_timeseries.csv")
    attachment3 = read_attachment3_mapped(config.q3.attachment3_interp_input, "INTERP")
    consistency = validate_point_mapped_consistency(config.q3.attachment3_point_input, attachment3)
    prices = read_price_records(config.q4.normalized_price_input)
    history = PriceHistory(prices, config.q4.parameters)
    sample = build_rolling_price_forecast(config.output_start, datetime.combine(config.output_start, time(6)), "P2_EWMA", history)
    return {
        "status": "PASS", "model_version": config.model_version, "inputs": inputs,
        "attachment3_point_interp": consistency, "feb1_initial_soc": soc,
        "feb1_initial_soc_identity": source,
        "sample_0600_observed_count": sum(bool(row["observed_at_decision"]) for row in sample.rows),
        "formal_boundary_observed_contract": 1002,
        "formal_run_executed": False,
    }


def _actual_price_enriched(rows: list[dict[str, Any]], history: PriceHistory) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        record = history.by_start.get(item["physical_interval_start"])
        if record is None:
            raise RuntimeError("Q4_3_PRICE_EVALUATION_MISSING_ACTUAL")
        item["price_actual"] = record.price
        result.append(item)
    return result


def _resettle_reference(config: Q43Config, q3_rows: tuple[ExecutedInterval, ...], history: PriceHistory) -> tuple[ExecutedInterval, ...]:
    output = []
    for row in q3_rows:
        record = history.by_start.get(row.interval_start)
        if record is None:
            raise RuntimeError(f"missing Attachment4 price for {row.interval_start}")
        output.append(resettle_frozen_q3(row, record.price))
    return tuple(output)


def _write_common_outputs(
    destination: Path, config: Q43Config, track: str, plans: dict[date, object],
    all_executed: tuple[ExecutedInterval, ...], formal: tuple[ExecutedInterval, ...],
    price_rows: list[dict[str, Any]], solver_updates: list[dict[str, Any]], assertions: dict[str, Any],
    identity: dict[str, Any], config_path: Path, inputs: dict[str, Any], feb1_soc: float,
    feb1_source: dict[str, object], highs_version: str,
) -> None:
    _json(destination / "config_snapshot.json", config.snapshot())
    _write_csv(destination / "dispatch_timeseries.csv", _dispatch_rows(all_executed))
    _write_csv(destination / "predictions_price.csv", price_rows)
    _write_csv(destination / "solver_updates.csv", solver_updates)
    metrics = economic_metrics(formal, soc_min=config.parameters.soc_min, soc_max=config.parameters.soc_max, tolerance=config.parameters.feasibility_tolerance)
    price_metrics = [] if not price_rows else [price_prediction_metrics(price_rows, unknown_only=False), price_prediction_metrics(price_rows, unknown_only=True)]
    _write_csv(destination / "prediction_metrics_price.csv", price_metrics)
    daily = []
    for day in date_range(config.output_start, config.output_end):
        rows = [row for row in formal if row.template_date == day.isoformat()]
        daily.append({"template_date": day.isoformat(), **q3_economic_metrics(rows)})
    _write_csv(destination / "daily_metrics.csv", daily)
    monthly = []
    for month in range(2, 13):
        rows = [row for row in formal if date.fromisoformat(row.template_date).month == month]
        monthly.append({"month": month, **q3_economic_metrics(rows)})
    _write_csv(destination / "monthly_metrics.csv", monthly)
    _write_csv(destination / "metrics_summary.csv", (
        {"track": track, "question_id": "Q4-3", "model_version": config.model_version,
         "split": "formal_template_days", "metric": key, "value": value, "status": "HUMAN_RUN_UNREVIEWED"}
        for key, value in metrics.items()
    ))
    _json(destination / "assertions.json", assertions)
    candidate = destination / "result4-3_candidate.xlsx"
    export_info = export_result4_3_candidate(config, candidate, plans, all_executed)
    export_check = validate_result4_3_candidate(config, candidate, plans, all_executed)
    _json(destination / "export_validation.json", export_check)
    if not export_check["passed"]:
        raise AssertionError("Q4-3 candidate round-trip validation failed")
    _write_csv(destination / "solver_audit.csv", solver_updates)
    (destination / "warnings_and_failures.log").write_text(
        "INFO-Q4-3: template-date accounting; result4-3 storage/emergency sheets use natural-day presentation.\n"
        "INFO-Q4-3: intermediate Q trajectories are not settlement transactions.\n",
        encoding="utf-8",
    )
    manifest = {
        "question_id": "Q4-3", "stage": 5, "track": track, "model_version": config.model_version,
        "run_status": "HUMAN_RUN_UNREVIEWED_CANDIDATE", "final_competition_result": False,
        "visibility_rule": config.visibility_rule, "warmup_rule": config.warmup_rule,
        "formal_dates": [config.output_start.isoformat(), config.output_end.isoformat()], "formal_days": 334,
        "pv_issue_set": [0, 360, 720, 1080], "pv_mapping_method": "INTERP", "cost_semantics": "MODEL_B",
        "predictor_id": TRACK_TO_PREDICTOR.get(track), "identity": identity, "metrics": metrics,
        "price_prediction_metrics": price_metrics, "assertions_passed": assertions["passed"],
        "export_validation_passed": True, "export": export_info,
    }
    assert_identity_unchanged(identity, config, config_path, inputs, feb1_soc, feb1_source, highs_version)
    _json(destination / "run_manifest.json", manifest)
    (destination / "human_feedback.md").write_text(
        "# Q4-3 人工验收\n\n- 实际命令：待填写\n- 身份门禁：待填写\n- 因果断言：待填写\n"
        "- Solver/导出证据：待填写\n- 预测器成本排序：待全部轨道运行后填写\n- 人工结论：待填写\n",
        encoding="utf-8",
    )


def run_q4_3(config_path: str | Path, output_dir: str | Path, track: str, *, allow_formal_run: bool = False) -> Path:
    if not allow_formal_run:
        raise PermissionError("Q4-3 formal run is not authorized; pass --allow-formal-run only after explicit human approval")
    config_path = Path(config_path).resolve(); config = load_config(config_path)
    if track not in TRACKS:
        raise ValueError(f"unknown Q4-3 track: {track}")
    destination = Path(output_dir).resolve()
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite output directory: {destination}")
    destination.mkdir(parents=True); log_dir = destination / "_solver_logs"; log_dir.mkdir()
    inputs = verify_inputs(config)
    q3_rows = read_frozen_q3_dispatch(config.frozen_q3_run)
    feb_soc, feb_source = feb1_initial_soc(q3_rows, config.frozen_q3_run / "dispatch_timeseries.csv")
    price_records = read_price_records(config.q4.normalized_price_input)
    history = PriceHistory(price_records, config.q4.parameters)
    highs_version = HighsPyBackend().name
    try:
        import highspy
        highs_version = str(highspy.Highs().version())
    except Exception:
        highs_version = "UNAVAILABLE"
    identity = identity_snapshot(config, config_path, inputs, feb_soc, feb_source, highs_version)

    if track == "REF_Q3_FIXED_PRICE_FROZEN":
        formal = tuple(row for row in q3_rows if config.output_start <= date.fromisoformat(row.template_date) <= config.output_end)
        fixed_metrics = q3_economic_metrics(formal)
        _json(destination / "config_snapshot.json", config.snapshot())
        _write_csv(destination / "metrics_summary.csv", ({"metric": k, "value": v} for k, v in fixed_metrics.items()))
        _json(destination / "run_manifest.json", {"track": track, "status": "REFERENCE_ONLY_NO_SOLVE", "source": str(config.frozen_q3_run), "identity": identity, "metrics": fixed_metrics})
        (destination / "human_feedback.md").write_text("# Q4-3 固定价格历史锚点\n\n- 引用身份：待人工确认\n", encoding="utf-8")
        return destination

    if track == "Q4_3_PRICE_UNAWARE_REFERENCE":
        all_resettled = _resettle_reference(config, q3_rows, history)
        formal = tuple(row for row in all_resettled if config.output_start <= date.fromisoformat(row.template_date) <= config.output_end)
        plans = plans_from_executed(all_resettled, config.output_start, config.output_end)
        assertions = {"passed": True, "checks": {"reference_action_identity": True, "reference_no_solve": True, "actual_price_model_b": True}}
        _write_common_outputs(destination, config, track, plans, all_resettled, formal, [], [{"solver_status": "REFERENCE_ONLY_NO_SOLVE"}], assertions, identity, config_path, inputs, feb_soc, feb_source, highs_version)
        return destination

    predictor_id = TRACK_TO_PREDICTOR[track]
    backend = backend_by_name(config.solver_name)
    data = read_q2_inputs(config.q3.normalized_price_input, config.q3.normalized_actual_input, config.parameters)
    actual_view = CausalActualView(data.actual_by_template_key)
    attachment3 = read_attachment3_mapped(config.q3.attachment3_interp_input, "INTERP")
    plans: dict[date, RollingPlan] = {}; frozen_days = {}; current_pv = {}
    executed: list[ExecutedInterval] = []
    price_rows: list[dict[str, Any]] = []; solver_updates: list[dict[str, Any]] = []; version_rows: list[dict[str, Any]] = []
    soc = feb_soc; previous_day: date | None = None

    def update(plan, frozen, day, decision, current_soc, name):
        pv_rows = pv_for_unexecuted(frozen, attachment3, decision, config.q3.issue_sets["rolling4"])
        prices = build_rolling_price_forecast(day, decision, predictor_id, history)
        if [row.template_slot for row in pv_rows] != [int(row["template_slot"]) for row in prices.rows]:
            raise AssertionError("Q4-3 PV/price physical suffix mismatch")
        old_g, old_q, old_c, old_d = plan.G.copy(), plan.Q.copy(), plan.C.copy(), plan.D.copy()
        start = pv_rows[0].template_slot
        audit = solve_price_aware_suffix(plan, frozen, pv_rows, prices, current_soc, config.parameters, backend, log_dir / f"{day}_{name}.log")
        if not np.array_equal(old_g, plan.G): raise AssertionError("Q4_3_G_FROZEN_HARD_FAIL")
        for old, new, label in ((old_q,plan.Q,"Q"),(old_c,plan.C,"C"),(old_d,plan.D,"D")):
            if not np.array_equal(old[:start-1], new[:start-1]): raise AssertionError(f"Q4_3_EXECUTED_PREFIX_HARD_FAIL:{label}")
        price_rows.extend(dict(row) for row in prices.rows)
        for pv in pv_rows: current_pv[pv.template_slot-1] = pv.forecast_kw
        version_rows.extend(asdict(row) for row in plan_version_rows(plan, current_pv, decision, name, start))
        solver_updates.append({"template_date": day.isoformat(), "decision_time": decision, "plan_version": name, "start_slot": start, **audit})

    for day in date_range(config.output_start, config.output_end):
        if day.day == 1: print(f"[Q4-3 progress] track={track} template_month={day:%Y-%m}", flush=True)
        midnight = datetime.combine(day, time.min); new_soc = soc; pending = None
        if previous_day is not None:
            prior = plans[previous_day]; prior_frozen = frozen_days[previous_day]
            update(prior, prior_frozen, previous_day, midnight, soc, "update_nextday_0000_slot144")
            new_soc = soc_after_action(soc, float(prior.C[143]), float(prior.D[143]), config.parameters); pending = prior
        predictor = CandidatePredictor(actual_view.snapshot(midnight, data.price), "weekday", True)
        q2_day = predictor.forecast_day(day)
        frozen = initial_planning_day(day, q2_day, attachment3, config.q3.issue_sets["rolling4"])
        initial_prices = build_rolling_price_forecast(day, midnight, predictor_id, history)
        plan = solve_price_aware_initial(frozen, initial_prices, config.parameters, new_soc, backend, log_dir / f"{day}_initial_0000.log")
        plans[day] = plan; frozen_days[day] = frozen; current_pv[day] = frozen.initial_pv_kw.copy()
        price_rows.extend(dict(row) for row in initial_prices.rows)
        version_rows.extend(asdict(row) for row in plan_version_rows(plan, current_pv[day], midnight, "initial_0000", 1))
        solver_updates.append({"template_date": day.isoformat(), "decision_time": midnight, "plan_version": "initial_0000", "start_slot": 1, "solver_name": plan.initial_solver_name, "solver_version": plan.initial_solver_version, "solver_status": plan.solver_status[0], "termination_condition": plan.initial_termination, "mip_gap": plan.initial_mip_gap, "runtime_seconds": plan.initial_runtime, "objective": plan.initial_objective})
        if pending is not None and previous_day is not None:
            actual = actual_view.get((previous_day, 144), target_day(previous_day)[143].interval_end)
            result = execute_with_actual_price(pending, 144, actual, history, soc, config.parameters)
            if abs(result.soc_after-new_soc) > config.parameters.feasibility_tolerance: raise AssertionError("Q4-3 midnight SOC bridge failed")
            executed.append(result); soc = result.soc_after
        for slot in range(1,144):
            target = target_day(day)[slot-1]; minute = target.interval_start.hour*60 + target.interval_start.minute
            if minute in (360,720,1080): update(plan, frozen, day, target.interval_start, soc, f"update_{minute//60:02d}00")
            actual = actual_view.get((day,slot), target.interval_end)
            result = execute_with_actual_price(plan,slot,actual,history,soc,config.parameters)
            executed.append(result); soc=result.soc_after
        previous_day=day
    last_day=config.output_end; last_plan=plans[last_day]
    final_actual=actual_view.get((last_day,144),target_day(last_day)[143].interval_end)
    executed.append(execute_with_actual_price(last_plan,144,final_actual,history,soc,config.parameters))
    formal=tuple(executed)
    bridge=next(row for row in q3_rows if row.template_date=="2025-01-31" and row.template_slot==144)
    all_for_export=(resettle_frozen_q3(bridge, history.by_start[bridge.interval_start].price),)+formal
    enriched=_actual_price_enriched(price_rows,history)
    assertions=validate_formal_run(config,plans,formal,enriched,solver_updates)
    if not assertions["passed"]: raise AssertionError(f"Q4-3 assertions failed: {assertions['failures']}")
    _write_csv(destination/"plan_versions.csv",version_rows)
    _write_common_outputs(destination,config,track,plans,all_for_export,formal,enriched,solver_updates,assertions,identity,config_path,inputs,feb_soc,feb_source,highs_version)
    return destination


def compare_tracks(run_root: str | Path, output_path: str | Path) -> Path:
    root = Path(run_root).resolve(); output = Path(output_path).resolve()
    required = ("REF_Q3_FIXED_PRICE_FROZEN", "Q4_3_PRICE_UNAWARE_REFERENCE", *TRACK_TO_PREDICTOR)
    manifests = {}
    for track in required:
        path = root / track / "run_manifest.json"
        if not path.is_file(): raise FileNotFoundError(path)
        manifests[track] = json.loads(path.read_text(encoding="utf-8"))
    reference_identity = manifests["Q4_3_PRICE_UNAWARE_REFERENCE"].get("identity")
    for track in required:
        if manifests[track].get("identity") != reference_identity:
            raise RuntimeError(f"Q4_3_COMPARE_IDENTITY_HARD_FAIL:{track}:cross-track identity mismatch")
    candidates = {}
    for track in TRACK_TO_PREDICTOR:
        manifest = manifests[track]
        if manifest.get("model_version") != "M4-Q4-3-PRICE-AWARE-ROLLING-v0.1" or not manifest.get("assertions_passed") or not manifest.get("export_validation_passed"):
            raise RuntimeError(f"Q4_3_COMPARE_IDENTITY_HARD_FAIL:{track}")
        candidates[track] = float(manifest["metrics"]["realized_total_cost"])
    reference_cost = float(manifests["Q4_3_PRICE_UNAWARE_REFERENCE"]["metrics"]["realized_total_cost"])
    selected = min(candidates, key=candidates.get)
    table = [
        {"track": track, "predictor_id": TRACK_TO_PREDICTOR[track], "realized_total_cost": cost,
         "price_awareness_value": reference_cost-cost, "selection_basis": "formal_realized_settlement_cost",
         "selected": track == selected}
        for track, cost in sorted(candidates.items(), key=lambda item: item[1])
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(output.parent / "model_selection_price.csv", table)
    fixed_metrics = manifests["REF_Q3_FIXED_PRICE_FROZEN"].get("metrics", {})
    fixed_cost = float(fixed_metrics.get("total_cost", float("nan")))
    _json(output, {
        "selected_track": selected, "selected_predictor": TRACK_TO_PREDICTOR[selected],
        "selection_basis": "minimum formal realized settlement cost",
        "PriceAwarenessValue": reference_cost-candidates[selected],
        "PriceSystemEffect": fixed_cost-reference_cost,
        "reference_cost": reference_cost, "candidate_costs": candidates,
        "no_storage_value": "NOT_REQUESTED_FOR_Q4_3",
    })
    return output
