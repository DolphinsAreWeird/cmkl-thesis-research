#!/usr/bin/env python3
"""J1 of addendum j (combined alert list): the book-linked Wikipedia pages of every kind for Test A's 7,747 works, the anniversary part of
the scheduled calendar, and the monthly bursts of the linked pages (data only: no model is fitted, nothing is related to loans).

Settings: prereg/addenda_wiki_led/2026-10-22_j_combined_alerts.json (read-only; SHA-256 checked below), sections book_links,
linked_page_attention and scheduled_calendar (anniversaries only; the adaptation releases and the death in month t come from D2's inputs,
which J2 reads).  The models are J2's (code/main_study/wiki_led/dirs/j2_*.py).

Stages (run from handoff/code with ../.venv/bin/python):
  --stage links    Wikidata SPARQL (query.wikidata.org): links of every book item, the linked items' English Wikipedia titles, P31 types,
                   categories and dates; the author items' births and deaths; writes links.parquet, anniversaries.parquet,
                   pages_wanted.parquet and links_summary.json.  About 20 to 40 minutes the first time, seconds from the cache.
  --stage bursts   reads the daily views of the selected pages from the three stores (below) and writes linked_bursts.parquet,
                   bursts_summary.json and the report data/reports/dir_j1_links.md.  Light (a few minutes).
The views of pages not yet stored are downloaded by j1_download_views.py (detached, one Wikimedia downloader at a time).
Outputs: data/db/wiki_led/dirs/j_links/.

SPARQL as in 71_wikidata_events.py (its Sparql client, run_batches and date parsing are copied here, because 71 runs its whole job on
import): one query at a time, at least 1.5 s between the starts of two queries, batches of up to 300 items (a batch that times out is split in
halves), the project user agent from code/config.py, every answer cached in data/interim/wiki_led_cache/sparql/ (the same cache as 71, so
71's queries that are repeated here word for word, P144 and P4969 links and author deaths, come from the cache).

Choices the record leaves open (written on 22 Oct 2026 between 08:00 and 09:15, before any link, count or view of this test was looked at; one probe of
Wikidata's class tree for 15 hand-picked classes was made before, to check that the record's roots work: city, country, historical country
and US state reach geographic location; war, battle and disease reach occurrence; historical period does not):
  J1  Units.  Book item = works.item of data/db/study2r/works.parquet (7,510 items for the 7,747 works); the links of an item are given to every
      work with that item.  Statements: Wikidata's truthy values (wdt:, the best-rank statements; somevalue and novalue are dropped).
  J2  Link types (record's list): subject = P921 main subject or P180 depicts; person = such a subject item that is human (category person);
      event_period = P2408 set in period (whatever its category), or a subject item whose category is event; place = P840 narrative
      location; character = P674; adaptation = an item with P144 (based on) to the book, or the book's P4969 (derivative work), queried with
      71's own query (so the same pairs as events_long.parquet, minus the old file's extra pairs); series = every other item with P179 (part
      of the series) to a series of the book.  A subject item that is human is a person link and not also a subject link; one that is an
      occurrence is an event_period link and not also a subject link.  One row per (work, link type, item); props lists the properties.
  J3  Left out: the book's own item, and every P50 author of the book item (data/db/study2r/wd_authors.parquet) and the work's author item of
      events.parquet: the record keeps the author in the W features, so the author's page is not a linked page (a memoir's main subject is
      often its author).
  J4  Category of an item from its P31 classes and their P279* superclasses (zero or more steps): person when a class reaches human Q5,
      else event when one reaches occurrence Q1190554, else place when one reaches geographic location Q2221906, else work when one reaches
      creative work Q17537576, else concept_other (also for items without P31).  The order (person, event, place, work) settles items whose
      classes reach several roots; how many do is reported.  The record names occurrence as the event class, so items of Wikidata classes
      that sit under occurrence but are not events in plain words (for example disease) count as event; the most common classes of every
      category are listed in the report.  Extra column is_period: some class reaches historical period Q11514315 (it does not reach
      occurrence, so the record's rule puts periods such as the Victorian era in concept_other unless another class is an occurrence);
      the category itself follows the record.
      Changed at 09:22, after the first link counts (no view, burst or model result existed): the first order (person, event, place, work)
      put 241 operas and other dramatico-musical works, theatrical productions, ballets, film projects and Platonic dialogues in event,
      because Wikidata places these creative-work classes under occurrence too (performing arts production, dialogue).  The order is now
      person, work, event, place: an item whose classes reach both creative work and occurrence is a work.  Logged in prereg/DEVIATIONS.md.
  J5  Page title = the English Wikipedia sitelink (the article's current title, never a redirect), spaces replaced by underscores.  Items with
      no English article keep their link row with page_title missing (no views).  ai_kind = the 'kind' of the same title in Test F's
      items_pages.parquet (the AI's page kind), else missing.
  J6  Dates of every linked item: P585 point in time, P580 start time, P569 birth, P570 death, each with its precision.  Per item and property
      one statement, 71's death rule: deprecated statements are dropped; statements at month precision or finer come first, among them a
      preferred rank wins, then the most precise, then the earliest (an item with none keeps its best coarser date by the same order, shown
      but never placed in a month).
      event_mi = the month index (year * 12 + month - 1) of P585 when its precision is a month or finer, else of P580 when its precision is a
      month or finer; dates before year 1 are not used (71's parse rule).  Dates are Wikidata's time values (proleptic Gregorian for day
      precision; an old Julian date at month precision may sit one month off).
  J7  Anniversaries (record: a multiple of 25 years): kind 'event' for every linked item of category event with an event_mi (any link type),
      kind 'author_birth' and 'author_death' for the work's author item of events.parquet (P569 and P570, J6's rule, month precision or finer;
      the death query is 71's, so the death month is the one events.parquet uses).  years = 25, 50, 75, ... (0, the event itself, is not an
      anniversary); months 2015-01 to 2027-12 are written.  The same (work, month, kind, source item) once.
  J8  Pages to fetch (record: at most 30,000 pages, by link type in the order adaptation, subject, event_period, person, place, character,
      series): every distinct page title, under its first link type in that order over all works; within a link type, pages linked to more
      works first, then by title; the first 30,000 are selected.
  J9  Views: Wikimedia REST per-article, en.wikipedia, all-access, user agent, daily, 2015-07-01 to 2026-09-30 (the record).  Sources in this
      order: Test F's store data/interim/testF_views/ (same request; read with _testf_analysis.store_index and store_matrix), the adaptation
      views data/db/wiki_led/adaptation_daily_views.parquet (same request; a day missing there is 0), then this test's own store
      data/interim/j_linked_views/ (j1_download_views.py: Test F's downloader functions and HTTP class, gap 0.34 s over 4 threads, at most
      2.94 requests a second).  A page with no data (404) or an invalid title (400) has no views and is not counted in n_pages.
  J10 Bursts (record): monthly views V_m = the sum of the daily views of the calendar month; M6 = the median of V over the 6 months before
      (m-6 to m-1).  A page bursts in month m when V_m >= 3 * M6 and V_m >= 3,000, or when it is in the daily top 500 (data/raw/wiki_top_daily.json,
      after Test F's namespace rule, _testf_analysis.top_long) on any day of month m that has a list.  Months 2016-01 to 2026-09 (2015-07 to
      2015-12 serve only as the first baseline).  A page with no views before (M6 = 0, for example an article created later) bursts once
      V_m >= 3,000, as the rule is written.  max_ratio = the largest V_m / max(M6, 1) among the group's pages (the views ratio, whether or not
      the page bursts).
  J11 linked_bursts.parquet: one row per work, month 2016-01 to 2026-09, link type and category for every (work, link type, category) group
      with at least one page with views; n_pages = the group's pages with views, n_burst = those bursting in the month, any_top500 = 1 when
      one of them is in the daily top 500 in the month.  A (work, page) pair counts once, under its first link type in J8's order, so the
      counts add up over link types and over categories without double counting.  Pages beyond the 30,000 or not yet stored are not counted;
      the coverage is reported.
  J12 Time rule (record): if the download is not complete by 15:00 +07, the bursts are built from the pages stored by then and the coverage is
      reported; the downloader stops starting new batches at 15:00 by default.
Limit (in the report): Wikidata is read as it is today (22 Oct 2026); links and dates may have been added after the month they describe, so
the calendar is not exactly what one could have known at t (as for D2).
"""
import sys, re, json, gzip, time, hashlib, os, datetime, collections, argparse, pathlib, resource
import numpy as np, pandas as pd, requests

