from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from q3_baseline.metrics import economic_metrics, evaluate_pv_predictions, soc_boundary_hits
from q3_baseline.state_machine import ExecutedInterval


class Q3MetricsTests(unittest.TestCase):
    def test_required_pv_metrics(self):
        issue = datetime(2025, 2, 1, 6)
        rows = [
            {"issue_datetime": issue, "interval_start": issue + timedelta(minutes=10*i), "actual_kw": float(i), "predicted_kw": float(i + 1)}
            for i in range(3)
        ]
        output = evaluate_pv_predictions(rows)
        all_months = next(row for row in output if row["month"] == "ALL")
        for key in ("mae_kw", "rmse_kw", "bias_kw", "daylight_mae_kw", "ramp_mae_kw", "p50_abs_error_kw", "p90_abs_error_kw", "p95_abs_error_kw", "p99_abs_error_kw"):
            self.assertIn(key, all_months)
        self.assertEqual(all_months["issue_time"], "06:00")

    def test_required_economic_and_energy_metrics(self):
        row = ExecutedInterval(
            template_date="2025-02-01",
            template_slot=1,
            interval_start=datetime(2025, 2, 1, 0, 10),
            interval_end=datetime(2025, 2, 1, 0, 20),
            G=2.0,
            Q=3.0,
            C=0.0,
            D=1.0,
            E=0.5,
            W=0.25,
            soc_before=6000.0,
            soc_after=5998.8,
            price=1.0,
            pv_forecast_source="attachment3",
            issue_datetime=datetime(2025, 2, 1, 0, 0),
            load_actual_kwh=1.0,
            pv_actual_kwh=2.0,
            planned_purchase_cost=1.0,
            fulfilled_normal_purchase_cost=1.0,
            cancelled_purchase_principal=0.0,
            downward_adjustment_penalty=0.0,
            upward_adjustment_cost=0.2,
            regular_purchase_cost=1.2,
            emergency_purchase_cost=0.3,
            total_cost=1.5,
            cost_semantics="MODEL_B",
        )
        metrics = economic_metrics([row])
        self.assertEqual(metrics["planned_grid_energy"], 2.0)
        self.assertEqual(metrics["final_grid_energy"], 3.0)
        self.assertEqual(metrics["soc_min"], 5998.8)
        self.assertEqual(metrics["soc_max"], 6000.0)

    def test_soc_boundary_hits_uses_explicit_feasibility_tolerance(self):
        row = ExecutedInterval(
            template_date="2025-02-01",
            template_slot=1,
            interval_start=datetime(2025, 2, 1, 0, 10),
            interval_end=datetime(2025, 2, 1, 0, 20),
            G=0.0,
            Q=0.0,
            C=0.0,
            D=0.0,
            E=0.0,
            W=0.0,
            soc_before=1200.0000005,
            soc_after=10799.9999995,
            price=1.0,
            pv_forecast_source="attachment3",
            issue_datetime=datetime(2025, 2, 1),
            load_actual_kwh=0.0,
            pv_actual_kwh=0.0,
            planned_purchase_cost=0.0,
            fulfilled_normal_purchase_cost=0.0,
            cancelled_purchase_principal=0.0,
            downward_adjustment_penalty=0.0,
            upward_adjustment_cost=0.0,
            regular_purchase_cost=0.0,
            emergency_purchase_cost=0.0,
            total_cost=0.0,
            cost_semantics="MODEL_B",
        )
        self.assertEqual(soc_boundary_hits([row], 1200.0, 10800.0, 1e-6), 2.0)


if __name__ == "__main__":
    unittest.main()
