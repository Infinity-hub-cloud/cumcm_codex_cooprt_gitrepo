from __future__ import annotations

import unittest
from datetime import date, datetime

from q2_baseline.forecast import COLD_START_SOURCE, RECENT_SOURCE, RecentCompletedSameClockPredictor

from tests.helpers_q2 import synthetic_data


class Q2ForecastCausalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = synthetic_data(date(2025, 1, 1), date(2025, 1, 31))
        cls.predictor = RecentCompletedSameClockPredictor(cls.data, "toy-v1")

    def test_locked_cold_start_boundaries(self) -> None:
        jan1 = self.predictor.forecast_day(date(2025, 1, 1))
        jan2 = self.predictor.forecast_day(date(2025, 1, 2))
        jan3 = self.predictor.forecast_day(date(2025, 1, 3))
        self.assertEqual(int(jan1.cold_mask.sum()), 144)
        self.assertEqual(int(jan2.cold_mask.sum()), 1)
        self.assertTrue(jan2.rows[-1].is_cold_start)
        self.assertTrue(all(row.forecast_source == RECENT_SOURCE for row in jan2.rows[:-1]))
        self.assertEqual(int(jan3.cold_mask.sum()), 0)

    def test_feb1_excludes_jan31_slot144(self) -> None:
        forecast = self.predictor.forecast_day(date(2025, 2, 1))
        slot144 = forecast.rows[-1]
        forbidden = self.data.actual_by_template_key[(date(2025, 1, 31), 144)]
        self.assertEqual(forbidden.interval_start, datetime(2025, 2, 1, 0, 0))
        self.assertEqual(forbidden.interval_end, datetime(2025, 2, 1, 0, 10))
        self.assertGreater(forbidden.interval_end, slot144.decision_time)
        self.assertNotEqual(slot144.source_interval_end, forbidden.interval_end)
        self.assertLessEqual(slot144.source_interval_end, slot144.decision_time)

    def test_every_used_source_is_completed(self) -> None:
        for day in (date(2025, 1, 1), date(2025, 1, 2), date(2025, 2, 1)):
            forecast = self.predictor.forecast_day(day)
            for row in forecast.rows:
                if row.forecast_source != COLD_START_SOURCE:
                    self.assertLessEqual(row.source_interval_end, row.decision_time)


if __name__ == "__main__":
    unittest.main()

