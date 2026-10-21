#!/usr/bin/env python3
"""Addendum i, direction D1_horizons_themes: longer horizons for the theme tests (a no-fitting ranking and the event windows).

Settings: prereg/addenda_wiki_led/2026-10-22_i_directions.json, key D1_horizons_themes (read-only; its SHA-256 is checked against
prereg/README.md on every run). Through it: addenda g and h of the Wikipedia-led tests (Test F; _testf_analysis checks their
fingerprints on import) and the Study 3 record with its addenda (hash-checked by the Chapter 6 code that is imported).
Header written on 22 Oct 2026 before any D1 number was computed.

Part 1, ranking (no fitting). Rows: the benchmark's main rows as in Test F step 25 (25_G3_forecast.main_rows: Seattle, print and
ebook, horizon 1, 36,081 rows, 510 series). Input x(t) = m(t) - m(t-1), the monthly log change of the theme's attention series at
the origin (25_G3_forecast.changes / attach_x; a row without x gets 0, as there), for S2 (ais2_wlog) and S2C (aic2_wlog) of
data/db/wiki_led/testF/series_monthly.parquet and the hand-checked concept pages (cur_wlog of benchmark/stage2/monthly_cov.parquet).
Target for k = 1, 3, 6, 12: c_k(t) = mean of y(t+1) .. y(t+k) minus y(t), y = the series' monthly log share. Measure: the Test C
measure (25_G3_forecast.test_c_scores: Spearman of x and c_k within origin x format x level groups of at least 10 rows, mean over
groups, 2,000 draws of 3-month blocks of origin months, seed 20261020; paired differences with the same draws, 25_G3_forecast.paired).
k = 1 must reproduce data/db/wiki_led/testF/g3_wikionly.csv (S2, concept pages) and h_g3_wikionly.csv (S2C) exactly.

Part 2, event windows. Lasting rises (4 weeks or more) of S2C, S2 and the hand-checked concept pages; panel a (Study 3 demand
panel with LibriVox); both levels pooled; synthetic control and own trend (event study), with everything of addendum g: the rises
and quality flags stored by Test F step 24 (shifts_S2C/S2.parquet, desktop_S2C/S2.parquet, the 'new+gdelt' screen) and, for the
concept pages, Chapter 6's stored rises (data/db/interest/shifts.parquet, Wikipedia source, screened with both sources as in
Chapter 6); the Study 3 functions (study3/_methods.py, which defines the windows from the record: primary months 0 to 2, secondary
0 to 5; study3/_analysis.Context for the donor and size rules; 12_shift_effects.plan for the tests; the bootstrap clustered by theme,
2,000 resamples, seed 20261013, 95% percentile intervals). New windows: months 3 to 5, 6 to 11 and 0 to 11. The months 0 to 2
numbers must reproduce the stored per-test values (g2_<S>_tests_a.parquet, data/db/study3/shift_effects.parquet) and the pooled
rows (g2_S2C_pooled.csv, g2_S2_pooled.csv, study3/pooled_effects.csv) before the later windows are used.
The Test F scripts are imported, never changed, and no Test F or Study 3 output is written.

Choices NOT IN ADDENDUM (fixed here before any D1 result):
 Part 1
  1. y(t+j) comes from the benchmark history that step 25 uses (benchmark/_stage2_common.history(): the log share at every origin
     with a row) joined with the benchmark's stored targets (wide2.parquet y_true at horizons 1 to 3 and y_t), because the history
     stops one month before the last target month (2026-08). The run stops if the two ever disagree. For k = 1 this is exactly
     y_true - y_t of step 25.
  2. A row needs all k months observed (a missing or excluded month drops the row), and rows whose window ends after the last
     month are dropped (the rule addendum i gives D1_horizons_books). Each k is scored on its own rows (groups of at least 10 rows
     recounted on them).
  3. Main comparison across k: all four k on the same rows (the rows that have k = 12), with paired differences k minus 1 from the
     same block draws (same rows for comparisons).
  4. Sensitivity (not the main interval): because c_k of neighbouring origins share months, intervals are also shown with blocks of
     max(3, k) origin months (same algorithm and seed as the 3-month blocks; with 3 it is the fixed one).
  5. Placebo: x of each row replaced by the x of another theme in the same origin month, format and level (a fixed random
     permutation within each group, seed 20261022); its mean Spearman should be near 0 for every k.
 Part 2
  6. Synthetic control after month +6: the record's code builds the synthetic control on months -24 to +6 (its last month is
     max(primary, secondary, carry-over lag) = +6). The same weights and donors (fitted on months -24 to -3, pool chosen by the
     record's rules) are carried forward to months 7 to 11 with the same demeaning; a month counts as missing when the treated theme
     or any donor with a positive weight is missing. Months 0 to 6 are the record's values unchanged.
  7. Own trend after month +6: the record's event-study model (trend and month-of-year effects fitted on months -30 to -7) is
     projected to month +11 (only the projection is longer; the fit is unchanged).
  8. A new window (3 to 5, 6 to 11, 0 to 11) is used only when its last month is inside the panel for that level and format (as in
     choice 2); inside it the record's rule holds (a window with fewer than 2 available months is missing). Months 0 to 2 and 0 to
     5 keep the record's rule as stored.
  9. Donor screen unchanged (no rise start in months -6 to +6, record): a donor can have its own rise in months 7 to 11; and the
     treated theme can have later rises. Descriptive sensitivity: rises whose theme has no other rise start of the same series
     (any class, flagged or seasonal included) in months +1 to +11.
 10. Main windows table: each window on every test where it is available. Comparison of windows: the tests that have all of
     months 0 to 2, 3 to 5 and 6 to 11 (then 0 to 11 too), with paired differences (later window minus months 0 to 2) and the mean
     gap per month -6 to +11, all from one clustered bootstrap (same draws for every column). As in step 24's pooled rows, the own
     trend is pooled over the tests that have a synthetic control.
 11. Positive control (wiring check of choices 6 to 8): a lift of 0.10 in log share added to panel a in months 6 to 11 after every
     tested lasting rise of S2C (all formats, as step 24's --mock-inject does for months 0 to 2); the pooled months 6 to 11 effect
     should rise by about 0.10 and months 0 to 2 should barely move. Run on S2C only.
 12. Placebo categories, placebo years, rank p-values and Benjamini-Hochberg are not computed for the new windows (addendum i:
     descriptive); they do not change any effect estimate.

Outputs: data/db/wiki_led/dirs/d1_themes/ (ranking_by_k.csv, ranking_same_rows.csv, ranking_pairs_by_k.csv, ranking_placebo.csv,
effects_tests_<series>.parquet, effects_windows.csv, effects_same_tests.csv, effects_monthly_gaps.csv, effects_positive_control.csv,
checks.json, summary.json); report data/reports/dir_d1_horizons_themes.md.
Run from code/:
  nice -n 10 ../.venv/bin/python main_study/wiki_led/dirs/d1_horizons_themes.py --part ranking
  bash ../jobs/heavy_lock.sh nice -n 10 ../.venv/bin/python main_study/wiki_led/dirs/d1_horizons_themes.py --part effects
  nice -n 10 ../.venv/bin/python main_study/wiki_led/dirs/d1_horizons_themes.py --part report --lines FILE   (FILE: the five opening lines)
"""
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '1')
import sys, json, time, pathlib, argparse, hashlib, importlib, importlib.util, contextlib
HERE = pathlib.Path(__file__).resolve().parent                  # code/main_study/wiki_led/dirs
TF = HERE.parent / 'testF'
sys.path.insert(0, str(TF))
import numpy as np, pandas as pd
import _testf_analysis as T                                      # checks the addendum g fingerprints on import
S = M = None                                                     # Study 3 settings and methods, loaded by study3() for Part 2 only (Part 1 loads
                                                                 # the benchmark helper, which imports study4's _settings under the same name)


