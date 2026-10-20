# Shared helpers for the Wikipedia-led Test B data scripts (settings: prereg/wiki_led_settings_2026-10-20.json, section test_B_new_books).
# Paths and the user agent come from code/config.py.  Nothing here fits a model or relates a feature to loans.
import sys, os, re, json, gzip, time, hashlib, threading, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))   # the code/ folder
from config import D, UA   # noqa: E402
import requests            # noqa: E402

D = pathlib.Path(D)
TAXO = D / 'db' / 'taxonomy_v3'
OUT = D / 'db' / 'wiki_led'
CACHE = D / 'interim' / 'wiki_led_cache'
REP = D / 'reports'
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)

T0 = time.time()
BASE_YM = 2005            # month index = (year - 2005) * 12 + month - 1


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def ym_to_idx(ym):
    """201701 -> month index (works on ints and numpy arrays)."""
    return (ym // 100 - BASE_YM) * 12 + (ym % 100) - 1


def idx_to_ym(i):
    return (i // 12 + BASE_YM) * 100 + (i % 12) + 1


class Http:
    """GET with an on-disk cache (gzip, one file per request), a minimum gap per host (thread safe) and back-off.

    rates: {host key: minimum seconds between two requests to that host}.  Only 200 and 404 are cached; an
    error (429, 5xx, maxlag) is retried with a growing pause and never cached.  After max_attempts the call raises,
    so a script stops instead of continuing with holes; a rerun picks up from the cache."""

    def __init__(self, rates, max_attempts=9, adaptive=(), throttle_gap=None, recover=True):
        self.s = requests.Session()
        self.s.headers['User-Agent'] = UA
        self.rates = dict(rates)
        self.base = dict(rates)          # the fastest gap allowed (the stated limit)
        self.adaptive = set(adaptive)    # hosts whose gap grows after a 429 and shrinks again after a run of successes
        self.ok_run = {h: 0 for h in rates}
        self.throttle_gap = throttle_gap  # first 429/5xx episode: the gap becomes at least this (e.g. 0.02 = 50 per second); later episodes halve the rate
        self.recover = recover            # False: the slowed rate is kept for the rest of the run
        self.episodes = {h: 0 for h in rates}
        self.last_change = {h: 0.0 for h in rates}
        self.max_attempts = max_attempts
        self.next_ok = {h: 0.0 for h in rates}
        self.locks = {h: threading.Lock() for h in rates}
        self.n_net = 0
        self.n_cache = 0
        self.n_backoff = 0
        self.codes = {}          # status code (or the exception name) -> count, for the log
        self.cnt_lock = threading.Lock()

    @staticmethod
    def path(url, params):
        key = json.dumps([url, sorted((params or {}).items())], sort_keys=True)
        h = hashlib.sha1(key.encode()).hexdigest()
        return CACHE / 'http' / h[:2] / (h + '.json.gz')

    def _wait(self, host):
        with self.locks[host]:
            now = time.time()
            w = self.next_ok[host] - now
            if w > 0:
                time.sleep(w)
            self.next_ok[host] = max(now, self.next_ok[host]) + self.rates[host]

    def pause(self, host, seconds):
        """Push every thread's next request on this host back (shared back-off)."""
        with self.locks[host]:
            self.next_ok[host] = max(self.next_ok[host], time.time() + seconds)

    def get(self, host, url, params=None, check=None, soft=()):
        """Return (status, text).  check(text) may return a pause in seconds when a 200 body is an API error (maxlag).
        soft: extra statuses (for example 400) that are cached and returned like a 404 instead of raising."""
        p = self.path(url, params)
        if p.exists():
            with self.cnt_lock:
                self.n_cache += 1
            d = json.loads(gzip.decompress(p.read_bytes()))
            return d['status'], d['text']
        for attempt in range(self.max_attempts):
            self._wait(host)
            try:
                r = self.s.get(url, params=params, timeout=90)
            except requests.RequestException as e:
                with self.cnt_lock:
                    self.n_backoff += 1
                    self.codes[type(e).__name__] = self.codes.get(type(e).__name__, 0) + 1
                self.pause(host, 5 * (attempt + 1))
                continue
            with self.cnt_lock:
                self.n_net += 1
                self.codes[r.status_code] = self.codes.get(r.status_code, 0) + 1
            if r.status_code in (200, 404) or r.status_code in soft:
                if host in self.adaptive and self.recover:
                    with self.cnt_lock:
                        self.ok_run[host] += 1
                        if self.ok_run[host] >= 60 and self.rates[host] > self.base[host]:
                            self.rates[host] = max(self.base[host], self.rates[host] * 0.9)
                            self.ok_run[host] = 0
                if r.status_code == 200 and check is not None:
                    wait = check(r.text)
                    if wait:
                        with self.cnt_lock:
                            self.n_backoff += 1
                        ra = r.headers.get('Retry-After')
                        self.pause(host, max(wait, int(ra) if ra and ra.isdigit() else 0))
                        continue
                text = r.text if r.status_code == 200 else ''
                p.parent.mkdir(parents=True, exist_ok=True)
                tmp = p.with_suffix('.tmp%d' % threading.get_ident())
                tmp.write_bytes(gzip.compress(json.dumps({'status': r.status_code, 'text': text}).encode(), 6))
                os.replace(tmp, p)
                return r.status_code, text
            if r.status_code in (429, 500, 502, 503, 504):
                with self.cnt_lock:
                    self.n_backoff += 1
                    if host in self.adaptive:
                        self.ok_run[host] = 0
                        if self.throttle_gap is None:
                            self.rates[host] = min(self.rates[host] * 1.3, 1.0)
                        elif time.time() - self.last_change[host] > 10:      # one slow-down per episode: many requests in flight fail together
                            self.episodes[host] += 1
                            self.last_change[host] = time.time()
                            if self.episodes[host] == 1:
                                self.rates[host] = max(self.rates[host], self.throttle_gap)
                            else:
                                self.rates[host] = min(self.rates[host] * 2, 1.0)      # halve the rate
                            log(f'  throttled by {host} ({r.status_code}); episode {self.episodes[host]}, gap now {self.rates[host]:.3f}s')
                ra = r.headers.get('Retry-After')
                self.pause(host, min(int(ra) if ra and ra.isdigit() else 10 * 2 ** attempt, 300))
                continue
            raise RuntimeError(f'HTTP {r.status_code} for {r.url[:200]}')
        raise RuntimeError(f'gave up after {self.max_attempts} attempts: {url} {str(params)[:120]}')


def maxlag_check(text):
    """For the Action API: a 200 body {"error": {"code": "maxlag"}} means wait and retry."""
    if text.startswith('{"error"'):
        try:
            e = json.loads(text)['error']
        except Exception:
            return 0
        if e.get('code') == 'maxlag':
            return 6
        raise RuntimeError('API error: ' + text[:300])
    return 0
