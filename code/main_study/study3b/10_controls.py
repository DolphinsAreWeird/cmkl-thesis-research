# 10. Positive controls (record, positive_controls): COVID-19 (Epidemics and plagues, 2020-03), George Floyd / BLM (Race and
# racism, 2020-06) and #MeToo (Sexual violence and domestic violence, 2017-10), all narrow. They are run first; no other Study
# 3b result is read until they are reported. For each control: the count event study, joint across the Seattle formats
# (per-format effects and LibriVox shown), the placebo-category rank p, and placebo years.
# Pass rule (record): tau > 0 with one-sided placebo-category p < 0.05 in the joint Seattle model. There is no size rule in
# Study 3b, so a control is untestable only when its model cannot be fitted (not feasible: fewer than 12 nonzero months in
# every format). A control with fewer than 5 expected weighted checkouts over the primary window is run but flagged too sparse.
# Also reported, descriptively and outside the pass rule: the values inside each control node (value level) and the monthly
# observed and expected weighted checkouts of the control (months -6 to +5).
# NOT IN RECORD: the reading of 'not testable' (model cannot be fitted) and the descriptive value-level controls (values whose parent node is the control node).
# Needs: the reports of 01 and 02. Output: data/db/study3b/controls.csv, controls_values.csv, report study3b_10_controls.md
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _s3
from _settings import SETTINGS as S
import _paths as IO
import _inference as INF
import _methods as M

B3 = _s3.build
SHOW = ['kind', 'formats', 'phi', 'sumy_p', 'summu_p', 'tau_p', 'z_p', 'p_cat_p', 'n_placebos', 'too_sparse', 'tau_s', 'z_s', 'p_cat_s',
        'tau_pre', 'py_share_ge', 'py_n']


def find_node(cats, label, level):
    m = cats[cats.label.str.lower() == label.lower()]
    if len(m) != 1:
        raise SystemExit(f'positive control "{label}" ({level}) not found exactly once among the {level} categories')
    return m.index[0]


def verdict(rec):
    if rec.get('skip', 'no counts') != '':
        return f'NOT TESTABLE ({rec.get("skip")})'
    return 'PASS' if (rec['tau_p'] > 0 and rec['p_cat_p'] < S.alpha) else 'FAIL'


def monthly_table(world, node, m0):
    C = world.C[('seattle', 'narrow')]
    es = M.event_study(C, m0, S, rows=[C.index[node]], detail=True)
    return pd.DataFrame({'month': es['det_rel'], 'observed': es['det_y'][0], 'expected': es['det_mu'][0]}).assign(ratio=lambda d: d.observed / d.expected)


def main():
    ap = IO.parser('Study 3b positive controls')
    args, P, meta, warn = IO.start('10', ap)
    shifts = INF.load_shifts(P, S)
    world = INF.World(P, S, shifts)
    recs, status, lines, vrows = [], {}, [], []
    for c in S.controls:
        node = find_node(world.cats['narrow'], c['label'], c['level'])
        m0 = B3.mi_from_ym(c['shift_month'])
        r = INF.test_unit(world, 'seattle', 'narrow', node, m0)
        v = verdict(r)
        status[c['name']] = v
        rs = [r]
        if ('librivox', 'narrow') in world.C:
            rs.append(INF.test_unit(world, 'librivox', 'narrow', node, m0))
        for x in rs:
            x['control'] = c['name']
        recs += rs
        T = pd.DataFrame(rs)
        lines += [f'### {c["name"]}: {v}', '', f'{c["label"]} (narrow, {node}), month 0 = {c["shift_month"]}', '']
        lines += IO.md_table(T.reindex(columns=['control'] + SHOW)) + ['']
        if r.get('skip') == '':
            pf = pd.DataFrame([dict(format=f, sumy_p=r[f'sumy_p_{f}'], summu_p=r[f'summu_p_{f}'], tau_p=r[f'tau_p_{f}'], z_p=r[f'z_p_{f}'],
                                    tau_s=r[f'tau_s_{f}'], z_s=r[f'z_s_{f}']) for f in S.seattle_formats])
            lines += ['Per format (secondary; z uses the joint dispersion):', ''] + IO.md_table(pf) + ['']
            lines += ['Monthly observed and expected weighted checkouts, months -6 to +5 (joint model, descriptive):', ''] + IO.md_table(monthly_table(world, node, m0)) + ['']
        # values inside the control node (descriptive)
        vals = world.cats['value'][world.cats['value'].parent == node].index
        tab = world.ztable('seattle', 'value', m0)
        for val in vals:
            vr = INF.test_unit(world, 'seattle', 'value', val, m0, tab, placebo_years_on=False)
            vr['control'] = c['name']
            if vr.get('skip') == '':
                vrows.append({k: vr.get(k) for k in ['control', 'node_id', 'formats', 'summu_p', 'tau_p', 'z_p', 'p_cat_p', 'n_placebos', 'too_sparse']})
    ok = all(v.startswith('PASS') or v.startswith('NOT TESTABLE') for v in status.values())
    IO.save_csv(pd.DataFrame(recs), P.out('controls.csv'))
    V = pd.DataFrame(vrows)
    IO.save_csv(V, P.out('controls_values.csv'))
    head = [f'- controls status: {"PASS" if ok else "FAIL"}'] + [f'- control {k}: {v}' for k, v in status.items()]
    head += [f'- shift screen for placebos: applied ({len(shifts)} interest shifts, narrow, middle and value)'] + [f'- WARNING: {w}' for w in warn]
    head += ['', f'Pass rule: tau_p > 0 with one-sided placebo-category rank p < {S.alpha} in the joint Seattle model (months {S.window_primary[0]} to +{S.window_primary[1]}). '
             'tau = log(sum Y / sum mu); z = tau / sqrt(phi / sum mu); p_cat = (1 + number of placebo categories with z >= treated z) / (placebos + 1); '
             '_s = months 0 to +5; py_share_ge = share of placebo years with z at or above the treated z. LibriVox is shown and does not decide.', '']
    if not ok:
        head += ['If a control fails (record): check data and mappings for errors only; log any fix in prereg/DEVIATIONS.md; do not tune settings on other '
                 'categories. Step 11 refuses to run until --accept-failed-controls is given.', '']
    L = head + lines + ['### Values inside the control nodes (descriptive, outside the pass rule)', '']
    if len(V):
        agg = V.groupby('control').agg(values_tested=('node_id', 'size'), tau_p_median=('tau_p', 'median'), share_tau_positive=('tau_p', lambda x: float((x > 0).mean())),
                                       share_p_below_alpha=('p_cat_p', lambda x: float((x < S.alpha).mean())), too_sparse=('too_sparse', 'sum')).reset_index()
        L += IO.md_table(agg) + ['', 'Single values are in controls_values.csv.']
    else:
        L += ['(no value could be tested)']
    path = IO.write_report(P, '10', 'Study 3b positive controls', L, S, meta)
    print('\n'.join(head))
    print('report:', path)


if __name__ == '__main__':
    main()
