from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

from q3_baseline.cli import _component_savings, _metrics, _revised_decomposition
from q3_baseline.config import TRACKS, load_config
from q3_baseline.runner import value_decomposition


class Q3TracksAndConfigTests(unittest.TestCase):
    def test_required_revised_tracks_exist(self):
        self.assertEqual(
            TRACKS,
            ("REF_Q2_FROZEN", "Q3_A3_0ONLY_ZOH", "Q3_A3_0ONLY_INTERP", "Q3_ROLLING_ZOH", "Q3_ROLLING_INTERP", "Q3_NOSTORAGE", "Q3_COST_A_SENSITIVITY"),
        )

    def test_issue_set_ablation_interface(self):
        config = load_config(Path("config/q3_baseline.json"))
        self.assertEqual(config.issue_sets["0only"], (0,))
        self.assertEqual(config.issue_sets["0_12"], (0, 720))
        self.assertEqual(config.issue_sets["rolling4"], (0, 360, 720, 1080))
        self.assertEqual(config.q2_frozen_model_version, "M2-Q2-EXPERIMENT-weekday_buffer-v1.0")
        self.assertFalse(config.parameters.solver_console_output)
        self.assertEqual(config.parameters.cost_semantics, "MODEL_B")

    def test_value_decomposition(self):
        result = value_decomposition(100.0, 90.0, 80.0)
        self.assertEqual(result["Value_A3_initial"], 10.0)
        self.assertEqual(result["Value_intraday_update"], 10.0)
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

    def test_revised_comparison_requires_same_identity(self):
        import json
        from argparse import Namespace
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);ref=root/"ref.csv"
            ref.write_text("model_id,baseline_id,split,period,metric,value\nM2-Q2-EXPERIMENT-weekday_buffer-v1.0,B1_WEEKDAY_BUFFER_MILP_R0,formal_output,formal_output,total_cost_yuan,100\n",encoding="utf-8")
            tracks={"initial_zoh":"Q3_A3_0ONLY_ZOH","initial_interp":"Q3_A3_0ONLY_INTERP","rolling_zoh":"Q3_ROLLING_ZOH","rolling_interp":"Q3_ROLLING_INTERP","no_storage":"Q3_NOSTORAGE","cost_a":"Q3_COST_A_SENSITIVITY"}
            costs={name:90-i for i,name in enumerate(tracks)}
            values={}
            for name,track in tracks.items():
                arm=root/name;arm.mkdir();values[f"{name}_run"]=str(arm)
                manifest={"track":track,"model_version":"v","data_version":"d","formal_output_start":"2025-02-01","formal_output_end":"2025-12-31","cost_semantics":"MODEL_A" if name=="cost_a" else "MODEL_B","code_identity":{"core_python_sha256":{"x":"h"}}}
                (arm/"run_manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
                (arm/"metrics_summary.csv").write_text(f"metric,value\ntotal_cost,{costs[name]}\n",encoding="utf-8")
            result=_revised_decomposition(Namespace(reference_metrics=str(ref),issue_frequency_run=None,**values))
            self.assertEqual(result["identity_gate"],"PASS")
            self.assertIn("Value_interpolation",result)


if __name__ == "__main__":
    unittest.main()
