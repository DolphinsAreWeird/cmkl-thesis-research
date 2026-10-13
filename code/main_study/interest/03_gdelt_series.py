# 03. Weekly GDELT interest and tone per theme value and per narrow, middle and broad node.
# volume share = mentions of the node's mapped codes / all mentions of all codes that week (the denominator includes
#                excluded and unmapped codes, i.e. everything in the weekly file).
# tone, positive, negative = mention-weighted mean over the node's codes of each code's weekly average.
# Weeks are ISO weeks starting Monday (the GDELT query truncates to WEEK(MONDAY)). A week is flagged partial when not all
# seven days fall inside the collected range (2017-01-01 to 2021-06-30): the first week (26 Dec 2016, one day) and the
# last week (28 Jun 2021, three days). Partial weeks are kept in the files but flagged; 08 treats them as missing.
# Caveats: GDELT keeps a code-week only with >= 50 mentions, so small codes drop in and out; an article carrying two
# codes of the same node counts twice (the weekly file has no article ids), so shares are mention shares, not article shares.
# Outputs: data/db/interest/gdelt/weekly_node.parquet, weekly_value.parquet, weekly_total.parquet
import numpy as np, pandas as pd, pyarrow.parquet as pq
from _ci import D, GD, load_taxonomy, save_parquet

COVER = (pd.Timestamp('2017-01-01'), pd.Timestamp('2021-06-30'))     # days collected in data/raw/gdelt_weekly_2017_2021H1.parquet
raw = pq.read_table(f'{D}/raw/gdelt_weekly_2017_2021H1.parquet').to_pandas(ignore_metadata=True)
raw['week'] = pd.to_datetime(raw.week)
assert (raw.week.dt.weekday == 0).all(), 'weeks must start on Monday'

tot = raw.groupby('week').mentions.sum().rename('total_mentions').reset_index()
tot['days_covered'] = [int(((pd.date_range(w, periods=7) >= COVER[0]) & (pd.date_range(w, periods=7) <= COVER[1])).sum()) for w in tot.week]
tot['partial_week'] = tot.days_covered < 7
save_parquet(tot, f'{GD}/weekly_total.parquet')

M = pd.read_parquet(f'{GD}/code_map.parquet')
V, N = load_taxonomy()
label = dict(zip(N.node_id, N.label))
x = raw.merge(M[['code', 'value', 'narrow_id', 'mid_id', 'broad_id']], left_on='theme', right_on='code', how='inner')
for c in ['tone', 'positive', 'negative']:
    x[c + '_w'] = x[c] * x.mentions
weeks = tot.week.sort_values().to_numpy()


def aggregate(df, key):
    g = df.groupby([key, 'week']).agg(mentions=('mentions', 'sum'), n_codes=('code', 'nunique'), tone_w=('tone_w', 'sum'),
                                     positive_w=('positive_w', 'sum'), negative_w=('negative_w', 'sum')).reset_index()
    full = pd.MultiIndex.from_product([sorted(df[key].dropna().unique()), weeks], names=[key, 'week']).to_frame(index=False)
    g = full.merge(g, on=[key, 'week'], how='left').fillna({'mentions': 0, 'n_codes': 0})
    for c in ['tone', 'positive', 'negative']:
        g[c] = np.where(g.mentions > 0, g[c + '_w'] / g.mentions.replace(0, np.nan), np.nan)
    g = g.drop(columns=['tone_w', 'positive_w', 'negative_w']).merge(tot, on='week', how='left')
    g['share'] = g.mentions / g.total_mentions
    return g


parts = []
for lvl, col in [(3, 'narrow_id'), (2, 'mid_id'), (1, 'broad_id')]:
    a = aggregate(x[x[col].notna()], col).rename(columns={col: 'node_id'})
    a['level'] = lvl
    parts.append(a)
W = pd.concat(parts, ignore_index=True)
W['label'] = W.node_id.map(label)
W['source'] = 'gdelt'
W = W[['source', 'level', 'node_id', 'label', 'week', 'mentions', 'share', 'tone', 'positive', 'negative', 'n_codes', 'total_mentions',
       'days_covered', 'partial_week']]
save_parquet(W, f'{GD}/weekly_node.parquet')
Wv = aggregate(x, 'value').merge(V[['theme', 'node_id']].rename(columns={'theme': 'value'}), on='value', how='left')
Wv['source'] = 'gdelt'
save_parquet(Wv, f'{GD}/weekly_value.parquet')

full = W[~W.partial_week]
cov = full.groupby(['level', 'node_id']).mentions.median().reset_index()
print('weeks', len(weeks), 'partial', tot.partial_week.sum(), tot[tot.partial_week].week.dt.date.tolist())
print('nodes with GDELT codes by level', W.groupby('level').node_id.nunique().to_dict())
print('nodes with median weekly mentions >= 100 (all full weeks):', cov[cov.mentions >= 100].groupby('level').size().to_dict())
