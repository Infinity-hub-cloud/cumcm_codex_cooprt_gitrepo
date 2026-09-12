from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

from q2_baseline.data import ActualInterval, Q2InputData
from q2_baseline.forecast import ForecastDay, ForecastRow
from q2_baseline.planner import DailyPlan


class FrozenQ2Reference:
    """Read-only adapter for the accepted Q2 weekday_buffer dispatch chain."""

    def __init__(self, dispatch_path: Path, data: Q2InputData):
        grouped: dict[date, list[dict[str, str]]] = defaultdict(list)
        with dispatch_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("baseline") == "B1_WEEKDAY_BUFFER_MILP_R0":
                    grouped[date.fromisoformat(row["template_date"])].append(row)
        if set(grouped) != {date(2025, 1, 1) + timedelta(days=i) for i in range(365)}:
            raise ValueError("frozen Q2 reference must contain all 365 B1 template days")
        self.plans: dict[date, DailyPlan] = {}
        self.rows = grouped
        for day, rows in grouped.items():
            rows.sort(key=lambda row: int(row["template_slot"]))
            if len(rows) != 144:
                raise ValueError(f"reference day {day} does not contain 144 rows")
            self.plans[day] = DailyPlan(
                template_date=day, baseline="Q2_FROZEN_REFERENCE",
                G=np.asarray([float(row["grid_plan_kwh"]) for row in rows]),
                C=np.asarray([float(row["charge_bus_kwh"]) for row in rows]),
                D=np.asarray([float(row["discharge_bus_kwh"]) for row in rows]),
                W_pred=np.asarray([float(row["spill_kwh"]) for row in rows]),
                z=np.asarray([float(row["charge_mode"]) for row in rows]),
                S=np.asarray([float(rows[0]["soc_before_kwh"])] + [float(row["soc_after_kwh"]) for row in rows]),
                objective_cost=0.0, solver_name="FROZEN_Q2", solver_version="1.0",
                status="REFERENCE_ONLY_NO_SOLVE", termination_condition="FROZEN_Q2",
                mip_gap=None, runtime_seconds=0.0,
            )
        self.data = data

    def plan(self, day: date) -> DailyPlan:
        return self.plans[day]

    def actual(self, day: date) -> tuple[ActualInterval, ...]:
        return tuple(self.data.actual_by_template_key[(day, slot)] for slot in range(1, 145))

    def forecast(self, day: date) -> ForecastDay:
        rows = self.rows[day]
        material = []
        for raw in rows:
            material.append(ForecastRow(
                template_date=day, template_slot=int(raw["template_slot"]),
                decision_time=datetime.fromisoformat(raw["decision_time"]),
                information_cutoff=datetime.fromisoformat(raw["information_cutoff"]),
                interval_start=datetime.fromisoformat(raw["interval_start"]),
                interval_end=datetime.fromisoformat(raw["interval_end"]),
                forecast_source="frozen_q2_weekday_buffer", forecast_version="q2-weekday_buffer-v1.0",
                source_interval_start=None, source_interval_end=datetime.fromisoformat(raw["decision_time"]),
                load_pred_kw=float(raw["load_pred_kwh"]) * 6,
                pv_pred_kw=float(raw["pv_pred_kwh"]) * 6,
                risk_buffer_kw=float(raw["risk_buffer_kwh"]) * 6,
                buffer_sample_count=0,
            ))
        return ForecastDay(day, tuple(material))

    def initial_soc_feb1(self) -> float:
        return float(self.plans[date(2025, 1, 31)].S[-1])
