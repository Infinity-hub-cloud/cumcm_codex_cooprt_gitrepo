from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from q1_baseline.baseline import compute_b0
from q1_baseline.export_templates import export_result1_candidate
from q1_baseline.export_validation import validate_result1_candidate
from q1_baseline.parameters import Q1Parameters
from q1_baseline.time_index import build_official_q1_intervals

from tests.helpers import toy_data


def make_toy_template(path: Path) -> None:
    workbook = Workbook()
    plan = workbook.active
    plan.title = "计划购电量"
    plan.append(["时段", "计划购电量"])
    for item in build_official_q1_intervals():
        plan.append([item.official_template_label, None])
    storage = workbook.create_sheet("充放电量")
    storage.append(["时段", "充电量", "放电量", "备注", "SOC"])
    for label in (
        "0:00-4:00",
        "4:00-8:00",
        "8:00-12:00",
        "12:00-16:00",
        "16:00-20:00",
        "20:00-24:00",
    ):
        storage.append([label, None, None, None, None])
    workbook.save(path)
    workbook.close()


class ExportRoundtripTests(unittest.TestCase):
    def test_toy_candidate_is_separate_and_rereads_cleanly(self) -> None:
        params = Q1Parameters()
        solution = compute_b0(toy_data(params), params)
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            official = base / "toy_official.xlsx"
            candidate = base / "result1_candidate.xlsx"
            make_toy_template(official)
            before = official.read_bytes()
            export_result1_candidate(official, candidate, solution, params)
            report = validate_result1_candidate(official, candidate, solution, params)
            self.assertTrue(report["passed"])
            self.assertEqual(official.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

