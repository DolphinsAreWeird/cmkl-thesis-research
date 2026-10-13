# 02. Map GDELT theme codes to taxonomy theme values (and through them to narrow, middle and broad nodes).
# Rule: a code that passed the family rules (01) is mapped to its most similar theme value when the cosine
# (centered taxonomy space, 'books about <text>') is >= SIM_THRESHOLD. Hand verdicts in _gdelt_review.py then
# correct, reassign, add or remove codes. Each code maps to one value, so a code is never counted twice in a node.
# Review sheet: the codes behind the four control categories (all candidates, by similarity and by keyword), the 100
# highest-volume mapped codes, and the two largest codes of every narrow and middle node, each with the hand verdict.
# Outputs: data/db/interest/gdelt/code_map.parquet (final mapping, one row per mapped code)
#          data/db/interest/gdelt/review_gdelt_mappings.csv (review sheet with verdicts)
#          data/db/interest/gdelt/review_todo.csv (codes in the review sets still without a verdict; should be empty)
import re, numpy as np, pandas as pd
from _ci import GD, load_taxonomy, ancestors, save_parquet
import _gdelt_review as RV

SIM_THRESHOLD = 0.70        # chosen after reading similarity bands (report section 2); hand verdicts decide the rest
C = pd.read_parquet(f'{GD}/codes.parquet')
S = np.load(f'{GD}/code_value_cos.npy')
V, N = load_taxonomy()
vals = V.theme.to_numpy(); vnode = dict(zip(V.theme, V.node_id))
label = dict(zip(N.node_id, N.label))
assert S.shape == (len(C), len(V))

# margin to the best value outside the best value's lineage (ancestors and descendants count as the same branch)
def lineage(a, b):
    return a.startswith(b) or b.startswith(a)


top5 = np.argsort(-S, axis=1)[:, :5]
C['top5'] = [' | '.join(f'{vals[j]} {S[i, j]:.2f}' for j in top5[i]) for i in range(len(C))]
marg = []
for i in range(len(C)):
    n1 = vnode[vals[top5[i, 0]]]
    o = np.argsort(-S[i])
    j = next(j for j in o if not lineage(vnode[vals[j]], n1))
    marg.append(S[i, top5[i, 0]] - S[i, j])
C['margin'] = marg

C['auto_value'] = pd.Series([v if ok else None for v, ok in zip(C.v1, (C.rule_excluded == '') & (C.s1 >= SIM_THRESHOLD))], dtype=object)


def _str(x):
    return x if isinstance(x, str) else None

# ---- hand verdicts: single-code verdicts first, then group rules for codes without one ----
REV = dict(RV.REVIEW)
unknown = sorted(c for c in REV if c not in set(C.code))
if unknown:
    print('note: review entries for codes not in this GDELT file (ignored):', unknown)
    for c in unknown:
        REV.pop(c)
for c, (verdict, value, note) in REV.items():
    if verdict not in RV.VERDICTS:
        raise SystemExit(f'unknown verdict {verdict} for {c}')
    if value is not None and value not in vnode:
        raise SystemExit(f'review value {value} for {c} is not a theme value')
auto = {c: _str(a) for c, a in zip(C.code, C.auto_value)}
n_rule = {}
for code in C.code:
    if code in REV:
        continue
    for pat in RV.PATTERNS:
        name, inc, exc, action, value, note = pat[:6]
        only_auto = pat[6] if len(pat) > 6 else None          # rule applies only when the automatic value is one of these
        a = auto.get(code)
        if only_auto is not None and a not in only_auto:
            continue
        if re.search(inc, code) and not (exc and re.search(exc, code)):
            if action == 'map':
                assert value in vnode, value
                verdict = 'correct' if a == value else ('reassign' if a else 'add')
                REV[code] = (verdict, value, f'rule: {name}')
            else:
                REV[code] = ('wrong' if a else 'not mapped', None, f'rule: {name}: {note}')
            n_rule[name] = n_rule.get(name, 0) + 1
            break
