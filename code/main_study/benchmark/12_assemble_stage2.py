# Method benchmark, stage 2: one wide table of level forecasts for every pipeline (stage 1 and stage 2, horizons 1 to 3) on the base rows,
# with the record's combinations recomputed with the record's code, the stage-2 reference and combinations of addendum b, the segment labels
# and the surge label. Reads whatever forecast files exist, so it can be run again as more pipelines finish.
# Output: data/db/benchmark/wide2.parquet
#   ../../../.venv/bin/python 12_assemble_stage2.py
import sys, time, pathlib, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import _stage2_common as C
import _settings as ST

_spec = importlib.util.spec_from_file_location('ev', HERE / '03_evaluate.py'); EV = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(EV)
K = C.K
DB = ST.DB
COMBOS1 = ['avg_ridge_cat_D', 'avg_ridge_cat_DW', 'avg_three_DW', 'avg_naive_ridge_D', 'median_all', 'invmae_all']
NONPIPE = set(K + ['tmonth', 'y_true', 'y_t', 's_sustained', 'split_qok_shift8', 'segment', 'surge', 'origin'])
DS = ['ridge_D', 'lightgbm_D', 'catboost_D', 'ridgechg_D', 'lgbmchg_D', 'catchg_D', 'chronos2']
BS = ['ridge_DW', 'lightgbm_DW', 'catboost_DW', 'ridgechg_DW', 'lgbmchg_DW', 'catchg_DW', 'chronos2_cur']
LEARNED = ['ridge_D', 'ridge_DW', 'catboost_D', 'catboost_DW', 'lightgbm_D', 'lightgbm_DW', 'chronos', 'chronos2', 'chronos2_cur', 'chronos2_curdw', 'chronos2_bk',
           'chronos2_top', 'chronos2_nli'] + [f'{m}_{f}' for m in ('ridgechg', 'lgbmchg', 'catchg') for f in ('D', 'DW', 'DWS', 'DVcur', 'DVtop', 'DVnli', 'DVbk', 'DVcurdw', 'DVdem')]


def main():
    t0 = time.time()
    base = C.base_rows()
    w = base[K + ['tmonth', 'y_true', 'y_t']].copy()
    w1 = pd.read_parquet(DB / 'benchmark' / 'wide.parquet')
    keep1 = [c for c in w1.columns if c not in NONPIPE and c not in COMBOS1]
    w = w.merge(w1[K + keep1], on=K, how='left')
    # 4b change models at horizon 3 (horizons 1 and 2 are already in the stage-1 table)
    b = pd.read_parquet(DB / 'study4b' / 'forecasts.parquet')
    b = b[(b.part == 'A') & (b.model != 'zero') & (b.h == 3)].copy()
    b['group'] = 'seattle'
    b['pipe'] = b.model.map({'ridge': 'ridgechg', 'catboost': 'catchg'}) + b.fset.map({'D': '_D', 'D+W': '_DW', 'D+W+S': '_DWS'})
    b['y_hat'] = b.ls_t + b.pred
    parts = [b[K + ['pipe', 'y_hat']]]
    # every other forecast file of stage 2 (long format: keys, pipe, y_hat)
    seen = []
    for f in sorted(C.OUT.glob('*_forecasts.parquet')):
        d = pd.read_parquet(f)
        if not set(K + ['pipe', 'y_hat']).issubset(d.columns):
            continue
        parts.append(d[K + ['pipe', 'y_hat']]); seen.append((f.name, sorted(d['pipe'].unique())))
    L = pd.concat(parts, ignore_index=True)
    dup = L.duplicated(K + ['pipe'], keep=False)
    if dup.any():
        raise SystemExit(f'{int(dup.sum())} duplicate forecasts for the same row and pipeline, e.g. {L[dup].head(3).to_dict("records")}')
    Wd = L.pivot_table(index=K, columns='pipe', values='y_hat', aggfunc='first').reset_index()
    new = [c for c in Wd.columns if c not in K]
    old = [c for c in new if c in w.columns]
    if old:                                                      # a pipeline present in the stage-1 table and in a new file: new file fills h = 3 only
        w = w.merge(Wd[K + old].rename(columns={c: c + '__n' for c in old}), on=K, how='left')
        for c in old:
            w[c] = w[c].fillna(w[c + '__n']); w = w.drop(columns=c + '__n')
    w = w.merge(Wd[K + [c for c in new if c not in old]], on=K, how='left')
    # baselines from the base rows
    w = w.merge(base[K + ['mean6', 'ls_ly', 'm12_last', 'm12_prev']], on=K, how='left')
    w['naive'] = w.y_t
    sn = w.ls_ly + w.m12_last - w.m12_prev
    if 'seasonal_naive' in w:
        chk = (w.seasonal_naive - sn).abs()
        assert chk.dropna().max() < 1e-9, 'seasonal naive of the stage-1 table differs from the formula'
        w['seasonal_naive'] = w.seasonal_naive.fillna(sn)
    else:
        w['seasonal_naive'] = sn
    w['revert6'] = w.mean6
    w = w.drop(columns=['mean6', 'ls_ly', 'm12_last', 'm12_prev'])
    # the record's combinations with the record's code (all horizons), then the stage-2 combinations of addendum b
    w = EV.add_combinations(w)
    ds = [c for c in DS if c in w]; bs = [c for c in BS if c in w]
    w['median_s2_demand'] = w[ds].median(axis=1, skipna=False) if len(ds) == len(DS) else np.nan
    w['median_s2_behavior'] = w[bs].median(axis=1, skipna=False) if len(bs) == len(BS) else np.nan
    w['median_s2_all'] = w[[c for c in LEARNED if c in w]].median(axis=1, skipna=True)
    w = EV.add_segments(w)
    w.to_parquet(DB / 'benchmark' / 'wide2.parquet', index=False)
    pipes = [c for c in w.columns if c not in NONPIPE]
    print(f'{time.strftime("%H:%M:%S")} wrote wide2.parquet: {len(w):,} rows, {len(pipes)} pipelines; {(time.time() - t0):.0f}s', flush=True)
    for h in (1, 2, 3):
        x = w[(w.h == h) & (w.group == 'seattle')]
        print(f'  h={h} Seattle rows {len(x):,}; pipelines with forecasts on at least 99% of rows: {sum(x[p].notna().mean() >= 0.99 for p in pipes)} of {len(pipes)}', flush=True)
    for name, ps in seen:
        print('  from', name, ps, flush=True)


if __name__ == '__main__':
    main()
