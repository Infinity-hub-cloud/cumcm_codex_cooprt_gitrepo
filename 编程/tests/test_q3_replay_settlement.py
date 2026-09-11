from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta

from q2_baseline.data import ActualInterval
from q3_baseline.config import Q3Parameters
from q3_baseline.state_machine import execute_r0_interval

from tests.helpers_q3 import zero_vector_plan


class Q3ReplaySettlementTests(unittest.TestCase):
    def test_final_q_and_four_cost_parts_are_used(self):
        day = date(2025, 2, 1)
        plan = zero_vector_plan(day)
        plan.G[0] = 10.0
        plan.Q[0] = 8.0
        start = datetime(2025, 2, 1, 0, 10)
        actual = ActualInterval(day, 1, start, start + timedelta(minutes=10), 120.0, 0.0, 20.0, 0.0)
        row = execute_r0_interval(plan, 1, actual, 2.0, 6000.0, Q3Parameters())
        self.assertEqual(row.E, 12.0)
        self.assertEqual(row.planned_purchase_cost, 20.0)
        self.assertEqual(row.downward_adjustment_penalty, 2.0)
        self.assertEqual(row.upward_adjustment_cost, 0.0)
        self.assertEqual(row.emergency_purchase_cost, 120.0)
        self.assertEqual(row.total_cost, 142.0)

    def test_upward_adjustment_cost(self):
        day = date(2025, 2, 1)
        plan = zero_vector_plan(day)
        plan.G[0] = 10.0
        plan.Q[0] = 12.0
        start = datetime(2025, 2, 1, 0, 10)
        actual = ActualInterval(day, 1, start, start + timedelta(minutes=10), 72.0, 0.0, 12.0, 0.0)
        row = execute_r0_interval(plan, 1, actual, 2.0, 6000.0, Q3Parameters())
        self.assertEqual(row.E, 0.0)
        self.assertEqual(row.upward_adjustment_cost, 6.0)
        self.assertEqual(row.total_cost, 26.0)


if __name__ == "__main__":
    unittest.main()
