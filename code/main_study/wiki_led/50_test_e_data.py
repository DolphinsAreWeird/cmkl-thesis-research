# 50. Test E (another platform), data only: monthly LibriVox listening (Internet Archive views) in the row layout of Test A.
# Nothing here fits a model or relates a feature to listens; the only outcome statistics are counts and base rates for the report.
# Units: LibriVox "books" = the 7,848 book groups of data/db/listening.parquet (book_id = LibriVox bookgroup; the catch-all
# group -1, 304 unrelated recordings, is dropped). Listens = Internet Archive non-robot views, all recordings of the group, per month.
# Links: reused as stored (data/interim/recordings_linked.pkl, made by code/link_titles.py), nothing is matched again.
# Wikipedia views: only series already on disk are used, nothing is downloaded:
#   book articles   data/db/study2r/weekly_book.parquet (same pipeline as Test A, redirects kept by the screen), else
#                   data/raw/wiki_book_daily.json (daily views of the article's own title, 2016-07-01 to 2026-08-31, code/weekly_collect.py)
#   author articles data/db/study2r/weekly_author.parquet
# Weekly shares are built exactly as in code/study2r/04_weekly_series.py (ISO weeks from Monday, missing day = 0 views, share of the
# week's total English Wikipedia user views in data/db/interest/wiki/weekly_total.parquet) and article_features is a verbatim copy
# of the function in 10_test_a.py.
# Differences from Test A (all also written to the report):
#   (1) Origins: the listening data begin in 2017-01 and a book needs 12 months of listens, so the first origin is 2017-12.
#   (2) Eligibility: listens summed over t-11..t (months not excluded, months before the book's first public month skipped) >= 24.
#   (3) Months before a book's first public month (earliest IA public date of its recordings) are missing, not zero; M6 and the
#       12-month mean skip them, h_lt1 and h_lyago read them as 0 (as Test A does for months before the first loan).
#   (4) Excluded months (not an origin or target; missing inside M6, the 12-month mean, the eligibility sum, h_lt1 and h_lyago):
#       2023-12 and 2024-10 (Internet Archive outages: at least 3 days of the 887-recording daily sample under half of the local
#       median) and 2025-01 (a one-day flood: month total more than twice its trailing 12-month median). Test A's half-of-median
#       rule is computed for every month and shown in test_e_months.csv, but it also fires on 2018-11 and 2018-12 because the
#       platform level halved on 2018-08-02, which is not missing data; those two months stay in (flag regime).
#   (5) h_age = months since the book's first public month (true age); h_age_obs = Test A's formula (months since the first
#       month with listens > 0 in this panel, which is 2017-01 for every older book). regime flags the 2018-08 level break.
#   (6) flag_jump = 1 when the origin month or its target month is a month in which the median listens of the books already public in
#       2017-01 moved by a factor of 1.5 or more from the previous month (platform-wide traffic, not demand for single books). It looks
#       at the target month's platform median and is a filter for scoring, never a feature.
# Output: data/db/wiki_led/test_e_rows.parquet, test_e_links.parquet, test_e_months.csv, test_e_wiki_features.parquet,
#         test_e_articles_needed.csv, data/reports/wiki_led_test_e_data.md
#   nice ../.venv/bin/python main_study/wiki_led/50_test_e_data.py     (from code/; about 2 minutes, under 1 GB)
import sys, json, time, pathlib, hashlib, gc, warnings
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
OUT = D / 'db' / 'wiki_led'
OUT.mkdir(parents=True, exist_ok=True)
REP = D / 'reports'
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def mi_of(ym):  # 'YYYY-MM' -> month index year*12 + month-1
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def ym_of(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


def month_end(mi):
    y, m = divmod(mi, 12)
    return pd.Timestamp(year=y, month=m + 1, day=1) + pd.offsets.MonthEnd(0)


ORIG0, ORIG1 = mi_of('2016-03'), mi_of('2026-07')    # the origins of Test A
SCORE0 = mi_of('2019-01')                            # Test A's first scored origin (training only before it)
MIN12 = 24                                           # listens over t-11..t needed for a book to be eligible
BREAK = mi_of('2018-08')                             # the Internet Archive level break (2018-08-02)
EPS = 1e-12
EXCL = {mi_of('2023-12'), mi_of('2024-10'), mi_of('2025-01')}     # checked against the two rules below (assert), reasons written from the data
warnings.filterwarnings('ignore', category=RuntimeWarning)

# ---------------------------------------------------------------- listening panel
lis = pd.read_parquet(D / 'db' / 'listening.parquet')
bks = pd.read_parquet(D / 'db' / 'books.parquet')
assert lis.book_id.nunique() == len(bks) == 7849 and set(lis.book_id) == set(bks.book_id)
n_listen_rows = len(lis)
lis = lis[lis.book_id != '-1']
P = lis.pivot(index='book_id', columns='period', values='listens')
P = P.loc[sorted(P.index, key=int)]
MI = np.array([mi_of(p) for p in P.columns])
assert (np.diff(MI) == 1).all() and MI[0] == mi_of('2017-01') and MI[-1] == mi_of('2026-08')
BOOKS = list(P.index)
A0 = P.values.astype(np.float32)                       # books x months, raw (zeros kept)
log('listening panel', A0.shape, 'zero cells', int((A0 == 0).sum()))

# ---------------------------------------------------------------- recordings: links, public dates, recordings per book
lk = pd.read_pickle(D / 'interim' / 'recordings_linked.pkl')
n_rec_all = len(lk)
lk = lk[lk.n_authors == 1].copy()                       # the recordings build_db.py summed into listening.parquet
lk['book_id'] = lk.bookgroup.astype(str)
n_rec_minus1 = int((lk.book_id == '-1').sum())
lk = lk[lk.book_id != '-1'].copy()
assert set(lk.book_id) == set(BOOKS)
pub = pd.to_datetime(lk.publicdate, utc=True).dt.tz_localize(None)
lk['pub_mi'] = pub.dt.year * 12 + pub.dt.month - 1      # NaN where the Internet Archive date is missing
gr = lk.groupby('book_id', sort=False)
pub_first = gr.pub_mi.min().reindex(BOOKS)
first_pos = np.array([MI[np.argmax(r > 0)] if (r > 0).any() else -1 for r in A0])
pub_use = pub_first.values.copy()
no_pub = np.isnan(pub_use)
pub_use[no_pub] = first_pos[no_pub]                     # no date: the first month with listens (2017-01 for all of them)
assert (first_pos > 0).all()
chk = pub_use >= MI[0]                                  # books first public inside the listening window
dd = (first_pos - pub_use)[chk]
assert dd.min() >= 0 and dd.max() <= 1, 'listens before the public month'
A = A0.copy()                                           # months before the first public month are missing, not zero
pre_pub_cells = 0
for b in np.where(chk)[0]:
    k = int(pub_use[b] - MI[0])
    A[b, :k] = np.nan
    pre_pub_cells += k
log('first public month inside the window for', int((chk & ~no_pub).sum()), 'books; cells set missing', pre_pub_cells,
    '| zero cells before public month', int(((A0 == 0) & np.isnan(A)).sum()), '| groups without a public date', int(no_pub.sum()))
ex_mask = np.isin(MI, sorted(EXCL))

# recordings public by month (n_rec): recordings with no date count from the start
rec_pub = np.where(lk.pub_mi.isna(), -10 ** 9, lk.pub_mi.fillna(0)).astype(np.int64)
NREC = np.zeros((len(BOOKS), len(MI)), np.int16)
bidx = {b: i for i, b in enumerate(BOOKS)}
rb = lk.book_id.map(bidx).values
for k, m in enumerate(MI):
    np.add.at(NREC[:, k], rb[rec_pub <= m], 1)

# ---------------------------------------------------------------- links at book level (as stored, one link per book)
def resolve(s):
    v = s.dropna().unique()
    if len(v) == 0:
        return None, 'none'
    if len(v) > 1:
        return None, 'conflict'
    return v[0].replace('_', ' '), ('partial' if s.isna().any() else 'full')


L = pd.DataFrame(index=pd.Index(BOOKS, name='book_id'))
for col, nm in [('wiki_book', 'book'), ('wiki_author', 'author')]:
    res = [resolve(g[col]) for _, g in gr]
    keys = [k for k, _ in gr]
    t = pd.DataFrame({nm + '_article': [r[0] for r in res], nm + '_link': [r[1] for r in res]}, index=keys)
    L = L.join(t)
L['title'] = bks.set_index('book_id').title.reindex(L.index).values
L['author'] = gr.author.first().reindex(L.index).values
L['n_rec'] = gr.size().reindex(L.index).values
L['pub_mi'] = pub_use
L['pub_ym'] = [ym_of(int(x)) for x in pub_use]
L['pub_known'] = ~no_pub
L['first_listen_mi'] = first_pos
L['listens_total'] = np.nansum(A.astype(np.float64), axis=1)
L['book_article_paren'] = L.book_article.str.contains(r'\(', na=False)
L['book_title_tag_nonbook'] = L.book_article.str.contains(r'\((?:[^)]*\b)?(?:film|play|opera|musical|TV|television|miniseries|series|ballet|song|album|comics|game|radio|drama|movie)\b[^)]*\)$', case=False, na=False)
L['author_article_paren'] = L.author_article.str.contains(r'\(', na=False)
log('links: book', L.book_article.notna().sum(), 'author', L.author_article.notna().sum(),
    '| conflicts', int((L.book_link == 'conflict').sum()), int((L.author_link == 'conflict').sum()))

# ---------------------------------------------------------------- stored Wikipedia series: which linked articles have them
TOT = pd.read_parquet(D / 'db' / 'interest' / 'wiki' / 'weekly_total.parquet').set_index('week')
want_b, want_a = set(L.book_article.dropna()), set(L.author_article.dropna())
import pyarrow.parquet as pq
S2 = D / 'db' / 'study2r'


def read_weekly(path, titles):
    t = pq.read_table(path, filters=[('article', 'in', sorted(titles))], columns=['article', 'week', 'views', 'share', 'top_day_share', 'valid'])
    return t.to_pandas()


WB_s2 = read_weekly(S2 / 'weekly_book.parquet', want_b)
WA_s2 = read_weekly(S2 / 'weekly_author.parquet', want_a)
log('study2r weekly series: book articles', WB_s2.article.nunique(), 'author articles', WA_s2.article.nunique())
raw_daily = json.load(open(D / 'raw' / 'wiki_book_daily.json'))
raw_daily = {k.replace('_', ' '): v for k, v in raw_daily.items()}
raw_titles = set(raw_daily) & want_b
log('raw daily series for linked book articles', len(raw_titles), '| in both sources', len(raw_titles & set(WB_s2.article.unique())))


def weekly_from_daily(title, daily, start='2016-07-01', end='2026-08-31'):
    """The weekly table of code/study2r/04_weekly_series.py for one article built from a {YYYYMMDD: views} dict."""
    DAYS = pd.date_range(start, end, freq='D')
    ks = pd.to_datetime(list(daily.keys()), format='%Y%m%d')
    s = pd.Series(np.array(list(daily.values()), dtype=float), index=ks)
    s = s[~s.index.duplicated()].reindex(DAYS, fill_value=0.0)          # a day missing from the API answer counts as 0 views
    wk = DAYS - pd.to_timedelta(DAYS.weekday, unit='D')
    df = pd.DataFrame({'week': wk, 'v': s.to_numpy()})
    g = df.groupby('week').v.agg(['sum', 'max', 'size']).reset_index()
    g = g[g.week.isin(TOT.index)]
    tt = TOT.loc[g.week]
    g['article'] = title
    g['views'] = g['sum'].to_numpy()
    g['share'] = g['sum'].to_numpy() / tt.total_views.to_numpy()
    g['top_day_share'] = np.where(g['sum'] > 0, g['max'] / g['sum'].replace(0, np.nan), np.nan)
    g['valid'] = ((g['size'] == 7) & ~tt.partial_week.to_numpy() & (g['sum'] > 0)).to_numpy()
    return g[['article', 'week', 'views', 'share', 'top_day_share', 'valid']]


# ---------------------------------------------------------------- article_features: verbatim copy of 10_test_a.py
ORIGINS = np.arange(ORIG0, ORIG1 + 1)
ENDS = np.array([month_end(m) for m in ORIGINS], dtype='datetime64[ns]')
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']


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


def features_of(frames):
    parts = []
    for a, g in frames.groupby('article', sort=False):
        h = article_features(g)
        h.insert(0, 'article', a)
        parts.append(h)
    return pd.concat(parts, ignore_index=True)


# book articles: Study 2R series where present, else the raw daily series; author articles: Study 2R series
s2_book_titles = set(WB_s2.article.unique())
raw_only = sorted(raw_titles - s2_book_titles)
RAWW = pd.concat([weekly_from_daily(t, raw_daily[t]) for t in raw_only], ignore_index=True)
FB_s2, FA_s2 = features_of(WB_s2), features_of(WA_s2)
FB_raw = features_of(RAWW)
log('features: study2r book', FB_s2.article.nunique(), 'raw book', FB_raw.article.nunique(), 'author', FA_s2.article.nunique())

# check 1: the copy of article_features reproduces the features stored for Test A (same input series)
TA = pq.read_table(OUT / 'test_a_wiki_features.parquet', filters=[('article', 'in', sorted(want_b | want_a))]).to_pandas()
check = {}
for name, F, kind in [('study2r_book', FB_s2, 'book'), ('study2r_author', FA_s2, 'author')]:
    ta = TA[TA.kind == kind].drop(columns='kind')
    m = F.merge(ta, on=['article', 'mi'], suffixes=('', '_ta'))
    dmax = max(float(np.nanmax(np.abs(m[c] - m[c + '_ta']))) for c in FEATS)
    nanmis = int(sum((m[c].isna() != m[c + '_ta'].isna()).sum() for c in FEATS))
    check[name] = dict(articles=int(m.article.nunique()), rows=int(len(m)), max_abs_diff=dmax, nan_mismatch=nanmis)
# check 2: the raw daily series gives the same features as the Study 2R series on the articles that are in both sources
both = sorted(raw_titles & s2_book_titles)
FB_raw_both = features_of(pd.concat([weekly_from_daily(t, raw_daily[t]) for t in both], ignore_index=True))
m = FB_raw_both.merge(FB_s2, on=['article', 'mi'], suffixes=('', '_s2'))
m = m[m.mi >= mi_of('2017-12')]
dd_ = pd.concat([(m[c] - m[c + '_s2']).abs().rename(c) for c in FEATS], axis=1)
nred = pd.read_csv(S2 / 'article_summary.csv').set_index('article').n_redirects_kept
no_red = m.article.map(nred).fillna(0).eq(0)
check['raw_vs_study2r'] = dict(articles=len(both), rows=int(len(m)), articles_without_redirects=int(m[no_red].article.nunique()),
                               max_abs_diff_without_redirects=float(np.nanmax(dd_[no_red].values)),
                               max_abs_diff_all=float(np.nanmax(dd_.values)),
                               nan_mismatch=int(sum((m[c].isna() != m[c + '_s2'].isna()).sum() for c in FEATS)),
                               share_cells_differing_with_redirects=float((dd_[~no_red] > 1e-9).values.mean()) if (~no_red).any() else 0.0)
log('feature checks', json.dumps(check))
del RAWW, FB_raw_both, m, dd_
gc.collect()

FBW = pd.concat([FB_s2.assign(src=1), FB_raw.assign(src=2)], ignore_index=True)
FAW = FA_s2.assign(src=1)
WFcache = pd.concat([FBW.assign(kind='book'), FAW.assign(kind='author')], ignore_index=True)
WFcache.to_parquet(OUT / 'test_e_wiki_features.parquet', index=False)
b_src = dict(FBW.drop_duplicates('article')[['article', 'src']].values)
a_src = dict(FAW.drop_duplicates('article')[['article', 'src']].values)
L['book_src'] = L.book_article.map(b_src).fillna(0).astype(np.int8)
L['author_src'] = L.author_article.map(a_src).fillna(0).astype(np.int8)
log('books with stored weekly views: book article', int((L.book_src > 0).sum()), 'author article', int((L.author_src > 0).sum()),
    'either', int(((L.book_src > 0) | (L.author_src > 0)).sum()))

# ---------------------------------------------------------------- platform months: totals, Test A's rule, the daily sample
tot = np.nansum(A0.astype(np.float64), axis=0)                          # raw totals of the 7,848 books (zeros kept, no missing)
tot_s = pd.Series(tot, index=MI)
trail = tot_s.rolling(12).median().shift(1)
ratio = tot_s / trail


def daily_sample():
    Lr = json.load(open(D / 'raw' / 'ia_views_daily_books.json'))     # 887 recordings, non-zero days only
    base = np.datetime64('2017-01-01')
    n = int((np.datetime64('2026-09-30') - base).astype(int)) + 1
    tt = np.zeros(n)
    for i, d in Lr.items():
        idx = (np.array(list(d.keys()), dtype='datetime64[D]') - base).astype(int)
        val = np.array(list(d.values()), dtype=float)
        ok = (idx >= 0) & (idx < n)
        np.add.at(tt, idx[ok], val[ok])
    nrec = len(Lr)
    ids = set(Lr)
    del Lr
    return pd.Series(tt, index=pd.date_range('2017-01-01', periods=n)), nrec, ids


DS, n_sample, sample_ids = daily_sample()
DS = DS.loc[:'2026-08-31']
med29 = DS.rolling(29, center=True, min_periods=15).median()
dr = DS / med29
low_days = (dr < 0.5)
flood_days = (dr > 3.0)
mkey = DS.index.year * 12 + DS.index.month - 1
n_low = pd.Series(low_days.values, index=mkey).groupby(level=0).sum()
n_flood = pd.Series(flood_days.values, index=mkey).groupby(level=0).sum()
max_day_ratio = pd.Series(dr.values, index=mkey).groupby(level=0).max()
M = pd.DataFrame({'ym': [ym_of(m) for m in MI], 'mi': MI, 'total_listens': tot.astype(np.int64),
                  'books_with_listens': (A0 > 0).sum(axis=0), 'trailing12_median': trail.values, 'ratio_to_trailing12': ratio.values})
M['test_a_rule_low'] = (M.ratio_to_trailing12 < 0.5)
M['flood_rule_high'] = (M.ratio_to_trailing12 > 2.0)
M['sample_days_below_half'] = M.mi.map(n_low).fillna(0).astype(int)
M['sample_days_above_3x'] = M.mi.map(n_flood).fillna(0).astype(int)
M['sample_max_day_ratio'] = M.mi.map(max_day_ratio)
M['outage_rule'] = M.sample_days_below_half >= 3
older = (pub_use < MI[0]) & ~no_pub                                     # books already public in 2017-01 (dated)
med_old = np.median(A0[older], axis=0)
M['older_books'] = int(older.sum())
M['median_older_books'] = med_old
M['p10_older_books'] = np.percentile(A0[older], 10, axis=0)
M['p90_older_books'] = np.percentile(A0[older], 90, axis=0)
prev_ok = np.r_[False, ~ex_mask[:-1]]                                    # the previous month exists and is not excluded
mr = np.r_[np.nan, med_old[1:] / med_old[:-1]]
M['median_ratio_prev'] = np.where(prev_ok, mr, np.nan)
M['median_jump'] = (M.median_ratio_prev >= 1.5) | (M.median_ratio_prev <= 1 / 1.5)     # the typical book moved 1.5 times or more in one month
JUMP = set(M.mi[M.median_jump])
M['excluded'] = M.mi.isin(EXCL)
zero_days = pd.Series((DS == 0).values, index=mkey).groupby(level=0).sum()


def reason(r):
    out = []
    if r.outage_rule:
        out.append(f'outage: {r.sample_days_below_half} days under half of the local median in the daily sample, {int(zero_days.get(r.mi, 0))} with no views at all')
    if r.flood_rule_high:
        out.append(f'flood: month total {r.ratio_to_trailing12:.1f} times its trailing 12-month median, largest sample day {r.sample_max_day_ratio:.0f} times normal')
    return '; '.join(out)


M['reason'] = [reason(r) if r.excluded else '' for r in M.itertuples()]
M['regime'] = np.where(M.mi < BREAK, 'before 2018-08 break', 'after break')
rule_fired = set(M.mi[M.outage_rule | M.flood_rule_high])
assert rule_fired == EXCL, (sorted(map(ym_of, rule_fired)), sorted(map(ym_of, EXCL)))   # the written reasons match the rules
log('median-jump months:', [ym_of(m) for m in sorted(JUMP)])
log('excluded months (outage or flood):', sorted(ym_of(m) for m in EXCL), '| Test A rule alone fires on', [ym_of(m) for m in M.mi[M.test_a_rule_low]])

# ---------------------------------------------------------------- rows
rows = []
n_drop_elig = 0
for m in ORIGINS:
    if m in EXCL or (m + 1) in EXCL:
        continue
    j = int(m - MI[0])
    if j < 11 or j + 1 >= len(MI):
        continue
    win = A[:, j - 11:j + 1].copy()
    win[:, ex_mask[j - 11:j + 1]] = np.nan
    s12 = np.nansum(win, axis=1)
    present = s12 >= MIN12
    w6 = A[:, j - 5:j + 1].copy()
    w6[:, ex_mask[j - 5:j + 1]] = np.nan
    M6 = np.nanmedian(w6, axis=1)
    m12 = np.nanmean(win, axis=1)
    Lt, Lnext = A[:, j], A[:, j + 1]
    Lt1 = np.nan_to_num(A[:, j - 1])
    if ex_mask[j - 1]:
        Lt1 = np.full(len(A), np.nan, np.float32)
    Lya = np.nan_to_num(A[:, j - 11])
    if ex_mask[j - 11]:
        Lya = np.full(len(A), np.nan, np.float32)
    base_ok = ~np.isnan(M6) & ~np.isnan(Lnext) & ~np.isnan(Lt)
    n_drop_elig += int((base_ok & ~present).sum())
    keep = present & base_ok
    if not keep.any():
        continue
    k = np.where(keep)[0]
    reg = 0 if m + 1 < BREAK else (1 if m - 11 < BREAK else 2)
    rows.append(pd.DataFrame({
        'book_id': np.array(BOOKS)[k], 'mi': m,
        'L_t': Lt[k], 'L_next': Lnext[k], 'M6': M6[k].astype(np.float32),
        'h_lt': np.log1p(Lt[k]), 'h_lt1': np.log1p(Lt1[k]), 'h_m6': np.log1p(M6[k]).astype(np.float32),
        'h_m12': np.log1p(m12[k]).astype(np.float32), 'h_lyago': np.log1p(Lya[k]),
        'h_age': (m - pub_use[k]).astype(np.float32), 'h_age_obs': (m - first_pos[k]).astype(np.float32),
        'n_rec': NREC[k, j], 'regime': np.int8(reg), 'flag_jump': np.int8(int(m in JUMP or (m + 1) in JUMP))}))
R = pd.concat(rows, ignore_index=True)
del rows
R['D'] = np.log1p(R.L_next) - np.log1p(R.M6)
R['Sg'] = ((R.D >= np.log(2)) & (R.L_next - R.M6 >= 5)).astype(int)
R['Y'] = np.log1p(R.L_next)
lk_b = L[['book_article', 'author_article', 'book_src', 'author_src']].rename(columns={'book_article': 'article', 'book_src': 'b_src', 'author_src': 'a_src'})
R = R.merge(lk_b, left_on='book_id', right_index=True, how='left')
FB = FBW.drop(columns='src').rename(columns={c: 'b_' + c for c in FEATS})
FA = FAW.drop(columns='src').rename(columns={c: 'a_' + c for c in FEATS})
R = R.merge(FB, on=['article', 'mi'], how='left')
R = R.merge(FA.rename(columns={'article': 'author_article'}), on=['author_article', 'mi'], how='left')
R['year'] = (R.mi + 1) // 12                                             # year of the target month
R['test_year'] = R['year']
cols = (['book_id', 'mi', 'L_t', 'L_next', 'M6', 'h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'D', 'Sg', 'Y', 'article', 'author_article']
        + ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS] + ['year', 'test_year', 'h_age_obs', 'n_rec', 'regime', 'flag_jump', 'b_src', 'a_src'])
R = R[cols]
R['b_src'] = R.b_src.astype(np.int8)
R['a_src'] = R.a_src.astype(np.int8)
R.to_parquet(OUT / 'test_e_rows.parquet', index=False)
log('rows', R.shape, 'origins', R.mi.nunique(), 'first', ym_of(R.mi.min()), 'last', ym_of(R.mi.max()), '| dropped by the 24-listen rule', n_drop_elig)

# platform-level outcome statistics by origin month (counts and base rates only)
g = R.groupby('mi')
M = M.merge(pd.DataFrame({'rows_as_origin': g.size(), 'median_D': g.D.median(), 'share_Sg': g.Sg.mean()}).reset_index().rename(columns={'mi': 'mi'}), on='mi', how='left')
M.to_csv(OUT / 'test_e_months.csv', index=False)

# ---------------------------------------------------------------- the links table and the list of articles still needed
L['rows'] = R.groupby('book_id').size().reindex(L.index).fillna(0).astype(int)
L.reset_index().to_parquet(OUT / 'test_e_links.parquet', index=False)

mon_books = json.load(open(D / 'raw' / 'wiki_pageviews_monthly.json'))
mon_auth = json.load(open(D / 'raw' / 'wiki_author_pageviews_monthly.json'))
mon_have = {k.replace('_', ' ') for k in mon_books} | set(mon_auth)
need = []
for kind, col, srccol in [('book', 'book_article', 'book_src'), ('author', 'author_article', 'author_src')]:
    x = L[L[col].notna() & (L[srccol] == 0)]
    t = x.groupby(col).agg(n_books=('title', 'size'), listens_total=('listens_total', 'sum'), n_rows=('rows', 'sum')).reset_index().rename(columns={col: 'article'})
    t.insert(0, 'kind', kind)
    need.append(t)
NEED = pd.concat(need, ignore_index=True)
NEED['api_title'] = NEED.article.str.replace(' ', '_')
NEED['title_has_parenthesis'] = NEED.article.str.contains(r'\(')
NEED['monthly_views_stored'] = NEED.article.isin(mon_have)
NEED['listens_total'] = NEED.listens_total.astype(np.int64)
NEED = NEED.sort_values(['kind', 'listens_total'], ascending=[True, False]).reset_index(drop=True)
NEED['priority_in_kind'] = NEED.groupby('kind').cumcount() + 1
NEED = NEED[['kind', 'priority_in_kind', 'article', 'api_title', 'n_books', 'n_rows', 'listens_total', 'title_has_parenthesis', 'monthly_views_stored']]
NEED.to_csv(OUT / 'test_e_articles_needed.csv', index=False)
log('articles still needed', len(NEED), NEED.kind.value_counts().to_dict())

# ---------------------------------------------------------------- cross-check of listening.parquet against the raw monthly file
V = json.load(open(D / 'raw' / 'ia_views_monthly.json'))
pm = {ym_of(m): f'{m // 12}{m % 12 + 1:02d}' for m in MI}
cols_raw = [pm[p] for p in P.columns]
bad = 0
for b, g_ in lk.groupby('book_id'):
    s = np.zeros(len(cols_raw))
    for i in g_.identifier:
        d = V[i]
        s += np.array([d.get(c, 0) for c in cols_raw], float)
    if not np.array_equal(s, A0[bidx[b]].astype(float)):
        bad += 1
sample_views = sum(sum(d.get(c, 0) for c in cols_raw) for i, d in V.items() if i in sample_ids)
all_views = sum(sum(d.get(c, 0) for c in cols_raw) for d in V.values())
tot_raw_sep = sum(d.get('202609', 0) for d in V.values())
tot_raw_aug = sum(d.get('202608', 0) for d in V.values())
raw_last = max(max(d) for d in V.values())
del V
gc.collect()
log('listening.parquet vs raw monthly file: books that differ', bad, '| raw 2026-09 over 2026-08', round(tot_raw_sep / tot_raw_aug, 3))

STATE = dict(sample_share_of_views=sample_views / all_views, check=check, n_listen_rows=n_listen_rows, n_rec_all=n_rec_all, n_rec_minus1=n_rec_minus1, n_drop_elig=n_drop_elig,
             pre_pub_cells=pre_pub_cells, bad_vs_raw=bad, raw_sep_over_aug=tot_raw_sep / tot_raw_aug, raw_last=raw_last,
             n_sample=n_sample, excluded={ym_of(k): v for k, v in zip(M.mi[M.excluded], M.reason[M.excluded])})
(OUT / 'test_e_build_info.json').write_text(json.dumps(STATE, indent=1, default=float))
log('done; seconds', round(time.time() - T0))