def study3():
    global S, M
    sys.path.insert(0, str(T.MAIN / 'interest'))
    sys.path.insert(0, str(T.MAIN / 'study3'))
    from _settings import SETTINGS as S_                         # Study 3 record + addenda (hash-checked)
    import _methods as M_
    if not hasattr(S_, 'window_primary'):
        raise SystemExit('the Study 3 settings module was shadowed by another _settings module')
    S, M = S_, M_

ADD_I = T.ADD / '2026-10-22_i_directions.json'
OUT = T.D / 'db' / 'wiki_led' / 'dirs' / 'd1_themes'
REPORT = T.D / 'reports' / 'dir_d1_horizons_themes.md'
KS = (1, 3, 6, 12)
SERIES_X = {'S2C (AI concept pages)': 'aic2_wlog', 'S2 (AI pages)': 'ais2_wlog', 'concept pages (hand-checked)': 'cur_wlog'}
STORED_NAME = {'S2C (AI concept pages)': ('h_g3_wikionly.csv', 'S2C (AI concept pages)'), 'S2 (AI pages)': ('g3_wikionly.csv', 'S2 (AI pages)'),
               'concept pages (hand-checked)': ('g3_wikionly.csv', 'concept pages')}
PLACEBO_SEED = 20261022
LAST_EXT = 11                                                    # last month after month 0 that the windows reach
WINDOWS = {'m0_2': (0, 2), 'm3_5': (3, 5), 'm6_11': (6, 11), 'm0_11': (0, 11), 'm0_5': (0, 5)}
NEW_WINDOWS = ('m3_5', 'm6_11', 'm0_11')                         # choice 8 applies to these
WIN_LABEL = {'m0_2': 'months 0 to 2', 'm3_5': 'months 3 to 5', 'm6_11': 'months 6 to 11', 'm0_11': 'months 0 to 11', 'm0_5': 'months 0 to 5'}
RELS = np.arange(-6, LAST_EXT + 1)                               # months kept per test (gaps)
LIFT = 0.10                                                      # choice 11
EFFECT_SERIES = ('S2C', 'S2', 'concept')
EFFECT_LABEL = {'S2C': 'S2C (AI concept pages)', 'S2': 'S2 (AI pages)', 'concept': 'concept pages (hand-checked, Chapter 6)'}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def check_addendum():
    sha = T.sha256_file(ADD_I)
    if sha not in (T.PREREG / 'README.md').read_text():
        raise SystemExit(f'{ADD_I.name} (SHA-256 {sha}) is not the fingerprinted record in prereg/README.md; nothing runs')
    return sha


def write_csv(df, name):
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / name, index=False)


def update_json(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / name
    cur = json.loads(f.read_text()) if f.exists() else {}
    cur.update(obj)
    T.write_json(cur, f)


# ================================================================ Part 1: ranking over horizons k
def monthly_log_share(G3, s):
    """{(group, format, level, node_id, mi): log share} from the benchmark history joined with the stored targets (choice 1)."""
    C = load_module('bm_s2c', G3.BENCH / '_stage2_common.py')
    H = C.history()
    parts = [pd.DataFrame(dict(group=k[0], format=k[1], level=k[2], node_id=k[3], mi=v.index.astype(int), y=v.to_numpy(float)))
             for k, v in H.items() if k[0] == 'seattle' and k[1] in ('print', 'ebook')]
    wd = pd.read_parquet(G3.WIDE2, columns=['group', 'format', 'level', 'node_id', 'origin_mi', 'h', 'y_true', 'y_t'])
    wd = wd[(wd.group == 'seattle') & wd.format.isin(['print', 'ebook']) & wd.h.isin([1, 2, 3])]
    for h in (1, 2, 3):
        w = wd[wd.h == h]
        a = w.dropna(subset=['y_true'])
        parts.append(pd.DataFrame(dict(group=a.group, format=a.format, level=a.level, node_id=a.node_id, mi=(a.origin_mi + h).astype(int), y=a.y_true)))
        b = w.dropna(subset=['y_t'])
        parts.append(pd.DataFrame(dict(group=b.group, format=b.format, level=b.level, node_id=b.node_id, mi=b.origin_mi.astype(int), y=b.y_t)))
    L = pd.concat(parts, ignore_index=True)
    g = L.groupby(['group', 'format', 'level', 'node_id', 'mi']).y.agg(['min', 'max'])
    dis = float((g['max'] - g['min']).abs().max())
    if dis > 1e-9:
        raise SystemExit(f'the benchmark history and the stored targets disagree (max {dis}); nothing runs')
    return g['min'].to_dict(), dict(cells=len(g), max_disagreement=dis, last_month=T.ym(int(g.index.get_level_values('mi').max())))


def add_targets(s, U):
    key = list(zip(s.group, s.format, s.level, s.node_id))
    o = s.origin_mi.to_numpy(int)
    Ymat = np.column_stack([np.array([U.get((*k, oo + j), np.nan) for k, oo in zip(key, o)]) for j in range(1, max(KS) + 1)])
    for k in KS:
        win = Ymat[:, :k]
        c = win.mean(axis=1) - s.y_t.to_numpy(float)
        c[np.isnan(win).any(axis=1)] = np.nan
        s[f'c{k}'] = c
    return s


def block_draws_L(n_months, L, seed, nboot):
    """block_draws_c of step 25 with block length L (L = 3 gives exactly the fixed draws)."""
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n_months / L))
    return np.array([np.concatenate([np.arange(a_, a_ + L) % n_months for a_ in rng.choice(n_months, nb)])[:n_months] for _ in range(nboot)])


@contextlib.contextmanager
def blocks_of(G3, L):
    """Run step 25's test_c_scores with blocks of L months (choice 4); restores the fixed function afterwards."""
    orig = G3.block_draws_c
    G3.block_draws_c = lambda n, seed=G3.SEED_C, nboot=G3.NB: block_draws_L(n, L, seed, nboot)
    try:
        yield
    finally:
        G3.block_draws_c = orig


def placebo_x(s, xcols, seed):
    """Choice 5: x permuted across the rows of each origin x format x level group (one fixed permutation per group)."""
    rng = np.random.default_rng(seed)
    out = s.copy()
    for _, idx in s.groupby(['origin_mi', 'format', 'level']).indices.items():
        p = rng.permutation(idx)
        for x in xcols:
            out.iloc[idx, out.columns.get_loc(x)] = s[x].to_numpy()[p]
    return out


