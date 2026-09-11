from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .data_contract import Q1InputData
from .parameters import Q1Parameters


@dataclass(frozen=True)
class DispatchSolution:
    G: np.ndarray
    C: np.ndarray
    D: np.ndarray
    W: np.ndarray
    z: np.ndarray
    S: np.ndarray
    objective_cost: float
    solver_name: str
    solver_version: str
    status: str
    termination_condition: str
    mip_gap: float | None
    runtime_seconds: float
    metadata: dict[str, Any]


def compute_b0(data: Q1InputData, params: Q1Parameters) -> DispatchSolution:
    data.validate(params)
    load = data.load_kwh(params)
    pv = data.pv_kwh(params)
    grid = np.maximum(load - pv, 0.0)
    waste = np.maximum(pv - load, 0.0)
    zeros = np.zeros(params.interval_count, dtype=np.float64)
    soc = np.full(params.interval_count + 1, params.soc_initial, dtype=np.float64)
    return DispatchSolution(
        G=grid,
        C=zeros.copy(),
        D=zeros.copy(),
        W=waste,
        z=zeros.copy(),
        S=soc,
        objective_cost=float(np.dot(data.price, grid)),
        solver_name="none",
        solver_version="not-applicable",
        status="BASELINE_COMPUTED",
        termination_condition="closed-form no-storage baseline",
        mip_gap=None,
        runtime_seconds=0.0,
        metadata={"baseline_id": "B0_NO_STORAGE"},
    )

