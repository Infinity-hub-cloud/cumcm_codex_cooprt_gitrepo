from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from q1_baseline.run_manifest import sha256_file
from q2_baseline.exporter import round4
from q2_baseline.time_axis import date_range

from .config import Q3Config
from .planner import RollingPlan
from .state_machine import ExecutedInterval


def validate_result3_candidate(
    config: Q3Config,
    candidate_path: Path,
    plans: dict[date, RollingPlan],
    executed: tuple[ExecutedInterval, ...],
    expected_official_sha256: str,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    official = config.official_result3_template.resolve()
    candidate = candidate_path.resolve()
    add("candidate_is_separate_file", candidate != official, str(candidate))
    add("candidate_exists", candidate.is_file(), str(candidate))
    if not candidate.is_file():
        return {"passed": False, "checks": checks}
    workbook = load_workbook(candidate, read_only=False, data_only=False)
    expected_sheets = ["计划购电量", "调整购电量", "充放电量", "紧急购电量"]
    add("sheet_names", workbook.sheetnames == expected_sheets, workbook.sheetnames)
    output_days = date_range(config.output_start, config.output_end)
    by_template = {(date.fromisoformat(row.template_date), row.template_slot): row for row in executed}

    def as_date(value: Any) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        return value if isinstance(value, date) else None

    for sheet_name, field in (("计划购电量", "G"), ("调整购电量", "Q")):
        sheet = workbook[sheet_name]
        add(f"{sheet_name}_dimensions", (sheet.max_row, sheet.max_column) == (335, 147), [sheet.max_row, sheet.max_column])
        add(
            f"{sheet_name}_slot_order",
            sheet.cell(1, 2).value == "0:10-0:20" and sheet.cell(1, 145).value == "0:00-0:10+1",
            [sheet.cell(1, 2).value, sheet.cell(1, 145).value],
        )
        errors = 0
        max_error = 0.0
        for row_index, day in enumerate(output_days, start=2):
            if as_date(sheet.cell(row_index, 1).value) != day:
                errors += 1
            vector = plans[day].G if field == "G" else plans[day].Q
            for i, expected in enumerate(vector, start=2):
                value = sheet.cell(row_index, i).value
                if not isinstance(value, (int, float)):
                    errors += 1
                else:
                    max_error = max(max_error, abs(float(value) - round4(float(expected))))
            rows = [by_template[(day, slot)] for slot in range(1, 145)]
            expected_quantity = round4(sum(float(value) for value in vector))
            expected_cost = round4(
                sum(
                    row.planned_purchase_cost
                    + (0.0 if field == "G" else row.downward_adjustment_penalty + row.upward_adjustment_cost)
                    for row in rows
                )
            )
            max_error = max(
                max_error,
                abs(float(sheet.cell(row_index, 146).value) - expected_quantity),
                abs(float(sheet.cell(row_index, 147).value) - expected_cost),
            )
        add(f"{sheet_name}_all_values", errors == 0 and max_error <= 5e-8, {"errors": errors, "max_error": max_error})

    formula_cells: list[str] = []
    ellipsis_cells: list[str] = []
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    formula_cells.append(f"{sheet.title}!{cell.coordinate}")
                if isinstance(cell.value, str) and "⁝" in cell.value:
                    ellipsis_cells.append(f"{sheet.title}!{cell.coordinate}")
    add("no_formulas", not formula_cells, formula_cells)
    add("no_template_ellipsis", not ellipsis_cells, ellipsis_cells)
    workbook.close()
    official_hash = sha256_file(official)
    add("official_template_unchanged", official_hash == expected_official_sha256, official_hash)
    return {
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "candidate_sha256": sha256_file(candidate),
        "official_sha256": official_hash,
    }
