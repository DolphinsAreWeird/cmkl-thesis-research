# 08. Quality checks for checkpoint 1: coverage, themes per work, largest and smallest nodes, examples per broad
# node, 20 random works for a human to judge, and suspicious merges (members far apart in meaning).
# Output: data/db/taxonomy_v2/quality/*.csv and quality_summary.json
import os, json, numpy as np, pandas as pd
from _common import OUT, save_json

Q = f'{OUT}/quality'; os.makedirs(Q, exist_ok=True)
W = pd.read_parquet(f'{OUT}/spl_works.parquet', columns=['work_id', 'title', 'creator', 'formats', 'subject_terms', 'checkouts_total',
                                                          'checkouts_audiobook', 'checkouts_ebook', 'first_ym', 'last_ym'])
WT = pd.read_parquet(f'{OUT}/work_theme.parquet'); EV = pd.read_parquet(f'{OUT}/work_theme_value.parquet')
N = pd.read_parquet(f'{OUT}/theme_nodes.parquet'); lab = dict(zip(N.node_id, N.label))
GEN = pd.read_parquet(f'{OUT}/work_genre.parquet'); AUD = pd.read_parquet(f'{OUT}/work_audience_label.parquet')
FORM = pd.read_parquet(f'{OUT}/work_form.parquet'); LINK = pd.read_parquet(f'{OUT}/spl_goodreads_link.parquet')
W['linked_gr'] = W.work_id.isin(LINK.work_id)
W['nonfiction'] = W.subject_terms.map(lambda t: 'Nonfiction' in t or any(x.endswith('(Nonfiction)') for x in t))
W['fiction'] = W.subject_terms.map(lambda t: 'Fiction' in t or any(x.endswith('(Fiction)') or x.endswith(' Fiction') for x in t))
W = W.merge(AUD, on='work_id', how='left')
tot_w, tot_c = len(W), W.checkouts_total.sum()
S = {}


def cover(mask_works, sub=None):
    d = W if sub is None else W[sub]
    m = d.work_id.isin(mask_works)
    return dict(works=int(len(d)), share_works=round(float(m.mean()), 4), share_checkouts=round(float(d[m].checkouts_total.sum() / max(1, d.checkouts_total.sum())), 4),
                share_audiobook_checkouts=round(float(d[m].checkouts_audiobook.sum() / max(1, d.checkouts_audiobook.sum())), 4),
                share_ebook_checkouts=round(float(d[m].checkouts_ebook.sum() / max(1, d.checkouts_ebook.sum())), 4))


rows = []
for name, works in [('any theme (any level)', set(WT.work_id)), ('broad level', set(WT[WT.level == 1].work_id)),
                    ('middle level', set(WT[WT.level == 2].work_id)), ('narrow level', set(WT[WT.level == 3].work_id)),
                    ('theme from SPL terms', set(EV[EV.source == 'spl'].work_id)), ('theme from Goodreads shelves', set(EV[EV.source == 'gr'].work_id)),
                    ('theme from title words', set(EV[EV.source == 'title'].work_id)),
                    ('narrow theme from SPL terms', set(EV[(EV.source == 'spl') & EV.node_id.map(lambda x: x.count('.') == 2)].work_id)),
                    ('narrow theme without title words', set(EV[(EV.source != 'title') & EV.node_id.map(lambda x: x.count('.') == 2)].work_id)),
                    ('any genre', set(GEN.work_id)), ('linked to Goodreads', set(LINK.work_id))]:
    for grp, sub in [('all works', None), ('fiction', W.fiction & ~W.nonfiction), ('nonfiction', W.nonfiction),
                     ('children', W.audience_label == 'children'), ('young adult', W.audience_label == 'young adult')]:
        rows.append(dict(measure=name, group=grp, **cover(works, sub)))
COV = pd.DataFrame(rows); COV.to_csv(f'{Q}/coverage.csv', index=False)
S['coverage_all'] = COV[COV.group == 'all works'].set_index('measure')[['share_works', 'share_checkouts']].to_dict('index')

