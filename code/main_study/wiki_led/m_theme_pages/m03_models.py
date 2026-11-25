# m03. Addendum m, step 4: the models, five LightGBM seeds.  Settings: prereg/addenda_wiki_led/2026-11-25_m_theme_pages_single_books.json
# (A_theme_pages.models; B_segments.five_seeds), read-only, SHA-256 checked.
#
# Rows, history and Wikipedia features, LightGBM settings, walk-forward and target D: addendum l (l_books_in_time/l04_backtest.py), unchanged.
# Theme features from m02 (feat_C, feat_A, feat_K; row order of rows.parquet up to origin 2026-07, checked).
# Models per arm X in {C, A}: HMW14X, HMX, X_alone (X + fmt), HMW14X_donor, X_donor_alone, HMW14X_lag, HMW14KX; shared HMW14K.
# HM and HMW14 come from the stored five-seed predictions of l07 (five_seeds/preds_<seed>.parquet); seed 20261020 equals l04 (checked here).
# Seeds 20261020 to 20261024, seed 20261020 first for every model.  Resumable: one .npy of test predictions per seed and model.
# Outputs: data/db/wiki_led/m_theme_pages/preds/keys.parquet, preds/<seed>/<model>.npy
#   Run from code/:  bash ../jobs/bg.sh m03_models main_study/wiki_led/m_theme_pages/m03_models.py
import sys, os, json, time, hashlib, pathlib, resource
import numpy as np, pandas as pd
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_m_theme_pages_single_books.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'df8a4fd95bb46cec3488ba062b0033156e2ded4d00678cf899471cc201663d7f', 'addendum m changed'
L = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
OUT = DATA / 'db' / 'wiki_led' / 'm_theme_pages'
PRED = OUT / 'preds'
PRED.mkdir(exist_ok=True)
SEEDS = [20261020 + i for i in range(5)]
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB', *a, flush=True)


# ---------------------------------------------------------------- settings copied from l04_backtest.py
FMTS = ['print', 'ebook', 'audiobook']
F18 = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
F14 = [c for c in F18 if c not in ('nrise8', 'rmax')]
W14C = ['b_' + c for c in F14] + ['a_' + c for c in F14]
HC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'fmt']
HMC = HC + ['cal_month', 'cal_days']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEEDS[0], n_jobs=4, verbose=-1)
LN15 = np.log(1.5)

R = pd.read_parquet(L / 'rows.parquet')
R = R[R.mi <= 2026 * 12 + 6].reset_index(drop=True)
R['format'] = R.format.astype(str)
R['fmt'] = R.format.map({f: i for i, f in enumerate(FMTS)}).astype('int8')
feat = {}
for arm in ('C', 'A', 'K'):
    Fx = pd.read_parquet(OUT / f'feat_{arm}.parquet')
    assert len(Fx) == len(R) and (Fx.work_id.to_numpy() == R.work_id.to_numpy()).all() and (Fx.mi.to_numpy() == R.mi.to_numpy()).all() \
        and (Fx.format.astype(str).to_numpy() == R.format.to_numpy()).all(), f'feat_{arm} rows differ from rows.parquet'
    cols = [c for c in Fx.columns if c not in ('work_id', 'format', 'mi')]
    for c in cols:
        R[c] = Fx[c].to_numpy(np.float32)
    feat[arm] = cols
    del Fx
log('rows', len(R), '| theme columns', {k: len(v) for k, v in feat.items()})
KC = feat['K']


def arm_cols(arm, kind):
    pre = {'real': f'{arm}_', 'donor': f'{arm}d_', 'lag': f'{arm}l_'}[kind]
    return [c for c in feat[arm] if c.startswith(pre)]


MODELS = {}
for X in ('C', 'A'):
    Xr, Xd, Xl = arm_cols(X, 'real'), arm_cols(X, 'donor'), arm_cols(X, 'lag')
    assert len(Xr) == len(Xd) == len(Xl) == 18
    MODELS[f'HMW14{X}'] = HMC + W14C + Xr
    MODELS[f'HM{X}'] = HMC + Xr
    MODELS[f'{X}_alone'] = Xr + ['fmt']
    MODELS[f'HMW14{X}_donor'] = HMC + W14C + Xd
    MODELS[f'{X}_donor_alone'] = Xd + ['fmt']
    MODELS[f'HMW14{X}_lag'] = HMC + W14C + Xl
    MODELS[f'HMW14K{X}'] = HMC + W14C + KC + Xr
MODELS['HMW14K'] = HMC + W14C + KC
ORDER = ['HMW14C', 'HMW14A', 'HMW14C_donor', 'HMW14A_donor', 'HMW14C_lag', 'HMW14A_lag', 'HMC', 'HMA', 'C_alone', 'A_alone',
         'C_donor_alone', 'A_donor_alone', 'HMW14K', 'HMW14KC', 'HMW14KA']
