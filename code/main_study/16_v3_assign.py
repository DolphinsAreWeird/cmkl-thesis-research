# 16. (v3) Assign every SPL work (all three formats) its themes with strengths, plus genres, audience and form.
# Main theme evidence, kept per source:
#   spl    OverDrive subject terms of the work's digital records (as in v2)
#   lcsh   print subject headings of the work's print records (the same work's audiobook and ebook share them);
#          the heading's own topic counts 1, themes from its subdivisions ('Psychological aspects') count 0.5
#   gr     Goodreads shelves of the linked Goodreads work (links from 13, title + author)
# For each source the work's theme weights become shares (sum 1) rolled up to parent nodes; strength = mean share over
# the sources that have theme evidence for the work. Title words are NOT used here: they are written separately as a
# flagged backup (work_theme_title_backup.parquet), for a positive-control category with fewer than 50 works only.
# Genres as in v2 (SPL terms + Goodreads shelves); print-only works without either take their print genre parts.
# Heading genre/form/place/period/person parts are also stored apart (work_lcsh_parts).
# Output (data/db/taxonomy_v3/): work_theme, work_theme_value, work_theme_title_backup, work_genre, work_audience_label,
#   work_form_label, work_lcsh_parts
import os
os.environ['TAXO'] = 'v3'
import json, re, collections, numpy as np, pandas as pd
from _common import OUT, OUT_V2, norm_text, clean_title
import _lexicon as L

W = pd.read_parquet(f'{OUT}/spl_works.parquet', columns=['work_id', 'title', 'formats', 'n_terms', 'n_headings'])
VN = pd.read_parquet(f'{OUT}/theme_value_node.parquet'); v2node = dict(zip(VN.theme, VN.node_id))
N = pd.read_parquet(f'{OUT}/theme_nodes.parquet'); level = dict(zip(N.node_id, N.level))
P2 = pd.read_parquet(f'{OUT_V2}/phrases.parquet', columns=['source', 'raw', 'components_json'])
comp = {(s, r): [tuple(x) for x in json.loads(c)] for s, r, c in zip(P2.source, P2.raw, P2.components_json)}
ev = []; cat = []

# ---------- spl: OverDrive terms ----------
WT = pd.read_parquet(f'{OUT}/work_terms.parquet')
for wid, t, s in zip(WT.work_id, WT.term, WT.share):
    cs = comp.get(('spl', t), [])
    th = [v for f, v in cs if f == 'theme']
    for v in th:
        ev.append((wid, 'spl', v, float(s) / len(th)))
    for f, v in cs:
        if f in ('genre', 'audience', 'form'):
            cat.append((wid, 'spl', f, v, float(s)))
del WT

# ---------- lcsh: print subject headings ----------
HP = pd.read_parquet(f'{OUT}/headings_parsed.parquet', columns=['heading_id', 'components_json'])
hth = {}; hpart = {}
for hid, cj in zip(HP.heading_id, HP.components_json):
    th = []; parts = []
    for f, v in json.loads(cj):
        if f == 'core_theme':
            th.append((v, 1.0))
        elif f == 'theme':
            th.append((v, 0.5))
        elif f in ('genre', 'audience', 'form', 'place', 'period', 'person', 'other'):
            parts.append((f, v))
    if th:
        hth[hid] = th
    if parts:
        hpart[hid] = parts
del HP
WH = pd.read_parquet(f'{OUT}/work_headings.parquet')
lp = []
for wid, hid, s in zip(WH.work_id, WH.heading_id, WH.share):
    for v, w in hth.get(hid, ()):
        ev.append((wid, 'lcsh', v, float(s) * w))
    for f, v in hpart.get(hid, ()):
        lp.append((wid, f, v, float(s)))
del WH
LP = pd.DataFrame(lp, columns=['work_id', 'facet', 'value', 'share']).groupby(['work_id', 'facet', 'value'], as_index=False).share.sum()
LP.to_parquet(f'{OUT}/work_lcsh_parts.parquet', index=False)
del lp

