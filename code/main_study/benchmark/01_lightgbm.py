# Method benchmark, stage 1: LightGBM D and D+W on the Study 4 feature table, same walk-forward training and test rows
# as Study 4 (study4/_models.training_rows / test_rows), horizons 1 and 2, Seattle and LibriVox groups.
# Settings: prereg/benchmark_settings_2026-10-15.json (pipelines_new.lightgbm_D, lightgbm_DW). One part per origin (resumable).
#   ../../../.venv/bin/python 01_lightgbm.py      (run under jobs/heavy_lock.sh)
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '3')
import sys, time, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import numpy as np, pandas as pd
import _settings as ST
import _models as M
from _features import feature_columns

OUT = ST.DB / 'benchmark'
PARTS = OUT / 'lightgbm_parts'
KEYS = ['group', 'format', 'level', 'node_id', 'origin_mi', 'origin', 'h', 'tmonth']
PARAMS = dict(objective='regression', n_estimators=600, learning_rate=0.05, max_depth=6, num_leaves=63,
              min_child_samples=20, subsample=1.0, colsample_bytree=1.0, random_state=20261013,
              deterministic=True, force_row_wise=True, n_jobs=3, verbose=-1)


def fit_predict(tr, te, fset):
    import lightgbm as lgb
    num, cat = feature_columns(fset)
    cols = list(num) + list(cat)

    def prep(d, cats=None):
        X = d[cols].copy()
        for c in cat:
            X[c] = pd.Categorical(X[c].astype(str), categories=cats[c] if cats else sorted(X[c].astype(str).unique()))
        return X
    Xtr = prep(tr)
    cats = {c: list(Xtr[c].cat.categories) for c in cat}
    m = lgb.LGBMRegressor(**PARAMS).fit(Xtr, tr['y'].to_numpy(float), categorical_feature=list(cat))
    return m.predict(prep(te, cats))


def main():
    S = ST.settings()
    PARTS.mkdir(parents=True, exist_ok=True)
    F = pd.read_parquet(ST.OUT / 'features.parquet')
    lo = ST.mi_from_ym(S.test_start)
    origins = sorted(int(m) for m in F[(F.origin_mi >= lo) & F.y.notna()].origin_mi.unique())
    t0 = time.time()
    for i, t in enumerate(origins, 1):
        p = PARTS / f'origin_{ST.ym_of(t)}.parquet'
        if p.exists():
            continue
        out = []
        for g in sorted(F.group.unique()):
            Fg = F[F.group == g]
            for h in S.horizons:
                te = M.test_rows(Fg, t, h)
                tr = M.training_rows(Fg, t, h)
                if len(te) == 0 or len(tr) < 30:
                    continue
                assert (tr.origin_mi + h <= t).all()
                base = te[KEYS].copy()
                base['y_true'] = te.y.to_numpy()
                base['y_t'] = te.ls_t.to_numpy()
                for fs in ('D', 'D+W'):
                    out.append(base.assign(model='lightgbm', fset=fs, y_hat=fit_predict(tr, te, fs)))
        df = pd.concat(out, ignore_index=True)
        df.to_parquet(p.with_suffix('.tmp'), index=False); os.replace(p.with_suffix('.tmp'), p)
        el = time.time() - t0
        print(f'{time.strftime("%H:%M:%S")} {ST.ym_of(t)}: {len(df)} forecasts ({i}/{len(origins)}, {el/60:.1f} min)', flush=True)
    allp = pd.concat([pd.read_parquet(f) for f in sorted(PARTS.glob('origin_*.parquet'))], ignore_index=True)
    allp.to_parquet(OUT / 'lightgbm_forecasts.parquet', index=False)
    print(f'wrote {OUT / "lightgbm_forecasts.parquet"} ({len(allp)} rows); {(time.time()-t0)/60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