assert sorted(ORDER) == sorted(MODELS)

# test rows in l04's order (test year by test year)
TEST = [(Y, np.flatnonzero(((R.year == Y) & (R.mi >= 2019 * 12)).to_numpy())) for Y in range(2019, 2027)]
TEST = [(Y, ix) for Y, ix in TEST if len(ix)]
allix = np.concatenate([ix for _, ix in TEST])
keys = R.loc[allix, ['work_id', 'format', 'mi', 'year', 'D', 'Sg', 'L_next', 'h_lt', 'h_m6', 'h_age', 'has_book_page', 'has_author_page']].reset_index(drop=True)
keys['rose'] = (keys.D >= LN15).astype('int8')
keys['not_yet'] = (keys.h_lt - keys.h_m6) < LN15
keys['has_C'] = R.loc[allix, 'C_n_r4'].notna().to_numpy() | R.loc[allix, 'C_m_r4'].notna().to_numpy()
keys['has_A'] = R.loc[allix, 'A_n_r4'].notna().to_numpy() | R.loc[allix, 'A_m_r4'].notna().to_numpy()
keys.to_parquet(PRED / 'keys.parquet', index=False)
log('test rows', len(keys))

# stored HM and HMW14 (l07), aligned with keys; seed 20261020 must equal l04
STORED = pd.read_parquet(L / 'preds.parquet', columns=['work_id', 'format', 'mi', 'HM', 'HMW14'])
STORED['format'] = STORED.format.astype(str)
for seed in SEEDS:
    sd = PRED / str(seed)
    sd.mkdir(exist_ok=True)
    f = L / 'five_seeds' / f'preds_{seed}.parquet'
    S = pd.read_parquet(f, columns=['work_id', 'format', 'mi', 'HM', 'HMW14'])
    S['format'] = S.format.astype(str)
    Mg = keys[['work_id', 'format', 'mi']].merge(S, on=['work_id', 'format', 'mi'], how='left', validate='one_to_one')
    assert len(Mg) == len(keys) and Mg.HM.notna().all() and Mg.HMW14.notna().all(), f'stored five-seed predictions do not cover the rows ({seed})'
    for m in ('HM', 'HMW14'):
        np.save(sd / f'{m}.npy', Mg[m].to_numpy(np.float64))
    if seed == SEEDS[0]:
        Ms = keys[['work_id', 'format', 'mi']].merge(STORED, on=['work_id', 'format', 'mi'], how='left', validate='one_to_one')
        dmax = max(float(np.abs(Mg[m] - Ms[m]).max()) for m in ('HM', 'HMW14'))
        log('check: stored five-seed HM and HMW14, seed', seed, 'against l04 preds: largest difference', dmax)
        assert dmax < 1e-9
assert len(STORED) == len(keys)


def lgb_fit(tr_ix, te_ix, cols, seed):
    cat = ['cal_month'] if 'cal_month' in cols else 'auto'
    tr = R.loc[tr_ix, cols]
    m = lgb.LGBMRegressor(**{**LGB, 'random_state': seed}).fit(tr, R.loc[tr_ix, 'D'], categorical_feature=cat)
    return m.predict(R.loc[te_ix, cols])


TRAIN = {Y: np.flatnonzero(((R.mi + 1) < Y * 12).to_numpy()) for Y, _ in TEST}
# check of the fitting path: refitting HMW14 for test year 2019 with seed 20261020 gives l04's stored predictions
Y0, ix0 = TEST[0]
p0 = lgb_fit(TRAIN[Y0], ix0, HMC + W14C, SEEDS[0])
d0 = float(np.abs(p0 - np.load(PRED / str(SEEDS[0]) / 'HMW14.npy')[:len(ix0)]).max())
log('check: refit of HMW14, test year', Y0, 'largest difference from l04', d0)
assert d0 < 1e-9, 'the fitting path does not reproduce l04'
for seed in SEEDS:
    for name in ORDER:
        fp = PRED / str(seed) / f'{name}.npy'
        if fp.exists():
            continue
        t1 = time.time()
        parts = [lgb_fit(TRAIN[Y], ix, MODELS[name], seed) for Y, ix in TEST]
        np.save(fp, np.concatenate(parts).astype(np.float64))
        log('seed', seed, 'model', name, f'{time.time() - t1:.0f}s')
(OUT / 'models_done.json').write_text(json.dumps(dict(seeds=SEEDS, models=ORDER, columns={k: v for k, v in MODELS.items()},
                                                      runtime_s=round(time.time() - T0)), indent=1))
log('done')
