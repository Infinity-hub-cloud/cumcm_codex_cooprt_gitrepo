from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from q2_baseline.config import Q2Parameters
from q2_baseline.data import ActualInterval
from q2_baseline.planner import DailyPlan


@dataclass(frozen=True)
class Q4ReplayDay:
    plan: DailyPlan
    actual: tuple[ActualInterval, ...]
    price_actual: np.ndarray
    emergency_kwh: np.ndarray
    surplus_kwh: np.ndarray
    regular_cost: np.ndarray
    emergency_cost: np.ndarray

    @property
    def total_cost(self) -> float:
        return float(np.sum(self.regular_cost) + np.sum(self.emergency_cost))


def replay_actual_price(
    plan: DailyPlan,
    actual: tuple[ActualInterval, ...],
    price_actual: np.ndarray,
    params: Q2Parameters,
) -> Q4ReplayDay:
    if len(actual) != 144 or price_actual.shape != (144,):
        raise ValueError("Q4 replay requires 144 actual and price intervals")
    if any(row.source_date != plan.template_date for row in actual):
        raise ValueError("actual rows do not match plan template date")
    if not np.all(np.isfinite(price_actual)) or np.any(price_actual <= 0):
        raise ValueError("actual Attachment4 prices must be finite and positive")
    load = np.asarray([row.load_kwh for row in actual], dtype=float)
    pv = np.asarray([row.pv_kwh for row in actual], dtype=float)
    imbalance = load + plan.C - plan.G - pv - plan.D
    emergency = np.maximum(imbalance, 0.0)
    surplus = np.maximum(-imbalance, 0.0)
    regular = price_actual * plan.G
    emergency_cost = params.emergency_price_multiplier * price_actual * emergency
    balance = plan.G + pv + plan.D + emergency - load - plan.C - surplus
    if float(np.max(np.abs(balance))) > params.feasibility_tolerance:
        raise AssertionError("Q4 R0 realized energy balance failed")
    return Q4ReplayDay(plan, actual, price_actual.copy(), emergency, surplus, regular, emergency_cost)
