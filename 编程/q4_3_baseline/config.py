from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from q3_baseline.config import Q3Config, load_config as load_q3_config
from q4_baseline.config import Q4Config, load_config as load_q4_config


MODEL_VERSION = "M4-Q4-3-PRICE-AWARE-ROLLING-v0.1"
VISIBILITY_RULE = "TIMESTAMP_LE_DECISION_VISIBLE"
WARMUP_RULE = "FROZEN_Q3_STATE_CHAIN"
ISSUE_SET = (0, 360, 720, 1080)
PREDICTORS = (
    "P0_RECENT_SAME_CLOCK",
    "P1_WEEKDAY_SAME_CLOCK",
    "P2_EWMA",
    "P3_SHAPE_LEVEL",
)
TRACK_TO_PREDICTOR = {
    "Q4_3_PRICE_BASELINE_P0": PREDICTORS[0],
    "Q4_3_PRICE_CANDIDATE_P1": PREDICTORS[1],
    "Q4_3_PRICE_CANDIDATE_P2": PREDICTORS[2],
    "Q4_3_PRICE_CANDIDATE_P3": PREDICTORS[3],
}
REFERENCE_TRACKS = ("REF_Q3_FIXED_PRICE_FROZEN", "Q4_3_PRICE_UNAWARE_REFERENCE")
TRACKS = REFERENCE_TRACKS + tuple(TRACK_TO_PREDICTOR)


@dataclass(frozen=True)
class Q43Config:
    model_version: str
    q3_frozen_model_version: str
    q3_frozen_track: str
    q4_2_frozen_model_version: str
    q4_2_frozen_predictor: str
    visibility_rule: str
    warmup_rule: str
    q3_config_path: Path
    q4_config_path: Path
    frozen_q3_run: Path
    frozen_q4_2_run: Path
    official_result4_3_template: Path
    official_result4_3_sha256: str
    frozen_q3_manifest_sha256: str
    frozen_q3_dispatch_sha256: str
    frozen_q4_2_manifest_sha256: str
    output_start: date
    output_end: date
    solver_name: str
    q3: Q3Config
    q4: Q4Config

    @property
    def parameters(self):
        return self.q3.parameters

    @property
    def price_parameters(self):
        return self.q4.parameters

    def validate(self) -> None:
        if self.model_version != MODEL_VERSION:
            raise ValueError("Q4-3 model version is not the locked production draft")
        if self.q3_frozen_model_version != "M3-Q3-POINT-MODEL-B-v2.0" or self.q3_frozen_track != "Q3_ROLLING_INTERP":
            raise ValueError("Q4-3 must inherit frozen Q3_ROLLING_INTERP")
        if self.q4_2_frozen_model_version != "M4-Q4-2-PRICE-AWARE-v0.1" or self.q4_2_frozen_predictor != "P2_EWMA":
            raise ValueError("Q4-2 frozen predictor identity changed")
        if self.visibility_rule != VISIBILITY_RULE or self.warmup_rule != WARMUP_RULE:
            raise ValueError("Q4-3 visibility/warmup contract changed")
        if self.output_start != date(2025, 2, 1) or self.output_end != date(2025, 12, 31):
            raise ValueError("Q4-3 formal template dates must be 2025-02-01..2025-12-31")
        if (self.output_end - self.output_start).days + 1 != 334:
            raise AssertionError("Q4-3 formal period must contain 334 template days")
        if self.q3.parameters.cost_semantics != "MODEL_B" or self.q3.issue_sets["rolling4"] != ISSUE_SET:
            raise ValueError("frozen Q3 MODEL-B/issue-set identity changed")
        if self.q4.parameters.visibility_rule != VISIBILITY_RULE:
            raise ValueError("Q4-2 price visibility identity changed")

    def snapshot(self) -> dict[str, Any]:
        return {
            "model_version": self.model_version,
            "q3_frozen_model_version": self.q3_frozen_model_version,
            "q3_frozen_track": self.q3_frozen_track,
            "q4_2_frozen_model_version": self.q4_2_frozen_model_version,
            "q4_2_frozen_predictor": self.q4_2_frozen_predictor,
            "visibility_rule": self.visibility_rule,
            "warmup_rule": self.warmup_rule,
            "q3_config_path": str(self.q3_config_path),
            "q4_config_path": str(self.q4_config_path),
            "frozen_q3_run": str(self.frozen_q3_run),
            "frozen_q4_2_run": str(self.frozen_q4_2_run),
            "official_result4_3_template": str(self.official_result4_3_template),
            "official_result4_3_sha256": self.official_result4_3_sha256,
            "frozen_q3_manifest_sha256": self.frozen_q3_manifest_sha256,
            "frozen_q3_dispatch_sha256": self.frozen_q3_dispatch_sha256,
            "frozen_q4_2_manifest_sha256": self.frozen_q4_2_manifest_sha256,
            "output_start": self.output_start.isoformat(),
            "output_end": self.output_end.isoformat(),
            "solver_name": self.solver_name,
            "issue_set_minutes": list(ISSUE_SET),
            "price_predictors": list(PREDICTORS),
        }


def load_config(path: str | Path) -> Q43Config:
    source = Path(path).resolve()
    payload = json.loads(source.read_text(encoding="utf-8"))
    base = source.parent

    def resolve(value: str) -> Path:
        item = Path(value)
        return item.resolve() if item.is_absolute() else (base / item).resolve()

    q3_path = resolve(payload["q3_config"])
    q4_path = resolve(payload["q4_config"])
    config = Q43Config(
        model_version=str(payload["model_version"]),
        q3_frozen_model_version=str(payload["q3_frozen_model_version"]),
        q3_frozen_track=str(payload["q3_frozen_track"]),
        q4_2_frozen_model_version=str(payload["q4_2_frozen_model_version"]),
        q4_2_frozen_predictor=str(payload["q4_2_frozen_predictor"]),
        visibility_rule=str(payload["visibility_rule"]),
        warmup_rule=str(payload["warmup_rule"]),
        q3_config_path=q3_path,
        q4_config_path=q4_path,
        frozen_q3_run=resolve(payload["frozen_q3_run"]),
        frozen_q4_2_run=resolve(payload["frozen_q4_2_run"]),
        official_result4_3_template=resolve(payload["official_result4_3_template"]),
        official_result4_3_sha256=str(payload["official_result4_3_sha256"]).upper(),
        frozen_q3_manifest_sha256=str(payload["frozen_q3_manifest_sha256"]).upper(),
        frozen_q3_dispatch_sha256=str(payload["frozen_q3_dispatch_sha256"]).upper(),
        frozen_q4_2_manifest_sha256=str(payload["frozen_q4_2_manifest_sha256"]).upper(),
        output_start=date.fromisoformat(payload["output_start"]),
        output_end=date.fromisoformat(payload["output_end"]),
        solver_name=str(payload["solver_name"]),
        q3=load_q3_config(q3_path),
        q4=load_q4_config(q4_path),
    )
    config.validate()
    return config

