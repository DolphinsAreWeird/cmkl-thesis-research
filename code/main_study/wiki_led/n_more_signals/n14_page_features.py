# n14. Addendum n, part 1, data for AD (film and TV pages) and LK (linked pages): per-work weekly shares and the features at each origin.
# DATA ONLY: no model is fitted and nothing is related to loans; the summary has counts only.
# Settings: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json (read-only; SHA-256 asserted), AD_film_and_TV_pages,
#   LK_linked_pages, common.time_rule, common.placebo_dates.  Pages from n12 (pages_AD.parquet, pages_LK.parquet), views located by n13
#   (views_index.parquet).  Choices the record leaves open, decided 2026-11-25 16:50 +07:00 (09:50 UTC) before this was run:
#   F1 Weekly series as m02's feats_from_series: days -> weeks starting Monday (2015-06-29), weekly views summed over the work's pages,
#      share = views / all English Wikipedia user views of the week (data/db/interest/wiki/weekly_total.parquet), valid = 7 days covered,
#      not a partial week and views > 0.  Features: article_features() of l_books_in_time/l02_views.py as copied (and checked) in m02,
#      unchanged, origins 2015-07 to 2026-08; the 7 kept features lvl4, r4, r1, run, dw, chg, valid4.  The copy is checked again here
#      against addendum l's stored book-article features (m02's check, 40 articles).
#   F2 A work's AD (LK) set = its pages of pages_AD (pages_LK) whose stored answer has data (status 200).  A work with none: every AD (LK)
#      column missing.  A page with status 200 but no view in the period stays in the set (it adds zeros).
#   F3 AD_out at origin t = 1 when some page of the work's AD set has a release month (n12, m01's rule) on or before t, else 0;
#      AD_since = t minus the latest such release month, capped at 120, missing when AD_out = 0.  Pages without a release month never count.
#   F4 LK_pages at origin t = log(1 + the work's LK-set pages with views > 0 in a week that ended on or before the last day of t).
#   F5 Placebo (record): the X_lag columns (ADl_*, LKl_*) are the same work's values at origin t-12; missing when t-12 is before 2015-07.
#   F6 Rows: data/db/wiki_led/l_books_in_time/rows.parquet restricted to origins up to 2026-07, in its order (asserted); a work's values are
#      the same for every format (asserted).  float32.
# Outputs (data/db/wiki_led/n_more_signals/): feat_AD.parquet (work_id, format, mi, AD_lvl4 .. AD_valid4, AD_out, AD_since, ADl_*),
#   feat_LK.parquet (LK_lvl4 .. LK_valid4, LK_pages, LKl_*), n14_summary.json; report data/reports/more_signals_ad_lk_data.md
#   Run from code/:  nice ../.venv/bin/python main_study/wiki_led/n_more_signals/n14_page_features.py
import sys, os, json, time, hashlib, pathlib, resource, warnings
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'testF'))
import _testf_analysis as T                                    # noqa: E402  (store_index, store_matrix, weekly_totals, DAYS)

DATA = T.D
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
WL = DATA / 'db' / 'wiki_led'
L = WL / 'l_books_in_time'
OUT = WL / 'n_more_signals'
REP = DATA / 'reports'
J_STORE = DATA / 'interim' / 'j_linked_views'
N_STORE = DATA / 'interim' / 'n_views'
PV = DATA / 'db' / 'study2r' / 'pv_daily'
fid = lambda t: hashlib.sha1(t.encode()).hexdigest()[:16]
os.nice(5)
T0 = time.time()
warnings.simplefilter('ignore', RuntimeWarning)


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB', *a, flush=True)


def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def month_end(mi):
    y, m = divmod(mi, 12)
    return pd.Timestamp(year=y, month=m + 1, day=1) + pd.offsets.MonthEnd(0)


# ---------------------------------------------------------------- article_features() as copied in m02 (from l02_views.py, unchanged)
ORIGINS = np.arange(mi_of('2015-07'), mi_of('2026-08') + 1)
ENDS = np.array([month_end(m) for m in ORIGINS], dtype='datetime64[ns]')
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
EPS = 1e-12


