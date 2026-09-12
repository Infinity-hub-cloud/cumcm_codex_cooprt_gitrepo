from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Mapping

import numpy as np

from q1_baseline.solver_backend import MILPBackend
from q2_baseline.planner import DailyPlan, build_daily_milp, compute_b0_plan, solve_daily_plan

from .config import Q3Parameters
from .forecast import FrozenPlanningDay, PVSelection


@dataclass(frozen=True)
class Q3Layout:
    Q: slice
    C: slice
    D: slice
    W: slice
    z: slice
    S: slice
    Jregular: slice


@dataclass(frozen=True)
class Q3MILP:
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
    layout: Q3Layout

    @property
    def num_col(self) -> int:
        return int(self.objective.size)

    @property
    def num_row(self) -> int:
        return int(self.row_lower.size)


@dataclass
class RollingPlan:
    template_date: date
    G: np.ndarray
    Q: np.ndarray
    C: np.ndarray
    D: np.ndarray
    W_pred: np.ndarray
    z: np.ndarray
    S: np.ndarray
    pv_source: list[str]
    issue_datetime: list[datetime | None]
    solver_status: list[str]
    pv_metadata: list[PVSelection]
    initial_solver_name: str = "NONE"
    initial_solver_version: str = "N/A"
    initial_objective: float = 0.0
    initial_mip_gap: float | None = None
    initial_runtime: float = 0.0
    initial_termination: str = "UNSET"
    initial_rows: int = 0
    initial_columns: int = 0
    initial_binary_count: int = 0

    @classmethod
    def from_initial(
        cls,
        daily: DailyPlan,
        frozen: FrozenPlanningDay,
        dimensions: tuple[int, int, int] = (0, 0, 0),
    ) -> "RollingPlan":
        return cls(
            daily.template_date,
            daily.G.copy(),
            daily.G.copy(),
            daily.C.copy(),
            daily.D.copy(),
            daily.W_pred.copy(),
            daily.z.copy(),
            daily.S.copy(),
            [row.forecast_source for row in frozen.initial_pv],
            [row.issue_datetime for row in frozen.initial_pv],
            [daily.status] * 144,
            list(frozen.initial_pv),
            daily.solver_name, daily.solver_version, daily.objective_cost, daily.mip_gap,
            daily.runtime_seconds, daily.termination_condition, *dimensions,
        )

    def assert_initial_g_immutable(self, original: np.ndarray) -> None:
        if not np.array_equal(self.G, original):
            raise AssertionError("Q3 G must remain immutable after 00:00")


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


def build_adjustment_milp(
    G: np.ndarray,
    load_plan_kw: np.ndarray,
    pv_rows: tuple[PVSelection, ...],
    price: np.ndarray,
    current_soc: float,
    params: Q3Parameters,
    *,
    no_storage: bool = False,
) -> Q3MILP:
    params.validate()
    n = len(pv_rows)
    if not n:
        raise ValueError("adjustment horizon cannot be empty")
    if G.shape != (n,) or load_plan_kw.shape != (n,) or price.shape != (n,):
        raise ValueError("Q3 adjustment arrays must match the remaining horizon")
    current_soc = params.normalize_soc(current_soc)
    for row in pv_rows:
        row.assert_causal()

    layout = Q3Layout(
        Q=slice(0, n),
        C=slice(n, 2 * n),
        D=slice(2 * n, 3 * n),
        W=slice(3 * n, 4 * n),
        z=slice(4 * n, 5 * n),
        S=slice(5 * n, 6 * n + 1),
        Jregular=slice(6 * n + 1, 7 * n + 1),
    )
    size = 7 * n + 1
    objective = np.zeros(size, dtype=np.float64)
    objective[layout.Jregular] = 1.0
    lower = np.zeros(size, dtype=np.float64)
    upper = np.full(size, np.inf, dtype=np.float64)
    upper[layout.C] = 0.0 if no_storage else params.charge_energy_max
    upper[layout.D] = 0.0 if no_storage else params.discharge_energy_max
    upper[layout.z] = 0.0 if no_storage else 1.0
    lower[layout.S] = params.soc_min
    upper[layout.S] = params.soc_max
    integrality = np.zeros(size, dtype=np.int8)
    integrality[layout.z] = 1

    load = load_plan_kw * params.delta_t
    pv = np.asarray([row.forecast_kw for row in pv_rows], dtype=np.float64) * params.delta_t
    rows = _Rows()
    for i in range(n):
        rows.add(
            f"predicted_balance[{i}]",
            {
                layout.Q.start + i: 1.0,
                layout.C.start + i: -1.0,
                layout.D.start + i: 1.0,
                layout.W.start + i: -1.0,
            },
            load[i] - pv[i],
            load[i] - pv[i],
        )
        rows.add(
            f"soc[{i}]",
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
            f"charge_mode[{i}]",
            {layout.C.start + i: 1.0, layout.z.start + i: -params.charge_energy_max},
            -np.inf,
            0.0,
        )
        rows.add(
            f"discharge_mode[{i}]",
            {layout.D.start + i: 1.0, layout.z.start + i: params.discharge_energy_max},
            -np.inf,
            params.discharge_energy_max,
        )
        # Convex epigraph.  MODEL_B is the approved primary semantics;
        # MODEL_A remains an explicitly labelled sensitivity only.
        if params.cost_semantics == "MODEL_B":
            first_rhs = 0.5 * price[i] * G[i]
            first_q = -0.5 * price[i]
        else:
            first_rhs = 1.5 * price[i] * G[i]
            first_q = 0.5 * price[i]
        rows.add(f"regular_cost_left[{i}]", {
            layout.Jregular.start + i: 1.0, layout.Q.start + i: first_q,
        }, first_rhs, np.inf)
        rows.add(f"regular_cost_right[{i}]", {
            layout.Jregular.start + i: 1.0,
            layout.Q.start + i: -1.5 * price[i],
        }, -0.5 * price[i] * G[i], np.inf)
    rows.add("current_real_soc", {layout.S.start: 1.0}, current_soc, current_soc)
    row_start, col_index, values = rows.csr()
    return Q3MILP(
        objective,
        lower,
        upper,
        integrality,
        np.asarray(rows.lower, dtype=np.float64),
        np.asarray(rows.upper, dtype=np.float64),
        row_start,
        col_index,
        values,
        tuple(rows.names),
        layout,
    )


