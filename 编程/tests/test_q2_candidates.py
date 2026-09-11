from dataclasses import replace
from datetime import date, datetime, timedelta
import unittest

import numpy as np

from q2_baseline.candidate_forecast import CandidatePredictor
from q2_baseline.config import Q2Parameters
from q2_baseline.data import Q2InputData
from q2_baseline.forecast import RecentCompletedSameClockPredictor
from q2_baseline.planner import build_daily_milp, compute_b0_plan
from q2_baseline.replay import replay_r0
from q2_baseline.validation import validate_day
from tests.helpers_q2 import synthetic_data


class CandidateForecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = synthetic_data(date(2025, 1, 1), date(2025, 2, 15))

    def test_recent_without_buffer_reproduces_baseline(self):
        day = date(2025, 2, 1)
        old = RecentCompletedSameClockPredictor(self.data, "old").forecast_day(day)
        new = CandidatePredictor(self.data, "recent", False).forecast_day(day)
        np.testing.assert_array_equal(old.load_pred_kw, new.load_pred_kw)
        np.testing.assert_array_equal(old.pv_pred_kw, new.pv_pred_kw)
        np.testing.assert_array_equal(old.load_pred_kw, new.planning_load_kw)

    def test_weekday_uses_target_natural_day_including_slot144(self):
        forecast = CandidatePredictor(self.data, "weekday", False).forecast_day(date(2025, 2, 1))
        for row in forecast.rows:
            self.assertEqual(row.load_source_interval_start, row.interval_start - timedelta(days=7))
            self.assertLessEqual(row.load_source_interval_end, row.decision_time)
        self.assertEqual(forecast.rows[-1].load_source_interval_start, datetime(2025, 1, 26))

    def test_future_actual_changes_do_not_change_forecast_or_buffer(self):
        cutoff = datetime(2025, 2, 1)
        changed = tuple(replace(row, load_kw=1e9, pv_kw=9e8) if row.interval_end > cutoff else row for row in self.data.actual)
        clocks = {minute: tuple(row for row in changed if row.natural_clock_minute == minute) for minute in self.data.actual_by_clock}
        perturbed = Q2InputData(self.data.price, changed, {}, clocks)
        for strategy in ("recent", "weekday"):
            old = CandidatePredictor(self.data, strategy, True).forecast_day(cutoff.date())
            new = CandidatePredictor(perturbed, strategy, True).forecast_day(cutoff.date())
            self.assertEqual(old, new)
            self.assertGreater(old.rows[0].buffer_sample_count, 0)

    def test_cold_start_still_has_zero_buffer_and_commitment(self):
        predictor = CandidatePredictor(self.data, "weekday", True)
        self.assertEqual(sum(predictor.forecast_day(date(2025, 1, 1)).cold_mask), 144)
        jan2 = predictor.forecast_day(date(2025, 1, 2))
        self.assertEqual(sum(jan2.cold_mask), 1)
        self.assertEqual(jan2.rows[-1].risk_buffer_kw, 0)

    def test_buffer_uses_historical_forecast_errors_and_keeps_point_prediction(self):
        forecast = CandidatePredictor(self.data, "recent", True).forecast_day(date(2025, 2, 1))
        plain = CandidatePredictor(self.data, "recent", False).forecast_day(date(2025, 2, 1))
        np.testing.assert_array_equal(forecast.load_pred_kw, plain.load_pred_kw)
        self.assertAlmostEqual(forecast.rows[0].risk_buffer_kw, 900.0)
        self.assertAlmostEqual(forecast.rows[-1].risk_buffer_kw, 1800.0)
        self.assertEqual(forecast.rows[0].buffer_sample_count, 28)
        params = Q2Parameters()
        plan = compute_b0_plan(forecast, self.data.price, params, 6000)
        self.assertAlmostEqual(plan.G[0], (plain.load_pred_kw[0] - plain.pv_pred_kw[0] + 900) / 6)
        problem = build_daily_milp(forecast, self.data.price, params, 6000)
        self.assertAlmostEqual(problem.row_lower[0], plan.G[0])

    def test_future_buffer_metadata_is_rejected(self):
        forecast = CandidatePredictor(self.data, "recent", True).forecast_day(date(2025, 2, 1))
        bad = replace(forecast.rows[0], buffer_source_end=datetime(2025, 2, 2))
        with self.assertRaises(AssertionError):
            replace(forecast, rows=(bad,) + forecast.rows[1:]).assert_causal()

    def test_buffered_plan_validates_and_replays_original_actuals(self):
        day = date(2025, 2, 1)
        forecast = CandidatePredictor(self.data, "recent", True).forecast_day(day)
        params = Q2Parameters()
        plan = compute_b0_plan(forecast, self.data.price, params, 6000)
        actual = tuple(self.data.actual_by_template_key[day, slot] for slot in range(1, 145))
        replay = replay_r0(plan, actual, self.data.price, params)
        passed, assertions, metrics = validate_day(forecast, plan, replay, self.data.price, params, 6000, False)
        self.assertTrue(passed, assertions)
        self.assertLess(metrics["emergency_kwh"], 1e-6)
        self.assertGreater(metrics["max_forecast_load_abs_error_kw"], 0)

    def test_insufficient_residual_history_falls_back_to_zero_margin(self):
        forecast = CandidatePredictor(self.data, "recent", True).forecast_day(date(2025, 1, 4))
        self.assertTrue(all(row.risk_buffer_kw == 0 for row in forecast.rows))
        self.assertTrue(all(row.buffer_sample_count < 7 for row in forecast.rows))


if __name__ == "__main__":
    unittest.main()
