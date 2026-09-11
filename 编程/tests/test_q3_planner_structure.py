from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta

import numpy as np

from q3_baseline.config import Q3Parameters
from q3_baseline.forecast import PVSelection
from q3_baseline.planner import build_adjustment_milp


class Q3PlannerStructureTests(unittest.TestCase):
    def test_adjustment_objective_and_exact_qmax(self):
        params = Q3Parameters()
        start = datetime(2025, 2, 1, 6)
        pv = tuple(
            PVSelection(date(2025, 2, 1), 36 + i, start + timedelta(minutes=10*i), start + timedelta(minutes=10*(i+1)), start, start, 20.0, "attachment3")
            for i in range(2)
        )
        problem = build_adjustment_milp(
            np.array([10.0, 20.0]), np.array([100.0, 100.0]), pv,
            np.array([1.0, 2.0]), 6000.0, params,
        )
        self.assertEqual(problem.col_upper[problem.layout.C.start], params.charge_power_max * params.delta_t)
        np.testing.assert_allclose(problem.objective[problem.layout.Uminus], [0.5, 1.0])
        np.testing.assert_allclose(problem.objective[problem.layout.Uplus], [1.5, 3.0])
        self.assertIn("current_real_soc", problem.row_names)

    def test_no_storage_fixes_charge_and_discharge_to_zero(self):
        params = Q3Parameters()
        start = datetime(2025, 2, 1, 6)
        pv = (PVSelection(date(2025, 2, 1), 36, start, start + timedelta(minutes=10), start, start, 20.0, "attachment3"),)
        problem = build_adjustment_milp(np.array([10.0]), np.array([100.0]), pv, np.array([1.0]), 6000.0, params, no_storage=True)
        self.assertEqual(problem.col_upper[problem.layout.C.start], 0.0)
        self.assertEqual(problem.col_upper[problem.layout.D.start], 0.0)

    def test_adjustment_milp_snaps_tolerance_scale_soc_boundary_drift(self):
        params = Q3Parameters()
        start = datetime(2025, 2, 1, 6)
        pv = (
            PVSelection(
                date(2025, 2, 1), 36, start, start + timedelta(minutes=10),
                start, start, 20.0, "attachment3",
            ),
        )
        problem = build_adjustment_milp(
            np.array([10.0]), np.array([100.0]), pv, np.array([1.0]),
            1199.9999995, params,
        )
        row = problem.row_names.index("current_real_soc")
        self.assertEqual(problem.row_lower[row], params.soc_min)
        self.assertEqual(problem.row_upper[row], params.soc_min)


if __name__ == "__main__":
    unittest.main()
