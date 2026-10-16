#!/usr/bin/env python3
"""Study 1 (Seattle new titles): coverage check of PRE-RELEASE attention signals.

Only the population (first Seattle month per work and format) is used from the borrowing data.
No outcomes are read, modelled or summarised.  See README.md in this folder.

Run from handoff/code:   nice -n 15 ../.venv/bin/python study1_seattle/00_coverage_check.py
Everything fetched is cached under data/interim/study1_coverage_cache/, so a rerun costs nothing.
"""
import sys, os, re, json, time, hashlib, gzip, threading, unicodedata, math, pathlib, datetime as dt
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd, requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from config import D, UA

D = pathlib.Path(D)
DB = D / 'db' / 'taxonomy_v3'
CACHE = D / 'interim' / 'study1_coverage_cache'
REP = D / 'reports'
RL_DONE = D / 'raw' / 'openlibrary' / 'ol_dump_reading-log_2026-09-30.txt.gz'
SEED = 20261014
PER_CELL = 80
FORMATS = ['book', 'ebook', 'audiobook']
YEARS = list(range(2017, 2026))
T0 = time.time()
TEST = int(sys.argv[sys.argv.index('--test') + 1]) if '--test' in sys.argv else 0
SUFFIX = '_test' if TEST else ''


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# ---------------------------------------------------------------- HTTP with cache and 1 request per second per host group
class Http:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers['User-Agent'] = UA
        self.last = {}
        self.locks = {'ol': threading.Lock(), 'wm': threading.Lock()}
        self.n_net = 0

    def _path(self, key):
        h = hashlib.sha1(key.encode()).hexdigest()
        return CACHE / 'http' / h[:2] / (h + '.json')

    def _wait(self, host):
        with self.locks[host]:
            w = 1.05 - (time.time() - self.last.get(host, 0))
            if w > 0:
                time.sleep(w)
            self.last[host] = time.time()

    def get(self, host, url, params=None, data=None, headers=None):
        key = json.dumps([url, params, data], sort_keys=True)
        p = self._path(key)
        if p.exists():
            return json.loads(p.read_text())
        for attempt in range(6):
            cur, hops, r = url, 0, None
            try:
                while True:
                    self._wait(host)
                    self.n_net += 1
                    r = self.s.request('POST' if data else 'GET', cur, params=params if cur == url else None,
                                       data=data, headers=headers, timeout=90, allow_redirects=False)
                    if r.status_code in (301, 302, 303, 307, 308) and hops < 4:
                        cur = urllib.parse.urljoin(cur, r.headers['Location']); hops += 1; continue
                    break
            except requests.RequestException:
                time.sleep(5 * (attempt + 1)); continue
            if r.status_code in (200, 404):
                out = {'status': r.status_code, 'text': r.text if r.status_code == 200 else ''}
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(out))
                return out
            if r.status_code in (429, 500, 502, 503, 504):
                ra = r.headers.get('Retry-After')
                time.sleep(min(int(ra) if ra and ra.isdigit() else 10 * 2 ** attempt, 300)); continue
            return {'status': r.status_code, 'text': ''}
        return {'status': 0, 'text': ''}


H = Http()


