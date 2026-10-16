# 15. Backlist robustness (addendum prereg/addenda_3b/2026-10-14_b_backlist_robustness.json, made after the 3b results were seen):
# the 3b positive controls (10) and all-shift tests (12) rerun with demand restricted to backlist works, i.e. works whose first
# checkout in any Seattle format is at least 13 months before month 0 of the test. Same shifts, model, windows, placebo ranking
# (placebo categories at the same month 0 on the same restricted demand; placebo years each at their own month 0), BH families,
# pooling and bootstrap as in 3b. Reported beside the main 3b results, never instead of them. Seattle only (no LibriVox).
# NOT IN RECORD: see the header of _backlist.py (first-checkout definition, exposure unchanged, LibriVox not run, separate z cache).
# Run (one process, from code/main_study/study3b/):  nice -n 10 ../../../.venv/bin/python 15_backlist.py
# Needs the reports of 01 and 12 on the same panel build. Writes data/db/study3b/backlist_*.csv/parquet, ztables_backlist/,
# data/reports/study3b_15_backlist.md and study3b_15_backlist_*.csv. Existing outputs are only read.
import sys, pathlib, time, importlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _s3
from _settings import SETTINGS as S
import _paths as IO
import _inference as INF
import _methods as M
import _panel as PN
import _backlist as BL

B3 = _s3.build
SH = importlib.import_module('12_shifts')          # plan columns, BH, pooling and summary functions are reused unchanged
DATA = pathlib.Path(IO.D)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def find_node(cats, label):
    m = cats[cats.label.str.lower() == label.lower()]
    if len(m) != 1:
        raise SystemExit(f'positive control "{label}" not found exactly once')
    return m.index[0]


def verdict(r):
    if r.get('skip', 'no counts') != '':
        return f'NOT TESTABLE ({r.get("skip")})'
    return 'PASS' if (r['tau_p'] > 0 and r['p_cat_p'] < S.alpha) else 'FAIL'


def monthly(world, node, m0):
    C = world.C[('seattle', 'narrow')]
    es = M.event_study(C, m0, S, rows=[C.index[node]], detail=True)
    return pd.DataFrame({'month': es['det_rel'], 'observed': es['det_y'][0], 'expected': es['det_mu'][0]}).assign(ratio=lambda d: d.observed / d.expected)


def verify_unrestricted(world):
    """Sanity check of the new builder: with every work eligible it must give the 3b panel (counts_seattle.parquet)."""
    out = []
    P = world.P
    for lv in S.levels_tested:
        cum = world.bl.cum[lv]
        cum.advance(cum.Wm.shape[0])
        ids = np.asarray(sorted(world.cats[lv].index))
        pos = world.bl.cat_pos[lv].reindex(ids).fillna(-1).to_numpy().astype(int)
        long = pd.read_parquet(P.counts, filters=[('level', '==', lv)])
        main = PN.make_counts(long, world._status, lv, ids, list(S.seattle_formats))
        worst = 0.0
        for f in S.seattle_formats:
            mine = np.zeros_like(main.Y[f])
            mine[pos >= 0] = cum.D[f][pos[pos >= 0]]
            kp = world.bl.keep.get(lv, {}).get(f)
            if kp is not None:
                mine[pos >= 0] *= kp[pos[pos >= 0]][:, None]
            mine[:, ~main.ok[f]] = np.nan
            d = np.nanmax(np.abs(mine - main.Y[f]) / np.maximum(1.0, np.abs(main.Y[f])))
            worst = max(worst, float(d))
        out.append((lv, worst))
        del long, main
        cum.reset()
    return out


def share_of_main(world, node, m0):
    """Backlist share of the node's weighted checkouts in months -6..+5 (descriptive), from the stored main counts."""
    return None


