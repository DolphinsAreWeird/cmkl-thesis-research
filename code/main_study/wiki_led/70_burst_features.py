#!/usr/bin/env python3
"""70. Burst-shape and noise features for the book and author articles (data only: no model is fitted, nothing is related to loans).

Specification: paper/lit_search/Improvement_Methods_2026-10-20.md, Section 3, change 2; binding adjustments in
prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json (read-only).  same_name and other_r4 are not built here (they need the REST API).

Units: the 7,427 book articles and 3,065 author articles in data/db/study2r/works.parquet, at every origin month mi = year*12 + month - 1
from 2016-03 to 2026-09 (127 origins).  Every feature uses only days up to the last day of the origin month.

Daily series
  book article    = daily user views of the canonical title plus the redirects kept by the Study 2R screen (data/db/study2r/redirect_screen.parquet,
                    keep = True), exactly as the weekly series of Test A (study2r/04_weekly_series.py);
  author article  = daily user views of the title itself (no redirects), as in Test A.
  share           = daily views divided by the day's total English Wikipedia user views (data/db/interest/wiki/total_daily.parquet).
  Days missing from a file count as 0 views.  Window = the last 28 days of the origin month (day 1 = the last day of the month).
  Normal = the median daily share of days 29 to 210 before the month end (the 182 days just before the window), the daily version of the Test A
  normal (median of the 26 weeks before the last 4 weeks).  Log ratios use Test A's floor: ln((x + 1e-12) / (normal + 1e-12)).

Scale rule (one rule for all features): shares wherever a level is compared with a baseline or with another article (pre7, dec, hi28, rec, corr28);
raw daily views inside one article's own last 28 days (pk28, dpk, and the choice of the peak day).

Features
  pk28    largest day (views) divided by the sum of the last 28 days (views)               missing when the window has no views
  dpk     days from the peak to the month end (0 = peak on the last day); the peak is the day with most views, the latest one when tied
  pre7    ln(mean share of the 7 days before the peak / normal)
  dec     ln(mean share of up to 7 days after the peak / share on the peak day); missing when the peak is on the last 2 days (dpk < 2)
  hi28    number of the last 28 days with share >= 1.5 x normal
  rec     ln(largest share of the last 28 days / largest share on any earlier day since 2015-07-01), earlier = before the window
  top500  number of the last 28 days on which the article (book: title or a kept redirect) was in the English daily top 500 (data/raw/wiki_top_daily.json);
          days with no list in the file (11 days in 2016 to 2026) count as not listed; top500_lists says how many of the 28 days had a list
  corr28  Pearson correlation of the daily shares of the book and its author article over the last 28 days (books only; missing when either raw series
          is constant, when there is no author article series, or when book and author are the same page)
  co      1 when b_r4 and a_r4 (Test A weekly features, data/db/wiki_led/test_a_wiki_features.parquet) are both >= ln 1.5, else 0; missing when either is missing
          (books only).  Test A stops at origin 2026-07; for 2026-08 and 2026-09 r4 is computed here with the identical Test A formula from the weekly files
          and the run checks that the formula reproduces the stored r4 values.
  nrm0    1 when the normal is zero (the log ratios then rest on the 1e-12 floor, usually an article that did not exist yet)

Output: data/db/wiki_led/burst_features.parquet (article, kind, mi, features), burst_features_summary.json (coverage, quantiles, checks).
Run from handoff/code (full run, detached):   nice -n 10 bash ../jobs/bg.sh wl_burst main_study/wiki_led/70_burst_features.py
Options: --test N  uses N book articles (evenly spaced) and their authors, checks them against a plain pandas version, writes *_test files.
"""
import sys, re, json, time, gc, hashlib, collections
import numpy as np, pandas as pd
import resource
from _common import D, OUT, log as _log, T0


def peak_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6      # bytes on macOS


def log(*a):
    _log(f'[peak {peak_mb():.0f} MB]', *a)


