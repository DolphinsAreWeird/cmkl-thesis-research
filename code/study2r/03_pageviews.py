"""Study 2R step 4a: daily English Wikipedia user views for every matched book article (canonical title plus redirects
with real traffic) and, as the secondary series, the author's article (canonical title only).
Same method as code/main_study/interest/05 and 06 (Wikimedia REST per-article API, agent=user, all-access, 2015-07-01 to
2026-09-30; redirects screened in batches of 50 by recent views and {{R from move}} / {{R from merge}} tags, monthly history
for flagged ones, daily views for those whose history passes the share rules), but at most 5 requests per second
(4 threads sharing one limiter) and every answer cached, so the script resumes after any stop.
Outputs: data/db/study2r/articles.parquet (canonical titles), redirects.parquet, redirect_screen.parquet,
pv_daily/<sha1>.parquet (one file per title), book_author_articles.parquet, total views come from data/db/interest/wiki.
"""
import re, urllib.parse, hashlib
import numpy as np, pandas as pd
from concurrent.futures import ThreadPoolExecutor
from common import *

START, END = '2015070100', '2026093000'
REST = 'https://wikimedia.org/api/rest_v1/metrics/pageviews'
MW = 'https://en.wikipedia.org/w/api.php'
RECENT_SHARE, RECENT_MIN = 0.005, 1000
REDIR_SHARE, REDIR_MONTH_SHARE, REDIR_MONTH_MIN = 0.01, 0.10, 1000
MOVE_TAG = re.compile(r'\{\{\s*R(cat)?\s*(from )?(move|merge|former name|historic name|previous name|from move|from merge)', re.I)
DAILY = OUT / 'pv_daily'
DAILY.mkdir(exist_ok=True)
fid = lambda t: hashlib.sha1(t.encode()).hexdigest()[:16]
POOL = ThreadPoolExecutor(4)

M = pd.read_parquet(OUT / 'book_matches.parquet')
book_titles = sorted(M.article.unique())
log('matched book articles', len(book_titles))


def save_json(o, p):
    open(str(p) + '.part', 'w').write(json.dumps(o)); os.replace(str(p) + '.part', p)


def mw(params, cache=True):
    r = H.get(MW, params={**params, 'format': 'json', 'formatversion': 2}, cache=cache)
    return json.loads(r['text']) if r['status'] == 200 else None


# ---------------------------------------------------------------- authors' articles (secondary series)
def author_articles():
    f = OUT / 'book_author_articles.parquet'
    if f.exists():
        return pd.read_parquet(f)
    AU = pd.read_parquet(OUT / 'wd_authors.parquet')
    AU = AU[AU.author_item != '']
    fam = dict(zip(M.item, M.creator.map(parse_creators)))
    AU = AU[AU.item.isin(M.item)].copy()
    AU['ok'] = [any(x in norm(l).split() for x in fam[i]) for i, l in zip(AU.item, AU.author_label)]
    AU = AU[AU.ok].drop_duplicates('item')           # first author whose family name matches the Seattle creator
    need = sorted(AU.author_item.unique()); out = {}
    for k in range(0, len(need), 300):
        vals = ' '.join('wd:' + x for x in need[k:k + 300])
        b = sparql(f'SELECT ?a ?n WHERE {{ VALUES ?a {{ {vals} }} ?s schema:about ?a ; schema:isPartOf <https://en.wikipedia.org/> ; schema:name ?n }}')
        if b is None:
            raise SystemExit('author article batch failed; rerun')
        for r in b:
            out[qid(r['a']['value'])] = r['n']['value']
    AU['author_article'] = AU.author_item.map(out)
    AU = AU[AU.author_article.notna()][['item', 'author_item', 'author_label', 'author_article']]
    AU.to_parquet(f, index=False)
    return AU


AUA = author_articles()
author_titles = sorted(AUA.author_article.unique())
log('author articles', len(author_titles))

# ---------------------------------------------------------------- canonical titles (follow redirects), disambiguation flag
fa = OUT / 'articles.parquet'
if fa.exists():
    A = pd.read_parquet(fa)