def main():
    ap = IO.parser('Study 3b backlist robustness')
    ap.add_argument('--boot', type=int, default=None, help='simulation runs only')
    args = ap.parse_args()
    if args.sim:
        raise SystemExit('15 runs on real data only (tests use _backlist.py directly)')
    P = IO.Paths(None)
    meta = IO.load_meta(P)
    IO.require_previous(P, '13', meta)             # needs report 12 on this panel build
    t0 = time.time()
    shifts = INF.load_shifts(P, S)
    log(f'backlist lag = {BL.BACKLIST_MONTHS} months (read from the addendum)')
    builder = BL.build_real(P, S)
    world = BL.BacklistWorld(P, S, shifts, builder)
    log('builder ready')
    ver = verify_unrestricted(world)
    log('unrestricted check against counts_seattle:', ver)
    for lv, d in ver:
        if d > 1e-6:
            raise SystemExit(f'backlist builder does not reproduce the 3b panel at level {lv} (max relative difference {d:.2e})')

    # ---------------- controls ----------------
    main_ctrl = pd.read_csv(P.out('controls.csv'))
    recs, lines, vrows, mrows, status = [], [], [], [], {}
    for c in S.controls:
        node = find_node(world.cats['narrow'], c['label'])
        m0 = B3.mi_from_ym(c['shift_month'])
        world.set_m0(m0)
        r = INF.test_unit(world, 'seattle', 'narrow', node, m0)
        r['control'] = c['name']
        status[c['name']] = verdict(r)
        recs.append(r)
        if r.get('skip') == '':
            mt = monthly(world, node, m0).assign(control=c['name'])
            mrows.append(mt)
        tab = world.ztable('seattle', 'value', m0)
        for val in world.cats['value'][world.cats['value'].parent == node].index:
            vr = INF.test_unit(world, 'seattle', 'value', val, m0, tab, placebo_years_on=False)
            if vr.get('skip') == '':
                vrows.append({'control': c['name'], **{k: vr.get(k) for k in ['node_id', 'formats', 'summu_p', 'tau_p', 'z_p', 'p_cat_p', 'n_placebos', 'too_sparse']}})
        log('control', c['name'], status[c['name']])
    CB = pd.DataFrame(recs)
    CM = main_ctrl[main_ctrl.kind == 'seattle'].set_index('control')
    rows = []
    for r in recs:
        m = CM.loc[r['control']]
        mv = 'PASS' if (m.tau_p > 0 and m.p_cat_p < S.alpha) else 'FAIL'
        rows.append(dict(control=r['control'], main_tau=m.tau_p, main_p=m.p_cat_p, main_verdict=mv, main_tau_pre=m.tau_pre, main_sumy=m.sumy_p,
                         backlist_tau=r['tau_p'], backlist_p=r['p_cat_p'], backlist_verdict=status[r['control']], backlist_z=r['z_p'],
                         backlist_tau_s=r['tau_s'], backlist_p_s=r['p_cat_s'], backlist_tau_pre=r['tau_pre'], backlist_sumy=r['sumy_p'],
                         backlist_share_of_main_y=r['sumy_p'] / m.sumy_p, backlist_phi=r['phi'], main_phi=m.phi,
                         n_placebos=r['n_placebos'], placebo_years=r.get('py_n'), py_share_ge=r.get('py_share_ge')))
    CT = pd.DataFrame(rows)
    IO.save_csv(CT, DATA / 'reports' / 'study3b_15_backlist_controls.csv')
    IO.save_csv(CB, P.out('backlist_controls.csv'))
    V = pd.DataFrame(vrows)
    IO.save_csv(V, P.out('backlist_controls_values.csv'))
    MT = pd.concat(mrows, ignore_index=True)

    # ---------------- all shifts ----------------
    ok = shifts.quality_ok
    s = shifts[shifts.labelled & ok & shifts.level.isin(S.levels_tested) & (shifts.m0 >= B3.mi_from_ym(S.study_start))]
    have = {lv: set(world.cats[lv].index) for lv in S.levels_tested}
    s = s[[n in have[lv] for lv, n in zip(s.level, s.node_id)]]
    units = s.groupby(['level', 'm0']).node_id.apply(lambda x: sorted(set(x))).reset_index()
    res = []
    for lv in S.levels_tested:
        u = units[units.level == lv].sort_values('m0')
        for k, r in enumerate(u.itertuples()):
            m0 = int(r.m0)
            world.set_m0(m0)
            tab = world.ztable('seattle', lv, m0)
            res += [INF.test_unit(world, 'seattle', lv, n, m0, tab) for n in r.node_id]
            if k % 10 == 0:
                log(f'{lv}: month 0 {k + 1}/{len(u)}')
    T = pd.DataFrame(res)
    R = s.reindex(columns=SH.SHIFT_COLS).merge(T.drop(columns=['broad_id', 'label'], errors='ignore'), on=['level', 'node_id', 'm0'], how='inner')
    R['broad_id'] = [world.cats[lv].broad_id.get(n) for lv, n in zip(R.level, R.node_id)]
    R['analysis'] = np.where(R.seasonal, 'seasonal', 'main')
    for c in ('too_sparse', 'y_zero'):
        R[c] = R[c].fillna(False).astype(bool) if c in R else False
    R = SH.add_q(R)
    IO.save_parquet(R.drop(columns=['py_years'], errors='ignore'), P.out('backlist_shift_effects.parquet'))
    n_boot = IO.sim_only(args, 'boot', S.boot_n)
    PT = pd.concat([SH.pooled(R, n_boot, False), SH.pooled(R, n_boot, True)], ignore_index=True)
    IO.save_csv(PT, P.out('backlist_pooled_effects.csv'))

    # ---------------- comparison with the main 3b run ----------------
    RM = pd.read_parquet(P.out('shift_effects.parquet'))
    PM = pd.read_csv(P.out('pooled_effects.csv'))
    keys = ['analysis', 'source', 'level', 'duration_class']
    pm = PM[(PM.include_sparse == False)]                                         # noqa: E712
    pb = PT[(PT.include_sparse == False)]                                         # noqa: E712
    cmp_ = pm[keys + ['tests', 'tau_p_mean', 'tau_p_ci_low', 'tau_p_ci_high']].merge(
        pb[keys + ['tests', 'tau_p_mean', 'tau_p_ci_low', 'tau_p_ci_high', 'share_p_below_alpha']], on=keys, how='outer', suffixes=('_main', '_backlist'))
    IO.save_csv(cmp_, DATA / 'reports' / 'study3b_15_backlist_pooled.csv')

    def supp(Rx):
        z = Rx[(Rx.skip == '') & ~Rx.too_sparse.fillna(False).astype(bool) & (Rx.analysis == 'main')].replace([np.inf, -np.inf], np.nan)
        out = []
        for (cl, lvs), g in [(('sustained', 'all levels'), z[z.duration_class == 'sustained']), (('fading', 'all levels'), z[z.duration_class == 'fading'])]:
            b = M.cluster_boot_mean(g.tau_p.to_numpy(), (g.level + g.node_id).to_numpy(), n_boot, S.boot_seed)
            out.append(dict(duration_class=cl, scope=lvs, tests=b['n'], tau_mean=b['mean'], ci_low=b.get('low'), ci_high=b.get('high')))
        return pd.DataFrame(out)
    SM, SB = supp(RM), supp(R)
    sup = SM.merge(SB, on=['duration_class', 'scope'], suffixes=('_main', '_backlist'))

    def det(Rx):
        z = Rx[(Rx.skip == '') & ~Rx.too_sparse.fillna(False).astype(bool)]
        return z.groupby(['analysis', 'level']).agg(tests=('p_cat_p', 'size'), p_below_005=('p_cat_p', lambda x: int((x < S.alpha).sum())),
                                                    bh_q_below_010=('detected_bh', lambda x: int(x.fillna(False).sum())), mean_tau=('tau_p', lambda x: float(x.replace([np.inf, -np.inf], np.nan).mean()))).reset_index()
    dm, db_ = det(RM), det(R)
    dd = dm.merge(db_, on=['analysis', 'level'], suffixes=('_main', '_backlist'))
    dd['share_p_below_005_main'] = dd.p_below_005_main / dd.tests_main
    dd['share_p_below_005_backlist'] = dd.p_below_005_backlist / dd.tests_backlist

    # paired change in tau for the same shift tests (main analysis, non-sparse in both runs)
    pr = RM[(RM.skip == '') & (RM.analysis == 'main')][['shift_id', 'level', 'tau_p', 'too_sparse']].merge(
        R[(R.skip == '') & (R.analysis == 'main')][['shift_id', 'tau_p', 'too_sparse']], on='shift_id', suffixes=('_main', '_backlist'))
    pr = pr[~pr.too_sparse_main.astype(bool) & ~pr.too_sparse_backlist.astype(bool)].replace([np.inf, -np.inf], np.nan).dropna()
    pr['d'] = pr.tau_p_backlist - pr.tau_p_main
    paired = pr.groupby('level').agg(tests=('d', 'size'), mean_tau_main=('tau_p_main', 'mean'), mean_tau_backlist=('tau_p_backlist', 'mean'),
                                     mean_change=('d', 'mean'), corr=('d', lambda x: np.nan)).reset_index().drop(columns='corr')

    # ---------------- report ----------------
    L = ['## What was run',
         f'- demand restricted to backlist works: first checkout in any Seattle format at least {BL.BACKLIST_MONTHS} months before month 0 of the test (addendum 2026-10-14 b, made after the 3b results were seen). Seattle formats only (LibriVox not run).',
         '- everything else as in 3b: same shifts, joint quasi-Poisson model, fit window, windows 0 to +2 and 0 to +5, placebo categories (same month 0, same restricted demand, same shift screen), placebo years (each at its own month 0), BH families, pooling and bootstrap (2,000 resamples, seed 20261013).',
         '- exposure N (all checkouts of the format that month) is unchanged; only Y is restricted. NOT IN RECORD, logged in DEVIATIONS.md.',
         '- builder check: with every work eligible it reproduces the 3b count panel (largest relative difference: ' + ', '.join(f'{lv} {d:.1e}' for lv, d in ver) + ').',
         f'- run time {time.time() - t0:.0f}s, one process.', '',
         '## Positive controls: backlist demand beside the main 3b run', '',
         'Pass rule as in 3b: tau > 0 and one-sided placebo-category rank p < 0.05 (months 0 to +2, joint Seattle model).', '']
    L += IO.md_table(CT[['control', 'main_tau', 'main_p', 'main_verdict', 'backlist_tau', 'backlist_p', 'backlist_verdict', 'backlist_tau_s', 'backlist_p_s',
                        'main_tau_pre', 'backlist_tau_pre', 'backlist_share_of_main_y', 'n_placebos', 'placebo_years', 'py_share_ge']])
    L += ['', 'main_tau_pre and backlist_tau_pre: log of observed over expected in months -6 to -1 (the earlier rise). backlist_share_of_main_y: backlist weighted checkouts over the main ones in months 0 to +2.', '']
    for c in S.controls:
        g = MT[MT.control == c['name']][['month', 'observed', 'expected', 'ratio']]
        L += [f'### {c["name"]}: monthly observed and expected weighted checkouts, backlist demand, months -6 to +5', ''] + IO.md_table(g) + ['']
    L += ['### Values inside the control nodes (backlist, descriptive)', '']
    if len(V):
        vm = pd.read_csv(P.out('controls_values.csv'))
        a = V.groupby('control').agg(values_tested=('node_id', 'size'), tau_p_median=('tau_p', 'median'), share_tau_positive=('tau_p', lambda x: float((x > 0).mean())),
                                     share_p_below_alpha=('p_cat_p', lambda x: float((x < S.alpha).mean())), too_sparse=('too_sparse', 'sum')).reset_index()
        L += IO.md_table(a) + ['', 'Single values: data/db/study3b/backlist_controls_values.csv.', '']
    L += ['## All shifts on backlist demand', '', '### Detection beside main 3b (non-sparse tests; BH within level and family)', '']
    L += IO.md_table(dd[['analysis', 'level', 'tests_main', 'p_below_005_main', 'share_p_below_005_main', 'bh_q_below_010_main', 'tests_backlist', 'p_below_005_backlist',
                         'share_p_below_005_backlist', 'bh_q_below_010_backlist']])
    L += ['', '### Same shift tests, change in tau (main analysis, non-sparse in both runs)', ''] + IO.md_table(paired)
    L += ['', '### Pooled mean tau (log lift, months 0 to +2; 95% bootstrap interval clustered by category), main 3b beside backlist (non-sparse, main analysis)', '']
    c2 = cmp_[(cmp_.analysis == 'main') & (cmp_.duration_class.isin(['sustained', 'fading', 'all']))].sort_values(['level', 'source', 'duration_class'])
    L += IO.md_table(c2[['source', 'level', 'duration_class', 'tests_main', 'tau_p_mean_main', 'tau_p_ci_low_main', 'tau_p_ci_high_main',
                         'tests_backlist', 'tau_p_mean_backlist', 'tau_p_ci_low_backlist', 'tau_p_ci_high_backlist']])
    L += ['', '### Supplementary (NOT IN RECORD): sustained and fading shifts pooled over sources and levels', ''] + IO.md_table(sup)
    L += ['', f'Full tables: study3b_15_backlist_pooled.csv; shift-level results data/db/study3b/backlist_shift_effects.parquet.']
    path = IO.write_report(P, '15', 'Study 3b backlist robustness run', L, S, meta)
    log('report', path)
    print('\n'.join(L[:60]))


if __name__ == '__main__':
    main()
