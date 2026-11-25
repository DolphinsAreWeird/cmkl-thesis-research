# n12. Addendum n, part 1, data for AD (film and TV pages) and LK (linked pages): the Wikidata items and their English articles.
# DATA ONLY: no model is fitted and nothing is related to loans; the summary has counts only.
# Settings: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json (read-only; SHA-256 asserted), sections
#   part_1_signals_in_hand.AD_film_and_TV_pages and .LK_linked_pages.  Choices the record leaves open, decided 2026-11-25 16:43 +07:00
#   (09:43 UTC) before this was run, also in data/db/wiki_led/n_more_signals/notes_ad_lk.md:
#   C1 Units: book item = book_item of l_books_in_time/matches.parquet; an item's pages go to every work with that item (j, J1).
#   C2 Requests: wbgetentities with m01's exact parameters (props=claims|labels, languages=en, format=json, maxlag=5), batches of 10, gap
#      0.34 s, the Http class of ../_common.py (cache, back-off), items fetched in m01's order (book items, followed-by items, adaptation
#      items, language items, class walk by depth) so m01's batches come from the cache; then linked items and their classes.  English
#      titles: wbgetentities props=sitelinks, sitefilter=enwiki, batches of 10, same gap.  Only the properties used are kept in memory.
#   C3 AD items exactly as m01: P4969 of the book item (every statement) plus data/db/wiki_led/adaptations.parquet pairs; class walk
#      P31 -> P279 (every statement, at most 12 levels); film when a class reaches Q11424, TV when another SCREEN_ROOT; 'other' dropped.
#      Check (assert): m01's film and TV counts (1,032 and 302) and per book item the earliest release equal to seg_works.adapt_mi.
#   C4 Release month: m01's release_mi; an item without a usable date never counts as released.
#   C5 Page = enwiki sitelink title with underscores; an item without an English article gives no page (counted).
#   C6 LK links from best-rank (truthy) statements (non-deprecated statements of the highest rank present; item values only): P921 or
#      P180 -> person if the item's category is person, event_period if event, else subject; P2408 -> event_period; P840 -> place;
#      P674 -> character.  Addendum j's adaptation and series link types are left out (record).
#   C7 Category (J4 as changed on 22 Oct 09:22): best-rank P31 classes and best-rank P279 superclasses walked until no new class (guard 40
#      levels); person (Q5), else work (Q17537576), else event (Q1190554), else place (Q2221906), else concept_other; is_period (Q11514315).
#   C8 Left out of LK for a work: (a) the book's own item; (b) every non-deprecated P50 of the book item; (c) adaptations: the book's C3
#      adaptation items (every class) and linked items with a non-deprecated P144 to the book item; (d) series: the book's P179 series,
#      linked items with a non-deprecated P179 to one of them, and the book's P155 and P156 items; (e) pages equal to the work's own book
#      or author article of addendum l (work_articles.parquet); (f) a page that is also one of the work's AD pages.
#   C9 One LK row per (work, page): kind = first link type in j's order (subject, event_period, person, place, character); props lists
#      every linking property; category and is_period of the item.
#   C10 Wikidata as read on 25 Nov 2026, not as at each origin (record, known_limits).
# Outputs (data/db/wiki_led/n_more_signals/): pages_AD.parquet (work_id, book_item, item, page, kind film|tv, release_mi),
#   pages_LK.parquet (work_id, book_item, item, page, kind, props, category, is_period), n12_summary.json.
#   Run from handoff/:  bash jobs/bg.sh n12_wd main_study/wiki_led/n_more_signals/n12_wikidata_pages.py
import sys, os, re, json, time, hashlib, pathlib
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _common import Http, maxlag_check, D as DATA_DIR      # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
WL = DATA / 'db' / 'wiki_led'
L = WL / 'l_books_in_time'
MT = WL / 'm_theme_pages'
OUT = WL / 'n_more_signals'
OUT.mkdir(parents=True, exist_ok=True)
WD_API = 'https://www.wikidata.org/w/api.php'
H = Http({'wd': 0.34})
SCREEN_ROOTS = {'Q11424': 'film', 'Q5398426': 'tv', 'Q15416': 'tv', 'Q3464665': 'tv', 'Q21191270': 'tv', 'Q526877': 'tv'}  # m01 / 71
J4_ROOTS = {'Q5': 'person', 'Q1190554': 'event', 'Q2221906': 'place', 'Q17537576': 'work'}
CAT_ORDER = ('person', 'work', 'event', 'place')
PERIOD = 'Q11514315'
LINK_ORDER = ['subject', 'event_period', 'person', 'place', 'character']
KEEP_PROPS = {'P4969', 'P921', 'P180', 'P2408', 'P840', 'P674', 'P179', 'P155', 'P156', 'P50', 'P31', 'P279', 'P577', 'P580', 'P144', 'P407'}
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def mi_of(y, m):
    return int(y) * 12 + int(m) - 1


