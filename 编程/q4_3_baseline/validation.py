from __future__ import annotations

from datetime import date
from typing import Iterable

import numpy as np

from .rolling import observed_boundary_contract_count


def validate_formal_run(config, plans, executed, price_rows, solver_updates) -> dict[str, object]:
    failures: list[str] = []
    if len(plans) != 334 or len(executed) != 334 * 144:
        failures.append("formal_cardinality")
    ordered = sorted(executed, key=lambda row: row.interval_start)
    max_balance = max_soc_residual = 0.0
    for left, right in zip(ordered, ordered[1:]):
        if left.interval_end != right.interval_start:
            failures.append(f"physical_gap:{left.interval_end}"); break
        if abs(left.soc_after - right.soc_before) > config.parameters.feasibility_tolerance:
            failures.append(f"soc_discontinuity:{right.interval_start}"); break
    qmax = config.parameters.charge_power_max * config.parameters.delta_t
    for row in ordered:
        if row.C > qmax + config.parameters.feasibility_tolerance or row.D > qmax + config.parameters.feasibility_tolerance:
            failures.append(f"exact_power_bound:{row.interval_start}"); break
        if row.C > config.parameters.feasibility_tolerance and row.D > config.parameters.feasibility_tolerance:
            failures.append(f"mutex:{row.interval_start}"); break
        expected_regular = row.price * min(row.G, row.Q) + 0.5 * row.price * max(row.G-row.Q, 0.0) + 1.5 * row.price * max(row.Q-row.G, 0.0)
        if abs(expected_regular - row.regular_purchase_cost) > config.parameters.aggregate_tolerance:
            failures.append(f"actual_price_model_b:{row.interval_start}"); break
        max_balance = max(max_balance, abs(row.Q + row.pv_actual_kwh + row.D + row.E - row.load_actual_kwh - row.C - row.W))
        max_soc_residual = max(max_soc_residual, abs(row.soc_after - row.soc_before - config.parameters.charge_efficiency*row.C + row.D/config.parameters.discharge_efficiency))
    boundary_count = sum(
        bool(row["observed_at_decision"]) and row["update_time"].hour in (6, 12, 18)
        for row in price_rows
        if date.fromisoformat(str(row["template_date"])) >= config.output_start
    )
    if boundary_count != observed_boundary_contract_count():
        failures.append(f"observed_boundary_count:{boundary_count}")
    if any(row["physical_interval_start"] < row["decision_time"] for row in price_rows):
        failures.append("price_rewrites_executed_prefix")
    if any(row["visibility_rule"] != config.visibility_rule for row in price_rows):
        failures.append("price_visibility_rule")
    failed_updates = sum(str(row.get("solver_status", "")).upper() not in {"OPTIMAL", "REFERENCE_ONLY_NO_SOLVE"} for row in solver_updates)
    return {
        "passed": not failures, "failures": failures,
        "observed_06_12_18_count": boundary_count,
        "expected_observed_06_12_18_count": 1002,
        "max_balance_residual": max_balance,
        "max_soc_residual": max_soc_residual,
        "qmax_internal": qmax,
        "failed_updates": failed_updates,
    }

