from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from q2_baseline.data import ActualInterval
from q2_baseline.planner import DailyPlan
from q4_baseline.config import Q4Parameters
from q4_baseline.metrics import value_decomposition
from q4_baseline.runner import aggregate_solver_metrics, structured_solver_audit, verify_compare_run_identity
from q4_baseline.settlement import replay_actual_price


class Q4ModelContracts(unittest.TestCase):
    def test_r0_uses_actual_attachment4_price(self):
        day = date(2025, 2, 1)
        start = datetime(2025, 2, 1, 0, 10)
        actual = tuple(ActualInterval(day, i + 1, start + timedelta(minutes=10 * i), start + timedelta(minutes=10 * (i + 1)), 12.0, 0.0, 2.0, 0.0) for i in range(144))
        zeros = np.zeros(144)
        grid = np.ones(144)
        plan = DailyPlan(day, "toy", grid, zeros.copy(), zeros.copy(), zeros.copy(), zeros.copy(), np.full(145, 6000.0), 0.0, "toy", "1", "OPTIMAL", "toy", 0.0, 0.0)
        prices = np.full(144, 2.0)
        replay = replay_actual_price(plan, actual, prices, Q4Parameters())
        self.assertAlmostEqual(replay.regular_cost[0], 2.0)
        self.assertAlmostEqual(replay.emergency_kwh[0], 1.0)
        self.assertAlmostEqual(replay.emergency_cost[0], 10.0)

    def test_value_decomposition_uses_resettlement_reference(self):
        values = value_decomposition({"REF_Q2_FIXED_PRICE_FROZEN": 100.0, "Q4_2_PRICE_UNAWARE_RESETTLEMENT": 120.0, "Q4_2_PRICE_CANDIDATE_P1": 90.0, "Q4_2_NOSTORAGE": 130.0}, "Q4_2_PRICE_CANDIDATE_P1")
        self.assertEqual(values["PriceSystemEffect"], 20.0)
        self.assertEqual(values["PriceAwarenessValue_selected"], 30.0)
        self.assertEqual(values["StorageValue_selected"], 40.0)

    def test_exact_qmax_is_not_rounded_display_value(self):
        params = Q4Parameters()
        self.assertAlmostEqual(params.charge_energy_max, 5000 / 6, places=12)
        self.assertNotEqual(params.charge_energy_max, 833.3333)

    def test_solver_summary_tracks_status_runtime_and_level_bounds(self):
        rows = [
            {"template_date": "2025-02-01", "status": "OPTIMAL", "runtime_seconds": 1.25, "level_bound_hit_count": 2},
            {"template_date": "2025-02-02", "status": "OPTIMAL_CLOSED_FORM", "runtime_seconds": 0.0, "level_bound_hit_count": 1},
        ]
        summary = aggregate_solver_metrics(rows)
        self.assertEqual(summary["optimal_count"], 2)
        self.assertEqual(summary["failure_count"], 0)
        self.assertAlmostEqual(summary["runtime_seconds"], 1.25)
        self.assertEqual(summary["level_bound_hit_count"], 3)
        audit = structured_solver_audit(rows)
        self.assertEqual(audit[0]["template_date"], "2025-02-01")
        self.assertEqual(audit[1]["level_bound_hit_count"], 1)

    def test_compare_rejects_cross_predictor_and_mixed_identity(self):
        tracks = {
            "REF_Q2_FIXED_PRICE_FROZEN", "Q4_2_PRICE_UNAWARE_RESETTLEMENT", "Q4_2_PRICE_BASELINE_P0",
            "Q4_2_PRICE_CANDIDATE_P1", "Q4_2_PRICE_CANDIDATE_P2", "Q4_2_PRICE_CANDIDATE_P3", "Q4_2_NOSTORAGE",
        }
        identity = {"config_sha256": "config", "q4_core_python_sha256": {"runner.py": "code"}}
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            costs = {}
            for index, track in enumerate(sorted(tracks), start=1):
                folder = root / track; folder.mkdir()
                manifest = {"track": track, "identity": identity, "input_sha256": {"actual": "a"}, "visibility_rule": "TIMESTAMP_LE_DECISION_VISIBLE", "formal_dates": ["2025-02-01", "2025-12-31"], "initial_soc_feb1": 1200.0, "predictor_id": "P2_EWMA", "metrics": {"realized_total_cost": float(index)}}
                if track == "REF_Q2_FIXED_PRICE_FROZEN":
                    manifest["reference_cost_yuan"] = float(index)
                (folder / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                costs[track] = float(index)
            verify_compare_run_identity(root, costs, "Q4_2_PRICE_CANDIDATE_P2")
            broken = root / "Q4_2_NOSTORAGE" / "run_manifest.json"
            manifest = json.loads(broken.read_text(encoding="utf-8")); manifest["predictor_id"] = "P1_WEEKDAY_SAME_CLOCK"
            broken.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "predictors differ"):
                verify_compare_run_identity(root, costs, "Q4_2_PRICE_CANDIDATE_P2")


if __name__ == "__main__":
    unittest.main()
