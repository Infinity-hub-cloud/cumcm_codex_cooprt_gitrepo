from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Q1Parameters:
    interval_count: int = 144
    delta_t: float = 1.0 / 6.0
    charge_efficiency: float = 0.9
    discharge_efficiency: float = 0.9
    soc_min: float = 1200.0
    soc_max: float = 10800.0
    charge_power_max: float = 5000.0
    discharge_power_max: float = 5000.0
    soc_initial: float = 6000.0
    soc_terminal: float = 6000.0
    feasibility_tolerance: float = 1e-6
    integrality_tolerance: float = 1e-6
    objective_tolerance: float = 1e-5
    aggregate_tolerance: float = 1e-5
    mip_rel_gap: float = 1e-8
    time_limit_seconds: float = 300.0

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "Q1Parameters":
        params = cls(**dict(values))
        params.validate()
        return params

    def validate(self) -> None:
        if self.interval_count != 144:
            raise ValueError("Q1 official template requires interval_count=144")
        if self.delta_t <= 0 or abs(self.delta_t - 1.0 / 6.0) > 1e-12:
            raise ValueError("Q1 requires delta_t=1/6 hour")
        if not (0 < self.charge_efficiency <= 1):
            raise ValueError("charge_efficiency must be in (0, 1]")
        if not (0 < self.discharge_efficiency <= 1):
            raise ValueError("discharge_efficiency must be in (0, 1]")
        if not self.soc_min <= self.soc_initial <= self.soc_max:
            raise ValueError("soc_initial is outside SOC bounds")
        if not self.soc_min <= self.soc_terminal <= self.soc_max:
            raise ValueError("soc_terminal is outside SOC bounds")
        if self.charge_power_max <= 0 or self.discharge_power_max <= 0:
            raise ValueError("charge/discharge power limits must be positive")
        if min(
            self.feasibility_tolerance,
            self.integrality_tolerance,
            self.objective_tolerance,
            self.aggregate_tolerance,
        ) <= 0:
            raise ValueError("all tolerances must be positive")

    @property
    def charge_energy_max(self) -> float:
        return self.charge_power_max * self.delta_t

    @property
    def discharge_energy_max(self) -> float:
        return self.discharge_power_max * self.delta_t

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

