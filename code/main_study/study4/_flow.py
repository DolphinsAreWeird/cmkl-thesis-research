# Secondary task (record, interest_flow): forecast the log mean weekly Wikipedia share of a category in month t+1
# from interest history up to the origin t. Pure functions; 04_interest_flow.py runs them.
import numpy as np, pandas as pd
import _models as M
import _features as FE
from _settings import mi_from_ym, ym_of

M_MIN = 30      # NOT IN RECORD: fewest training rows for a CatBoost fit
FLOW_CAT = ('level', 'broad_id', 'tmonth')     # NOT IN RECORD: the main task's categoricals without format (no demand format here)
KEYS = ['node_id', 'level', 'broad_id', 'origin_mi', 'origin', 'tmonth']


def flow_num_cols(S):
    return list(FE.W_NUM) + [f'lag{k}' for k in S.flow_lags]


def flow_table(wiki, shifts, sw, nodes, S, drop_missing_target=True):
    """One row per node (narrow and middle level) and origin month t: the W features, log weekly shares at weekly
    lags, the naive forecast, the node's normal level, and the target (log mean weekly share in month t+1).
    NOT IN RECORD: lag k is the week k weeks before the last included week L (lag 0 would be L itself, which the last-week
    ratio and the 4-week mean already contain); all weeks of month t+1 must be present for the target; the normal
    level is the median of the 26 weeks before L (L excluded), as in the shift definition; no size rule applies (there
    is no demand here)."""
    if S.flow_recent_weeks != S.recent_weeks:
        raise SystemExit('the record uses different "last weeks" for the flow naive and the W features')
    ids = set(nodes[nodes.level.isin(S.levels)].node_id)
    wk = wiki[wiki.node_id.isin(ids)]
    valid = ~wk.partial_week.astype(bool) if 'partial_week' in wk.columns else None
    Mx = FE.weekly_matrix(wk, 'share', valid)
    first, last = Mx.index.min(), Mx.index.max()
    mi0 = FE.mi_of_ts(first) + 1
    mi1 = FE.mi_of_ts(last)
    origins = list(range(mi0, mi1 + 1))
    # W features (volume + shift state) for every origin
    W = FE.interest_frame(wk, shifts, sw, 'wikipedia', origins, S).drop(columns=['split_qok'])
    W = W.rename(columns={c: 'w_' + c for c in FE.INTEREST_SUFFIX})
    Ls = {m: FE.last_week_monday(m) for m in origins}
    idx = pd.DatetimeIndex([Ls[m] for m in origins])
    logM = FE._log_pos(Mx)
    lag_parts = []
    for k in S.flow_lags:
        sub = logM.shift(k).reindex(index=idx)
        sub.index = origins
        lag_parts.append(sub.stack(future_stack=True).rename(f'lag{k}'))
    normal = Mx.shift(1).rolling(S.normal_weeks, min_periods=S.normal_weeks).median().reindex(index=idx)
    normal.index = origins
    lag_parts.append(normal.stack(future_stack=True).rename('normal'))
    X = pd.concat(lag_parts, axis=1)
    X.index.names = ['origin_mi', 'node_id']
    X = X.reset_index()
    W = W.merge(X, on=['node_id', 'origin_mi'], how='left')
    # target: log of the mean weekly share over the weeks of month t+1 (a week belongs to the month holding its Sunday)
    wm = pd.Series({w: FE.week_month(w) for w in Mx.index})
    cnt = wm.value_counts()
    mean_by_month = Mx.groupby(wm.to_numpy()).mean()
    full = Mx.notna().groupby(wm.to_numpy()).sum().ge(cnt.reindex(mean_by_month.index).to_numpy()[:, None])
    mean_by_month = mean_by_month.where(full)
    # NOT IN RECORD: the first and last months of the data are dropped if their weeks are partial (flagged invalid above)
    tgt = _log(mean_by_month).stack(future_stack=True).rename('y').reset_index()
    tgt.columns = ['target_mi', 'node_id', 'y']
    W['target_mi'] = W.origin_mi + 1
    W = W.merge(tgt, on=['target_mi', 'node_id'], how='left')
    info = nodes.drop_duplicates('node_id').set_index('node_id')[['level', 'broad_id']]
    W['level'] = W.node_id.map(info.level)
    W['broad_id'] = W.node_id.map(info.broad_id)
    W['origin'] = [ym_of(m) for m in W.origin_mi]
    W['tmonth'] = ((W.target_mi % 12) + 1).map('{:02d}'.format)
    W['naive'] = W['w_logmean4']
    W = W[W.w_logmean4.notna()]
    if drop_missing_target:
        W = W[W.y.notna()]
    cols = KEYS + ['target_mi', 'y', 'naive', 'normal'] + flow_num_cols(S)
    return W[cols].sort_values(['origin_mi', 'node_id']).reset_index(drop=True)


def _log(x):
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.log(x.where(x > 0))


def flow_origin(T, origin_mi, S, thread_count):
    """Forecasts at one origin: naive and CatBoost (record), trained on origins s with s + 1 <= t."""
    tr = T[(T.origin_mi + 1 <= origin_mi) & T.y.notna()]
    te = T[(T.origin_mi == origin_mi) & T.y.notna()]
    if len(te) == 0 or len(tr) < M_MIN:
        return pd.DataFrame()
    assert (tr.target_mi <= origin_mi).all()
    p = M.fit_predict_catboost_cols(tr, te, flow_num_cols(S), FLOW_CAT, S, thread_count)
    out = te[KEYS + ['y', 'naive', 'normal']].copy()
    out['catboost'] = p
    out['n_train'] = len(tr)
    return out



def flow_metrics(R, S):
    """Rows R: y, naive, catboost, normal, level, origin_mi. MAE skill against naive (with interval and DM), Spearman of
    forecast change against actual change across categories within each month, AUC for next month >= flow_ratio x normal."""
    rows = []
    groups = [(l, d) for l, d in R.groupby('level')] + [('all', R)]
    for lev, d in groups:
        d = d.reset_index(drop=True)
        e0, e1 = (d.naive - d.y).abs(), (d.catboost - d.y).abs()
        r = M.compare_models(d.origin_mi.to_numpy(), e0.to_numpy(), e1.to_numpy(), S)
        pos = (d.y >= np.log(S.flow_ratio * d.normal)) & d.normal.notna()
        ok = d.normal.notna() & (d.normal > 0)
        lognorm = np.log(d.normal.where(d.normal > 0))
        gcols = ['origin_mi'] + (['level'] if lev == 'all' else [])
        sp = M.spearman_within(d, d.catboost - d.naive, d.y - d.naive, gcols)
        r.update(level=lev, spearman=sp,
                 auc_naive=M.auc((d.naive - lognorm)[ok], pos[ok]), auc_catboost=M.auc((d.catboost - lognorm)[ok], pos[ok]),
                 base_rate=float(pos[ok].mean()) if ok.any() else np.nan)
        rows.append(r)
    return pd.DataFrame(rows)[['level', 'n', 'months', 'mae_base', 'mae_new', 'skill', 'ci_lo', 'ci_hi', 'dm_stat', 'dm_p',
                               'spearman', 'auc_naive', 'auc_catboost', 'base_rate']].rename(
        columns={'mae_base': 'mae_naive', 'mae_new': 'mae_catboost'})
