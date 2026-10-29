# l04. Addendum l, step 3: backtest on the frame "books chosen in time".  Settings: prereg/addenda_wiki_led/2026-10-30_l_books_in_time.json,
# models, measures, decisions (read-only; SHA-256 checked).  Not blind: Test D's results on overlapping rows were known (see the record).
#
# Walk-forward by test year 2019 to 2026 as Test D (code/main_study/wiki_led/61c_test_d_models.py): test rows of year Y (year of the target
#   month) from origin 2019-01; training rows with target month before January of Y.  LightGBM settings of Tests A and D, formats pooled
#   with format as the feature fmt (0 print, 1 ebook, 2 audiobook), as Test D; one model for the change D and one for the level Y.
# Models: naive; H (Test D's history features and fmt); HM (H plus cal_month, categorical, and cal_days); W14 (the 7 features kept by L3 for
#   the book and author articles, plus fmt, as Test D's W); HMW14; W18 and HW18 (Test D's 18 features, the bridge); W14_ridge (L4).
# Ridge (L4): features standardized on training rows; a missing value becomes 0 with a 0/1 indicator for each column missing somewhere in
#   the training rows (code/main_study/study4/_models.py, _design); format as three 0/1 columns; alpha from {0.1, 1, 10, 100} by mean
#   absolute error of D on the last 12 training origins, each candidate fitted on training rows whose target month is on or before the first
#   of those origins (choose_alpha), then refitted on all training rows.
# Measures (record): change rank, Spearman of prediction and D within each format and origin month, averaged over format-months; share of
#   the top 20 and top 50 that rose (D >= ln 1.5), lists within each format and month, pooled; the same among rows not yet risen; surge
#   average precision over the surge rate; level: mean absolute error of Y, and in loans (expm1 floored at 0) the mean and median absolute
#   error and the share within 2 loans.  All formats and by format; 2019-2026 and 2024-2026 (target years).  Wikipedia-only models also on
#   rows with an article feature (descriptive).  Intervals: 2,000 draws of blocks of 3 consecutive scored months (seed 20261020), every
#   measure a ratio of monthly sums so a draw re-weights months; differences paired by month on the same draws.
# Outputs: data/db/wiki_led/l_books_in_time/preds.parquet, data/reports/wiki_led_l_backtest.json and .md
#   Run from code/:  bash ../jobs/bg.sh wl_l04 main_study/wiki_led/l_books_in_time/l04_backtest.py
import sys, os, json, time, hashlib, pathlib, resource
import numpy as np, pandas as pd
import lightgbm as lgb
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import average_precision_score

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-30_l_books_in_time.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == '36778f86ced0550c90e8578813ae476c6ae1d4d7220c430ef140244e5d5e028a', 'addendum l changed'
OUT = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
REP = DATA / 'reports'
SEED = 20261020
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


FMTS = ['print', 'ebook', 'audiobook']
F18 = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
F14 = [c for c in F18 if c not in ('nrise8', 'rmax')]
W18C = ['b_' + c for c in F18] + ['a_' + c for c in F18]
W14C = ['b_' + c for c in F14] + ['a_' + c for c in F14]
HC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'fmt']
HMC = HC + ['cal_month', 'cal_days']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)
SETS_D = {'H': HC, 'HM': HMC, 'W14': W14C + ['fmt'], 'HMW14': HMC + W14C, 'W18': W18C + ['fmt'], 'HW18': HC + W18C}
SETS_Y = {'H': HC, 'HM': HMC, 'HMW14': HMC + W14C}
ALPHAS, NVAL = (0.1, 1.0, 10.0, 100.0), 12
LN15 = np.log(1.5)

R = pd.read_parquet(OUT / 'rows.parquet')
R = R[R.mi <= 2026 * 12 + 6].copy()                         # backtest origins to 2026-07; origin 2026-08 is for the frozen forecasts
R['format'] = R.format.astype(str)
R['fmt'] = R.format.map({f: i for i, f in enumerate(FMTS)}).astype('int8')
R['rose'] = (R.D >= LN15).astype('int8')
R['not_yet'] = (R.h_lt - R.h_m6) < LN15
R['any_page'] = (R.has_book_page == 1) | (R.has_author_page == 1)
log('rows', len(R), R.format.value_counts().to_dict())


