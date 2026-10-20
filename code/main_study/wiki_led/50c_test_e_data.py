# 50c. Test E (another platform), data only, CORRECTED RERUN: 50_test_e_data.py with correction A1 of addendum e
# (prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json, 20 Oct 2026 20:34 +07). Addendum e did not name Test E; this rerun
# is for consistency with it (prereg/DEVIATIONS.md, section "Wikipedia-led tests", entry of 20 Oct 2026 21:45 +07). The original run and
# its files stay on file.
# The only change in the build is inside article_features(), exactly as in 10c_test_a.py: the weeks before an article's first week with
# at least one view (views > 0) are missing, not zero. They are removed from the weekly series before any rolling computation, so every
# feature of an origin month that ends before that first week is missing and every later feature is computed from the article's own
# weeks only; an article with no view in any week gets no features. This covers the Study 2R book and author series and the book series
# built from the raw daily file. Nothing else in the rows, links, months, flags or settings changed. One line of bookkeeping follows:
# b_src and a_src (the source of an article's stored weekly series, 0 = none stored) are read from the stored series themselves instead
# of the feature table, so that an article with a stored series but no corrected feature keeps its source (same values as the original
# run, checked below through the links table).
# Checks added (written to data/db/wiki_led/test_e_build_info_c.json and the log; the script stops if one fails):
#   check 1 compares this copy of the corrected function with the corrected Test A features (test_a_wiki_features_c.parquet made by
#     10c_test_a.py) on the same input series, including which origin months have features;
#   check 3 (A1): the original article_features, read with ast from 50_test_e_data.py itself, run on today's inputs must reproduce the
#     stored original features (test_e_wiki_features.parquet) exactly; then, for every article whose first week with views is the first
#     week of its stored series, the corrected features must equal the original ones exactly (same origin months, same values, NaN equal
#     to NaN, no tolerance); for the other articles the differences are counted;
#   check 4: the rows equal the original rows (test_e_rows.parquet) in every column except the 18 Wikipedia features, in the same order;
#     the links table, the months table and the list of articles still needed equal the stored originals (so they are not written again).
# Output (data/db/wiki_led/): test_e_rows_c.parquet, test_e_wiki_features_c.parquet, test_e_build_info_c.json.
#   bash jobs/bg.sh wl_test_e_c main_study/wiki_led/50c_test_e_data.py        (from handoff/; about 30 seconds, under 1 GB)
#
# Original header of 50_test_e_data.py:
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
#       Option --raw-hist: h_lt1 and h_lyago keep the recorded value of an excluded month, as Test A and Test D do (output
#       test_e_rows_rawhist.parquet; the default sets them missing).
#   (4) Excluded months (not an origin or target; missing inside M6, the 12-month mean, the eligibility sum, h_lt1 and h_lyago):
#       2023-12 and 2024-10 (Internet Archive outages: at least 3 days of the 887-recording daily sample under half of the local
#       median) and 2025-01 (a one-day flood: month total more than twice its trailing 12-month median). Test A's half-of-median
#       rule is computed for every month and shown in test_e_months.csv, but it also fires on 2018-11 and 2018-12 because the
#       platform level halved on 2018-08-02, which is not missing data; those two months stay in (flag regime).
#   (5) h_age is Test A's formula (months since the first month with listens > 0 in this panel, which is 2017-01 for every book
#       that was public before 2017); h_age_pub is the true age (months since the book's first public month, the earliest
#       Internet Archive public date of its recordings). regime flags the 2018-08 level break.
#   (6) flag_jump = 1 when the origin month or its target month is a month in which the median listens of the books already public in
#       2017-01 moved by a factor of 1.5 or more from the previous month (platform-wide traffic, not demand for single books). It looks
#       at the target month's platform median and is a filter for scoring, never a feature.
# Output (data/db/wiki_led/): test_e_rows.parquet, test_e_links.parquet, test_e_months.csv, test_e_wiki_features.parquet,
#         test_e_articles_needed.csv, test_e_build_info.json. The report data/reports/wiki_led_test_e_data.md and the independent
#         checks of the rows are made by 51_test_e_report.py, which must be run after this script.
#   nice ../.venv/bin/python main_study/wiki_led/50_test_e_data.py     (from code/; about 30 seconds, under 1 GB)
import sys, os, io, ast, json, time, pathlib, gc, warnings, re, unicodedata, resource, hashlib
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

