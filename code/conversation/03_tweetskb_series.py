# 03. Weekly TweetsKB series from the cached daily counts (counts only; no tweet text, IDs or user fields).
# tweets in a week = distinct tweets in the 5% sample that mention any article of the node (each tweet once per node);
# share = tweets / all tweets in the sample that week (record: conversation_sources_settings_2026-10-14.json);
# mean_pos / mean_neg = mean SentiStrength-based positive and negative score (0 to 1) of those tweets (weekly sums / tweets).
# Weeks are ISO weeks starting Monday. A week is partial if fewer than 7 days of the sample have any tweets (days with
# no row in the 'total' answer): the first week (Feb 2013) and the last (Jun 2023) are partial; partial weeks count as missing.
# Outputs (data/db/interest/tweetskb/): weekly_node.parquet, weekly_article.parquet, weekly_total.parquet, weekly_all.parquet
import glob, json, numpy as np, pandas as pd
from tk_common import *

UNITS = f'{CACHE}/units'
FIRST, LAST = pd.Timestamp('2013-02-01'), pd.Timestamp('2023-06-30')
V, N = load_taxonomy()
label = dict(zip(N.node_id, N.label))
E = pd.read_parquet(f'{TK}/entities.parquet')
A = pd.read_parquet(f'{WK}/articles.parquet')
theme_node = V.set_index('theme').node_id
node_art = {}
for t, arts in A.groupby('theme').canonical.apply(lambda s: list(dict.fromkeys(s.dropna()))).items():
    for a in ancestors(theme_node[t]):
        node_art.setdefault(a, set()).update(arts)


def day_frame(kind):
    out = []
    for f in sorted(glob.glob(f'{UNITS}/{kind}_*.json')):
        j = json.load(open(f))
        if j['rows']:
            out.append(pd.DataFrame(j['rows']))
    if not out:
        return pd.DataFrame()
    d = pd.concat(out, ignore_index=True)
    d['date'] = pd.to_datetime(dict(year=d.y.astype(int), month=d.m.astype(int), day=d.dd.astype(int)))
    for c in ('n', 'sp', 'sn', 'np'):
        if c in d:
            d[c] = d[c].astype(float)
    return d.drop(columns=['y', 'm', 'dd'])


def wk(d):
    return d - pd.to_timedelta(d.dt.weekday, unit='D')


# ---- total tweets per day and week ----
tot = day_frame('total')
tot = tot[(tot.date >= FIRST) & (tot.date <= LAST)].groupby('date', as_index=False).n.sum()
tot['week'] = wk(tot.date)
T = tot.groupby('week').agg(total_tweets=('n', 'sum'), days_covered=('n', lambda s: int((s > 0).sum()))).reset_index()
T['partial_week'] = T.days_covered < 7
all_weeks = pd.DataFrame({'week': pd.date_range(wk(pd.Series([FIRST])).iloc[0], LAST, freq='7D')})
T = all_weeks.merge(T, on='week', how='left')
T['total_tweets'] = T.total_tweets.fillna(0); T['days_covered'] = T.days_covered.fillna(0).astype(int)
T['partial_week'] = T.days_covered < 7
save_parquet(T, f'{TK}/weekly_total.parquet')
print('weeks', len(T), 'partial', int(T.partial_week.sum()), T[T.partial_week].week.dt.date.astype(str).tolist()[:12])


def weekly(df, key, expected_ids):
    """df daily rows with column g; returns weekly frame for every (g, week) in the grid (missing = 0 tweets)."""
    df = df[(df.date >= FIRST) & (df.date <= LAST)].copy()
    df['week'] = wk(df.date)
    g = df.groupby(['g', 'week'], as_index=False)[['n', 'sp', 'sn', 'np']].sum()
    grid = pd.MultiIndex.from_product([sorted(expected_ids), T.week], names=['g', 'week']).to_frame(index=False)
    g = grid.merge(g, on=['g', 'week'], how='left').fillna({'n': 0, 'sp': 0, 'sn': 0, 'np': 0})
    g = g.merge(T, on='week', how='left')
    g['share'] = g.n / g.total_tweets.replace(0, np.nan)
    g['mean_pos'] = np.where(g.np > 0, g.sp / g.np.replace(0, np.nan), np.nan)
    g['mean_neg'] = np.where(g.np > 0, g.sn / g.np.replace(0, np.nan), np.nan)
    return g.rename(columns={'n': 'tweets'}).drop(columns=['sp', 'sn', 'np'])


# ---- nodes ----
rows = []
for kind, lvl in (('broad', 1), ('mid', 2), ('narrow', 3)):
    d = day_frame(kind)
    if d.empty:
        continue
    ids = [k for k in node_art if k.count('.') + 1 == lvl]
    g = weekly(d, 'g', ids)
    g['level'] = lvl
    rows.append(g)
W = pd.concat(rows, ignore_index=True).rename(columns={'g': 'node_id'})
W['label'] = W.node_id.map(label)
W['n_articles'] = W.node_id.map(lambda k: len(node_art[k]))
W['n_articles_in_tweetskb'] = W.node_id.map(lambda k: int(E[E.article.isin(node_art[k]) & E.exists_in_tweetskb].article.nunique()))
W['source'] = 'tweetskb'
W = W[['source', 'level', 'node_id', 'label', 'week', 'tweets', 'share', 'mean_pos', 'mean_neg', 'n_articles', 'n_articles_in_tweetskb',
       'total_tweets', 'days_covered', 'partial_week']]
save_parquet(W, f'{TK}/weekly_node.parquet')

# ---- articles ----
d = day_frame('art')
if not d.empty:
    arts = sorted(set(A.canonical.dropna()))
    G = weekly(d, 'g', arts).rename(columns={'g': 'article'})
    G['source'] = 'tweetskb'
    G = G[['source', 'article', 'week', 'tweets', 'share', 'mean_pos', 'mean_neg', 'total_tweets', 'days_covered', 'partial_week']]
    save_parquet(G, f'{TK}/weekly_article.parquet')

# ---- all mapped articles together (share of sample tweets that mention any mapped article) ----
d = day_frame('all')
if not d.empty:
    Z = weekly(d, 'g', ['ALL']).rename(columns={'g': 'series'})
    save_parquet(Z, f'{TK}/weekly_all.parquet')
print('node rows', len(W), 'by level', W.groupby('level').node_id.nunique().to_dict())
