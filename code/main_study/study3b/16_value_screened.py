# 16. Value-level calibration against screened placebos (robustness; made after the 3b results were seen).
# Addendum 3b a says the record's placebo universe at the value level is every value without a detected shift (values with no
# interest series count as shift-free) and that "a screened p is reported as a robustness check". The power report (11) showed
# the largest value band flagging 9.5% of tests at lift 0 (5% expected). Here the value-level rank p is recomputed against
# SCREENED placebo values:
#   screened placebo value = feasible fit at the same month 0, not sharing the parent of the tested value, no interest shift
#   start (any source, any class) in months -6..+6 (the record's screen), AND an interest series exists for the value (a Wikipedia
#   or GDELT weekly value series, i.e. 'no shift' is known rather than assumed). This is the `screened=True` placebo_mask of
#   _inference.py (p_cat_p_screened in step 12). NOT IN RECORD: the exact screen is only described in the README/addendum as
#   "placebo values that have a series"; the shift screen of the record is kept on top of it.
# Outputs: (a) the 11 draws (same units, same band edges, same seed, read from power_draws.parquet) rerun at every lift with the
# screened pool; (b) NOT IN RECORD: an extended lift-0 calibration with 2,000 draws per band (seed 20261014) because 200 draws
# give a rate only to about +-3 points, for the unscreened and the screened pool, for units with and without an interest series;
# (c) the value-level shift tests of step 12 (main and seasonal): p < 0.05 and BH q < 0.10 on the screened p beside the record's p.
# Run (one process): nice -n 10 ../../../.venv/bin/python 16_value_screened.py
# Needs: the reports of 11 and 12 on this panel build; the cached z tables of the value level (made by 11). Writes
# data/reports/study3b_16_value_screened.md and study3b_16_*.csv. Existing outputs are only read.
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _s3
from _settings import SETTINGS as S
import _paths as IO
import _inference as INF
import _methods as M

B3 = _s3.build
EXT_DRAWS, EXT_SEED = 2000, 20261014            # NOT IN RECORD
DATA = pathlib.Path(IO.D)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


class Cache:
    """Per month 0: z table, shift screen, series mask; per unit: the two placebo sets and the ranks."""

    def __init__(self, world):
        self.w = world
        C = world.C[('seattle', 'value')]
        self.C = C
        self.par = world.parent_arr[('seattle', 'value')]
        self.has_series = np.isin(C.ids, list(world.interest_ids['value']))
        self.tab, self.near = {}, {}

    def month(self, m0):
        if m0 not in self.tab:
            self.tab[m0] = self.w.ztable('seattle', 'value', m0)
            self.near[m0] = self.w.near_mask('seattle', 'value', m0)
        return self.tab[m0], self.near[m0]

    def pools(self, i, m0):
        tab, near = self.month(m0)
        base = tab['feasible'] & ~near
        base[i] = False
        pi = self.par[i]
        if pi is not None and not (isinstance(pi, float) and np.isnan(pi)):
            base &= (self.par != pi)
        return tab, base, base & self.has_series

    def ps(self, i, m0, lifts):
        """Rank p of unit i at each lift against the record's pool and the screened pool."""
        tab, pool, scr = self.pools(i, m0)
        z0, smu, phi, sy = float(tab['z_p'][i]), float(tab['summu_p'][i]), float(tab['phi'][i]), float(tab['sumy_p'][i])
        out = []
        for L in lifts:
            zl = float(M.lifted_z(z0, smu, phi, sy, L))
            out.append((M.rank_p(zl, tab['z_p'][pool].astype(float)), M.rank_p(zl, tab['z_p'][scr].astype(float))))
        return out, int(pool.sum()), int(scr.sum())


def calibrate(cache, draws, lifts):
    rows = []
    for (node, m0, band) in draws:
        i = cache.C.index[node]
        ps, n_all, n_scr = cache.ps(i, int(m0), lifts)
        for L, (p_all, p_scr) in zip(lifts, ps):
            rows.append(dict(node_id=node, m0=int(m0), band=int(band), lift=L, p_all=p_all, p_scr=p_scr, has_series=bool(cache.has_series[i]),
                             n_all=n_all, n_scr=n_scr))
    return pd.DataFrame(rows)


def rate_table(D, col, label):
    out = []
    for (b, L), g in D.groupby(['band', 'lift']):
        g = g[g[col].notna()]
        k = int((g[col] < S.power_alpha).sum())
        lo, hi = wilson(k, len(g))
        out.append(dict(pool=label, band=b + 1, lift=L, draws=len(g), detected=k, rate=k / max(1, len(g)), ci_low=lo, ci_high=hi))
    return pd.DataFrame(out)


