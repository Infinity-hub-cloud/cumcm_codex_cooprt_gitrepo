from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from q3_baseline.state_machine import ExecutedInterval, execute_r0_interval

from .price import PriceHistory


def model_b_regular_components(G: float, Q: float, actual_price: float) -> dict[str, float]:
    down = max(G - Q, 0.0)
    up = max(Q - G, 0.0)
    fulfilled = actual_price * min(G, Q)
    return {
        "planned_purchase_cost": actual_price * G,
        "fulfilled_normal_purchase_cost": fulfilled,
        "cancelled_purchase_principal": actual_price * down,
        "downward_adjustment_penalty": 0.5 * actual_price * down,
        "upward_adjustment_cost": 1.5 * actual_price * up,
        "regular_purchase_cost": fulfilled + 0.5 * actual_price * down + 1.5 * actual_price * up,
    }


def execute_with_actual_price(plan, slot, actual, history: PriceHistory, soc_before, params) -> ExecutedInterval:
    decision = actual.interval_end
    price = history.view(decision).get(actual.interval_start)
    if price is None:
        raise RuntimeError("Q4_3_SETTLEMENT_PRICE_MISSING")
    return execute_r0_interval(plan, slot, actual, float(price), soc_before, params)


def resettle_frozen_q3(row: ExecutedInterval, actual_price: float) -> ExecutedInterval:
    parts = model_b_regular_components(row.G, row.Q, actual_price)
    emergency = 5.0 * actual_price * row.E
    return replace(
        row,
        price=actual_price,
        **parts,
        emergency_purchase_cost=emergency,
        total_cost=parts["regular_purchase_cost"] + emergency,
        cost_semantics="MODEL_B",
    )


def settle_final_adjustment_once(G: float, final_Q: float, actual_price: float, emergency: float) -> float:
    """Settlement is path-independent: intermediate Q versions are intentionally absent."""
    return model_b_regular_components(G, final_Q, actual_price)["regular_purchase_cost"] + 5.0 * actual_price * emergency

