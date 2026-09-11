from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .baseline import DispatchSolution
from .data_contract import Q1InputData
from .parameters import Q1Parameters


@dataclass(frozen=True)
class AssertionRecord:
    name: str
    passed: bool
    value: Any
    limit: Any
    unit: str


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    assertions: tuple[AssertionRecord, ...]
    metrics: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "assertions": [asdict(item) for item in self.assertions],
            "metrics": self.metrics,
        }


def validate_dispatch(
    solution: DispatchSolution,
    data: Q1InputData,
    params: Q1Parameters,
    *,
    b0_cost: float | None = None,
    require_optimal: bool = False,
) -> ValidationReport:
    data.validate(params)
    T = params.interval_count
    tol = params.feasibility_tolerance
    load = data.load_kwh(params)
    pv = data.pv_kwh(params)
    arrays = (solution.G, solution.C, solution.D, solution.W, solution.z)
    if any(values.shape != (T,) for values in arrays) or solution.S.shape != (T + 1,):
        raise ValueError("dispatch output shapes do not match Q1 contract")

    balance = solution.G + pv + solution.D - load - solution.C - solution.W
    soc_residual = (
        solution.S[1:]
        - solution.S[:-1]
        - params.charge_efficiency * solution.C
        + solution.D / params.discharge_efficiency
    )
    recomputed_objective = float(np.dot(data.price, solution.G))
    aggregate_residual = float(
        np.sum(solution.G)
        + np.sum(pv)
        - np.sum(load)
        - np.sum(solution.W)
        - (1.0 - params.charge_efficiency * params.discharge_efficiency)
        * np.sum(solution.C)
    )
    simultaneous = int(np.count_nonzero((solution.C > tol) & (solution.D > tol)))
    integrality_error = float(np.max(np.abs(solution.z - np.rint(solution.z))))

    assertions: list[AssertionRecord] = []

    def add(name: str, passed: bool, value: Any, limit: Any, unit: str = "") -> None:
        assertions.append(AssertionRecord(name, bool(passed), value, limit, unit))

    all_finite = all(np.all(np.isfinite(x)) for x in (*arrays, solution.S))
    add("all_solution_values_finite", all_finite, all_finite, True)
    add(
        "grid_nonnegative",
        np.min(solution.G) >= -tol,
        float(np.min(solution.G)),
        f">={-tol}",
        "kWh",
    )
    add("charge_nonnegative", np.min(solution.C) >= -tol, float(np.min(solution.C)), f">={-tol}", "kWh")
    add("discharge_nonnegative", np.min(solution.D) >= -tol, float(np.min(solution.D)), f">={-tol}", "kWh")
    add("waste_nonnegative", np.min(solution.W) >= -tol, float(np.min(solution.W)), f">={-tol}", "kWh")
    add("soc_lower_bound", np.min(solution.S) >= params.soc_min - tol, float(np.min(solution.S)), params.soc_min, "kWh")
    add("soc_upper_bound", np.max(solution.S) <= params.soc_max + tol, float(np.max(solution.S)), params.soc_max, "kWh")
    add("charge_exact_physical_limit", np.max(solution.C) <= params.charge_energy_max + tol, float(np.max(solution.C)), params.charge_energy_max, "kWh")
    add("discharge_exact_physical_limit", np.max(solution.D) <= params.discharge_energy_max + tol, float(np.max(solution.D)), params.discharge_energy_max, "kWh")
    add("binary_integrality", integrality_error <= params.integrality_tolerance, integrality_error, params.integrality_tolerance)
    add("no_simultaneous_charge_discharge", simultaneous == 0, simultaneous, 0, "intervals")
    add("energy_balance", np.max(np.abs(balance)) <= tol, float(np.max(np.abs(balance))), tol, "kWh")
    add("soc_recurrence", np.max(np.abs(soc_residual)) <= tol, float(np.max(np.abs(soc_residual))), tol, "kWh")
    add("soc_midnight_initial", abs(solution.S[T - 1] - params.soc_initial) <= tol, float(solution.S[T - 1]), params.soc_initial, "kWh")
    add("soc_midnight_terminal", abs(solution.S[T - 1] - params.soc_terminal) <= tol, float(solution.S[T - 1]), params.soc_terminal, "kWh")
    add("soc_cycle_0010", abs(solution.S[T] - solution.S[0]) <= tol, float(solution.S[T] - solution.S[0]), 0.0, "kWh")
    add("objective_recomputed", abs(recomputed_objective - solution.objective_cost) <= params.objective_tolerance, recomputed_objective - solution.objective_cost, params.objective_tolerance, "yuan")
    add("daily_energy_reconciliation", abs(aggregate_residual) <= params.aggregate_tolerance, aggregate_residual, params.aggregate_tolerance, "kWh")
    if b0_cost is not None:
        add("b1_cost_not_above_b0", solution.objective_cost <= b0_cost + params.objective_tolerance, solution.objective_cost - b0_cost, params.objective_tolerance, "yuan")
    if require_optimal:
        add("solver_status_optimal", solution.status == "OPTIMAL", solution.status, "OPTIMAL")
        add("mip_gap", solution.mip_gap is not None and solution.mip_gap <= params.mip_rel_gap + 1e-12, solution.mip_gap, params.mip_rel_gap)

    metrics = {
        "objective_cost_yuan": recomputed_objective,
        "total_grid_energy_kwh": float(np.sum(solution.G)),
        "total_charge_kwh": float(np.sum(solution.C)),
        "total_discharge_kwh": float(np.sum(solution.D)),
        "total_waste_kwh": float(np.sum(solution.W)),
        "soc_min_kwh": float(np.min(solution.S)),
        "soc_max_kwh": float(np.max(solution.S)),
        "max_balance_residual_kwh": float(np.max(np.abs(balance))),
        "max_soc_residual_kwh": float(np.max(np.abs(soc_residual))),
        "aggregate_residual_kwh": aggregate_residual,
        "simultaneous_violation_count": float(simultaneous),
    }
    return ValidationReport(
        passed=all(item.passed for item in assertions),
        assertions=tuple(assertions),
        metrics=metrics,
    )
