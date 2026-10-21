#!/usr/bin/env python3
"""Test F, step 21: the theme attention series S1 (top-500 days) and S2 (full daily views), weekly and monthly. No loans are read.

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (theme_attention_series):
  weights   confidence 3, 2, 1 count 1.0, 0.6, 0.3; narrow themes from the page assignments; a middle theme is the sum of its narrow themes.
  S1        weekly sum over a theme's pages of their user views on the days they were in the daily top 500 (data/raw/wiki_top_daily.json),
            times the weight, divided by all English Wikipedia user views that week (data/db/interest/wiki/weekly_total.parquet, the
            totals of the benchmark). All confidences.
  S2        the same with each page's full daily user views (the store of 22_download_views.py) for the page-theme assignments of
            confidence 2 or 3 of the S2 pages (at most 40,000, the ones with the most top-500 days).
Only universe pages (2 or more top-500 days) count; the one-day coverage sample is never used here.
Weeks are ISO weeks starting Monday; the first (2015-06-29) and last (2026-09-28) weeks are partial, as in the benchmark's totals.
NOT IN ADDENDUM (fixed before any series exists): S1 has no data before 2016-01-01, so its weeks before 2016-01-04 are missing; a week in which
the top-500 list of a day is absent from the raw file (11 days) is a partial week for S1, because its sum would be too low; the S2 page
selection breaks ties at the 40,000 cut by top-500 views, then title; S2 reads the assignments of confidence 2 or 3 (a page-theme pair of
confidence 1 does not count in S2 even when the page has another theme of confidence 2 or 3).
Monthly series: the benchmark's rule (benchmark/07_stage2_features.py, monthly_log): the log of the mean of the weekly shares of the weeks
whose Sunday is in the month, missing if any such week is missing or partial or the mean is 0; month index year * 12 + month - 1, as the
benchmark's covariates (cur_wlog, nli_wlog) are aligned.
Outputs: series_weekly_S1.parquet, series_weekly_S2.parquet (series, level, node_id, week, views, share, top_day_share, n_pages,
total_views, days_covered, partial_week), series_monthly.parquet (mi, node_id, ais1_wlog, ais2_wlog), s2_pages.parquet, series_info.json;
report testF_21_series.md.
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/21_series.py [--series S1,S2] [--allow-incomplete-s2] [--root DIR]
"""
import sys, json, pathlib, argparse, importlib.util
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from scipy import sparse
import _testf_analysis as T

_spec = importlib.util.spec_from_file_location('bm07', T.MAIN / 'benchmark' / '07_stage2_features.py')
BM07 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BM07)                                 # the benchmark's weekly matrix and monthly_log (hash-checked settings)


def node_tables(pairs):
    """pairs: title, code, weight (narrow). Returns the pairs extended to middle themes (a middle theme gets each child pair) and
    pages per node."""
    par = T.parent_map()
    mid = pairs.assign(node_id=pairs.code.map(par))
    nar = pairs.assign(node_id=pairs.code)
    allp = pd.concat([nar, mid], ignore_index=True)
    npages = allp.groupby('node_id').title.nunique()
    return allp, npages


def weekly_from_daily(daily, weeks_ok, npages, series):
    """daily: DataFrame index date, columns node_id (weighted views). weeks_ok: DataFrame week, total_views, days_covered, partial_week.
    -> long weekly table."""
    wk = daily.index - pd.to_timedelta(daily.index.weekday, unit='D')
    g = daily.groupby(wk)
    V, M = g.sum(), g.max()
    V = V.reindex(weeks_ok.week).fillna(0.0)
    M = M.reindex(weeks_ok.week)
    out = V.stack(future_stack=True).rename('views').reset_index()
    out.columns = ['week', 'node_id', 'views']
    out['top_day'] = M.stack(future_stack=True).reindex(pd.MultiIndex.from_frame(out[['week', 'node_id']])).to_numpy()
    out = out.merge(weeks_ok, on='week', how='left')
    out['share'] = out.views / out.total_views
    out['top_day_share'] = np.where(out.views > 0, out.top_day / out.views.where(out.views > 0), np.nan)
    out['n_pages'] = out.node_id.map(npages).fillna(0).astype(int)
    out['level'] = out.node_id.map(T.level_of)
    out['series'] = series
    out['partial_week'] = out.partial_week.astype(bool)          # partial weeks keep their numbers but are not usable (detector and monthly rule)
    return out[['series', 'level', 'node_id', 'week', 'views', 'share', 'top_day_share', 'n_pages', 'total_views', 'days_covered', 'partial_week']]


