# Step 04 (Study 4b): Part B again with a secondary surge definition (addendum 2026-10-14_a_secondary_surges.json).
# One part file per origin (resumable). Reuses the saved features (features.parquet) and the Part B code paths.
#   .venv/bin/python 04_secondary_surges.py --surge-def base98|pct20 [--workers 3] [--only-origins YYYY-MM,..] [--features F] [--out-dir D] [--reset]
# Long job: bash jobs/bg.sh s4b_base98 main_study/study4b/04_secondary_surges.py --surge-def base98 --workers 3
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import sys, json, time, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import multiprocessing as mp
import pandas as pd
import _settings as ST
import _b_run as BR
import _b_surge2 as SG

_W = {}


def init_worker(features_path, parts_dir, threads, defn):
    import _settings as ST2
    _W['F'] = pd.read_parquet(features_path)
    _W.update(parts=parts_dir, threads=threads, defn=defn, B=ST2.settings())


def run_origin(mi):
    t0 = time.time()
    df = SG.forecast_origin_surge(_W['F'], mi, _W['B'], _W['defn'], _W['threads'])
    BR.write_part(df, BR.part_path(_W['parts'], mi))
    return mi, len(df), time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--surge-def', required=True, choices=SG.DEFS)
    ap.add_argument('--workers', type=int, default=ST.DEFAULT_WORKERS)
    ap.add_argument('--only-origins', default=None)
    ap.add_argument('--features', default=str(ST.OUT / 'features.parquet'))
    ap.add_argument('--out-dir', default=str(ST.OUT))
    ap.add_argument('--reset', action='store_true')
    a = ap.parse_args()
    B = ST.settings()
    workers, threads = ST.thread_plan(min(a.workers, 3))          # request: at most 3 workers
    out_dir = pathlib.Path(a.out_dir)
    parts = out_dir / f'surge_parts_{a.surge_def}'
    parts.mkdir(parents=True, exist_ok=True)
    feat = pathlib.Path(a.features)
    meta = dict(features_sha256=ST.sha256_of(feat), settings_sha256=B.sha256, study4_sha256=B.sha256_study4,
                addenda=[x[1] for x in B.addenda], surge_def=a.surge_def)
    mf = parts / '_meta.json'
    if a.reset:
        for f in parts.glob('origin_*.parquet'):
            f.unlink()
    if mf.exists() and json.loads(mf.read_text()) != meta and any(parts.glob('origin_*.parquet')):
        raise SystemExit('saved parts were made from other features or settings; use --reset')
    mf.write_text(json.dumps(meta))
    F = pd.read_parquet(feat, columns=['h', 'origin_mi', 'y'])
    lo = ST.mi_from_ym(B.test_start)
    origins = sorted(int(m) for m in F[(F.origin_mi >= lo) & F.y.notna() & (F.h == B.h_surge)].origin_mi.unique())
    del F
    if a.only_origins:
        origins = [m for m in origins if ST.ym_of(m) in set(a.only_origins.split(','))]
    todo = [m for m in origins if not BR.part_path(parts, m).exists()]
    print(f'{time.strftime("%H:%M:%S")} {a.surge_def}: {len(origins)} origins, {len(origins) - len(todo)} saved, {len(todo)} to run; workers {workers}, threads {threads}', flush=True)
    t0 = time.time()
    if todo:
        with mp.get_context('spawn').Pool(workers, initializer=init_worker, initargs=(str(feat), str(parts), threads, a.surge_def)) as pool:
            for i, (mi, n, sec) in enumerate(pool.imap_unordered(run_origin, todo), 1):
                el = time.time() - t0
                print(f'{time.strftime("%H:%M:%S")} origin {ST.ym_of(mi)} done: {n} forecasts in {sec:.0f}s ({i}/{len(todo)}; elapsed {el / 60:.1f} min, '
                      f'{el / i * (len(todo) - i) / 60:.1f} min left)', flush=True)
    n = BR.consolidate(parts, out_dir / f'forecasts_surge_{a.surge_def}.parquet')
    print(f'{time.strftime("%H:%M:%S")} wrote forecasts_surge_{a.surge_def}.parquet ({n} rows); total {(time.time() - t0) / 60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
