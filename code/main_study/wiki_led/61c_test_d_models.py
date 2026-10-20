# 61c. Test D models, CORRECTED RERUN (addendum e, prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json): 61_test_d_models.py on the
# rows of 60c_test_d_rows.py (data/db/wiki_led/test_d_rows_c.parquet, which carry the Wikipedia features of the corrected Test A: weeks before an
# article's first week with views are missing).  Same models, settings, seed, walk-forward and measures.
# Output: data/db/wiki_led/test_d_preds_c.parquet, data/reports/wiki_led_test_d_c.json.   Full run: bash jobs/bg.sh wl_test_d_c main_study/wiki_led/61c_test_d_models.py
#
# Original header of 61_test_d_models.py:
# 61. Test D (all books, by format): Test A's models and measures on a 25% sample of all Seattle works plus the Test A works,
# one series per work and format. Settings: prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json, test_D_all_books
# (read-only; SHA-256 in prereg/README.md). No tuning on Test D: Test A's LightGBM settings, walk-forward by year, formats pooled
# with format as a feature.
# Output: data/db/wiki_led/test_d_preds.parquet, data/reports/wiki_led_test_d.json
import sys, os, json, time, pathlib, hashlib, resource
import numpy as np, pandas as pd
from scipy.stats import spearmanr, beta
from sklearn.metrics import average_precision_score
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
ADD = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_d_v2_all_books_platforms.json'
assert hashlib.sha256(ADD.read_bytes()).hexdigest() == '5f7f4ef33070f466951c7e37491c17fc3f746d2cf0abad7c90be58a832ad4585'
ADD_E = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_e_corrections_robustness.json'
assert hashlib.sha256(ADD_E.read_bytes()).hexdigest() == '36f3605286b51b8123d791c1d59a7dc89356ec3bb66bfba6b9667327d31b3e52', 'addendum e changed'
os.nice(5)                                                               # machine rule: nice, one heavy job at a time
OUT, REP = D / 'db' / 'wiki_led', D / 'reports'
SEED = 20261020
T0 = time.time()
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
WC = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS] + ['fmt']
HC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'fmt']
HWC = HC + WC[:-1]
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)
FMTS = ['print', 'ebook', 'audiobook']


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


def peak_mb():                                                           # macOS reports ru_maxrss in bytes
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20


R = pd.read_parquet(OUT / 'test_d_rows_c.parquet')
R['fmt'] = R.format.map({f: i for i, f in enumerate(FMTS)}).astype('int8')
R['rose'] = (R.D >= np.log(1.5)).astype('int8')
R['not_yet'] = ((R.h_lt - R.h_m6) < np.log(1.5))
log('rows', len(R), R.format.value_counts().to_dict())

preds = []
for Y in range(2019, 2027):
    te = R[(R.year == Y) & (R.mi >= 2019 * 12)]
    tr = R[(R.mi + 1) < Y * 12]
    if te.empty:
        continue
    p = te[['work_id', 'format', 'mi', 'year', 'D', 'Sg', 'Y', 'rose', 'not_yet', 'L_t', 'in_test_a', 'has_book_page', 'has_author_page']].copy()
    p['naive'] = (te.h_lt - te.h_m6).values
    p['naive_Y'] = te.h_lt.values
    for name, cols in (('W', WC), ('H', HC), ('HW', HWC)):
        p[name] = lgb.LGBMRegressor(**LGB).fit(tr[cols], tr.D).predict(te[cols])
    for name, cols in (('H_Y', HC), ('HW_Y', HWC)):
        p[name] = lgb.LGBMRegressor(**LGB).fit(tr[cols], tr.Y).predict(te[cols])
    preds.append(p)
    log('year', Y, 'train', len(tr), 'test', len(te))
P = pd.concat(preds, ignore_index=True)
P.to_parquet(OUT / 'test_d_preds_c.parquet', index=False)
MODELS = ['W', 'H', 'HW', 'naive']


