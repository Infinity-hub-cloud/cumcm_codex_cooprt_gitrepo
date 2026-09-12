from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable

import numpy as np

from q2_baseline.config import Q2Parameters

from .price import PriceRecord
from .settlement import Q4ReplayDay


def validate_price_records(records: tuple[PriceRecord, ...]) -> dict[str, object]:
    starts = [row.interval_start for row in records]
    failures: list[str] = []
    if len(records) != 365 * 144:
        failures.append("row_count")
    if len(set(starts)) != len(starts):
        failures.append("duplicate_interval_start")
    if any(row.interval_end - row.interval_start != timedelta(minutes=10) for row in records):
        failures.append("interval_duration")
    if any(not np.isfinite(row.price) or row.price <= 0 for row in records):
        failures.append("price_positive_finite")
    return {"passed": not failures, "failures": failures, "rows": len(records), "unique_interval_starts": len(set(starts))}


def validate_replays(replays: Iterable[Q4ReplayDay], params: Q2Parameters) -> dict[str, object]:
    rows = list(replays)
    failures: list[str] = []
    for replay in rows:
        if len(replay.actual) != 144:
            failures.append(f"shape:{replay.plan.template_date}")
        balance = replay.plan.G + np.asarray([a.pv_kwh for a in replay.actual]) + replay.plan.D + replay.emergency_kwh - np.asarray([a.load_kwh for a in replay.actual]) - replay.plan.C - replay.surplus_kwh
        if float(np.max(np.abs(balance))) > params.feasibility_tolerance:
            failures.append(f"balance:{replay.plan.template_date}")
        if np.any(replay.plan.C > params.charge_energy_max + params.feasibility_tolerance) or np.any(replay.plan.D > params.discharge_energy_max + params.feasibility_tolerance):
            failures.append(f"qmax:{replay.plan.template_date}")
        if np.any((replay.plan.C > params.feasibility_tolerance) & (replay.plan.D > params.feasibility_tolerance)):
            failures.append(f"mutex:{replay.plan.template_date}")
    return {"passed": not failures, "failures": failures, "days": len(rows)}
