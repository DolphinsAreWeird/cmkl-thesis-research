# 05. Collect theme and genre phrases from the books (SPL subject terms, Goodreads shelves, Wikidata main
# subjects of literary works, LibriVox genres), split each phrase into facet components by rules
# (_lexicon.py) plus hand review (_review.py), and write the phrase table.
# Output: data/db/taxonomy_v2/phrases.parquet (+ phrases_review.csv for reading)
import json, re, ast, collections, numpy as np, pandas as pd
from _common import OUT, D, save_json
import _lexicon as L
try:
    import _review as RV          # hand decisions after reading the rule output (created after the first pass)
except ImportError:
    RV = None

MIN_GR_WORKS = 10            # Goodreads shelves used on fewer works are dropped as noise
AUTHOR_SHARE = 0.6           # shelf mostly on one author's works -> author or series shelf


def canon(s):
    s = str(s).lower().replace('&', ' and ')
    s = re.sub(r"[\-_/\.,:;!\?\(\)\[\]\"’'`+]+", ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return L.SYNONYMS.get(s, s)


# combined surface lexicon for longest-match decomposition
LEX = {}
def add(surface, comps):
    LEX.setdefault(surface, comps)
for k, v in L.GENRE.items(): add(k, v)
for k, v in L.AUDIENCE.items(): add(k, [('audience', v)] + ([('form', L.FORM[k])] if k in L.FORM else []))
for k, v in L.FORM.items(): add(k, [('form', v)])
for k, v in L.PERIOD.items(): add(k, [('period', v)])
for p in L.PLACES: add(p, [('place', L.DEMONYM.get(p, p))])
for k, v in L.DEMONYM.items(): add(k, [('place', v)])
for k, v in L.THEMES.items(): add(k, [('theme', v)])
for k in L.TROPE: add(k, [('other', 'trope')])
for k in L.MOOD: add(k, [('other', 'mood')])
for k in L.FRANCHISE: add(k, [('other', 'franchise')])
for k in L.PUBLISHER: add(k, [('other', 'publisher')])
for k in L.LANGUAGE: add(k, [('other', 'language')])
for k, v in L.SYNONYMS.items():
    if v in LEX and k not in LEX: LEX[k] = LEX[v]
MAXN = max(len(k.split()) for k in LEX)


def decompose(p):
    """Return (components, leftover words, rule)."""
    if RV is not None and p in RV.OVERRIDE:
        return RV.OVERRIDE[p], [], 'review'
    if p in LEX:
        return LEX[p], [], 'lexicon'
    if DECADE_OK(p):
        return [('period', p.replace('the ', ''))], [], 'decade'
    m = L.CENTURY_RE.search(p)
    if m and len(p.split()) <= 4:
        c = m.group(1) or m.group(4)
        if m.group(4):
            n = int(m.group(4)) + 1
        else:
            n = int(c)
        suf = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        rest = L.CENTURY_RE.sub('', p).strip()
        comps = [('period', f'{n}{suf} century')]
        if rest and rest in LEX: comps += LEX[rest]
        return comps, [], 'century'
    if any(r.search(p) for r in L.PERSONAL_RE):
        return [('other', 'personal')], [], 'personal'
    if L.YEARISH_RE.search(p):
        return [('other', 'personal')], [], 'year'
    if L.AWARD_RE.search(p):
        return [('other', 'award_list')], [], 'award'
    m = re.match(r'^(books )?set in (.+)$', p)
    if m:
        q = m.group(2)
        return (LEX.get(q) or [('place', q)]), [], 'set in'
    toks = p.split(); i = 0; comps = []; left = []; run = []
    while i < len(toks):
        for n in range(min(MAXN, len(toks) - i), 0, -1):
            s = ' '.join(toks[i:i + n])
            if s in LEX:
                if run: left.append(' '.join(run)); run = []
                comps += LEX[s]; i += n; break
        else:
            if toks[i] in L.FILLER:
                if run: left.append(' '.join(run)); run = []
            else:
                run.append(toks[i])
            i += 1
    if run: left.append(' '.join(run))
    return comps, left, 'tokens'


def DECADE_OK(p):
    return bool(L.DECADE_RE.match(p))


rows = []
# 1. SPL subject terms
T = pd.read_csv(f'{OUT}/profile/spl_subject_terms.csv')
for t in T.itertuples():
    rows.append(dict(source='spl', raw=t.term, phrase=canon(t.term), spl_works=int(t.n_works), spl_checkouts=int(t.checkouts)))
# 2. Goodreads shelves (work level)
G = pd.read_parquet(f'{OUT}/goodreads_works.parquet', columns=['gr_work_id', 'author_id', 'shelves', 'shelf_counts'])
link = pd.read_parquet(f'{OUT}/spl_goodreads_link.parquet')
linked = set(link.gr_work_id)
sh_works = collections.Counter(); sh_count = collections.Counter(); sh_auth = collections.defaultdict(collections.Counter); sh_linked = collections.Counter()
for wid, a, shs, cs in zip(G.gr_work_id, G.author_id, G.shelves, G.shelf_counts):
    for s, c in zip(shs, cs):
        sh_works[s] += 1; sh_count[s] += int(c); sh_auth[s][a] += 1
        if wid in linked: sh_linked[s] += 1
for s, n in sh_works.items():
    if n < MIN_GR_WORKS:
        continue
    top_share = sh_auth[s].most_common(1)[0][1] / n
    rows.append(dict(source='goodreads', raw=s, phrase=canon(s), gr_works=n, gr_count=sh_count[s], gr_linked_works=sh_linked[s],
                     gr_top_author_share=round(top_share, 3)))
n_small = sum(1 for s, n in sh_works.items() if n < MIN_GR_WORKS)
# 3. Wikidata main subjects of literary works (P921), with Wikipedia short descriptions
WD = json.load(open(f'{D}/raw/wikidata_book_subjects.json')); desc = json.load(open(f'{D}/raw/subject_desc.json'))
for x in WD:
    name = x['art'].replace('_', ' ')
    rows.append(dict(source='wikidata', raw=name, phrase=canon(re.sub(r'\s*\(.*?\)\s*', ' ', name)), wd_works=int(x['n']), wd_qid=x['qid'],
                     wd_desc=desc.get(x['art'], '')))
# 4. LibriVox genre labels
LV = pd.read_csv(f'{D}/raw/librivox_spotify_dataset.csv', usecols=['genres'])
lv = collections.Counter(g['name'] for s in LV.genres.dropna() for g in ast.literal_eval(s))
for g, n in lv.items():
    rows.append(dict(source='librivox', raw=g, phrase=canon(g.lstrip('*')), lv_recordings=int(n)))
P = pd.DataFrame(rows)

# Wikidata rules from the short description (persons, places, periods), applied before the generic rules
PERSON_RE = re.compile(r'\(\d{3,4}\s*[–-]|\bborn\b|philosopher|poet|playwright|novelist|writer|king of|emperor|president of|leader of|'
                       r'dictator|monk|preacher|founder of|mother of|revolutionary|neurologist|saint|apostle|politician|composer', re.I)
PLACE_RE = re.compile(r'^(country|continent|capital|city|archipelago|island|region|state)\b|\bcountry in\b|\bcity (in|of)\b|capital (and|of)|'
                      r'ancient city|archipelago', re.I)


def classify(r):
    p = r.phrase
    if RV is not None and f'{r.source}|{p}' in RV.OVERRIDE:
        return RV.OVERRIDE[f'{r.source}|{p}'], [], 'review'
    if r.source == 'spl':
        return L.SPL_TERMS.get(r.raw, [('other', 'unclassified')]), [], 'spl hand'
    if r.source == 'goodreads' and r.gr_top_author_share >= AUTHOR_SHARE and (RV is None or p not in RV.OVERRIDE) and p not in L.THEMES:
        return [('other', 'author_series')], [], 'author share'
    if r.source == 'wikidata' and (RV is None or p not in RV.OVERRIDE):
        d = r.wd_desc or ''
        if PERSON_RE.search(d):
            return [('other', 'person')], [], 'wd person'
        if PLACE_RE.search(d):
            return [('place', p)], [], 'wd place'
        m = re.match(r'^history of (the )?(.+)$', p)
        if m:
            q = m.group(2); return [('theme', 'history')] + (LEX.get(q) or [('place', q)]), [], 'wd history of'
        m = re.match(r'^(.+?) in the (early |high |late )?middle ages$', p)
        if m:
            q = m.group(1); return (LEX.get(q) or [('place', q)]) + [('period', 'middle ages')], [], 'wd middle ages'
    return decompose(p)


out = [classify(r) for r in P.itertuples()]
P['components'] = [list(dict.fromkeys(o[0])) for o in out]; P['leftover'] = [o[1] for o in out]; P['rule'] = [o[2] for o in out]

# Tail rule for phrases that no rule or hand decision resolved (all are Goodreads shelves used on < 20 works):
# keep as a theme only if it is close in meaning to a theme value already accepted; otherwise 'unclassified'.
from _common import embed
TAIL_SIM = 0.80
unres = [i for i, (c, l) in enumerate(zip(P.components, P.leftover)) if l and not c]
known = sorted({v for c in P.components for f, v in c if f == 'theme'})
tail = []
if unres:
    Ek = embed([f'books about {v}' for v in known])
    Eu = embed([f'books about {P.phrase.iat[i]}' for i in unres])
    S = Eu @ Ek.T
    for k, i in enumerate(unres):
        j = int(S[k].argmax()); sim = float(S[k, j])
        if sim >= TAIL_SIM:
            P.at[P.index[i], 'components'] = [('theme', P.phrase.iat[i])]
            P.at[P.index[i], 'rule'] = f'tail: near "{known[j]}" ({sim:.2f})'
        else:
            P.at[P.index[i], 'components'] = [('other', 'unclassified')]
            P.at[P.index[i], 'rule'] = f'tail: unclassified (nearest "{known[j]}" {sim:.2f})'
        P.at[P.index[i], 'leftover'] = []
        tail.append((P.phrase.iat[i], known[j], round(sim, 3)))
else:
    tail = []
pd.DataFrame(tail, columns=['phrase', 'nearest_theme', 'sim']).sort_values('sim', ascending=False).to_csv(f'{OUT}/profile/phrases_tail_rule.csv', index=False)


def primary(comps, left):
    if left and not comps:
        return 'unresolved'
    order = ['theme', 'genre', 'audience', 'place', 'period', 'form', 'other']
    fs = [f for f, v in comps]
    for f in order:
        if f in fs: return f
    return 'unresolved'


P['facet'] = [primary(c, l) for c, l in zip(P.components, P.leftover)]
P['has_leftover'] = P.leftover.map(len) > 0
P['n_components'] = P.components.map(len)
P['components_str'] = P.components.map(lambda c: ' + '.join(f'{f}:{v}' for f, v in c))
P['leftover_str'] = P.leftover.map(lambda l: ' | '.join(l))
P['reviewed'] = P.rule.isin(['spl hand', 'review'])
P['auto_tail'] = P.rule.str.startswith('tail:')
P.to_pickle(f'{OUT}/_phrases_stage.pkl')
# final phrase table
P['phrase_id'] = np.arange(len(P))
P['components_json'] = P.components.map(lambda c: json.dumps([[f, v] for f, v in c]))
P['theme_values'] = P.components.map(lambda c: [v for f, v in c if f == 'theme'])
P['genre_values'] = P.components.map(lambda c: [v for f, v in c if f == 'genre'])
P['audience_values'] = P.components.map(lambda c: [v for f, v in c if f == 'audience'])
P['other_subtype'] = P.components.map(lambda c: ','.join(sorted({v for f, v in c if f == 'other'})))
keep = ['phrase_id', 'source', 'raw', 'phrase', 'facet', 'components_json', 'components_str', 'theme_values', 'genre_values', 'audience_values',
        'other_subtype', 'leftover_str', 'rule', 'reviewed', 'auto_tail', 'spl_works', 'spl_checkouts', 'gr_works', 'gr_count', 'gr_linked_works',
        'gr_top_author_share', 'wd_qid', 'wd_works', 'wd_desc', 'lv_recordings']
P[keep].to_parquet(f'{OUT}/phrases.parquet', index=False)
# theme vocabulary: one row per canonical theme value, with support from each source
tv = []
for r in P.itertuples():
    for v in r.theme_values:
        tv.append(dict(theme=v, source=r.source, raw=r.raw, spl_works=r.spl_works, gr_works=r.gr_works, wd_works=r.wd_works, lv=r.lv_recordings,
                       reviewed=r.reviewed, auto_tail=r.auto_tail))
TV = pd.DataFrame(tv)
V = TV.groupby('theme').agg(n_phrases=('raw', 'size'), sources=('source', lambda s: ','.join(sorted(set(s)))),
                            spl_works=('spl_works', 'sum'), gr_works=('gr_works', 'sum'), wd_works=('wd_works', 'sum'), lv_recordings=('lv', 'sum'),
                            examples=('raw', lambda s: ' | '.join(list(dict.fromkeys(s))[:6])), any_reviewed=('reviewed', 'max'),
                            only_auto=('auto_tail', 'min')).reset_index()
V['general'] = V.theme.isin(L.GENERAL_THEMES)
V.to_parquet(f'{OUT}/theme_values.parquet', index=False)
print('theme values', len(V), 'general', int(V.general.sum()), 'from tail rule only', int(V.only_auto.sum()))
cols = ['source', 'raw', 'phrase', 'facet', 'components_str', 'leftover_str', 'rule', 'spl_works', 'gr_works', 'gr_linked_works',
        'gr_top_author_share', 'wd_works', 'wd_desc', 'lv_recordings']
P.sort_values(['source', 'gr_works', 'wd_works', 'spl_checkouts'], ascending=[True, False, False, False])[cols].to_csv(f'{OUT}/phrases_review.csv', index=False)
print('phrases', len(P), 'goodreads shelves dropped (<%d works)' % MIN_GR_WORKS, n_small)
print(P.groupby(['source', 'facet']).size().unstack(fill_value=0))
