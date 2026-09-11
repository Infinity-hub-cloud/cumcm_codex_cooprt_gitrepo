from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from q1_baseline.run_manifest import sha256_file
from q2_baseline.config import load_config
from q2_baseline.integrity import InputHashMismatchError, assert_file_sha256
from q2_baseline.runner import validate_input_only


PROGRAMMING_ROOT = Path(__file__).resolve().parents[1]
FORMAL_CONFIG = PROGRAMMING_ROOT / "config" / "q2_baseline.json"


class Q2InputHashGateTests(unittest.TestCase):
    def test_hash_error_contains_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            path.write_bytes(b"original")
            expected = sha256_file(path)
            path.write_bytes(b"originalX")
            with self.assertRaises(InputHashMismatchError) as caught:
                assert_file_sha256(path, expected)
            self.assertEqual(caught.exception.file, str(path))
            self.assertEqual(caught.exception.expected_sha256, expected)
            self.assertEqual(caught.exception.actual_sha256, sha256_file(path))

    def test_validate_input_rejects_one_byte_modified_temporary_actual(self) -> None:
        formal = load_config(FORMAL_CONFIG)
        payload = json.loads(FORMAL_CONFIG.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            altered = root / "attachment2_actual_long.csv"
            shutil.copyfile(formal.normalized_actual_input, altered)
            with altered.open("ab") as handle:
                handle.write(b"X")
            payload["normalized_price_input"] = str(formal.normalized_price_input)
            payload["normalized_actual_input"] = str(altered)
            payload["official_result2_template"] = str(formal.official_result2_template)
            payload["audit_manifest"] = str(formal.audit_manifest)
            payload["audit_summary"] = str(formal.audit_summary)
            config_path = root / "q2_modified_input.json"
            config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(InputHashMismatchError) as caught:
                validate_input_only(config_path)
            self.assertEqual(caught.exception.file, str(altered))
            self.assertIn("expected_sha256", str(caught.exception))
            self.assertIn("actual_sha256", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

