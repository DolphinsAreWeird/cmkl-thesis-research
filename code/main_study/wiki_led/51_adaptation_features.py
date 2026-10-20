#!/usr/bin/env python3
"""Adaptation pages, step 2 of 2: Wikipedia features of the adaptation pages of each book, by origin month.

Settings: prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json, change 5.  Data only: no model is fitted and no feature is related
to loans.  No network: it reads the files written by 50_adaptation_views.py and the stored weekly totals.  The publication-date column of the
adaptations is not used anywhere.

Per page (data/db/wiki_led/adaptation_daily_views.parquet): daily user views are summed to weeks (Monday to Sunday) and divided by the
English Wikipedia total of that week (data/db/interest/wiki/weekly_total.parquet), exactly as in code/study2r/04_weekly_series.py (a day missing
from the answer is 0 views; valid = a full 7-day week that is not a partial week of the site total and has views).  The page features are
those of article_features in 10_test_a.py (lvl4, r4, r1, rmax, nrise8, run, dw, chg, valid4; the function is copied here and the script checks
the copy against the original on 12 pages at every run), at every origin month 2016-03 to 2026-09, from the weeks that ended on or before the
last day of the origin month.  mi = year*12 + month - 1.

A page "has data" at an origin when its first week with views ended on or before the end of the origin month.  A page before that week is
not counted at all (its zero weeks would otherwise enter the maxima).  The pre-creation weeks of a page are zero and its normal is floored at
1e-12, as for book articles created late: r4 and rmax of a page in its first weeks are therefore large (about +8 to +12 on the log scale) by
construction.  Views before a page move stay under the old title, so such a page starts at its move.

Per work (works.parquet work_id; the book is its Wikidata item) and origin month, over the kept pages of that book that have data:
  ad_n          number of adaptation pages with data (0 when none)
  ad_r4         maximum of r4
  ad_rmax       maximum of rmax
  ad_run        maximum of run
  ad_dw         sum of dw
  ad_lvl4       maximum of lvl4
  ad_new_weeks  weeks from the first week with views of the newest page (the "new adaptation" signal) to the last week used at the origin;
                pages that already had views in the first week of the data (2015-06-29, left-censored: their age is unknown) are not used
All columns except ad_n are missing (NaN) when ad_n = 0; ad_new_weeks is also missing when every page with data is left-censored.
Works with at least one kept page are all in the table (rows for every origin); works without a kept page are absent (treat as ad_n = 0).
Outputs (data/db/wiki_led/): adaptation_features.parquet (work_id, mi, ad_*), adaptation_page_features.parquet (article, mi, the nine
page features, has_data, age_weeks, first_week, left_censored), adaptation_features_summary.json.

Run from handoff/code:  nice -n 10 ../.venv/bin/python main_study/wiki_led/51_adaptation_features.py     (about 20 seconds; --test reads the *_test files of 50)
"""
import sys, ast, json, time, pathlib, warnings
import numpy as np, pandas as pd
import pyarrow.parquet as pq
from _common import D, OUT, log, T0

TEST = '--test' in sys.argv
SUF = '_test' if TEST else ''
EPS = 1e-12
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
DAYS = pd.date_range('2015-07-01', '2026-09-30', freq='D')           # the days fetched by 50_adaptation_views.py
ORIGINS = np.arange(2016 * 12 + 2, 2026 * 12 + 9)                     # 2016-03 to 2026-09


def month_end(mi):
    y, m = divmod(int(mi), 12)
    return pd.Timestamp(year=y, month=m + 1, day=1) + pd.offsets.MonthEnd(0)


ENDS = np.array([month_end(m) for m in ORIGINS], dtype='datetime64[ns]')

# ------------------------------------------------------------------------------------------------ weekly series (as in study2r/04)
TOT = pd.read_parquet(D / 'db' / 'interest' / 'wiki' / 'weekly_total.parquet').set_index('week')
WK_OF_DAY = DAYS - pd.to_timedelta(DAYS.weekday, unit='D')
WEEKS = pd.DatetimeIndex(WK_OF_DAY.unique())
WIDX = np.searchsorted(WEEKS.values, WK_OF_DAY.values)                # week number of each day
WSIZE = np.bincount(WIDX)                                             # days of the window in each week (5 in the first, 3 in the last)
TOTAL = TOT.reindex(WEEKS).total_views.to_numpy()
PARTIAL = TOT.reindex(WEEKS).partial_week.fillna(True).to_numpy().astype(bool)
IN_TOT = WEEKS.isin(TOT.index)                                        # study2r keeps only weeks that are in the site totals
assert IN_TOT.all() and len(WEEKS) == len(TOT)                        # all 588 weeks are there, so a week's position in a page's table is its position in WEEKS
WEND = (WEEKS + pd.Timedelta(days=6)).values
LIDX = np.searchsorted(WEND, ENDS, side='right') - 1                  # last week that ended on or before each origin month's last day
assert (LIDX >= 0).all()


