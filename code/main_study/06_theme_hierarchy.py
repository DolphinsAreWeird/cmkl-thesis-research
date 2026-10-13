# 06. Three-level theme hierarchy from the theme vocabulary (05).
# 1) Specific theme values are embedded with paraphrase-multilingual-MiniLM-L12-v2 (text 'books about <value or
#    hand gloss>', mean-centered, unit length) and clustered with Ward linkage; one tree is cut at three heights
#    (20 / 90 / 260), so the levels nest.
# 2) Hand edits from _labels.py (whole middle nodes moved to another broad node, values joined to another value's
#    narrow node, a few new narrow nodes), all keyed by theme values so they survive reruns.
# 3) Very general values (history, politics, science...) are not clustered: each is attached to the middle node it
#    clearly fits or else to the closest broad node, with hand placements from _labels.GENERAL_PLACE.
# 4) Labels: hand labels for broad and middle nodes (_labels.LABELS, keyed by level and anchor value), otherwise the
#    best-supported member values.
# Output: theme_nodes.parquet, theme_value_node.parquet, profile/hierarchy_edits.csv
import json, numpy as np, pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from _common import OUT, embed
import _labels as LB

K_BROAD, K_MID, K_NARROW = 20, 90, 260
V = pd.read_parquet(f'{OUT}/theme_values.parquet')
V['support'] = V.spl_works.fillna(0) + V.gr_works.fillna(0) + V.wd_works.fillna(0) + V.lv_recordings.fillna(0)
spec = V[~V.general].sort_values('theme').reset_index(drop=True)
gen = V[V.general].sort_values('theme').reset_index(drop=True)
GL = LB.GLOSS
E = embed([f'books about {GL.get(t, t)}' for t in spec.theme])
mu = E.mean(0)
Ec = E - mu; Ec /= np.linalg.norm(Ec, axis=1, keepdims=True)
Z = linkage(Ec, method='ward')
spec['b'] = fcluster(Z, K_BROAD, 'maxclust'); spec['m'] = fcluster(Z, K_MID, 'maxclust') * 1000; spec['n'] = fcluster(Z, K_NARROW, 'maxclust') * 1000
assert spec.groupby('n').m.nunique().max() == 1 and spec.groupby('m').b.nunique().max() == 1
spec['cluster_b'], spec['cluster_m'], spec['cluster_n'] = spec.b, spec.m, spec.n
pos = {t: i for i, t in enumerate(spec.theme)}
edits = []


def row(v):
    if v not in pos:
        raise SystemExit(f'hand edit refers to unknown theme value: {v}')
    return pos[v]


for a, bv in LB.MOVE_MID.items():
    m = spec.at[row(a), 'm']; nb = spec.at[row(bv), 'b']
    spec.loc[spec.m == m, 'b'] = nb
    edits.append(dict(kind='move middle node', what=a, to=f'broad node of "{bv}"', n_values=int((spec.m == m).sum())))
new_id = 1
for vals, host in LB.NEW_NARROW:
    h = row(host)
    for v in vals:
        i = row(v); spec.at[i, 'b'] = spec.at[h, 'b']; spec.at[i, 'm'] = spec.at[h, 'm']; spec.at[i, 'n'] = 10 ** 7 + new_id
    edits.append(dict(kind='new narrow node', what=' / '.join(vals), to=f'middle node of "{host}"', n_values=len(vals)))
    new_id += 1
for a, bv in LB.JOIN.items():
    i, j = row(a), row(bv)
    spec.loc[i, ['b', 'm', 'n']] = spec.loc[j, ['b', 'm', 'n']].values
    edits.append(dict(kind='join value', what=a, to=f'narrow node of "{bv}"', n_values=1))
assert spec.groupby('n').m.nunique().max() == 1 and spec.groupby('m').b.nunique().max() == 1

# renumber: broad nodes by support, middle and narrow nodes by support within their parent
bsup = spec.groupby('b').support.sum().sort_values(ascending=False)
bid = {b: f'B{k + 1:02d}' for k, b in enumerate(bsup.index)}
spec['broad_id'] = spec.b.map(bid)
mid = {}
for b, g in spec.groupby('broad_id'):
    for k, m in enumerate(g.groupby('m').support.sum().sort_values(ascending=False).index):
        mid[m] = f'{b}.M{k + 1:02d}'
spec['mid_id'] = spec.m.map(mid)
nar = {}
for m, g in spec.groupby('mid_id'):
    for k, n in enumerate(g.groupby('n').support.sum().sort_values(ascending=False).index):
        nar[n] = f'{m}.N{k + 1:02d}'
spec['narrow_id'] = spec.n.map(nar)
centroid = {}
for col in ['broad_id', 'mid_id', 'narrow_id']:
    for nid, g in spec.groupby(col):
        c = Ec[g.index].mean(0); centroid[nid] = c / np.linalg.norm(c)

