from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .baseline import DispatchSolution, compute_b0
from .config import Q1Config, load_config
from .data_contract import Q1InputData
from .export_templates import export_result1_candidate
from .export_validation import validate_result1_candidate
from .metrics import ValidationReport, validate_dispatch
from .normalized_reader import read_q1_normalized
from .optimize import solve_b1_milp
from .run_manifest import (
    environment_snapshot,
    git_snapshot,
    sha256_file,
    timestamp,
    write_json,
)
from .solver_backend import HighsPyBackend, backend_by_name


REQUIRED_OUTPUTS = (
    "run_manifest.json",
    "config_snapshot.json",
    "dispatch_timeseries.csv",
    "metrics_summary.csv",
    "assertions.json",
    "solver.log",
    "warnings_and_failures.log",
    "result1_candidate.xlsx",
    "export_validation.json",
    "human_feedback.md",
)


def validate_input_only(config_path: str | Path) -> dict[str, Any]:
    """Validate configuration and normalized input without building or solving B1."""

    config = load_config(config_path)
    data = read_q1_normalized(config.normalized_input, config.parameters)
    return {
        "passed": True,
        "model_version": config.model_version,
        "data_version": config.data_version,
        "rows": config.parameters.interval_count,
        "input_path": str(data.source_path),
        "input_sha256": data.source_sha256,
        "time_mapping": {
            "slot_1": data.intervals[0].official_template_label,
            "slot_2": data.intervals[1].official_template_label,
            "slot_143": data.intervals[142].official_template_label,
            "slot_144": data.intervals[143].official_template_label,
        },
    }


def _write_dispatch_csv(
    path: Path,
    config: Q1Config,
    data: Q1InputData,
    b0: DispatchSolution,
    b1: DispatchSolution,
) -> None:
    params = config.parameters
    load = data.load_kwh(params)
    pv = data.pv_kwh(params)
    fieldnames = [
        "template_slot",
        "sample_time_label",
        "official_interval_label",
        "price_yuan_per_kwh",
        "load_kw",
        "pv_kw",
        "load_kwh",
        "pv_kwh",
        "b0_grid_kwh",
        "b0_waste_kwh",
        "b1_grid_kwh",
        "b1_charge_kwh",
        "b1_discharge_kwh",
        "b1_waste_kwh",
        "b1_charge_mode",
        "b1_soc_before_kwh",
        "b1_soc_after_kwh",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for i, interval in enumerate(data.intervals):
            writer.writerow(
                {
                    "template_slot": i + 1,
                    "sample_time_label": interval.sample_time_label,
                    "official_interval_label": interval.official_template_label,
                    "price_yuan_per_kwh": float(data.price[i]),
                    "load_kw": float(data.load_kw[i]),
                    "pv_kw": float(data.pv_kw[i]),
                    "load_kwh": float(load[i]),
                    "pv_kwh": float(pv[i]),
                    "b0_grid_kwh": float(b0.G[i]),
                    "b0_waste_kwh": float(b0.W[i]),
                    "b1_grid_kwh": float(b1.G[i]),
                    "b1_charge_kwh": float(b1.C[i]),
                    "b1_discharge_kwh": float(b1.D[i]),
                    "b1_waste_kwh": float(b1.W[i]),
                    "b1_charge_mode": float(b1.z[i]),
                    "b1_soc_before_kwh": float(b1.S[i]),
                    "b1_soc_after_kwh": float(b1.S[i + 1]),
                }
            )


def _write_metrics_csv(
    path: Path, reports: dict[str, ValidationReport]
) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["baseline", "metric", "value"])
        writer.writeheader()
        for baseline, report in reports.items():
            for metric, value in report.metrics.items():
                writer.writerow(
                    {"baseline": baseline, "metric": metric, "value": value}
                )


def _feedback_template(config: Q1Config, output_dir: Path) -> str:
    return f"""# 人工运行反馈（待填写）

- 当前阶段：5
- 当前状态：待人工运行
- 模型版本：{config.model_version}
- 数据版本：{config.data_version}
- 运行目录：{output_dir}
- 运行人：待回填
- 运行时间：待回填
- 环境与依赖：待回填
- Solver 状态与日志审查：待回填
- 断言是否全部通过：待回填
- 导出回读是否通过：待回填
- 是否接受为后续人工审查候选：待回填
- 警告、失败和人工判断：待回填

注意：本目录结果均为 HUMAN-RUN / UNREVIEWED CANDIDATE，不是最终比赛结果；
不得覆盖官方 result1.xlsx，不得据此自动进入问题2。
"""