# ---------- gr: Goodreads shelves ----------
link = pd.read_parquet(f'{OUT}/spl_goodreads_link.parquet')
G = pd.read_parquet(f'{OUT}/goodreads_works.parquet', columns=['gr_work_id', 'shelves', 'shelf_counts']).merge(link, on='gr_work_id')
for wid, shs, cs_ in zip(G.work_id, G.shelves, G.shelf_counts):
    for sh, c in zip(shs, cs_):
        if c < 2:
            continue
        cs = comp.get(('goodreads', sh))
        if not cs:
            continue
        th = [v for f, v in cs if f == 'theme']
        for v in th:
            ev.append((wid, 'gr', v, float(c) / len(th)))
        for f, v in cs:
            if f in ('genre', 'audience', 'form'):
                cat.append((wid, 'gr', f, v, float(c)))
del G

EV = pd.DataFrame(ev, columns=['work_id', 'source', 'theme', 'weight']); del ev
EV = EV.groupby(['work_id', 'source', 'theme'], as_index=False).weight.sum()
EV['node_id'] = EV.theme.map(v2node)
EV.to_parquet(f'{OUT}/work_theme_value.parquet', index=False)        # includes values without a node (node_id empty)
E = EV[EV.node_id.notna()].copy()
E['share'] = E.weight / E.groupby(['work_id', 'source']).weight.transform('sum')


def rollup(E, sources):
    rows = []
    for lvl in [1, 2, 3]:
        t = E[E.node_id.map(lambda x: level[x] >= lvl)].copy()
        t['anc'] = t.node_id.map(lambda x: '.'.join(x.split('.')[:lvl]))
        rows.append(t.groupby(['work_id', 'source', 'anc'], as_index=False).share.sum().assign(level=lvl))
    S = pd.concat(rows).rename(columns={'anc': 'node_id'})
    wide = S.pivot_table(index=['work_id', 'node_id', 'level'], columns='source', values='share', fill_value=0.0).reset_index()
    has = E.groupby(['work_id', 'source']).size().unstack(fill_value=0) > 0
    for c in sources:
        if c not in wide: wide[c] = 0.0
        if c not in has: has[c] = False
    wide = wide.merge(has[sources].rename(columns=lambda c: f'has_{c}').reset_index(), on='work_id')
    den = wide[[f'has_{c}' for c in sources]].sum(axis=1)
    wide['strength'] = sum(wide[c] * wide[f'has_{c}'] for c in sources) / den
    wide['sources'] = [','.join(c for c, h in zip(sources, hs) if h) for hs in wide[[f'has_{c}' for c in sources]].values]
    wide = wide.rename(columns={c: f's_{c}' for c in sources})
    out = wide[['work_id', 'node_id', 'level', 'strength'] + [f's_{c}' for c in sources] + ['sources']].copy()
    out['rank_in_level'] = out.groupby(['work_id', 'level']).strength.rank(ascending=False, method='first').astype(int)
    return out


WTH = rollup(E, ['spl', 'lcsh', 'gr'])
WTH.to_parquet(f'{OUT}/work_theme.parquet', index=False)
print('main assignment: works with a theme', WTH.work_id.nunique(), 'by level', WTH.groupby('level').work_id.nunique().to_dict(), flush=True)

# ---------- genres (v2 method), audience and form labels ----------
C = pd.DataFrame(cat, columns=['work_id', 'source', 'facet', 'value', 'weight']).groupby(['work_id', 'source', 'facet', 'value'], as_index=False).weight.sum()
C['share'] = C.weight / C.groupby(['work_id', 'source', 'facet']).weight.transform('sum')
spl_nonfic = set(C[(C.source == 'spl') & (C.facet == 'form') & (C.value == 'nonfiction')].work_id)
FICTION_GENRES = {'historical fiction', 'mystery', 'cozy mystery', 'thriller', 'psychological thriller', 'legal thriller', 'political thriller', 'suspense',
                  'romance', 'contemporary romance', 'historical romance', 'paranormal romance', 'erotic romance', 'romantic comedy', 'fantasy',
                  'epic fantasy', 'urban fantasy', 'dark fantasy', 'science fiction', 'space opera', 'dystopian', 'post-apocalyptic', 'horror', 'gothic',
                  'literary fiction', 'general fiction', 'contemporary fiction', 'chick lit', 'womens fiction', 'western', 'christian fiction',
                  'urban fiction', 'war fiction', 'spy fiction', 'crime', 'adventure', 'action', 'magical realism', 'paranormal'}
