from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Any

from q1_baseline.run_manifest import timestamp, write_json


def flush_failure_evidence(
    destination: Path,
    manifest: dict[str, Any],
    solver_rows: list[dict[str, Any]],
    assertion_days: list[dict[str, Any]],
    *,
    last_completed_template_date: date | None,
    failed_template_date: date | None,
    error: BaseException,
) -> None:
    """Persist essential evidence before propagating a failed/incomplete run."""
    if failed_template_date is not None and not any(
        row.get("template_date") == failed_template_date.isoformat() for row in solver_rows
    ):
        solver_rows.append(
            {
                "template_date": failed_template_date.isoformat(),
                "period": "unknown",
                "status": "FAILED_OR_INCOMPLETE",
                "solver_name": manifest.get("solver_name", "UNKNOWN"),
                "solver_version": manifest.get("solver_version", "UNKNOWN"),
                "termination_condition": f"{type(error).__name__}: {error}",
                "mip_gap": "",
                "runtime_seconds": "",
            }
        )
    solver_fields = [
        "template_date", "period", "status", "solver_name", "solver_version",
        "termination_condition", "mip_gap", "runtime_seconds",
    ]
    with (destination / "solver_days.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=solver_fields)
        writer.writeheader()
        writer.writerows(solver_rows)
    write_json(
        destination / "assertions.json",
        {"passed": False, "incomplete": True, "daily": assertion_days},
    )
    with (destination / "warnings_and_failures.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp()} FAILURE {type(error).__name__}: {error}\n")
    manifest.update(
        {
            "status": "FAILED_OR_INCOMPLETE",
            "run_status": "FAILED_OR_INCOMPLETE",
            "finished_at": timestamp(),
            "failures_count": max(1, int(manifest.get("failures_count", 0)) + 1),
            "last_completed_template_date": (
                None if last_completed_template_date is None else last_completed_template_date.isoformat()
            ),
            "failed_template_date": (
                None if failed_template_date is None else failed_template_date.isoformat()
            ),
            "termination_reason": f"{type(error).__name__}: {error}",
        }
    )
    write_json(destination / "run_manifest.json", manifest)

