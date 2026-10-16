# One origin's Study 4b forecasts (Part A change forecasts at h = 1, 2, 3 and Part B surge probabilities at h = 2) and the
# worker used by 02_run.py. Origins are independent (training uses only rows with s + h <= t), so they run in parallel.
import time
import numpy as np, pandas as pd
import _s4
import _b_models as BM

M4, FC4 = _s4.models, _s4.forecast
KEYS = ['format', 'level', 'node_id', 'origin_mi', 'origin', 'h', 'tmonth']
write_part, consolidate, part_path = FC4.write_part, FC4.consolidate, FC4.part_path
ym_of = _s4.settings.ym_of


def forecast_origin(F, origin_mi, B, thread_count, parts=('A', 'B'), models=('ridge', 'catboost'), log=None):
    """All forecasts at one origin. F: the 4b feature table. Long format: part ('A' change forecast, 'B' surge probability),
    model, fset, keys, h, ls_t, target (the realised change), pred (the forecast change, or P(surge))."""
    out = []
    for h in B.horizons:
        te = M4.test_rows(F, origin_mi, h)
        if len(te) == 0:
            continue
        tr = M4.training_rows(F, origin_mi, h)
        assert (tr.origin_mi + h <= origin_mi).all() and (tr.target_mi <= origin_mi).all()
        base = te[KEYS].copy()
        base['ls_t'] = te.ls_t.to_numpy()
        base['target'] = te.change.to_numpy()
        base['n_train'] = len(tr)
        if 'A' in parts:
            out.append(base.assign(part='A', model='zero', fset='-', pred=BM.zero_change(te), alpha=np.nan))
        enough = len(tr) >= BM.MIN_TRAIN_ROWS
        for fs in B.feature_sets:
            if 'A' in parts and enough:
                if 'ridge' in models:
                    p, a = BM.fit_predict_ridge_change(tr, te, fs, h, B)
                    out.append(base.assign(part='A', model='ridge', fset=fs, pred=p, alpha=a))
                if 'catboost' in models:
                    p = BM.fit_predict_catboost_change(tr, te, fs, B, thread_count)
                    out.append(base.assign(part='A', model='catboost', fset=fs, pred=p, alpha=np.nan))
            if 'B' in parts and h == B.h_surge and enough:
                if 'catboost' in models:
                    out.append(base.assign(part='B', model='catboost_clf', fset=fs, pred=BM.fit_predict_catboost_surge(tr, te, fs, B, thread_count), alpha=np.nan))
                if 'ridge' in models:
                    out.append(base.assign(part='B', model='logistic', fset=fs, pred=BM.fit_predict_logistic_surge(tr, te, fs, B), alpha=np.nan))
            if log:
                log(f'  {ym_of(origin_mi)} h={h} {fs}: train {len(tr)} test {len(te)}')
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


_W = {}


def init_worker(features_path, parts_dir, threads):
    """The settings are loaded again in each worker (both hashes checked again); the Settings objects are never pickled."""
    import _settings as ST
    _W['F'] = pd.read_parquet(features_path)
    _W['parts'], _W['threads'], _W['B'] = parts_dir, threads, ST.settings()


def run_origin(origin_mi):
    t0 = time.time()
    df = forecast_origin(_W['F'], origin_mi, _W['B'], _W['threads'])
    write_part(df, part_path(_W['parts'], origin_mi))
    return origin_mi, len(df), time.time() - t0