g = C[C.facet == 'genre']
g = g[~((g.source == 'gr') & g.value.isin(FICTION_GENRES) & g.work_id.isin(spl_nonfic))]
gw = g.pivot_table(index=['work_id', 'value'], columns='source', values='share', fill_value=0.0).reset_index()
for s in ['spl', 'gr']:
    if s not in gw: gw[s] = 0.0
hs = g.groupby(['work_id', 'source']).size().unstack(fill_value=0) > 0
for s in ['spl', 'gr']:
    if s not in hs: hs[s] = False
gw = gw.merge(hs[['spl', 'gr']].rename(columns=lambda s: f'has_{s}').reset_index(), on='work_id')
gw['strength'] = (gw.spl * gw.has_spl + gw.gr * gw.has_gr) / (gw.has_spl.astype(int) + gw.has_gr.astype(int))
gw = gw.rename(columns={'spl': 's_spl', 'gr': 's_gr'})
gw = gw[(gw.s_spl > 0) | (gw.s_gr >= 0.05)]
# Print-only works have no SPL terms, so (decision 8 at checkpoint 2) their print genre parts ('Mystery fiction',
# 'Fantasy fiction') fill the genre facet when Goodreads gives none. Strength = share of the work's genre parts.
# Three LCSH genres are not in the v2 genre list: 'domestic fiction' -> family saga, 'psychological fiction' ->
# literary fiction, 'coming of age novel' -> left out (coming of age is a theme, not a genre, in the v2 tree).
LCSH_GENRE_MAP = {'domestic fiction': 'family saga', 'psychological fiction': 'literary fiction', 'coming of age novel': None}
po = set(W[W.formats == 'BOOK'].work_id) - set(gw.work_id)
lg = LP[(LP.facet == 'genre') & LP.work_id.isin(po)].copy()
lg['value'] = lg.value.map(lambda v: LCSH_GENRE_MAP.get(v, v))
lg = lg[lg.value.notna()].groupby(['work_id', 'value'], as_index=False).share.sum()
lg['strength'] = lg.share / lg.groupby('work_id').share.transform('sum')
lg['s_spl'] = 0.0; lg['s_gr'] = 0.0; lg['s_lcsh'] = lg.strength
gw['s_lcsh'] = 0.0
gw = pd.concat([gw[['work_id', 'value', 'strength', 's_spl', 's_gr', 's_lcsh']], lg[['work_id', 'value', 'strength', 's_spl', 's_gr', 's_lcsh']]], ignore_index=True)
print('genres: works', gw.work_id.nunique(), 'of which print-only from print genre parts', lg.work_id.nunique(), flush=True)
gw[['work_id', 'value', 'strength', 's_spl', 's_gr', 's_lcsh']].to_parquet(f'{OUT}/work_genre.parquet', index=False)


def first_label(*series_list, default):
    out = pd.Series(default, index=W.work_id)
    for s in reversed(series_list):
        out.loc[s.index.intersection(out.index)] = s
    return out


