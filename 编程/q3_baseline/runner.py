from __future__ import annotations

import csv
import json
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, replace
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from q1_baseline.run_manifest import sha256_file
from q1_baseline.solver_backend import backend_by_name
from q2_baseline.candidate_forecast import CandidatePredictor
from q2_baseline.data import Q2InputData, read_q2_inputs
from q2_baseline.planner import cold_start_plan
from q2_baseline.time_axis import date_range, target_day

from .attachment3 import Attachment3Data, read_attachment3_mapped, validate_point_mapped_consistency
from .config import Q3Config, TRACKS, load_config
from .export_validation import validate_result3_candidate
from .exporter import export_result3_candidate
from .forecast import FrozenPlanningDay, initial_planning_day, pv_for_unexecuted
from .integrity import LOCKED_SHA256, verify_input_integrity
from .metrics import economic_metrics, evaluate_pv_predictions, soc_boundary_hits
from .planner import RollingPlan, solve_and_apply_adjustment, solve_initial_plan
from .state_machine import (
    ExecutedInterval,
    CausalActualView,
    PlanVersionRow,
    execute_r0_interval,
    plan_version_rows,
    soc_after_action,
)
from .validation import validate_run


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    material = list(rows)
    if fieldnames is None:
        fieldnames = list(material[0]) if material else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(material)


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

