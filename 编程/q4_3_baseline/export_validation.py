from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

from q2_baseline.time_axis import date_range
from q3_baseline.export_validation import validate_result3_candidate

from .config import Q43Config


def validate_result4_3_candidate(config: Q43Config, candidate_path: Path, plans: dict[date, object], executed: tuple[object, ...]) -> dict[str, Any]:
    adapter = replace(config.q3, official_result3_template=config.official_result4_3_template)
    january_end = date.fromordinal(config.output_start.toordinal() - 1)
    padded: dict[date, object] = {day: None for day in date_range(adapter.warmup_start, january_end)}
    padded.update(plans)
    return validate_result3_candidate(adapter, candidate_path, padded, executed, config.official_result4_3_sha256)

