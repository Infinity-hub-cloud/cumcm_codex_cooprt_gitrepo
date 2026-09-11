from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

import numpy as np

from q1_baseline.solver_backend import backend_by_name
from q2_baseline.config import Q2Parameters
from q2_baseline.planner import solve_daily_plan

from tests.helpers_q2 import normal_forecast


@unittest.skipUnless(os.environ.get("RUN_Q2_SOLVER_INTEGRATION") == "1", "REQUIRES_HUMAN_RUN")
class Q2SolverIntegrationTests(unittest.TestCase):
    def test_full_solver_path_is_human_gated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = solve_daily_plan(
                normal_forecast(date(2025, 2, 1)), np.ones(144), Q2Parameters(),
                6000.0, backend_by_name("highs"), Path(directory) / "solver.log",
            )
        self.assertEqual(plan.status, "OPTIMAL")
        self.assertAlmostEqual(plan.S[0], 6000.0)


if __name__ == "__main__":
    unittest.main()
