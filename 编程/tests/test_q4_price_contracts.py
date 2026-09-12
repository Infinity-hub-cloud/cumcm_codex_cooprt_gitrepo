from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta

from q4_baseline.config import Q4Parameters, load_config
from q4_baseline.price import CausalPriceView, PriceHistory, PriceRecord
from q4_baseline.runner import run_q4_2
from q4_baseline.reference import FrozenQ2Reference
from q2_baseline.config import load_config as load_q2_config
from q2_baseline.data import read_q2_inputs


def records(days: int = 21) -> tuple[PriceRecord, ...]:
    output = []
    start = datetime(2025, 1, 1)
    for day in range(days):
        for slot in range(144):
            left = start + timedelta(days=day, minutes=10 * slot)
            output.append(PriceRecord((start + timedelta(days=day)).date(), slot + 1, left, left + timedelta(minutes=10), 0.2 + 0.001 * slot + 0.01 * day))
    return tuple(output)


class Q4PriceContracts(unittest.TestCase):
    def test_timestamp_visibility_accepts_boundary_and_rejects_future(self):
        rows = records(2)
        decision = datetime(2025, 1, 2, 0, 0)
        view = CausalPriceView(rows, decision)
        self.assertIsNotNone(view.get(decision))
        with self.assertRaisesRegex(RuntimeError, "Q4_CAUSAL_PRICE_HARD_FAIL"):
            view.get(decision + timedelta(minutes=10))

    def test_all_predictors_are_positive_and_causal(self):
        history = PriceHistory(records(21), Q4Parameters())
        decision = datetime(2025, 1, 21)
        target = datetime(2025, 1, 21, 12, 10)
        for predictor in ("P0_RECENT_SAME_CLOCK", "P1_WEEKDAY_SAME_CLOCK", "P2_EWMA", "P3_SHAPE_LEVEL"):
            value, reason, hits, observed, source = history.predict(predictor, target, decision)
            self.assertGreater(value, 0)
            self.assertFalse(observed)
            self.assertEqual(source, "predicted")

    def test_price_forecast_uses_observed_at_decision(self):
        history = PriceHistory(records(2), Q4Parameters())
        decision = datetime(2025, 1, 2)
        value, reason, hits, observed, source = history.predict("P0_RECENT_SAME_CLOCK", decision, decision)
        self.assertTrue(observed)
        self.assertEqual(source, "observed_at_decision")
        self.assertEqual(value, history.by_start[decision].price)

    def test_production_rejects_old_visibility_rule_and_formal_run_is_gated(self):
        with self.assertRaises(ValueError):
            Q4Parameters(visibility_rule="INTERVAL_END_LE_DECISION_VISIBLE").validate()
        with self.assertRaises(PermissionError):
            run_q4_2("config/q4_baseline.json", "runs/q4_test_forbidden", "Q4_2_PRICE_BASELINE_P0")

    def test_frozen_q2_feb1_soc_bridge_is_read_only(self):
        config = load_config(__import__("pathlib").Path("config/q4_baseline.json").resolve())
        q2 = load_q2_config(config.q2_config)
        data = read_q2_inputs(q2.normalized_price_input, config.normalized_actual_input, q2.parameters)
        reference = FrozenQ2Reference(config.q2_reference_run / "dispatch_timeseries.csv", data)
        self.assertEqual(reference.initial_soc_feb1(), reference.plan(date(2025, 1, 31)).S[-1])


if __name__ == "__main__":
    unittest.main()
