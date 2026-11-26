# o02. Addendum o, step 3: the new LightGBM models, five seeds, walk-forward as addendum n (n30_models.py, whose code this copies).
# Settings: prereg/addenda_wiki_led/2026-11-26_o_transformer_inputs_check.json, models (read-only; SHA-256 checked).
# Models: HMW14C = HMW14 + C; HMW14CZ = HMW14 + C + Z; HMW14Z1 = HMW14 + Z_c2; HMW14Z2 = HMW14 + Z_c2w; HMW14Zlag = HMW14 + Z_lag.
#   HM, HMW14 and HMW14Z are addendum n's stored predictions (data/db/wiki_led/n_more_signals/preds/).
# Outputs: data/db/wiki_led/o_transformer_check/preds/<seed>/<model>.npy (scored rows in the order of n's preds/keys.parquet).
#   Run from handoff/:  bash jobs/bg.sh o02_models main_study/wiki_led/o_transformer_check/o02_models.py
import sys, os, json, time, hashlib, pathlib, resource
import numpy as np, pandas as pd
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-26_o_transformer_inputs_check.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'ad6a417b47cc60b21b59742fbf79574a5370150ff78ba617e932c0a8a7fc62d6', 'addendum o changed'
L = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
NOUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
OUT = DATA / 'db' / 'wiki_led' / 'o_transformer_check'
PRED = OUT / 'preds'
PRED.mkdir(parents=True, exist_ok=True)
SEEDS = [20261020 + i for i in range(5)]
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB', *a, flush=True)


FMTS = ['print', 'ebook', 'audiobook']
F14 = ['lvl4', 'r4', 'r1', 'run', 'dw', 'chg', 'valid4']
W14C = ['b_' + c for c in F14] + ['a_' + c for c in F14]
HMC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'fmt', 'cal_month', 'cal_days']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEEDS[0], n_jobs=4, verbose=-1)

R = pd.read_parquet(L / 'rows.parquet', columns=['work_id', 'format', 'mi', 'year', 'D'] + [c for c in HMC if c != 'fmt'] + W14C)
R = R[R.mi <= 2026 * 12 + 6].reset_index(drop=True)
R['format'] = R.format.astype(str)
R['fmt'] = R.format.map({f: i for i, f in enumerate(FMTS)}).astype('int8')


def attach(path, keep):
    Fx = pd.read_parquet(path)
    Fx = Fx[Fx.mi <= 2026 * 12 + 6].reset_index(drop=True)
    assert len(Fx) == len(R) and (Fx.work_id.to_numpy() == R.work_id.to_numpy()).all() and (Fx.mi.to_numpy() == R.mi.to_numpy()).all() \
        and (Fx.format.astype(str).to_numpy() == R.format.to_numpy()).all(), f'{path.name} rows differ from rows.parquet'
    cols = [c for c in Fx.columns if keep(c)]
    return cols, pd.DataFrame({c: Fx[c].to_numpy(np.float32) for c in cols})


ZC, Zdf = attach(NOUT / 'feat_Z.parquet', lambda c: c.startswith('Z_'))
ZLC, ZLdf = attach(OUT / 'feat_Zlag.parquet', lambda c: c.startswith('Zl_'))
CC, Cdf = attach(OUT / 'feat_C.parquet', lambda c: c.startswith('c_'))
R = pd.concat([R, Zdf, ZLdf, Cdf], axis=1)
del Zdf, ZLdf, Cdf
assert ZC == ['Z_c2', 'Z_c2w'] and ZLC == ['Zl_c2', 'Zl_c2w'] and len(CC) == 35, (ZC, ZLC, len(CC))
MODELS = {'HMW14C': HMC + W14C + CC, 'HMW14CZ': HMC + W14C + CC + ZC, 'HMW14Z1': HMC + W14C + ['Z_c2'], 'HMW14Z2': HMC + W14C + ['Z_c2w'],
          'HMW14Zlag': HMC + W14C + ZLC}
log('rows', len(R), '| models', {k: len(v) for k, v in MODELS.items()})

TEST = [(Y, np.flatnonzero(((R.year == Y) & (R.mi >= 2019 * 12)).to_numpy())) for Y in range(2019, 2027)]
TEST = [(Y, ix) for Y, ix in TEST if len(ix)]
allix = np.concatenate([ix for _, ix in TEST])
keys = pd.read_parquet(NOUT / 'preds' / 'keys.parquet', columns=['work_id', 'format', 'mi'])
assert (keys.work_id.to_numpy() == R.work_id.to_numpy()[allix]).all() and (keys.mi.to_numpy() == R.mi.to_numpy()[allix]).all()
TRAIN = {Y: np.flatnonzero(((R.mi + 1) < Y * 12).to_numpy()) for Y, _ in TEST}


def lgb_fit(tr_ix, te_ix, cols, seed):
    cat = ['cal_month'] if 'cal_month' in cols else 'auto'
    m = lgb.LGBMRegressor(**{**LGB, 'random_state': seed}).fit(R.loc[tr_ix, cols], R.loc[tr_ix, 'D'], categorical_feature=cat)
    return m.predict(R.loc[te_ix, cols])


Y0, ix0 = TEST[0]
d0 = float(np.abs(lgb_fit(TRAIN[Y0], ix0, HMC + W14C, SEEDS[0]) - np.load(NOUT / 'preds' / str(SEEDS[0]) / 'HMW14.npy')[:len(ix0)]).max())
log('check: refit of HMW14, test year', Y0, 'largest difference from the stored predictions', d0)
assert d0 < 1e-9
for seed in SEEDS:
    (PRED / str(seed)).mkdir(exist_ok=True)
    for name, cols in MODELS.items():
        fp = PRED / str(seed) / f'{name}.npy'
        if fp.exists():
            continue
        t1 = time.time()
        np.save(fp, np.concatenate([lgb_fit(TRAIN[Y], ix, cols, seed) for Y, ix in TEST]).astype(np.float64))
        log('seed', seed, 'model', name, f'{time.time() - t1:.0f}s')
(OUT / 'models_done.json').write_text(json.dumps(MODELS, indent=1))
log('done')