# ---------------------------------------------------------------- text helpers
def norm(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower().replace('&', ' and ')
    s = re.sub(r'[\W_]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def strip_art(s):
    return re.sub(r'^(the|a|an) ', '', s)


def title_variants(main, full):
    v = set()
    for t in (main, full):
        n = norm(t)
        if n:
            v.add(n); v.add(strip_art(n))
    return v


def title_ok(cand, variants):
    n = norm(cand)
    return bool(n) and (n in variants or strip_art(n) in variants)


def parse_author(c):
    """Return (display name 'First Last', family name) for the FIRST author of a Seattle creator string, or (None, None)."""
    c = (c or '').strip()
    if not c:
        return None, None
    c = c.split(';')[0]
    c = re.sub(r',?\s*(\(?\d{4}\??\)?\s*-\s*(\d{4})?\)?|\(?b\.\s*\d{4}\)?|\(?d\.\s*\d{4}\)?)\s*\.?$', '', c.strip())
    c = c.strip(' ,.')
    if not c:
        return None, None
    if ',' in c:
        fam, given = [x.strip() for x in c.split(',', 1)]
        given = given.split(',')[0].strip()
        return (f'{given} {fam}'.strip(), fam)
    c = re.split(r'\s+(?:and|&|with)\s+|,\s*', c)[0].strip()
    toks = c.split()
    return (c, toks[-1] if toks else None)


def fam_token(fam):
    n = norm(fam)
    return n.split()[-1] if n else ''


def author_family_ok(fam, names):
    t = fam_token(fam)
    if not t:
        return False
    return any(t in norm(n).split() for n in names)


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


# ---------------------------------------------------------------- 1. population and sample
def build_population():
    w = pd.read_parquet(DB / 'spl_works.parquet', columns=['work_id', 'title', 'creator', 'title_main',
                        'first_ym_book', 'first_ym_ebook', 'first_ym_audiobook', 'pub_year_min'])
    out = []
    for f in FORMATS:
        c = 'first_ym_' + f
        x = w[w[c].between(201701, 202506) & w.pub_year_min.notna()].copy()
        x['cohort_year'] = (x[c] // 100).astype(int)
        x = x[x.pub_year_min >= x.cohort_year - 1]
        x['format'] = f
        x['first_ym'] = x[c].astype(int)
        out.append(x[['work_id', 'format', 'cohort_year', 'first_ym', 'pub_year_min', 'title', 'creator', 'title_main']])
    return pd.concat(out, ignore_index=True)


def build_sample(pop):
    rng = np.random.RandomState(SEED)
    parts = []
    for f in FORMATS:
        for y in YEARS:
            g = pop[(pop.format == f) & (pop.cohort_year == y)].sort_values('work_id')
            n = min(PER_CELL, len(g))
            idx = np.sort(rng.choice(len(g), n, replace=False))
            parts.append(g.iloc[idx])
    return pd.concat(parts, ignore_index=True)


def attach_isbns(sample):
    rw = pd.read_parquet(DB / 'spl_record_work.parquet')
    rw = rw[rw.work_id.isin(sample.work_id.unique())]
    r = pd.read_parquet(DB / 'spl_records.parquet', columns=['record_id', 'isbn'])
    r = r[r.isbn.str.len().isin([10, 13])]
    r = r.merge(rw, on='record_id')
    r['isbn'] = r.isbn.str.replace('-', '', regex=False).str.upper()
    r = r[r.isbn.str.fullmatch(r'(97[89]\d{10}|\d{9}[\dX])')]
    r['is13'] = r.isbn.str.len() == 13
    r = r.sort_values(['work_id', 'is13'], ascending=[True, False]).drop_duplicates(['work_id', 'isbn'])
    d = r.groupby('work_id').isbn.apply(list).to_dict()
    return d


# ---------------------------------------------------------------- 2. Open Library match
def ol_match(work):
    """work: dict with isbns, title, title_main, creator.  Returns dict of match fields."""
    res = {'ol_key': None, 'ol_method': 'none', 'ol_isbn_tried': 0, 'ol_title': None, 'ol_title_agree': None,
           'ol_first_pub_year': None}
    var = title_variants(work['main'], work['title'])
    for isbn in work['isbns'][:3]:
        res['ol_isbn_tried'] += 1
        r = H.get('ol', f'https://openlibrary.org/isbn/{isbn}.json')
        if r['status'] == 200:
            try:
                j = json.loads(r['text'])
                k = j['works'][0]['key']
            except Exception:
                continue
            res.update(ol_key=k, ol_method='isbn', ol_title=j.get('title'))
            res['ol_title_agree'] = bool(j.get('title')) and (title_ok(j['title'], var) or
                                    any(v in norm(j['title']) for v in var if len(v) > 4))
            return res
    name, fam = work['author'], work['family']
    if not fam:
        res['ol_method'] = 'none_no_author'
        return res
    q = {'title': work['main'], 'author': fam, 'fields': 'key,title,author_name,first_publish_year', 'limit': 5}
    r = H.get('ol', 'https://openlibrary.org/search.json', params=q)
    if r['status'] == 200:
        try:
            docs = json.loads(r['text']).get('docs', [])
        except Exception:
            docs = []
        for d in docs:
            if title_ok(d.get('title', ''), var) and author_family_ok(fam, d.get('author_name', [])):
                res.update(ol_key=d['key'], ol_method='search', ol_title=d.get('title'), ol_title_agree=True,
                           ol_first_pub_year=d.get('first_publish_year'))
                break
    return res


def run_ol(works):
    out = {}
    for i, (wid, w) in enumerate(works.items()):
        out[wid] = ol_match(w)
        if i % 200 == 0:
            log(f'  OL {i}/{len(works)} (network calls {H.n_net})')
    return out


# ---------------------------------------------------------------- 3. Wikidata and Wikipedia
WD_API = 'https://www.wikidata.org/w/api.php'
SPARQL = 'https://query.wikidata.org/sparql'
WP_API = 'https://en.wikipedia.org/w/api.php'


def wb_search(term):
    p = {'action': 'wbsearchentities', 'search': term, 'language': 'en', 'uselang': 'en', 'type': 'item',
         'limit': 15, 'format': 'json'}
    r = H.get('wm', WD_API, params=p)
    if r['status'] != 200:
        return []
    try:
        return json.loads(r['text']).get('search', [])
    except Exception:
        return []


def run_wm_search(works, authors):
    book_hits, auth_hits = {}, {}
    for i, (wid, w) in enumerate(works.items()):
        book_hits[wid] = wb_search(w['main']) if norm(w['main']) else []
        if i % 200 == 0:
            log(f'  Wikidata title search {i}/{len(works)}')
    for i, a in enumerate(authors):
        auth_hits[a] = wb_search(a)
        if i % 200 == 0:
            log(f'  Wikidata author search {i}/{len(authors)}')
    return book_hits, auth_hits


def sparql(q):
    r = H.get('wm', SPARQL, data={'query': q, 'format': 'json'}, headers={'Accept': 'application/sparql-results+json'})
    if r['status'] != 200:
        log('  SPARQL failed, status', r['status'])
        return None
    try:
        return json.loads(r['text'])['results']['bindings']
    except Exception:
        return None


def qid(u):
    return u.rsplit('/', 1)[-1]


def values_q(items):
    return ' '.join('wd:' + i for i in items)


def hyphen_variants(isbn):
    """Wikidata stores most ISBNs with hyphens; generate the plausible hyphenations (plus the compact form)."""
    v = {isbn}
    if len(isbn) == 13:
        pre, rest = isbn[:3], isbn[3:]
    else:
        pre, rest = '', isbn
    body, chk = rest[:-1], rest[-1]
    glens = [1] if body[0] in '01' and (len(isbn) == 10 or pre == '978') else [1, 2, 3]
    for a in glens:
        for b in range(2, 8):
            c = len(body) - a - b
            if c < 1:
                continue
            parts = [pre] if pre else []
            parts += [body[:a], body[a:a + b], body[a + b:], chk]
            v.add('-'.join(parts))
    return v


def batches(seq, n):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


CLASSES = 'wd:Q47461344 wd:Q7725634 wd:Q3331189 wd:Q571 wd:Q8261'  # written work, literary work, edition, book, novel
OCCS = 'wd:Q36180 wd:Q482980 wd:Q49757 wd:Q1930187'  # writer (incl. subclasses), author, poet, journalist


def wd_isbn_items(isbns):
    """ISBN -> set of Wikidata items through P212 / P957."""
    res = {}
    vmap = {}
    for isbn in isbns:
        for v in hyphen_variants(isbn):
            vmap.setdefault(v, isbn)
    allv = sorted(vmap)
    for b in batches(allv, 400):
        vals = ' '.join('"%s"' % x for x in b)
        q = f'SELECT ?item ?v WHERE {{ VALUES ?v {{ {vals} }} ?item wdt:P212|wdt:P957 ?v }}'
        rows = sparql(q)
        for r in rows or []:
            res.setdefault(vmap[r['v']['value']], set()).add(qid(r['item']['value']))
    return res


def wd_ol_items(olids):
    res = {}
    for b in batches(sorted(olids), 200):
        vals = ' '.join('"%s"' % x for x in b)
        rows = sparql(f'SELECT ?item ?v WHERE {{ VALUES ?v {{ {vals} }} ?item wdt:P648 ?v }}')
        for r in rows or []:
            res.setdefault(r['v']['value'], set()).add(qid(r['item']['value']))
    return res


def wd_class_ok(items):
    ok = set()
    for b in batches(sorted(items), 150):
        rows = sparql(f'SELECT DISTINCT ?item WHERE {{ VALUES ?item {{ {values_q(b)} }} '
                      f'?item wdt:P31/wdt:P279* ?c . VALUES ?c {{ {CLASSES} }} }}')
        for r in rows or []:
            ok.add(qid(r['item']['value']))
    return ok


def wd_info(items):
    """label, edition-of work, authors (id, label), English Wikipedia title for each item."""
    info = {}
    for b in batches(sorted(items), 100):
        q = f'''SELECT ?item ?lab ?work ?auth ?authlab ?art WHERE {{ VALUES ?item {{ {values_q(b)} }}
          OPTIONAL {{ ?item rdfs:label ?lab FILTER(lang(?lab) IN ("en","mul")) }}
          OPTIONAL {{ ?item wdt:P629 ?work }}
          OPTIONAL {{ ?item wdt:P50 ?auth . OPTIONAL {{ ?auth rdfs:label ?authlab FILTER(lang(?authlab) IN ("en","mul")) }} }}
          OPTIONAL {{ ?art schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }} }}'''
        for r in sparql(q) or []:
            i = qid(r['item']['value'])
            d = info.setdefault(i, {'label': None, 'work': set(), 'auth': {}, 'art': None})
            if 'lab' in r: d['label'] = r['lab']['value']
            if 'work' in r: d['work'].add(qid(r['work']['value']))
            if 'auth' in r: d['auth'][qid(r['auth']['value'])] = r.get('authlab', {}).get('value', '')
            if 'art' in r: d['art'] = urllib.parse.unquote(r['art']['value'].rsplit('/wiki/', 1)[-1]).replace('_', ' ')
    return info


def wd_author_info(items):
    info = {}
    for b in batches(sorted(items), 100):
        q = f'''SELECT ?item ?lab ?art ?occ ?wk WHERE {{ VALUES ?item {{ {values_q(b)} }} ?item wdt:P31 wd:Q5 .
          OPTIONAL {{ ?item rdfs:label ?lab FILTER(lang(?lab) IN ("en","mul")) }}
          OPTIONAL {{ ?art schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }}
          BIND(EXISTS {{ ?item wdt:P106/wdt:P279* ?o . VALUES ?o {{ {OCCS} }} }} AS ?occ)
          BIND(EXISTS {{ ?item wdt:P800 ?w }} AS ?wk) }}'''
        for r in sparql(q) or []:
            i = qid(r['item']['value'])
            d = info.setdefault(i, {'label': None, 'art': None, 'occ': False, 'wk': False})
            if 'lab' in r: d['label'] = r['lab']['value']
            if 'art' in r: d['art'] = urllib.parse.unquote(r['art']['value'].rsplit('/wiki/', 1)[-1]).replace('_', ' ')
            d['occ'] = d['occ'] or r['occ']['value'] == 'true'
            d['wk'] = d['wk'] or r['wk']['value'] == 'true'
    return info


def wp_created(titles):
    out = {}
    for i, t in enumerate(sorted(titles)):
        p = {'action': 'query', 'prop': 'revisions', 'titles': t, 'rvprop': 'timestamp', 'rvdir': 'newer',
             'rvlimit': 1, 'format': 'json', 'formatversion': 2}
        r = H.get('wm', WP_API, params=p)
        ts = None
        if r['status'] == 200:
            try:
                pg = json.loads(r['text'])['query']['pages'][0]
                ts = pg['revisions'][0]['timestamp']
            except Exception:
                ts = None
        out[t] = ts
        if i % 200 == 0:
            log(f'  Wikipedia creation dates {i}/{len(titles)}')
    return out


def resolve_wikidata(works, ol, book_hits, auth_hits):
    """Per work: Wikidata book item and article, author item and article."""
    # --- book items by three routes
    isbn_items = wd_isbn_items({i for w in works.values() for i in w['isbns'][:3]})
    log(f'  ISBN route: {len(isbn_items)} ISBNs hit Wikidata')
    ol_items = wd_ol_items({o['ol_key'].rsplit('/', 1)[-1] for o in ol.values() if o['ol_key']})
    log(f'  OL id route: {len(ol_items)} OL works hit Wikidata')
    cand = {}  # wid -> list of (item, label) passing title filter
    for wid, w in works.items():
        var = title_variants(w['main'], w['title'])
        c = []
        for h in book_hits.get(wid, []):
            texts = [h.get('label', '')] + [h.get('match', {}).get('text', '')]
            if any(title_ok(t, var) for t in texts):
                c.append(h['id'])
        cand[wid] = c
    class_ok = wd_class_ok({i for c in cand.values() for i in c})
    items = set(class_ok)
    for s in isbn_items.values(): items |= s
    for s in ol_items.values(): items |= s
    info = wd_info(items)
    works_needed = {x for d in info.values() for x in d['work']} - set(info)
    info.update(wd_info(works_needed))
    # --- choose
    book = {}
    for wid, w in works.items():
        got = {'wd_item_isbn': None, 'wd_item_ol': None, 'wd_item_title': None}
        for isbn in w['isbns'][:3]:
            if isbn in isbn_items:
                got['wd_item_isbn'] = sorted(isbn_items[isbn])[0]; break
        ok = ol.get(wid, {}).get('ol_key')
        if ok and ok.rsplit('/', 1)[-1] in ol_items:
            got['wd_item_ol'] = sorted(ol_items[ok.rsplit('/', 1)[-1]])[0]
        for i in cand[wid]:
            if i in class_ok:
                d = info.get(i, {})
                names = list(d.get('auth', {}).values())
                for wk in d.get('work', ()):
                    names += list(info.get(wk, {}).get('auth', {}).values())
                if w['family'] and author_family_ok(w['family'], names):
                    got['wd_item_title'] = i; break
        for m, k in (('isbn', 'wd_item_isbn'), ('ol_id', 'wd_item_ol'), ('title_author', 'wd_item_title')):
            if got[k]:
                got['wd_item'], got['wd_method'] = got[k], m; break
        else:
            got['wd_item'], got['wd_method'] = None, 'none'
        i = got['wd_item']
        got.update(wd_label=None, wd_art=None, wd_book_authors=[])
        if i:
            d = info.get(i, {})
            got['wd_label'] = d.get('label')
            art = d.get('art')
            auths = dict(d.get('auth', {}))
            for wk in d.get('work', ()):
                wd_ = info.get(wk, {})
                art = wd_.get('art') or art          # article usually sits on the work item
                auths.update(wd_.get('auth', {}))
            got['wd_art'] = art
            got['wd_book_authors'] = sorted(auths)
        book[wid] = got
    # --- authors
    a_cand = {}
    for wid, w in works.items():
        a = w['author']
        if not a:
            continue
        key = norm(a).replace(' ', '')
        if not key:
            a_cand[wid] = []
            continue
        c = []
        for h in auth_hits.get(a, []):
            if any(norm(t).replace(' ', '') == key for t in [h.get('label', ''), h.get('match', {}).get('text', '')] if t):
                c.append(h['id'])
        a_cand[wid] = c
    a_info = wd_author_info({i for c in a_cand.values() for i in c} | {i for b in book.values() for i in b['wd_book_authors']})
    author = {}
    for wid, w in works.items():
        res = {'au_item': None, 'au_label': None, 'au_art': None, 'au_corroborated': False, 'au_n_cand': 0, 'au_method': 'none'}
        if not w['author']:
            res['au_method'] = 'no_creator'
        else:
            good = [i for i in a_cand.get(wid, []) if a_info.get(i, {}).get('art') and (a_info[i]['occ'] or a_info[i]['wk'])]
            res['au_n_cand'] = len(good)
            corro = [i for i in good if i in book[wid]['wd_book_authors']]
            pick = corro[0] if corro else (good[0] if good else None)
            if pick:
                d = a_info[pick]
                res.update(au_item=pick, au_label=d['label'], au_art=d['art'], au_corroborated=bool(corro),
                           au_method='name_occupation' + ('_book_author' if corro else ''))
        author[wid] = res
    # --- creation dates
    titles = {b['wd_art'] for b in book.values() if b['wd_art']} | {a['au_art'] for a in author.values() if a['au_art']}
    created = wp_created(titles)
    for b in book.values(): b['wd_art_created'] = created.get(b['wd_art'])
    for a in author.values(): a['au_art_created'] = created.get(a['au_art'])
    return book, author


# ---------------------------------------------------------------- 4. reading-log counts (work level only)
def reading_log_counts(rows):
    """rows: DataFrame with row_id, ol_key, first_ym.  Returns {row_id: (n_before, n_26w)}.  User fields never read."""
    cut = {}
    for r in rows.itertuples():
        c = dt.date(r.first_ym // 100, r.first_ym % 100, 1)
        cut.setdefault(r.ol_key, []).append((r.row_id, c.isoformat(), (c - dt.timedelta(days=182)).isoformat()))
    cnt = {r.row_id: [0, 0] for r in rows.itertuples()}
    n = 0
    with gzip.open(RL_DONE, 'rt', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            n += 1
            k = line.split('\t', 1)[0]
            if k in cut:
                p = line.rstrip('\n').split('\t')
                if len(p) < 4:
                    continue
                d = p[3][:10]
                for rid, c, s in cut[k]:
                    if d < c:
                        cnt[rid][0] += 1
                        if d >= s:
                            cnt[rid][1] += 1
    log(f'  reading-log lines scanned: {n:,}')
    return {k: tuple(v) for k, v in cnt.items()}


# ---------------------------------------------------------------- assemble
def assemble(sample, ol, book, author, rl):
    rows = []
    for r in sample.itertuples():
        wid = r.work_id
        o, b, a = ol[wid], book[wid], author[wid]
        start = dt.datetime(r.first_ym // 100, r.first_ym % 100, 1)
        lim = start - dt.timedelta(days=28)

        def ok(ts):
            return bool(ts) and dt.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ') <= lim
        d = dict(work_id=wid, format=r.format, cohort_year=r.cohort_year, cohort_month=r.first_ym, pub_year_min=int(r.pub_year_min),
                 title=r.title, creator=r.creator, author_parsed=parse_author(r.creator)[0],
                 has_isbn=bool(sample_isbns.get(wid)), n_isbn_tried=o['ol_isbn_tried'],
                 ol_work=o['ol_key'], ol_method=o['ol_method'], ol_title=o['ol_title'], ol_title_agree=o['ol_title_agree'],
                 ol_first_pub_year=o['ol_first_pub_year'])
        k = (r.format, wid)
        d['rl_before'], d['rl_26w'] = rl.get(k, (np.nan, np.nan)) if o['ol_key'] else (np.nan, np.nan)
        d['rl_any'] = False if not o['ol_key'] else (np.nan if np.isnan(d['rl_before']) else bool(d['rl_before'] > 0))
        d.update(wd_book_method=b['wd_method'], wd_book_item=b['wd_item'], wd_item_isbn=b['wd_item_isbn'], wd_item_ol=b['wd_item_ol'],
                 wd_item_title=b['wd_item_title'], wd_book_label=b['wd_label'], wp_book_article=b['wd_art'],
                 wp_book_created=b['wd_art_created'], book_article_4w=ok(b['wd_art_created']))
        d.update(author_method=a['au_method'], author_item=a['au_item'], author_label=a['au_label'], author_n_cand=a['au_n_cand'],
                 author_corroborated=a['au_corroborated'], wp_author_article=a['au_art'], wp_author_created=a['au_art_created'],
                 author_article_4w=ok(a['au_art_created']))
        rows.append(d)
    df = pd.DataFrame(rows)
    df['any_signal_excl_rl'] = df.book_article_4w | df.author_article_4w
    df['any_signal'] = df.any_signal_excl_rl | (df.rl_any == True)
    return df


# ---------------------------------------------------------------- report
def cell(x):
    return '' if (x is None or (isinstance(x, float) and math.isnan(x))) else str(x).replace('|', '/')


def pct(k, n):
    if n == 0:
        return 'n/a'
    lo, hi = wilson(k, n)
    return f'{100*k/n:.0f}% ({100*lo:.0f}-{100*hi:.0f})'


def pooled(df, pop_n, col, fmt, mask=None):
    """Population-weighted share over the nine cohort years with a stratified normal interval."""
    est, var, N = 0.0, 0.0, 0
    for y in YEARS:
        g = df[(df.format == fmt) & (df.cohort_year == y)]
        Ny = pop_n.get((fmt, y), 0)
        if len(g) == 0 or Ny == 0:
            continue
        p = g[col].astype(float).mean()
        est += Ny * p; var += Ny ** 2 * p * (1 - p) / len(g); N += Ny
    if N == 0:
        return 'n/a'
    p, se = est / N, math.sqrt(var) / N
    return f'{100*p:.0f}% ({100*max(0,p-1.96*se):.0f}-{100*min(1,p+1.96*se):.0f})'


def write_report(df, pop, rl_ok, runtime, sample_isbns):
    pop_n = pop.groupby(['format', 'cohort_year']).size().to_dict()
    L = []
    L += ['# Study 1 (Seattle new titles): coverage of pre-release attention signals', '',
          'Author: Khant Phyo Wai (CMKL University, 01323050). Coverage check only: no borrowing outcomes were read or modelled.', '',
          f'Run on {dt.date.today().isoformat()}; sample seed {SEED}; run time {runtime/60:.0f} minutes.', '',
          '## What was measured', '',
          'A new title in a format is a work whose first Seattle month in that format falls in 2017-01 to 2025-06 and whose earliest '
          'publication year is at most one year before the year of that first month. The first day of the first Seattle month stands in for the release date. '
          'Each cell below (format by cohort year) holds a random sample of 80 works (all works if fewer). Shares are out of the sampled works, '
          'with Wilson 95% intervals in brackets. A work with no creator on its Seattle record cannot have an author signal and counts as "no".', '',
          'Signals: (1) Open Library reading-log entries dated before the first Seattle month; (2) an English Wikipedia article about the book that was '
          'created at least 4 weeks before that month; (3) the same for the first author. "Any signal" is one of the three.', '']
    if not rl_ok:
        L += ['**The Open Library reading-log dump was not complete when this report was written, so the reading-log columns are empty and "any signal" '
              'below uses the two Wikipedia signals only.**', '']
    # population
    L += ['## Population and sample', '', '| format | ' + ' | '.join(str(y) for y in YEARS) + ' | total |', '|---|' + '---|' * (len(YEARS) + 1)]
    for f in FORMATS:
        L.append(f'| {f} | ' + ' | '.join(f'{pop_n.get((f, y), 0):,}' for y in YEARS) + f' | {sum(pop_n.get((f, y), 0) for y in YEARS):,} |')
    L += ['', 'Counts are works (one Seattle title family, all editions together). The 2020 book cohort is small and the 2021 book cohort is large; '
          'this follows the Seattle first-month dates in the data and has not been investigated here.', '',
          f'Sampled works: {len(df):,} rows ({df.work_id.nunique():,} distinct works; a work can be drawn in more than one format).', '']

    def table(title, cols, note=None):
        out = ['## ' + title, '', '| format | cohort | n | ' + ' | '.join(c[0] for c in cols) + ' |', '|---|---|---|' + '---|' * len(cols)]
        for f in FORMATS:
            for y in YEARS:
                g = df[(df.format == f) & (df.cohort_year == y)]
                out.append(f'| {f} | {y} | {len(g)} | ' + ' | '.join(c[1](g) for c in cols) + ' |')
            out.append(f'| {f} | pooled | {len(df[df.format == f])} | ' + ' | '.join(c[2](f) for c in cols) + ' |')
        if note:
            out += ['', note]
        return out + ['']

    def share(col, val=True):
        return (lambda g: pct(int((g[col] == val).sum()), len(g)))

    def pool(col):
        return lambda f: pooled(df, pop_n, col, f)
    df = df.copy()
    df['ol_any'] = df.ol_work.notna()
    df['wd_found'] = df.wd_book_item.notna()
    df['has_creator'] = df.creator.fillna('').str.strip().ne('')
    df['ol_isbn'] = df.ol_method == 'isbn'
    df['ol_search'] = df.ol_method == 'search'
    L += table('Open Library match', [('any match', share('ol_any'), pool('ol_any')), ('by ISBN', share('ol_isbn'), pool('ol_isbn')),
                                       ('by title and author', share('ol_search'), pool('ol_search'))],
               'Pooled rows weight each cohort year by its population size (stratified estimate and interval).')
    if rl_ok:
        def med(g):
            m = g[g.ol_any]
            return f'{m.rl_before.median():.0f} / {m.rl_26w.median():.0f}' if len(m) else 'n/a'

        def medp(f):
            m = df[(df.format == f) & df.ol_any]
            return f'{m.rl_before.median():.0f} / {m.rl_26w.median():.0f}'

        def med1(g):
            m = g[g.rl_before > 0]
            return f'{m.rl_before.median():.0f} / {m.rl_26w.median():.0f} (n={len(m)})' if len(m) else 'n/a'

        def med1p(f):
            m = df[(df.format == f) & (df.rl_before > 0)]
            return f'{m.rl_before.median():.0f} / {m.rl_26w.median():.0f} (n={len(m)})' if len(m) else 'n/a'
        L += table('Reading-log entries before release', [('any entry before release', share('rl_any'), pool('rl_any')),
                   ('median count, all time / last 26 weeks (Open Library matches)', med, medp),
                   ('median count among works with at least one entry', med1, med1p)],
                   'The first median is over works with an Open Library match and counts zeros. The second is over works with at least one entry before release. Shares are out of all sampled works.')
    L += table('Wikipedia article about the book, created 4+ weeks before release', [('book article', share('book_article_4w'), pool('book_article_4w')),
               ('Wikidata item found', share('wd_found'), pool('wd_found'))])
    L += table('Wikipedia article about the author, created 4+ weeks before release', [('author article', share('author_article_4w'), pool('author_article_4w')),
               ('has creator', share('has_creator'), pool('has_creator'))])
    L += table('At least one signal', [('any signal', share('any_signal'), pool('any_signal')),
               ('Wikipedia signals only', share('any_signal_excl_rl'), pool('any_signal_excl_rl'))])
    # trend lines
    L += ['## Trend in "any signal" by cohort year (sample share, %)', '', '| format | ' + ' | '.join(str(y) for y in YEARS) + ' |', '|---|' + '---|' * len(YEARS)]
    for f in FORMATS:
        L.append(f'| {f} | ' + ' | '.join(f'{100*df[(df.format==f)&(df.cohort_year==y)].any_signal.mean():.0f}' for y in YEARS) + ' |')
    L.append('')
    # quality
    u = df.drop_duplicates('work_id')
    isb = u[u.ol_method == 'isbn']
    L += ['## Match quality', '',
          f'- Distinct sampled works: {len(u):,}. With at least one valid ISBN on any record: {100*u.has_isbn.mean():.0f}%. Print-only works have no ISBN, so they depend on the title and author search.',
          f'- Open Library: {int((u.ol_method=="isbn").sum())} by ISBN, {int((u.ol_method=="search").sum())} by title and author search, {int(u.ol_method.str.startswith("none").sum())} without a match '
          f'({int((u.ol_method=="none_no_author").sum())} of these had no creator and no usable ISBN, so the search was not tried).',
          f'- Of the ISBN matches, {100*isb.ol_title_agree.astype(float).mean():.0f}% have an Open Library edition title that agrees with the Seattle title; the rest may be a wrong ISBN on a Seattle record or a different title for the same work.',
          '- Title and author search accepts a hit only when the normalised title equals the Seattle main title or full title (leading "The", "A" or "An" ignored) and the author family name appears in the Open Library author list. This is strict, so it misses retitled editions and works with the author in a different spelling, and it can still accept a different book with the same title by a relative with the same family name.',
          f'- Wikidata book item found for {int(u.wd_book_item.notna().sum())} works ({int((u.wd_book_method=="isbn").sum())} by ISBN, {int((u.wd_book_method=="ol_id").sum())} through the Open Library ID, {int((u.wd_book_method=="title_author").sum())} by title and author). Wikidata mostly stores ISBNs with hyphens, so the script tries the plausible hyphenations of each ISBN.',
          f'- Book article found for {int(u.wp_book_article.notna().sum())} works. The article date is the first revision of the page at its current title; a page first created as a redirect or stub counts from that first revision.',
          f'- Author: {int(u.author_item.notna().sum())} works have a Wikidata person with an English article, matched on exact name (case, accents and punctuation ignored) plus a writing occupation or a notable work; {int(u.author_corroborated.sum())} of these are confirmed by the book item naming the same person as author. '
          f'{int((u.author_n_cand>1).sum())} works had more than one qualifying namesake (the first was used). Exact name matching misses authors whose Seattle name includes a middle name or initial that Wikidata lacks, and it can match a different person with the same name.',
          f'- {int(u.creator.fillna("").str.strip().eq("").sum())} sampled works have no creator on the Seattle record, so no author match was possible.',
          '- The reading-log dump holds the current state of each user shelf, so entries are dated by when the user added the book. Open Library merges duplicate works over time and the dump uses current keys; a key from an old match may be redirected and show a count of zero.' if rl_ok else
          '- The reading-log columns are empty (dump incomplete).',
          '']
    # check lists
    rs = np.random.RandomState(SEED + 1)
    bm = u[u.wd_book_item.notna()]
    am = u[u.author_item.notna()]
    L += ['## Book matches to check by hand (random 30)', '', '| title | creator | method | matched item | Wikipedia article |', '|---|---|---|---|---|']
    for r in bm.iloc[rs.permutation(len(bm))[:30]].itertuples():
        L.append(f'| {cell(r.title[:70])} | {cell(r.creator)} | {r.wd_book_method} | {r.wd_book_item} {cell(r.wd_book_label)} | {cell(r.wp_book_article)} |')
    L += ['', '## Author matches to check by hand (random 30)', '', '| title | creator | method | matched item | Wikipedia article |', '|---|---|---|---|---|']
    for r in am.iloc[rs.permutation(len(am))[:30]].itertuples():
        L.append(f'| {cell(r.title[:70])} | {cell(r.creator)} | {r.author_method}, {r.author_n_cand} candidate(s) | {r.author_item} {cell(r.author_label)} | {cell(r.wp_author_article)} |')
    L.append('')
    (REP / f'study1_seattle_coverage{SUFFIX}.md').write_text('\n'.join(L), encoding='utf-8')


# ---------------------------------------------------------------- main
def main():
    global sample_isbns
    CACHE.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    pop = build_population()
    sample = build_sample(pop)
    if TEST:
        sample = sample.sample(TEST, random_state=1).sort_values(['format', 'cohort_year']).reset_index(drop=True)
    sample.to_csv(CACHE / f'sample_list{SUFFIX}.csv', index=False)
    log(f'population {len(pop):,}; sample {len(sample):,} rows, {sample.work_id.nunique():,} works')
    sample_isbns = attach_isbns(sample)
    u = sample.drop_duplicates('work_id')
    works = {}
    for r in u.itertuples():
        name, fam = parse_author(r.creator)
        main_t = re.split(r':\s', r.title)[0].strip()
        main_t = re.sub(r'\s*\([^)]*\)\s*$', '', main_t).strip() or r.title_main
        works[r.work_id] = dict(isbns=sample_isbns.get(r.work_id, []), title=r.title, main=main_t, author=name, family=fam)
    authors = sorted({w['author'] for w in works.values() if w['author']})
    log(f'{len(works):,} distinct works, {len(authors):,} distinct author names')
    with ThreadPoolExecutor(2) as ex:
        f1 = ex.submit(run_ol, works)
        f2 = ex.submit(run_wm_search, works, authors)
        ol = f1.result(); book_hits, auth_hits = f2.result()
    log('Open Library and Wikidata searches done; resolving on Wikidata and Wikipedia')
    book, author = resolve_wikidata(works, ol, book_hits, auth_hits)
    for v in ol.values():
        v['ol_key_present'] = bool(v['ol_key'])
    log(f'network calls this run: {H.n_net}; elapsed {(time.time()-T0)/60:.1f} min')
    # preliminary outputs without reading log
    df = assemble(sample, ol, book, author, {})
    df['ol_key_present'] = df.ol_work.notna()
    if not RL_DONE.exists():
        write_report(df, pop, False, time.time() - T0, sample_isbns)   # preliminary, without reading log
    waited = 0
    while not TEST and not RL_DONE.exists() and waited < 3 * 3600:
        log('reading-log dump not complete; waiting 10 minutes'); time.sleep(600); waited += 600
    rl_ok = RL_DONE.exists()
    rl = {}
    if rl_ok:
        m = df[df.ol_work.notna()].copy()
        m['row_id'] = list(zip(m.format, m.work_id))
        rl = reading_log_counts(pd.DataFrame({'row_id': m.row_id, 'ol_key': m.ol_work, 'first_ym': m.cohort_month}))
        df = assemble(sample, ol, book, author, rl)
        df['ol_key_present'] = df.ol_work.notna()
    else:
        log('READING LOG DUMP STILL INCOMPLETE after 3 hours: reading-log columns left empty')
    out = df.drop(columns=['ol_key_present'], errors='ignore').copy()
    out.to_csv(REP / f'study1_seattle_coverage{SUFFIX}.csv', index=False)
    write_report(df, pop, rl_ok, time.time() - T0, sample_isbns)
    log('wrote reports; total minutes', round((time.time() - T0) / 60, 1))
    if not rl_ok:
        sys.exit(2)


sample_isbns = {}
if __name__ == '__main__':
    main()