def weekly_table(s):
    """s: float array of daily views over DAYS (0 for a day with no views) -> DataFrame(week, views, share, valid)."""
    wsum = np.bincount(WIDX, weights=s, minlength=len(WEEKS))
    g = pd.DataFrame({'week': WEEKS, 'views': wsum, 'share': wsum / TOTAL, 'valid': (WSIZE == 7) & ~PARTIAL & (wsum > 0)})
    return g[IN_TOT].reset_index(drop=True)


# ------------------------------------------------------------------------------------------------ page features (copy of 10_test_a.py)
def article_features(g):
    g = g.set_index('week').sort_index()
    grid = pd.date_range(g.index.min(), g.index.max(), freq='7D')
    s = g['share'].reindex(grid).astype(float)
    v = g['valid'].reindex(grid).astype(float)
    m4 = s.rolling(4, min_periods=1).mean()
    normal = s.shift(4).rolling(26, min_periods=13).median()              # 26 weeks before the last 4
    nrm_w = s.shift(1).rolling(26, min_periods=13).median()               # 26 weeks before each week
    ratio_w = (s + EPS) / (nrm_w + EPS)
    up = (ratio_w >= 1.5) & nrm_w.notna() & s.notna()
    upv = up.values.astype(int)
    runlen = np.zeros(len(upv), int)
    for i in range(len(upv)):
        runlen[i] = (runlen[i - 1] + 1 if i else 1) if upv[i] else 0
    contrib = pd.Series(np.where(upv == 1, np.log(ratio_w.values) * np.minimum(runlen, 4) / 4, 0.0), index=grid)
    lr = np.log((s + EPS) / (normal + EPS))
    f = pd.DataFrame({
        'lvl4': np.log(m4.clip(lower=EPS)),
        'r4': np.log((m4 + EPS) / (normal + EPS)),
        'r1': lr,
        'rmax': np.log((s + EPS) / (normal + EPS)).rolling(4, min_periods=1).max(),
        'nrise8': up.astype(int).rolling(8, min_periods=1).sum(),
        'run': pd.Series(runlen, index=grid),
        'dw': contrib.rolling(8, min_periods=1).sum(),
        'chg': np.log((m4 + EPS) / (s.shift(4).rolling(4, min_periods=1).mean() + EPS)),
        'valid4': v.rolling(4, min_periods=1).mean(),
    }, index=grid)
    f.loc[normal.isna(), ['r4', 'r1', 'rmax']] = np.nan
    wend = (grid + pd.Timedelta(days=6)).values
    idx = np.searchsorted(wend, ENDS, side='right') - 1                     # last week ending on or before the month end
    ok = idx >= 0
    out = f.iloc[idx[ok]].copy()
    out['mi'] = ORIGINS[ok]
    # a week more than 2 weeks before the month end means the article had no data that month: features missing
    stale = (ENDS[ok] - wend[idx[ok]]) > np.timedelta64(13, 'D')
    out.loc[stale, FEATS] = np.nan
    return out.reset_index(drop=True)


def original_article_features():
    """The function as it stands in 10_test_a.py, taken from the source text (the script itself runs a whole test when imported)."""
    src = (pathlib.Path(__file__).resolve().parent / '10_test_a.py').read_text()
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == 'article_features')
    ns = dict(np=np, pd=pd, EPS=EPS, ORIGINS=ORIGINS, ENDS=ENDS, FEATS=FEATS)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), '10_test_a.py:article_features', 'exec'), ns)
    return ns['article_features']


# ------------------------------------------------------------------------------------------------ daily file -> pages
def read_pages():
    """Yield (article, daily array over DAYS) from the daily file, one row group at a time."""
    pf = pq.ParquetFile(OUT / f'adaptation_daily_views{SUF}.parquet')
    d0 = np.datetime64('2015-07-01')
    for i in range(pf.num_row_groups):
        t = pf.read_row_group(i).to_pandas()
        for a, g in t.groupby('article', sort=False):
            off = (g.date.to_numpy().astype('datetime64[D]') - d0).astype(int)
            assert off.min() >= 0 and off.max() < len(DAYS), a
            s = np.zeros(len(DAYS))
            s[off] = g.views.to_numpy()
            yield a, s