print('codes decided by group rules:', n_rule)


def final(row):
    a = _str(row.auto_value)
    r = REV.get(row.code)
    if r is None:
        return a, ('auto' if a else '')
    verdict, value, note = r
    if verdict == 'correct':
        return (a or value), 'hand: correct'
    if verdict in ('reassign', 'add'):
        return value, f'hand: {verdict}'
    if verdict == 'borderline':
        return (value or a), 'hand: borderline, kept'
    return None, f'hand: {verdict}'      # wrong, generic, not a topic, not mapped, excluded ok -> unmapped


res = C.apply(final, axis=1, result_type='expand'); C['value'], C['decided_by'] = res[0], res[1]
# figurative-use check: drivers of GDELT shifts whose rises come from figurative use are dropped
FIG = getattr(RV, 'FIGURATIVE', {})
for c, (fv, note) in FIG.items():
    assert fv in ('figurative', 'literal'), (c, fv)
fig_drop = C.code.map(lambda c: FIG.get(c, (None,))[0] == 'figurative')
C.loc[fig_drop, 'value'] = None
C.loc[fig_drop, 'decided_by'] = 'hand: figurative'
C['figurative_check'] = C.code.map(lambda c: FIG.get(c, (None,))[0])
C['figurative_note'] = C.code.map(lambda c: FIG.get(c, (None, None))[1])
C['node_id'] = C.value.map(vnode)
C['verdict'] = C.code.map(lambda c: REV.get(c, (None,))[0])
C['review_note'] = C.code.map(lambda c: REV.get(c, (None, None, None))[2])
C.loc[fig_drop, 'verdict'] = 'figurative'

M = C[C.value.notna()].copy()
M['narrow_id'] = [n if n.count('.') == 2 else None for n in M.node_id]
M['mid_id'] = [ancestors(n)[-2] if n.count('.') >= 1 else None for n in M.node_id]
M['broad_id'] = [ancestors(n)[-1] for n in M.node_id]
M['node_label'] = M.node_id.map(label)
save_parquet(M[['code', 'text', 'family', 'mentions', 'weeks', 'value', 'node_id', 'narrow_id', 'mid_id', 'broad_id', 'node_label',
                's1', 'v1', 'margin', 'decided_by']], f'{GD}/code_map.parquet')

# ---- review sets ----
CONTROL_NODES = {'B15.M04.N05': 'epidemics and plagues', 'B05.M02.N02': 'race and racism',
                 'B12.M01.N02': 'sexual and domestic violence', 'B09.M07.N02': 'climate change and weather'}
CONTROL_KW = {
    'B15.M04.N05': r'PANDEMIC|EPIDEMIC|CORONAVIRUS|COVID|OUTBREAK|QUARANTIN|PLAGUE|INFLUENZA|_FLU$|_FLU_|SARS|MERS|EBOLA|CONTAGI|INFECTIOUS|VACCIN|IMMUNIZ|SOCIAL_DISTANC|LOCKDOWN|ZIKA|CHOLERA',
    'B05.M02.N02': r'RACIS|_RACE_|_RACE$|RACIAL|DISCRIMINATION|HATE_CRIME|HATE_SPEECH|POLICE_?BRUTALITY|SEGREGATION|CIVIL_RIGHTS|XENOPHOB|WHITE_SUPREMAC|SLAVERY|ETHNICITY_BLACK$|AFRICAN_AMERICAN',
    'B12.M01.N02': r'RAPE|SEXUAL|HARASS|GENDER_VIOLENCE|GENDER_BASED|DOMESTIC_VIOLENCE|DOMESTIC_ABUSE|ASSAULT|ABUSE|VIOLENCE|FEMICIDE|TRAFFICKING|MOLEST',
    'B09.M07.N02': r'CLIMATE|GLOBAL_WARMING|EMISSION|GREENHOUSE|CARBON|WEATHER|HURRICANE|HEATWAVE|HEAT_WAVE|DROUGHT|STORM|FLOOD|WILDFIRE|SEA_LEVEL|POLAR',
}
rows = []
for nid, nm in CONTROL_NODES.items():
    nv = set(V[V.node_id == nid].theme)
    cols = [k for k, v in enumerate(vals) if v in nv]
    sim_hit = (S[:, cols].max(axis=1) >= 0.45) & (np.isin(np.argsort(-S, axis=1)[:, :5], cols).any(axis=1))
    kw_hit = C.code.str.contains(CONTROL_KW[nid], regex=True)
    mapped = C.node_id == nid
    sel = C[(sim_hit & (C.rule_excluded == '')) | kw_hit | mapped | (C.v1.isin(nv) & (C.rule_excluded == ''))]
    for r in sel.itertuples():
        rows.append(dict(review_set=f'control: {nm}', code=r.code))
