from __future__ import annotations

import unittest

from q1_baseline.time_index import (
    build_official_q1_intervals,
    natural_day_zero_based_order,
)


class TimeMappingTests(unittest.TestCase):
    def test_locked_template_mapping(self) -> None:
        intervals = build_official_q1_intervals()
        expected = {
            1: ("0:10", "0:10-0:20"),
            2: ("0:20", "0:20-0:30"),
            143: ("23:50", "23:50-0:00+1"),
            144: ("0:00+1", "0:00+1-0:10+1"),
        }
        for slot, pair in expected.items():
            item = intervals[slot - 1]
            self.assertEqual((item.sample_time_label, item.official_template_label), pair)

    def test_natural_day_order_does_not_change_template_order(self) -> None:
        order = natural_day_zero_based_order()
        self.assertEqual(order[:3], (143, 0, 1))
        self.assertEqual(order[-1], 142)
        self.assertEqual(sorted(order), list(range(144)))


if __name__ == "__main__":
    unittest.main()

