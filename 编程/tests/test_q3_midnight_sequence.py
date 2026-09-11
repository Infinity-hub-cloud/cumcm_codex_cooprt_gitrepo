from __future__ import annotations

import unittest

from q3_baseline.config import Q3Parameters
from q3_baseline.state_machine import soc_after_action


class Q3MidnightSequenceTests(unittest.TestCase):
    def test_slot144_action_determines_new_window_soc(self):
        params = Q3Parameters()
        result = soc_after_action(6000.0, 100.0, 45.0, params)
        self.assertAlmostEqual(result, 6040.0)

    def test_soc_outside_bounds_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "physical bounds"):
            soc_after_action(10800.0, 100.0, 0.0, Q3Parameters())

    def test_tolerance_scale_soc_drift_is_snapped_to_exact_boundary(self):
        params = Q3Parameters()
        self.assertEqual(params.normalize_soc(1199.9999995), 1200.0)
        self.assertEqual(params.normalize_soc(10800.0000005), 10800.0)
        self.assertEqual(soc_after_action(1199.9999995, 0.0, 0.0, params), 1200.0)

    def test_material_soc_violation_is_not_hidden_by_snapping(self):
        with self.assertRaisesRegex(ValueError, "value="):
            Q3Parameters().normalize_soc(1199.99)


if __name__ == "__main__":
    unittest.main()
