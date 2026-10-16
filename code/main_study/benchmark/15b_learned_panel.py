# Method benchmark, stage 2f (f1), step 2: the demand panel of the learned categories with the Study 3 definition and size rule.
# Demand = sum over works of checkouts x strength / all checkouts of the format and month (strength 1 for the work's cluster, 0 elsewhere; the denominator holds every
# checkout, including works that are in no cluster), log share, Study 3 minimum-size rule, Study 3 month status (missing and closure months). Uses the Study 3 modules
# with the Study 3 settings (its own hash check); node ids L86_000.. (level middle) and L242_000.. (level narrow); broad_id is the constant 'none' (no broad category).
# HARD RULE as in Study 3: this script prints structure only (counts), never a category's demand.
#   ../../../.venv/bin/python 15b_learned_panel.py        (run under jobs/heavy_lock.sh)
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '3')
import sys, time, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study3'))
import numpy as np, pandas as pd
from _settings import SETTINGS as S3          # Study 3 settings (hash checked against prereg/README.md)
import _files as IO
import _build as B
import _inputs as I

OUT = pathlib.Path(IO.D) / 'db' / 'benchmark' / 'stage2' / 'learned'
KS = ((86, 'middle'), (242, 'narrow'))


def main():
    t0 = time.time()
    P = IO.Paths()
    rw = I.load_record_work(P)
    api = I.api_counts(P)
    WT, N = {}, {}
    for k, level in KS:
        A = pd.read_parquet(OUT / f'clusters_k{k}.parquet')
        node = 'L%d_' % k + A.cluster.astype(str).str.zfill(3)
        WT[level] = pd.DataFrame({'work_id': A.work_id.astype(np.int64), 'node_id': node, 'strength': 1.0})
        ids = sorted(node.unique())
        N[level] = pd.DataFrame({'node_id': ids, 'parent': np.nan, 'broad_id': 'none', 'label': ids})
    panels = []
    for fmt in S3.seattle_formats:
        wm, totals, st, raw = I.format_month_data(P, S3, fmt, rw, api)
        for k, level in KS:
            panels.append(B.assemble(wm, WT[level], st, N[level], fmt, level, S3))
        print(f'{time.strftime("%H:%M:%S")} {fmt}: {raw["raw_rows"]:,} rows, {len(st)} months ({int(st.month_ok.sum())} usable); {(time.time() - t0) / 60:.1f} min', flush=True)
        del wm
    panel = pd.concat(panels, ignore_index=True)
    IO.save_parquet(panel, OUT / 'demand_panel.parquet')
    lines = ['# Learned categories: demand panel (structure only)', '', f'Written {time.strftime("%Y-%m-%d %H:%M")}. Study 3 definition and size rule; no category demand is shown.', '']
    for (fmt, level), g in panel.groupby(['format', 'level']):
        ref = g[g.ym == '2020-03']
        lines.append(f'- {fmt}, {level}: {g.node_id.nunique()} clusters; passing the size rule at 2020-03: {int(ref.size_ok.sum()) if len(ref) else "no data"}')
    pathlib.Path(IO.D, 'reports', 'benchmark_stage2_learned_panel.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines), flush=True)
    print(f'{time.strftime("%H:%M:%S")} wrote demand_panel.parquet ({len(panel):,} rows); {(time.time() - t0) / 60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
