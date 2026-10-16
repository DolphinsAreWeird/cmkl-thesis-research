# Method benchmark, stage 2: interest series and features that need no demand data.
#   cur  : the curated Wikipedia series (record), only used for its duration-weighted interest and monthly covariates here
#   top  : the embedding routing of the daily top-500 pages (addendum a), weekly_node.parquet from 05_top_routing.py
#   nli  : the context-reading routing (08_nli_routing.py), same layout, optional until that script has run
#   bkb, bka : book-anchored routing through the Wikipedia articles of the Seattle works (book articles) and of their authors
# Outputs (data/db/benchmark/stage2/): bk_weekly_book.parquet, bk_weekly_author.parquet, dwi_weekly.parquet, monthly_cov.parquet,
# features_stage2.parquet (the Study 4b feature table for Seattle, horizons 1 to 3, plus the new columns), and the coverage report
# data/reports/benchmark_stage2_routing_coverage.md (counts only, no demand data).
# Settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json (interest_series_definitions, 2b, 2c, 2d).
#   ../../../.venv/bin/python 07_stage2_features.py [--sources cur,top,bk,nli] [--selftest]
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '3')
import sys, time, pathlib, argparse
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import _stage2_common as C
import _features as FT
import _settings as ST

S = ST.settings()
DB = ST.DB
VOL = ['logmean4', 'ratio', 'dlog4', 'mk8']
WIKI = DB / 'interest' / 'wiki'
# addendum 2d: constants taken from the record (shift_definitions, minimum_volume)
DWI_RATIO, DWI_MIN_VIEWS, DWI_NORMAL_WEEKS, DWI_WINDOW, DWI_CAP = 1.5, 1000.0, S.normal_weeks, 8, 4


# ---------------- weekly tables (node_id, week, views, share, partial_week) ----------------
def level_of(node_id):
    return node_id.count('.') + 1


def load_weekly(source):
    if source == 'cur':
        w = pd.read_parquet(WIKI / 'weekly_node.parquet')
        w = w[w.source == 'wikipedia']
    elif source == 'top':
        w = pd.read_parquet(C.OUT.parent / 'top_routing' / 'weekly_node.parquet')
    elif source == 'nli':
        w = pd.read_parquet(C.OUT / 'nli_routing' / 'weekly_node.parquet')
    elif source in ('bkb', 'bka'):
        w = pd.read_parquet(C.OUT / ('bk_weekly_book.parquet' if source == 'bkb' else 'bk_weekly_author.parquet'))
    else:
        raise ValueError(source)
    return w[['node_id', 'week', 'views', 'share', 'partial_week']].copy()


def build_bk(kind):
    """Book-anchored weekly series (addendum 2b). kind 'book' or 'author'. Returns node_id, week, views, share, partial_week and
    the article x node weight table (for the coverage report)."""
    works = pd.read_parquet(DB / 'study2r' / 'works.parquet', columns=['work_id', 'article', 'author_article'])
    key = 'article' if kind == 'book' else 'author_article'
    wt = pd.read_parquet(DB / 'taxonomy_v3' / 'work_theme.parquet', columns=['work_id', 'node_id', 'level', 'strength'])
    wt = wt[wt.level.isin([2, 3]) & (wt.strength > 0) & wt.work_id.isin(works.work_id)]
    m = works[['work_id', key]].dropna()
    nw = m.groupby(key).work_id.nunique()
    x = wt.merge(m, on='work_id')
    Wt = x.groupby([key, 'node_id']).strength.sum().rename('s').reset_index()
    Wt['w'] = Wt.s / Wt[key].map(nw)                                   # mean strength over the article's works (0 for works outside the node)
    wk = pd.read_parquet(DB / 'study2r' / ('weekly_book.parquet' if kind == 'book' else 'weekly_author.parquet'), columns=['article', 'week', 'views'])
    wk = wk[wk.article.isin(set(Wt[key]))]
    tot = pd.read_parquet(WIKI / 'weekly_total.parquet').sort_values('week').reset_index(drop=True)
    V = wk.pivot_table(index='week', columns='article', values='views', aggfunc='sum').reindex(tot.week).fillna(0.0)
    arts = list(V.columns)
    nodes = sorted(Wt.node_id.unique())
    ai = {a: i for i, a in enumerate(arts)}; ni = {n: i for i, n in enumerate(nodes)}
    Wm = np.zeros((len(arts), len(nodes)))
    for a, n, w in zip(Wt[key], Wt.node_id, Wt.w):
        if a in ai:
            Wm[ai[a], ni[n]] = w
    R = V.to_numpy() @ Wm                                              # weeks x nodes: routed views
    out = pd.DataFrame(R, index=tot.week, columns=nodes).stack().rename('views').reset_index()
    out.columns = ['week', 'node_id', 'views']
    out['total_views'] = out.week.map(tot.set_index('week').total_views)
    out['share'] = out.views / out.total_views
    out['partial_week'] = out.week.map(tot.set_index('week').partial_week).astype(bool)
    return out[['node_id', 'week', 'views', 'share', 'partial_week']], Wt.rename(columns={key: 'article'}), len(arts)