S2R = D / 'db' / 'study2r'
PV = S2R / 'pv_daily'
EPS = 1e-12
DAYS = pd.date_range('2015-07-01', '2026-09-30', freq='D')
T = len(DAYS)
DAY0 = DAYS[0]
ORIGINS = np.arange(2016 * 12 + 2, 2026 * 12 + 9)          # 2016-03 to 2026-09
K = len(ORIGINS)
NAMES = ['pk28', 'dpk', 'pre7', 'dec', 'hi28', 'rec', 'top500', 'top500_lists', 'corr28', 'nrm0']
TEST = int(sys.argv[sys.argv.index('--test') + 1]) if '--test' in sys.argv else 0
SUF = '_test' if TEST else ''
CHUNK = 400
LN15 = float(np.log(1.5))


def fid(t):
    return hashlib.sha1(t.encode()).hexdigest()[:16]


def month_end(mi):
    y, m = divmod(int(mi), 12)
    return pd.Timestamp(year=y, month=m + 1, day=1) + pd.offsets.MonthEnd(0)


E = np.array([(month_end(m) - DAY0).days for m in ORIGINS])   # index in DAYS of the last day of each origin month
assert E[-1] == T - 1 and E[0] - 209 >= 0

# ---------------------------------------------------------------- daily totals
TOT = pd.read_parquet(D / 'db' / 'interest' / 'wiki' / 'total_daily.parquet').set_index('date').views.reindex(DAYS).astype(float)
assert TOT.notna().all() and (TOT > 0).all(), 'daily totals have gaps'
TOT = TOT.to_numpy()


def load_views(title):
    """daily views of one title on the DAYS grid (float64), or None when no file exists (a failed download)."""
    f = PV / f'{fid(title)}.parquet'
    if not f.exists():
        return None
    d = pd.read_parquet(f, columns=['date', 'views'])
    out = np.zeros(T)
    if len(d):
        i = (d['date'] - DAY0).dt.days.to_numpy()
        ok = (i >= 0) & (i < T)
        out[i[ok]] = d['views'].to_numpy()[ok]
    return out


