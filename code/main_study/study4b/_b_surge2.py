# Study 4b secondary surge definitions (addendum prereg/addenda_4b/2026-10-14_a_secondary_surges.json). Part B at horizon 2 again,
# with a different surge label, same models, feature sets, retraining at every origin and metrics as the primary surge.
#   base98: surge = 2-month change in log share at or above the 98th percentile of that change within the same format and level;
#           the percentile is computed on the TRAINING rows of the origin only (origins s with s + h <= t), then applied to the
#           training labels and to the test rows of that origin (no information from the test month or later enters it).
#   pct20 : surge = change >= log(1.2).
import numpy as np, pandas as pd
import _s4
import _b_models as BM
import _b_run as BR

M4 = _s4.models
DEFS = ('base98', 'pct20')
# From the addendum wording; the record's own surge (log 1.3) stays the primary one.
BASE_PCTL = 0.98          # 98th percentile
PCT20_CHANGE = float(np.log(1.2))
MIN_GROUP_ROWS = 1        # NOT IN RECORD: a (format, level) group absent from the training rows falls back to the cut-off of all training rows


def surge_cutoffs(train, defn):
    """Cut-offs (a DataFrame with format, level, thr) computed from the training rows only. For pct20 the same constant everywhere."""
    if defn == 'pct20':
        g = train[['format', 'level']].drop_duplicates()
        return g.assign(thr=PCT20_CHANGE), PCT20_CHANGE
    if defn == 'base98':
        ch = train.dropna(subset=['change'])
        g = ch.groupby(['format', 'level']).change.quantile(BASE_PCTL).rename('thr').reset_index()
        return g, float(ch.change.quantile(BASE_PCTL))
    raise ValueError(defn)


def apply_cutoffs(df, cut, fallback):
    """Row-wise cut-off by format and level (training-based); returns thr, and the 0/1 label (NaN where the change is NaN)."""
    thr = df[['format', 'level']].merge(cut, on=['format', 'level'], how='left').thr.fillna(fallback).to_numpy(float)
    lab = np.where(df.change.notna().to_numpy(), (df.change.to_numpy(float) >= thr).astype(float), np.nan)
    return thr, lab


def forecast_origin_surge(F, origin_mi, B, defn, thread_count, models=('ridge', 'catboost')):
    """Long table like Part B of 4b (part 'B'), plus `thr` (the training-based cut-off applied to each test row) and `surge_def`."""
    h = B.h_surge
    te = M4.test_rows(F, origin_mi, h)
    if len(te) == 0:
        return pd.DataFrame()
    tr = M4.training_rows(F, origin_mi, h)
    assert (tr.origin_mi + h <= origin_mi).all() and (tr.target_mi <= origin_mi).all()
    if len(tr) < BM.MIN_TRAIN_ROWS:
        return pd.DataFrame()
    cut, fb = surge_cutoffs(tr, defn)
    tr = tr.copy(); te = te.copy()
    tr['thr'], tr['surge'] = apply_cutoffs(tr, cut, fb)
    te['thr'], te['surge'] = apply_cutoffs(te, cut, fb)
    base = te[BR.KEYS].copy()
    base['ls_t'] = te.ls_t.to_numpy()
    base['target'] = te.change.to_numpy()
    base['thr'] = te.thr.to_numpy()
    base['n_train'] = len(tr)
    base['train_base_rate'] = float(tr.surge.mean())
    out = []
    for fs in B.feature_sets:
        if 'catboost' in models:
            out.append(base.assign(part='B', model='catboost_clf', fset=fs, pred=BM.fit_predict_catboost_surge(tr, te, fs, B, thread_count), alpha=np.nan))
        if 'ridge' in models:
            out.append(base.assign(part='B', model='logistic', fset=fs, pred=BM.fit_predict_logistic_surge(tr, te, fs, B), alpha=np.nan))
    return pd.concat(out, ignore_index=True).assign(surge_def=defn)
