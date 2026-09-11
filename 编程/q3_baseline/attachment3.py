from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path


TEN_MINUTES = timedelta(minutes=10)
OFFICIAL_ISSUE_MINUTES = (0, 360, 720, 1080)


def _clock(text: str) -> int:
    hour, minute = (int(part) for part in text.split(":"))
    return hour * 60 + minute


@dataclass(frozen=True)
class PVForecastInterval:
    issue_datetime: datetime
    interval_start: datetime
    interval_end: datetime
    forecast_kw: float
    lead_hour: int
    natural_interval_index: int
    source: str = "attachment3"

    @property
    def physical_key(self) -> tuple[datetime, datetime]:
        return self.interval_start, self.interval_end


@dataclass(frozen=True)
class Attachment3Data:
    rows: tuple[PVForecastInterval, ...]
    by_issue: dict[datetime, dict[tuple[datetime, datetime], PVForecastInterval]]
    by_physical: dict[tuple[datetime, datetime], tuple[PVForecastInterval, ...]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if self.by_physical:
            return
        index: dict[tuple[datetime, datetime], list[PVForecastInterval]] = {}
        for row in self.rows:
            index.setdefault(row.physical_key, []).append(row)
        object.__setattr__(
            self,
            "by_physical",
            {
                key: tuple(sorted(values, key=lambda item: item.issue_datetime))
                for key, values in index.items()
            },
        )

    def issue(self, when: datetime) -> dict[tuple[datetime, datetime], PVForecastInterval]:
        return self.by_issue.get(when, {})

    def latest_covering(
        self,
        decision_time: datetime,
        key: tuple[datetime, datetime],
        allowed_issue_minutes: tuple[int, ...],
    ) -> PVForecastInterval | None:
        candidates = [
            row for row in self.by_physical.get(key, ())
            if row.physical_key == key
            and row.issue_datetime <= decision_time
            and row.issue_datetime.hour * 60 + row.issue_datetime.minute in allowed_issue_minutes
        ]
        return max(candidates, key=lambda row: row.issue_datetime, default=None)

    def validate(self) -> None:
        if len(self.rows) != 365 * 4 * 144:
            raise ValueError("attachment3 mapped file must contain 365*4*144 rows")
        if len(self.by_issue) != 365 * 4:
            raise ValueError("attachment3 must contain four releases for each of 365 days")
        for issue, mapping in self.by_issue.items():
            if issue.hour * 60 + issue.minute not in OFFICIAL_ISSUE_MINUTES:
                raise ValueError(f"unexpected attachment3 issue time: {issue}")
            if len(mapping) != 144:
                raise ValueError(f"issue {issue} does not contain 144 ten-minute intervals")
            starts = sorted(key[0] for key in mapping)
            if starts[0] != issue or starts[-1] + TEN_MINUTES != issue + timedelta(hours=24):
                raise ValueError(f"issue {issue} does not cover exactly 24 hours")
            for i, start in enumerate(starts):
                if start != issue + i * TEN_MINUTES:
                    raise ValueError(f"attachment3 issue {issue} contains a time gap")
                row = mapping[(start, start + TEN_MINUTES)]
                if row.issue_datetime > row.interval_start:
                    raise ValueError("forecast interval starts before its publication")
                if row.forecast_kw < 0:
                    raise ValueError("attachment3 contains negative PV forecast")


def read_attachment3_mapped(path: Path) -> Attachment3Data:
    rows: list[PVForecastInterval] = []
    by_issue: dict[datetime, dict[tuple[datetime, datetime], PVForecastInterval]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            issue_day = date.fromisoformat(raw["issue_date"])
            issue_minute = _clock(raw["issue_time"])
            issue = datetime.combine(issue_day, time.min) + timedelta(minutes=issue_minute)
            target_day = date.fromisoformat(raw["target_date"])
            start = datetime.combine(target_day, time.min) + timedelta(
                minutes=int(raw["interval_start_minute"])
            )
            end = datetime.combine(target_day, time.min) + timedelta(
                minutes=int(raw["interval_end_minute"])
            )
            row = PVForecastInterval(
                issue_datetime=issue,
                interval_start=start,
                interval_end=end,
                forecast_kw=float(raw["forecast_kw"]),
                lead_hour=int(raw["lead_hour"]),
                natural_interval_index=int(raw["interval_index"]),
            )
            if row.physical_key in by_issue.setdefault(issue, {}):
                raise ValueError(f"duplicate attachment3 physical interval for issue {issue}")
            by_issue[issue][row.physical_key] = row
            rows.append(row)
    result = Attachment3Data(tuple(rows), by_issue)
    result.validate()
    return result


def validate_long_mapped_consistency(long_path: Path, mapped: Attachment3Data) -> dict[str, int]:
    expected: dict[tuple[datetime, int], float] = {}
    with long_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            issue_day = date.fromisoformat(raw["issue_date"])
            issue = datetime.combine(issue_day, time.min) + timedelta(minutes=_clock(raw["issue_time"]))
            expected[(issue, int(raw["lead_hour"]))] = float(raw["forecast_kw"])
    if len(expected) != 365 * 4 * 24:
        raise ValueError("attachment3 long file must contain 365*4*24 rows")
    mismatches = 0
    counts: dict[tuple[datetime, int], int] = {}
    for row in mapped.rows:
        key = row.issue_datetime, row.lead_hour
        counts[key] = counts.get(key, 0) + 1
        if key not in expected or row.forecast_kw != expected[key]:
            mismatches += 1
    if mismatches or any(value != 6 for value in counts.values()) or set(counts) != set(expected):
        raise AssertionError("attachment3 long/mapped consistency failed")
    return {"long_rows": len(expected), "mapped_rows": len(mapped.rows), "mismatches": 0}
