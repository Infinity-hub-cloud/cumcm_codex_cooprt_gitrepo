from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from q2_baseline.config import Q2Parameters
from q2_baseline.data import ActualInterval, Q2InputData
from q2_baseline.forecast import ForecastDay, ForecastRow, RECENT_SOURCE
from q2_baseline.planner import DailyPlan
from q2_baseline.replay import ReplayDay, replay_r0
from q2_baseline.time_axis import decision_time, target_day


def synthetic_data(start: date, end: date) -> Q2InputData:
    params = Q2Parameters()
    actual: list[ActualInterval] = []
    by_key: dict[tuple[date, int], ActualInterval] = {}
    by_clock_mut: dict[int, list[ActualInterval]] = {}
    day = start
    while day <= end:
        for target in target_day(day):
            value = float((day - start).days * 1000 + target.template_slot)
            row = ActualInterval(
                day, target.template_slot, target.interval_start, target.interval_end,
                load_kw=value + 10.0, pv_kw=value / 10.0,
                load_kwh=(value + 10.0) * params.delta_t,
                pv_kwh=(value / 10.0) * params.delta_t,
            )
            actual.append(row)
            by_key[(day, target.template_slot)] = row
            by_clock_mut.setdefault(row.natural_clock_minute, []).append(row)
        day += timedelta(days=1)
    by_clock = {key: tuple(sorted(rows, key=lambda item: item.interval_end)) for key, rows in by_clock_mut.items()}
    return Q2InputData(np.ones(144), tuple(sorted(actual, key=lambda item: item.interval_start)), by_key, by_clock)


def normal_forecast(day: date, load_kw: float = 100.0, pv_kw: float = 20.0) -> ForecastDay:
    cutoff = decision_time(day)
    rows = tuple(
        ForecastRow(
            day, target.template_slot, cutoff, cutoff,
            target.interval_start, target.interval_end,
            RECENT_SOURCE, "toy-v1",
            target.interval_start - timedelta(days=2 if target.template_slot == 144 else 1),
            target.interval_end - timedelta(days=2 if target.template_slot == 144 else 1),
            load_kw, pv_kw,
        )
        for target in target_day(day)
    )
    return ForecastDay(day, rows)


def zero_plan(day: date, soc: float = 6000.0, baseline: str = "B1_RECENT_SAME_CLOCK_MILP_R0") -> DailyPlan:
    zeros = np.zeros(144)
    return DailyPlan(
        day, baseline, zeros.copy(), zeros.copy(), zeros.copy(), zeros.copy(), zeros.copy(),
        np.full(145, soc), 0.0, "TOY", "1", "OPTIMAL", "TOY", 0.0, 0.0,
    )


def zero_replay(day: date, emergency_pattern: dict[int, float] | None = None) -> ReplayDay:
    params = Q2Parameters()
    plan = zero_plan(day)
    actual: list[ActualInterval] = []
    for i, target in enumerate(target_day(day)):
        load = 0.0 if emergency_pattern is None else emergency_pattern.get(i, 0.0)
        actual.append(ActualInterval(day, i + 1, target.interval_start, target.interval_end, load / params.delta_t, 0.0, load, 0.0))
    return replay_r0(plan, tuple(actual), np.ones(144), params)
