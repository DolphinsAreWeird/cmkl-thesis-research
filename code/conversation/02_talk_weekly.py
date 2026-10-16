# Conversation sources, talk pages, step 2: weekly talk-page edit series per theme value and per narrow, middle and broad node.
# Mirrors code/main_study/interest/07_wiki_series.py: an article's value is its canonical title (a theme value's articles are
# the 'main' and 'related' pages in articles.parquet); a node's articles are those of every value below it, each article once
# per node; ISO weeks starting Monday; the first week (29 Dec 2014, 3 days) and the last (28 Sep 2026, 3 days) are partial.
# Edits counted = human edits (registered + anonymous), bots left out. The bot edits are kept in their own column.
# Normaliser: the API has no total for talk pages only (the edits/aggregate endpoint offers page types all, content and
# non-content, no namespace; non-content mixes in user, project and other namespaces), so the share is
#   share = human talk edits this week / mean of human talk edits of the same series in the previous 52 full weeks
# (at least 26 of them), as the record says for this case. The mean excludes the current week.
# Outputs (data/db/interest/talk_edits/): weekly_node.parquet, weekly_value.parquet, article_summary.csv
import os, sys, json, pathlib, hashlib, numpy as np, pandas as pd
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'main_study' / 'interest'))
from _ci import load_taxonomy, ancestors, save_parquet, D  # noqa: E402

CACHE = pathlib.Path(f'{D}/interim/talk_edits_cache')
OUT = f'{D}/db/interest/talk_edits'
os.makedirs(OUT, exist_ok=True)
COVER = (pd.Timestamp('2015-01-01'), pd.Timestamp('2026-09-30'))
days = pd.date_range(*COVER, freq='D')
wk = days - pd.to_timedelta(days.weekday, unit='D')
TYPES = ['user', 'anonymous', 'group-bot', 'name-bot']


def fid(title, typ):
    return hashlib.sha1(f'Talk:{title}|{typ}'.encode()).hexdigest()[:20] + '.json'


def load(title, typ):
    d = json.loads((CACHE / fid(title, typ)).read_text())['daily']
    s = pd.Series(d, dtype=float)
    s.index = pd.to_datetime(s.index)
    return s.reindex(days, fill_value=0).astype(float)


A = pd.read_parquet(f'{D}/db/interest/wiki/articles.parquet')
V, N = load_taxonomy()
label = dict(zip(N.node_id, N.label))
human, bots, summ = {}, {}, []
for t in sorted(A.canonical.dropna().unique()):
    if not all((CACHE / fid(t, y)).exists() for y in TYPES):
        raise SystemExit(f'cache incomplete for {t}')
    h = load(t, 'user') + load(t, 'anonymous')
    b = load(t, 'group-bot') + load(t, 'name-bot')
    human[t] = h.to_numpy(); bots[t] = b.to_numpy()
    summ.append(dict(article=t, human_edits=h.sum(), bot_edits=b.sum(), human_edits_2016_on=h[h.index >= '2016-01-01'].sum(),
                     days_with_edits=int((h > 0).sum())))
pd.DataFrame(summ).to_csv(f'{OUT}/article_summary.csv', index=False)
print('articles', len(human), flush=True)

week_idx = pd.Series(wk)
T = pd.DataFrame({'week': wk}).groupby('week').size().rename('days_covered').reset_index()
T['partial_week'] = T.days_covered < 7


def weekly(titles, key):
    titles = [t for t in dict.fromkeys(titles) if t in human]
    if not titles:
        return None
    h = np.sum([human[t] for t in titles], axis=0); b = np.sum([bots[t] for t in titles], axis=0)
    g = pd.DataFrame({'week': wk, 'edits': h, 'bot_edits': b}).groupby('week').sum().reset_index()
    g = g.merge(T, on='week')
    e = pd.Series(np.where(g.partial_week, np.nan, g.edits))
    m = e.shift(1).rolling(52, min_periods=26).mean()
    g['trailing_mean_52'] = m.to_numpy()
    g['share'] = np.where((m > 0) & ~g.partial_week, g.edits / m.where(m > 0), np.nan)
    g['n_articles'] = len(titles)
    return g


vals_art = A.groupby('theme').canonical.apply(lambda s: list(dict.fromkeys(s.dropna()))).to_dict()
rows = []
for t, titles in vals_art.items():
    g = weekly(titles, t)
    g['value'] = t; rows.append(g)
Wv = pd.concat(rows, ignore_index=True).merge(V[['theme', 'node_id']].rename(columns={'theme': 'value'}), on='value', how='left')
Wv['source'] = 'talk_edits'
save_parquet(Wv, f'{OUT}/weekly_value.parquet')

node_art = {}
for t, titles in vals_art.items():
    for a in ancestors(V.set_index('theme').node_id[t]):
        node_art.setdefault(a, []).extend(titles)
rows = []
for nid, titles in node_art.items():
    g = weekly(titles, nid)
    g['node_id'] = nid; g['level'] = nid.count('.') + 1; rows.append(g)
W = pd.concat(rows, ignore_index=True)
W['label'] = W.node_id.map(label); W['source'] = 'talk_edits'
W = W[['source', 'level', 'node_id', 'label', 'week', 'edits', 'bot_edits', 'trailing_mean_52', 'share', 'n_articles', 'days_covered', 'partial_week']]
save_parquet(W, f'{OUT}/weekly_node.parquet')
full = W[~W.partial_week & (W.week >= '2016-01-04')]
med = full.groupby(['level', 'node_id']).edits.median().reset_index()
print('nodes by level', W.groupby('level').node_id.nunique().to_dict())
print('nodes with median weekly human talk edits >= 20 (2016 on):', med[med.edits >= 20].groupby('level').size().to_dict())
