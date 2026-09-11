from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from q1_baseline.metrics import validate_dispatch
from q1_baseline.optimize import solve_b1_milp
from q1_baseline.parameters import Q1Parameters
from q1_baseline.solver_backend import HighsPyBackend

from tests.helpers import toy_data


@unittest.skipUnless(
    os.environ.get("RUN_Q1_SOLVER_INTEGRATION") == "1",
    "REQUIRES_HUMAN_RUN: would invoke a real MILP solver",
)
class SolverIntegrationTests(unittest.TestCase):
    def test_toy_milp(self) -> None:
        params = Q1Parameters(time_limit_seconds=30.0)
        data = toy_data(params)
        with tempfile.TemporaryDirectory() as temp_dir:
            solution = solve_b1_milp(
                data, params, HighsPyBackend(), Path(temp_dir) / "solver.log"
            )
        self.assertTrue(
            validate_dispatch(solution, data, params, require_optimal=True).passed
        )


if __name__ == "__main__":
    unittest.main()

