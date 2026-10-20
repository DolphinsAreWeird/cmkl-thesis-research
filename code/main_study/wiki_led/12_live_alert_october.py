# 12. Live test: the Wikipedia-only alert list for October 2026, made from Wikipedia views to 30 September 2026 and frozen before
# the library releases September or October 2026. Same features and model as Test A (W_lgbm, change target D), trained on every
# Test A row whose target month is at most 2026-08 (the last released month).
# Eligible books: the Test A books with at least one loan in 2025-09 to 2026-08.
# Output: prereg/live_alert/alert_list_2026-10.csv (top 50 with rank, score and reasons) and the full ranking
#         data/db/wiki_led/live_alert_2026-10_all.parquet; the scoring rule is in prereg/live_alert/README.md.
import sys, time, pathlib, importlib.util
import numpy as np, pandas as pd
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
OUT = D / 'db' / 'wiki_led'
LIVE = ROOT / 'prereg' / 'live_alert'
LIVE.mkdir(parents=True, exist_ok=True)
SEED = 20261020
EPS = 1e-12
T0 = time.time()
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
WCOLS = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS]
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)
ORIGIN = 2026 * 12 + 8                                                   # September 2026
END = (pd.Timestamp('2026-09-30')).to_datetime64()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def article_features(g):                                                # identical to 10_test_a.py, one origin
    g = g.set_index('week').sort_index()
    grid = pd.date_range(g.index.min(), g.index.max(), freq='7D')
    s = g['share'].reindex(grid).astype(float)
    v = g['valid'].reindex(grid).astype(float)
    m4 = s.rolling(4, min_periods=1).mean()
    normal = s.shift(4).rolling(26, min_periods=13).median()
    nrm_w = s.shift(1).rolling(26, min_periods=13).median()
    ratio_w = (s + EPS) / (nrm_w + EPS)
    up = (ratio_w >= 1.5) & nrm_w.notna() & s.notna()
    upv = up.values.astype(int)
    runlen = np.zeros(len(upv), int)
    for i in range(len(upv)):
        runlen[i] = (runlen[i - 1] + 1 if i else 1) if upv[i] else 0
    contrib = pd.Series(np.where(upv == 1, np.log(ratio_w.values) * np.minimum(runlen, 4) / 4, 0.0), index=grid)
    f = pd.DataFrame({
        'lvl4': np.log(m4.clip(lower=EPS)), 'r4': np.log((m4 + EPS) / (normal + EPS)),
        'r1': np.log((s + EPS) / (normal + EPS)), 'rmax': np.log((s + EPS) / (normal + EPS)).rolling(4, min_periods=1).max(),
        'nrise8': up.astype(int).rolling(8, min_periods=1).sum(), 'run': pd.Series(runlen, index=grid),
        'dw': contrib.rolling(8, min_periods=1).sum(),
        'chg': np.log((m4 + EPS) / (s.shift(4).rolling(4, min_periods=1).mean() + EPS)),
        'valid4': v.rolling(4, min_periods=1).mean()}, index=grid)
    f.loc[normal.isna(), ['r4', 'r1', 'rmax']] = np.nan
    wend = (grid + pd.Timedelta(days=6)).values
    i = np.searchsorted(wend, END, side='right') - 1
    if i < 0 or (END - wend[i]) > np.timedelta64(13, 'D'):
        return None
    out = f.iloc[i].to_dict()
    out['views_last_week'] = float(g['views'].reindex(grid).iloc[i]) if 'views' in g else np.nan
    return out


def features(path, names):
    X = pd.read_parquet(path, columns=['article', 'week', 'share', 'valid', 'views'])
    X = X[X.article.isin(names)]
    X['week'] = pd.to_datetime(X['week'])
    rows = {}
    for a, g in X.groupby('article', sort=False):
        r = article_features(g)
        if r is not None:
            rows[a] = r
    return pd.DataFrame.from_dict(rows, orient='index')


W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
C = pd.read_parquet(D / 'db' / 'study2r' / 'counts_work.parquet')
recent = C[(C.mi >= 2025 * 12 + 8) & (C.mi <= 2026 * 12 + 7)].groupby('work_id').y.sum()
elig = W[W.work_id.isin(recent[recent > 0].index)].copy()
log('eligible books', len(elig))
fb = features(D / 'db' / 'study2r' / 'weekly_book.parquet', set(elig.article.dropna())).add_prefix('b_')
fa = features(D / 'db' / 'study2r' / 'weekly_author.parquet', set(elig.author_article.dropna())).add_prefix('a_')
X = elig.merge(fb, left_on='article', right_index=True, how='left').merge(fa, left_on='author_article', right_index=True, how='left')
log('features', X.shape, 'with book features', X.b_lvl4.notna().mean().round(3))

R = pd.read_parquet(OUT / 'test_a_rows.parquet')
tr = R[(R.mi + 1) <= 2026 * 12 + 7]                                      # target month at most 2026-08
model = lgb.LGBMRegressor(**LGB).fit(tr[WCOLS], tr.D)
X['score'] = model.predict(X[WCOLS])
X = X.sort_values('score', ascending=False).reset_index(drop=True)
X['rank'] = np.arange(1, len(X) + 1)
X['book_views_vs_normal'] = np.exp(X.b_r4).round(2)
X['author_views_vs_normal'] = np.exp(X.a_r4).round(2)
X['book_weeks_rising'] = X.b_run
X['author_weeks_rising'] = X.a_run
X.to_parquet(OUT / 'live_alert_2026-10_all.parquet', index=False)
cols = ['rank', 'work_id', 'title', 'creator', 'article', 'author_article', 'score', 'book_views_vs_normal', 'book_weeks_rising',
        'author_views_vs_normal', 'author_weeks_rising', 'b_views_last_week', 'a_views_last_week']
X.head(50)[cols].to_csv(LIVE / 'alert_list_2026-10.csv', index=False, float_format='%.4f')
X[['rank', 'work_id', 'score']].to_csv(LIVE / 'ranking_all_2026-10.csv', index=False, float_format='%.6f')
log('training rows', len(tr), '| wrote top 50 and full ranking of', len(X))
print(X.head(20)[['rank', 'title', 'creator', 'book_views_vs_normal', 'author_views_vs_normal']].to_string(index=False))
