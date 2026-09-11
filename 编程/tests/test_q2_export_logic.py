from __future__ import annotations

import unittest
from datetime import date

from q2_baseline.exporter import merge_emergency_events, natural_day_four_hour_summary, physical_dispatch_rows

from tests.helpers_q2 import zero_replay


class Q2ExportLogicTests(unittest.TestCase):
    def test_natural_midnight_comes_from_previous_template_slot144(self) -> None:
        jan31 = zero_replay(date(2025, 1, 31))
        feb1 = zero_replay(date(2025, 2, 1))
        jan31.plan.C[-1] = 7.0
        feb1.plan.C[0] = 3.0
        physical = physical_dispatch_rows((jan31, feb1))
        summary = natural_day_four_hour_summary(physical, date(2025, 2, 1))
        self.assertEqual(summary[0][0], 10.0)

    def test_consecutive_positive_emergency_intervals_are_merged(self) -> None:
        previous = zero_replay(date(2025, 1, 31), {143: 1.0})
        current = zero_replay(date(2025, 2, 1), {0: 2.0, 1: 3.0, 3: 4.0})
        physical = physical_dispatch_rows((previous, current))
        events = merge_emergency_events(physical, date(2025, 2, 1), 1e-6)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].energy_kwh, 6.0)
        self.assertEqual(events[1].energy_kwh, 4.0)


if __name__ == "__main__":
    unittest.main()

