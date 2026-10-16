# 02. Query the public TweetsKB endpoint (5% sample) for daily tweet counts and summed sentiment, by month window.
#   total  : all tweets in the sample per day (denominator)
#   art    : per Wikipedia article (its title and kept redirect titles together, each tweet once), batches of <= 50 IRIs
#   narrow / mid / broad : per taxonomy node, each tweet once per node (a tweet that mentions two articles of a node counts
#            once). Whole nodes are packed into batches of <= 50 IRIs; a node with more than 50 IRIs gets its own query.
# Only IRIs found in TweetsKB by script 01 are queried. A query that fails or returns 10,000 rows is split in half (by days)
# and retried. At most one query every 3 seconds; every answer is cached (tk_common.run_query); every finished
# (kind, batch, month) is stored as a small counts-only JSON under data/interim/tweetskb_cache/units/, so a restart skips it.
# Order: 2016-01 to 2023-06 first (total, middle, narrow, article, broad), then 2013-02 to 2015-12.
# Run: bash jobs/heavy_lock.sh nice -n 10 jobs/bg... (see report). Single process.
import json, os, sys, time, datetime as dt, pandas as pd
os.nice(10)
from tk_common import *

UNITS = f'{CACHE}/units'
os.makedirs(UNITS, exist_ok=True)
E = pd.read_parquet(f'{TK}/entities.parquet')
E = E[E.exists_in_tweetskb]
A = pd.read_parquet(f'{WK}/articles.parquet')
V, N = load_taxonomy()
theme_node = V.set_index('theme').node_id
theme_arts = A.groupby('theme').canonical.apply(lambda s: list(dict.fromkeys(s.dropna()))).to_dict()
art_iris = E.groupby('article').iri.apply(list).to_dict()


def pack(groups, limit=50):
    """groups: dict group -> list of IRIs. Whole groups into batches of <= limit pairs (bigger groups alone)."""
    batches, cur, n = [], [], 0
    for g in sorted(groups):
        p = [(u, g) for u in dict.fromkeys(groups[g])]
        if not p:
            continue
        if cur and n + len(p) > limit:
            batches.append(cur); cur, n = [], 0
        cur += p; n += len(p)
    if cur:
        batches.append(cur)
    return batches


node_art = {}
for t, arts in theme_arts.items():
    for a in ancestors(theme_node[t]):
        node_art.setdefault(a, set()).update(arts)
node_iris = {nid: [u for a in sorted(arts) for u in art_iris.get(a, [])] for nid, arts in node_art.items()}
BATCH = {'art': pack({a: u for a, u in art_iris.items()}),
         'narrow': pack({k: v for k, v in node_iris.items() if k.count('.') == 2}),
         'mid': pack({k: v for k, v in node_iris.items() if k.count('.') == 1}),
         'broad': pack({k: v for k, v in node_iris.items() if k.count('.') == 0})}
print({k: (len(v), sum(len(b) for b in v)) for k, v in BATCH.items()}, flush=True)


def months(a, b):
    y, m = a
    while (y, m) <= b:
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        yield dt.date(y, m, 1), dt.date(ny, nm, 1)
        y, m = ny, nm


def fetch(build, tag, d0, d1, depth=0):
    rows = run_query(build(d0, d1), tag)
    if rows is not None and len(rows) < 10000:
        return rows
    if (d1 - d0).days <= 1:
        return None
    mid = d0 + dt.timedelta(days=(d1 - d0).days // 2)
    a = fetch(build, tag, d0, mid, depth + 1)
    b = fetch(build, tag, mid, d1, depth + 1)
    return None if a is None or b is None else a + b


def work():
    P1 = list(months((2016, 1), (2023, 6))); P2 = list(months((2013, 2), (2015, 12)))
    order = []
    for P in (P1, P2):
        for kind in ('total', 'mid', 'narrow', 'art', 'broad'):
            for (d0, d1) in P:
                if kind == 'total':
                    order.append((kind, 0, d0, d1))
                else:
                    order += [(kind, i, d0, d1) for i in range(len(BATCH[kind]))]
    return order


order = work()
t0 = time.time(); done = skipped = failed = 0
for k, (kind, i, d0, d1) in enumerate(order):
    f = f'{UNITS}/{kind}_{i:03d}_{d0:%Y%m}.json'
    if os.path.exists(f):
        skipped += 1; continue
    if kind == 'total':
        rows = fetch(q_total, 'total', d0, d1)
    else:
        b = BATCH[kind][i]
        rows = fetch(lambda a, c, b=b: q_group(b, a, c), kind, d0, d1)
    if rows is None:
        failed += 1; print('FAILED', kind, i, d0, flush=True); continue
    json.dump(dict(kind=kind, batch=i, month=f'{d0:%Y-%m}', rows=rows), open(f + '.part', 'w')); os.replace(f + '.part', f)
    done += 1
    if done % 100 == 0:
        print(f'{time.strftime("%H:%M:%S")} done {done} skipped {skipped} failed {failed} of {len(order)}  last {kind} {d0:%Y-%m}  elapsed {(time.time() - t0) / 60:.1f} min', flush=True)
print('FINISHED', f'done {done} skipped {skipped} failed {failed} of {len(order)} in {(time.time() - t0) / 60:.1f} min', flush=True)
