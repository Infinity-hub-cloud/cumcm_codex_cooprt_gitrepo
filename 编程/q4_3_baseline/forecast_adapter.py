from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import numpy as np

from q2_baseline.time_axis import target_day

from .config import PREDICTORS, VISIBILITY_RULE
from .price import PriceHistory


@dataclass(frozen=True)
class RollingPriceForecast:
    template_date: date
    update_time: datetime
    predictor_id: str
    start_slot: int
    rows: tuple[dict[str, object], ...]

    @property
    def price_plan(self) -> np.ndarray:
        values = np.asarray([float(row["price_plan"]) for row in self.rows], dtype=float)
        if np.any(~np.isfinite(values)) or np.any(values <= 0):
            raise RuntimeError("Q4_PRICE_PREDICTION_HARD_FAIL")
        return values

    def assert_causal(self) -> None:
        expected = tuple(range(self.start_slot, 145))
        if tuple(int(row["template_slot"]) for row in self.rows) != expected:
            raise AssertionError("Q4-3 price horizon must be a contiguous template suffix")
        for row in self.rows:
            if row["decision_time"] != self.update_time or row["visibility_rule"] != VISIBILITY_RULE:
                raise AssertionError("Q4-3 price metadata mismatch")
            start = row["physical_interval_start"]
            if not isinstance(start, datetime) or start < self.update_time:
                raise AssertionError("Q4-3 attempted to price an executed interval")
            if bool(row["observed_at_decision"]) != (start == self.update_time):
                raise AssertionError("observed-at-decision boundary contract failed")


def build_rolling_price_forecast(
    template_date: date,
    update_time: datetime,
    predictor_id: str,
    history: PriceHistory,
) -> RollingPriceForecast:
    if predictor_id not in PREDICTORS:
        raise ValueError(f"unregistered Q4-3 predictor: {predictor_id}")
    targets = tuple(target for target in target_day(template_date) if target.interval_start >= update_time)
    if not targets:
        raise ValueError("Q4-3 update has no unexecuted suffix")
    view = history.view(update_time)
    rows: list[dict[str, object]] = []
    for target in targets:
        value, reason, hits, observed, source = history.predict(
            predictor_id, target.interval_start, update_time, view
        )
        if value is None:
            raise RuntimeError(f"Q4_PRICE_PREDICTION_HARD_FAIL: no price for {target.interval_start}")
        rows.append(
            {
                "template_date": template_date.isoformat(),
                "template_slot": target.template_slot,
                "update_time": update_time,
                "physical_interval_start": target.interval_start,
                "physical_interval_end": target.interval_end,
                "decision_time": update_time,
                "visibility_rule": view.visibility_rule,
                "history_last_visible_time": view.history_last_visible_time,
                "predictor_id": predictor_id,
                "forecast_version": "q4-3-price-v0.1",
                "fallback_reason": reason,
                "observed_at_decision": observed,
                "price_source": source,
                # Actual price is appended only by post-run evaluation.  The
                # planning object never receives future Attachment4 values.
                "price_actual": None,
                "price_pred": float(value),
                "price_plan": float(value),
                "evaluation_scope": "ALL_PLANNING_PRICE_INPUTS",
                "unknown_at_decision": not observed,
                "level_bound_hit_count": hits,
            }
        )
    result = RollingPriceForecast(template_date, update_time, predictor_id, targets[0].template_slot, tuple(rows))
    result.price_plan
    result.assert_causal()
    return result
