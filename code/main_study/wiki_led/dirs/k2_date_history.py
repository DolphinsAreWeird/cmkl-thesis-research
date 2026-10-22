#!/usr/bin/env python3
"""K2 of addendum k (dates known in time): were the film and television adaptation release dates used by D2 and addendum j already in Wikidata
before the releases, so that an alert list could really have known them in advance?

Settings: prereg/addenda_wiki_led/2026-10-22_k_intent_dates_human.json, section K2_dates_known_in_time (read-only; SHA-256 checked below).
Descriptive.  No model is fitted.  Every interval is a 95% interval.
Run from handoff/code:   ../.venv/bin/python main_study/wiki_led/dirs/k2_date_history.py            (fetch, then analysis and report)
   detached:             bash ../jobs/bg.sh k2_wd_revisions main_study/wiki_led/dirs/k2_date_history.py
   options:              --test N   only N items (no outputs written except the cache and a short log);  --no-fetch  analysis from the cache only
                         (items not in the cache are reported as not done, with the coverage).
Outputs: data/db/wiki_led/dirs/k2_dates/ (tables, k2_results.json) and the report data/reports/dir_k2_dates.md (written by this script).

Source: the Wikidata Action API (https://www.wikidata.org/w/api.php, action=query&prop=revisions on the item page), maxlag=5, at most 2 requests
a second (one request at a time, at least 0.5 s between the starts of two requests), the project user agent from code/config.py.  Every answer
is cached under data/interim/k2_wikidata_revisions/ (gzip, one file per request), so a rerun makes no request.  Only revision ids, timestamps,
sizes and the item content are requested: no user names, no edit comments.  This is not the Wikimedia REST pageviews API.

Fixed by the record: the items (every film or tv adaptation release used by D2 and addendum j, release month 2016-01 to 2026-09), the event
(the first revision whose statements carry the release date used: P577 or P580 at month precision or finer, same month), the measures (share in
Wikidata before the release month, 1 month before, 3 months before; D2's release-alert shares, rose and surged in t+1..t+3, re-scored on alerts
whose date was already in Wikidata at the alert's origin month, beside all alerts).  The caller added: lead-time distribution, the share of
adaptation items created after their release, a monotonicity check on a sample.

Choices the record leaves open (made here before any revision history was fetched or looked at):
  K2-C1 Items: D2's release table (ADP in d2_events.py: events_long.parquet, event adaptation, type group film or tv, release month known,
        linked to a Test A work through events.parquet), which is the same table as addendum j's events_releases.parquet (asserted here), with
        release month 2016-01 to 2026-09.  The date used = the item's events_long date (71's rule: the earliest best-rank P577 or P580 date
        at month precision or finer, deprecated statements dropped) and its month e.
  K2-C2 A revision carries the date when its main-slot content (the entity JSON; the internal format of before 2014 is read too) has a P577 or
        P580 statement with a value (not "no value" or "unknown"), precision 10 or more (month, day or finer), the same year and month as e,
        and a rank other than deprecated (71 drops deprecated statements, which is how Wikidata marks a rescheduled date).  Qualifiers (place
        of release, edition) are ignored, as in 71.  Recorded beside it: whether the first carrying revision also has the exact day used
        (day-precision dates), and whether 71's release rule applied to that revision gives the same month (the date could be present but
        not yet the earliest one).
  K2-C3 Search: list all revisions oldest first (rvprop=ids|timestamp|size, rvlimit=max, continued).  Check the latest revision; if it does
        not carry the date (edited after 71's query on 20 Oct), the revisions are checked backwards from the latest to the last one before
        2026-10-21 00:00 UTC and the latest carrying one is the upper end; if none carries, the item is "date not found" (counted, left out).
        Then the creation revision; if it carries, it is the first.  Otherwise a binary search with "lower end lacks, upper end carries".
        A revision whose content is hidden or missing is replaced by its nearest readable neighbour inside the interval.
  K2-C4 Monotonicity sample: 60 items drawn with numpy default_rng(20261022) among the items done (all of them if fewer).  For each, up to 6
        evenly spaced revisions before the first carrying one (excluding the creation revision, checked already) and up to 4 evenly spaced
        revisions after it are checked.  An earlier carrying revision means the date was added, removed and re-added: the binary search is
        repeated below that revision (and the check again), and the first addition is used for that item and reported.  A later revision
        without the date (removed for a while) is reported; it is not used to change the item's first time.  The sample rate is the stated
        uncertainty for the other items.
  K2-C5 Time: Wikidata timestamps are UTC; month boundaries are taken in UTC.  "Before the release month" = first carrying revision before
        00:00 UTC on the first day of month e; "at least 1 month before" = before the first day of e-1; "at least 3 months before" = before
        the first day of e-3.  Lead time in days = from the revision to the first day of e (negative = after the month began); in calendar
        months = e minus the revision's month (1 = added in the month before the release month).  Extra, day-precision dates only: before the
        release day itself (00:00 UTC of that day).
  K2-C6 Alert timing: an alert at origin t (D2's adapt list: a release in t+1..t+3) has its date "in Wikidata at the origin month" when at
        least one of the adaptation items that trigger it (release month in t+1..t+3) had its first carrying revision before the end of
        month t (00:00 UTC on the first day of t+1), D2's "by the end of t" timing.  An alert whose items were not all done and none of the
        done ones is known counts as "status unknown" and is left out of both groups (counted).
  K2-C7 Re-scoring: D2's alert_measures (copied unchanged): share rose and surged in t+1..t+3 (rose3, surge3; scored origins 2019-01 to 2026-05)
        and next month (rose1, surge1; 2019-01 to 2026-07), base = rate of all books in the same month, excess, lift, excess over books of the
        same month and H-score decile; 2,000 work-cluster bootstrap draws, numpy default_rng(20261020).  Lists: D2's adapt (all), adapt with
        the date known at t, adapt with the date not yet known at t; the same split of adapt_public; and, as D2's C11, the same three adapt
        lists among books not yet risen at t.  Difference known minus not known: 2,000 draws resampling works (a work in both groups keeps
        all its rows), seed 20261022.  D2's stored flags are reproduced first (asserted).
  K2-C8 Created after release: the item's first revision on or after the first day of the release month; also reported: after the end of the
        release month (first day of e+1).
  K2-C9 Shares over items get Wilson 95% intervals.  Splits: film and tv, release property (P577 or P580), release year groups 2016-2018,
        2019-2022, 2023-2026.  Lead-time bins in calendar months: added after the release month, in the release month, 1, 2, 3, 4 to 6,
        7 to 12, 13 to 24, more than 24 months before.
  K2-C10 Examples in the report: among items behind D2's scored adapt alerts, the one with the most revisions (a sign of a well-known title)
        whose date was in Wikidata at least 3 months before the release month, and the one with the most revisions whose date was added only
        in or after the release month.
  K2-C11 Coverage of addendum j: j's release features E (e_rel_film, e_rel_tv, e_rel_soon) are built from the same (work, t) pairs as D2's adapt
        list over all Test A origins; the share of those pairs whose date was known at t is reported (2016-03 to 2026-07 and the scored years).
Added at about 14:00 after an interim look at 499 items (not fixed in advance; descriptive extras, no fixed setting changed): what the revision just before
  the first carrying one held (no date, a year-only date, a date in another month), a flag for possible merges (the first carrying revision adds more
  than 20 KB to a page under 1 KB), and the months-to-release mix of known and late alerts.  The wording of the five plain lines was also set then.
Limits (in the report): the revision that first carries a date shows when Wikidata had it, not when a person could have known it elsewhere
(studio announcements); merged items lose the history of the merged-away item; the query service lags edits by minutes.
"""
import sys, json, time, gzip, hashlib, pathlib, datetime, os, math
import numpy as np, pandas as pd, requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))          # code/
from config import D, UA

D = pathlib.Path(D)
ROOT = D.parent
IN = D / 'db' / 'wiki_led'
OUT = IN / 'dirs' / 'k2_dates'
REP = D / 'reports'
CACHE = D / 'interim' / 'k2_wikidata_revisions'
ADD_K = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-22_k_intent_dates_human.json'
assert hashlib.sha256(ADD_K.read_bytes()).hexdigest() == '8290202d260dfd845f502c93f779e8a56d54851996cc930da9bbc09e4e99bb90', 'addendum k changed'
SET = json.loads(ADD_K.read_text())['K2_dates_known_in_time']
TEST = int(sys.argv[sys.argv.index('--test') + 1]) if '--test' in sys.argv else 0
FETCH = '--no-fetch' not in sys.argv
API = 'https://www.wikidata.org/w/api.php'
GAP = 0.5                      # seconds between the starts of two requests (at most 2 a second)
SNAP_END = datetime.datetime(2026, 10, 21, tzinfo=datetime.timezone.utc)
SEED_BOOT, SEED_K2 = 20261020, 20261022
NB = 2000
LN15, LN2 = np.log(1.5), np.log(2)
T0 = time.time()
PROPS = ('P577', 'P580')


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:5.0f}s', *a, flush=True)