def build_s1(P, A, TW):
    pairs = A[A.set == 'universe'][['title', 'code', 'weight']]
    allp, npages = node_tables(pairs)
    L, days = T.top_long(titles=set(pairs.title))
    grid = pd.date_range(min(days.min(), T.DAY0), T.DAY1, freq='D')
    titles = sorted(allp.title.unique())
    tpos = pd.Series(np.arange(len(titles)), index=titles)
    nodes = sorted(allp.node_id.unique())
    npos = pd.Series(np.arange(len(nodes)), index=nodes)
    V = sparse.csr_matrix((L.views.to_numpy(dtype=float), (tpos.reindex(L.title).to_numpy(), (L.date - grid[0]).dt.days.to_numpy())),
                          shape=(len(titles), len(grid)))                       # pages x days, views on top-500 days
    Wm = sparse.csr_matrix((allp.weight.to_numpy(), (tpos.reindex(allp.title).to_numpy(), npos.reindex(allp.node_id).to_numpy())),
                           shape=(len(titles), len(nodes)))
    daily = pd.DataFrame((Wm.T @ V).toarray().T, index=grid, columns=nodes)
    have = pd.Series(grid.isin(days), index=grid)
    wk_have = have.groupby(grid - pd.to_timedelta(grid.weekday, unit='D')).agg(['sum', 'size'])
    W = TW.copy()
    full_list = W.week.map(wk_have['sum']).fillna(0).to_numpy() == 7
    W['partial_week'] = W.partial_week.to_numpy() | ~full_list
    missing_days = [d.strftime('%Y-%m-%d') for d in grid[(grid >= days.min()) & ~grid.isin(days)]]
    w = weekly_from_daily(daily, W, npages, 'S1')
    info = dict(pages=int(pairs.title.nunique()), pairs=len(pairs), page_days_used=int(V.nnz),
                top_list_days_missing=missing_days, weeks_partial_for_s1=int(W.partial_week.sum()))
    return w, info


def build_s2(P, A, TW, allow_incomplete):
    sel = T.s2_selection(A, T.top_days_count())
    idx = T.store_index(P)
    st = idx.set_index('title').status
    sel['stored'] = sel.title.isin(st.index)
    sel['status'] = sel.title.map(st)
    T.write_parquet(sel, P / 's2_pages.parquet')
    chosen = sel[sel.selected]
    missing = int((~chosen.stored).sum())
    info = dict(pages_with_conf2plus=len(sel), selected=len(chosen), cap_applied=bool(len(sel) > T.S2_MAX_PAGES),
                min_top_days_selected=int(chosen.top_days.min()) if len(chosen) else None, stored=int(chosen.stored.sum()), not_stored=missing,
                status=chosen.status.value_counts(dropna=False).rename(lambda x: str(x)).to_dict())
    if missing and not allow_incomplete:
        T.log(f'S2 not built: {missing:,} of {len(chosen):,} selected pages are not in the store yet (run 22_download_views.py, or pass '
              '--allow-incomplete-s2 to build it from the stored pages and report the coverage)')
        info['built'] = False
        return None, info
    use = set(chosen[chosen.stored].title)
    pairs = A[(A.set == 'universe') & (A.conf >= T.S2_MIN_CONF) & A.title.isin(use)][['title', 'code', 'weight']]
    allp, npages = node_tables(pairs)
    nodes = sorted(allp.node_id.unique())
    npos = {n: j for j, n in enumerate(nodes)}
    acc = np.zeros((len(nodes), len(T.DAYS)))
    ix = idx[idx.title.isin(use)]
    for f, g in ix.groupby('file'):                         # batch by batch: memory stays at one batch
        with np.load(P.views / f, allow_pickle=False) as z:
            Vb = z['views'][g.row.to_numpy()].astype(np.float64)
        tpos = {t: i for i, t in enumerate(g.title)}
        pb = allp[allp.title.isin(tpos)]
        Wb = sparse.csr_matrix((pb.weight.to_numpy(), (pb.title.map(tpos).to_numpy(), pb.node_id.map(npos).to_numpy())), shape=(len(g), len(nodes)))
        acc += (Wb.T @ Vb)
    daily = pd.DataFrame(acc.T, index=T.DAYS, columns=nodes)
    w = weekly_from_daily(daily, TW, npages, 'S2')
    info.update(built=True, pairs=len(pairs), pages_used=len(use), complete=missing == 0)
    return w, info


def monthly(w, name):
    Msh, _ = BM07.week_matrices(w[['node_id', 'week', 'views', 'share', 'partial_week']])
    M = BM07.monthly_log(Msh)
    s = M.stack(future_stack=True).rename(name)
    s.index.names = ['mi', 'node_id']
    return s


