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


def read_new_months(test=False):
    f = OUT / ('test' if test else '') / 'new_months_api_counts.parquet'
    rawdir = DL.RAW_TEST if test else DL.RAW
    if not f.exists():
        raise SystemExit(f'no downloaded months ({f} is missing)')
    c = pd.read_parquet(f)
    ok = c.groupby(['year', 'month']).complete.all()
    months = [(int(y), int(m)) for (y, m), v in ok.items() if v]
    if not months:
        raise SystemExit('no complete month downloaded')
    raw = {}
    for fmt in X.FILE_OF:
        recs = []
        for y, m in months:
            p = rawdir / f'seattle_{fmt.lower()}_{y}-{m:02d}.jsonl'
            with open(p) as fh:
                recs += [json.loads(line) for line in fh]
        df = pd.DataFrame(recs, dtype=object) if recs else pd.DataFrame(columns=X.RAW_COLS)
        for col in X.RAW_COLS:
            if col not in df.columns:
                df[col] = ''
        raw[fmt] = df.fillna('')
    return months, raw, c


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--known-test', default=None, help='YYYY-MM: test on months already known (downloaded with 28 --test-months): treat everything from this month on as new')
    a = ap.parse_args()
    test = a.known_test is not None
    if test:
        y, m = int(a.known_test[:4]), int(a.known_test[5:7])
        before = y * 12 + m - 1
        world = OUT / f'world_known_test_{a.known_test}'
    else:
        name, sha = DL.guard()
        say(f'addendum d {name}')
        before, world = None, WORLD
    months, raw, counts = read_new_months(test)
    say(f'new months {months}; rows {({f: len(r) for f, r in raw.items()})}')
    world.mkdir(parents=True, exist_ok=True)
    rep = X.extend(raw, world, before_mi=before, hash_cache=OUT / 'record_keys.npz', log=say)
    old = pd.read_parquet(X.V2 / 'spl_api_counts.parquet')
    new = counts[['materialtype', 'year', 'month', 'n_rows', 'checkouts', 'api_queried']]
    pd.concat([old[~old.set_index(['materialtype', 'year', 'month']).index.isin(new.set_index(['materialtype', 'year', 'month']).index)], new], ignore_index=True) \
        .to_parquet(world / 'taxonomy' / 'spl_api_counts.parquet', index=False)
    (world / 'extend_report.json').write_text(json.dumps(rep, indent=1, default=str))
    say(f'extension done: {json.dumps(rep, default=str)}')
    r = subprocess.call([sys.executable, '-u', str(HERE / '26_final_test_panel.py'), '--world', str(world)])
    if r:
        raise SystemExit(f'panel build failed ({r})')
    a_ = pd.read_parquet(STORED_PANEL)
    b_ = pd.read_parquet(world / 'db' / 'demand_panel.parquet')
    key = ['format', 'level', 'node_id', 'mi']
    last_known = 2026 * 12 + 7
    lim = (before - 1) if test else last_known                 # months that must equal the stored panel
    m_ = a_[a_.mi <= lim][key + ['log_share', 'month_ok', 'size_ok']].merge(b_[b_.mi <= lim][key + ['log_share', 'month_ok', 'size_ok']], on=key, how='outer', suffixes=('_s', '_w'), indicator=True)
    d = (m_.log_share_s - m_.log_share_w).abs()
    same = bool((m_._merge == 'both').all() and (np.nanmax(d) < 1e-9 if d.notna().any() else True) and (m_.size_ok_s == m_.size_ok_w).all() and (m_.month_ok_s == m_.month_ok_w).all())
    say(f'months up to {X.pd.Timestamp(year=lim // 12, month=lim % 12 + 1, day=1):%Y-%m} equal the stored panel: {same} (rows {len(m_):,}, max abs difference {np.nanmax(d):.2e})')
    if not same:
        raise SystemExit('the extended panel changes the stored months; stop')
    if test:
        post = a_[a_.mi >= before][key + ['log_share']].merge(b_[b_.mi >= before][key + ['log_share']], on=key, how='outer', suffixes=('_s', '_w'), indicator=True)
        both = post[(post._merge == 'both') & post.log_share_s.notna() & post.log_share_w.notna()]
        dd = (both.log_share_w - both.log_share_s).abs()
        say(f'known-month test, months from {a.known_test} on: rows {len(post):,}, only in one {int((post._merge != "both").sum())}, abs difference median {dd.median():.4f}, 90th pct {dd.quantile(.9):.4f}, '
            f'99th pct {dd.quantile(.99):.4f}, max {dd.max():.4f}')
    say('done')


if __name__ == '__main__':
    main()