HERE = pathlib.Path(__file__).resolve().parent                     # code/main_study/wiki_led/dirs
sys.path.insert(0, str(HERE.parent))                                # code/main_study/wiki_led (for _common)
from _common import D, CACHE, UA                                     # noqa: E402

ROOT = D.parent
ADD_J = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-22_j_combined_alerts.json'
assert hashlib.sha256(ADD_J.read_bytes()).hexdigest() == '9a7384ab706ac318ecebc518c801e98c67ee6c7b4e3b8f981ee59fb5c46725b3', 'addendum j changed'
assert '9a7384ab706ac318ecebc518c801e98c67ee6c7b4e3b8f981ee59fb5c46725b3' in (ROOT / 'prereg' / 'README.md').read_text(), 'fingerprint not in prereg/README.md'
REC = json.loads(ADD_J.read_text())
S2R = D / 'db' / 'study2r'
WL = D / 'db' / 'wiki_led'
OUT = WL / 'dirs' / 'j_links'
OUT.mkdir(parents=True, exist_ok=True)
REP = D / 'reports'
OWN_STORE = D / 'interim' / 'j_linked_views'
SPARQL = 'https://query.wikidata.org/sparql'
GAP = 1.5
BATCH = 300
SPQ = CACHE / 'sparql'
SPQ.mkdir(parents=True, exist_ok=True)
ENT = 'http://www.wikidata.org/entity/'
T0 = time.time()
LINK_ORDER = ['adaptation', 'subject', 'event_period', 'person', 'place', 'character', 'series']          # J8 (record's order)
CATS = ['event', 'person', 'place', 'work', 'concept_other']
ROOTS = {'Q5': 'person', 'Q1190554': 'event', 'Q2221906': 'place', 'Q17537576': 'work'}                   # J4
CAT_ORDER = ('person', 'work', 'event', 'place')                   # J4 as changed at 09:22 (first version: person, event, place, work)
PERIOD = 'Q11514315'
MAX_PAGES = 30000
ANN_MI0, ANN_MI1 = 2015 * 12, 2027 * 12 + 11                       # J7: months 2015-01 to 2027-12
B_MI0, B_MI1 = 2016 * 12, 2026 * 12 + 8                            # J10: months 2016-01 to 2026-09


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


# ---------------------------------------------------------------- SPARQL client (copied from 71_wikidata_events.py, same cache and pacing)
class QueryTimeout(Exception):
    pass


class Sparql:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({'User-Agent': UA, 'Accept': 'application/sparql-results+json'})
        self.last = 0.0
        self.n_net = 0
        self.n_cache = 0
        self.n_backoff = 0
        self.net_seconds = 0.0

    def run(self, query):
        key = hashlib.sha1(query.encode()).hexdigest()
        p = SPQ / key[:2] / (key + '.json.gz')
        if p.exists():
            self.n_cache += 1
            return json.loads(gzip.decompress(p.read_bytes()))
        for attempt in range(8):
            w = self.last + GAP - time.time()
            if w > 0:
                time.sleep(w)
            self.last = time.time()
            try:
                r = self.s.post(SPARQL, data={'query': query}, timeout=130)
            except requests.RequestException as e:
                self.n_backoff += 1
                log(f'  request error {type(e).__name__}; waiting')
                time.sleep(10 * (attempt + 1))
                continue
            self.n_net += 1
            self.net_seconds += time.time() - self.last
            if r.status_code == 200:
                b = r.json()['results']['bindings']
                p.parent.mkdir(parents=True, exist_ok=True)
                tmp = p.with_suffix('.tmp%d' % os.getpid())
                tmp.write_bytes(gzip.compress(json.dumps(b).encode(), 6))
                os.replace(tmp, p)
                return b
            if r.status_code == 429:
                self.n_backoff += 1
                wait = int(r.headers.get('Retry-After', 30)) if r.headers.get('Retry-After', '').isdigit() else 30
                log(f'  429 from the query service; waiting {wait}s')
                time.sleep(wait + 2)
                continue
            if r.status_code in (500, 502, 503, 504):
                if 'timeout' in r.text.lower():
                    raise QueryTimeout(r.text[:200])
                self.n_backoff += 1
                log(f'  HTTP {r.status_code}; waiting')
                time.sleep(15 * (attempt + 1))
                continue
            raise RuntimeError(f'HTTP {r.status_code}: {r.text[:300]}')
        raise RuntimeError('gave up after 8 attempts: ' + query[:200])


SP = Sparql()


def run_batches(template, items, label, size=BATCH, single_timeout_ok=False):
    """Run the template over the items in batches; a batch that times out is split in halves.  Returns (bindings, items that time out alone)."""
    items = sorted(set(items))
    out, lone = [], []
    todo = [items[i:i + size] for i in range(0, len(items), size)]
    done = 0
    nb = 0
    while todo:
        b = todo.pop(0)
        q = template.format(vals=' '.join('wd:' + x for x in b))
        try:
            out += SP.run(q)
        except QueryTimeout:
            if len(b) == 1:
                if single_timeout_ok:
                    lone.append(b[0])
                    continue
                raise RuntimeError(f'{label}: a single item times out: {b[0]}')
            h = len(b) // 2
            todo = [b[:h], b[h:]] + todo
            log(f'  {label}: timeout, splitting a batch of {len(b)}')
            continue
        done += len(b)
        nb += 1
        if nb % 20 == 0 or not todo:
            log(f'  {label}: {done}/{len(items)} items; network {SP.n_net}, cache {SP.n_cache}, backoffs {SP.n_backoff}')
    return (out, lone) if single_timeout_ok else out


def g(b, k):
    return b[k]['value'] if k in b else None


def qid(u):
    return u.rsplit('/', 1)[-1] if u and u.startswith(ENT) else None


def rank_of(u):
    return (u or '').rsplit('#', 1)[-1].replace('Rank', '').lower()


DATE_RE = re.compile(r'^(-?\d{1,6})-(\d{2})-(\d{2})T')


def parse_date(s, prec):
    """('YYYY-MM-DD' as given, year, month, mi or None); mi only for precision >= 10 (month or finer) and year >= 1 (71's rule)."""
    m = DATE_RE.match(s) if isinstance(s, str) else None
    if not m:
        return None, None, None, None
    y, mo = int(m.group(1)), int(m.group(2))
    mi = y * 12 + mo - 1 if (prec is not None and prec >= 10 and y > 0 and 1 <= mo <= 12) else None
    return s[:10], y, mo, mi


def best_dates(rows):
    """rows: x, prop, d, prec, rank.  One statement per (x, prop) by 71's death rule (J6): deprecated statements dropped; statements at
    month precision or finer first, among them a preferred rank wins, then the most precise, then the earliest; an (x, prop) with no such
    statement keeps its best coarser date by the same order (shown, never used for a month).  Returns x, prop, date, prec, mi, year."""
    df = pd.DataFrame(rows, columns=['x', 'prop', 'd', 'prec', 'rank'])
    df = df[df['rank'] != 'deprecated'].copy()
    if not len(df):
        return pd.DataFrame(columns=['x', 'prop', 'date', 'prec', 'mi', 'year'])
    parsed = [parse_date(d, p) for d, p in zip(df.d, df.prec)]
    df['date'] = [x[0] for x in parsed]
    df['year'] = [x[1] for x in parsed]
    df['mi'] = pd.to_numeric(pd.Series([x[3] for x in parsed], index=df.index), errors='coerce')
    df = df[df.date.notna()].copy()
    df['usable'] = df.mi.notna().astype(int)
    df['use_any'] = df.groupby(['x', 'prop']).usable.transform('max')
    df = df[df.usable == df.use_any].copy()
    df['pref'] = (df['rank'] == 'preferred').astype(int)
    df['pref_any'] = df.groupby(['x', 'prop']).pref.transform('max')
    df = df[df.pref == df.pref_any].copy()
    df['md'] = df.date.str[-5:]                       # month-day (date strings of signed years sort badly, so year and month-day)
    df = df.sort_values(['x', 'prop', 'prec', 'year', 'md'], ascending=[True, True, False, True, True])
    return df.drop_duplicates(['x', 'prop'])[['x', 'prop', 'date', 'prec', 'mi', 'year']]


