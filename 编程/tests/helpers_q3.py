from __future__ import annotations

from datetime import date, datetime, time, timedelta

import numpy as np

from q2_baseline.forecast import ForecastDay, ForecastRow
from q2_baseline.time_axis import target_day
from q3_baseline.attachment3 import Attachment3Data, PVForecastInterval


def q2_frozen_day(day: date, load_kw: float = 100.0, pv_kw: float = 20.0) -> ForecastDay:
    decision = datetime.combine(day, time.min)
    rows = []
    for target in target_day(day):
        source_start = target.interval_start - timedelta(days=7)
        source_end = target.interval_end - timedelta(days=7)
        rows.append(
            ForecastRow(
                template_date=day,
                template_slot=target.template_slot,
                decision_time=decision,
                information_cutoff=decision,
                interval_start=target.interval_start,
                interval_end=target.interval_end,
                forecast_source="weekday-load_recent-pv_buffer-1-v1.0",
                forecast_version="q2-weekday_buffer-v1.0",
                source_interval_start=source_start,
                source_interval_end=source_end,
                load_pred_kw=load_kw,
                pv_pred_kw=pv_kw,
                load_source_interval_start=source_start,
                load_source_interval_end=source_end,
                risk_buffer_kw=10.0,
                buffer_sample_count=7,
                buffer_source_start=source_start - timedelta(days=28),
                buffer_source_end=source_end,
            )
        )
    result = ForecastDay(day, tuple(rows))
    result.assert_causal()
    return result


def attachment3_issues(day: date, issue_minutes: tuple[int, ...] = (0, 360, 720, 1080)) -> Attachment3Data:
    rows: list[PVForecastInterval] = []
    by_issue = {}
    for issue_minute in issue_minutes:
        issue = datetime.combine(day, time.min) + timedelta(minutes=issue_minute)
        mapping = {}
        for i in range(144):
            start = issue + timedelta(minutes=10 * i)
            row = PVForecastInterval(
                issue,
                start,
                start + timedelta(minutes=10),
                50.0 + issue_minute / 60.0,
                i // 6 + 1,
                start.hour * 6 + start.minute // 10 + 1,
            )
            rows.append(row)
            mapping[row.physical_key] = row
        by_issue[issue] = mapping
    return Attachment3Data(tuple(rows), by_issue)


def zero_vector_plan(day: date):
    from q3_baseline.planner import RollingPlan

    zeros = np.zeros(144)
    return RollingPlan(
        day,
        np.full(144, 10.0),
        np.full(144, 10.0),
        zeros.copy(),
        zeros.copy(),
        zeros.copy(),
        zeros.copy(),
        np.full(145, 6000.0),
        ["attachment3"] * 144,
        [datetime.combine(day, time.min)] * 144,
        ["TOY"] * 144,
    )