def article_features(g):
    g = g.set_index('week').sort_index()
    seen = (g['views'] > 0).to_numpy()
    if not seen.any():
        return None
    g = g.iloc[int(seen.argmax()):]
    grid = pd.date_range(g.index.min(), g.index.max(), freq='7D')
    s = g['share'].reindex(grid).astype(float)
    v = g['valid'].reindex(grid).astype(float)
    m4 = s.rolling(4, min_periods=1).mean()
    normal = s.shift(4).rolling(26, min_periods=13).median()
    nrm_w = s.shift(1).rolling(26, min_periods=13).median()
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
    idx = np.searchsorted(wend, ENDS, side='right') - 1
    ok = idx >= 0
    out = f.iloc[idx[ok]].copy()
    out['mi'] = ORIGINS[ok]
    stale = (ENDS[ok] - wend[idx[ok]]) > np.timedelta64(13, 'D')
    out.loc[stale, FEATS] = np.nan
    return out.reset_index(drop=True)


F7 = ['lvl4', 'r4', 'r1', 'run', 'dw', 'chg', 'valid4']

# check of the copy (m02's check): addendum l's stored book-article features are reproduced
WB = pd.read_parquet(L / 'weekly_book.parquet')
WFs = pd.read_parquet(L / 'wiki_features.parquet')
WFs = WFs[WFs.kind == 'book']
chk_titles = sorted(WFs.article.unique())[::max(1, WFs.article.nunique() // 40)][:40]
worst = 0.0
for t in chk_titles:
    g = WB[WB.article == t][['week', 'views', 'share', 'valid']].copy()
    g['week'] = pd.to_datetime(g.week)
    mine = article_features(g)
    ref = WFs[WFs.article == t]
    cm = ref.merge(mine, on='mi', suffixes=('_ref', ''))
    for c in FEATS:
        d = np.nanmax(np.abs(cm[c].to_numpy(float) - cm[c + '_ref'].to_numpy(float))) if len(cm) else 0.0
        assert (cm[c].isna() == cm[c + '_ref'].isna()).all(), f'missing pattern differs for {t} {c}'
        worst = max(worst, 0.0 if np.isnan(d) else d)
assert worst < 1e-6, f'copied article_features does not reproduce addendum l ({worst})'
log('check: article_features copy reproduces addendum l on', len(chk_titles), 'articles, largest difference', worst)
del WB, WFs

TW = T.weekly_totals()[['week', 'total_views', 'days_covered', 'partial_week']].reset_index(drop=True)
TW['week'] = pd.to_datetime(TW.week)
NW = len(TW)
TOTV = TW.total_views.to_numpy(float)
FULLWK = ((TW.days_covered == 7) & ~TW.partial_week).to_numpy()
WEND = (TW.week + pd.Timedelta(days=6)).to_numpy(dtype='datetime64[ns]')
dwk = ((T.DAYS - pd.Timestamp('2015-06-29')).days // 7).to_numpy()
assert (TW.week.iloc[0] == pd.Timestamp('2015-06-29')) and dwk.max() < NW


def feats_from_series(views):
    g = pd.DataFrame({'week': TW.week, 'views': views, 'share': views / TOTV, 'valid': FULLWK & (views > 0)})
    return article_features(g)


# ---------------------------------------------------------------- weekly views of every page (sources of n13)
AD = pd.read_parquet(OUT / 'pages_AD.parquet')
LK = pd.read_parquet(OUT / 'pages_LK.parquet')
VI = pd.read_parquet(OUT / 'views_index.parquet')
assert set(VI.page) == set(AD.page) | set(LK.page), 'views_index does not cover the pages of n12; rerun n13'
n_missing = int(VI.source.isna().sum())
assert n_missing == 0, f'{n_missing} pages not stored yet; finish n13 first'
use = VI[VI.status == 200].reset_index(drop=True)
ppos = {t: i for i, t in enumerate(use.page)}
WK = np.zeros((len(use), NW), np.float64)


class StoreP:
    def __init__(self, views):
        self.views = views


def put(titles, V):
    for k, t in enumerate(titles):
        w = np.zeros(NW)
        np.add.at(w, dwk, V[k].astype(np.float64))
        WK[ppos[t]] = w


for src, store in (('testF', T.Paths().views), ('j', J_STORE), ('n13', N_STORE)):
    tl = list(use[use.source == src].page)
    for i in range(0, len(tl), 2000):
        ch = tl[i:i + 2000]
        V, st = T.store_matrix(StoreP(store), ch)
        assert (st == 200).all(), f'status differs in the {src} store'
        put(ch, V)
    log(f'weekly views from {src}: {len(tl)} pages')
tl = list(use[use.source == 'adaptation'].page)
if tl:
    AV = pd.read_parquet(WL / 'adaptation_daily_views.parquet', filters=[('article', 'in', tl)])
    dpos = {d: i for i, d in enumerate(T.DAYS)}
    for a, g in AV.groupby('article'):
        v = np.zeros(len(T.DAYS), np.int64)
        di = np.array([dpos.get(pd.Timestamp(d), -1) for d in g.date])
        ok = di >= 0
        np.add.at(v, di[ok], g.views.to_numpy()[ok])
        put([a], v[None, :])
log(f'weekly views from adaptation: {len(tl)} pages')
tl = list(use[use.source == 'study2r'].page)
for t in tl:
    d = pd.read_parquet(PV / f'{fid(t.replace("_", " "))}.parquet')
    assert (d.title == t.replace('_', ' ')).all(), f'pv_daily title differs for {t}'
    v = d.set_index('date').views.reindex(T.DAYS, fill_value=0).to_numpy()
    put([t], v[None, :])
log(f'weekly views from study2r: {len(tl)} pages')
first_seen = np.where((WK > 0).any(axis=1), (WK > 0).argmax(axis=1), -1)
first_wend = np.where(first_seen >= 0, WEND[np.clip(first_seen, 0, None)], np.datetime64('NaT', 'ns'))
n_zero = int((first_seen < 0).sum())
log('pages with data', len(use), '| of them no view in the period', n_zero)

# ---------------------------------------------------------------- per-work grids (origins 2015-07 .. 2026-08)
R = pd.read_parquet(L / 'rows.parquet', columns=['work_id', 'format', 'mi'])
R = R[R.mi <= mi_of('2026-07')].reset_index(drop=True)
R['format'] = R.format.astype(str)
AM0 = int(ORIGINS[0])
NO = len(ORIGINS)
ri_o = (R.mi - AM0).to_numpy()
assert ri_o.min() >= 0


def grid_for(P, extra):
    """P: work_id, page (and release_mi for AD).  -> (works, grid works x origins x (7 + extra)), counts."""
    P = P[P.page.isin(ppos)]
    works = np.sort(P.work_id.unique())
    G = np.full((len(works), NO, len(F7) + (2 if extra == 'AD' else 1)), np.nan, np.float32)
    n_feat = 0
    for k, (w, g) in enumerate(P.groupby('work_id', sort=True)):
        assert works[k] == w
        rows_ = [ppos[t] for t in g.page]
        f = feats_from_series(WK[rows_].sum(axis=0))
        if f is not None and len(f):
            G[k, (f.mi - AM0).to_numpy(), :len(F7)] = f[F7].to_numpy(np.float32)
            n_feat += 1
        if extra == 'AD':
            rel = g.release_mi.to_numpy(float)
            rel = rel[np.isfinite(rel)]
            if len(rel):
                last = np.array([rel[rel <= m].max() if (rel <= m).any() else np.nan for m in ORIGINS])
            else:
                last = np.full(NO, np.nan)
            out = np.isfinite(last)
            G[k, :, len(F7)] = out.astype(np.float32)
            sinc = np.where(out, np.minimum(ORIGINS - np.nan_to_num(last), 120), np.nan)
            G[k, :, len(F7) + 1] = sinc.astype(np.float32)
        else:
            fw = first_wend[rows_]
            n_by = (fw[None, :] <= ENDS[:, None]).sum(axis=1)          # NaT compares False
            G[k, :, len(F7)] = np.log1p(n_by).astype(np.float32)
    return works, G, n_feat


def to_rows(works, G, names, tag, tagl):
    wpos = {w: i for i, w in enumerate(works)}
    wi = R.work_id.map(wpos).to_numpy(dtype=float)
    has = np.isfinite(wi)
    wi_ = np.where(has, wi, 0).astype(int)
    real = np.full((len(R), len(names)), np.nan, np.float32)
    real[has] = G[wi_[has], ri_o[has], :]
    lag = np.full_like(real, np.nan)
    lo = ri_o - 12
    okl = has & (lo >= 0)
    lag[okl] = G[wi_[okl], lo[okl], :]
    out = pd.DataFrame({'work_id': R.work_id, 'format': R.format, 'mi': R.mi})
    for k, c in enumerate(names):
        out[f'{tag}_{c}'] = real[:, k]
    for k, c in enumerate(names):
        out[f'{tagl}_{c}'] = lag[:, k]
    return out


summ = dict(check_article_features_max_diff=worst, pages_with_data=len(use), pages_with_data_no_views=n_zero,
            pages_by_source={str(k): int(v) for k, v in VI.source.value_counts().items()},
            pages_by_status={str(k): int(v) for k, v in VI.status.value_counts().items()})
sc = (R.mi >= mi_of('2019-01')).to_numpy()
R0 = pd.read_parquet(L / 'rows.parquet', columns=['work_id', 'format', 'mi'])
R0 = R0[R0.mi <= mi_of('2026-07')].reset_index(drop=True)
for sig, P, names in (('AD', AD, F7 + ['out', 'since']), ('LK', LK, F7 + ['pages'])):
    works, G, n_feat = grid_for(P, sig)
    O = to_rows(works, G, names, sig, sig + 'l')
    assert (O.work_id.to_numpy() == R0.work_id.to_numpy()).all() and (O.mi.to_numpy() == R0.mi.to_numpy()).all() \
        and (O.format.to_numpy() == R0.format.astype(str).to_numpy()).all(), 'row order differs from rows.parquet'
    fc = [c for c in O.columns if c not in ('work_id', 'format', 'mi')]
    chk = O[['work_id', 'mi'] + fc].copy()
    chk[fc] = chk[fc].fillna(-9999.0)
    assert len(chk.drop_duplicates()) == len(chk[['work_id', 'mi']].drop_duplicates()), 'values differ between formats of a work'
    O.to_parquet(OUT / f'feat_{sig}.parquet', index=False)
    in_set = P[P.page.isin(ppos)]
    summ[sig] = dict(work_page_rows=len(P), works_with_pages=int(P.work_id.nunique()), pages=int(P.page.nunique()),
                     pages_with_data=int(P[P.page.isin(ppos)].page.nunique()), works_with_a_set=len(works), works_with_a_feature_series=n_feat,
                     pages_by_source={str(k): int(v) for k, v in VI[VI.page.isin(set(P.page))].source.value_counts().items()},
                     pages_per_work=in_set.groupby('work_id').size().describe().round(2).to_dict(),
                     rows_with_a_set=int(np.isfinite(O[f'{sig}_{names[-1]}'].to_numpy()).sum()) if sig == 'LK' else int(np.isfinite(O['AD_out'].to_numpy()).sum()),
                     scored_rows=int(sc.sum()),
                     share_scored_rows_lvl4=float(np.mean(np.isfinite(O[f'{sig}_lvl4'].to_numpy()[sc]))),
                     share_scored_rows_r4=float(np.mean(np.isfinite(O[f'{sig}_r4'].to_numpy()[sc]))),
                     share_scored_rows_set=float(np.mean(np.isfinite(O[f'{sig}_{"out" if sig == "AD" else "pages"}'].to_numpy()[sc]))),
                     share_scored_rows_lag_lvl4=float(np.mean(np.isfinite(O[f'{sig}l_lvl4'].to_numpy()[sc]))))
    if sig == 'AD':
        summ[sig]['scored_rows_AD_out_1'] = int(np.nansum(O.AD_out.to_numpy()[sc] == 1))
        summ[sig]['release_month_known_pages'] = int(in_set.drop_duplicates('page').release_mi.notna().sum())
    log(sig, json.dumps(summ[sig]))
    del O, G, chk

summ['runtime_s'] = round(time.time() - T0)
summ['peak_gb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30, 2)
summ['written'] = time.strftime('%Y-%m-%d %H:%M %z')
(OUT / 'n14_summary.json').write_text(json.dumps(summ, indent=1, default=str))
S12 = json.loads((OUT / 'n12_summary.json').read_text())
S13 = json.loads((OUT / 'n13_summary.json').read_text())
Lr = ['# Addendum n, part 1: AD (film and TV pages) and LK (linked pages), data (counts only)', '',
      f'Made by `code/main_study/wiki_led/n_more_signals/n12_wikidata_pages.py`, `n13_views.py` and `n14_page_features.py`; this report '
      f'{time.strftime("%Y-%m-%d %H:%M")} (+07:00). Data only: no model, nothing related to loans. Choices: '
      '`data/db/wiki_led/n_more_signals/notes_ad_lk.md` (C1 to C10, V1 to V4, F1 to F6).', '',
      '## Wikidata (n12)', '',
      f'- Book items {S12["book_items"]:,} ({S12["works_with_item"]:,} works). Requests: network {S12["wikidata"]["network"]:,}, from cache '
      f'{S12["wikidata"]["cache"]:,}, back-offs {S12["wikidata"]["backoffs"]}.',
      f'- AD: adaptation items {S12["AD"]["adaptation_items"]:,} {S12["AD"]["groups"]} (m01 reproduced on {S12["AD"]["m01_check_items"]:,} book items); '
      f'film or TV items without an English article {S12["AD"]["screen_items_without_english_article"]:,}; work-page rows {S12["AD"]["work_page_rows"]:,}, '
      f'works {S12["AD"]["works"]:,}, pages {S12["AD"]["pages"]:,} {S12["AD"]["rows_by_kind"]}; rows without a release month {S12["AD"]["rows_without_release_month"]}.',
      f'- LK: best-rank statements {S12["LK"]["best_rank_statements"]:,} {S12["LK"]["statements_by_property"]}; left out by item {S12["LK"]["left_out_by_item"]}; '
      f'left out by page {S12["LK"]["left_out_pages"]}; linked items without an English article {S12["LK"]["linked_items_without_english_article"]:,}; '
      f'work-page rows {S12["LK"]["work_page_rows"]:,}, works {S12["LK"]["works"]:,}, pages {S12["LK"]["pages"]:,}; by link type {S12["LK"]["rows_by_kind"]}; '
      f'by category {S12["LK"]["rows_by_category"]}.', '',
      '## Views (n13)', '',
      f'- Pages {S13["pages"]:,} (AD {S13["AD_pages"]:,}, LK {S13["LK_pages"]:,}); by source {S13["by_source"]}; by status {S13["by_status"]}.',
      f'- Downloaded in this run {S13["downloaded_now"]:,} (own store data/interim/n_views/); stored before: the rest.', '',
      '## Features (n14)', '',
      f'- Check: the copied article_features() gives addendum l\'s stored features on 40 articles (largest difference {worst:.1e}).',
      f'- Pages with data {len(use):,}, of which no view in the period {n_zero}.']
for sig in ('AD', 'LK'):
    s = summ[sig]
    Lr.append(f'- {sig}: works with a set {s["works_with_a_set"]:,} (with a feature series {s["works_with_a_feature_series"]:,}); pages with data '
              f'{s["pages_with_data"]:,} of {s["pages"]:,}; share of the {s["scored_rows"]:,} scored rows (origins 2019-01 to 2026-07) with lvl4 '
              f'{s["share_scored_rows_lvl4"]:.4f}, with r4 {s["share_scored_rows_r4"]:.4f}, in a set {s["share_scored_rows_set"]:.4f}; '
              f'lag (t-12) lvl4 {s["share_scored_rows_lag_lvl4"]:.4f}.')
Lr.append(f'- Run time {summ["runtime_s"]} s, peak memory {summ["peak_gb"]} GB.')
(REP / 'more_signals_ad_lk_data.md').write_text('\n'.join(Lr) + '\n')
log('done')
