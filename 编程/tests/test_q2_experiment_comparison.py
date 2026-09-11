import unittest

from q2_baseline.experiments import compare_costs


class ExperimentComparisonTests(unittest.TestCase):
    def test_comparison_keeps_same_strategy_and_original_baselines_distinct(self):
        runs = {}
        for experiment, costs in (("baseline", (100.0, 90.0)), ("weekday", (60.0, 50.0))):
            runs[experiment] = [
                {"period": "formal_output", "baseline": track,
                 "template_date": "2025-02-01", "total_cost_yuan": cost,
                 "planned_purchase_cost_yuan": cost * 0.6,
                 "emergency_purchase_cost_yuan": cost * 0.4,
                 "emergency_kwh": cost / 5, "surplus_kwh": 1.0,
                 "charge_kwh": 2.0, "discharge_kwh": 1.62,
                 "planned_grid_kwh": cost,
                 "soc_start_0010_kwh": 6000.0,
                 "soc_end_0010_next_day_kwh": 1200.0}
                for track, cost in zip(("B0_NO_STORAGE_REFERENCE", "B1_TEST"), costs)
            ]
        totals, months, days = compare_costs(runs)
        candidate = next(row for row in totals if row["experiment"] == "weekday" and row["track"] == "B1")
        self.assertEqual(candidate["saving_vs_original_b1_yuan"], 40)
        self.assertEqual(candidate["saving_vs_matched_b0_yuan"], 10)
        self.assertEqual(candidate["saving_vs_original_b0_yuan"], 50)
        self.assertEqual(candidate["improved_days_vs_original_b1"], 1)
        self.assertEqual(candidate["improved_months_vs_original_b1"], 1)
        self.assertEqual(len(months), 4)
        self.assertEqual(len(days), 4)

    def test_comparison_rejects_different_calendar_coverage(self):
        with self.assertRaises(ValueError):
            compare_costs({"baseline": [], "weekday": []})


if __name__ == "__main__":
    unittest.main()