def summary_lines(w):
    full = w[~w.partial_week]
    nz = full.groupby(['level', 'node_id']).views.apply(lambda s: (s > 0).mean())
    vol = full.groupby(['level', 'node_id']).views.median()
    out = []
    for lv, nm in ((3, 'narrow'), (2, 'middle')):
        if lv not in nz.index.get_level_values(0):
            out.append(f'  - {nm}: no theme with pages'); continue
        out.append(f'  - {nm}: {nz.loc[lv].size} themes with pages; share of full weeks with views > 0, median over themes {nz.loc[lv].median():.0%}; '
                   f'themes whose median weekly weighted views reach 1,000 (the minimum of Chapter 6): {int((vol.loc[lv] >= 1000).sum())}')
    return out


def main():
    ap = T.add_root_arg(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    ap.add_argument('--series', default='S1,S2')
    ap.add_argument('--allow-incomplete-s2', action='store_true')
    a = ap.parse_args()
    P = T.Paths(a.root)
    T.be_nice(10)
    A = T.read_assign(P, 'pages')
    TW = T.weekly_totals()[['week', 'total_views', 'days_covered', 'partial_week']]
    want = a.series.split(',')
    info, months = {}, []
    lines = [f'# Test F, step 21: theme attention series ({P.tag()})', '', f'- written {pd.Timestamp.now():%Y-%m-%d %H:%M}; code main_study/wiki_led/testF/21_series.py',
             f'- assignments: {A.id.nunique():,} pages with themes ({(A.set == "universe").groupby(A.id).first().sum():,} in the universe), {len(A):,} page-theme pairs', '']
    if 'S1' in want:
        w1, i1 = build_s1(P, A, TW)
        T.write_parquet(w1, P / 'series_weekly_S1.parquet')
        months.append(monthly(w1, 'ais1_wlog'))
        info['S1'] = i1
        lines += [f'## S1 (views on top-500 days, all confidences)', f'- pages {i1["pages"]:,}, page-theme pairs {i1["pairs"]:,}, page-days used {i1["page_days_used"]:,}',
                  f'- days without a top-500 list in the raw file: {len(i1["top_list_days_missing"])}; weeks partial for S1: {i1["weeks_partial_for_s1"]}'] + summary_lines(w1) + ['']
        T.log(f'S1 built: {w1.node_id.nunique()} themes, {len(w1):,} theme-weeks')
    if 'S2' in want:
        w2, i2 = build_s2(P, A, TW, a.allow_incomplete_s2)
        info['S2'] = i2
        lines += [f'## S2 (full daily views, confidence 2 or 3)', f'- pages with a theme of confidence 2 or 3: {i2["pages_with_conf2plus"]:,}; selected {i2["selected"]:,} '
                  f'(cap of 40,000 applied: {i2["cap_applied"]}; fewest top-500 days among them {i2["min_top_days_selected"]}); in the store {i2["stored"]:,}, '
                  f'not yet {i2["not_stored"]:,}; download statuses {i2["status"]}']
        if w2 is not None:
            T.write_parquet(w2, P / 'series_weekly_S2.parquet')
            months.append(monthly(w2, 'ais2_wlog'))
            lines += [f'- built from {i2["pages_used"]:,} pages ({"complete" if i2["complete"] else "INCOMPLETE: the coverage above applies"})'] + summary_lines(w2) + ['']
            T.log(f'S2 built: {w2.node_id.nunique()} themes, {len(w2):,} theme-weeks')
        else:
            lines += ['- not built (pages missing from the store)', '']
    if months:
        M = pd.concat(months, axis=1).reset_index()
        old = P / 'series_monthly.parquet'
        if old.exists():                                         # keep a series that was not rebuilt this time
            O = pd.read_parquet(old)
            keep = [c for c in O.columns if c not in M.columns]
            if keep:
                M = M.merge(O[['mi', 'node_id'] + keep], on=['mi', 'node_id'], how='outer')
        T.write_parquet(M, P / 'series_monthly.parquet')
        lines += [f'## Monthly series', f'- {len(M):,} theme-months; columns {[c for c in M.columns if c.endswith("_wlog")]}; months {T.ym(M.mi.min())} to {T.ym(M.mi.max())}']
    prev = P / 'series_info.json'
    if prev.exists():
        old = json.loads(prev.read_text())
        old.update(info)
        info = old
    T.write_json(info, prev)
    T.write_text('\n'.join(lines) + '\n', P.report('testF_21_series.md'))
    T.log(f'done; peak memory {T.peak_gb():.2f} GB')


if __name__ == '__main__':
    main()
