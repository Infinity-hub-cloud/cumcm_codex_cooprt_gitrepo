from __future__ import annotations

import unittest
from datetime import date, datetime

import numpy as np

from q3_baseline.forecast import PVSelection, assert_load_frozen, initial_planning_day

from tests.helpers_q3 import attachment3_issues, q2_frozen_day


class Q3CausalityTests(unittest.TestCase):
    def test_future_issue_is_rejected(self):
        row = PVSelection(
            date(2025, 2, 1), 36, datetime(2025, 2, 1, 6), datetime(2025, 2, 1, 6, 10),
            datetime(2025, 2, 1, 6), datetime(2025, 2, 1, 12), 20.0, "attachment3",
        )
        with self.assertRaisesRegex(AssertionError, "issue_datetime"):
            row.assert_causal()

    def test_load_forecast_is_frozen(self):
        day = date(2025, 2, 1)
        frozen = initial_planning_day(day, q2_frozen_day(day), attachment3_issues(day))
        assert_load_frozen(frozen, frozen.load_plan_kw.copy())
        changed = frozen.load_plan_kw.copy()
        changed[0] += 1
        with self.assertRaisesRegex(AssertionError, "LOAD_FORECAST_MUTATION"):
            assert_load_frozen(frozen, changed)


if __name__ == "__main__":
    unittest.main()
