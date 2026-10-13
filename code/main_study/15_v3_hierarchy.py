# 15. (v3) Keep the approved v2 tree fixed (19 broad, 86 middle and 241 narrow nodes, ids and labels unchanged) and
# place every new theme value from the print headings into it:
#   1. hand placement (_review_v3.VALUE_PLACE): join the narrow node of a named v2 value, attach to the middle node of a
#      named v2 value, or go into a new narrow node defined in _review_v3.NEW_NARROW_V3;
#   2. otherwise the nearest existing narrow node by embedding (same model, text and centering as v2), if the similarity
#      reaches the calibrated threshold; else the nearest middle node if that reaches its threshold; else unplaced.
# New narrow nodes are only created by hand, under an existing middle node, with the next free id.
# Output (data/db/taxonomy_v3/): theme_nodes.parquet, theme_value_node.parquet, theme_values.parquet,
#   profile/placement_log.csv (every new value: node, method, similarity, reason), profile/new_nodes.csv,
#   profile/placement_calibration.json, profile/placement_review.csv
import os
os.environ['TAXO'] = 'v3'
import json, numpy as np, pandas as pd
from _common import OUT, OUT_V2, embed, save_json
import _labels as LB
try:
    import _review_v3 as RV3
except ImportError:
    RV3 = None

MIN_WORKS = 3          # new values on fewer works are kept in the data but not placed
N2 = pd.read_parquet(f'{OUT_V2}/theme_nodes.parquet')
VN2 = pd.read_parquet(f'{OUT_V2}/theme_value_node.parquet')
SP2 = pd.read_parquet(f'{OUT_V2}/_spec_values.parquet')          # v2 specific values with their final narrow node
V2 = pd.read_parquet(f'{OUT_V2}/theme_values.parquet')
GL = dict(LB.GLOSS); GL.update(getattr(RV3, 'GLOSS', {}) if RV3 else {})

# ---------- v2 embedding space (same text, glosses and centering as 06) ----------
spec_all = V2[~V2.general].sort_values('theme').reset_index(drop=True)
E = embed([f'books about {LB.GLOSS.get(t, t)}' for t in spec_all.theme])
mu = E.mean(0)
Ec = E - mu; Ec /= np.linalg.norm(Ec, axis=1, keepdims=True)
pos = {t: i for i, t in enumerate(spec_all.theme)}
SP2 = SP2[SP2.theme.isin(pos)]
nar_ids = sorted(SP2.narrow_id.unique()); mid_ids = sorted(SP2.mid_id.unique())
def centroid(idx):
    c = Ec[idx].mean(0); return c / np.linalg.norm(c)
NC = np.vstack([centroid([pos[t] for t in SP2[SP2.narrow_id == n].theme]) for n in nar_ids])
MC = np.vstack([centroid([pos[t] for t in SP2[SP2.mid_id == m].theme]) for m in mid_ids])

# ---------- calibration on v2 values: leave-one-out nearest narrow and middle node ----------
cal = []
for t, nid, mid in zip(SP2.theme, SP2.narrow_id, SP2.mid_id):
    i = pos[t]
    members = [pos[x] for x in SP2[SP2.narrow_id == nid].theme if x != t]
    nc = NC.copy()
    if members:
        nc[nar_ids.index(nid)] = centroid(members)
    else:
        nc[nar_ids.index(nid)] = -1e9
    s = nc @ Ec[i]; j = int(np.argmax(s))
    mm = [pos[x] for x in SP2[SP2.mid_id == mid].theme if x != t]
    mc = MC.copy(); mc[mid_ids.index(mid)] = centroid(mm) if mm else -1e9
    sm = mc @ Ec[i]; k = int(np.argmax(sm))
    cal.append(dict(theme=t, best_narrow_sim=float(s[j]), narrow_ok=nar_ids[j] == nid, best_mid_sim=float(sm[k]), mid_ok=mid_ids[k] == mid))
CAL = pd.DataFrame(cal)
calib = {}
for col, ok in [('best_narrow_sim', 'narrow_ok'), ('best_mid_sim', 'mid_ok')]:
    rows = []
    for th in np.arange(0.30, 0.80, 0.05):
        x = CAL[CAL[col] >= th]
        rows.append(dict(threshold=round(float(th), 2), share_above=round(len(x) / len(CAL), 3), precision=round(float(x[ok].mean()) if len(x) else np.nan, 3)))
    calib[col] = rows
calib['loo_accuracy_narrow'] = float(CAL.narrow_ok.mean()); calib['loo_accuracy_middle'] = float(CAL.mid_ok.mean())
# thresholds: lowest similarity at which leave-one-out precision reaches 0.75 (narrow) and 0.80 (middle)
def pick(col, target):
    for r in calib[col]:
        if not np.isnan(r['precision']) and r['precision'] >= target:
            return r['threshold']
    return 0.75
