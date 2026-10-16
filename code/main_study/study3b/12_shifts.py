# 12. Effects of every interest shift on demand (record, all_shifts): for each quality-ok, labelled shift at the narrow, middle and
# value levels (from 2017-01), the count event study at month 0, joint across the Seattle formats: tau, z, the placebo-category
# rank p (one-sided), placebo years, per-format effects (secondary) and the secondary window 0..+5. LibriVox is tested separately
# with its own exposure. Benjamini-Hochberg q-values within each level over the main tests; pooled mean tau by source, level and
# duration class with a bootstrap clustered by category (2,000 resamples, seed 20261013).
# Tests with fewer than 5 expected weighted checkouts over the primary window (sum mu) are reported separately as too sparse:
# they stay out of the BH family and the main pooled means, and a second pooled table includes them.
# NOT IN RECORD: (1) the BH family is every non-sparse joint Seattle test of the main analysis (labelled, quality-ok, not seasonal)
# at a level, both sources together, primary window; seasonal shifts are a separate family and pooled table (as in Study 3);
# (2) shifts without a record duration class (interrupted, censored) are not tested; they still count in the placebo screens;
# (3) several shifts of one category in the same month 0 share one test; (4) tau is undefined when sum Y = 0 (z = -inf is kept
# for ranking), such tests leave the pooled means and the carry-over regression and are counted; (5) per-format effects have
# no placebo p; (6) LibriVox tests are outside BH, pooling and the carry-over regression, and are summarised in their own table;
# (7) pooled means by source x level x duration class, source x level, and level.
# Needs: the power report. Output: data/db/study3b/shift_effects.parquet, shift_effects_librivox.parquet, pooled_effects.csv,
# report study3b_12_shifts.md. --include-flagged: robustness run with flagged shifts too (own files and report, never the step report).
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _s3
from _settings import SETTINGS as S
import _paths as IO
import _inference as INF
import _methods as M

B3 = _s3.build
SHIFT_COLS = ['shift_id', 'source', 'level', 'node_id', 'start_week', 'm0', 'duration_class', 'size', 'large', 'seasonal', 'quality_ok', 'quality_flag',
              'duration_count', 'whole_duration']


def plan(shifts, include_flagged, world, kind):
    ok = shifts.quality_ok | include_flagged                 # addenda g and i: flagged shifts only in the robustness run
    s = shifts[shifts.labelled & ok & shifts.level.isin(S.levels_tested) & (shifts.m0 >= B3.mi_from_ym(S.study_start))]
    have = {lv: set(world.C[(kind, lv)].ids) for lv in S.levels_tested if (kind, lv) in world.C}
    s = s[[n in have.get(lv, ()) for lv, n in zip(s.level, s.node_id)]]
    units = s.groupby(['level', 'm0']).node_id.apply(lambda x: sorted(set(x))).reset_index()
    return s, [(kind, 'unit', r.level, int(r.m0), list(r.node_id)) for r in units.itertuples()]


def add_q(R):
    """BH q-values within each level and family (main, seasonal) over the primary-window rank p of the non-sparse tests."""
    R['bh_q'] = np.nan
    fam = R[(R.skip == '') & ~R.too_sparse.fillna(False).astype(bool) & R.p_cat_p.notna()]
    for (a, lv), g in fam.groupby(['analysis', 'level']):
        R.loc[g.index, 'bh_q'] = M.bh_q(g.p_cat_p.to_numpy(dtype=float))
    R['detected_bh'] = R.bh_q < S.bh_q
    R['significant_single'] = R.p_cat_p < S.alpha
    return R


def pooled(R, n_boot, include_sparse):
    rows = []
    ok = R[(R.skip == '')]
    if not include_sparse:
        ok = ok[~ok.too_sparse.fillna(False).astype(bool)]
    ok = ok.replace([np.inf, -np.inf], np.nan)
    groups = [('analysis', 'source', 'level', 'duration_class'), ('analysis', 'source', 'level'), ('analysis', 'level')]
    for keys in groups:
        for k, g in ok.groupby(list(keys)):
            r = dict(zip(keys, k)); r.setdefault('source', 'all'); r.setdefault('duration_class', 'all')
            r.update(include_sparse=include_sparse, tests=len(g), shifts=g.shift_id.nunique(), categories=g.node_id.nunique(),
                     share_p_below_alpha=float((g.p_cat_p < S.alpha).mean()))
            for col in ('tau_p', 'tau_s'):
                b = M.cluster_boot_mean(g[col].to_numpy(), g.node_id.to_numpy(), n_boot, S.boot_seed)
                r.update({f'{col}_mean': b['mean'], f'{col}_ci_low': b.get('low'), f'{col}_ci_high': b.get('high'), f'{col}_n': b['n']})
            rows.append(r)
    return pd.DataFrame(rows)


def run_kind(world, spec, shifts, kind, include_flagged, workers):
    s, tasks = plan(shifts, include_flagged, world, kind)
    res = INF.run_tasks(spec, tasks, workers)
    T = pd.DataFrame([r for t in res for r in t[3]])
    if len(T) == 0:
        return s, pd.DataFrame()
    R = s.reindex(columns=SHIFT_COLS).merge(T.drop(columns=['broad_id', 'label'], errors='ignore'), on=['level', 'node_id', 'm0'], how='inner')
    R['broad_id'] = [world.cats[lv].broad_id.get(n) for lv, n in zip(R.level, R.node_id)]
    R['analysis'] = np.where(R.seasonal, 'seasonal', 'main')
    for c in ('too_sparse', 'y_zero'):
        R[c] = R[c].fillna(False).astype(bool) if c in R else False
    return s, R


