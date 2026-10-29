# l02. Addendum l, step 1 continued: daily views, weekly shares and Wikipedia features for the articles of the sampled works.
# Settings: prereg/addenda_wiki_led/2026-10-30_l_books_in_time.json, L1 views and point_in_time, L3 (read-only; SHA-256 checked).
# DATA ONLY: no loan, model or outcome.
#
# Method of code/study2r/03_pageviews.py and 04_weekly_series.py, copied: canonical titles through the Action API (redirects followed,
#   disambiguation flagged); for book articles the redirects are listed and screened (recent views and move or merge tags, monthly
#   history for flagged ones, the same keep rules) and the kept redirects' views are added; author articles by canonical title only.
#   Daily user views (agent=user, all-access) 2015-07-01 to 2026-09-30 from the Wikimedia per-article service, one parquet per title in
#   data/db/study2r/pv_daily/ (shared with Test A: a title already downloaded is not downloaded again). Weekly shares of all English
#   Wikipedia user views (data/db/interest/wiki/weekly_total.parquet).
# Test A's articles keep Test A's stored canonical titles, redirect decisions and weekly series (data/db/study2r/articles.parquet,
#   redirect_screen.parquet, weekly_book.parquet, weekly_author.parquet), so their features are those of Test A; only new articles are
#   resolved, screened and downloaded.  At most 3 requests a second for every request (record: 3 a second for the views).
# Features: article_features() of code/main_study/wiki_led/10c_test_a.py copied unchanged (with correction A1 of addendum e), for origins
#   2016-03 to 2026-08 (2026-08 only for the frozen forecasts).  Check: for Test A's articles and origins to 2026-07 the features must
#   equal data/db/wiki_led/test_a_wiki_features_c.parquet.
# Outputs (data/db/wiki_led/l_books_in_time/): articles.parquet, redirect_screen.parquet, weekly_book.parquet, weekly_author.parquet,
#   wiki_features.parquet (article, kind, mi, the nine features), views_summary.json; report data/reports/wiki_led_l_views.md
#   Run from code/:  bash ../jobs/bg.sh wl_l02 main_study/wiki_led/l_books_in_time/l02_views.py
import sys, re, os, json, time, hashlib, pathlib, urllib.parse
import numpy as np, pandas as pd
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'study2r'))
import common as C2                                         # noqa: E402
from common import log                                      # noqa: E402

D = C2.D
ROOT = D.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-30_l_books_in_time.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == '36778f86ced0550c90e8578813ae476c6ae1d4d7220c430ef140244e5d5e028a', 'addendum l changed'
OUT = D / 'db' / 'wiki_led' / 'l_books_in_time'
S2 = D / 'db' / 'study2r'
REP = D / 'reports'
DAILY = S2 / 'pv_daily'
T0 = time.time()
H = C2.Http(gap=0.34)                                       # at most 3 requests a second, all threads together
POOL = ThreadPoolExecutor(8)                               # many requests wait about 4 s; the 3-a-second cap is in H
START, END = '2015070100', '2026093000'
REST = 'https://wikimedia.org/api/rest_v1/metrics/pageviews'
MW = 'https://en.wikipedia.org/w/api.php'
RECENT_SHARE, RECENT_MIN = 0.005, 1000
REDIR_SHARE, REDIR_MONTH_SHARE, REDIR_MONTH_MIN = 0.01, 0.10, 1000
MOVE_TAG = re.compile(r'\{\{\s*R(cat)?\s*(from )?(move|merge|former name|historic name|previous name|from move|from merge)', re.I)
fid = lambda t: hashlib.sha1(t.encode()).hexdigest()[:16]

M = pd.read_parquet(OUT / 'matches.parquet')
A2 = pd.read_parquet(S2 / 'articles.parquet')                # Test A: requested -> canonical
ta_book_req = set(A2[A2.kind == 'book'].requested); ta_auth_req = set(A2[A2.kind == 'author'].requested)
book_req = sorted(set(M.book_article.dropna())); auth_req = sorted(set(M.author_article.dropna()))
new_req = sorted((set(book_req) - ta_book_req - ta_auth_req) | (set(auth_req) - ta_book_req - ta_auth_req))
log('book articles', len(book_req), '| author articles', len(auth_req), '| titles not resolved by Test A', len(new_req))


