from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import numpy as np

from q1_baseline.solver_backend import MILPBackend
from q2_baseline.forecast import ForecastDay
from q2_baseline.planner import DailyPlan, compute_b0_plan, solve_daily_plan
from q2_baseline.config import Q2Parameters


@dataclass(frozen=True)
class PricePlanDay:
    template_date: date
    decision_time: datetime
    predictor_id: str
    price_plan: np.ndarray
    price_actual: np.ndarray
    price_pred: np.ndarray
    observed_at_decision: np.ndarray
    history_last_visible_time: datetime | None
    fallback_reasons: tuple[str, ...]
    level_bound_hit_count: int

    def validate(self) -> None:
        for value in (self.price_plan, self.price_actual, self.price_pred, self.observed_at_decision):
            if value.shape != (144,):
                raise ValueError("Q4 price day must contain 144 intervals")
        if not np.all(np.isfinite(self.price_plan)) or np.any(self.price_plan <= 0):
            raise RuntimeError("Q4_PRICE_PREDICTION_HARD_FAIL: invalid planning price")


def solve_price_plan(
    forecast: ForecastDay,
    price_plan: PricePlanDay,
    params: Q2Parameters,
    initial_soc_0010: float,
    backend: MILPBackend,
    log_path: Path,
    *,
    no_storage: bool = False,
) -> DailyPlan:
    if no_storage:
        return compute_b0_plan(forecast, price_plan.price_plan, params, initial_soc_0010)
    return solve_daily_plan(forecast, price_plan.price_plan, params, initial_soc_0010, backend, log_path)
