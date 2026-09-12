from __future__ import annotations

from datetime import date, datetime, time, timedelta

import numpy as np

from q2_baseline.forecast import ForecastDay, ForecastRow
from q2_baseline.time_axis import target_day
from q3_baseline.attachment3 import Attachment3Data, PVForecastInterval
from q3_baseline.forecast import PVSelection


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


def attachment3_issues(day: date, issue_minutes: tuple[int, ...] = (0, 360, 720, 1080), method: str = "INTERP") -> Attachment3Data:
    rows: list[PVForecastInterval] = []
    by_issue = {}
    for issue_minute in issue_minutes:
        issue = datetime.combine(day, time.min) + timedelta(minutes=issue_minute)
        mapping = {}
        for i in range(139):
            start = issue + timedelta(hours=1, minutes=10 * i)
            lead = min(24, 1 + i // 6)
            target = issue + timedelta(hours=lead)
            endpoint = lead == 24
            row = PVForecastInterval(
                issue, issue, lead, target, start, start + timedelta(minutes=10),
                50.0 + issue_minute / 60.0, (50.0 + issue_minute / 60.0) / 6,
                "attachment3", "TOY-POINT-v1", method, lead,
                None if method == "ZOH" or endpoint else lead + 1, endpoint,
            )
            rows.append(row)
            mapping[row.physical_key] = row
        by_issue[issue] = mapping
    return Attachment3Data(tuple(rows), method, by_issue)


def pv_selection(day: date, slot: int, start: datetime, decision: datetime | None = None, issue: datetime | None = None, kw: float = 20.0) -> PVSelection:
    decision = decision or start
    issue = issue or (start - timedelta(hours=1))
    lead = max(1, int((start - issue).total_seconds() // 3600))
    target = issue + timedelta(hours=lead)
    return PVSelection(day, slot, start, start + timedelta(minutes=10), decision, issue,
                       lead, target, kw, kw / 6, "attachment3", "TOY-POINT-v1",
                       "ZOH", lead, None, lead == 24 and start == target, "")


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
        [pv_selection(day, slot, target.interval_start, issue=datetime.combine(day, time.min) - timedelta(hours=6)) for slot, target in enumerate(target_day(day), 1)],
    )
