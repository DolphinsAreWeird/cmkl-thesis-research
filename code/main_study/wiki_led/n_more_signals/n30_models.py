# n30. Addendum n: the LightGBM models of parts 1, 2, 3a and the stacking of 3c, five seeds.  Settings:
# prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json (read-only; SHA-256 checked).  Rows, history and Wikipedia features,
# LightGBM settings, walk-forward and target D are addendum l's (as addendum m's m03_models.py, whose code this copies).
# Feature files (row order of l_books_in_time/rows.parquet up to origin 2026-07, checked): feat_BA (3a donors), feat_N, feat_AD, feat_LK,
#   feat_OL, feat_AZ (parts 1 and 2; real columns <X>_*, t-12 columns <X>l_*), feat_Z (3c, Chronos-2 predictions).
# Usage (from code/):  ../.venv/bin/python main_study/wiki_led/n_more_signals/n30_models.py PART [PART ...]   PART in 3a, 1, 2, 3c
#   A model is fitted only when its feature files exist; one .npy of test predictions per seed and model (resumable).
# Outputs: data/db/wiki_led/n_more_signals/preds/keys.parquet, preds/<seed>/<model>.npy
import sys, os, json, time, hashlib, pathlib, resource
import numpy as np, pandas as pd
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
L = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
OUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
PRED = OUT / 'preds'
PRED.mkdir(parents=True, exist_ok=True)
SEEDS = [20261020 + i for i in range(5)]
PARTS = sys.argv[1:] or ['3a']
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB', *a, flush=True)


FMTS = ['print', 'ebook', 'audiobook']
F14 = ['lvl4', 'r4', 'r1', 'run', 'dw', 'chg', 'valid4']
BC, AC = ['b_' + c for c in F14], ['a_' + c for c in F14]
W14C = BC + AC
HC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'fmt']
HMC = HC + ['cal_month', 'cal_days']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEEDS[0], n_jobs=4, verbose=-1)
LN15 = np.log(1.5)

R = pd.read_parquet(L / 'rows.parquet')
R = R[R.mi <= 2026 * 12 + 6].reset_index(drop=True)
R['format'] = R.format.astype(str)
R['fmt'] = R.format.map({f: i for i, f in enumerate(FMTS)}).astype('int8')


def load_feat(name):
    f = OUT / f'feat_{name}.parquet'
    if not f.exists():
        return None
    Fx = pd.read_parquet(f)
    assert len(Fx) == len(R) and (Fx.work_id.to_numpy() == R.work_id.to_numpy()).all() and (Fx.mi.to_numpy() == R.mi.to_numpy()).all() \
        and (Fx.format.astype(str).to_numpy() == R.format.to_numpy()).all(), f'feat_{name} rows differ from rows.parquet'
    cols = [c for c in Fx.columns if c not in ('work_id', 'format', 'mi')]
    new = pd.DataFrame({c: Fx[c].to_numpy(np.float32) for c in cols})
    del Fx
    return cols, new


FEAT = {}
for name in ('BA', 'N', 'AD', 'LK', 'OL', 'AZ', 'Z'):
    got = load_feat(name)
    if got is not None:
        FEAT[name] = got[0]
        R = pd.concat([R, got[1]], axis=1)
log('rows', len(R), '| feature files', {k: len(v) for k, v in FEAT.items()})


def cols_of(x, lag=False):
    pre = f'{x}l_' if lag else f'{x}_'
    return [c for c in FEAT.get(x, []) if c.startswith(pre)]


MODELS = {}
if '3a' in PARTS and 'BA' in FEAT:
    MODELS.update({'HMB': HMC + BC, 'HMA': HMC + AC, 'HMB_donor': HMC + [c for c in FEAT['BA'] if c.startswith('Bd_')],
                   'HMA_donor': HMC + [c for c in FEAT['BA'] if c.startswith('Ad_')]})
for part, sigs in (('1', ('N', 'AD', 'LK', 'OL')), ('2', ('AZ',))):
    if part not in PARTS:
        continue
    for X in sigs:
        if X not in FEAT:
            log('features missing, skipped:', X)
            continue
        Xr, Xl = cols_of(X), cols_of(X, lag=True)
        assert len(Xr) == len(Xl) > 0
        MODELS[f'HMW14{X}'] = HMC + W14C + Xr
        MODELS[f'{X}_alone'] = Xr + ['fmt']
        MODELS[f'HMW14{X}_lag'] = HMC + W14C + Xl
    if part == '1' and all(X in FEAT for X in sigs):
        MODELS['HMW14_ALL'] = HMC + W14C + sum((cols_of(X) for X in sigs), [])
        MODELS['ALL_lag'] = HMC + W14C + sum((cols_of(X, lag=True) for X in sigs), [])
