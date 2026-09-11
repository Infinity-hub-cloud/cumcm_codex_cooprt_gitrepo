from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from .milp import CanonicalMILP
from .parameters import Q1Parameters


class SolverUnavailableError(RuntimeError):
    pass


class SolverTerminationError(RuntimeError):
    pass


@dataclass(frozen=True)
class BackendResult:
    vector: np.ndarray
    objective_cost: float
    solver_name: str
    solver_version: str
    status: str
    termination_condition: str
    mip_gap: float | None
    runtime_seconds: float


class MILPBackend(Protocol):
    def solve(
        self, problem: CanonicalMILP, params: Q1Parameters, log_path: Path
    ) -> BackendResult: ...


class HighsPyBackend:
    """Explicit HiGHS adapter.

    Importing this module does not import or run HiGHS.  `highspy` is loaded only
    when a human invokes the run command.
    """

    name = "highs"

    @staticmethod
    def available() -> bool:
        return importlib.util.find_spec("highspy") is not None

    @classmethod
    def require_available(cls) -> None:
        if not cls.available():
            raise SolverUnavailableError(
                "highspy is not installed. Install it manually in the approved "
                "environment before running Q1; Codex did not install dependencies."
            )

    def solve(
        self, problem: CanonicalMILP, params: Q1Parameters, log_path: Path
    ) -> BackendResult:
        self.require_available()
        import highspy  # type: ignore[import-not-found]

        highs = highspy.Highs()
        highs.setOptionValue("output_flag", True)
        highs.setOptionValue("log_file", str(log_path))
        highs.setOptionValue("time_limit", float(params.time_limit_seconds))
        highs.setOptionValue("mip_rel_gap", float(params.mip_rel_gap))

        lp = highspy.HighsLp()
        lp.num_col_ = problem.num_col
        lp.num_row_ = problem.num_row
        lp.col_cost_ = problem.objective.tolist()
        lp.col_lower_ = problem.col_lower.tolist()
        lp.col_upper_ = problem.col_upper.tolist()
        lp.row_lower_ = problem.row_lower.tolist()
        lp.row_upper_ = problem.row_upper.tolist()
        lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
        lp.a_matrix_.start_ = problem.row_start.tolist()
        lp.a_matrix_.index_ = problem.col_index.tolist()
        lp.a_matrix_.value_ = problem.values.tolist()
        lp.integrality_ = [
            highspy.HighsVarType.kInteger if flag else highspy.HighsVarType.kContinuous
            for flag in problem.integrality
        ]

        model = highspy.HighsModel()
        model.lp_ = lp
        pass_status = highs.passModel(model)
        if pass_status != highspy.HighsStatus.kOk:
            raise SolverTerminationError(f"HiGHS rejected model: {pass_status}")
        run_status = highs.run()
        model_status = highs.getModelStatus()
        status_text = highs.modelStatusToString(model_status)
        if run_status != highspy.HighsStatus.kOk:
            raise SolverTerminationError(f"HiGHS run failed: {run_status}; {status_text}")
        if model_status != highspy.HighsModelStatus.kOptimal:
            raise SolverTerminationError(
                f"Q1 result is not optimal: model_status={status_text}"
            )
        solution = highs.getSolution()
        info = highs.getInfo()
        vector = np.asarray(solution.col_value, dtype=np.float64)
        if vector.shape != (problem.num_col,):
            raise SolverTerminationError("HiGHS did not return a complete primal vector")
        return BackendResult(
            vector=vector,
            objective_cost=float(highs.getObjectiveValue()),
            solver_name="HiGHS",
            solver_version=str(highs.version()),
            status="OPTIMAL",
            termination_condition=status_text,
            mip_gap=float(info.mip_gap),
            runtime_seconds=float(highs.getRunTime()),
        )


def backend_by_name(name: str) -> MILPBackend:
    if name.lower() == "highs":
        return HighsPyBackend()
    raise ValueError(f"unsupported MILP backend: {name}")