# ---------------------------------------------------------------- units
W = pd.read_parquet(S2R / 'works.parquet', columns=['work_id', 'article', 'author_article'])
books = sorted(set(W.article.dropna()))
authors = sorted(set(W.author_article.dropna()))
b2a = W.dropna(subset=['author_article']).drop_duplicates('article').set_index('article').author_article.to_dict()
RS = pd.read_parquet(S2R / 'redirect_screen.parquet', columns=['canonical', 'redirect', 'keep'])
RS = RS[RS['keep'].fillna(False).astype(bool)]
kept = RS.groupby('canonical').redirect.apply(list).to_dict()
if TEST:
    step = max(1, len(books) // TEST)
    books = books[step // 2::step][:TEST]
    authors = sorted({b2a[b] for b in books if b in b2a} | set(authors[step // 2::step][:10]))
log(f'book articles {len(books)}, author articles {len(authors)}, books with kept redirects {sum(b in kept for b in books)}, origins {K}')

# ---------------------------------------------------------------- English daily top 500 (compact: title -> day indices)
want = {b.replace(' ', '_') for b in books} | {r.replace(' ', '_') for b in books for r in kept.get(b, [])} | {a.replace(' ', '_') for a in authors}


def iter_top_days(path):
    """(day key 'YYYYMMDD', list of [title, views]) one day at a time: the file is one 58 MB line, and json.load would hold about 1 GB of small lists."""
    txt = open(path, encoding='ascii').read()
    n_expected = txt.count('": [[')
    dec = json.JSONDecoder()
    pat = re.compile(r'\s*[{,]\s*"(\d{8})"\s*:\s*')
    pos, n = 0, 0
    while True:
        m = pat.match(txt, pos)
        if not m:
            break
        lst, pos = dec.raw_decode(txt, m.end())
        n += 1
        yield m.group(1), lst
    assert n == n_expected and txt[pos:].strip() == '}', 'wiki_top_daily.json was not read to the end'


TOPDAYS = collections.defaultdict(list)
LISTED = np.zeros(T, bool)
for key, lst in iter_top_days(D / 'raw' / 'wiki_top_daily.json'):
    di = (pd.Timestamp(key) - DAY0).days
    if di < 0 or di >= T:
        continue
    LISTED[di] = True
    for title, _ in lst:
        if title in want:
            TOPDAYS[title].append(di)
n_list_days = int(LISTED.sum())
log(f'top-500 lists: {n_list_days} days with a list, {len(TOPDAYS)} of our titles appear at least once')


def top_matrix(titles_per_row):
    """bool matrix (rows, T): the row's article (any of its titles) was in the top 500 that day."""
    B = np.zeros((len(titles_per_row), T), bool)
    for i, ts in enumerate(titles_per_row):
        for t in ts:
            ix = TOPDAYS.get(t.replace(' ', '_'))
            if ix:
                B[i, ix] = True
    return B


# ---------------------------------------------------------------- the feature block (vectorised over articles, loop over origins)
def block(V, B, VA=None, skip_corr=None):
    """V (n, T) raw daily views of the articles; B (n, T) top-500 flags; VA (n, T) raw views of each row's author article, or None.
    skip_corr (n,) bool: corr28 not defined for the row (no author series, or same page).  Returns {name: (n, K) float32}."""
    n = V.shape[0]
    S = V / TOT
    CM = np.maximum.accumulate(S, axis=1)
    SA = VA / TOT if VA is not None else None
    out = {k: np.full((n, K), np.nan, np.float32) for k in NAMES}
    r_ = np.arange(n)
    rows = r_[:, None]
    ar_before, ar_after = np.arange(-7, 0)[None, :], np.arange(1, 8)[None, :]
    cumL = np.cumsum(LISTED)
    for j, e in enumerate(E):
        wv, ws = V[:, e - 27:e + 1], S[:, e - 27:e + 1]
        nrm = np.median(S[:, e - 209:e - 27], axis=1)                  # days e-209 .. e-28: the 182 days before the window
        tot = wv.sum(1)
        pos = tot > 0
        off = wv[:, ::-1].argmax(1)                                   # days from the latest maximum to the month end
        p = e - off                                                   # index of the peak day
        with np.errstate(divide='ignore', invalid='ignore'):
            pk = np.where(pos, wv.max(1) / tot, np.nan)
            pre = np.log((S[rows, p[:, None] + ar_before].mean(1) + EPS) / (nrm + EPS))
            mask = ar_after <= off[:, None]
            aft = (S[rows, np.minimum(p[:, None] + ar_after, e)] * mask).sum(1) / np.maximum(mask.sum(1), 1)
            dec = np.log((aft + EPS) / (S[r_, p] + EPS))
            rec = np.log((ws.max(1) + EPS) / (CM[:, e - 28] + EPS))
        dec[off < 2] = np.nan
        out['pk28'][:, j] = pk
        out['dpk'][:, j] = np.where(pos, off, np.nan)
        out['pre7'][:, j] = np.where(pos, pre, np.nan)
        out['dec'][:, j] = np.where(pos, dec, np.nan)
        out['rec'][:, j] = np.where(pos, rec, np.nan)
        out['hi28'][:, j] = (((ws + EPS) / (nrm[:, None] + EPS)) >= 1.5).sum(1)
        out['top500'][:, j] = B[:, e - 27:e + 1].sum(1)
        out['top500_lists'][:, j] = cumL[e] - cumL[e - 28]
        out['nrm0'][:, j] = (nrm == 0)
        if SA is not None:
            a, b = ws, SA[:, e - 27:e + 1]
            a = a - a.mean(1, keepdims=True)
            b = b - b.mean(1, keepdims=True)
            den = np.sqrt((a * a).sum(1) * (b * b).sum(1))
            with np.errstate(divide='ignore', invalid='ignore'):
                r = (a * b).sum(1) / den
            bad = skip_corr | (np.ptp(wv, axis=1) == 0) | (np.ptp(VA[:, e - 27:e + 1], axis=1) == 0) | ~(den > 0)
            out['corr28'][:, j] = np.where(bad, np.nan, np.clip(r, -1, 1))
    return out


def to_frame(arts, kind, res):
    n = len(arts)
    df = pd.DataFrame({'article': np.repeat(np.array(arts, dtype=object), K), 'kind': kind,
                       'mi': np.tile(ORIGINS.astype(np.int32), n)})
    for k in NAMES:
        df[k] = res[k].reshape(-1)
    return df


def empty_frame(arts, kind):
    return to_frame(arts, kind, {k: np.full((len(arts), K), np.nan, np.float32) for k in NAMES})


# ---------------------------------------------------------------- authors
t1 = time.time()
AV = np.zeros((len(authors), T), np.float32)
a_have = np.zeros(len(authors), bool)
for i, a in enumerate(authors):
    v = load_views(a)
    if v is not None:
        AV[i] = v
        a_have[i] = True
a_idx = {a: i for i, a in enumerate(authors)}
log(f'author series loaded: {int(a_have.sum())} of {len(authors)} have a file ({time.time() - t1:.0f}s)')

parts = []
have_i = np.where(a_have)[0]
for k in range(0, len(have_i), CHUNK):
    ii = have_i[k:k + CHUNK]
    V = AV[ii].astype(np.float64)
    B = top_matrix([[authors[i]] for i in ii])
    parts.append(to_frame([authors[i] for i in ii], 'author', block(V, B)))
    log(f'  authors {min(k + CHUNK, len(have_i))}/{len(have_i)}')
nofile = [authors[i] for i in np.where(~a_have)[0]]
if nofile:
    parts.append(empty_frame(nofile, 'author'))

# ---------------------------------------------------------------- books (canonical title + kept redirects)
no_series_books = []
for k in range(0, len(books), CHUNK):
    bs = books[k:k + CHUNK]
    V = np.zeros((len(bs), T))
    titles = []
    ok = np.ones(len(bs), bool)
    for i, b in enumerate(bs):
        v = load_views(b)
        if v is None:
            ok[i] = False
            titles.append([b])
            continue
        for r in kept.get(b, []):
            x = load_views(r)
            if x is not None:
                v = v + x
        V[i] = v
        titles.append([b] + kept.get(b, []))
    ai = np.array([a_idx.get(b2a.get(b), -1) for b in bs])
    has_a = (ai >= 0) & np.where(ai >= 0, a_have[np.maximum(ai, 0)], False)
    VA = np.where(has_a[:, None], AV[np.maximum(ai, 0)], 0.0).astype(np.float64)
    same = np.array([b2a.get(b) == b for b in bs])
    B = top_matrix(titles)
    res = block(V, B, VA, skip_corr=~has_a | same)
    df = to_frame(bs, 'book', res)
    if (~ok).any():
        bad_rows = np.repeat(~ok, K)
        df.loc[bad_rows, NAMES] = np.nan
        no_series_books += [b for b, o in zip(bs, ok) if not o]
    parts.append(df)
    log(f'  books {min(k + CHUNK, len(books))}/{len(books)}')
F = pd.concat(parts, ignore_index=True)
del parts
gc.collect()
log('features built', F.shape)

# ---------------------------------------------------------------- co: Test A weekly r4 of the book and of its author article
EXT = [m for m in ORIGINS if m > 2026 * 12 + 6]                    # 2026-08 and 2026-09 are not in the Test A file


def weekly_r4(path, names, origins):
    """r4 exactly as in 10_test_a.py (article_features), from the weekly series, at the given origins.  Returns (article, mi, r4) rows."""
    # windows use at most 30 weeks, so weeks before 2025-09-01 cannot change these values (the filter keeps memory small)
    X = pd.read_parquet(path, columns=['article', 'week', 'share'], filters=[('week', '>=', pd.Timestamp('2025-09-01'))])
    X = X[X.article.isin(names)]
    X['week'] = pd.to_datetime(X['week'])
    P = X.pivot(index='week', columns='article', values='share').sort_index().astype(float)
    P = P.reindex(pd.date_range(P.index.min(), P.index.max(), freq='7D'))
    m4 = P.rolling(4, min_periods=1).mean()
    normal = P.shift(4).rolling(26, min_periods=13).median()
    r4 = np.log((m4 + EPS) / (normal + EPS))
    r4 = r4.where(normal.notna())
    wend = (P.index + pd.Timedelta(days=6)).values
    ends = np.array([month_end(m) for m in origins], dtype='datetime64[ns]')
    idx = np.searchsorted(wend, ends, side='right') - 1
    rows = []
    for o, i, en in zip(origins, idx, ends):
        if i < 0:
            continue
        v = r4.iloc[i]
        if (en - wend[i]) > np.timedelta64(13, 'D'):
            v = v * np.nan
        rows.append(pd.DataFrame({'article': v.index, 'mi': int(o), 'r4': v.values}))
    return pd.concat(rows, ignore_index=True)


TA = pd.read_parquet(OUT / 'test_a_wiki_features.parquet', columns=['article', 'kind', 'mi', 'r4'])
chk = {}
for kind, wk, names in (('book', 'weekly_book.parquet', set(books)), ('author', 'weekly_author.parquet', set(authors))):
    recheck_origins = [2026 * 12 + 4, 2026 * 12 + 5, 2026 * 12 + 6]            # 2026-05 to 2026-07, inside the stored range
    rr = weekly_r4(S2R / wk, names, recheck_origins + EXT)
    st = TA[TA.kind == kind].drop(columns='kind')
    both = rr[rr.mi.isin(recheck_origins)].merge(st, on=['article', 'mi'], suffixes=('_new', '_stored'))
    d = (both.r4_new - both.r4_stored).abs()
    chk[kind] = dict(n_compared=int(len(both)), max_abs_diff=float(d.max()) if len(d) else None,
                     both_missing_or_equal=bool(((both.r4_new.isna() & both.r4_stored.isna()) | (d < 1e-9)).all()))
    log(f'  r4 check {kind}: {chk[kind]}')
    assert chk[kind]['both_missing_or_equal'], 'the weekly r4 formula does not reproduce the stored Test A values'
    TA = pd.concat([TA, rr[rr.mi.isin(EXT)].assign(kind=kind)], ignore_index=True)
rb = TA[TA.kind == 'book'].rename(columns={'r4': 'b_r4'})[['article', 'mi', 'b_r4']]
ra = TA[TA.kind == 'author'].rename(columns={'article': 'author_article', 'r4': 'a_r4'})[['author_article', 'mi', 'a_r4']]
bk = F[F.kind == 'book'][['article', 'mi']].copy()
bk['author_article'] = bk.article.map(b2a)
bk = bk.merge(rb, on=['article', 'mi'], how='left').merge(ra, on=['author_article', 'mi'], how='left')
bk['co'] = np.where(bk.b_r4.notna() & bk.a_r4.notna(), ((bk.b_r4 >= LN15) & (bk.a_r4 >= LN15)).astype(float), np.nan)
F = F.merge(bk[['article', 'mi', 'co']].assign(kind='book'), on=['article', 'kind', 'mi'], how='left')
F['co'] = F['co'].astype('float32')
del TA, rb, ra, bk
gc.collect()

# ---------------------------------------------------------------- checks against a plain pandas version (test mode)
checks = {}
if TEST:
    rng = np.random.default_rng(20261020)
    sample_o = sorted(rng.choice(K, 8, replace=False).tolist() + [0, K - 1])
    Wk = pd.read_parquet(S2R / 'weekly_book.parquet', columns=['article', 'week', 'views', 'share'])
    worst = collections.defaultdict(float)
    n_cmp = 0
    ser_cache = {}

    def series(title, with_red):
        if (title, with_red) not in ser_cache:
            v = load_views(title)
            for r in (kept.get(title, []) if with_red else []):
                v = v + load_views(r)
            ser_cache[(title, with_red)] = pd.Series(v, index=DAYS)
        return ser_cache[(title, with_red)]

    def plain(vs, top_titles, j, kind, author_vs=None, same=False):
        e = DAYS[E[j]]
        vsl = vs[:e]
        sh = vsl / pd.Series(TOT, index=DAYS)[:e]
        last = vsl.iloc[-28:]
        lasts = sh.iloc[-28:]
        nrm = sh.iloc[-210:-28].median()
        o = {}
        o['pk28'] = last.max() / last.sum() if last.sum() > 0 else np.nan
        pk_pos = max(i for i, x in enumerate(last.values) if x == last.max())
        pkd = last.index[pk_pos]
        o['dpk'] = (e - pkd).days if last.sum() > 0 else np.nan
        pre = sh[pkd - pd.Timedelta(days=7):pkd - pd.Timedelta(days=1)].mean()
        o['pre7'] = np.log((pre + EPS) / (nrm + EPS)) if last.sum() > 0 else np.nan
        after = sh[pkd + pd.Timedelta(days=1):pkd + pd.Timedelta(days=7)]
        o['dec'] = np.log((after.mean() + EPS) / (sh[pkd] + EPS)) if (last.sum() > 0 and o['dpk'] >= 2) else np.nan
        o['hi28'] = int(((lasts + EPS) / (nrm + EPS) >= 1.5).sum())
        o['rec'] = np.log((lasts.max() + EPS) / (sh.iloc[:-28].max() + EPS)) if last.sum() > 0 else np.nan
        days = [i for i in last.index]
        o['top500'] = sum(any((DAYS.get_loc(d) in set(TOPDAYS.get(t.replace(' ', '_'), []))) for t in top_titles) for d in days)
        o['top500_lists'] = int(sum(LISTED[DAYS.get_loc(d)] for d in days))
        o['nrm0'] = float(nrm == 0)
        o['corr28'] = np.nan
        if kind == 'book' and author_vs is not None and not same:
            av = author_vs[:e]
            la = av.iloc[-28:]
            if last.nunique() > 1 and la.nunique() > 1:
                o['corr28'] = float(np.corrcoef(lasts.values, (av / pd.Series(TOT, index=DAYS)[:e]).iloc[-28:].values)[0, 1])
        return o

    Fi = F.set_index(['kind', 'article', 'mi'])
    for kind, arts in (('book', books[:25]), ('author', [a for a in authors if a_have[a_idx[a]]][:25])):
        for a in arts:
            for j in sample_o:
                mi = int(ORIGINS[j])
                if kind == 'book':
                    vs = series(a, True)
                    au = b2a.get(a)
                    avs = series(au, False) if (au is not None and a_have[a_idx[au]]) else None
                    o = plain(vs, [a] + kept.get(a, []), j, 'book', avs, same=(au == a))
                else:
                    o = plain(series(a, False), [a], j, 'author')
                got = Fi.loc[(kind, a, mi)]
                for k, v in o.items():
                    g = got[k]
                    n_cmp += 1
                    if (np.isnan(v) != np.isnan(g)):
                        worst[k] = max(worst[k], 1e9)
                        print('MISMATCH nan', kind, a, mi, k, v, g)
                    elif not np.isnan(v):
                        diff = abs(float(v) - float(g))
                        worst[k] = max(worst[k], diff / (1 + abs(float(v))))
                        if diff / (1 + abs(float(v))) > 1e-4:
                            print('MISMATCH', kind, a, mi, k, v, g)
    checks['plain_pandas_comparison'] = dict(values_compared=n_cmp, worst_relative_diff={k: float(v) for k, v in worst.items()})
    log('plain pandas comparison', checks['plain_pandas_comparison'])
    # weekly equivalence: our daily series (canonical + kept redirects) summed by ISO week equals the stored weekly views of Test A
    wk_bad = 0
    n_wk = 0
    for b in books[:25]:
        s = series(b, True)
        w = s.groupby(s.index - pd.to_timedelta(s.index.weekday, unit='D')).sum()
        st = Wk[Wk.article == b].set_index(pd.to_datetime(Wk[Wk.article == b].week)).views
        c = w.reindex(st.index)
        n_wk += int(c.notna().sum())
        wk_bad += int(((c - st).abs() > 1e-6).sum())
    checks['weekly_sum_equals_study2r_weekly_book'] = dict(weeks_compared=n_wk, weeks_different=wk_bad)
    log('weekly equivalence', checks['weekly_sum_equals_study2r_weekly_book'])
    # share of windows where the raw-views peak and the share peak are the same day
    # (informative for the scale choice in the report; sample only)
    agree, tot_w = 0, 0
    for b in books[:25]:
        s = series(b, True)
        sh = s / pd.Series(TOT, index=DAYS)
        for j in sample_o:
            e = DAYS[E[j]]
            lv, ls = s[:e].iloc[-28:], sh[:e].iloc[-28:]
            if lv.sum() > 0:
                tot_w += 1
                agree += int(max(i for i, x in enumerate(lv.values) if x == lv.max()) == max(i for i, x in enumerate(ls.values) if x == ls.max()))
    checks['peak_day_raw_vs_share_agreement'] = dict(windows=tot_w, same_day=agree)
    log('peak agreement raw vs share', checks['peak_day_raw_vs_share_agreement'])

# ---------------------------------------------------------------- write
F = F.sort_values(['kind', 'article', 'mi']).reset_index(drop=True)
for c in NAMES + ['co']:
    F[c] = F[c].astype('float32')
F['mi'] = F['mi'].astype('int32')
F.to_parquet(OUT / f'burst_features{SUF}.parquet', index=False)


def quant(x):
    x = x.dropna()
    return {} if x.empty else {q: float(x.quantile(p)) for q, p in (('p1', .01), ('p5', .05), ('p25', .25), ('p50', .5), ('p75', .75), ('p95', .95), ('p99', .99))} | {
        'mean': float(x.mean()), 'min': float(x.min()), 'max': float(x.max())}


summ = dict(rows=int(len(F)), articles_book=int((F.kind == 'book').sum() // K), articles_author=int((F.kind == 'author').sum() // K), origins=K,
            mi_first=int(ORIGINS[0]), mi_last=int(ORIGINS[-1]), book_articles_without_any_series=no_series_books, author_articles_without_file=len(nofile),
            zero_window_share={kd: float(F.loc[F.kind == kd, 'pk28'].isna().mean()) for kd in ('book', 'author')},
            zero_normal_share={kd: float(F.loc[(F.kind == kd) & F.pk28.notna(), 'nrm0'].mean()) for kd in ('book', 'author')},
            peak_memory_mb=round(peak_mb()),
            top500_days_with_list=n_list_days, top500_titles_seen=len(TOPDAYS), checks=chk | checks, test=TEST,
            share_missing={kd: {c: float(F.loc[F.kind == kd, c].isna().mean()) for c in NAMES + ['co']} for kd in ('book', 'author')},
            quantiles={kd: {c: quant(F.loc[F.kind == kd, c]) for c in NAMES + ['co']} for kd in ('book', 'author')},
            runtime_s=round(time.time() - T0))
(OUT / f'burst_features_summary{SUF}.json').write_text(json.dumps(summ, indent=1))
log('wrote', OUT / f'burst_features{SUF}.parquet', F.shape, f'runtime {time.time() - T0:.0f}s')
