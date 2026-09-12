from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta

from q4_baseline.config import Q4Parameters
from q4_3_baseline.forecast_adapter import build_rolling_price_forecast
from q4_3_baseline.price import CausalPriceView, PriceHistory, PriceRecord
from q4_3_baseline.rolling import observed_boundary_contract_count
from q4_3_baseline.runner import validate_input_only


def records(days: int = 40) -> tuple[PriceRecord, ...]:
    start = datetime(2025, 1, 1)
    rows = []
    for i in range(days * 144 + 1):
        stamp = start + timedelta(minutes=10 * i)
        rows.append(PriceRecord(stamp.date(), i % 144 + 1, stamp, stamp + timedelta(minutes=10), 0.5 + (i % 144) / 500))
    return tuple(rows)


class PriceContracts(unittest.TestCase):
    def test_boundary_visible_future_hard_fail(self):
        rows = records(2); decision = datetime(2025, 1, 2, 6)
        view = CausalPriceView(rows, decision)
        self.assertIsNotNone(view.get(decision))
        with self.assertRaisesRegex(RuntimeError, "Q4_CAUSAL_PRICE_HARD_FAIL"):
            view.get(decision + timedelta(minutes=10))

    def test_all_predictors_ignore_future_perturbation(self):
        base = records(40); decision = datetime(2025, 2, 1, 6); target = decision + timedelta(hours=2)
        altered = tuple(
            PriceRecord(r.source_date, r.interval_index, r.interval_start, r.interval_end, r.price * (100 if r.interval_start > decision else 1))
            for r in base
        )
        for predictor in ("P0_RECENT_SAME_CLOCK", "P1_WEEKDAY_SAME_CLOCK", "P2_EWMA", "P3_SHAPE_LEVEL"):
            left = PriceHistory(base, Q4Parameters()).predict(predictor, target, decision)[0]
            right = PriceHistory(altered, Q4Parameters()).predict(predictor, target, decision)[0]
            self.assertAlmostEqual(left, right)

    def test_0600_boundary_and_no_future_actual_in_planner_payload(self):
        history = PriceHistory(records(40), Q4Parameters())
        result = build_rolling_price_forecast(date(2025, 2, 1), datetime(2025, 2, 1, 6), "P2_EWMA", history)
        self.assertEqual(sum(bool(row["observed_at_decision"]) for row in result.rows), 1)
        self.assertTrue(all(row["price_actual"] is None for row in result.rows))
        self.assertEqual(result.rows[0]["physical_interval_start"], datetime(2025, 2, 1, 6))

    def test_formal_boundary_contract(self):
        self.assertEqual(observed_boundary_contract_count(334), 1002)

    def test_frozen_q3_and_interp_identity(self):
        result = validate_input_only("config/q4_3_baseline.json")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["attachment3_point_interp"]["mapped_rows"], 202940)
        self.assertEqual(result["attachment3_point_interp"]["mismatches"], 0)
        self.assertAlmostEqual(result["feb1_initial_soc"], 1200.0)


if __name__ == "__main__": unittest.main()
