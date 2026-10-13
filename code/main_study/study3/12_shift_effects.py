# 12. Effects of every interest shift on demand (record, tests): for each shift at a tested level (narrow, middle)
# and each format where the category passes the minimum-size rule: event study, synthetic control with the
# in-space placebo rank p-value (placebo categories), event-study placebo categories, placebo years, and the lag of
# the peak gap. Benjamini-Hochberg q-values across all shift-level synthetic-control p-values (months 0..+2); pooled
# means with a bootstrap clustered by category.
# Seasonal shifts are analysed separately (record): they get their own Benjamini-Hochberg family and pooled table.
# NOT IN RECORD: the BH family is every shift x format test of the main (non-seasonal) analysis, primary window.
# NOT IN RECORD: pooled means are reported per source x level x format, per source x level, and per duration class.
# Needs: the power report and data/db/interest/shifts.parquet. Output: data/db/study3/shift_effects.parquet,
# pooled_effects.csv, data/reports/study3_12_shift_effects.md
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from _settings import SETTINGS as S
import _files as IO
import _analysis as A
import _methods as M
from _build import mi_from_ym
from _interest import load_shifts, status_line, require_gdelt_durations, SHIFTS_FILE

SHIFT_COLS = ['shift_id', 'source', 'node_id', 'level', 'start_week', 'm0', 'duration_class', 'size', 'large', 'seasonal', 'quality_flag']


def plan(shifts, ctx, include_flagged=False):
    """Unique (level, format, category, month 0) tests; several shifts can share one. NOT IN RECORD: shifts the
    interest side could not label in real time (interrupted, censored) are not tested; they still count in the donor
    and placebo-year shift screens."""
    ok = shifts.quality_ok | include_flagged          # addendum h: flagged Wikipedia shifts only in the robustness run
    s = shifts[shifts.labelled & ok & shifts.level.isin(S.levels_tested) & (shifts.m0 >= mi_from_ym(S.study_start))]
    items = sorted({(lv, fmt, n, int(m)) for lv, n, m in zip(s.level, s.node_id, s.m0) for (_, fmt) in ctx.keys([lv])})
    return s, items


def add_q(R):
    """BH q-values within each family (main, seasonal) over the primary-window synthetic-control p-values."""
    R['bh_q'] = np.nan
    for fam, g in R.groupby('analysis'):
        R.loc[g.index, 'bh_q'] = M.bh_q(g.sc_p_p.to_numpy(dtype=float))
    R['detected_bh'] = R.bh_q < S.bh_q
    R['significant_single'] = R.sc_p_p < S.alpha
    return R


def pooled(R, n_boot):
    """Mean effects with a bootstrap clustered by category, per analysis, source, level and format (and all formats)."""
    rows = []
    ok = R[R.sc_ok == True]  # noqa: E712
    groups = [('analysis', 'source', 'level', 'format'), ('analysis', 'source', 'level'), ('analysis', 'source', 'level', 'duration_class')]
    for keys in groups:
        for k, g in ok.groupby(list(keys)):
            r = dict(zip(keys, k)); r.setdefault('format', 'all'); r.setdefault('duration_class', 'all')
            r.update(tests=len(g), shifts=g.shift_id.nunique(), categories=g.node_id.nunique())
            for col in ('sc_effect_p', 'es_effect_p', 'sc_effect_s', 'es_effect_s'):
                v = g.dropna(subset=[col])
                r[f'{col}_mean'] = float(v[col].mean()) if len(v) else np.nan
                if v.node_id.nunique() >= 2:
                    bs = M.cluster_bootstrap(v.reset_index(drop=True), 'node_id', lambda d, c=col: float(d[c].mean()), n_boot, S.boot_seed)
                    r[f'{col}_ci_low'], r[f'{col}_ci_high'] = M.percentile_ci(bs)
            rows.append(r)
    return pd.DataFrame(rows)


