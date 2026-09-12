from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import numpy as np

from q2_baseline.time_axis import target_day

from .price import PriceHistory


@dataclass(frozen=True)
class PriceForecastDay:
    template_date: date
    decision_time: datetime
    predictor_id: str
    rows: tuple[dict[str, object], ...]

    @property
    def price_plan(self) -> np.ndarray:
        return np.asarray([float(row["price_plan"]) for row in self.rows], dtype=float)

    def validate(self) -> None:
        if len(self.rows) != 144:
            raise ValueError("Q4 price forecast must contain 144 intervals")
        self.price_plan  # force conversion and positivity check
        for row in self.rows:
            value = float(row["price_plan"])
            if not np.isfinite(value) or value <= 0:
                raise RuntimeError("Q4_PRICE_PREDICTION_HARD_FAIL")
            if row["decision_time"] != self.decision_time:
                raise AssertionError("price decision-time mismatch")


def build_price_forecast_day(template_date: date, predictor_id: str, history: PriceHistory) -> PriceForecastDay:
    decision = datetime.combine(template_date, datetime.min.time())
    view = history.view(decision)
    rows: list[dict[str, object]] = []
    for target in target_day(template_date):
        value, reason, hits, observed, source = history.predict(predictor_id, target.interval_start, decision, view)
        if value is None:
            raise RuntimeError(f"Q4_PRICE_PREDICTION_HARD_FAIL: no price for {target.interval_start}")
        rows.append({
            "template_date": template_date.isoformat(), "template_slot": target.template_slot,
            "interval_start": target.interval_start, "interval_end": target.interval_end,
            "decision_time": decision, "visibility_rule": view.visibility_rule,
            "history_last_visible_time": view.history_last_visible_time,
            "predictor_id": predictor_id, "predictor_version": "q4-price-v0.1",
            "fallback_reason": reason, "observed_at_decision": observed,
            "price_source": source, "price_actual": history.by_start.get(target.interval_start).price if target.interval_start in history.by_start else None,
            "price_pred": float(value), "price_plan": float(value), "level_bound_hit_count": hits,
        })
    result = PriceForecastDay(template_date, decision, predictor_id, tuple(rows))
    result.validate()
    return result


def history_last_visible(records, decision_time: datetime) -> datetime | None:
    visible = [row.interval_start for row in records if row.interval_start <= decision_time]
    return max(visible, default=None)
