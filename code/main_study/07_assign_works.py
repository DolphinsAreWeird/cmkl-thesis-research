# 07. Assign every SPL work its themes (with strengths, at all three levels), genres, audience and form.
# Theme evidence, kept per source:
#   spl    the work's SPL subject terms (OverDrive), weighted by the share of its checkouts that carried each term
#   gr     Goodreads shelves of the linked Goodreads work (04), weighted by shelf counts
#   title  theme words in the title or subtitle, nonfiction works only (hand rules in _lexicon.TITLE_*)
# For each source, a work's theme weights are turned into shares (sum 1) and rolled up to parent nodes; the
# combined strength is the mean share over the sources that have any theme evidence for that work.
# Output: work_theme.parquet (work x node), work_theme_value.parquet (work x theme value x source),
#         work_genre.parquet, work_audience.parquet, work_form.parquet
import json, collections, re, numpy as np, pandas as pd
from _common import OUT, norm_text, clean_title
import _lexicon as L

W = pd.read_parquet(f'{OUT}/spl_works.parquet', columns=['work_id', 'title', 'creator', 'subject_terms', 'subject_term_share', 'checkouts_total'])
P = pd.read_parquet(f'{OUT}/phrases.parquet', columns=['source', 'raw', 'components_json'])
comp = {(s, r): [tuple(x) for x in json.loads(c)] for s, r, c in zip(P.source, P.raw, P.components_json)}
VN = pd.read_parquet(f'{OUT}/theme_value_node.parquet')
v2node = dict(zip(VN.theme, VN.node_id))
N = pd.read_parquet(f'{OUT}/theme_nodes.parquet')
level = dict(zip(N.node_id, N.level))


def ancestors(nid):
    p = nid.split('.')
    return ['.'.join(p[:k]) for k in range(1, len(p) + 1)]


# ---------- evidence ----------
ev = []          # (work_id, source, value, weight)
cat = []         # (work_id, source, facet, value, weight) for genre / audience / form
for wid, terms, shares in zip(W.work_id, W.subject_terms, W.subject_term_share):
    for t, s in zip(terms, shares):
        cs = comp.get(('spl', t), [])
        th = [v for f, v in cs if f == 'theme']
        for v in th:
            ev.append((wid, 'spl', v, float(s) / len(th)))
        for f, v in cs:
            if f in ('genre', 'audience', 'form'):
                cat.append((wid, 'spl', f, v, float(s)))
link = pd.read_parquet(f'{OUT}/spl_goodreads_link.parquet')
G = pd.read_parquet(f'{OUT}/goodreads_works.parquet', columns=['gr_work_id', 'shelves', 'shelf_counts', 'gr_genres'])
G = G.merge(link, on='gr_work_id')
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
# title surfaces: specific theme values, their single-value source phrases, lexicon synonyms, and TITLE_SURFACES
spec_vals = set(VN[VN.level == 3].theme)
surf = collections.defaultdict(set)
for (s, r), cs in comp.items():
    th = [v for f, v in cs if f == 'theme']
    if len(th) == 1 and th[0] in spec_vals and s in ('goodreads', 'wikidata', 'spl'):
        surf[norm_text(r.replace('-', ' '))].add(th[0])
for k, v in L.THEMES.items():
    if v in spec_vals:
        surf[norm_text(k)].add(v)
for v in spec_vals:
    surf[norm_text(v)].add(v)
for v, forms in L.TITLE_SURFACES.items():
    for f in forms:
        surf[norm_text(f)].add(v)
hand_forms = {norm_text(f) for fs in L.TITLE_SURFACES.values() for f in fs}


def keep_surface(k, vals):
    if not k or k.startswith('the ') or k.startswith('a '):
        return False
    if k in hand_forms:
        return True
    if len(k.split()) >= 2:
        return True
    # single words: only the theme value itself, long enough and not a word titles use loosely
    return len(k) >= 5 and k not in L.TITLE_STOP and k in vals


surf = {k: v for k, v in surf.items() if keep_surface(k, v)}
pd.DataFrame([(k, ' | '.join(sorted(v))) for k, v in sorted(surf.items())], columns=['surface', 'theme_values']).to_csv(f'{OUT}/profile/title_surfaces.csv', index=False)
# nonfiction = any SPL term naming nonfiction ('Nonfiction', 'Juvenile Nonfiction', 'Young Adult Nonfiction', 'Humor (Nonfiction)'...)
nonfic = {wid for wid, terms in zip(W.work_id, W.subject_terms) if any('Nonfiction' in t for t in terms)}
title_hits = []
for wid, t in zip(W.work_id, W.title):
    if wid not in nonfic:
        continue
    toks = norm_text(clean_title(t)).split()
    found = set(); used = [False] * len(toks)
    for n in range(4, 0, -1):                       # longest phrase first; its words cannot match again
        for i in range(len(toks) - n + 1):
            if any(used[i:i + n]):
                continue
            g = ' '.join(toks[i:i + n])
            if g in surf:
                found |= surf[g]; used[i:i + n] = [True] * n
    low = ' '.join(toks)
    for v in found:
        if any(re.search(pat, low) for pat in L.TITLE_NEGATIVE.get(v, [])):
            continue
        ev.append((wid, 'title', v, 1.0)); title_hits.append((wid, v))
EV = pd.DataFrame(ev, columns=['work_id', 'source', 'theme', 'weight'])
EV = EV[EV.theme.isin(v2node)]                     # every theme value has a node; guard anyway
EV = EV.groupby(['work_id', 'source', 'theme'], as_index=False).weight.sum()
EV['node_id'] = EV.theme.map(v2node)
EV.to_parquet(f'{OUT}/work_theme_value.parquet', index=False)

