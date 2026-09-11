from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

import numpy as np

from .data import ActualInterval, Q2InputData
from .time_axis import decision_time, target_day


COLD_START_SOURCE = "cold_start_no_history"
RECENT_SOURCE = "recent_completed_same_clock"


@dataclass(frozen=True)
class ForecastRow:
    template_date: date
    template_slot: int
    decision_time: datetime
    information_cutoff: datetime
    interval_start: datetime
    interval_end: datetime
    forecast_source: str
    forecast_version: str
    source_interval_start: datetime | None
    source_interval_end: datetime | None
    load_pred_kw: float
    pv_pred_kw: float

    @property
    def is_cold_start(self) -> bool:
        return self.forecast_source == COLD_START_SOURCE


@dataclass(frozen=True)
class ForecastDay:
    template_date: date
    rows: tuple[ForecastRow, ...]

    @property
    def load_pred_kw(self) -> np.ndarray:
        return np.asarray([row.load_pred_kw for row in self.rows], dtype=np.float64)

    @property
    def pv_pred_kw(self) -> np.ndarray:
        return np.asarray([row.pv_pred_kw for row in self.rows], dtype=np.float64)

    @property
    def cold_mask(self) -> np.ndarray:
        return np.asarray([row.is_cold_start for row in self.rows], dtype=bool)

    def assert_causal(self) -> None:
        if len(self.rows) != 144:
            raise AssertionError("forecast day must contain 144 rows")
        for row in self.rows:
            if row.information_cutoff != row.decision_time:
                raise AssertionError("baseline information cutoff must equal decision time")
            if row.source_interval_end is not None and row.source_interval_end > row.decision_time:
                raise AssertionError("FORECAST_LEAKAGE: source interval was not completed")
            if row.source_interval_start is not None:
                source_clock = row.source_interval_start.hour * 60 + row.source_interval_start.minute
                target_clock = row.interval_start.hour * 60 + row.interval_start.minute
                if source_clock != target_clock:
                    raise AssertionError("forecast source is not the same natural clock interval")
            if row.is_cold_start != (row.source_interval_end is None):
                raise AssertionError("cold-start source metadata is inconsistent")


class ForecastProvider(Protocol):
    """Candidate-track forecast interface; no advanced candidate is implemented here."""

    version: str

    def forecast_day(self, template_date: date) -> ForecastDay: ...


class RecentCompletedSameClockPredictor:
    def __init__(self, data: Q2InputData, version: str) -> None:
        self.version = version
        self._by_clock = data.actual_by_clock
        self._ends = {
            minute: tuple(record.interval_end for record in rows)
            for minute, rows in self._by_clock.items()
        }

    def _latest_completed(self, target_start: datetime, cutoff: datetime) -> ActualInterval | None:
        minute = target_start.hour * 60 + target_start.minute
        records = self._by_clock.get(minute, ())
        ends = self._ends.get(minute, ())
        index = bisect_right(ends, cutoff) - 1
        if index < 0:
            return None
        record = records[index]
        if record.interval_end > cutoff:
            raise AssertionError("FORECAST_LEAKAGE: binary search selected future actual")
        return record

    def forecast_day(self, template_date: date) -> ForecastDay:
        cutoff = decision_time(template_date)
        rows: list[ForecastRow] = []
        for target in target_day(template_date):
            source = self._latest_completed(target.interval_start, cutoff)
            rows.append(
                ForecastRow(
                    template_date=template_date,
                    template_slot=target.template_slot,
                    decision_time=cutoff,
                    information_cutoff=cutoff,
                    interval_start=target.interval_start,
                    interval_end=target.interval_end,
                    forecast_source=COLD_START_SOURCE if source is None else RECENT_SOURCE,
                    forecast_version=self.version,
                    source_interval_start=None if source is None else source.interval_start,
                    source_interval_end=None if source is None else source.interval_end,
                    load_pred_kw=0.0 if source is None else source.load_kw,
                    pv_pred_kw=0.0 if source is None else source.pv_kw,
                )
            )
        result = ForecastDay(template_date, tuple(rows))
        result.assert_causal()
        return result
