"""Study 2R step 5b: feasibility numbers of the addendum. NO ATTENTION DATA ARE USED. Placebo windows (random month 0) for
works on the 2R book list, with the method of parameter_audit/calibrate_2r_noise.py (quasi-Poisson count model for print
and ebook jointly, fitted on the 24 months ending at month -7, tau = log(sum Y / sum mu) over months 0 to +2, seed 20261013).
Works: the matched 2R books with >= 500 print + ebook checkouts in 2016-01..2026-08 (as in that script), up to NWORKS drawn
at random. The number of works a class needs for the upper 95% bound of its mean tau to fall below log(1.10) under a true
effect of zero is (1.96 * SD / log 1.10)^2 (SD of the placebo taus; the robust SD is also given).
Outputs: data/db/study2r/feasibility.json, data/reports/study2r_feasibility_placebo_taus.csv
"""
import numpy as np, pandas as pd, pyarrow.dataset as ds, statsmodels.api as sm, warnings
from common import *
warnings.simplefilter('ignore')
SEED13, NWORKS = 20261013, 3000
T = str(TAXO)
rng = np.random.default_rng(SEED13)
mi = lambda y, m: y * 12 + (m - 1)
MI_LO, MI_HI = mi(2016, 1), mi(2026, 8)

M = pd.read_parquet(OUT / 'book_matches.parquet')
_can = pd.read_parquet(OUT / 'articles.parquet'); M['canonical'] = M.article.map(dict(zip(_can.requested, _can.canonical)))
M = M[M.canonical.isin(set(pd.read_parquet(OUT / 'kept_articles.parquet').article))]   # book set kept at the chosen floor
RW = pd.read_parquet(f'{T}/spl_record_work.parquet')
RW = RW[RW.work_id.isin(M.work_id)]
rid_all = set(RW.record_id.astype(int))
rows = []
for f, fmt in (('book', 'print'), ('ebook', 'ebook')):
    t = ds.dataset(f'{T}/spl_rows_{f}.parquet').to_table(filter=ds.field('record_id').isin(list(rid_all)), columns=['record_id', 'year', 'month', 'checkouts']).to_pandas()
    t['format'] = fmt
    rows.append(t)
Y = pd.concat(rows)
Y['mi'] = Y.year.astype(int) * 12 + Y.month.astype(int) - 1
Y = Y.merge(RW, on='record_id').groupby(['work_id', 'format', 'mi'], as_index=False).checkouts.sum()
tot = Y[(Y.mi >= MI_LO) & (Y.mi <= MI_HI)].groupby('work_id').checkouts.sum()
first = Y[Y.checkouts > 0].groupby('work_id').mi.min()
eligible = tot[tot >= 500].index.to_numpy()
log('2R books:', M.work_id.nunique(), '| with >= 500 print+ebook checkouts in the window:', len(eligible))
pool = rng.permutation(eligible)[: NWORKS * 2]
MS = pd.read_parquet(D / 'db' / 'study3b' / 'month_status.parquet')
MS = MS[MS.format.isin(['print', 'ebook'])].set_index(['format', 'mi'])
okm = MS.month_ok.to_dict(); N = MS.total_checkouts.to_dict()
Yg = {w: g.set_index(['format', 'mi']).checkouts for w, g in Y[Y.work_id.isin(pool)].groupby('work_id')}
res = []
for w in pool:
    if len(res) >= NWORKS:
        break
    lo = max(mi(2019, 1), int(first[w]) + 31); hi = mi(2026, 6)
    if lo > hi:
        continue
    m0 = int(rng.integers(lo, hi + 1))
    g = Yg[w]
    fit_m = list(range(m0 - 30, m0 - 6)); win_m = [m0, m0 + 1, m0 + 2]
    data, entered = [], []
    for fmt in ('print', 'ebook'):
        usable = [m for m in fit_m if okm.get((fmt, m), False)]
        yv = [g.get((fmt, m), 0) for m in usable]
        if len(usable) >= 18 and sum(v > 0 for v in yv) >= 12:
            entered.append(fmt)
            for m, v in zip(usable, yv):
                data.append(dict(fmt=fmt, m=m, y=v, off=np.log(N[(fmt, m)]), fit=1))
            for m in win_m:
                if okm.get((fmt, m), False):
                    data.append(dict(fmt=fmt, m=m, y=g.get((fmt, m), 0), off=np.log(N[(fmt, m)]), fit=0))
    if not entered:
        continue
    d = pd.DataFrame(data)
    d['t'] = (d.m - (m0 - 18.5)) / 12.0; d['moy'] = d.m % 12
    X = pd.DataFrame({f'a_{f}': (d.fmt == f).astype(float) for f in entered})
    for f in entered:
        X[f'b_{f}'] = (d.fmt == f) * d.t
    fit_moy = sorted(d[d.fit == 1].moy.unique())
    for k in fit_moy[1:]:
        X[f'm{k}'] = (d.moy == k).astype(float)
    F = d.fit == 1
    win = d[(d.fit == 0) & d.moy.isin(fit_moy)]
    if len(win) == 0 or win.m.nunique() < 2:
        continue
    try:
        r = sm.GLM(d.y[F], X[F], family=sm.families.Poisson(), offset=d.off[F]).fit()
    except Exception:
        continue
    phi = max(r.pearson_chi2 / r.df_resid, 1e-9) if r.df_resid > 0 else np.nan
    mu = np.exp(X.loc[win.index] @ r.params + win.off)
    sy, sm_ = win.y.sum(), mu.sum()
    tau = (np.log(sy / sm_) if sm_ > 0 and sy > 0 else (np.nan if sy > 0 else -np.inf))
    res.append(dict(work_id=w, m0=m0, formats='+'.join(entered), sum_y=sy, sum_mu=sm_, phi=phi, tau=tau,
                    z=tau / np.sqrt(phi / sm_) if np.isfinite(tau) and phi > 0 else np.nan))
