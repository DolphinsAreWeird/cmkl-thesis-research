# Method benchmark, stage 2e: the record's level models and Chronos-Bolt at horizon 3 (Seattle), so that the record's combinations exist at horizon 3
# (addendum 2e, level_models_h3). Same code paths as Study 4 (ridge, CatBoost) and the benchmark record (LightGBM, Chronos-Bolt small); horizon 3 rows come
# from the Study 4b feature table, which was checked equal to the Study 4 table at horizons 1 and 2.
#   --part models : ridge_D, ridge_DW, catboost_D, catboost_DW, lightgbm_D, lightgbm_DW at h = 3, origins in parallel (workers x 1 thread)
#   --part bolt   : Chronos-Bolt (small, zero-shot, univariate, stage-1 construction) at h = 3
#   ../../../.venv/bin/python 11_level_h3.py --part models --workers 3        (run under jobs/heavy_lock.sh)
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_v] = '1'
import sys, time, json, pathlib, argparse, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import multiprocessing as mp
import _stage2_common as C
import _models as M
import _settings as ST

H = 3
_W = {}


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def init_worker(parts_name='parts_level_h3'):
    F = pd.read_parquet(ST.DB / 'study4b' / 'features.parquet')
    F = F[F.h == H].reset_index(drop=True)
    LG = _load('lg', '01_lightgbm.py')
    LG.PARAMS['n_jobs'] = 1
    _W.update(F=F, S=ST.settings(), LG=LG, out=C.OUT / parts_name)


def run_origin(t):
    t0 = time.time()
    F, S, LG = _W['F'], _W['S'], _W['LG']
    te, tr = M.test_rows(F, t, H), M.training_rows(F, t, H)
    out = []
    if len(te) and len(tr) >= 30:
        assert (tr.origin_mi + H <= t).all()
        base = te[C.K + ['tmonth']].copy()
        for fs, tag in (('D', 'D'), ('D+W', 'DW')):
            p, _ = M.fit_predict_ridge(tr, te, fs, H, S)
            out.append(base.assign(pipe=f'ridge_{tag}', y_hat=p))
            out.append(base.assign(pipe=f'catboost_{tag}', y_hat=M.fit_predict_catboost(tr, te, fs, S, 1)))
            out.append(base.assign(pipe=f'lightgbm_{tag}', y_hat=LG.fit_predict(tr, te, fs)))
    df = pd.concat(out, ignore_index=True) if out else pd.DataFrame()
    p = _W['out'] / f'origin_{ST.ym_of(t)}.parquet'
    df.to_parquet(p.with_suffix('.tmp'), index=False); os.replace(p.with_suffix('.tmp'), p)
    return t, len(df), time.time() - t0


def part_models(workers, only=None):
    parts_name = 'parts_level_h3_test' if only else 'parts_level_h3'
    parts = C.OUT / parts_name
    parts.mkdir(parents=True, exist_ok=True)
    S = ST.settings()
    F = pd.read_parquet(ST.DB / 'study4b' / 'features.parquet', columns=['h', 'origin_mi', 'y'])
    lo = ST.mi_from_ym(S.test_start)
    origins = sorted(int(m) for m in F[(F.h == H) & (F.origin_mi >= lo) & F.y.notna()].origin_mi.unique())
    if only:
        origins = [m for m in origins if ST.ym_of(m) in set(only.split(','))]
    todo = [m for m in origins if not (parts / f'origin_{ST.ym_of(m)}.parquet').exists()]
    print(f'{time.strftime("%H:%M:%S")} {len(origins)} origins at h = {H}, {len(todo)} to run; workers {workers} x 1 thread', flush=True)
    t0 = time.time()
    if todo:
        with mp.get_context('spawn').Pool(workers, initializer=init_worker, initargs=(parts_name,)) as pool:
            for i, (mi, n, sec) in enumerate(pool.imap_unordered(run_origin, todo), 1):
                el = time.time() - t0
                print(f'{time.strftime("%H:%M:%S")} origin {ST.ym_of(mi)}: {n} forecasts in {sec:.0f}s ({i}/{len(todo)}; {el / 60:.1f} min, about {el / i * (len(todo) - i) / 60:.0f} min left)', flush=True)
    if only:
        print('only-origins given: structure check, no consolidated file', flush=True)
        return
    P = pd.concat([pd.read_parquet(f) for f in sorted(parts.glob('origin_*.parquet'))], ignore_index=True)
    P.to_parquet(C.OUT / 'level_h3_forecasts.parquet', index=False)
    print(f'{time.strftime("%H:%M:%S")} wrote level_h3_forecasts.parquet ({len(P)} rows); {(time.time() - t0) / 60:.1f} min', flush=True)


def part_bolt():
    os.environ['OMP_NUM_THREADS'] = '3'
    import torch
    torch.set_num_threads(3)
    torch.manual_seed(C.SEED)
    from chronos import BaseChronosPipeline
    c2 = _load('c2', '09_chronos2.py')
    base = C.base_rows()
    base = base[(base.h == H)].reset_index(drop=True)
    hist = C.history()
    T, inputs = c2.build_tasks(base, hist, {}, 'chronos2')
    ctx = [torch.tensor(d['target'], dtype=torch.float32) for d in inputs]
    pipe = BaseChronosPipeline.from_pretrained('amazon/chronos-bolt-small', device_map='cpu', torch_dtype=torch.float32)
    t0 = time.time()
    preds = np.full(len(ctx), np.nan)
    for i in range(0, len(ctx), 256):
        q, _ = pipe.predict_quantiles(ctx[i:i + 256], prediction_length=3, quantile_levels=[0.5])
        preds[i:i + 256] = q[..., 0].numpy()[:, 2]
        if (i // 256) % 40 == 0:
            print(f'{time.strftime("%H:%M:%S")} {i + len(ctx[i:i + 256])}/{len(ctx)} ({(time.time() - t0) / 60:.1f} min)', flush=True)
    T = T.assign(h=H, y_hat=preds)
    R = base[C.K].merge(T[C.K + ['y_hat']], on=C.K, how='inner')
    R['pipe'] = 'chronos'
    R.to_parquet(C.OUT / 'chronos_bolt_h3_forecasts.parquet', index=False)
    print(f'{time.strftime("%H:%M:%S")} wrote chronos_bolt_h3_forecasts.parquet ({len(R)} rows of {len(base)}); {(time.time() - t0) / 60:.1f} min', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--part', default='models')
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--only-origins', default=None)
    a = ap.parse_args()
    C.check_addendum()
    part_models(a.workers, a.only_origins) if a.part == 'models' else part_bolt()
