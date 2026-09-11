from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

from q1_baseline.solver_backend import HighsPyBackend
from q3_baseline.config import Q3Parameters
from q3_baseline.forecast import PVSelection
from q3_baseline.planner import build_adjustment_milp


@unittest.skipUnless(os.environ.get("RUN_Q3_SOLVER_INTEGRATION") == "1", "REQUIRES_HUMAN_RUN")
class Q3SolverIntegrationTests(unittest.TestCase):
    def test_toy_adjustment_milp(self):
        start = datetime(2025, 2, 1, 6)
        pv = (PVSelection(date(2025, 2, 1), 36, start, start + timedelta(minutes=10), start, start, 0.0, "attachment3"),)
        problem = build_adjustment_milp(np.array([10.0]), np.array([60.0]), pv, np.array([1.0]), 6000.0, Q3Parameters(), no_storage=True)
        with tempfile.TemporaryDirectory() as directory:
            result = HighsPyBackend().solve(problem, Q3Parameters(), Path(directory) / "toy.log")
        self.assertEqual(result.status, "OPTIMAL")


if __name__ == "__main__":
    unittest.main()