RAW_HIST = '--raw-hist' in sys.argv
D = pathlib.Path(D)
ROOT = D.parent
OUT = D / 'db' / 'wiki_led'
OUT.mkdir(parents=True, exist_ok=True)
T0 = time.time()
ADD_E = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_e_corrections_robustness.json'
assert hashlib.sha256(ADD_E.read_bytes()).hexdigest() == '36f3605286b51b8123d791c1d59a7dc89356ec3bb66bfba6b9667327d31b3e52', 'addendum e changed'
os.nice(5)                                                               # machine rule: nice, one heavy job at a time


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def peak_mb():                                                           # macOS reports ru_maxrss in bytes
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20


def mi_of(ym):  # 'YYYY-MM' -> month index year*12 + month-1
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def ym_of(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


def month_end(mi):
    y, m = divmod(mi, 12)
    return pd.Timestamp(year=y, month=m + 1, day=1) + pd.offsets.MonthEnd(0)


ORIG0, ORIG1 = mi_of('2016-03'), mi_of('2026-07')    # the origins of Test A
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
minus1_listens = int(lis.listens[lis.book_id == '-1'].sum())
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
L['book_title_tag_nonbook'] = L.book_article.str.contains(r'\((?:[^)]*\b)?(?:film|play|opera|musical|TV|television|miniseries|series|ballet|song|album|comics|graphic novel|game|radio|drama|movie)\b[^)]*\)$', case=False, na=False)
L['author_article_paren'] = L.author_article.str.contains(r'\(', na=False)
HON = {'sir', 'saint', 'st', 'captain', 'dr', 'rev', 'reverend', 'the', 'mr', 'mrs', 'lord', 'lady', 'father', 'professor', 'prof', 'general', 'colonel'}


def name_key(x):
    """A name without accents, parentheses, punctuation, honorifics and initials, for a cheap same-person check."""
    if not isinstance(x, str):
        return None
    x = unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode().lower()
    x = re.sub(r'\([^)]*\)', ' ', x)
    x = re.sub(r"[^a-z0-9' ]", ' ', x)
    return ' '.join(t for t in x.split() if len(t) > 1 and t not in HON)


L['author_name_exact'] = [(name_key(a) == name_key(t)) if isinstance(t, str) else None for a, t in zip(L.author, L.author_article)]
L['author_name_exact'] = L.author_name_exact.astype('boolean')
L['author_link_clean'] = (L.author_name_exact == True) & ~L.author_article_paren          # same name and no disambiguator
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


# ---------------------------------------------------------------- article_features: the corrected function of 10c_test_a.py (A1)
ORIGINS = np.arange(ORIG0, ORIG1 + 1)
ENDS = np.array([month_end(m) for m in ORIGINS], dtype='datetime64[ns]')
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']


def article_features(g):
    g = g.set_index('week').sort_index()
    # A1 (addendum e): weeks before the article's first week with at least one view are missing, not zero.  They are removed
    # here, before any rolling computation.  An article with no view in any week has no weeks left and gets no features (None).
    seen = (g['views'] > 0).to_numpy()
    if not seen.any():
        return None
    g = g.iloc[int(seen.argmax()):]
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


def features_of(frames, fn=None):
    fn = article_features if fn is None else fn
    parts = []
    for a, g in frames.groupby('article', sort=False):
        h = fn(g)
        if h is None or len(h) == 0:                                         # A1: no view at all, or first view after the last origin month
            continue
        h.insert(0, 'article', a)
        parts.append(h)
    return pd.concat(parts, ignore_index=True)


# book articles: Study 2R series where present, else the raw daily series; author articles: Study 2R series
s2_book_titles = set(WB_s2.article.unique())
raw_only = sorted(raw_titles - s2_book_titles)
RAWW = pd.concat([weekly_from_daily(t, raw_daily[t]) for t in raw_only], ignore_index=True)
FB_s2, FA_s2 = features_of(WB_s2), features_of(WA_s2)


def late_articles(frames, cut='2017-06-01'):
    """Articles whose first week with views is after the cut: before it their weekly share is a stored zero (as in Test A)."""
    f = frames[frames.views > 0].groupby('article').week.min()
    return int((f > pd.Timestamp(cut)).sum()), int(len(f))


LATE = dict(book_study2r=late_articles(WB_s2), book_raw=late_articles(RAWW), author=late_articles(WA_s2))
FB_raw = features_of(RAWW)
log('features: study2r book', FB_s2.article.nunique(), 'raw book', FB_raw.article.nunique(), 'author', FA_s2.article.nunique())


def same(a, b):
    """Exact equality with NaN equal to NaN."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return (a == b) | (np.isnan(a) & np.isnan(b))


def same_tol(a, b, tol=1e-9):
    """Equal up to floating-point rounding (a rolling sum that starts in another week carries another rounding error)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return np.isclose(a, b, rtol=tol, atol=tol) | (np.isnan(a) & np.isnan(b))


# check 1: this copy of the corrected function reproduces the corrected features stored for Test A (same input series)
TA = pq.read_table(OUT / 'test_a_wiki_features_c.parquet', filters=[('article', 'in', sorted(want_b | want_a))]).to_pandas()
check = {}
for name, F, kind in [('study2r_book', FB_s2, 'book'), ('study2r_author', FA_s2, 'author')]:
    ta = TA[TA.kind == kind].drop(columns='kind')
    m = F.merge(ta, on=['article', 'mi'], suffixes=('', '_ta'))
    dmax = max(float(np.nanmax(np.abs(m[c] - m[c + '_ta']))) for c in FEATS)
    nanmis = int(sum((m[c].isna() != m[c + '_ta'].isna()).sum() for c in FEATS))
    common = set(F.article) & set(ta.article)
    o = F[F.article.isin(common)][['article', 'mi']].merge(ta[ta.article.isin(common)][['article', 'mi']], how='outer', indicator=True)
    check[name] = dict(articles=int(m.article.nunique()), rows=int(len(m)), max_abs_diff=dmax, nan_mismatch=nanmis,
                       origin_months_only_here=int((o._merge == 'left_only').sum()), origin_months_only_in_test_a=int((o._merge == 'right_only').sum()))
assert all(v['max_abs_diff'] == 0 and v['nan_mismatch'] == 0 and v['origin_months_only_here'] == 0 and v['origin_months_only_in_test_a'] == 0
           for v in check.values()), check
del TA
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
                               nan_mismatch_without_redirects=int(sum((m[c].isna() != m[c + '_s2'].isna())[no_red].sum() for c in FEATS)),
                               share_cells_differing_with_redirects=float((dd_[~no_red] > 1e-9).values.mean()) if (~no_red).any() else 0.0)
