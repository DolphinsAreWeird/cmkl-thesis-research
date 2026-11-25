# r04. Five-seed reruns, part 2: five re-drawn 25% samples of works, and the four quarters on their own.
# Record: prereg/DEVIATIONS.md, "Five-seed reruns asked for by the advisor (20 November 2026)", part 2 rule 4 (written first).
# Pool: every work with rows in q0 (data/db/wiki_led/l_books_in_time/rows.parquet, the published main set) and q1 to q3
#   (data/db/wiki_led/l_resplit/q<k>/rows.parquet).  Sample k (k = 1 to 5), seed s = 20261019 + k: numpy default_rng(s) draws
#   round(N/4) of the N pool works without replacement; all rows of a drawn work go with it.  Quarters q0 to q3: seed 20261020.
# Models H, HM, W14, HMW14 for the change D, l04's settings and test years, LightGBM random_state s; scored as l07 (point values,
#   origins 2019-01 to 2026-07, all formats; 2019-2026 and 2024-2026).  Check: q0 with seed 20261020 equals the published l04 values.
# Outputs: data/db/wiki_led/l_resplit/r04_parts/<run>.json (one per sample or quarter; finished runs are skipped), and
#   data/reports/five_seeds_resplit.json
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/l_resplit/r04_resplit.py
import sys, os, json, time, hashlib, pathlib, resource
import numpy as np, pandas as pd
import lightgbm as lgb
from scipy.stats import spearmanr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-30_l_books_in_time.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == '36778f86ced0550c90e8578813ae476c6ae1d4d7220c430ef140244e5d5e028a', 'addendum l changed'
LB = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
RS = DATA / 'db' / 'wiki_led' / 'l_resplit'
PARTS = RS / 'r04_parts'
PARTS.mkdir(parents=True, exist_ok=True)
REP = DATA / 'reports'
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


