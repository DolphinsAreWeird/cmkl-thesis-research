# Final unseen test: the extended world for the months released after August 2026. Reads the downloaded months (28_final_test_download.py), extends the frozen taxonomy
# tables with them (_final_extend.py), appends the API's own counts, and makes the demand panel with Study 3's builder (26_final_test_panel.py). The months up to
# 2026-08 of the extended panel must equal the stored panel, or nothing else runs. Refuses to run unless addendum d is fingerprinted (guard of 28_final_test_download.py).
#   ../../../.venv/bin/python 29_final_test_world.py        (under the heavy-job lock)
import os
os.environ.setdefault('TAXO', 'v3')
import sys, json, time, pathlib, subprocess, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import _final_extend as X

DL = importlib.util.module_from_spec(importlib.util.spec_from_file_location('dl', HERE / '28_final_test_download.py'))
DL.__spec__.loader.exec_module(DL)
OUT = DL.OUT
WORLD = OUT / 'world'
STORED_PANEL = X.DB / 'study3' / 'demand_panel.parquet'


def say(m):
    print(f'{time.strftime("%H:%M:%S")} {m}', flush=True)


def read_new_months():
    f = OUT / 'new_months_api_counts.parquet'
    if not f.exists():
        raise SystemExit('no downloaded months (new_months_api_counts.parquet is missing)')
    c = pd.read_parquet(f)
    ok = c.groupby(['year', 'month']).complete.all()
    months = [(int(y), int(m)) for (y, m), v in ok.items() if v]
    if not months:
        raise SystemExit('no complete month downloaded')
    raw = {}
    for fmt in X.FILE_OF:
        parts = []
        for y, m in months:
            p = DL.RAW / f'seattle_{fmt.lower()}_{y}-{m:02d}.jsonl'
            parts.append(pd.read_json(p, lines=True, dtype=False) if p.stat().st_size else pd.DataFrame())
        raw[fmt] = pd.concat(parts, ignore_index=True)
        for col in X.RAW_COLS:
            if col not in raw[fmt].columns:
                raw[fmt][col] = ''
        raw[fmt] = raw[fmt].fillna('')
    return months, raw, c


def main():
    name, sha = DL.guard()
    say(f'addendum d {name}')
    months, raw, counts = read_new_months()
    say(f'new months {months}; rows {({f: len(r) for f, r in raw.items()})}')
    WORLD.mkdir(parents=True, exist_ok=True)
    rep = X.extend(raw, WORLD, before_mi=None, hash_cache=OUT / 'record_keys.npz', log=say)
    old = pd.read_parquet(X.V2 / 'spl_api_counts.parquet')
    new = counts[['materialtype', 'year', 'month', 'n_rows', 'checkouts', 'api_queried']]
    pd.concat([old[~old.set_index(['materialtype', 'year', 'month']).index.isin(new.set_index(['materialtype', 'year', 'month']).index)], new], ignore_index=True) \
        .to_parquet(WORLD / 'taxonomy' / 'spl_api_counts.parquet', index=False)
    (WORLD / 'extend_report.json').write_text(json.dumps(rep, indent=1, default=str))
    say(f'extension done: {json.dumps(rep, default=str)}')
    r = subprocess.call([sys.executable, '-u', str(HERE / '26_final_test_panel.py'), '--world', str(WORLD)])
    if r:
        raise SystemExit(f'panel build failed ({r})')
    # months up to 2026-08 must equal the stored panel
    a = pd.read_parquet(STORED_PANEL)
    b = pd.read_parquet(WORLD / 'db' / 'demand_panel.parquet')
    key = ['format', 'level', 'node_id', 'mi']
    m = a[a.mi <= 2026 * 12 + 7][key + ['log_share', 'month_ok', 'size_ok']].merge(b[b.mi <= 2026 * 12 + 7][key + ['log_share', 'month_ok', 'size_ok']], on=key, how='outer',
                                                                                     suffixes=('_s', '_w'), indicator=True)
    d = (m.log_share_s - m.log_share_w).abs()
    same = bool((m._merge == 'both').all() and (np.nanmax(d) < 1e-9 if d.notna().any() else True) and (m.size_ok_s == m.size_ok_w).all() and (m.month_ok_s == m.month_ok_w).all())
    say(f'months up to 2026-08 equal the stored panel: {same} (rows {len(m):,}, max abs difference {np.nanmax(d):.2e})')
    if not same:
        raise SystemExit('the extended panel changes the stored months; stop')
    say('done')


if __name__ == '__main__':
    main()
