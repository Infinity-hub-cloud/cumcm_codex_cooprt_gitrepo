from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, time
import numpy as np

from q2_baseline.forecast import ForecastDay, ForecastRow
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
    lead_hour: int | None
    target_time: datetime | None
    forecast_kw: float
    forecast_kwh: float
    forecast_source: str
    forecast_version: str
    mapping_method: str
    interpolation_left_lead: int | None
    interpolation_right_lead: int | None
    endpoint_hold: bool
    fallback_reason: str

    @property
    def physical_key(self) -> tuple[datetime, datetime]:
        return self.interval_start, self.interval_end

    def assert_causal(self) -> None:
        if self.issue_datetime is not None and self.issue_datetime > self.decision_time:
            raise AssertionError("Q3_FORECAST_LEAKAGE: issue_datetime > decision_time")
        if self.forecast_kw < 0 or not np.isfinite(self.forecast_kw):
            raise AssertionError("Q3 PV forecast must be finite and nonnegative")
        if abs(self.forecast_kwh - self.forecast_kw / 6) > 1e-7:
            raise AssertionError("Q3 interval-start power conversion failed")
        if self.forecast_source == FALLBACK_Q2_PV_SOURCE:
            if self.issue_datetime is not None or not self.fallback_reason:
                raise AssertionError("fallback must have no Attachment3 issue and a reason")
        elif self.issue_datetime is None:
            raise AssertionError("Attachment3 selection requires issue metadata")

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
            raise AssertionError("Q3 frozen day must contain 144 intervals")
        for target, selected in zip(target_day(self.q2_forecast.template_date), self.initial_pv, strict=True):
            selected.assert_causal()
            if selected.physical_key != (target.interval_start, target.interval_end):
                raise AssertionError("Q3 selection is not physically keyed")

    def as_q2_forecast_for_initial_solve(self) -> ForecastDay:
        rows = tuple(replace(row, pv_pred_kw=float(pv.forecast_kw)) for row, pv in zip(self.q2_forecast.rows, self.initial_pv, strict=True))
        return ForecastDay(self.q2_forecast.template_date, rows)

def _fallback(template_date: date, slot: int, decision: datetime, q2: ForecastRow, reason: str) -> PVSelection:
    return PVSelection(template_date, slot, q2.interval_start, q2.interval_end, decision, None, None, None,
                       float(q2.pv_pred_kw), float(q2.pv_pred_kw) / 6, FALLBACK_Q2_PV_SOURCE,
                       q2.forecast_version, "Q2_FALLBACK", None, None, False, reason)

def _selection(template_date: date, slot: int, decision: datetime, row: PVForecastInterval) -> PVSelection:
    result = PVSelection(template_date, slot, row.interval_start, row.interval_end, decision,
                         row.issue_datetime, row.lead_hour, row.target_time, row.forecast_kw,
                         row.forecast_kwh, row.source, row.forecast_version, row.mapping_method,
                         row.interpolation_left_lead, row.interpolation_right_lead,
                         row.endpoint_hold, "")
    result.assert_causal()
    return result

def _choose(template_date: date, slot: int, decision: datetime, q2: ForecastRow,
            attachment3: Attachment3Data, allowed: tuple[int, ...]) -> PVSelection:
    key = q2.interval_start, q2.interval_end
    matched = attachment3.latest_covering(decision, key, allowed)
    return _selection(template_date, slot, decision, matched) if matched else _fallback(
        template_date, slot, decision, q2, "no_causally_available_allowed_issue_with_complete_support")

def initial_planning_day(template_date: date, q2_frozen_forecast: ForecastDay,
                         attachment3: Attachment3Data, allowed_issue_minutes: tuple[int, ...]) -> FrozenPlanningDay:
    if q2_frozen_forecast.template_date != template_date:
        raise ValueError("Q2 frozen forecast date mismatch")
    decision = datetime.combine(template_date, time.min)
    selected = tuple(_choose(template_date, row.template_slot, decision, row, attachment3, allowed_issue_minutes)
                     for row in q2_frozen_forecast.rows)
    result = FrozenPlanningDay(q2_frozen_forecast, q2_frozen_forecast.planning_load_kw.copy(), selected)
    result.assert_valid()
    return result

def pv_for_unexecuted(frozen: FrozenPlanningDay, attachment3: Attachment3Data,
                      decision: datetime, allowed_issue_minutes: tuple[int, ...]) -> tuple[PVSelection, ...]:
    rows = []
    for q2 in frozen.q2_forecast.rows:
        if q2.interval_start >= decision:
            rows.append(_choose(frozen.q2_forecast.template_date, q2.template_slot, decision, q2, attachment3, allowed_issue_minutes))
    return tuple(rows)

def assert_load_frozen(frozen: FrozenPlanningDay, candidate: np.ndarray) -> None:
    if not np.array_equal(frozen.load_plan_kw, candidate):
        raise AssertionError("Q3_LOAD_FORECAST_MUTATION: frozen net-load-buffer planning load changed")
