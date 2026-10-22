"""Shared helpers for the Open Library collectors (openlibrary_map.py, openlibrary_reading_log.py).
Polite client: one request at a time, a fixed minimum gap between request starts (Open Library 1.05 s, so at most
1 request a second; Wikidata SPARQL 2 s), the project user agent with a contact address, retries with back-off on
429/5xx/network errors. A shared lock file keeps the two Open Library scripts from running at the same time, so the
combined rate never passes 1 request a second. Stores no personal data: reading-log counts are totals per work."""
import os, re, time, fcntl, pathlib, difflib, unicodedata, requests

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_UA = 'CMKL-thesis-research/0.1 (student project; CMKL University; kwai@cmkl.ac.th)'   # same as code/config.py
OUT = pathlib.Path(os.environ.get('OL_OUT', str(pathlib.Path.home() / 'thesis-collectors' / 'data' / 'openlibrary')))
OL = 'https://openlibrary.org'
WDQS = 'https://query.wikidata.org/sparql'


def user_agent():
    """USER_AGENT from the .env next to this script (or the project's .env one level up); only that line is read."""
    for f in (HERE / '.env', HERE.parent / '.env'):
        if f.exists():
            for line in f.read_text().splitlines():
                if line.startswith('USER_AGENT='):
                    v = line.split('=', 1)[1].split(' #', 1)[0].strip()
                    if v:
                        return v
    return DEFAULT_UA


class Client:
    def __init__(self, gap, log=print):
        self.s = requests.Session()
        self.s.headers.update({'User-Agent': user_agent(), 'Accept': 'application/json'})
        self.gap, self.last, self.n, self.log = gap, 0.0, 0, log
        self.fail_run = 0                      # consecutive requests that failed every retry (network down, Mac asleep)

    def _wait(self):
        w = self.last + self.gap - time.monotonic()
        if w > 0:
            time.sleep(w)
        self.last = time.monotonic()
        self.n += 1

    def get(self, url, params=None, data=None, tries=6, timeout=60):
        """JSON of a 200 (or of a 404 when the body is JSON, e.g. {"error": "notfound"}); None after all retries."""
        for a in range(tries):
            self._wait()
            try:
                r = self.s.post(url, data=data, timeout=timeout) if data is not None else self.s.get(url, params=params, timeout=timeout)
            except requests.RequestException as e:
                self.log(f'  network error {type(e).__name__} on {url} (try {a + 1})')
                time.sleep(min(300, 5 * 2 ** a))
                continue
            if r.status_code in (200, 404):
                try:
                    j = r.json()
                    self.fail_run = 0
                    if r.status_code == 404 and isinstance(j, dict):
                        j.setdefault('error', 'notfound')
                    return j
                except ValueError:
                    if r.status_code == 404:
                        self.fail_run = 0
                        return {'error': 'notfound'}
                    self.log(f'  bad JSON from {url} (try {a + 1})')
            elif r.status_code in (429, 503):
                ra = r.headers.get('Retry-After', '')
                wait = int(ra) if ra.isdigit() else 60 * (a + 1)
                self.log(f'  HTTP {r.status_code} on {url}: waiting {wait} s')
                time.sleep(min(wait, 900))
                continue
            else:
                self.log(f'  HTTP {r.status_code} on {url} (try {a + 1})')
            time.sleep(min(300, 5 * 2 ** a))
        self.fail_run += 1
        return None


def take_lock(name='.openlibrary.lock'):
    """Non-blocking exclusive lock shared by the Open Library scripts; None when another one holds it."""
    OUT.mkdir(parents=True, exist_ok=True)
    f = open(OUT / name, 'w')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        f.close()
        return None
    return f