if '3c' in PARTS and 'Z' in FEAT:
    MODELS['HMW14Z'] = HMC + W14C + [c for c in FEAT['Z'] if c.startswith('Z_')]
log('models', list(MODELS))

TEST = [(Y, np.flatnonzero(((R.year == Y) & (R.mi >= 2019 * 12)).to_numpy())) for Y in range(2019, 2027)]
TEST = [(Y, ix) for Y, ix in TEST if len(ix)]
allix = np.concatenate([ix for _, ix in TEST])
kf = PRED / 'keys.parquet'
keys = R.loc[allix, ['work_id', 'format', 'mi', 'year', 'D', 'Sg', 'L_next', 'h_lt', 'h_m6', 'h_age', 'has_book_page', 'has_author_page']].reset_index(drop=True)
keys['rose'] = (keys.D >= LN15).astype('int8')
keys['not_yet'] = (keys.h_lt - keys.h_m6) < LN15
if kf.exists():
    old = pd.read_parquet(kf, columns=['work_id', 'format', 'mi'])
    assert (old.work_id.to_numpy() == keys.work_id.to_numpy()).all() and (old.mi.to_numpy() == keys.mi.to_numpy()).all()
else:
    keys.to_parquet(kf, index=False)
STORED = pd.read_parquet(L / 'preds.parquet', columns=['work_id', 'format', 'mi', 'HM', 'HMW14'])
STORED['format'] = STORED.format.astype(str)
for seed in SEEDS:
    sd = PRED / str(seed)
    sd.mkdir(exist_ok=True)
    if (sd / 'HMW14.npy').exists():
        continue
    S = pd.read_parquet(L / 'five_seeds' / f'preds_{seed}.parquet', columns=['work_id', 'format', 'mi', 'HM', 'HMW14'])
    S['format'] = S.format.astype(str)
    Mg = keys[['work_id', 'format', 'mi']].merge(S, on=['work_id', 'format', 'mi'], how='left', validate='one_to_one')
    assert Mg.HM.notna().all() and Mg.HMW14.notna().all()
    for m in ('HM', 'HMW14'):
        np.save(sd / f'{m}.npy', Mg[m].to_numpy(np.float64))
    if seed == SEEDS[0]:
        Ms = keys[['work_id', 'format', 'mi']].merge(STORED, on=['work_id', 'format', 'mi'], how='left', validate='one_to_one')
        assert max(float(np.abs(Mg[m] - Ms[m]).max()) for m in ('HM', 'HMW14')) < 1e-9


def lgb_fit(tr_ix, te_ix, cols, seed):
    cat = ['cal_month'] if 'cal_month' in cols else 'auto'
    m = lgb.LGBMRegressor(**{**LGB, 'random_state': seed}).fit(R.loc[tr_ix, cols], R.loc[tr_ix, 'D'], categorical_feature=cat)
    return m.predict(R.loc[te_ix, cols])


TRAIN = {Y: np.flatnonzero(((R.mi + 1) < Y * 12).to_numpy()) for Y, _ in TEST}
Y0, ix0 = TEST[0]
d0 = float(np.abs(lgb_fit(TRAIN[Y0], ix0, HMC + W14C, SEEDS[0]) - np.load(PRED / str(SEEDS[0]) / 'HMW14.npy')[:len(ix0)]).max())
log('check: refit of HMW14, test year', Y0, 'largest difference from l04', d0)
assert d0 < 1e-9
for seed in SEEDS:
    for name, cols in MODELS.items():
        fp = PRED / str(seed) / f'{name}.npy'
        if fp.exists():
            continue
        t1 = time.time()
        np.save(fp, np.concatenate([lgb_fit(TRAIN[Y], ix, cols, seed) for Y, ix in TEST]).astype(np.float64))
        log('seed', seed, 'model', name, f'{time.time() - t1:.0f}s')
done = json.loads((OUT / 'models_done.json').read_text()) if (OUT / 'models_done.json').exists() else {}
done.update({k: v for k, v in MODELS.items()})
(OUT / 'models_done.json').write_text(json.dumps(done, indent=1))
log('done', PARTS)