# The leave-one-out check above is optimistic (the v2 values were clustered in this same space). The thresholds used are
# set from hand judgments of 25 random new values per similarity band (13 Oct 2026): placements judged correct were
# 6/25 at 0.30-0.40, 6/25 at 0.40-0.50, 21/25 at 0.50-0.60, 22/25 at 0.60-0.70 and 24/25 at 0.70 and above.
# Below 0.50 a value is left unplaced unless placed by hand (no middle-level fallback: that band is mostly wrong too).
calib['hand_judged_bands'] = {'0.30-0.40': '6/25', '0.40-0.50': '6/25', '0.50-0.60': '21/25', '0.60-0.70': '22/25', '0.70+': '24/25'}
TAU_N = 0.50; TAU_M = 9.0
calib['tau_narrow'] = TAU_N; calib['tau_middle'] = 'not used'
os.makedirs(f'{OUT}/profile', exist_ok=True)
save_json(calib, f'{OUT}/profile/placement_calibration.json')
print('leave-one-out accuracy narrow %.3f middle %.3f; threshold narrow %.2f (hand-judged)' % (calib['loo_accuracy_narrow'], calib['loo_accuracy_middle'], TAU_N), flush=True)

# ---------- new values and their work counts ----------
HP = pd.read_parquet(f'{OUT}/headings_parsed.parquet', columns=['heading_id', 'components_json'])
hv = []
for hid, cj in zip(HP.heading_id, HP.components_json):
    for f, v in json.loads(cj):
        if f in ('theme', 'core_theme') and v:
            hv.append((hid, v))
HV = pd.DataFrame(hv, columns=['heading_id', 'theme']).drop_duplicates()
WH = pd.read_parquet(f'{OUT}/work_headings.parquet', columns=['work_id', 'heading_id'])
cnt = WH.merge(HV, on='heading_id').groupby('theme').work_id.nunique()
v2_node = dict(zip(VN2.theme, VN2.node_id)); v2_level = dict(zip(VN2.theme, VN2.level))
new_vals = sorted(set(cnt.index) - set(v2_node))
NV = pd.DataFrame({'theme': new_vals}); NV['n_works'] = NV.theme.map(cnt).astype(int)
NV = NV.sort_values(['n_works', 'theme'], ascending=[False, True]).reset_index(drop=True)
todo = NV[NV.n_works >= MIN_WORKS].copy()
Eq = embed([f'books about {GL.get(t, t)}' for t in todo.theme]) - mu
Eq /= np.linalg.norm(Eq, axis=1, keepdims=True)
Sn = Eq @ NC.T; Sm = Eq @ MC.T
o = np.argsort(-Sn, axis=1)
todo['narrow_1'] = [nar_ids[i] for i in o[:, 0]]; todo['sim_1'] = Sn[np.arange(len(todo)), o[:, 0]]
todo['narrow_2'] = [nar_ids[i] for i in o[:, 1]]; todo['sim_2'] = Sn[np.arange(len(todo)), o[:, 1]]
km = np.argmax(Sm, axis=1); todo['middle_1'] = [mid_ids[i] for i in km]; todo['mid_sim'] = Sm[np.arange(len(todo)), km]

# ---------- new narrow nodes (hand) ----------
nodes = N2.copy(); nodes['added_in'] = 'v2'
lab = dict(zip(N2.node_id, N2.label))
NEWN = getattr(RV3, 'NEW_NARROW_V3', {}) if RV3 else {}
new_node_rows = []; new_node_id = {}
for key, (label, mid_anchor, reason) in NEWN.items():
    mid = v2_node[mid_anchor] if v2_level.get(mid_anchor) == 2 else SP2.set_index('theme').mid_id.get(mid_anchor)
    if mid is None:
        raise SystemExit(f'new node {key}: unknown middle anchor {mid_anchor}')
    k = max(int(n.split('.N')[1]) for n in nodes[nodes.parent == mid].node_id) + 1
    nid = f'{mid}.N{k:02d}'
    new_node_id[key] = nid
    nodes = pd.concat([nodes, pd.DataFrame([dict(node_id=nid, level=3, parent=mid, anchor=key, n_values=0, values=[], general_values=[], support=0.0,
                                                  auto_label=label, label=label, label_source='hand', added_in='v3')])], ignore_index=True)
    new_node_rows.append(dict(node_id=nid, label=label, parent=mid, parent_label=lab[mid], reason=reason))
lab.update({v: NEWN[k][0] for k, v in new_node_id.items()})