log('feature checks', json.dumps(check))
del FB_raw_both, m, dd_


# check 3 (A1): the corrected features against the original ones
def load_original_article_features():
    """article_features of 50_test_e_data.py itself, with the constants it uses, read with ast and run here (nothing else of that
    script runs), so that the comparison is with the original code and not with a copy of it."""
    path = pathlib.Path(__file__).resolve().parent / '50_test_e_data.py'
    keep = []
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.FunctionDef) and node.name in ('mi_of', 'month_end', 'article_features'):
            keep.append(node)
        elif isinstance(node, ast.Assign):
            names = {n.id for t in node.targets for n in ast.walk(t) if isinstance(n, ast.Name)}
            if names & {'ORIG0', 'ORIG1', 'EPS', 'ORIGINS', 'ENDS', 'FEATS'}:
                keep.append(node)
    ns = {'np': np, 'pd': pd}
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(path), 'exec'), ns)
    assert ns['FEATS'] == FEATS and ns['EPS'] == EPS and np.array_equal(ns['ORIGINS'], ORIGINS) and np.array_equal(ns['ENDS'], ENDS)
    return ns['article_features']


orig_features = load_original_article_features()
WF0 = pd.read_parquet(OUT / 'test_e_wiki_features.parquet')                  # the stored features of the original run (20 Oct 17:58)
A1CHECK = {}
for name, kind, src, frames, Fc in [('book_study2r', 'book', 1, WB_s2, FB_s2), ('book_raw', 'book', 2, RAWW, FB_raw),
                                    ('author_study2r', 'author', 1, WA_s2, FA_s2)]:
    F0 = WF0[(WF0.kind == kind) & (WF0.src == src)].drop(columns=['kind', 'src'])
    Fo = features_of(frames, orig_features)                                  # the original code on today's inputs
    k = F0.merge(Fo, on=['article', 'mi'], how='outer', suffixes=('', '_o'), indicator=True)
    reproduces = bool((k._merge == 'both').all() and all(same(k[c], k[c + '_o']).all() for c in FEATS))
    wk_first = frames.groupby('article').week.min()                          # first week of the article's stored series
    wk_view = frames[frames.views > 0].groupby('article').week.min().reindex(wk_first.index)
    g1 = set(wk_first.index[wk_view == wk_first])                            # first view in the first week of the series
    gl = set(wk_first.index[wk_view > wk_first])                             # first view later
    g0 = set(wk_first.index[wk_view.isna()])                                 # no view at all
    m = F0.merge(Fc, on=['article', 'mi'], how='outer', suffixes=('', '_c'), indicator=True)
    eq = np.logical_and.reduce([same(m[c], m[c + '_c']) for c in FEATS])
    eqt = np.logical_and.reduce([same_tol(m[c], m[c + '_c']) for c in FEATS])
    bothm = (m._merge == 'both').to_numpy()
    i1, il = m.article.isin(g1).to_numpy(), m.article.isin(gl).to_numpy()
    last = m[il & bothm & ~eqt].groupby('article').mi.max()                 # last origin month that differs beyond rounding
    wks = np.array([(month_end(int(mi)) - wk_view[a]).days / 7 for a, mi in last.items()]) if len(last) else np.array([np.nan])
    A1CHECK[name] = dict(
        original_code_reproduces_stored_original_file=reproduces,
        first_week_of_series=str(wk_first.min().date()) + ' to ' + str(wk_first.max().date()),
        articles=int(len(wk_first)), articles_first_view_in_first_week=len(g1), articles_first_view_later=len(gl), articles_without_view=len(g0),
        first_week_rows_original=int((i1 & (m._merge != 'right_only').to_numpy()).sum()), first_week_rows_corrected=int((i1 & (m._merge != 'left_only').to_numpy()).sum()),
        first_week_rows_only_in_one_file=int((i1 & ~bothm).sum()), first_week_rows_differing=int((i1 & bothm & ~eq).sum()),
        later_rows_original=int((il & (m._merge != 'right_only').to_numpy()).sum()), later_rows_corrected=int((il & (m._merge != 'left_only').to_numpy()).sum()),
        later_rows_without_corrected_features=int((il & (m._merge == 'left_only').to_numpy()).sum()),
        later_rows_only_corrected=int((il & (m._merge == 'right_only').to_numpy()).sum()),
        later_rows_identical=int((il & bothm & eq).sum()), later_rows_equal_within_1e9=int((il & bothm & eqt & ~eq).sum()),
        later_rows_differing=int((il & bothm & ~eqt).sum()), later_articles_with_a_differing_row=int(len(last)),
        later_weeks_after_first_view_of_last_differing_row=dict(median=float(np.nanmedian(wks)), max=float(np.nanmax(wks))),
        no_view_articles_rows_original=int(m.article.isin(g0).sum()),
        rows_only_corrected_any=int((m._merge == 'right_only').sum()))
    log('A1 check', name, json.dumps(A1CHECK[name]))