# ---------------------------------------------------------------- Wikidata (m01's fetch, with the kept properties only)
ENT = {}


def prune(e):
    if not e:
        return {}
    cl = {p: [{'mainsnak': s.get('mainsnak'), 'rank': s.get('rank')} for s in v] for p, v in (e.get('claims') or {}).items() if p in KEEP_PROPS}
    return {'claims': cl, 'labels': {'en': (e.get('labels') or {}).get('en')} if (e.get('labels') or {}).get('en') else {}}


def fetch(qids, what, redirects=False):
    """m01's fetch.  redirects=True (items new here only): an id answered under its redirect target is read from that answer."""
    todo = sorted({q for q in qids if isinstance(q, str) and q.startswith('Q') and q not in ENT})
    for i in range(0, len(todo), 10):
        batch = todo[i:i + 10]
        st, text = H.get('wd', WD_API, dict(action='wbgetentities', ids='|'.join(batch), props='claims|labels', languages='en',
                                            format='json', maxlag=5), check=maxlag_check)
        if st != 200:
            raise RuntimeError(f'Wikidata status {st}')
        ents = json.loads(text).get('entities', {})
        red = {}
        if redirects:
            for e in ents.values():
                fr = (e.get('redirects') or {}).get('from')
                if fr:
                    red[fr] = e
        for q in batch:
            e = ents.get(q) or red.get(q) or {}
            ENT[q] = prune(e) if 'missing' not in e else {}
        if (i // 10) % 100 == 0:
            log(f'  {what}: {i + len(batch):,} of {len(todo):,} (network {H.n_net}, cache {H.n_cache})')
    log(f'{what}: {len(todo):,} items fetched or read (network {H.n_net}, cache {H.n_cache}, back-offs {H.n_backoff})')


def stmts(q, prop):
    return (ENT.get(q) or {}).get('claims', {}).get(prop, [])


def val_item(s):
    try:
        return s['mainsnak']['datavalue']['value']['id']
    except (KeyError, TypeError):
        return None


def val_time(s):
    try:
        v = s['mainsnak']['datavalue']['value']
    except (KeyError, TypeError):
        return None
    return parse_time(v)


def parse_time(v):
    m = re.match(r'^([+-])(\d+)-(\d\d)-(\d\d)', v.get('time', ''))
    if not m or m.group(1) == '-':
        return None
    p = int(v.get('precision', 0))
    if p < 9:
        return None
    return int(m.group(2)), (int(m.group(3)) if p >= 10 and int(m.group(3)) > 0 else None), p


def nondep(q, prop):
    return {v for v in (val_item(s) for s in stmts(q, prop) if s.get('rank') != 'deprecated') if v}


def best(q, prop):
    """Truthy values (C6): the non-deprecated statements of the highest rank present, item values only."""
    ss = [s for s in stmts(q, prop) if s.get('rank') != 'deprecated']
    pref = [s for s in ss if s.get('rank') == 'preferred']
    return sorted({v for v in (val_item(s) for s in (pref if pref else ss)) if v})


# ---------------------------------------------------------------- m01's sequence (C2, C3)
M = pd.read_parquet(L / 'matches.parquet', columns=['work_id', 'creator_key', 'book_item'])
items = sorted(M.book_item.dropna().unique())
log('main-set works', len(M), '| with a book item', int(M.book_item.notna().sum()), '| distinct items', len(items))
fetch(items, 'book items')
nxt = {q: [val_item(s) for s in stmts(q, 'P156') if s.get('rank') != 'deprecated' and val_item(s)] for q in items}
ADX = pd.read_parquet(WL / 'adaptations.parquet', columns=['adapt', 'book'])
ad_links = {q: set(v for v in (val_item(s) for s in stmts(q, 'P4969')) if v) for q in items}
for a, b in ADX[ADX.book.isin(set(items))][['adapt', 'book']].itertuples(index=False):
    ad_links[b].add(a)
langs = {q: [val_item(s) for s in stmts(q, 'P407') if s.get('rank') != 'deprecated' and val_item(s)] for q in items}
fetch({x for v in nxt.values() for x in v}, 'followed-by items')
fetch({x for v in ad_links.values() for x in v}, 'adaptation items')
fetch({x for v in langs.values() for x in v}, 'language items')
ad_items = sorted({x for v in ad_links.values() for x in v})
p31 = {a: {val_item(s) for s in stmts(a, 'P31') if val_item(s)} for a in ad_items}
classes = set().union(*p31.values()) if p31 else set()
parents, frontier = {}, set(classes)
for depth in range(12):
    fetch(frontier, f'classes, depth {depth}')
    new = set()
    for c in frontier:
        parents[c] = {val_item(s) for s in stmts(c, 'P279') if val_item(s)}
        new |= parents[c]
    frontier = {c for c in new if c not in parents}
    if not frontier:
        break
log('m01 class walk: classes', len(parents), '| unfinished frontier', len(frontier))


def roots_of(cls_set):
    seen, stack, r = set(), list(cls_set), set()
    while stack:
        c = stack.pop()
        if c in seen:
            continue
        seen.add(c)
        if c in SCREEN_ROOTS:
            r.add(c)
        stack.extend(parents.get(c, ()))
    return r


def group_of(a):
    r = roots_of(p31.get(a, set()))
    return 'film' if 'Q11424' in r else ('tv' if r else 'other')


def release_mi(a):
    """m01 (71's rule): earliest non-deprecated best-rank P577/P580 at month precision or finer; year precision only: January next year."""
    month_dates, years = [], []
    for prop in ('P577', 'P580'):
        ss = [s for s in stmts(a, prop) if s.get('rank') != 'deprecated']
        pref = [s for s in ss if s.get('rank') == 'preferred']
        bst = pref if pref else ss
        for s in bst:
            t = val_time(s)
            if t and t[1] is not None:
                month_dates.append(mi_of(t[0], t[1]))
        for s in ss:
            t = val_time(s)
            if t:
                years.append(t[0])
    if month_dates:
        return min(month_dates)
    return mi_of(min(years) + 1, 1) if years else np.nan


grp = {a: group_of(a) for a in ad_items}
rel = {a: release_mi(a) for a in ad_items}
gcount = pd.Series(grp).value_counts().to_dict()
log('adaptation items', len(ad_items), gcount)
assert gcount.get('film', 0) == 1032 and gcount.get('tv', 0) == 302, f'film/TV counts differ from m01: {gcount}'
SW = pd.read_parquet(MT / 'seg_works.parquet', columns=['book_item', 'adapt_mi', 'n_screen_adaptations']).dropna(subset=['book_item']).drop_duplicates('book_item').set_index('book_item')
n_chk = 0
for q in items:
    ads = [a for a in ad_links[q] if grp[a] in ('film', 'tv')]
    r = [rel[a] for a in ads if np.isfinite(rel[a])]
    mine = min(r) if r else np.nan
    ref = SW.adapt_mi.get(q, np.nan)
    assert (np.isnan(mine) and np.isnan(ref)) or mine == ref, f'adapt_mi differs from m01 for {q}: {mine} vs {ref}'
    assert len(ads) == SW.n_screen_adaptations.get(q), f'number of screen adaptations differs from m01 for {q}'
    n_chk += 1
log('check: m01 film/TV counts and earliest release per book item reproduced on', n_chk, 'items')

# ---------------------------------------------------------------- linked items (C6 to C8)
PROPS = ('P921', 'P180', 'P2408', 'P840', 'P674')
raw = [(q, p, x) for q in items for p in PROPS for x in best(q, p)]
linked = sorted({x for _, _, x in raw})
log('best-rank link statements', len(raw), '| distinct linked items', len(linked))
fetch(linked, 'linked items', redirects=True)
types = {x: best(x, 'P31') for x in linked}
parents2, frontier = {}, set().union(*types.values()) if types else set()
n_cls0 = len(frontier)
depth = 0
for depth in range(40):
    fetch(frontier, f'J4 classes, depth {depth}', redirects=True)
    new = set()
    for c in frontier:
        parents2[c] = set(best(c, 'P279'))
        new |= parents2[c]
    frontier = {c for c in new if c not in parents2}
    if not frontier:
        break
log('J4 class walk: P31 classes', n_cls0, '| classes in the walk', len(parents2), '| levels', depth + 1, '| unfinished frontier', len(frontier))
ROOTSET = set(J4_ROOTS) | {PERIOD}
memo = {}


def j4_roots(cls_list):
    seen, stack, r = set(), list(cls_list), set()
    while stack:
        c = stack.pop()
        if c in seen:
            continue
        seen.add(c)
        if c in ROOTSET:
            r.add(c)
        stack.extend(parents2.get(c, ()))
    return r


cat, isper, nroots = {}, {}, {}
for x in linked:
    rs = j4_roots(types.get(x, []))
    found = [J4_ROOTS[r] for r in J4_ROOTS if r in rs]
    nroots[x] = len(found)
    isper[x] = PERIOD in rs
    cat[x] = next((c for c in CAT_ORDER if c in found), 'concept_other')


def ltype(p, x):
    if p in ('P921', 'P180'):
        return {'person': 'person', 'event': 'event_period'}.get(cat[x], 'subject')
    return {'P2408': 'event_period', 'P840': 'place', 'P674': 'character'}[p]


R = pd.DataFrame(raw, columns=['book_item', 'p', 'item'])
R['link_type'] = [ltype(p, x) for p, x in zip(R.p, R.item)]
excl = {}
keep = []
for q, x in zip(R.book_item, R.item):
    series = nondep(q, 'P179')
    if x == q:
        why = 'own_item'
    elif x in nondep(q, 'P50'):
        why = 'author'
    elif x in ad_links[q] or q in nondep(x, 'P144'):
        why = 'adaptation'
    elif x in series or (series & nondep(x, 'P179')) or x in nondep(q, 'P155') or x in nondep(q, 'P156'):
        why = 'series'
    else:
        why = ''
    keep.append(why == '')
    if why:
        excl[why] = excl.get(why, 0) + 1
R = R[np.array(keep)]
log('statements left out by item (C8 a-d):', excl, '| kept', len(R))

# ---------------------------------------------------------------- English titles (C5)
SL = {}


def sitelinks(qids, what):
    todo = sorted({q for q in qids if isinstance(q, str) and q.startswith('Q') and q not in SL})
    for i in range(0, len(todo), 10):
        batch = todo[i:i + 10]
        st, text = H.get('wd', WD_API, dict(action='wbgetentities', ids='|'.join(batch), props='sitelinks', sitefilter='enwiki',
                                            format='json', maxlag=5), check=maxlag_check)
        if st != 200:
            raise RuntimeError(f'Wikidata status {st}')
        ents = json.loads(text).get('entities', {})
        red = {(e.get('redirects') or {}).get('from'): e for e in ents.values() if (e.get('redirects') or {}).get('from')}
        for q in batch:
            e = ents.get(q) or red.get(q) or {}
            t = ((e.get('sitelinks') or {}).get('enwiki') or {}).get('title')
            SL[q] = t.replace(' ', '_') if t else None
        if (i // 10) % 100 == 0:
            log(f'  {what}: {i + len(batch):,} of {len(todo):,} (network {H.n_net}, cache {H.n_cache})')
    log(f'{what}: {len(todo):,} items (network {H.n_net}, cache {H.n_cache}, back-offs {H.n_backoff})')


screen = sorted(a for a in ad_items if grp[a] in ('film', 'tv'))
sitelinks(screen, 'English titles, film and TV items')
sitelinks(sorted(set(R.item)), 'English titles, linked items')

WK = M.dropna(subset=['book_item'])[['work_id', 'book_item']]
WA = pd.read_parquet(L / 'work_articles.parquet')
own_titles = {w: {str(t).replace(' ', '_') for t in (b, a) if isinstance(t, str)} for w, b, a in zip(WA.work_id, WA.book_canonical, WA.author_canonical)}

# AD pages per work
ad_rows = [(q, a, grp[a], rel[a], SL.get(a)) for q in items for a in sorted(ad_links[q]) if grp[a] in ('film', 'tv')]
ADI = pd.DataFrame(ad_rows, columns=['book_item', 'item', 'kind', 'release_mi', 'page'])
n_ad_items_no_page = int(ADI.page.isna().sum())
ADW = WK.merge(ADI.dropna(subset=['page']), on='book_item')
ADW = ADW[[p not in own_titles.get(w, ()) for w, p in zip(ADW.work_id, ADW.page)]]
ADW = (ADW.sort_values(['work_id', 'page', 'release_mi']).groupby(['work_id', 'page'], as_index=False)
       .agg(book_item=('book_item', 'first'), item=('item', lambda s: '|'.join(sorted(set(s)))),
            kind=('kind', lambda s: 'film' if (s == 'film').any() else 'tv'), release_mi=('release_mi', 'min')))
ADW = ADW[['work_id', 'book_item', 'item', 'page', 'kind', 'release_mi']].sort_values(['work_id', 'page']).reset_index(drop=True)
ADW['release_mi'] = ADW.release_mi.astype('float64')
ADW.to_parquet(OUT / 'pages_AD.parquet', index=False)
log('AD: rows', len(ADW), '| works', ADW.work_id.nunique(), '| pages', ADW.page.nunique(), '| film/TV items without an English article', n_ad_items_no_page)

# LK pages per work
R['page'] = R.item.map(SL)
n_lk_items_no_page = int(R.drop_duplicates('item').page.isna().sum())
LKW = WK.merge(R.dropna(subset=['page']), on='book_item')
ad_pairs = set(zip(ADW.work_id, ADW.page))
own_drop = np.array([p in own_titles.get(w, ()) for w, p in zip(LKW.work_id, LKW.page)])
ad_drop = np.array([(w, p) in ad_pairs for w, p in zip(LKW.work_id, LKW.page)]) & ~own_drop
excl_pages = dict(own_book_or_author_article=int(own_drop.sum()), also_AD_page=int(ad_drop.sum()))
LKW = LKW[~own_drop & ~ad_drop].copy()
LKW['rank'] = LKW.link_type.map({t: i for i, t in enumerate(LINK_ORDER)})
props = LKW.groupby(['work_id', 'page']).p.apply(lambda s: '|'.join(sorted(set(s))))
LKW = LKW.sort_values(['work_id', 'page', 'rank']).drop_duplicates(['work_id', 'page'])
LKW['props'] = [props[(w, p)] for w, p in zip(LKW.work_id, LKW.page)]
LKW['category'] = LKW.item.map(cat)
LKW['is_period'] = LKW.item.map(isper).astype(bool)
LKW = LKW.rename(columns={'link_type': 'kind'})[['work_id', 'book_item', 'item', 'page', 'kind', 'props', 'category', 'is_period']]
LKW = LKW.sort_values(['work_id', 'page']).reset_index(drop=True)
LKW.to_parquet(OUT / 'pages_LK.parquet', index=False)
log('LK: rows', len(LKW), '| works', LKW.work_id.nunique(), '| pages', LKW.page.nunique(), '| linked items without an English article', n_lk_items_no_page)


def vc(s):
    return {str(k): int(v) for k, v in s.value_counts().items()}


summ = dict(written=time.strftime('%Y-%m-%d %H:%M %z'), works=len(M), works_with_item=int(len(WK)), book_items=len(items),
            wikidata=dict(network=H.n_net, cache=H.n_cache, backoffs=H.n_backoff, codes={str(k): v for k, v in H.codes.items()}),
            AD=dict(adaptation_items=len(ad_items), groups=gcount, screen_items=len(screen), screen_items_without_english_article=n_ad_items_no_page,
                    screen_items_with_release_month=int(sum(np.isfinite(rel[a]) for a in screen)), work_page_rows=len(ADW),
                    works=int(ADW.work_id.nunique()), pages=int(ADW.page.nunique()), rows_by_kind=vc(ADW.kind),
                    rows_without_release_month=int(ADW.release_mi.isna().sum()), m01_check_items=n_chk),
            LK=dict(best_rank_statements=len(raw), statements_by_property=vc(pd.Series([p for _, p, _ in raw])), distinct_linked_items=len(linked),
                    left_out_by_item=excl, left_out_pages=excl_pages, linked_items_kept=int(R.item.nunique()),
                    linked_items_without_english_article=n_lk_items_no_page, work_page_rows=len(LKW), works=int(LKW.work_id.nunique()),
                    pages=int(LKW.page.nunique()), rows_by_kind=vc(LKW.kind), rows_by_category=vc(LKW.category),
                    items_reaching_several_roots=int(sum(nroots[x] > 1 for x in set(LKW.item))), is_period_items=int(sum(isper[x] for x in set(LKW.item))),
                    j4_classes_walked=len(parents2), j4_unfinished_frontier=len(frontier), pages_per_work=LKW.groupby('work_id').size().describe().round(2).to_dict()),
            runtime_s=round(time.time() - T0))
(OUT / 'n12_summary.json').write_text(json.dumps(summ, indent=1, default=str))
log(json.dumps(summ, default=str))
log('done')
