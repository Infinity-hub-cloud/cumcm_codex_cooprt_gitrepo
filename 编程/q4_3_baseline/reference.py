from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path

import numpy as np

from q3_baseline.state_machine import ExecutedInterval

from .integrity import sha256_file


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def read_frozen_q3_dispatch(run_dir: Path) -> tuple[ExecutedInterval, ...]:
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("model_version") != "M3-Q3-POINT-MODEL-B-v2.0" or manifest.get("track") != "Q3_ROLLING_INTERP":
        raise RuntimeError("Q4_3_FROZEN_Q3_IDENTITY_HARD_FAIL")
    rows: list[ExecutedInterval] = []
    with (run_dir / "dispatch_timeseries.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                ExecutedInterval(
                    raw["template_date"], int(raw["template_slot"]), _dt(raw["interval_start"]), _dt(raw["interval_end"]),
                    float(raw["grid_plan_kwh"]), float(raw["grid_final_kwh"]), float(raw["charge_bus_kwh"]),
                    float(raw["discharge_bus_kwh"]), float(raw["grid_emergency_kwh"]), float(raw["spill_kwh"]),
                    float(raw["soc_before"]), float(raw["soc_after"]), float(raw["price"]), raw["pv_forecast_source"],
                    _dt(raw["issue_datetime"]) if raw["issue_datetime"] else None,
                    float(raw["load_actual_kwh"]), float(raw["pv_actual_kwh"]), float(raw["planned_purchase_cost"]),
                    float(raw["fulfilled_normal_purchase_cost"]), float(raw["cancelled_purchase_principal"]),
                    float(raw["downward_adjustment_penalty"]), float(raw["upward_adjustment_cost"]),
                    float(raw["regular_purchase_cost"]), float(raw["emergency_purchase_cost"]), float(raw["total_cost"]),
                    raw["cost_semantics"],
                )
            )
    if len(rows) != 365 * 144:
        raise RuntimeError("frozen Q3 dispatch state chain is incomplete")
    return tuple(rows)


def feb1_initial_soc(rows: tuple[ExecutedInterval, ...], dispatch_path: Path) -> tuple[float, dict[str, object]]:
    matches = [row for row in rows if row.template_date == "2025-02-01" and row.template_slot == 1]
    if len(matches) != 1:
        raise RuntimeError("BLOCKER-Q4-3-FEB1-SOC: frozen Q3 state chain is ambiguous")
    return matches[0].soc_before, {
        "source": str(dispatch_path.resolve()),
        "sha256": sha256_file(dispatch_path),
        "template_date": "2025-02-01",
        "template_slot": 1,
        "physical_time": matches[0].interval_start.isoformat(),
    }


class PlanVectors:
    def __init__(self, day: date, rows: list[ExecutedInterval]):
        ordered = sorted(rows, key=lambda row: row.template_slot)
        if [row.template_slot for row in ordered] != list(range(1, 145)):
            raise ValueError(f"incomplete frozen plan for {day}")
        self.template_date = day
        self.G = np.asarray([row.G for row in ordered], dtype=float)
        self.Q = np.asarray([row.Q for row in ordered], dtype=float)


def plans_from_executed(rows: tuple[ExecutedInterval, ...], start: date, end: date) -> dict[date, PlanVectors]:
    output: dict[date, PlanVectors] = {}
    day = start
    while day <= end:
        subset = [row for row in rows if row.template_date == day.isoformat()]
        output[day] = PlanVectors(day, subset)
        day = date.fromordinal(day.toordinal() + 1)
    return output