assert all(v['original_code_reproduces_stored_original_file'] for v in A1CHECK.values()), 'inputs or original code changed'
assert all(v['first_week_rows_only_in_one_file'] == 0 and v['first_week_rows_differing'] == 0 and v['rows_only_corrected_any'] == 0
           for v in A1CHECK.values()), 'first-week articles differ'
del RAWW, WF0, F0, Fo, k, m
gc.collect()

FBW = pd.concat([FB_s2.assign(src=1), FB_raw.assign(src=2)], ignore_index=True)
FAW = FA_s2.assign(src=1)
WFcache = pd.concat([FBW.assign(kind='book'), FAW.assign(kind='author')], ignore_index=True)
WFcache.to_parquet(OUT / 'test_e_wiki_features_c.parquet', index=False)
# source of the stored weekly series (1 Study 2R, 2 raw daily file), read from the series themselves (see the header)
b_src = {**{a: 1 for a in s2_book_titles}, **{a: 2 for a in raw_only}}
a_src = {a: 1 for a in set(WA_s2.article.unique())}
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
    j12 = np.array([d.get('2025-01-12', 0) for d in Lr.values()], float)
    flood = dict(jan12_share_over_100=float((j12 > 100).mean()), jan12_max=float(j12.max()), jan12_n_recordings=int(len(j12)))
    del Lr
    return pd.Series(tt, index=pd.date_range('2017-01-01', periods=n)), nrec, ids, flood


