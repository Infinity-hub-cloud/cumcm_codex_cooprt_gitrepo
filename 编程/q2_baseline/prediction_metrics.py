from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import sqrt
from typing import Any, Iterable

import numpy as np

from .data import Q2InputData
from .forecast import ForecastDay


@dataclass(frozen=True)
class PredictionObservation:
    interval_start: datetime
    interval_end: datetime
    load_actual_kw: float
    load_pred_kw: float
    pv_actual_kw: float
    pv_pred_kw: float


def build_prediction_observations(
    forecasts: Iterable[ForecastDay],
    data: Q2InputData,
    output_start: date,
    output_end: date,
) -> tuple[PredictionObservation, ...]:
    rows: list[PredictionObservation] = []
    for forecast in forecasts:
        for item in forecast.rows:
            actual = data.actual_by_template_key[(forecast.template_date, item.template_slot)]
            natural_date = actual.interval_start.date()
            if output_start <= natural_date <= output_end:
                rows.append(
                    PredictionObservation(
                        actual.interval_start,
                        actual.interval_end,
                        actual.load_kw,
                        item.load_pred_kw,
                        actual.pv_kw,
                        item.pv_pred_kw,
                    )
                )
    rows.sort(key=lambda item: item.interval_start)
    expected_count = ((output_end - output_start).days + 1) * 144
    if len(rows) != expected_count:
        raise AssertionError(
            f"formal physical-time prediction coverage failed: {len(rows)} != {expected_count}"
        )
    return tuple(rows)


def _season(month: int) -> str:
    if month in (12, 1, 2):
        return "winter_DJF"
    if month in (3, 4, 5):
        return "spring_MAM"
    if month in (6, 7, 8):
        return "summer_JJA"
    return "autumn_SON"


def _groups(
    observations: tuple[PredictionObservation, ...],
) -> Iterable[tuple[str, str, tuple[PredictionObservation, ...]]]:
    yield "overall", "formal_output", observations
    for month in sorted({row.interval_start.strftime("%Y-%m") for row in observations}):
        yield "month", month, tuple(row for row in observations if row.interval_start.strftime("%Y-%m") == month)
    for season in ("winter_DJF", "spring_MAM", "summer_JJA", "autumn_SON"):
        rows = tuple(row for row in observations if _season(row.interval_start.month) == season)
        if rows:
            yield "season", season, rows


def _metric_row(
    scope: str,
    group: str,
    series: str,
    metric: str,
    value: float,
    unit: str,
    sample_count: int,
    definition: str,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "group": group,
        "series": series,
        "metric": metric,
        "value": float(value),
        "unit": unit,
        "sample_count": int(sample_count),
        "valid_coverage": 1.0,
        "definition": definition,
        "posthoc_evaluation_only": True,
    }