# ---------------- duration-weighted interest (addendum 2d) ----------------
def dwi_matrix(Msh, Mvw):
    """Weeks x nodes. ratio = share / median of the previous 26 weeks; excess = ln ratio when ratio >= 1.5 and the normal level is at
    least 1,000 views a week, else 0; run = consecutive weeks with excess > 0; DWI = sum over the last 8 weeks of excess x min(run, 4) / 4.
    Missing if any of the 8 weeks is missing or partial. Causal: only weeks up to the current one are used."""
    normal = Msh.shift(1).rolling(DWI_NORMAL_WEEKS, min_periods=DWI_NORMAL_WEEKS).median()
    nviews = Mvw.shift(1).rolling(DWI_NORMAL_WEEKS, min_periods=DWI_NORMAL_WEEKS).median()
    ratio = Msh / normal.where(normal > 0)
    ok = ratio.notna() & nviews.notna()
    up = (ratio >= DWI_RATIO) & (nviews >= DWI_MIN_VIEWS)
    with np.errstate(divide='ignore', invalid='ignore'):
        excess = np.log(ratio).where(up, 0.0).where(ok)
    E = excess.to_numpy(float)
    run = np.full(E.shape, np.nan)
    prev = np.zeros(E.shape[1])
    for k in range(E.shape[0]):
        e = E[k]
        cur = np.where(np.isnan(e), np.nan, np.where(e > 0, prev + 1.0, 0.0))
        run[k] = cur
        prev = np.where(np.isnan(cur), 0.0, cur)
    wgt = np.minimum(run, DWI_CAP) / DWI_CAP
    term = pd.DataFrame(E * wgt, index=Msh.index, columns=Msh.columns)
    return term.rolling(DWI_WINDOW, min_periods=DWI_WINDOW).sum()


def week_matrices(w):
    valid = ~w.partial_week.astype(bool)
    return FT.weekly_matrix(w, 'share', valid), FT.weekly_matrix(w, 'views', valid)


def at_origins(Mat, origins):
    """Value of a weeks x nodes matrix at the last included week of each origin month -> long (origin_mi, node_id, value)."""
    mis = sorted(int(m) for m in origins)
    idx = pd.DatetimeIndex([FT.last_week_monday(m) for m in mis])
    sub = Mat.reindex(index=idx)
    sub.index = mis
    s = sub.stack(future_stack=True)
    s.index.names = ['origin_mi', 'node_id']
    return s


def monthly_log(Msh):
    """Monthly log share: ln of the mean of the weekly shares of the weeks whose Sunday is in the month; missing if any such week is
    missing or partial, or the mean is 0. Index month index, columns nodes."""
    mi = np.array([FT.week_month(w) for w in Msh.index])
    g = Msh.groupby(mi)
    mean, cnt, tot = g.mean(), g.count(), g.size()
    ok = cnt.eq(tot, axis=0)
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.log(mean.where(ok & (mean > 0)))


def monthly_at_last_week(Mat):
    mi = sorted({FT.week_month(w) for w in Mat.index})
    idx = pd.DatetimeIndex([FT.last_week_monday(m) for m in mi])
    sub = Mat.reindex(index=idx)
    sub.index = mi
    return sub


def vol_features(w, origins, prefix):
    X = FT.interest_frame(w[['node_id', 'week', 'share', 'partial_week']], None, None, 'wikipedia', origins, S)
    return X[['node_id', 'origin_mi'] + VOL].rename(columns={c: f'{prefix}_{c}' for c in VOL})