DS, n_sample, sample_ids, FLOOD = daily_sample()
sample_last_day = str(DS[DS > 0].index.max().date())                     # last day the Internet Archive API had data (the pull was on 12 Oct 2026)
break_ratio = float(DS.loc['2018-08-03':'2018-08-31'].mean() / DS.loc['2018-07-01':'2018-07-31'].mean())   # level after / before the 2018-08-02 break
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
M['regime_label'] = np.where(M.mi < BREAK, 'before the 2018-08 break', 'after the break')
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
    if ex_mask[j - 1] and not RAW_HIST:
        Lt1 = np.full(len(A), np.nan, np.float32)
    Lya = np.nan_to_num(A[:, j - 11])
    if ex_mask[j - 11] and not RAW_HIST:
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
        'h_age': (m - first_pos[k]).astype(np.float32), 'h_age_pub': (m - pub_use[k]).astype(np.float32),
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
R['has_book_page'] = R.article.notna().astype(np.int8)                   # a book article is linked (views stored or not: see b_src)
R['has_author_page'] = R.author_article.notna().astype(np.int8)
cols = (['book_id', 'mi', 'L_t', 'L_next', 'M6', 'h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'D', 'Sg', 'Y', 'article', 'author_article']
        + ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS] + ['year', 'test_year', 'h_age_pub', 'n_rec', 'regime', 'flag_jump', 'has_book_page', 'has_author_page', 'b_src', 'a_src'])
R = R[cols]
R['b_src'] = R.b_src.astype(np.int8)
R['a_src'] = R.a_src.astype(np.int8)
R['mi'] = R.mi.astype(np.int32)
R['year'] = R.year.astype(np.int16)
R['test_year'] = R.test_year.astype(np.int16)
R['Sg'] = R.Sg.astype(np.int8)
assert R.duplicated(['book_id', 'mi']).sum() == 0
ROWS_FILE = OUT / ('test_e_rows_rawhist_c.parquet' if RAW_HIST else 'test_e_rows_c.parquet')
R.to_parquet(ROWS_FILE, index=False)
assert (np.diff(R.mi.values) >= 0).all()
log('rows', R.shape, 'origins', R.mi.nunique(), 'first', ym_of(R.mi.min()), 'last', ym_of(R.mi.max()), '| dropped by the 24-listen rule', n_drop_elig)

