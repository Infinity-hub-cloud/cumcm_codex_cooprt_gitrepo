from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .parameters import Q1Parameters


@dataclass(frozen=True)
class Q1Config:
    config_path: Path
    model_version: str
    data_version: str
    normalized_input: Path
    official_result1_template: Path
    parameters: Q1Parameters
    solver_name: str

    def snapshot(self) -> dict[str, Any]:
        return {
            "model_version": self.model_version,
            "data_version": self.data_version,
            "normalized_input": str(self.normalized_input),
            "official_result1_template": str(self.official_result1_template),
            "solver_name": self.solver_name,
            "parameters": self.parameters.to_dict(),
        }


def _resolve(base: Path, raw: str) -> Path:
    path = Path(raw)
    return (base / path).resolve() if not path.is_absolute() else path.resolve()


def load_config(path: str | Path) -> Q1Config:
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    base = config_path.parent
    params = Q1Parameters.from_mapping(payload["parameters"])
    solver_name = str(payload.get("solver_name", "highs")).lower()
    if solver_name != "highs":
        raise ValueError("only the explicit HiGHS MILP adapter is implemented")
    return Q1Config(
        config_path=config_path,
        model_version=str(payload["model_version"]),
        data_version=str(payload["data_version"]),
        normalized_input=_resolve(base, payload["normalized_input"]),
        official_result1_template=_resolve(
            base, payload["official_result1_template"]
        ),
        parameters=params,
        solver_name=solver_name,
    )

