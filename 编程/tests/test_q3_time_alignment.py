import unittest
from dataclasses import replace
from datetime import date, datetime, time, timedelta

from q2_baseline.time_axis import target_interval
from q2_baseline.forecast import COLD_START_SOURCE, ForecastDay
from q3_baseline.attachment3 import Attachment3Data
from q3_baseline.forecast import FALLBACK_Q2_PV_SOURCE, initial_planning_day, pv_for_unexecuted
from q3_baseline.state_machine import interval_state
from tests.helpers_q3 import attachment3_issues, q2_frozen_day

def combine(*items: Attachment3Data) -> Attachment3Data:
    return Attachment3Data(tuple(row for item in items for row in item.rows), items[0].mapping_method,
                           {key: value for item in items for key, value in item.by_issue.items()})

class Q3TimeAlignmentTests(unittest.TestCase):
    def test_lead_1_2_24_for_all_official_issues(self):
        day=date(2025,6,21);data=attachment3_issues(day)
        for hour in (0,6,12,18):
            issue=datetime.combine(day,time.min)+timedelta(hours=hour)
            values=data.by_issue[issue].values()
            for lead in (1,2,24):
                selected=[row for row in values if row.lead_hour==lead]
                self.assertTrue(selected)
                self.assertTrue(all(row.target_time==issue+timedelta(hours=lead) for row in selected))
    def test_0only_first_five_fallback_then_139_point_rows(self):
        day = date(2025, 2, 1)
        frozen = initial_planning_day(day, q2_frozen_day(day), attachment3_issues(day, (0,)), (0,))
        self.assertEqual([r.forecast_source for r in frozen.initial_pv[:5]], [FALLBACK_Q2_PV_SOURCE] * 5)
        self.assertEqual(sum(r.forecast_source == "attachment3" for r in frozen.initial_pv), 139)
        self.assertEqual(frozen.initial_pv[5].lead_hour, 1)
        self.assertTrue(frozen.initial_pv[143].endpoint_hold)
        self.assertEqual(frozen.initial_pv[143].lead_hour, 24)

    def test_jan1_cold_start_has_no_previous_issue(self):
        day=date(2025,1,1)
        base=q2_frozen_day(day)
        cold=ForecastDay(day,tuple(replace(row,forecast_source=COLD_START_SOURCE,source_interval_start=None,source_interval_end=None,load_source_interval_start=None,load_source_interval_end=None,load_pred_kw=0.,pv_pred_kw=0.,risk_buffer_kw=0.,buffer_sample_count=0,buffer_source_start=None,buffer_source_end=None) for row in base.rows))
        frozen=initial_planning_day(day,cold,attachment3_issues(day),(0,360,720,1080))
        self.assertTrue(cold.cold_mask.all())
        self.assertTrue(all(row.forecast_source==FALLBACK_Q2_PV_SOURCE for row in frozen.initial_pv[:5]))

    def test_full_rolling_first_hour_uses_previous_18_issue(self):
        day = date(2025, 2, 1)
        data = combine(attachment3_issues(day - timedelta(days=1)), attachment3_issues(day))
        frozen = initial_planning_day(day, q2_frozen_day(day), data, (0, 360, 720, 1080))
        self.assertTrue(all(r.issue_datetime == datetime(2025, 1, 31, 18) for r in frozen.initial_pv[:5]))
        self.assertTrue(all(r.issue_datetime == datetime(2025, 2, 1) for r in frozen.initial_pv[5:]))

    def test_issue_set_zero_cannot_use_other_published_issues(self):
        day = date(2025, 2, 1)
        data = attachment3_issues(day)
        frozen = initial_planning_day(day, q2_frozen_day(day), data, (0,))
        rows = pv_for_unexecuted(frozen, data, datetime(2025, 2, 1, 12), (0,))
        self.assertTrue(all(r.issue_datetime in (None, datetime(2025, 2, 1)) for r in rows))

    def test_new_issue_first_hour_keeps_previous_issue(self):
        day = date(2025, 2, 1)
        data = attachment3_issues(day)
        frozen = initial_planning_day(day, q2_frozen_day(day), data, (0, 360, 720, 1080))
        rows = pv_for_unexecuted(frozen, data, datetime(2025, 2, 1, 6), (0, 360, 720, 1080))
        self.assertEqual(rows[0].interval_start, datetime(2025, 2, 1, 6))
        self.assertEqual(rows[0].issue_datetime, datetime(2025, 2, 1))
        at_seven = next(r for r in rows if r.interval_start == datetime(2025, 2, 1, 7))
        self.assertEqual(at_seven.issue_datetime, datetime(2025, 2, 1, 6))

    def test_no_cross_issue_interpolation(self):
        day = date(2025, 2, 1)
        rows = attachment3_issues(day, method="INTERP").rows
        self.assertTrue(all(r.interpolation_right_lead in (None, r.lead_hour + 1) for r in rows))
        self.assertTrue(all(r.target_time == r.issue_datetime + timedelta(hours=r.lead_hour) for r in rows))

    def test_closed_open_decision_boundaries(self):
        day = date(2025, 2, 1)
        for hour, frozen_slot, adjustable_slot in ((6, 35, 36), (12, 71, 72), (18, 107, 108)):
            decision = datetime(2025, 2, 1, hour)
            self.assertEqual(interval_state(target_interval(day, frozen_slot), decision), "frozen")
            self.assertEqual(interval_state(target_interval(day, adjustable_slot), decision), "adjustable")

    def test_midnight_old_slot144_uses_prior_18_not_new_00(self):
        day = date(2025, 2, 1)
        data = combine(attachment3_issues(day), attachment3_issues(day + timedelta(days=1), (0,)))
        frozen = initial_planning_day(day, q2_frozen_day(day), data, (0, 360, 720, 1080))
        rows = pv_for_unexecuted(frozen, data, datetime(2025, 2, 2), (0, 360, 720, 1080))
        self.assertEqual([r.template_slot for r in rows], [144])
        self.assertEqual(rows[0].issue_datetime, datetime(2025, 2, 1, 18))

    def test_dec31_boundary_has_no_fictitious_issue(self):
        day = date(2025, 12, 31)
        data = attachment3_issues(day)
        frozen = initial_planning_day(day, q2_frozen_day(day), data, (0, 360, 720, 1080))
        rows = pv_for_unexecuted(frozen, data, datetime(2026, 1, 1), (0, 360, 720, 1080))
        self.assertEqual(rows[0].issue_datetime, datetime(2025, 12, 31, 18))

if __name__ == "__main__": unittest.main()