# general values
Eg = embed([f'books about {GL.get(t, t)}' for t in gen.theme]) - mu; Eg /= np.linalg.norm(Eg, axis=1, keepdims=True)
mids = sorted(spec.mid_id.unique()); broads = sorted(spec.broad_id.unique())
Cm = np.vstack([centroid[x] for x in mids]); Cb = np.vstack([centroid[x] for x in broads])
grows = []
for i, t in enumerate(gen.theme):
    sm = Cm @ Eg[i]; sb = Cb @ Eg[i]
    o = np.argsort(-sm); m1 = mids[o[0]]; b1 = m1.split('.')[0]
    other = [sm[j] for j in o[1:] if mids[j].split('.')[0] != b1]
    margin = float(sm[o[0]] - (other[0] if other else -1))
    if t in LB.GENERAL_PLACE:
        lvl, v = LB.GENERAL_PLACE[t]; r = spec.iloc[row(v)]
        node = r.mid_id if lvl == 'mid' else r.broad_id
        grows.append(dict(theme=t, level=2 if lvl == 'mid' else 1, node_id=node, sim=float((centroid[node] @ Eg[i])), margin=margin, placed='hand'))
    elif sm[o[0]] >= 0.55 and margin >= 0.08:
        grows.append(dict(theme=t, level=2, node_id=m1, sim=float(sm[o[0]]), margin=margin, placed='rule'))
    else:
        bb = broads[int(np.argmax(sb))]
        grows.append(dict(theme=t, level=1, node_id=bb, sim=float(sb.max()), margin=margin, placed='rule'))
G = pd.DataFrame(grows)
VN = pd.concat([spec[['theme', 'narrow_id']].rename(columns={'narrow_id': 'node_id'}).assign(level=3, sim=np.nan, margin=np.nan, placed='cluster'),
                G[['theme', 'node_id', 'level', 'sim', 'margin', 'placed']]], ignore_index=True)
VN['moved_by_hand'] = VN.theme.isin(set(LB.JOIN) | {v for vals, _ in LB.NEW_NARROW for v in vals}) | \
    VN.theme.isin(spec[spec.b != spec.cluster_b].theme)


def parent(nid):
    return '.'.join(nid.split('.')[:-1]) or None


rows = []
for lvl, col in [(1, 'broad_id'), (2, 'mid_id'), (3, 'narrow_id')]:
    for nid, g in spec.groupby(col):
        members = g.sort_values(['support', 'theme'], ascending=[False, True]).theme.tolist()
        s = Ec[g.index] @ centroid[nid]
        rows.append(dict(node_id=nid, level=lvl, parent=parent(nid), anchor=members[0], n_values=len(members), values=members,
                         general_values=G[G.node_id == nid].theme.tolist(), support=float(g.support.sum()),
                         auto_label=' / '.join(members[:2] if lvl == 3 else members[:3]), cohesion=float(s.mean()), min_member_sim=float(s.min()),
                         lowest_member=members[int(np.argmin(s))] if len(members) > 1 else None))
N = pd.DataFrame(rows)
N['label'] = [LB.LABELS.get((l, a), al) for l, a, al in zip(N.level, N.anchor, N.auto_label)]
N['label_source'] = np.where(N.label == N.auto_label, 'auto', 'hand')
N.to_parquet(f'{OUT}/theme_nodes.parquet', index=False)
VN.to_parquet(f'{OUT}/theme_value_node.parquet', index=False)
pd.DataFrame(edits).to_csv(f'{OUT}/profile/hierarchy_edits.csv', index=False)
np.save(f'{OUT}/theme_value_embeddings.npy', Ec)
spec[['theme', 'broad_id', 'mid_id', 'narrow_id', 'support', 'cluster_b']].to_parquet(f'{OUT}/_spec_values.parquet', index=False)
print(N.groupby('level').size().to_dict(), 'general attached:', G.groupby(['level', 'placed']).size().to_dict(), 'edits', len(edits))
print('values per narrow node', N[N.level == 3].n_values.describe().round(2).to_dict())
for b in N[N.level == 1].itertuples():
    print(f'\n{b.node_id} [{b.n_values}] {b.label} (anchor: {b.anchor}) | general: {b.general_values}')
    for m in N[(N.level == 2) & (N.parent == b.node_id)].itertuples():
        nar = N[(N.level == 3) & (N.parent == m.node_id)]
        print(f'   {m.node_id} [{m.n_values}] {m.label} (anchor: {m.anchor}) | gen: {m.general_values}')
        print('        ' + ' || '.join(' / '.join(x.values[:5]) for x in nar.itertuples()))
