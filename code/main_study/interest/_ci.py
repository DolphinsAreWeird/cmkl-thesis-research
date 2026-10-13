# Shared helpers for the interest-side scripts (main study, checkpoint 2). Paths come from code/config.py.
# The taxonomy folder is a setting (env INTEREST_TAXONOMY, default taxonomy_v2) so the same code can be rerun on v3,
# which adds theme values into the same nodes. Everything here works at the level of theme values and nodes.
import sys, os, json, time, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))      # code/  (config.py)
sys.path.insert(0, str(HERE.parent))          # code/main_study/  (_labels.py: GLOSS used for the taxonomy embeddings)
from config import D, UA  # noqa: E402

TAXO = os.environ.get('INTEREST_TAXONOMY', f'{D}/db/taxonomy_v2')
TAXO_V3 = f'{D}/db/taxonomy_v3'
# The only v3 change applied to the interest side (decision of 13 Oct 2026, prereg addendum f): the value "violence"
# leaves the sexual and domestic violence node for the new narrow node B12.M01.N04 "Violence and violent crime".
V3_MOVES = {'violence': 'B12.M01.N04'}
OUT = f'{D}/db/interest'
GD = f'{OUT}/gdelt'
WK = f'{OUT}/wiki'
REP = f'{D}/reports'
for p in (OUT, GD, WK):
    os.makedirs(p, exist_ok=True)

EMB_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
EMB_CACHE = f'{OUT}/_embedding_cache.parquet'     # own cache: the taxonomy cache may be written by the v3 build


def save_json(obj, path):
    with open(path + '.part', 'w') as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(path + '.part', path)


def save_parquet(df, path):
    df.to_parquet(path + '.part', index=False)
    os.replace(path + '.part', path)


# ---------------- taxonomy ----------------
def load_taxonomy():
    """Theme values with their node and every ancestor.
    Returns (V, N): V one row per value (theme, general, node_id, level, narrow_id, mid_id, broad_id, support),
    N the node table (node_id, level, parent, label)."""
    import pandas as pd
    V = pd.read_parquet(f'{TAXO}/theme_values.parquet')
    VN = pd.read_parquet(f'{TAXO}/theme_value_node.parquet')[['theme', 'node_id', 'level']]
    N = pd.read_parquet(f'{TAXO}/theme_nodes.parquet')[['node_id', 'level', 'parent', 'label']]
    V = V.merge(VN, on='theme', how='left')
    assert V.node_id.notna().all(), 'value without node'
    # approved v3 structure changes applied to the v2 value list (the interest side stays on the v2 values)
    for value, nid in V3_MOVES.items():
        if nid not in set(N.node_id):
            N3 = pd.read_parquet(f'{TAXO_V3}/theme_nodes.parquet')[['node_id', 'level', 'parent', 'label']]
            row = N3[N3.node_id == nid]
            assert len(row) == 1, f'v3 node {nid} not found in {TAXO_V3}'
            N = pd.concat([N, row], ignore_index=True)
        lvl = int(N.set_index('node_id').level[nid])
        V.loc[V.theme == value, ['node_id', 'level']] = [nid, lvl]
    V['support'] = V.spl_works.fillna(0) + V.gr_works.fillna(0) + V.wd_works.fillna(0) + V.lv_recordings.fillna(0)
    V['broad_id'] = V.node_id.str.split('.').str[0]
    V['mid_id'] = [n if l == 2 else ('.'.join(n.split('.')[:2]) if l == 3 else None) for n, l in zip(V.node_id, V.level)]
    V['narrow_id'] = [n if l == 3 else None for n, l in zip(V.node_id, V.level)]
    return V, N


def ancestors(node_id):
    """'B05.M02.N02' -> ['B05.M02.N02', 'B05.M02', 'B05']"""
    p = node_id.split('.')
    return ['.'.join(p[:k]) for k in range(len(p), 0, -1)]


def value_text(v):
    """Same text template as the taxonomy embeddings (code/main_study/06_theme_hierarchy.py)."""
    import _labels as LB
    return f'books about {LB.GLOSS.get(v, v)}'


def embed(texts):
    """Unit-length embeddings, cached by exact text (own cache file)."""
    import numpy as np, pandas as pd
    cache = {}
    if os.path.exists(EMB_CACHE):
        c = pd.read_parquet(EMB_CACHE)
        cache = dict(zip(c.text, c.vec))
    todo = sorted({t for t in texts if t not in cache})
    if todo:
        from fastembed import TextEmbedding
        m = TextEmbedding(EMB_MODEL)
        for t, v in zip(todo, m.embed(todo, batch_size=64)):
            cache[t] = np.asarray(v, dtype=np.float32)
        save_parquet(pd.DataFrame({'text': list(cache), 'vec': [np.asarray(v, dtype=np.float32) for v in cache.values()]}), EMB_CACHE)
    E = np.vstack([np.asarray(cache[t], dtype=np.float32) for t in texts])
    return E / np.linalg.norm(E, axis=1, keepdims=True)


