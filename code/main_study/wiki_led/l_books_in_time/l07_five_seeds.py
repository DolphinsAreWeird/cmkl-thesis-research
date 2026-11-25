# l07. Five-seed rerun of the main set (addendum l), asked for by the advisor on 20 Nov 2026.
# Record: prereg/DEVIATIONS.md, "Five-seed reruns asked for by the advisor (20 November 2026)", part 1.1 (written before this ran).
# Rows, features, test years and LightGBM settings are those of l04_backtest.py; only LightGBM's random_state changes (20261020 to
#   20261024).  Models H, HM, W14, HMW14 for the change D.  Point values only, scored as l04 does (ratio of monthly sums):
#   change rank, top 20 that rose, top 20 among rows not yet risen; all formats; 2019-2026 and 2024-2026.
# Check: with seed 20261020 the refits must equal the stored l04 predictions (preds.parquet) to 1e-9.
# Outputs: data/db/wiki_led/l_books_in_time/five_seeds/preds_<seed>.parquet, data/reports/five_seeds_main.json
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/l_books_in_time/l07_five_seeds.py
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
OUT = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
FS = OUT / 'five_seeds'
FS.mkdir(exist_ok=True)
REP = DATA / 'reports'
SEEDS = [20261020 + i for i in range(5)]
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


# ---------------------------------------------------------------- settings and rows, copied from l04_backtest.py
FMTS = ['print', 'ebook', 'audiobook']
F18 = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
F14 = [c for c in F18 if c not in ('nrise8', 'rmax')]
W14C = ['b_' + c for c in F14] + ['a_' + c for c in F14]
HC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'fmt']
HMC = HC + ['cal_month', 'cal_days']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEEDS[0], n_jobs=4, verbose=-1)
SETS_D = {'H': HC, 'HM': HMC, 'W14': W14C + ['fmt'], 'HMW14': HMC + W14C}
LN15 = np.log(1.5)

R = pd.read_parquet(OUT / 'rows.parquet')
R = R[R.mi <= 2026 * 12 + 6].copy()
R['format'] = R.format.astype(str)
R['fmt'] = R.format.map({f: i for i, f in enumerate(FMTS)}).astype('int8')
R['rose'] = (R.D >= LN15).astype('int8')
R['not_yet'] = (R.h_lt - R.h_m6) < LN15
log('rows', len(R))


def lgb_fit(tr, te, cols, target, seed):
    cat = ['cal_month'] if 'cal_month' in cols else 'auto'
    return lgb.LGBMRegressor(**{**LGB, 'random_state': seed}).fit(tr[cols], tr[target], categorical_feature=cat).predict(te[cols])


# ---------------------------------------------------------------- scoring, as l04 (point values)
def monthly(q, col, kind, MPOS, n):
    num, den = np.zeros(n), np.zeros(n)
    if kind == 'rank':
        for (f, m), g in q.groupby(['format', 'mi']):
            if len(g) >= 3 and g[col].nunique() > 1:
                r = spearmanr(g[col], g.D).statistic
                if np.isfinite(r):
                    num[MPOS[m]] += r; den[MPOS[m]] += 1
    else:                                                    # top20
        t = q.sort_values(col, ascending=False, kind='stable').groupby(['format', 'mi'], sort=False).head(20)
        g = t.groupby('mi').rose.agg(['sum', 'size'])
        for m, r in g.iterrows():
            num[MPOS[m]] += r['sum']; den[MPOS[m]] += r['size']
    return num[den > 0].sum() / den[den > 0].sum() if den.sum() else float('nan')


STORED = pd.read_parquet(OUT / 'preds.parquet', columns=['work_id', 'format', 'mi'] + list(SETS_D))
STORED['format'] = STORED.format.astype(str)
res = dict(record='prereg/DEVIATIONS.md, Five-seed reruns asked for by the advisor (20 November 2026), part 1.1', seeds={}, check={})
for seed in SEEDS:
    fpred = FS / f'preds_{seed}.parquet'
    if fpred.exists():
        P = pd.read_parquet(fpred)
        log('seed', seed, 'predictions already made, read', fpred.name)
    else:
        parts = []
        for Y in range(2019, 2027):
            te = R[(R.year == Y) & (R.mi >= 2019 * 12)]
            tr = R[(R.mi + 1) < Y * 12]
            if te.empty:
                continue
            p = te[['work_id', 'format', 'mi', 'year', 'D', 'rose', 'not_yet']].copy()
            for name, cols in SETS_D.items():
                p[name] = lgb_fit(tr, te, cols, 'D', seed)
            parts.append(p)
            log('seed', seed, 'year', Y, 'train', len(tr), 'test', len(te))
        P = pd.concat(parts, ignore_index=True)
        P.to_parquet(fpred, index=False)
    if seed == SEEDS[0]:
        M = P.merge(STORED, on=['work_id', 'format', 'mi'], suffixes=('', '_stored'), validate='one_to_one')
        res['check'] = dict(rows=int(len(P)), rows_matched=int(len(M)),
                            max_abs_diff={m: float((M[m] - M[m + '_stored']).abs().max()) for m in SETS_D})
        log('check against stored l04 predictions', res['check'])
        assert len(M) == len(P) == len(STORED) and max(res['check']['max_abs_diff'].values()) < 1e-9, 'seed 20261020 does not reproduce l04'
    out = {}
    for period, sel in (('2019-2026', P.year >= 2019), ('2024-2026', P.year >= 2024)):
        q = P[sel]
        months = np.sort(q.mi.unique()); MPOS = {m: i for i, m in enumerate(months)}; n = len(months)
        nyq = q[q.not_yet]
        v = {m: dict(rank=monthly(q, m, 'rank', MPOS, n), top20=monthly(q, m, 'top20', MPOS, n),
                     early_top20=monthly(nyq, m, 'top20', MPOS, n)) for m in SETS_D}
        v['L2a_HMW14_minus_HM_rank'] = v['HMW14']['rank'] - v['HM']['rank']
        v['L2b_HMW14_minus_HM_early_top20'] = v['HMW14']['early_top20'] - v['HM']['early_top20']
        v['HMW14_minus_HM_top20'] = v['HMW14']['top20'] - v['HM']['top20']
        out[period] = v
    res['seeds'][str(seed)] = out
    a = out['2019-2026']
    log('seed', seed, 'W14 rank', round(a['W14']['rank'], 4), 'HM', round(a['HM']['rank'], 4), 'HMW14', round(a['HMW14']['rank'], 4),
        'L2a', round(a['L2a_HMW14_minus_HM_rank'], 4), 'L2b', round(a['L2b_HMW14_minus_HM_early_top20'], 4))

res['runtime_s'] = round(time.time() - T0)
res['peak_rss_mb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20)
(REP / 'five_seeds_main.json').write_text(json.dumps(res, indent=1, default=float))
log('done')