def part_ranking():
    t0 = time.time()
    sha = check_addendum()
    G3 = load_module('g3', TF / '25_G3_forecast.py')
    assert all(np.array_equal(block_draws_L(n, 3, G3.SEED_C, 50), G3.block_draws_c(n, nboot=50)) for n in (30, 91)), 'block draws differ'
    s = G3.main_rows()
    U, uinfo = monthly_log_share(G3, s)
    s = add_targets(s, U)
    d1 = float(np.nanmax(np.abs(s.c1 - (s.y_true - s.y_t))))
    if s.c1.isna().any() or d1 > 1e-12:
        raise SystemExit(f'k = 1 target is not y_true - y_t of step 25 ({int(s.c1.isna().sum())} missing, max diff {d1})')
    Mser = pd.read_parquet(T.REAL_DIR / 'series_monthly.parquet')
    MC = pd.read_parquet(G3.MCOV)
    xs = {}
    for name, col in SERIES_X.items():
        frame = MC if col == 'cur_wlog' else Mser
        xn = 'x_' + col
        s = G3.attach_x(s, G3.changes(frame, col), xn)
        xs[name] = xn
    xcols = list(xs.values())
    checks = {}
    rows, pairs, rows_same, plac = [], [], [], []
    # each k on its own rows
    for k in KS:
        sk = s[s[f'c{k}'].notna()].reset_index(drop=True)
        W, Dr = G3.test_c_scores(sk, xcols, ccol=f'c{k}')
        L = max(3, k)
        if L != 3:
            with blocks_of(G3, L):
                WL, _ = G3.test_c_scores(sk, xcols, ccol=f'c{k}')
        else:
            WL = W
        for name, xn in xs.items():
            rows.append(dict(series=name, k=k, rows=len(sk), origin_months=sk.origin_mi.nunique(), first_origin=T.ym(sk.origin_mi.min()),
                             last_origin=T.ym(sk.origin_mi.max()), **W[xn], block_months_sensitivity=L, lo_long_blocks=WL[xn]['lo'], hi_long_blocks=WL[xn]['hi']))
        for a_, b_ in (('concept pages (hand-checked)', 'S2C (AI concept pages)'), ('concept pages (hand-checked)', 'S2 (AI pages)'),
                       ('S2 (AI pages)', 'S2C (AI concept pages)')):
            pairs.append(dict(k=k, rows=len(sk), **(G3.paired(Dr, W, xs[a_], xs[b_]) | dict(base=a_, other=b_))))
        if k == 1:                                                 # reproduction of the stored Test F numbers
            for name, xn in xs.items():
                f, lab = STORED_NAME[name]
                st = pd.read_csv(T.REAL_DIR / f).set_index('series').loc[lab]
                diff = max(abs(W[xn][c] - float(st[c])) for c in ('rho', 'lo', 'hi'))
                checks[f'k1_{name}'] = dict(stored_file=f, stored=dict(rho=float(st.rho), lo=float(st.lo), hi=float(st.hi)), mine=W[xn],
                                            max_abs_diff=diff, reproduced=bool(diff < 1e-12 and int(st.groups) == W[xn]['groups']))
            if not all(v['reproduced'] for v in checks.values()):
                write_csv(pd.DataFrame(rows), 'ranking_by_k.csv')
                update_json('checks.json', dict(ranking=checks))
                raise SystemExit('k = 1 does not reproduce the stored Test F ranking; nothing else is computed')
            T.log('k = 1 reproduces g3_wikionly.csv and h_g3_wikionly.csv exactly')
        # placebo (choice 5)
        pk = placebo_x(sk, xcols, PLACEBO_SEED)
        WP, _ = G3.test_c_scores(pk, xcols, ccol=f'c{k}')
        for name, xn in xs.items():
            plac.append(dict(series=name, k=k, rows=len(sk), **WP[xn]))
    # all k on the same rows (those with k = 12), paired k minus 1 (choice 3)
    same = s[s.c12.notna()].reset_index(drop=True)
    res = {k: G3.test_c_scores(same, xcols, ccol=f'c{k}') for k in KS}
    for name, xn in xs.items():
        for k in KS:
            W, Dr = res[k]
            r = dict(series=name, k=k, rows=len(same), origin_months=same.origin_mi.nunique(), first_origin=T.ym(same.origin_mi.min()),
                     last_origin=T.ym(same.origin_mi.max()), **W[xn])
            d = Dr[xn] - res[1][1][xn]
            r.update(diff_vs_k1=W[xn]['rho'] - res[1][0][xn]['rho'], diff_lo=float(np.percentile(d, 2.5)), diff_hi=float(np.percentile(d, 97.5)))
            rows_same.append(r)
    write_csv(pd.DataFrame(rows), 'ranking_by_k.csv')
    write_csv(pd.DataFrame(rows_same), 'ranking_same_rows.csv')
    write_csv(pd.DataFrame(pairs), 'ranking_pairs_by_k.csv')
    write_csv(pd.DataFrame(plac), 'ranking_placebo.csv')
    lost = {k: dict(rows=int(s[f'c{k}'].notna().sum()), rows_before_window_end=int((s.origin_mi + k <= max(m for *_, m in U.keys())).sum()))
            for k in KS}
    update_json('checks.json', dict(ranking=checks))
    update_json('summary.json', dict(addendum_i_sha256=sha, ranking=dict(history=uinfo, rows_per_k=lost, same_rows=len(same),
                                                                         seconds=round(time.time() - t0), peak_gb=round(T.peak_gb(), 2))))
    T.log(f'part 1 done in {time.time() - t0:.0f}s')


# ================================================================ Part 2: event windows
class Ext:
    """The Study 3 settings with one change (choice 7): the event study projects to month +11 (the last month any method looks at is
    max(primary, secondary, carry-over lag), so the lag window's end is set to +11 here). Fit, windows and every other value are the
    record's."""

    def __init__(self, base):
        self.base = base

    def __getattr__(self, k):
        if k.startswith('_') or k == 'base':
            raise AttributeError(k)
        if k == 'carry_lag':
            return (self.base.carry_lag[0], LAST_EXT)
        return getattr(self.base, k)


def _win(gap, rels, win, m0, last, new, min_avail):
    if new and m0 + win[1] > last:                               # choice 8: the whole window must be inside the panel
        return np.nan
    sel = (rels >= win[0]) & (rels <= win[1])
    return M.window_mean(gap[sel], min_avail)[0]