a = C[C.facet == 'audience']
aud_spl = a[a.source == 'spl'].sort_values('share', ascending=False).drop_duplicates('work_id').set_index('work_id').value
aud_gr = a[a.source == 'gr'].sort_values('share', ascending=False).drop_duplicates('work_id').set_index('work_id').value
la = LP[LP.facet == 'audience'].sort_values('share', ascending=False).drop_duplicates('work_id').set_index('work_id').value
aud = first_label(aud_spl, la, aud_gr, default='adult (default)')
f = C[(C.facet == 'form') & C.value.isin(['fiction', 'nonfiction'])]
f_spl = f[f.source == 'spl'].groupby('work_id').value.agg(lambda s: 'fiction' if 'fiction' in set(s) and 'nonfiction' not in set(s) else ('nonfiction' if 'nonfiction' in set(s) and 'fiction' not in set(s) else 'mixed'))
lf = LP[LP.facet == 'form'].copy()
lfic = set(lf[lf.value == 'fiction'].work_id) | set(LP[(LP.facet == 'genre') & LP.value.isin(FICTION_GENRES)].work_id)
lnon = set(LP[(LP.facet == 'form') & (LP.value == 'nonfiction')].work_id) | set(LP[(LP.facet == 'genre') & LP.value.isin({'biography', 'memoir', 'true crime', 'self-help', 'literary criticism'})].work_id)
hasl = set(W[W.n_headings > 0].work_id)
f_l = pd.Series({w: ('fiction' if w in lfic and w not in lnon else ('mixed' if w in lfic else 'nonfiction')) for w in hasl})
f_gr = f[f.source == 'gr'].sort_values('share', ascending=False).drop_duplicates('work_id').set_index('work_id').value
form = first_label(f_spl, f_l, f_gr, default='unknown')
pd.DataFrame({'work_id': W.work_id.values, 'audience_label': aud.reindex(W.work_id).values, 'form_label': form.reindex(W.work_id).values}).to_parquet(f'{OUT}/work_form_label.parquet', index=False)
pd.DataFrame({'work_id': W.work_id.values, 'audience_label': aud.reindex(W.work_id).values}).to_parquet(f'{OUT}/work_audience_label.parquet', index=False)
print('form labels', form.value_counts().to_dict(), 'audience', aud.value_counts().to_dict(), flush=True)

# ---------- title words: flagged backup only ----------
spec_vals = set(VN[VN.level == 3].theme)
surf = collections.defaultdict(set)
for (s, r), cs in comp.items():
    th = [v for f_, v in cs if f_ == 'theme']
    if len(th) == 1 and th[0] in spec_vals and s in ('goodreads', 'wikidata', 'spl'):
        surf[norm_text(r.replace('-', ' '))].add(th[0])
for k, v in L.THEMES.items():
    if v in spec_vals:
        surf[norm_text(k)].add(v)
for v in spec_vals & set(VN[VN.source == 'v2'].theme):
    surf[norm_text(v)].add(v)
for v, forms in L.TITLE_SURFACES.items():
    for f_ in forms:
        surf[norm_text(f_)].add(v)
hand_forms = {norm_text(f_) for fs in L.TITLE_SURFACES.values() for f_ in fs}
surf = {k: v for k, v in surf.items() if k and not k.startswith(('the ', 'a ')) and (k in hand_forms or len(k.split()) >= 2 or (len(k) >= 5 and k not in L.TITLE_STOP and k in v))}
nonfic = set(form[form == 'nonfiction'].index)
tb = []
for wid, t in zip(W.work_id, W.title):
    if wid not in nonfic:
        continue
    toks = norm_text(clean_title(t)).split(); used = [False] * len(toks); found = set()
    for n in range(4, 0, -1):
        for i in range(len(toks) - n + 1):
            if any(used[i:i + n]):
                continue
            gg = ' '.join(toks[i:i + n])
            if gg in surf:
                found |= surf[gg]; used[i:i + n] = [True] * n
    low = ' '.join(toks)
    for v in found:
        if any(re.search(p, low) for p in L.TITLE_NEGATIVE.get(v, [])):
            continue
        tb.append((wid, 'title', v, 1.0))
TB = pd.DataFrame(tb, columns=['work_id', 'source', 'theme', 'weight'])
TB['node_id'] = TB.theme.map(v2node)
TB = TB[TB.node_id.notna()]
TB['share'] = TB.weight / TB.groupby('work_id').weight.transform('sum')
TBW = rollup(TB, ['title'])
TBW['flag'] = 'backup: title words, use only for a control category with fewer than 50 works'
TBW.to_parquet(f'{OUT}/work_theme_title_backup.parquet', index=False)
print('title backup: works', TB.work_id.nunique(), flush=True)
