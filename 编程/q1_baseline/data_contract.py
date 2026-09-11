from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .parameters import Q1Parameters
from .time_index import TemplateInterval, validate_q1_intervals


class DataContractError(ValueError):
    pass


@dataclass(frozen=True)
class Q1InputData:
    intervals: tuple[TemplateInterval, ...]
    price: np.ndarray
    load_kw: np.ndarray
    pv_kw: np.ndarray
    source_path: Path
    source_sha256: str

    def validate(self, params: Q1Parameters) -> None:
        try:
            validate_q1_intervals(self.intervals, params.interval_count, 10)
        except ValueError as exc:
            raise DataContractError(str(exc)) from exc
        arrays = {
            "price": self.price,
            "load_kw": self.load_kw,
            "pv_kw": self.pv_kw,
        }
        for name, values in arrays.items():
            if values.shape != (params.interval_count,):
                raise DataContractError(
                    f"{name} shape must be ({params.interval_count},), got {values.shape}"
                )
            if not np.all(np.isfinite(values)):
                raise DataContractError(f"{name} contains missing or non-finite values")
            if np.any(values < 0):
                raise DataContractError(f"{name} contains negative values")

    def load_kwh(self, params: Q1Parameters) -> np.ndarray:
        return self.load_kw * params.delta_t

    def pv_kwh(self, params: Q1Parameters) -> np.ndarray:
        return self.pv_kw * params.delta_t

