from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from q1_baseline.run_manifest import sha256_file
from q2_baseline.integrity import InputHashMismatchError, assert_file_sha256

from .config import Q3Config


LOCKED_DATA_VERSION = "PREP-TIME-REV-20260911T170805+0800"
LOCKED_AUDIT_GENERATED_AT = "2026-09-11T17:08:05+08:00"
LOCKED_SHA256 = {
    "attachment1_single_day.csv": "695E14DD02D011E24AE8CE1C5CD7BFF4CA963F5C92FA884BACC0386059AD07E3",
    "attachment2_actual_long.csv": "00DA155528AFC173776F59E620C8AEFCD661A5C5D8520472CE3AA9F0A91631ED",
    "attachment3_forecast_long.csv": "B9F67A02CC979DDE70E9045E7B18A32DC9B1FBCC002C23AEB04DAAA697452328",
    "attachment3_mapped_10min.csv": "5830C5F598039F765CDDA4C70E8B14FE152AC7C7D3BDDA031737A98CAB5D8DFD",
    "result3.xlsx": "C59DA470CABD0BE23F602C95C8AA9D11EC224A0CDAC216B3E1F218E65D006BDC",
}


def verify_input_integrity(config: Q3Config) -> dict[str, Any]:
    """Hard gate before any formal data load, forecast, model build, or solve."""
    if config.data_version != LOCKED_DATA_VERSION:
        raise RuntimeError("Q3 DATA_VERSION_MISMATCH")
    summary = json.loads(config.audit_summary.read_text(encoding="utf-8"))
    manifest = json.loads(config.audit_manifest.read_text(encoding="utf-8"))
    if summary.get("status") != "PASS" or summary.get("generated_at") != LOCKED_AUDIT_GENERATED_AT:
        raise RuntimeError("Q3 formal audit summary identity mismatch")
    result3_rows = [
        row for row in manifest
        if str(row.get("relative_path", "")).replace("/", "\\").endswith("附件5\\result3.xlsx")
    ]
    if len(result3_rows) != 1 or result3_rows[0].get("sha256") != LOCKED_SHA256["result3.xlsx"]:
        raise RuntimeError("AUDIT_MANIFEST_RESULT3_HASH_MISMATCH")
    verified = {
        "price": assert_file_sha256(config.normalized_price_input, LOCKED_SHA256["attachment1_single_day.csv"]),
        "actual": assert_file_sha256(config.normalized_actual_input, LOCKED_SHA256["attachment2_actual_long.csv"]),
        "attachment3_long": assert_file_sha256(config.attachment3_forecast_input, LOCKED_SHA256["attachment3_forecast_long.csv"]),
        "attachment3_mapped": assert_file_sha256(config.attachment3_mapped_input, LOCKED_SHA256["attachment3_mapped_10min.csv"]),
        "official_result3": assert_file_sha256(config.official_result3_template, LOCKED_SHA256["result3.xlsx"]),
    }
    q2_manifest = config.q2_reference_run / "run_manifest.json"
    q2_payload = json.loads(q2_manifest.read_text(encoding="utf-8"))
    if q2_payload.get("model_version") != config.q2_frozen_model_version:
        raise RuntimeError("Q2_FROZEN_REFERENCE_MODEL_MISMATCH")
    if q2_payload.get("experiment") != "weekday_buffer" or not q2_payload.get("assertions_passed"):
        raise RuntimeError("Q2_FROZEN_REFERENCE_NOT_ACCEPTABLE")
    return {
        "data_version": config.data_version,
        "verified_input_sha256": verified,
        "input_manifest_sha256": sha256_file(config.audit_manifest),
        "audit_summary_sha256": sha256_file(config.audit_summary),
        "audit_status": "PASS",
        "q2_reference_manifest_sha256": sha256_file(q2_manifest),
        "warning": "WARNING-Q3-MANIFEST-NORMALIZED-001: normalized CSV hashes are locked from the formal handoff because audit/manifest.json lists raw inputs only",
    }


__all__ = ["InputHashMismatchError", "LOCKED_SHA256", "verify_input_integrity"]
