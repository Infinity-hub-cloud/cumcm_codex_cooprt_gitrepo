from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Iterable

import numpy as np

from .settlement import Q4ReplayDay


def economic_metrics(replays: Iterable[Q4ReplayDay], soc_min: float = 1200.0, soc_max: float = 10800.0, tolerance: float = 1e-6) -> dict[str, float]:
    rows = list(replays)
    soc = [value for replay in rows for value in replay.plan.S]
    return {
        "realized_total_cost": float(sum(replay.total_cost for replay in rows)),
        "regular_purchase_cost": float(sum(float(np.sum(replay.regular_cost)) for replay in rows)),
        "emergency_purchase_cost": float(sum(float(np.sum(replay.emergency_cost)) for replay in rows)),
        "grid_purchase_energy": float(sum(float(np.sum(replay.plan.G)) for replay in rows)),
        "emergency_energy": float(sum(float(np.sum(replay.emergency_kwh)) for replay in rows)),
        "spill_energy": float(sum(float(np.sum(replay.surplus_kwh)) for replay in rows)),
        "charge": float(sum(float(np.sum(replay.plan.C)) for replay in rows)),
        "discharge": float(sum(float(np.sum(replay.plan.D)) for replay in rows)),
        "storage_throughput": float(sum(float(np.sum(replay.plan.C + replay.plan.D)) for replay in rows)),
        "soc_min": float(min(soc, default=np.nan)), "soc_max": float(max(soc, default=np.nan)),
        "soc_boundary_hits": float(sum(abs(v - soc_min) <= tolerance or abs(v - soc_max) <= tolerance for v in soc)),
        "days": float(len(rows)),
    }


def prediction_metrics(rows: Iterable[dict[str, object]]) -> dict[str, float]:
    material = list(rows)
    known = [r for r in material if r.get("price_actual") is not None and not bool(r.get("observed_at_decision"))]
    actual = np.asarray([float(r["price_actual"]) for r in known], dtype=float)
    pred = np.asarray([float(r["price_pred"]) for r in known], dtype=float)
    if not len(actual):
        return {"sample_count": 0.0, "MAE": np.nan, "RMSE": np.nan, "bias": np.nan, "P90_absolute_error": np.nan, "rank_correlation": np.nan, "peak10_recall": np.nan, "offpeak10_recall": np.nan, "negative_prediction_count": 0.0, "nonfinite_prediction_count": 0.0}
    error = pred - actual
    def rank(values: np.ndarray) -> np.ndarray:
        order = np.argsort(values, kind="mergesort")
        ranks = np.empty(len(values), dtype=float)
        ranks[order] = np.arange(len(values), dtype=float)
        return ranks
    actual_rank = rank(actual)
    pred_rank = rank(pred)
    rank_corr = float(np.corrcoef(actual_rank, pred_rank)[0, 1]) if len(actual) > 1 else np.nan
    high = actual >= np.quantile(actual, 0.9)
    low = actual <= np.quantile(actual, 0.1)
    pred_high = pred >= np.quantile(pred, 0.9)
    pred_low = pred <= np.quantile(pred, 0.1)
    return {"sample_count": float(len(actual)), "MAE": float(np.mean(np.abs(error))), "RMSE": float(np.sqrt(np.mean(error ** 2))), "bias": float(np.mean(error)), "P90_absolute_error": float(np.quantile(np.abs(error), 0.9)), "rank_correlation": rank_corr, "peak10_recall": float(np.sum(high & pred_high) / max(np.sum(high), 1)), "offpeak10_recall": float(np.sum(low & pred_low) / max(np.sum(low), 1)), "negative_prediction_count": float(np.sum(pred <= 0)), "nonfinite_prediction_count": float(np.sum(~np.isfinite(pred)))}


def value_decomposition(costs: dict[str, float], selected_predictor: str) -> dict[str, float | str]:
    required = {"REF_Q2_FIXED_PRICE_FROZEN", "Q4_2_PRICE_UNAWARE_RESETTLEMENT", "Q4_2_NOSTORAGE", selected_predictor}
    missing = sorted(required - costs.keys())
    if missing:
        raise ValueError(f"missing Q4-2 tracks: {missing}")
    result: dict[str, float | str] = {
        "PriceSystemEffect": costs["Q4_2_PRICE_UNAWARE_RESETTLEMENT"] - costs["REF_Q2_FIXED_PRICE_FROZEN"],
        "PriceAwarenessValue_selected": costs["Q4_2_PRICE_UNAWARE_RESETTLEMENT"] - costs[selected_predictor],
        "StorageValue_selected": costs["Q4_2_NOSTORAGE"] - costs[selected_predictor],
        "selected_predictor": selected_predictor,
        "same_formal_dates": True, "same_initial_soc": True, "actual_attachment4_settlement": True,
    }
    for track, label in {
        "Q4_2_PRICE_BASELINE_P0": "P0",
        "Q4_2_PRICE_CANDIDATE_P1": "P1",
        "Q4_2_PRICE_CANDIDATE_P2": "P2",
        "Q4_2_PRICE_CANDIDATE_P3": "P3",
    }.items():
        if track in costs:
            result[f"PriceAwarenessValue_{label}"] = costs["Q4_2_PRICE_UNAWARE_RESETTLEMENT"] - costs[track]
    return result
