# Method benchmark, stage 2a: Chronos-2 (zero-shot), alone and with interest as past covariates, on the stage-1 rows plus Seattle horizon 3.
# Settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json (stage2_pipelines.2a_chronos2); the script stops if that file changed.
# Context at origin t = the series' monthly log share up to and including month t (missing months stay missing, leading missing months dropped,
# at most the last 512 months); covariates = past covariates only (monthly, aligned with the context; a covariate missing in the whole context is dropped
# for that task). One call forecasts t+1, t+2, t+3 (median). No cross-learning between series.
#   ../../../.venv/bin/python 09_chronos2.py --variants chronos2,chronos2_cur      (run under jobs/heavy_lock.sh, nice)
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '3')
import sys, time, pathlib, argparse
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd, torch
import _stage2_common as C

MODEL = 'amazon/chronos-2'
REVISION = '29ec3766d36d6f73f0696f85560a422f50e8498c'
CHUNK, BATCH = 2048, 128
VARIANTS = {
    'chronos2': [],
    'chronos2_cur': ['cur_wlog'],
    'chronos2_curdw': ['cur_wlog', 'cur_dwi'],
    'chronos2_bk': ['bkb_wlog', 'bka_wlog'],
    'chronos2_top': ['top_wlog'],
    'chronos2_nli': ['nli_wlog'],
}
LIBRIVOX_VARIANTS = ('chronos2', 'chronos2_cur')


def patch_loader():
    """The library builds its own DataLoader with one worker process (needs a main guard on macOS and adds start-up time per call).
    Same data, same order, no extra process: num_workers 0 and no pinned memory. No change to the model or its inputs."""
    import chronos.chronos2.pipeline as P
    from torch.utils.data import DataLoader as DL

    def dl(dataset, **kw):
        kw['num_workers'] = 0
        kw['pin_memory'] = False
        return DL(dataset, **kw)
    P.DataLoader = dl


def load_covariates():
    p = C.OUT / 'monthly_cov.parquet'
    if not p.exists():
        return {}
    M = pd.read_parquet(p)                           # node_id, mi, <covariate columns>
    return {c: {n: g.set_index('mi')[c] for n, g in M[['node_id', 'mi', c]].dropna(subset=[c]).groupby('node_id')}
            for c in M.columns if c not in ('node_id', 'mi')}


def build_tasks(base, hist, covs, variant):
    cols = VARIANTS[variant]
    keys = base[C.SER + ['origin_mi']].drop_duplicates().reset_index(drop=True)
    if variant not in LIBRIVOX_VARIANTS:
        keys = keys[keys.group == 'seattle'].reset_index(drop=True)
    inputs, keep, ncov = [], [], []
    for r in keys.itertuples(index=False):
        s = hist.get((r.group, r.format, r.level, r.node_id))
        if s is None:
            continue
        s = s[s.index <= r.origin_mi]
        if len(s) == 0 or s.index.max() != r.origin_mi:
            continue
        months = np.arange(int(s.index.min()), int(r.origin_mi) + 1)[-512:]
        y = s.reindex(months).to_numpy(np.float32)
        d = {'target': y}
        pc = {}
        for c in cols:
            v = covs.get(c, {}).get(r.node_id)
            if v is None:
                continue
            a = v.reindex(months).to_numpy(np.float32)
            if np.isfinite(a).any():
                pc[c] = a
        if pc:
            d['past_covariates'] = pc
        inputs.append(d); keep.append(r); ncov.append(len(pc))
    T = pd.DataFrame(keep, columns=list(keys.columns))
    T['ncov'] = ncov
    return T, inputs


def run_variant(variant, pipe, base, hist, covs, limit=None):
    parts = C.OUT / ('chronos2_parts_test' if limit else 'chronos2_parts') / variant
    parts.mkdir(parents=True, exist_ok=True)
    T, inputs = build_tasks(base, hist, covs, variant)
    if limit:
        T, inputs = T.iloc[:limit], inputs[:limit]
    n = len(T)
    print(f'{time.strftime("%H:%M:%S")} {variant}: {n} tasks; covariates kept per task: '
          + ', '.join(f'{k}: {v}' for k, v in T.ncov.value_counts().sort_index().items()), flush=True)
    t0 = time.time()
    for i in range(0, n, CHUNK):
        p = parts / f'chunk_{i // CHUNK:04d}.parquet'
        if p.exists():
            continue
        q, _ = pipe.predict_quantiles(inputs[i:i + CHUNK], prediction_length=3, quantile_levels=[0.5], batch_size=BATCH)
        Y = np.stack([x[0, :, 0].numpy() for x in q])               # tasks x 3
        out = T.iloc[i:i + CHUNK].copy()
        out['yhat1'], out['yhat2'], out['yhat3'] = Y[:, 0], Y[:, 1], Y[:, 2]
        out.to_parquet(p.with_suffix('.tmp'), index=False); os.replace(p.with_suffix('.tmp'), p)
        done = min(i + CHUNK, n)
        el = time.time() - t0
        print(f'{time.strftime("%H:%M:%S")} {variant}: {done}/{n} ({el / 60:.1f} min)', flush=True)
    if limit:
        print('limit given: structure check only, no forecast file written', flush=True)
        return
    P = pd.concat([pd.read_parquet(f) for f in sorted(parts.glob('chunk_*.parquet'))], ignore_index=True)
    L = pd.concat([P.assign(h=h, y_hat=P[f'yhat{h}']) for h in (1, 2, 3)], ignore_index=True)[C.K + ['y_hat', 'ncov']]
    R = base[C.K].merge(L, on=C.K, how='inner')
    R['pipe'] = variant
    R.to_parquet(C.OUT / f'{variant}_forecasts.parquet', index=False)
    print(f'{time.strftime("%H:%M:%S")} wrote {variant}_forecasts.parquet: {len(R)} rows of {len(base)} base rows; {(time.time() - t0) / 60:.1f} min', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variants', default='chronos2')
    ap.add_argument('--limit', type=int, default=None, help='first N tasks only (timing and structure checks)')
    a = ap.parse_args()
    C.check_addendum()
    torch.set_num_threads(3)
    torch.manual_seed(C.SEED)
    patch_loader()
    from chronos import Chronos2Pipeline
    pipe = Chronos2Pipeline.from_pretrained(MODEL, device_map='cpu', dtype=torch.float32, revision=REVISION)
    base, hist, covs = C.base_rows(), C.history(), load_covariates()
    print(f'{time.strftime("%H:%M:%S")} base rows {len(base)}, series {len(hist)}, covariates available: {sorted(covs)}', flush=True)
    for v in a.variants.split(','):
        if VARIANTS[v] and any(c not in covs for c in VARIANTS[v]):
            raise SystemExit(f'{v}: covariates {[c for c in VARIANTS[v] if c not in covs]} not built yet (07_stage2_features.py)')
        run_variant(v, pipe, base, hist, covs, a.limit)


if __name__ == '__main__':
    main()
