# 62c. Test E (LibriVox), CORRECTED RERUN: 62_test_e_models.py on the rows of 50c_test_e_data.py, with correction A1 of addendum e
# (prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json). Addendum e did not name Test E; this rerun is for consistency with
# it (prereg/DEVIATIONS.md, section "Wikipedia-led tests", entry of 20 Oct 2026 21:45 +07). The original run and its files stay on file.
# Changes, and nothing else:
#   - E1 trains and scores on data/db/wiki_led/test_e_rows_c.parquet (the same rows as test_e_rows.parquet; only the 18 Wikipedia
#     columns are corrected, checked by 50c_test_e_data.py);
#   - E2 trains on the corrected Seattle Test A rows data/db/wiki_led/test_a_rows_c.parquet (made by 10c_test_a.py: the rows of
#     test_a_rows.parquet with corrected Wikipedia columns), because E2 applies the Test A models and A1 covers their features too.
#     Only the columns the models use are read from that file (memory); the rows and their order are unchanged;
#   - output files carry the suffix _c; nice; peak memory is logged and stored.
# Models, seeds, settings, filters and the scoring code are those of 62_test_e_models.py.
# Output: data/db/wiki_led/test_e_preds_c.parquet, data/reports/wiki_led_test_e_c.json
#   bash jobs/bg.sh wl_test_e_c main_study/wiki_led/62c_test_e_models.py      (from handoff/; about 3 minutes, under 2 GB)
#
# Original header of 62_test_e_models.py:
# 62. Test E (LibriVox, another platform). E1: Test A's models retrained on LibriVox listening, walk-forward by year.
# E2: the Seattle Test A models (trained on Test A rows whose target month is before 1 January of the test year) applied unchanged.
# Settings: prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json (test_E_librivox) and the dated choices in
# prereg/DEVIATIONS.md (excluded months, 2018 level break, automated-traffic months).
# Output: data/db/wiki_led/test_e_preds.parquet, data/reports/wiki_led_test_e.json
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
WC = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS]
HC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)


def peak_mb():                                                           # macOS reports ru_maxrss in bytes
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s [peak {peak_mb():.0f} MB]', *a, flush=True)


E = pd.read_parquet(OUT / 'test_e_rows_c.parquet')
E['rose'] = (E.D >= np.log(1.5)).astype('int8')
E['not_yet'] = (E.h_lt - E.h_m6) < np.log(1.5)
A = pd.read_parquet(OUT / 'test_a_rows_c.parquet', columns=['mi', 'D'] + HC + WC)     # corrected Seattle rows for E2 (columns used only)
log('LibriVox rows', len(E), 'regime', E.regime.value_counts().to_dict(), 'jump', int(E.flag_jump.sum()), '| Seattle rows', len(A))
EK = E[E.regime != 1]                                                   # straddling the 2018 break: out of training and scoring

preds = []
for Y in range(2019, 2027):
    te = EK[(EK.year == Y)]
    if te.empty:
        continue
    tr = EK[((EK.mi + 1) < Y * 12) & (EK.flag_jump == 0)]
    trA = A[(A.mi + 1) < Y * 12]
    p = te[['book_id', 'mi', 'year', 'D', 'Sg', 'Y', 'rose', 'not_yet', 'flag_jump', 'has_book_page', 'has_author_page', 'L_t']].copy()
    p['naive'] = (te.h_lt - te.h_m6).values
    for name, cols in (('W', WC), ('H', HC), ('HW', HC + WC)):
        p['E1_' + name] = lgb.LGBMRegressor(**LGB).fit(tr[cols], tr.D).predict(te[cols])
        p['E2_' + name] = lgb.LGBMRegressor(**LGB).fit(trA[cols], trA.D).predict(te[cols])
    preds.append(p)
    log('year', Y, 'train LibriVox', len(tr), 'train Seattle', len(trA), 'test', len(te))
P = pd.concat(preds, ignore_index=True)
P.to_parquet(OUT / 'test_e_preds_c.parquet', index=False)
MODELS = ['E1_W', 'E1_H', 'E1_HW', 'E2_W', 'E2_H', 'E2_HW', 'naive']


def cp(k, n):
    return (float(beta.ppf(0.025, k, n - k + 1)) if k > 0 else 0.0, float(beta.ppf(0.975, k + 1, n - k)) if k < n else 1.0)


def alert(df, col, k):
    t = df.sort_values(col, ascending=False).groupby('mi', sort=False).head(k)
    hits, slots = int(t.rose.sum()), len(t)
    return dict(rose=hits / slots, surged=float(t.Sg.mean()), hits=hits, slots=slots, ci=cp(hits, slots))


res = {}
for label, q in (('main (no automated-traffic months)', P[P.flag_jump == 0]), ('check (all rows)', P)):
    r = {'rows': len(q), 'base_rose': float(q.rose.mean()), 'base_surge': float(q.Sg.mean()), 'models': {}}
    for m in MODELS:
        rk = [spearmanr(g[m], g.D).statistic for _, g in q.groupby('mi')]
        r['models'][m] = dict(change_rank=float(np.nanmean(rk)),
                              surge_ap_ratio=float(average_precision_score(q.Sg, q[m]) / q.Sg.mean()),
                              top20=alert(q, m, 20), top50=alert(q, m, 50), early_top20=alert(q[q.not_yet], m, 20))
    for period, sel in (('2019-2026', q.year >= 2019), ('2024-2026', q.year >= 2024)):
        for m in ('E1_HW', 'E2_HW'):
            a = alert(q[sel], m, 20)
            r[f'q90|{m}|{period}'] = dict(hit_rate=a['rose'], ci=a['ci'], at_least_90=a['rose'] >= 0.90, slots=a['slots'])
    res[label] = r
    log(label, {m: (round(r['models'][m]['change_rank'], 3), round(r['models'][m]['top20']['rose'], 3)) for m in MODELS})
res['runtime_s'] = round(time.time() - T0)
res['peak_rss_mb'] = round(peak_mb())
res['correction'] = ('A1 of addendum e: weeks before the first week with views > 0 are missing, in the LibriVox rows (50c_test_e_data.py) '
                     'and in the Seattle rows of E2 (test_a_rows_c.parquet); everything else as 62_test_e_models.py')
(REP / 'wiki_led_test_e_c.json').write_text(json.dumps(res, indent=1))
log('done')