# ---------- shares per source, rolled up, then averaged ----------
EV['share'] = EV.weight / EV.groupby(['work_id', 'source']).weight.transform('sum')
rows = []
for anc_level in [1, 2, 3]:
    tmp = EV[EV.node_id.map(lambda x: level[x] >= anc_level)].copy()
    tmp['anc'] = tmp.node_id.map(lambda x: ancestors(x)[anc_level - 1])
    rows.append(tmp.groupby(['work_id', 'source', 'anc'], as_index=False).share.sum().assign(level=anc_level))
S = pd.concat(rows).rename(columns={'anc': 'node_id'})
wide = S.pivot_table(index=['work_id', 'node_id', 'level'], columns='source', values='share', fill_value=0.0).reset_index()
for c in ['spl', 'gr', 'title']:
    if c not in wide: wide[c] = 0.0
nsrc = EV.groupby('work_id').source.nunique()
has = EV.groupby(['work_id', 'source']).size().unstack(fill_value=0) > 0
for c in ['spl', 'gr', 'title']:
    if c not in has: has[c] = False
wide = wide.merge(has.rename(columns=lambda c: f'has_{c}').reset_index(), on='work_id')
den = wide[['has_spl', 'has_gr', 'has_title']].sum(axis=1)
wide['strength'] = (wide.spl * wide.has_spl + wide.gr * wide.has_gr + wide.title * wide.has_title) / den
wide = wide.rename(columns={'spl': 's_spl', 'gr': 's_gr', 'title': 's_title'})
wide['sources'] = [','.join(s for s, h in zip(['spl', 'gr', 'title'], hs) if h) for hs in wide[['has_spl', 'has_gr', 'has_title']].values]
WT = wide[['work_id', 'node_id', 'level', 'strength', 's_spl', 's_gr', 's_title', 'sources']].copy()
WT['rank_in_level'] = WT.groupby(['work_id', 'level']).strength.rank(ascending=False, method='first').astype(int)
WT.to_parquet(f'{OUT}/work_theme.parquet', index=False)

# ---------- genres, audience, form ----------
C = pd.DataFrame(cat, columns=['work_id', 'source', 'facet', 'value', 'weight']).groupby(['work_id', 'source', 'facet', 'value'], as_index=False).weight.sum()
# Goodreads shelves such as 'historical' or 'mystery' on a nonfiction book describe its subject, not a fiction genre
FICTION_GENRES = {'historical fiction', 'mystery', 'cozy mystery', 'thriller', 'psychological thriller', 'legal thriller', 'political thriller',
                  'suspense', 'romance', 'contemporary romance', 'historical romance', 'paranormal romance', 'erotic romance', 'romantic comedy',
                  'fantasy', 'epic fantasy', 'urban fantasy', 'dark fantasy', 'science fiction', 'space opera', 'dystopian', 'post-apocalyptic',
                  'horror', 'gothic', 'literary fiction', 'general fiction', 'contemporary fiction', 'chick lit', 'womens fiction', 'western',
                  'christian fiction', 'urban fiction', 'war fiction', 'spy fiction', 'crime', 'adventure', 'action', 'magical realism', 'paranormal'}
C = C[~((C.source == 'gr') & (C.facet == 'genre') & C.value.isin(FICTION_GENRES) & C.work_id.isin(nonfic))]
C['share'] = C.weight / C.groupby(['work_id', 'source', 'facet']).weight.transform('sum')
for facet, fn in [('genre', 'work_genre'), ('audience', 'work_audience'), ('form', 'work_form')]:
    c = C[C.facet == facet]
    wd = c.pivot_table(index=['work_id', 'value'], columns='source', values='share', fill_value=0.0).reset_index()
    for s in ['spl', 'gr']:
        if s not in wd: wd[s] = 0.0
    hs = c.groupby(['work_id', 'source']).size().unstack(fill_value=0) > 0
    for s in ['spl', 'gr']:
        if s not in hs: hs[s] = False
    wd = wd.merge(hs.rename(columns=lambda s: f'has_{s}').reset_index(), on='work_id')
    wd['strength'] = (wd.spl * wd.has_spl + wd.gr * wd.has_gr) / (wd.has_spl.astype(int) + wd.has_gr.astype(int))
    wd = wd.rename(columns={'spl': 's_spl', 'gr': 's_gr'})
    if facet == 'genre':      # Goodreads genre shelves are noisy in the tail; keep values with at least 5% of a source
        wd = wd[(wd.s_spl > 0) | (wd.s_gr >= 0.05)]
    wd[['work_id', 'value', 'strength', 's_spl', 's_gr']].to_parquet(f'{OUT}/{fn}.parquet', index=False)
# audience label per work: SPL first (it is the library's own catalogue), Goodreads only when SPL says nothing
A = pd.read_parquet(f'{OUT}/work_audience.parquet')
lab = A[A.s_spl > 0].sort_values('s_spl', ascending=False).drop_duplicates('work_id').set_index('work_id').value
lab2 = A[A.s_gr > 0].sort_values('s_gr', ascending=False).drop_duplicates('work_id').set_index('work_id').value
aud = pd.Series('adult (default)', index=W.work_id)
aud.loc[lab2.index.intersection(aud.index)] = lab2
aud.loc[lab.index] = lab
pd.DataFrame({'work_id': aud.index, 'audience_label': aud.values}).to_parquet(f'{OUT}/work_audience_label.parquet', index=False)
print('evidence rows', len(EV), EV.groupby('source').work_id.nunique().to_dict())
print('work-theme rows', len(WT), WT.groupby('level').work_id.nunique().to_dict())
print('title hits', len(title_hits), 'works', len({w for w, v in title_hits}))
print(pd.Series([v for w, v in title_hits]).value_counts().head(30).to_dict())