def mi_of(s):
    return int(s[:4]) * 12 + int(s[5:7]) - 1


def ym(mi):
    mi = int(mi)
    return f'{mi // 12}-{mi % 12 + 1:02d}'


def month_start(mi):
    mi = int(mi)
    return datetime.datetime(mi // 12, mi % 12 + 1, 1, tzinfo=datetime.timezone.utc)


def ts_parse(s):
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)


def ts_mi(t):
    return t.year * 12 + t.month - 1


# ====================================================================== polite cached Action API client
class Api:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({'User-Agent': UA, 'Accept-Encoding': 'gzip'})
        self.last = 0.0
        self.n_net = self.n_cache = self.n_lag = self.n_retry = 0
        self.bytes = 0

    @staticmethod
    def path(params):
        h = hashlib.sha1(json.dumps(sorted(params.items())).encode()).hexdigest()
        return CACHE / h[:2] / (h + '.json.gz')

    def get(self, params, cache_only=False):
        p = self.path(params)
        if p.exists():
            self.n_cache += 1
            return json.loads(gzip.decompress(p.read_bytes()))
        if cache_only or not FETCH:
            return None
        q = dict(params, format='json', formatversion='2', maxlag='5')
        for attempt in range(10):
            w = self.last + GAP - time.time()
            if w > 0:
                time.sleep(w)
            self.last = time.time()
            try:
                r = self.s.get(API, params=q, timeout=90)
            except requests.RequestException:
                self.n_retry += 1
                time.sleep(5 * (attempt + 1))
                continue
            self.n_net += 1
            if r.status_code == 200:
                j = r.json()
                if 'error' in j:
                    if j['error'].get('code') == 'maxlag':
                        self.n_lag += 1
                        ra = r.headers.get('Retry-After')
                        time.sleep(max(5, int(ra) if ra and ra.isdigit() else 5))
                        continue
                    raise RuntimeError('API error: ' + json.dumps(j['error'])[:300])
                self.bytes += len(r.content)
                p.parent.mkdir(parents=True, exist_ok=True)
                tmp = p.with_suffix('.tmp')
                tmp.write_bytes(gzip.compress(json.dumps(j).encode(), 6))
                os.replace(tmp, p)
                return j
            if r.status_code in (429, 500, 502, 503, 504):
                self.n_retry += 1
                ra = r.headers.get('Retry-After')
                time.sleep(min(int(ra) if ra and ra.isdigit() else 10 * 2 ** attempt, 300))
                continue
            raise RuntimeError(f'HTTP {r.status_code}')
        raise RuntimeError('gave up after 10 attempts')


api = Api()


def list_revisions(q, cache_only=False):
    """all revisions of item q, oldest first: list of (revid, timestamp, size); also the page title actually listed (redirects followed)."""
    revs, cont, title = [], None, q
    while True:
        params = dict(action='query', prop='revisions', titles=q, redirects='1', rvprop='ids|timestamp|size', rvlimit='max', rvdir='newer')
        if cont:
            params['rvcontinue'] = cont
        j = api.get(params, cache_only=cache_only)
        if j is None:
            return None, None
        pages = j.get('query', {}).get('pages', [])
        if not pages or pages[0].get('missing'):
            return [], None
        title = pages[0].get('title', q)
        for r in pages[0].get('revisions', []):
            revs.append((int(r['revid']), r['timestamp'], int(r.get('size', 0))))
        cont = j.get('continue', {}).get('rvcontinue')
        if not cont:
            return revs, title


def time_value(v):
    """(year, month, precision) from a Wikibase time value dict; None when unusable."""
    try:
        t = v['time']
        prec = int(v['precision'])
    except (KeyError, TypeError, ValueError):
        return None
    neg = t.startswith('-')
    t = t.lstrip('+-')
    parts = t.split('-')
    try:
        y, m = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return None
    if neg:
        y = -y
    day = parts[2][:2] if len(parts) > 2 else '00'
    return y, m, prec, day


def date_statements(content):
    """every P577 / P580 statement of an entity JSON (current or pre-2014 internal format): list of (prop, year, month, day, precision, rank)."""
    out = []
    claims = content.get('claims', {}) if isinstance(content, dict) else {}
    if isinstance(claims, dict):                                        # current format
        for prop in PROPS:
            for st in claims.get(prop, []) or []:
                sn = st.get('mainsnak', {})
                if sn.get('snaktype') != 'value':
                    continue
                tv = time_value(sn.get('datavalue', {}).get('value'))
                if tv:
                    out.append((prop, tv[0], tv[1], tv[3], tv[2], st.get('rank', 'normal')))
    elif isinstance(claims, list):                                      # old internal format: {"m": ["value", 577, "time", {...}], "rank": 1}
        rk = {0: 'deprecated', 1: 'normal', 2: 'preferred'}
        for st in claims:
            m = st.get('m', [])
            if len(m) >= 4 and m[0] == 'value' and f'P{m[1]}' in PROPS and m[2] == 'time':
                tv = time_value(m[3])
                if tv:
                    out.append((f'P{m[1]}', tv[0], tv[1], tv[3], tv[2], rk.get(st.get('rank', 1), 'normal')))
    return out


def rule_month(stmts):
    """71's release rule on a set of statements: earliest best-rank month-or-finer date (preferred wins within a property); else any rank."""
    ok = [s for s in stmts if s[5] != 'deprecated']
    best = []
    for prop in PROPS:
        sp = [s for s in ok if s[0] == prop]
        if any(s[5] == 'preferred' for s in sp):
            sp = [s for s in sp if s[5] == 'preferred']
        best += sp
    cand = [s[1] * 12 + s[2] - 1 for s in best if s[4] >= 10 and s[1] > 0 and 1 <= s[2] <= 12]
    if not cand:
        cand = [s[1] * 12 + s[2] - 1 for s in ok if s[4] >= 10 and s[1] > 0 and 1 <= s[2] <= 12]
    return min(cand) if cand else None


CONTENT_MEMO = {}


def revision_statements(revid, cache_only=False):
    """date statements of one revision; None when the content is hidden or missing; 'nocache' when not cached and cache_only."""
    if revid in CONTENT_MEMO:
        return CONTENT_MEMO[revid]
    j = api.get(dict(action='query', prop='revisions', revids=str(revid), rvprop='ids|timestamp|content', rvslots='main'), cache_only=cache_only)
    if j is None:
        return 'nocache'
    pages = j.get('query', {}).get('pages', [])
    res = None
    if pages and pages[0].get('revisions'):
        r = pages[0]['revisions'][0]
        sl = r.get('slots', {}).get('main', {})
        txt = sl.get('content')
        if txt is not None and not sl.get('texthidden') and not r.get('texthidden'):
            try:
                res = date_statements(json.loads(txt))
            except json.JSONDecodeError:
                res = None
    CONTENT_MEMO[revid] = res
    return res


def carries(stmts, e):
    """K2-C2: a non-deprecated P577/P580 value at month precision or finer in month e."""
    y, m = e // 12, e % 12 + 1
    return any(s[5] != 'deprecated' and s[4] >= 10 and s[1] == y and s[2] == m for s in stmts)


class NotCached(Exception):
    pass


def make_pred(revs, e, cache_only):
    n_fetch = [0]

    def pred(i, lo=0, hi=None):
        """carries at revision index i; a hidden revision is replaced by the nearest readable one in (lo, hi). Returns (flag, index used)."""
        hi = len(revs) - 1 if hi is None else hi
        order = [i] + [x for d in range(1, len(revs)) for x in (i - d, i + d)]
        for j in order:
            if j < lo or j > hi or j < 0 or j >= len(revs):
                continue
            was = revs[j][0] in CONTENT_MEMO
            st = revision_statements(revs[j][0], cache_only=cache_only)
            if st == 'nocache':
                raise NotCached()
            if not was:
                n_fetch[0] += 1
            if st is not None:
                return carries(st, e), j
            if abs(j - i) > 20:
                break
        return None, i
    return pred, n_fetch