def _code_identity(config_path: Path, mapping_path: Path) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    core = [root / "q3_baseline" / name for name in (
        "attachment3.py", "forecast.py", "planner.py", "state_machine.py", "runner.py",
        "metrics.py", "validation.py", "exporter.py", "export_validation.py", "integrity.py",
    )]
    repo = root.parent
    def git(*args: str) -> str:
        result = subprocess.run(["git", "-c", f"safe.directory={repo}", "-C", str(repo), *args], capture_output=True, text=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else f"UNAVAILABLE: {result.stderr.strip()}"
    return {
        "core_python_sha256": {path.name: sha256_file(path) for path in core},
        "config_sha256": sha256_file(config_path.resolve()),
        "revised_mapping_sha256": sha256_file(mapping_path),
        "git_head": git("rev-parse", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain")) if not git("status", "--porcelain").startswith("UNAVAILABLE") else "UNAVAILABLE",
    }


def _track_settings(
    config: Q3Config, track: str, issue_set_name: str | None = None
) -> tuple[tuple[int, ...], bool, str, str]:
    if issue_set_name is not None:
        if track not in {"Q3_ROLLING_ZOH", "Q3_ROLLING_INTERP"}:
            raise ValueError("issue-set override is only valid for the rolling experiment track")
        if issue_set_name not in config.issue_sets:
            raise ValueError(f"unknown issue-set experiment: {issue_set_name}")
        return config.issue_sets[issue_set_name], False, "INTERP" if track.endswith("INTERP") else "ZOH", "MODEL_B"
    if track == "Q3_A3_0ONLY_ZOH":
        return config.issue_sets["0only"], False, "ZOH", "MODEL_B"
    if track == "Q3_A3_0ONLY_INTERP":
        return config.issue_sets["0only"], False, "INTERP", "MODEL_B"
    if track == "Q3_ROLLING_ZOH":
        return config.issue_sets["rolling4"], False, "ZOH", "MODEL_B"
    if track == "Q3_ROLLING_INTERP":
        return config.issue_sets["rolling4"], False, "INTERP", "MODEL_B"
    if track == "Q3_NOSTORAGE":
        return config.issue_sets["rolling4"], True, "INTERP", "MODEL_B"
    if track == "Q3_COST_A_SENSITIVITY":
        return config.issue_sets["rolling4"], False, "INTERP", "MODEL_A"
    raise ValueError(f"track has no Q3 simulation settings: {track}")


def validate_input_only(config_path: str | Path) -> dict[str, Any]:
    config = load_config(Path(config_path))
    integrity = verify_input_integrity(config)
    zoh = read_attachment3_mapped(config.attachment3_zoh_input, "ZOH")
    interp = read_attachment3_mapped(config.attachment3_interp_input, "INTERP")
    consistency = {
        "zoh": validate_point_mapped_consistency(config.attachment3_point_input, zoh),
        "interp": validate_point_mapped_consistency(config.attachment3_point_input, interp),
    }
    data = read_q2_inputs(config.normalized_price_input, config.normalized_actual_input, config.parameters)
    sample_day = config.output_start
    sample_decision = datetime.combine(sample_day, time.min)
    predictor = CandidatePredictor(CausalActualView(data.actual_by_template_key).snapshot(sample_decision, data.price), "weekday", True)
    frozen = initial_planning_day(sample_day, predictor.forecast_day(sample_day), interp, config.issue_sets["rolling4"])
    return {
        "status": "PASS",
        "integrity": integrity,
        "attachment3_consistency": consistency,
        "sample_fallback_count": sum(row.forecast_source == "fallback_q2_pv" for row in frozen.initial_pv),
        "sample_mapping_method": interp.mapping_method,
        "model_version": config.model_version,
    }


def _record_versions(
    destination: list[PlanVersionRow],
    plan: RollingPlan,
    pv_kw: np.ndarray,
    decision: datetime,
    name: str,
    start_slot: int,
) -> None:
    destination.extend(plan_version_rows(plan, pv_kw, decision, name, start_slot))


def _update_suffix(
    *,
    plan: RollingPlan,
    frozen: FrozenPlanningDay,
    attachment3: Attachment3Data,
    decision: datetime,
    allowed_issues: tuple[int, ...],
    price: np.ndarray,
    current_soc: float,
    config: Q3Config,
    backend: Any,
    log_dir: Path,
    version_name: str,
    pv_current: np.ndarray,
    versions: list[PlanVersionRow],
    solver_updates: list[dict[str, Any]],
    no_storage: bool,
) -> None:
    rows = pv_for_unexecuted(frozen, attachment3, decision, allowed_issues)
    if not rows:
        return
    start_slot = rows[0].template_slot
    if any(row.interval_start < decision or row.decision_time != decision for row in rows):
        raise AssertionError("Q3 update attempted to touch an executed interval")
    original_g = plan.G.copy()
    log_path = log_dir / f"{plan.template_date}_{version_name}.log"
    audit = solve_and_apply_adjustment(
        plan,
        frozen,
        rows,
        price,
        current_soc,
        config.parameters,
        backend,
        log_path,
        no_storage=no_storage,
    )
    if not np.array_equal(original_g, plan.G):
        raise AssertionError("immutable_initial_plan was changed")
    for row in rows:
        pv_current[row.template_slot - 1] = row.forecast_kw
    _record_versions(versions, plan, pv_current, decision, version_name, start_slot)
    solver_updates.append(
        {
            "template_date": plan.template_date.isoformat(),
            "decision_time": decision.isoformat(),
            "plan_version": version_name,
            "start_slot": start_slot,
            "remaining_intervals": len(rows),
            **audit,
        }
    )


def run_reference(config: Q3Config, output_dir: Path) -> Path:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    integrity = verify_input_integrity(config)
    source = config.q2_reference_run
    required = ("run_manifest.json", "metrics_summary.csv", "monthly_metrics.csv")
    for name in required:
        if not (source / name).is_file():
            raise FileNotFoundError(source / name)
        shutil.copy2(source / name, output_dir / f"q2_reference_{name}")
    _json(output_dir / "config_snapshot.json", config.snapshot())
    _json(
        output_dir / "run_manifest.json",
        {
            "question_id": "Q3_REFERENCE",
            "track": "REF_Q2_FROZEN",
            "status": "REFERENCE_ONLY_NO_SOLVE",
            "source_q2_run": str(source),
            "source_q2_model": config.q2_frozen_model_version,
            "integrity": integrity,
        },
    )
    (output_dir / "human_feedback.md").write_text(
        "# REF_Q2_FROZEN 人工复核\n\n- 状态：待人工确认引用身份\n- 本轨道未重新求解Q2。\n",
        encoding="utf-8",
    )
    return output_dir


def run_q3_track(
    config_path: str | Path,
    output_dir: str | Path,
    track: str,
    *,
    issue_set_name: str | None = None,
) -> Path:
    config = load_config(Path(config_path))
    if track not in TRACKS:
        raise ValueError(f"unknown Q3 track: {track}")
    destination = Path(output_dir).resolve()
    if track == "REF_Q2_FROZEN":
        return run_reference(config, destination)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite output directory: {destination}")
    destination.mkdir(parents=True)
    log_dir = destination / "_solver_logs"
    log_dir.mkdir()

    integrity = verify_input_integrity(config)
    data = read_q2_inputs(config.normalized_price_input, config.normalized_actual_input, config.parameters)
    issue_set, no_storage, mapping_method, cost_semantics = _track_settings(config, track, issue_set_name)
    params = replace(config.parameters, cost_semantics=cost_semantics)
    config = replace(config, parameters=params)
    mapping_path = config.attachment3_interp_input if mapping_method == "INTERP" else config.attachment3_zoh_input
    code_identity = _code_identity(Path(config_path), mapping_path)
    attachment3 = read_attachment3_mapped(mapping_path, mapping_method)
    long_check = validate_point_mapped_consistency(config.attachment3_point_input, attachment3)
    backend = backend_by_name(config.solver_name)
    actual_view = CausalActualView(data.actual_by_template_key)

    plans: dict[date, RollingPlan] = {}
    frozen_days: dict[date, FrozenPlanningDay] = {}
    current_pv: dict[date, np.ndarray] = {}
    executed: list[ExecutedInterval] = []
    versions: list[PlanVersionRow] = []
    solver_updates: list[dict[str, Any]] = []
    soc = config.parameters.soc_initial
    previous_day: date | None = None

    for day in date_range(config.warmup_start, config.output_end):
        if day.day == 1:
            print(f"[Q3 progress] track={track} template_month={day:%Y-%m}", flush=True)
        midnight = datetime.combine(day, time.min)
        new_window_initial_soc = soc
        pending_prior: RollingPlan | None = None
        # Q3-MIDNIGHT-SEQUENCE-001: finalize prior slot144 before creating new G.
        if previous_day is not None:
            prior = plans[previous_day]
            prior_frozen = frozen_days[previous_day]
            _update_suffix(
                plan=prior,
                frozen=prior_frozen,
                attachment3=attachment3,
                decision=midnight,
                allowed_issues=issue_set,
                price=data.price,
                current_soc=soc,
                config=config,
                backend=backend,
                log_dir=log_dir,
                version_name="update_nextday_0000_slot144",
                pv_current=current_pv[previous_day],
                versions=versions,
                solver_updates=solver_updates,
                no_storage=no_storage,
            )
            # The new day's G is built from the action-implied 00:10 SOC before
            # the not-yet-observed 00:00-00:10 actual load/PV is read.
            new_window_initial_soc = soc_after_action(
                soc, float(prior.C[143]), float(prior.D[143]), config.parameters
            )
            pending_prior = prior

        # The predictor receives a capability-limited snapshot, not the full year.
        predictor = CandidatePredictor(actual_view.snapshot(midnight, data.price), "weekday", True)
        q2_day = predictor.forecast_day(day)
        frozen = initial_planning_day(day, q2_day, attachment3, issue_set)
        initial_log = log_dir / f"{day}_initial_0000.log"
        if np.all(q2_day.cold_mask):
            daily = cold_start_plan(
                frozen.as_q2_forecast_for_initial_solve(), new_window_initial_soc
            )
            plan = RollingPlan.from_initial(daily, frozen)
        else:
            plan = solve_initial_plan(
                frozen,
                data.price,
                config.parameters,
                new_window_initial_soc,
                backend,
                initial_log,
                no_storage=no_storage,
            )
        plans[day] = plan
        frozen_days[day] = frozen
        current_pv[day] = frozen.initial_pv_kw.copy()
        _record_versions(versions, plan, current_pv[day], midnight, "initial_0000", 1)
        solver_updates.append(
            {
                "template_date": day.isoformat(),
                "decision_time": midnight.isoformat(),
                "plan_version": "initial_0000",
                "start_slot": 1,
                "remaining_intervals": 144,
                "solver_name": plan.initial_solver_name,
                "solver_version": plan.initial_solver_version,
                "solver_status": plan.solver_status[0],
                "termination_condition": plan.initial_termination,
                "mip_gap": plan.initial_mip_gap,
                "runtime_seconds": plan.initial_runtime,
                "objective": plan.initial_objective,
                "rows": plan.initial_rows,
                "columns": plan.initial_columns,
                "binary_count": plan.initial_binary_count,
            }
        )

        if pending_prior is not None and previous_day is not None:
            actual = actual_view.get((previous_day, 144), datetime.combine(day, time.min) + timedelta(minutes=10))
            result = execute_r0_interval(
                pending_prior, 144, actual, float(data.price[143]), soc, config.parameters
            )
            if abs(result.soc_after - new_window_initial_soc) > config.parameters.feasibility_tolerance:
                raise AssertionError("Q3 midnight action-implied SOC changed during R0 replay")
            executed.append(result)
            soc = result.soc_after

        for slot in range(1, 144):
            target = target_day(day)[slot - 1]
            minute = target.interval_start.hour * 60 + target.interval_start.minute
            if minute in issue_set and minute != 0:
                name = f"update_{minute // 60:02d}00"
                _update_suffix(
                    plan=plan,
                    frozen=frozen,
                    attachment3=attachment3,
                    decision=target.interval_start,
                    allowed_issues=issue_set,
                    price=data.price,
                    current_soc=soc,
                    config=config,
                    backend=backend,
                    log_dir=log_dir,
                    version_name=name,
                    pv_current=current_pv[day],
                    versions=versions,
                    solver_updates=solver_updates,
                    no_storage=no_storage,
                )
            actual = actual_view.get((day, slot), target.interval_end)
            result = execute_r0_interval(plan, slot, actual, float(data.price[slot - 1]), soc, config.parameters)
            executed.append(result)
            soc = result.soc_after
        previous_day = day

    # 2025-12-31 slot144: no fictitious 2026-01-01 issue.
    if previous_day is None:
        raise AssertionError("Q3 simulation produced no template day")
    prior = plans[previous_day]
    final_actual = actual_view.get((previous_day, 144), target_day(previous_day)[143].interval_end)
    final_result = execute_r0_interval(prior, 144, final_actual, float(data.price[143]), soc, config.parameters)
    executed.append(final_result)

    expected_count = 365 * 144
    if len(executed) != expected_count:
        raise AssertionError(f"Q3 execution count mismatch: {len(executed)} != {expected_count}")
    executed_tuple = tuple(executed)
    formal = tuple(
        row for row in executed_tuple
        if config.output_start <= date.fromisoformat(row.template_date) <= config.output_end
    )
    formal_solver_updates = [
        row
        for row in solver_updates
        if config.output_start <= date.fromisoformat(str(row["template_date"])) <= config.output_end
    ]
    metrics = economic_metrics(formal)
    metrics.update(
        {
            "soc_boundary_hits": soc_boundary_hits(
                formal,
                config.parameters.soc_min,
                config.parameters.soc_max,
                config.parameters.feasibility_tolerance,
            ),
            "solver_runtime_seconds": sum(
                float(row.get("runtime_seconds", 0.0)) for row in formal_solver_updates
            ),
            "failed_updates": float(
                sum(
                    not (
                        str(row.get("solver_status", "")).upper().startswith("OPTIMAL")
                        or str(row.get("solver_status", "")).upper().startswith("FEASIBLE")
                        or str(row.get("solver_status", "")).upper() == "COLD_START_NO_SOLVE"
                    )
                    for row in formal_solver_updates
                )
            ),
            "infeasible_updates": float(
                sum(
                    "INFEAS" in str(row.get("termination_condition", "")).upper()
                    for row in formal_solver_updates
                )
            ),
        }
    )

    _json(destination / "config_snapshot.json", config.snapshot())
    _write_csv(destination / "plan_versions.csv", (asdict(row) for row in versions))
    _write_csv(destination / "solver_updates.csv", solver_updates)
    dispatch_rows = []
    for row in executed_tuple:
        payload = asdict(row)
        payload.update(
            {
                "grid_plan_kwh": payload.pop("G"),
                "grid_final_kwh": payload.pop("Q"),
                "charge_bus_kwh": payload.pop("C"),
                "discharge_bus_kwh": payload.pop("D"),
                "grid_emergency_kwh": payload.pop("E"),
                "spill_kwh": payload.pop("W"),
                "adjust_down_kwh": max(row.G - row.Q, 0.0),
                "adjust_up_kwh": max(row.Q - row.G, 0.0),
            }
        )
        dispatch_rows.append(payload)
    _write_csv(destination / "dispatch_timeseries.csv", dispatch_rows)
    actual_by_physical = {
        (row.interval_start, row.interval_end): row for row in data.actual
    }
    pv_metric_material: list[dict[str, object]] = []
    for row in attachment3.rows:
        issue_minute = row.issue_datetime.hour * 60 + row.issue_datetime.minute
        actual = actual_by_physical.get(row.physical_key)
        if issue_minute not in issue_set or actual is None:
            continue
        pv_metric_material.append(
            {
                "issue_datetime": row.issue_datetime,
                "decision_time": row.decision_time,
                "target_time": row.target_time,
                "interval_start": row.interval_start,
                "interval_end": row.interval_end,
                "lead_hour": row.lead_hour,
                "forecast_source": row.source,
                "forecast_version": row.forecast_version,
                "mapping_method": row.mapping_method,
                "interpolation_left_lead": row.interpolation_left_lead,
                "interpolation_right_lead": row.interpolation_right_lead,
                "endpoint_hold": row.endpoint_hold,
                "fallback_reason": row.fallback_reason,
                "forecast_kw": row.forecast_kw,
                "forecast_kwh": row.forecast_kwh,
                "predicted_kw": row.forecast_kw,
                "actual_kw": actual.pv_kw,
            }
        )
    _write_csv(destination / "predictions_pv_by_issue.csv", pv_metric_material)
    pv_metrics = evaluate_pv_predictions(pv_metric_material)
    _write_csv(destination / "prediction_metrics.csv", pv_metrics)
    _write_csv(
        destination / "metrics_summary.csv",
        (
            {
                "track": track,
                "question_id": "Q3",
                "model_version": config.model_version,
                "split": "formal_output",
                "metric": key,
                "value": value,
                "status": "HUMAN_RUN_UNREVIEWED",
            }
            for key, value in metrics.items()
        ),
    )
    daily_rows: list[dict[str, Any]] = []
    for day in date_range(config.output_start, config.output_end):
        day_rows = [row for row in formal if date.fromisoformat(row.template_date) == day]
        daily_rows.append({"template_date": day.isoformat(), **economic_metrics(day_rows)})
    _write_csv(destination / "daily_metrics.csv", daily_rows)
    monthly_rows: list[dict[str, Any]] = []
    for month in range(2, 13):
        rows = [row for row in formal if date.fromisoformat(row.template_date).month == month]
        monthly_rows.append({"month": month, **economic_metrics(rows)})
    _write_csv(destination / "monthly_metrics.csv", monthly_rows)
    _write_csv(
        destination / "forecast_alignment_audit.csv",
        (
            {
                "template_date": day.isoformat(),
                "time_semantics": "target_time=issue_datetime+lead_hour",
                "mapping_method": mapping_method,
                "template_start": target_day(day)[0].interval_start.isoformat(),
                "template_end": target_day(day)[-1].interval_end.isoformat(),
                "initial_attachment3_count": sum(row.forecast_source == "attachment3" for row in frozen_days[day].initial_pv),
                "initial_fallback_count": sum(row.forecast_source == "fallback_q2_pv" for row in frozen_days[day].initial_pv),
                "first_slot_issue": frozen_days[day].initial_pv[0].issue_datetime,
                "slot144_issue": frozen_days[day].initial_pv[-1].issue_datetime,
                "slot144_endpoint_hold": frozen_days[day].initial_pv[-1].endpoint_hold,
            }
            for day in date_range(config.warmup_start, config.output_end)
        ),
    )
    numerical_validation = validate_run(
        config, plans, frozen_days, executed_tuple, tuple(versions)
    )
    assertions = {
        "passed": bool(numerical_validation["passed"]),
        "numerical_validation": numerical_validation,
        "checks": {
            "input_hash_gate": True,
            "attachment3_point_mapped": long_check,
            "point_time_semantics": True,
            "issue_set_strict": True,
            "first_hour_previous_issue_or_fallback": True,
            "endpoint_hold_t24_only": True,
            "cost_semantics": cost_semantics,
            "issue_datetime_lte_decision_time": True,
            "executed_history_immutable": True,
            "initial_G_immutable": True,
            "load_forecast_frozen": True,
            "soc_continuous": True,
            "r0_balance": True,
            "dec31_no_fictitious_issue": True,
        },
    }
    _json(destination / "assertions.json", assertions)
    if not assertions["passed"]:
        raise AssertionError(f"Q3 numerical assertions failed: {numerical_validation['failures']}")

    candidate = destination / "result3_candidate.xlsx"
    export_info = export_result3_candidate(config, candidate, plans, executed_tuple)
    export_validation = validate_result3_candidate(
        config,
        candidate,
        plans,
        executed_tuple,
        LOCKED_SHA256["result3.xlsx"],
    )
    _json(destination / "export_validation.json", export_validation)
    if not export_validation["passed"]:
        raise AssertionError("result3_candidate.xlsx round-trip validation failed")

    log_files = sorted(log_dir.glob("*.log"))
    with (destination / "solver.log").open("w", encoding="utf-8") as combined:
        for path in log_files:
            combined.write(f"\n===== {path.name} =====\n")
            combined.write(path.read_text(encoding="utf-8", errors="replace"))
    with (destination / "solver_audit.log").open("w", encoding="utf-8") as audit_log:
        for row in solver_updates:
            audit_log.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    warning = (
        "WARNING-Q3-PLAN-SURPLUS-001: W_pred is retained in planning balance for physical feasibility; "
        "actual W is computed only after replay.\n"
        "INFO-Q3-SOLVER-LOG-001: solver_audit.log is the guaranteed structured audit log; "
        "native HiGHS log files are listed only when physically present.\n"
    )
    (destination / "warnings_and_failures.log").write_text(warning, encoding="utf-8")
    manifest = {
        "question_id": "Q3",
        "stage": 5,
        "track": track,
        "model_version": config.model_version,
        "q2_frozen_model_version": config.q2_frozen_model_version,
        "run_status": "HUMAN_RUN_UNREVIEWED_CANDIDATE",
        "final_competition_result": False,
        "created_at": datetime.now().astimezone().isoformat(),
        "data_version": config.data_version,
        "integrity": integrity,
        "issue_set_minutes": list(issue_set),
        "issue_set_experiment": issue_set_name,
        "mapping_method": mapping_method,
        "cost_semantics": cost_semantics,
        "midnight_sequence": "Q3-MIDNIGHT-SEQUENCE-001",
        "environment": {"python": sys.version, "platform": platform.platform()},
        "solver_name": config.solver_name,
        "solver_backend_versions": sorted({str(row.get("solver_version")) for row in solver_updates}),
        "code_identity": code_identity,
        "formal_output_days": 334,
        "formal_output_start": config.output_start.isoformat(),
        "formal_output_end": config.output_end.isoformat(),
        "assertions_passed": True,
        "export_validation_passed": True,
        "metrics": metrics,
        "export": export_info,
    }
    identity_after = _code_identity(Path(config_path), mapping_path)
    if identity_after["core_python_sha256"] != code_identity["core_python_sha256"] or identity_after["config_sha256"] != code_identity["config_sha256"] or identity_after["revised_mapping_sha256"] != code_identity["revised_mapping_sha256"]:
        raise RuntimeError("Q3_CODE_OR_CONFIG_CHANGED_DURING_RUN")
    _json(destination / "run_manifest.json", manifest)
    (destination / "human_feedback.md").write_text(
        "# Q3人工验收\n\n"
        f"- 轨道：{track}\n- 映射：{mapping_method}\n- 费用语义：{cost_semantics}\n"
        "- 实际运行命令：待填写\n- 环境与Solver版本：待填写\n"
        "- 输入/代码身份检查：待填写\n- 断言是否全通过：待填写\n"
        "- 四工作表Excel回读：待填写\n- 候选Excel人工打开抽查：待填写\n"
        "- Solver evidence完整性：待填写\n- 异常/警告：待填写\n- 人工结论：待填写\n",
        encoding="utf-8",
    )
    return destination


def value_decomposition(reference_cost: float, initial_cost: float, rolling_cost: float) -> dict[str, float]:
    return {
        "Value_A3_initial": reference_cost - initial_cost,
        "Value_intraday_update": initial_cost - rolling_cost,
        "Total_Q3_Improvement": reference_cost - rolling_cost,
    }
