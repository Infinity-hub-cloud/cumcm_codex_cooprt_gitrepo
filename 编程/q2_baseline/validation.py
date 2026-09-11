from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .config import Q2Parameters
from .forecast import ForecastDay
from .planner import DailyPlan
from .replay import ReplayDay


@dataclass(frozen=True)
class AssertionRecord:
    name: str
    passed: bool
    value: Any
    limit: Any
    unit: str = ""


def validate_day(
    forecast: ForecastDay,
    plan: DailyPlan,
    replay: ReplayDay,
    price: np.ndarray,
    params: Q2Parameters,
    expected_initial_soc: float,
    require_optimal: bool,
) -> tuple[bool, tuple[AssertionRecord, ...], dict[str, float]]:
    forecast.assert_causal()
    tol = params.feasibility_tolerance
    pred_load = forecast.planning_load_kw * params.delta_t
    pred_pv = forecast.pv_pred_kw * params.delta_t
    pred_balance = plan.G + pred_pv + plan.D - pred_load - plan.C - plan.W_pred
    soc_residual = plan.S[1:] - plan.S[:-1] - params.charge_efficiency * plan.C + plan.D / params.discharge_efficiency
    actual_load = np.asarray([row.load_kwh for row in replay.actual])
    actual_pv = np.asarray([row.pv_kwh for row in replay.actual])
    realized_balance = plan.G + actual_pv + plan.D + replay.emergency_kwh - actual_load - plan.C - replay.surplus_kwh
    assertions: list[AssertionRecord] = []

    def add(name: str, passed: bool, value: Any, limit: Any, unit: str = "") -> None:
        assertions.append(AssertionRecord(name, bool(passed), value, limit, unit))

    arrays = (plan.G, plan.C, plan.D, plan.W_pred, plan.z, plan.S, replay.emergency_kwh, replay.surplus_kwh)
    add("all_finite", all(np.all(np.isfinite(x)) for x in arrays), True, True)
    add("grid_nonnegative", float(np.min(plan.G)) >= -tol, float(np.min(plan.G)), f">={-tol}", "kWh")
    add("charge_nonnegative", float(np.min(plan.C)) >= -tol, float(np.min(plan.C)), f">={-tol}", "kWh")
    add("discharge_nonnegative", float(np.min(plan.D)) >= -tol, float(np.min(plan.D)), f">={-tol}", "kWh")
    add("predicted_waste_nonnegative", float(np.min(plan.W_pred)) >= -tol, float(np.min(plan.W_pred)), f">={-tol}", "kWh")
    add("emergency_nonnegative", float(np.min(replay.emergency_kwh)) >= -tol, float(np.min(replay.emergency_kwh)), f">={-tol}", "kWh")
    add("realized_surplus_nonnegative", float(np.min(replay.surplus_kwh)) >= -tol, float(np.min(replay.surplus_kwh)), f">={-tol}", "kWh")
    add("charge_exact_qmax", float(np.max(plan.C)) <= params.charge_energy_max + tol, float(np.max(plan.C)), params.charge_energy_max, "kWh")
    add("discharge_exact_qmax", float(np.max(plan.D)) <= params.discharge_energy_max + tol, float(np.max(plan.D)), params.discharge_energy_max, "kWh")
    add("soc_lower_bound", float(np.min(plan.S)) >= params.soc_min - tol, float(np.min(plan.S)), params.soc_min, "kWh")
    add("soc_upper_bound", float(np.max(plan.S)) <= params.soc_max + tol, float(np.max(plan.S)), params.soc_max, "kWh")
    add("soc_window_start_0010", abs(float(plan.S[0]) - expected_initial_soc) <= tol, float(plan.S[0]), expected_initial_soc, "kWh")
    add("predicted_balance", float(np.max(np.abs(pred_balance))) <= tol, float(np.max(np.abs(pred_balance))), tol, "kWh")
    add("soc_recurrence", float(np.max(np.abs(soc_residual))) <= tol, float(np.max(np.abs(soc_residual))), tol, "kWh")
    simultaneous = int(np.count_nonzero((plan.C > tol) & (plan.D > tol)))
    add("no_simultaneous_charge_discharge", simultaneous == 0, simultaneous, 0, "intervals")
    integrality_error = float(np.max(np.abs(plan.z - np.rint(plan.z))))
    add("binary_integrality", integrality_error <= params.integrality_tolerance, integrality_error, params.integrality_tolerance)
    cold = forecast.cold_mask
    cold_commitment = 0.0 if not np.any(cold) else float(np.max(np.abs(np.concatenate((plan.G[cold], plan.C[cold], plan.D[cold])))))
    add("cold_start_zero_commitment", cold_commitment <= tol, cold_commitment, tol, "kWh")
    leakage = sum(row.source_interval_end is not None and row.source_interval_end > row.decision_time for row in forecast.rows)
    add("no_forecast_leakage", leakage == 0, leakage, 0, "rows")
    add("realized_r0_balance", float(np.max(np.abs(realized_balance))) <= tol, float(np.max(np.abs(realized_balance))), tol, "kWh")
    overlap = int(np.count_nonzero((replay.emergency_kwh > tol) & (replay.surplus_kwh > tol)))
    add("no_emergency_surplus_overlap", overlap == 0, overlap, 0, "intervals")
    cost_error = abs(float(np.dot(price, plan.G)) - float(np.sum(replay.planned_purchase_cost)))
    add("planned_cost_identity", cost_error <= params.aggregate_tolerance, cost_error, params.aggregate_tolerance, "yuan")
    objective_error = abs(float(np.dot(price, plan.G)) - plan.objective_cost)
    add("objective_recomputed", objective_error <= params.aggregate_tolerance, objective_error, params.aggregate_tolerance, "yuan")
    emergency_error = abs(float(np.dot(params.emergency_price_multiplier * price, replay.emergency_kwh)) - float(np.sum(replay.emergency_purchase_cost)))
    add("emergency_cost_identity", emergency_error <= params.aggregate_tolerance, emergency_error, params.aggregate_tolerance, "yuan")
    total_cost_error = abs(replay.total_cost - float(np.sum(replay.planned_purchase_cost) + np.sum(replay.emergency_purchase_cost)))
    add("total_cost_identity", total_cost_error <= params.aggregate_tolerance, total_cost_error, params.aggregate_tolerance, "yuan")
    if require_optimal:
        add("solver_status_optimal", plan.status == "OPTIMAL", plan.status, "OPTIMAL")
        add("mip_gap", plan.mip_gap is not None and plan.mip_gap <= params.mip_rel_gap + 1e-12, plan.mip_gap, params.mip_rel_gap)
    metrics = {
        "planned_grid_kwh": float(np.sum(plan.G)),
        "charge_kwh": float(np.sum(plan.C)),
        "discharge_kwh": float(np.sum(plan.D)),
        "emergency_kwh": float(np.sum(replay.emergency_kwh)),
        "surplus_kwh": float(np.sum(replay.surplus_kwh)),
        "planned_purchase_cost_yuan": float(np.sum(replay.planned_purchase_cost)),
        "emergency_purchase_cost_yuan": float(np.sum(replay.emergency_purchase_cost)),
        "total_cost_yuan": replay.total_cost,
        "soc_start_0010_kwh": float(plan.S[0]),
        "soc_end_0010_next_day_kwh": float(plan.S[-1]),
        "max_forecast_load_abs_error_kw": float(np.max(np.abs(forecast.load_pred_kw - np.asarray([x.load_kw for x in replay.actual])))),
        "max_forecast_pv_abs_error_kw": float(np.max(np.abs(forecast.pv_pred_kw - np.asarray([x.pv_kw for x in replay.actual])))),
    }
    return all(item.passed for item in assertions), tuple(assertions), metrics


def assertion_payload(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "passed": all(record["passed"] for record in records),
        "daily": records,
    }


def records_to_dict(items: tuple[AssertionRecord, ...]) -> list[dict[str, Any]]:
    return [asdict(item) for item in items]
