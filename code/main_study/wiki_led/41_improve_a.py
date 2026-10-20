# 41. Improvement round v1 (existing books): tune on test years 2019-2023, choose by the fixed rule, run the chosen once on 2024-2026.
# Settings: prereg/addenda_wiki_led/2026-10-20_c_improvement_round.json (read-only; SHA-256 in prereg/README.md).
# Output: data/reports/wiki_led_improve_a.json, data/db/wiki_led/improve_a_preds.parquet
import sys, json, time, pathlib, hashlib
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
ADD = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_c_improvement_round.json'
assert hashlib.sha256(ADD.read_bytes()).hexdigest() == 'b6a7319372f57be6d9c337f7fcda2467f46b7ba3085513a6068a15f200023dac'
OUT, REP = D / 'db' / 'wiki_led', D / 'reports'
SEED = 20261020
T0 = time.time()
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
EXTRA = ['yoy4', 'peakr', 'spike4', 'age', 'd1']
W0C = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS]
W1C = W0C + ['b_' + c for c in EXTRA] + ['a_' + c for c in EXTRA] + ['b_minus_a']
HC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
BASE = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
            colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


R = pd.read_parquet(OUT / 'test_a_rows.parquet')
X = pd.read_parquet(OUT / 'extra_wiki_features.parquet')
for kind, key, pre in (('book', 'article', 'b_'), ('author', 'author_article', 'a_')):
    x = X[X.kind == kind].drop(columns='kind').rename(columns={'article': key, **{c: pre + c for c in EXTRA}})
    R = R.merge(x, on=[key, 'mi'], how='left')
R['b_minus_a'] = R.b_lvl4 - R.a_lvl4
R['rel'] = np.where(R.Sg == 1, 2, np.where(R.D >= np.log(1.5), 1, 0))
R['rose'] = (R.D >= np.log(1.5)).astype(int)
R = R.sort_values(['mi', 'work_id']).reset_index(drop=True)
log('rows', len(R))

CONFIGS = {
    'W0': (W0C, 'reg', {}), 'W1': (W1C, 'reg', {}), 'W2': (W1C, 'rank', {}),
    'W3a': (W1C, 'reg', dict(num_leaves=15, min_child_samples=200, n_estimators=600, learning_rate=0.03)),
    'W3b': (W1C, 'reg', dict(num_leaves=63, min_child_samples=200, n_estimators=600, learning_rate=0.03)),
    'W3c': (W1C, 'reg', dict(num_leaves=31, min_child_samples=200, n_estimators=600, learning_rate=0.03)),
    'HW0': (HC + W0C, 'reg', {}), 'HW1': (HC + W1C, 'reg', {}), 'HW2': (HC + W1C, 'rank', {}),
}
FAMILY = {'W': ['W0', 'W1', 'W2', 'W3a', 'W3b', 'W3c'], 'HW': ['HW0', 'HW1', 'HW2']}
SIMPLE = ['W0', 'W1', 'W3a', 'W3c', 'W3b', 'W2', 'HW0', 'HW1', 'HW2']        # order of simplicity for ties


def fit_predict(cfg, tr, te):
    cols, kind, extra = CONFIGS[cfg]
    params = {**BASE, **extra}
    if kind == 'reg':
        return lgb.LGBMRegressor(**params).fit(tr[cols], tr.D).predict(te[cols])
    grp = tr.groupby('mi').size().values
    m = lgb.LGBMRanker(objective='lambdarank', **params).fit(tr[cols], tr.rel, group=grp)
    return m.predict(te[cols])


def score(P, col):
    alert, rank = [], []
    for m, g in P.groupby('mi'):
        alert.append(g.nlargest(20, col).rose.mean())
        rank.append(spearmanr(g[col], g.D).statistic)
    return dict(alert20=float(np.mean(alert)), change_rank=float(np.mean(rank)),
                surge_ap_ratio=float(average_precision_score(P.Sg, P[col]) / P.Sg.mean()))


def run(cfgs, years):
    out = []
    for Y in years:
        te = R[(R.year == Y)]
        tr = R[(R.mi + 1) < Y * 12]
        p = te[['work_id', 'mi', 'year', 'D', 'Sg', 'rose']].copy()
        for c in cfgs:
            p[c] = fit_predict(c, tr, te)
        out.append(p)
        log('year', Y, 'done', cfgs)
    return pd.concat(out, ignore_index=True)


res = {'tuning_2019_2023': {}, 'chosen': {}, 'check_2024_2026': {}}
P = run(list(CONFIGS), range(2019, 2024))
for c in CONFIGS:
    res['tuning_2019_2023'][c] = score(P, c)
    log('tuning', c, res['tuning_2019_2023'][c])
for fam, cs in FAMILY.items():
    best = max(res['tuning_2019_2023'][c]['alert20'] for c in cs)
    near = [c for c in cs if res['tuning_2019_2023'][c]['alert20'] >= best - 0.005]
    res['chosen'][fam] = sorted(near, key=SIMPLE.index)[0]
log('chosen', res['chosen'])
Q = run(['W0', 'HW0'] + [c for c in res['chosen'].values() if c not in ('W0', 'HW0')], range(2024, 2027))
for c in Q.columns:
    if c in CONFIGS:
        res['check_2024_2026'][c] = score(Q, c)
        log('check', c, res['check_2024_2026'][c])
pd.concat([P.assign(phase='tuning'), Q.assign(phase='check')]).to_parquet(OUT / 'improve_a_preds.parquet', index=False)
res['runtime_s'] = round(time.time() - T0)
(REP / 'wiki_led_improve_a.json').write_text(json.dumps(res, indent=1))
log('done')
