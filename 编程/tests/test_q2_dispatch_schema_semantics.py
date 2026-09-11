from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from q2_baseline.config import Q2Config, Q2Parameters
from q2_baseline.runner import DISPATCH_FIELDS, _dispatch_rows

from tests.helpers_q2 import normal_forecast, synthetic_data, zero_replay


class Q2DispatchSchemaTests(unittest.TestCase):
    def test_q2_non_applicable_common_fields_are_blank(self) -> None:
        day = date(2025, 2, 1)
        config = Q2Config(
            model_version="toy", forecast_version="toy", data_version="toy",
            normalized_price_input=Path("price"), normalized_actual_input=Path("actual"),
            official_result2_template=Path("result2"), audit_manifest=Path("manifest"),
            audit_summary=Path("summary"), solver_name="none",
            warmup_start=date(2025, 1, 1), output_start=day,
            output_end=date(2025, 12, 31), parameters=Q2Parameters(),
        )
        data = synthetic_data(day, day)
        forecast = normal_forecast(day)
        replay = zero_replay(day, {0: 2.0})
        row = next(iter(_dispatch_rows(config, data, {day: forecast}, [replay])))
        self.assertEqual(row["price_actual"], 1.0)
        self.assertEqual(row["price_pred"], "")
        self.assertEqual(row["grid_plan_kwh"], 0.0)
        self.assertEqual(row["grid_final_kwh"], "")
        self.assertEqual(row["grid_emergency_kwh"], 2.0)
        for name in (
            "adjust_down_kwh", "adjust_up_kwh",
            "downward_adjustment_penalty", "upward_adjustment_cost",
        ):
            self.assertEqual(row[name], "")
        self.assertEqual(list(row), DISPATCH_FIELDS)


if __name__ == "__main__":
    unittest.main()

