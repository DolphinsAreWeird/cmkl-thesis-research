# q02. Addendum q, step 3: the frozen forecasts of the blind month for HM60.  Settings: prereg/addenda_wiki_led/2026-11-26_q_wikipedia_on_top_of_5_years.json,
# tests.Q3_blind_month (read-only; SHA-256 checked).  Code copied from o03_freeze.py, part 2 (no Chronos-2 here).
# HM60 (and HM, for the check) fitted with five seeds on every row whose target month is 2026-08 or earlier (all rows with origin up to 2026-07);
# C from o01's feat_C.parquet; the forecast is the mean over the five seeds.  HMW14C's frozen forecasts are in prereg/blind_o/ already.
# Check: seed 20261020's HM equals addendum l's frozen HM_D (prereg/blind_l/forecasts_origin_2026-08.csv).
# Refuses to run if any month after 2026-08 has been downloaded (data/raw/modern/final_test/), as l05_freeze.py, and never overwrites.
# Outputs: prereg/blind_q/forecasts_origin_2026-08.csv and forecasts_origin_2026-08_meta.json (SHA-256 into prereg/README.md).
#   Run from handoff/:  bash jobs/bg.sh q02_freeze main_study/wiki_led/q_wiki_on_5_years/q02_freeze.py
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '4')
import sys, json, time, hashlib, pathlib
import numpy as np, pandas as pd
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-26_q_wikipedia_on_top_of_5_years.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f4dffc8f803fd86e6914db73d32924052e044a1b9050b0d02b48d6dae0c77c4a', 'addendum q changed'
NEW = DATA / 'raw' / 'modern' / 'final_test'
assert not NEW.exists() or not any(NEW.iterdir()), 'a month after 2026-08 has been downloaded: no blind forecast can be frozen'
L = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
OOUT = DATA / 'db' / 'wiki_led' / 'o_transformer_check'
FZ = ROOT / 'prereg' / 'blind_q'
FZ.mkdir(exist_ok=True)
ORIGIN, O_YM, T_YM = 2026 * 12 + 7, '2026-08', '2026-09'
CSV = FZ / f'forecasts_origin_{O_YM}.csv'
assert not CSV.exists(), 'forecasts already frozen; never overwritten'
SEEDS = [20261020 + i for i in range(5)]
os.nice(5)
T0 = time.time()


def log(*x):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *x, flush=True)


FMTS = ['print', 'ebook', 'audiobook']
HMC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'fmt', 'cal_month', 'cal_days']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEEDS[0], n_jobs=4, verbose=-1)

R = pd.read_parquet(L / 'rows.parquet')
R['format'] = R.format.astype(str)
R['fmt'] = R.format.map({f: i for i, f in enumerate(FMTS)}).astype('int8')
te_ix = np.flatnonzero(R.mi.to_numpy() == ORIGIN)
tr_ix = np.flatnonzero((R.mi.to_numpy() + 1) <= ORIGIN)
assert len(te_ix) == 20122 and R.D.iloc[te_ix].isna().all() and R.D.iloc[tr_ix].notna().all()
C = pd.read_parquet(OOUT / 'feat_C.parquet')
assert len(C) == len(R) and (C.work_id.to_numpy() == R.work_id.to_numpy()).all() and (C.mi.to_numpy() == R.mi.to_numpy()).all()
CC = [c for c in C.columns if c.startswith('c_')]
assert len(CC) == 35
R = pd.concat([R, pd.DataFrame({c: C[c].to_numpy(np.float32) for c in CC})], axis=1)
del C
MODELS = {'HM': HMC, 'HM60': HMC + CC}
tr, te = R.iloc[tr_ix], R.iloc[te_ix]
P_ = {}
for name, cols in MODELS.items():
    ps = []
    for seed in (SEEDS[:1] if name == 'HM' else SEEDS):
        m = lgb.LGBMRegressor(**{**LGB, 'random_state': seed}).fit(tr[cols], tr['D'], categorical_feature=['cal_month'])
        ps.append(m.predict(te[cols]))
        log('fit', name, seed)
    P_[name] = np.mean(ps, axis=0)

out = te[['work_id', 'format', 'L_t', 'M6', 'h_lt', 'h_m6', 'has_book_page', 'has_author_page']].copy()
out['origin'] = O_YM; out['target'] = T_YM
out['not_yet'] = ((te.h_lt - te.h_m6) < np.log(1.5)).astype(int).to_numpy()
out['naive_D'] = (te.h_lt - te.h_m6).to_numpy()
out['HM60_D'] = P_['HM60']
# check against addendum l's frozen HM (same rows, settings and seed)
FL = pd.read_csv(ROOT / 'prereg' / 'blind_l' / 'forecasts_origin_2026-08.csv', usecols=['work_id', 'format', 'HM_D'])
ck = out[['work_id', 'format']].assign(s1=P_['HM']).merge(FL, on=['work_id', 'format'], how='outer', validate='one_to_one', indicator=True)
dmax = float((ck.s1 - ck.HM_D).abs().max())
log('check: seed 20261020 HM against addendum l frozen HM_D, rows', int((ck._merge == 'both').sum()), 'of', len(ck), 'largest difference', dmax)
assert (ck._merge == 'both').all() and dmax < 1e-6
out = out.sort_values(['format', 'work_id']).reset_index(drop=True)
out.to_csv(CSV, index=False, float_format='%.10g')
sha = hashlib.sha256(CSV.read_bytes()).hexdigest()
meta = dict(record='prereg/addenda_wiki_led/2026-11-26_q_wikipedia_on_top_of_5_years.json', made=time.strftime('%Y-%m-%d %H:%M %z'),
            made_utc=time.strftime('%Y-%m-%d %H:%M', time.gmtime()) + ' UTC', origin=O_YM, target=T_YM, training_rows=int(len(tr_ix)),
            forecast_rows=int(len(out)), by_format=out.format.value_counts().to_dict(), csv_sha256=sha, no_month_after_2026_08=True,
            seeds=SEEDS, lightgbm_settings=LGB, check_HM_seed1_equals_blind_l=dmax,
            columns=f'HM60_D: predicted change D = ln(1 + L({T_YM})) - ln(1 + M6) of HM60 (history, calendar and the 35 plain 60-month features, no '
                    f'Wikipedia), mean over five seeds; naive_D: ln(1+L_t) - ln(1+M6). HMW14C_D for the same rows is in prereg/blind_o/.')
(FZ / f'forecasts_origin_{O_YM}_meta.json').write_text(json.dumps(meta, indent=1, default=str))
os.chmod(CSV, 0o444)
log(json.dumps(meta, default=str))
log('meta sha256', hashlib.sha256((FZ / f'forecasts_origin_{O_YM}_meta.json').read_bytes()).hexdigest())