def lgb_fit(tr, te, cols, target):
    cat = ['cal_month'] if 'cal_month' in cols else 'auto'
    return lgb.LGBMRegressor(**LGB).fit(tr[cols], tr[target], categorical_feature=cat).predict(te[cols])


def design(tr, te, cols):
    Xtr, Xte = tr[cols].to_numpy(float), te[cols].to_numpy(float)
    mu, sd = np.nanmean(Xtr, axis=0), np.nanstd(Xtr, axis=0)
    mu = np.where(np.isfinite(mu), mu, 0.0); sd = np.where(np.isfinite(sd) & (sd > 0), sd, 1.0)
    ztr, zte = (Xtr - mu) / sd, (Xte - mu) / sd
    miss = np.where(np.isnan(Xtr).any(axis=0))[0]
    btr = [np.where(np.isnan(ztr), 0.0, ztr), np.isnan(Xtr[:, miss]).astype(float), np.stack([tr.fmt == i for i in range(3)], 1).astype(float)]
    bte = [np.where(np.isnan(zte), 0.0, zte), np.isnan(Xte[:, miss]).astype(float), np.stack([te.fmt == i for i in range(3)], 1).astype(float)]
    return np.hstack(btr), np.hstack(bte)


def ridge_fit(tr, te, cols, target):
    origins = np.sort(tr.mi.unique())
    n_val = min(NVAL, len(origins) // 3)
    alpha = ALPHAS[len(ALPHAS) // 2]
    if n_val >= 1:
        val = origins[-n_val:]
        fit, va = tr[tr.mi + 1 <= val[0]], tr[tr.mi.isin(val)]
        if len(fit) >= 10 and len(va) >= 1:
            err = []
            for a in ALPHAS:
                Xf, Xv = design(fit, va, cols)
                err.append(np.mean(np.abs(Ridge(alpha=a).fit(Xf, fit[target]).predict(Xv) - va[target].to_numpy())))
            alpha = ALPHAS[int(np.argmin(err))]
    Xtr, Xte = design(tr, te, cols)
    return Ridge(alpha=alpha).fit(Xtr, tr[target]).predict(Xte), alpha


preds, alphas = [], {}
for Y in range(2019, 2027):
    te = R[(R.year == Y) & (R.mi >= 2019 * 12)]
    tr = R[(R.mi + 1) < Y * 12]
    if te.empty:
        continue
    p = te[['work_id', 'format', 'mi', 'year', 'D', 'Sg', 'Y', 'L_next', 'rose', 'not_yet', 'any_page', 'has_book_page', 'has_author_page']].copy()
    p['naive'] = (te.h_lt - te.h_m6).values
    p['naive_Y'] = te.h_lt.values
    for name, cols in SETS_D.items():
        p[name] = lgb_fit(tr, te, cols, 'D')
    for name, cols in SETS_Y.items():
        p[name + '_Y'] = lgb_fit(tr, te, cols, 'Y')
    p['W14_ridge'], alphas[Y] = ridge_fit(tr, te, W14C, 'D')
    preds.append(p)
    log('year', Y, 'train', len(tr), 'test', len(te), '| ridge alpha', alphas[Y])
P = pd.concat(preds, ignore_index=True)
P.to_parquet(OUT / 'preds.parquet', index=False)

# ---------------------------------------------------------------- monthly sums and block bootstrap
MONTHS = np.sort(P.mi.unique())
MPOS = {m: i for i, m in enumerate(MONTHS)}
rng = np.random.default_rng(SEED)
n, kb = len(MONTHS), int(np.ceil(len(MONTHS) / 3))
BD = np.array([np.concatenate([np.arange(a, a + 3) % n for a in rng.choice(n, kb)])[:n] for _ in range(2000)])


def monthly(q, col, kind):
    """Per scored month: (numerator, denominator) so that the measure is sum(num)/sum(den) over months."""
    num, den = np.zeros(n), np.zeros(n)
    if kind == 'rank':
        for (f, m), g in q.groupby(['format', 'mi']):
            if len(g) >= 3 and g[col].nunique() > 1:
                r = spearmanr(g[col], g.D).statistic
                if np.isfinite(r):
                    num[MPOS[m]] += r; den[MPOS[m]] += 1
    elif kind.startswith('top'):
        k = int(kind[3:])
        t = q.sort_values(col, ascending=False, kind='stable').groupby(['format', 'mi'], sort=False).head(k)
        g = t.groupby('mi').rose.agg(['sum', 'size'])
        for m, r in g.iterrows():
            num[MPOS[m]] += r['sum']; den[MPOS[m]] += r['size']
    elif kind == 'mae_y':
        g = (q[col] - q.Y).abs().groupby(q.mi).agg(['sum', 'size'])
        for m, r in g.iterrows():
            num[MPOS[m]] += r['sum']; den[MPOS[m]] += r['size']
    elif kind in ('mae_loans', 'within2'):
        e = (np.expm1(q[col]).clip(lower=0) - q.L_next).abs()
        v = e if kind == 'mae_loans' else (e <= 2).astype(float)
        g = v.groupby(q.mi).agg(['sum', 'size'])
        for m, r in g.iterrows():
            num[MPOS[m]] += r['sum']; den[MPOS[m]] += r['size']
    return num, den


def est(a, b=None):
    """a, b: (num, den) arrays. Returns point, 95% interval of a (or of a - b, paired on the same month draws)."""
    pa_ = a[0].sum() / a[1].sum()
    da = a[0][BD].sum(1) / a[1][BD].sum(1)
    if b is None:
        return dict(est=float(pa_), lo=float(np.percentile(da, 2.5)), hi=float(np.percentile(da, 97.5)))
    pb = b[0].sum() / b[1].sum()
    db = b[0][BD].sum(1) / b[1][BD].sum(1)
    d = da - db
    return dict(est=float(pa_ - pb), lo=float(np.percentile(d, 2.5)), hi=float(np.percentile(d, 97.5)))


MOD_D = ['naive', 'H', 'HM', 'W14', 'W14_ridge', 'HMW14', 'W18', 'HW18']
MOD_Y = [('naive', 'naive_Y'), ('H', 'H_Y'), ('HM', 'HM_Y'), ('HMW14', 'HMW14_Y')]
res = dict(rows=len(P), months=int(n), ridge_alpha=alphas, base_rose={}, base_surge={}, measures={}, by_period={})


def score(q, label):
    out = {}
    nyq = q[q.not_yet]
    for m in MOD_D:
        S = {}
        mm = {kind: monthly(q, m, kind) for kind in ('rank', 'top20', 'top50')}
        mm['early_top20'] = monthly(nyq, m, 'top20')
        for k, v in mm.items():
            S[k] = est(v)
        S['surge_ap_ratio'] = float(average_precision_score(q.Sg, q[m]) / q.Sg.mean()) if q.Sg.sum() else None
        out[m] = (S, mm)
    for m, c in MOD_Y:
        S = out[m][0] if m in out else {}
        mm = out[m][1] if m in out else {}
        for kind in ('mae_y', 'mae_loans', 'within2'):
            mm[kind] = monthly(q, c, kind)
            S[kind] = est(mm[kind])
        S['median_abs_err_loans'] = float(np.median((np.expm1(q[c]).clip(lower=0) - q.L_next).abs()))
        out[m] = (S, mm)
    return out


for period, sel in (('2019-2026', P.year >= 2019), ('2024-2026', P.year >= 2024)):
    res['by_period'][period] = {}
    for f in ['all'] + FMTS:
        q = P[sel] if f == 'all' else P[sel & (P.format == f)]
        sc = score(q, f)
        block = {m: v[0] for m, v in sc.items()}
        mm = {m: v[1] for m, v in sc.items()}
        block['_base_rose'] = float(q.rose.mean()); block['_base_surge'] = float(q.Sg.mean())
        block['_diff'] = {
            'L2a_HMW14_minus_HM_rank': est(mm['HMW14']['rank'], mm['HM']['rank']),
            'L2b_HMW14_minus_HM_early_top20': est(mm['HMW14']['early_top20'], mm['HM']['early_top20']),
            'L3_HM_minus_H_mae_y': est(mm['HM']['mae_y'], mm['H']['mae_y']),
            'HM_minus_H_rank': est(mm['HM']['rank'], mm['H']['rank']),
            'HM_minus_H_mae_loans': est(mm['HM']['mae_loans'], mm['H']['mae_loans']),
            'HMW14_minus_HM_top20': est(mm['HMW14']['top20'], mm['HM']['top20']),
            'HW18_minus_H_rank': est(mm['HW18']['rank'], mm['H']['rank']),
            'W14_minus_W18_rank': est(mm['W14']['rank'], mm['W18']['rank']),
            'HMW14_minus_HW18_rank': est(mm['HMW14']['rank'], mm['HW18']['rank'])}
        qa = q[q.any_page]
        block['_rows_with_page'] = {m: est(monthly(qa, m, 'rank')) for m in ('W14', 'W14_ridge', 'HMW14', 'HM')}
        block['_rows_with_page']['n_rows'] = int(len(qa))
        res['by_period'][period][f] = block
        log(period, f, 'rank W14', round(block['W14']['rank']['est'], 4), 'HM', round(block['HM']['rank']['est'], 4),
            'HMW14', round(block['HMW14']['rank']['est'], 4), '| L3', {k: round(v, 4) for k, v in block['_diff']['L3_HM_minus_H_mae_y'].items()})

A_ = res['by_period']['2019-2026']['all']
dec = {'L1': dict(rule='W14 change rank, 95% interval above 0', **A_['W14']['rank']),
       'L2a': dict(rule='HMW14 minus HM change rank, paired, interval above 0', **A_['_diff']['L2a_HMW14_minus_HM_rank']),
       'L2b': dict(rule='HMW14 minus HM top-20 share that rose among rows not yet risen, interval above 0', **A_['_diff']['L2b_HMW14_minus_HM_early_top20']),
       'L3': dict(rule='HM minus H mean absolute error of Y, paired, interval below 0', **A_['_diff']['L3_HM_minus_H_mae_y'])}
for k in ('L1', 'L2a', 'L2b'):
    dec[k]['passed'] = dec[k]['lo'] > 0
dec['L3']['passed'] = dec['L3']['hi'] < 0
res['decisions'] = dec

# ---------------------------------------------------------------- bridge to Test D (descriptive)
TDJ = json.loads((REP / 'wiki_led_test_d_c.json').read_text())
TDP = pd.read_parquet(DATA / 'db' / 'wiki_led' / 'test_d_preds_c.parquet')
TDP = TDP[TDP.work_id.isin(set(P.work_id))].copy()
TDP['format'] = TDP.format.astype(str)
TDP['mi'] = TDP.mi.astype(int)
TDP = TDP[TDP.mi.isin(MONTHS)]
br = {'test_d_published_all_rows': {m: dict(change_rank=TDJ['change_rank'][f'all|{m}'], top20=TDJ['alert'][f'all|{m}']['top20']['rose'],
                                             early_top20=TDJ['early'][f'all|{m}']['top20']['rose']) for m in ('W', 'H', 'HW')},
      'test_d_stored_predictions_on_sampled_rows': {}, 'here': {}}
for m in ('W', 'H', 'HW'):
    br['test_d_stored_predictions_on_sampled_rows'][m] = dict(change_rank=est(monthly(TDP, m, 'rank'))['est'], top20=est(monthly(TDP, m, 'top20'))['est'],
                                                              early_top20=est(monthly(TDP[TDP.not_yet], m, 'top20'))['est'], rows=int(len(TDP)))
for m in ('W18', 'H', 'HW18', 'W14', 'HM', 'HMW14'):
    br['here'][m] = dict(change_rank=A_[m]['rank']['est'], top20=A_[m]['top20']['est'], early_top20=A_[m]['early_top20']['est'])
res['bridge_to_test_d'] = br
res['runtime_s'] = round(time.time() - T0)
res['peak_rss_mb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20)
(REP / 'wiki_led_l_backtest.json').write_text(json.dumps(res, indent=1, default=float))

# ---------------------------------------------------------------- report
f3 = lambda d: f'{d["est"]:.4f} [{d["lo"]:.4f}, {d["hi"]:.4f}]'
L = ['# Addendum l, step 3: backtest on books chosen in time', '',
     f'Made by `code/main_study/wiki_led/l_books_in_time/l04_backtest.py` on {time.strftime("%Y-%m-%d %H:%M")} (local time, UTC+06:30). '
     'Settings: `prereg/addenda_wiki_led/2026-10-30_l_books_in_time.json`. Not blind (see the record); the blind test is the frozen '
     'forecast for September 2026.', '',
     f'Scored rows {len(P):,} over {n} origin months (2019-01 to 2026-07); ridge penalties by test year {alphas}.', '',
     '## Decisions fixed in advance (all formats, 2019 to 2026; 95% intervals from 3-month blocks)', '',
     '| Rule | Estimate [95% interval] | Passed |', '| --- | --- | --- |']
for k, v in dec.items():
    L.append(f'| {k}: {v["rule"]} | {f3(v)} | {"yes" if v["passed"] else "no"} |')
for period in ('2019-2026', '2024-2026'):
    L += ['', f'## Scores, {period}', '',
          '| Formats | Model | Change rank | Top 20 rose | Top 50 rose | Not yet risen, top 20 | Surge AP / rate |',
          '| --- | --- | --- | --- | --- | --- | --- |']
    for f in ['all'] + FMTS:
        b = res['by_period'][period][f]
        for m in MOD_D:
            s = b[m]
            L.append(f'| {f} | {m} | {f3(s["rank"])} | {s["top20"]["est"]:.3f} | {s["top50"]["est"]:.3f} | {s["early_top20"]["est"]:.3f} | '
                     f'{s["surge_ap_ratio"]:.2f} |' if s['surge_ap_ratio'] is not None else '')
        L.append(f'| {f} | base rate | | {b["_base_rose"]:.3f} | | | surge {b["_base_surge"]:.4f} |')
    L += ['', f'Level accuracy, {period}', '', '| Formats | Model | MAE of Y | MAE in loans | Median error in loans | Within 2 loans |',
          '| --- | --- | --- | --- | --- | --- |']
    for f in ['all'] + FMTS:
        b = res['by_period'][period][f]
        for m, _ in MOD_Y:
            s = b[m]
            L.append(f'| {f} | {m} | {f3(s["mae_y"])} | {s["mae_loans"]["est"]:.2f} | {s["median_abs_err_loans"]:.2f} | {s["within2"]["est"]:.3f} |')
    L += ['', f'Paired differences, {period}, all formats', '']
    for k, v in res['by_period'][period]['all']['_diff'].items():
        L.append(f'- {k}: {f3(v)}')
    wp = res['by_period'][period]['all']['_rows_with_page']
    L += ['', f'Rows with an article feature ({wp["n_rows"]:,}), change rank: ' + '; '.join(f'{m} {f3(wp[m])}' for m in ('W14', 'W14_ridge', 'HMW14', 'HM'))]
L += ['', '## Bridge to Test D (descriptive)', '', '| Source | Model | Change rank | Top 20 rose | Not yet risen, top 20 |', '| --- | --- | --- | --- | --- |']
for src, d in br.items():
    for m, v in d.items():
        L.append(f'| {src} | {m} | {v["change_rank"]:.4f} | {v["top20"]:.3f} | {v["early_top20"]:.3f} |')
L += ['', f'Run time {res["runtime_s"]} s; peak memory {res["peak_rss_mb"]} MB.']
(REP / 'wiki_led_l_backtest.md').write_text('\n'.join(x for x in L if x is not None) + '\n')
log('decisions', {k: (round(v['est'], 4), v['passed']) for k, v in dec.items()})
log('done')
