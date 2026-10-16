# Benchmark stage 2a: route the daily top-500 English Wikipedia pages into the book-derived themes with the taxonomy
# embedding model (rule in prereg/addenda_benchmark/2026-10-15_a_top_pages_routing.json), build weekly node series,
# and check the rule against the hand-curated pages. No demand data are read here.
import sys, json, pathlib, time
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'interest'))
import numpy as np, pandas as pd
import _ci as CI

OUT = pathlib.Path(CI.D) / 'db' / 'benchmark' / 'top_routing'
NS = ('Special:', 'Wikipedia:', 'File:', 'Portal:', 'Help:', 'Category:', 'Template:', 'User:', 'Talk:')
THRESH = 0.70


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    top = json.load(open(pathlib.Path(CI.D) / 'raw' / 'wiki_top_daily.json'))
    desc = json.load(open(pathlib.Path(CI.D) / 'raw' / 'wiki_top_descriptions.json'))
    rows = [(d, t, v) for d, lst in top.items() for t, v in lst]
    L = pd.DataFrame(rows, columns=['date', 'title', 'views'])
    L = L[~L.title.isin(['Main_Page', '-']) & ~L.title.str.startswith(NS)]
    L['date'] = pd.to_datetime(L.date, format='%Y%m%d')
    titles = sorted(L.title.unique())
    text = [t.replace('_', ' ') + (', ' + desc[t] if desc.get(t) else '') for t in titles]
    print(f'{time.strftime("%H:%M:%S")} {len(L)} page-days, {len(titles)} pages, {sum(bool(desc.get(t)) for t in titles)} with a description', flush=True)
    V, N = CI.load_taxonomy()
    Ev, mu = CI.value_space(V)
    from fastembed import TextEmbedding
    m = TextEmbedding(CI.EMB_MODEL)
    E = np.vstack([np.asarray(v, np.float32) for v in m.embed([f'books about {x}' for x in text], batch_size=128)])
    E = E / np.linalg.norm(E, axis=1, keepdims=True) - mu
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    print(f'{time.strftime("%H:%M:%S")} embedded ({(time.time()-t0)/60:.1f} min)', flush=True)
    S = E @ Ev.T
    j = S.argmax(1); s = S.max(1)
    R = pd.DataFrame({'title': titles, 'text': text, 'value': V.theme.to_numpy()[j], 'node_id': V.node_id.to_numpy()[j], 'cos': s})
    R['routed'] = R.cos >= THRESH
    R.to_parquet(OUT / 'routes.parquet', index=False)
    # weekly node series
    X = L.merge(R[R.routed][['title', 'node_id']], on='title')
    X = X.assign(node_id=X.node_id.map(CI.ancestors)).explode('node_id')
    X['week'] = X.date - pd.to_timedelta(X.date.dt.weekday, unit='D')
    Wv = X.groupby(['node_id', 'week']).views.sum().rename('views').reset_index()
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
    # outcome-free check against the hand-curated pages
    A = pd.read_parquet(pathlib.Path(CI.WK) / 'articles.parquet')
    A = A[A.chosen.notna()].assign(title=lambda d: d.chosen.str.replace(' ', '_'))
    C = A.merge(R, on='title', how='inner', suffixes=('_cur', '_top'))
    def rel(a, b):
        if not isinstance(b, str): return 'not routed'
        if a == b: return 'same node'
        if b.startswith(a + '.') or a.startswith(b + '.'): return 'ancestor or descendant'
        return 'other node'
    C['agree'] = [rel(a, b if r else None) for a, b, r in zip(C.node_id_cur, C.node_id_top, C.routed)]
    lev = W[~W.partial_week].groupby(['level', 'node_id']).share.apply(lambda s: (s > 0).mean())
    lines = ['# Routing the daily top-500 Wikipedia pages into book themes (stage 2a)', '',
             f'Written {time.strftime("%Y-%m-%d %H:%M")}. Rule: prereg/addenda_benchmark/2026-10-15_a_top_pages_routing.json. No demand data read.', '',
             f'- Pool: {len(titles):,} pages over {L.date.nunique():,} days ({len(L):,} page-days in the top 500, after the namespace rule).',
             f'- Routed at cosine >= {THRESH}: {int(R.routed.sum()):,} pages ({R.routed.mean():.1%}); page-days routed: {X.drop_duplicates(["date","title"]).shape[0]:,}.',
             f'- Nodes with a series: {len(nodes)} (broad {sum(n.count(".")==0 for n in nodes)}, middle {sum(n.count(".")==1 for n in nodes)}, narrow {sum(n.count(".")==2 for n in nodes)}).',
             f'- Share of full weeks with any routed views, median over nodes: middle {lev.loc[2].median():.0%}, narrow {lev.loc[3].median():.0%}.' if 3 in lev.index.get_level_values(0) else '',
             '', '## Agreement with the hand-curated pages that appear in the pool', '',
             f'{len(C)} of {len(A)} curated pages appear in the top-500 pool.', '',
             C.agree.value_counts().rename_axis('result').reset_index().to_csv(index=False, sep='|').replace('|', ' | '), '',
             '## Most-viewed routed pages per broad theme (top 3, by total top-500 views)', '']
    tv = L.groupby('title').views.sum()
    R2 = R[R.routed].assign(views=lambda d: d.title.map(tv), broad=lambda d: d.node_id.str.split('.').str[0])
    for b, g in R2.sort_values('views', ascending=False).groupby('broad'):
        lines.append(f'- {b}: ' + '; '.join(f'{t.replace("_"," ")} -> {v} ({c:.2f})' for t, v, c in zip(g.title[:3], g.value[:3], g.cos[:3])))
    (pathlib.Path(CI.REP) / 'benchmark_top_routing.md').write_text('\n'.join(lines) + '\n')
    print(f'{time.strftime("%H:%M:%S")} done ({(time.time()-t0)/60:.1f} min)', flush=True)


if __name__ == '__main__':
    main()