def _finite(actual: np.ndarray, predicted: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    mask = np.isfinite(actual) & np.isfinite(predicted)
    coverage = float(np.count_nonzero(mask) / mask.size) if mask.size else 0.0
    return actual[mask], predicted[mask], coverage


def evaluate_prediction_observations(
    observations: tuple[PredictionObservation, ...],
) -> list[dict[str, Any]]:
    if not observations:
        raise ValueError("prediction evaluation requires observations")
    formal_actual_load = np.asarray([row.load_actual_kw for row in observations], dtype=float)
    peak_threshold = float(np.quantile(formal_actual_load, 0.90))
    output: list[dict[str, Any]] = []

    for scope, group, selected in _groups(observations):
        load_actual_all = np.asarray([row.load_actual_kw for row in selected], dtype=float)
        load_pred_all = np.asarray([row.load_pred_kw for row in selected], dtype=float)
        load_actual, load_pred, load_coverage = _finite(load_actual_all, load_pred_all)
        load_error = load_pred - load_actual
        load_abs = np.abs(load_error)
        load_n = int(load_actual.size)
        load_definition = "error=predicted-actual; percentiles use absolute error"
        load_metrics = {
            "MAE": (float(np.mean(load_abs)), "kW", "mean(abs(predicted-actual))"),
            "RMSE": (sqrt(float(np.mean(load_error**2))), "kW", "sqrt(mean((predicted-actual)^2))"),
            "nMAE": (float(np.mean(load_abs) / np.mean(load_actual)), "ratio", "MAE / mean(actual_load)"),
            "bias": (float(np.mean(load_error)), "kW", "mean(predicted-actual)"),
            "max_absolute_error": (float(np.max(load_abs)), "kW", load_definition),
            "error_p50": (float(np.quantile(load_abs, 0.50)), "kW", load_definition),
            "error_p90": (float(np.quantile(load_abs, 0.90)), "kW", load_definition),
            "error_p95": (float(np.quantile(load_abs, 0.95)), "kW", load_definition),
            "error_p99": (float(np.quantile(load_abs, 0.99)), "kW", load_definition),
            "sample_count": (float(load_n), "count", "finite actual/predicted pairs"),
            "valid_coverage": (load_coverage, "ratio", "finite pairs / requested pairs"),
            "peak_threshold_p90": (peak_threshold, "kW", "global formal-output actual-load 90th percentile; posthoc only"),
        }
        peak_mask = load_actual >= peak_threshold
        peak_abs = load_abs[peak_mask]
        load_metrics.update(
            {
                "peak_MAE": (float(np.mean(peak_abs)) if peak_abs.size else float("nan"), "kW", "MAE where actual_load >= global formal p90"),
                "peak_max_absolute_error": (float(np.max(peak_abs)) if peak_abs.size else float("nan"), "kW", "max absolute error where actual_load >= global formal p90"),
                "peak_sample_count": (float(peak_abs.size), "count", "samples where actual_load >= global formal p90"),
            }
        )
        for metric, (value, unit, definition) in load_metrics.items():
            row = _metric_row(scope, group, "load", metric, value, unit, load_n, definition)
            row["valid_coverage"] = load_coverage
            output.append(row)

        pv_actual_all = np.asarray([row.pv_actual_kw for row in selected], dtype=float)
        pv_pred_all = np.asarray([row.pv_pred_kw for row in selected], dtype=float)
        pv_actual, pv_pred, pv_coverage = _finite(pv_actual_all, pv_pred_all)
        pv_error = pv_pred - pv_actual
        pv_abs = np.abs(pv_error)
        daylight = pv_actual > 0.0
        daylight_error = pv_error[daylight]
        pv_metrics = {
            "all_day_MAE": (float(np.mean(pv_abs)), "kW", "mean(abs(predicted-actual)) over all intervals"),
            "all_day_RMSE": (sqrt(float(np.mean(pv_error**2))), "kW", "RMSE over all intervals"),
            "bias": (float(np.mean(pv_error)), "kW", "mean(predicted-actual)"),
            "max_absolute_error": (float(np.max(pv_abs)), "kW", "max(abs(predicted-actual))"),
            "sample_count": (float(pv_actual.size), "count", "finite actual/predicted pairs"),
            "valid_coverage": (pv_coverage, "ratio", "finite pairs / requested pairs"),
            "daylight_MAE": (float(np.mean(np.abs(daylight_error))) if daylight_error.size else float("nan"), "kW", "MAE where actual_pv_kw > 0"),
            "daylight_RMSE": (sqrt(float(np.mean(daylight_error**2))) if daylight_error.size else float("nan"), "kW", "RMSE where actual_pv_kw > 0"),
            "daylight_sample_count": (float(daylight_error.size), "count", "samples where actual_pv_kw > 0"),
        }

        ramp_errors: list[float] = []
        by_day: dict[date, list[PredictionObservation]] = {}
        for item in selected:
            by_day.setdefault(item.interval_start.date(), []).append(item)
        for day_rows in by_day.values():
            day_rows.sort(key=lambda item: item.interval_start)
            for previous, current in zip(day_rows, day_rows[1:]):
                if previous.interval_end != current.interval_start:
                    continue
                actual_ramp = current.pv_actual_kw - previous.pv_actual_kw
                predicted_ramp = current.pv_pred_kw - previous.pv_pred_kw
                ramp_errors.append(abs(predicted_ramp - actual_ramp))
        pv_metrics["ramp_MAE"] = (
            float(np.mean(ramp_errors)) if ramp_errors else float("nan"),
            "kW/10min",
            "mean(abs(predicted_ramp-actual_ramp)); adjacent physical intervals within the same natural day only",
        )
        pv_metrics["ramp_sample_count"] = (
            float(len(ramp_errors)), "count", "within-natural-day adjacent physical interval pairs"
        )
        for metric, (value, unit, definition) in pv_metrics.items():
            row = _metric_row(scope, group, "pv", metric, value, unit, int(pv_actual.size), definition)
            row["valid_coverage"] = pv_coverage
            output.append(row)
    return output