def summary_lines(s_all, s, R, P_tab, kind):
    L = ['## Shifts', f'- in the interest tables (narrow, middle, value): {len(s_all)}; without a record duration class (interrupted, censored): '
         f'{int((~s_all.labelled).sum())}; labelled, quality-ok (unless robustness), tested levels, from {S.study_start}, category with counts: {len(s)}']
    L += IO.md_table(s.groupby(['source', 'level', 'duration_class', 'seasonal']).size().rename('shifts').reset_index())
    L += ['', '## Tests (joint Seattle model, one per category and month 0 shared by its shifts)']
    t = R.assign(skip=R.skip.replace('', 'tested'))
    L += IO.md_table(t.groupby(['analysis', 'level', 'skip']).size().rename('shift rows').reset_index())
    ok = R[R.skip == '']
    L += ['', f'## Detection (placebo-category rank, months {S.window_primary[0]} to +{S.window_primary[1]})']
    for (a, lv), g in ok.groupby(['analysis', 'level']):
        ns = g[~g.too_sparse]
        L.append(f'- {a}, {lv}: {len(g)} shift rows tested, {int(g.too_sparse.sum())} too sparse (sum mu < {S.sparse_below:g}, reported separately); among the other {len(ns)}: '
                 f'one-sided p < {S.alpha}: {int(ns.significant_single.sum())} ({100 * ns.significant_single.mean():.1f}%, {100 * S.alpha:.0f}% expected under no effect); '
                 f'BH q < {S.bh_q}: {int(ns.detected_bh.sum())}; sum Y = 0 tests: {int(ns.y_zero.sum())}')
    L += ['', '## Pooled mean tau = log(sum Y / sum mu) (log lift; 95% intervals from a bootstrap clustered by category)']
    if len(P_tab):
        cols = ['include_sparse', 'analysis', 'source', 'level', 'duration_class', 'tests', 'categories', 'share_p_below_alpha', 'tau_p_mean', 'tau_p_ci_low',
                'tau_p_ci_high', 'tau_s_mean', 'tau_s_ci_low', 'tau_s_ci_high']
        L += IO.md_table(P_tab.reindex(columns=cols))
    return L


def main():
    ap = IO.parser('Study 3b shift effects')
    ap.add_argument('--boot', type=int, default=None, help='simulation runs only: bootstrap resamples')
    ap.add_argument('--include-flagged', action='store_true', help='robustness run (addenda g and i): also test flagged shifts; own files and report')
    args, P, meta, warn = IO.start('12', ap)
    n_boot = IO.sim_only(args, 'boot', S.boot_n)
    shifts = INF.load_shifts(P, S)
    world = INF.World(P, S, shifts)
    spec, workers = dict(sim=args.sim), IO.workers_of(args)
    sfx = '_with_flagged' if args.include_flagged else ''
    t0 = time.time()
    s, R = run_kind(world, spec, shifts, 'seattle', args.include_flagged, workers)
    if len(R) == 0:
        raise SystemExit('no shift could be tested')
    R = add_q(R)
    IO.save_parquet(R.drop(columns=['py_years'], errors='ignore'), P.out(f'shift_effects{sfx}.parquet'))
    P_tab = pd.concat([pooled(R, n_boot, False), pooled(R, n_boot, True)], ignore_index=True)
    IO.save_csv(P_tab, P.out(f'pooled_effects{sfx}.csv'))
    L = summary_lines(shifts, s, R, P_tab, 'seattle')
    lv_lines = ['', '## LibriVox (its own exposure; outside BH, pooling and the carry-over regression)']
    if any(k[0] == 'librivox' for k in world.C):
        s2, RL = run_kind(world, spec, shifts, 'librivox', args.include_flagged, workers)
        if len(RL):
            IO.save_parquet(RL.drop(columns=['py_years'], errors='ignore'), P.out(f'shift_effects_librivox{sfx}.parquet'))
            okl = RL[(RL.skip == '') & ~RL.too_sparse]
            lv_lines += [f'- tests {len(RL)} shift rows, {len(okl)} usable and not too sparse; one-sided p < {S.alpha}: {int((okl.p_cat_p < S.alpha).sum())}; '
                         f'mean tau {okl.replace([np.inf, -np.inf], np.nan).tau_p.mean():.3f}']
            lv_lines += IO.md_table(okl.replace([np.inf, -np.inf], np.nan).groupby(['source', 'level']).agg(tests=('tau_p', 'size'), mean_tau=('tau_p', 'mean'),
                                                                                                         share_p_below_alpha=('p_cat_p', lambda x: float((x < S.alpha).mean()))).reset_index())
        else:
            lv_lines += ['- no LibriVox test could be run']
    else:
        lv_lines += ['- LibriVox is not in the panel']
    head = [f'- bootstrap resamples: {n_boot} (record {S.boot_n}), seed {S.boot_seed}', f'- last demand month per level (Seattle): ' +
            ', '.join(f'{lv}: {B3.ym_of(world.last_month("seattle", lv))}' for lv in S.levels_tested),
            f'- run time {time.time() - t0:.0f}s with {workers} workers'] + [f'- WARNING: {w}' for w in warn] + ['']
    out = head + L + lv_lines
    if args.include_flagged:
        path = pathlib.Path(str(P.report('12')).replace('.md', '_with_flagged.md'))
        path.write_text('# Study 3b shift effects, robustness run with flagged shifts\n\n' + '\n'.join(out) + '\n')
    else:
        path = IO.write_report(P, '12', 'Study 3b shift effects', out, S, meta)
    print('\n'.join(out))
    print('report:', path)


if __name__ == '__main__':
    main()
