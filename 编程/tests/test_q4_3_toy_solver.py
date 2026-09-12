from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

from q1_baseline.solver_backend import HighsPyBackend
from q3_baseline.config import Q3Parameters
from q3_baseline.forecast import PVSelection
from q4_3_baseline.exporter import toy_export_roundtrip
from q4_3_baseline.planner import build_adjustment_milp


def pv(slot: int, start: datetime) -> PVSelection:
    return PVSelection(date(2025,2,1), slot, start, start+timedelta(minutes=10), start, None, None, None,
        0.0, 0.0, "fallback_q2_pv", "toy", "Q2_FALLBACK", None, None, False, "toy_fallback")


class ToySolverAndExport(unittest.TestCase):
    def test_toy_model_b_solver(self):
        if not HighsPyBackend.available(): self.skipTest("REQUIRES_HUMAN_RUN: highspy unavailable")
        params=Q3Parameters(solver_console_output=False, cost_semantics="MODEL_B")
        start=datetime(2025,2,1,0,10)
        problem=build_adjustment_milp(np.array([10.,10.]),np.array([60.,60.]),(pv(1,start),pv(2,start+timedelta(minutes=10))),np.array([1.,2.]),6000.,params)
        with tempfile.TemporaryDirectory() as folder:
            result=HighsPyBackend().solve(problem,params,Path(folder)/"toy_highs.log")
        self.assertEqual(result.status,"OPTIMAL")
        self.assertEqual(result.vector.shape,(problem.num_col,))
        self.assertLessEqual(float(np.max(result.vector[problem.layout.C])),5000/6+params.feasibility_tolerance)

    def test_toy_candidate_export_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            result=toy_export_roundtrip(Path(folder)/"toy_result4-3.xlsx")
        self.assertTrue(result["passed"])


if __name__ == "__main__": unittest.main()
