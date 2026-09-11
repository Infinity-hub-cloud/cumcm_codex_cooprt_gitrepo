from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import Q2Parameters
from .data import ActualInterval
from .planner import DailyPlan


@dataclass(frozen=True)
class ReplayDay:
    plan: DailyPlan
    actual: tuple[ActualInterval, ...]
    emergency_kwh: np.ndarray
    surplus_kwh: np.ndarray
    planned_purchase_cost: np.ndarray
    emergency_purchase_cost: np.ndarray

    @property
    def total_cost(self) -> float:
        return float(np.sum(self.planned_purchase_cost) + np.sum(self.emergency_purchase_cost))


def replay_r0(
    plan: DailyPlan,
    actual: tuple[ActualInterval, ...],
    price: np.ndarray,
    params: Q2Parameters,
) -> ReplayDay:
    if len(actual) != 144 or price.shape != (144,):
        raise ValueError("R0 replay requires 144 actual and price intervals")
    if any(row.source_date != plan.template_date for row in actual):
        raise ValueError("R0 actual rows do not match plan template date")
    load = np.asarray([row.load_kwh for row in actual], dtype=np.float64)
    pv = np.asarray([row.pv_kwh for row in actual], dtype=np.float64)
    # Fixed day-ahead G/C/D; forecast error is absorbed only by E/W.
    imbalance = load + plan.C - plan.G - pv - plan.D
    emergency = np.maximum(imbalance, 0.0)
    surplus = np.maximum(-imbalance, 0.0)
    planned_cost = price * plan.G
    emergency_cost = params.emergency_price_multiplier * price * emergency
    result = ReplayDay(plan, actual, emergency, surplus, planned_cost, emergency_cost)
    balance = plan.G + pv + plan.D + emergency - load - plan.C - surplus
    if float(np.max(np.abs(balance))) > params.feasibility_tolerance:
        raise AssertionError("R0 realized energy balance failed")
    return result