def check_keys(cli, keys, log=print):
    """Which Open Library work keys are live works. Batch search (100 keys a request), then /works/X.json for keys the
    search index does not return, following redirects (merged works). Returns {key: dict(status, work, title, authors,
    edition_count, readinglog_count)}; status is 'ok', 'redirect' (work = target), 'gone' or 'unknown' (request failed)."""
    out, keys = {}, sorted(set(keys))
    unk = dict(status='unknown', title='', subtitle='', authors=[], edition_count=None, readinglog_count=None)
    for i in range(0, len(keys), 100):
        part = keys[i:i + 100]
        j = cli.get(f'{OL}/search.json', params=dict(q='key:(' + ' OR '.join(f'/works/{k}' for k in part) + ')',
                    fields='key,title,subtitle,author_name,edition_count,readinglog_count', limit=200))
        if j is None:                          # batch failed: treat its keys as live rather than checking each one
            out.update({k: dict(unk, work=k) for k in part})
            continue
        for d in j.get('docs', []):
            k = d['key'].rsplit('/', 1)[-1]
            out[k] = dict(status='ok', work=k, title=d.get('title', ''), subtitle=d.get('subtitle', ''), authors=d.get('author_name', []),
                          edition_count=d.get('edition_count', 0), readinglog_count=d.get('readinglog_count', 0))
        if (i // 100) % 20 == 19:
            log(f'  checked {i + len(part):,} of {len(keys):,} keys')
    for k in keys:
        if k in out:
            continue
        if cli.fail_run >= 5:                  # Open Library not answering: stop checking one by one
            out[k] = dict(unk, work=k)
            continue
        cur, hops, st = k, 0, 'ok'
        while True:
            j = cli.get(f'{OL}/works/{cur}.json')
            if j is None:
                st = 'unknown'; break
            t = (j.get('type') or {}).get('key', '')
            if j.get('error') or t == '/type/delete':
                st = 'gone'; break
            if t == '/type/redirect' and hops < 5:
                cur, hops = str(j.get('location', '')).rsplit('/', 1)[-1], hops + 1
                if not re.fullmatch(r'OL\d+W', cur):
                    st = 'gone'; break
                continue
            if hops:
                st = 'redirect'
            out[k] = dict(status=st, work=cur, title=j.get('title', ''), subtitle=j.get('subtitle', ''), authors=[],
                          edition_count=None, readinglog_count=None)
            break
        if k not in out:                       # 'unknown' (request failed) keeps the key, 'gone' has no work
            out[k] = dict(status=st, work=k if st == 'unknown' else None, title='', subtitle='', authors=[], edition_count=None, readinglog_count=None)
    return out


# ---------- title and author comparison (used to flag match quality) ----------
def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower().replace('&', ' and ')
    s = re.sub(r"['’]", '', s)
    s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    return re.sub(r'^(the|a|an) ', '', s)


def title_main(t):
    t = re.sub(r'\[.*?\]', ' ', str(t or ''))
    t = re.split(r'\s[:/;=]\s|:\s|\s\(', t)[0]
    return re.sub(r'\s+', ' ', t).strip(' .,;:/')


def title_variants(t):
    """Main title of a library title plus forms without catalogue extras: 'The hobbit, or, There and back again',
    'Madeline's rescue; story and pictures by ...', 'The cat in the hat comes back! by Dr. Seuss',
    'Father Bear comes home. Pictures by ...', series forms 'Bone. , Eyes of the storm', 'Thea Stilton. 4, Catching ...'."""
    s = re.sub(r'\[.*?\]', ' ', str(t or ''))
    v = [title_main(s)]
    for pat in (r',\s*or,?\s', r';', r'[.!?]\s+(?:story and pictures|pictures|illustrated|illustrations|story|text|written|by)\b'):
        parts = re.split(pat, s, maxsplit=1, flags=re.I)
        if len(parts) > 1:
            v.append(title_main(parts[0]))
    m = re.match(r'^(.+?)\.\s*(?:\d+\s*)?,\s*(.+)$', s)
    if m:
        v.append(title_main(m.group(2)))
    return [x for x in dict.fromkeys(v) if x]


def title_sim(study_title, cand_title, cand_sub=''):
    """0..1 agreement of the study book's main title with a candidate's title. Also tries the candidate title after a
    series prefix ('Artemis Fowl. The Lost Colony', 'Theodore Boone, The Fugitive', 'Star Wars - Lost Stars') and gives
    0.9 when a study title of two or more words ends the candidate title ('Artemis Fowl and the Eternity Code')."""
    ct = str(cand_title or '')
    best = 0.0
    for v in title_variants(study_title):
        best = max(best, _sim1(norm(v), ct, cand_sub))
    return best


def _sim1(a, ct, cand_sub):
    if not a:
        return 0.0
    cands = {norm(ct), norm(title_main(ct)), norm(f'{ct} {cand_sub or ""}')}
    for sep in ('. ', ', ', ' - ', ': ', ' : '):
        if sep in ct:
            rest = ct.split(sep, 1)[1]
            cands.update({norm(rest), norm(title_main(rest))})
    cands.discard('')
    best = 0.0
    for b in cands:
        best = max(best, 1.0 if a == b else difflib.SequenceMatcher(None, a, b).ratio())
    if best < 0.9 and len(a.split()) >= 2 and any(b.endswith(' ' + a) for b in cands):
        best = 0.9
    return round(best, 3)


_DROP = {'jr', 'sr', 'author', 'editor', 'illustrator', 'phd', 'ph d', 'md', 'm d', 'translator', 'narrator', 'compiler', 'inc', 'ltd', 'llc'}


def author_parts(creator):
    """('First Last', 'last') from a library creator such as 'Mull, Brandon, 1974-' or 'Ashley Flowers'."""
    c = re.sub(r'\(.*?\)|\[.*?\]', ' ', str(creator or ''))
    parts = [p.strip(' .') for p in c.split(',')]
    parts = [p for p in parts if p and not re.search(r'\d', p) and norm(p) not in _DROP]
    if len(parts) >= 2:
        return f'{parts[1]} {parts[0]}', norm(parts[0])
    if parts:
        toks = norm(parts[0]).split()
        return parts[0], (toks[-1] if toks else '')
    return '', ''


_STOP = {'and', 'the', 'inc', 'ltd', 'llc', 'press', 'for', 'associates', 'staff', 'editors'}


def author_agree(study_creator, cand_authors, alt_names=()):
    """True / False, or None when either side has no usable author (no author, or names only in a non-Latin script).
    Surnames match exactly or closely (similarity >= 0.85 for names of 5+ letters: Dostoevsky / Dostoyevsky);
    alt_names are Open Library's alternative names of the candidate's authors (pen names, other spellings)."""
    _, last = author_parts(study_creator)
    toks = [t for t in last.split() if len(t) >= 3 and t not in _STOP] or [t for t in last.split() if t not in _STOP]
    if not toks:
        return None
    have = set(' '.join(norm(a) for a in list(cand_authors or []) + list(alt_names or [])).split())
    if not have:
        return None
    if any(t in have for t in toks):
        return True
    return any(len(t) >= 5 and len(h) >= 5 and difflib.SequenceMatcher(None, t, h).ratio() >= 0.85 for t in toks for h in have)