# check 4a: the rows equal the original rows except in the 18 Wikipedia features
WCOLS = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS]
ROWS0 = OUT / ('test_e_rows_rawhist.parquet' if RAW_HIST else 'test_e_rows.parquet')
ROWCHECK = {'original_rows_file': ROWS0.name, 'available': ROWS0.exists()}
if ROWS0.exists():
    R0 = pd.read_parquet(ROWS0)
    assert list(R0.columns) == list(R.columns) and len(R0) == len(R), 'row layout differs'
    other = {}
    for c in R.columns:
        if c in WCOLS:
            continue
        a, b = R0[c], R[c]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            ok_ = same(a, b) & (a.dtype == b.dtype)
        else:                                                            # text columns (pandas 3 string dtype)
            na_a, na_b = a.isna().to_numpy(), b.isna().to_numpy()
            ok_ = (na_a & na_b) | (~na_a & ~na_b & (a.fillna('').astype(str).to_numpy() == b.fillna('').astype(str).to_numpy()))
        other[c] = int((~ok_).sum())
    wsame = np.logical_and.reduce([same(R0[c], R[c]) for c in WCOLS])
    ROWCHECK.update(
        rows=int(len(R)), same_order=bool((R0.book_id.to_numpy() == R.book_id.to_numpy()).all() and (R0.mi.to_numpy() == R.mi.to_numpy()).all()),
        other_columns_differing_values={c: v for c, v in other.items() if v}, other_columns_compared=len(other),
        rows_with_a_differing_wikipedia_value=int((~wsame).sum()),
        cells_differing={c: int((~same(R0[c], R[c])).sum()) for c in WCOLS},
        cells_finite_to_missing={c: int((R0[c].notna() & R[c].isna()).sum()) for c in WCOLS},
        cells_missing_to_finite={c: int((R0[c].isna() & R[c].notna()).sum()) for c in WCOLS},
        share_rows_b_lvl4_present=dict(original=float(R0.b_lvl4.notna().mean()), corrected=float(R.b_lvl4.notna().mean())),
        share_rows_a_lvl4_present=dict(original=float(R0.a_lvl4.notna().mean()), corrected=float(R.a_lvl4.notna().mean())),
        rows_with_stored_series_but_no_feature=dict(
            book=dict(original=int(((R0.b_src > 0) & R0.b_lvl4.isna()).sum()), corrected=int(((R.b_src > 0) & R.b_lvl4.isna()).sum())),
            author=dict(original=int(((R0.a_src > 0) & R0.a_lvl4.isna()).sum()), corrected=int(((R.a_src > 0) & R.a_lvl4.isna()).sum()))))
    del R0
    gc.collect()
    log('rows against the original rows', json.dumps({k: v for k, v in ROWCHECK.items() if k not in ('cells_differing', 'cells_finite_to_missing', 'cells_missing_to_finite')}))

# platform-level outcome statistics by origin month (counts and base rates only)
g = R.groupby('mi')
M = M.merge(pd.DataFrame({'rows_as_origin': g.size(), 'median_D': g.D.median(), 'share_Sg': g.Sg.mean()}).reset_index().rename(columns={'mi': 'mi'}), on='mi', how='left')
SAME_AS_ORIGINAL = {}
SAME_AS_ORIGINAL['test_e_months.csv'] = M.to_csv(index=False) == (OUT / 'test_e_months.csv').read_text()     # not written again

# ---------------------------------------------------------------- the links table and the list of articles still needed
L['rows'] = R.groupby('book_id').size().reindex(L.index).fillna(0).astype(int)
buf = io.BytesIO()
L.reset_index().to_parquet(buf, index=False)                            # the same round trip through parquet as the stored file
try:
    pd.testing.assert_frame_equal(pd.read_parquet(io.BytesIO(buf.getvalue())), pd.read_parquet(OUT / 'test_e_links.parquet'))
    SAME_AS_ORIGINAL['test_e_links.parquet'] = True
except AssertionError as e:
    SAME_AS_ORIGINAL['test_e_links.parquet'] = False
    log('links table differs from the original:', str(e)[:500])

mon_books = json.load(open(D / 'raw' / 'wiki_pageviews_monthly.json'))
mon_auth = json.load(open(D / 'raw' / 'wiki_author_pageviews_monthly.json'))
mon_have = {k.replace('_', ' ') for k in mon_books} | set(mon_auth)
need = []
for kind, col, srccol in [('book', 'book_article', 'book_src'), ('author', 'author_article', 'author_src')]:
    x = L[L[col].notna() & (L[srccol] == 0)].copy()
    x['name_exact'] = x.author_name_exact if kind == 'author' else pd.array([None] * len(x), dtype='boolean')
    x['tag_nonbook'] = x.book_title_tag_nonbook if kind == 'book' else False
    top = x.sort_values('listens_total', ascending=False).drop_duplicates(col)      # the most listened book that uses the article
    t = x.groupby(col).agg(n_books=('title', 'size'), listens_total=('listens_total', 'sum'), n_rows=('rows', 'sum')).reset_index().rename(columns={col: 'article'})
    t = t.merge(top[[col, 'author', 'title', 'name_exact', 'tag_nonbook']].rename(columns={col: 'article', 'author': 'lv_author', 'title': 'lv_title'}), on='article')
    t.insert(0, 'kind', kind)
    need.append(t)
