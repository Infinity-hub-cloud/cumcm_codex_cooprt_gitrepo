from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
from dataclasses import replace

from q1_baseline.solver_backend import HighsPyBackend
from q3_baseline.config import Q3Parameters
from q3_baseline.planner import build_adjustment_milp
from tests.helpers_q3 import pv_selection


@unittest.skipUnless(os.environ.get("RUN_Q3_SOLVER_INTEGRATION") == "1", "REQUIRES_HUMAN_RUN")
class Q3SolverIntegrationTests(unittest.TestCase):
    def solve(self, demand_kwh, semantics="MODEL_B"):
        start = datetime(2025, 2, 1, 6)
        pv = (pv_selection(date(2025, 2, 1), 36, start, kw=0.0),)
        params=replace(Q3Parameters(),cost_semantics=semantics)
        problem = build_adjustment_milp(np.array([10.0]), np.array([demand_kwh*6]), pv, np.array([1.0]), 6000.0, params, no_storage=True)
        with tempfile.TemporaryDirectory() as directory:
            result = HighsPyBackend().solve(problem, params, Path(directory) / "toy.log")
        self.assertEqual(result.status, "OPTIMAL")
        return result,problem

    def test_model_b_q_less_equal_greater(self):
        for demand,expected_q,expected_cost in ((6.,6.,8.),(10.,10.,10.),(14.,14.,16.)):
            with self.subTest(demand=demand):
                result,problem=self.solve(demand)
                self.assertAlmostEqual(result.vector[problem.layout.Q.start],expected_q)
                self.assertAlmostEqual(result.objective_cost,expected_cost)

    def test_model_a_sensitivity_downward_is_dominated(self):
        result,problem=self.solve(6.,"MODEL_A")
        self.assertAlmostEqual(result.vector[problem.layout.Q.start],10.)
        self.assertAlmostEqual(result.objective_cost,10.)


if __name__ == "__main__":
    unittest.main()
