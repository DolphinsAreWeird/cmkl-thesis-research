# 20. (v3) LibriVox recordings in taxonomy v3: themes and genres per LibriVox book (book_id = the bookgroup used in
# data/db/listening.parquet and books.parquet, single-author books only, as in Study 2).
# Same value-assignment logic as the Seattle works (16): theme evidence is kept per source, mapped to theme values and
# through theme_value_node.parquet to the fixed tree (the same values, nodes and embedding placements), each source's
# weights become shares rolled up to parent nodes, and strength = mean share over the sources that have evidence.
# Sources available on disk:
#   lv    LibriVox genres of the book's recordings (a closed list like the OverDrive terms; split into facets by the v2
#         phrase rules, data/db/taxonomy_v2/phrases.parquet source 'librivox'), weighted by recordings
#   gr    Goodreads shelves of the linked Goodreads work (data/interim/goodreads_linked.pkl; shelves from goodreads_works),
#         same rule as 16 (shelves with >= 2 users, v2 phrase rules)
#   desc  the LibriVox description: whole-word matches of a curated value list (v2 theme values, the v2 lexicon, and the
#         v3 values placed by hand or hand rule; values placed only by embedding are not matched in free text).
#         Phrases of two or more words count (minus DESC_BLOCK_MULTI); a single word counts only if it is in the
#         hand-reviewed list DESC_ALLOW_SINGLE (specific words such as 'slavery', 'pirates', 'plague'). Ambiguous single
#         words were left out after review: 'white' and 'race' (matched race and racism), 'black', 'light', 'night',
#         'prejudice' (Pride and Prejudice), 'violence', 'outbreak' (of war), 'storm', 'rain', 'reading' (LibriVox
#         readers) and others. Values found in more than DESC_MAX_DF of all descriptions are too generic and are dropped.
#         Boilerplate about the recording is removed first. Each value counts once per book. The reviewed word lists
#         are written to quality/librivox_desc_words.csv.
# Not used: Wikidata main subjects (P921) and Open Library subjects per book are not on disk (only a global list of
# Wikidata subjects is); fetching them would need a new download. Title words are not used.
# Output: data/db/taxonomy_v3/librivox_work_theme.parquet (book_id, node_id, level, strength, s_lv, s_gr, s_desc, sources)
#         librivox_work_theme_value.parquet, librivox_work_genre.parquet (book_id, value, strength, s_lv, s_gr),
#         quality/librivox_coverage.csv, quality/librivox_top_nodes.csv
import os
os.environ['TAXO'] = 'v3'
import ast, json, re, collections, numpy as np, pandas as pd
from _common import OUT, OUT_V2, D
import _lexicon as L
import _review_v3 as RV3

DESC_MAX_DF = 0.03
# hand review of the most frequent single-word matches (13 Oct 2026): only these single words count as evidence
DESC_ALLOW_SINGLE = set("""
marriage wedding weddings bible jesus christianity catholic catholicism theology saint saints philosophy slavery slave slaves
christmas ghost ghosts magic pirate pirates mythology myths castle castles knight knights alien aliens mars planet planets
universe evolution poverty prison police crime crimes revenge betrayal orphan orphans suicide opera democracy revolution
exploration hunting fishing sailing widow widows aristocracy gang gangs hospital disease illness museum museums painting
artist artists music dog dogs cat cats horse horses bird birds bear bears mountain mountains wilderness education teaching
economics business money wealth greed happiness ethics morality virtue virtues grief loyalty kindness terrorism psychology
logic consciousness dreams personality fashion plants heaven prayer prayers spiritual invention inventions medicine
childhood sister sisters government military animals survival consciousness technology
racism lynching lynchings segregation plague plagues epidemic epidemics pandemic pandemics cholera smallpox influenza
quarantine rape hurricane hurricanes blizzard blizzards tornadoes drought droughts typhoon typhoons monsoons meteorology
climatology vaccine vaccines virus viruses
""".split())
DESC_BLOCK_MULTI = {'racism in', 'weather control', 'black races'}
VN = pd.read_parquet(f'{OUT}/theme_value_node.parquet'); vnode = dict(zip(VN.theme, VN.node_id))
N = pd.read_parquet(f'{OUT}/theme_nodes.parquet'); level = dict(zip(N.node_id, N.level)); label = dict(zip(N.node_id, N.label))
P2 = pd.read_parquet(f'{OUT_V2}/phrases.parquet', columns=['source', 'raw', 'components_json'])
comp = {(s, r): [tuple(x) for x in json.loads(c)] for s, r, c in zip(P2.source, P2.raw, P2.components_json)}

lk = pd.read_pickle(f'{D}/interim/recordings_linked.pkl')
lk = lk[lk.n_authors == 1].copy()
lk['book_id'] = lk.bookgroup.astype(str)
books = pd.read_parquet(f'{D}/db/books.parquet').book_id.astype(str)
lk = lk[lk.book_id.isin(set(books))]
ev = []; cat = []

