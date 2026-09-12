from __future__ import annotations

from datetime import datetime

import numpy as np

from q2_baseline.time_axis import target_day
from q3_baseline.planner import RollingPlan


def suffix_start_slot(template_date, decision_time: datetime) -> int:
    candidates = [row.template_slot for row in target_day(template_date) if row.interval_start >= decision_time]
    if not candidates:
        raise ValueError("decision is outside the template horizon")
    return candidates[0]


def assert_update_contract(
    before: RollingPlan,
    after: RollingPlan,
    start_slot: int,
    executed_prefix: tuple[object, ...],
    executed_prefix_after: tuple[object, ...],
) -> None:
    if not np.array_equal(before.G, after.G):
        raise AssertionError("Q4_3_G_FROZEN_HARD_FAIL")
    prefix = slice(0, start_slot - 1)
    for name in ("Q", "C", "D"):
        if not np.array_equal(getattr(before, name)[prefix], getattr(after, name)[prefix]):
            raise AssertionError(f"Q4_3_EXECUTED_PREFIX_HARD_FAIL:{name}")
    if executed_prefix != executed_prefix_after:
        raise AssertionError("Q4_3_EXECUTED_HISTORY_HARD_FAIL")


def observed_boundary_contract_count(formal_days: int = 334) -> int:
    return formal_days * 3