# ---------------------------------------------------------------- settings of l04_backtest.py
FMTS = ['print', 'ebook', 'audiobook']
F18 = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
F14 = [c for c in F18 if c not in ('nrise8', 'rmax')]
W14C = ['b_' + c for c in F14] + ['a_' + c for c in F14]
HC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'fmt']
HMC = HC + ['cal_month', 'cal_days']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=20261020, n_jobs=4, verbose=-1)
SETS_D = {'H': HC, 'HM': HMC, 'W14': W14C + ['fmt'], 'HMW14': HMC + W14C}
LN15 = np.log(1.5)
COLS = ['work_id', 'format', 'mi', 'year', 'D', 'h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'cal_month', 'cal_days'] + W14C

parts = []
for q, f in [(0, LB / 'rows.parquet')] + [(k, RS / f'q{k}' / 'rows.parquet') for k in (1, 2, 3)]:
    x = pd.read_parquet(f, columns=COLS)
    x = x[x.mi <= 2026 * 12 + 6]
    x['q'] = np.int8(q)
    parts.append(x)
    log('quarter', q, 'rows', len(x), 'works', x.work_id.nunique())
R = pd.concat(parts, ignore_index=True)
del parts
R['format'] = R.format.astype(str)
R['fmt'] = R.format.map({f: i for i, f in enumerate(FMTS)}).astype('int8')
R['rose'] = (R.D >= LN15).astype('int8')
R['not_yet'] = (R.h_lt - R.h_m6) < LN15
POOL = np.sort(R.work_id.unique())
log('pool rows', len(R), 'works', len(POOL))


def monthly(q, col, kind, MPOS, n):
    num, den = np.zeros(n), np.zeros(n)
    if kind == 'rank':
        for (f, m), g in q.groupby(['format', 'mi']):
            if len(g) >= 3 and g[col].nunique() > 1:
                r = spearmanr(g[col], g.D).statistic
                if np.isfinite(r):
                    num[MPOS[m]] += r; den[MPOS[m]] += 1
    else:
        t = q.sort_values(col, ascending=False, kind='stable').groupby(['format', 'mi'], sort=False).head(20)
        g = t.groupby('mi').rose.agg(['sum', 'size'])
        for m, r in g.iterrows():
            num[MPOS[m]] += r['sum']; den[MPOS[m]] += r['size']
    return num[den > 0].sum() / den[den > 0].sum() if den.sum() else float('nan')


def run(name, S, seed):
    fpart = PARTS / f'{name}.json'
    if fpart.exists():
        log(name, 'already done')
        return json.loads(fpart.read_text())
    preds = []
    for Y in range(2019, 2027):
        te = S[(S.year == Y) & (S.mi >= 2019 * 12)]
        tr = S[(S.mi + 1) < Y * 12]
        if te.empty:
            continue
        p = te[['work_id', 'format', 'mi', 'year', 'D', 'rose', 'not_yet']].copy()
        for m, cols in SETS_D.items():
            cat = ['cal_month'] if 'cal_month' in cols else 'auto'
            p[m] = lgb.LGBMRegressor(**{**LGB, 'random_state': seed}).fit(tr[cols], tr.D, categorical_feature=cat).predict(te[cols])
        preds.append(p)
        log(name, 'year', Y, 'train', len(tr), 'test', len(te))
    P = pd.concat(preds, ignore_index=True)
    out = dict(seed=seed, works=int(S.work_id.nunique()), rows_scored=int(len(P)), by_period={})
    for period, sel in (('2019-2026', P.year >= 2019), ('2024-2026', P.year >= 2024)):
        q = P[sel]
        months = np.sort(q.mi.unique()); MPOS = {m: i for i, m in enumerate(months)}; n = len(months)
        nyq = q[q.not_yet]
        v = {m: dict(rank=monthly(q, m, 'rank', MPOS, n), top20=monthly(q, m, 'top20', MPOS, n),
                     early_top20=monthly(nyq, m, 'top20', MPOS, n)) for m in SETS_D}
        v['L2a_HMW14_minus_HM_rank'] = v['HMW14']['rank'] - v['HM']['rank']
        v['L2b_HMW14_minus_HM_early_top20'] = v['HMW14']['early_top20'] - v['HM']['early_top20']
        v['HMW14_minus_HM_top20'] = v['HMW14']['top20'] - v['HM']['top20']
        out['by_period'][period] = v
    a = out['by_period']['2019-2026']
    log(name, 'W14 rank', round(a['W14']['rank'], 4), 'HM', round(a['HM']['rank'], 4), 'HMW14', round(a['HMW14']['rank'], 4),
        'L2a', round(a['L2a_HMW14_minus_HM_rank'], 4), 'L2b', round(a['L2b_HMW14_minus_HM_early_top20'], 4))
    fpart.write_text(json.dumps(out, indent=1, default=float))
    return out


res = dict(record='prereg/DEVIATIONS.md, Five-seed reruns asked for by the advisor (20 November 2026), part 2',
           pool_works=int(len(POOL)), pool_rows=int(len(R)), quarters={}, samples={})
# quarters first: q0 with seed 20261020 must equal the published values
for q in range(4):
    res['quarters'][f'q{q}'] = run(f'quarter_q{q}', R[R.q == q], 20261020)
pub = json.loads((REP / 'wiki_led_l_backtest.json').read_text())['by_period']['2019-2026']['all']
chk = {m: abs(res['quarters']['q0']['by_period']['2019-2026'][m]['rank'] - pub[m]['rank']['est']) for m in SETS_D}
res['check_q0_vs_published_rank'] = chk
log('q0 against the published change ranks', chk)
assert max(chk.values()) < 1e-9, 'q0 does not reproduce the published values'
for k in range(1, 6):
    s = 20261019 + k
    pick = np.random.default_rng(s).choice(len(POOL), int(round(len(POOL) / 4)), replace=False)
    S = R[R.work_id.isin(POOL[pick])]
    res['samples'][f'sample_{k}'] = run(f'sample_{k}', S, s)
    res['samples'][f'sample_{k}']['share_from_q0'] = float(S[S.q == 0].work_id.nunique() / S.work_id.nunique())
res['runtime_s'] = round(time.time() - T0)
res['peak_rss_mb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20)
(REP / 'five_seeds_resplit.json').write_text(json.dumps(res, indent=1, default=float))
log('done')