# ---------------- self test: no feature at origin t changes when later weeks are altered ----------------
def selftest(weeklies, origins_test=('2020-06', '2023-03')):
    rng = np.random.default_rng(20261013)
    for name, w in weeklies.items():
        for ym in origins_test:
            t = ST.mi_from_ym(ym)
            L = FT.last_week_monday(t)
            w2 = w.copy()
            late = pd.to_datetime(w2.week) > L
            noise = rng.uniform(0.2, 5.0, size=int(late.sum()))
            w2.loc[late, 'share'] = w2.loc[late, 'share'].to_numpy() * noise
            w2.loc[late, 'views'] = w2.loc[late, 'views'].to_numpy() * noise
            a = vol_features(w, [t], 'x').set_index('node_id').sort_index()
            b = vol_features(w2, [t], 'x').set_index('node_id').sort_index()
            assert a.shape == b.shape and np.allclose(a.to_numpy(float), b.to_numpy(float), equal_nan=True), f'{name} {ym}: volume features use later weeks'
            Sa, Va = week_matrices(w); Sb, Vb = week_matrices(w2)
            da, db = at_origins(dwi_matrix(Sa, Va), [t]), at_origins(dwi_matrix(Sb, Vb), [t])
            assert np.allclose(da.to_numpy(float), db.to_numpy(float), equal_nan=True), f'{name} {ym}: DWI uses later weeks'
            ma = monthly_log(Sa).loc[t]; mb = monthly_log(Sb).loc[t]
            assert np.allclose(ma.to_numpy(float), mb.to_numpy(float), equal_nan=True), f'{name} {ym}: monthly log share uses later weeks'
        print(f'  self test passed for {name}', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sources', default='cur,top,bk,nli')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    C.check_addendum()
    C.OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    want = a.sources.split(',')
    weeklies, cover = {}, []
    if 'bk' in want:
        for kind, nm in (('book', 'bkb'), ('author', 'bka')):
            w, Wt, narts = build_bk(kind)
            w.to_parquet(C.OUT / f'bk_weekly_{kind}.parquet', index=False)
            weeklies[nm] = w
            cover.append(f'- {nm}: {narts:,} {kind} articles with weekly views, routed to {w.node_id.nunique()} nodes '
                         f'(middle {sum(level_of(n) == 2 for n in w.node_id.unique())}, narrow {sum(level_of(n) == 3 for n in w.node_id.unique())}); '
                         f'article-node pairs {len(Wt):,}; weeks {w.week.nunique()}; share of full weeks with routed views > 0, median over nodes '
                         f'{w[~w.partial_week].groupby("node_id").views.apply(lambda s: (s > 0).mean()).median():.0%}')
            print(f'{time.strftime("%H:%M:%S")} built {nm} ({(time.time() - t0) / 60:.1f} min)', flush=True)
    for s in ('cur', 'top', 'nli'):
        if s in want:
            try:
                weeklies[s] = load_weekly(s)
            except FileNotFoundError:
                print(f'{s}: weekly table not found, skipped', flush=True)
    if a.selftest:
        selftest(weeklies)
        return
    F = pd.read_parquet(DB / 'study4b' / 'features.parquet')
    origins = list(range(int(F.origin_mi.min()), int(F.origin_mi.max()) + 1))
    cov_parts, feat_cols = [], []
    for name, w in weeklies.items():
        if name == 'cur':
            Msh, Mvw = week_matrices(w)
            D = dwi_matrix(Msh, Mvw)
            long = D.stack(future_stack=True).rename('dwi').reset_index(); long.columns = ['week', 'node_id', 'dwi']
            long.to_parquet(C.OUT / 'dwi_weekly.parquet', index=False)
            dwi_o = at_origins(D, origins).rename('dwi').reset_index()
            F = F.merge(dwi_o, on=['node_id', 'origin_mi'], how='left')
            feat_cols.append('dwi')
            cov_parts.append(monthly_at_last_week(D).stack(future_stack=True).rename('cur_dwi'))
            cov_parts.append(monthly_log(Msh).stack(future_stack=True).rename('cur_wlog'))
            cover.append(f'- cur DWI: nodes {D.shape[1]}, share of node-weeks with a value {D.notna().mean().mean():.0%}, share of defined node-weeks with DWI > 0 '
                         f'{(D.to_numpy()[np.isfinite(D.to_numpy())] > 0).mean():.1%}')
        else:
            pre = name
            X = vol_features(w, origins, pre)
            F = F.merge(X, on=['node_id', 'origin_mi'], how='left')
            feat_cols += [f'{pre}_{c}' for c in VOL]
            Msh, _ = week_matrices(w)
            cov_parts.append(monthly_log(Msh).stack(future_stack=True).rename(f'{pre}_wlog'))
            cover.append(f'- {name}: nodes with a series {w.node_id.nunique()}; rows of F with a ratio feature {F[f"{pre}_ratio"].notna().mean():.0%}')
        print(f'{time.strftime("%H:%M:%S")} features for {name} ({(time.time() - t0) / 60:.1f} min)', flush=True)
    M = pd.concat(cov_parts, axis=1)
    M.index.names = ['mi', 'node_id']
    M = M.reset_index()
    old = C.OUT / 'monthly_cov.parquet'
    if old.exists():
        O = pd.read_parquet(old)
        keep = [c for c in O.columns if c not in M.columns and c not in ('mi', 'node_id')]
        if keep:
            M = M.merge(O[['mi', 'node_id'] + keep], on=['mi', 'node_id'], how='outer')
    M.to_parquet(old, index=False)
    prev = C.OUT / 'features_stage2.parquet'
    if prev.exists():
        P = pd.read_parquet(prev)
        extra = [c for c in P.columns if c not in F.columns]
        if extra:
            F = F.merge(P[['group', 'format', 'level', 'node_id', 'origin_mi', 'h'] + extra], on=['group', 'format', 'level', 'node_id', 'origin_mi', 'h'], how='left')
    F.to_parquet(prev, index=False)
    rep = ['# Stage-2 interest series and features: coverage (counts only, no demand data)', '',
           f'Written {time.strftime("%Y-%m-%d %H:%M")}. Settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json. Code: code/main_study/benchmark/07_stage2_features.py.', ''] + cover
    pathlib.Path(ST.DATA / 'reports' / 'benchmark_stage2_routing_coverage.md').write_text('\n'.join(rep) + '\n')
    print(f'{time.strftime("%H:%M:%S")} wrote {prev} ({len(F):,} rows, new columns {feat_cols}) and {old}; {(time.time() - t0) / 60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
