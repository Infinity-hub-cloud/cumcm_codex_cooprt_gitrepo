from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

import numpy as np

from .config import Q2Parameters
from .time_axis import TEN_MINUTES, date_range, target_interval


@dataclass(frozen=True)
class ActualInterval:
    source_date: date
    template_slot: int
    interval_start: datetime
    interval_end: datetime
    load_kw: float
    pv_kw: float
    load_kwh: float
    pv_kwh: float

    @property
    def natural_clock_minute(self) -> int:
        return self.interval_start.hour * 60 + self.interval_start.minute


@dataclass(frozen=True)
class Q2InputData:
    price: np.ndarray
    actual: tuple[ActualInterval, ...]
    actual_by_template_key: dict[tuple[date, int], ActualInterval]
    actual_by_clock: dict[int, tuple[ActualInterval, ...]]

    def validate(self, params: Q2Parameters) -> None:
        if self.price.shape != (params.interval_count,):
            raise ValueError("price input must contain 144 rows")
        if not np.all(np.isfinite(self.price)) or np.any(self.price < 0):
            raise ValueError("price input contains invalid values")
        if len(self.actual) != 365 * params.interval_count:
            raise ValueError("2025 actual input must contain exactly 365*144 rows")
        expected_keys = {
            (day, slot)
            for day in date_range(date(2025, 1, 1), date(2025, 12, 31))
            for slot in range(1, 145)
        }
        if set(self.actual_by_template_key) != expected_keys:
            missing = len(expected_keys - set(self.actual_by_template_key))
            extra = len(set(self.actual_by_template_key) - expected_keys)
            raise ValueError(f"actual template key coverage failed: missing={missing}, extra={extra}")
        for record in self.actual:
            expected = target_interval(record.source_date, record.template_slot)
            if (record.interval_start, record.interval_end) != (
                expected.interval_start,
                expected.interval_end,
            ):
                raise ValueError("actual physical timestamp disagrees with template mapping")
            if record.interval_end - record.interval_start != TEN_MINUTES:
                raise ValueError("actual interval is not ten minutes")
            if min(record.load_kw, record.pv_kw, record.load_kwh, record.pv_kwh) < 0:
                raise ValueError("actual input contains negative energy or power")
            if abs(record.load_kwh - record.load_kw * params.delta_t) > params.input_energy_rounding_tolerance:
                raise ValueError("actual load kW/kWh unit conversion is inconsistent")
            if abs(record.pv_kwh - record.pv_kw * params.delta_t) > params.input_energy_rounding_tolerance:
                raise ValueError("actual PV kW/kWh unit conversion is inconsistent")


def _dt(day_text: str, minute_text: str) -> datetime:
    return datetime.combine(date.fromisoformat(day_text), time.min) + TEN_MINUTES * (
        int(minute_text) // 10
    )


def read_q2_inputs(price_path: Path, actual_path: Path, params: Q2Parameters) -> Q2InputData:
    prices: list[float] = []
    with price_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            prices.append(float(row["price_yuan_per_kwh"]))

    actual: list[ActualInterval] = []
    by_key: dict[tuple[date, int], ActualInterval] = {}
    by_clock_mut: dict[int, list[ActualInterval]] = {}
    with actual_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            source_date = date.fromisoformat(row["source_date"])
            slot = int(row["interval_index"])
            start = _dt(row["interval_start_date"], row["interval_start_minute"])
            end = _dt(row["interval_end_date"], row["interval_end_minute"])
            record = ActualInterval(
                source_date=source_date,
                template_slot=slot,
                interval_start=start,
                interval_end=end,
                load_kw=float(row["load_kw"]),
                pv_kw=float(row["pv_actual_kw"]),
                load_kwh=float(row["load_kwh"]),
                pv_kwh=float(row["pv_actual_kwh"]),
            )
            if (source_date, slot) in by_key:
                raise ValueError(f"duplicate actual row: {source_date} slot {slot}")
            actual.append(record)
            by_key[(source_date, slot)] = record
            by_clock_mut.setdefault(record.natural_clock_minute, []).append(record)

    actual.sort(key=lambda item: (item.interval_start, item.interval_end))
    by_clock = {
        minute: tuple(sorted(rows, key=lambda item: item.interval_end))
        for minute, rows in by_clock_mut.items()
    }
    data = Q2InputData(np.asarray(prices, dtype=np.float64), tuple(actual), by_key, by_clock)
    data.validate(params)
    return data
