from __future__ import annotations

import math
import unittest
from datetime import datetime, timedelta

from q2_baseline.prediction_metrics import PredictionObservation, evaluate_prediction_observations


class Q2PredictionMetricsTests(unittest.TestCase):
    def test_locked_metrics_and_no_cross_natural_day_ramp(self) -> None:
        starts = [
            datetime(2025, 2, 1, 0, 0), datetime(2025, 2, 1, 0, 10),
            datetime(2025, 2, 2, 0, 0), datetime(2025, 2, 2, 0, 10),
        ]
        load_actual = [10.0, 20.0, 30.0, 40.0]
        load_pred = [12.0, 18.0, 33.0, 36.0]
        pv_actual = [0.0, 1.0, 3.0, 0.0]
        pv_pred = [0.0, 2.0, 2.0, 1.0]
        observations = tuple(
            PredictionObservation(start, start + timedelta(minutes=10), la, lp, pa, pp)
            for start, la, lp, pa, pp in zip(starts, load_actual, load_pred, pv_actual, pv_pred)
        )
        rows = evaluate_prediction_observations(observations)
        overall = {
            (row["series"], row["metric"]): row
            for row in rows
            if row["scope"] == "overall"
        }
        self.assertAlmostEqual(overall[("load", "MAE")]["value"], 2.75)
        self.assertAlmostEqual(overall[("load", "RMSE")]["value"], math.sqrt(33.0 / 4.0))
        self.assertAlmostEqual(overall[("load", "nMAE")]["value"], 2.75 / 25.0)
        self.assertAlmostEqual(overall[("load", "bias")]["value"], -0.25)
        self.assertEqual(overall[("load", "peak_sample_count")]["value"], 1.0)
        self.assertEqual(overall[("load", "peak_MAE")]["value"], 4.0)
        self.assertEqual(overall[("pv", "daylight_MAE")]["value"], 1.0)
        self.assertEqual(overall[("pv", "daylight_RMSE")]["value"], 1.0)
        self.assertEqual(overall[("pv", "daylight_sample_count")]["value"], 2.0)
        self.assertAlmostEqual(overall[("pv", "ramp_MAE")]["value"], 1.5)
        self.assertEqual(overall[("pv", "ramp_sample_count")]["value"], 2.0)
        self.assertTrue(all(row["posthoc_evaluation_only"] for row in rows))
        self.assertTrue(any(row["scope"] == "month" for row in rows))
        self.assertTrue(any(row["scope"] == "season" for row in rows))


if __name__ == "__main__":
    unittest.main()