# themes per work (among works with any theme)
k = WT.groupby(['work_id', 'level']).size().unstack(fill_value=0).reindex(W.work_id, fill_value=0)
tpw = pd.DataFrame({f'level_{l}': k[l].describe(percentiles=[.5, .9]).round(2) for l in [1, 2, 3]})
tpw_cov = pd.DataFrame({f'level_{l}': k[k[l] > 0][l].describe(percentiles=[.5, .9]).round(2) for l in [1, 2, 3]})
dist = pd.DataFrame({f'level_{l}': k[l].clip(upper=6).value_counts().sort_index() for l in [1, 2, 3]}).fillna(0).astype(int)
dist.index = [f'{i}' if i < 6 else '6+' for i in dist.index]
dist.to_csv(f'{Q}/themes_per_work_distribution.csv'); tpw_cov.to_csv(f'{Q}/themes_per_work_among_covered.csv')
S['themes_per_work_among_covered'] = tpw_cov.to_dict()
S['top_strength'] = WT[WT.rank_in_level == 1].groupby('level').strength.describe().round(3).to_dict('index')

# node sizes: works with strength > 0, works where the node is the strongest at its level, strength-weighted checkouts
X = WT.merge(W[['work_id', 'checkouts_total', 'checkouts_audiobook', 'checkouts_ebook']], on='work_id')
X['w_co'] = X.strength * X.checkouts_total
size = X.groupby('node_id').agg(works=('work_id', 'size'), works_top=('rank_in_level', lambda r: int((r == 1).sum())),
                                weighted_checkouts=('w_co', 'sum'), works_from_gr=('s_gr', lambda s: int((s > 0).sum())),
                                works_from_title=('s_title', lambda s: int((s > 0).sum()))).reset_index()
size = N[['node_id', 'level', 'label', 'n_values', 'values']].merge(size, on='node_id', how='left').fillna({'works': 0, 'works_top': 0, 'weighted_checkouts': 0})
size['weighted_checkouts'] = size.weighted_checkouts.round(0)
size['values'] = size['values'].map(lambda v: ' / '.join(list(v)[:6]))
size.to_csv(f'{Q}/node_sizes.csv', index=False)
S['nodes_with_no_works'] = size[size.works == 0].groupby('level').size().to_dict()

# examples per broad node: highest strength-weighted checkouts among works whose top broad theme is this node
ex = []
for b in N[N.level == 1].sort_values('node_id').itertuples():
    x = X[(X.node_id == b.node_id) & (X.rank_in_level == 1)].sort_values('w_co', ascending=False).head(10)
    for r in x.itertuples():
        narrow = WT[(WT.work_id == r.work_id) & (WT.level == 3) & WT.node_id.str.startswith(b.node_id + '.')].sort_values('strength', ascending=False)
        ex.append(dict(broad=f'{b.node_id} {b.label}', work_id=r.work_id, strength=round(r.strength, 2), sources=r.sources, checkouts=int(r.checkouts_total),
                       narrow=' ; '.join(lab[n] for n in narrow.node_id.head(2))))
EX = pd.DataFrame(ex).merge(W[['work_id', 'title', 'creator']], on='work_id'); EX.to_csv(f'{Q}/examples_per_broad.csv', index=False)

