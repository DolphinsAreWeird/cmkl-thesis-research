# 04. Candidate English Wikipedia concept articles for every theme value, through the official Wikidata API.
# For each value: wbsearchentities on the value and on its gloss (the hand description used for the taxonomy
# embeddings), then labels, descriptions and the enwiki sitelink of every candidate (wbgetentities), and the
# 'instance of' (P31) classes from the Wikidata query service. Candidates that are people, works (books, films,
# albums...), lists, disambiguation pages, names or organisations are marked as unsuitable. The first suitable
# candidate of the bare-value search is the automatic pick; the hand choices in _wiki_choices.py are applied in 05.
# All API answers are cached in data/db/interest/wiki/_*.json, so the script resumes after a restart.
# Output: data/db/interest/wiki/candidates.parquet
import json, os, pandas as pd
from _ci import load_taxonomy, polite_get, save_json, save_parquet, WK
import _labels as LB

API = 'https://www.wikidata.org/w/api.php'
SPARQL = 'https://query.wikidata.org/sparql'
BAD_P31 = {
    'Q4167410': 'disambiguation page', 'Q5': 'human', 'Q13406463': 'list article', 'Q4167836': 'category', 'Q11266439': 'template',
    'Q101352': 'family name', 'Q202444': 'given name', 'Q12308941': 'male given name', 'Q11879590': 'female given name',
    'Q3409032': 'unisex given name', 'Q11424': 'film', 'Q7725634': 'literary work', 'Q571': 'book', 'Q47461344': 'written work',
    'Q8261': 'novel', 'Q482994': 'album', 'Q134556': 'single', 'Q7366': 'song', 'Q105543609': 'musical work', 'Q215380': 'musical group',
    'Q5741069': 'rock band', 'Q5398426': 'TV series', 'Q15416': 'TV program', 'Q21191270': 'TV episode', 'Q7889': 'video game',
    'Q41298': 'magazine', 'Q1002697': 'periodical', 'Q3305213': 'painting', 'Q4830453': 'business', 'Q6881511': 'enterprise',
    'Q18127': 'record label', 'Q13442814': 'scholarly article', 'Q95074': 'fictional character', 'Q1667921': 'novel series',
    'Q24856': 'film series', 'Q14406742': 'comic book series', 'Q1004': 'comics', 'Q838948': 'work of art', 'Q17537576': 'creative work',
    'Q22808320': 'disambiguation page (human name)', 'Q15184295': 'Wikimedia module', 'Q43229': 'organization', 'Q163740': 'nonprofit',
    'Q2085381': 'publisher', 'Q169930': 'extended play', 'Q208569': 'studio album', 'Q1259759': 'miniseries', 'Q24862': 'short film',
    'Q506240': 'television film', 'Q25379': 'play', 'Q7777570': 'theatrical genre?', 'Q19389637': 'biographical article',
    'Q3331189': 'version, edition or translation', 'Q1371849': 'season', 'Q63952888': 'anime TV series', 'Q182832': 'concert tour?',
}
BAD_P31.pop('Q7777570'); BAD_P31.pop('Q182832'); BAD_P31.pop('Q1371849')   # keep only clear-cut classes

V, _ = load_taxonomy()
f_search, f_ent, f_p31 = f'{WK}/_search_cache.json', f'{WK}/_entity_cache.json', f'{WK}/_p31_cache.json'
search = json.load(open(f_search)) if os.path.exists(f_search) else {}
ent = json.load(open(f_ent)) if os.path.exists(f_ent) else {}
p31 = json.load(open(f_p31)) if os.path.exists(f_p31) else {}

queries = []
for t in V.theme:
    queries.append((t, 'value', t, 10))
    g = LB.GLOSS.get(t)
    if g and g != t:
        queries.append((t, 'gloss', g, 5))
todo = [q for q in queries if q[2] not in search]
print('searches to run', len(todo), 'of', len(queries), flush=True)
for i, (t, kind, q, lim) in enumerate(todo):
    r = polite_get(API, dict(action='wbsearchentities', search=q, language='en', uselang='en', type='item', limit=lim, format='json'))
    if r is not None and r.status_code == 200:
        search[q] = [dict(qid=x['id'], label=x.get('label'), desc=x.get('description'), match=x.get('match', {}).get('text'))
                     for x in r.json().get('search', [])]
    if (i + 1) % 50 == 0:
        save_json(search, f_search); print('search', i + 1, flush=True)
save_json(search, f_search)

qids = sorted({c['qid'] for q in queries for c in search.get(q[2], [])})
todo = [q for q in qids if q not in ent]
print('entities to fetch', len(todo), flush=True)
for i in range(0, len(todo), 50):
    b = todo[i:i + 50]
    r = polite_get(API, dict(action='wbgetentities', ids='|'.join(b), props='labels|descriptions|sitelinks', languages='en',
                             sitefilter='enwiki', format='json'))
    if r is None or r.status_code != 200:
        continue
    for q, e in r.json().get('entities', {}).items():
        ent[q] = dict(label=e.get('labels', {}).get('en', {}).get('value'), desc=e.get('descriptions', {}).get('en', {}).get('value'),
                      enwiki=e.get('sitelinks', {}).get('enwiki', {}).get('title'))
    save_json(ent, f_ent)

todo = [q for q in qids if q not in p31]
print('P31 lookups', len(todo), flush=True)
for i in range(0, len(todo), 150):
    b = todo[i:i + 150]
    sp = 'SELECT ?item ?c WHERE { VALUES ?item { %s } ?item wdt:P31 ?c }' % ' '.join('wd:' + q for q in b)
    r = polite_get(SPARQL, dict(query=sp, format='json'), min_gap=1.5, timeout=90)
    if r is None or r.status_code != 200:
        continue
    got = {q: [] for q in b}
    for row in r.json()['results']['bindings']:
        got[row['item']['value'].rsplit('/', 1)[1]].append(row['c']['value'].rsplit('/', 1)[1])
    p31.update(got); save_json(p31, f_p31)

rows = []
for t, kind, q, lim in queries:
    for rank, c in enumerate(search.get(q, [])):
        e = ent.get(c['qid'], {})
        cls = p31.get(c['qid'], [])
        bad = [BAD_P31[x] for x in cls if x in BAD_P31]
        rows.append(dict(theme=t, query_kind=kind, query=q, rank=rank, qid=c['qid'], label=e.get('label') or c['label'],
                         desc=e.get('desc') or c['desc'], enwiki=e.get('enwiki'), p31=','.join(cls), unsuitable=', '.join(bad)))
C = pd.DataFrame(rows)
C['suitable'] = C.enwiki.notna() & (C.unsuitable == '')
pick = {}
for kind in ['value', 'gloss']:
    for t, g in C[C.suitable & (C.query_kind == kind)].sort_values('rank').groupby('theme'):
        pick.setdefault(t, g.iloc[0].qid)
C['auto_pick'] = [pick.get(t) == q for t, q in zip(C.theme, C.qid)]
save_parquet(C, f'{WK}/candidates.parquet')
print('values', V.theme.nunique(), 'with an automatic pick', len(pick), 'candidates', len(C))
