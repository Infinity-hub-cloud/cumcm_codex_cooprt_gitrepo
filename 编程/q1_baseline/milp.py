from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .baseline import DispatchSolution
from .data_contract import Q1InputData
from .parameters import Q1Parameters


@dataclass(frozen=True)
class VariableLayout:
    G: slice
    C: slice
    D: slice
    W: slice
    z: slice
    S: slice


@dataclass(frozen=True)
class CanonicalMILP:
    objective: np.ndarray
    col_lower: np.ndarray
    col_upper: np.ndarray
    integrality: np.ndarray
    row_lower: np.ndarray
    row_upper: np.ndarray
    row_start: np.ndarray
    col_index: np.ndarray
    values: np.ndarray
    row_names: tuple[str, ...]
    layout: VariableLayout

    @property
    def num_col(self) -> int:
        return int(self.objective.size)

    @property
    def num_row(self) -> int:
        return int(self.row_lower.size)


class _Rows:
    def __init__(self) -> None:
        self.lower: list[float] = []
        self.upper: list[float] = []
        self.names: list[str] = []
        self.coefficients: list[dict[int, float]] = []

    def add(
        self, name: str, coefficients: Mapping[int, float], lower: float, upper: float
    ) -> None:
        self.names.append(name)
        self.coefficients.append(dict(coefficients))
        self.lower.append(float(lower))
        self.upper.append(float(upper))

    def csr(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        starts = [0]
        indices: list[int] = []
        values: list[float] = []
        for row in self.coefficients:
            for index, value in sorted(row.items()):
                if value:
                    indices.append(index)
                    values.append(float(value))
            starts.append(len(indices))
        return (
            np.asarray(starts, dtype=np.int32),
            np.asarray(indices, dtype=np.int32),
            np.asarray(values, dtype=np.float64),
        )


def build_q1_milp(data: Q1InputData, params: Q1Parameters) -> CanonicalMILP:
    data.validate(params)
    params.validate()
    T = params.interval_count
    layout = VariableLayout(
        G=slice(0, T),
        C=slice(T, 2 * T),
        D=slice(2 * T, 3 * T),
        W=slice(3 * T, 4 * T),
        z=slice(4 * T, 5 * T),
        S=slice(5 * T, 6 * T + 1),
    )
    n = 6 * T + 1
    objective = np.zeros(n, dtype=np.float64)
    objective[layout.G] = data.price
    lower = np.zeros(n, dtype=np.float64)
    upper = np.full(n, np.inf, dtype=np.float64)
    upper[layout.C] = params.charge_energy_max
    upper[layout.D] = params.discharge_energy_max
    upper[layout.z] = 1.0
    lower[layout.S] = params.soc_min
    upper[layout.S] = params.soc_max
    integrality = np.zeros(n, dtype=np.int8)
    integrality[layout.z] = 1

    load = data.load_kwh(params)
    pv = data.pv_kwh(params)
    rows = _Rows()
    for i in range(T):
        rows.add(
            f"balance[{i + 1}]",
            {
                layout.G.start + i: 1.0,
                layout.C.start + i: -1.0,
                layout.D.start + i: 1.0,
                layout.W.start + i: -1.0,
            },
            load[i] - pv[i],
            load[i] - pv[i],
        )
        rows.add(
            f"soc[{i + 1}]",
            {
                layout.S.start + i + 1: 1.0,
                layout.S.start + i: -1.0,
                layout.C.start + i: -params.charge_efficiency,
                layout.D.start + i: 1.0 / params.discharge_efficiency,
            },
            0.0,
            0.0,
        )
        rows.add(
            f"charge_mode[{i + 1}]",
            {
                layout.C.start + i: 1.0,
                layout.z.start + i: -params.charge_energy_max,
            },
            -np.inf,
            0.0,
        )
        rows.add(
            f"discharge_mode[{i + 1}]",
            {
                layout.D.start + i: 1.0,
                layout.z.start + i: params.discharge_energy_max,
            },
            -np.inf,
            params.discharge_energy_max,
        )

    # S[T-1] is next-day 00:00; both named constraints are retained so the
    # input contract cannot silently diverge if the two configured values differ.
    rows.add(
        "soc_midnight_initial",
        {layout.S.start + T - 1: 1.0},
        params.soc_initial,
        params.soc_initial,
    )
    rows.add(
        "soc_midnight_terminal",
        {layout.S.start + T - 1: 1.0},
        params.soc_terminal,
        params.soc_terminal,
    )
    rows.add(
        "soc_cycle_0010",
        {layout.S.start + T: 1.0, layout.S.start: -1.0},
        0.0,
        0.0,
    )
    row_start, col_index, values = rows.csr()
    return CanonicalMILP(
        objective=objective,
        col_lower=lower,
        col_upper=upper,
        integrality=integrality,
        row_lower=np.asarray(rows.lower, dtype=np.float64),
        row_upper=np.asarray(rows.upper, dtype=np.float64),
        row_start=row_start,
        col_index=col_index,
        values=values,
        row_names=tuple(rows.names),
        layout=layout,
    )


def dispatch_from_vector(
    vector: np.ndarray,
    problem: CanonicalMILP,
    *,
    objective_cost: float,
    solver_name: str,
    solver_version: str,
    status: str,
    termination_condition: str,
    mip_gap: float | None,
    runtime_seconds: float,
) -> DispatchSolution:
    if vector.shape != (problem.num_col,):
        raise ValueError("solver vector has unexpected shape")
    layout = problem.layout
    return DispatchSolution(
        G=vector[layout.G].copy(),
        C=vector[layout.C].copy(),
        D=vector[layout.D].copy(),
        W=vector[layout.W].copy(),
        z=vector[layout.z].copy(),
        S=vector[layout.S].copy(),
        objective_cost=float(objective_cost),
        solver_name=solver_name,
        solver_version=solver_version,
        status=status,
        termination_condition=termination_condition,
        mip_gap=mip_gap,
        runtime_seconds=float(runtime_seconds),
        metadata={"baseline_id": "B1_Q1_MILP"},
    )