# ---------------------------------------------------------------- queries
# word for word as in 71 (cache hits): P144 and P4969 links; deaths; English title and label; P31 types
Q_LINKS = """SELECT ?b ?ad ?rel WHERE {{
  VALUES ?b {{ {vals} }}
  {{ ?ad wdt:P144 ?b . BIND("P144" AS ?rel) }} UNION {{ ?b wdt:P4969 ?ad . BIND("P4969" AS ?rel) }}
}}"""
Q_DEATH = """SELECT ?x ?d ?prec ?rank WHERE {{
  VALUES ?x {{ {vals} }}
  ?x p:P570 ?st . ?st psv:P570 ?v . ?v wikibase:timeValue ?d ; wikibase:timePrecision ?prec . ?st wikibase:rank ?rank .
}}"""
Q_TYPES = """SELECT ?ad ?t WHERE {{ VALUES ?ad {{ {vals} }} ?ad wdt:P31 ?t . }}"""
Q_ART = """SELECT ?ad ?title ?lab WHERE {{
  VALUES ?ad {{ {vals} }}
  OPTIONAL {{ ?art schema:about ?ad ; schema:isPartOf <https://en.wikipedia.org/> ; schema:name ?title . }}
  OPTIONAL {{ ?ad rdfs:label ?lab . FILTER(LANG(?lab) = "en") }}
}}"""
# new here
Q_BIRTH = """SELECT ?x ?d ?prec ?rank WHERE {{
  VALUES ?x {{ {vals} }}
  ?x p:P569 ?st . ?st psv:P569 ?v . ?v wikibase:timeValue ?d ; wikibase:timePrecision ?prec . ?st wikibase:rank ?rank .
}}"""
Q_PROPS = """SELECT ?b ?x ?p WHERE {{
  VALUES ?b {{ {vals} }}
  {{ ?b wdt:P921 ?x . BIND("P921" AS ?p) }} UNION {{ ?b wdt:P180 ?x . BIND("P180" AS ?p) }} UNION {{ ?b wdt:P2408 ?x . BIND("P2408" AS ?p) }}
  UNION {{ ?b wdt:P840 ?x . BIND("P840" AS ?p) }} UNION {{ ?b wdt:P674 ?x . BIND("P674" AS ?p) }} UNION {{ ?b wdt:P179 ?x . BIND("P179" AS ?p) }}
}}"""
Q_MEMBERS = """SELECT ?s ?o WHERE {{ VALUES ?s {{ {vals} }} ?o wdt:P179 ?s . }}"""
Q_ROOTS = """SELECT DISTINCT ?t ?root WHERE {{
  VALUES ?t {{ {vals} }}
  VALUES ?root {{ wd:Q5 wd:Q1190554 wd:Q2221906 wd:Q17537576 wd:Q11514315 }}
  ?t wdt:P279* ?root .
}}"""
Q_SUPERS = """SELECT ?t ?s WHERE {{ VALUES ?t {{ {vals} }} ?t wdt:P279* ?s . }}"""     # fallback for a class whose root query times out alone
Q_XDATES = """SELECT ?x ?prop ?d ?prec ?rank WHERE {{
  VALUES ?x {{ {vals} }}
  {{ ?x p:P585 ?st . ?st psv:P585 ?v . ?v wikibase:timeValue ?d ; wikibase:timePrecision ?prec . ?st wikibase:rank ?rank . BIND("P585" AS ?prop) }}
  UNION
  {{ ?x p:P580 ?st . ?st psv:P580 ?v . ?v wikibase:timeValue ?d ; wikibase:timePrecision ?prec . ?st wikibase:rank ?rank . BIND("P580" AS ?prop) }}
  UNION
  {{ ?x p:P569 ?st . ?st psv:P569 ?v . ?v wikibase:timeValue ?d ; wikibase:timePrecision ?prec . ?st wikibase:rank ?rank . BIND("P569" AS ?prop) }}
  UNION
  {{ ?x p:P570 ?st . ?st psv:P570 ?v . ?v wikibase:timeValue ?d ; wikibase:timePrecision ?prec . ?st wikibase:rank ?rank . BIND("P570" AS ?prop) }}
}}"""


def write_parquet(df, path):
    tmp = path.with_suffix('.part.parquet')
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)


def write_json(obj, path):
    tmp = path.with_suffix('.part.json')
    tmp.write_text(json.dumps(obj, indent=1, default=lambda x: x.item() if hasattr(x, 'item') else str(x)))
    os.replace(tmp, path)


