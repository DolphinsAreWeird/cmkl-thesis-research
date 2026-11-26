# o03. Addendum o, step 4: the frozen forecasts of the blind month.  Settings: prereg/addenda_wiki_led/2026-11-26_o_transformer_inputs_check.json,
# tests.O3_blind_month (read-only; SHA-256 checked).
# 1. Chronos-2 forecasts (C2, C2W) for every row of rows.parquet at origin 2026-08 (the 20,122 rows of addendum l's blind test), made as in
#    n40_chronos.py (code copied: same model and revision, 60-month context, covariates, median, minus ln(1 + M6)).
# 2. HMW14, HMW14Z, HMW14C and HMW14CZ fitted with five seeds on every row whose target month is 2026-08 or earlier (all rows with origin up to
#    2026-07), Z from n's feat_Z.parquet and C from o01's feat_C.parquet; each forecast is the mean over the five seeds.
#    Check: seed 20261020's HMW14 equals addendum l's frozen HMW14_D (prereg/blind_l/forecasts_origin_2026-08.csv).
# Refuses to run if any month after 2026-08 has been downloaded (data/raw/modern/final_test/), as l05_freeze.py, and never overwrites.
# Outputs: prereg/blind_o/forecasts_origin_2026-08.csv and forecasts_origin_2026-08_meta.json (SHA-256 into prereg/README.md, public before
#   any month after 2026-08 is downloaded).
#   Run from handoff/:  bash jobs/bg.sh o03_freeze main_study/wiki_led/o_transformer_check/o03_freeze.py
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '4')
import sys, json, time, hashlib, pathlib
import numpy as np, pandas as pd, pyarrow.parquet as pq

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-26_o_transformer_inputs_check.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'ad6a417b47cc60b21b59742fbf79574a5370150ff78ba617e932c0a8a7fc62d6', 'addendum o changed'
NEW = DATA / 'raw' / 'modern' / 'final_test'
assert not NEW.exists() or not any(NEW.iterdir()), 'a month after 2026-08 has been downloaded: the blind part moves to origin 2026-09 (record, fallback)'
L = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
TAXO = DATA / 'db' / 'taxonomy_v3'
NOUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
OUT = DATA / 'db' / 'wiki_led' / 'o_transformer_check'
FZ = ROOT / 'prereg' / 'blind_o'
FZ.mkdir(exist_ok=True)
ORIGIN, O_YM, T_YM = 2026 * 12 + 7, '2026-08', '2026-09'
CSV = FZ / f'forecasts_origin_{O_YM}.csv'
assert not CSV.exists(), 'forecasts already frozen; never overwritten'
MODEL, REVISION = 'amazon/chronos-2', '29ec3766d36d6f73f0696f85560a422f50e8498c'
BATCH, CTX = 256, 60
SEEDS = [20261020 + i for i in range(5)]
os.nice(5)
T0 = time.time()


def log(*x):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *x, flush=True)


def mi_of(y, m):
    return y * 12 + m - 1


FMTS = ['print', 'ebook', 'audiobook']
F14 = ['lvl4', 'r4', 'r1', 'run', 'dw', 'chg', 'valid4']
W14C = ['b_' + c for c in F14] + ['a_' + c for c in F14]
HMC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'fmt', 'cal_month', 'cal_days']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEEDS[0], n_jobs=4, verbose=-1)

R = pd.read_parquet(L / 'rows.parquet')
R['format'] = R.format.astype(str)
R['fmt'] = R.format.map({f: i for i, f in enumerate(FMTS)}).astype('int8')
te_ix = np.flatnonzero(R.mi.to_numpy() == ORIGIN)
tr_ix = np.flatnonzero((R.mi.to_numpy() + 1) <= ORIGIN)
assert len(te_ix) == 20122 and R.D.iloc[te_ix].isna().all() and R.D.iloc[tr_ix].notna().all()

