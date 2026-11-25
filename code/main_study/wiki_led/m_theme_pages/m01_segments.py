# m01. Addendum m, step 2: Wikidata facts and the per-work and per-series inputs of the segment families (B_segments).  DATA ONLY:
# no loans are related to anything; the report has counts.  Settings: prereg/addenda_wiki_led/2026-11-25_m_theme_pages_single_books.json
# (read-only; SHA-256 checked).
#
# Wikidata (record, B_segments.wikidata_facts): wbgetentities, props=claims, batches of 10 ids, gap 0.34 s (under 3 requests a second),
#   cached by the Http class of ../_common.py.  Items: the main set's matched book items (l_books_in_time/matches.parquet), the items
#   they point to by P156, their adaptation items (P4969 on the book item, plus the pairs of data/db/wiki_led/adaptations.parquet), the
#   P279 parents of the adaptation classes (walked until no new class or depth 12), and the P407 language items (labels).
# Per work (static or dated facts; the scoring step turns dated facts into labels at each origin t):
#   has_item; follows (P155 has a value, or a P179 statement whose P1545 ordinal starts with a number >= 2); next_pub_mi (earliest month
#   by which a P156 'followed by' book had surely been published: its earliest non-deprecated P577, month precision -> that month, year
#   precision -> December of that year); adapt_mi (earliest release month of a film or TV adaptation, rule of 71_wikidata_events.py:
#   earliest non-deprecated best-rank P577 or P580 at month precision or finer; with year precision only, January of the following year);
#   award_mi (earliest P166 statement's P585, month precision -> that month, year precision -> December of that year); translated (1 if
#   the item has P407 and none of its values is an English language item, 0 if one is, missing without P407); pub_year (earliest
#   non-deprecated P577 year; classic = before 1930); form, audience, broad theme, has a narrow theme; author_earlier (creator_key has
#   another Seattle work first lent before this one; missing for an empty creator).
# Per series (work, format) and test year Y: loans in the 12 calendar months of Y-1, excluded months skipped (F3).
# Outputs: data/db/wiki_led/m_theme_pages/seg_works.parquet, seg_pop.parquet, wd_facts.json; report data/reports/theme_pages_m01_segments.md
#   Run from code/:  bash ../jobs/bg.sh m01_segments main_study/wiki_led/m_theme_pages/m01_segments.py
import sys, os, re, json, time, hashlib, pathlib
import numpy as np, pandas as pd, pyarrow.parquet as pq

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _common import Http, maxlag_check, D as DATA_DIR      # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_m_theme_pages_single_books.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'df8a4fd95bb46cec3488ba062b0033156e2ded4d00678cf899471cc201663d7f', 'addendum m changed'
L = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
TAXO = DATA / 'db' / 'taxonomy_v3'
OUT = DATA / 'db' / 'wiki_led' / 'm_theme_pages'
OUT.mkdir(parents=True, exist_ok=True)
REP = DATA / 'reports'
WD_API = 'https://www.wikidata.org/w/api.php'
H = Http({'wd': 0.34})
SCREEN_ROOTS = {'Q11424': 'film', 'Q5398426': 'tv', 'Q15416': 'tv', 'Q3464665': 'tv', 'Q21191270': 'tv', 'Q526877': 'tv'}  # 71_wikidata_events.py
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def mi_of(y, m):
    return int(y) * 12 + int(m) - 1


# ---------------------------------------------------------------- Wikidata
ENT = {}


def fetch(qids, what):
    todo = sorted({q for q in qids if isinstance(q, str) and q.startswith('Q') and q not in ENT})
    for i in range(0, len(todo), 10):
        batch = todo[i:i + 10]
        st, text = H.get('wd', WD_API, dict(action='wbgetentities', ids='|'.join(batch), props='claims|labels', languages='en',
                                            format='json', maxlag=5), check=maxlag_check)
        if st != 200:
            raise RuntimeError(f'Wikidata status {st}')
        ents = json.loads(text).get('entities', {})
        for q in batch:
            e = ents.get(q) or {}
            ENT[q] = e if 'missing' not in e else {}
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
    """(year, month or None, precision) of a time statement; None for unknown values or BCE dates."""
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


def label(q):
    return ((ENT.get(q) or {}).get('labels', {}).get('en') or {}).get('value', '')


M = pd.read_parquet(L / 'matches.parquet', columns=['work_id', 'creator_key', 'book_item'])
items = sorted(M.book_item.dropna().unique())
log('main-set works', len(M), '| with a book item', int(M.book_item.notna().sum()), '| distinct items', len(items))
fetch(items, 'book items')

