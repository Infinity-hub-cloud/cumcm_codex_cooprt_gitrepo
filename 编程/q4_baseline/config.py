from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from q2_baseline.config import Q2Parameters


VISIBILITY_RULE = "TIMESTAMP_LE_DECISION_VISIBLE"
PREDICTORS = ("P0_RECENT_SAME_CLOCK", "P1_WEEKDAY_SAME_CLOCK", "P2_EWMA", "P3_SHAPE_LEVEL")
TRACKS = (
    "REF_Q2_FIXED_PRICE_FROZEN", "Q4_2_PRICE_UNAWARE_RESETTLEMENT",
    "Q4_2_PRICE_BASELINE_P0", "Q4_2_PRICE_CANDIDATE_P1",
    "Q4_2_PRICE_CANDIDATE_P2", "Q4_2_PRICE_CANDIDATE_P3", "Q4_2_NOSTORAGE",
)


@dataclass(frozen=True)
class Q4Parameters(Q2Parameters):
    visibility_rule: str = VISIBILITY_RULE
    ewma_alpha: float = 0.35
    ewma_max_days: int = 28
    p3_level_window_intervals: int = 6
    p3_level_lower: float = 0.5
    p3_level_upper: float = 1.5

    def validate(self) -> None:
        super().validate()
        if self.visibility_rule != VISIBILITY_RULE:
            raise ValueError("Q4-2 production requires timestamp-at-decision visibility")
        if not 0 < self.ewma_alpha <= 1 or self.ewma_max_days < 1:
            raise ValueError("invalid EWMA parameters")
        if self.p3_level_window_intervals < 1 or not 0 < self.p3_level_lower <= self.p3_level_upper:
            raise ValueError("invalid P3 level bounds")


@dataclass(frozen=True)
class Q4Config:
    model_version: str
    q2_frozen_model_version: str
    q2_reference_run: Path
    data_version: str
    normalized_price_input: Path
    normalized_price_sha256: str
    normalized_actual_input: Path
    normalized_actual_sha256: str
    q2_price_input: Path
    q2_config: Path
    q2_reference_dispatch_sha256: str
    official_result4_2_template: Path
    official_result4_2_sha256: str
    audit_manifest: Path
    audit_summary: Path
    solver_name: str
    warmup_start: date
    output_start: date
    output_end: date
    parameters: Q4Parameters

    def validate(self) -> None:
        self.parameters.validate()
        if self.q2_frozen_model_version != "M2-Q2-EXPERIMENT-weekday_buffer-v1.0":
            raise ValueError("Q4-2 must inherit frozen Q2 weekday_buffer")
        if self.warmup_start != date(2025, 1, 1) or self.output_start != date(2025, 2, 1) or self.output_end != date(2025, 12, 31):
            raise ValueError("Q4-2 dates must be 2025-01-01 warmup and 2025-02-01..12-31 formal")
        if (self.output_end - self.output_start).days + 1 != 334:
            raise ValueError("Q4-2 formal period must contain 334 template days")
        hashes = (self.normalized_price_sha256, self.normalized_actual_sha256, self.q2_reference_dispatch_sha256, self.official_result4_2_sha256)
        if any(len(value) != 64 or any(character not in "0123456789ABCDEF" for character in value) for value in hashes):
            raise ValueError("Q4-2 input SHA-256 gates must be explicit")

    def snapshot(self) -> dict[str, Any]:
        return {**asdict(self), "q2_reference_run": str(self.q2_reference_run), "normalized_price_input": str(self.normalized_price_input), "normalized_actual_input": str(self.normalized_actual_input), "q2_price_input": str(self.q2_price_input), "q2_config": str(self.q2_config), "official_result4_2_template": str(self.official_result4_2_template), "audit_manifest": str(self.audit_manifest), "audit_summary": str(self.audit_summary), "warmup_start": self.warmup_start.isoformat(), "output_start": self.output_start.isoformat(), "output_end": self.output_end.isoformat(), "parameters": asdict(self.parameters)}


def load_config(path: Path) -> Q4Config:
    payload = json.loads(path.read_text(encoding="utf-8"))
    base = path.parent
    def resolve(value: str) -> Path:
        candidate = Path(value)
        return candidate if candidate.is_absolute() else (base / candidate).resolve()
    config = Q4Config(
        model_version=str(payload["model_version"]), q2_frozen_model_version=str(payload["q2_frozen_model_version"]),
        q2_reference_run=resolve(payload["q2_reference_run"]), data_version=str(payload["data_version"]),
        normalized_price_input=resolve(payload["normalized_price_input"]), normalized_price_sha256=str(payload["normalized_price_sha256"]), normalized_actual_input=resolve(payload["normalized_actual_input"]), normalized_actual_sha256=str(payload["normalized_actual_sha256"]),
        q2_price_input=resolve(payload["q2_price_input"]), q2_config=resolve(payload["q2_config"]), q2_reference_dispatch_sha256=str(payload["q2_reference_dispatch_sha256"]),
        official_result4_2_template=resolve(payload["official_result4_2_template"]), official_result4_2_sha256=str(payload["official_result4_2_sha256"]), audit_manifest=resolve(payload["audit_manifest"]),
        audit_summary=resolve(payload["audit_summary"]), solver_name=str(payload["solver_name"]),
        warmup_start=date.fromisoformat(payload["warmup_start"]), output_start=date.fromisoformat(payload["output_start"]), output_end=date.fromisoformat(payload["output_end"]),
        parameters=Q4Parameters(**payload["parameters"]),
    )
    config.validate()
    return config
