from __future__ import annotations

import csv
from bisect import bisect_right
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

import numpy as np

from .config import Q4Parameters, VISIBILITY_RULE

TEN_MINUTES = timedelta(minutes=10)


@dataclass(frozen=True)
class PriceRecord:
    source_date: date
    interval_index: int
    interval_start: datetime
    interval_end: datetime
    price: float


class CausalPriceView:
    def __init__(self, records: Iterable[PriceRecord], decision_time: datetime, visibility_rule: str = VISIBILITY_RULE, *, records_are_sorted_visible: bool = False):
        if visibility_rule != VISIBILITY_RULE:
            raise ValueError("historical interval-end rule is not a production Q4-2 branch")
        self.decision_time = decision_time
        self.visibility_rule = visibility_rule
        material = tuple(records)
        self._records = material if records_are_sorted_visible else tuple(sorted((r for r in material if r.interval_start <= decision_time), key=lambda r: r.interval_start))
        if records_are_sorted_visible and any(r.interval_start > decision_time for r in self._records):
            raise AssertionError("CausalPriceView received future records")
        self._by_start = {r.interval_start: r for r in self._records}

    @property
    def history_last_visible_time(self) -> datetime | None:
        return self._records[-1].interval_start if self._records else None

    def get(self, timestamp: datetime) -> float | None:
        if timestamp > self.decision_time:
            raise RuntimeError("Q4_CAUSAL_PRICE_HARD_FAIL: future price access")
        row = self._by_start.get(timestamp)
        return None if row is None else row.price

    def records(self) -> tuple[PriceRecord, ...]:
        return self._records


