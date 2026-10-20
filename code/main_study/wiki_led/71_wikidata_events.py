#!/usr/bin/env python3
"""71. Dated events from Wikidata for the 7,747 works: the author's death, dated awards, and film or television adaptations
(data only: no model is fitted, nothing is related to loans).

Specification: paper/lit_search/Improvement_Methods_2026-10-20.md, Section 3, change 5 (data part); binding adjustments in
prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json (read-only).  Nothing here calls the Wikimedia REST pageviews API.

Source: Wikidata SPARQL (query.wikidata.org), one query at a time, batches of up to 300 items, at least 1.5 s between two queries,
the project user agent from code/config.py; every answer is cached under data/interim/wiki_led_cache/sparql/, so a rerun costs nothing.

Units
  book item     = works.item (7,510 distinct items for the 7,747 works).
  author item   = for works with an English author article, the author of that article (data/db/study2r/book_author_articles.parquet, so the events
                  belong to the same person as the author page views); for the other works, the first P50 author of the book item whose label contains a
                  family name of the Seattle creator string (the rule of study2r/03_pageviews.py, applied to data/db/study2r/wd_authors.parquet).
                  Only this one author is used even when a book has several.

Events (a date is usable only when its precision is a month or finer; year-only dates cannot be placed in a month and are counted, not used)
  death        P570 of the author item.  Several statements: deprecated ones are dropped, a preferred rank wins, then the most precise date, then the earliest.
  award        P166 with the point-in-time qualifier P585, on the book item and on the author item (undated P166 statements are counted, not used).
  adaptation   items linked to the book item by P144 (based on, queried again here to get P577 and P580 with their precision) or by P4969 (derivative work),
               plus the pairs of the existing data/db/wiki_led/adaptations.parquet (P144).  For each adaptation item the script keeps its P31 types, its class
               group (film, tv or other; by P31/P279* to film, television series, television program, season, episode or web series), its English Wikipedia title
               and all P577 and P580 dates.  Release date = the earliest P577 or P580 date with month precision or finer among the best-rank statements
               (a preferred rank wins over normal ones; deprecated statements, which is how Wikidata marks rescheduled dates, are dropped);
               only the first release is used, the other regional dates are not.  Only film and tv adaptations (the note's film, television series, miniseries) feed ad_rel.

Per work and origin month mi = year*12 + month - 1, 2016-03 to 2026-09 (events.parquet)
  died               1 when the author died in month t or t-1
  award              1 when a dated award of the book or of the author falls in t or t-1
  ad_rel             1 when the release date of a film or tv adaptation of the book falls in t-1, t or t+1
  ad_rel_public      left missing on purpose: whether that adaptation's English article already had views before the end of t (another job fills it from the
                     adaptation article views; the adaptation items and release months are in events_long.parquet, event == 'adaptation')
  months_since_event months from the latest event dated in t or earlier (death, award or film/tv release) to t, capped at 24 (24 when there is none)

Output: data/db/wiki_led/events.parquet (work_id, item, author_item, mi, died, award, ad_rel, ad_rel_public, months_since_event),
        data/db/wiki_led/events_long.parquet (one row per dated event or adaptation link), events_adaptation_dates.parquet (every P577 and P580 statement
        of the adaptation items with rank and precision), events_summary.json.
Run from handoff/code (full run, detached):   nice -n 10 bash ../jobs/bg.sh wl_events main_study/wiki_led/71_wikidata_events.py
Options: --test N  uses about N book items (evenly spaced, plus some with known adaptations) and their authors, writes *_test files.
"""
import sys, re, json, gzip, time, hashlib, os, datetime, collections, resource
import numpy as np, pandas as pd, requests
from _common import D, OUT, CACHE, log, T0, UA

S2R = D / 'db' / 'study2r'
SPARQL = 'https://query.wikidata.org/sparql'
GAP = 1.5                         # seconds between the starts of two queries
BATCH = 300
TEST = int(sys.argv[sys.argv.index('--test') + 1]) if '--test' in sys.argv else 0
SUF = '_test' if TEST else ''
SPQ = CACHE / 'sparql'
SPQ.mkdir(parents=True, exist_ok=True)
ORIGINS = np.arange(2016 * 12 + 2, 2026 * 12 + 9)          # 2016-03 to 2026-09
K = len(ORIGINS)
CAP = 24
SCREEN_ROOTS = {'Q11424': 'film', 'Q5398426': 'tv', 'Q15416': 'tv', 'Q3464665': 'tv', 'Q21191270': 'tv', 'Q526877': 'tv'}
ENT = 'http://www.wikidata.org/entity/'


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


