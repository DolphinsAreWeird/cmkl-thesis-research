# Final test machinery: build the Study 3 demand panel (Seattle formats) from the tables of a 'world' folder (made by _final_extend.extend or, for the unchanged
# stored tables, by --self-check). It runs Study 3's own build_seattle (01_demand_panel.py) on the world's taxonomy folder, so the panel of an extended world is
# made by the same code, the same Study 3 record and the same month rules (missing months, closure months, API row counts) as the stored panel.
# Own process: Study 3's modules share names with Study 4's (_settings, _files), so this script imports only Study 3's.
#   ../../../.venv/bin/python 26_final_test_panel.py --world data/db/final_test/dryrun_2026-06
import os
os.environ.setdefault('TAXO', 'v3')
import sys, json, time, pathlib, argparse, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
STUDY3 = HERE.parent / 'study3'
sys.path.insert(0, str(STUDY3))
import numpy as np, pandas as pd
from _settings import SETTINGS as S
import _files as IO
import _build as B
import _inputs as I


def load_builder():
    spec = importlib.util.spec_from_file_location('s3_panel', STUDY3 / '01_demand_panel.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--world', required=True)
    ap.add_argument('--out', default=None, help='file for the panel (default: <world>/db/demand_panel.parquet)')
    a = ap.parse_args()
    world = pathlib.Path(a.world).resolve()
    P = IO.Paths(sim=str(world))                     # world/db, world/reports, world/taxonomy: the layout of Study 3's simulated worlds
    tx = world / 'taxonomy'
    for need in ('spl_record_work.parquet', 'spl_works.parquet', 'work_theme.parquet', 'theme_nodes.parquet', 'spl_api_counts.parquet'):
        if not (tx / need).exists():
            raise SystemExit(f'{tx / need} is missing')
    mod = load_builder()
    src = I.choose_source(P)
    if src['development']:
        raise SystemExit('development taxonomy: work_theme.parquet is missing')
    t0 = time.time()
    panel, overlap, nodes, checks, months, how, info = mod.build_seattle(P, src)
    out = pathlib.Path(a.out) if a.out else P.db / 'demand_panel.parquet'
    out.parent.mkdir(parents=True, exist_ok=True)
    IO.save_parquet(panel, out)
    IO.save_parquet(nodes, P.db / 'nodes.parquet')
    meta = dict(settings_sha256=S.sha256, formats=list(S.seattle_formats), theme_strength=how, created=time.strftime('%Y-%m-%d %H:%M:%S'),
                months={f: [B.ym_of(st.index.min()), B.ym_of(st.index.max())] for f, st in months.items()},
                month_status={f: {B.ym_of(m): (r if r else 'ok') for m, r in st.reason.items() if m >= st.index.max() - 12} for f, st in months.items()},
                checks={f: {k: (v if isinstance(v, (bool, int, float, str)) else str(v)) for k, v in c.items()} for f, c in checks.items()})
    (P.db / 'demand_panel_meta.json').write_text(json.dumps(meta, indent=1, default=str))
    print(f'{time.strftime("%H:%M:%S")} panel {len(panel):,} rows, months {meta["months"]}; {time.time() - t0:.0f}s -> {out}', flush=True)


if __name__ == '__main__':
    main()
