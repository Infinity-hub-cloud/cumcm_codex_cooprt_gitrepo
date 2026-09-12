"""Independent CSV reconciliation. No model imports, solve, or workbook writes."""
import csv
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE / 'runs' / 'q3_20260912_032050'
OUT = BASE / '审计' / 'Q3_独立审计_20260912' / 'run_reconciliation.json'

def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def main():
    evidence = {}
    for track in ('Q3_ATTACHMENT3_0ONLY', 'Q3_ROLLING_4ISSUE_retry_socfix_indexed', 'Q3_NOSTORAGE_REFERENCE'):
        directory = ROOT / track
        data = rows(directory / 'dispatch_timeseries.csv')
        manifest = json.loads((directory / 'run_manifest.json').read_text(encoding='utf-8-sig'))
        residuals = dict(balance=0., soc_transition=0., soc_continuity=0., cost_A=0., nonnegative_violation=0., physical_violation=0.)
        formal_cost = 0.
        last_soc = None
        versions = rows(directory / 'plan_versions.csv')
        initial = {}
        latest = {}
        late_decisions = future_issues = changed_G = 0
        for row in versions:
            key = (row['template_date'], row['template_slot'])
            g = float(row['G_initial'])
            if key in initial and abs(g-initial[key]) > 1e-7:
                changed_G += 1
            initial.setdefault(key, g)
            latest[key] = row
            late_decisions += row['decision_time'] > row['interval_start']
            future_issues += bool(row['issue_datetime']) and row['issue_datetime'] > row['decision_time']
        version_error = 0.
        for row in data:
            num = lambda name: float(row[name])
            g,q,c,d,e,w = (num(n) for n in ('grid_plan_kwh','grid_final_kwh','charge_bus_kwh','discharge_bus_kwh','grid_emergency_kwh','spill_kwh'))
            before,after,p = (num(n) for n in ('soc_before','soc_after','price'))
            cost = p*g + .5*p*max(g-q,0.) + 1.5*p*max(q-g,0.) + 5*p*e
            residuals['balance'] = max(residuals['balance'],abs(q+e+num('pv_actual_kwh')+d-num('load_actual_kwh')-c-w))
            residuals['soc_transition'] = max(residuals['soc_transition'],abs(after-before-.9*c+d/.9))
            residuals['cost_A'] = max(residuals['cost_A'],abs(cost-num('total_cost')))
            residuals['nonnegative_violation'] = max(residuals['nonnegative_violation'],-min(g,q,c,d,e,w))
            residuals['physical_violation'] = max(residuals['physical_violation'],1200-min(before,after),max(before,after)-10800,c-5000/6,d-5000/6,min(c,d))
            if last_soc is not None:
                residuals['soc_continuity'] = max(residuals['soc_continuity'],abs(before-last_soc))
            last_soc = after
            if row['template_date'] >= '2025-02-01':
                formal_cost += cost
            v = latest[(row['template_date'],row['template_slot'])]
            version_error = max(version_error,abs(g-float(v['G_initial'])),abs(q-float(v['Q_version'])),abs(c-float(v['C_version'])),abs(d-float(v['D_version'])))
        updates = rows(directory / 'solver_updates.csv')
        evidence[track] = {
            'rows':len(data), 'formal_cost_recomputed_A':formal_cost,
            'formal_cost_manifest_difference':formal_cost-manifest['metrics']['total_cost'],
            'max_residuals':residuals, 'G_changes_in_versions':changed_G,
            'version_decisions_after_interval_start':late_decisions,
            'version_issue_after_decision':future_issues,
            'max_last_version_vs_dispatch_error':version_error,
            'solver_update_records':len(updates),
            'solver_log_files':len(list((directory/'_solver_logs').glob('*'))),
            'dispatch_sha256':hashlib.sha256((directory/'dispatch_timeseries.csv').read_bytes()).hexdigest(),
            'scope_note':'CSV arithmetic and emitted timestamps only; not proof of runtime access isolation or all workbook cells.'
        }
    with OUT.open('x', encoding='utf-8') as f:
        json.dump(evidence,f,ensure_ascii=False,indent=2)
    print(OUT)

if __name__ == '__main__':
    main()
