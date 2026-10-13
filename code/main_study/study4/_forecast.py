# One origin's forecasts from every model and feature set, and the worker used by 02_forecast.py.
# The origin is independent of the others (training uses only earlier origins' rows), so origins run in parallel.
import os, time, json, pathlib
import numpy as np, pandas as pd
import _models as M
from _settings import mi_from_ym, ym_of

# NOT IN RECORD: a model is fitted only if the training set has at least this many rows (LibriVox has few early on);
# the naive forecasts are always made.
MIN_TRAIN_ROWS = 30
KEYS = ['group', 'format', 'level', 'node_id', 'origin_mi', 'origin', 'h', 'tmonth']


def feature_sets_for(origin_mi, S):
    """D and D+W at every test origin; D+W+G and D+W+G+T only up to the end of the GDELT period (record)."""
    out = [fs for fs in S.feature_sets if fs in ('D', 'D+W')]
    if origin_mi <= mi_from_ym(S.gdelt_end):
        out += [fs for fs in S.feature_sets if fs not in ('D', 'D+W')]
    return out


def forecast_origin(F, origin_mi, S, thread_count, groups=None, models=('ridge', 'catboost'), log=None):
    """All forecasts made at one origin. F: the feature table (all groups and horizons)."""
    out = []
    for g in (groups or sorted(F.group.unique())):
        Fg = F[F.group == g]
        for h in S.horizons:
            te = M.test_rows(Fg, origin_mi, h)
            if len(te) == 0:
                continue
            tr = M.training_rows(Fg, origin_mi, h)
            assert (tr.origin_mi + h <= origin_mi).all() and (tr.target_mi <= origin_mi).all()
            base = te[KEYS].copy()
            base['y_true'] = te.y.to_numpy()
            base['y_t'] = te.ls_t.to_numpy()
            base['n_train'] = len(tr)
            for name, fc in (('naive', M.naive(te)), ('seasonal_naive', M.seasonal_naive(te))):
                out.append(base.assign(model=name, fset='-', y_hat=fc, alpha=np.nan))
            if len(tr) < MIN_TRAIN_ROWS:
                continue
            for fs in feature_sets_for(origin_mi, S):
                if 'ridge' in models:
                    p, a = M.fit_predict_ridge(tr, te, fs, h, S)
                    out.append(base.assign(model='ridge', fset=fs, y_hat=p, alpha=a))
                if 'catboost' in models:
                    p = M.fit_predict_catboost(tr, te, fs, S, thread_count)
                    out.append(base.assign(model='catboost', fset=fs, y_hat=p, alpha=np.nan))
                if log:
                    log(f'  {ym_of(origin_mi)} {g} h={h} {fs}: train {len(tr)} test {len(te)}')
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


# ---------------- parts on disk (resumable) ----------------
def part_path(parts_dir, origin_mi):
    return pathlib.Path(parts_dir) / f'origin_{ym_of(origin_mi)}.parquet'


def write_part(df, path):
    path = pathlib.Path(path)
    tmp = path.with_suffix('.tmp')
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)


def consolidate(parts_dir, out_file):
    files = sorted(pathlib.Path(parts_dir).glob('origin_*.parquet'))
    if not files:
        return 0
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    tmp = pathlib.Path(str(out_file) + '.tmp')
    df.to_parquet(tmp, index=False)
    os.replace(tmp, out_file)
    return len(df)


# ---------------- worker ----------------
_W = {}


def init_worker(features_path, parts_dir, threads, S):
    _W['F'] = pd.read_parquet(features_path)
    _W['parts'] = parts_dir
    _W['threads'] = threads
    _W['S'] = S


def run_origin(origin_mi):
    t0 = time.time()
    df = forecast_origin(_W['F'], origin_mi, _W['S'], _W['threads'])
    write_part(df, part_path(_W['parts'], origin_mi))
    return origin_mi, len(df), time.time() - t0
