# 40. Extra Wikipedia features for the improvement round (data only: no model, no relation to loans).
# From the same weekly series as Test A (data/db/study2r/weekly_book.parquet, weekly_author.parquet), at every origin month
# 2016-03 to 2026-09, using only weeks that ended on or before the last day of the origin month:
#   yoy4    ln(mean share of the last 4 weeks / mean share of the same 4 weeks one year earlier)      (yearly cycles: school terms)
#   peakr   ln(mean share of the last 4 weeks / max 4-week mean over the previous 104 weeks)        (novelty: highest ever?)
#   spike4  max over the last 4 weeks of the top-day share of the week (one-day spikes)
#   age     weeks since the article's first week with views (new articles)
#   d1      ln(last week / week before)                                                                (acceleration)
# Output: data/db/wiki_led/extra_wiki_features.parquet (article, kind, mi, features)
import sys, time, pathlib
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
OUT = D / 'db' / 'wiki_led'
EPS = 1e-12
T0 = time.time()
ORIGINS = np.arange(2016 * 12 + 2, 2026 * 12 + 9)


def month_end(mi):
    y, m = divmod(int(mi), 12)
    return pd.Timestamp(year=y, month=m + 1, day=1) + pd.offsets.MonthEnd(0)


ENDS = np.array([month_end(m) for m in ORIGINS], dtype='datetime64[ns]')


def feats(g):
    g = g.set_index('week').sort_index()
    grid = pd.date_range(g.index.min(), g.index.max(), freq='7D')
    s = g['share'].reindex(grid).astype(float)
    td = g['top_day_share'].reindex(grid).astype(float)
    m4 = s.rolling(4, min_periods=1).mean()
    f = pd.DataFrame({
        'yoy4': np.log((m4 + EPS) / (m4.shift(52) + EPS)),
        'peakr': np.log((m4 + EPS) / (m4.shift(4).rolling(104, min_periods=26).max() + EPS)),
        'spike4': td.rolling(4, min_periods=1).max(),
        'age': pd.Series(np.arange(len(grid)), index=grid, dtype=float),
        'd1': np.log((s + EPS) / (s.shift(1) + EPS)),
    }, index=grid)
    wend = (grid + pd.Timedelta(days=6)).values
    idx = np.searchsorted(wend, ENDS, side='right') - 1
    ok = idx >= 0
    out = f.iloc[idx[ok]].copy()
    out['mi'] = ORIGINS[ok]
    stale = (ENDS[ok] - wend[idx[ok]]) > np.timedelta64(13, 'D')
    out.loc[stale, ['yoy4', 'peakr', 'spike4', 'd1']] = np.nan
    return out.reset_index(drop=True)


W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
parts = []
for kind, path, names in (('book', 'weekly_book.parquet', set(W.article.dropna())),
                          ('author', 'weekly_author.parquet', set(W.author_article.dropna()))):
    X = pd.read_parquet(D / 'db' / 'study2r' / path, columns=['article', 'week', 'share', 'top_day_share'])
    X = X[X.article.isin(names)]
    X['week'] = pd.to_datetime(X['week'])
    for a, g in X.groupby('article', sort=False):
        h = feats(g)
        h.insert(0, 'article', a)
        h.insert(1, 'kind', kind)
        parts.append(h)
    print(time.strftime('%H:%M:%S'), kind, 'done', round(time.time() - T0), 's', flush=True)
F = pd.concat(parts, ignore_index=True)
F.to_parquet(OUT / 'extra_wiki_features.parquet', index=False)
print('rows', len(F), F.describe().round(2).to_string())
