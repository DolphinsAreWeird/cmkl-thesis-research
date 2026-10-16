# Step 02 (Study 4b): Part A (change forecasts, h = 1, 2, 3) and Part B (surges, h = 2) over the record's test origins; walk-forward,
# expanding window, retrained at every origin. One part file per origin (resumable); then all forecasts together.
#   .venv/bin/python 02_run.py [--workers 3] [--limit-origins N] [--only-origins YYYY-MM,...] [--features F] [--out-dir D] [--reset]
# Long job: bash jobs/bg.sh s4b main_study/study4b/02_run.py --workers 3     (then renice -n 10 -p $(cat data/reports/s4b.pid))
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'                       # machine rule: at most 3 threads in all (workers x CatBoost threads)
import sys, json, time, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import multiprocessing as mp
import pandas as pd
import _settings as ST
import _b_run as BR


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=ST.DEFAULT_WORKERS)
    ap.add_argument('--limit-origins', type=int, default=None, help='only the first N test origins (for timing)')
    ap.add_argument('--only-origins', default=None, help='comma-separated YYYY-MM list (for timing; use a scratch --out-dir)')
    ap.add_argument('--features', default=str(ST.OUT / 'features.parquet'))
    ap.add_argument('--out-dir', default=str(ST.OUT))
    ap.add_argument('--reset', action='store_true', help='delete saved parts and start again')
    a = ap.parse_args()
    B = ST.settings()                                   # checks both hashes; stops on a mismatch
    workers, threads = ST.thread_plan(a.workers)
    out_dir = pathlib.Path(a.out_dir)
    parts = out_dir / 'forecast_parts'
    parts.mkdir(parents=True, exist_ok=True)
    feat = pathlib.Path(a.features)
    if not feat.exists():
        raise SystemExit(f'{feat} not found: run 01_features.py first')
    meta = dict(features_sha256=ST.sha256_of(feat), settings_sha256=B.sha256, study4_sha256=B.sha256_study4,
                addenda=[x[1] for x in B.addenda], addenda_study4=[x[1] for x in B.addenda_study4])
    mf = parts / '_meta.json'
    if a.reset:
        for f in parts.glob('origin_*.parquet'):
            f.unlink()
    if mf.exists() and json.loads(mf.read_text()) != meta and any(parts.glob('origin_*.parquet')):
        raise SystemExit('saved parts were made from other features or settings; use --reset to start again')
    mf.write_text(json.dumps(meta))
    F = pd.read_parquet(feat, columns=['h', 'origin_mi', 'y'])
    lo = ST.mi_from_ym(B.test_start)
    origins = sorted(int(m) for m in F[(F.origin_mi >= lo) & F.y.notna()].origin_mi.unique())
    del F
    if a.only_origins:
        origins = [m for m in origins if ST.ym_of(m) in set(a.only_origins.split(','))]
    if a.limit_origins:
        origins = origins[:a.limit_origins]
    todo = [m for m in origins if not BR.part_path(parts, m).exists()]
    print(f'{time.strftime("%H:%M:%S")} {len(origins)} test origins ({ST.ym_of(origins[0])} to {ST.ym_of(origins[-1])}), '
          f'{len(origins) - len(todo)} already saved, {len(todo)} to run; workers {workers}, CatBoost threads each {threads}', flush=True)
    t0 = time.time()
    if todo:
        # biggest training sets last to run fastest first is not needed; imap_unordered keeps all workers busy
        ctx = mp.get_context('spawn')
        with ctx.Pool(workers, initializer=BR.init_worker, initargs=(str(feat), str(parts), threads)) as pool:
            for i, (mi, n, sec) in enumerate(pool.imap_unordered(BR.run_origin, todo), 1):
                el = time.time() - t0
                eta = el / i * (len(todo) - i)
                print(f'{time.strftime("%H:%M:%S")} origin {ST.ym_of(mi)} done: {n} forecasts in {sec:.0f}s ({i}/{len(todo)}; '
                      f'elapsed {el / 60:.1f} min, estimated {eta / 60:.1f} min left, finish about '
                      f'{time.strftime("%H:%M", time.localtime(time.time() + eta))})', flush=True)
    n = BR.consolidate(parts, out_dir / 'forecasts.parquet')
    print(f'{time.strftime("%H:%M:%S")} wrote {out_dir / "forecasts.parquet"} ({n} rows from '
          f'{len(list(parts.glob("origin_*.parquet")))} origins); total {(time.time() - t0) / 60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