# ---------- placement ----------
import re
VP = dict(getattr(RV3, 'VALUE_PLACE', {}) if RV3 else {})
RULES = getattr(RV3, 'PLACE_RULES', []) if RV3 else []
rule_hit = {}
for t in NV.theme:
    if t in VP:
        continue
    for pat, kind, target, reason in RULES:
        if re.search(pat, t):
            rule_hit[t] = (kind, target, reason); break
log = []
for r in NV.itertuples():
    t = r.theme
    rec = dict(theme=t, n_works=int(r.n_works))
    if t in VP or t in rule_hit:
        kind, target, reason = VP.get(t) or rule_hit[t]
        if kind == 'join':
            node = v2_node.get(target) or (new_node_id.get(target))
            lvl = v2_level.get(target, 3)
        elif kind == 'mid':
            node = v2_node[target] if v2_level.get(target) == 2 else SP2.set_index('theme').mid_id[target]; lvl = 2
        elif kind == 'new':
            node = new_node_id[target]; lvl = 3
        elif kind == 'broad':
            node = (v2_node[target] if v2_level.get(target) == 1 else SP2.set_index('theme').broad_id[target]); lvl = 1
        elif kind == 'none':
            node, lvl = None, None
        rec.update(node_id=node, level=lvl, method='hand' if t in VP else 'hand rule (pattern)', reason=reason)
    elif r.n_works >= MIN_WORKS:
        x = todo[todo.theme == t].iloc[0]
        rec.update(sim=round(float(x.sim_1), 3), second=f'{x.narrow_2} {lab[x.narrow_2]} ({x.sim_2:.2f})', mid_sim=round(float(x.mid_sim), 3))
        control_nodes = {v2_node[a] for a in getattr(RV3, 'CONTROL_ANCHORS', [])} if RV3 else set()
        if x.sim_1 >= TAU_N and x.narrow_1 in control_nodes:
            rec.update(node_id=None, level=None, method='unplaced', reason=f'nearest node is a control node ({lab[x.narrow_1]}, {x.sim_1:.2f}); control nodes take hand rules only')
        elif x.sim_1 >= TAU_N:
            rec.update(node_id=x.narrow_1, level=3, method='embedding: narrow', reason=f'nearest narrow node, similarity {x.sim_1:.2f} >= {TAU_N}')
        elif x.mid_sim >= TAU_M:
            rec.update(node_id=x.middle_1, level=2, method='embedding: middle', reason=f'no narrow node above {TAU_N}; nearest middle node {x.mid_sim:.2f} >= {TAU_M}')
        else:
            rec.update(node_id=None, level=None, method='unplaced', reason=f'best narrow {x.sim_1:.2f}, best middle {x.mid_sim:.2f}: below thresholds')
    else:
        rec.update(node_id=None, level=None, method='unplaced (rare)', reason=f'fewer than {MIN_WORKS} works')
    rec['node_label'] = lab.get(rec['node_id'], '') if rec.get('node_id') else ''
    log.append(rec)
LOG = pd.DataFrame(log)
LOG.to_csv(f'{OUT}/profile/placement_log.csv', index=False)
pd.DataFrame(new_node_rows).to_csv(f'{OUT}/profile/new_nodes.csv', index=False)
rv = todo.copy(); rv['label_1'] = rv.narrow_1.map(lab); rv['label_2'] = rv.narrow_2.map(lab); rv['mid_label'] = rv.middle_1.map(lab)
rv['hand'] = rv.theme.isin(VP)
rv.head(2500).to_csv(f'{OUT}/profile/placement_review.csv', index=False)

# ---------- outputs: nodes and value -> node over all values ----------
VN3 = pd.concat([VN2.assign(source='v2', method='v2'),
                 LOG[LOG.node_id.notna()][['theme', 'node_id', 'level', 'method']].assign(source='print headings', placed='v3')], ignore_index=True)
VN3['level'] = VN3.level.astype(int)
VN3.to_parquet(f'{OUT}/theme_value_node.parquet', index=False)
memb = VN3[VN3.level == 3].groupby('node_id').theme.apply(list)
nodes['values_v3'] = nodes.node_id.map(memb)
nodes['n_values_v3'] = nodes.values_v3.map(lambda x: len(x) if isinstance(x, list) else 0)
nodes.to_parquet(f'{OUT}/theme_nodes.parquet', index=False)
TV = pd.concat([V2.assign(source='v2'), NV.assign(source='print headings')], ignore_index=True)
TV.to_parquet(f'{OUT}/theme_values.parquet', index=False)
print('new values', len(NV), 'with >=', MIN_WORKS, 'works:', len(todo))
print(LOG.method.value_counts().to_dict())
print('works covered by placed new values (sum over values):', int(LOG[LOG.node_id.notna()].n_works.sum()), 'unplaced:', int(LOG[LOG.node_id.isna()].n_works.sum()))
print('nodes', nodes.groupby(['level', 'added_in']).size().to_dict())