def summary_lines(s_all, s, R, P_tab):
    L = ['## Shifts', f'- in the interest table: {len(s_all)}; without a record duration class (interrupted, censored): '
         f'{int((~s_all.labelled).sum())}; labelled, at tested levels, from {S.study_start}: {len(s)}']
    L += IO.md_table(s.groupby(['source', 'level', 'duration_class', 'seasonal']).size().rename('shifts').reset_index())
    L += ['', '## Tests (shift x format)']
    L += IO.md_table(R.assign(skip=R.skip.replace('', 'tested')).groupby(['analysis', 'format', 'skip']).size().rename('tests').reset_index())
    t = R[R.sc_ok == True]  # noqa: E712
    L += ['', f'## Detection (synthetic control, months {S.window_primary[0]} to +{S.window_primary[1]})']
    for fam, g in t.groupby('analysis'):
        L.append(f'- {fam}: {len(g)} tests; one-sided p < {S.alpha}: {int(g.significant_single.sum())}; '
                 f'BH q < {S.bh_q}: {int(g.detected_bh.sum())}')
    L += ['', '## Pooled mean effects (log share; 95% intervals from a bootstrap clustered by category)']
    if len(P_tab):
        cols = ['analysis', 'source', 'level', 'format', 'duration_class', 'tests', 'categories', 'sc_effect_p_mean',
                'sc_effect_p_ci_low', 'sc_effect_p_ci_high', 'es_effect_p_mean', 'es_effect_p_ci_low', 'es_effect_p_ci_high']
        L += IO.md_table(P_tab.reindex(columns=cols))
    return L


def main():
    ap = IO.parser('Study 3 shift effects')
    ap.add_argument('--boot', type=int, default=None, help='simulation runs only: bootstrap resamples')
    ap.add_argument('--include-flagged', action='store_true',
                    help='robustness run (addendum h): also test Wikipedia shifts flagged by the quality check; '
                         'writes *_with_flagged files and its own report, never the step report')
    args, P, meta, warn = IO.start('12', ap)
    n_boot = IO.sim_only(args, 'boot', S.boot_n)
    shifts = load_shifts(P, S)
    if shifts is None:
        raise SystemExit(f'Step 12 refuses to run: {P.interest / SHIFTS_FILE} does not exist (interest side not finished).')
    require_gdelt_durations(S, shifts, '12', P.sim)
    panel, nodes, overlap = IO.load_panels(P), IO.read_parquet(P.nodes), IO.read_parquet(P.overlap)
    ctx = A.Context(panel, nodes, overlap, shifts, S)
    s, items = plan(shifts, ctx, args.include_flagged)
    sfx = '_with_flagged' if args.include_flagged else ''
    t0 = time.time()
    res = A.run_parallel(A.test_unit, ctx, items, args.workers)
    T = pd.DataFrame(res)
    R = s[SHIFT_COLS].merge(T.drop(columns=['broad_id', 'label']), on=['level', 'node_id', 'm0'], how='inner')
    R['broad_id'] = R.node_id.map(ctx.broad)
    R['analysis'] = np.where(R.seasonal, 'seasonal', 'main')
    R['sc_ok'] = R.sc_ok.fillna(False).astype(bool)
    R = add_q(R)
    IO.save_parquet(R, P.out(f'shift_effects{sfx}.parquet'))
    P_tab = pooled(R, n_boot)
    IO.save_csv(P_tab, P.out(f'pooled_effects{sfx}.csv'))
    head = [f'- {status_line(P)}', f'- bootstrap resamples: {n_boot} (record {S.boot_n}), seed {S.boot_seed}',
            f'- last demand month per format: ' + ', '.join(f'{f}: {A.ym_of(ctx.last_month(lv, f))}' for lv, f in ctx.keys(S.levels_tested[:1])),
            f'- run time {time.time() - t0:.0f}s'] + [f'- WARNING: {w}' for w in warn] + ['']
    L = head + summary_lines(shifts, s, R, P_tab)
    if args.include_flagged:
        path = pathlib.Path(str(P.report('12')).replace('.md', '_with_flagged.md'))
        path.write_text('# Study 3 shift effects, robustness run with flagged Wikipedia shifts\n\n' + '\n'.join(L) + '\n')
    else:
        path = IO.write_report(P, '12', 'Study 3 shift effects', L, S, meta)
    print('\n'.join(L))
    print('report:', path)


if __name__ == '__main__':
    main()
