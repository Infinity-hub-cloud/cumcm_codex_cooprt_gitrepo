"""Build the approved Q3 point-forecast mappings. Does not import or run a solver."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
OLD = BASE / "预处理审计输出_时间口径修订版" / "normalized"
RAW_A3 = BASE.parent / "C题" / "附件" / "附件3.xlsx"
OUT = BASE / "预处理审计输出_Q3修订版_点值语义"
VERSION = "Q3-A3-POINT-v1.0"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite revised mapping directory: {OUT}")
    source = OLD / "attachment3_forecast_long.csv"
    old_map = OLD / "attachment3_mapped_10min.csv"
    points: list[dict[str, object]] = []
    by_issue: dict[datetime, dict[int, float]] = {}
    with source.open(encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            hour, minute = (int(part) for part in raw["issue_time"].split(":"))
            issue = datetime.fromisoformat(raw["issue_date"]) + timedelta(hours=hour, minutes=minute)
            lead = int(raw["lead_hour"])
            target = issue + timedelta(hours=lead)
            value = float(raw["forecast_kw"])
            by_issue.setdefault(issue, {})[lead] = value
            points.append({
                "issue_datetime": issue.isoformat(sep=" "),
                "lead_hour": lead,
                "target_time": target.isoformat(sep=" "),
                "forecast_kw": f"{value:.4f}",
                "forecast_version": VERSION,
                "time_semantics": "target_time=issue_datetime+lead_hour",
            })
    if len(points) != 365 * 4 * 24 or any(set(v) != set(range(1, 25)) for v in by_issue.values()):
        raise AssertionError("unexpected Attachment3 point topology")
    point_path = OUT / "attachment3_point_forecast_long.csv"
    write_csv(point_path, points)

    outputs: dict[str, Path] = {}
    audit: list[dict[str, object]] = []
    for method in ("zoh", "interp"):
        mapped: list[dict[str, object]] = []
        for issue, forecasts in sorted(by_issue.items()):
            for lead in range(1, 24):
                left, right = forecasts[lead], forecasts[lead + 1]
                target = issue + timedelta(hours=lead)
                for step in range(6):
                    start = target + timedelta(minutes=10 * step)
                    weight = step / 6
                    value = left if method == "zoh" else left + weight * (right - left)
                    mapped.append({
                        "issue_datetime": issue.isoformat(sep=" "),
                        "decision_time": issue.isoformat(sep=" "),
                        "lead_hour": lead,
                        "target_time": target.isoformat(sep=" "),
                        "interval_start": start.isoformat(sep=" "),
                        "interval_end": (start + timedelta(minutes=10)).isoformat(sep=" "),
                        "forecast_kw": f"{value:.10f}",
                        "forecast_kwh": f"{value / 6:.10f}",
                        "forecast_source": "attachment3",
                        "forecast_version": VERSION,
                        "mapping_method": method.upper(),
                        "interpolation_left_lead": lead,
                        "interpolation_right_lead": "" if method == "zoh" else lead + 1,
                        "endpoint_hold": False,
                        "fallback_reason": "",
                    })
            lead = 24
            target = issue + timedelta(hours=24)
            mapped.append({
                "issue_datetime": issue.isoformat(sep=" "),
                "decision_time": issue.isoformat(sep=" "),
                "lead_hour": lead,
                "target_time": target.isoformat(sep=" "),
                "interval_start": target.isoformat(sep=" "),
                "interval_end": (target + timedelta(minutes=10)).isoformat(sep=" "),
                "forecast_kw": f"{forecasts[lead]:.10f}",
                "forecast_kwh": f"{forecasts[lead] / 6:.10f}",
                "forecast_source": "attachment3",
                "forecast_version": VERSION,
                "mapping_method": method.upper(),
                "interpolation_left_lead": lead,
                "interpolation_right_lead": "",
                "endpoint_hold": True,
                "fallback_reason": "",
            })
        if len(mapped) != 365 * 4 * 139:
            raise AssertionError("revised mapping row count mismatch")
        path = OUT / f"attachment3_mapped_10min_q3rev_{method}.csv"
        write_csv(path, mapped)
        outputs[method] = path
        audit.append({
            "mapping_method": method.upper(), "issue_count": len(by_issue),
            "rows": len(mapped), "rows_per_issue": 139,
            "first_supported_offset_minutes": 60,
            "last_interval_offset_minutes": 1440,
            "endpoint_hold_rows": len(by_issue),
            "cross_issue_interpolation_rows": 0,
        })
    audit_path = OUT / "attachment3_mapping_audit.csv"
    write_csv(audit_path, audit)
    created = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    summary = {
        "status": "PASS", "mapping_version": VERSION, "created_at": created,
        "time_semantics": "lead h is a point forecast at issue_datetime + h hours",
        "issue_selection_rule": "latest allowed issue <= decision that contains exact physical interval",
        "interpolation_rule": "same-issue adjacent points only; interval-start power / 6",
        "endpoint_rule": "P24 hold for [t24,t24+10min) only",
        "fallback_rule": "fallback_q2_pv only when no legal Attachment3 row exists",
        "point_rows": len(points), "mapped_rows_each": 365 * 4 * 139,
    }
    (OUT / "attachment3_mapping_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        **summary,
        "raw_source": {"path": str(RAW_A3), "sha256": sha256(RAW_A3)},
        "old_mapping": {"path": str(old_map), "sha256": sha256(old_map), "preserved": True},
        "source_long": {"path": str(source), "sha256": sha256(source)},
        "outputs": {
            "point_long": {"path": str(point_path), "sha256": sha256(point_path)},
            "zoh": {"path": str(outputs['zoh']), "sha256": sha256(outputs['zoh'])},
            "interp": {"path": str(outputs['interp']), "sha256": sha256(outputs['interp'])},
            "audit": {"path": str(audit_path), "sha256": sha256(audit_path)},
        },
    }
    (OUT / "attachment3_mapping_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
