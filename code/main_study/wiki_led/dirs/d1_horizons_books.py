# d1_horizons_books.py  Direction D1 (books) of addendum i: does Wikipedia's value for predicting which books' borrowing rises
# grow when the prediction looks further ahead (the mean loans of the next 1, 3, 6 or 12 months) instead of next month only?
# Settings: prereg/addenda_wiki_led/2026-10-22_i_directions.json, section D1_horizons_books (read-only; SHA-256 checked below),
# on top of prereg/wiki_led_settings_2026-10-20.json (test_A_existing_books) and addendum e (correction A1).  Built on Test A's
# corrected code, main_study/wiki_led/10c_test_a.py, whose rows, features, model settings, seed, years and scoring are reused.
# This header was written on 22 Oct 2026 (about 03:30 +07) BEFORE any D1 result was computed or seen.
#
# What it does
#   1. Reads Test A's corrected rows (data/db/wiki_led/test_a_rows_c.parquet: the 7,747 works with their own English article,
#      origin months 2016-03 to 2026-07, M6, history features h_*, Wikipedia features b_* and a_*).  Rebuilds Test A's monthly
#      loans panel exactly as 10c_test_a.py does (data/db/study2r/counts_work.parquet, all formats summed, a month without a row
#      is 0 loans, months before a work's first loan missing) and Test A's excluded months (data/db/study3/demand_panel.parquet,
#      month_ok), and checks them against the rows (L_next and D must match exactly) and the Test A report.
#   2. Targets for k = 1, 3, 6, 12: mean_k = mean of L(t+1), ..., L(t+k); D_k = ln(1 + mean_k) - ln(1 + M6) (Test A's change
#      target with the mean in place of next month); rose_k = D_k >= ln 1.5; surge_k = D_k >= ln 2 and mean_k - M6 >= 5.
#      A row is kept only when all of t+1..t+k lie inside the loans panel (last month 2026-08) and none of them is an excluded
#      month (Test A already requires that t and t+1 are not excluded).  Rows whose window ends after 2026-08 are dropped.
#   3. Refits Test A's three LightGBM models on D_k with Test A's exact settings (n_estimators 300, learning_rate 0.05,
#      num_leaves 31, min_child_samples 50, subsample 0.8, subsample_freq 1, colsample_bytree 0.8, seed 20261020, 4 threads;
#      nothing tuned): W = b_* and a_* features, H = h_* features, HW = both.  Persistence = ln(1 + L_t) - ln(1 + M6) (Test A's
#      naive change ranking, Hnaive_D), the same ranking for every k.  Walk-forward by test year 2019 to 2026 as in Test A.
#   4. Scores each k: mean within-origin-month Spearman of predicted and actual D_k over the scored origins (2019-01 onwards), with
#      Test A's interval (2,000 draws of blocks of 3 consecutive scored months, seed 20261020); HW minus H paired by month; the
#      share of each model's top 20 per month that rose (and surged), with the same month-block interval, beside the base rate.
#   5. Checks that k = 1 reproduces Test A's corrected numbers (data/reports/wiki_led_test_a_c.json and
#      data/reports/wiki_led_test_a_alert_list_c.csv) and its stored predictions (data/db/wiki_led/test_a_preds_c.parquet).
#
# Choices the addendum did not fix (made here, before any result):
#   (c1) Test year of a row = year of month t+1, as in Test A, for every k, so an origin month sits in the same test year (and is
#        predicted by the same refit) at every horizon.
#   (c2) Training rows for test year Y are the rows whose whole target window t+1..t+k ends before 1 January of Y, i.e.
#        (t + k) < 12 Y (Test A's rule "outcome month before 1 January of Y" applied to the last month of the window; for k = 1 it is
#        Test A's rule).  Without it the long-horizon models would learn from loans in the test year.
#   (c3) 'rose' is Test A's rule as its code applies it (13c_accuracy_alert_panels.py): D >= ln 1.5, i.e. (1 + mean_k) at least
#        1.5 times (1 + M6).  This keeps k = 1 identical to Test A's alert lists.  'surge' is Test A's surge rule with mean_k.
#   (c4) Top 20 per month: rows sorted by the model's score (pandas default sort, as 13c), first 20 per origin month; the share
#        that rose is averaged over months.  The base rate is the share of all rows that rose, averaged over the same months.
#   (c5) Growth from k = 1 (the addendum's main comparison): for k = 3, 6, 12 the per-month difference (k minus 1) of W's Spearman,
#        of H's, and of HW minus H, on the origin months where both horizons exist (the months of k, all of which also exist at
#        k = 1), with a month-block interval over those months (fresh generator, seed 20261020).
#   (c6) Because the long horizons lose the origin months whose windows touch the closures (2020, 2024) and the end of the data,
#        a second table scores every k on the same origin months, those available at k = 12; within an origin month the books are
#        the same at every k, so these are also the same rows.  The main table is each k on all its own months (the addendum).
#   (c7) Book-resampling intervals of Test A are not repeated (the addendum names the month-block bootstrap).  The ridge model,
#        the no-fitting rule and the level target of Test A are not refit (not named in D1).
#   (c8) Each bootstrap set (each k, each growth pair, the common-month table) uses a fresh generator with seed 20261020, so
#        k = 1 uses exactly Test A's month-block draws.
#   (c9) Per-test-year Spearman means are also written (descriptive; not named by the addendum).
# Outputs: data/db/wiki_led/dirs/d1_books/ (targets.parquet, preds_k{1,3,6,12}.parquet, results.json, tables.md);
# the report data/reports/dir_d1_horizons_books.md is written from results.json and tables.md.
#   Run from code/:  bash ../jobs/heavy_lock.sh nice -n 10 ../.venv/bin/python -u main_study/wiki_led/dirs/d1_horizons_books.py
import sys, os, json, time, pathlib, hashlib, resource, argparse
import numpy as np, pandas as pd
from scipy.stats import spearmanr
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
REC = ROOT / 'prereg' / 'wiki_led_settings_2026-10-20.json'
ADD_I = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-22_i_directions.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == '88d895c38c128753aaaabf3294c85969c066db8b0852089ae6e47609958c145b', 'settings record changed'
assert hashlib.sha256(ADD_I.read_bytes()).hexdigest() == '5659fbc6e63f5c477603564971dd9e4cb82bfcda57d1e9f1ae03915460ddb58e', 'addendum i changed'
SET = json.loads(ADD_I.read_text())['D1_horizons_books']
OUT = D / 'db' / 'wiki_led' / 'dirs' / 'd1_books'
OUT.mkdir(parents=True, exist_ok=True)
REP = D / 'reports'
SEED = 20261020
KS = (1, 3, 6, 12)
NB = 2000
T0 = time.time()
os.nice(5)
ap = argparse.ArgumentParser()
ap.add_argument('--refit', action='store_true', help='refit even when preds_k*.parquet exist')
REFIT = ap.parse_args().refit


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


