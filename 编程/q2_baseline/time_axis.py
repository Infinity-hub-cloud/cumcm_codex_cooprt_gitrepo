from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


TEN_MINUTES = timedelta(minutes=10)


@dataclass(frozen=True)
class TargetInterval:
    template_date: date
    template_slot: int
    interval_start: datetime
    interval_end: datetime

    @property
    def natural_clock_minute(self) -> int:
        return self.interval_start.hour * 60 + self.interval_start.minute


def decision_time(template_date: date) -> datetime:
    return datetime.combine(template_date, time.min)


def target_interval(template_date: date, template_slot: int) -> TargetInterval:
    if not 1 <= template_slot <= 144:
        raise ValueError("template_slot must be in 1..144")
    start = datetime.combine(template_date, time.min) + TEN_MINUTES * template_slot
    return TargetInterval(template_date, template_slot, start, start + TEN_MINUTES)


def target_day(template_date: date) -> tuple[TargetInterval, ...]:
    result = tuple(target_interval(template_date, slot) for slot in range(1, 145))
    if result[0].interval_start != decision_time(template_date) + TEN_MINUTES:
        raise AssertionError("slot 1 mapping failed")
    if result[-1].interval_start != decision_time(template_date) + timedelta(days=1):
        raise AssertionError("slot 144 mapping failed")
    return result


def date_range(start: date, end: date) -> tuple[date, ...]:
    if end < start:
        raise ValueError("end date precedes start date")
    return tuple(start + timedelta(days=i) for i in range((end - start).days + 1))


def natural_day_template_source(day: date, clock_minute: int) -> tuple[date, int]:
    """Return the template date/slot containing a natural-day clock interval."""
    if clock_minute % 10 or not 0 <= clock_minute < 1440:
        raise ValueError("clock_minute must be a ten-minute boundary in [0, 1440)")
    if clock_minute == 0:
        return day - timedelta(days=1), 144
    return day, clock_minute // 10