def unit_ext(ctx, level, fmt, node, m0):
    """One test: the record's event study and synthetic control (no placebos), with gaps to month +11 (choices 6 to 8)."""
    Sx = ctx.S
    rec = dict(level=level, format=fmt, node_id=node, m0=int(m0))
    Y = ctx.Y.get((level, fmt))
    if Y is None or node not in Y.columns:
        rec['skip'] = 'no data'
        return rec
    if not ctx.size_ok(level, fmt, node, m0):
        rec['skip'] = 'below minimum size'
        return rec
    last = int(Y.index.max())
    rec['last_mi'] = last
    es = M.event_study(Y[node], m0, Ext(Sx))
    rec['es_ok'] = bool(es['es_ok'])
    if es['es_ok']:
        rec['es_effect_p'], rec['es_effect_s'] = es['es_effect_p'], es['es_effect_s']
        g = np.array([es['es_gaps'].get(int(r), np.nan) for r in RELS], dtype=float)
        for r, v in zip(RELS, g):
            rec[f'es_g{r}'] = v
        for w, win in WINDOWS.items():
            rec[f'es_{w}'] = _win(g, RELS, win, m0, last, w in NEW_WINDOWS, Sx.min_window_months)
    pool = ctx.donors(level, fmt, node, m0)
    prep = M.sc_prepare(Y, node, pool, m0, Sx)
    rec['sc_n_donors'] = len(prep['donors'])
    if len(prep['donors']) < M.MIN_DONORS:
        rec.update(sc_ok=False, skip='too few donors')
        return rec
    F = M.sc_fit(prep['y'], prep['X'], prep['rel'], prep['obs'], Sx)
    if F is None:
        rec.update(sc_ok=False, skip='too few fit months')
        return rec
    rec.update(sc_ok=True, skip='')
    rel0 = prep['rel']                                           # -24 .. +6 (the record's synthetic-control months)
    fitm = prep['obs'] & (rel0 >= Sx.sc_fit[0]) & (rel0 <= Sx.sc_fit[1])
    ybar, Xbar = prep['y'][fitm].mean(), prep['X'][fitm].mean(axis=0)
    w = F['w']
    pos = w > 0
    ext = np.arange(int(rel0[-1]) + 1, LAST_EXT + 1)
    ye = M.values(Y[node], m0 + ext)
    Xe = Y.reindex(index=m0 + ext, columns=[d for d, p in zip(prep['donors'], pos) if p]).to_numpy(dtype=float)
    ge = (ye - ybar) - (Xe - Xbar[pos]) @ w[pos]                  # NaN when the theme or a weighted donor is missing (choice 6)
    rels = np.concatenate([rel0, ext])
    gap = np.concatenate([F['gap'], ge])
    st_p = M.window_stats(F['gap'], rel0, Sx.window_primary, F['pre_rmspe'], Sx)
    st_s = M.window_stats(F['gap'], rel0, Sx.window_secondary, F['pre_rmspe'], Sx)
    rec['sc_effect_p'], rec['sc_effect_s'], rec['sc_pre_rmspe'] = st_p['effect'], st_s['effect'], F['pre_rmspe']
    for r in RELS:
        rec[f'sc_g{r}'] = float(gap[rels == r][0]) if (rels == r).any() else np.nan
    for wn, win in WINDOWS.items():
        rec[f'sc_{wn}'] = _win(gap, rels, win, m0, last, wn in NEW_WINDOWS, Sx.min_window_months)
    return rec


def effect_inputs(name, G2):
    """Rises to test (Xn) and the rises for the donor and placebo screens (Xs), as stored by step 24 or Chapter 6."""
    G = G2.load_shifts(G2.IO.Paths(), S)
    if name == 'concept':
        return G[G.source == 'wikipedia'].reset_index(drop=True), G
    P = T.Paths()
    X = pd.read_parquet(P / f'shifts_{name}.parquet')
    X['start_week'] = pd.to_datetime(X.start_week)
    Xd = G2.desktop_flags(P, X, name)
    if Xd is None:
        raise SystemExit(f'desktop_{name}.parquet not found')
    if int((Xd.driver.notna() & ~Xd.desktop_checked).sum()):
        raise SystemExit(f'some rises of {name} have no desktop views')
    X = Xd
    X['quality_flag'] = [','.join(f for f, on in (('one_day', sd), ('desktop_only', dr)) if on)
                         for sd, dr in zip(X.single_day.fillna(False), X.desktop_rise.fillna(False))]
    X['quality_ok'] = X.quality_flag == ''
    Xn = G2.normalise_shifts(X.drop(columns=[c for c in ('m0',) if c in X.columns]), S)
    Xn['series'] = name
    return Xn, pd.concat([Xn, G[G.source == 'gdelt']], ignore_index=True)


def run_tests(G2, Xn, Xs, panel, nodes, overlap, workers, only=None):
    ctx = G2.A3.Context(panel, nodes, overlap, Xs, S)
    s, items = G2.E12.plan(Xn, ctx, False)
    if only is not None:
        items = [it for it in items if (it[0], it[2], it[3]) in only]
    res = G2.A3.run_parallel(unit_ext, ctx, items, workers)
    Tt = pd.DataFrame(res)
    R = s[G2.E12.SHIFT_COLS].merge(Tt, on=['level', 'node_id', 'm0'], how='inner')
    R['analysis'] = np.where(R.seasonal, 'seasonal', 'main')
    R['sc_ok'] = R.sc_ok.fillna(False).astype(bool)
    return R, s, ctx


def compare_tests(R, name):
    """Per-test check against the stored run (months 0 to 2 and 0 to 5 effects, and the stored gaps of months 3 to 6)."""
    if name == 'concept':
        St = pd.read_parquet(T.D / 'db' / 'study3' / 'shift_effects.parquet')
        St = St[St.source == 'wikipedia']
    else:
        St = pd.read_parquet(T.REAL_DIR / f'g2_{name}_tests_a.parquet')
    k = ['shift_id', 'format']
    m = R.merge(St[k + ['sc_ok', 'sc_effect_p', 'es_effect_p', 'sc_effect_s', 'es_effect_s', 'sc_gaps', 'es_gaps']], on=k, how='outer',
                suffixes=('', '_st'), indicator=True)
    out = dict(rows_mine=len(R), rows_stored=len(St), only_one_side=int((m._merge != 'both').sum()))
    m = m[m._merge == 'both']
    out['sc_ok_differs'] = int((m.sc_ok.astype(bool) != m.sc_ok_st.fillna(False).astype(bool)).sum())
    for c in ('sc_effect_p', 'es_effect_p', 'sc_effect_s', 'es_effect_s'):
        a, b = m[c].to_numpy(float), m[f'{c}_st'].to_numpy(float)
        out[f'{c}_nan_differs'] = int((np.isnan(a) != np.isnan(b)).sum())
        both = ~np.isnan(a) & ~np.isnan(b)
        out[f'{c}_max_abs_diff'] = float(np.max(np.abs(a[both] - b[both]))) if both.any() else 0.0
    gd = []
    for tag in ('sc', 'es'):
        for r_, js in zip(m.itertuples(), m[f'{tag}_gaps']):
            if not isinstance(js, str):
                continue
            g = json.loads(js)
            for rr in (3, 4, 5, 6):
                v = g.get(str(rr))
                mine = getattr(r_, f'{tag}_g{rr}', np.nan)
                if v is not None and not (isinstance(mine, float) and np.isnan(mine)):
                    gd.append(abs(v - mine))
    out['gaps_3_to_6_compared'] = len(gd)
    out['gaps_3_to_6_max_abs_diff'] = float(max(gd)) if gd else None
    out['reproduced'] = bool(out['only_one_side'] == 0 and out['sc_ok_differs'] == 0 and
                             all(out[f'{c}_nan_differs'] == 0 and out[f'{c}_max_abs_diff'] < 1e-9 for c in ('sc_effect_p', 'es_effect_p', 'sc_effect_s', 'es_effect_s'))
                             and (out['gaps_3_to_6_max_abs_diff'] or 0) < 1e-9)
    return out


