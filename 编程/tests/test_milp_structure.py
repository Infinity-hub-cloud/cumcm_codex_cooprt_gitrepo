from __future__ import annotations

import unittest

import numpy as np

from q1_baseline.milp import build_q1_milp
from q1_baseline.parameters import Q1Parameters

from tests.helpers import toy_data


class MilpStructureTests(unittest.TestCase):
    def test_dimensions_integrality_and_exact_power_conversion(self) -> None:
        params = Q1Parameters()
        problem = build_q1_milp(toy_data(params), params)
        self.assertEqual(problem.num_col, 6 * 144 + 1)
        self.assertEqual(problem.num_row, 4 * 144 + 3)
        self.assertEqual(int(np.sum(problem.integrality)), 144)
        expected_q_max = params.charge_power_max * params.delta_t
        np.testing.assert_allclose(problem.col_upper[problem.layout.C], expected_q_max)
        np.testing.assert_allclose(problem.col_upper[problem.layout.D], expected_q_max)
        self.assertNotEqual(expected_q_max, 833.3333)

    def test_required_soc_rows_are_present(self) -> None:
        problem = build_q1_milp(toy_data(), Q1Parameters())
        self.assertEqual(
            problem.row_names[-3:],
            ("soc_midnight_initial", "soc_midnight_terminal", "soc_cycle_0010"),
        )


if __name__ == "__main__":
    unittest.main()

