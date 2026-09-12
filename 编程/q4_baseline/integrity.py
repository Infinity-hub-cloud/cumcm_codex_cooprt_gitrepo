from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .config import Q4Config, VISIBILITY_RULE


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def verify_q4_inputs(config: Q4Config) -> dict[str, Any]:
    config.validate()
    paths = {"attachment4": config.normalized_price_input, "actual": config.normalized_actual_input, "q2_reference_dispatch": config.q2_reference_run / "dispatch_timeseries.csv", "official_result4_2": config.official_result4_2_template}
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Q4 input files missing: {missing}")
    hashes = {name: sha256_file(path) for name, path in paths.items()}
    if hashes["attachment4"] != config.normalized_price_sha256.upper():
        raise RuntimeError("Q4_ATTACHMENT4_HASH_HARD_FAIL")
    if hashes["actual"] != config.normalized_actual_sha256.upper():
        raise RuntimeError("Q4_ACTUAL_INPUT_HASH_HARD_FAIL")
    if hashes["q2_reference_dispatch"] != config.q2_reference_dispatch_sha256.upper():
        raise RuntimeError("Q4_FROZEN_Q2_REFERENCE_HASH_HARD_FAIL")
    if hashes["official_result4_2"] != config.official_result4_2_sha256.upper():
        raise RuntimeError("Q4_RESULT4_2_TEMPLATE_HASH_HARD_FAIL")
    return {"passed": True, "visibility_rule": VISIBILITY_RULE, "sha256": hashes, "paths": {name: str(path) for name, path in paths.items()}}
