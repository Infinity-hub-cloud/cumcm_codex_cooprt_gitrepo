from __future__ import annotations

import unittest
import csv
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from q3_baseline.state_machine import CausalActualView
from q4_3_baseline.reference import read_frozen_q3_dispatch
from q4_3_baseline.runner import _write_csv
from q4_3_baseline.settlement import resettle_frozen_q3
from q4_3_baseline.rolling import assert_update_contract
from q4_3_baseline.settlement import model_b_regular_components, settle_final_adjustment_once


class ModelContracts(unittest.TestCase):
    def test_model_b_two_branches(self):
        down = model_b_regular_components(10, 6, 2)
        up = model_b_regular_components(10, 14, 2)
        self.assertEqual(down["regular_purchase_cost"], 16)
        self.assertEqual(up["regular_purchase_cost"], 32)

    def test_adjustment_settled_once_not_path(self):
        direct = settle_final_adjustment_once(10, 8, 2, 1)
        trajectory_a = [10, 14, 7, 8]
        trajectory_b = [10, 1, 20, 8]
        self.assertEqual(direct, settle_final_adjustment_once(10, trajectory_a[-1], 2, 1))
        self.assertEqual(direct, settle_final_adjustment_once(10, trajectory_b[-1], 2, 1))
        self.assertEqual(direct, 28)

    def test_g_and_executed_prefix_are_frozen_suffix_may_change(self):
        before = SimpleNamespace(G=np.arange(6.), Q=np.arange(6.), C=np.zeros(6), D=np.zeros(6))
        after = SimpleNamespace(G=before.G.copy(), Q=before.Q.copy(), C=before.C.copy(), D=before.D.copy())
        after.Q[3:] += 1; after.C[3:] += 2; after.D[3:] += 3
        assert_update_contract(before, after, 4, ("executed",), ("executed",))
        after.G[5] += 1
        with self.assertRaisesRegex(AssertionError, "G_FROZEN"):
            assert_update_contract(before, after, 4, (), ())

    def test_future_actual_load_pv_access_hard_fails(self):
        actual = SimpleNamespace(interval_end=datetime(2025,2,1,6,10))
        view = CausalActualView({(date(2025,2,1),36): actual})
        with self.assertRaisesRegex(PermissionError, "Q3_CAUSAL_ACTUAL_HARD_FAIL"):
            view.get((date(2025,2,1),36), datetime(2025,2,1,6))

    def test_future_actual_perturbation_does_not_change_snapshot(self):
        decision = datetime(2025,2,1,6)
        completed = SimpleNamespace(interval_start=decision-timedelta(minutes=10), interval_end=decision,
            natural_clock_minute=350, source_date=date(2025,2,1), template_slot=35, load_kwh=10.0, pv_kwh=2.0)
        future_a = SimpleNamespace(interval_start=decision, interval_end=decision+timedelta(minutes=10),
            natural_clock_minute=360, source_date=date(2025,2,1), template_slot=36, load_kwh=20.0, pv_kwh=3.0)
        future_b = SimpleNamespace(**{**future_a.__dict__, "load_kwh": 9999.0, "pv_kwh": 9999.0})
        left = CausalActualView({("past",1):completed,("future",1):future_a}).snapshot(decision,np.ones(144))
        right = CausalActualView({("past",1):completed,("future",1):future_b}).snapshot(decision,np.ones(144))
        self.assertEqual([(r.load_kwh,r.pv_kwh) for r in left.actual],[(r.load_kwh,r.pv_kwh) for r in right.actual])

    def test_price_unaware_resettlement_preserves_all_actions(self):
        row = read_frozen_q3_dispatch(__import__("pathlib").Path("runs/q3_revised_20260912_112347/Q3_ROLLING_INTERP"))[0]
        changed = resettle_frozen_q3(row, row.price * 1.7)
        self.assertEqual((row.G,row.Q,row.C,row.D,row.E,row.W,row.soc_before,row.soc_after),
                         (changed.G,changed.Q,changed.C,changed.D,changed.E,changed.W,changed.soc_before,changed.soc_after))

    def test_solver_update_csv_uses_union_schema(self):
        rows = [
            {"plan_version": "initial_0000", "objective": 1.0},
            {"plan_version": "update_0600", "objective": 2.0, "rows": 413, "columns": 613, "binary_count": 109},
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "solver_updates.csv"
            _write_csv(path, rows)
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                output = list(csv.DictReader(handle))
        self.assertEqual(output[1]["rows"], "413")
        self.assertEqual(output[1]["columns"], "613")
        self.assertEqual(output[1]["binary_count"], "109")


if __name__ == "__main__": unittest.main()
