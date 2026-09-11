from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Q2Parameters:
    interval_count: int = 144
    delta_t: float = 1.0 / 6.0
    charge_efficiency: float = 0.9
    discharge_efficiency: float = 0.9
    soc_min: float = 1200.0
    soc_max: float = 10800.0
    charge_power_max: float = 5000.0
    discharge_power_max: float = 5000.0
    soc_initial: float = 6000.0
    emergency_price_multiplier: float = 5.0
    feasibility_tolerance: float = 1e-6
    integrality_tolerance: float = 1e-6
    aggregate_tolerance: float = 1e-5
    input_energy_rounding_tolerance: float = 5.1e-5
    mip_rel_gap: float = 1e-8
    time_limit_seconds: float = 300.0

    @property
    def charge_energy_max(self) -> float:
        return self.charge_power_max * self.delta_t

    @property
    def discharge_energy_max(self) -> float:
        return self.discharge_power_max * self.delta_t

    def validate(self) -> None:
        if self.interval_count != 144 or self.delta_t != 1.0 / 6.0:
            raise ValueError("Q2 baseline requires 144 exact ten-minute intervals")
        if not (0 < self.charge_efficiency <= 1):
            raise ValueError("invalid charge efficiency")
        if not (0 < self.discharge_efficiency <= 1):
            raise ValueError("invalid discharge efficiency")
        if not self.soc_min <= self.soc_initial <= self.soc_max:
            raise ValueError("initial SOC is outside its physical bounds")
        if self.input_energy_rounding_tolerance <= 0:
            raise ValueError("input rounding tolerance must be positive")
        if self.charge_energy_max != self.charge_power_max * self.delta_t:
            raise AssertionError("charge q_max must use exact p_max * delta_t")
        if self.discharge_energy_max != self.discharge_power_max * self.delta_t:
            raise AssertionError("discharge q_max must use exact p_max * delta_t")


@dataclass(frozen=True)
class Q2Config:
    model_version: str
    forecast_version: str
    data_version: str
    normalized_price_input: Path
    normalized_actual_input: Path
    official_result2_template: Path
    audit_manifest: Path
    audit_summary: Path
    solver_name: str
    warmup_start: date
    output_start: date
    output_end: date
    parameters: Q2Parameters

    def validate(self) -> None:
        self.parameters.validate()
        if self.warmup_start != date(2025, 1, 1):
            raise ValueError("locked warmup start is 2025-01-01")
        if self.output_start != date(2025, 2, 1):
            raise ValueError("locked formal output start is 2025-02-01")
        if self.output_end != date(2025, 12, 31):
            raise ValueError("locked formal output end is 2025-12-31")
        if (self.output_end - self.output_start).days + 1 != 334:
            raise AssertionError("formal Q2 output must contain 334 template days")

    def snapshot(self) -> dict[str, Any]:
        return {
            "model_version": self.model_version,
            "forecast_version": self.forecast_version,
            "data_version": self.data_version,
            "normalized_price_input": str(self.normalized_price_input),
            "normalized_actual_input": str(self.normalized_actual_input),
            "official_result2_template": str(self.official_result2_template),
            "audit_manifest": str(self.audit_manifest),
            "audit_summary": str(self.audit_summary),
            "solver_name": self.solver_name,
            "warmup_start": self.warmup_start.isoformat(),
            "output_start": self.output_start.isoformat(),
            "output_end": self.output_end.isoformat(),
            "parameters": asdict(self.parameters),
        }


def load_config(path: Path) -> Q2Config:
    payload = json.loads(path.read_text(encoding="utf-8"))
    base = path.parent

    def resolve(value: str) -> Path:
        candidate = Path(value)
        return candidate if candidate.is_absolute() else (base / candidate).resolve()

    config = Q2Config(
        model_version=str(payload["model_version"]),
        forecast_version=str(payload["forecast_version"]),
        data_version=str(payload["data_version"]),
        normalized_price_input=resolve(payload["normalized_price_input"]),
        normalized_actual_input=resolve(payload["normalized_actual_input"]),
        official_result2_template=resolve(payload["official_result2_template"]),
        audit_manifest=resolve(payload["audit_manifest"]),
        audit_summary=resolve(payload["audit_summary"]),
        solver_name=str(payload["solver_name"]),
        warmup_start=date.fromisoformat(payload["warmup_start"]),
        output_start=date.fromisoformat(payload["output_start"]),
        output_end=date.fromisoformat(payload["output_end"]),
        parameters=Q2Parameters(**payload["parameters"]),
    )
    config.validate()
    return config
