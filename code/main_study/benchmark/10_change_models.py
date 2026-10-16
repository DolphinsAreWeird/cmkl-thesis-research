# Method benchmark, stage 2b to 2d: models trained on the change y(t+h) - y(t), on the Study 4b feature table plus the stage-2 columns
# (features_stage2.parquet), one part file per test origin (resumable), origins in parallel (workers x threads <= 3).
#   models: ridgechg (Study 4 ridge), lgbmchg (LightGBM, benchmark settings), catchg (Study 4 CatBoost)
#   feature sets (addendum 2b to 2d): D, DW, DWS, DVcur, DVtop, DVnli, DVbk, DVcurdw  (see FSETS)
# level forecast = y(t) + predicted change. Training rows: origins s with s + h <= t and a known target (Study 4 rule); Seattle, all three formats pooled.
#   ../../../.venv/bin/python 10_change_models.py --models ridgechg,lgbmchg,catchg --fsets DVcur,DVtop --horizons 1 --tag h1_a [--workers 3] [--only-origins 2026-07]
# Run under jobs/heavy_lock.sh (bash jobs/bg.sh NAME main_study/benchmark/_locked.py 10_change_models.py ...).
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'                               # machine rule: at most 3 threads in all (workers x threads)
import sys, time, json, pathlib, argparse, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import multiprocessing as mp
import _stage2_common as C
import _features as FT
import _models as M
import _settings as ST

VOL = ['logmean4', 'ratio', 'dlog4', 'mk8']
W4 = ['w_' + c for c in VOL]
S2 = ['s_sustained', 's_resp']
FSETS = {
    'D': list(FT.D_NUM),
    'DW': list(FT.D_NUM) + list(FT.W_NUM),
    'DWS': list(FT.D_NUM) + list(FT.W_NUM) + S2,
    'DVcur': list(FT.D_NUM) + W4,
    'DVtop': list(FT.D_NUM) + ['top_' + c for c in VOL],
    'DVnli': list(FT.D_NUM) + ['nli_' + c for c in VOL],
    'DVbk': list(FT.D_NUM) + ['bkb_' + c for c in VOL] + ['bka_' + c for c in VOL],
    'DVcurdw': list(FT.D_NUM) + W4 + ['dwi'],
    'DVdem': list(FT.D_NUM) + ['dem_' + c for c in VOL],            # demand-aligned routing (14_demand_aligned.py), keyed by series, origin and horizon
}
CAT = list(FT.CAT_COLS)
MIN_TRAIN = 30
LGB_PARAMS = dict(objective='regression', n_estimators=600, learning_rate=0.05, max_depth=6, num_leaves=63, min_child_samples=20,
                  subsample=1.0, colsample_bytree=1.0, random_state=20261013, deterministic=True, force_row_wise=True, n_jobs=1, verbose=-1)
_W = {}


def fit_lgbm(tr, te, num):
    import lightgbm as lgb
    cols = list(num) + CAT
    Xtr, Xte = tr[cols].copy(), te[cols].copy()
    for c in CAT:
        cats = sorted(Xtr[c].astype(str).unique())
        Xtr[c] = pd.Categorical(Xtr[c].astype(str), categories=cats)
        Xte[c] = pd.Categorical(Xte[c].astype(str), categories=cats)
    return lgb.LGBMRegressor(**LGB_PARAMS).fit(Xtr, tr['change'].to_numpy(float), categorical_feature=CAT).predict(Xte)


def forecast_origin(F, t, S, models, fsets, horizons):
    out = []
    for h in horizons:
        te = M.test_rows(F, t, h)
        tr = M.training_rows(F, t, h)
        if len(te) == 0 or len(tr) < MIN_TRAIN:
            continue
        assert (tr.origin_mi + h <= t).all()
        trc = tr.assign(y=tr['change'])                 # Study 4 trainers fit df['y']: here the change
        base = te[C.K + ['tmonth']].copy()
        for fs in fsets:
            num = FSETS[fs]
            for mod in models:
                if mod == 'ridgechg':
                    a = M.choose_alpha(trc, num, CAT, h, S)
                    p = M._ridge_fit_predict(trc, te, num, CAT, a)
                elif mod == 'catchg':
                    p = M.fit_predict_catboost_cols(trc, te, num, CAT, S, 1)
                elif mod == 'lgbmchg':
                    p = fit_lgbm(tr, te, num)
                else:
                    raise ValueError(mod)
                out.append(base.assign(pipe=f'{mod}_{fs}', y_hat=te.ls_t.to_numpy(float) + p))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def init_worker(features_path, parts_dir, models, fsets, horizons):
    need = sorted({c for fs in fsets for c in FSETS[fs]} | set(CAT) | {'change', 'y', 'ls_t', 'tmonth', 'origin_mi', 'h', 'group', 'format', 'level', 'node_id', 'origin'})
    have = set(__import__('pyarrow.parquet', fromlist=['x']).ParquetFile(features_path).schema.names)
    F = pd.read_parquet(features_path, columns=[c for c in need if c in have])
    if 'DVdem' in fsets:
        D = pd.concat([pd.read_parquet(C.OUT / f'features_dem_h{h}.parquet') for h in horizons], ignore_index=True)
        F = F.merge(D[C.K + ['dem_' + c for c in VOL]], on=C.K, how='left')
    _W.update(F=F, parts=pathlib.Path(parts_dir), models=models, fsets=fsets, horizons=horizons, S=ST.settings())


