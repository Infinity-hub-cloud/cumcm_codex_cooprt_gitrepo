from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from q2_baseline.evidence import flush_failure_evidence


class Q2FailureEvidenceTests(unittest.TestCase):
    def test_failure_keeps_completed_and_failed_day_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            (destination / "warnings_and_failures.log").write_text("warning\n", encoding="utf-8")
            (destination / "solver.log").write_text("solver evidence\n", encoding="utf-8")
            solver_rows = [{
                "template_date": "2025-01-01", "period": "warmup",
                "status": "COLD_START_NO_SOLVE", "solver_name": "NONE",
                "solver_version": "N/A", "termination_condition": "cold",
                "mip_gap": "", "runtime_seconds": 0.0,
            }]
            manifest = {
                "run_id": "toy", "run_status": "HUMAN_RUN_UNREVIEWED",
                "solver_name": "highs", "solver_version": "PENDING_HUMAN_RUN",
                "warnings_count": 1, "failures_count": 0,
            }
            error = RuntimeError("toy infeasible")
            flush_failure_evidence(
                destination, manifest, solver_rows, [],
                last_completed_template_date=date(2025, 1, 1),
                failed_template_date=date(2025, 1, 2), error=error,
            )
            saved = json.loads((destination / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["run_status"], "FAILED_OR_INCOMPLETE")
            self.assertGreaterEqual(saved["failures_count"], 1)
            self.assertEqual(saved["last_completed_template_date"], "2025-01-01")
            self.assertEqual(saved["failed_template_date"], "2025-01-02")
            with (destination / "solver_days.csv").open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["template_date"] for row in rows], ["2025-01-01", "2025-01-02"])
            self.assertEqual(rows[-1]["status"], "FAILED_OR_INCOMPLETE")
            self.assertIn("toy infeasible", (destination / "warnings_and_failures.log").read_text(encoding="utf-8"))
            self.assertTrue((destination / "solver.log").is_file())


if __name__ == "__main__":
    unittest.main()