def compare_pooled(R, name, G2, n_boot):
    """Pooled months 0 to 2 (and 0 to 5) rows against the stored pooled file, with the stored code (12_shift_effects.pooled and step
    24's both_levels)."""
    Pt = pd.concat([G2.E12.pooled(R, n_boot), G2.both_levels(R, n_boot)], ignore_index=True)
    if name == 'concept':
        St = pd.read_csv(T.D / 'db' / 'study3' / 'pooled_effects.csv')
        St = St[St.source == 'wikipedia']
    else:
        St = pd.read_csv(T.REAL_DIR / f'g2_{name}_pooled.csv')
        St = St[St.panel == 'a']
    k = ['analysis', 'source', 'level', 'format', 'duration_class']
    num = [c for c in St.columns if c.endswith(('_mean', '_ci_low', '_ci_high'))] + ['tests', 'shifts', 'categories']
    m = Pt.merge(St[k + num], on=k, how='inner', suffixes=('', '_st'))
    diffs = {c: float(np.nanmax(np.abs(m[c].to_numpy(float) - m[f'{c}_st'].to_numpy(float)))) for c in num if c in Pt}
    out = dict(rows_compared=len(m), rows_stored=len(St), rows_mine=len(Pt), max_abs_diff=max(diffs.values()), by_column=diffs)
    out['reproduced'] = bool(len(m) == len(St) and out['max_abs_diff'] < 1e-9)
    both = Pt[(Pt.analysis == 'main') & (Pt.level == 'both') & (Pt.duration_class == 'sustained')]
    out['both_sustained_m0_2'] = both[['tests', 'categories', 'sc_effect_p_mean', 'sc_effect_p_ci_low', 'sc_effect_p_ci_high',
                                       'es_effect_p_mean', 'es_effect_p_ci_low', 'es_effect_p_ci_high']].iloc[0].to_dict() if len(both) else None
    return out, Pt


def pool(v, col, n_boot):
    v = v.dropna(subset=[col]).reset_index(drop=True)
    r = dict(tests=len(v), shifts=v.shift_id.nunique(), categories=v.node_id.nunique(), mean=float(v[col].mean()) if len(v) else np.nan,
             ci_low=np.nan, ci_high=np.nan)
    if v.node_id.nunique() >= 2:
        bs = M.cluster_bootstrap(v, 'node_id', lambda d: float(d[col].mean()), n_boot, S.boot_seed)
        r['ci_low'], r['ci_high'] = M.percentile_ci(bs)
    return r


def joint(v, cols, n_boot):
    """Means of several columns with one clustered bootstrap (the same draws for every column)."""
    v = v.reset_index(drop=True)
    est = v[cols].mean()
    B = pd.DataFrame(M.cluster_bootstrap(v, 'node_id', lambda d: d[cols].mean(), n_boot, S.boot_seed))
    return {c: dict(mean=float(est[c]), ci_low=M.percentile_ci(B[c])[0], ci_high=M.percentile_ci(B[c])[1]) for c in cols}


def isolated(R, Xn):
    """Choice 9: no other rise start of the same series in the same theme in months +1 to +11."""
    m0s = {k: np.sort(g.m0.to_numpy()) for k, g in Xn.groupby(['level', 'node_id'])}
    out = []
    for lv, n, m0 in zip(R.level, R.node_id, R.m0):
        a = m0s.get((lv, n), np.array([]))
        out.append(not np.any((a >= m0 + 1) & (a <= m0 + LAST_EXT)))
    return np.array(out)


def window_rows(R, label, n_boot):
    rows = []
    ok = R[(R.analysis == 'main') & R.sc_ok]
    for lv in ('both', 'narrow', 'middle'):
        for cls in (('sustained', 'fading', 'all') if lv == 'both' else ('sustained',)):
            g = ok if lv == 'both' else ok[ok.level == lv]
            g = g if cls == 'all' else g[g.duration_class == cls]
            for meth in ('sc', 'es'):
                for wn in WINDOWS:
                    col = f'{meth}_{wn}'
                    if col not in g:
                        continue
                    r = pool(g, col, n_boot)
                    rows.append(dict(series=label, panel='a', level=lv, duration_class=cls, method='synthetic control' if meth == 'sc' else 'own trend',
                                     window=WIN_LABEL[wn], **r))
    return rows


def same_test_rows(R, label, n_boot, subset='all lasting rises'):
    rows, prof = [], []
    g0 = R[(R.analysis == 'main') & R.sc_ok & (R.duration_class == 'sustained')]
    for meth in ('sc', 'es'):
        g = g0.dropna(subset=[f'{meth}_m0_2', f'{meth}_m3_5', f'{meth}_m6_11', f'{meth}_m0_11']).copy()
        if g.node_id.nunique() < 2:
            continue
        for wn in ('m3_5', 'm6_11', 'm0_11'):
            g[f'd_{wn}'] = g[f'{meth}_{wn}'] - g[f'{meth}_m0_2']
        cols = [f'{meth}_{w}' for w in ('m0_2', 'm3_5', 'm6_11', 'm0_11')] + [f'd_{w}' for w in ('m3_5', 'm6_11', 'm0_11')]
        gcols = [f'{meth}_g{r}' for r in RELS]
        J = joint(g, cols + gcols, n_boot)
        mname = 'synthetic control' if meth == 'sc' else 'own trend'
        base = dict(series=label, subset=subset, method=mname, tests=len(g), shifts=g.shift_id.nunique(), categories=g.node_id.nunique(),
                    first_month0=T.ym(g.m0.min()), last_month0=T.ym(g.m0.max()))
        for c in cols:
            what = WIN_LABEL['m' + c.split('_m', 1)[1]] if not c.startswith('d_') else f'{WIN_LABEL[c[2:]]} minus months 0 to 2'
            rows.append(dict(base, quantity=what, **J[c]))
        for r, c in zip(RELS, gcols):
            prof.append(dict(series=label, subset=subset, method=mname, tests=len(g), month=int(r), available=int(g[c].notna().sum()), **J[c]))
    return rows, prof


def inject_late(panel, Xn, lift):
    """Choice 11: add `lift` to the log share of each tested lasting rise's theme in months 6 to 11 (all formats); step 24's inject()
    with the later window."""
    p = panel.copy()
    t = Xn[Xn.labelled & Xn.quality_ok & (Xn.duration_class == 'sustained') & Xn.level.isin(S.levels_tested) & ~Xn.seasonal
           & (Xn.m0 >= G2_mi(S.study_start))]
    key = pd.MultiIndex.from_frame(p[['level', 'node_id', 'mi']])
    want = sorted({(lv, nid, int(m0) + k) for lv, nid, m0 in zip(t.level, t.node_id, t.m0) for k in range(6, LAST_EXT + 1)})
    hit = key.isin(pd.MultiIndex.from_tuples(want)) if want else np.zeros(len(p), bool)
    p.loc[hit, 'log_share'] = p.loc[hit, 'log_share'] + lift
    return p, int(hit.sum())


