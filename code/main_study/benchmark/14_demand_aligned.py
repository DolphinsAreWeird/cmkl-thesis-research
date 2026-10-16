# Method benchmark, stage 2f: routing learned from past demand (walk-forward, with shrinkage), addendum b, stage2_pipelines.2f.f2_demand_aligned_routing.
# For each origin t, Seattle series (format x node) and horizon h: the pool of the node is the book and author articles routed to it in 2b (weight > 0);
# every article gets a weight from how well its monthly change in log views anticipated the series' change y(m+h) - y(m) over the months m with
# m + h <= t (from 2016-08), positive part of the Pearson correlation, shrunk towards equal weights with lambda = n / (n + 36); the feature is the
# four volume features of the weights x the articles' weekly shares, as of the origin. Weights use only months up to t, views only weeks up to the
# origin's last included week. Output: data/db/benchmark/stage2/features_dem_h<h>.parquet (keys + dem_logmean4, dem_ratio, dem_dlog4, dem_mk8).
#   ../../../.venv/bin/python 14_demand_aligned.py --horizons 1 [--selftest]       (run under jobs/heavy_lock.sh)
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '2')
import sys, time, pathlib, argparse
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import _stage2_common as C
import _features as FT
import _settings as ST

S = ST.settings()
DB = ST.DB
WIKI = DB / 'interest' / 'wiki'
KAPPA, MIN_PAIRS, START_MI = 36.0, 12, ST.mi_from_ym('2016-08')
VOL = ['logmean4', 'ratio', 'dlog4', 'mk8']


def load_pool():
    """Article x node weights (book and author articles), weekly views and shares (weeks x articles), monthly log views (months x articles)."""
    works = pd.read_parquet(DB / 'study2r' / 'works.parquet', columns=['work_id', 'article', 'author_article'])
    wt = pd.read_parquet(DB / 'taxonomy_v3' / 'work_theme.parquet', columns=['work_id', 'node_id', 'level', 'strength'])
    wt = wt[wt.level.isin([2, 3]) & (wt.strength > 0) & wt.work_id.isin(works.work_id)]
    tot = pd.read_parquet(WIKI / 'weekly_total.parquet').sort_values('week').reset_index(drop=True)
    cols, pools = {}, {}
    V = []
    for kind, key, fn in (('b', 'article', 'weekly_book.parquet'), ('a', 'author_article', 'weekly_author.parquet')):
        m = works[['work_id', key]].dropna()
        nw = m.groupby(key).work_id.nunique()
        x = wt.merge(m, on='work_id')
        Wt = x.groupby([key, 'node_id']).strength.sum().rename('s').reset_index()
        Wt['w'] = Wt.s / Wt[key].map(nw)
        wk = pd.read_parquet(DB / 'study2r' / fn, columns=['article', 'week', 'views'])
        wk = wk[wk.article.isin(set(Wt[key]))]
        P = wk.pivot_table(index='week', columns='article', values='views', aggfunc='sum').reindex(tot.week).fillna(0.0)
        P.columns = [f'{kind}:{a}' for a in P.columns]
        V.append(P)
        Wt['col'] = kind + ':' + Wt[key]
        for n, g in Wt.groupby('node_id'):
            pools.setdefault(n, []).extend(g.col.tolist())
    Vw = pd.concat(V, axis=1)
    cidx = {c: i for i, c in enumerate(Vw.columns)}
    pools = {n: np.array(sorted({cidx[c] for c in cs if c in cidx})) for n, cs in pools.items()}
    totv = tot.set_index('week').total_views.to_numpy()
    partial = tot.set_index('week').partial_week.to_numpy(bool)
    views = Vw.to_numpy(float)
    share = views / totv[:, None]
    share[partial] = np.nan
    views_v = views.copy(); views_v[partial] = np.nan
    weeks = pd.DatetimeIndex(tot.week.to_numpy())
    # monthly mean weekly views of the weeks whose Sunday is in the month, full weeks only, then log
    mo = np.array([FT.week_month(w) for w in weeks])
    ms = np.arange(mo.min(), mo.max() + 1)
    LX = np.full((len(ms), views.shape[1]), np.nan)
    for i, m in enumerate(ms):
        sel = mo == m
        v = views_v[sel]
        ok = ~np.isnan(v).any(axis=0) & (v.mean(axis=0) > 0)
        LX[i, ok] = np.log(v[:, ok].mean(axis=0))
    DX = np.full_like(LX, np.nan)
    DX[1:] = LX[1:] - LX[:-1]
    return dict(pools=pools, share=share, weeks=weeks, months=ms, DX=DX, ncols=views.shape[1])


