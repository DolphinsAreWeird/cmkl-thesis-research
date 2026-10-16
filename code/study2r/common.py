"""Shared helpers for Study 2R preparation: paths, identified User-Agent, a cached HTTP client with a global rate limit
(at most 5 requests per second to Wikimedia), text normalisation and Seattle creator parsing.
Run every script from handoff/code with:  nice -n 10 ../.venv/bin/python study2r/NAME.py
"""
import sys, os, re, json, time, hashlib, threading, pathlib, unicodedata
import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from config import D, UA  # noqa: E402

D = pathlib.Path(D)
TAXO = D / 'db' / 'taxonomy_v3'
CACHE = D / 'interim' / 'study2r_cache'
OUT = D / 'db' / 'study2r'
REP = D / 'reports'
WK = D / 'db' / 'interest' / 'wiki'
for p in (CACHE, OUT, REP):
    p.mkdir(parents=True, exist_ok=True)
assert 'kwai@cmkl.ac.th' in UA, 'the User-Agent must name kwai@cmkl.ac.th'
SEED = 20261014
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


class Http:
    """GET/POST with an on-disk cache (200 and 404 answers), a global minimum gap between requests (default 0.21 s,
    i.e. under 5 per second across all threads) and back-off on 429/5xx. SPARQL gets a longer gap (1 s)."""
    def __init__(self, gap=0.21):
        self.s = requests.Session()
        self.s.headers['User-Agent'] = UA
        self.gap = gap
        self.lock = threading.Lock()
        self.last = 0.0
        self.n_net = 0

    def _path(self, key):
        h = hashlib.sha1(key.encode()).hexdigest()
        return CACHE / 'http' / h[:2] / (h + '.json')

    def _wait(self, gap):
        with self.lock:
            w = self.last + gap - time.time()
            if w > 0:
                time.sleep(w)
            self.last = time.time()

    def get(self, url, params=None, data=None, headers=None, gap=None, timeout=100, cache=True):
        key = json.dumps([url, params, data], sort_keys=True)
        p = self._path(key)
        if cache and p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
        for attempt in range(7):
            self._wait(gap or self.gap)
            self.n_net += 1
            try:
                r = self.s.request('POST' if data else 'GET', url, params=params, data=data, headers=headers, timeout=timeout)
            except requests.RequestException:
                time.sleep(4 * (attempt + 1)); continue
            if r.status_code in (200, 404):
                out = {'status': r.status_code, 'text': r.text if r.status_code == 200 else ''}
                if not cache:
                    return out
                p.parent.mkdir(parents=True, exist_ok=True)
                tmp = p.with_suffix('.tmp%d' % threading.get_ident())
                tmp.write_text(json.dumps(out)); os.replace(tmp, p)
                return out
            if r.status_code in (429, 500, 502, 503, 504):
                ra = r.headers.get('Retry-After')
                time.sleep(min(int(ra) if ra and ra.isdigit() else 8 * 2 ** attempt, 240)); continue
            return {'status': r.status_code, 'text': r.text[:300]}
        return {'status': 0, 'text': ''}


H = Http()
SPARQL = 'https://query.wikidata.org/sparql'


def sparql(q):
    """Returns the list of bindings, or None on failure (not cached when failed)."""
    r = H.get(SPARQL, data={'query': q, 'format': 'json'}, headers={'Accept': 'application/sparql-results+json'}, gap=1.1, timeout=130)
    if r['status'] != 200:
        log('  SPARQL failed', r['status'], r['text'][:120].replace('\n', ' '))
        return None
    try:
        return json.loads(r['text'])['results']['bindings']
    except Exception:
        return None


def qid(u):
    return u.rsplit('/', 1)[-1]


# ---------------------------------------------------------------- text helpers (as in study1_seattle/00_coverage_check.py)
def norm(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower().replace('&', ' and ')
    s = re.sub(r'[\W_]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def strip_art(s):
    return re.sub(r'^(the|a|an) ', '', s)


def title_keys(*titles):
    """normalised variants: as is, without a leading article, before a colon or dash subtitle, without a parenthesis"""
    v = set()
    for t in titles:
        if not t:
            continue
        cands = {t, re.sub(r'\s*\([^)]*\)\s*', ' ', t), re.split(r'\s*[:–—]\s+', t)[0]}
        for c in cands:
            n = norm(c)
            if n:
                v.add(n); v.add(strip_art(n))
    return {x for x in v if x}


def parse_creators(c):
    """Family names of every creator in a Seattle creator string (split on ';'), as normalised tokens."""
    out = []
    for part in (c or '').split(';'):
        part = re.sub(r',?\s*(\(?\d{4}\??\)?\s*-\s*(\d{4})?\)?|\(?b\.\s*\d{4}\)?|\(?d\.\s*\d{4}\)?)\s*\.?$', '', part.strip()).strip(' ,.')
        if not part:
            continue
        if ',' in part:
            fam = part.split(',', 1)[0]
        else:
            fam = re.split(r'\s+(?:and|&|with)\s+', part)[0].split()[-1] if part.split() else ''
        n = norm(fam)
        if n:
            out.append(n.split()[-1])
    return out


def isbn13(s):
    """canonical ISBN-13 (digits only) from an ISBN-10 or ISBN-13 with any hyphens; None if invalid"""
    s = re.sub(r'[^0-9Xx]', '', s or '').upper()
    if len(s) == 10 and re.fullmatch(r'\d{9}[\dX]', s):
        b = '978' + s[:9]
    elif len(s) == 13 and re.fullmatch(r'97[89]\d{10}', s):
        b = s[:12]
    else:
        return None
    ck = (10 - sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(b)) % 10) % 10
    return b + str(ck)