def solve_initial_plan(
    frozen: FrozenPlanningDay,
    price: np.ndarray,
    params: Q3Parameters,
    initial_soc_0010: float,
    backend: MILPBackend,
    log_path: Path,
    *,
    no_storage: bool = False,
) -> RollingPlan:
    q2_view = frozen.as_q2_forecast_for_initial_solve()
    if no_storage:
        daily = compute_b0_plan(q2_view, price, params, initial_soc_0010)
        dimensions = (0, 0, 0)
    else:
        structure = build_daily_milp(q2_view, price, params, initial_soc_0010)
        dimensions = (structure.num_row, structure.num_col, int(np.sum(structure.integrality)))
        daily = solve_daily_plan(q2_view, price, params, initial_soc_0010, backend, log_path)
    return RollingPlan.from_initial(daily, frozen, dimensions)


def apply_adjustment_solution(
    plan: RollingPlan,
    start_slot: int,
    pv_rows: tuple[PVSelection, ...],
    problem: Q3MILP,
    vector: np.ndarray,
    status: str,
) -> None:
    if not 1 <= start_slot <= 144:
        raise ValueError("start_slot must be in 1..144")
    n = 145 - start_slot
    if len(pv_rows) != n or vector.shape != (problem.num_col,):
        raise ValueError("adjustment solution shape mismatch")
    q = problem.layout
    sl = slice(start_slot - 1, 144)
    original_g = plan.G.copy()
    plan.Q[sl] = vector[q.Q]
    plan.C[sl] = vector[q.C]
    plan.D[sl] = vector[q.D]
    plan.W_pred[sl] = vector[q.W]
    plan.z[sl] = vector[q.z]
    plan.S[start_slot - 1 :] = vector[q.S]
    for offset, row in enumerate(pv_rows, start=start_slot - 1):
        plan.pv_source[offset] = row.forecast_source
        plan.issue_datetime[offset] = row.issue_datetime
        plan.solver_status[offset] = status
        plan.pv_metadata[offset] = row
    plan.assert_initial_g_immutable(original_g)


def solve_and_apply_adjustment(
    plan: RollingPlan,
    frozen: FrozenPlanningDay,
    pv_rows: tuple[PVSelection, ...],
    price: np.ndarray,
    current_soc: float,
    params: Q3Parameters,
    backend: MILPBackend,
    log_path: Path,
    *,
    no_storage: bool = False,
) -> dict[str, object]:
    if not pv_rows:
        raise ValueError("no unexecuted intervals supplied")
    start_slot = pv_rows[0].template_slot
    expected = tuple(range(start_slot, 145))
    if tuple(row.template_slot for row in pv_rows) != expected:
        raise AssertionError("adjustment horizon must be a contiguous template suffix")
    sl = slice(start_slot - 1, 144)
    problem = build_adjustment_milp(
        plan.G[sl],
        frozen.load_plan_kw[sl],
        pv_rows,
        price[sl],
        current_soc,
        params,
        no_storage=no_storage,
    )
    result = backend.solve(problem, params, log_path)  # explicit human-run path only
    apply_adjustment_solution(plan, start_slot, pv_rows, problem, result.vector, result.status)
    return {
        "objective": result.objective_cost, "mip_gap": result.mip_gap,
        "solver_status": result.status, "termination_condition": result.termination_condition,
        "runtime_seconds": result.runtime_seconds, "solver_name": result.solver_name,
        "solver_version": result.solver_version, "rows": problem.num_row,
        "columns": problem.num_col, "binary_count": int(np.sum(problem.integrality)),
    }


def adjustment_positive_parts(plan: RollingPlan) -> tuple[np.ndarray, np.ndarray]:
    return np.maximum(plan.G - plan.Q, 0.0), np.maximum(plan.Q - plan.G, 0.0)