def value_space(V):
    """Centered unit embeddings for every theme value, in the taxonomy's own space: 'books about <gloss>', minus the
    mean of the specific (non-general) values, unit length (as in 06_theme_hierarchy.py). Returns (E_values, mu).
    Checks that the specific values reproduce the stored theme_value_embeddings.npy."""
    import numpy as np
    spec = V[~V.general].sort_values('theme')
    Es = embed([value_text(t) for t in spec.theme])
    mu = Es.mean(0)
    stored = f'{TAXO}/theme_value_embeddings.npy'
    if os.path.exists(stored):
        S = np.load(stored)
        Ec = Es - mu; Ec /= np.linalg.norm(Ec, axis=1, keepdims=True)
        if S.shape == Ec.shape:
            agree = float(np.min(np.sum(S * Ec, axis=1)))
            assert agree > 0.999, f'embeddings do not reproduce the stored taxonomy space (min cos {agree:.4f})'
    E = embed([value_text(t) for t in V.theme]) - mu
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    return E, mu


# ---------------- weeks ----------------
def week_start(dates):
    """Monday of the week (same clock as the GDELT query: DATE_TRUNC(..., WEEK(MONDAY)))."""
    import pandas as pd
    d = pd.to_datetime(dates)
    return (d - pd.to_timedelta(d.dt.weekday if hasattr(d, 'dt') else d.weekday, unit='D')).normalize()


# ---------------- polite HTTP ----------------
_last = [0.0]


def polite_get(url, params=None, min_gap=1.0, timeout=40, tries=8):
    """GET with the project User-Agent, at most one request per `min_gap` seconds, backing off on 429/5xx.
    Returns the requests.Response (status 200 or 404), or None after repeated failures."""
    import requests
    for k in range(tries):
        wait = _last[0] + min_gap - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = requests.get(url, params=params, headers={'User-Agent': UA}, timeout=timeout)
        except Exception:
            time.sleep(3 * (k + 1)); continue
        if r.status_code in (200, 404):
            return r
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(int(r.headers.get('retry-after', 5 * (k + 1))) + 1); continue
        return r
    return None


# ---------------- fixed settings (prereg/study3_settings_2026-10-13.json, read-only, hashed) ----------------
PREREG = HERE.parents[2] / 'prereg'
SETTINGS_FILE = PREREG / 'study3_settings_2026-10-13.json'


def settings():
    """Shift and interest settings parsed from the fixed, dated record. Nothing is hard-coded here: every number is
    read from the record's text, and the parse fails loudly if the wording changes. The file's SHA-256 must match the
    value in prereg/README.md."""
    import hashlib, re
    raw = SETTINGS_FILE.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    readme = (PREREG / 'README.md').read_text()
    assert sha in readme, f'settings file hash {sha} does not match prereg/README.md'
    J = json.loads(raw)
    sd, it = J['shift_definitions'], J['interest']

    def num(pattern, text):
        m = re.search(pattern, text)
        if not m:
            raise SystemExit(f'cannot parse /{pattern}/ from: {text}')
        return float(m.group(1))

    S = dict(
        sha256=sha, fixed_on=J['fixed_on'],
        normal_weeks=int(num(r'median of the previous (\d+) weeks', sd['normal_level'])),
        normal_excludes_current='not including the current week' in sd['normal_level'],
        rise_ratio=num(r'ratio >= ([\d.]+)', sd['rising_week']),
        mk_weeks=int(num(r'over the last (\d+) weeks', sd['rising_week'])),
        mk_includes_current='including this week' in sd['rising_week'],
        mk_alpha_one_sided=num(r'one-sided p < ([\d.]+)', sd['rising_week']),
        mk_tau_positive='tau > 0' in sd['rising_week'],
        mk_hamed_rao='Hamed-Rao' in sd['rising_week'],
        quiet_weeks=int(num(r'at least (\d+) consecutive weeks', sd['shift_start'])),
        quiet_ratio=num(r'ratio < ([\d.]+)', sd['shift_start']),
        sustained_min=int(num(r'duration_count >= (\d+)', sd['sustained'])),
        sustained_label_week=int(num(r'label assigned in week (\d+)', sd['sustained'])),
        intermediate_eq=int(num(r'duration_count == (\d+)', sd['intermediate'])),
        fading_max=int(num(r'duration_count <= (\d+)', sd['fading'])),
        large_ratio=num(r'size >= ([\d.]+)', sd['large_shift']),
        seasonal_window=int(num(r'within \+/-(\d+) weeks', sd['seasonal_shift'])),
        seasonal_share=0.5 if 'at least half of the other years' in sd['seasonal_shift'] else None,
        min_wiki_views=float(it['minimum_volume']['wikipedia_normal_views_per_week']),
        min_gdelt_mentions=float(it['minimum_volume']['gdelt_normal_mentions_per_week']),
        primary_source=it['primary_source'], secondary_source=it['secondary_source'],
        levels_tested=J['taxonomy']['levels_tested'], broad_level=J['taxonomy']['broad_level'],
        gdelt_durations_rule=sd['gdelt_durations'],
    )
    assert S['normal_excludes_current'] and S['mk_includes_current'] and S['mk_tau_positive'] and S['mk_hamed_rao']
    assert S['seasonal_share'] == 0.5 and 'ISO week, Monday start' in it['week']
    assert S['rise_ratio'] == S['quiet_ratio'], 'rising and quiet thresholds differ; check the record'
    return S
