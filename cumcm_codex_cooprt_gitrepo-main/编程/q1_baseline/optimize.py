from __future__ import annotations

from pathlib import Path

from .baseline import DispatchSolution
from .data_contract import Q1InputData
from .milp import build_q1_milp, dispatch_from_vector
from .parameters import Q1Parameters
from .solver_backend import MILPBackend


def solve_b1_milp(
    data: Q1InputData,
    params: Q1Parameters,
    backend: MILPBackend,
    solver_log_path: Path,
) -> DispatchSolution:
    """Build and solve B1 through the explicitly supplied backend.

    This function is never called by import checks or ordinary unit tests.
    """

    problem = build_q1_milp(data, params)
    result = backend.solve(problem, params, solver_log_path)
    return dispatch_from_vector(
        result.vector,
        problem,
        objective_cost=result.objective_cost,
        solver_name=result.solver_name,
        solver_version=result.solver_version,
        status=result.status,
        termination_condition=result.termination_condition,
        mip_gap=result.mip_gap,
        runtime_seconds=result.runtime_seconds,
    )

