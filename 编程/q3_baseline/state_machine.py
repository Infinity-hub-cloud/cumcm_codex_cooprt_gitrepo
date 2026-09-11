from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np

from q2_baseline.data import ActualInterval
from q2_baseline.time_axis import TargetInterval

from .config import Q3Parameters
from .planner import RollingPlan, adjustment_positive_parts


@dataclass(frozen=True)
class ExecutedInterval:
    template_date: str
    template_slot: int
    interval_start: datetime
    interval_end: datetime
    G: float
    Q: float
    C: float
    D: float
    E: float
    W: float
    soc_before: float
    soc_after: float
    price: float
    pv_forecast_source: str
    issue_datetime: datetime | None
    load_actual_kwh: float
    pv_actual_kwh: float
    planned_purchase_cost: float
    downward_adjustment_penalty: float
    upward_adjustment_cost: float
    emergency_purchase_cost: float
    total_cost: float


@dataclass(frozen=True)
class PlanVersionRow:
    template_date: str
    template_slot: int
    interval_start: datetime
    interval_end: datetime
    issue_datetime: datetime | None
    decision_time: datetime
    plan_version: str
    G_initial: float
    Q_version: float
    C_version: float
    D_version: float
    soc_before_planned: float
    soc_after_planned: float
    pv_forecast: float
    pv_forecast_source: str
    solver_status: str


def interval_state(target: TargetInterval, decision_time: datetime) -> str:
    if target.interval_end <= decision_time:
        return "frozen"
    if target.interval_start >= decision_time:
        return "adjustable"
    raise AssertionError("decision time cuts through a ten-minute interval")


def soc_after_action(soc_before: float, charge: float, discharge: float, params: Q3Parameters) -> float:
    result = soc_before + params.charge_efficiency * charge - discharge / params.discharge_efficiency
    try:
        return params.normalize_soc(result)
    except ValueError as exc:
        raise AssertionError(f"Q3 SOC action left physical bounds: {exc}") from exc


def execute_r0_interval(
    plan: RollingPlan,
    slot: int,
    actual: ActualInterval,
    price: float,
    soc_before: float,
    params: Q3Parameters,
) -> ExecutedInterval:
    i = slot - 1
    if actual.template_slot != slot or actual.source_date != plan.template_date:
        raise ValueError("actual interval does not match Q3 template slot")
    G, Q, C, D = (float(plan.G[i]), float(plan.Q[i]), float(plan.C[i]), float(plan.D[i]))
    shortage = actual.load_kwh + C - Q - actual.pv_kwh - D
    E = max(shortage, 0.0)
    W = max(-shortage, 0.0)
    soc_after = soc_after_action(soc_before, C, D, params)
    uminus = max(G - Q, 0.0)
    uplus = max(Q - G, 0.0)
    planned = price * G
    down = params.downward_adjustment_multiplier * price * uminus
    up = params.upward_adjustment_multiplier * price * uplus
    emergency = params.emergency_price_multiplier * price * E
    balance = Q + actual.pv_kwh + D + E - actual.load_kwh - C - W
    if abs(balance) > params.feasibility_tolerance:
        raise AssertionError("Q3 R0 realized energy balance failed")
    return ExecutedInterval(
        plan.template_date.isoformat(),
        slot,
        actual.interval_start,
        actual.interval_end,
        G,
        Q,
        C,
        D,
        E,
        W,
        float(soc_before),
        soc_after,
        float(price),
        plan.pv_source[i],
        plan.issue_datetime[i],
        actual.load_kwh,
        actual.pv_kwh,
        planned,
        down,
        up,
        emergency,
        planned + down + up + emergency,
    )


def assert_executed_prefix_immutable(before: tuple[ExecutedInterval, ...], after: tuple[ExecutedInterval, ...]) -> None:
    if before != after[: len(before)]:
        raise AssertionError("Q3 update modified executed history")


def plan_version_rows(
    plan: RollingPlan,
    pv_kw: np.ndarray,
    decision_time: datetime,
    plan_version: str,
    start_slot: int,
) -> tuple[PlanVersionRow, ...]:
    rows: list[PlanVersionRow] = []
    for slot in range(start_slot, 145):
        i = slot - 1
        # Physical times are reconstructed from the immutable template identity.
        from q2_baseline.time_axis import target_interval

        target = target_interval(plan.template_date, slot)
        rows.append(
            PlanVersionRow(
                plan.template_date.isoformat(),
                slot,
                target.interval_start,
                target.interval_end,
                plan.issue_datetime[i],
                decision_time,
                plan_version,
                float(plan.G[i]),
                float(plan.Q[i]),
                float(plan.C[i]),
                float(plan.D[i]),
                float(plan.S[i]),
                float(plan.S[i + 1]),
                float(pv_kw[i]),
                plan.pv_source[i],
                plan.solver_status[i],
            )
        )
    return tuple(rows)


def validate_plan_cost_parts(plan: RollingPlan) -> tuple[np.ndarray, np.ndarray]:
    down, up = adjustment_positive_parts(plan)
    if np.any((down > 0) & (up > 0)):
        raise AssertionError("Uminus and Uplus cannot both be positive")
    return down, up