# ---------- lv: LibriVox genres ----------
for b, gs in zip(lk.book_id, lk.genres.fillna('[]')):
    names = [g['name'] for g in ast.literal_eval(gs)] if gs.startswith('[') else []
    for nm in names:
        cs = comp.get(('librivox', nm), [])
        th = [v for f, v in cs if f == 'theme']
        for v in th:
            ev.append((b, 'lv', v, 1.0 / len(th)))
        for f, v in cs:
            if f in ('genre', 'audience', 'form'):
                cat.append((b, 'lv', f, v, 1.0))

# ---------- gr: Goodreads shelves ----------
gl = pd.read_pickle(f'{D}/interim/goodreads_linked.pkl')[['identifier', 'gr_work']]
gl = gl.merge(lk[['identifier', 'book_id']], on='identifier')
G = pd.read_parquet(f'{OUT}/goodreads_works.parquet', columns=['gr_work_id', 'shelves', 'shelf_counts'])
G['gr_work_id'] = G.gr_work_id.astype(str)
gl['gr_work'] = gl.gr_work.astype(str)
GB = gl.drop_duplicates(['book_id', 'gr_work']).merge(G, left_on='gr_work', right_on='gr_work_id')
for b, shs, cs_ in zip(GB.book_id, GB.shelves, GB.shelf_counts):
    for sh, c in zip(shs, cs_):
        if c < 2:
            continue
        cs = comp.get(('goodreads', sh))
        if not cs:
            continue
        th = [v for f, v in cs if f == 'theme']
        for v in th:
            ev.append((b, 'gr', v, float(c) / len(th)))
        for f, v in cs:
            if f in ('genre', 'audience', 'form'):
                cat.append((b, 'gr', f, v, float(c)))

