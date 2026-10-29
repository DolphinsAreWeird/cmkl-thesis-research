# 92. Course (AIC-400) checklist items 6.1 and 6.4 on Test A, tuning years only (test years 2019-2023; later years untouched).
# Residual = actual change D minus the library-only LightGBM forecast (Hlgbm_D), each year predicted by a model fitted
# on earlier years only, so these are out-of-sample residuals. Read-only, descriptive; prints its tables.
# Run from code/:  nice ../.venv/bin/python main_study/wiki_led/92_residuals_2019_2023.py
import pandas as pd, numpy as np, sys
from scipy.stats import spearmanr
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))   # code/, for config
from config import D
P = pd.read_parquet(f'{D}/db/wiki_led/test_a_preds_c.parquet', columns=['work_id', 'mi', 'year', 'D', 'Hlgbm_D', 'HWlgbm_D'])
P = P[P.year <= 2023]
R = pd.read_parquet(f'{D}/db/wiki_led/test_a_rows_c.parquet')
X = P.merge(R.drop(columns=['D', 'year']), on=['work_id', 'mi'], how='left')
X['res'] = X.D - X.Hlgbm_D
X['res_hw'] = X.D - X.HWlgbm_D
print('rows', len(X), 'years', X.year.min(), X.year.max(), '| mean residual', round(X.res.mean(), 4), 'sd', round(X.res.std(), 4))
moy = (X.mi - 12 * X.year) % 12
print('mi - 12*year values (sample):', sorted(moy.unique())[:12])
X['target_moy'] = (moy + 1) % 12 + 1   # origin month-of-year is moy+1 if mi = 12*year + month - 1; target is the next month
def tab(col, bins=None, q=None):
    c = X[col] if bins is None and q is None else (pd.cut(X[col], bins) if bins is not None else pd.qcut(X[col], q, duplicates='drop'))
    g = X.groupby(c, observed=True).agg(n=('res', 'size'), res_H=('res', 'mean'), res_HW=('res_hw', 'mean'))
    print(f'\n-- residual by {col}'); print(g.round(4).to_string())
tab('target_moy')
tab('h_age', q=8)
tab('L_t', bins=[-1, 0, 2, 5, 10, 20, 50, 1e9])
X['b_risen'] = (X.b_nrise8 > 0).map({True: 'book page rose in last 8 weeks', False: 'no rise'}).where(X.b_nrise8.notna(), 'no book feature')
X['a_risen'] = (X.a_nrise8 > 0).map({True: 'author page rose in last 8 weeks', False: 'no rise'}).where(X.a_nrise8.notna(), 'no author feature')
tab('b_risen'); tab('a_risen')
print('\n-- Spearman of H residual with features not in H')
for c in ['b_dw', 'a_dw', 'b_r4', 'a_r4', 'b_lvl4', 'a_lvl4', 'b_chg', 'a_chg']:
    m = X[c].notna()
    print(f'{c}: rho {spearmanr(X.loc[m, c], X.loc[m, "res"]).statistic:+.4f} (n {m.sum():,})')
print('\n-- 6.4: pairs of Wikipedia features with |Spearman| >= 0.8 (rows 2019-2023)')
F = [c for c in R.columns if c[:2] in ('b_', 'a_')]
C = X[F].corr(method='spearman')
pairs = [(a, b, C.loc[a, b]) for i, a in enumerate(F) for b in F[i + 1:] if abs(C.loc[a, b]) >= 0.8]
for a, b, v in sorted(pairs, key=lambda t: -abs(t[2])):
    print(f'{a} ~ {b}: {v:+.3f}')
print('pairs >= 0.8:', len(pairs), 'of', len(F) * (len(F) - 1) // 2)