def cp(k, n):  # exact (Clopper-Pearson) 95% interval
    lo = beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return float(lo), float(hi)


def alert(df, col, k, by_format=True):
    keys = ['format', 'mi'] if by_format else ['mi']
    t = df.sort_values(col, ascending=False).groupby(keys, sort=False).head(k)
    hits, slots = int(t.rose.sum()), len(t)
    return dict(rose=hits / slots, surged=float(t.Sg.mean()), hits=hits, slots=slots, ci=cp(hits, slots))


res = {'n': {f: int((P.format == f).sum()) for f in FMTS}, 'base_rose': {}, 'base_surge': {}, 'alert': {}, 'early': {},
       'change_rank': {}, 'surge_ap_ratio': {}, 'accuracy': {}, 'q90': {}}
for f in FMTS + ['all']:
    q = P if f == 'all' else P[P.format == f]
    res['base_rose'][f] = float(q.rose.mean())
    res['base_surge'][f] = float(q.Sg.mean())
    for m in MODELS:
        key = f'{f}|{m}'
        bf = f != 'all'
        res['alert'][key] = {f'top{k}': alert(q, m, k, by_format=True) for k in (20, 50)}
        res['early'][key] = {f'top{k}': alert(q[q.not_yet], m, k, by_format=True) for k in (20, 50)}
        rk = [spearmanr(g[m], g.D).statistic for _, g in q.groupby(['format', 'mi'])]
        res['change_rank'][key] = float(np.nanmean(rk))
        res['surge_ap_ratio'][key] = float(average_precision_score(q.Sg, q[m]) / q.Sg.mean())
    for m, c in (('naive', 'naive_Y'), ('H', 'H_Y'), ('HW', 'HW_Y')):
        act = np.expm1(q.Y)
        e = (np.expm1(q[c]).clip(lower=0) - act).abs()
        res['accuracy'][f'{f}|{m}'] = dict(mae_loans=float(e.mean()), wape=float(e.sum() / act.sum()),
                                          within_25pct=float(((e <= 0.25 * act) & (act >= 4)).sum() / (act >= 4).sum()))
    for period, sel in (('2019-2026', q.year >= 2019), ('2024-2026', q.year >= 2024)):
        a = alert(q[sel], 'HW', 20, by_format=True)
        res['q90'][f'{f}|{period}'] = dict(hit_rate=a['rose'], ci=a['ci'], at_least_90=a['rose'] >= 0.90, slots=a['slots'])
    log(f, 'HW top20', round(res['alert'][f'{f}|HW']['top20']['rose'], 3), 'W top20', round(res['alert'][f'{f}|W']['top20']['rose'], 3),
        'early HW', round(res['early'][f'{f}|HW']['top20']['rose'], 3), 'early W', round(res['early'][f'{f}|W']['top20']['rose'], 3))
# paired monthly change-rank gain of HW over H (all formats), 3-month blocks
months = np.sort(P.mi.unique())
gm = []
for m in months:
    g = P[P.mi == m]
    gm.append(np.nanmean([spearmanr(x.HW, x.D).statistic - spearmanr(x.H, x.D).statistic for _, x in g.groupby('format')]))
gm = np.array(gm)
rng = np.random.default_rng(SEED)
n, kb = len(gm), int(np.ceil(len(gm) / 3))
bs = [gm[np.concatenate([np.arange(a, a + 3) % n for a in rng.choice(n, kb)])[:n]].mean() for _ in range(2000)]
res['HW_minus_H_change_rank'] = dict(mean=float(gm.mean()), lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)))
res['runtime_s'] = round(time.time() - T0)
res['peak_rss_mb'] = round(peak_mb())
res['correction'] = 'rows of 60c_test_d_rows.py (corrected Test A features, A1); models and measures as 61_test_d_models.py'
(REP / 'wiki_led_test_d_c.json').write_text(json.dumps(res, indent=1))
log('q90', {k: (round(v['hit_rate'], 3), v['at_least_90']) for k, v in res['q90'].items()})
log('done')
