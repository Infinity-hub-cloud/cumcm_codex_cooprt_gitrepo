from __future__ import annotations

import unittest
from datetime import date

import numpy as np

from q2_baseline.config import Q2Parameters
from q2_baseline.data import ActualInterval
from q2_baseline.planner import DailyPlan
from q2_baseline.replay import replay_r0
from q2_baseline.time_axis import target_day


class Q2ReplayTests(unittest.TestCase):
    def test_r0_positive_parts_and_costs(self) -> None:
        params = Q2Parameters()
        zeros = np.zeros(144)
        G = zeros.copy(); C = zeros.copy(); D = zeros.copy()
        G[0] = 2.0; C[0] = 1.0
        G[1] = 4.0; D[1] = 1.0
        plan = DailyPlan(
            date(2025, 2, 1), "B1", G, C, D, zeros.copy(), zeros.copy(),
            np.full(145, 6000.0), 0.0, "TOY", "1", "OPTIMAL", "TOY", 0.0, 0.0,
        )
        actual = []
        for i, target in enumerate(target_day(date(2025, 2, 1))):
            load = 5.0 if i in (0, 1) else 0.0
            actual.append(ActualInterval(date(2025, 2, 1), i + 1, target.interval_start, target.interval_end, load / params.delta_t, 0.0, load, 0.0))
        price = np.full(144, 2.0)
        result = replay_r0(plan, tuple(actual), price, params)
        self.assertEqual(result.emergency_kwh[0], 4.0)
        self.assertEqual(result.emergency_kwh[1], 0.0)
        self.assertEqual(result.surplus_kwh[1], 0.0)
        self.assertEqual(result.planned_purchase_cost[0], 4.0)
        self.assertEqual(result.emergency_purchase_cost[0], 40.0)


if __name__ == "__main__":
    unittest.main()