def run_batches(template, items, label, size=BATCH):
    """Run the template over the items in batches; a batch that times out is split in halves.  Returns the list of bindings."""
    items = sorted(set(items))
    out = []
    todo = [items[i:i + size] for i in range(0, len(items), size)]
    done = 0
    while todo:
        b = todo.pop(0)
        q = template.format(vals=' '.join('wd:' + x for x in b))
        try:
            out += SP.run(q)
        except QueryTimeout:
            if len(b) == 1:
                raise RuntimeError(f'{label}: a single item times out: {b[0]}')
            h = len(b) // 2
            todo = [b[:h], b[h:]] + todo
            log(f'  {label}: timeout, splitting a batch of {len(b)}')
            continue
        done += len(b)
        if (done // size) % 5 == 0 or not todo:
            log(f'  {label}: {done}/{len(items)} items; network {SP.n_net}, cache {SP.n_cache}, backoffs {SP.n_backoff}')
    return out


Q_DEATH = """SELECT ?x ?d ?prec ?rank WHERE {{
  VALUES ?x {{ {vals} }}
  ?x p:P570 ?st . ?st psv:P570 ?v . ?v wikibase:timeValue ?d ; wikibase:timePrecision ?prec . ?st wikibase:rank ?rank .
}}"""
Q_AWARD = """SELECT ?x ?award ?d ?prec ?rank WHERE {{
  VALUES ?x {{ {vals} }}
  ?x p:P166 ?st . ?st ps:P166 ?award ; wikibase:rank ?rank .
  OPTIONAL {{ ?st pqv:P585 ?v . ?v wikibase:timeValue ?d ; wikibase:timePrecision ?prec . }}
}}"""
Q_LINKS = """SELECT ?b ?ad ?rel WHERE {{
  VALUES ?b {{ {vals} }}
  {{ ?ad wdt:P144 ?b . BIND("P144" AS ?rel) }} UNION {{ ?b wdt:P4969 ?ad . BIND("P4969" AS ?rel) }}
}}"""
Q_TYPES = """SELECT ?ad ?t WHERE {{ VALUES ?ad {{ {vals} }} ?ad wdt:P31 ?t . }}"""
Q_LABEL = """SELECT ?x ?l WHERE {{ VALUES ?x {{ {vals} }} ?x rdfs:label ?l . FILTER(LANG(?l) = "en") }}"""
Q_ROOTS = """SELECT DISTINCT ?ad ?root WHERE {{
  VALUES ?ad {{ {vals} }}
  VALUES ?root {{ %s }}
  ?ad wdt:P31/wdt:P279* ?root .
}}""" % ' '.join('wd:' + r for r in SCREEN_ROOTS)
Q_ART = """SELECT ?ad ?title ?lab WHERE {{
  VALUES ?ad {{ {vals} }}
  OPTIONAL {{ ?art schema:about ?ad ; schema:isPartOf <https://en.wikipedia.org/> ; schema:name ?title . }}
  OPTIONAL {{ ?ad rdfs:label ?lab . FILTER(LANG(?lab) = "en") }}
}}"""
# the joins on the time value sit inside each branch of the UNION: placed after it, the query service times out even for one item
Q_DATES = """SELECT ?ad ?prop ?d ?prec ?rank WHERE {{
  VALUES ?ad {{ {vals} }}
  {{ ?ad p:P577 ?st . ?st psv:P577 ?v . ?v wikibase:timeValue ?d ; wikibase:timePrecision ?prec . ?st wikibase:rank ?rank . BIND("P577" AS ?prop) }}
  UNION
  {{ ?ad p:P580 ?st . ?st psv:P580 ?v . ?v wikibase:timeValue ?d ; wikibase:timePrecision ?prec . ?st wikibase:rank ?rank . BIND("P580" AS ?prop) }}
}}"""


def g(b, k):
    return b[k]['value'] if k in b else None


def qid(u):
    return u.rsplit('/', 1)[-1] if u and u.startswith(ENT) else None


DATE_RE = re.compile(r'^(-?\d{1,6})-(\d{2})-(\d{2})T')


def parse_date(s, prec):
    """('YYYY-MM-DD' as given, year, month, mi_event or None); mi_event only for precision >= 10 (month or finer)."""
    m = DATE_RE.match(s) if isinstance(s, str) else None
    if not m:
        return None, None, None, None
    y, mo = int(m.group(1)), int(m.group(2))
    mi = y * 12 + mo - 1 if (prec is not None and prec >= 10 and y > 0 and 1 <= mo <= 12) else None
    return s[:10], y, mo, mi


def add_dates(df, dcol='d', pcol='prec'):
    """adds date, year, month, mi_event columns (mi_event only for month precision or finer)."""
    parsed = [parse_date(d, p) for d, p in zip(df[dcol], df[pcol])]
    df['date'] = [x[0] for x in parsed]
    df['year'] = pd.to_numeric(pd.Series([x[1] for x in parsed], index=df.index), errors='coerce')
    df['month'] = pd.to_numeric(pd.Series([x[2] for x in parsed], index=df.index), errors='coerce')
    df['mi_event'] = pd.to_numeric(pd.Series([x[3] for x in parsed], index=df.index), errors='coerce')
    return df


def frame(rows, cols):
    return pd.DataFrame(rows, columns=cols)


def rank_of(u):
    return (u or '').rsplit('#', 1)[-1].replace('Rank', '').lower()          # preferred / normal / deprecated


# ---------------------------------------------------------------- units: works, book items, author items
W = pd.read_parquet(S2R / 'works.parquet', columns=['work_id', 'title', 'creator', 'item', 'article', 'author_article'])
AUW = pd.read_parquet(S2R / 'wd_authors.parquet')
AUW = AUW[AUW.author_item != '']
BAA = pd.read_parquet(S2R / 'book_author_articles.parquet')


def norm(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower().replace('&', ' and ')
    s = re.sub(r'[\W_]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def parse_creators(c):
    """Family names of every creator in a Seattle creator string (copied from study2r/common.py, which builds an HTTP client on import)."""
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


cands = collections.defaultdict(list)
for it_, a_, l_ in zip(AUW['item'], AUW.author_item, AUW.author_label):
    cands[it_].append((a_, l_))


def pick_author(item, creator):
    fam = parse_creators(creator)
    for a, lab in cands.get(item, []):
        if any(f in norm(lab).split() for f in fam):
            return a
    return None


baa = BAA.drop_duplicates('item').set_index('item').author_item
rule_author = [pick_author(i, c) for i, c in zip(W['item'], W.creator)]
W['author_item'] = np.where(W.author_article.notna(), W['item'].map(baa), pd.Series(rule_author, index=W.index))
W['author_item'] = W.author_item.where(W.author_item.notna(), None)
assert W.loc[W.author_article.notna(), 'author_item'].notna().all(), 'a work with an author article has no author item in book_author_articles'
agree = float((pd.Series(rule_author, index=W.index)[W.author_article.notna()] == W.loc[W.author_article.notna(), 'author_item']).mean())
log(f'works {len(W)}; with an author item {int(W.author_item.notna().sum())} (with an author article {int(W.author_article.notna().sum())}, '
    f'from the family-name rule only {int((W.author_article.isna() & W.author_item.notna()).sum())}); the rule alone agrees with the Study 2R author on {agree:.4f} of the works with an article')

ADEX = pd.read_parquet(D / 'db' / 'wiki_led' / 'adaptations.parquet')
ADEX = ADEX[ADEX.book.isin(set(W['item']))]
if TEST:
    items_all = sorted(W['item'].unique())
    step = max(1, len(items_all) // max(1, int(TEST * 0.6)))
    samp = set(items_all[step // 2::step][:int(TEST * 0.6)])
    all_set = set(items_all)
    withad = [i for i in sorted(ADEX.book.unique()) if i in all_set and i not in samp]
    samp |= set(withad[:TEST - len(samp)])
    W = W[W['item'].isin(samp)].reset_index(drop=True)
    ADEX = ADEX[ADEX.book.isin(samp)]
items = sorted(W['item'].unique())
author_items = sorted(W.author_item.dropna().unique())
log(f'book items {len(items)}, author items {len(author_items)}, works {len(W)}')
fetched_at = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

# ---------------------------------------------------------------- queries
log('deaths of the author items')
rows = run_batches(Q_DEATH, author_items, 'deaths')
D0 = frame([dict(x=qid(g(b, 'x')), d=g(b, 'd'), prec=int(g(b, 'prec')), rank=rank_of(g(b, 'rank'))) for b in rows], ['x', 'd', 'prec', 'rank'])
log('awards of the author items')
rows = run_batches(Q_AWARD, author_items, 'author awards')
AA = frame([dict(x=qid(g(b, 'x')), award=qid(g(b, 'award')), d=g(b, 'd'), prec=int(g(b, 'prec')) if g(b, 'prec') else np.nan, rank=rank_of(g(b, 'rank')))
            for b in rows], ['x', 'award', 'd', 'prec', 'rank'])
AA['subject_kind'] = 'author'
log('awards of the book items')
rows = run_batches(Q_AWARD, items, 'book awards')
BA = frame([dict(x=qid(g(b, 'x')), award=qid(g(b, 'award')), d=g(b, 'd'), prec=int(g(b, 'prec')) if g(b, 'prec') else np.nan, rank=rank_of(g(b, 'rank')))
            for b in rows], ['x', 'award', 'd', 'prec', 'rank'])
BA['subject_kind'] = 'book'
log('adaptation links (P144, P4969)')
rows = run_batches(Q_LINKS, items, 'links')
LK = frame([dict(book=qid(g(b, 'b')), ad=qid(g(b, 'ad')), rel=g(b, 'rel')) for b in rows], ['book', 'ad', 'rel'])
LK = LK[LK.ad.notna()]
lk = LK.groupby(['book', 'ad']).rel.apply(lambda s: '+'.join(sorted(set(s)))).rename('wd_property').reset_index()
ex = ADEX[['book', 'adapt']].drop_duplicates().rename(columns={'adapt': 'ad'})
ex['in_existing_file'] = True
lk['found_now'] = True
AD = lk.merge(ex, on=['book', 'ad'], how='outer')
AD['found_now'] = AD.found_now.fillna(False).astype(bool)
AD['in_existing_file'] = AD.in_existing_file.fillna(False).astype(bool)
AD['wd_property'] = AD.wd_property.fillna('existing file only')
link_counts = dict(pairs=int(len(AD)), found_now=int(AD.found_now.sum()), in_existing_file=int(AD.in_existing_file.sum()),
                   both=int((AD.found_now & AD.in_existing_file).sum()), existing_only=int((~AD.found_now & AD.in_existing_file).sum()),
                   now_only=int((AD.found_now & ~AD.in_existing_file).sum()),
                   p144_now=int(AD.wd_property.str.contains('P144').sum()), p4969_now=int(AD.wd_property.str.contains('P4969').sum()),
                   p4969_only=int((AD.wd_property == 'P4969').sum()),
                   books_with_adaptation=int(AD.book.nunique()), adaptation_items=int(AD.ad.nunique()))
log('links', link_counts)
ads = sorted(AD.ad.unique())
log('adaptation items: types, class groups, English titles, dates')
TY = frame([dict(ad=qid(g(b, 'ad')), t=qid(g(b, 't'))) for b in run_batches(Q_TYPES, ads, 'types')], ['ad', 't']).dropna()
RT = frame([dict(ad=qid(g(b, 'ad')), root=qid(g(b, 'root'))) for b in run_batches(Q_ROOTS, ads, 'class groups')], ['ad', 'root'])
AR = frame([dict(ad=qid(g(b, 'ad')), title=g(b, 'title'), lab=g(b, 'lab')) for b in run_batches(Q_ART, ads, 'titles')], ['ad', 'title', 'lab'])
DT = frame([dict(ad=qid(g(b, 'ad')), prop=g(b, 'prop'), d=g(b, 'd'), prec=int(g(b, 'prec')), rank=rank_of(g(b, 'rank')))
            for b in run_batches(Q_DATES, ads, 'dates')], ['ad', 'prop', 'd', 'prec', 'rank'])
log('queries done', f'network {SP.n_net}, cache {SP.n_cache}, backoffs {SP.n_backoff}, query seconds {SP.net_seconds:.0f}')

# ---------------------------------------------------------------- adaptation table (one row per book item and adaptation item)
types = TY.groupby('ad').t.apply(lambda s: '|'.join(sorted(set(s)))).rename('types')
grp = RT.groupby('ad').root.apply(lambda s: set(s)) if len(RT) else pd.Series(dtype=object)


def group_of(a):
    r = grp.get(a, set())
    if 'Q11424' in r:
        return 'film'
    return 'tv' if r else 'other'


art = AR.dropna(subset=['title']).drop_duplicates('ad').set_index('ad').title
lab = AR.dropna(subset=['lab']).drop_duplicates('ad').set_index('ad').lab
DT = add_dates(DT)
# every P577 and P580 statement of the adaptation items, any rank and precision, for whoever wants another release rule
DT.rename(columns={'prec': 'precision'}).drop(columns=['d']).to_parquet(OUT / f'events_adaptation_dates{SUF}.parquet', index=False)
n_date_statements = dict(total=int(len(DT)), deprecated=int((DT['rank'] == 'deprecated').sum()), month_or_finer_not_deprecated=int((DT.mi_event.notna() & (DT['rank'] != 'deprecated')).sum()))
DT = DT[DT['rank'] != 'deprecated'].copy()              # superseded (rescheduled) dates are marked deprecated on Wikidata and drop out here
# best-rank rule of Wikidata's truthy statements: within an adaptation and property, preferred statements win over normal ones
has_pref = DT.groupby(['ad', 'prop'])['rank'].transform(lambda x: (x == 'preferred').any())
DT['is_best'] = np.where(has_pref, DT['rank'] == 'preferred', True)
ok = DT[DT.mi_event.notna()].sort_values(['ad', 'mi_event', 'date', 'prop'])
ok_best = ok[ok.is_best]
# the release date is the earliest best-rank date at month precision or finer; when the best-rank dates have only a year, the earliest date of any rank
first = pd.concat([ok_best.drop_duplicates('ad'), ok[~ok.ad.isin(ok_best.ad)].drop_duplicates('ad')]).set_index('ad')
ndates = DT.groupby('ad').size()
ndates_ok = ok.groupby('ad').size()
A = pd.DataFrame({'ad': ads})
A['types'] = A.ad.map(types).fillna('')
A['type_group'] = A.ad.map(group_of)
A['en_title'] = A.ad.map(art)
A['label'] = A.ad.map(lab)
A['release_date'] = A.ad.map(first.date)
A['release_prop'] = A.ad.map(first.prop)
A['release_rank'] = A.ad.map(first['rank'])
A['release_precision'] = A.ad.map(first.prec).astype('float')
A['release_mi'] = A.ad.map(first.mi_event)
earliest_any = DT[DT.year.notna()].sort_values(['ad', 'year', 'month']).drop_duplicates('ad').set_index('ad')
A['release_year'] = np.where(A.release_mi.notna(), A.ad.map(first.year), A.ad.map(earliest_any.year))      # the earliest year of any precision when no month is known
A['n_dates'] = A.ad.map(ndates).fillna(0).astype(int)
A['n_dates_month_or_finer'] = A.ad.map(ndates_ok).fillna(0).astype(int)
AD = AD.merge(A, on='ad', how='left')
log('adaptation table', AD.shape, AD.type_group.value_counts().to_dict())

# ---------------------------------------------------------------- death and award events
D0 = D0[D0['rank'] != 'deprecated'].copy()
D0 = add_dates(D0)
D0['pref'] = (D0['rank'] == 'preferred').astype(int)
usable = D0[D0.mi_event.notna()].copy()
if len(usable):
    pref_any = usable.groupby('x').pref.transform('max')
    usable = usable[usable.pref == pref_any].sort_values(['x', 'prec', 'mi_event'], ascending=[True, False, True])
conflict = int((usable.groupby('x').mi_event.nunique() > 1).sum()) if len(usable) else 0
death = usable.drop_duplicates('x').set_index('x')
year_only_death = sorted(set(D0.x) - set(death.index))
log(f'author deaths: {len(death)} usable (month or finer), {len(year_only_death)} authors with a death date at year precision only, {conflict} with conflicting dates')

AW = pd.concat([AA, BA], ignore_index=True)
AW = AW[AW['rank'] != 'deprecated'].copy()
AW = AW[AW.award.notna()].copy()
AW['dated'] = AW.d.notna()
AW = add_dates(AW)
award_counts = dict(statements=int(len(AW)), undated=int((~AW.dated).sum()), dated=int(AW.dated.sum()),
                    dated_month_or_finer=int(AW.mi_event.notna().sum()), dated_year_only=int((AW.dated & AW.mi_event.isna()).sum()))
log('awards', award_counts)
AWu = AW[AW.mi_event.notna()].drop_duplicates(['x', 'award', 'date', 'subject_kind'])
AWy = AW[AW.dated & AW.mi_event.isna() & AW.year.notna()].drop_duplicates(['x', 'award', 'date', 'subject_kind'])
# English labels of the awards and of the most common adaptation types, so the long file and the report can name them
type_top = TY.t.value_counts().head(25).index.tolist()
labmap = {qid(g(b, 'x')): g(b, 'l') for b in run_batches(Q_LABEL, sorted(set(AWu.award) | set(AWy.award) | set(type_top)), 'labels')}

# ---------------------------------------------------------------- long file
long_rows = []
for a, r in death.iterrows():
    long_rows.append(dict(event='death', subject=a, subject_kind='author', detail=None, date=r.date, year=int(r.year), precision=int(r.prec), mi_event=int(r.mi_event)))
yo = D0[D0.x.isin(year_only_death) & D0.year.notna()].sort_values(['x', 'year']).drop_duplicates('x')
for r in yo.itertuples():
    long_rows.append(dict(event='death', subject=r.x, subject_kind='author', detail=None, date=r.date, year=int(r.year), precision=int(r.prec), mi_event=np.nan))
for r in AWu.itertuples():
    long_rows.append(dict(event='award', subject=r.x, subject_kind=r.subject_kind, detail=r.award, label=labmap.get(r.award), date=r.date, year=int(r.year), precision=int(r.prec),
                          mi_event=int(r.mi_event)))
for r in AWy.itertuples():
    long_rows.append(dict(event='award', subject=r.x, subject_kind=r.subject_kind, detail=r.award, label=labmap.get(r.award), date=r.date, year=int(r.year), precision=int(r.prec),
                          mi_event=np.nan))
LONG = frame(long_rows, ['event', 'subject', 'subject_kind', 'detail', 'label', 'date', 'year', 'precision', 'mi_event'])
adl = AD.rename(columns={'book': 'subject', 'ad': 'detail'}).assign(event='adaptation', subject_kind='book', date=lambda x: x.release_date,
                                                                    year=lambda x: x.release_year, precision=lambda x: x.release_precision,
                                                                    mi_event=lambda x: x.release_mi)
LONG = pd.concat([LONG, adl[['event', 'subject', 'subject_kind', 'detail', 'date', 'year', 'precision', 'mi_event', 'wd_property', 'in_existing_file', 'types',
                             'type_group', 'en_title', 'label', 'release_prop', 'release_rank', 'n_dates', 'n_dates_month_or_finer']]], ignore_index=True)
LONG['mi_event'] = LONG.mi_event.astype('float64')
LONG.to_parquet(OUT / f'events_long{SUF}.parquet', index=False)

# ---------------------------------------------------------------- per work and origin month
death_mi = W.author_item.map(death.mi_event)
by_subject = collections.defaultdict(list)                       # (kind, item) -> list of (event kind, month)
for r in AWu.itertuples():
    by_subject[(r.subject_kind, r.x)].append(int(r.mi_event))
scr = AD[AD.type_group.isin(['film', 'tv']) & AD.release_mi.notna()]
ad_by_book = scr.groupby('book').release_mi.apply(lambda s: sorted(set(int(v) for v in s))).to_dict()
n = len(W)
died = np.zeros((n, K), np.int8)
award = np.zeros((n, K), np.int8)
adrel = np.zeros((n, K), np.int8)
since = np.full((n, K), CAP, np.int8)
o0 = int(ORIGINS[0])


def mark(arr, i, months, offsets):
    for m in months:
        for o in offsets:
            j = m + o - o0
            if 0 <= j < K:
                arr[i, j] = 1


for i, (item, ai, dm) in enumerate(zip(W['item'], W.author_item, death_mi)):
    d_list = [] if pd.isna(dm) else [int(dm)]
    a_list = by_subject.get(('book', item), []) + (by_subject.get(('author', ai), []) if isinstance(ai, str) else [])
    r_list = ad_by_book.get(item, [])
    mark(died, i, d_list, (0, 1))
    mark(award, i, a_list, (0, 1))
    mark(adrel, i, r_list, (-1, 0, 1))
    ev = np.array(sorted(set(d_list + a_list + r_list)), dtype=np.int64)
    if len(ev):
        pos = np.searchsorted(ev, ORIGINS, side='right') - 1                # latest event month <= t
        has = pos >= 0
        s = np.where(has, ORIGINS - ev[np.maximum(pos, 0)], CAP)
        since[i] = np.minimum(s, CAP).astype(np.int8)
E = pd.DataFrame({'work_id': np.repeat(W.work_id.to_numpy().astype(np.int64), K), 'item': np.repeat(W['item'].to_numpy(dtype=object), K),
                  'author_item': np.repeat(W.author_item.to_numpy(dtype=object), K), 'mi': np.tile(ORIGINS.astype(np.int32), n),
                  'died': died.reshape(-1), 'award': award.reshape(-1), 'ad_rel': adrel.reshape(-1)})
E['ad_rel_public'] = np.float32(np.nan)
E['months_since_event'] = since.reshape(-1)
E.to_parquet(OUT / f'events{SUF}.parquet', index=False)
log('events table', E.shape, {c: float(E[c].mean().round(5)) for c in ('died', 'award', 'ad_rel')})

# ---------------------------------------------------------------- summary
def by_year(mask_df, col='mi_event'):
    y = (mask_df[col].dropna() // 12).astype(int)
    return {int(k): int(v) for k, v in y.value_counts().sort_index().items()}


L = LONG
deaths_u = L[(L.event == 'death') & L.mi_event.notna()]
awards_u = L[(L.event == 'award') & L.mi_event.notna()]
ads_u = L[(L.event == 'adaptation') & L.mi_event.notna()]
summ = dict(test=TEST, fetched_at=fetched_at, works=int(len(W)), book_items=len(items), author_items=len(author_items),
            works_with_author_item=int(W.author_item.notna().sum()), author_mapping_agreement=agree,
            deaths=dict(authors_with_usable_date=int(len(death)), year_only_only=len(year_only_death), conflicting=conflict,
                        by_year_distinct_authors=by_year(deaths_u)),
            awards=award_counts | dict(distinct_dated_month_or_finer=int(len(AWu)), distinct_dated_year_only=int(len(AWy)),
                                       by_year_book=by_year(awards_u[(awards_u.subject_kind == 'book') & awards_u.mi_event.notna()]),
                                       by_year_author=by_year(awards_u[(awards_u.subject_kind == 'author') & awards_u.mi_event.notna()]),
                                       year_only_by_year_book={int(k): int(v) for k, v in AWy[AWy.subject_kind == 'book'].year.value_counts().sort_index().items()},
                                       year_only_by_year_author={int(k): int(v) for k, v in AWy[AWy.subject_kind == 'author'].year.value_counts().sort_index().items()},
                                       top_awards_month_precision={f'{labmap.get(k, k)} ({k})': int(v) for k, v in AWu.award.value_counts().head(12).items()},
                                       top_awards_year_only={f'{labmap.get(k, k)} ({k})': int(v) for k, v in AWy.award.value_counts().head(12).items()}),
            adaptations=link_counts | dict(date_statements=n_date_statements, by_type_group=AD.drop_duplicates('ad').type_group.value_counts().to_dict(),
                                           pairs_by_type_group=AD.type_group.value_counts().to_dict(),
                                           with_english_article=int(AD.drop_duplicates('ad').en_title.notna().sum()),
                                           release_month_or_finer=int(AD.drop_duplicates('ad').release_mi.notna().sum()),
                                           year_only_or_no_date=int(AD.drop_duplicates('ad').release_mi.isna().sum()),
                                           release_by_year_film=by_year(ads_u[ads_u.type_group == 'film']),
                                           release_by_year_tv=by_year(ads_u[ads_u.type_group == 'tv']),
                                           release_by_year_other=by_year(ads_u[ads_u.type_group == 'other']),
                                           top_types={f'{labmap.get(k, k)} ({k})': int(v) for k, v in TY.t.value_counts().head(25).items()}),
            table_means={c: float(E[c].mean()) for c in ('died', 'award', 'ad_rel')},
            months_since_quantiles={str(q): float(E.months_since_event.quantile(q)) for q in (0.05, 0.25, 0.5, 0.75, 0.95)},
            months_since_share_capped=float((E.months_since_event == CAP).mean()),
            queries=dict(network=SP.n_net, cache=SP.n_cache, backoffs=SP.n_backoff, query_seconds=round(SP.net_seconds), gap_s=GAP, batch=BATCH),
            peak_memory_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6), runtime_s=round(time.time() - T0))
(OUT / f'events_summary{SUF}.json').write_text(json.dumps(summ, indent=1, default=str))
log('wrote', OUT / f'events{SUF}.parquet', E.shape, f'runtime {time.time() - T0:.0f}s')
