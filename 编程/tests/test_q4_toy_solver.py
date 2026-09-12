from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

from q2_baseline.forecast import ForecastDay, ForecastRow
from q4_baseline.config import Q4Parameters
from q4_baseline.planner import PricePlanDay, solve_price_plan
from q1_baseline.solver_backend import HighsPyBackend


def toy_forecast() -> ForecastDay:
    rows = []
    day = date(2025, 2, 1)
    decision = datetime.combine(day, datetime.min.time())
    for slot in range(1, 145):
        start = decision + timedelta(minutes=10 * slot)
        rows.append(ForecastRow(day, slot, decision, decision, start, start + timedelta(minutes=10), "toy", "toy-v1", None, decision, 100.0, 0.0))
    return ForecastDay(day, tuple(rows))


class Q4ToySolver(unittest.TestCase):
    def test_price_plan_shape_and_positive_gate(self):
        day = date(2025, 2, 1)
        prices = np.full(144, 0.5)
        plan = PricePlanDay(day, datetime.combine(day, datetime.min.time()), "P1_WEEKDAY_SAME_CLOCK", prices, prices.copy(), prices.copy(), np.zeros(144, dtype=bool), None, tuple(), 0)
        plan.validate()
        self.assertEqual(plan.price_plan.shape, (144,))

    @unittest.skipUnless(os.getenv("RUN_Q4_SOLVER_INTEGRATION") == "1", "REQUIRES_HUMAN_RUN")
    def test_q4_toy_highs(self):
        params = Q4Parameters()
        prices = np.full(144, 0.5)
        day = date(2025, 2, 1)
        price_day = PricePlanDay(day, datetime.combine(day, datetime.min.time()), "P1_WEEKDAY_SAME_CLOCK", prices, prices.copy(), prices.copy(), np.zeros(144, dtype=bool), None, tuple(), 0)
        with tempfile.TemporaryDirectory() as tmp:
            result = solve_price_plan(toy_forecast(), price_day, params, 6000.0, HighsPyBackend(), Path(tmp) / "toy.log")
        self.assertEqual(result.status, "OPTIMAL")
        self.assertEqual(result.G.shape, (144,))


if __name__ == "__main__":
    unittest.main()
