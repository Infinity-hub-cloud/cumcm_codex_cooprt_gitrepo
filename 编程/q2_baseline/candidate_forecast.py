from __future__ import annotations

from bisect import bisect_right
from dataclasses import replace
from datetime import date, datetime, timedelta

import numpy as np

from .data import ActualInterval, Q2InputData
from .forecast import COLD_START_SOURCE, ForecastDay, ForecastRow
from .time_axis import decision_time, target_day


EXPERIMENTS = ("baseline", "weekday", "recent_buffer", "weekday_buffer")
BUFFER_HISTORY_DAYS = 28
BUFFER_MIN_SAMPLES = 7
BUFFER_QUANTILE = 0.8


class CandidatePredictor:
    def __init__(self, data: Q2InputData, load_strategy: str, use_buffer: bool) -> None:
        if load_strategy not in ("recent", "weekday"):
            raise ValueError("unsupported load strategy")
        self.load_strategy = load_strategy
        self.use_buffer = use_buffer
        self.version = f"{load_strategy}-load_recent-pv_buffer-{int(use_buffer)}-v1.0"
        self._by_clock = data.actual_by_clock
        self._ends = {
            minute: tuple(record.interval_end for record in records)
            for minute, records in self._by_clock.items()
        }

    def _completed(self, target_start: datetime, cutoff: datetime) -> tuple[ActualInterval, ...]:
        minute = target_start.hour * 60 + target_start.minute
        records = self._by_clock.get(minute, ())
        count = bisect_right(self._ends.get(minute, ()), cutoff)
        return records[:count]

    def _sources(self, target_start: datetime, cutoff: datetime):
        records = self._completed(target_start, cutoff)
        if not records:
            return None, None
        recent = records[-1]
        load_source = recent
        if self.load_strategy == "weekday":
            load_source = next(
                (record for record in reversed(records)
                 if record.interval_start.weekday() == target_start.weekday()),
                recent,
            )
        return load_source, recent

    def _buffer(self, target_start: datetime, cutoff: datetime):
        residuals: list[float] = []
        sources: list[ActualInterval] = []
        for actual in self._completed(target_start, cutoff):
            if actual.interval_end <= cutoff - timedelta(days=BUFFER_HISTORY_DAYS):
                continue
            historical_cutoff = decision_time(actual.source_date)
            load_source, pv_source = self._sources(actual.interval_start, historical_cutoff)
            if load_source is None:
                continue
            residuals.append(
                (actual.load_kw - actual.pv_kw) - (load_source.load_kw - pv_source.pv_kw)
            )
            sources.append(actual)
        margin = 0.0
        if len(residuals) >= BUFFER_MIN_SAMPLES:
            margin = max(0.0, float(np.quantile(residuals, BUFFER_QUANTILE)))
        return (
            margin, len(residuals),
            None if not sources else sources[0].interval_start,
            None if not sources else sources[-1].interval_end,
        )

    def forecast_day(self, template_date: date) -> ForecastDay:
        cutoff = decision_time(template_date)
        rows: list[ForecastRow] = []
        for target in target_day(template_date):
            load_source, pv_source = self._sources(target.interval_start, cutoff)
            row = ForecastRow(
                template_date=template_date,
                template_slot=target.template_slot,
                decision_time=cutoff,
                information_cutoff=cutoff,
                interval_start=target.interval_start,
                interval_end=target.interval_end,
                forecast_source=COLD_START_SOURCE if load_source is None else self.version,
                forecast_version=self.version,
                source_interval_start=None if pv_source is None else pv_source.interval_start,
                source_interval_end=None if pv_source is None else pv_source.interval_end,
                load_pred_kw=0.0 if load_source is None else load_source.load_kw,
                pv_pred_kw=0.0 if pv_source is None else pv_source.pv_kw,
                load_source_interval_start=None if load_source is None else load_source.interval_start,
                load_source_interval_end=None if load_source is None else load_source.interval_end,
            )
            if self.use_buffer and load_source is not None:
                margin, count, first, last = self._buffer(target.interval_start, cutoff)
                row = replace(
                    row, risk_buffer_kw=margin, buffer_sample_count=count,
                    buffer_source_start=first, buffer_source_end=last,
                )
            rows.append(row)
        result = ForecastDay(template_date, tuple(rows))
        result.assert_causal()
        return result
