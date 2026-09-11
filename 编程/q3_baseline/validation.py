from __future__ import annotations

from datetime import date, datetime, time, timedelta

import numpy as np

from .config import Q3Config
from .forecast import FrozenPlanningDay
from .planner import RollingPlan
from .state_machine import ExecutedInterval, PlanVersionRow


def validate_run(
    config: Q3Config,
    plans: dict[date, RollingPlan],
    frozen_days: dict[date, FrozenPlanningDay],
    executed: tuple[ExecutedInterval, ...],
    versions: tuple[PlanVersionRow, ...],
) -> dict[str, object]:
    params = config.parameters
    failures: list[str] = []
    if len(plans) != 365 or len(executed) != 365 * 144:
        failures.append("calendar/cardinality")
    ordered = sorted(executed, key=lambda row: row.interval_start)
    for left, right in zip(ordered, ordered[1:]):
        if left.interval_end != right.interval_start:
            failures.append(f"physical_gap:{left.interval_end}->{right.interval_start}")
            break
        if abs(left.soc_after - right.soc_before) > params.feasibility_tolerance:
            failures.append(f"soc_discontinuity:{right.interval_start}")
            break
    qmax_c = params.charge_power_max * params.delta_t
    qmax_d = params.discharge_power_max * params.delta_t
    max_balance = 0.0
    max_soc_residual = 0.0
    for row in ordered:
        if min(row.G, row.Q, row.C, row.D, row.E, row.W) < -params.feasibility_tolerance:
            failures.append(f"negative_energy:{row.interval_start}")
            break
        if row.C > qmax_c + params.feasibility_tolerance or row.D > qmax_d + params.feasibility_tolerance:
            failures.append(f"power_limit:{row.interval_start}")
            break
        if row.C > params.feasibility_tolerance and row.D > params.feasibility_tolerance:
            failures.append(f"charge_discharge_mutex:{row.interval_start}")
            break
        if not params.soc_min - params.feasibility_tolerance <= row.soc_after <= params.soc_max + params.feasibility_tolerance:
            failures.append(f"soc_bound:{row.interval_start}")
            break
        balance = row.Q + row.pv_actual_kwh + row.D + row.E - row.load_actual_kwh - row.C - row.W
        max_balance = max(max_balance, abs(balance))
        expected_soc = row.soc_before + params.charge_efficiency * row.C - row.D / params.discharge_efficiency
        max_soc_residual = max(max_soc_residual, abs(row.soc_after - expected_soc))
        if row.issue_datetime is not None and row.issue_datetime > row.interval_start:
            failures.append(f"future_issue:{row.interval_start}")
            break
    for day, plan in plans.items():
        if len(plan.G) != 144 or len(plan.Q) != 144:
            failures.append(f"plan_shape:{day}")
        if frozen_days[day].initial_pv[-1].forecast_source != "fallback_q2_pv":
            failures.append(f"slot144_fallback:{day}")
        if not np.array_equal(frozen_days[day].load_plan_kw, frozen_days[day].q2_forecast.planning_load_kw):
            failures.append(f"load_not_frozen:{day}")
    version_g: dict[tuple[str, int], float] = {}
    for row in versions:
        key = row.template_date, row.template_slot
        if key in version_g and version_g[key] != row.G_initial:
            failures.append(f"G_mutated:{key}")
            break
        version_g[key] = row.G_initial
        if row.issue_datetime is not None and row.issue_datetime > row.decision_time:
            failures.append(f"version_future_issue:{key}")
            break
        if row.interval_start < row.decision_time:
            failures.append(f"version_rewrites_history:{key}")
            break
    for day in sorted(plans)[1:]:
        midnight_start = datetime.combine(day, time.min)
        previous = next((row for row in ordered if row.interval_start == midnight_start), None)
        if previous is None or abs(plans[day].S[0] - previous.soc_after) > params.feasibility_tolerance:
            failures.append(f"midnight_sequence:{day}")
            break
    if max_balance > params.feasibility_tolerance:
        failures.append(f"balance_residual:{max_balance}")
    if max_soc_residual > params.feasibility_tolerance:
        failures.append(f"soc_residual:{max_soc_residual}")
    return {
        "passed": not failures,
        "failures": failures,
        "max_balance_residual": max_balance,
        "max_soc_residual": max_soc_residual,
        "qmax_charge_internal": qmax_c,
        "qmax_discharge_internal": qmax_d,
        "executed_intervals": len(executed),
        "plan_versions": len(versions),
    }