def first_carrier(revs, pred, lo_i, hi_i):
    """binary search on [lo_i, hi_i] with pred(lo_i) False and pred(hi_i) True: the first carrying index."""
    lo, hi = lo_i, hi_i
    while hi - lo > 1:
        mid = (lo + hi) // 2
        f, j = pred(mid, lo + 1, hi - 1)
        if f is None:                                 # nothing readable between: stop at hi
            break
        if f:
            hi = j
        else:
            lo = j
    return hi


def search_item(q, e, cache_only=False):
    """K2-C3 for one item.  Returns a dict (status ok / no_revisions / date_not_found / not_cached)."""
    revs, title = list_revisions(q, cache_only=cache_only)
    if revs is None:
        return dict(item=q, status='not_cached')
    if not revs:
        return dict(item=q, status='no_revisions')
    pred, nf = make_pred(revs, e, cache_only)
    out = dict(item=q, title_listed=title, n_revs=len(revs), created=revs[0][1], latest=revs[-1][1], latest_revid=revs[-1][0])
    try:
        n = len(revs)
        f_last, j_last = pred(n - 1, 0, n - 1)
        hi = j_last if f_last else None
        out['latest_carries'] = bool(f_last)
        if not f_last:                                            # changed after 71's query: latest carrying revision up to 2026-10-20
            for k in range(n - 2, -1, -1):
                if ts_parse(revs[k][1]) >= SNAP_END:
                    continue
                f, j = pred(k, k, k)
                if f:
                    hi = k
                    break
                if ts_parse(revs[k][1]) < SNAP_END - datetime.timedelta(days=30):
                    break
            if hi is None:
                out.update(status='date_not_found', n_fetch=nf[0])
                return out
        f0, j0 = pred(0, 0, 0)
        if f0:
            first = 0
        else:
            first = first_carrier(revs, pred, 0, hi)
        st = revision_statements(revs[first][0], cache_only=cache_only)
        y, m = e // 12, e % 12 + 1
        out.update(status='ok', first_idx=int(first), first_revid=revs[first][0], first_ts=revs[first][1],
                   prev_ts=revs[first - 1][1] if first > 0 else None, upper_idx=int(hi),
                   rule_month_at_first=rule_month(st) if st else None, n_fetch=nf[0])
        out['stmts_at_first'] = json.dumps(st)
        return out
    except NotCached:
        return dict(item=q, status='not_cached')


def check_monotone(q, e, res, cache_only=False):
    """K2-C4 for one sampled item: (first index after any correction, earlier carrier found?, later gap found?, revisions checked)."""
    revs, _ = list_revisions(q, cache_only=cache_only)
    pred, nf = make_pred(revs, e, cache_only)
    first = res['first_idx']
    earlier_found, rounds = False, 0
    checked = []
    while True:
        cand = sorted(set(np.linspace(1, first - 1, 6).round().astype(int))) if first >= 2 else []
        hit = None
        for i in cand:
            f, j = pred(int(i), 1, first - 1)
            checked.append(('before', int(j), f))
            if f:
                hit = j
                break
        if hit is None:
            break
        earlier_found = True
        rounds += 1
        first = first_carrier(revs, pred, 0, hit)
        if rounds > 5:
            break
    later_gap = False
    up = res['upper_idx']
    if up - res['first_idx'] >= 2:
        for i in sorted(set(np.linspace(res['first_idx'] + 1, up - 1, 4).round().astype(int))):
            f, j = pred(int(i), res['first_idx'] + 1, up - 1)
            checked.append(('after', int(j), f))
            if f is False:
                later_gap = True
    return dict(item=q, first_idx_checked=int(first), first_ts_checked=revs[first][1], earlier_carrier=earlier_found,
                later_gap=later_gap, n_checked=len(checked), n_fetch=nf[0])


# ====================================================================== items (K2-C1)
EV = pd.read_parquet(IN / 'events.parquet', columns=['work_id', 'item', 'author_item']).drop_duplicates('work_id')
EL = pd.read_parquet(IN / 'events_long.parquet')
W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id', 'title', 'creator'])
EV = EV[EV.work_id.isin(set(W.work_id))]
ad = EL[(EL.event == 'adaptation') & EL.type_group.isin(['film', 'tv']) & EL.mi_event.notna()].copy()
ad = ad.merge(EV[['work_id', 'item']], left_on='subject', right_on='item')
ad['e'] = ad.mi_event.astype(int)
ADP = ad[['work_id', 'e', 'type_group', 'detail', 'label', 'en_title', 'date', 'precision', 'release_prop', 'release_rank']].copy()
JREL = pd.read_parquet(IN / 'dirs' / 'j_alerts' / 'events_releases.parquet')
assert set(map(tuple, ADP[['work_id', 'e', 'detail']].itertuples(index=False))) == set(map(tuple, JREL[['work_id', 'e', 'detail']].itertuples(index=False))), \
    'D2 release table differs from addendum j'
E0, E1 = mi_of('2016-01'), mi_of('2026-09')
REL_ALL = ADP.copy()
ITEMS = (ADP[(ADP.e >= E0) & (ADP.e <= E1)].sort_values(['detail', 'work_id'])
         .groupby('detail', as_index=False).agg(e=('e', 'first'), n_e=('e', 'nunique'), type_group=('type_group', 'first'), label=('label', 'first'),
                                                 en_title=('en_title', 'first'), date=('date', 'first'), precision=('precision', 'first'),
                                                 release_prop=('release_prop', 'first'), release_rank=('release_rank', 'first'), n_works=('work_id', 'nunique')))
assert ITEMS.n_e.max() == 1
ITEMS = ITEMS.rename(columns={'detail': 'item'}).drop(columns='n_e').sort_values(['e', 'item']).reset_index(drop=True)
log(f'items: {len(ITEMS)} (film {int((ITEMS.type_group == "film").sum())}, tv {int((ITEMS.type_group == "tv").sum())}), '
    f'release months {ym(ITEMS.e.min())} to {ym(ITEMS.e.max())}; D2 table equals j events_releases: yes')
if TEST:
    ITEMS = ITEMS.iloc[np.linspace(0, len(ITEMS) - 1, TEST).round().astype(int)].reset_index(drop=True)

# ====================================================================== fetch and search
RES = []
for i, r in enumerate(ITEMS.itertuples()):
    try:
        x = search_item(r.item, int(r.e))
    except Exception as ex:                                       # an API error on one item: record and go on (reported as not done)
        x = dict(item=r.item, status='error', error=str(ex)[:200])
    RES.append(x)
    if (i + 1) % 25 == 0 or i + 1 == len(ITEMS) or TEST:
        st = pd.Series([z['status'] for z in RES]).value_counts().to_dict()
        log(f'{i + 1}/{len(ITEMS)} items  {st}  requests {api.n_net} (cache {api.n_cache}, maxlag waits {api.n_lag}, retries {api.n_retry}), '
            f'{api.bytes / 1e6:.0f} MB')
RES = pd.DataFrame(RES)
ok_items = RES[RES.status == 'ok']

# monotonicity sample (K2-C4)
rng_s = np.random.default_rng(SEED_K2)
samp = ok_items.item.to_numpy()
samp = rng_s.choice(samp, size=min(60, len(samp)), replace=False) if len(samp) else samp
MONO = []
emap = ITEMS.set_index('item').e
for q in samp:
    res = ok_items.set_index('item').loc[q]
    try:
        MONO.append(check_monotone(q, int(emap[q]), dict(first_idx=int(res.first_idx), upper_idx=int(res.upper_idx))))
    except NotCached:
        MONO.append(dict(item=q, earlier_carrier=np.nan, later_gap=np.nan, n_checked=0, not_cached=True))
MONO = pd.DataFrame(MONO)
log('monotonicity sample', len(MONO), 'earlier carrier', int(MONO.earlier_carrier.fillna(False).sum()) if len(MONO) else 0,
    'later gap', int(MONO.later_gap.fillna(False).sum()) if len(MONO) else 0, f'requests {api.n_net}')
if TEST:
    print(RES.drop(columns=['stmts_at_first'], errors='ignore').to_string())
    print(MONO.to_string())
    sys.exit(0)

# ====================================================================== item measures
OUT.mkdir(parents=True, exist_ok=True)
T = ITEMS.merge(RES.drop(columns=['stmts_at_first'], errors='ignore'), on='item', how='left')
T['first_ts_search'], T['first_idx_search'] = T.get('first_ts'), T.get('first_idx')
if len(MONO) and 'first_ts_checked' in MONO:                          # first addition after the sample check (only differs if re-added)
    fix = MONO[MONO.earlier_carrier == True].set_index('item')
    for q, r in fix.iterrows():
        T.loc[T.item == q, 'first_ts'] = r.first_ts_checked
        T.loc[T.item == q, 'first_idx'] = r.first_idx_checked
