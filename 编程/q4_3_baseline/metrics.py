from __future__ import annotations

from collections import defaultdict
from typing import Iterable

import numpy as np

from q3_baseline.metrics import economic_metrics as q3_economic_metrics, soc_boundary_hits


def economic_metrics(executed: Iterable[object], *, soc_min: float, soc_max: float, tolerance: float) -> dict[str, float]:
    rows = tuple(executed)
    result = q3_economic_metrics(rows)
    result["realized_total_cost"] = result["total_cost"]
    result["soc_boundary_hits"] = soc_boundary_hits(rows, soc_min, soc_max, tolerance)
    return result


def _ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    ranks[order] = np.arange(len(values), dtype=float)
    return ranks


def _rank_corr(actual: np.ndarray, predicted: np.ndarray) -> float:
    if len(actual) < 2 or np.std(actual) == 0 or np.std(predicted) == 0:
        return float("nan")
    return float(np.corrcoef(_ranks(actual), _ranks(predicted))[0, 1])


def price_prediction_metrics(rows: Iterable[dict[str, object]], *, unknown_only: bool) -> dict[str, float | str]:
    material = [row for row in rows if (bool(row["unknown_at_decision"]) if unknown_only else True)]
    actual = np.asarray([float(row["price_actual"]) for row in material], dtype=float)
    predicted = np.asarray([float(row["price_pred"]) for row in material], dtype=float)
    error = predicted - actual
    groups: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(material):
        groups[str(row["update_time"])].append(index)
    correlations: list[float] = []
    peak_hits = offpeak_hits = peak_total = offpeak_total = 0
    for indices in groups.values():
        a, p = actual[indices], predicted[indices]
        corr = _rank_corr(a, p)
        if np.isfinite(corr):
            correlations.append(corr)
        count = max(1, int(np.ceil(0.10 * len(indices))))
        a_hi, p_hi = set(np.argsort(a)[-count:]), set(np.argsort(p)[-count:])
        a_lo, p_lo = set(np.argsort(a)[:count]), set(np.argsort(p)[:count])
        peak_hits += len(a_hi & p_hi); peak_total += len(a_hi)
        offpeak_hits += len(a_lo & p_lo); offpeak_total += len(a_lo)
    return {
        "scope": "UNKNOWN_AT_DECISION_ONLY" if unknown_only else "ALL_PLANNING_PRICE_INPUTS",
        "sample_count": float(len(material)),
        "MAE": float(np.mean(np.abs(error))) if len(error) else float("nan"),
        "RMSE": float(np.sqrt(np.mean(error ** 2))) if len(error) else float("nan"),
        "bias": float(np.mean(error)) if len(error) else float("nan"),
        "P90_absolute_error": float(np.quantile(np.abs(error), 0.9)) if len(error) else float("nan"),
        "mean_rank_correlation": float(np.mean(correlations)) if correlations else float("nan"),
        "median_rank_correlation": float(np.median(correlations)) if correlations else float("nan"),
        "peak10_recall": peak_hits / peak_total if peak_total else float("nan"),
        "offpeak10_recall": offpeak_hits / offpeak_total if offpeak_total else float("nan"),
        "negative_count": float(np.sum(predicted < 0)),
        "nonfinite_count": float(np.sum(~np.isfinite(predicted))),
        "observed_at_decision_count": float(sum(bool(row["observed_at_decision"]) for row in material)),
    }

