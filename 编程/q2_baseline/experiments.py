from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from q1_baseline.run_manifest import timestamp, write_json
from .candidate_forecast import EXPERIMENTS


ENERGY_COST_FIELDS = (
    "planned_grid_kwh", "charge_kwh", "discharge_kwh", "emergency_kwh", "surplus_kwh",
    "planned_purchase_cost_yuan", "emergency_purchase_cost_yuan", "total_cost_yuan",
)


def compare_costs(runs: dict[str, list[dict]]) -> tuple[list[dict], list[dict], list[dict]]:
    if "baseline" not in runs:
        raise ValueError("original baseline run is required")
    indexed = {}
    for experiment, rows in runs.items():
        for track in ("B0", "B1"):
            selected = [row for row in rows if row["period"] == "formal_output" and row["baseline"].startswith(track)]
            by_date = {row["template_date"]: row for row in selected}
            if not selected or len(by_date) != len(selected):
                raise ValueError("missing or duplicate formal day")
            if not all(np.isfinite(float(row[field])) for row in selected for field in ENERGY_COST_FIELDS):
                raise ValueError("nonfinite comparison metric")
            indexed[experiment, track] = by_date
    reference_dates = set(indexed["baseline", "B1"])
    if any(set(rows) != reference_dates for rows in indexed.values()):
        raise ValueError("experiments have different calendar coverage")
    totals, monthly, daily = [], [], []
    reference_b0 = indexed["baseline", "B0"]
    reference_b1 = indexed["baseline", "B1"]
    for (experiment, track), rows in indexed.items():
        by_month = defaultdict(list)
        matched_b0 = indexed[experiment, "B0"]
        for day in sorted(rows):
            row = rows[day]
            cost = float(row["total_cost_yuan"])
            result = {
                "experiment": experiment, "track": track, "template_date": day,
                **{field: float(row[field]) for field in ENERGY_COST_FIELDS},
                "saving_vs_original_b0_yuan": float(reference_b0[day]["total_cost_yuan"]) - cost,
                "saving_vs_original_b1_yuan": float(reference_b1[day]["total_cost_yuan"]) - cost,
                "saving_vs_matched_b0_yuan": float(matched_b0[day]["total_cost_yuan"]) - cost,
            }
            daily.append(result)
            by_month[day[:7]].append(result)
        fields = ENERGY_COST_FIELDS + (
            "saving_vs_original_b0_yuan", "saving_vs_original_b1_yuan", "saving_vs_matched_b0_yuan",
        )
        model_months = []
        for month, month_rows in sorted(by_month.items()):
            aggregate = {
                "experiment": experiment, "track": track, "month": month,
                **{field: sum(row[field] for row in month_rows) for field in fields},
            }
            model_months.append(aggregate)
            monthly.append(aggregate)
        aggregate = {
            "experiment": experiment, "track": track,
            **{field: sum(row[field] for row in model_months) for field in fields},
        }
        original_cost = sum(float(row["total_cost_yuan"]) for row in reference_b1.values())
        aggregate.update({
            "saving_vs_original_b1_pct": 100 * aggregate["saving_vs_original_b1_yuan"] / original_cost if original_cost else None,
            "improved_months_vs_original_b1": sum(row["saving_vs_original_b1_yuan"] > 1e-5 for row in model_months),
            "worst_month_saving_vs_original_b1_yuan": min(row["saving_vs_original_b1_yuan"] for row in model_months),
            "improved_days_vs_original_b1": sum(float(reference_b1[day]["total_cost_yuan"]) - float(row["total_cost_yuan"]) > 1e-5 for day, row in rows.items()),
            "daily_cost_p95_yuan": float(np.quantile([float(row["total_cost_yuan"]) for row in rows.values()], 0.95)),
            "start_soc_0010_kwh": float(rows[min(rows)]["soc_start_0010_kwh"]),
            "end_soc_0010_next_day_kwh": float(rows[max(rows)]["soc_end_0010_next_day_kwh"]),
            "formal_days": len(rows),
        })
        totals.append(aggregate)
    return totals, monthly, daily


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize_suite(destination: Path) -> None:
    runs = {}
    manifests = {}
    expected_integrity = None
    for experiment in EXPERIMENTS:
        folder = destination / experiment
        manifest = json.loads((folder / "run_manifest.json").read_text(encoding="utf-8"))
        if manifest.get("experiment") != experiment:
            raise ValueError(f"experiment identity mismatch: {experiment}")
        if not manifest.get("assertions_passed") or not manifest.get("export_validation_passed"):
            raise ValueError(f"experiment not validated: {experiment}")
        snapshot = json.loads((folder / "config_snapshot.json").read_text(encoding="utf-8"))
        integrity = (
            manifest["input_sha256"], manifest["data_version"], manifest["output_period"],
            manifest["code_version_or_hashes"], manifest["common_code_hashes"],
            snapshot["parameters"], snapshot["warmup_start"],
        )
        if expected_integrity is not None and integrity != expected_integrity:
            raise ValueError("input/code/physical parameters differ between experiments")
        expected_integrity = integrity
        manifests[experiment] = manifest
        runs[experiment] = _read_csv(folder / "daily_metrics.csv")
    totals, months, days = compare_costs(runs)
    if any(row["formal_days"] != 334 for row in totals):
        raise ValueError("formal comparison requires all 334 days")
    _write_csv(destination / "comparison_summary.csv", totals)
    _write_csv(destination / "comparison_monthly.csv", months)
    _write_csv(destination / "comparison_daily.csv", days)
    prediction_rows, solver_rows = [], []
    for experiment in EXPERIMENTS:
        folder = destination / experiment
        prediction_rows.extend({"experiment": experiment, **row} for row in _read_csv(folder / "prediction_metrics.csv"))
        solver_days = _read_csv(folder / "solver_days.csv")
        solved = [row for row in solver_days if row["status"] != "COLD_START_NO_SOLVE"]
        solver_rows.append({
            "experiment": experiment, "day_count": len(solver_days),
            "optimal_days": sum(row["status"] == "OPTIMAL" for row in solved),
            "cold_start_days": len(solver_days) - len(solved),
            "nonoptimal_days": sum(row["status"] != "OPTIMAL" for row in solved),
            "max_mip_gap": max(float(row["mip_gap"]) for row in solved),
            "solver_seconds": sum(float(row["runtime_seconds"]) for row in solved),
            "warnings_count": manifests[experiment]["warnings_count"],
        })
    _write_csv(destination / "comparison_prediction_metrics.csv", prediction_rows)
    _write_csv(destination / "comparison_solver.csv", solver_rows)
    lines = [
        "# Q2 低复杂度对照：人工运行后的汇总", "",
        "本报告比较同一模板输出期、相同物理参数与R0结算的四组实验；结果待人工审核。",
        "全年数据的基线表现已被观察，本次是固定方案的探索性消融，不能宣称独立留出测试。",
        "预测误差使用原始点预测；风险缓冲单独记录，不冒充负载预测。", "",
        "| 实验 | 储能 | 总费用/元 | 紧急购电费/元 | 相对原B1节省/元 | 相同预测下储能节省/元 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in totals:
        lines.append(
            f"| {row['experiment']} | {row['track']} | {row['total_cost_yuan']:.2f} | "
            f"{row['emergency_purchase_cost_yuan']:.2f} | {row['saving_vs_original_b1_yuan']:.2f} | "
            f"{row['saving_vs_matched_b0_yuan']:.2f} |"
        )
    lines.extend([
        "", "总费用下降不代表每个月均改善；逐月差额、最差月份、日费用P95和首末SOC见comparison文件。",
        "参数固定为最近28天已完成同刻残差、至少7个有效样本、0.8分位数正部。",
        "不自动选择最优组或覆盖官方模板。若进一步调参，应仅用每个决策日之前已完成的数据滚动选择。",
    ])
    (destination / "comparison_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Human-run Q2 fixed low-complexity ablation suite")
    parser.add_argument("--config", type=Path, default=Path("config/q2_baseline.json"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--summarize-only", action="store_true")
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    if args.summarize_only:
        summarize_suite(destination)
        return 0
    from .runner import run_q2, validate_input_only

    validate_input_only(args.config)
    destination.mkdir(parents=True, exist_ok=False)
    manifest = {
        "started_at": timestamp(), "status": "RUNNING", "experiments": list(EXPERIMENTS),
        "completed": [], "selection_policy": "FIXED_ABLATION_EXPLORATORY_NOT_HELD_OUT",
        "final_competition_result": False,
    }
    write_json(destination / "experiment_manifest.json", manifest)
    try:
        for experiment in EXPERIMENTS:
            print(f"Q2 experiment: {experiment}", flush=True)
            run_q2(args.config, destination / experiment, experiment=experiment)
            manifest["completed"].append(experiment)
            write_json(destination / "experiment_manifest.json", manifest)
        summarize_suite(destination)
        manifest.update(status="HUMAN_RUN_UNREVIEWED_CANDIDATES", finished_at=timestamp())
        write_json(destination / "experiment_manifest.json", manifest)
    except Exception as error:
        manifest.update(status="FAILED_OR_INCOMPLETE", error=str(error), finished_at=timestamp())
        write_json(destination / "experiment_manifest.json", manifest)
        raise
    print(f"Q2 comparison package: {destination}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
