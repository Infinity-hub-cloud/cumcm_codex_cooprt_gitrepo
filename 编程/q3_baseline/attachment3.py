from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

TEN_MINUTES = timedelta(minutes=10)
OFFICIAL_ISSUE_MINUTES = (0, 360, 720, 1080)
MAPPING_METHODS = ("ZOH", "INTERP")

@dataclass(frozen=True)
class PVForecastInterval:
    issue_datetime: datetime
    decision_time: datetime
    lead_hour: int
    target_time: datetime
    interval_start: datetime
    interval_end: datetime
    forecast_kw: float
    forecast_kwh: float
    source: str
    forecast_version: str
    mapping_method: str
    interpolation_left_lead: int
    interpolation_right_lead: int | None
    endpoint_hold: bool
    fallback_reason: str = ""

    @property
    def physical_key(self) -> tuple[datetime, datetime]:
        return self.interval_start, self.interval_end

    def validate(self) -> None:
        if self.issue_datetime != self.decision_time:
            raise ValueError("static mapping decision_time must equal publication time")
        if self.target_time != self.issue_datetime + timedelta(hours=self.lead_hour):
            raise ValueError("point target violates issue+lead semantics")
        if self.mapping_method not in MAPPING_METHODS or self.interval_end - self.interval_start != TEN_MINUTES:
            raise ValueError("invalid mapping method or interval duration")
        if self.interval_start < self.target_time:
            raise ValueError("mapped interval precedes its left point")
        if self.endpoint_hold:
            if self.lead_hour != 24 or self.interval_start != self.target_time:
                raise ValueError("endpoint_hold is allowed only at t24")
        elif not self.target_time <= self.interval_start < self.target_time + timedelta(hours=1):
            raise ValueError("mapped interval falls outside adjacent point support")
        if self.mapping_method == "INTERP" and not self.endpoint_hold:
            if self.interpolation_right_lead != self.lead_hour + 1:
                raise ValueError("INTERP requires next lead from same issue")
        elif self.interpolation_right_lead is not None:
            raise ValueError("ZOH/endpoint row cannot declare a right lead")
        if self.forecast_kw < 0 or abs(self.forecast_kwh - self.forecast_kw / 6) > 1e-7:
            raise ValueError("invalid forecast power/energy")

@dataclass(frozen=True)
class Attachment3Data:
    rows: tuple[PVForecastInterval, ...]
    mapping_method: str
    by_issue: dict[datetime, dict[tuple[datetime, datetime], PVForecastInterval]]
    by_physical: dict[tuple[datetime, datetime], tuple[PVForecastInterval, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.by_physical:
            return
        index: dict[tuple[datetime, datetime], list[PVForecastInterval]] = {}
        for row in self.rows:
            index.setdefault(row.physical_key, []).append(row)
        object.__setattr__(self, "by_physical", {key: tuple(sorted(values, key=lambda x: x.issue_datetime)) for key, values in index.items()})

    def latest_covering(self, decision_time: datetime, key: tuple[datetime, datetime], allowed_issue_minutes: tuple[int, ...]) -> PVForecastInterval | None:
        candidates = [row for row in self.by_physical.get(key, ()) if row.issue_datetime <= decision_time and row.issue_datetime.hour * 60 + row.issue_datetime.minute in allowed_issue_minutes]
        return max(candidates, key=lambda row: row.issue_datetime, default=None)

    def validate(self) -> None:
        if self.mapping_method not in MAPPING_METHODS or len(self.rows) != 365 * 4 * 139 or len(self.by_issue) != 365 * 4:
            raise ValueError("revised Attachment3 mapping topology mismatch")
        for issue, mapping in self.by_issue.items():
            if issue.hour * 60 + issue.minute not in OFFICIAL_ISSUE_MINUTES or len(mapping) != 139:
                raise ValueError(f"invalid issue topology: {issue}")
            starts = sorted(key[0] for key in mapping)
            if starts[0] != issue + timedelta(hours=1) or starts[-1] != issue + timedelta(hours=24):
                raise ValueError("issue support must be +1h through t24 endpoint")
            for i, start in enumerate(starts):
                if start != issue + timedelta(hours=1, minutes=10 * i):
                    raise ValueError("gap in revised mapping")
                mapping[(start, start + TEN_MINUTES)].validate()
            if sum(row.endpoint_hold for row in mapping.values()) != 1:
                raise ValueError("each issue must have one endpoint_hold row")

def _dt(text: str) -> datetime:
    return datetime.fromisoformat(text)

def read_attachment3_mapped(path: Path, expected_method: str) -> Attachment3Data:
    rows: list[PVForecastInterval] = []
    by_issue: dict[datetime, dict[tuple[datetime, datetime], PVForecastInterval]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            right = raw["interpolation_right_lead"].strip()
            row = PVForecastInterval(
                _dt(raw["issue_datetime"]), _dt(raw["decision_time"]), int(raw["lead_hour"]),
                _dt(raw["target_time"]), _dt(raw["interval_start"]), _dt(raw["interval_end"]),
                float(raw["forecast_kw"]), float(raw["forecast_kwh"]), raw["forecast_source"],
                raw["forecast_version"], raw["mapping_method"], int(raw["interpolation_left_lead"]),
                int(right) if right else None, raw["endpoint_hold"].lower() == "true", raw["fallback_reason"],
            )
            if row.physical_key in by_issue.setdefault(row.issue_datetime, {}):
                raise ValueError(f"duplicate interval for issue {row.issue_datetime}")
            by_issue[row.issue_datetime][row.physical_key] = row
            rows.append(row)
    result = Attachment3Data(tuple(rows), expected_method.upper(), by_issue)
    result.validate()
    return result

def validate_point_mapped_consistency(point_path: Path, mapped: Attachment3Data) -> dict[str, int]:
    points: dict[tuple[datetime, int], tuple[datetime, float]] = {}
    with point_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            points[(_dt(raw["issue_datetime"]), int(raw["lead_hour"]))] = (_dt(raw["target_time"]), float(raw["forecast_kw"]))
    if len(points) != 365 * 4 * 24:
        raise ValueError("point forecast topology mismatch")
    for row in mapped.rows:
        target, left = points[(row.issue_datetime, row.lead_hour)]
        if row.mapping_method == "ZOH" or row.endpoint_hold:
            expected = left
        else:
            _, right = points[(row.issue_datetime, row.lead_hour + 1)]
            expected = left + (row.interval_start - target).total_seconds() / 3600 * (right - left)
        if target != row.target_time or abs(row.forecast_kw - expected) > 5e-8:
            raise AssertionError("point/mapped consistency failed")
    return {"point_rows": len(points), "mapped_rows": len(mapped.rows), "mismatches": 0}
