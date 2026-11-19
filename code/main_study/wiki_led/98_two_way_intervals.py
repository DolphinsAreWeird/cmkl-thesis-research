# 98. Intervals that resample books and time together (prereg/DEVIATIONS.md, "Checks asked for by an outside review of the draft
# (19 November 2026)", part A). Descriptive; no model is refitted: the stored predictions are rescored.
#
# New books (Test B, 30_test_b.py and the stronger library models of 90_robustness.py, R5):
#   predictions data/db/wiki_led/test_b_preds.parquet (W_lgbm, L_lgbm, LW_lgbm) and robustness_b_preds.parquet (Lq, L0 = first-month
#   records, Lp = as fixed, each with and without W); n_prior_works from test_b_rows.parquet. Score: Spearman of prediction and Y6 within
#   first-loan year, averaged over years (a year counts when it holds more than 10 drawn rows). Book sets: all, no earlier Seattle work,
#   some earlier work.
# Existing books (main set, l_books_in_time/preds.parquet): change rank of l04_backtest.py, Spearman of prediction and D within each
#   format and origin month (groups of 3 rows or more with more than one predicted value), a ratio of monthly sums; W14, HM, HMW14.
# Intervals (2,000 draws, seed 20261119; every gain paired on the same draws):
#   (i)   books only: author clusters (new books) or works (main set), all years or months kept;
#   (ii)  time only: first-loan years drawn with replacement (new books) or blocks of 3 consecutive months as in l04 (main set);
#   (iii) both at once, drawn independently in each draw.
#   A drawn author or work enters with a weight equal to the number of times it is drawn; ranks within a year or format-month are the
#   weighted mid-ranks, which equal the ranks of the resampled rows (ties averaged) exactly, and the correlation is the weighted Pearson
#   correlation of those ranks.
# Outputs: data/reports/two_way_intervals.json and .md.   Run from code/:  nice ../.venv/bin/python main_study/wiki_led/98_two_way_intervals.py
import sys, json, time, pathlib
import numpy as np, pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D                                         # noqa: E402

D = pathlib.Path(D)
WL, REP = D / 'db' / 'wiki_led', D / 'reports'
SEED, NB = 20261119, 2000
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


class Ranker:
    """Weighted mid-ranks of one variable within groups, for any vector of row weights (presorted once)."""

    def __init__(self, grp, x):
        o = np.lexsort((x, grp))
        gs, xs = grp[o], x[o]
        new = np.r_[True, (gs[1:] != gs[:-1]) | (xs[1:] != xs[:-1])]
        self.o, self.tie = o, np.cumsum(new) - 1                              # tie group of each sorted row
        self.tie_grp = gs[new]                                               # the group of each tie group
        self.n_tie, self.n_grp = int(new.sum()), int(grp.max()) + 1

    def ranks(self, w):
        ws = w[self.o]
        tw = np.bincount(self.tie, ws, self.n_tie)
        before = np.cumsum(tw) - tw                                          # weight before each tie group, over all groups
        gfirst = np.full(self.n_grp, np.inf)
        np.minimum.at(gfirst, self.tie_grp, before)
        r_tie = before - gfirst[self.tie_grp] + (tw + 1) / 2
        r = np.empty(len(w))
        r[self.o] = r_tie[self.tie]
        return r


def wcorr(grp, ng, w, rx, ry):
    """Weighted Pearson correlation of rx and ry within each group."""
    sw = np.bincount(grp, w, ng)
    mx, my = np.bincount(grp, w * rx, ng), np.bincount(grp, w * ry, ng)
    with np.errstate(invalid='ignore', divide='ignore'):
        mx, my = mx / sw, my / sw
        dx, dy = rx - mx[grp], ry - my[grp]
        cxy = np.bincount(grp, w * dx * dy, ng)
        vx, vy = np.bincount(grp, w * dx * dx, ng), np.bincount(grp, w * dy * dy, ng)
        return cxy / np.sqrt(vx * vy), sw