def G2_mi(ym):
    y, m = ym.split('-')
    return int(y) * 12 + int(m) - 1


def part_effects(workers, series):
    t0 = time.time()
    sha = check_addendum()
    study3()
    G2 = load_module('g2', TF / '24_G2_matchmaking.py')
    if G2.S is not S or G2.M is not M:
        raise SystemExit('step 24 and this script do not share the Study 3 settings and methods')
    P3 = G2.IO.Paths()
    panel, nodes, overlap = G2.IO.load_panels(P3), G2.IO.read_parquet(P3.nodes), G2.IO.read_parquet(P3.overlap)
    n_boot = S.boot_n
    checks = json.loads((OUT / 'checks.json').read_text()).get('effects', {}) if (OUT / 'checks.json').exists() else {}
    win_all, same_all, prof_all = [], [], []
    old = OUT / 'effects_windows.csv'
    keep_old = {}
    if old.exists():                                              # rows of series not rerun now are kept
        for f, lst in (('effects_windows.csv', win_all), ('effects_same_tests.csv', same_all), ('effects_monthly_gaps.csv', prof_all)):
            if (OUT / f).exists():
                d = pd.read_csv(OUT / f)
                keep_old[f] = d[~d.series.isin([EFFECT_LABEL[x] for x in series])]
    for name in series:
        lab = EFFECT_LABEL[name]
        Xn, Xs = effect_inputs(name, G2)
        R, s, ctx = run_tests(G2, Xn, Xs, panel, nodes, overlap, workers)
        T.log(f'{name}: {len(R):,} tests ({int(R.sc_ok.sum()):,} with a synthetic control); {time.time() - t0:.0f}s')
        ct = compare_tests(R, name)
        cp, _ = compare_pooled(R, name, G2, n_boot)
        checks[name] = dict(tests=ct, pooled=cp)
        update_json('checks.json', dict(effects=checks))
        T.log(f'{name}: per-test check reproduced={ct["reproduced"]}, pooled check reproduced={cp["reproduced"]} (max diff {cp["max_abs_diff"]:.2e})')
        if not (ct['reproduced'] and cp['reproduced']):
            raise SystemExit(f'{name}: months 0 to 2 do not reproduce the stored run; the later windows are not computed (see checks.json)')
        R['isolated'] = isolated(R, Xn)
        R.to_parquet(OUT / f'effects_tests_{name}.parquet', index=False)
        win_all += window_rows(R, lab, n_boot)
        a, b = same_test_rows(R, lab, n_boot)
        same_all += a; prof_all += b
        a, b = same_test_rows(R[R.isolated], lab, n_boot, subset='no other rise of the theme in months 1 to 11')
        same_all += a; prof_all += b
        T.log(f'{name}: windows pooled; {time.time() - t0:.0f}s')
        if name == 'S2C':                                         # positive control (choice 11)
            pin, nh = inject_late(panel, Xn, LIFT)
            sus = R[(R.analysis == 'main') & (R.duration_class == 'sustained')]
            only = set(zip(sus.level, sus.node_id, sus.m0))
            Ri, _, _ = run_tests(G2, Xn, Xs, pin, nodes, overlap, workers, only=only)
            base = R[(R.analysis == 'main') & R.sc_ok & (R.duration_class == 'sustained')]
            inj = Ri[(Ri.analysis == 'main') & Ri.sc_ok & (Ri.duration_class == 'sustained')]
            pc = []
            for meth in ('sc', 'es'):
                for wn in ('m0_2', 'm3_5', 'm6_11', 'm0_11'):
                    r0, r1 = pool(base, f'{meth}_{wn}', 0), pool(inj, f'{meth}_{wn}', 0)
                    pc.append(dict(series=lab, method='synthetic control' if meth == 'sc' else 'own trend', window=WIN_LABEL[wn], lift=LIFT,
                                   cells_lifted=nh, tests_real=r0['tests'], tests_lifted=r1['tests'], mean_real=r0['mean'], mean_lifted=r1['mean'],
                                   difference=r1['mean'] - r0['mean']))
            write_csv(pd.DataFrame(pc), 'effects_positive_control.csv')
            T.log(f'positive control done; {time.time() - t0:.0f}s')
    for f, lst in (('effects_windows.csv', win_all), ('effects_same_tests.csv', same_all), ('effects_monthly_gaps.csv', prof_all)):
        d = pd.DataFrame(lst)
        if f in keep_old:
            d = pd.concat([keep_old[f], d], ignore_index=True)
        write_csv(d, f)
    update_json('summary.json', dict(addendum_i_sha256=sha, effects=dict(series=list(series), boot=n_boot, seed=S.boot_seed,
                                                                         record_windows=dict(primary=S.window_primary, secondary=S.window_secondary),
                                                                         last_panel_month={f'{lv}|{fm}': T.ym(int(Y.index.max())) for (lv, fm), Y in ctx.Y.items()},
                                                                         seconds=round(time.time() - t0), peak_gb=round(T.peak_gb(), 2),
                                                                         finished=time.strftime('%Y-%m-%d %H:%M'))))
    T.log(f'part 2 done in {time.time() - t0:.0f}s; peak memory {T.peak_gb():.2f} GB')


# ================================================================ report
def f3(x):
    return '' if x is None or x != x else f'{x:+.3f}'


def ci(m, lo, hi):
    return f'{f3(m)} [{f3(lo)}, {f3(hi)}]'


def pct(x):
    return '' if x is None or x != x else f'{100 * (np.exp(x) - 1):+.1f}%'