else:
    rows = []
    allt = sorted(set(book_titles) | set(author_titles))
    for i in range(0, len(allt), 50):
        b = allt[i:i + 50]
        q = mw(dict(action='query', titles='|'.join(b), redirects=1, prop='pageprops', ppprop='wikibase_item|disambiguation'))
        if q is None:
            raise SystemExit('canonical lookup failed')
        q = q['query']
        norm_ = {x['from']: x['to'] for x in q.get('normalized', [])}
        red = {x['from']: x['to'] for x in q.get('redirects', [])}
        pages = {p['title']: p for p in q['pages']}
        for t in b:
            t2 = red.get(norm_.get(t, t), norm_.get(t, t)); p = pages.get(t2, {})
            rows.append(dict(requested=t, canonical=None if p.get('missing') else t2, qid=p.get('pageprops', {}).get('wikibase_item'),
                             disambiguation='disambiguation' in p.get('pageprops', {}), kind='book' if t in set(book_titles) else 'author'))
        if (i // 50) % 40 == 0:
            log('canonical', i, '/', len(allt))
    A = pd.DataFrame(rows)
    A.to_parquet(fa, index=False)
log('canonical resolved; missing', int(A.canonical.isna().sum()), 'disambiguation', int(A.disambiguation.sum()))
book_can = sorted(set(A[(A.requested.isin(book_titles))].canonical.dropna()))
author_can = sorted(set(A[(A.requested.isin(author_titles))].canonical.dropna()) - set(book_can))

# ---------------------------------------------------------------- redirects of the book articles
fr = OUT / 'redirects.parquet'
if fr.exists():
    RD = pd.read_parquet(fr)
else:
    rd = []
    for i in range(0, len(book_can), 50):
        b = book_can[i:i + 50]
        got = {t: [] for t in b}
        params = dict(action='query', titles='|'.join(b), prop='redirects', rdlimit='max', rdnamespace=0, rdprop='title|pageid')
        while True:
            r = mw(params)
            if r is None:
                raise SystemExit('redirect list failed')
            for p in r['query']['pages']:
                if p['title'] in got:
                    got[p['title']].extend(x['title'] for x in p.get('redirects', []))
            if 'continue' not in r:
                break
            params.update(r['continue'])
        rd += [dict(canonical=t, redirect=x) for t, v in got.items() for x in v]
        if (i // 50) % 40 == 0:
            log('redirect lists', i, '/', len(book_can))
    RD = pd.DataFrame(rd)
    RD.to_parquet(fr, index=False)
log('redirects listed', len(RD))


# ---------------------------------------------------------------- per-article REST (not cached by HTTP layer: parquet per title instead)
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
    for k in range(0, len(todo), 400):
        res = list(POOL.map(fetch_daily, todo[k:k + 400]))
        done += sum(res)
        log(label, 'daily fetched', k + len(res), '/', len(todo), 'failed so far', (k + len(res)) - done)


run_daily(book_can, 'book articles')

# ---------------------------------------------------------------- screening of redirects: recent views and move tags, 50 titles per request
fi = OUT / '_redirect_info.json'
info = json.load(open(fi)) if fi.exists() else {}
titles = sorted(set(RD.redirect)) + sorted(set(book_can))      # redirects and canonical titles go in separate batches
todo = [t for t in titles if t not in info]
log('titles to screen (batches of 50)', len(todo))


def screen(b):
    # redirects: page text too (tags); canonical articles: recent views only (their text is large and not needed)
    isred = set(b) & set(RD.redirect)
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
for k in range(0, len(batches), 40):
    for res in POOL.map(screen, batches[k:k + 40]):
        if res:
            info.update(res)
    save_json(info, fi); log('screened batches', k + 40, '/', len(batches))

S = RD.copy()
S['recent60'] = S.redirect.map(lambda t: info.get(t, {}).get('recent60'))
S['moved_or_merged'] = S.redirect.map(lambda t: info.get(t, {}).get('moved'))
S['tags'] = S.redirect.map(lambda t: info.get(t, {}).get('tags'))
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


for k in range(0, len(todo), 400):
    for t, d in POOL.map(monthly, todo[k:k + 400]):
        if d is not None:
            mon[t] = d
    save_json(mon, fm); log('monthly', k + 400, '/', len(todo))

own = {}
for t in book_can:
    f = DAILY / f'{fid(t)}.parquet'
    if f.exists():
        d = pd.read_parquet(f)
        own[t] = d.groupby(d.date.dt.strftime('%Y%m')).views.sum().to_dict() if len(d) else {}
keep, reason, mtot = [], [], []
for r in S.itertuples():
    m = mon.get(r.redirect) if r.flagged else None
    if m is None:
        keep.append(False); reason.append('not flagged' if not r.flagged else 'monthly not fetched'); mtot.append(None); continue
    tot = sum(m.values()); o = own.get(r.canonical, {}); otot = sum(o.values())
    big = any(v >= REDIR_MONTH_MIN and v >= REDIR_MONTH_SHARE * max(o.get(k, 0), 1) for k, v in m.items())
    share = tot >= REDIR_SHARE * max(otot, 1)
    keep.append(share or big); reason.append('share of total' if share else ('large month' if big else 'small')); mtot.append(tot)
S['monthly_total'] = mtot; S['keep'] = keep; S['reason'] = reason
S.to_parquet(OUT / 'redirect_screen.parquet', index=False)
run_daily(list(S[S.keep].redirect.unique()), 'redirects kept')
run_daily(author_can, 'author articles')
log('redirects kept', int(S.keep.sum()), 'of', len(S), '| seconds', int(time.time() - T0), '| network requests', H.n_net)
log('DONE')