def run_origin(t):
    t0 = time.time()
    df = forecast_origin(_W['F'], t, _W['S'], _W['models'], _W['fsets'], _W['horizons'])
    p = _W['parts'] / f'origin_{ST.ym_of(t)}.parquet'
    df.to_parquet(p.with_suffix('.tmp'), index=False); os.replace(p.with_suffix('.tmp'), p)
    return t, len(df), time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--models', default='ridgechg,lgbmchg,catchg')
    ap.add_argument('--fsets', required=True)
    ap.add_argument('--horizons', default='1')
    ap.add_argument('--tag', required=True)
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--only-origins', default=None)
    a = ap.parse_args()
    C.check_addendum()
    S = ST.settings()
    models, fsets, horizons = a.models.split(','), a.fsets.split(','), [int(x) for x in a.horizons.split(',')]
    feat = C.OUT / 'features_stage2.parquet'
    import pyarrow.parquet as pq
    have = set(pq.ParquetFile(feat).schema.names)
    for fs in fsets:
        miss = [c for c in FSETS[fs] if c not in have and not (fs == 'DVdem' and c.startswith('dem_'))]
        if fs == 'DVdem' and not all((C.OUT / f'features_dem_h{h}.parquet').exists() for h in horizons):
            raise SystemExit('DVdem needs features_dem_h<h>.parquet for every horizon (14_demand_aligned.py)')
        if miss:
            raise SystemExit(f'feature set {fs}: columns {miss} are not in features_stage2.parquet (run 07_stage2_features.py with the source first)')
    parts = C.OUT / f'parts_{a.tag}'
    parts.mkdir(parents=True, exist_ok=True)
    meta = dict(models=models, fsets=fsets, horizons=horizons, features_sha=C.ST.sha256_of(feat), addendum=C.ADDENDUM_SHA)
    mf = parts / '_meta.json'
    if mf.exists() and json.loads(mf.read_text()) != meta and any(parts.glob('origin_*.parquet')):
        raise SystemExit('saved parts were made with other settings or features; use a new --tag')
    mf.write_text(json.dumps(meta))
    F = pd.read_parquet(feat, columns=['h', 'origin_mi', 'y'])
    lo = ST.mi_from_ym(S.test_start)
    origins = sorted(int(m) for m in F[(F.origin_mi >= lo) & F.y.notna()].origin_mi.unique())
    del F
    if a.only_origins:
        origins = [m for m in origins if ST.ym_of(m) in set(a.only_origins.split(','))]
    todo = [m for m in origins if not (parts / f'origin_{ST.ym_of(m)}.parquet').exists()]
    print(f'{time.strftime("%H:%M:%S")} {len(origins)} test origins, {len(origins) - len(todo)} saved, {len(todo)} to run; models {models}, fsets {fsets}, '
          f'horizons {horizons}; workers {a.workers} x 1 thread', flush=True)
    t0 = time.time()
    if todo:
        ctx = mp.get_context('spawn')
        with ctx.Pool(a.workers, initializer=init_worker, initargs=(str(feat), str(parts), models, fsets, horizons)) as pool:
            for i, (mi, n, sec) in enumerate(pool.imap_unordered(run_origin, todo), 1):
                el = time.time() - t0
                print(f'{time.strftime("%H:%M:%S")} origin {ST.ym_of(mi)}: {n} forecasts in {sec:.0f}s ({i}/{len(todo)}; {el / 60:.1f} min, about '
                      f'{el / i * (len(todo) - i) / 60:.0f} min left)', flush=True)
    if a.only_origins:
        print('only-origins given: structure check, no consolidated file', flush=True)
        return
    P = pd.concat([pd.read_parquet(f) for f in sorted(parts.glob('origin_*.parquet'))], ignore_index=True)
    P.to_parquet(C.OUT / f'chg_{a.tag}_forecasts.parquet', index=False)
    print(f'{time.strftime("%H:%M:%S")} wrote chg_{a.tag}_forecasts.parquet ({len(P)} rows); {(time.time() - t0) / 60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