def pct(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


# ---------------------------------------------------------------- new books
B = pd.read_parquet(WL / 'test_b_preds.parquet', columns=['work_id', 'creator_key', 'year', 'Y6', 'W_lgbm', 'L_lgbm', 'LW_lgbm'])
RB = pd.read_parquet(WL / 'robustness_b_preds.parquet', columns=['work_id', 'L_lgbm', 'LW_lgbm', 'Lq_lgbm', 'LqW_lgbm', 'L0_lgbm',
                                                                  'L0W_lgbm', 'Lp_lgbm', 'LpW_lgbm'])
assert len(B) == len(RB) == B.work_id.nunique()
B = B.merge(RB.rename(columns={'L_lgbm': 'L_rb', 'LW_lgbm': 'LW_rb'}), on='work_id', validate='1:1')
TB = pd.read_parquet(WL / 'test_b_rows.parquet', columns=['work_id', 'n_prior_works'])
B = B.merge(TB, on='work_id', how='left', validate='1:1')
assert B.n_prior_works.notna().all()
log('new books', len(B), '| L in robustness file equals Test B:', bool(np.allclose(B.L_lgbm, B.L_rb)), bool(np.allclose(B.LW_lgbm, B.LW_rb)))
MB = ['W_lgbm', 'L_lgbm', 'LW_lgbm', 'Lq_lgbm', 'LqW_lgbm', 'L0_lgbm', 'L0W_lgbm', 'Lp_lgbm', 'LpW_lgbm']
GAINS_B = {'Wikipedia over L (main)': ('LW_lgbm', 'L_lgbm'), 'Wikipedia over Lq (no theme)': ('LqW_lgbm', 'Lq_lgbm'),
           'Wikipedia over L0 (first-month records)': ('L0W_lgbm', 'L0_lgbm'), 'Wikipedia over Lp (as fixed)': ('LpW_lgbm', 'Lp_lgbm')}


def new_books(df, label, rng):
    years = np.sort(df.year.unique()); ny = len(years)
    yi = np.searchsorted(years, df.year.values)
    clu, cl_of = np.unique(df.creator_key.values, return_inverse=True); nc = len(clu)
    y = df.Y6.values.astype(float)
    ry = Ranker(yi, y)
    rk = {m: Ranker(yi, df[m].values.astype(float)) for m in MB}
    full = np.ones(len(df))
    base_ry = ry.ranks(full)
    rho0 = {m: wcorr(yi, ny, full, rk[m].ranks(full), base_ry)[0] for m in MB}            # per year, full sample
    for m in MB:                                                                          # check against scipy
        g = df[df.year == years[0]]
        assert abs(rho0[m][0] - spearmanr(g[m], g.Y6).statistic) < 1e-9
    point = {m: float(np.mean(rho0[m])) for m in MB}
    draws = {k: {m: [] for m in MB} for k in ('i', 'ii', 'iii')}
    for b in range(NB):
        cw = np.bincount(rng.integers(0, nc, nc), minlength=nc).astype(float)
        yc = np.bincount(rng.integers(0, ny, ny), minlength=ny).astype(float)
        w = cw[cl_of]
        r_y = ry.ranks(w)
        for m in MB:
            rho, sw = wcorr(yi, ny, w, rk[m].ranks(w), r_y)
            ok = (sw > 10) & np.isfinite(rho)
            draws['i'][m].append(rho[ok].mean())
            draws['ii'][m].append((rho0[m] * yc).sum() / yc.sum())
            draws['iii'][m].append((rho[ok] * yc[ok]).sum() / yc[ok].sum())
        if b % 500 == 0:
            log('  new books', label, b)
    out = dict(rows=len(df), authors=nc, years=[int(v) for v in years], scores={}, gains={})
    for m in MB:
        out['scores'][m] = dict(est=point[m], **{k: pct(draws[k][m]) for k in ('i', 'ii', 'iii')})
    for name, (a, c) in GAINS_B.items():
        out['gains'][name] = dict(est=point[a] - point[c],
                                  **{k: pct(np.array(draws[k][a]) - np.array(draws[k][c])) for k in ('i', 'ii', 'iii')})
    return out


res = {'new_books': {}}
rng = np.random.default_rng(SEED)
for label, sel in (('all', B.n_prior_works >= 0), ('no earlier Seattle work', B.n_prior_works == 0), ('some earlier work', B.n_prior_works > 0)):
    res['new_books'][label] = new_books(B[sel].reset_index(drop=True), label, rng)
    g = res['new_books'][label]['gains']['Wikipedia over L (main)']
    log('new books', label, 'gain', round(g['est'], 4), 'i', np.round(g['i'], 4), 'ii', np.round(g['ii'], 4), 'iii', np.round(g['iii'], 4))

# ---------------------------------------------------------------- existing books, main set
P = pd.read_parquet(WL / 'l_books_in_time' / 'preds.parquet', columns=['work_id', 'format', 'mi', 'D', 'W14', 'HM', 'HMW14'])
MONTHS = np.sort(P.mi.unique()); n = len(MONTHS)
P['m'] = np.searchsorted(MONTHS, P.mi.values)
P['g'] = P.groupby(['format', 'mi'], sort=True).ngroup()
MM = ['W14', 'HM', 'HMW14']
size = P.groupby('g').size(); nun = {m: P.groupby('g')[m].nunique() for m in MM}
g_m = P.groupby('g').m.first().sort_index().values
ng = len(g_m)
works, wk_of = np.unique(P.work_id.values, return_inverse=True); nw = len(works)
gi = P.g.values
rdv = Ranker(gi, P.D.values.astype(float))
rkm = {m: Ranker(gi, P[m].values.astype(float)) for m in MM}
keep = {m: ((size >= 3) & (nun[m] > 1)).sort_index().values for m in MM}
full = np.ones(len(P))
r0 = rdv.ranks(full)
rho0 = {m: wcorr(gi, ng, full, rkm[m].ranks(full), r0)[0] for m in MM}


def monthly(rho, okg):
    """(num, den) per month from per-group correlations, as l04's monthly(..., 'rank')."""
    ok = okg & np.isfinite(rho)
    return np.bincount(g_m[ok], rho[ok], n), np.bincount(g_m[ok], minlength=n).astype(float)


base = {m: monthly(rho0[m], keep[m]) for m in MM}
point = {m: float(base[m][0].sum() / base[m][1].sum()) for m in MM}
# check one group against scipy
g0 = P[P.g == 0]
assert abs(rho0['HM'][0] - spearmanr(g0.HM, g0.D).statistic) < 1e-9
log('main set rows', len(P), 'works', nw, 'months', n, '| point', {m: round(point[m], 4) for m in MM})
kb = int(np.ceil(n / 3))
draws = {k: {m: [] for m in MM} for k in ('i', 'ii', 'iii')}
for b in range(NB):
    cw = np.bincount(rng.integers(0, nw, nw), minlength=nw).astype(float)
    blocks = np.concatenate([np.arange(a, a + 3) % n for a in rng.integers(0, n, kb)])[:n]
    mc = np.bincount(blocks, minlength=n).astype(float)
    w = cw[wk_of]
    r_d = rdv.ranks(w)
    for m in MM:
        rho, sw = wcorr(gi, ng, w, rkm[m].ranks(w), r_d)
        num, den = monthly(rho, keep[m] & (sw >= 3))
        draws['i'][m].append(num.sum() / den.sum())
        draws['ii'][m].append((base[m][0] * mc).sum() / (base[m][1] * mc).sum())
        draws['iii'][m].append((num * mc).sum() / (den * mc).sum())
    if b % 250 == 0:
        log('  main set', b)
out = dict(rows=len(P), works=nw, months=n, scores={}, gains={})
for m in MM:
    out['scores'][m] = dict(est=point[m], **{k: pct(draws[k][m]) for k in ('i', 'ii', 'iii')})
for name, (a, c) in {'Wikipedia over HM (main)': ('HMW14', 'HM')}.items():
    out['gains'][name] = dict(est=point[a] - point[c], **{k: pct(np.array(draws[k][a]) - np.array(draws[k][c])) for k in ('i', 'ii', 'iii')})
res['main_set'] = out
g = out['gains']['Wikipedia over HM (main)']
log('main set gain', round(g['est'], 4), 'i', np.round(g['i'], 4), 'ii', np.round(g['ii'], 4), 'iii', np.round(g['iii'], 4))

# ---------------------------------------------------------------- outputs
res['rule'] = 'a gain holds when books and time are resampled together only if interval (iii) lies above zero (DEVIATIONS, 19 Nov 2026, A4)'
res['runtime_s'] = round(time.time() - T0)
(REP / 'two_way_intervals.json').write_text(json.dumps(res, indent=1))
f = lambda t: f'{t[0]:.4f} to {t[1]:.4f}'
L = ['# Intervals that resample books and time together', '',
     'Record: prereg/DEVIATIONS.md, 19 November 2026, part A. Stored predictions rescored; 2,000 draws, seed 20261119. '
     '(i) books only (author clusters for new books, works for the main set); (ii) time only (first-loan years; blocks of 3 months); '
     '(iii) both at once. 95% percentile intervals.', '',
     '| Books | Score | Estimate | (i) books | (ii) time | (iii) both | (iii) above zero |', '| --- | --- | --- | --- | --- | --- | --- |']
for label, r in res['new_books'].items():
    for name, v in list(r['gains'].items()) + [(k, v) for k, v in r['scores'].items() if k in ('W_lgbm', 'L_lgbm', 'LW_lgbm')]:
        L.append(f"| New books, {label} ({r['rows']:,}) | {name} | {v['est']:.4f} | {f(v['i'])} | {f(v['ii'])} | {f(v['iii'])} | "
                 f"{'yes' if v['iii'][0] > 0 else 'no'} |")
for name, v in list(out['gains'].items()) + list(out['scores'].items()):
    L.append(f"| Main set ({out['rows']:,} rows, {out['works']:,} works) | {name} | {v['est']:.4f} | {f(v['i'])} | {f(v['ii'])} | {f(v['iii'])} | "
             f"{'yes' if v['iii'][0] > 0 else 'no'} |")
(REP / 'two_way_intervals.md').write_text('\n'.join(L) + '\n')
print('\n'.join(L))
