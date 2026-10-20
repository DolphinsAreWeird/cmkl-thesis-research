# 14. Live test, comparison lists for October 2026 (examiner review, 20 Oct): the library's own lists, frozen before the library
# releases September or October 2026, so the Wikipedia list frozen at 17:01 can be judged against them, not only against chance.
# Library model: Test A's H_lgbm (library history only, change target, trained on every Test A row whose target month is at most
# 2026-08), applied at origin August 2026 (the latest released month), i.e. two months before October.
# Persistence list: books ranked by ln(1 + L(Aug)) - ln(1 + M6 over Mar-Aug 2026).
# Books: the same 7,650 books as the Wikipedia list (at least one loan in 2025-09 to 2026-08).
# Output: prereg/live_alert/library_list_2026-10.csv, persistence_list_2026-10.csv, library_rankings_all_2026-10.csv
import sys, pathlib
import numpy as np, pandas as pd
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
OUT = D / 'db' / 'wiki_led'
LIVE = ROOT / 'prereg' / 'live_alert'
SEED = 20261020
HC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)
T = 2026 * 12 + 7                                                        # origin month August 2026

W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
C = pd.read_parquet(D / 'db' / 'study2r' / 'counts_work.parquet')
L = C.groupby(['work_id', 'mi']).y.sum().unstack('mi')
first = L.apply(lambda r: r[r > 0].index.min(), axis=1)
P = pd.read_parquet(D / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok']).drop_duplicates()
EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi']}
months = list(range(T - 11, T + 1))
Lm = L.reindex(columns=months).fillna(0)
for m in months:                                                         # months before the first loan: not in the collection
    Lm.loc[first > m, m] = np.nan
elig_ids = Lm.index[Lm.sum(axis=1) > 0]
X = pd.DataFrame(index=elig_ids)
win6 = [m for m in range(T - 5, T + 1) if m not in EXCL]
win12 = [m for m in range(T - 11, T + 1) if m not in EXCL]
X['L_t'] = Lm.loc[elig_ids, T]
X['M6'] = Lm.loc[elig_ids, win6].median(axis=1)
X['h_lt'] = np.log1p(X.L_t)
X['h_lt1'] = np.log1p(Lm.loc[elig_ids, T - 1].fillna(0))
X['h_m6'] = np.log1p(X.M6)
X['h_m12'] = np.log1p(Lm.loc[elig_ids, win12].mean(axis=1))
X['h_lyago'] = np.log1p(Lm.loc[elig_ids, T - 11].fillna(0))
X['h_age'] = T - first.reindex(elig_ids)
X = X.dropna(subset=['h_lt', 'h_m6'])
R = pd.read_parquet(OUT / 'test_a_rows.parquet')
tr = R[(R.mi + 1) <= 2026 * 12 + 7]
model = lgb.LGBMRegressor(**LGB).fit(tr[HC], tr.D)
X['library_score'] = model.predict(X[HC])
X['persistence_score'] = X.h_lt - X.h_m6
X = X.join(W.set_index('work_id')[['title', 'creator']])
wl = pd.read_csv(LIVE / 'ranking_all_2026-10.csv')
X = X[X.index.isin(wl.work_id)]                                          # the same books as the Wikipedia list
for name, col in (('library', 'library_score'), ('persistence', 'persistence_score')):
    Y = X.sort_values(col, ascending=False).reset_index().rename(columns={'index': 'work_id'})
    Y['rank'] = np.arange(1, len(Y) + 1)
    Y.head(50)[['rank', 'work_id', 'title', 'creator', col, 'L_t', 'M6']].to_csv(LIVE / f'{name}_list_2026-10.csv', index=False, float_format='%.4f')
    X[f'{name}_rank'] = X[col].rank(ascending=False, method='first').astype(int)
X.reset_index().rename(columns={'index': 'work_id'})[['work_id', 'library_score', 'library_rank', 'persistence_score', 'persistence_rank']] \
    .to_csv(LIVE / 'library_rankings_all_2026-10.csv', index=False, float_format='%.6f')
print('books', len(X), 'training rows', len(tr))
print(X.sort_values('library_score', ascending=False).head(10)[['title', 'creator', 'L_t', 'M6']].to_string())
