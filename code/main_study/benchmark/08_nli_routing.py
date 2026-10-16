# Method benchmark, stage 2c: context-reading routing. The pages of the daily top-500 list whose best theme-value cosine is at least 0.55 (addendum a's
# routes.parquet) get a short description (fetched from the MediaWiki API when missing), their 5 closest theme values are re-ranked by a zero-shot
# natural-language-inference classifier, and a page goes to every candidate whose entailment probability is at least 0.50. No demand data are read.
# Settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json (stage2_pipelines.2c_context_reading_routing).
# Phases: fetch (network, light) -> candidates (embedding) -> nli (the heavy one) -> series (weekly node series and the outcome-free report).
#   ../../../.venv/bin/python 08_nli_routing.py --phase fetch|candidates|nli|series|all
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '3')
import sys, json, time, pathlib, argparse
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / 'interest'))
import numpy as np, pandas as pd
import _stage2_common as C
import _ci as CI

OUT = C.OUT / 'nli_routing'
RAW = pathlib.Path(CI.D) / 'raw'
TOP = C.OUT.parent / 'top_routing'
POOL_COS, K_CAND, THRESH = 0.55, 5, 0.50
NLI_MODEL, NLI_REV = 'MoritzLaurer/deberta-v3-base-zeroshot-v2.0', '8e7e5af5983a0ddb1a5b45a38b129ab69e2258e8'
TEMPLATE = 'This text is about {}.'
API = 'https://en.wikipedia.org/w/api.php'


def pool_titles():
    R = pd.read_parquet(TOP / 'routes.parquet')
    return R[R.cos >= POOL_COS].title.tolist()


# ---------------- phase 1: descriptions ----------------
def phase_fetch():
    import requests
    OUT.mkdir(parents=True, exist_ok=True)
    desc = json.load(open(RAW / 'wiki_top_descriptions.json'))
    cache_p = OUT / 'descriptions_extra.json'
    cache = json.load(open(cache_p)) if cache_p.exists() else {}
    titles = pool_titles()
    todo = [t for t in titles if not desc.get(t) and t not in cache]
    print(f'{time.strftime("%H:%M:%S")} pool {len(titles)} pages; {sum(bool(desc.get(t)) for t in titles)} have a description; fetching {len(todo)}', flush=True)
    s = requests.Session(); s.headers['User-Agent'] = CI.UA
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        names = [t.replace('_', ' ') for t in batch]
        for attempt in range(4):
            try:
                r = s.get(API, params={'action': 'query', 'prop': 'description', 'titles': '|'.join(names), 'redirects': 1, 'format': 'json',
                                       'formatversion': 2, 'maxlag': 5}, timeout=60)
                j = r.json()
                if 'error' in j and j['error'].get('code') == 'maxlag':
                    time.sleep(5); continue
                break
            except Exception as e:                                   # network hiccup: wait and retry
                print('retry', attempt, e, flush=True); time.sleep(5)
        else:
            raise SystemExit('description fetch failed')
        q = j.get('query', {})
        norm = {x['from']: x['to'] for x in q.get('normalized', [])}
        redir = {x['from']: x['to'] for x in q.get('redirects', [])}
        got = {p['title']: p.get('description', '') for p in q.get('pages', []) if not p.get('missing')}
        for t, nm in zip(batch, names):
            f = norm.get(nm, nm); f = redir.get(f, f)
            cache[t] = got.get(f, '')
        if (i // 50) % 20 == 0:
            json.dump(cache, open(cache_p, 'w')); print(f'{time.strftime("%H:%M:%S")} {i + len(batch)}/{len(todo)}', flush=True)
        time.sleep(0.25)
    json.dump(cache, open(cache_p, 'w'))
    got = sum(bool(v) for v in cache.values())
    print(f'{time.strftime("%H:%M:%S")} fetched {len(cache)} pages, {got} with a description', flush=True)


def page_text(t, desc, extra):
    d = desc.get(t) or extra.get(t) or ''
    return t.replace('_', ' ') + (', ' + d if d else '')


# ---------------- phase 2: candidates ----------------
def phase_candidates():
    OUT.mkdir(parents=True, exist_ok=True)
    desc = json.load(open(RAW / 'wiki_top_descriptions.json'))
    extra = json.load(open(OUT / 'descriptions_extra.json'))
    titles = pool_titles()
    text = [page_text(t, desc, extra) for t in titles]
    V, N = CI.load_taxonomy()
    Ev, mu = CI.value_space(V)
    from fastembed import TextEmbedding
    t0 = time.time()
    m = TextEmbedding(CI.EMB_MODEL)
    E = np.vstack([np.asarray(v, np.float32) for v in m.embed([f'books about {x}' for x in text], batch_size=128)])
    E = E / np.linalg.norm(E, axis=1, keepdims=True) - mu
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    print(f'{time.strftime("%H:%M:%S")} embedded {len(titles)} pages ({(time.time() - t0) / 60:.1f} min)', flush=True)
    Sm = E @ Ev.T
    top = np.argpartition(-Sm, K_CAND, axis=1)[:, :K_CAND]
    rows = []
    for i, t in enumerate(titles):
        js = top[i][np.argsort(-Sm[i, top[i]])]
        for rank, j in enumerate(js, 1):
            rows.append((t, text[i], rank, V.theme.to_numpy()[j], V.node_id.to_numpy()[j], float(Sm[i, j])))
    P = pd.DataFrame(rows, columns=['title', 'text', 'rank', 'value', 'node_id', 'cos'])
    P.to_parquet(OUT / 'candidates.parquet', index=False)
    print(f'{time.strftime("%H:%M:%S")} wrote candidates.parquet ({len(P)} pairs)', flush=True)


# ---------------- phase 3: NLI ----------------
def phase_nli(batch=64, chunk=8192):
    import torch
    torch.set_num_threads(3)
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    P = pd.read_parquet(OUT / 'candidates.parquet')
    parts = OUT / 'nli_parts'; parts.mkdir(exist_ok=True)
    tok = AutoTokenizer.from_pretrained(NLI_MODEL, revision=NLI_REV)
    model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL, revision=NLI_REV, torch_dtype=torch.float32).eval()
    lab = {int(k): v for k, v in model.config.id2label.items()}
    ent = [k for k, v in lab.items() if v.lower().startswith('entail')][0]
    print(f'{time.strftime("%H:%M:%S")} model loaded; labels {lab}; entailment index {ent}', flush=True)
    P = P.assign(hyp=[TEMPLATE.format(v) for v in P.value])
    P['len'] = P.text.str.len() + P.hyp.str.len()
    order = P.sort_values('len', kind='stable').index.to_numpy()
    t0 = time.time()
    for ci in range(0, len(order), chunk):
        p = parts / f'part_{ci // chunk:04d}.parquet'
        if p.exists():
            continue
        idx = order[ci:ci + chunk]
        res = np.zeros(len(idx), np.float32)
        for b in range(0, len(idx), batch):
            ii = idx[b:b + batch]
            enc = tok(P.text.to_numpy()[ii].tolist(), P.hyp.to_numpy()[ii].tolist(), truncation=True, max_length=160, padding=True, return_tensors='pt')
            with torch.inference_mode():
                lg = model(**enc).logits
            res[b:b + len(ii)] = torch.softmax(lg, dim=-1)[:, ent].numpy()
        pd.DataFrame({'row': idx, 'p_entail': res}).to_parquet(p.with_suffix('.tmp'), index=False); os.replace(p.with_suffix('.tmp'), p)
        el = time.time() - t0
        print(f'{time.strftime("%H:%M:%S")} {min(ci + chunk, len(order))}/{len(order)} pairs ({el / 60:.1f} min)', flush=True)
    R = pd.concat([pd.read_parquet(f) for f in sorted(parts.glob('part_*.parquet'))], ignore_index=True).drop_duplicates('row').set_index('row').p_entail
    P = P.drop(columns=['hyp', 'len']).assign(p_entail=R.reindex(P.index).to_numpy())
    assert P.p_entail.notna().all()
    P.to_parquet(OUT / 'pairs.parquet', index=False)
    print(f'{time.strftime("%H:%M:%S")} wrote pairs.parquet; {(time.time() - t0) / 60:.1f} min', flush=True)