# ---------------------------------------------------------------- 1. Chronos-2 for the origin-2026-08 rows (copied from n40_chronos.py)
ZF = OUT / f'blind_Z_origin_{O_YM}.parquet'
if not ZF.exists():
    # torch and LightGBM each bring their own copy of the OpenMP thread library and deadlock in one process (seen 26 Nov), so the
    # Chronos-2 part saves its forecasts and the script restarts itself without torch for the fits.
    import torch
    torch.set_num_threads(4)
    WA = pd.read_parquet(L / 'work_articles.parquet')
    S_ids = np.sort(pd.read_parquet(L / 'matches.parquet', columns=['work_id']).work_id.to_numpy(np.int64))
    NS = len(S_ids)
    wpos = pd.Series(np.arange(NS), index=S_ids)
    P = pd.read_parquet(DATA / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok']).drop_duplicates(['format', 'mi'])
    EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= mi_of(2015, 1)}
    MI0, MI1 = mi_of(2005, 4), mi_of(2026, 8)
    NM = MI1 - MI0 + 1
    rw = pd.read_parquet(TAXO / 'spl_record_work.parquet')
    rid, wid = rw.record_id.to_numpy(np.int64), rw.work_id.to_numpy(np.int64)
    p = np.searchsorted(S_ids, wid); p[p >= NS] = 0
    inS = S_ids[p] == wid
    LUT = np.full(int(rid.max()) + 1, -1, np.int32); LUT[rid[inS]] = p[inS]
    LOANS = {}
    for label, fname in (('print', 'book'), ('ebook', 'ebook'), ('audiobook', 'audiobook')):
        pf = pq.ParquetFile(TAXO / f'spl_rows_{fname}.parquet')
        A = np.zeros((NS, NM), np.float32)
        for g in range(pf.num_row_groups):
            t = pf.read_row_group(g, columns=['record_id', 'year', 'month', 'checkouts'])
            w = LUT[t.column('record_id').to_numpy()]
            mc = t.column('year').to_numpy().astype(np.int32) * 12 + t.column('month').to_numpy().astype(np.int32) - 1 - MI0
            k = w >= 0
            np.add.at(A, (w[k], mc[k]), t.column('checkouts').to_numpy()[k])
        first = (A > 0).argmax(axis=1)
        A = np.log1p(A)
        A[np.arange(NM)[None, :] < first[:, None]] = np.nan
        A[:, [m - MI0 for m in sorted(EXCL) if MI0 <= m <= MI1]] = np.nan
        LOANS[label] = A
    WF = pd.read_parquet(L / 'wiki_features.parquet', columns=['article', 'kind', 'mi', 'lvl4'])
    assert WF.mi.max() <= MI1
    COV = {}
    for kind, col in (('book', 'book_canonical'), ('author', 'author_canonical')):
        g = WF[WF.kind == kind]
        arts = sorted(g.article.unique()); apos = {x: i for i, x in enumerate(arts)}
        M = np.full((len(arts) + 1, NM), np.nan, np.float32)
        M[g.article.map(apos).to_numpy(), g.mi.to_numpy() - MI0] = g.lvl4.to_numpy(np.float32)
        idx = WA.set_index('work_id')[col].map(apos).reindex(S_ids).fillna(len(arts)).astype(int).to_numpy()
        COV[kind] = (M, idx)
    del WF
    log('loans and covariates ready')


    def inputs_for(ix, with_cov):
        out = []
        wi = wpos.reindex(R.work_id.to_numpy()[ix]).to_numpy()
        for r, w in zip(ix, wi):
            f = R.format.iat[r]; t = int(R.mi.iat[r])
            j1 = t - MI0
            j0 = max(0, j1 - CTX + 1)
            y = LOANS[f][w, j0:j1 + 1]
            ok = np.flatnonzero(~np.isnan(y))
            y = y[ok[0]:] if len(ok) else y
            d = {'target': y.astype(np.float32)}
            if with_cov:
                pc = {}
                for kind, nm in (('book', 'b'), ('author', 'a')):
                    M, idx = COV[kind]
                    v = M[idx[w], j0:j1 + 1][(ok[0] if len(ok) else 0):]
                    if np.isfinite(v).any():
                        pc[nm] = v.astype(np.float32)
                if pc:
                    d['past_covariates'] = pc
            out.append(d)
        return out


    import chronos.chronos2.pipeline as CP                      # noqa: E402
    from torch.utils.data import DataLoader as _DL              # noqa: E402


    def _dl(dataset, **kw):
        kw['num_workers'] = 0; kw['pin_memory'] = False
        return _DL(dataset, **kw)


    CP.DataLoader = _dl
    from chronos import Chronos2Pipeline                        # noqa: E402
    pipe = Chronos2Pipeline.from_pretrained(MODEL, device_map='cpu', dtype=torch.float32, revision=REVISION)
    ZB = {}
    for variant, with_cov in (('c2', False), ('c2w', True)):
        vals = []
        for c0 in range(0, len(te_ix), 4096):
            ix = te_ix[c0:c0 + 4096]
            q, _ = pipe.predict_quantiles(inputs_for(ix, with_cov), prediction_length=1, quantile_levels=[0.5], batch_size=BATCH)
            vals.append(np.array([x[0, 0, 0].item() for x in q], np.float32))
        yhat = np.concatenate(vals)
        ZB['Z_' + variant] = yhat - np.log1p(R.M6.to_numpy()[te_ix]).astype(np.float32)
        log('Chronos-2', variant, 'done')
    del pipe, LOANS, COV
    pd.DataFrame({'row': te_ix, **ZB}).to_parquet(ZF)
    log('Chronos-2 forecasts saved; restarting without torch for the fits')
    os.execv(sys.executable, [sys.executable, '-u'] + sys.argv)
ZB = pd.read_parquet(ZF)
assert (ZB.row.to_numpy() == te_ix).all()
ZB = {c: ZB[c].to_numpy(np.float32) for c in ('Z_c2', 'Z_c2w')}

