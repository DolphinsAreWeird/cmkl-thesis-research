# Shared helpers for the TweetsKB conversation series (record: prereg/conversation_sources_settings_2026-10-14.json).
# Query runner for the public TweetsKB SPARQL endpoint: one query every 3 seconds, identified User-Agent, every answer
# cached under data/interim/tweetskb_cache/ (the cache holds only aggregate counts; the queries never return tweet text,
# tweet IDs or user fields), resume after interruption. Interest side only: nothing here reads borrowing data.
import sys, os, json, time, hashlib, pathlib, urllib.parse
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'main_study' / 'interest'))
sys.path.insert(0, str(HERE.parent))
from _ci import D, OUT, WK, REP, load_taxonomy, ancestors, save_parquet, save_json  # noqa: E402

UA = 'CMKL-thesis-research/0.1 (student project; CMKL University; kwai@cmkl.ac.th)'
ENDPOINT = 'https://data.gesis.org/tweetskb/sparql'
GRAPH = 'http://data.gesis.org/tweetskb'
CACHE = f'{D}/interim/tweetskb_cache'
TK = os.environ.get('TK_TEST_DIR', f'{OUT}/tweetskb')   # TK_TEST_DIR only for a dry run on stand-in data
for p in (CACHE, TK):
    os.makedirs(p, exist_ok=True)
MIN_GAP = 3.0
DBR = 'http://dbpedia.org/resource/'
PRE = """PREFIX nee: <http://www.ics.forth.gr/isl/oae/core#>
PREFIX schema: <http://schema.org/>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX onyx: <http://www.gsi.dit.upm.es/ontologies/onyx/ns#>
PREFIX wna: <http://www.gsi.dit.upm.es/ontologies/wnaffect/ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""


def iri(title):
    """Wikipedia title -> DBpedia resource IRI as TweetsKB writes it: spaces to underscores, characters that cannot sit
    in an IRI reference percent-encoded, everything else (letters, accents, brackets, commas, apostrophes) left as is."""
    t = title.strip().replace(' ', '_')
    return DBR + ''.join(urllib.parse.quote(c, safe='') if c in '"#%<>?[\\]^`{|}' or ord(c) < 33 else c for c in t)


def ts(d):
    return f'"{d}T00:00:00"^^xsd:dateTime'


_last = [0.0]


def run_query(body, tag):
    """Run one SPARQL SELECT (body without prefixes). Returns list of dicts (value strings), or None on failure.
    The answer is cached by the query text under CACHE/<tag>/ ; a cached answer costs no request."""
    q = PRE + body
    key = hashlib.sha1(q.encode()).hexdigest()[:20]
    d = f'{CACHE}/{tag}'
    os.makedirs(d, exist_ok=True)
    f = f'{d}/{key}.json'
    if os.path.exists(f):
        return json.load(open(f))['rows']
    import requests
    for k in range(6):
        wait = _last[0] + MIN_GAP - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = requests.post(ENDPOINT, data={'query': q, 'default-graph-uri': GRAPH},
                              headers={'User-Agent': UA, 'Accept': 'application/sparql-results+json'}, timeout=150)
        except Exception:
            time.sleep(10 * (k + 1)); continue
        if r.status_code == 200:
            try:
                j = r.json()
                rows = [{kk: v['value'] for kk, v in b.items()} for b in j['results']['bindings']]
            except Exception:
                return None            # partial or error text from the server: caller splits the window
            json.dump(dict(rows=rows), open(f + '.part', 'w')); os.replace(f + '.part', f)
            return rows
        if r.status_code in (429, 502, 503):
            time.sleep(30 * (k + 1)); continue
        return None                    # 400/500 etc: timeout inside the engine; caller splits
    return None


# ---------------- query builders ----------------
SENT = """  OPTIONAL { ?t onyx:hasEmotionSet ?s1 . ?s1 onyx:hasEmotion ?e1 . ?e1 onyx:hasEmotionCategory wna:positive-emotion ; onyx:hasEmotionIntensity ?pos }
  OPTIONAL { ?t onyx:hasEmotionSet ?s2 . ?s2 onyx:hasEmotion ?e2 . ?e2 onyx:hasEmotionCategory wna:negative-emotion ; onyx:hasEmotionIntensity ?neg }
"""


def q_group(pairs, d0, d1):
    """Distinct tweets per group per day in [d0, d1). pairs: list of (iri, group). A tweet that mentions two IRIs of the
    same group counts once in that group. Returns y, m, dd, g, n (tweets), sp / sn (sums of positive / negative score),
    np (tweets with a score)."""
    vals = ' '.join(f'(<{u}> "{g}")' for u, g in pairs)
    return f"""SELECT ?g (year(?d) AS ?y) (month(?d) AS ?m) (day(?d) AS ?dd) (count(?t) AS ?n) (sum(?pos) AS ?sp) (sum(?neg) AS ?sn) (count(?pos) AS ?np) WHERE {{
  {{ SELECT DISTINCT ?g ?t ?d WHERE {{
    VALUES (?u ?g) {{ {vals} }}
    ?e nee:hasMatchedURI ?u . ?t schema:mentions ?e . ?t dc:created ?d .
    FILTER(?d >= {ts(d0)} && ?d < {ts(d1)}) }} }}
{SENT}}} GROUP BY ?g year(?d) month(?d) day(?d)"""


def q_total(d0, d1):
    return f"""SELECT (year(?d) AS ?y) (month(?d) AS ?m) (day(?d) AS ?dd) (count(?t) AS ?n) WHERE {{
  ?t dc:created ?d . FILTER(?d >= {ts(d0)} && ?d < {ts(d1)}) }} GROUP BY year(?d) month(?d) day(?d)"""
