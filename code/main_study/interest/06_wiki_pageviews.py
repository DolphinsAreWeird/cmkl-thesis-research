# 06. Daily English Wikipedia user views for the chosen concept articles, their redirects that carry traffic, and the site.
# Official Wikimedia REST pageviews API (per-article and aggregate), agent=user, all-access, 2015-07-01 to 2026-09-30,
# about one request per second with the project User-Agent. Resumes after a restart (every title's daily file and every
# screening answer are kept on disk).
# Redirects: the API does not follow redirects. A view of a redirect title is counted under that title, and after a page
# move the old title keeps the history from before the move (an earlier finding: moved titles showed zero views).
# 18,000 redirects cannot each be fetched at one request per second in reasonable time, so they are screened in batches:
#   a) MediaWiki API, 50 titles per request: views in the last 60 days (prop=pageviews) and the redirect's own page text,
#      whose redirect categories say whether it is an old title after a move or a merged article ({{R from move}},
#      {{R from merge}}, {{R from former name}} ...);
#   b) monthly history (per-article API) for every redirect that is a moved or merged title, or that has >= RECENT_SHARE of
#      its article's recent views or >= RECENT_MIN views in 60 days;
#   c) daily views for each of those whose history passes: total >= REDIR_SHARE of the article's own total, or any month
#      with >= REDIR_MONTH_SHARE of the article's views that month and >= REDIR_MONTH_MIN views (catches pre-move years).
# Inputs: data/db/interest/wiki/articles.parquet, redirects.parquet (from 05)
# Outputs: wiki/pv_daily/<id>.parquet (one per title), total_daily.parquet, redirect_screen.parquet, fetch_log.json
import os, re, json, time, hashlib, urllib.parse, pandas as pd
from _ci import WK, polite_get, save_json, save_parquet

START, END = '2015070100', '2026093000'
REST = 'https://wikimedia.org/api/rest_v1/metrics/pageviews'
MW = 'https://en.wikipedia.org/w/api.php'
RECENT_SHARE, RECENT_MIN = 0.005, 1000
REDIR_SHARE, REDIR_MONTH_SHARE, REDIR_MONTH_MIN = 0.01, 0.10, 1000
MOVE_TAG = re.compile(r'\{\{\s*R(cat)?\s*(from )?(move|merge|former name|historic name|previous name|from move|from merge)', re.I)
DAILY = f'{WK}/pv_daily'
os.makedirs(DAILY, exist_ok=True)
LOG = f'{WK}/fetch_log.json'
log = json.load(open(LOG)) if os.path.exists(LOG) else {'missing': {}, 'failed': {}}


def fid(title):
    return hashlib.sha1(title.encode()).hexdigest()[:16]


def per_article(title, gran):
    t = urllib.parse.quote(title.replace(' ', '_'), safe='')
    r = polite_get(f'{REST}/per-article/en.wikipedia/all-access/user/{t}/{gran}/{START}/{END}')
    if r is None:
        return None
    if r.status_code == 404:
        return {}
    return {x['timestamp'][:8]: x['views'] for x in r.json().get('items', [])}


def fetch_daily(title):
    f = f'{DAILY}/{fid(title)}.parquet'
    if os.path.exists(f):
        return
    d = per_article(title, 'daily')
    if d is None:
        log['failed'][title] = time.strftime('%Y-%m-%d %H:%M'); return
    log['failed'].pop(title, None)
    if not d:
        log['missing'][title] = 'no data (404)'
    df = pd.DataFrame({'date': pd.to_datetime(list(d.keys()), format='%Y%m%d'), 'views': list(d.values()), 'title': title})
    save_parquet(df, f)


A = pd.read_parquet(f'{WK}/articles.parquet')
RD = pd.read_parquet(f'{WK}/redirects.parquet')
targets = sorted(A.canonical.dropna().unique())
print('articles', len(targets), 'redirects', len(RD), flush=True)

# 1) site total (one request)
ft = f'{WK}/total_daily.parquet'
if not os.path.exists(ft):
    it = polite_get(f'{REST}/aggregate/en.wikipedia/all-access/user/daily/{START}/{END}').json()['items']
    save_parquet(pd.DataFrame({'date': pd.to_datetime([x['timestamp'][:8] for x in it], format='%Y%m%d'),
                               'views': [x['views'] for x in it]}), ft)
    print('site total saved', len(it), 'days', flush=True)

