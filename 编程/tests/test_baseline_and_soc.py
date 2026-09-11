from __future__ import annotations

import unittest

import numpy as np

from q1_baseline.baseline import DispatchSolution, compute_b0
from q1_baseline.metrics import validate_dispatch
from q1_baseline.parameters import Q1Parameters

from tests.helpers import toy_data


class BaselineAndSocTests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = Q1Parameters()
        self.data = toy_data(self.params)

    def test_b0_closed_form(self) -> None:
        solution = compute_b0(self.data, self.params)
        report = validate_dispatch(solution, self.data, self.params)
        self.assertTrue(report.passed)
        np.testing.assert_allclose(solution.G, 100.0)
        np.testing.assert_allclose(solution.W, 0.0)

    def test_nontrivial_cyclic_soc_and_separate_efficiencies(self) -> None:
        T = self.params.interval_count
        charge = np.zeros(T)
        discharge = np.zeros(T)
        mode = np.zeros(T)
        charge[0] = 100.0
        discharge[1] = 81.0
        mode[0] = 1.0
        soc = np.full(T + 1, 6000.0)
        soc[1] = 6090.0
        grid = np.full(T, 100.0) + charge - discharge
        solution = DispatchSolution(
            G=grid,
            C=charge,
            D=discharge,
            W=np.zeros(T),
            z=mode,
            S=soc,
            objective_cost=float(np.sum(grid)),
            solver_name="toy",
            solver_version="toy",
            status="TOY",
            termination_condition="TOY",
            mip_gap=None,
            runtime_seconds=0.0,
            metadata={"round_trip_efficiency": 0.81},
        )
        report = validate_dispatch(solution, self.data, self.params)
        self.assertTrue(report.passed)
        self.assertEqual(solution.S[T - 1], 6000.0)
        self.assertEqual(solution.S[T], solution.S[0])


if __name__ == "__main__":
    unittest.main()

