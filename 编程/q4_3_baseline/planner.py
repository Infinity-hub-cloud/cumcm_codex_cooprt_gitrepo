from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from q3_baseline.forecast import FrozenPlanningDay, PVSelection
from q3_baseline.planner import RollingPlan, build_adjustment_milp, solve_and_apply_adjustment, solve_initial_plan

from .forecast_adapter import RollingPriceForecast


def solve_price_aware_initial(
    frozen: FrozenPlanningDay,
    prices: RollingPriceForecast,
    params: Any,
    initial_soc_0010: float,
    backend: Any,
    log_path: Path,
) -> RollingPlan:
    if prices.start_slot != 1 or len(prices.rows) != 144:
        raise AssertionError("Q4-3 initial solve requires all 144 prices")
    return solve_initial_plan(frozen, prices.price_plan, params, initial_soc_0010, backend, log_path)


def solve_price_aware_suffix(
    plan: RollingPlan,
    frozen: FrozenPlanningDay,
    pv_rows: tuple[PVSelection, ...],
    prices: RollingPriceForecast,
    current_soc: float,
    params: Any,
    backend: Any,
    log_path: Path,
) -> dict[str, object]:
    if prices.start_slot != pv_rows[0].template_slot or len(prices.rows) != len(pv_rows):
        raise AssertionError("PV and price suffix horizons differ")
    full_price = np.zeros(144, dtype=float)
    full_price[prices.start_slot - 1 :] = prices.price_plan
    return solve_and_apply_adjustment(
        plan, frozen, pv_rows, full_price, current_soc, params, backend, log_path
    )


__all__ = [
    "RollingPlan",
    "build_adjustment_milp",
    "solve_price_aware_initial",
    "solve_price_aware_suffix",
]
