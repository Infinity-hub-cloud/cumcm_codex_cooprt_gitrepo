from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Iterable

import numpy as np

from .state_machine import ExecutedInterval


def _stats(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = predicted - actual
    absolute = np.abs(error)
    return {
        "mae_kw": float(np.mean(absolute)),
        "rmse_kw": float(np.sqrt(np.mean(error**2))),
        "bias_kw": float(np.mean(error)),
        "p50_abs_error_kw": float(np.quantile(absolute, 0.50)),
        "p90_abs_error_kw": float(np.quantile(absolute, 0.90)),
        "p95_abs_error_kw": float(np.quantile(absolute, 0.95)),
        "p99_abs_error_kw": float(np.quantile(absolute, 0.99)),
    }


def evaluate_pv_predictions(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Evaluate physical-key matched predictions by issue time and month.

    Each input row must contain issue_datetime, interval_start, actual_kw and
    predicted_kw. Fallback rows may be included but remain separately sourced.
    """
    material = list(rows)
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in material:
        issue = row["issue_datetime"]
        start = row["interval_start"]
        if not isinstance(issue, datetime) or not isinstance(start, datetime):
            raise TypeError("PV metric timestamps must be datetime")
        groups[(f"{issue.hour:02d}:00", f"{start.month:02d}")].append(row)
        groups[(f"{issue.hour:02d}:00", "ALL")].append(row)
    output: list[dict[str, object]] = []
    for (issue_time, month), items in sorted(groups.items()):
        actual = np.asarray([float(row["actual_kw"]) for row in items])
        predicted = np.asarray([float(row["predicted_kw"]) for row in items])
        stats = _stats(actual, predicted)
        daylight = actual > 0
        stats["daylight_mae_kw"] = float(np.mean(np.abs(predicted[daylight] - actual[daylight]))) if np.any(daylight) else 0.0
        ordered = sorted(items, key=lambda row: (row["issue_datetime"], row["interval_start"]))
        ramp_errors = [
            abs(
                (float(right["predicted_kw"]) - float(left["predicted_kw"]))
                - (float(right["actual_kw"]) - float(left["actual_kw"]))
            )
            for left, right in zip(ordered, ordered[1:])
            if left["issue_datetime"] == right["issue_datetime"]
            and right["interval_start"] - left["interval_start"] == timedelta(minutes=10)
        ]
        stats["ramp_mae_kw"] = float(np.mean(ramp_errors)) if ramp_errors else 0.0
        output.append({"issue_time": issue_time, "month": month, "sample_count": len(items), **stats})
    return output


def economic_metrics(executed: Iterable[ExecutedInterval]) -> dict[str, float]:
    rows = list(executed)
    soc_values = [value for row in rows for value in (row.soc_before, row.soc_after)]
    return {
        "total_cost": sum(row.total_cost for row in rows),
        "planned_purchase_cost": sum(row.planned_purchase_cost for row in rows),
        "downward_penalty": sum(row.downward_adjustment_penalty for row in rows),
        "upward_adjustment_cost": sum(row.upward_adjustment_cost for row in rows),
        "emergency_purchase_cost": sum(row.emergency_purchase_cost for row in rows),
        "emergency_energy": sum(row.E for row in rows),
        "spill_energy": sum(row.W for row in rows),
        "planned_grid_energy": sum(row.G for row in rows),
        "final_grid_energy": sum(row.Q for row in rows),
        "total_charge": sum(row.C for row in rows),
        "total_discharge": sum(row.D for row in rows),
        "adjust_down_energy": sum(max(row.G - row.Q, 0.0) for row in rows),
        "adjust_up_energy": sum(max(row.Q - row.G, 0.0) for row in rows),
        "adjustment_count": float(sum(abs(row.Q - row.G) > 1e-9 for row in rows)),
        "soc_min": min(soc_values, default=float("nan")),
        "soc_max": max(soc_values, default=float("nan")),
    }


def soc_boundary_hits(
    executed: Iterable[ExecutedInterval],
    soc_min: float,
    soc_max: float,
    tolerance: float,
) -> float:
    return float(
        sum(
            abs(value - soc_min) <= tolerance or abs(value - soc_max) <= tolerance
            for row in executed
            for value in (row.soc_before, row.soc_after)
        )
    )


def value_decomposition(costs: dict[str, float]) -> dict[str, float]:
    required = {"REF_Q2_FROZEN", "Q3_ATTACHMENT3_0ONLY", "Q3_ROLLING_4ISSUE"}
    if not required <= costs.keys():
        raise ValueError(f"missing value-decomposition tracks: {sorted(required - costs.keys())}")
    return {
        "Value_Attachment3_Initial": costs["REF_Q2_FROZEN"] - costs["Q3_ATTACHMENT3_0ONLY"],
        "Value_Intraday_Rolling": costs["Q3_ATTACHMENT3_0ONLY"] - costs["Q3_ROLLING_4ISSUE"],
        "Total_Q3_Improvement": costs["REF_Q2_FROZEN"] - costs["Q3_ROLLING_4ISSUE"],
    }