def mw(params, cache=True):
    r = H.get(MW, params={**params, 'format': 'json', 'formatversion': 2}, cache=cache)
    return json.loads(r['text']) if r['status'] == 200 else None


# ---------------------------------------------------------------- canonical titles of the new titles (as 03_pageviews.py)
fa = OUT / 'articles.parquet'
if fa.exists():
    A = pd.read_parquet(fa)
else:
    rows = []
    for i in range(0, len(new_req), 50):
        b = new_req[i:i + 50]
        q = mw(dict(action='query', titles='|'.join(b), redirects=1, prop='pageprops', ppprop='wikibase_item|disambiguation'))
        if q is None:
            raise SystemExit('canonical lookup failed; rerun')
        q = q['query']
        norm_ = {x['from']: x['to'] for x in q.get('normalized', [])}
        red = {x['from']: x['to'] for x in q.get('redirects', [])}
        pages = {p['title']: p for p in q['pages']}
        for t in b:
            t2 = red.get(norm_.get(t, t), norm_.get(t, t)); p = pages.get(t2, {})
            rows.append(dict(requested=t, canonical=None if p.get('missing') else t2, qid=p.get('pageprops', {}).get('wikibase_item'),
                             disambiguation='disambiguation' in p.get('pageprops', {}), source='new'))
        if (i // 50) % 40 == 0:
            log('canonical', i, '/', len(new_req))
    A = pd.concat([A2.drop(columns='kind').assign(source='test_a'), pd.DataFrame(rows)], ignore_index=True)
    A.to_parquet(fa, index=False)
can = dict(zip(A.requested, A.canonical))
M['book_canonical'] = M.book_article.map(can); M['author_canonical'] = M.author_article.map(can)
M[['work_id', 'book_canonical', 'author_canonical']].to_parquet(OUT / 'work_articles.parquet', index=False)
WB2 = pd.read_parquet(S2 / 'weekly_book.parquet', columns=['article']).article.unique()
WA2 = pd.read_parquet(S2 / 'weekly_author.parquet', columns=['article']).article.unique()
book_can = sorted(set(M.book_canonical.dropna())); author_can = sorted(set(M.author_canonical.dropna()))
new_book = sorted(set(book_can) - set(WB2)); new_auth = sorted(set(author_can) - set(WA2))
log('book canonicals', len(book_can), 'new', len(new_book), '| author canonicals', len(author_can), 'new', len(new_auth))

# ---------------------------------------------------------------- redirects of the new book articles, screening (as 03_pageviews.py)
fr = OUT / 'redirects.parquet'
if fr.exists():
    RD = pd.read_parquet(fr)
else:
    rd = []
    for i in range(0, len(new_book), 50):
        b = new_book[i:i + 50]
        got = {t: [] for t in b}
        params = dict(action='query', titles='|'.join(b), prop='redirects', rdlimit='max', rdnamespace=0, rdprop='title|pageid')
        while True:
            r = mw(params)
            if r is None:
                raise SystemExit('redirect list failed; rerun')
            for p in r['query']['pages']:
                if p['title'] in got:
                    got[p['title']].extend(x['title'] for x in p.get('redirects', []))
            if 'continue' not in r:
                break
            params.update(r['continue'])
        rd += [dict(canonical=t, redirect=x) for t, v in got.items() for x in v]
        if (i // 50) % 40 == 0:
            log('redirect lists', i, '/', len(new_book))
    RD = pd.DataFrame(rd, columns=['canonical', 'redirect'])
    RD.to_parquet(fr, index=False)
log('redirects of new book articles', len(RD))


def per_article(title, gran):
    t = urllib.parse.quote(title.replace(' ', '_'), safe='')
    r = H.get(f'{REST}/per-article/en.wikipedia/all-access/user/{t}/{gran}/{START}/{END}', cache=False)
    if r['status'] == 404:
        return {}
    if r['status'] != 200:
        return None
    return {x['timestamp'][:8]: x['views'] for x in json.loads(r['text']).get('items', [])}


def fetch_daily(title):
    f = DAILY / f'{fid(title)}.parquet'
    if f.exists():
        return 1
    d = per_article(title, 'daily')
    if d is None:
        return 0
    pd.DataFrame({'date': pd.to_datetime(list(d.keys()), format='%Y%m%d'), 'views': np.array(list(d.values()), dtype='int64'),
                  'title': title}).to_parquet(f, index=False)
    return 1


def run_daily(titles, label):
    todo = [t for t in titles if not (DAILY / f'{fid(t)}.parquet').exists()]
    log(label, 'daily to fetch', len(todo))
    done = 0
    for k in range(0, len(todo), 300):
        res = list(POOL.map(fetch_daily, todo[k:k + 300]))
        done += sum(res)
        log(label, 'daily fetched', k + len(res), '/', len(todo), 'failed so far', (k + len(res)) - done)
    return len(todo) - done


fail_b = run_daily(new_book, 'new book articles')
fi = OUT / '_redirect_info.json'
info = json.load(open(fi)) if fi.exists() else {}
titles = sorted(set(RD.redirect)) + sorted(set(new_book))
todo = [t for t in titles if t not in info]
rset = set(RD.redirect)
log('titles to screen (batches of 50)', len(todo))


def screen(b):
    isred = set(b) & rset
    q = mw(dict(action='query', titles='|'.join(b), prop='pageviews|revisions', pvipdays=60, rvprop='content', rvslots='main',
                rvsection=0), cache=False) if isred else mw(dict(action='query', titles='|'.join(b), prop='pageviews', pvipdays=60), cache=False)
    if q is None:
        return None
    q = q.get('query', {})
    norm_ = {x['from']: x['to'] for x in q.get('normalized', [])}
    pages = {p['title']: p for p in q.get('pages', [])}
    out = {}
    for t in b:
        p = pages.get(norm_.get(t, t), {}); pv = p.get('pageviews') or {}
        txt = ((p.get('revisions') or [{}])[0].get('slots', {}).get('main', {}).get('content') or '')
        out[t] = dict(recent60=int(sum(v for v in pv.values() if v)), moved=bool(MOVE_TAG.search(txt)),
                      tags=' '.join(sorted(set(re.findall(r'\{\{\s*(R [^}|]+)', txt))))[:300])
    return out


batches = [todo[i:i + 50] for i in range(0, len(todo), 50)]
for k in range(0, len(batches), 30):
    for res in POOL.map(screen, batches[k:k + 30]):
        if res:
            info.update(res)
    C2.json.dump(info, open(str(fi) + '.part', 'w')); os.replace(str(fi) + '.part', fi)
    log('screened batches', min(k + 30, len(batches)), '/', len(batches))
S = RD.copy()
S['recent60'] = S.redirect.map(lambda t: info.get(t, {}).get('recent60'))
S['moved_or_merged'] = S.redirect.map(lambda t: info.get(t, {}).get('moved'))
S['canonical_recent60'] = S.canonical.map(lambda t: info.get(t, {}).get('recent60'))
S['flagged'] = S.moved_or_merged.fillna(False) | (S.recent60.fillna(0) >= RECENT_MIN) | \
    (S.recent60.fillna(0) >= RECENT_SHARE * S.canonical_recent60.fillna(0).clip(lower=1))
fm = OUT / '_redirect_monthly.json'
mon = json.load(open(fm)) if fm.exists() else {}
todo = sorted(set(S[S.flagged].redirect) - set(mon))
log('redirects flagged', int(S.flagged.sum()), 'monthly to fetch', len(todo))


def monthly(t):
    d = per_article(t, 'monthly')
    return t, None if d is None else {k[:6]: v for k, v in d.items()}


for k in range(0, len(todo), 300):
    for t, d in POOL.map(monthly, todo[k:k + 300]):
        if d is not None:
            mon[t] = d
    C2.json.dump(mon, open(str(fm) + '.part', 'w')); os.replace(str(fm) + '.part', fm)
    log('monthly', min(k + 300, len(todo)), '/', len(todo))
own = {}
for t in new_book:
    f = DAILY / f'{fid(t)}.parquet'
    if f.exists():
        d = pd.read_parquet(f)
        own[t] = d.groupby(d.date.dt.strftime('%Y%m')).views.sum().to_dict() if len(d) else {}
keep, reason = [], []
for r in S.itertuples():
    m = mon.get(r.redirect) if r.flagged else None
    if m is None:
        keep.append(False); reason.append('not flagged' if not r.flagged else 'monthly not fetched'); continue
    tot = sum(m.values()); o = own.get(r.canonical, {}); otot = sum(o.values())
    big = any(v >= REDIR_MONTH_MIN and v >= REDIR_MONTH_SHARE * max(o.get(k, 0), 1) for k, v in m.items())
    share = tot >= REDIR_SHARE * max(otot, 1)
    keep.append(share or big); reason.append('share of total' if share else ('large month' if big else 'small'))
S['keep'] = keep; S['reason'] = reason
S.to_parquet(OUT / 'redirect_screen.parquet', index=False)
fail_r = run_daily(sorted(set(S[S.keep].redirect)), 'redirects kept')
fail_a = run_daily(new_auth, 'new author articles')

# ---------------------------------------------------------------- weekly series (as 04_weekly_series.py); Test A's series reused
DAYS = pd.date_range('2015-07-01', '2026-09-30', freq='D')
TOT = pd.read_parquet(C2.WK / 'weekly_total.parquet').set_index('week')
wk = DAYS - pd.to_timedelta(DAYS.weekday, unit='D')
kept = S[S.keep].groupby('canonical').redirect.apply(list).to_dict()


def load(t):
    f = DAILY / f'{fid(t)}.parquet'
    if not f.exists():
        return None
    d = pd.read_parquet(f)
    return d.set_index('date').views.reindex(DAYS, fill_value=0).astype(float)


def build(titles, with_redirects):
    frames = []
    for t in titles:
        own_ = load(t)
        if own_ is None:
            continue
        s = own_.copy()
        if with_redirects:
            for r in kept.get(t, []):
                x = load(r)
                if x is not None:
                    s = s + x
        df = pd.DataFrame({'week': wk, 'v': s.to_numpy()})
        g = df.groupby('week').v.agg(['sum', 'max', 'size']).reset_index()
        g = g[g.week.isin(TOT.index)]
        tt = TOT.loc[g.week]
        g['article'] = t; g['views'] = g['sum'].to_numpy(); g['share'] = g['sum'].to_numpy() / tt.total_views.to_numpy()
        g['top_day_share'] = np.where(g['sum'] > 0, g['max'] / g['sum'].replace(0, np.nan), np.nan)
        g['valid'] = ((g['size'] == 7) & ~tt.partial_week.to_numpy() & (g['sum'] > 0)).to_numpy()
        frames.append(g[['article', 'week', 'views', 'share', 'top_day_share', 'valid']])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=['article', 'week', 'views', 'share', 'top_day_share', 'valid'])


old_b = pd.read_parquet(S2 / 'weekly_book.parquet'); old_b = old_b[old_b.article.isin(book_can)]
old_a = pd.read_parquet(S2 / 'weekly_author.parquet'); old_a = old_a[old_a.article.isin(author_can)]
WB = pd.concat([old_b, build(new_book, True)], ignore_index=True)
WA = pd.concat([old_a, build(new_auth, False)], ignore_index=True)
WB.to_parquet(OUT / 'weekly_book.parquet', index=False); WA.to_parquet(OUT / 'weekly_author.parquet', index=False)
log('weekly series: book', WB.article.nunique(), 'of', len(book_can), '| author', WA.article.nunique(), 'of', len(author_can))

# ---------------------------------------------------------------- features: article_features() copied unchanged from 10c_test_a.py
def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def month_end(mi):
    y, m = divmod(mi, 12)
    return pd.Timestamp(year=y, month=m + 1, day=1) + pd.offsets.MonthEnd(0)


ORIGINS = np.arange(mi_of('2016-03'), mi_of('2026-08') + 1)
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


def features_for(X):
    X = X[['article', 'week', 'views', 'share', 'valid']].copy()
    X['week'] = pd.to_datetime(X['week'])
    parts = []
    for i, (a, g) in enumerate(X.groupby('article', sort=False)):
        h = article_features(g)
        if h is None or len(h) == 0:
            continue
        h.insert(0, 'article', a)
        parts.append(h)
        if i % 2000 == 0:
            log('  features', i)
    return pd.concat(parts, ignore_index=True)


fb = features_for(WB).assign(kind='book'); fa_ = features_for(WA).assign(kind='author')
WF = pd.concat([fb, fa_], ignore_index=True)
WF.to_parquet(OUT / 'wiki_features.parquet', index=False)
# check: Test A's articles reproduce test_a_wiki_features_c.parquet on origins to 2026-07
ref = pd.read_parquet(D / 'db' / 'wiki_led' / 'test_a_wiki_features_c.parquet')
cmp_ = WF[WF.mi <= mi_of('2026-07')].merge(ref, on=['article', 'kind', 'mi'], suffixes=('', '_ref'))
diff = max(float(np.nanmax(np.abs(cmp_[c] - cmp_[c + '_ref']))) if cmp_[c].notna().any() else 0.0 for c in FEATS)
nan_mismatch = int(sum(((cmp_[c].isna()) != (cmp_[c + '_ref'].isna())).sum() for c in FEATS))
log('check against Test A features: rows compared', len(cmp_), '| largest difference', diff, '| missing-pattern mismatches', nan_mismatch)
assert len(cmp_) > 0 and diff < 1e-9 and nan_mismatch == 0, 'features do not reproduce Test A'

summ = dict(book_canonicals=len(book_can), new_book=len(new_book), author_canonicals=len(author_can), new_author=len(new_auth),
            redirects_listed=len(RD), redirects_kept=int(S.keep.sum()), failed_daily=dict(book=fail_b, redirects=fail_r, author=fail_a),
            weekly_book_articles=int(WB.article.nunique()), weekly_author_articles=int(WA.article.nunique()),
            feature_rows=len(WF), check_rows=len(cmp_), check_max_diff=diff, network_requests=H.n_net, runtime_s=round(time.time() - T0))
(OUT / 'views_summary.json').write_text(json.dumps(summ, indent=1))
Lr = ['# Addendum l, step 1 continued: views, weekly series and features of the sampled works\' articles', '',
      f'Made by `code/main_study/wiki_led/l_books_in_time/l02_views.py` on {time.strftime("%Y-%m-%d %H:%M")} (local time, UTC+06:30). Data only.', '',
      f'- Book articles (canonical): {len(book_can):,}, of which new {len(new_book):,}; redirects of new ones listed {len(RD):,}, kept {int(S.keep.sum()):,}.',
      f'- Author articles (canonical): {len(author_can):,}, of which new {len(new_auth):,}.',
      f'- Failed daily downloads: {summ["failed_daily"]}.',
      f'- Weekly series: book {summ["weekly_book_articles"]:,}, author {summ["weekly_author_articles"]:,}.',
      f'- Feature rows (article and origin month, 2016-03 to 2026-08): {len(WF):,}.',
      f'- Check: on {len(cmp_):,} rows of Test A\'s articles (origins to 2026-07) the features equal Test A\'s (largest difference {diff:.1e}, '
      f'missing-pattern mismatches {nan_mismatch}).',
      f'- Network requests {H.n_net:,} (at most 3 a second); run time {summ["runtime_s"]} s.']
(REP / 'wiki_led_l_views.md').write_text('\n'.join(Lr) + '\n')
log(json.dumps(summ))
