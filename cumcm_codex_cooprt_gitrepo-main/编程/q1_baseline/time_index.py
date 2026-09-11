from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class TemplateInterval:
    template_slot: int
    sample_time_label: str
    sample_minute: int
    interval_start_day_offset: int
    interval_start_minute: int
    interval_end_day_offset: int
    interval_end_minute: int
    official_template_label: str

    @property
    def absolute_start_minute(self) -> int:
        return 1440 * self.interval_start_day_offset + self.interval_start_minute

    @property
    def absolute_end_minute(self) -> int:
        return 1440 * self.interval_end_day_offset + self.interval_end_minute


def _format_minute(total_minute: int) -> str:
    day_offset, minute_of_day = divmod(total_minute, 1440)
    hour, minute = divmod(minute_of_day, 60)
    suffix = f"+{day_offset}" if day_offset else ""
    return f"{hour}:{minute:02d}{suffix}"


def official_interval_label(start_minute: int, end_minute: int) -> str:
    return f"{_format_minute(start_minute)}-{_format_minute(end_minute)}"


def build_official_q1_intervals(
    interval_count: int = 144, delta_minutes: int = 10
) -> tuple[TemplateInterval, ...]:
    intervals: list[TemplateInterval] = []
    for slot in range(1, interval_count + 1):
        start = slot * delta_minutes
        end = start + delta_minutes
        start_day, start_clock = divmod(start, 1440)
        end_day, end_clock = divmod(end, 1440)
        intervals.append(
            TemplateInterval(
                template_slot=slot,
                sample_time_label=_format_minute(start),
                sample_minute=start,
                interval_start_day_offset=start_day,
                interval_start_minute=start_clock,
                interval_end_day_offset=end_day,
                interval_end_minute=end_clock,
                official_template_label=official_interval_label(start, end),
            )
        )
    validate_q1_intervals(intervals, interval_count, delta_minutes)
    return tuple(intervals)


def validate_q1_intervals(
    intervals: Sequence[TemplateInterval],
    interval_count: int = 144,
    delta_minutes: int = 10,
) -> None:
    if len(intervals) != interval_count:
        raise ValueError(f"expected {interval_count} intervals, got {len(intervals)}")
    for index, item in enumerate(intervals, start=1):
        expected_start = index * delta_minutes
        expected_end = expected_start + delta_minutes
        if item.template_slot != index:
            raise ValueError(f"template_slot discontinuity at position {index}")
        if item.sample_minute != expected_start:
            raise ValueError(f"sample minute mismatch at slot {index}")
        if item.absolute_start_minute != expected_start:
            raise ValueError(f"interval start mismatch at slot {index}")
        if item.absolute_end_minute != expected_end:
            raise ValueError(f"interval end mismatch at slot {index}")
        expected_label = official_interval_label(expected_start, expected_end)
        if item.official_template_label != expected_label:
            raise ValueError(f"official label mismatch at slot {index}")
    required = {
        1: ("0:10-0:20", 10, 20),
        2: ("0:20-0:30", 20, 30),
        143: ("23:50-0:00+1", 1430, 1440),
        144: ("0:00+1-0:10+1", 1440, 1450),
    }
    for slot, (label, start, end) in required.items():
        item = intervals[slot - 1]
        if (
            item.official_template_label != label
            or item.absolute_start_minute != start
            or item.absolute_end_minute != end
        ):
            raise ValueError(f"hard-gate time mapping failed at slot {slot}")


def natural_day_zero_based_order(interval_count: int = 144) -> tuple[int, ...]:
    """Return G-array indices for natural-day 00:00--24:00 observation.

    The official template remains in its original order; this rotation is only
    for natural-clock aggregation and cycle interpretation.
    """

    return (interval_count - 1, *range(interval_count - 1))