# ---------- desc: curated value list matched in the description ----------
def canon_basic(s):
    s = str(s).lower().replace('&', ' and ')
    s = re.sub(r"[\-_/\.,:;!\?\(\)\[\]\"’'`+#]+", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

lex = {}
V2 = set(pd.read_parquet(f'{OUT_V2}/theme_values.parquet').theme)
for v in V2:
    lex[canon_basic(v)] = v
for k, v in L.THEMES.items():
    lex.setdefault(canon_basic(k), v)
LOG = pd.read_csv(f'{OUT}/profile/placement_log.csv', usecols=['theme', 'method'], low_memory=False)
for v in LOG[LOG.method.isin(['hand', 'hand rule (pattern)'])].theme:
    lex.setdefault(canon_basic(v), v)
lex = {k: v for k, v in lex.items() if v in vnode and len(k) >= 3}
for k, v in list(lex.items()):                      # simple plural / singular variants
    alt = k[:-1] if k.endswith('s') and not k.endswith('ss') else k + 's'
    lex.setdefault(alt, v)
maxn = max(len(k.split()) for k in lex)
BOILER = re.compile(r'\(summary (?:from|by)[^)]*\)|summary (?:from|by) [^.]*\.|this (?:is a )?librivox recording[^.]*\.|'
                    r'project gutenberg|public domain|read by [^.]*\.|librivox|recording|recorded|chapters?|reader|volunteers?',
                    re.I)
desc = lk.groupby('book_id').desc.apply(lambda s: ' '.join(dict.fromkeys(x for x in s.fillna('') if x)))
found = {}; KEYS = collections.Counter(); SKIPPED = collections.Counter()
for b, t in desc.items():
    t = re.sub(r'<[^>]+>', ' ', t)
    t = BOILER.sub(' ', t)
    toks = canon_basic(t).split()
    hits = set()
    for n in range(maxn, 0, -1):
        for i in range(len(toks) - n + 1):
            g = ' '.join(toks[i:i + n])
            if g in lex and ((n == 1 and g in DESC_ALLOW_SINGLE) or (n > 1 and g not in DESC_BLOCK_MULTI)):
                hits.add(lex[g]); KEYS[g] += 1
            elif g in lex and n == 1:
                SKIPPED[g] += 1
    found[b] = hits
df = collections.Counter(v for h in found.values() for v in h)
too_common = {v for v, c in df.items() if c > DESC_MAX_DF * len(found)}
for b, hits in found.items():
    hs = [v for v in hits if v not in too_common]
    for v in hs:
        ev.append((b, 'desc', v, 1.0))
Q = f'{OUT}/quality'; os.makedirs(Q, exist_ok=True)
pd.DataFrame([dict(word=k, value=lex[k], node=label.get(vnode[lex[k]]), books=c, used='yes' if lex[k] not in too_common else 'no (too common)') for k, c in KEYS.most_common()] +
             [dict(word=k, value=lex[k], node=label.get(vnode[lex[k]]), books=c, used='no (ambiguous single word)') for k, c in SKIPPED.most_common()]
             ).to_csv(f'{Q}/librivox_desc_words.csv', index=False)
print('books', len(books), 'with recordings metadata', lk.book_id.nunique(), '| description values dropped as too common:',
      sorted(too_common), flush=True)

# ---------- shares, roll-up and strength (as in 16) ----------
EV = pd.DataFrame(ev, columns=['book_id', 'source', 'theme', 'weight']).groupby(['book_id', 'source', 'theme'], as_index=False).weight.sum()
EV['node_id'] = EV.theme.map(vnode)
EV.to_parquet(f'{OUT}/librivox_work_theme_value.parquet', index=False)
E = EV[EV.node_id.notna()].copy()
E['share'] = E.weight / E.groupby(['book_id', 'source']).weight.transform('sum')
sources = ['lv', 'gr', 'desc']
rows = []
for lvl in [1, 2, 3]:
    t = E[E.node_id.map(lambda x: level[x] >= lvl)].copy()
    t['anc'] = t.node_id.map(lambda x: '.'.join(x.split('.')[:lvl]))
    rows.append(t.groupby(['book_id', 'source', 'anc'], as_index=False).share.sum().assign(level=lvl))
S = pd.concat(rows).rename(columns={'anc': 'node_id'})
wide = S.pivot_table(index=['book_id', 'node_id', 'level'], columns='source', values='share', fill_value=0.0).reset_index()
has = E.groupby(['book_id', 'source']).size().unstack(fill_value=0) > 0
for c in sources:
    if c not in wide: wide[c] = 0.0
    if c not in has: has[c] = False
wide = wide.merge(has[sources].rename(columns=lambda c: f'has_{c}').reset_index(), on='book_id')
den = wide[[f'has_{c}' for c in sources]].sum(axis=1)
wide['strength'] = sum(wide[c] * wide[f'has_{c}'] for c in sources) / den
wide['sources'] = [','.join(c for c, h in zip(sources, hs) if h) for hs in wide[[f'has_{c}' for c in sources]].values]
wide = wide.rename(columns={c: f's_{c}' for c in sources})
WT = wide[['book_id', 'node_id', 'level', 'strength'] + [f's_{c}' for c in sources] + ['sources']].copy()
WT['level'] = WT.level.astype(int)
WT.to_parquet(f'{OUT}/librivox_work_theme.parquet', index=False)

# ---------- genres (v2 method: LibriVox genres and Goodreads shelves) ----------
C = pd.DataFrame(cat, columns=['book_id', 'source', 'facet', 'value', 'weight']).groupby(['book_id', 'source', 'facet', 'value'], as_index=False).weight.sum()
C['share'] = C.weight / C.groupby(['book_id', 'source', 'facet']).weight.transform('sum')
g = C[C.facet == 'genre']
gw = g.pivot_table(index=['book_id', 'value'], columns='source', values='share', fill_value=0.0).reset_index()
for s_ in ['lv', 'gr']:
    if s_ not in gw: gw[s_] = 0.0
hs = g.groupby(['book_id', 'source']).size().unstack(fill_value=0) > 0
for s_ in ['lv', 'gr']:
    if s_ not in hs: hs[s_] = False
gw = gw.merge(hs[['lv', 'gr']].rename(columns=lambda s_: f'has_{s_}').reset_index(), on='book_id')
gw['strength'] = (gw.lv * gw.has_lv + gw.gr * gw.has_gr) / (gw.has_lv.astype(int) + gw.has_gr.astype(int))
gw = gw.rename(columns={'lv': 's_lv', 'gr': 's_gr'})
gw = gw[(gw.s_lv > 0) | (gw.s_gr >= 0.05)]
gw[['book_id', 'value', 'strength', 's_lv', 's_gr']].to_parquet(f'{OUT}/librivox_work_genre.parquet', index=False)

# ---------- coverage (recordings = LibriVox books; listens = all months in listening.parquet) ----------
Lis = pd.read_parquet(f'{D}/db/listening.parquet', columns=['book_id', 'listens'])
lis = Lis.groupby(Lis.book_id.astype(str)).listens.sum().reindex(books).fillna(0)
cov = []
for meas, ws in [('any theme', set(WT.book_id)), ('narrow theme', set(WT[WT.level == 3].book_id)), ('any genre', set(gw.book_id))] + \
                [(f'theme evidence from {s_}', set(E[E.source == s_].book_id)) for s_ in sources]:
    m = books.isin(ws)
    cov.append(dict(measure=meas, recordings=int(m.sum()), share_recordings=round(float(m.mean()), 4),
                    share_listens=round(float(lis[m.values].sum() / lis.sum()), 4)))
cov.append(dict(measure='all LibriVox books', recordings=len(books), share_recordings=1.0, share_listens=1.0))
pd.DataFrame(cov).to_csv(f'{Q}/librivox_coverage.csv', index=False)
top = WT.groupby(['node_id', 'level']).book_id.nunique().rename('recordings').reset_index()
top['label'] = top.node_id.map(label)
top = top.sort_values(['level', 'recordings'], ascending=[True, False])
top[['level', 'node_id', 'label', 'recordings']].to_csv(f'{Q}/librivox_top_nodes.csv', index=False)
print(pd.DataFrame(cov).to_string(index=False))
print(top[top.level == 3].head(15).to_string(index=False))
print('genres: books', gw.book_id.nunique(), 'themes per covered book (narrow, median):', WT[WT.level == 3].groupby('book_id').size().median())
