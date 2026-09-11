from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Mapping

import numpy as np

from q1_baseline.milp import CanonicalMILP, VariableLayout
from q1_baseline.solver_backend import MILPBackend

from .config import Q2Parameters
from .forecast import ForecastDay


@dataclass(frozen=True)
class DailyPlan:
    template_date: date
    baseline: str
    G: np.ndarray
    C: np.ndarray
    D: np.ndarray
    W_pred: np.ndarray
    z: np.ndarray
    S: np.ndarray
    objective_cost: float
    solver_name: str
    solver_version: str
    status: str
    termination_condition: str
    mip_gap: float | None
    runtime_seconds: float


class _Rows:
    def __init__(self) -> None:
        self.lower: list[float] = []
        self.upper: list[float] = []
        self.names: list[str] = []
        self.coefficients: list[dict[int, float]] = []

    def add(self, name: str, coefficients: Mapping[int, float], lower: float, upper: float) -> None:
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


def compute_window_start_soc(
    soc_at_midnight: float,
    previous_slot144_charge: float,
    previous_slot144_discharge: float,
    params: Q2Parameters,
) -> float:
    result = (
        soc_at_midnight
        + params.charge_efficiency * previous_slot144_charge
        - previous_slot144_discharge / params.discharge_efficiency
    )
    if not params.soc_min - params.feasibility_tolerance <= result <= params.soc_max + params.feasibility_tolerance:
        raise AssertionError("Q2-SOC-BRIDGE-001 produced SOC outside physical bounds")
    return float(result)


def build_daily_milp(
    forecast: ForecastDay,
    price: np.ndarray,
    params: Q2Parameters,
    initial_soc_0010: float,
) -> CanonicalMILP:
    params.validate()
    forecast.assert_causal()
    T = params.interval_count
    if price.shape != (T,):
        raise ValueError("daily price must have 144 values")
    if not params.soc_min <= initial_soc_0010 <= params.soc_max:
        raise ValueError("daily 00:10 initial SOC is outside physical bounds")

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
    objective[layout.G] = price
    lower = np.zeros(n, dtype=np.float64)
    upper = np.full(n, np.inf, dtype=np.float64)
    upper[layout.C] = params.charge_energy_max
    upper[layout.D] = params.discharge_energy_max
    upper[layout.z] = 1.0
    lower[layout.S] = params.soc_min
    upper[layout.S] = params.soc_max
    integrality = np.zeros(n, dtype=np.int8)
    integrality[layout.z] = 1

    cold = forecast.cold_mask
    # Q2-COLDSTART-001: zero commitment is enforced by variable bounds.
    for i in np.flatnonzero(cold):
        upper[layout.G.start + i] = 0.0
        upper[layout.C.start + i] = 0.0
        upper[layout.D.start + i] = 0.0
        upper[layout.z.start + i] = 0.0

    load = forecast.planning_load_kw * params.delta_t
    pv = forecast.pv_pred_kw * params.delta_t
    rows = _Rows()
    for i in range(T):
        rows.add(
            f"predicted_balance[{i + 1}]",
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
            {layout.C.start + i: 1.0, layout.z.start + i: -params.charge_energy_max},
            -np.inf,
            0.0,
        )
        rows.add(
            f"discharge_mode[{i + 1}]",
            {layout.D.start + i: 1.0, layout.z.start + i: params.discharge_energy_max},
            -np.inf,
            params.discharge_energy_max,
        )
    rows.add("soc_window_start_0010", {layout.S.start: 1.0}, initial_soc_0010, initial_soc_0010)
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


def _plan_from_vector(
    forecast: ForecastDay,
    problem: CanonicalMILP,
    vector: np.ndarray,
    *,
    baseline: str,
    objective_cost: float,
    solver_name: str,
    solver_version: str,
    status: str,
    termination_condition: str,
    mip_gap: float | None,
    runtime_seconds: float,
) -> DailyPlan:
    if vector.shape != (problem.num_col,):
        raise ValueError("solver vector has unexpected shape")
    q = problem.layout
    return DailyPlan(
        template_date=forecast.template_date,
        baseline=baseline,
        G=vector[q.G].copy(),
        C=vector[q.C].copy(),
        D=vector[q.D].copy(),
        W_pred=vector[q.W].copy(),
        z=vector[q.z].copy(),
        S=vector[q.S].copy(),
        objective_cost=float(objective_cost),
        solver_name=solver_name,
        solver_version=solver_version,
        status=status,
        termination_condition=termination_condition,
        mip_gap=mip_gap,
        runtime_seconds=float(runtime_seconds),
    )


def solve_daily_plan(
    forecast: ForecastDay,
    price: np.ndarray,
    params: Q2Parameters,
    initial_soc_0010: float,
    backend: MILPBackend,
    log_path: Path,
) -> DailyPlan:
    problem = build_daily_milp(forecast, price, params, initial_soc_0010)
    result = backend.solve(problem, params, log_path)  # explicit human-run path only
    return _plan_from_vector(
        forecast,
        problem,
        result.vector,
        baseline="B1_RECENT_SAME_CLOCK_MILP_R0",
        objective_cost=result.objective_cost,
        solver_name=result.solver_name,
        solver_version=result.solver_version,
        status=result.status,
        termination_condition=result.termination_condition,
        mip_gap=result.mip_gap,
        runtime_seconds=result.runtime_seconds,
    )


def cold_start_plan(forecast: ForecastDay, initial_soc_0010: float) -> DailyPlan:
    if not np.all(forecast.cold_mask):
        raise ValueError("cold_start_plan is only valid when all 144 intervals are cold")
    zeros = np.zeros(144, dtype=np.float64)
    return DailyPlan(
        template_date=forecast.template_date,
        baseline="B1_RECENT_SAME_CLOCK_MILP_R0",
        G=zeros.copy(), C=zeros.copy(), D=zeros.copy(), W_pred=zeros.copy(), z=zeros.copy(),
        S=np.full(145, initial_soc_0010, dtype=np.float64),
        objective_cost=0.0,
        solver_name="NONE",
        solver_version="N/A",
        status="COLD_START_NO_SOLVE",
        termination_condition="Q2-COLDSTART-001",
        mip_gap=None,
        runtime_seconds=0.0,
    )


def compute_b0_plan(
    forecast: ForecastDay, price: np.ndarray, params: Q2Parameters, soc_reference: float
) -> DailyPlan:
    load = forecast.planning_load_kw * params.delta_t
    pv = forecast.pv_pred_kw * params.delta_t
    G = np.maximum(load - pv, 0.0)
    W = np.maximum(pv - load, 0.0)
    G[forecast.cold_mask] = 0.0
    W[forecast.cold_mask] = 0.0
    zeros = np.zeros(144, dtype=np.float64)
    return DailyPlan(
        template_date=forecast.template_date,
        baseline="B0_NO_STORAGE_REFERENCE",
        G=G, C=zeros.copy(), D=zeros.copy(), W_pred=W, z=zeros.copy(),
        S=np.full(145, soc_reference, dtype=np.float64),
        objective_cost=float(np.dot(price, G)),
        solver_name="ANALYTIC",
        solver_version="1.0",
        status="OPTIMAL_CLOSED_FORM",
        termination_condition="ANALYTIC",
        mip_gap=0.0,
        runtime_seconds=0.0,
    )

