# Method benchmark, stage 1: Chronos-Bolt (small), zero-shot and univariate, on each series' monthly log share.
# Context at origin t = the series' log share up to and including month t (missing months stay missing, leading
# missing months dropped, at most the last 512 months); forecast = the 0.5 quantile for t+1 and t+2.
# Forecasts are made for exactly the rows the Study 4 naive forecast covers (same series, origins and horizons).
# Settings: prereg/benchmark_settings_2026-10-15.json (pipelines_new.chronos).
import os
os.environ.setdefault('OMP_NUM_THREADS', '3')
import sys, time, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import numpy as np, pandas as pd, torch
import _settings as ST

MODEL = 'amazon/chronos-bolt-small'
OUT = ST.DB / 'benchmark'
SER = ['group', 'format', 'level', 'node_id']
BATCH = 256


def main():
    torch.set_num_threads(3)
    torch.manual_seed(20261013)
    from chronos import BaseChronosPipeline
    pipe = BaseChronosPipeline.from_pretrained(MODEL, device_map='cpu', torch_dtype=torch.float32)
    OUT.mkdir(parents=True, exist_ok=True)
    F = pd.read_parquet(ST.OUT / 'features.parquet', columns=SER + ['origin_mi', 'ls_t'])
    hist = (F.dropna(subset=['ls_t']).drop_duplicates(SER + ['origin_mi'])
             .set_index(SER + ['origin_mi']).ls_t.sort_index())
    fc = pd.read_parquet(ST.OUT / 'forecasts.parquet', columns=SER + ['origin_mi', 'origin', 'h', 'tmonth', 'y_true', 'y_t', 'model'])
    fc = fc[fc.model == 'naive'].drop(columns='model')
    jobs = fc[SER + ['origin_mi']].drop_duplicates().reset_index(drop=True)
    series = {k: g.droplevel(list(range(len(SER)))) for k, g in hist.groupby(level=list(range(len(SER))))}
    ctx, keep = [], []
    for r in jobs.itertuples(index=False):
        s = series.get(tuple(r[:4]))
        if s is None:
            continue
        s = s[s.index <= r.origin_mi]
        if len(s) == 0 or s.index.max() != r.origin_mi:
            continue
        full = s.reindex(range(int(s.index.min()), int(r.origin_mi) + 1)).to_numpy(float)[-512:]
        ctx.append(torch.tensor(full, dtype=torch.float32)); keep.append(r)
    jobs = pd.DataFrame(keep, columns=SER + ['origin_mi'])
    print(f'{time.strftime("%H:%M:%S")} {len(jobs)} series-origins to forecast', flush=True)
    preds = np.full((len(jobs), 2), np.nan)
    t0 = time.time()
    for i in range(0, len(ctx), BATCH):
        q, _ = pipe.predict_quantiles(ctx[i:i + BATCH], prediction_length=2, quantile_levels=[0.5])
        preds[i:i + BATCH] = q[..., 0].numpy()
        if (i // BATCH) % 20 == 0:
            print(f'{time.strftime("%H:%M:%S")} {i + len(ctx[i:i + BATCH])}/{len(ctx)} ({(time.time()-t0)/60:.1f} min)', flush=True)
    long = pd.concat([jobs.assign(h=1, y_hat=preds[:, 0]), jobs.assign(h=2, y_hat=preds[:, 1])], ignore_index=True)
    out = fc.merge(long, on=SER + ['origin_mi', 'h'], how='inner').assign(model='chronos', fset='-')
    out.to_parquet(OUT / 'chronos_forecasts.parquet', index=False)
    print(f'wrote {OUT / "chronos_forecasts.parquet"} ({len(out)} rows of {len(fc)} naive rows); {(time.time()-t0)/60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