def main():
    pages, X, HAS, FIRST, ORIG_CHECK = [], [], [], [], []
    original = original_article_features()
    n_checked = 0
    for a, s in read_pages():
        g = weekly_table(s)
        f = article_features(g)
        if n_checked < 12:                                                  # the copy against the original, exactly
            pd.testing.assert_frame_equal(f, original(g), check_exact=True)
            n_checked += 1
        nz = np.flatnonzero(g.views.to_numpy() > 0)                          # weeks with views (g has every week of WEEKS)
        if len(nz) == 0:
            continue
        pages.append(a); X.append(f[FEATS].to_numpy()); FIRST.append(int(nz[0]))
        assert (f.mi.to_numpy() == ORIGINS).all()
        if len(pages) % 500 == 0:
            log(f'  pages {len(pages)}')
    X = np.stack(X)                                                         # pages x origins x features
    FIRST = np.array(FIRST)
    HAS = FIRST[:, None] <= LIDX[None, :]                                   # the first week with views ended on or before the origin month's end
    CENS = FIRST == 0                                                       # views already in the first week of the data
    AGE = np.where(HAS, LIDX[None, :] - FIRST[:, None], np.nan)             # weeks since the first week with views
    log(f'pages with data {len(pages)}; original-function check passed on {n_checked} pages')

    # ---- page-level table
    M = len(ORIGINS)
    pf_ = pd.DataFrame(X.reshape(-1, len(FEATS)), columns=FEATS)
    pf_.insert(0, 'article', np.repeat(np.array(pages, dtype=object), M))
    pf_.insert(1, 'mi', np.tile(ORIGINS, len(pages)))
    pf_['has_data'] = HAS.reshape(-1)
    pf_['age_weeks'] = AGE.reshape(-1)
    pf_['first_week'] = np.repeat(WEEKS.values[FIRST], M)
    pf_['left_censored'] = np.repeat(CENS, M)
    pf_.to_parquet(OUT / f'adaptation_page_features{SUF}.parquet', index=False)

    # ---- work level
    W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id', 'item'])
    pairs = pd.read_parquet(OUT / 'adaptation_pairs.parquet', columns=['book', 'article', 'keep'])
    scope = set(pd.read_parquet(OUT / f'adaptation_fetch_status{SUF}.parquet', columns=['article']).article)   # the pages fetched in this run
    WP = pairs[pairs.keep & pairs.article.isin(scope)].drop_duplicates(['book', 'article'])
    WP = WP.merge(W, left_on='book', right_on='item')[['work_id', 'article']].drop_duplicates()
    pidx = {a: i for i, a in enumerate(pages)}
    works = sorted(WP.work_id.unique())
    F = {c: FEATS.index(c) for c in ('r4', 'rmax', 'run', 'dw', 'lvl4')}
    out = {k: np.full((len(works), M), np.nan) for k in ('ad_r4', 'ad_rmax', 'ad_run', 'ad_dw', 'ad_lvl4', 'ad_new_weeks')}
    n_out = np.zeros((len(works), M), dtype=np.int32)
    grp = WP.groupby('work_id').article.agg(list)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)                     # all-NaN slices give NaN on purpose
        for k, w in enumerate(works):
            ix = [pidx[a] for a in grp[w] if a in pidx]                     # kept pages of this work that have a daily series
            if not ix:
                continue
            h = HAS[ix]
            n = h.sum(0)
            n_out[k] = n
            for name, col, fn in (('ad_r4', 'r4', np.nanmax), ('ad_rmax', 'rmax', np.nanmax), ('ad_run', 'run', np.nanmax), ('ad_lvl4', 'lvl4', np.nanmax)):
                out[name][k] = fn(np.where(h, X[ix][:, :, F[col]], np.nan), axis=0)
            out['ad_dw'][k] = np.where(n > 0, np.nansum(np.where(h, X[ix][:, :, F['dw']], np.nan), axis=0), np.nan)
            out['ad_new_weeks'][k] = np.nanmin(np.where(h & ~CENS[ix][:, None], AGE[ix], np.nan), axis=0)
    R = pd.DataFrame({'work_id': np.repeat(np.array(works, dtype=np.int64), M), 'mi': np.tile(ORIGINS, len(works)).astype(np.int64),
                      'ad_n': n_out.reshape(-1), **{k: v.reshape(-1) for k, v in out.items()}})
    R.to_parquet(OUT / f'adaptation_features{SUF}.parquet', index=False)

    summ = dict(test=TEST, pages_with_data=len(pages), pages_in_scope=len(scope), pages_left_censored=int(CENS.sum()),
                works=len(works), works_with_a_page_with_data=int(WP[WP.article.isin(set(pages))].work_id.nunique()),
                origins=f'{ORIGINS[0] // 12}-{ORIGINS[0] % 12 + 1:02d} to {ORIGINS[-1] // 12}-{ORIGINS[-1] % 12 + 1:02d}', n_origins=M,
                rows=int(len(R)), rows_with_ad_n_positive=int((R.ad_n > 0).sum()), page_rows=int(len(pf_)),
                original_function_check_pages=n_checked, runtime_s=round(time.time() - T0))
    (OUT / f'adaptation_features_summary{SUF}.json').write_text(json.dumps(summ, indent=1))
    log(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