mapped_auto = C[C.auto_value.notna()].sort_values('mentions', ascending=False)
for r in mapped_auto.head(100).itertuples():
    rows.append(dict(review_set='top 100 mapped by volume', code=r.code))
fin = C[C.value.notna()].copy()
fin['narrow'] = [n if isinstance(n, str) and n.count('.') == 2 else None for n in fin.node_id]
fin['mid'] = [ancestors(n)[-2] if isinstance(n, str) and n.count('.') >= 1 else None for n in fin.node_id]
for col in ['narrow', 'mid']:
    for nid, g in fin[fin[col].notna()].groupby(col):
        for r in g.sort_values('mentions', ascending=False).head(2).itertuples():
            rows.append(dict(review_set=f'largest codes per {col} node', code=r.code))
for c in sorted(FIG):
    rows.append(dict(review_set='figurative check (driver of a GDELT main-set shift)', code=c))
listed = {r['code'] for r in rows}
for c in sorted(REV):                      # every other code with a hand verdict or a group-rule decision
    if c not in listed:
        rows.append(dict(review_set='other codes with a hand verdict or group rule', code=c))
R = pd.DataFrame(rows).groupby('code').review_set.agg(lambda s: '; '.join(dict.fromkeys(s))).reset_index()
R = R.merge(C[['code', 'text', 'family', 'mentions', 'rule_excluded', 'v1', 's1', 'margin', 'top5', 'auto_value', 'verdict', 'value',
               'node_id', 'decided_by', 'review_note', 'figurative_check', 'figurative_note']], on='code', how='left')
R['node_label'] = R.node_id.map(label)
R['auto_node_label'] = R.auto_value.map(vnode).map(label)
R = R.sort_values(['review_set', 'mentions'], ascending=[True, False])
bulk = R.verdict.isna() & R.review_set.str.contains('control') & R.value.isna() & R.auto_value.isna()
R.loc[bulk, 'verdict'] = 'not mapped'
R.loc[bulk, 'review_note'] = np.where(R.loc[bulk, 'rule_excluded'].fillna('') != '', 'excluded by family rule; listed by keyword or similarity, checked',
                                      'listed by keyword or similarity; checked, not about this category')
R.to_csv(f'{GD}/review_gdelt_mappings.csv', index=False)
todo = R[R.verdict.isna() & ((R.rule_excluded == '') | R.review_set.str.contains('control'))]
todo.to_csv(f'{GD}/review_todo.csv', index=False)

# ---- summary ----
print('threshold', SIM_THRESHOLD, '| auto-mapped codes', C.auto_value.notna().sum(), '| final mapped codes', len(M),
      '| share of all mentions mapped', round(M.mentions.sum() / C.mentions.sum(), 3))
print('review sheet rows', len(R), '| without verdict', len(todo))
ver = R[R.review_set.str.contains('top 100')]
print('top-100 verdicts', ver.verdict.value_counts(dropna=False).to_dict())
print('dropped as figurative', int(fig_drop.sum()), sorted(C[fig_drop].code))
print('narrow nodes with GDELT codes', M.narrow_id.nunique(), '| middle', M.mid_id.nunique(), '| broad', M.broad_id.nunique())