# ---------------- phase 4: series and outcome-free report ----------------
def phase_series():
    NS = ('Special:', 'Wikipedia:', 'File:', 'Portal:', 'Help:', 'Category:', 'Template:', 'User:', 'Talk:')
    P = pd.read_parquet(OUT / 'pairs.parquet')
    R = P[P.p_entail >= THRESH].copy()
    R['nodes'] = R.node_id.map(CI.ancestors)
    X = R[['title', 'nodes']].explode('nodes').rename(columns={'nodes': 'node_id'}).drop_duplicates(['title', 'node_id'])
    top = json.load(open(RAW / 'wiki_top_daily.json'))
    L = pd.DataFrame([(d, t, v) for d, lst in top.items() for t, v in lst], columns=['date', 'title', 'views'])
    L = L[~L.title.isin(['Main_Page', '-']) & ~L.title.str.startswith(NS)]
    L['date'] = pd.to_datetime(L.date, format='%Y%m%d')
    Xv = L.merge(X, on='title')
    Xv['week'] = Xv.date - pd.to_timedelta(Xv.date.dt.weekday, unit='D')
    Wv = Xv.groupby(['node_id', 'week']).views.sum().rename('views').reset_index()
    T = pd.read_parquet(pathlib.Path(CI.WK) / 'total_daily.parquet')
    T['date'] = pd.to_datetime(T.date)
    T = T[(T.date >= L.date.min()) & (T.date <= L.date.max())]
    T['week'] = T.date - pd.to_timedelta(T.date.dt.weekday, unit='D')
    TW = T.groupby('week').agg(total_views=('views', 'sum'), days_covered=('date', 'nunique')).reset_index()
    nodes = sorted(set(Wv.node_id))
    grid = pd.MultiIndex.from_product([nodes, TW.week], names=['node_id', 'week']).to_frame(index=False)
    W = grid.merge(Wv, on=['node_id', 'week'], how='left').merge(TW, on='week')
    W['views'] = W.views.fillna(0.0)
    W['share'] = W.views / W.total_views
    W['partial_week'] = W.days_covered < 7
    W['level'] = W.node_id.str.count(r'\.') + 1
    W.to_parquet(OUT / 'weekly_node.parquet', index=False)
    # outcome-free checks
    pages = P.drop_duplicates('title')
    routed_titles = set(R.title)
    A = pd.read_parquet(pathlib.Path(CI.WK) / 'articles.parquet')
    A = A[A.chosen.notna()].assign(title=lambda d: d.chosen.str.replace(' ', '_'))
    A = A[A.title.isin(pages.title)]
    nodes_of = R.groupby('title').node_id.apply(set)

    def rel(cur, title):
        if title not in routed_titles:
            return 'not routed'
        s = nodes_of[title]
        if cur in s:
            return 'same node'
        if any(n.startswith(cur + '.') or cur.startswith(n + '.') for n in s):
            return 'ancestor or descendant'
        return 'other node'
    A['agree'] = [rel(c, t) for c, t in zip(A.node_id, A.title)]
    stage1 = pd.read_parquet(TOP / 'routes.parquet')
    s1_routed = set(stage1[stage1.cos >= 0.70].title)
    ex = ['Ocean\'s_8', 'The_Bear_(TV_series)', 'Kinds_of_Kindness', 'Oppenheimer_(film)', 'COVID-19_pandemic']
    exr = []
    for t in ex:
        q = P[P.title == t]
        if len(q):
            exr.append(f'- {t.replace("_", " ")}: ' + '; '.join(f'{v} (cos {c:.2f}, entail {p:.2f})' for v, c, p in zip(q.value, q.cos, q.p_entail)))
    lines = ['# Context-reading routing of the daily top-500 pages (stage 2c)', '',
             f'Written {time.strftime("%Y-%m-%d %H:%M")}. Settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json (2c). No demand data read.', '',
             f'- Pool: {pages.shape[0]:,} pages with a best cosine of at least {POOL_COS} in addendum a; {int(pages.text.str.contains(",").sum()):,} have a short description in their text; {P.shape[0]:,} page-candidate pairs.',
             f'- Entailment probability of the pairs: median {P.p_entail.median():.2f}; share at or above {THRESH}: {(P.p_entail >= THRESH).mean():.1%}; at or above 0.8: {(P.p_entail >= 0.8).mean():.1%}.',
             f'- Routed (any candidate at or above {THRESH}): {len(routed_titles):,} pages ({len(routed_titles) / pages.shape[0]:.1%} of the pool); addendum a routed {len(s1_routed):,} pages at cosine 0.70; overlap {len(routed_titles & s1_routed):,}.',
             f'- Nodes with a series: {len(nodes)} (middle {sum(n.count(".") == 1 for n in nodes)}, narrow {sum(n.count(".") == 2 for n in nodes)}); median share of full weeks with routed views: '
             f'middle {W[(~W.partial_week) & (W.level == 2)].groupby("node_id").share.apply(lambda s: (s > 0).mean()).median():.0%}, '
             f'narrow {W[(~W.partial_week) & (W.level == 3)].groupby("node_id").share.apply(lambda s: (s > 0).mean()).median():.0%}.', '',
             '## Agreement with the hand-checked pages that are in the pool', '', f'{len(A)} hand-checked pages are in the pool.', '',
             A.agree.value_counts().rename_axis('result').reset_index().to_csv(index=False, sep='|').replace('|', ' | '), '',
             '## Examples named in addendum a', ''] + exr + ['', '## Most-viewed routed pages per broad theme (top 3, by total top-500 views)', '']
    tv = L.groupby('title').views.sum()
    R2 = R.assign(views=lambda d: d.title.map(tv), broad=lambda d: d.node_id.str.split('.').str[0]).sort_values('p_entail', ascending=False)
    R2 = R2.sort_values('views', ascending=False)
    for b, g in R2.groupby('broad'):
        g = g.drop_duplicates('title')
        lines.append(f'- {b}: ' + '; '.join(f'{t.replace("_", " ")} -> {v} ({p:.2f})' for t, v, p in zip(g.title[:3], g.value[:3], g.p_entail[:3])))
    (pathlib.Path(CI.REP) / 'benchmark_stage2_nli_routing.md').write_text('\n'.join(lines) + '\n')
    print(f'{time.strftime("%H:%M:%S")} wrote weekly_node.parquet and the report', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', default='all')
    a = ap.parse_args()
    C.check_addendum()
    ph = ['fetch', 'candidates', 'nli', 'series'] if a.phase == 'all' else a.phase.split(',')
    for p in ph:
        {'fetch': phase_fetch, 'candidates': phase_candidates, 'nli': phase_nli, 'series': phase_series}[p]()
