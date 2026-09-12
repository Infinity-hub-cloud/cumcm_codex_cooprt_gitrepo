from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from q3_baseline.cli import main


class Q3CliFailureEvidenceTests(unittest.TestCase):
    def test_existing_output_is_not_overwritten_by_launch_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "existing_run"
            output.mkdir()
            sentinel = output / "run_manifest.json"
            sentinel.write_text("keep", encoding="utf-8")
            argv = [
                "--config",
                "config/q3_baseline.json",
                "run",
                "--track",
                "Q3_ROLLING_INTERP",
                "--output-dir",
                str(output),
            ]
            with patch("q3_baseline.cli.run_q3_track", side_effect=FileExistsError("duplicate")):
                with self.assertRaises(FileExistsError):
                    main(argv)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            evidence = list(root.glob("existing_run_launch_failure_*"))
            self.assertEqual(len(evidence), 1)
            self.assertTrue((evidence[0] / "run_manifest.failure.json").is_file())


if __name__ == "__main__":
    unittest.main()
