from __future__ import annotations

import unittest
from datetime import date

import numpy as np

from q2_baseline.config import Q2Parameters
from q2_baseline.forecast import COLD_START_SOURCE, ForecastDay, ForecastRow
from q2_baseline.planner import build_daily_milp
from q2_baseline.time_axis import decision_time, target_day

from tests.helpers_q2 import normal_forecast


class Q2PlannerStructureTests(unittest.TestCase):
    def test_daily_milp_has_no_terminal_reset_constraint(self) -> None:
        params = Q2Parameters()
        problem = build_daily_milp(normal_forecast(date(2025, 2, 1)), np.ones(144), params, 5432.0)
        self.assertEqual(problem.num_col, 865)
        self.assertEqual(problem.num_row, 577)
        self.assertEqual(problem.row_names[-1], "soc_window_start_0010")
        self.assertFalse(any("terminal" in name or "cycle" in name for name in problem.row_names))

    def test_cold_slot_has_zero_commitment_bounds(self) -> None:
        day = date(2025, 1, 2)
        cutoff = decision_time(day)
        base = list(normal_forecast(day).rows)
        target = target_day(day)[-1]
        base[-1] = ForecastRow(
            day, 144, cutoff, cutoff, target.interval_start, target.interval_end,
            COLD_START_SOURCE, "toy-v1", None, None, 0.0, 0.0,
        )
        problem = build_daily_milp(ForecastDay(day, tuple(base)), np.ones(144), Q2Parameters(), 6000.0)
        q = problem.layout
        self.assertEqual(problem.col_upper[q.G.stop - 1], 0.0)
        self.assertEqual(problem.col_upper[q.C.stop - 1], 0.0)
        self.assertEqual(problem.col_upper[q.D.stop - 1], 0.0)


if __name__ == "__main__":
    unittest.main()