def read_price_records(path: Path) -> tuple[PriceRecord, ...]:
    rows: list[PriceRecord] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            start = datetime.combine(date.fromisoformat(raw["interval_start_date"]), datetime.min.time()) + TEN_MINUTES * (int(raw["interval_start_minute"]) // 10)
            end = datetime.combine(date.fromisoformat(raw["interval_end_date"]), datetime.min.time()) + TEN_MINUTES * (int(raw["interval_end_minute"]) // 10)
            price = float(raw["price_yuan_per_kwh"])
            if not np.isfinite(price) or price <= 0:
                raise ValueError("Attachment4 price must be finite and strictly positive")
            rows.append(PriceRecord(date.fromisoformat(raw["source_date"]), int(raw["interval_index"]), start, end, price))
    if len(rows) != 365 * 144 or len({r.interval_start for r in rows}) != len(rows):
        raise ValueError("Attachment4 must contain 52560 unique physical intervals")
    return tuple(sorted(rows, key=lambda r: r.interval_start))


class PriceHistory:
    def __init__(self, records: Iterable[PriceRecord], params: Q4Parameters | None = None):
        rows = tuple(sorted(records, key=lambda r: r.interval_start))
        self.records = rows
        self.by_start = {r.interval_start: r for r in rows}
        self.by_date_clock = {(r.interval_start.date(), r.interval_start.hour * 60 + r.interval_start.minute): r.price for r in rows}
        self.by_date_records: dict[date, tuple[PriceRecord, ...]] = {}
        for row in rows:
            self.by_date_records.setdefault(row.interval_start.date(), tuple())
            self.by_date_records[row.interval_start.date()] += (row,)
        self.starts = tuple(r.interval_start for r in rows)
        self.params = params or Q4Parameters()
        self._p3_level_cache: dict[datetime, tuple[float, int]] = {}

    def view(self, decision_time: datetime) -> CausalPriceView:
        visible_count = bisect_right(self.starts, decision_time)
        return CausalPriceView(self.records[:visible_count], decision_time, self.params.visibility_rule, records_are_sorted_visible=True)

    @staticmethod
    def _candidate_date(target: datetime, cutoff: datetime) -> date:
        clock = target.hour * 60 + target.minute
        return cutoff.date() if clock <= cutoff.hour * 60 + cutoff.minute else cutoff.date() - timedelta(days=1)

    def latest_any(self, view: CausalPriceView) -> float | None:
        return view.records()[-1].price if view.records() else None

    def p0(self, target: datetime, view: CausalPriceView) -> tuple[float | None, str]:
        candidate = self._candidate_date(target, view.decision_time)
        clock = target.hour * 60 + target.minute
        for _ in range(370):
            value = self.by_date_clock.get((candidate, clock))
            if value is not None and datetime.combine(candidate, datetime.min.time()) + timedelta(minutes=clock) <= view.decision_time:
                return value, ""
            candidate -= timedelta(days=1)
        value = self.latest_any(view)
        return value, "fallback_latest_visible" if value is not None else "no_visible_history"

    def p1(self, target: datetime, view: CausalPriceView) -> tuple[float | None, str]:
        candidate = self._candidate_date(target, view.decision_time)
        clock = target.hour * 60 + target.minute
        for _ in range(370):
            if candidate.weekday() == target.weekday():
                value = self.by_date_clock.get((candidate, clock))
                if value is not None and datetime.combine(candidate, datetime.min.time()) + timedelta(minutes=clock) <= view.decision_time:
                    return value, ""
            candidate -= timedelta(days=1)
        value, reason = self.p0(target, view)
        return value, "fallback_p0" if value is not None else reason

    def p2(self, target: datetime, view: CausalPriceView) -> tuple[float | None, str]:
        candidate = self._candidate_date(target, view.decision_time)
        clock = target.hour * 60 + target.minute
        newest: list[float] = []
        for _ in range(370):
            value = self.by_date_clock.get((candidate, clock))
            timestamp = datetime.combine(candidate, datetime.min.time()) + timedelta(minutes=clock)
            if value is not None and timestamp <= view.decision_time:
                newest.append(value)
                if len(newest) == self.params.ewma_max_days:
                    break
            candidate -= timedelta(days=1)
        if not newest:
            return self.p0(target, view)
        values = np.asarray(list(reversed(newest)), dtype=float)
        ages = np.arange(len(values) - 1, -1, -1, dtype=float)
        weights = (1.0 - self.params.ewma_alpha) ** ages
        return float(np.dot(values, weights) / weights.sum()), ""

    def p3(self, target: datetime, view: CausalPriceView) -> tuple[float | None, str, int]:
        base, reason = self.p2(target, view)
        if base is None:
            return None, reason, 0
        cached = self._p3_level_cache.get(view.decision_time)
        if cached is None:
            day = view.decision_time.date()
            observed = [row for row in self.by_date_records.get(day, ()) if row.interval_start <= view.decision_time]
            shape_cutoff = datetime.combine(day, datetime.min.time()) - TEN_MINUTES
            shape_visible_count = bisect_right(self.starts, shape_cutoff)
            shape_view = CausalPriceView(self.records[:shape_visible_count], shape_cutoff, self.params.visibility_rule, records_are_sorted_visible=True)
            ratios: list[float] = []
            for row in observed[-self.params.p3_level_window_intervals:]:
                shape, _ = self.p2(row.interval_start, shape_view)
                if shape is not None and shape > 0 and np.isfinite(shape):
                    ratios.append(row.price / shape)
            raw_level = 1.0 if not ratios else float(np.median(ratios))
            hits = int(raw_level < self.params.p3_level_lower or raw_level > self.params.p3_level_upper)
            level = min(max(raw_level, self.params.p3_level_lower), self.params.p3_level_upper)
            cached = (level, hits)
            self._p3_level_cache[view.decision_time] = cached
        level, hits = cached
        return float(base * level), reason, hits

    def predict(self, predictor_id: str, target: datetime, decision_time: datetime, view: CausalPriceView | None = None) -> tuple[float | None, str, int, bool, str]:
        if target == decision_time:
            observed = self.by_start.get(target)
            if observed is None:
                return None, "no_observed_at_decision", 0, False, "predicted"
            return observed.price, "", 0, True, "observed_at_decision"
        view = view or self.view(decision_time)
        if view.decision_time != decision_time:
            raise AssertionError("price view decision-time mismatch")
        if predictor_id == "P0_RECENT_SAME_CLOCK": value, reason = self.p0(target, view); hits = 0
        elif predictor_id == "P1_WEEKDAY_SAME_CLOCK": value, reason = self.p1(target, view); hits = 0
        elif predictor_id == "P2_EWMA": value, reason = self.p2(target, view); hits = 0
        elif predictor_id == "P3_SHAPE_LEVEL": value, reason, hits = self.p3(target, view)
        else: raise ValueError(predictor_id)
        if value is not None and (not np.isfinite(value) or value <= 0):
            raise RuntimeError("Q4_PRICE_PREDICTION_HARD_FAIL: nonpositive/nonfinite prediction")
        return value, reason, hits, False, "predicted"