# P156 targets, adaptation items, P407 languages
nxt = {q: [val_item(s) for s in stmts(q, 'P156') if s.get('rank') != 'deprecated' and val_item(s)] for q in items}
ADX = pd.read_parquet(DATA / 'db' / 'wiki_led' / 'adaptations.parquet', columns=['adapt', 'book'])
ad_links = {q: set(v for v in (val_item(s) for s in stmts(q, 'P4969')) if v) for q in items}
for a, b in ADX[ADX.book.isin(set(items))][["adapt", "book"]].itertuples(index=False):
    ad_links[b].add(a)
langs = {q: [val_item(s) for s in stmts(q, 'P407') if s.get('rank') != 'deprecated' and val_item(s)] for q in items}
fetch({x for v in nxt.values() for x in v}, 'followed-by items')
fetch({x for v in ad_links.values() for x in v}, 'adaptation items')
fetch({x for v in langs.values() for x in v}, 'language items')

# class walk for adaptation types (P31 -> P279*)
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
log('class walk: classes', len(parents), '| unfinished frontier', len(frontier))


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
    """71_wikidata_events.py's rule: earliest non-deprecated best-rank P577/P580 at month precision or finer; with year precision only,
    January of the following year."""
    month_dates, years = [], []
    for prop in ('P577', 'P580'):
        ss = [s for s in stmts(a, prop) if s.get('rank') != 'deprecated']
        pref = [s for s in ss if s.get('rank') == 'preferred']
        best = pref if pref else ss
        for s in best:
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


def sure_mi(t):
    """month by which a dated fact had surely happened: month precision -> that month; year precision -> December of that year."""
    return mi_of(t[0], t[1]) if t[1] is not None else mi_of(t[0], 12)


ENGLISH_EXCL = {'old english', 'middle english'}


def is_english(q):
    lab = label(q).lower()
    return lab not in ENGLISH_EXCL and (lab == 'english' or lab.endswith(' english'))


rows = []
for q in items:
    follows = any(val_item(s) for s in stmts(q, 'P155') if s.get('rank') != 'deprecated')
    for s in stmts(q, 'P179'):
        if s.get('rank') == 'deprecated':
            continue
        for qs in s.get('qualifiers', {}).get('P1545', []):
            m = re.match(r'\s*(\d+)', str((qs.get('datavalue') or {}).get('value', '')))
            if m and int(m.group(1)) >= 2:
                follows = True
    nm = [sure_mi(t) for x in nxt[q] for t in (val_time(s) for s in stmts(x, 'P577') if s.get('rank') != 'deprecated') if t]
    ads = [a for a in ad_links[q] if group_of(a) in ('film', 'tv')]
    rel = [release_mi(a) for a in ads]
    rel = [r for r in rel if np.isfinite(r)]
    aw = []
    for s in stmts(q, 'P166'):
        if s.get('rank') == 'deprecated':
            continue
        for qs in s.get('qualifiers', {}).get('P585', []):
            t = parse_time((qs.get('datavalue') or {}).get('value', {}) or {})
            if t:
                aw.append(sure_mi(t))
    lg = langs[q]
    py = [t[0] for t in (val_time(s) for s in stmts(q, 'P577') if s.get('rank') != 'deprecated') if t]
    rows.append(dict(book_item=q, follows=int(follows), in_series_any=int(follows or bool(nxt[q]) or bool(stmts(q, 'P179'))),
                     next_pub_mi=min(nm) if nm else np.nan, n_screen_adaptations=len(ads), adapt_mi=min(rel) if rel else np.nan,
                     award_mi=min(aw) if aw else np.nan, translated=(np.nan if not lg else float(not any(is_english(x) for x in lg))),
                     pub_year=min(py) if py else np.nan))
F = pd.DataFrame(rows)
log('facts per item', len(F))

# ---------------------------------------------------------------- per work
W = M[['work_id', 'creator_key', 'book_item']].merge(F, on='book_item', how='left')
W['has_item'] = W.book_item.notna().astype(np.int8)
FL = pd.read_parquet(TAXO / 'work_form_label.parquet', columns=['work_id', 'audience_label', 'form_label'])
W = W.merge(FL, on='work_id', how='left')
W['form'] = W.form_label.map({'fiction': 'fiction', 'nonfiction': 'nonfiction'}).fillna('other (mixed or unknown)')
W['audience'] = W.audience_label.map({'children': 'children', 'middle grade': 'children', 'young adult': 'young adult',
                                      'new adult': 'young adult', 'adult': 'adult', 'adult (default)': 'adult'}).fillna('adult')
