# Step 02: every model and feature set, horizons 1 and 2, over the record's test origins (walk-forward, expanding
# window, retrained at every origin). Saves one part file per origin (resumable) and then all forecasts together.
#   .venv/bin/python 02_forecast.py [--workers 3] [--limit-origins N] [--features FILE] [--out-dir DIR]
# Run long jobs with: bash jobs/bg.sh s4_forecast main_study/study4/02_forecast.py --workers 3
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'                       # the machine rule: at most 3 threads in all (workers x CatBoost threads)
import sys, json, time, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import multiprocessing as mp
import numpy as np, pandas as pd
import _settings as ST
import _forecast as FC


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=ST.DEFAULT_WORKERS)
    ap.add_argument('--limit-origins', type=int, default=None, help='only the first N test origins (for timing)')
    ap.add_argument('--features', default=str(ST.OUT / 'features.parquet'))
    ap.add_argument('--out-dir', default=str(ST.OUT))
    ap.add_argument('--reset', action='store_true', help='delete saved parts and start again')
    a = ap.parse_args()
    S = ST.settings()
    workers, threads = ST.thread_plan(a.workers)
    out_dir = pathlib.Path(a.out_dir)
    parts = out_dir / 'forecast_parts'
    parts.mkdir(parents=True, exist_ok=True)
    feat = pathlib.Path(a.features)
    if not feat.exists():
        raise SystemExit(f'{feat} not found: run 01_features.py first')
    meta = dict(features_sha256=ST.sha256_of(feat), settings_sha256=S.sha256, addenda=[x[1] for x in S.addenda])
    mf = parts / '_meta.json'
    if a.reset:
        for f in parts.glob('origin_*.parquet'):
            f.unlink()
    if mf.exists() and json.loads(mf.read_text()) != meta and any(parts.glob('origin_*.parquet')):
        raise SystemExit('saved parts were made from other features or settings; use --reset to start again')
    mf.write_text(json.dumps(meta))

    F = pd.read_parquet(feat, columns=['group', 'h', 'origin_mi', 'y'])
    lo = ST.mi_from_ym(S.test_start)
    origins = sorted(int(m) for m in F[(F.origin_mi >= lo) & F.y.notna()].origin_mi.unique())
    del F
    if a.limit_origins:
        origins = origins[:a.limit_origins]
    todo = [m for m in origins if not FC.part_path(parts, m).exists()]
    print(f'{time.strftime("%H:%M:%S")} {len(origins)} test origins ({ST.ym_of(origins[0])} to {ST.ym_of(origins[-1])}), '
          f'{len(origins) - len(todo)} already saved, {len(todo)} to run; workers {workers}, CatBoost threads each {threads}', flush=True)
    t0 = time.time()
    done_times = []
    if todo:
        ctx = mp.get_context('spawn')
        with ctx.Pool(workers, initializer=FC.init_worker, initargs=(str(feat), str(parts), threads, S)) as pool:
            for i, (mi, n, sec) in enumerate(pool.imap_unordered(FC.run_origin, todo), 1):
                done_times.append(sec)
                el = time.time() - t0
                eta = el / i * (len(todo) - i)
                print(f'{time.strftime("%H:%M:%S")} origin {ST.ym_of(mi)} done: {n} forecasts in {sec:.0f}s '
                      f'({i}/{len(todo)}; elapsed {el / 60:.1f} min, estimated {eta / 60:.1f} min left, '
                      f'finish about {time.strftime("%H:%M", time.localtime(time.time() + eta))})', flush=True)
    n = FC.consolidate(parts, out_dir / 'forecasts.parquet')
    print(f'{time.strftime("%H:%M:%S")} wrote {out_dir / "forecasts.parquet"} ({n} forecasts from '
          f'{len(list(parts.glob("origin_*.parquet")))} origins); total {(time.time() - t0) / 60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