def vol_features_last(Sx):
    """The four Study 4 volume features at the last column of the weekly series in the rows of Sx (series x weeks, at least 27 weeks);
    complete windows only (NaN propagates), as in _features.weekly_feature_matrices."""
    with np.errstate(divide='ignore', invalid='ignore'):
        m4, m4p = Sx[:, -4:].mean(axis=1), Sx[:, -8:-4].mean(axis=1)
        lm4 = np.where(m4 > 0, np.log(m4), np.nan); lm4p = np.where(m4p > 0, np.log(m4p), np.nan)
        normal = np.median(Sx[:, -27:-1], axis=1)
        ratio = Sx[:, -1] / np.where(normal > 0, normal, np.nan)
        W8 = Sx[:, -8:]
        s = np.zeros(len(Sx))
        for i in range(8):
            for j in range(i + 1, 8):
                s = s + np.sign(W8[:, j] - W8[:, i])
        return np.column_stack([lm4, ratio, lm4 - lm4p, s / 28.0])


def corr_weights(X, dy):
    """X: articles x months (monthly change in log views, NaN where undefined); dy: months (change of the series, NaN where undefined).
    Pairwise-complete Pearson correlation per article (at least MIN_PAIRS pairs), positive part."""
    V = ~np.isnan(X) & ~np.isnan(dy)[None, :]
    n = V.sum(axis=1).astype(float)
    Xz = np.where(V, X, 0.0); Yz = np.where(V, dy[None, :], 0.0)
    sx, sy = Xz.sum(axis=1), Yz.sum(axis=1)
    sxx, syy, sxy = (Xz ** 2).sum(axis=1), (Yz ** 2).sum(axis=1), (Xz * Yz).sum(axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        r = (n * sxy - sx * sy) / np.sqrt((n * sxx - sx ** 2) * (n * syy - sy ** 2))
    r = np.where((n >= MIN_PAIRS) & np.isfinite(r), r, 0.0)
    return np.maximum(r, 0.0)


def features_for(pool, hist, h, origins, series_keys, only_series=None):
    """Rows: one per (series, origin) with the four dem_ features. series_keys: list of (group, format, level, node_id)."""
    share, weeks, months, DX = pool['share'], pool['weeks'], pool['months'], pool['DX']
    month_pos = {int(m): i for i, m in enumerate(months)}
    rows = []
    for t in origins:
        Lw = FT.last_week_monday(t)
        wi = int(np.searchsorted(weeks.to_numpy(), np.datetime64(Lw), side='right')) - 1
        if wi < 40 or weeks[wi] != Lw:
            continue
        for key in series_keys:
            g, f, lev, n = key
            P = pool['pools'].get(n)
            y = hist.get(key)
            if P is None or len(P) == 0 or y is None:
                continue
            ms = np.arange(START_MI, t - h + 1)
            ypos = y.reindex(np.concatenate([ms, ms + h])).to_numpy(float)
            dy = ypos[len(ms):] - ypos[:len(ms)]
            idx = np.array([month_pos.get(int(m), -1) for m in ms])
            ok = idx >= 0
            X = np.full((len(P), len(ms)), np.nan)
            X[:, ok] = DX[idx[ok]][:, P].T
            rho = corr_weights(X, dy)
            nm = int(np.isfinite(dy).sum())
            lam = nm / (nm + KAPPA)
            wts = (np.full(len(P), 1.0 / len(P)) if rho.sum() <= 0 else lam * rho / rho.sum() + (1 - lam) / len(P))
            if rho.sum() <= 0:
                wts = np.full(len(P), 1.0 / len(P))
            ser = share[wi - 39:wi + 1][:, P] @ wts                    # weighted sum of the articles' weekly shares, last 40 weeks
            rows.append((g, f, lev, n, int(t), h, ser, nm, lam))
    if not rows:
        return pd.DataFrame()
    Sx = np.vstack([r[6] for r in rows])
    Fv = vol_features_last(Sx)
    out = pd.DataFrame([r[:6] for r in rows], columns=['group', 'format', 'level', 'node_id', 'origin_mi', 'h'])
    for j, c in enumerate(VOL):
        out['dem_' + c] = Fv[:, j]
    out['dem_months'] = [r[7] for r in rows]; out['dem_lambda'] = [r[8] for r in rows]
    return out


def selftest(pool, hist, keys):
    """Time safety and the numpy features against the Study 4 functions."""
    rng = np.random.default_rng(1)
    A = np.abs(rng.normal(size=(60, 3))) + 0.1
    M = pd.DataFrame(A, index=pd.date_range('2020-01-06', periods=60, freq='7D'))
    F = FT.weekly_feature_matrices(M, S)
    Sx = A.T
    mine = vol_features_last(Sx)
    ref = np.column_stack([F['logmean4'].iloc[-1], F['ratio'].iloc[-1], F['dlog4'].iloc[-1], F['mk8'].iloc[-1]])
    assert np.allclose(mine, ref, equal_nan=True), (mine, ref)
    print('  numpy volume features equal the Study 4 functions', flush=True)
    t = ST.mi_from_ym('2022-05')
    sub = [k for k in keys if k[1] == 'print'][:40]
    a = features_for(pool, hist, 1, [t], sub)
    L = FT.last_week_monday(t)
    p2 = dict(pool); p2['share'] = pool['share'].copy()
    late = pool['weeks'] > L
    p2['share'][late] = p2['share'][late] * rng.uniform(0.2, 5, size=(int(late.sum()), 1))
    p2['DX'] = pool['DX'].copy(); late_m = pool['months'] > t
    p2['DX'][late_m] = rng.normal(size=p2['DX'][late_m].shape)
    h2 = {k: v.copy() for k, v in hist.items()}
    for k in h2:
        h2[k].loc[h2[k].index > t] = rng.normal(size=int((h2[k].index > t).sum()))
    b = features_for(p2, h2, 1, [t], sub)
    cols = ['dem_' + c for c in VOL]
    assert len(a) == len(b) and np.allclose(a[cols].to_numpy(float), b[cols].to_numpy(float), equal_nan=True), 'features at t changed when later data were altered'
    print(f'  time-safety test passed on {len(a)} series at 2022-05', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--horizons', default='1')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    C.check_addendum()
    t0 = time.time()
    pool = load_pool()
    hist = C.history()
    keys = sorted(k for k in hist if k[0] == 'seattle' and k[3] in pool['pools'])
    print(f'{time.strftime("%H:%M:%S")} pool: {len(pool["pools"])} nodes, {pool["ncols"]} articles; {len(keys)} Seattle series', flush=True)
    if a.selftest:
        selftest(pool, hist, keys)
        return
    F = pd.read_parquet(C.ST.DB / 'study4b' / 'features.parquet', columns=['h', 'origin_mi'])
    for h in [int(x) for x in a.horizons.split(',')]:
        origins = [m for m in range(START_MI + 12, int(F.origin_mi.max()) + 1)]
        out = features_for(pool, hist, h, origins, keys)
        out.to_parquet(C.OUT / f'features_dem_h{h}.parquet', index=False)
        print(f'{time.strftime("%H:%M:%S")} h={h}: {len(out):,} rows, share with a ratio {out.dem_ratio.notna().mean():.0%}, mean lambda {out.dem_lambda.mean():.2f}; {(time.time() - t0) / 60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
