# Step 04: secondary interest-flow task. Forecast the log mean weekly Wikipedia share of a category in month t+1:
# naive (last 4 weeks' mean) against CatBoost with the W features and log weekly shares at lags 1-8 and 52.
# Metrics: MAE skill against naive, Spearman of forecast change against actual change across categories, AUC for next
# month at least 1.5 times its normal level. Walk-forward by month from 2019-01, expanding window.
#   .venv/bin/python 04_interest_flow.py [--workers 3] [--limit-origins N] [--reports-dir D]
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import sys, time, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import multiprocessing as mp
import numpy as np, pandas as pd
import _settings as ST
import _flow as FL
from _eval import md_table

_W = {}


def _init(T, threads, S):
    _W.update(T=T, threads=threads, S=S)


def _run(mi):
    t0 = time.time()
    return mi, FL.flow_origin(_W['T'], mi, _W['S'], _W['threads']), time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=ST.DEFAULT_WORKERS)
    ap.add_argument('--limit-origins', type=int, default=None)
    ap.add_argument('--reports-dir', default=str(ST.REPORTS))
    ap.add_argument('--out-dir', default=str(ST.OUT))
    ap.add_argument('--interest-dir', default=str(ST.DB / 'interest'))
    ap.add_argument('--nodes', default=str(ST.DB / 'study3' / 'nodes.parquet'))
    a = ap.parse_args()
    S = ST.settings()
    workers, threads = ST.thread_plan(a.workers)
    idir = pathlib.Path(a.interest_dir)
    wiki = pd.read_parquet(idir / 'wiki' / 'weekly_node.parquet')
    shifts = pd.read_parquet(idir / 'shifts.parquet')
    sw = pd.read_parquet(idir / 'shift_weekly.parquet')
    nodes = pd.read_parquet(a.nodes)
    T = FL.flow_table(wiki, shifts, sw, nodes, S)
    print(f'{time.strftime("%H:%M:%S")} flow table: {len(T):,} rows, {T.node_id.nunique()} categories, '
          f'origins {T.origin.min()} to {T.origin.max()}', flush=True)
    lo = ST.mi_from_ym(S.flow_test_start)
    origins = sorted(int(m) for m in T[T.origin_mi >= lo].origin_mi.unique())
    if a.limit_origins:
        origins = origins[:a.limit_origins]
    res = []
    t0 = time.time()
    ctx = mp.get_context('spawn')
    with ctx.Pool(workers, initializer=_init, initargs=(T, threads, S)) as pool:
        for i, (mi, df, sec) in enumerate(pool.imap_unordered(_run, origins), 1):
            res.append(df)
            print(f'{time.strftime("%H:%M:%S")} origin {ST.ym_of(mi)} done in {sec:.0f}s ({i}/{len(origins)})', flush=True)
    R = pd.concat([r for r in res if len(r)], ignore_index=True)
    out = pathlib.Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    R.to_parquet(out / 'interest_flow_forecasts.parquet', index=False)
    t = FL.flow_metrics(R, S)
    rep = pathlib.Path(a.reports_dir); rep.mkdir(parents=True, exist_ok=True)
    t.to_csv(rep / 'study4_04_interest_flow.csv', index=False)
    L = ['# Study 4, step 04: interest flow (secondary task)', '',
         f'Made {time.strftime("%Y-%m-%d %H:%M")}. Record SHA-256 `{S.sha256}`. Target: log mean weekly Wikipedia share of the '
         f'category in month t+1. Naive: last {S.flow_recent_weeks} weeks\' mean. CatBoost: W features plus log weekly shares at lags '
         f'{", ".join(str(k) for k in S.flow_lags)} (see README for the lag convention). Origins {R.origin.min()} to {R.origin.max()}; '
         f'{len(R):,} category-months, {R.node_id.nunique()} categories (narrow and middle levels).', '',
         f'Skill = 1 - MAE(CatBoost) / MAE(naive); interval from the moving-block bootstrap ({S.boot_block}-month blocks, {S.boot_n:,} '
         f'resamples, seed {S.boot_seed}); DM one-sided, Newey-West lag {S.dm_lag}. Spearman: forecast change against actual change '
         f'(both measured from the naive level) across categories within each month, averaged. AUC: score = forecast minus log of the '
         f'normal level (median of the 26 weeks before the last week), outcome = next month at least {S.flow_ratio} times normal; '
         'base_rate is the share of category-months that reached it.', '', md_table(t, int_cols=('n', 'months')), '']
    (rep / 'study4_04_interest_flow.md').write_text('\n'.join(L))
    print(f'wrote {rep / "study4_04_interest_flow.md"} ({(time.time() - t0) / 60:.1f} min)')


if __name__ == '__main__':
    main()