WT = pd.read_parquet(TAXO / 'work_theme.parquet', columns=['work_id', 'node_id', 'level', 'rank_in_level'])
WT = WT[WT.work_id.isin(set(M.work_id))]
broad = WT[(WT.level == 1) & (WT.rank_in_level == 1)].drop_duplicates('work_id').set_index('work_id').node_id
NL = pd.read_parquet(TAXO / 'theme_nodes.parquet', columns=['node_id', 'label']).set_index('node_id').label
W['genre'] = W.work_id.map(broad).map(lambda n: f'{n} {NL.get(n, "")}' if isinstance(n, str) else 'no theme')
W['has_theme'] = W.work_id.isin(set(WT[WT.level == 3].work_id)).map({True: 'yes', False: 'no'})
SW = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'creator_key', 'first_ym'])
SW = SW[SW.creator_key.fillna('') != '']
first_by_creator = SW.groupby('creator_key').first_ym.min()
mine = SW.set_index('work_id').first_ym
ck = W.creator_key.fillna('')
own_first = W.work_id.map(mine)
# another work with the same creator was first lent earlier: the creator's earliest first_ym is earlier than this work's own first_ym
W['author_earlier'] = np.where(ck == '', 'unknown', np.where(ck.map(first_by_creator) < own_first, 'yes', 'no'))
W = W.drop(columns=['audience_label', 'form_label'])
W.to_parquet(OUT / 'seg_works.parquet', index=False)

# ---------------------------------------------------------------- per series and test year: loans in Y-1 (F3)
P = pd.read_parquet(DATA / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok']).drop_duplicates(['format', 'mi'])
EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= mi_of(2015, 1)}
S_ids = np.sort(M.work_id.to_numpy(np.int64))
NS = len(S_ids)
rw = pd.read_parquet(TAXO / 'spl_record_work.parquet')
rid, wid = rw.record_id.to_numpy(np.int64), rw.work_id.to_numpy(np.int64)
p = np.searchsorted(S_ids, wid); p[p >= NS] = 0
inS = S_ids[p] == wid
LUT = np.full(int(rid.max()) + 1, -1, np.int32); LUT[rid[inS]] = p[inS]
MI0, MI1 = mi_of(2017, 1), mi_of(2025, 12)
NM = MI1 - MI0 + 1
pop = []
for label_, fname in (('print', 'book'), ('ebook', 'ebook'), ('audiobook', 'audiobook')):
    pf = pq.ParquetFile(TAXO / f'spl_rows_{fname}.parquet')
    A = np.zeros((NS, NM), np.float64)
    for g in range(pf.num_row_groups):
        t = pf.read_row_group(g, columns=['record_id', 'year', 'month', 'checkouts'])
        w = LUT[t.column('record_id').to_numpy()]
        mc = t.column('year').to_numpy().astype(np.int32) * 12 + t.column('month').to_numpy().astype(np.int32) - 1 - MI0
        k = (w >= 0) & (mc >= 0) & (mc < NM)
        if k.any():
            np.add.at(A, (w[k], mc[k]), t.column('checkouts').to_numpy()[k])
    for Y in range(2019, 2027):
        cols = [m - MI0 for m in range(mi_of(Y - 1, 1), mi_of(Y - 1, 12) + 1) if m not in EXCL]
        pop.append(pd.DataFrame({'work_id': S_ids, 'format': label_, 'test_year': Y, 'loans_prev_year': A[:, cols].sum(axis=1)}))
    log('loans by year', label_)
POP = pd.concat(pop, ignore_index=True)
POP.to_parquet(OUT / 'seg_pop.parquet', index=False)

# ---------------------------------------------------------------- report (counts only)
wi = W[W.has_item == 1]
summ = dict(works=len(W), works_with_item=len(wi), items=len(items), wikidata=dict(network=H.n_net, cache=H.n_cache, backoffs=H.n_backoff),
            follows=int(wi.follows.sum()), with_next_pub=int(wi.next_pub_mi.notna().sum()), with_screen_adaptation_dated=int(wi.adapt_mi.notna().sum()),
            with_award_dated=int(wi.award_mi.notna().sum()), translated=wi.translated.value_counts(dropna=False).rename(str).to_dict(),
            pub_year_known=int(wi.pub_year.notna().sum()), before_1930=int((wi.pub_year < 1930).sum()),
            adaptation_items=len(ad_items), adaptation_groups=pd.Series([group_of(a) for a in ad_items]).value_counts().to_dict(),
            form=W.form.value_counts().to_dict(), audience=W.audience.value_counts().to_dict(), author_earlier=W.author_earlier.value_counts().to_dict(),
            has_theme=W.has_theme.value_counts().to_dict(), runtime_s=round(time.time() - T0))
(OUT / 'wd_facts.json').write_text(json.dumps(summ, indent=1, default=str))
Lr = ['# Addendum m, step 2: Wikidata facts and segment inputs (counts only)', '',
      f'Made by `code/main_study/wiki_led/m_theme_pages/m01_segments.py` on {time.strftime("%Y-%m-%d %H:%M")} (+07:00). Data only; no loans related to anything.', '']
Lr += [f'- {k}: {v}' for k, v in summ.items()]
(REP / 'theme_pages_m01_segments.md').write_text('\n'.join(Lr) + '\n')
log(json.dumps(summ, default=str))
log('done')
