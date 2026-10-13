# 14. (v3) Parse every print subject heading (_lcsh.parse_heading) into facet parts, reduce it to its core, and map
# each topical core to a theme value: a hand alias (_review_v3.ALIAS), else the v2 lexicon (same facet rules as v2),
# else the core itself becomes a new theme value. Hand facet decisions for cores are in _review_v3.CORE_FACETS.
# Output (data/db/taxonomy_v3/): headings_parsed.parquet (one row per heading), lcsh_cores.parquet (one row per core),
#                                profile/lcsh_cores_review.csv (cores by number of works, for hand review)
import os
os.environ['TAXO'] = 'v3'
import json, re, collections, numpy as np, pandas as pd
from _common import OUT, OUT_V2
import _lexicon as L
import _lcsh as P
try:
    import _review_v3 as RV3
except ImportError:
    RV3 = None

V2 = pd.read_parquet(f'{OUT_V2}/theme_values.parquet')
v2_values = set(V2.theme)


def canon(s):
    s = str(s).lower().replace('&', ' and ')
    s = re.sub(r"[\-_/\.,:;!\?\(\)\[\]\"’'`+#]+", ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return L.SYNONYMS.get(s, s)


def canon_basic(s):          # like canon() but without v2's genre/form synonyms ('theater' must not become the form 'drama')
    s = str(s).lower().replace('&', ' and ')
    s = re.sub(r"[\-_/\.,:;!\?\(\)\[\]\"’'`+#]+", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


THEME_LEX = {canon_basic(k): v for k, v in L.THEMES.items()}
P.PROTECT |= v2_values | set(THEME_LEX)
H = pd.read_parquet(f'{OUT}/headings.parquet', columns=['heading_id', 'heading', 'n_records', 'n_works'])
parsed = [P.parse_heading(h) for h in H.heading]
H['core'] = [p[0] for p in parsed]; H['kind'] = [p[2] for p in parsed]
H['parts'] = [p[1] for p in parsed]

ALIAS = getattr(RV3, 'ALIAS', {}) if RV3 else {}
CORE_FACETS = getattr(RV3, 'CORE_FACETS', {}) if RV3 else {}


# Library of Congress renames (_review_v3.LC_RENAMES, old form -> new form): a core that starts with the new form takes
# the placement of the matching old-form core ('multiracial people' -> 'racially mixed people', 'multiracial children'
# -> 'racially mixed children'), when that old-form core exists in the data or in the v2 value lists. A new-form core
# with no old counterpart (for example a new place subdivision) keeps its own placement.
LC_RENAMES = getattr(RV3, 'LC_RENAMES', []) if RV3 else []
TOPIC_CORES = set(H.core[H.kind == 'topic'])


def lc_old(core):
    for old, new, *_ in LC_RENAMES:
        if core == new or core.startswith(new + ' '):
            cand = old + core[len(new):]
            if (cand in TOPIC_CORES or cand in CORE_FACETS or cand in ALIAS or canon_basic(cand) in v2_values
                    or canon_basic(cand) in THEME_LEX):
                return cand
    return core


def core_value(core, kind):
    """theme value for a topical core, and how it was found."""
    renamed = lc_old(core)
    if renamed != core:
        v, how = core_value(renamed, kind)
        return v, 'LC rename'
    if core in CORE_FACETS:
        return None, 'hand facets'
    if core in ALIAS:
        return ALIAS[core], 'hand alias'
    c = canon_basic(core)
    if c in v2_values:
        return c, 'v2 value'
    if c in THEME_LEX:
        return THEME_LEX[c], 'v2 lexicon'
    for alt in (c[:-1] if c.endswith('s') else c + 's', re.sub(r'ies$', 'y', c), re.sub(r'y$', 'ies', c)):
        if alt in v2_values:
            return alt, 'v2 value (plural)'
        if alt in THEME_LEX:
            return THEME_LEX[alt], 'v2 lexicon (plural)'
    return c, 'new value'


rows = []
for r in H.itertuples():
    comps = list(r.parts)
    src = ''
    if r.kind == 'topic' and r.core:
        if lc_old(r.core) in CORE_FACETS:
            comps = comps + CORE_FACETS[lc_old(r.core)]; src = 'hand facets'
        else:
            v, src = core_value(r.core, r.kind)
            comps = comps + [('theme', v)]
            comps = [('core_theme', v)] + [c for c in comps if c != ('theme', v)]   # mark the core's own value
    # 'Women -- Violence against' is gender-based violence (close to the sexual and domestic violence control); the same
    # subdivision on other groups ('Gays -- Violence against') is general violence
    if ('theme', 'violence against groups') in comps and re.search(r'(^|\s)(women|woman|wives|girls)$', str(r.core)):
        comps = [('theme', 'violence against women') if c == ('theme', 'violence against groups') else c for c in comps]
    rows.append(json.dumps([[f, v] for f, v in dict.fromkeys(comps)]))
    if src:
        pass
H['components_json'] = rows
H['core_source'] = [('hand facets' if (k == 'topic' and lc_old(c) in CORE_FACETS) else (core_value(c, k)[1] if (k == 'topic' and c) else k)) for c, k in zip(H.core, H.kind)]
H.drop(columns=['parts']).to_parquet(f'{OUT}/headings_parsed.parquet', index=False)

# core table: works per core (a work counts once even if several headings share the core)
wh = pd.read_parquet(f'{OUT}/work_headings.parquet', columns=['work_id', 'heading_id'])
wh = wh.merge(H[['heading_id', 'core', 'kind']], on='heading_id')
C = wh[wh.core != ''].groupby(['core', 'kind']).work_id.nunique().rename('n_works').reset_index()
ex = H[H.core != ''].sort_values('n_works', ascending=False).groupby(['core', 'kind']).heading.apply(lambda s: ' | '.join(s.head(3))).rename('examples')
nh = H[H.core != ''].groupby(['core', 'kind']).size().rename('n_headings')
C = C.join(ex, on=['core', 'kind']).join(nh, on=['core', 'kind'])
vals = [core_value(c, k) if k == 'topic' else (None, k) for c, k in zip(C.core, C.kind)]
C['theme_value'] = [v[0] for v in vals]; C['value_source'] = [v[1] for v in vals]
C['facets_hand'] = C.core.map(lambda c: ' + '.join(f'{f}:{v}' for f, v in CORE_FACETS[lc_old(c)]) if lc_old(c) in CORE_FACETS else '')
C = C.sort_values('n_works', ascending=False).reset_index(drop=True)
C.to_parquet(f'{OUT}/lcsh_cores.parquet', index=False)
os.makedirs(f'{OUT}/profile', exist_ok=True)
C.head(3000).to_csv(f'{OUT}/profile/lcsh_cores_review.csv', index=False)
print('headings', len(H), H.kind.value_counts().to_dict())
print('cores', len(C), C.kind.value_counts().to_dict())
t = C[C.kind == 'topic']
print('topic cores by source (cores / works):', t.groupby('value_source').agg(cores=('core', 'size'), works=('n_works', 'sum')).to_dict('index'))
print('topic cores with >= 3 works', int((t.n_works >= 3).sum()), 'new values with >= 3 works', int(((t.value_source == 'new value') & (t.n_works >= 3)).sum()))

# hand decisions with reasons (aliases, facet decisions, subdivision rules changed by hand)
hd = []
for k, v in ALIAS.items():
    hd.append(dict(kind='alias (core -> value)', item=k, decision=v, reason=getattr(RV3, 'ALIAS_REASON', {}).get(k, 'LCSH wording for an existing value'),
                   n_works=int(C[C.core == k].n_works.sum())))
for k, v in CORE_FACETS.items():
    hd.append(dict(kind='core facet', item=k, decision=' + '.join(f'{f}:{x}' for f, x in v), reason=getattr(RV3, 'FACET_REASON_ITEM', {}).get(k, getattr(RV3, 'FACET_REASON', '')),
                   n_works=int(C[C.core == k].n_works.sum())))
for k, v, why in [('crimes against', 'theme:violent crimes', "'Women Crimes against Fiction' is a crime story with a female victim, not sexual violence; first v3 run sent it to the v2 value violence (control node)"),
                  ('violence against', 'theme:violence against groups (women, wives, girls: violence against women)', 'violence against women is gender-based violence, close to the control; other groups are general violence'),
                  ('ethnic relations', 'theme:ethnic relations', 'LCSH separates Ethnic relations (e.g. Germany, Israel) from Race relations; first v3 run counted it as race relations'),
                  ('race identity', 'theme:race', 'racial identity, kept in race and racism'), ('climate', 'theme:weather', "a place's climate, e.g. 'Seattle Wash Climate'")]:
    hd.append(dict(kind='subdivision rule', item=k, decision=v, reason=why, n_works=int(H[H.heading.str.lower().str.contains(r'\b' + k + r'\b')].n_works.sum())))   # summed over matching headings (a work may count twice)
# LC renames: evidence from the SPL records themselves. A title (same title and creator) "switched" when one of its print
# records carries a heading in the old form and a later record of the same title carries the same heading in the new
# form; the month is the median first month of those later records. Works counted on the new-form cores.
R = pd.read_parquet(f'{OUT}/spl_records.parquet', columns=['record_id', 'format', 'title', 'creator', 'subjects'])
R = R[R['format'].astype(str) == 'BOOK']
fm = pd.read_parquet(f'{OUT}/spl_rows_book.parquet', columns=['record_id', 'year', 'month'])
fm = (fm.year.astype(np.int32) * 100 + fm.month.astype(np.int32)).groupby(fm.record_id).min()
R['first_ym'] = R.record_id.map(fm)
R['key'] = R.title.fillna('') + '||' + R.creator.fillna('')
R['subj'] = ', ' + R.subjects.fillna('').str.lower() + ','
def mm_med(ym):   # median of yyyymm values, taken on a month count so the result is a real month
    k = int(np.median((ym // 100) * 12 + ym % 100 - 1))
    return f'{k // 12}-{k % 12 + 1:02d}'


for old, new, note, *rest in ([(o, n, x, 'core rename') for o, n, x in LC_RENAMES] +
                              [(o, n, x, 'event rename (parser)') for o, n, x in getattr(RV3, 'LC_RENAMES_EVENTS', [])] +
                              [(o, n, x, 'not applied') for o, n, x in getattr(RV3, 'LC_RENAMES_NOT_APPLIED', [])]):
    ro = R[R.subj.str.contains(', ' + re.escape(old) + r'\b', regex=True)]
    rn = R[R.subj.str.contains(', ' + re.escape(new) + r'\b', regex=True)]
    m = ro.groupby('key').first_ym.min().rename('o').to_frame().join(rn.groupby('key').first_ym.min().rename('n'), how='inner')
    sw = m[m.n >= m.o]
    newc = C[(C.kind.isin(['topic', 'event'])) & (C.core.str.match('^' + re.escape(new) + r'(\b|$)'))]
    hd.append(dict(kind=f'LC rename ({rest[0]})', item=f'{old} -> {new}', decision=('new form takes the old form\'s placement' if rest[0] != 'not applied' else 'not applied'),
                   reason=note + f'; SPL evidence: {len(sw)} titles switched from the old to the new form'
                          + (f', median month {mm_med(sw.n)}' if len(sw) else '') + f'; old form on {ro.key.nunique()} titles, new form on {rn.key.nunique()} titles',
                   n_works=int(newc.n_works.sum())))
pd.DataFrame(hd).to_csv(f'{OUT}/profile/hand_decisions.csv', index=False)
print('hand decisions', len(hd))