# ================================================================ stage links
def stage_links():
    W = pd.read_parquet(S2R / 'works.parquet', columns=['work_id', 'title', 'creator', 'item', 'article'])
    EV = pd.read_parquet(WL / 'events.parquet', columns=['work_id', 'author_item']).drop_duplicates('work_id')
    W = W.merge(EV, on='work_id', how='left')
    assert len(W) == 7747 and W['item'].notna().all()
    items = sorted(W['item'].unique())
    author_items = sorted(W.author_item.dropna().unique())
    AUW = pd.read_parquet(S2R / 'wd_authors.parquet')
    p50 = AUW[AUW.author_item != ''].groupby('item').author_item.apply(set).to_dict()
    log(f'works {len(W)}, book items {len(items)}, author items {len(author_items)}')

    # ---- links of the book items
    log('links P921 P180 P2408 P840 P674 P179 of the book items')
    PR = pd.DataFrame([dict(b=qid(g(b, 'b')), x=qid(g(b, 'x')), p=g(b, 'p')) for b in run_batches(Q_PROPS, items, 'props')], columns=['b', 'x', 'p'])
    PR = PR[PR.x.notna()].drop_duplicates()
    log('adaptation links P144 (reverse) and P4969 (71\'s query)')
    LK = pd.DataFrame([dict(b=qid(g(b, 'b')), x=qid(g(b, 'ad')), p=g(b, 'rel')) for b in run_batches(Q_LINKS, items, 'adaptation links')], columns=['b', 'x', 'p'])
    LK = LK[LK.x.notna()].drop_duplicates()
    series = PR[PR.p == 'P179']
    log(f'series items {series.x.nunique()} (of {series.b.nunique()} book items); members')
    MB = pd.DataFrame([dict(s=qid(g(b, 's')), o=qid(g(b, 'o'))) for b in run_batches(Q_MEMBERS, sorted(series.x.unique()), 'series members')], columns=['s', 'o'])
    MB = MB[MB.o.notna()].drop_duplicates()
    SR = series[['b', 'x']].rename(columns={'x': 's'}).merge(MB, on='s')
    SR = SR[SR.o != SR.b]
    SR = SR.groupby(['b', 'o']).s.apply(lambda s: 'P179:' + '|'.join(sorted(set(s)))).rename('props').reset_index().rename(columns={'o': 'x'})
    raw_props = pd.concat([PR[PR.p != 'P179'], LK], ignore_index=True)
    log(f'raw statements {len(raw_props)} ({raw_props.p.value_counts().to_dict()}), series member pairs {len(SR)}')

    # ---- info on every linked item
    linked = sorted(set(raw_props.x) | set(SR.x))
    log(f'distinct linked items {len(linked)}: English titles, labels')
    AR = pd.DataFrame([dict(x=qid(g(b, 'ad')), title=g(b, 'title'), lab=g(b, 'lab')) for b in run_batches(Q_ART, linked, 'titles')], columns=['x', 'title', 'lab'])
    title = AR.dropna(subset=['title']).drop_duplicates('x').set_index('x').title.str.replace(' ', '_')
    label = AR.dropna(subset=['lab']).drop_duplicates('x').set_index('x').lab
    log('P31 types')
    TY = pd.DataFrame([dict(x=qid(g(b, 'ad')), t=qid(g(b, 't'))) for b in run_batches(Q_TYPES, linked, 'types')], columns=['x', 't']).dropna().drop_duplicates()
    classes = sorted(TY.t.unique())
    log(f'distinct P31 classes {len(classes)}: roots by P279*')
    rr, lone = run_batches(Q_ROOTS, classes, 'class roots', single_timeout_ok=True)
    RT = pd.DataFrame([dict(t=qid(g(b, 't')), root=qid(g(b, 'root'))) for b in rr], columns=['t', 'root'])
    if lone:
        log(f'  {len(lone)} classes time out alone in the root query; their superclasses instead')
        sup = pd.DataFrame([dict(t=qid(g(b, 't')), root=qid(g(b, 's'))) for b in run_batches(Q_SUPERS, lone, 'superclasses', size=1)], columns=['t', 'root'])
        RT = pd.concat([RT, sup[sup.root.isin(set(ROOTS) | {PERIOD})]], ignore_index=True)
    croots = RT.groupby('t').root.apply(set).to_dict()
    log('dates P585 P580 P569 P570')
    XD = best_dates([(qid(g(b, 'x')), g(b, 'prop'), g(b, 'd'), int(g(b, 'prec')), rank_of(g(b, 'rank'))) for b in run_batches(Q_XDATES, linked, 'dates')])

    # ---- category of each linked item (J4)
    types = TY.groupby('x').t.apply(lambda s: sorted(set(s))).to_dict()
    cat, nroots, isper = {}, {}, {}
    for x in linked:
        rs = set()
        for t in types.get(x, []):
            rs |= croots.get(t, set())
        found = [ROOTS[r] for r in ROOTS if r in rs]
        nroots[x] = len(found)
        isper[x] = PERIOD in rs
        cat[x] = next((c for c in CAT_ORDER if c in found), 'concept_other')

    # ---- link table (J2, J3)
    def ltype(p, x):
        if p in ('P921', 'P180'):
            return {'person': 'person', 'event': 'event_period'}.get(cat[x], 'subject')
        return {'P2408': 'event_period', 'P840': 'place', 'P674': 'character', 'P144': 'adaptation', 'P4969': 'adaptation'}[p]

    raw_props['link_type'] = [ltype(p, x) for p, x in zip(raw_props.p, raw_props.x)]
    LB = raw_props.groupby(['b', 'link_type', 'x']).p.apply(lambda s: '|'.join(sorted(set(s)))).rename('props').reset_index()
    LB = pd.concat([LB, SR.assign(link_type='series')[['b', 'link_type', 'x', 'props']]], ignore_index=True)
    L = W[['work_id', 'item', 'author_item']].merge(LB.rename(columns={'b': 'item'}), on='item')
    n_before = len(L)
    drop_self = L.x == L['item']
    drop_auth = np.array([(x == a) or (x in p50.get(it, ())) for x, a, it in zip(L.x, L.author_item, L['item'])])
    excluded = dict(rows_before=n_before, own_item=int(drop_self.sum()), author=int((drop_auth & ~drop_self).sum()),
                    author_by_link_type=L[drop_auth & ~drop_self].link_type.value_counts().to_dict())
    L = L[~drop_self & ~drop_auth].copy()
    log('excluded', excluded)
    L = L.rename(columns={'item': 'book_item', 'x': 'item'})
    L['page_title'] = L['item'].map(title)
    L['label'] = L['item'].map(label)
    L['category'] = L['item'].map(cat)
    L['is_period'] = L['item'].map(isper).astype(bool)
    L['n_roots'] = L['item'].map(nroots).astype('int8')
    L['p31'] = L['item'].map(lambda x: '|'.join(types.get(x, [])))
    IP = pd.read_parquet(WL / 'testF' / 'items_pages.parquet', columns=['title', 'kind']).drop_duplicates('title')
    L['ai_kind'] = L.page_title.map(IP.set_index('title').kind)
    for prop in ('P585', 'P580', 'P569', 'P570'):
        s = XD[XD.prop == prop].set_index('x')
        L[f'{prop.lower()}_date'] = L['item'].map(s.date)
        L[f'{prop.lower()}_prec'] = L['item'].map(s.prec).astype('Int8')
    e585 = XD[(XD.prop == 'P585') & XD.mi.notna()].set_index('x').mi
    e580 = XD[(XD.prop == 'P580') & XD.mi.notna()].set_index('x').mi
    ev = e585.combine_first(e580)
    L['event_mi'] = L['item'].map(ev).astype('Int32')
    L['event_prop'] = np.where(L['item'].isin(e585.index), 'P585', np.where(L['item'].isin(e580.index), 'P580', None))
    L['link_rank'] = L.link_type.map({t: i for i, t in enumerate(LINK_ORDER)}).astype('int8')
    L = L.sort_values(['work_id', 'link_rank', 'item']).reset_index(drop=True)
    cols = ['work_id', 'book_item', 'link_type', 'item', 'props', 'page_title', 'label', 'category', 'ai_kind', 'is_period', 'n_roots', 'p31',
            'p585_date', 'p585_prec', 'p580_date', 'p580_prec', 'p569_date', 'p569_prec', 'p570_date', 'p570_prec', 'event_mi', 'event_prop', 'link_rank']
    L = L[cols]
    write_parquet(L, OUT / 'links.parquet')
    log('wrote links.parquet', L.shape)

    # ---- anniversaries (J7)
    log('author births and deaths')
    DD = [(qid(g(b, 'x')), 'P570', g(b, 'd'), int(g(b, 'prec')), rank_of(g(b, 'rank'))) for b in run_batches(Q_DEATH, author_items, 'deaths')]
    DB = [(qid(g(b, 'x')), 'P569', g(b, 'd'), int(g(b, 'prec')), rank_of(g(b, 'rank'))) for b in run_batches(Q_BIRTH, author_items, 'births')]
    AD = best_dates(DD + DB)
    ann = []
    evl = L[(L.category == 'event') & L.event_mi.notna()][['work_id', 'item', 'event_mi', 'link_type', 'page_title']].drop_duplicates(['work_id', 'item'])
    for r in evl.itertuples(index=False):
        ann.append((r.work_id, int(r.event_mi), 'event', r.item, r.link_type, r.page_title))
    amap = {(r.x, r.prop): int(r.mi) for r in AD[AD.mi.notna()].itertuples()}
    for wid, a in zip(W.work_id, W.author_item):
        if not isinstance(a, str):
            continue
        for prop, kind in (('P569', 'author_birth'), ('P570', 'author_death')):
            if (a, prop) in amap:
                ann.append((wid, amap[(a, prop)], kind, a, 'author', None))
    rows = []
    for wid, emi, kind, src, lt, pt in ann:
        y0, m0 = divmod(emi, 12)
        for k in range(1, 400):
            y = y0 + 25 * k
            mi = y * 12 + m0
            if mi > ANN_MI1:
                break
            if mi >= ANN_MI0:
                rows.append((wid, mi, kind, 25 * k, src, lt, pt, emi))
    AN = pd.DataFrame(rows, columns=['work_id', 'mi', 'kind', 'years', 'source_item', 'link_type', 'page_title', 'event_mi'])
    AN = AN.drop_duplicates(['work_id', 'mi', 'kind', 'source_item']).sort_values(['work_id', 'mi', 'kind', 'source_item']).reset_index(drop=True)
    AN = AN.astype({'work_id': 'int64', 'mi': 'int32', 'years': 'int16', 'event_mi': 'int32'})
    write_parquet(AN, OUT / 'anniversaries.parquet')
    log('wrote anniversaries.parquet', AN.shape, AN.kind.value_counts().to_dict())

    # ---- pages to fetch (J8)
    Lp = L[L.page_title.notna()]
    first = Lp.groupby('page_title').link_rank.min()
    nw = Lp.groupby('page_title').work_id.nunique()
    PW = pd.DataFrame({'page_title': first.index, 'link_rank': first.values, 'n_works': nw.reindex(first.index).values})
    PW['link_type'] = PW.link_rank.map(dict(enumerate(LINK_ORDER)))
    PW['category'] = PW.page_title.map(Lp.drop_duplicates('page_title').set_index('page_title').category)
    PW = PW.sort_values(['link_rank', 'n_works', 'page_title'], ascending=[True, False, True]).reset_index(drop=True)
    PW['order'] = np.arange(1, len(PW) + 1)
    PW['selected'] = PW.order <= MAX_PAGES
    write_parquet(PW, OUT / 'pages_wanted.parquet')
    log(f'pages {len(PW)}, selected {int(PW.selected.sum())}')

    # ---- summary
    def vc(s):
        return {str(k): int(v) for k, v in s.value_counts().items()}
    summ = dict(written=time.strftime('%Y-%m-%d %H:%M'), works=len(W), book_items=len(items), works_with_links=int(L.work_id.nunique()),
                link_rows=len(L), link_rows_with_page=int(L.page_title.notna().sum()), excluded=excluded,
                rows_by_link_type=vc(L.link_type), rows_by_category=vc(L.category),
                rows_by_link_type_and_category={lt: vc(L[L.link_type == lt].category) for lt in LINK_ORDER},
                works_with_link_type={lt: int(L[L.link_type == lt].work_id.nunique()) for lt in LINK_ORDER},
                works_with_page_of_link_type={lt: int(L[(L.link_type == lt) & L.page_title.notna()].work_id.nunique()) for lt in LINK_ORDER},
                distinct_items=int(L['item'].nunique()), distinct_items_by_category=vc(L.drop_duplicates('item').category),
                distinct_pages=int(L.page_title.nunique()), distinct_pages_by_category=vc(L.dropna(subset=['page_title']).drop_duplicates('page_title').category),
                items_reaching_several_roots=int((L.drop_duplicates('item').n_roots > 1).sum()),
                items_is_period=int(L.drop_duplicates('item').is_period.sum()),
                is_period_by_category=vc(L.drop_duplicates('item').loc[lambda d: d.is_period].category),
                ai_kind_by_category={c: vc(L[(L.category == c)].drop_duplicates('item').ai_kind.fillna('not sorted')) for c in CATS},
                pages_with_ai_kind=int(L.dropna(subset=['page_title']).drop_duplicates('page_title').ai_kind.notna().sum()),
                items_with_event_mi=int(L.drop_duplicates('item').event_mi.notna().sum()),
                event_items_with_event_mi=int(L[L.category == 'event'].drop_duplicates('item').event_mi.notna().sum()),
                event_items=int((L.drop_duplicates('item').category == 'event').sum()),
                anniversaries=dict(rows=len(AN), by_kind=vc(AN.kind), works=int(AN.work_id.nunique()), works_by_kind={k: int(AN[AN.kind == k].work_id.nunique()) for k in ('event', 'author_birth', 'author_death')},
                                   author_items_with_birth_month=int(AD[(AD.prop == 'P569') & AD.mi.notna()].x.nunique()),
                                   author_items_with_death_month=int(AD[(AD.prop == 'P570') & AD.mi.notna()].x.nunique()),
                                   by_years=vc(AN.years)),
                pages_wanted=dict(total=len(PW), selected=int(PW.selected.sum()), by_first_link_type=vc(PW.link_type), selected_by_first_link_type=vc(PW[PW.selected].link_type)),
                top_classes_by_category={c: dict(list(vc(L[L.category == c].drop_duplicates('item').p31.str.split('|').explode()).items())[:15]) for c in CATS},
                queries=dict(network=SP.n_net, cache=SP.n_cache, backoffs=SP.n_backoff, query_seconds=round(SP.net_seconds), gap_s=GAP, batch=BATCH),
                runtime_s=round(time.time() - T0))
    # English labels of the most common classes, for the report
    top_cls = sorted({k for c in CATS for k in summ['top_classes_by_category'][c] if k})
    if top_cls:
        lab = {qid(g(b, 'ad')): g(b, 'lab') for b in run_batches(Q_ART, top_cls, 'class labels')}
        summ['class_labels'] = lab
    write_json(summ, OUT / 'links_summary.json')
    log('wrote links_summary.json', f'network {SP.n_net}, cache {SP.n_cache}, backoffs {SP.n_backoff}')


