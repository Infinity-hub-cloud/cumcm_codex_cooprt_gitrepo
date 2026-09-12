from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from q2_baseline.export_validation import validate_result2_candidate
from q2_baseline.replay import ReplayDay

from .config import Q4Config
from .settlement import Q4ReplayDay


@dataclass(frozen=True)
class _Q2ValidationConfig:
    official_result2_template: Path
    warmup_start: object
    output_start: object
    output_end: object
    parameters: object


def validate_result4_2_candidate(config: Q4Config, candidate_path: Path, replays: tuple[Q4ReplayDay, ...]) -> dict[str, object]:
    adapter = _Q2ValidationConfig(config.official_result4_2_template, config.warmup_start, config.output_start, config.output_end, config.parameters)
    q2_replays = tuple(ReplayDay(r.plan, r.actual, r.emergency_kwh, r.surplus_kwh, r.regular_cost, r.emergency_cost) for r in replays)
    return validate_result2_candidate(adapter, candidate_path, q2_replays, config.official_result4_2_sha256)
