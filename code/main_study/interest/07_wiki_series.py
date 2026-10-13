# 07. Weekly Wikipedia interest per theme value and per narrow, middle and broad node.
# An article's daily views = views of its canonical title + views of the redirects kept by the screen in 06 (old titles
# after a move, merged pages, and redirects with real traffic). A day missing from the API answer counts as 0 views.
# interest share = weekly views of the node's articles (each article once per node) / total English Wikipedia user views
# that week. Weeks are ISO weeks starting Monday; the first (29 Jun 2015, 5 days) and last (28 Sep 2026, 3 days) weeks are
# partial and flagged. top_day_share = largest single day / weekly views of the node: a value near 1 means one day carried
# the week (a one-day news spike, a Google doodle, or automated traffic labelled as user); it is a flag, nothing is removed.
# Outputs: data/db/interest/wiki/weekly_node.parquet, weekly_value.parquet, weekly_total.parquet, article_daily_summary.csv
import hashlib, os, numpy as np, pandas as pd
from _ci import WK, load_taxonomy, ancestors, save_parquet

COVER = (pd.Timestamp('2015-07-01'), pd.Timestamp('2026-09-30'))
days = pd.date_range(*COVER, freq='D')


def fid(title):
    return hashlib.sha1(title.encode()).hexdigest()[:16]


def load(title):
    f = f'{WK}/pv_daily/{fid(title)}.parquet'
    if not os.path.exists(f):
        return None
    d = pd.read_parquet(f)
    return d.set_index('date').views.reindex(days, fill_value=0).astype(float)


A = pd.read_parquet(f'{WK}/articles.parquet')
S = pd.read_parquet(f'{WK}/redirect_screen.parquet') if os.path.exists(f'{WK}/redirect_screen.parquet') else pd.DataFrame(columns=['canonical', 'redirect', 'keep'])
kept = S[S.keep == True].groupby('canonical').redirect.apply(list).to_dict()  # noqa: E712
V, N = load_taxonomy()
label = dict(zip(N.node_id, N.label))

art = {}
summ = []
for t in sorted(A.canonical.dropna().unique()):
    s = load(t)
    if s is None:
        summ.append(dict(article=t, fetched=False)); continue
    own = s.copy()
    for r in kept.get(t, []):
        x = load(r)
        if x is not None:
            s = s + x
    art[t] = s
    nz = own[own > 0]
    summ.append(dict(article=t, fetched=True, own_total=own.sum(), with_redirects_total=s.sum(), n_redirects_kept=len(kept.get(t, [])),
                     redirect_share=1 - own.sum() / s.sum() if s.sum() else np.nan,
                     first_day_with_views=nz.index.min() if len(nz) else None,
                     zero_days_after_first=int((own[own.index >= (nz.index.min() if len(nz) else days[0])] == 0).sum()),
                     median_daily=float(s.median())))
pd.DataFrame(summ).to_csv(f'{WK}/article_daily_summary.csv', index=False)
print('articles with daily data', len(art), 'of', A.canonical.nunique())

tot = pd.read_parquet(f'{WK}/total_daily.parquet').set_index('date').views.reindex(days).astype(float)
wk = (days - pd.to_timedelta(days.weekday, unit='D'))
T = pd.DataFrame({'week': wk, 'total_views': tot.values}).groupby('week').agg(total_views=('total_views', 'sum'),
                                                                              days_covered=('total_views', 'size')).reset_index()
T['partial_week'] = T.days_covered < 7
save_parquet(T, f'{WK}/weekly_total.parquet')


def weekly(titles):
    titles = [t for t in dict.fromkeys(titles) if t in art]
    if not titles:
        return None
    s = sum(art[t] for t in titles)
    df = pd.DataFrame({'week': wk, 'views': s.values})
    g = df.groupby('week').views.agg(['sum', 'max']).reset_index().rename(columns={'sum': 'views', 'max': 'top_day'})
    g['top_day_share'] = np.where(g.views > 0, g.top_day / g.views.replace(0, np.nan), np.nan)
    g['n_articles'] = len(titles)
    return g.drop(columns='top_day')


vals_art = A.groupby('theme').canonical.apply(lambda s: list(dict.fromkeys(s.dropna()))).to_dict()
rows = []
for t, titles in vals_art.items():
    g = weekly(titles)
    if g is not None:
        g['value'] = t; rows.append(g)
Wv = pd.concat(rows).merge(T, on='week', how='left')
Wv['share'] = Wv.views / Wv.total_views
Wv = Wv.merge(V[['theme', 'node_id']].rename(columns={'theme': 'value'}), on='value', how='left')
Wv['source'] = 'wikipedia'
save_parquet(Wv, f'{WK}/weekly_value.parquet')

node_art = {}
for t, titles in vals_art.items():
    nid = V.set_index('theme').node_id[t]
    for a in ancestors(nid):
        node_art.setdefault(a, []).extend(titles)
rows = []
for nid, titles in node_art.items():
    g = weekly(titles)
    if g is not None:
        g['node_id'] = nid; g['level'] = nid.count('.') + 1; rows.append(g)
W = pd.concat(rows).merge(T, on='week', how='left')
W['share'] = W.views / W.total_views
W['label'] = W.node_id.map(label)
W['source'] = 'wikipedia'
W = W[['source', 'level', 'node_id', 'label', 'week', 'views', 'share', 'top_day_share', 'n_articles', 'total_views', 'days_covered', 'partial_week']]
save_parquet(W, f'{WK}/weekly_node.parquet')
full = W[~W.partial_week]
cov = full.groupby(['level', 'node_id']).views.median().reset_index()
print('weeks', T.week.nunique(), 'partial', T[T.partial_week].week.dt.date.tolist())
print('nodes with articles by level', W.groupby('level').node_id.nunique().to_dict())
print('nodes with median weekly views >= 1000:', cov[cov.views >= 1000].groupby('level').size().to_dict())