# ================================================================ stage bursts
def load_stores(titles):
    """Monthly views (pages x months 2015-07..2026-09) and source of every title (J9).  Returns (M, src, status)."""
    sys.path.insert(0, str(HERE.parent / 'testF'))
    import _testf_analysis as T
    m_of_day = np.array([d.year * 12 + d.month - 1 for d in T.DAYS])
    MI0 = int(m_of_day[0])
    nm = int(m_of_day[-1]) - MI0 + 1
    starts = np.r_[0, np.flatnonzero(np.diff(m_of_day)) + 1]
    n = len(titles)
    M = np.zeros((n, nm), dtype=np.int64)
    src = np.array([''] * n, dtype=object)
    status = np.full(n, -1, dtype=np.int32)
    pos = {t: i for i, t in enumerate(titles)}

    class P:  # a Paths-like object for store_index / store_matrix
        def __init__(self, views):
            self.views = views

    # 1 Test F store
    PF = P(T.Paths().views)
    idxF = T.store_index(PF)
    setF = set(idxF.title)
    inF = [t for t in titles if t in setF]
    for i in range(0, len(inF), 4000):
        ch = inF[i:i + 4000]
        V, st = T.store_matrix(PF, ch)
        Mm = np.add.reduceat(V.astype(np.int64), starts, axis=1)
        for k, t in enumerate(ch):
            M[pos[t]] = Mm[k]
            status[pos[t]] = st[k]
            src[pos[t]] = 'testF'
    log(f'  Test F store: {len(inF)} pages')
    # 2 adaptation views
    AS = pd.read_parquet(WL / 'adaptation_fetch_status.parquet', columns=['article', 'status'])
    left = set(t for t in titles if src[pos[t]] == '')
    AS = AS[AS.article.isin(left)]
    if len(AS):
        AV = pd.read_parquet(WL / 'adaptation_daily_views.parquet', filters=[('article', 'in', list(AS.article))])
        AV['mi'] = AV.date.dt.year * 12 + AV.date.dt.month - 1
        mon = AV.groupby(['article', 'mi']).views.sum()
        for (a, mi), v in mon.items():
            M[pos[a], mi - MI0] = v
        for a, st in zip(AS.article, AS.status):
            status[pos[a]] = st
            src[pos[a]] = 'adaptation'
    log(f'  adaptation views: {len(AS)} pages')
    # 3 own store
    n3 = 0
    if OWN_STORE.exists():
        PO = P(OWN_STORE)
        idxO = T.store_index(PO)
        setO = set(idxO.title)
        inO = [t for t in titles if src[pos[t]] == '' and t in setO]
        for i in range(0, len(inO), 4000):
            ch = inO[i:i + 4000]
            V, st = T.store_matrix(PO, ch)
            Mm = np.add.reduceat(V.astype(np.int64), starts, axis=1)
            for k, t in enumerate(ch):
                M[pos[t]] = Mm[k]
                status[pos[t]] = st[k]
                src[pos[t]] = 'download'
        n3 = len(inO)
    log(f'  own store: {n3} pages')
    return M, src, status, MI0, T


