from __future__ import annotations

import unittest
from datetime import date, datetime, time, timedelta

from q2_baseline.time_axis import target_interval
from q3_baseline.forecast import FALLBACK_Q2_PV_SOURCE, initial_planning_day, pv_for_unexecuted
from q3_baseline.state_machine import interval_state

from tests.helpers_q3 import attachment3_issues, q2_frozen_day


class Q3TimeAlignmentTests(unittest.TestCase):
    def test_0000_issue_has_143_direct_matches_and_slot144_fallback(self):
        day = date(2025, 2, 1)
        frozen = initial_planning_day(day, q2_frozen_day(day), attachment3_issues(day))
        self.assertEqual(sum(row.forecast_source == "attachment3" for row in frozen.initial_pv), 143)
        self.assertEqual(frozen.initial_pv[0].interval_start, datetime(2025, 2, 1, 0, 10))
        self.assertEqual(frozen.initial_pv[142].interval_start, datetime(2025, 2, 1, 23, 50))
        self.assertEqual(frozen.initial_pv[143].interval_start, datetime(2025, 2, 2, 0, 0))
        self.assertEqual(frozen.initial_pv[143].forecast_source, FALLBACK_Q2_PV_SOURCE)

    def test_interval_index_is_not_template_slot(self):
        day = date(2025, 2, 1)
        data = attachment3_issues(day, (0,))
        issue = data.issue(datetime.combine(day, time.min))
        target = target_interval(day, 1)
        matched = issue[(target.interval_start, target.interval_end)]
        self.assertEqual(matched.natural_interval_index, 2)
        self.assertNotEqual(matched.natural_interval_index, target.template_slot)

    def test_attachment3_uses_physical_interval_index_for_lookup(self):
        day = date(2025, 2, 1)
        data = attachment3_issues(day)
        target = target_interval(day, 36)
        key = (target.interval_start, target.interval_end)
        self.assertIn(key, data.by_physical)
        selected = data.latest_covering(datetime(2025, 2, 1, 6), key, (0, 360))
        self.assertIsNotNone(selected)
        self.assertEqual(selected.issue_datetime, datetime(2025, 2, 1, 6))

    def test_0600_boundary(self):
        day = date(2025, 2, 1)
        decision = datetime(2025, 2, 1, 6, 0)
        self.assertEqual(interval_state(target_interval(day, 35), decision), "frozen")
        self.assertEqual(interval_state(target_interval(day, 36), decision), "adjustable")
        self.assertEqual(interval_state(target_interval(day, 37), decision), "adjustable")

    def test_1200_and_1800_boundaries_use_the_same_closed_open_rule(self):
        day = date(2025, 2, 1)
        for hour, last_frozen_slot, first_adjustable_slot in ((12, 71, 72), (18, 107, 108)):
            decision = datetime(2025, 2, 1, hour, 0)
            self.assertEqual(
                interval_state(target_interval(day, last_frozen_slot), decision), "frozen"
            )
            self.assertEqual(
                interval_state(target_interval(day, first_adjustable_slot), decision), "adjustable"
            )

    def test_next_midnight_updates_only_old_slot144(self):
        day = date(2025, 2, 1)
        data = attachment3_issues(day)
        next_data = attachment3_issues(day + timedelta(days=1), (0,))
        combined = type(data)(data.rows + next_data.rows, {**data.by_issue, **next_data.by_issue})
        frozen = initial_planning_day(day, q2_frozen_day(day), combined)
        rows = pv_for_unexecuted(frozen, combined, datetime(2025, 2, 2), (0, 360, 720, 1080))
        self.assertEqual([row.template_slot for row in rows], [144])
        self.assertEqual(rows[0].issue_datetime, datetime(2025, 2, 2))

    def test_dec31_slot144_uses_last_covering_issue_without_fictitious_2026_issue(self):
        day = date(2025, 12, 31)
        data = attachment3_issues(day)
        frozen = initial_planning_day(day, q2_frozen_day(day), data)
        rows = pv_for_unexecuted(frozen, data, datetime(2026, 1, 1), (0, 360, 720, 1080))
        self.assertEqual([row.template_slot for row in rows], [144])
        self.assertEqual(rows[0].issue_datetime, datetime(2025, 12, 31, 18))


if __name__ == "__main__":
    unittest.main()