# 20 random works (any work with at least one theme), for a human to judge
rng = np.random.RandomState(2026)
pool = W[W.work_id.isin(WT.work_id)]
smp = pool.sample(20, random_state=rng)
rr = []
for r in smp.itertuples():
    t = WT[WT.work_id == r.work_id].sort_values(['level', 'strength'], ascending=[True, False])
    def fmt(l, n=3):
        return ' ; '.join(f'{lab[a]} ({s:.2f})' for a, s in zip(t[t.level == l].node_id.head(n), t[t.level == l].strength.head(n)))
    g = GEN[GEN.work_id == r.work_id].sort_values('strength', ascending=False)
    rr.append(dict(work_id=r.work_id, title=r.title, creator=r.creator, formats=r.formats, checkouts=int(r.checkouts_total),
                   spl_subjects=', '.join(r.subject_terms), goodreads_linked=r.linked_gr, sources=t.sources.iloc[0],
                   broad=fmt(1), middle=fmt(2), narrow=fmt(3), genres=' ; '.join(f'{v} ({s:.2f})' for v, s in zip(g.value.head(4), g.strength.head(4))),
                   audience=r.audience_label, judge_ok='', judge_note=''))
pd.DataFrame(rr).to_csv(f'{Q}/random_20_works_for_review.csv', index=False)

# suspicious merges: the least similar pair of values inside each node, from the embeddings used for clustering
Ec = np.load(f'{OUT}/theme_value_embeddings.npy'); spec = pd.read_parquet(f'{OUT}/_spec_values.parquet')
pos = {t: i for i, t in enumerate(spec.theme)}
sus = []
for r in N[N.level >= 2].itertuples():
    vals = [v for v in r.values if v in pos]
    if len(vals) < 2:
        continue
    M = Ec[[pos[v] for v in vals]] @ Ec[[pos[v] for v in vals]].T
    np.fill_diagonal(M, 9)
    i, j = np.unravel_index(np.argmin(M), M.shape)
    sus.append(dict(node_id=r.node_id, level=r.level, label=r.label, n_values=len(vals), least_similar_pair=f'{vals[i]} <> {vals[j]}',
                    pair_similarity=round(float(M[i, j]), 3), cohesion=round(r.cohesion, 3), values=' / '.join(vals[:10])))
SUS = pd.DataFrame(sus).sort_values('pair_similarity'); SUS.to_csv(f'{Q}/suspicious_merges.csv', index=False)
S['suspicious_counts'] = {'narrow pairs below 0.10': int(((SUS.level == 3) & (SUS.pair_similarity < 0.10)).sum()),
                          'middle pairs below 0.0': int(((SUS.level == 2) & (SUS.pair_similarity < 0.0)).sum())}
save_json(S, f'{Q}/quality_summary.json')
print(COV[COV.group == 'all works'][['measure', 'share_works', 'share_checkouts', 'share_audiobook_checkouts', 'share_ebook_checkouts']].to_string(index=False))
print(COV[COV.measure.isin(['any theme (any level)', 'narrow level'])][['measure', 'group', 'works', 'share_works', 'share_checkouts']].to_string(index=False))
print(dist); print(tpw_cov)
print(size.sort_values('weighted_checkouts', ascending=False).groupby('level').head(5)[['node_id', 'label', 'works', 'works_top', 'weighted_checkouts']].to_string(index=False))
print(SUS.head(25)[['node_id', 'label', 'least_similar_pair', 'pair_similarity']].to_string(index=False))

# samples for checking the two weaker evidence routes by hand
T = EV[EV.source == 'title'].merge(W[['work_id', 'title', 'creator']], on='work_id').sample(50, random_state=11)
T.assign(judge_ok='')[['work_id', 'title', 'creator', 'theme', 'judge_ok']].to_csv(f'{Q}/title_match_sample_50.csv', index=False)
G = pd.read_parquet(f'{OUT}/goodreads_works.parquet', columns=['gr_work_id', 'gr_title', 'author_name', 'year_min'])
LC = LINK[LINK.tier.isin(['C', 'D'])].merge(W[['work_id', 'title', 'creator', 'first_ym']], on='work_id').merge(G, on='gr_work_id').sample(30, random_state=7)
LC.assign(judge_ok='')[['work_id', 'tier', 'title', 'creator', 'first_ym', 'gr_title', 'year_min', 'judge_ok']].to_csv(f'{Q}/goodreads_title_link_sample_30.csv', index=False)