# ---------------------------------------------------------------- 2. features and fits
Z = pd.read_parquet(NOUT / 'feat_Z.parquet')
assert len(Z) == len(tr_ix) and (Z.work_id.to_numpy() == R.work_id.to_numpy()[tr_ix]).all() and (Z.mi.to_numpy() == R.mi.to_numpy()[tr_ix]).all()
for c in ('Z_c2', 'Z_c2w'):
    v = np.full(len(R), np.nan, np.float32)
    v[tr_ix] = Z[c].to_numpy(np.float32); v[te_ix] = ZB[c]
    R[c] = v
del Z
C = pd.read_parquet(OUT / 'feat_C.parquet')
assert len(C) == len(R) and (C.work_id.to_numpy() == R.work_id.to_numpy()).all() and (C.mi.to_numpy() == R.mi.to_numpy()).all()
CC = [c for c in C.columns if c.startswith('c_')]
assert len(CC) == 35
R = pd.concat([R, pd.DataFrame({c: C[c].to_numpy(np.float32) for c in CC})], axis=1)
del C
ZC = ['Z_c2', 'Z_c2w']
MODELS = {'HMW14': HMC + W14C, 'HMW14Z': HMC + W14C + ZC, 'HMW14C': HMC + W14C + CC, 'HMW14CZ': HMC + W14C + CC + ZC}
import lightgbm as lgb                                       # noqa: E402
tr, te = R.iloc[tr_ix], R.iloc[te_ix]
P_ = {}
for name, cols in MODELS.items():
    ps = []
    for seed in SEEDS:
        m = lgb.LGBMRegressor(**{**LGB, 'random_state': seed}).fit(tr[cols], tr['D'], categorical_feature=['cal_month'])
        ps.append(m.predict(te[cols]))
        log('fit', name, seed)
    P_[name] = np.mean(ps, axis=0)
    if name == 'HMW14':
        P_['HMW14_seed1'] = ps[0]

out = te[['work_id', 'format', 'L_t', 'M6', 'h_lt', 'h_m6', 'has_book_page', 'has_author_page']].copy()
out['origin'] = O_YM; out['target'] = T_YM
out['not_yet'] = ((te.h_lt - te.h_m6) < np.log(1.5)).astype(int).to_numpy()
out['naive_D'] = (te.h_lt - te.h_m6).to_numpy()
out['Z_c2'] = te.Z_c2.to_numpy(); out['Z_c2w'] = te.Z_c2w.to_numpy()
for name in MODELS:
    out[name + '_D'] = P_[name]
# check against addendum l's frozen HMW14 (same rows, settings and seed)
FL = pd.read_csv(ROOT / 'prereg' / 'blind_l' / 'forecasts_origin_2026-08.csv', usecols=['work_id', 'format', 'HMW14_D'])
ck = out[['work_id', 'format']].assign(s1=P_['HMW14_seed1']).merge(FL, on=['work_id', 'format'], how='outer', validate='one_to_one', indicator=True)
dmax = float((ck.s1 - ck.HMW14_D).abs().max())
log('check: seed 20261020 HMW14 against addendum l frozen HMW14_D, rows', int((ck._merge == 'both').sum()), 'of', len(ck), 'largest difference', dmax)
assert (ck._merge == 'both').all() and dmax < 1e-6
out = out.sort_values(['format', 'work_id']).reset_index(drop=True)
out.to_csv(CSV, index=False, float_format='%.10g')
sha = hashlib.sha256(CSV.read_bytes()).hexdigest()
meta = dict(record='prereg/addenda_wiki_led/2026-11-26_o_transformer_inputs_check.json', made=time.strftime('%Y-%m-%d %H:%M %z'),
            made_utc=time.strftime('%Y-%m-%d %H:%M', time.gmtime()) + ' UTC', origin=O_YM, target=T_YM, training_rows=int(len(tr_ix)),
            forecast_rows=int(len(out)), by_format=out.format.value_counts().to_dict(), csv_sha256=sha, no_month_after_2026_08=True,
            seeds=SEEDS, lightgbm_settings=LGB, chronos=dict(model=MODEL, revision=REVISION, context=CTX),
            check_HMW14_seed1_equals_blind_l=dmax,
            columns=f'X_D: predicted change D = ln(1 + L({T_YM})) - ln(1 + M6), mean over five seeds; Z_c2, Z_c2w: Chronos-2 median forecast minus ln(1 + M6); naive_D: ln(1+L_t) - ln(1+M6)')
(FZ / f'forecasts_origin_{O_YM}_meta.json').write_text(json.dumps(meta, indent=1, default=str))
os.chmod(CSV, 0o444)
log(json.dumps(meta, default=str))
log('meta sha256', hashlib.sha256((FZ / f'forecasts_origin_{O_YM}_meta.json').read_bytes()).hexdigest())