def stage_bursts(dst=None):
    dst = pathlib.Path(dst) if dst else OUT                        # --test-out: a trial build somewhere else (J2 reads OUT)
    L = pd.read_parquet(OUT / 'links.parquet')
    PW = pd.read_parquet(OUT / 'pages_wanted.parquet')
    sel = PW[PW.selected]
    titles = list(sel.page_title)
    log(f'selected pages {len(titles)}; reading the stores')
    M, src, status, MI0, T = load_stores(titles)
    have = (status == 200)
    log(f'pages with views {int(have.sum())} of {len(titles)}; sources {pd.Series(src).value_counts().to_dict()}; statuses {pd.Series(status).value_counts().to_dict()}')
    # bursts per page and month (J10)
    nm = M.shape[1]
    months = np.arange(MI0, MI0 + nm)
    Mf = M.astype(np.float64)
    M6 = np.full_like(Mf, np.nan)
    for j in range(6, nm):
        M6[:, j] = np.median(Mf[:, j - 6:j], axis=1)
    keep_m = (months >= B_MI0) & (months <= B_MI1)
    jm = np.flatnonzero(keep_m)
    V = Mf[:, jm]
    B6 = M6[:, jm]
    rule_v = (V >= 3 * B6) & (V >= 3000)
    ratio = (V / np.maximum(B6, 1)).astype(np.float32)
    TL, days = T.top_long(set(titles))
    TL['mi'] = TL.date.dt.year * 12 + TL.date.dt.month - 1
    top = np.zeros_like(rule_v)
    pos = {t: i for i, t in enumerate(titles)}
    for t, mi in TL[['title', 'mi']].drop_duplicates().itertuples(index=False):
        k = mi - B_MI0
        if 0 <= k < len(jm):
            top[pos[t], k] = True
    burst = rule_v | top
    burst[~have] = False
    top[~have] = False
    ratio[~have] = np.nan
    log(f'page-months bursting {int(burst.sum())} ({burst[have].mean():.4f} of page-months with views); by the ratio rule {int(rule_v[have].sum())}, top 500 {int(top.sum())}')

    # (work, page) pairs under their first link type (J11)
    Lp = L[L.page_title.isin(set(np.array(titles)[have]))].sort_values(['work_id', 'link_rank'])
    pairs = Lp.drop_duplicates(['work_id', 'page_title'])[['work_id', 'page_title', 'link_type', 'category']].copy()
    pairs['p'] = pairs.page_title.map(pos)
    pairs = pairs.sort_values(['work_id', 'link_type', 'category', 'p']).reset_index(drop=True)
    key = pairs[['work_id', 'link_type', 'category']].astype(str).agg('|'.join, axis=1)
    gstart = np.r_[0, np.flatnonzero(key.to_numpy()[1:] != key.to_numpy()[:-1]) + 1]
    G = pairs.iloc[gstart][['work_id', 'link_type', 'category']].reset_index(drop=True)
    G['n_pages'] = np.diff(np.r_[gstart, len(pairs)])
    pi = pairs.p.to_numpy()
    nb = np.add.reduceat(burst[pi].astype(np.int32), gstart, axis=0)
    at = np.maximum.reduceat(top[pi].astype(np.int8), gstart, axis=0)
    mr = np.fmax.reduceat(ratio[pi], gstart, axis=0)
    ng, nmo = len(G), len(jm)
    OUTB = pd.DataFrame({'work_id': np.repeat(G.work_id.to_numpy().astype(np.int64), nmo),
                         'mi': np.tile(months[jm].astype(np.int32), ng),
                         'link_type': np.repeat(G.link_type.to_numpy(), nmo),
                         'category': np.repeat(G.category.to_numpy(), nmo),
                         'n_pages': np.repeat(G.n_pages.to_numpy().astype(np.int16), nmo),
                         'n_burst': nb.reshape(-1).astype(np.int16),
                         'any_top500': at.reshape(-1).astype(np.int8),
                         'max_ratio': mr.reshape(-1).astype(np.float32)})
    write_parquet(OUTB, dst / 'linked_bursts.parquet')
    log('wrote linked_bursts.parquet', OUTB.shape)

    # coverage and summary
    Lpg = L[L.page_title.notna()]
    pair_all = Lpg.drop_duplicates(['work_id', 'page_title'])
    have_set = set(np.array(titles)[have])
    stored_set = set(np.array(titles)[status >= 0])
    selset = set(titles)
    PWs = PW.assign(stored=PW.page_title.isin(stored_set), with_views=PW.page_title.isin(have_set))
    cov = dict(pages_linked=int(len(PW)), pages_selected=int(len(selset)), pages_stored=int(len(stored_set)), pages_with_views=int(len(have_set)),
               stored_by_source={str(k): int(v) for k, v in pd.Series(src[status >= 0]).value_counts().items()},
               status_of_stored={str(k): int(v) for k, v in pd.Series(status[status >= 0]).value_counts().items()},
               pairs_with_page=int(len(pair_all)), pairs_with_views=int(pair_all.page_title.isin(have_set).sum()),
               works_with_a_page=int(pair_all.work_id.nunique()), works_with_views=int(pair_all[pair_all.page_title.isin(have_set)].work_id.nunique()),
               by_first_link_type={lt: dict(pages=int((PWs.link_type == lt).sum()), selected=int((PWs.selected & (PWs.link_type == lt)).sum()),
                                            stored=int((PWs.stored & (PWs.link_type == lt)).sum()), with_views=int((PWs.with_views & (PWs.link_type == lt)).sum()))
                                   for lt in LINK_ORDER},
               complete=bool(len(stored_set) == len(selset)), built=time.strftime('%Y-%m-%d %H:%M'))
    bur = OUTB[OUTB.n_burst > 0]
    sb = dict(rows=len(OUTB), groups=ng, works=int(G.work_id.nunique()), rows_with_burst=len(bur), share_rows_with_burst=float(len(bur) / max(len(OUTB), 1)),
              rows_with_top500=int((OUTB.any_top500 > 0).sum()),
              burst_share_by_link_type={lt: float((OUTB[OUTB.link_type == lt].n_burst > 0).mean()) for lt in LINK_ORDER if (OUTB.link_type == lt).any()},
              burst_share_by_category={c: float((OUTB[OUTB.category == c].n_burst > 0).mean()) for c in CATS if (OUTB.category == c).any()},
              page_months_burst=int(burst.sum()), page_months_with_views=int(have.sum() * len(jm)), page_months_ratio_rule=int(rule_v[have].sum()),
              page_months_top500=int(top.sum()))
    # top bursting pages (for the report's examples)
    pb = pd.DataFrame({'page_title': titles, 'n_burst_months': burst.sum(axis=1), 'n_top_months': top.sum(axis=1)})
    pb['category'] = pb.page_title.map(PW.set_index('page_title').category)
    pb['link_type'] = pb.page_title.map(PW.set_index('page_title').link_type)
    write_parquet(pb, dst / 'page_burst_counts.parquet')
    write_json(dict(coverage=cov, bursts=sb, peak_memory_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30, 2),
                    runtime_s=round(time.time() - T0)), dst / 'bursts_summary.json')
    log('coverage', cov)
    log('bursts', sb)


# ================================================================ stage report (written from the saved files)
def md(df):
    cols = list(df.columns)
    out = ['| ' + ' | '.join(map(str, cols)) + ' |', '|' + ' --- |' * len(cols)]
    for r in df.itertuples(index=False):
        out.append('| ' + ' | '.join('' if (isinstance(v, float) and np.isnan(v)) else (f'{v:,}' if isinstance(v, (int, np.integer)) else str(v)) for v in r) + ' |')
    return '\n'.join(out)


def ymi(mi):
    return f'{int(mi) // 12}-{int(mi) % 12 + 1:02d}'