# 2) daily views of every chosen article
todo = [t for t in targets if not os.path.exists(f'{DAILY}/{fid(t)}.parquet')]
print('articles to fetch', len(todo), flush=True)
for i, t in enumerate(todo):
    fetch_daily(t)
    if (i + 1) % 50 == 0:
        save_json(log, LOG); print('articles', i + 1, flush=True)
save_json(log, LOG)

# 3a) recent views and redirect categories, 50 titles per request
fi = f'{WK}/_redirect_info.json'
info = json.load(open(fi)) if os.path.exists(fi) else {}
titles = sorted(set(RD.redirect) | set(targets))
todo = [t for t in titles if t not in info]
print('titles to screen (batches of 50)', len(todo), flush=True)
for i in range(0, len(todo), 50):
    b = todo[i:i + 50]
    params = dict(action='query', titles='|'.join(b), prop='pageviews|revisions', pvipdays=60, rvprop='content', rvslots='main',
                  format='json', formatversion=2)
    r = polite_get(MW, params)
    if r is None:
        continue
    q = r.json().get('query', {})
    norm = {x['from']: x['to'] for x in q.get('normalized', [])}
    pages = {p['title']: p for p in q.get('pages', [])}
    for t in b:
        p = pages.get(norm.get(t, t), {})
        pv = p.get('pageviews') or {}
        txt = ((p.get('revisions') or [{}])[0].get('slots', {}).get('main', {}).get('content') or '')
        info[t] = dict(recent60=int(sum(v for v in pv.values() if v)), moved=bool(MOVE_TAG.search(txt)),
                       tags=' '.join(sorted(set(re.findall(r'\{\{\s*(R [^}|]+)', txt))))[:300])
    if (i // 50 + 1) % 20 == 0:
        save_json(info, fi); print('screened', i + 50, flush=True)
save_json(info, fi)

# 3b) monthly history of flagged redirects
S = RD.copy()
S['recent60'] = S.redirect.map(lambda t: info.get(t, {}).get('recent60'))
S['moved_or_merged'] = S.redirect.map(lambda t: info.get(t, {}).get('moved'))
S['tags'] = S.redirect.map(lambda t: info.get(t, {}).get('tags'))
S['canonical_recent60'] = S.canonical.map(lambda t: info.get(t, {}).get('recent60'))
S['flagged'] = S.moved_or_merged.fillna(False) | (S.recent60.fillna(0) >= RECENT_MIN) | \
    (S.recent60.fillna(0) >= RECENT_SHARE * S.canonical_recent60.fillna(0).clip(lower=1))
fm = f'{WK}/_redirect_monthly.json'
mon = json.load(open(fm)) if os.path.exists(fm) else {}
todo = sorted(set(S[S.flagged].redirect) - set(mon))
print('redirects flagged', int(S.flagged.sum()), 'monthly to fetch', len(todo), flush=True)
for i, t in enumerate(todo):
    d = per_article(t, 'monthly')
    if d is not None:
        mon[t] = {k[:6]: v for k, v in d.items()}
    if (i + 1) % 100 == 0:
        save_json(mon, fm); print('monthly', i + 1, flush=True)
save_json(mon, fm)

# 3c) keep redirects with real traffic and fetch them daily
own = {}
for t in targets:
    f = f'{DAILY}/{fid(t)}.parquet'
    if os.path.exists(f):
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
    keep.append(share or big); reason.append('share of total' if share else ('large month' if big else 'small'))
    mtot.append(tot)
S['monthly_total'] = mtot; S['keep'] = keep; S['reason'] = reason
save_parquet(S, f'{WK}/redirect_screen.parquet')
todo = [t for t in S[S.keep].redirect.unique() if not os.path.exists(f'{DAILY}/{fid(t)}.parquet')]
print('redirects kept', int(S.keep.sum()), 'daily to fetch', len(todo), flush=True)
for i, t in enumerate(todo):
    fetch_daily(t)
    if (i + 1) % 50 == 0:
        save_json(log, LOG); print('redirect daily', i + 1, flush=True)
save_json(log, LOG)
rec_all = S.recent60.fillna(0).sum() + pd.Series({t: info.get(t, {}).get('recent60', 0) for t in targets}).sum()
print('share of the last 60 days of views on redirects not kept:', round(S[~S.keep].recent60.fillna(0).sum() / max(rec_all, 1), 4))
print('DONE', 'failed', len(log['failed']), 'missing', len(log['missing']), flush=True)
