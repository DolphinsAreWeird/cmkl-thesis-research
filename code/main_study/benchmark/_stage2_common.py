# Shared helpers for the stage-2 benchmark scripts (settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json).
# Reads the Study 4 settings through study4/_settings.py (hash-checked), so nothing here runs on an edited record.
# The base rows are the stage-1 rows (Study 4 forecasts at horizons 1 and 2, Seattle and LibriVox) plus horizon 3 for Seattle
# from the Study 4b feature table; the series histories are the log shares at every origin where a row exists.
import sys, json, hashlib, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import numpy as np, pandas as pd
import _settings as ST

ADDENDUM = ST.PREREG / 'addenda_benchmark' / '2026-10-15_b_stage2_metrics_tasks_pipelines.json'
ADDENDUM_SHA = '9315927d3df0336a534ea0bd248ed68d1fc9a2c5cd30f0ca5c5d6c71d8169a22'
OUT = ST.DB / 'benchmark' / 'stage2'
SER = ['group', 'format', 'level', 'node_id']
K = SER + ['origin_mi', 'h']
SEED = 20261013


def check_addendum():
    got = hashlib.sha256(ADDENDUM.read_bytes()).hexdigest()
    if got != ADDENDUM_SHA:
        raise SystemExit(f'stage-2 addendum changed: {got} is not {ADDENDUM_SHA}; nothing runs')
    return json.loads(ADDENDUM.read_text())


def base_rows(cache=True):
    """One row per (series, origin, horizon) to forecast: keys, origin, tmonth, y_true, y_t and the baseline ingredients.
    h = 1, 2: Study 4 naive rows (Seattle and LibriVox). h = 3: Seattle rows of the 4b feature table with a known target, test origins only."""
    p = OUT / 'base_rows.parquet'
    if cache and p.exists():
        return pd.read_parquet(p)
    OUT.mkdir(parents=True, exist_ok=True)
    fc = pd.read_parquet(ST.DB / 'study4' / 'forecasts.parquet', columns=K + ['origin', 'tmonth', 'y_true', 'y_t', 'model'])
    fc = fc[fc.model == 'naive'].drop(columns='model')
    f4 = pd.read_parquet(ST.DB / 'study4' / 'features.parquet', columns=K + ['mean6', 'ls_ly', 'm12_last', 'm12_prev'])
    b12 = fc.merge(f4, on=K, how='left', validate='one_to_one')
    lo = ST.mi_from_ym(ST.settings().test_start)
    f4b = pd.read_parquet(ST.DB / 'study4b' / 'features.parquet',
                          columns=K + ['origin', 'tmonth', 'y', 'ls_t', 'mean6', 'ls_ly', 'm12_last', 'm12_prev'])
    b3 = f4b[(f4b.h == 3) & (f4b.origin_mi >= lo) & f4b.y.notna() & f4b.ls_t.notna()].rename(columns={'y': 'y_true', 'ls_t': 'y_t'})
    b3 = b3[list(b12.columns)]
    B = pd.concat([b12, b3], ignore_index=True).sort_values(K).reset_index(drop=True)
    B.to_parquet(p, index=False)
    return B


def history():
    """{(group, format, level, node_id): pandas Series of the log share indexed by month index, every origin where a row exists
    (Study 4 horizons 1 and 2, Study 4b horizon 3), duplicates must agree}."""
    f4 = pd.read_parquet(ST.DB / 'study4' / 'features.parquet', columns=SER + ['origin_mi', 'ls_t'])
    f4b = pd.read_parquet(ST.DB / 'study4b' / 'features.parquet', columns=SER + ['origin_mi', 'ls_t'])
    H = pd.concat([f4, f4b], ignore_index=True).dropna(subset=['ls_t'])
    chk = H.groupby(SER + ['origin_mi']).ls_t.agg(['min', 'max'])
    assert (chk['max'] - chk['min']).abs().max() < 1e-9, 'ls_t differs between tables for the same series and origin'
    H = H.drop_duplicates(SER + ['origin_mi']).set_index(SER + ['origin_mi']).ls_t.sort_index()
    return {k: g.droplevel(list(range(len(SER)))) for k, g in H.groupby(level=list(range(len(SER))))}


def months_range(lo, hi):
    return list(range(int(lo), int(hi) + 1))
