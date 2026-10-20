# 13. Descriptive panels of Test A (added after the main scores were seen; logged in prereg/DEVIATIONS.md): accuracy of the
# level predictions against next month's actual loans, and the monthly alert lists (top 20 / top 50 by predicted rise).
# Reproduces data/reports/wiki_led_test_a_accuracy.csv and wiki_led_test_a_alert_list.csv from data/db/wiki_led/test_a_preds.parquet.
import sys, pathlib
import numpy as np, pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
p = pd.read_parquet(D / 'db' / 'wiki_led' / 'test_a_preds.parquet')
r = pd.read_parquet(D / 'db' / 'wiki_led' / 'test_a_rows.parquet', columns=['work_id', 'mi', 'b_r4'])

# ---- accuracy panel (level task)
p['M6_Y'] = np.log1p(p.M6)
act = np.expm1(p.Y)
models = {'No information (average book)': 'N0_Y', 'Repeat last month': 'Hnaive_Y', 'Median of last 6 months': 'M6_Y',
          'Wikipedia only (ridge)': 'Wridge_Y', 'Wikipedia only (trees)': 'Wlgbm_Y', 'Library history (trees)': 'Hlgbm_Y',
          'Library + Wikipedia (trees)': 'HWlgbm_Y'}
up_act = np.sign(act - p.L_t)
top = p.groupby('mi').Y.transform(lambda s: s >= s.quantile(.9))
rows = []
for name, c in models.items():
    pr = np.expm1(p[c]).clip(lower=0)
    err = (pr - act).abs()
    r2 = 1 - ((p[c] - p.Y) ** 2).sum() / ((p.Y - p.Y.mean()) ** 2).sum()
    sp = np.mean([spearmanr(g[c], g.Y).statistic if g[c].nunique() > 1 else 0 for _, g in p.groupby('mi')])
    dirn = np.sign(pr - p.L_t)
    m = (up_act != 0) & (dirn != 0)
    ptop = p.groupby('mi')[c].transform(lambda s: s >= s.quantile(.9)) if p[c].nunique() > 1 else pd.Series(False, index=p.index)
    rows.append(dict(model=name, MAE_loans=err.mean(), median_err=err.median(), WAPE=err.sum() / act.sum(), within_2=(err <= 2).mean(),
                     within_25pct=((err <= 0.25 * act) & (act >= 4)).sum() / (act >= 4).sum(), R2_log=r2, rank_corr=sp,
                     direction_right=(dirn[m] == up_act[m]).mean() if m.any() else np.nan,
                     top10_hit=(ptop & top).sum() / max(ptop.sum(), 1)))
pd.DataFrame(rows).set_index('model').to_csv(D / 'reports' / 'wiki_led_test_a_accuracy.csv')
# note: "Repeat last month" never predicts a direction; its direction_right value comes from floating-point noise and is not used.

# ---- alert lists
q = p.merge(r, on=['work_id', 'mi'])
q['rose'] = (q.Y - np.log1p(q.M6)) >= np.log(1.5)
base = q.groupby('mi').rose.mean()
out = {}
for name, c in [('Wikipedia only', 'Wlgbm_D'), ('Wikipedia rule (no fitting)', 'Wrule_D'), ('Library record', 'Hlgbm_D'),
                ('Library + Wikipedia', 'HWlgbm_D')]:
    for k in (20, 50):
        g = q.sort_values(c, ascending=False).groupby('mi').head(k)
        hit = g.groupby('mi').rose.mean()
        out[(name, k)] = dict(rose=hit.mean(), surged=g.groupby('mi').Sg.mean().mean(), months_beating_base=(hit > base.reindex(hit.index)).mean())
fl = q[np.exp(q.b_r4) >= 3]
out[('Page views >= 3x normal (simple rule)', 'all')] = dict(rose=fl.rose.mean(), surged=fl.Sg.mean(), months_beating_base=np.nan)
pd.DataFrame(out).T.to_csv(D / 'reports' / 'wiki_led_test_a_alert_list.csv')
print('wrote the two panels')
