from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from q1_baseline.run_manifest import sha256_file

from .config import Q2Config


LOCKED_DATA_VERSION = "PREP-TIME-REV-20260911T170805+0800"
LOCKED_AUDIT_GENERATED_AT = "2026-09-11T17:08:05+08:00"
LOCKED_INPUT_SHA256 = {
    "attachment1_single_day.csv": "695E14DD02D011E24AE8CE1C5CD7BFF4CA963F5C92FA884BACC0386059AD07E3",
    "attachment2_actual_long.csv": "00DA155528AFC173776F59E620C8AEFCD661A5C5D8520472CE3AA9F0A91631ED",
    "official result2.xlsx": "1C26494CFC6D754E0BD9BFF7E13E1126A73D2D2DA6C5336EB251D89B9A1A1A47",
}


@dataclass(frozen=True)
class InputHashMismatchError(RuntimeError):
    file: str
    expected_sha256: str
    actual_sha256: str

    def __str__(self) -> str:
        return json.dumps(
            {
                "error": "INPUT_SHA256_MISMATCH",
                "file": self.file,
                "expected_sha256": self.expected_sha256,
                "actual_sha256": self.actual_sha256,
            },
            ensure_ascii=False,
        )


def assert_file_sha256(path: Path, expected_sha256: str) -> str:
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise InputHashMismatchError(str(path), expected_sha256, actual)
    return actual


def verify_input_integrity(config: Q2Config) -> dict[str, Any]:
    """Hard gate executed before any data read, forecast, model build, or solve."""
    if config.data_version != LOCKED_DATA_VERSION:
        raise RuntimeError(
            f"DATA_VERSION_MISMATCH: expected={LOCKED_DATA_VERSION}, actual={config.data_version}"
        )
    verified = {
        "price": assert_file_sha256(
            config.normalized_price_input,
            LOCKED_INPUT_SHA256["attachment1_single_day.csv"],
        ),
        "actual": assert_file_sha256(
            config.normalized_actual_input,
            LOCKED_INPUT_SHA256["attachment2_actual_long.csv"],
        ),
        "official_result2": assert_file_sha256(
            config.official_result2_template,
            LOCKED_INPUT_SHA256["official result2.xlsx"],
        ),
    }

    audit_manifest_hash = sha256_file(config.audit_manifest)
    audit_summary_hash = sha256_file(config.audit_summary)
    manifest_payload = json.loads(config.audit_manifest.read_text(encoding="utf-8"))
    summary_payload = json.loads(config.audit_summary.read_text(encoding="utf-8"))
    if summary_payload.get("status") != "PASS":
        raise RuntimeError(f"AUDIT_SUMMARY_NOT_PASS: {config.audit_summary}")
    if summary_payload.get("generated_at") != LOCKED_AUDIT_GENERATED_AT:
        raise RuntimeError(
            "AUDIT_VERSION_MISMATCH: "
            f"expected_generated_at={LOCKED_AUDIT_GENERATED_AT}, "
            f"actual={summary_payload.get('generated_at')}"
        )
    result2_rows = [
        row for row in manifest_payload
        if str(row.get("relative_path", "")).replace("/", "\\").endswith("附件5\\result2.xlsx")
    ]
    if len(result2_rows) != 1 or result2_rows[0].get("sha256") != LOCKED_INPUT_SHA256["official result2.xlsx"]:
        raise RuntimeError("AUDIT_MANIFEST_RESULT2_HASH_MISMATCH")
    return {
        "data_version": config.data_version,
        "verified_input_sha256": verified,
        "input_manifest_sha256": audit_manifest_hash,
        "audit_summary_sha256": audit_summary_hash,
        "audit_status": "PASS",
        "audit_generated_at": LOCKED_AUDIT_GENERATED_AT,
    }