NEED = pd.concat(need, ignore_index=True)
NEED['api_title'] = NEED.article.str.replace(' ', '_')
NEED['title_has_parenthesis'] = NEED.article.str.contains(r'\(')
NEED['monthly_views_stored'] = NEED.article.isin(mon_have)
NEED['listens_total'] = NEED.listens_total.astype(np.int64)
NEED['likely_ok'] = np.where(NEED.kind == 'author', NEED.name_exact.fillna(False).astype(bool) & ~NEED.title_has_parenthesis, ~NEED.tag_nonbook.astype(bool))
NEED = NEED.sort_values(['kind', 'listens_total'], ascending=[True, False]).reset_index(drop=True)
NEED['priority_in_kind'] = NEED.groupby('kind').cumcount() + 1
NEED['name_exact'] = NEED.name_exact.astype('boolean')
NEED = NEED[['kind', 'priority_in_kind', 'article', 'api_title', 'lv_author', 'lv_title', 'n_books', 'n_rows', 'listens_total', 'likely_ok',
             'name_exact', 'title_has_parenthesis', 'tag_nonbook', 'monthly_views_stored']]
SAME_AS_ORIGINAL['test_e_articles_needed.csv'] = NEED.to_csv(index=False) == (OUT / 'test_e_articles_needed.csv').read_text()
log('articles still needed', len(NEED), NEED.kind.value_counts().to_dict(), '| same as the original files:', SAME_AS_ORIGINAL)

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

later = lk[lk.pub_mi.notna() & (lk.pub_mi >= MI[0]) & (lk.pub_mi > lk.book_id.map(pub_first))]   # recordings public after their book's first public month, inside the window
groups_new_rec = int(later.book_id.nunique())
new_rec_events = int(len(later))
STATE = dict(late_articles=LATE, flood=FLOOD, zero_cells=int((A0 == 0).sum()), minus1_listens=minus1_listens, sample_last_day=sample_last_day, break_ratio=break_ratio, groups_new_recording_in_window=groups_new_rec, new_recordings_in_window=new_rec_events,
             pub_min=str(pub.min().date()), pub_max=str(pub.max().date()), recordings_without_date=int(lk.pub_mi.isna().sum()),
             runtime_s=round(time.time() - T0), peak_rss_mb=round(peak_mb()), rows_file=ROWS_FILE.name, sample_share_of_views=sample_views / all_views, check=check, n_listen_rows=n_listen_rows, n_rec_all=n_rec_all, n_rec_minus1=n_rec_minus1, n_drop_elig=n_drop_elig,
             pre_pub_cells=pre_pub_cells, bad_vs_raw=bad, raw_sep_over_aug=tot_raw_sep / tot_raw_aug, raw_last=raw_last,
             n_sample=n_sample, excluded={ym_of(k): v for k, v in zip(M.mi[M.excluded], M.reason[M.excluded])},
             correction='A1 of addendum e: weeks before the first week with views > 0 are missing; everything else as 50_test_e_data.py',
             a1_check=A1CHECK, rows_check=ROWCHECK, same_as_original_files=SAME_AS_ORIGINAL,
             articles_without_corrected_features=dict(
                 book_study2r=sorted(s2_book_titles - set(FB_s2.article)), book_raw=sorted(set(raw_only) - set(FB_raw.article)),
                 author_study2r=sorted(set(WA_s2.article.unique()) - set(FA_s2.article))))
if not RAW_HIST:
    (OUT / 'test_e_build_info_c.json').write_text(json.dumps(STATE, indent=1, default=float))
assert all(SAME_AS_ORIGINAL.values()), SAME_AS_ORIGINAL
if ROWCHECK['available']:
    assert ROWCHECK['same_order'] and not ROWCHECK['other_columns_differing_values'], 'non-Wikipedia columns differ from the original rows'
log('done; seconds', round(time.time() - T0), '| peak memory MB', round(peak_mb()))
