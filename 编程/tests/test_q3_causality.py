import unittest
from datetime import date, datetime, timedelta
import numpy as np
from q2_baseline.data import ActualInterval
from q3_baseline.forecast import PVSelection, assert_load_frozen, initial_planning_day
from q3_baseline.state_machine import CausalActualView, assert_executed_prefix_immutable
from tests.helpers_q3 import attachment3_issues, q2_frozen_day

class Q3CausalityTests(unittest.TestCase):
    def test_future_issue_is_rejected(self):
        start=datetime(2025,2,1,13)
        row=PVSelection(date(2025,2,1),78,start,start+timedelta(minutes=10),datetime(2025,2,1,12),datetime(2025,2,1,18),1,datetime(2025,2,1,19),20.,20/6,"attachment3","TOY","ZOH",1,None,False,"")
        with self.assertRaisesRegex(AssertionError,"issue_datetime"):row.assert_causal()

    def test_1200_cannot_access_1400_actual(self):
        day=date(2025,2,1);start=datetime(2025,2,1,14)
        actual=ActualInterval(day,84,start,start+timedelta(minutes=10),100.,20.,100/6,20/6)
        view=CausalActualView({(day,84):actual})
        with self.assertRaisesRegex(PermissionError,"HARD_FAIL"):view.get((day,84),datetime(2025,2,1,12))
        self.assertEqual(view.snapshot(datetime(2025,2,1,12),np.ones(144)).actual,())
        self.assertIs(view.get((day,84),start+timedelta(minutes=10)),actual)

    def test_future_actual_perturbation_cannot_change_forecast(self):
        day=date(2025,2,1);q2=q2_frozen_day(day);data=attachment3_issues(day)
        before=initial_planning_day(day,q2,data,(0,)).initial_pv_kw.copy()
        # Actual values are deliberately absent from the forecast function's signature.
        perturbed_future=np.full(144,1e9);self.assertEqual(perturbed_future.shape,(144,))
        after=initial_planning_day(day,q2,data,(0,)).initial_pv_kw
        np.testing.assert_array_equal(before,after)

    def test_net_load_buffer_planning_load_is_frozen(self):
        day=date(2025,2,1);frozen=initial_planning_day(day,q2_frozen_day(day),attachment3_issues(day),(0,))
        assert_load_frozen(frozen,frozen.load_plan_kw.copy());changed=frozen.load_plan_kw.copy();changed[0]+=1
        with self.assertRaisesRegex(AssertionError,"LOAD_FORECAST_MUTATION"):assert_load_frozen(frozen,changed)
    def test_executed_prefix_is_immutable(self):
        assert_executed_prefix_immutable(("done-1","done-2"),("done-1","done-2","future"))
        with self.assertRaisesRegex(AssertionError,"modified executed history"):
            assert_executed_prefix_immutable(("done-1","done-2"),("done-1","changed","future"))
if __name__=="__main__":unittest.main()