def main():
    ap = IO.parser('Study 3b value-level calibration with screened placebos')
    args = ap.parse_args()
    if args.sim:
        raise SystemExit('16 runs on real data only')
    P = IO.Paths(None)
    meta = IO.load_meta(P)
    IO.require_previous(P, '12', meta)               # report 11 on this panel build
    IO.require_previous(P, '13', meta)               # report 12 on this panel build
    t0 = time.time()
    shifts = INF.load_shifts(P, S)
    world = INF.World(P, S, shifts)
    if world.interest_ids.get('value') is None:
        raise SystemExit('no value-level interest series found; nothing to screen with')
    cache = Cache(world)
    n_series = int(cache.has_series.sum())
    lifts = (0.0,) + tuple(S.power_lifts)

    # (a) the step 11 draws at the value level, screened pool
    PD = pd.read_parquet(P.out('power_draws.parquet'))
    PD = PD[PD.level == 'value']
    d11 = PD[PD.lift == 0.0][['node_id', 'm0', 'band']].drop_duplicates()
    log(f'step 11 value draws: {len(d11)} units')
    A = calibrate(cache, list(d11.itertuples(index=False, name=None)), lifts)
    chk = PD.merge(A, on=['node_id', 'm0', 'band', 'lift'], how='inner')
    agree = float(np.mean(np.isclose(chk.p.to_numpy(float), chk.p_all.to_numpy(float), equal_nan=True)))
    log('share of recomputed record p equal to stored step 11 p:', agree)
    ta = pd.concat([rate_table(A.assign(p_all=A.p_all), 'p_all', 'record pool (all values, recomputed)'), rate_table(A, 'p_scr', 'screened pool')], ignore_index=True)
    tb = rate_table(A[A.has_series], 'p_scr', 'screened pool, units with an interest series')
    tc = rate_table(A[A.has_series], 'p_all', 'record pool, units with an interest series')

    # (b) extended lift-0 calibration
    lo, hi = B3.mi_from_ym(S.study_start), world.last_month('seattle', 'value') - S.window_primary[1]
    tabs = {m: cache.month(m)[0] for m in range(lo, hi + 1)}
    ids, ms, sm = INF.power_candidates(world, 'seattle', 'value', lo, hi, tabs)
    edges = M.size_bands(sm, S.power_bands)
    band = M.band_of(sm, edges)
    rng = np.random.default_rng(EXT_SEED)
    ext = []
    for b in range(S.power_bands):
        cand = np.flatnonzero(band == b)
        pick = rng.choice(cand, size=EXT_DRAWS, replace=len(cand) < EXT_DRAWS)
        ext += [(cache.C.ids[ids[k]], int(ms[k]), b) for k in pick]
    E = calibrate(cache, ext, (0.0,))
    te = pd.concat([rate_table(E, 'p_all', 'record pool'), rate_table(E, 'p_scr', 'screened pool'),
                    rate_table(E[E.has_series], 'p_all', 'record pool, units with a series'), rate_table(E[E.has_series], 'p_scr', 'screened pool, units with a series'),
                    rate_table(E[~E.has_series], 'p_scr', 'screened pool, units without a series')], ignore_index=True)
    ext_n = E.groupby('band').agg(units=('node_id', 'size'), with_series=('has_series', 'sum'), median_pool_all=('n_all', 'median'), median_pool_screened=('n_scr', 'median')).reset_index()
    ext_n['band'] += 1
    cal = pd.concat([ta.assign(set='step 11 draws'), tb.assign(set='step 11 draws'), tc.assign(set='step 11 draws'), te.assign(set='extended 2000 draws, lift 0')], ignore_index=True)
    IO.save_csv(cal, DATA / 'reports' / 'study3b_16_calibration.csv')

    # (c) value-level shift tests
    R = pd.read_parquet(P.out('shift_effects.parquet'))
    V = R[(R.level == 'value') & (R.skip == '') & ~R.too_sparse.fillna(False).astype(bool)].copy()
    V['bh_q_screened'] = np.nan
    for a, g in V.groupby('analysis'):
        ok = g.p_cat_p_screened.notna()
        V.loc[g.index[ok.to_numpy()], 'bh_q_screened'] = M.bh_q(g.p_cat_p_screened[ok].to_numpy(dtype=float))
    V['p_record'] = V.p_cat_p
    V['sig_record'] = V.p_cat_p < S.alpha
    V['sig_screened'] = V.p_cat_p_screened < S.alpha
    V['bh_record'] = V.bh_q < S.bh_q
    V['bh_screened'] = V.bh_q_screened < S.bh_q
    rows = []
    for a, g in V.groupby('analysis'):
        rows.append(dict(analysis=a, tests=len(g), p_record_below_005=int(g.sig_record.sum()), share_record=g.sig_record.mean(),
                         p_screened_below_005=int(g.sig_screened.sum()), share_screened=g.sig_screened.mean(),
                         both=int((g.sig_record & g.sig_screened).sum()), bh_record=int(g.bh_record.sum()), bh_screened=int(g.bh_screened.sum()),
                         bh_both=int((g.bh_record & g.bh_screened).sum()), median_placebos_record=g.n_placebos.median(), median_placebos_screened=g.n_placebos_screened.median()))
    sh = pd.DataFrame(rows)
    by_src = V.groupby(['analysis', 'source']).agg(tests=('p_record', 'size'), p_record_below_005=('sig_record', 'sum'), p_screened_below_005=('sig_screened', 'sum'),
                                                   bh_screened=('bh_screened', 'sum')).reset_index()
    surv = V[V.bh_screened | V.bh_record].sort_values(['analysis', 'bh_q_screened'])
    keep = ['analysis', 'shift_id', 'source', 'node_id', 'month0', 'duration_class', 'tau_p', 'p_record', 'bh_q', 'p_cat_p_screened', 'bh_q_screened', 'bh_record', 'bh_screened']
    IO.save_csv(V[keep + ['sig_record', 'sig_screened']], DATA / 'reports' / 'study3b_16_value_tests_screened.csv')

    cond = V[V.sig_screened]
    L = ['## What was done',
         f'- Value-level one-sided rank p recomputed against screened placebo values: feasible fit at the same month 0, other parent, no interest shift start (any source, any class) in months -6 to +6, and an interest series exists for the value (Wikipedia or GDELT weekly value series: {n_series} of {len(cache.has_series):,} values in the panel have one). '
         'Same as `p_cat_p_screened` of step 12. NOT IN RECORD: the exact screen (the README and addendum a only say "placebo values that have a series"); the record\'s shift screen was kept on top.',
         f'- Step 11 draws reused (same units, band edges and seed): {len(d11)} units; the recomputed record p equals the stored step 11 p for {100 * agree:.1f}% of rows (a check of this code).',
         f'- NOT IN RECORD: an extended lift-0 calibration, {EXT_DRAWS} draws per band (seed {EXT_SEED}), because 200 draws only fix a rate to about 3 points.',
         f'- run time {time.time() - t0:.0f}s, one process.', '',
         '## Lift-0 false-positive rate (share of placebo units with one-sided p < 0.05; 5% expected)', '', '### Step 11 draws (200 per band), with 95% Wilson intervals', '']
    z0 = cal[(cal.set == 'step 11 draws') & (cal.lift == 0.0)]
    L += IO.md_table(z0[['pool', 'band', 'draws', 'detected', 'rate', 'ci_low', 'ci_high']].sort_values(['pool', 'band']))
    L += ['', f'### Extended calibration ({EXT_DRAWS} draws per band)', '']
    L += IO.md_table(te[['pool', 'band', 'draws', 'detected', 'rate', 'ci_low', 'ci_high']].sort_values(['pool', 'band']))
    L += ['', 'Units in the extended draws:', ''] + IO.md_table(ext_n)
    L += ['', '### Power with the screened pool, step 11 draws (detection rate at each lift)', '']
    pw = ta[ta.pool == 'screened pool'].pivot(index='band', columns='lift', values='rate').reset_index()
    pr_ = ta[ta.pool.str.startswith('record')].pivot(index='band', columns='lift', values='rate').reset_index()
    L += ['Screened pool:', ''] + IO.md_table(pw) + ['', 'Record pool (recomputed, equals step 11):', ''] + IO.md_table(pr_)
    L += ['', '## Value-level shift tests (step 12, non-sparse; main and seasonal families)', '']
    L += IO.md_table(sh) + ['', 'By source:', ''] + IO.md_table(by_src)
    L += ['', f'Share of record detections (p < 0.05) that also pass on the screened p: {int((V.sig_record & V.sig_screened).sum())} of {int(V.sig_record.sum())}.',
          '', '### BH q < 0.10 detections (record or screened)', '']
    L += IO.md_table(surv[keep]) if len(surv) else ['(none)']
    path = IO.write_report(P, '16', 'Study 3b value-level calibration with screened placebos', L, S, meta)
    log('report', path)
    print('\n'.join(L[:70]))


if __name__ == '__main__':
    main()
