from __future__ import annotations

import unittest
from datetime import date, datetime

from q2_baseline.time_axis import target_day
from q3_baseline.config import Q3Parameters
from q3_baseline.state_machine import soc_after_action
from q4_3_baseline.rolling import suffix_start_slot
from q4_3_baseline.runner import run_q4_3


class MidnightContracts(unittest.TestCase):
    def test_template_window_and_dec31_boundary(self):
        rows = target_day(date(2025,12,31))
        self.assertEqual(rows[0].interval_start, datetime(2025,12,31,0,10))
        self.assertEqual(rows[-1].interval_start, datetime(2026,1,1,0,0))
        self.assertEqual(rows[-1].interval_end, datetime(2026,1,1,0,10))

    def test_midnight_updates_only_prior_slot144(self):
        self.assertEqual(suffix_start_slot(date(2025,2,1), datetime(2025,2,2,0,0)), 144)
        self.assertEqual(suffix_start_slot(date(2025,2,1), datetime(2025,2,1,6,0)), 36)

    def test_action_implied_soc_bridge(self):
        params = Q3Parameters()
        value = soc_after_action(6000, 100, 0, params)
        self.assertAlmostEqual(value, 6090)
        q_max = params.charge_power_max * params.delta_t
        self.assertAlmostEqual(q_max, 5000/6)

    def test_formal_runner_requires_explicit_gate(self):
        with self.assertRaisesRegex(PermissionError, "not authorized"):
            run_q4_3("config/q4_3_baseline.json", "runs/SHOULD_NOT_EXIST_Q4_3_TEST", "Q4_3_PRICE_CANDIDATE_P2")


if __name__ == "__main__": unittest.main()