def run_q1(config_path: str | Path, output_dir: str | Path) -> Path:
    """Execute the human-authorized B0/B1 run and candidate export.

    This function is reachable only through the explicit ``run`` CLI command.
    It refuses to overwrite an existing run directory or official template.
    """

    config = load_config(config_path)
    data = read_q1_normalized(config.normalized_input, config.parameters)
    backend = backend_by_name(config.solver_name)
    if isinstance(backend, HighsPyBackend):
        backend.require_available()

    destination = Path(output_dir).resolve()
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing run directory: {destination}")
    destination.mkdir(parents=True)
    write_json(destination / "config_snapshot.json", config.snapshot())
    (destination / "warnings_and_failures.log").write_text(
        "No warning recorded before solve.\n", encoding="utf-8"
    )
    (destination / "human_feedback.md").write_text(
        _feedback_template(config, destination), encoding="utf-8"
    )

    manifest: dict[str, Any] = {
        "stage": 5,
        "status": "HUMAN_RUN_UNREVIEWED",
        "final_competition_result": False,
        "created_at": timestamp(),
        "model_version": config.model_version,
        "data_version": config.data_version,
        "input_path": str(data.source_path),
        "input_sha256": data.source_sha256,
        "config_path": str(config.config_path),
        "config_sha256": sha256_file(config.config_path),
        "official_template_path": str(config.official_result1_template),
        "official_template_sha256_before": sha256_file(
            config.official_result1_template
        ),
        "environment": environment_snapshot(),
        "git": git_snapshot(config.config_path.parents[2]),
        "required_outputs": list(REQUIRED_OUTPUTS),
    }
    try:
        b0 = compute_b0(data, config.parameters)
        b0_report = validate_dispatch(b0, data, config.parameters)
        if not b0_report.passed:
            raise RuntimeError("B0 internal validation failed")

        b1 = solve_b1_milp(
            data,
            config.parameters,
            backend,
            destination / "solver.log",
        )
        b1_report = validate_dispatch(
            b1,
            data,
            config.parameters,
            b0_cost=b0.objective_cost,
            require_optimal=True,
        )
        reports = {"B0_NO_STORAGE": b0_report, "B1_Q1_MILP": b1_report}
        write_json(
            destination / "assertions.json",
            {name: report.to_dict() for name, report in reports.items()},
        )
        _write_dispatch_csv(destination / "dispatch_timeseries.csv", config, data, b0, b1)
        _write_metrics_csv(destination / "metrics_summary.csv", reports)
        if not b1_report.passed:
            raise RuntimeError("B1 assertions failed; candidate export blocked")

        export_record = export_result1_candidate(
            config.official_result1_template,
            destination / "result1_candidate.xlsx",
            b1,
            config.parameters,
        )
        export_validation = validate_result1_candidate(
            config.official_result1_template,
            destination / "result1_candidate.xlsx",
            b1,
            config.parameters,
        )
        write_json(destination / "export_validation.json", export_validation)
        if not export_validation["passed"]:
            raise RuntimeError("candidate workbook reread validation failed")

        manifest.update(
            {
                "run_completed_at": timestamp(),
                "status": "HUMAN_RUN_UNREVIEWED_CANDIDATE",
                "solver": {
                    "name": b1.solver_name,
                    "version": b1.solver_version,
                    "status": b1.status,
                    "termination_condition": b1.termination_condition,
                    "mip_gap": b1.mip_gap,
                    "runtime_seconds": b1.runtime_seconds,
                },
                "b0_objective_cost_yuan": b0.objective_cost,
                "b1_objective_cost_yuan": b1.objective_cost,
                "assertions_passed": True,
                "export_validation_passed": True,
                "export": export_record,
                "official_template_sha256_after": sha256_file(
                    config.official_result1_template
                ),
            }
        )
        write_json(destination / "run_manifest.json", manifest)
        return destination
    except Exception as exc:
        manifest.update(
            {
                "run_completed_at": timestamp(),
                "status": "FAILED_OR_INCOMPLETE",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        write_json(destination / "run_manifest.json", manifest)
        with (destination / "warnings_and_failures.log").open(
            "a", encoding="utf-8"
        ) as handle:
            handle.write(f"{timestamp()} {type(exc).__name__}: {exc}\n")
        raise
