from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from q2_baseline.config import Q2Parameters


TRACKS = (
    "REF_Q2_FROZEN",
    "Q3_ATTACHMENT3_0ONLY",
    "Q3_ROLLING_4ISSUE",
    "Q3_NOSTORAGE_REFERENCE",
)


@dataclass(frozen=True)
class Q3Parameters(Q2Parameters):
    downward_adjustment_multiplier: float = 0.5
    upward_adjustment_multiplier: float = 1.5
    solver_console_output: bool = False

    def validate(self) -> None:
        super().validate()
        if self.downward_adjustment_multiplier != 0.5:
            raise ValueError("Q3 downward adjustment multiplier must be 0.5")
        if self.upward_adjustment_multiplier != 1.5:
            raise ValueError("Q3 upward adjustment multiplier must be 1.5")
        if not isinstance(self.solver_console_output, bool):
            raise ValueError("solver_console_output must be boolean")

    def normalize_soc(self, value: float) -> float:
        """Snap tolerance-scale boundary drift before fixing SOC in a MILP."""
        current = float(value)
        if not math.isfinite(current):
            raise ValueError(f"current SOC is not finite: {current!r}")
        lower = self.soc_min - self.feasibility_tolerance
        upper = self.soc_max + self.feasibility_tolerance
        if not lower <= current <= upper:
            raise ValueError(
                "current SOC is outside physical bounds: "
                f"value={current!r}, allowed_with_tolerance=[{lower!r}, {upper!r}]"
            )
        return min(max(current, self.soc_min), self.soc_max)


@dataclass(frozen=True)
class Q3Config:
    model_version: str
    q2_frozen_model_version: str
    data_version: str
    normalized_price_input: Path
    normalized_actual_input: Path
    attachment3_forecast_input: Path
    attachment3_mapped_input: Path
    official_result3_template: Path
    audit_manifest: Path
    audit_summary: Path
    q2_reference_run: Path
    solver_name: str
    warmup_start: date
    output_start: date
    output_end: date
    issue_sets: dict[str, tuple[int, ...]]
    parameters: Q3Parameters

    def validate(self) -> None:
        self.parameters.validate()
        if self.q2_frozen_model_version != "M2-Q2-EXPERIMENT-weekday_buffer-v1.0":
            raise ValueError("Q3 must inherit the accepted weekday_buffer Q2 model")
        if self.warmup_start != date(2025, 1, 1):
            raise ValueError("locked warmup start is 2025-01-01")
        if self.output_start != date(2025, 2, 1) or self.output_end != date(2025, 12, 31):
            raise ValueError("locked formal Q3 output is 2025-02-01..2025-12-31")
        if (self.output_end - self.output_start).days + 1 != 334:
            raise AssertionError("formal Q3 output must contain 334 template days")
        allowed = {0, 360, 720, 1080}
        for name, values in self.issue_sets.items():
            if not values or values[0] != 0 or not set(values) <= allowed:
                raise ValueError(f"invalid official issue set {name}: {values}")

    def snapshot(self) -> dict[str, Any]:
        return {
            "model_version": self.model_version,
            "q2_frozen_model_version": self.q2_frozen_model_version,
            "data_version": self.data_version,
            "normalized_price_input": str(self.normalized_price_input),
            "normalized_actual_input": str(self.normalized_actual_input),
            "attachment3_forecast_input": str(self.attachment3_forecast_input),
            "attachment3_mapped_input": str(self.attachment3_mapped_input),
            "official_result3_template": str(self.official_result3_template),
            "audit_manifest": str(self.audit_manifest),
            "audit_summary": str(self.audit_summary),
            "q2_reference_run": str(self.q2_reference_run),
            "solver_name": self.solver_name,
            "warmup_start": self.warmup_start.isoformat(),
            "output_start": self.output_start.isoformat(),
            "output_end": self.output_end.isoformat(),
            "issue_sets": {key: list(value) for key, value in self.issue_sets.items()},
            "parameters": asdict(self.parameters),
        }


def load_config(path: Path) -> Q3Config:
    payload = json.loads(path.read_text(encoding="utf-8"))
    base = path.parent

    def resolve(value: str) -> Path:
        candidate = Path(value)
        return candidate if candidate.is_absolute() else (base / candidate).resolve()

    config = Q3Config(
        model_version=str(payload["model_version"]),
        q2_frozen_model_version=str(payload["q2_frozen_model_version"]),
        data_version=str(payload["data_version"]),
        normalized_price_input=resolve(payload["normalized_price_input"]),
        normalized_actual_input=resolve(payload["normalized_actual_input"]),
        attachment3_forecast_input=resolve(payload["attachment3_forecast_input"]),
        attachment3_mapped_input=resolve(payload["attachment3_mapped_input"]),
        official_result3_template=resolve(payload["official_result3_template"]),
        audit_manifest=resolve(payload["audit_manifest"]),
        audit_summary=resolve(payload["audit_summary"]),
        q2_reference_run=resolve(payload["q2_reference_run"]),
        solver_name=str(payload["solver_name"]),
        warmup_start=date.fromisoformat(payload["warmup_start"]),
        output_start=date.fromisoformat(payload["output_start"]),
        output_end=date.fromisoformat(payload["output_end"]),
        issue_sets={key: tuple(int(v) for v in values) for key, values in payload["issue_sets"].items()},
        parameters=Q3Parameters(**payload["parameters"]),
    )
    config.validate()
    return config
