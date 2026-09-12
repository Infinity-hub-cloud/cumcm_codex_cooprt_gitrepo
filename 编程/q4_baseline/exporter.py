from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from q2_baseline.exporter import export_result2_candidate
from q2_baseline.replay import ReplayDay
from q1_baseline.run_manifest import sha256_file

from .config import Q4Config
from .settlement import Q4ReplayDay


@dataclass(frozen=True)
class _Q2ExportConfig:
    official_result2_template: Path
    warmup_start: object
    output_start: object
    output_end: object
    parameters: object


def export_result4_2_candidate(config: Q4Config, candidate_path: Path, replays: tuple[Q4ReplayDay, ...]) -> dict[str, object]:
    """Export only during an explicitly authorized human full-year run.

    The established Q2 exporter is reused to preserve the accepted workbook
    layout, four-hour natural-day convention, event merging, and four-decimal
    rounding rules.  The official result4-2 template is never overwritten.
    """
    if sha256_file(config.official_result4_2_template) != config.official_result4_2_sha256:
        raise RuntimeError("Q4_RESULT4_2_TEMPLATE_HASH_HARD_FAIL")
    adapter = _Q2ExportConfig(config.official_result4_2_template, config.warmup_start, config.output_start, config.output_end, config.parameters)
    q2_replays = tuple(ReplayDay(r.plan, r.actual, r.emergency_kwh, r.surplus_kwh, r.regular_cost, r.emergency_cost) for r in replays)
    return export_result2_candidate(adapter, candidate_path, q2_replays)
