from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

from q3_baseline.cli import _component_savings, _metrics
from q3_baseline.config import TRACKS, load_config
from q3_baseline.runner import value_decomposition


class Q3TracksAndConfigTests(unittest.TestCase):
    def test_four_required_tracks_exist(self):
        self.assertEqual(
            TRACKS,
            ("REF_Q2_FROZEN", "Q3_ATTACHMENT3_0ONLY", "Q3_ROLLING_4ISSUE", "Q3_NOSTORAGE_REFERENCE"),
        )

    def test_issue_set_ablation_interface(self):
        config = load_config(Path("config/q3_baseline.json"))
        self.assertEqual(config.issue_sets["0only"], (0,))
        self.assertEqual(config.issue_sets["0_12"], (0, 720))
        self.assertEqual(config.issue_sets["rolling4"], (0, 360, 720, 1080))
        self.assertEqual(config.q2_frozen_model_version, "M2-Q2-EXPERIMENT-weekday_buffer-v1.0")
        self.assertFalse(config.parameters.solver_console_output)

    def test_value_decomposition(self):
        result = value_decomposition(100.0, 90.0, 80.0)
        self.assertEqual(result["Value_Attachment3_Initial"], 10.0)
        self.assertEqual(result["Value_Intraday_Rolling"], 10.0)
        self.assertEqual(result["Total_Q3_Improvement"], 20.0)

    def test_q2_reference_metric_selector_uses_frozen_b1_not_first_b0(self):
        text = (
            "model_id,baseline_id,split,period,metric,value\n"
            "B0,B0_NO_STORAGE_REFERENCE,formal_output,formal_output,total_cost_yuan,999\n"
            "M2-Q2-EXPERIMENT-weekday_buffer-v1.0,B1_WEEKDAY_BUFFER_MILP_R0,formal_output,formal_output,total_cost_yuan,100\n"
            "M2-Q2-EXPERIMENT-weekday_buffer-v1.0,B1_WEEKDAY_BUFFER_MILP_R0,formal_output,formal_output,planned_purchase_cost_yuan,80\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metrics.csv"
            path.write_text(text, encoding="utf-8")
            selected = _metrics(str(path), q2_frozen_reference=True)
        self.assertEqual(selected["total_cost"], 100.0)
        self.assertEqual(selected["planned_purchase_cost"], 80.0)

    def test_component_savings_includes_required_decomposition(self):
        result = _component_savings(
            {"total_cost": 10.0, "downward_penalty": 1.0, "total_charge": 4.0},
            {"total_cost": 7.0, "downward_penalty": 0.5, "total_charge": 3.0},
        )
        self.assertEqual(result["total_cost"], 3.0)
        self.assertEqual(result["adjustment_cost"], 0.5)
        self.assertEqual(result["storage_throughput"], 1.0)


if __name__ == "__main__":
    unittest.main()