def peak_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20


def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def ym(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


SCORE0 = mi_of('2019-01')

# ---------------------------------------------------------------- excluded months (as Test A)
P = pd.read_parquet(D / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok']).drop_duplicates(['format', 'mi'])
EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= mi_of('2015-01')}
TA = json.loads((REP / 'wiki_led_test_a_c.json').read_text())
assert sorted(ym(m) for m in EXCL) == TA['excluded_months'], 'excluded months differ from Test A'
log('excluded months', sorted(ym(m) for m in EXCL))

# ---------------------------------------------------------------- loans panel (as Test A)
W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id'])
C = pd.read_parquet(D / 'db' / 'study2r' / 'counts_work.parquet')
L = C.groupby(['work_id', 'mi']).y.sum()
first = L[L > 0].reset_index().groupby('work_id').mi.min()
MI = np.arange(mi_of('2005-04'), mi_of('2026-08') + 1)
LW = L.unstack('mi').reindex(columns=MI).fillna(0).astype(np.float32).reindex(W.work_id).fillna(0)
A = LW.values.copy()
f0 = first.reindex(W.work_id).values                                   # every work has a first loan (checked below)
assert not np.isnan(f0.astype(float)).any()
A[MI[None, :] < f0[:, None]] = np.nan                                  # months before the first loan: not in the collection
ex_mask = np.isin(MI, sorted(EXCL))
LAST = len(MI) - 1
log('loans panel', A.shape, 'last month', ym(MI[-1]))
del C, L, LW

# ---------------------------------------------------------------- rows (Test A's corrected rows)
WCOLS = [f'{p}_{c}' for p in ('b', 'a') for c in ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']]
HCOLS = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
R = pd.read_parquet(D / 'db' / 'wiki_led' / 'test_a_rows_c.parquet',
                    columns=['work_id', 'mi', 'L_t', 'L_next', 'M6', 'D', 'Sg', 'year'] + HCOLS + WCOLS)
log('rows', R.shape)
wpos = pd.Index(W.work_id).get_indexer(R.work_id)
assert (wpos >= 0).all()
j = (R.mi.values - MI[0]).astype(int)
chk_next = A[wpos, j + 1]
assert np.array_equal(chk_next, R.L_next.values.astype(np.float32)), 'loans panel does not match Test A L_next'
assert np.array_equal(A[wpos, j], R.L_t.values.astype(np.float32)), 'loans panel does not match Test A L_t'
assert not ex_mask[j].any() and not ex_mask[j + 1].any(), 'Test A rows with an excluded t or t+1'

# ---------------------------------------------------------------- targets
M6 = R.M6.values.astype(np.float32)
T = {}
tg_parts = []
for k in KS:
    ok = (j + k) <= LAST
    cols = np.clip(j[:, None] + np.arange(1, k + 1)[None, :], 0, LAST)
    win = A[wpos[:, None], cols]                                       # rows x k, float32
    ok &= ~ex_mask[cols].any(axis=1)
    ok &= ~np.isnan(win).any(axis=1)
    mean_k = win.mean(axis=1, dtype=np.float32).astype(np.float32)
    Dk = (np.log1p(mean_k) - np.log1p(M6)).astype(np.float32)
    rose = Dk >= np.log(1.5)
    surge = (Dk >= np.log(2)) & (mean_k - M6 >= 5)
    T[k] = dict(ok=ok, D=Dk, rose=rose.astype(np.int8), surge=surge.astype(np.int8))
    tg_parts.append(pd.DataFrame({'work_id': R.work_id.values[ok], 'mi': R.mi.values[ok], 'k': k, 'mean_k': mean_k[ok],
                                  'D_k': Dk[ok], 'rose_k': rose[ok].astype(np.int8), 'surge_k': surge[ok].astype(np.int8)}))
    log(f'k={k}: rows kept {ok.sum()} of {len(R)}; scored origins', len(np.unique(R.mi.values[ok & (R.mi.values >= SCORE0)])))
d1 = T[1]['D'][T[1]['ok']]
k1_D_maxdiff = float(np.abs(d1 - R.D.values[T[1]['ok']].astype(np.float32)).max())
k1_sg_same = bool(np.array_equal(T[1]['surge'][T[1]['ok']], R.Sg.values[T[1]['ok']]))
assert T[1]['ok'].all(), 'k = 1 should keep every Test A row'
log('k=1 target check: max |D_1 - D_TestA| =', k1_D_maxdiff, ' surge identical:', k1_sg_same)
pd.concat(tg_parts, ignore_index=True).to_parquet(OUT / 'targets.parquet', index=False)
del tg_parts

# ---------------------------------------------------------------- models (Test A's settings, refit per k)
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)
MOD = {'W': WCOLS, 'H': HCOLS, 'HW': HCOLS + WCOLS}                    # HW column order as Test A (HCOLS + WCOLS)


def fit_predict(tr, te, cols):
    m = lgb.LGBMRegressor(**LGB).fit(tr[cols], tr['Dk'])
    return m.predict(te[cols])


PRED = {}
ntrain = {}
for k in KS:
    fp = OUT / f'preds_k{k}.parquet'
    Rk = R[T[k]['ok']].copy()
    Rk['Dk'] = T[k]['D'][T[k]['ok']]
    Rk['rose'] = T[k]['rose'][T[k]['ok']]
    Rk['surge'] = T[k]['surge'][T[k]['ok']]
    if fp.exists() and not REFIT:
        PRED[k] = pd.read_parquet(fp)
        log(f'k={k}: predictions read from', fp.name)
        continue
    parts, ntrain[k] = [], {}
    for Y in range(2019, 2027):
        te = Rk[(Rk.year == Y) & (Rk.mi >= SCORE0)]
        if te.empty:
            continue
        tr = Rk[(Rk.mi + k) < Y * 12]                                   # whole target window before 1 January of Y (c2)
        p = te[['work_id', 'mi', 'year', 'Dk', 'rose', 'surge', 'L_t', 'M6']].copy()
        p['P'] = (te.h_lt - te.h_m6).values                             # persistence (Test A's Hnaive_D)
        for name, cols in MOD.items():
            p[name] = fit_predict(tr, te, cols)
        parts.append(p)
        ntrain[k][Y] = int(len(tr))
        log(f'k={k} year {Y}: train {len(tr)} (origins {ym(tr.mi.min())} to {ym(tr.mi.max())}), test {len(te)}, peak {peak_mb():.0f} MB')
    PRED[k] = pd.concat(parts, ignore_index=True)
    PRED[k].to_parquet(fp, index=False)
del R

# ---------------------------------------------------------------- scoring helpers (Test A's)


def block_draws(n, rng, block=3):
    starts = np.arange(n)
    kk = int(np.ceil(n / block))
    draws = []
    for _ in range(NB):
        s = rng.choice(starts, kk)
        idx = np.concatenate([np.arange(a, a + block) % n for a in s])[:n]
        draws.append(idx)
    return np.array(draws)


def ci(x, BD):
    b = x[BD].mean(axis=1)
    return dict(mean=float(x.mean()), lo=float(np.percentile(b, 2.5)), hi=float(np.percentile(b, 97.5)))


def month_stats(p):
    """Per origin month: Spearman of each model with D_k, top-20 share rose and surged, base rates."""
    out = {}
    months = np.sort(p.mi.unique())
    g = {m: d for m, d in p.groupby('mi', sort=True)}
    for c in ('W', 'H', 'HW', 'P'):
        out[('sp', c)] = np.array([spearmanr(g[m][c], g[m]['Dk']).statistic if g[m][c].nunique() > 1 else 0.0 for m in months])
        top = p.sort_values(c, ascending=False).groupby('mi').head(20)    # as 13c: pandas default sort, first 20 per month
        out[('top_rose', c)] = top.groupby('mi').rose.mean().reindex(months).values
        out[('top_surge', c)] = top.groupby('mi').surge.mean().reindex(months).values
    out[('base', 'rose')] = p.groupby('mi').rose.mean().reindex(months).values
    out[('base', 'surge')] = p.groupby('mi').surge.mean().reindex(months).values
    return months, out


RES = {'settings': SET, 'choices': 'see header of code/main_study/wiki_led/dirs/d1_horizons_books.py (c1 to c9)', 'by_k': {},
       'growth_vs_k1': {}, 'common_months': {}, 'by_year': {}, 'k1_check': {}}
MS = {}
for k in KS:
    months, st = month_stats(PRED[k])
    MS[k] = (months, st)
    BD = block_draws(len(months), np.random.default_rng(SEED))
    r = {'n': dict(rows=int(len(PRED[k])), origin_months=int(len(months)), books=int(PRED[k].work_id.nunique()),
                   first_origin=ym(months.min()), last_origin=ym(months.max()),
                   rose_rate_rows=float(PRED[k].rose.mean()), surge_rate_rows=float(PRED[k].surge.mean()),
                   train_rows_by_test_year=ntrain.get(k, 'read from cache')),
         'spearman': {}, 'top20_rose': {}, 'top20_surge': {}}
    for c in ('W', 'H', 'HW', 'P'):
        r['spearman'][c] = ci(st[('sp', c)], BD)
        r['spearman'][c]['months_above_0'] = float((st[('sp', c)] > 0).mean())
        r['top20_rose'][c] = ci(st[('top_rose', c)], BD)
        r['top20_surge'][c] = ci(st[('top_surge', c)], BD)
    r['top20_rose']['base'] = ci(st[('base', 'rose')], BD)
    r['top20_surge']['base'] = ci(st[('base', 'surge')], BD)
    r['spearman']['HW_minus_H'] = ci(st[('sp', 'HW')] - st[('sp', 'H')], BD)
    r['spearman']['HW_minus_H']['months_above_0'] = float(((st[('sp', 'HW')] - st[('sp', 'H')]) > 0).mean())
    r['spearman']['W_minus_P'] = ci(st[('sp', 'W')] - st[('sp', 'P')], BD)
    r['top20_rose']['HW_minus_H'] = ci(st[('top_rose', 'HW')] - st[('top_rose', 'H')], BD)
    r['top20_rose']['W_minus_base'] = ci(st[('top_rose', 'W')] - st[('base', 'rose')], BD)
    RES['by_k'][str(k)] = r
    log(f'k={k}: months {len(months)}  Spearman W {r["spearman"]["W"]["mean"]:.4f} H {r["spearman"]["H"]["mean"]:.4f} '
        f'HW {r["spearman"]["HW"]["mean"]:.4f} P {r["spearman"]["P"]["mean"]:.4f}  HW-H {r["spearman"]["HW_minus_H"]["mean"]:.4f} '
        f'[{r["spearman"]["HW_minus_H"]["lo"]:.4f}, {r["spearman"]["HW_minus_H"]["hi"]:.4f}]')
    # per test year (c9)
    yr = PRED[k].groupby('mi').year.first().reindex(months).values
    RES['by_year'][str(k)] = {int(Y): {c: float(st[('sp', c)][yr == Y].mean()) for c in ('W', 'H', 'HW', 'P')} | {
        'HW_minus_H': float((st[('sp', 'HW')] - st[('sp', 'H')])[yr == Y].mean()), 'months': int((yr == Y).sum())}
        for Y in np.unique(yr)}

# growth from k = 1, paired by month on the months of k (c5)
m1, s1 = MS[1]
pos1 = {m: i for i, m in enumerate(m1)}
for k in KS[1:]:
    mk, sk = MS[k]
    assert set(mk) <= set(m1)
    i1 = np.array([pos1[m] for m in mk])
    BD = block_draws(len(mk), np.random.default_rng(SEED))
    g = {}
    for c in ('W', 'H', 'HW', 'P'):
        g[f'{c}_k_minus_k1'] = ci(sk[('sp', c)] - s1[('sp', c)][i1], BD)
    g['HWminusH_k_minus_k1'] = ci((sk[('sp', 'HW')] - sk[('sp', 'H')]) - (s1[('sp', 'HW')] - s1[('sp', 'H')])[i1], BD)
    g['HWminusH_at_k1_same_months'] = ci((s1[('sp', 'HW')] - s1[('sp', 'H')])[i1], BD)
    g['W_at_k1_same_months'] = ci(s1[('sp', 'W')][i1], BD)
    g['top20_rose_HWminusH_k_minus_k1'] = ci((sk[('top_rose', 'HW')] - sk[('top_rose', 'H')]) - (s1[('top_rose', 'HW')] - s1[('top_rose', 'H')])[i1], BD)
    g['months'] = int(len(mk))
    RES['growth_vs_k1'][str(k)] = g

# all k on the origin months of k = 12 (c6)
m12 = MS[12][0]
BD = block_draws(len(m12), np.random.default_rng(SEED))
for k in KS:
    mk, sk = MS[k]
    pk = {m: i for i, m in enumerate(mk)}
    ii = np.array([pk[m] for m in m12])
    c6 = {c: ci(sk[('sp', c)][ii], BD) for c in ('W', 'H', 'HW', 'P')}
    c6['HW_minus_H'] = ci((sk[('sp', 'HW')] - sk[('sp', 'H')])[ii], BD)
    c6['top20_rose'] = {c: ci(sk[('top_rose', c)][ii], BD) for c in ('W', 'H', 'HW', 'P')}
    c6['top20_rose']['base'] = ci(sk[('base', 'rose')][ii], BD)
    c6['months'] = int(len(m12))
    RES['common_months'][str(k)] = c6

# ---------------------------------------------------------------- k = 1 against Test A
TP = pd.read_parquet(D / 'db' / 'wiki_led' / 'test_a_preds_c.parquet', columns=['work_id', 'mi', 'Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D', 'Hnaive_D'])
q = PRED[1].merge(TP, on=['work_id', 'mi'], how='outer', indicator=True)
chk = {'rows_only_one_side': int((q._merge != 'both').sum()), 'target_D_maxdiff': k1_D_maxdiff, 'surge_identical': k1_sg_same}
for a, b in (('W', 'Wlgbm_D'), ('H', 'Hlgbm_D'), ('HW', 'HWlgbm_D'), ('P', 'Hnaive_D')):
    chk[f'pred_maxdiff_{a}'] = float((q[a] - q[b]).abs().max())
    chk[f'spearman_{a}_here'] = RES['by_k']['1']['spearman'][a]
    chk[f'spearman_{a}_testA'] = {kk: TA['change_rank'][b][kk] for kk in ('mean', 'lo', 'hi')}
chk['HW_minus_H_here'] = RES['by_k']['1']['spearman']['HW_minus_H']
chk['HW_minus_H_testA'] = TA['paired']['HW_minus_H_change_rank']
AL = pd.read_csv(REP / 'wiki_led_test_a_alert_list_c.csv', header=0, names=['model', 'k', 'rose', 'surged', 'beat'])
AL = AL[AL.k.astype(str) == '20'].set_index('model')
for a, b in (('W', 'Wikipedia only'), ('H', 'Library record'), ('HW', 'Library + Wikipedia')):
    chk[f'top20_rose_{a}'] = dict(here=RES['by_k']['1']['top20_rose'][a]['mean'], testA=float(AL.loc[b, 'rose']))
    chk[f'top20_surge_{a}'] = dict(here=RES['by_k']['1']['top20_surge'][a]['mean'], testA=float(AL.loc[b, 'surged']))
sp_diffs = [abs(chk[f'spearman_{a}_here'][s] - chk[f'spearman_{a}_testA'][s]) for a in ('W', 'H', 'HW', 'P') for s in ('mean', 'lo', 'hi')]
top_diffs = [abs(chk[f'top20_{t}_{a}']['here'] - chk[f'top20_{t}_{a}']['testA']) for a in ('W', 'H', 'HW') for t in ('rose', 'surge')]
chk['max_abs_diff_spearman_and_intervals'] = float(max(sp_diffs))
chk['max_abs_diff_top20'] = float(max(top_diffs))
chk['reproduced'] = bool(chk['rows_only_one_side'] == 0 and max(sp_diffs) < 1e-6 and max(top_diffs) < 1e-6)
RES['k1_check'] = chk
log('k=1 check: reproduced', chk['reproduced'], ' max Spearman diff', chk['max_abs_diff_spearman_and_intervals'],
    ' max top-20 diff', chk['max_abs_diff_top20'], ' max pred diff', {a: chk[f'pred_maxdiff_{a}'] for a in ('W', 'H', 'HW', 'P')})

RES['runtime_s'] = round(time.time() - T0)
RES['peak_rss_mb'] = round(peak_mb())
RES['versions'] = dict(lightgbm=lgb.__version__, pandas=pd.__version__, numpy=np.__version__)
(OUT / 'results.json').write_text(json.dumps(RES, indent=1, default=float))


# ---------------------------------------------------------------- tables for the report


def f3(d):
    return f"{d['mean']:.3f} [{d['lo']:.3f}, {d['hi']:.3f}]"


def f3s(d):
    return f"{d['mean']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}]"


def pc(d):
    return f"{100 * d['mean']:.1f}% [{100 * d['lo']:.1f}, {100 * d['hi']:.1f}]"


def pcs(d):
    return f"{100 * d['mean']:+.1f} [{100 * d['lo']:+.1f}, {100 * d['hi']:+.1f}]"


lines = []
lines.append('### Table 1. Spearman per horizon, each horizon on all its own origin months\n')
lines.append('| Horizon k | Origin months | Rows | Wikipedia only (W) | Library history (H) | Library + Wikipedia (HW) | Persistence | HW minus H |')
lines.append('|---|---|---|---|---|---|---|---|')
for k in KS:
    r = RES['by_k'][str(k)]
    lines.append(f"| {k} | {r['n']['origin_months']} ({r['n']['first_origin']} to {r['n']['last_origin']}) | {r['n']['rows']:,} | "
                 f"{f3(r['spearman']['W'])} | {f3(r['spearman']['H'])} | {f3(r['spearman']['HW'])} | {f3(r['spearman']['P'])} | "
                 f"{f3s(r['spearman']['HW_minus_H'])} |")
lines.append('\n### Table 2. Share of each model\'s top 20 per month that rose (mean of next k months at least 1.5 times normal)\n')
lines.append('| Horizon k | Base rate (all books) | W | H | HW | Persistence | HW minus H (points) |')
lines.append('|---|---|---|---|---|---|---|')
for k in KS:
    r = RES['by_k'][str(k)]['top20_rose']
    lines.append(f"| {k} | {pc(r['base'])} | {pc(r['W'])} | {pc(r['H'])} | {pc(r['HW'])} | {pc(r['P'])} | {pcs(r['HW_minus_H'])} |")
lines.append('\n### Table 3. Share of each model\'s top 20 per month that surged (mean at least 2 times normal and 5 loans more)\n')
lines.append('| Horizon k | Base rate | W | H | HW | Persistence |')
lines.append('|---|---|---|---|---|---|')
for k in KS:
    r = RES['by_k'][str(k)]['top20_surge']
    lines.append(f"| {k} | {pc(r['base'])} | {pc(r['W'])} | {pc(r['H'])} | {pc(r['HW'])} | {pc(r['P'])} |")
lines.append('\n### Table 4. Change from k = 1, paired by origin month (months where both horizons exist)\n')
lines.append('| Horizon k | Months | W at k=1 (same months) | W: k minus 1 | H: k minus 1 | HW minus H at k=1 (same months) | HW minus H: k minus 1 | Top-20 rose, HW minus H: k minus 1 (points) |')
lines.append('|---|---|---|---|---|---|---|---|')
for k in KS[1:]:
    g = RES['growth_vs_k1'][str(k)]
    lines.append(f"| {k} | {g['months']} | {f3(g['W_at_k1_same_months'])} | {f3s(g['W_k_minus_k1'])} | {f3s(g['H_k_minus_k1'])} | "
                 f"{f3s(g['HWminusH_at_k1_same_months'])} | {f3s(g['HWminusH_k_minus_k1'])} | {pcs(g['top20_rose_HWminusH_k_minus_k1'])} |")
lines.append(f'\n### Table 5. Every horizon on the same {len(m12)} origin months (those available at k = 12)\n')
lines.append('| Horizon k | W | H | HW | Persistence | HW minus H | Top-20 rose: base | Top-20 rose: H | Top-20 rose: HW | Top-20 rose: W |')
lines.append('|---|---|---|---|---|---|---|---|---|---|')
for k in KS:
    c6 = RES['common_months'][str(k)]
    lines.append(f"| {k} | {f3(c6['W'])} | {f3(c6['H'])} | {f3(c6['HW'])} | {f3(c6['P'])} | {f3s(c6['HW_minus_H'])} | "
                 f"{pc(c6['top20_rose']['base'])} | {pc(c6['top20_rose']['H'])} | {pc(c6['top20_rose']['HW'])} | {pc(c6['top20_rose']['W'])} |")
lines.append('\n### Table 6. Spearman by test year (mean over that year\'s origin months; descriptive)\n')
lines.append('| Horizon k | Test year | Months | W | H | HW | Persistence | HW minus H |')
lines.append('|---|---|---|---|---|---|---|---|')
for k in KS:
    for Y, v in RES['by_year'][str(k)].items():
        lines.append(f"| {k} | {Y} | {v['months']} | {v['W']:.3f} | {v['H']:.3f} | {v['HW']:.3f} | {v['P']:.3f} | {v['HW_minus_H']:+.3f} |")
lines.append('\n### Table 7. Check: k = 1 against Test A (corrected)\n')
lines.append('| Measure | This script | Test A |')
lines.append('|---|---|---|')
for a, nm in (('W', 'W'), ('H', 'H'), ('HW', 'HW'), ('P', 'Persistence')):
    lines.append(f"| Spearman {nm} | {f3(chk[f'spearman_{a}_here'])} | {f3(chk[f'spearman_{a}_testA'])} |")
lines.append(f"| HW minus H | {f3s(chk['HW_minus_H_here'])} | {f3s(chk['HW_minus_H_testA'])} |")
for a in ('W', 'H', 'HW'):
    lines.append(f"| Top-20 rose {a} | {100 * chk[f'top20_rose_{a}']['here']:.2f}% | {100 * chk[f'top20_rose_{a}']['testA']:.2f}% |")
    lines.append(f"| Top-20 surged {a} | {100 * chk[f'top20_surge_{a}']['here']:.2f}% | {100 * chk[f'top20_surge_{a}']['testA']:.2f}% |")
lines.append(f"\nLargest difference in a prediction (k = 1 against test_a_preds_c.parquet): W {chk['pred_maxdiff_W']:.2e}, "
             f"H {chk['pred_maxdiff_H']:.2e}, HW {chk['pred_maxdiff_HW']:.2e}, persistence {chk['pred_maxdiff_P']:.2e}; "
             f"rows on one side only: {chk['rows_only_one_side']}; largest target difference {chk['target_D_maxdiff']:.2e}. "
             f"Reproduced: {'yes' if chk['reproduced'] else 'NO'}.")
lines.append('\n### Table 8. Rows, months and base rates per horizon\n')
lines.append('| Horizon k | Rows scored | Origin months | Books | Rose (rows) | Surged (rows) | Training rows by test year |')
lines.append('|---|---|---|---|---|---|---|')
for k in KS:
    n = RES['by_k'][str(k)]['n']
    tr = n['train_rows_by_test_year']
    trs = ', '.join(f'{y}: {v:,}' for y, v in tr.items()) if isinstance(tr, dict) else tr
    lines.append(f"| {k} | {n['rows']:,} | {n['origin_months']} | {n['books']:,} | {100 * n['rose_rate_rows']:.1f}% | {100 * n['surge_rate_rows']:.1f}% | {trs} |")
(OUT / 'tables.md').write_text('\n'.join(lines) + '\n')
log('done; results.json and tables.md written; peak', round(peak_mb()), 'MB')
