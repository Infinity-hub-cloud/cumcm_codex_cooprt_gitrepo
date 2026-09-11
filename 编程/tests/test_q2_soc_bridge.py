from __future__ import annotations

import unittest

from q2_baseline.config import Q2Parameters
from q2_baseline.planner import compute_window_start_soc


class Q2SocBridgeTests(unittest.TestCase):
    def test_bridge_executes_committed_previous_slot144(self) -> None:
        params = Q2Parameters()
        result = compute_window_start_soc(6000.0, 100.0, 45.0, params)
        self.assertAlmostEqual(result, 6040.0)

    def test_bridge_does_not_reset_feb1(self) -> None:
        params = Q2Parameters()
        result = compute_window_start_soc(4321.0, 0.0, 0.0, params)
        self.assertEqual(result, 4321.0)
        self.assertNotEqual(result, params.soc_initial)


if __name__ == "__main__":
    unittest.main()

