# 03. Brisbane replication, step 3: positive controls first (record, secondary): COVID-19 (month 0 2020-03) and George Floyd (month 0 2020-06),
# narrow level, through the Study 3b test (count model, placebo-category rank on z, placebo years). Brisbane closure months are marked.
# Output data/db/brisbane/controls.csv, report data/reports/brisbane_03_controls.md. Run with `python -I`.
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _bris as B

B3, S, INF, M = B.B3, B.S, B.INF, B.M
CONTROLS = [c for c in S.controls if c['name'] in ('covid19', 'covid', 'COVID-19') or 'covid' in c['name'].lower() or 'floyd' in c['name'].lower() or 'blm' in c['name'].lower() or 'race' in c['label'].lower()]


def monthly(world, node, m0):
    C = world.C[('seattle', 'narrow')]
    es = M.event_study(C, m0, S, rows=[C.index[node]], detail=True)
    st = world_status(world)
    d = pd.DataFrame({'rel': es['det_rel'], 'month': [B3.ym_of(m0 + r) for r in es['det_rel']], 'observed_loans_weighted': es['det_y'][0], 'expected': es['det_mu'][0]})
    d['ratio'] = d.observed_loans_weighted / d.expected
    d['usable'] = [bool(st.get(m0 + r, False)) for r in es['det_rel']]
    return d


def world_status(world):
    s = world._status
    return dict(zip(s.mi, s.month_ok))


def main():
    t0 = time.time()
    world, shifts = B.make_world()
    L = ['# Brisbane replication: positive controls (reported first)', '', f'- written: {time.strftime("%Y-%m-%d %H:%M:%S")}; Brisbane record SHA-256 `{B.SHA}`',
         f'- data: Brisbane library loans {B3.ym_of(world.C[("seattle", "narrow")].mi0)} to {B3.ym_of(world.last_month("seattle", "narrow"))}, formats pooled; model: Study 3b count model, one pooled series; window months 0 to +2',
         f'- pass reading (Study 3b): tau > 0 with one-sided placebo-category rank p < {S.alpha}', '']
    st = pd.read_parquet(B.DB / 'month_status.parquet')
    closed = [B3.ym_of(m) for m in st[~st.month_ok].mi]
    L += [f'- Brisbane months out of the data (closure rule or too few sampled days): {", ".join(closed)}', '']
    recs = []
    wanted = [('COVID-19', 'Epidemics and plagues', '2020-03'), ('George Floyd / BLM', 'Race and racism', '2020-06')]
    for name, label, ym in wanted:
        cats = world.cats['narrow']
        hit = cats[cats.label.str.lower() == label.lower()]
        if len(hit) != 1:
            raise SystemExit(f'control {label} not found exactly once')
        node = hit.index[0]
        m0 = B3.mi_from_ym(ym)
        r = INF.test_unit(world, 'seattle', 'narrow', node, m0)
        r['control'] = name
        recs.append(r)
        v = 'NOT TESTABLE (' + str(r.get('skip')) + ')' if r.get('skip') else ('PASS' if (r['tau_p'] > 0 and r['p_cat_p'] < S.alpha) else 'FAIL')
        L += [f'## {name}: {v}', '', f'{label} (narrow, {node}), month 0 = {ym}', '']
        if r.get('skip') == 'window too short':
            es = M.event_study(world.C[('seattle', 'narrow')], m0, S)                # every category, secondary window 0..+5 (descriptive only)
            C = world.C[('seattle', 'narrow')]
            i = C.index[node]
            par = world.parent_arr[('seattle', 'narrow')]
            ok = es['feasible'] & ~np.isnan(es['z_s']) & (par != par[i]) & ~world.near_mask('seattle', 'narrow', m0)
            ok[i] = False
            usable_p = [B3.ym_of(m0 + k) for k in range(0, 3) if world._status.set_index('mi').month_ok.get(m0 + k, False)]
            usable_s = [B3.ym_of(m0 + k) for k in range(0, 6) if world._status.set_index('mi').month_ok.get(m0 + k, False)]
            L += [f'The record\'s primary window (months 0 to +2) has only {len(usable_p)} usable Brisbane month(s) ({", ".join(usable_p) or "none"}); the rule needs at least {S.min_window_months}, so the control cannot be tested as the record specifies.',
                  f'Descriptive only, not the record\'s test: secondary window months 0 to +5 has {len(usable_s)} usable months ({", ".join(usable_s)}).']
            if not np.isnan(es['z_s'][i]):
                ps = M.rank_p(float(es['z_s'][i]), es['z_s'][ok])
                L += ['', f'Secondary window: tau_s = {es["tau_s"][i]:.3f} (ratio {np.exp(es["tau_s"][i]):.2f}), observed {es["sumy_s"][i]:.0f} against expected {es["summu_s"][i]:.0f} weighted loans, z = {es["z_s"][i]:.2f}, '
                      f'placebo-category rank p = {ps:.3f} among {int(ok.sum())} placebo themes.', '']
                r['tau_s_desc'], r['p_s_desc'] = float(es['tau_s'][i]), float(ps)
            else:
                L += ['', 'Secondary window also has too few usable months.', '']
            L += ['Monthly observed and expected weighted loans, months -6 to +5 (descriptive; "usable" false = out of the data):', '']
            L += B.IO.md_table(monthly(world, node, m0), floatfmt='{:.4g}') + ['']
        if not r.get('skip'):
            show = {k: r.get(k) for k in ('formats', 'phi', 'sumy_p', 'summu_p', 'tau_p', 'z_p', 'p_cat_p', 'n_placebos', 'too_sparse', 'tau_s', 'z_s', 'p_cat_s', 'tau_pre', 'py_share_ge', 'py_n')}
            L += B.IO.md_table(pd.DataFrame([show]), floatfmt='{:.4g}') + ['', f'tau 0 to +2 = {r["tau_p"]:.3f} (log lift; ratio {np.exp(r["tau_p"]):.2f}); sum observed {r["sumy_p"]:.0f} against expected {r["summu_p"]:.0f} weighted loans.', '']
            L += ['Monthly observed and expected weighted loans, months -6 to +5 (descriptive; "usable" false = a Brisbane closure month, left out of the model):', '']
            L += B.IO.md_table(monthly(world, node, m0), floatfmt='{:.4g}') + ['']
    out = pd.DataFrame(recs)
    out.to_csv(B.DB / 'controls.csv', index=False)
    (B.REP / 'brisbane_03_controls.md').write_text('\n'.join(L) + '\n')
    print('\n'.join(L)); print(f'{time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
