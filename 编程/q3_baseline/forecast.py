from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, time

import numpy as np

from q2_baseline.forecast import ForecastDay
from q2_baseline.time_axis import target_day

from .attachment3 import Attachment3Data, PVForecastInterval


ATTACHMENT3_SOURCE = "attachment3"
FALLBACK_Q2_PV_SOURCE = "fallback_q2_pv"


@dataclass(frozen=True)
class PVSelection:
    template_date: date
    template_slot: int
    interval_start: datetime
    interval_end: datetime
    decision_time: datetime
    issue_datetime: datetime | None
    forecast_kw: float
    forecast_source: str

    def assert_causal(self) -> None:
        if self.issue_datetime is not None and self.issue_datetime > self.decision_time:
            raise AssertionError("Q3_FORECAST_LEAKAGE: issue_datetime > decision_time")
        if self.forecast_kw < 0 or not np.isfinite(self.forecast_kw):
            raise AssertionError("Q3 PV forecast must be finite and nonnegative")
        if self.forecast_source == FALLBACK_Q2_PV_SOURCE and self.issue_datetime is not None:
            raise AssertionError("fallback_q2_pv cannot carry an attachment3 issue time")


@dataclass(frozen=True)
class FrozenPlanningDay:
    q2_forecast: ForecastDay
    load_plan_kw: np.ndarray
    initial_pv: tuple[PVSelection, ...]

    @property
    def initial_pv_kw(self) -> np.ndarray:
        return np.asarray([row.forecast_kw for row in self.initial_pv], dtype=np.float64)

    def assert_valid(self) -> None:
        self.q2_forecast.assert_causal()
        if self.load_plan_kw.shape != (144,) or len(self.initial_pv) != 144:
            raise AssertionError("Q3 frozen planning day must contain 144 intervals")
        expected = target_day(self.q2_forecast.template_date)
        for target, selected in zip(expected, self.initial_pv, strict=True):
            selected.assert_causal()
            if (selected.interval_start, selected.interval_end) != (
                target.interval_start,
                target.interval_end,
            ):
                raise AssertionError("Q3 PV selection is not matched by physical interval")
        if any(row.forecast_source != ATTACHMENT3_SOURCE for row in self.initial_pv[:143]):
            raise AssertionError("initial slots 1..143 must use attachment3")
        if self.initial_pv[-1].forecast_source != FALLBACK_Q2_PV_SOURCE:
            raise AssertionError("initial slot144 must use fallback_q2_pv")

    def as_q2_forecast_for_initial_solve(self) -> ForecastDay:
        rows = tuple(
            replace(row, pv_pred_kw=float(pv.forecast_kw))
            for row, pv in zip(self.q2_forecast.rows, self.initial_pv, strict=True)
        )
        return ForecastDay(self.q2_forecast.template_date, rows)


def initial_planning_day(
    template_date: date,
    q2_frozen_forecast: ForecastDay,
    attachment3: Attachment3Data,
) -> FrozenPlanningDay:
    if q2_frozen_forecast.template_date != template_date:
        raise ValueError("Q2 frozen forecast date mismatch")
    decision = datetime.combine(template_date, time.min)
    issue = attachment3.issue(decision)
    targets = target_day(template_date)
    selected: list[PVSelection] = []
    direct_matches = 0
    for target, q2_row in zip(targets, q2_frozen_forecast.rows, strict=True):
        matched = issue.get((target.interval_start, target.interval_end))
        if matched is None:
            selected.append(
                PVSelection(
                    template_date,
                    target.template_slot,
                    target.interval_start,
                    target.interval_end,
                    decision,
                    None,
                    q2_row.pv_pred_kw,
                    FALLBACK_Q2_PV_SOURCE,
                )
            )
        else:
            direct_matches += 1
            selected.append(_selection(template_date, target.template_slot, decision, matched))
    if direct_matches != 143:
        raise AssertionError(f"Q3 00:00/template direct overlap must be 143, got {direct_matches}")
    result = FrozenPlanningDay(
        q2_frozen_forecast,
        q2_frozen_forecast.planning_load_kw.copy(),
        tuple(selected),
    )
    result.assert_valid()
    return result


def _selection(
    template_date: date,
    template_slot: int,
    decision: datetime,
    row: PVForecastInterval,
) -> PVSelection:
    result = PVSelection(
        template_date,
        template_slot,
        row.interval_start,
        row.interval_end,
        decision,
        row.issue_datetime,
        row.forecast_kw,
        ATTACHMENT3_SOURCE,
    )
    result.assert_causal()
    return result


def pv_for_unexecuted(
    frozen: FrozenPlanningDay,
    attachment3: Attachment3Data,
    decision: datetime,
    allowed_issue_minutes: tuple[int, ...],
) -> tuple[PVSelection, ...]:
    rows: list[PVSelection] = []
    for target, fallback in zip(target_day(frozen.q2_forecast.template_date), frozen.initial_pv, strict=True):
        if target.interval_start < decision:
            continue
        matched = attachment3.latest_covering(
            decision,
            (target.interval_start, target.interval_end),
            allowed_issue_minutes,
        )
        if matched is None:
            rows.append(
                PVSelection(
                    target.template_date,
                    target.template_slot,
                    target.interval_start,
                    target.interval_end,
                    decision,
                    None,
                    fallback.forecast_kw,
                    fallback.forecast_source,
                )
            )
        else:
            rows.append(_selection(target.template_date, target.template_slot, decision, matched))
    return tuple(rows)


def assert_load_frozen(frozen: FrozenPlanningDay, candidate: np.ndarray) -> None:
    if not np.array_equal(frozen.load_plan_kw, candidate):
        raise AssertionError("Q3_LOAD_FORECAST_MUTATION: 00:00 weekday_buffer must remain frozen")