T['done'] = T.status == 'ok'
d = T[T.done].copy()
d['t_first'] = d.first_ts.map(ts_parse)
d['t_created'] = d.created.map(ts_parse)
d['S'] = d.e.map(month_start)
d['lead_days'] = [(s - t).total_seconds() / 86400 for s, t in zip(d.S, d.t_first)]
d['lead_months'] = d.e - d.t_first.map(ts_mi)
d['before_month'] = d.t_first < d.S
d['before_1m'] = [t < month_start(e - 1) for t, e in zip(d.t_first, d.e)]
d['before_3m'] = [t < month_start(e - 3) for t, e in zip(d.t_first, d.e)]
d['day_prec'] = d.precision >= 11
d['release_day'] = [datetime.datetime.strptime(x, '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc) if p >= 11 else pd.NaT
                    for x, p in zip(d.date, d.precision)]
d['before_day'] = [(t < rd) if p >= 11 else np.nan for t, rd, p in zip(d.t_first, d.release_day, d.precision)]
d['created_after_month_start'] = d.t_created >= d.S
d['created_after_month_end'] = [t >= month_start(e + 1) for t, e in zip(d.t_created, d.e)]
d['created_lead_months'] = d.e - d.t_created.map(ts_mi)
d['carried_at_creation'] = d.first_idx == 0
d['rule_same_month_at_first'] = d.rule_month_at_first == d.e
d['exact_day_at_first'] = pd.Series([None] * len(d), index=d.index, dtype=object)
_st = RES.set_index('item').stmts_at_first if 'stmts_at_first' in RES else pd.Series(dtype=object)
for k, r in d.iterrows():
    if r.precision >= 11 and r['item'] in _st.index and isinstance(_st[r['item']], str):
        y, m, dd = int(r.date[:4]), int(r.date[5:7]), r.date[8:10]
        d.at[k, 'exact_day_at_first'] = any(s[5] != 'deprecated' and s[4] >= 11 and s[1] == y and s[2] == m and s[3] == dd for s in json.loads(_st[r['item']]))
d['year_group'] = pd.cut(d.e // 12, [2015, 2018, 2022, 2026], labels=['2016-2018', '2019-2022', '2023-2026']).astype(str)
# extra, from the cache only (added after the first interim look at 499 items, not fixed in advance): what the revision just before the first
# carrying one held (a year-only date, a date in another month, or no date), and a possible merge (the first carrying revision adds more than
# 20 KB to a page under 1 KB, so the date may have come with the history of another item)
_prev, _merge = [], []
for r in d.itertuples():
    revs_, _ = list_revisions(r.item, cache_only=True)
    fi = int(r.first_idx)
    if fi == 0 or revs_ is None:
        _prev.append('page created with the date' if fi == 0 else 'not read')
        _merge.append(False)
        continue
    stp = revision_statements(revs_[fi - 1][0], cache_only=True)
    if not isinstance(stp, list):
        _prev.append('not read')
    else:
        ok_ = [x_ for x_ in stp if x_[5] != 'deprecated']
        if any(x_[4] >= 10 for x_ in ok_):
            _prev.append('a date in another month')
        elif ok_:
            _prev.append('a year-only date')
        else:
            _prev.append('no release date')
    _merge.append(bool(revs_[fi][2] - revs_[fi - 1][2] > 20000 and revs_[fi - 1][2] < 1000))
d['before_first_held'] = _prev
d['possible_merge'] = _merge
PREV_HELD = d.before_first_held.value_counts().to_dict()
PREV_HELD_LATE = d[~d.before_month].before_first_held.value_counts().to_dict()
MERGES = d.loc[d.possible_merge, 'item'].tolist()


def bin_lead(L):
    if L < 0:
        return 'a: after the release month'
    if L == 0:
        return 'b: in the release month'
    if L <= 3:
        return f'c{L}: {L} month{"s" if L > 1 else ""} before'
    if L <= 6:
        return 'd: 4 to 6 months before'
    if L <= 12:
        return 'e: 7 to 12 months before'
    if L <= 24:
        return 'f: 13 to 24 months before'
    return 'g: more than 24 months before'


d['lead_bin'] = d.lead_months.map(bin_lead)


def wilson(k, n):
    if n == 0:
        return np.nan, np.nan, np.nan
    z = 1.959963984540054
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, c - h, c + h


MEAS = ['before_month', 'before_1m', 'before_3m', 'created_after_month_start', 'created_after_month_end', 'carried_at_creation', 'rule_same_month_at_first']


def share_rows(g, name):
    rows = []
    for m in MEAS + ['before_day']:
        x = g[m].dropna().astype(bool)
        p, lo, hi = wilson(int(x.sum()), len(x))
        rows.append(dict(group=name, measure=m, n=len(x), k=int(x.sum()), share=p, lo=lo, hi=hi))
    return rows


SH = share_rows(d, 'all')
for col in ('type_group', 'release_prop', 'year_group'):
    for v, g in d.groupby(col):
        SH += share_rows(g, f'{col}={v}')
SH = pd.DataFrame(SH)
LB = d.lead_bin.value_counts().sort_index().rename('items').to_frame()
LB['share'] = LB['items'] / LB['items'].sum()
LB_tv = d.groupby(['type_group', 'lead_bin']).size().unstack(0).fillna(0).astype(int)
LB = LB.join(LB_tv)
QL = d.lead_days.quantile([0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]).to_dict()
QLm = d.lead_months.quantile([0.1, 0.25, 0.5, 0.75, 0.9]).to_dict()
log('shares (all):', SH[SH.group == 'all'][['measure', 'n', 'share', 'lo', 'hi']].round(3).to_dict('records'))

# ====================================================================== D2 alerts re-scored (K2-C6, K2-C7)
PR = pd.read_parquet(IN / 'dirs' / 'd2_events' / 'scored_rows_alerts.parquet')
from scipy.stats import rankdata
PR['h_dec'] = PR.groupby('mi').Hlgbm_D.transform(lambda s: np.minimum((10 * (rankdata(s) - 0.5) / len(s)).astype(int), 9))
LAST = mi_of('2026-08')
months_all = np.sort(PR.mi.unique())
months3 = months_all[months_all + 3 <= LAST]
D2R = json.loads((IN / 'dirs' / 'd2_events' / 'd2_results.json').read_text())
tfirst = d.set_index('item').t_first
done_set = set(d.item)
rel = []
for k in (1, 2, 3):
    x = REL_ALL[['work_id', 'e', 'detail']].copy()
    x['mi'] = x.e - k
    rel.append(x)
REL = pd.concat(rel, ignore_index=True)
REL['done'] = REL.detail.isin(done_set)
REL['known'] = [bool(dn and tfirst[q] < month_start(t + 1)) for q, t, dn in zip(REL.detail, REL.mi, REL.done)]
REL['in_k2_range'] = (REL.e >= E0) & (REL.e <= E1)
tcreated = d.set_index('item').t_created
REL['page_at_t'] = [bool(dn and tcreated[q] < month_start(t + 1)) for q, t, dn in zip(REL.detail, REL.mi, REL.done)]
REL['k'] = REL.e - REL.mi
AGG = REL.groupby(['work_id', 'mi']).agg(known=('known', 'any'), all_done=('done', 'all'), n_items=('detail', 'nunique'),
                                          in_range=('in_k2_range', 'all'), page_at_t=('page_at_t', 'any'), min_k=('k', 'min')).reset_index()
AGG['status'] = np.where(AGG.known, 'known', np.where(AGG.all_done, 'not_known', 'unknown'))           # unknown: an item not done or outside 2016-01..2026-09
PR = PR.merge(AGG[['work_id', 'mi', 'status', 'in_range', 'page_at_t', 'min_k']], on=['work_id', 'mi'], how='left')
chk = bool(((PR.status.notna()) == (PR.al_adapt == 1)).all())
assert chk, 'rebuilt release alerts differ from D2 al_adapt'
OUT_OF_RANGE = dict(scored=int((PR.al_adapt == 1).sum() - PR.loc[PR.al_adapt == 1, 'in_range'].fillna(False).astype(bool).sum()),
                    scored_3m=int(((PR.al_adapt == 1) & (PR.mi + 3 <= LAST)).sum() - PR.loc[(PR.al_adapt == 1) & (PR.mi + 3 <= LAST), 'in_range'].fillna(False).astype(bool).sum()))
PR['al_adapt_known'] = ((PR.al_adapt == 1) & (PR.status == 'known')).astype(int)
PR['al_adapt_notknown'] = ((PR.al_adapt == 1) & (PR.status == 'not_known')).astype(int)
PR['al_adapt_unknown'] = ((PR.al_adapt == 1) & (PR.status == 'unknown')).astype(int)
PR['al_adapt_public_known'] = ((PR.al_adapt_public == 1) & (PR.status == 'known')).astype(int)
PR['al_adapt_public_notknown'] = ((PR.al_adapt_public == 1) & (PR.status == 'not_known')).astype(int)


def alert_measures(R, nm, out_cols, rng, months, with_h=True):
    """D2's function, unchanged: share rose/surged of the alert rows, matched base, excess, lift, H-decile excess; work-cluster bootstrap."""
    R = R[R.mi.isin(months)]
    al = R['al_' + nm] == 1
    res = dict(rows=int(al.sum()), works=int(R.loc[al, 'work_id'].nunique()), months_with_alert=int(R.loc[al, 'mi'].nunique()), months=int(len(months)))
    if not al.any():
        return res
    cl = pd.factorize(R.loc[al, 'work_id'])[0]
    nc = cl.max() + 1
    cnt = np.stack([np.bincount(d_, minlength=nc) for d_ in rng.integers(0, nc, size=(NB, nc))]).astype(float)
    n_c = np.bincount(cl, minlength=nc).astype(float)
    for o in out_cols:
        base_m = R.groupby('mi')[o].mean()
        y = R.loc[al, o].to_numpy().astype(float)
        b = R.loc[al, 'mi'].map(base_m).to_numpy()
        S_y, S_b = np.bincount(cl, y, nc), np.bincount(cl, b, nc)
        share, base = y.mean(), b.mean()
        bs_y, bs_b, bs_n = cnt @ S_y, cnt @ S_b, cnt @ n_c
        dd = dict(share=float(share), share_lo=float(np.percentile(bs_y / bs_n, 2.5)), share_hi=float(np.percentile(bs_y / bs_n, 97.5)),
                  base=float(base), excess=float(share - base), excess_lo=float(np.percentile((bs_y - bs_b) / bs_n, 2.5)),
                  excess_hi=float(np.percentile((bs_y - bs_b) / bs_n, 97.5)), lift=float(share / base) if base > 0 else np.nan,
                  lift_lo=float(np.percentile(bs_y / bs_b, 2.5)), lift_hi=float(np.percentile(bs_y / bs_b, 97.5)))
        if with_h:
            nonal = R[~al]
            bh = nonal.groupby(['mi', 'h_dec'])[o].mean()
            bhv = pd.MultiIndex.from_arrays([R.loc[al, 'mi'], R.loc[al, 'h_dec']]).map(lambda t: bh.get(t, np.nan))
            bhv = np.asarray(bhv, dtype=float)
            S_h = np.bincount(cl, np.nan_to_num(bhv), nc)
            bs_h = cnt @ S_h
            dd.update(base_same_H_decile=float(np.nanmean(bhv)), excess_over_H=float(share - np.nanmean(bhv)),
                      excess_over_H_lo=float(np.percentile((bs_y - bs_h) / bs_n, 2.5)), excess_over_H_hi=float(np.percentile((bs_y - bs_h) / bs_n, 97.5)))
        res[o] = dd
    return res


def diff_known(R, months, outs, rng):
    """known minus not known: share difference with works resampled (rows of a work kept together across both groups)."""
    R = R[R.mi.isin(months) & ((R.al_adapt_known == 1) | (R.al_adapt_notknown == 1))]
    res = {}
    if not len(R) or R.al_adapt_known.sum() == 0 or R.al_adapt_notknown.sum() == 0:
        return res
    cl = pd.factorize(R.work_id)[0]
    nc = cl.max() + 1
    cnt = np.stack([np.bincount(d_, minlength=nc) for d_ in rng.integers(0, nc, size=(NB, nc))]).astype(float)
    kn = R.al_adapt_known.to_numpy() == 1
    for o in outs:
        y = R[o].to_numpy().astype(float)
        Sk, Nk = np.bincount(cl, y * kn, nc), np.bincount(cl, kn.astype(float), nc)
        Su, Nu = np.bincount(cl, y * ~kn, nc), np.bincount(cl, (~kn).astype(float), nc)
        with np.errstate(all='ignore'):
            b = (cnt @ Sk) / (cnt @ Nk) - (cnt @ Su) / (cnt @ Nu)
        est = y[kn].mean() - y[~kn].mean()
        res[o] = dict(known=float(y[kn].mean()), not_known=float(y[~kn].mean()), diff=float(est),
                      lo=float(np.nanpercentile(b, 2.5)), hi=float(np.nanpercentile(b, 97.5)))
    return res


rng = np.random.default_rng(SEED_BOOT)
OUTS1, OUTS3 = ['rose1', 'surge1'], ['rose3', 'surge3']
LISTS = ['adapt', 'adapt_known', 'adapt_notknown', 'adapt_unknown', 'adapt_public', 'adapt_public_known', 'adapt_public_notknown']
PRED = {nm: dict(three_months=alert_measures(PR, nm, OUTS3, rng, months3), next_month=alert_measures(PR, nm, OUTS1, rng, months_all)) for nm in LISTS}
PRe = PR[PR.not_yet].copy()
PRe['h_dec'] = PRe.groupby('mi').Hlgbm_D.transform(lambda s: np.minimum((10 * (rankdata(s) - 0.5) / len(s)).astype(int), 9))
PRED_E = {nm: dict(three_months=alert_measures(PRe, nm, OUTS3, rng, months3), next_month=alert_measures(PRe, nm, OUTS1, rng, months_all))
          for nm in ['adapt', 'adapt_known', 'adapt_notknown']}
rng2 = np.random.default_rng(SEED_K2)
DIFF = dict(three_months=diff_known(PR, months3, OUTS3, rng2), next_month=diff_known(PR, months_all, OUTS1, rng2),
            three_months_not_yet=diff_known(PRe, months3, OUTS3, rng2))
# reproduction check against D2's stored shares (the share and base are deterministic; intervals differ by the draws)
D2_CHECK = {}
for hz, outs in (('three_months', OUTS3), ('next_month', OUTS1)):
    for o in outs:
        D2_CHECK[f'{hz}_{o}'] = dict(d2=D2R['prediction']['adapt'][hz][o]['share'], here=PRED['adapt'][hz][o]['share'])
assert all(abs(v['d2'] - v['here']) < 1e-12 for v in D2_CHECK.values()), D2_CHECK
assert PRED['adapt']['three_months']['rows'] == D2R['prediction']['adapt']['three_months']['rows']
rows = []
for tag, PP in (('all books', PRED), ('not yet risen at t', PRED_E)):
    for nm, r in PP.items():
        for hz, outs in (('three_months', OUTS3), ('next_month', OUTS1)):
            x = r[hz]
            for o in outs:
                if o in x:
                    rows.append(dict(books=tag, alert=nm, horizon=hz, outcome=o, rows=x['rows'], works=x['works'], months_with_alert=x['months_with_alert'], **x[o]))
PREDT = pd.DataFrame(rows)

# alert rows by status, scored and all Test A origins (K2-C11)
al = PR[PR.al_adapt == 1]
STAT_SCORED = al.status.value_counts().to_dict()
STAT_SCORED3 = al[al.mi.isin(months3)].status.value_counts().to_dict()
_nk3 = al[al.mi.isin(months3) & (al.status == 'not_known')]
NOTKNOWN_PAGE = dict(rows=int(len(_nk3)), page_existed_at_t=int(_nk3.page_at_t.fillna(False).astype(bool).sum()))
_a3 = al[al.mi.isin(months3) & al.status.isin(['known', 'not_known'])]
K_MIX = {st: {int(k): int(v) for k, v in g.min_k.value_counts().sort_index().items()} for st, g in _a3.groupby('status')}
# by months to the release (the nearest release of the alert): known and late alerts compared within the same k, and a k-standardised difference
# (weights = the k mix of all known and late alerts)
KTAB, KSTD = [], {}
for hz, outs, mths in (('next_month', OUTS1, months_all), ('three_months', OUTS3, months3)):
    g0 = al[al.mi.isin(mths) & al.status.isin(['known', 'not_known'])]
    w = g0.min_k.value_counts(normalize=True)
    for o in outs:
        tab = g0.groupby(['min_k', 'status'])[o].agg(['mean', 'size']).unstack('status')
        for k in tab.index:
            KTAB.append(dict(horizon=hz, outcome=o, months_to_release=int(k), known=float(tab.loc[k, ('mean', 'known')]), known_rows=int(tab.loc[k, ('size', 'known')]),
                             late=float(tab.loc[k, ('mean', 'not_known')]), late_rows=int(tab.loc[k, ('size', 'not_known')])))
        dk_ = (tab[('mean', 'known')] - tab[('mean', 'not_known')])
        KSTD[o] = float((dk_ * w.reindex(dk_.index)).sum())
KTAB = pd.DataFrame(KTAB)
UNKNOWN_ROWS = al[al.status == 'unknown'][['work_id', 'mi']].assign(origin=lambda x: x.mi.map(ym)).origin.value_counts().to_dict()
RW = pd.read_parquet(IN / 'test_a_rows_c.parquet', columns=['work_id', 'mi'])
RWa = RW.merge(AGG, on=['work_id', 'mi'])
STAT_TESTA = RWa.status.value_counts().to_dict()
STAT_TESTA_YEAR = RWa.assign(year=RWa.mi // 12).groupby('year').status.value_counts().unstack().fillna(0).astype(int)
log('alert status scored months:', STAT_SCORED, 'Test A rows:', STAT_TESTA)

# examples (K2-C10)
scored_items = set(REL[REL.mi.isin(months3)].merge(al[['work_id', 'mi']], on=['work_id', 'mi']).detail)
ex_pool = d[d.item.isin(scored_items)]
ex1 = ex_pool[ex_pool.before_3m].sort_values(['n_revs', 'item'], ascending=[False, True]).head(1)
ex2 = ex_pool[~ex_pool.before_month].sort_values(['n_revs', 'item'], ascending=[False, True]).head(1)
if not len(ex1):
    ex1 = d[d.before_3m].sort_values('n_revs', ascending=False).head(1)
if not len(ex2):
    ex2 = d[~d.before_month].sort_values('n_revs', ascending=False).head(1)


def ex_info(x):
    if not len(x):
        return None
    r = x.iloc[0]
    w = REL_ALL[REL_ALL.detail == r['item']].work_id.unique()
    alr = al[al.work_id.isin(w) & al.mi.between(r.e - 3, r.e - 1) & al.obs3].sort_values(['mi', 'work_id']).drop_duplicates('mi')
    return dict(item=r['item'], label=r.label, en_title=r.en_title, type=r.type_group, date_used=r.date, precision=int(r.precision), prop=r.release_prop,
                release_month=ym(r.e), created=r.created, first_carry=r.first_ts, lead_days=float(r.lead_days), lead_months=int(r.lead_months),
                n_revs=int(r.n_revs), works=[int(v) for v in w], book_titles=sorted(set(W.loc[W.work_id.isin(w), 'title'].astype(str))),
                alerts=[dict(origin=ym(a.mi), work_id=int(a.work_id), status=a.status, rose3=int(a.rose3), surge3=int(a.surge3), obs3=bool(a.obs3)) for a in alr.itertuples()])


EX = [ex_info(ex1), ex_info(ex2)]

# ====================================================================== write tables and json
T_out = T.merge(d[['item', 'lead_days', 'lead_months', 'lead_bin', 'before_month', 'before_1m', 'before_3m', 'before_day', 'created_after_month_start',
                   'created_after_month_end', 'carried_at_creation', 'rule_same_month_at_first', 'exact_day_at_first', 'before_first_held', 'possible_merge']],
                on='item', how='left')
T_out['release_month'] = T_out.e.map(ym)
T_out.to_parquet(OUT / 'items_date_history.parquet', index=False)
T_out.drop(columns=['error'], errors='ignore').to_csv(OUT / 'items_date_history.csv', index=False)
SH.to_csv(OUT / 'shares.csv', index=False)
LB.to_csv(OUT / 'lead_time_bins.csv')
PREDT.to_csv(OUT / 'alerts_rescored.csv', index=False)
MONO.to_csv(OUT / 'monotonicity_sample.csv', index=False)
STAT_TESTA_YEAR.to_csv(OUT / 'alert_rows_status_by_year.csv')
PR[['work_id', 'mi', 'al_adapt', 'status', 'min_k', 'page_at_t', 'rose3', 'surge3', 'rose1', 'surge1', 'obs3', 'not_yet']][PR.al_adapt == 1].to_csv(OUT / 'alert_rows_scored.csv', index=False)
KTAB.to_csv(OUT / 'known_vs_late_by_months_to_release.csv', index=False)
n_items = len(ITEMS)
COV = dict(items=n_items, done=int(T.done.sum()), status=T.status.value_counts().to_dict(),
           requests_network=api.n_net, requests_cache=api.n_cache, maxlag_waits=api.n_lag, retries=api.n_retry, mb_downloaded=round(api.bytes / 1e6, 1),
           content_fetches=int(T['n_fetch'].fillna(0).sum()) if 'n_fetch' in T else 0, median_revisions=float(d.n_revs.median()) if len(d) else None,
           alerts_with_a_release_outside_range=OUT_OF_RANGE)
MONO_SUM = dict(sampled=int(len(MONO)), earlier_carrier=int(MONO.earlier_carrier.fillna(False).astype(bool).sum()) if len(MONO) else 0,
                later_gap=int(MONO.later_gap.fillna(False).astype(bool).sum()) if len(MONO) else 0,
                revisions_checked=int(MONO.n_checked.sum()) if len(MONO) else 0,
                items_earlier=MONO.loc[MONO.earlier_carrier == True, 'item'].tolist() if len(MONO) else [],
                items_later_gap=MONO.loc[MONO.later_gap == True, 'item'].tolist() if len(MONO) else [])
RESJ = dict(settings=SET, coverage=COV, shares=SH.to_dict('records'), lead_bins=LB.reset_index().to_dict('records'), lead_days_quantiles=QL,
            lead_months_quantiles=QLm, monotonicity=MONO_SUM, held_just_before_first=PREV_HELD, held_just_before_first_items_not_in_time=PREV_HELD_LATE,
            possible_merges=MERGES, alerts=PREDT.to_dict('records'), diff_known_minus_not=DIFF, d2_check=D2_CHECK,
            alert_status_scored=STAT_SCORED, alert_status_scored_3m=STAT_SCORED3, not_known_alerts_page_existed=NOTKNOWN_PAGE,
            months_to_release_by_status_3m=K_MIX, unknown_rows_by_origin=UNKNOWN_ROWS, known_vs_late_by_k=KTAB.to_dict('records'), known_minus_late_k_standardised=KSTD, alert_status_test_a=STAT_TESTA, examples=EX,
            runtime_s=round(time.time() - T0, 1), written=time.strftime('%Y-%m-%d %H:%M %z'))
(OUT / 'k2_results.json').write_text(json.dumps(RESJ, indent=1, default=str))
log('tables written', OUT)

# ====================================================================== report
Lr = []
P_ = Lr.append
pc = lambda x: f'{100 * x:.0f}%' if x == x else 'n/a'
pc1 = lambda x: f'{100 * x:.1f}%' if x == x else 'n/a'


def S_(m, g='all'):
    r = SH[(SH.group == g) & (SH.measure == m)].iloc[0]
    return r


def ci(r):
    return f"{pc(r.share)} ({pc(r['lo'])} to {pc(r['hi'])}; {r.k} of {r.n})"


def A_(nm, hz, o, books='all books'):
    x = PREDT[(PREDT.books == books) & (PREDT.alert == nm) & (PREDT.horizon == hz) & (PREDT.outcome == o)]
    return x.iloc[0] if len(x) else None


def ash(nm, hz, o, books='all books'):
    r = A_(nm, hz, o, books)
    return f"{pc(r.share)} ({pc(r.share_lo)} to {pc(r.share_hi)})" if r is not None else 'n/a'


bm, b1, b3 = S_('before_month'), S_('before_1m'), S_('before_3m')
ca = S_('created_after_month_start')
nk3 = A_('adapt_known', 'three_months', 'rose3')
nu3 = A_('adapt_notknown', 'three_months', 'rose3')
n_al3 = A_('adapt', 'three_months', 'rose3')
dk = DIFF.get('three_months', {})
P_('# K2: were the film and TV release dates in Wikidata before the releases?')
P_('')
P_(f"Khant Phyo Wai, 01323050. Run {time.strftime('%d %b %Y %H:%M')} +07. Addendum k, section K2_dates_known_in_time (`prereg/addenda_wiki_led/2026-10-22_k_intent_dates_human.json`, "
   f"fixed 2026-10-22 11:45 +07). Choices the record leaves open: K2-C1 to K2-C11 in the header of `code/main_study/wiki_led/dirs/k2_date_history.py`. Descriptive; every interval is a 95% interval. "
   f"Coverage: {COV['done']} of {n_items} adaptation items done.")
P_('')
P_('## In plain words')
P_('')
P_(f"1. For {COV['done']} film and TV adaptations released 2016 to 2026 that D2 and addendum j used, we looked back through each Wikidata page's edit history for the first edit that held the release month.")
P_(f"2. The release date was already on Wikidata before the release month for {pc(bm.share)} of them, at least a month before for {pc(b1.share)}, and at least three months before for {pc(b3.share)}.")
P_(f"3. {pc(ca.share)} of the adaptation pages did not exist on Wikidata until the release month or later, so for those the date could not have been known there in advance.")
ks3 = A_('adapt_known', 'three_months', 'surge3')
as3 = A_('adapt', 'three_months', 'surge3')
P_(f"4. Of D2's {int(n_al3.rows):,} scored release alerts (a film or TV release in the next three months), {int(nk3.rows) if nk3 is not None else 0:,} "
   f"({pc(nk3.rows / n_al3.rows) if nk3 is not None else '0%'}) had the release date on Wikidata by the end of the alert month. "
   f"Those books rose in the next three months in {ash('adapt_known', 'three_months', 'rose3')} of cases and surged in {ash('adapt_known', 'three_months', 'surge3')}, "
   f"against {ash('adapt', 'three_months', 'rose3')} and {ash('adapt', 'three_months', 'surge3')} for all of D2's alerts and {pc(nk3.base) if nk3 is not None else 'n/a'} and "
   f"{pc(ks3.base) if ks3 is not None else 'n/a'} for all books in the same months.")
_dd = DIFF.get('three_months', {}).get('rose3')
if nk3 is not None and nk3.excess_over_H_lo > 0:
    _s5 = (f"5. So the release alert still works on dates that were really known in time (it beats books with the same H score by {100 * nk3.excess_over_H:.0f} points, "
           f"interval {100 * nk3.excess_over_H_lo:.0f} to {100 * nk3.excess_over_H_hi:.0f}), but a calendar read from Wikidata at the time would have flagged only about "
           f"{pc(nk3.rows / n_al3.rows)} as many book-months as D2's list")
else:
    _s5 = "5. So the release alert does not clearly hold up when only dates known in time are used"
if _dd:
    if _dd['lo'] <= 0 <= _dd['hi']:
        _s5 += (f"; alerts whose date reached Wikidata only later rose about as often ({pc(_dd['not_known'])} against {pc(_dd['known'])}; "
                f"in time minus late {100 * _dd['diff']:+.0f} points, interval {100 * _dd['lo']:+.0f} to {100 * _dd['hi']:+.0f}).")
    else:
        _s5 += (f"; alerts whose date reached Wikidata only later rose {'more' if _dd['diff'] < 0 else 'less'} often ({pc(_dd['not_known'])} against {pc(_dd['known'])}; "
                f"in time minus late {100 * _dd['diff']:+.0f} points, interval {100 * _dd['lo']:+.0f} to {100 * _dd['hi']:+.0f}).")
else:
    _s5 += '.'
P_(_s5)
P_('')
P_('## Two real examples')
P_('')
for k, x in enumerate(EX, 1):
    if not x:
        continue
    al_txt = '; '.join(f"end of {a['origin']}: {'date already on Wikidata' if a['status'] == 'known' else 'date not yet on Wikidata'}, "
                       f"{'rose' if a['rose3'] else 'did not rise'} in the next three months{', surged' if a['surge3'] else ''}" for a in x['alerts'][:3])
    name = x['en_title'] or x['label']
    P_(f"{k}. **{name}** ({x['type']}, Wikidata {x['item']}), adapted from the Seattle library work{'s' if len(x['book_titles']) > 1 else ''} "
       f"'{"', '".join(x['book_titles'])}'. Release date used: {x['date_used']} ({x['prop']}), month {x['release_month']}. "
       f"Page created {x['created'][:10]}; the release month first appeared on {x['first_carry'][:10]}, "
       + (f"{abs(x['lead_months'])} calendar month{'s' if abs(x['lead_months']) != 1 else ''} {'before' if x['lead_months'] > 0 else 'after'} the release month" if x['lead_months'] != 0 else 'in the release month itself')
       + f" ({abs(x['lead_days']):.0f} days {'before' if x['lead_days'] > 0 else 'after'} the release month began). "
       f"D2's alert for the book: {al_txt if al_txt else 'none in the scored months'}.")
P_('')
P_("Terms. **Rose**: loans at least 1.5 times the book's usual level (M6, the median of its last six months); **surged**: at least 2 times and at least 5 loans more (Test A's arithmetic). "
   "**H**: Test A's library-history model. An alert at the end of month **t** names books with a film or TV release in t+1 to t+3 (D2's list).")
P_('')
P_('## 1. What was checked')
P_('')
P_(f"- Items: every film or TV adaptation release in D2's table (the same table as addendum j's `events_releases.parquet`, checked) with a release month from 2016-01 to 2026-09: "
   f"{n_items} items ({int((ITEMS.type_group == 'film').sum())} films, {int((ITEMS.type_group == 'tv').sum())} TV), linked to {int(ITEMS.n_works.sum())} work links.")
P_("- For each item, its whole Wikidata revision list, then a binary search over revision contents for the first revision with a P577 (publication date) or P580 (start time) statement "
   "in the release month used (month precision or finer, not deprecated). Wikidata Action API, maxlag 5, at most 2 requests a second, the project user agent, every answer cached.")
_cf = list(CACHE.rglob('*.json.gz'))
COV['cached_answers'] = len(_cf)
COV['cache_mb'] = round(sum(f.stat().st_size for f in _cf) / 1e6, 1)
P_(f"- Requests: every answer is cached ({COV['cached_answers']:,} answers, {COV['cache_mb']} MB compressed in `data/interim/k2_wikidata_revisions/`), one network request each; "
   f"this run made {COV['requests_network']:,} network requests and read {COV['requests_cache']:,} answers from the cache (maxlag pauses {COV['maxlag_waits']}, retries {COV['retries']}; "
   f"the fetch log is `data/reports/k2_wd_revisions.log`). Item status: {COV['status']}.")
P_(f"- Monotonicity (a date added, removed and added again): {MONO_SUM['sampled']} random items were checked at {MONO_SUM['revisions_checked']} more revisions. "
   f"Earlier addition found: {MONO_SUM['earlier_carrier']} ({', '.join(MONO_SUM['items_earlier']) or 'none'}); removed for a while after the first addition: {MONO_SUM['later_gap']} "
   f"({', '.join(MONO_SUM['items_later_gap']) or 'none'}). Where an earlier addition was found, the first addition is used.")
P_('')
P_('## 2. Was the date in Wikidata in time?')
P_('')
P_('| Group | Items | Before the release month | At least 1 month before | At least 3 months before | Page created in or after the release month |')
P_('|---|---|---|---|---|---|')
groups = ['all'] + [g for g in SH.group.unique() if g != 'all']
for g in groups:
    r0 = S_('before_month', g)
    P_(f"| {g.replace('type_group=', '').replace('release_prop=', 'property ').replace('year_group=', 'released ')} | {r0.n} | {ci(S_('before_month', g))} | {ci(S_('before_1m', g))} | "
       f"{ci(S_('before_3m', g))} | {ci(S_('created_after_month_start', g))} |")
P_('')
bd = S_('before_day')
P_(f"- Day-precision dates only: the date was on Wikidata before the release day itself for {ci(bd)}.")
P_(f"- Page created after the end of the release month: {ci(S_('created_after_month_end'))}. The date was already in the first revision of the page for {ci(S_('carried_at_creation'))}.")
P_(f"- At the first revision carrying the release month, 71's rule (earliest dated release) already gave that month for {ci(S_('rule_same_month_at_first'))}; "
   "for the rest an earlier dated release was listed then and removed or deprecated later.")
if 'exact_day_at_first' in d:
    xd = d.exact_day_at_first.dropna().astype(bool)
    if len(xd):
        P_(f"- Day-precision dates: the exact day used was already there at that first revision for {pc(xd.mean())} ({int(xd.sum())} of {len(xd)}); otherwise the month came first and the day later.")
_nl = int((~d.before_month).sum())
P_(f"- What the item held just before the release month first appeared (all {len(d)} items): " + ', '.join(f"{k} {v} ({pc(v / len(d))})" for k, v in PREV_HELD.items()) +
   f". Among the {_nl} items whose date was not there before the release month: " + ', '.join(f"{k} {v}" for k, v in PREV_HELD_LATE.items()) +
   ". A year-only date cannot place a release in a month (D2 and 71 do not use them); a date in another month is often a planned date that moved or another country's release.")
P_(f"- Possible merges (the first revision with the date adds more than 20 KB to a page under 1 KB, so the date may have come from another item's history, which is not searched): "
   f"{len(MERGES)} ({', '.join(MERGES) or 'none'}). Their times are kept as found. (These two checks were added after a first look at 499 items.)")
P_('')
P_('## 3. Lead time')
P_('')
P_('Calendar months from the first revision holding the release month to the release month (by type).')
P_('')
P_('| Lead time | Items | Share | Film | TV |')
P_('|---|---|---|---|---|')
for b, r in LB.iterrows():
    P_(f"| {b.split(': ', 1)[1]} | {int(r['items'])} | {pc1(r['share'])} | {int(r.get('film', 0))} | {int(r.get('tv', 0))} |")
P_('')
P_(f"Lead time in days to the first day of the release month: 10th percentile {QL[0.1]:.0f}, quartiles {QL[0.25]:.0f} / {QL[0.5]:.0f} / {QL[0.75]:.0f}, 90th percentile {QL[0.9]:.0f} "
   "(negative = added after the release month began).")
P_('')
P_("## 4. D2's release alerts re-scored")
P_('')
P_(f"An alert at the end of month t (a release in t+1..t+3) counts as known in time when at least one of its adaptations had the release month on Wikidata before the end of t. "
   f"Scored alert rows (origins 2019-01 to 2026-07): {STAT_SCORED}; with t+3 observed (origins 2019-01 to 2026-05): {STAT_SCORED3}. "
   f"Of the {NOTKNOWN_PAGE['rows']} not-known rows with t+3 observed, the adaptation's Wikidata page already existed at t (without the date) for {NOTKNOWN_PAGE['page_existed_at_t']}; "
   "for the rest the page did not exist yet. "
   f"The {STAT_SCORED.get('unknown', 0)} rows of unknown status are at the last origins ({', '.join(sorted(UNKNOWN_ROWS))}) and are triggered only by releases after 2026-09, "
   "outside the record's range; none is in the three-month scoring.")
P_('')
P_('| Alert list | Rows | Works | Rose in t+1..t+3 | Base | Excess over books of the same month and H decile | Surged in t+1..t+3 | Base | Excess over same H decile |')
P_('|---|---|---|---|---|---|---|---|---|')
names = {'adapt': 'All release alerts (D2)', 'adapt_known': 'Date on Wikidata by the end of t', 'adapt_notknown': 'Date not yet on Wikidata at t',
         'adapt_unknown': 'Status unknown (item not done)', 'adapt_public': 'D2 "already public" list', 'adapt_public_known': 'Already public, date on Wikidata at t',
         'adapt_public_notknown': 'Already public, date not yet on Wikidata'}
for tag in ('all books', 'not yet risen at t'):
    if tag != 'all books':
        P_(f'| *Books not yet risen at t (D2 C11)* | | | | | | | | |')
    for nm in names:
        r1, r2 = A_(nm, 'three_months', 'rose3', tag), A_(nm, 'three_months', 'surge3', tag)
        if r1 is None:
            continue
        P_(f"| {names[nm]} | {int(r1.rows)} | {int(r1.works)} | {pc(r1.share)} ({pc(r1.share_lo)} to {pc(r1.share_hi)}) | {pc(r1.base)} | "
           f"{100 * r1.excess_over_H:+.0f} ({100 * r1.excess_over_H_lo:+.0f} to {100 * r1.excess_over_H_hi:+.0f}) points | "
           f"{pc(r2.share)} ({pc(r2.share_lo)} to {pc(r2.share_hi)}) | {pc(r2.base)} | {100 * r2.excess_over_H:+.0f} ({100 * r2.excess_over_H_lo:+.0f} to {100 * r2.excess_over_H_hi:+.0f}) points |")
P_('')
for hz, lab in (('three_months', 't+1..t+3, all books'), ('next_month', 'next month (t+1), all books'), ('three_months_not_yet', 't+1..t+3, books not yet risen')):
    x = DIFF.get(hz, {})
    if x:
        P_(f"- Known in time minus not known ({lab}): " + '; '.join(f"{o} {pc(v['known'])} vs {pc(v['not_known'])}, difference {100 * v['diff']:+.0f} points ({100 * v['lo']:+.0f} to {100 * v['hi']:+.0f})" for o, v in x.items()) + '.')
def _kshare(st, k):
    g = K_MIX.get(st, {})
    return g.get(k, 0) / sum(g.values()) if g else float('nan')


P_(f"- Alerts known in time sit closer to the release: the release falls in t+1 for {pc(_kshare('known', 1))} of them against {pc(_kshare('not_known', 1))} of the late ones "
   f"(t+2: {pc(_kshare('known', 2))} against {pc(_kshare('not_known', 2))}; t+3: {pc(_kshare('known', 3))} against {pc(_kshare('not_known', 3))}). "
   f"Compared within the same number of months to the release and weighted to the same mix, known minus late is {100 * KSTD['rose1']:+.0f} points for rising next month "
   f"(raw {100 * DIFF['next_month']['rose1']['diff']:+.0f}), {100 * KSTD['surge1']:+.0f} for surging next month (raw {100 * DIFF['next_month']['surge1']['diff']:+.0f}), "
   f"{100 * KSTD['rose3']:+.0f} for rising in t+1..t+3 (raw {100 * DIFF['three_months']['rose3']['diff']:+.0f}) and {100 * KSTD['surge3']:+.0f} for surging in t+1..t+3 "
   f"(raw {100 * DIFF['three_months']['surge3']['diff']:+.0f}); table by month: `known_vs_late_by_months_to_release.csv`.")
r_n1, r_n2 = A_('adapt_known', 'next_month', 'rose1'), A_('adapt_known', 'next_month', 'surge1')
if r_n1 is not None:
    P_(f"- Next month only (Test A's outcome), known in time: rose {ash('adapt_known', 'next_month', 'rose1')}, surged {ash('adapt_known', 'next_month', 'surge1')}; "
       f"all release alerts: rose {ash('adapt', 'next_month', 'rose1')}, surged {ash('adapt', 'next_month', 'surge1')}.")
P_(f"- Check: the alert rows rebuilt here are exactly D2's `al_adapt` rows, and the all-alert shares equal D2's stored ones ({ {k: round(v['here'], 4) for k, v in D2_CHECK.items()} }). "
   "Intervals differ slightly from D2's because the bootstrap draws differ.")
P_('')
P_("## 5. Addendum j's release features")
P_('')
tot = sum(STAT_TESTA.values())
P_(f"Addendum j's release features (e_rel_film, e_rel_tv, e_rel_soon) are on for the same (book, month) pairs as D2's list. Over all Test A origins (2016-03 to 2026-07): {tot:,} pairs, "
   f"known in time {STAT_TESTA.get('known', 0):,} ({pc(STAT_TESTA.get('known', 0) / tot) if tot else 'n/a'}), not yet known {STAT_TESTA.get('not_known', 0):,}, status unknown {STAT_TESTA.get('unknown', 0):,}. "
   "By year: `data/db/wiki_led/dirs/k2_dates/alert_rows_status_by_year.csv`. j's models were not refitted here.")
P_('')
P_('## 6. Limits')
P_('')
P_('- The first revision holding a date shows when Wikidata had it, not when it was public elsewhere (studio announcements, trade press); a calendar built from other sources could know more.')
P_('- Month boundaries are in UTC; the query service lags edits by minutes. Items merged into another item lose the merged-away history.')
P_('- The date used is the earliest dated release (often a festival premiere or first broadcast); the search asks for that month, not for the US date.')
P_(f"- Monotonicity was checked on a sample of {MONO_SUM['sampled']} items; for the rest the binary search assumes the date stayed once added.")
P_('- Descriptive; many shares are shown without adjustment.')
P_('')
P_('## 7. Files')
P_('')
P_('- Code: `code/main_study/wiki_led/dirs/k2_date_history.py` (run from `code/`; a rerun uses the cache in `data/interim/k2_wikidata_revisions/` and makes no request).')
P_('- `data/db/wiki_led/dirs/k2_dates/`: `items_date_history.parquet` and `.csv` (one row per item: release month, created, first revision with the date, lead time, flags), '
   '`shares.csv`, `lead_time_bins.csv`, `alerts_rescored.csv`, `alert_rows_scored.csv`, `alert_rows_status_by_year.csv`, `known_vs_late_by_months_to_release.csv`, '
   '`monotonicity_sample.csv`, `k2_results.json`.')
(REP / 'dir_k2_dates.md').write_text('\n'.join(Lr) + '\n')
RESJ['coverage'] = COV
(OUT / 'k2_results.json').write_text(json.dumps(RESJ, indent=1, default=str))
log('report', REP / 'dir_k2_dates.md')
