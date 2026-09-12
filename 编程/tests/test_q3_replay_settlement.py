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
        self.assertEqual(row.fulfilled_normal_purchase_cost, 16.0)
        self.assertEqual(row.cancelled_purchase_principal, 4.0)
        self.assertEqual(row.downward_adjustment_penalty, 2.0)
        self.assertEqual(row.upward_adjustment_cost, 0.0)
        self.assertEqual(row.emergency_purchase_cost, 120.0)
        self.assertEqual(row.regular_purchase_cost, 18.0)
        self.assertEqual(row.total_cost, 138.0)

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

    def test_equal_purchase_and_model_a_sensitivity(self):
        day = date(2025, 2, 1); plan = zero_vector_plan(day); plan.G[0] = plan.Q[0] = 10.0
        start = datetime(2025, 2, 1, 0, 10)
        actual = ActualInterval(day, 1, start, start + timedelta(minutes=10), 60.0, 0.0, 10.0, 0.0)
        self.assertEqual(execute_r0_interval(plan, 1, actual, 2.0, 6000.0, Q3Parameters()).regular_purchase_cost, 20.0)
        plan.Q[0] = 8.0
        from dataclasses import replace
        row = execute_r0_interval(plan, 1, actual, 2.0, 6000.0, replace(Q3Parameters(), cost_semantics="MODEL_A"))
        self.assertEqual(row.regular_purchase_cost, 22.0)

    def test_simultaneous_charge_discharge_is_rejected(self):
        day = date(2025, 2, 1); plan = zero_vector_plan(day); plan.C[0] = plan.D[0] = 1.0
        start = datetime(2025, 2, 1, 0, 10)
        actual = ActualInterval(day, 1, start, start + timedelta(minutes=10), 0.0, 0.0, 0.0, 0.0)
        with self.assertRaisesRegex(AssertionError, "simultaneous"):
            execute_r0_interval(plan, 1, actual, 1.0, 6000.0, Q3Parameters())


if __name__ == "__main__":
    unittest.main()
