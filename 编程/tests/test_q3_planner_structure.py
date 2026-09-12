import unittest
from dataclasses import replace
from datetime import date, datetime
import numpy as np
from q3_baseline.config import Q3Parameters
from q3_baseline.planner import build_adjustment_milp
from tests.helpers_q3 import pv_selection

def row_coefficients(problem, name):
    i=problem.row_names.index(name); result=np.zeros(problem.num_col)
    start,end=problem.row_start[i:i+2]; result[problem.col_index[start:end]]=problem.values[start:end]
    return result,problem.row_lower[i]

class Q3PlannerStructureTests(unittest.TestCase):
    def problem(self,params=Q3Parameters(),no_storage=False):
        start=datetime(2025,2,1,7)
        return build_adjustment_milp(np.array([10.]),np.array([100.]),(pv_selection(date(2025,2,1),42,start),),np.array([2.]),6000.,params,no_storage=no_storage)
    def test_model_b_epigraph_and_exact_qmax(self):
        p=self.problem();q=p.layout
        self.assertEqual(p.col_upper[q.C.start],Q3Parameters().charge_power_max*Q3Parameters().delta_t);self.assertEqual(p.objective[q.Jregular.start],1.)
        left,rhs=row_coefficients(p,"regular_cost_left[0]");self.assertEqual((rhs,left[q.Q.start],left[q.Jregular.start]),(10.,-1.,1.))
        right,rhs=row_coefficients(p,"regular_cost_right[0]");self.assertEqual((rhs,right[q.Q.start]),(-10.,-3.))
    def test_model_a_sensitivity_epigraph_is_bounded(self):
        p=self.problem(replace(Q3Parameters(),cost_semantics="MODEL_A"));q=p.layout
        left,rhs=row_coefficients(p,"regular_cost_left[0]");self.assertEqual((rhs,left[q.Q.start]),(30.,1.));self.assertEqual(p.col_lower[q.Jregular.start],0.)
    def test_no_storage_and_current_soc(self):
        p=self.problem(no_storage=True);self.assertEqual(p.col_upper[p.layout.C.start],0.);self.assertEqual(p.col_upper[p.layout.D.start],0.)
        row=p.row_names.index("current_real_soc");self.assertEqual(p.row_lower[row],6000.)
    def test_soc_tolerance_snap(self):
        start=datetime(2025,2,1,7)
        p=build_adjustment_milp(np.array([10.]),np.array([100.]),(pv_selection(date(2025,2,1),42,start),),np.array([1.]),1199.9999995,Q3Parameters())
        row=p.row_names.index("current_real_soc");self.assertEqual(p.row_lower[row],1200.)
if __name__=="__main__":unittest.main()