R = pd.DataFrame(res); R.to_csv(REP / 'study2r_feasibility_placebo_taus.csv', index=False)
fin = R[np.isfinite(R.tau)]
sd = float(fin.tau.std()); rsd = float(1.4826 * np.median(np.abs(fin.tau - fin.tau.median())))
B = np.log(1.10)
need = {f'{lab}_true{int(round((np.exp(tr) - 1) * 100))}pct': float((1.96 * s_ / (B - tr)) ** 2)
        for lab, s_ in (('sd', sd), ('robust_sd', rsd)) for tr in (0.0, np.log(1.03), np.log(1.05))}
fin = fin.assign(size_quintile=pd.qcut(fin.sum_mu, 5, labels=False) + 1)
byq = fin.groupby('size_quintile').agg(tests=('tau', 'size'), median_sum_mu=('sum_mu', 'median'), sd_tau=('tau', 'std')).round(3)
byq['works_needed_zero_effect'] = ((1.96 * byq.sd_tau / B) ** 2).round(0)
out = dict(books_on_2r_list=int(M.work_id.nunique()), works_with_500_print_ebook=int(len(eligible)), placebo_tests=int(len(R)), finite_tau=int(len(fin)),
           zero_window_tests=int((R.tau == -np.inf).sum()), mean_tau=float(fin.tau.mean()), median_tau=float(fin.tau.median()), sd_tau=sd, robust_sd_tau=rsd,
           median_phi=float(fin.phi.median()), median_sum_mu=float(fin.sum_mu.median()), share_abs_tau_ge_log110=float((fin.tau.abs() >= B).mean()),
           share_z_gt_1645=float((fin.z > 1.645).mean()), works_needed=need, by_size_quintile=byq.reset_index().to_dict('records'), seed=SEED13)
json.dump(out, open(OUT / 'feasibility.json', 'w'), indent=1)
log(f'placebo tests {len(R)}, finite {len(fin)}; tau mean {fin.tau.mean():.3f} SD {sd:.3f} robust SD {rsd:.3f}; works needed at zero effect: SD {need["sd_true0pct"]:.0f}, robust SD {need["robust_sd_true0pct"]:.0f}')
print(byq.to_string())
log('done', int(time.time() - T0), 's')