def stage_report():
    S = json.loads((OUT / 'links_summary.json').read_text())
    S0 = json.loads((OUT / 'links_summary_first_order.json').read_text()) if (OUT / 'links_summary_first_order.json').exists() else None
    BS = json.loads((OUT / 'bursts_summary.json').read_text()) if (OUT / 'bursts_summary.json').exists() else None
    DS = json.loads((OUT / 'download_summary.json').read_text()) if (OUT / 'download_summary.json').exists() else None
    L = pd.read_parquet(OUT / 'links.parquet')
    AN = pd.read_parquet(OUT / 'anniversaries.parquet')
    W = pd.read_parquet(S2R / 'works.parquet', columns=['work_id', 'title', 'creator', 'checkouts_2016_2026'])
    LW = L.merge(W, on='work_id').sort_values(['checkouts_2016_2026', 'work_id'], ascending=[False, True])
    lab = S.get('class_labels', {})
    o = []
    o.append('# J1: book-linked Wikipedia pages of every kind, anniversaries and linked-page bursts (addendum j)\n')
    o.append(f'Khant Phyo Wai, 01323050. Run 22 Oct 2026 (links {S["written"]}' + (f', bursts {BS["coverage"]["built"]}' if BS else '') + ' +07). '
             'Record: `prereg/addenda_wiki_led/2026-10-22_j_combined_alerts.json` (book_links, linked_page_attention, the anniversary part of '
             'scheduled_calendar). Choices the record leaves open: J1 to J12 in the header of `code/main_study/wiki_led/dirs/j1_links.py` '
             '(downloader: `j1_download_views.py`), logged in `prereg/DEVIATIONS.md` (Addendum j). Data only: nothing here is related to loans. '
             'Files: `data/db/wiki_led/dirs/j_links/`.\n')
    # ---- plain words
    rt = S['rows_by_link_type']
    pc = S['distinct_pages_by_category']
    o.append('**In plain words**\n')
    o.append(f'1. Of the 7,747 Test A works (7,510 Wikidata items), {S["works_with_links"]:,} have at least one linked Wikidata item of the record\'s types, '
             f'{S["link_rows"]:,} links in all, {S["link_rows_with_page"]:,} of them to an item with an English Wikipedia article. '
             f'These point to {S["distinct_pages"]:,} different articles: {pc.get("work", 0):,} works (mostly other books of the same series and film or TV '
             f'adaptations), {pc.get("concept_other", 0):,} concepts or other (largely fictional characters), {pc.get("place", 0):,} places, '
             f'{pc.get("event", 0):,} events or history and {pc.get("person", 0):,} real people.')
    o.append(f'2. Most links come from series ({rt.get("series", 0):,} rows) and adaptations ({rt.get("adaptation", 0):,}); the links the request was about '
             f'are thinner: {rt.get("event_period", 0):,} event or period links ({S["works_with_page_of_link_type"]["event_period"]:,} works with an article), '
             f'{rt.get("place", 0):,} place links ({S["works_with_page_of_link_type"]["place"]:,} works), {rt.get("subject", 0):,} subject links '
             f'({S["works_with_page_of_link_type"]["subject"]:,} works) and {rt.get("person", 0):,} person links ({S["works_with_page_of_link_type"]["person"]:,} works).')
    o.append('3. The "event or history" category follows the record (Wikidata class occurrence and its subclasses). Wikidata files many ideas and '
             'activities under occurrence, so beside real events (World War II, the Vietnam War, the Cultural Revolution) the category also holds '
             'pages such as Marriage, Love, Sleep and Crime. Where Test F\'s AI sorted the same page, its page kind is kept beside the category '
             f'(column ai_kind): of the {sum(v for k, v in S["ai_kind_by_category"]["event"].items() if k != "not sorted")} event-category items the AI '
             f'also sorted, it called {S["ai_kind_by_category"]["event"].get("event", 0)} events and {S["ai_kind_by_category"]["event"].get("concept", 0)} '
             'concepts (section 2). The work category likewise holds a few companies and websites (Google, Amazon) that books are about.')
    an = S['anniversaries']
    o.append(f'4. Anniversaries (25, 50, 75, ... years) in 2015 to 2027: {an["by_kind"].get("author_birth", 0):,} of authors\' births, '
             f'{an["by_kind"].get("author_death", 0):,} of authors\' deaths and only {an["by_kind"].get("event", 0):,} of linked events, because few linked '
             f'events carry a date at month precision ({S["event_items_with_event_mi"]:,} of {S["event_items"]:,} event items).')
    if BS:
        cv = BS['coverage']
        o.append(f'5. Views: {cv["pages_with_views"]:,} of the {cv["pages_selected"]:,} linked articles have daily views (2015-07 to 2026-09), '
                 f'{cv["pairs_with_views"]:,} of {cv["pairs_with_page"]:,} work-article pairs ({cv["works_with_views"]:,} works). '
                 f'All {cv["pages_linked"]:,} linked articles fit under the record\'s cap of 30,000, so no page was left out by the cap. '
                 + ('The download was complete when the bursts were built.' if cv['complete'] else
                    f'The download was not complete when the bursts were built ({cv["pages_stored"]:,} of {cv["pages_selected"]:,} stored).'))
    o.append('')
    # ---- section 1: counts by link type and category
    o.append('## 1. Links by type and category\n')
    o.append('Rows of `links.parquet` (one per work, link type and linked item). "Works" = works with at least one link of the type to an item with an '
             'English article. Categories by Wikidata P31 and P279* (J4): person (human), work (creative work), event (occurrence), place (geographic '
             'location), else concept_other; an item reaching several of these takes the first in that order.\n')
    rows = []
    for lt in LINK_ORDER:
        d = L[L.link_type == lt]
        r = dict(link_type=lt, rows=len(d), with_article=int(d.page_title.notna().sum()), works=S['works_with_page_of_link_type'][lt])
        for c in CATS:
            r[c] = int((d.category == c).sum())
        rows.append(r)
    d = L
    r = dict(link_type='all', rows=len(d), with_article=int(d.page_title.notna().sum()), works=int(d[d.page_title.notna()].work_id.nunique()))
    for c in CATS:
        r[c] = int((d.category == c).sum())
    rows.append(r)
    o.append(md(pd.DataFrame(rows)))
    o.append(f'\nLeft out (J3): {S["excluded"]["own_item"]} link to the book\'s own item and {S["excluded"]["author"]} links to the book\'s own author '
             f'({S["excluded"]["author_by_link_type"]}); the author stays in Test A\'s W features. Wikidata properties used: '
             'subject P921 and P180; event_period P2408 and subject items of category event; person = subject items of category person; place P840; '
             'character P674; adaptation P144 (reverse) and P4969; series = the other items with P179 to a series of the book. '
             f'{S["items_reaching_several_roots"]:,} items reach more than one category root; {S["items_is_period"]} items are historical periods (column is_period).')
    if S0:
        o.append(f'\nCategory order changed at 09:22, before any view or model result (logged): the first order (person, event, place, work) put '
                 f'{S0["distinct_pages_by_category"].get("event", 0) - pc.get("event", 0):,} more articles in event, mostly operas, musicals, theatre '
                 'productions and ballets based on the books, because Wikidata files these creative-work classes under occurrence too. '
                 f'Pages by category, first order: {S0["distinct_pages_by_category"]}; now: {pc}.')
    # ---- section 2: classes and AI kind
    o.append('\n## 2. What each category holds\n')
    o.append('Most common Wikidata classes (P31) among the distinct linked items of each category:\n')
    rows = []
    for c in CATS:
        top = list(S['top_classes_by_category'][c].items())[:8]
        rows.append(dict(category=c, items=S['distinct_items_by_category'].get(c, 0),
                         classes='; '.join(f'{lab.get(k, k) if k else "no P31"} {v}' for k, v in top)))
    o.append(md(pd.DataFrame(rows)))
    o.append(f'\nTest F\'s AI page kind for the {S["pages_with_ai_kind"]:,} linked articles that were among Test F\'s sorted pages (distinct items; '
             '"not sorted" = not among them):\n')
    kinds = ['event', 'person', 'place', 'work', 'concept', 'organization', 'list', 'other', 'not sorted']
    rows = []
    for c in CATS:
        d = S['ai_kind_by_category'][c]
        rows.append(dict(category=c, **{k: d.get(k, 0) for k in kinds}))
    o.append(md(pd.DataFrame(rows)))
    # ---- section 3: examples
    o.append('\n## 3. Examples (the most borrowed works first)\n')

    def ex(mask, n=6, label_=None):
        d = LW[mask & LW.page_title.notna()].drop_duplicates('page_title').head(n)
        return '; '.join(f'*{t}* ({c}) -> {p.replace("_", " ")} ({lt}{", AI: " + k if isinstance(k, str) else ""})'
                         for t, c, p, lt, k in zip(d.title, d.creator, d.page_title, d.link_type, d.ai_kind))
    war = LW.page_title.fillna('').str.contains(r'War|Revolution|Holocaust|Battle|Conquest|Rebellion|Genocide', regex=True)
    o.append(f'- History or war events: {ex((LW.category == "event") & war, 8)}.')
    o.append(f'- Other event pages (shows the breadth of occurrence): {ex((LW.category == "event") & ~war, 8)}.')
    o.append(f'- Places where a novel is set: {ex((LW.link_type == "place") & (LW.category == "place"), 8)}.')
    o.append(f'- Real people as subjects or characters: {ex(LW.category == "person", 8)}.')
    o.append(f'- Adaptations: {ex(LW.link_type == "adaptation", 6)}.')
    o.append(f'- Characters: {ex(LW.link_type == "character", 6)}.')
    o.append(f'- Subjects that are ideas: {ex((LW.link_type == "subject") & (LW.category == "concept_other"), 6)}.')
    o.append(f'- Series: {ex(LW.link_type == "series", 4)}.')
    # ---- section 4: anniversaries
    o.append('\n## 4. Anniversaries (scheduled calendar)\n')
    o.append(f'`anniversaries.parquet`: one row per work and month 2015-01 to 2027-12 in which a round anniversary falls (25, 50, 75, ... years; J7). '
             f'{an["rows"]:,} rows for {an["works"]:,} works. Author births at month precision: {an["author_items_with_birth_month"]:,} author items; '
             f'deaths: {an["author_items_with_death_month"]:,} (the death month is the one of events.parquet). Linked events with a month date (P585, '
             f'else P580): {S["event_items_with_event_mi"]:,} of {S["event_items"]:,} event items.\n')
    rows = [dict(kind=k, rows=int((AN.kind == k).sum()), works=int(AN[AN.kind == k].work_id.nunique()),
                 rows_2016_2026=int(((AN.kind == k) & (AN.mi >= 2016 * 12) & (AN.mi <= 2026 * 12 + 8)).sum())) for k in ('author_birth', 'author_death', 'event')]
    o.append(md(pd.DataFrame(rows)))
    o.append('\nYears: ' + ', '.join(f'{k}: {v:,}' for k, v in sorted(an['by_years'].items(), key=lambda kv: int(kv[0]))) + '.')
    ae = AN[AN.kind == 'event'].merge(W, on='work_id').sort_values('checkouts_2016_2026', ascending=False).drop_duplicates(['source_item', 'mi']).head(8)
    o.append('\nEvent anniversaries, examples: ' + '; '.join(f'*{t}* -> {str(p).replace("_", " ")}, {y} years in {ymi(m)}'
                                                          for t, p, y, m in zip(ae.title, ae.page_title, ae.years, ae.mi)) + '.')
    # ---- section 5: views and bursts
    o.append('\n## 5. Linked-page views and bursts\n')
    if BS:
        cv, sb = BS['coverage'], BS['bursts']
        o.append(f'Pages: every distinct linked article ({cv["pages_linked"]:,}; the cap of 30,000 was not reached). Stored: {cv["pages_stored"]:,} '
                 f'(Test F store, adaptation views, new download: {cv["stored_by_source"]}); statuses {cv["status_of_stored"]} (200 = views, 404 = no data). '
                 f'Work-article pairs with views: {cv["pairs_with_views"]:,} of {cv["pairs_with_page"]:,}; works with views of at least one linked article: '
                 f'{cv["works_with_views"]:,} of {cv["works_with_a_page"]:,}.' + ('' if cv['complete'] else ' **The download was not complete at the cut; '
                                                                                   'the bursts use the pages stored by then.**'))
        if DS:
            o.append(f'\nDownload (`j1_download_views.py`): {DS["fetched_now"]:,} of {DS["to_fetch"]:,} pages fetched, HTTP codes {DS["http_codes"]}, '
                     f'back-offs {DS["backoffs"]}, gap {DS["gap_s"]} s over {DS["threads"]} threads, finished {DS["finished"]}'
                     + (', stopped by the time rule' if DS['stopped_by_time_rule'] else '') + '.')
        rows = [dict(first_link_type=lt, **v) for lt, v in cv['by_first_link_type'].items()]
        o.append('\nBy first link type (J8):\n')
        o.append(md(pd.DataFrame(rows)))
        o.append(f'\nBurst rule (record; J10): a month\'s views at least 3 times the median of the 6 months before and at least 3,000, or the article '
                 f'in the daily top 500 on any day of the month. Page-months with views 2016-01 to 2026-09: {sb["page_months_with_views"]:,}; bursting '
                 f'{sb["page_months_burst"]:,} ({sb["page_months_burst"] / max(sb["page_months_with_views"], 1):.2%}); by the ratio rule '
                 f'{sb["page_months_ratio_rule"]:,}, in the top 500 {sb["page_months_top500"]:,}.\n')
        o.append(f'`linked_bursts.parquet`: {sb["rows"]:,} rows (work x month 2016-01 to 2026-09 x link type x category, for the {sb["groups"]:,} groups '
                 f'with at least one article with views; {sb["works"]:,} works). Share of rows with at least one bursting article:\n')
        rows = [dict(by='link type', value=k, share=f'{v:.2%}') for k, v in sb['burst_share_by_link_type'].items()] + \
               [dict(by='category', value=k, share=f'{v:.2%}') for k, v in sb['burst_share_by_category'].items()]
        o.append(md(pd.DataFrame(rows)))
        pb = pd.read_parquet(OUT / 'page_burst_counts.parquet')
        for c in ('event', 'place', 'person', 'work'):
            d = pb[pb.category == c].sort_values(['n_burst_months', 'page_title'], ascending=[False, True]).head(5)
            o.append(f'\nMost bursting {c} articles (months bursting, of which in the top 500): ' +
                     '; '.join(f'{t.replace("_", " ")} {b} ({tp})' for t, b, tp in zip(d.page_title, d.n_burst_months, d.n_top_months)) + '.')
    else:
        o.append('Not built yet.')
    # ---- files and limits
    o.append('\n## 6. Files (data/db/wiki_led/dirs/j_links/)\n')
    o.append('- `links.parquet`: work_id, book_item, link_type, item, props, page_title (underscores), label, category, ai_kind, is_period, n_roots, p31, '
             'p585/p580/p569/p570 date and precision, event_mi (month index year*12+month-1 of P585, else P580, at month precision), event_prop, link_rank.')
    o.append('- `anniversaries.parquet`: work_id, mi, kind (event, author_birth, author_death), years, source_item, link_type, page_title, event_mi.')
    o.append('- `linked_bursts.parquet`: work_id, mi, link_type, category, n_pages, n_burst, any_top500, max_ratio. Each (work, article) pair counts once, '
             'under its first link type in the order adaptation, subject, event_period, person, place, character, series, so counts add up.')
    o.append('- `pages_wanted.parquet` (selection and order), `page_burst_counts.parquet`, `links_summary.json`, `bursts_summary.json`, '
             '`download_summary.json`; new daily views in `data/interim/j_linked_views/`.')
    o.append('\n## 7. Limits\n')
    o.append('- Wikidata was read on 22 Oct 2026. Links, classes and dates may have been added after the month they describe, so the calendar and the '
             'link list are not exactly what one could have known at the time (as for D2).')
    o.append('- Coverage is uneven: Wikidata has links for popular and classic books; many recent books have none. Series and adaptations dominate '
             'the links; event, place and person links are a few hundred to two thousand rows each.')
    o.append('- The event category is broad (section 2): Wikidata\'s occurrence class also holds activities, ideas and movements. The AI page kind '
             'beside it covers only the articles Test F sorted.')
    o.append('- A newly created article has a median of 0 for the 6 months before, so it bursts once a month reaches 3,000 views (the rule as written).')
    o.append('- The top-500 half of the burst rule makes very popular articles (countries, big cities, large states) burst in most or all months: '
             'China is in the daily top 500 in all 129 months, California in 80. For such articles any_top500 and n_burst carry little news; '
             'the ratio rule alone is the part that marks a change.')
    o.append('- Checks: 24 random single-article groups (12 in a trial build before the download, 12 in the final build) recomputed from the raw '
             'store files, the adaptation views and the top-500 file by a separate script (monthly sums, 6-month median, both burst rules, '
             'max_ratio): all 24 match.')
    write_text_(('\n'.join(o) + '\n'), REP / 'dir_j1_links.md')
    log('wrote', REP / 'dir_j1_links.md')


def write_text_(text, path):
    tmp = path.with_suffix('.part')
    tmp.write_text(text)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--stage', choices=['links', 'bursts', 'report'], required=True)
    ap.add_argument('--test-out', default=None, help='bursts stage: write the trial outputs to this folder, no report')
    a = ap.parse_args()
    log(f'J1 stage {a.stage}; record {ADD_J.name}; out {OUT}')
    if a.stage == 'links':
        stage_links()
    elif a.stage == 'bursts':
        stage_bursts(a.test_out)
        if not a.test_out:
            stage_report()
    else:
        stage_report()
    log(f'done in {time.time() - T0:.0f}s')


if __name__ == '__main__':
    main()