def part_report(lines5):
    """Writes the report from the stored D1 files. lines5: the five plain-language opening lines (written after reading the results)."""
    chk = json.loads((OUT / 'checks.json').read_text())
    summ = json.loads((OUT / 'summary.json').read_text())
    RK = pd.read_csv(OUT / 'ranking_by_k.csv')
    RS = pd.read_csv(OUT / 'ranking_same_rows.csv')
    RP = pd.read_csv(OUT / 'ranking_pairs_by_k.csv')
    PL = pd.read_csv(OUT / 'ranking_placebo.csv')
    L = [f'# Direction D1 (themes): longer horizons for the theme tests', ''] + lines5 + ['',
         f'- written {pd.Timestamp.now():%Y-%m-%d %H:%M} +07 by code/main_study/wiki_led/dirs/d1_horizons_themes.py; record '
         f'prereg/addenda_wiki_led/2026-10-22_i_directions.json (SHA-256 {summ["addendum_i_sha256"][:12]}..., fixed 22 Oct 03:13 before any '
         'result), key D1_horizons_themes; every interval is a 95% interval; descriptive (no decision rule).', '',
         '## Part 1: Wikipedia-only ranking of themes, no fitting', '',
         'Input: the change of a theme\'s attention series from last month to this month. Target: the change in the theme\'s borrowing share '
         'from this month to the mean of the next k months (log share). Score: the mean Spearman correlation within origin month, format and '
         'level (the Test C measure of Test F step 25), intervals from 2,000 draws of 3-month blocks of origin months. Rows: the benchmark\'s '
         'main rows (Seattle print and ebook, 510 theme series).', '']
    ok1 = all(v['reproduced'] for v in chk['ranking'].values())
    L.append(f'- Check: k = 1 reproduces the stored Test F numbers (g3_wikionly.csv, h_g3_wikionly.csv) exactly: {"yes" if ok1 else "NO"} '
             f'(largest difference {max(v["max_abs_diff"] for v in chk["ranking"].values()):.1e}).')
    rp = summ['ranking']['rows_per_k']
    L.append('- Rows: a row needs all k months observed. ' + '; '.join(f'k = {k}: {rp[str(k)]["rows"]:,} rows' for k in KS) +
             '. Apart from the end of the data, rows are lost when the window touches months that are missing for most series: 2020-04 to '
             '2020-09 (the 2020 closure months) and 2024-05 to 2024-07 (missing in the benchmark history), so the k = 12 rows have few origins from mid-2019 to early 2020 and from '
             'mid-2023 to mid-2024 and none after 2025-08.')
    L += ['', '### Each k on its own rows', '', '| series | k | rows | origin months | Spearman [95% interval] | interval with blocks of max(3, k) months |',
          '| --- | --- | --- | --- | --- | --- |']
    for r in RK.itertuples():
        L.append(f'| {r.series} | {r.k} | {r.rows:,} | {r.origin_months} ({r.first_origin} to {r.last_origin}) | {ci(r.rho, r.lo, r.hi)} | '
                 f'[{f3(r.lo_long_blocks)}, {f3(r.hi_long_blocks)}] |')
    L += ['', f'### All k on the same rows (the {int(RS.rows.iloc[0]):,} rows that have k = 12), and k minus k = 1 from the same draws', '',
          '| series | k = 1 | k = 3 | k = 6 | k = 12 | k = 3 minus 1 | k = 6 minus 1 | k = 12 minus 1 |', '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for sname, g in RS.groupby('series', sort=False):
        g = g.set_index('k')
        L.append(f'| {sname} | ' + ' | '.join(ci(g.loc[k, 'rho'], g.loc[k, 'lo'], g.loc[k, 'hi']) for k in KS) + ' | ' +
                 ' | '.join(ci(g.loc[k, 'diff_vs_k1'], g.loc[k, 'diff_lo'], g.loc[k, 'diff_hi']) for k in KS[1:]) + ' |')
    L += ['', '### Series against each other at each k (other minus base, same draws)', '']
    for r in RP.itertuples():
        L.append(f'- k = {r.k}: {r.other} minus {r.base}: {ci(r.diff, r.lo, r.hi)}')
    L += ['', '### Placebo: each row\'s attention change swapped with another theme\'s in the same month, format and level', '']
    L.append('- ' + '; '.join(f'{r.series}, k = {r.k}: {ci(r.rho, r.lo, r.hi)}' for r in PL.itertuples()))
    # ---------------- Part 2
    L += ['', '## Part 2: borrowing after lasting rises, later months', '']
    if not (OUT / 'effects_windows.csv').exists():
        L.append('- Not done: ' + str(summ.get('effects_note', 'the event windows were not computed.')))
    else:
        W = pd.read_csv(OUT / 'effects_windows.csv')
        ST = pd.read_csv(OUT / 'effects_same_tests.csv')
        MG = pd.read_csv(OUT / 'effects_monthly_gaps.csv')
        ce = chk.get('effects', {})
        L += ['Lasting rises (4 weeks or more at 1.5 times the normal level or more) of each attention series; borrowing in panel a (the Study 3 '
              'panel: Seattle print, ebook and audiobook loans, and LibriVox); narrow and middle themes pooled; effect = mean gap in log share between '
              'the theme and its synthetic control, or between the theme and its own trend (event study), in the window; intervals from 2,000 '
              'resamples of themes (seed 20261013). Everything else as Test F step 24 and Chapter 6.', '', '### Checks', '']
        for n in EFFECT_SERIES:
            if n not in ce:
                continue
            t, p = ce[n]['tests'], ce[n]['pooled']
            b = p.get('both_sustained_m0_2') or {}
            L.append(f'- {EFFECT_LABEL[n]}: per-test months 0 to 2 and 0 to 5 effects and the stored gaps of months 3 to 6 reproduced: '
                     f'{"yes" if t["reproduced"] else "NO"} ({t["rows_mine"]:,} tests, largest difference '
                     f'{max(t[c + "_max_abs_diff"] for c in ("sc_effect_p", "es_effect_p", "sc_effect_s", "es_effect_s")):.1e}); pooled rows reproduced: '
                     f'{"yes" if p["reproduced"] else "NO"} ({p["rows_compared"]} rows, largest difference {p["max_abs_diff"]:.1e}); '
                     f'months 0 to 2, both levels, lasting rises: synthetic control {ci(b.get("sc_effect_p_mean"), b.get("sc_effect_p_ci_low"), b.get("sc_effect_p_ci_high"))}, '
                     f'own trend {ci(b.get("es_effect_p_mean"), b.get("es_effect_p_ci_low"), b.get("es_effect_p_ci_high"))}.')
        if (OUT / 'effects_positive_control.csv').exists():
            PC = pd.read_csv(OUT / 'effects_positive_control.csv')
            L.append(f'- Positive control (S2C): {LIFT:.2f} added to the log share in months 6 to 11 after every tested lasting rise '
                     f'({int(PC.cells_lifted.iloc[0]):,} theme-months); change of the pooled effect: ' +
                     '; '.join(f'{r.method}, {r.window}: {f3(r.difference)}' for r in PC.itertuples()) + '.')
        L += ['', '### Main table: lasting rises, both levels pooled, each window on every test where it is available', '',
              '| series | method | months 0 to 2 | months 3 to 5 | months 6 to 11 | months 0 to 11 |', '| --- | --- | --- | --- | --- | --- |']
        Wm = W[(W.level == 'both') & (W.duration_class == 'sustained')]
        for (sname, meth), g in Wm.groupby(['series', 'method'], sort=False):
            g = g.set_index('window')
            cells = []
            for w in ('m0_2', 'm3_5', 'm6_11', 'm0_11'):
                r = g.loc[WIN_LABEL[w]]
                cells.append(f'{ci(r["mean"], r.ci_low, r.ci_high)} ({pct(r["mean"])}; {int(r.tests)} tests, {int(r.categories)} themes)')
            L.append(f'| {sname} | {meth} | ' + ' | '.join(cells) + ' |')
        for subset in ST.subset.unique():
            Sx = ST[ST.subset == subset]
            L += ['', f'### Same tests for every window ({subset}): window means and later window minus months 0 to 2', '',
                  '| series | method | tests (themes) | months 0 to 2 | months 3 to 5 | months 6 to 11 | months 0 to 11 | 3 to 5 minus 0 to 2 | 6 to 11 minus 0 to 2 | 0 to 11 minus 0 to 2 |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
            for (sname, meth), g in Sx.groupby(['series', 'method'], sort=False):
                g = g.set_index('quantity')
                q = [WIN_LABEL[w] for w in ('m0_2', 'm3_5', 'm6_11', 'm0_11')] + [f'{WIN_LABEL[w]} minus months 0 to 2' for w in ('m3_5', 'm6_11', 'm0_11')]
                L.append(f'| {sname} | {meth} | {int(g.tests.iloc[0])} ({int(g.categories.iloc[0])}) | ' +
                         ' | '.join(ci(g.loc[x, 'mean'], g.loc[x, 'ci_low'], g.loc[x, 'ci_high']) for x in q) + ' |')
        L += ['', '### Mean gap by month after the start (same tests as above, all lasting rises), log share', '',
              '| series | method | ' + ' | '.join(f'm{m}' for m in range(-3, LAST_EXT + 1)) + ' |', '| --- | --- | ' + ' | '.join('---' for _ in range(-3, LAST_EXT + 1)) + ' |']
        MGa = MG[MG.subset == 'all lasting rises']
        for (sname, meth), g in MGa.groupby(['series', 'method'], sort=False):
            g = g.set_index('month')
            L.append(f'| {sname} | {meth} | ' + ' | '.join(f'{g.loc[m, "mean"]:+.3f}' for m in range(-3, LAST_EXT + 1)) + ' |')
        L += ['', 'Intervals for each month are in effects_monthly_gaps.csv.', '',
              '### Per level (lasting rises, each window on every test where it is available)', '']
        Wl = W[(W.level != 'both') & (W.duration_class == 'sustained') & (W.window != WIN_LABEL['m0_5'])]
        for (sname, meth, lv), g in Wl.groupby(['series', 'method', 'level'], sort=False):
            L.append(f'- {sname}, {meth}, {lv}: ' + '; '.join(f'{r.window} {ci(r.mean, r.ci_low, r.ci_high)} ({int(r.tests)} tests)' for r in g.itertuples()))
        L += ['', '### Rises of 1 or 2 weeks, for contrast (both levels)', '']
        Wf = W[(W.level == 'both') & (W.duration_class == 'fading') & (W.window != WIN_LABEL['m0_5'])]
        for (sname, meth), g in Wf.groupby(['series', 'method'], sort=False):
            L.append(f'- {sname}, {meth}: ' + '; '.join(f'{r.window} {ci(r.mean, r.ci_low, r.ci_high)} ({int(r.tests)} tests)' for r in g.itertuples()))
    share_iso = 'not computed'
    n2020 = {}
    if (OUT / 'effects_windows.csv').exists():
        parts = []
        for n in EFFECT_SERIES:
            f = OUT / f'effects_tests_{n}.parquet'
            if f.exists():
                R = pd.read_parquet(f, columns=['analysis', 'sc_ok', 'duration_class', 'isolated', 'm0'])
                R = R[(R.analysis == 'main') & R.sc_ok & (R.duration_class == 'sustained')]
                parts.append(f'{EFFECT_LABEL[n].split(" (")[0]} {100 * (1 - R.isolated.mean()):.0f}%')
                n2020[n] = f'{int(((R.m0 >= G2_mi("2020-01")) & (R.m0 <= G2_mi("2020-12"))).sum())} of {len(R)}'
        share_iso = 'share of lasting-rise tests with another rise of the same theme in months 1 to 11: ' + ', '.join(parts)
    L += ['', '## Choices the addendum did not fix (listed in the script header before any result)', '',
          '- Part 1: the monthly log share is the benchmark history joined with its stored targets (they agree exactly; the history alone '
          'stops at 2026-07); a row needs all k months observed; the main comparison across k uses the same rows; intervals with blocks of '
          'max(3, k) months are a sensitivity because neighbouring targets share months; a placebo swaps attention changes across themes.',
          '- Part 2: the synthetic control is carried to months 7 to 11 with the same weights and donors (a month is missing when a weighted '
          'donor is missing); the own-trend model is projected to month 11 with the same fit; a new window counts only when it ends inside '
          'the panel; the donor screen stays at months -6 to +6, so donors may rise later and the treated theme may rise again (one '
          'sensitivity keeps only rises with no other rise of the theme in months 1 to 11); placebo p-values are not computed for the new '
          'windows.',
          '', '## Limits', '',
          '- Descriptive only; the longer windows were not part of any earlier decision rule. Months 6 to 11 rely on long projections: the own '
          'trend is fitted on months -30 to -7 and carried 18 months forward, and the synthetic control is fitted on months -24 to -3.',
          f'- Rises from about 2025-09 on drop out of the windows that reach month 11. Many lasting rises started in 2020 (S2C {n2020.get("S2C")} '
          f'tests, S2 {n2020.get("S2")}, concept pages {n2020.get("concept")}), and months 2020-04 to 2020-09 are missing: for rises in spring and summer 2020 months 0 to 2 '
          'are missing but months 6 to 11 exist, so the main table compares windows on partly different tests; the same-tests tables do not have this problem.',
          f'- Themes often rise again within a year: {share_iso}. Later months therefore mix the first rise with later ones; the sensitivity '
          'without such rises gives a similar pattern.',
          '- The own-trend method shows positive gaps for the concept pages already in months -3 to -1 (about +0.02 to +0.03), so its numbers '
          'carry some pre-trend; the synthetic control has gaps near 0 before month 0.',
          '- For rises of 1 or 2 weeks the two methods disagree in sign in the later windows (synthetic control about +1%, own trend about -1 '
          'to -2%), so no conclusion is drawn for them.',
          '- The negative twelve-month ranking of S2C (themes whose AI concept pages gained attention lost borrowing share over the next year, '
          'relative to other themes) is not explained here; the placebo shows it is not built into the measure.',
          '', '## Files', '',
          '- data/db/wiki_led/dirs/d1_themes/: ranking_by_k.csv, ranking_same_rows.csv, ranking_pairs_by_k.csv, ranking_placebo.csv, '
          'effects_windows.csv, effects_same_tests.csv, effects_monthly_gaps.csv, effects_positive_control.csv, effects_tests_<series>.parquet, '
          'checks.json, summary.json']
    T.write_text('\n'.join(L) + '\n', REPORT)
    T.log(f'wrote {REPORT}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--part', choices=['ranking', 'effects', 'report'], required=True)
    ap.add_argument('--workers', type=int, default=1, help='1 = serial (about 1.5 ms a test, so serial is enough)')
    ap.add_argument('--series', default='S2C,S2,concept')
    ap.add_argument('--lines', default=None, help='report: text file with the five plain-language opening lines')
    a = ap.parse_args()
    T.be_nice(10)
    if a.part == 'ranking':
        part_ranking()
    elif a.part == 'effects':
        part_effects(max(1, min(a.workers, 3)), [x for x in a.series.split(',') if x in EFFECT_SERIES])
    else:
        if not a.lines:
            raise SystemExit('--lines FILE (the five plain-language opening lines, written after reading the results) is required')
        part_report([x.rstrip() for x in open(a.lines) if x.strip()])


if __name__ == '__main__':
    main()
