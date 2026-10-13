# Pure functions that turn the Study 3 demand panel and the interest series into the origin x category x format table.
# Months are integers mi = year * 12 + (month - 1). An origin is a month t; the table has one row per origin, category,
# format and horizon h (1 or 2). Every feature at origin t uses only data up to t (demand months <= t, interest weeks
# whose Sunday is on or before the last day of t, shifts whose start week and labelling week are <= that last week).
import numpy as np, pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

LABELS = ('sustained', 'intermediate', 'fading')       # record: the real-time shift labels
CAT_COLS = ['format', 'level', 'broad_id', 'tmonth']
D_NUM = ['ls_t', 'ls_t1', 'ls_t2', 'ls_ly', 'mean6', 'dlog_total']
INTEREST_SUFFIX = ['logmean4', 'ratio', 'dlog4', 'mk8', 'shift8', 'lab_sustained', 'lab_intermediate', 'lab_fading',
                   'shift_size', 'shift_weeks']
W_NUM = ['w_' + s for s in INTEREST_SUFFIX]
G_NUM = ['g_' + s for s in INTEREST_SUFFIX]
T_NUM = ['t_tone', 't_pos', 't_neg']
FSET_PARTS = {'D': ['D'], 'D+W': ['D', 'W'], 'D+W+G': ['D', 'W', 'G'], 'D+W+G+T': ['D', 'W', 'G', 'T']}
PART_NUM = {'D': D_NUM, 'W': W_NUM, 'G': G_NUM, 'T': T_NUM}
# columns that are never features (targets, baselines' ingredients, scoring splits, keys)
NON_FEATURES = ['y', 'm12_last', 'm12_prev', 'split_qok_shift8', 'group', 'node_id', 'origin_mi', 'origin', 'h', 'target_mi',
                'last_week', 'target_ok']


def feature_columns(fset):
    """(numeric columns, categorical columns) of a feature set."""
    num = [c for p in FSET_PARTS[fset] for c in PART_NUM[p]]
    return num, list(CAT_COLS)


# ---------------- months and weeks ----------------
def mi_of_ts(ts):
    ts = pd.Timestamp(ts)
    return ts.year * 12 + ts.month - 1


def last_week_monday(mi):
    """Monday of the last ISO week whose Sunday falls on or before the last day of month mi (record)."""
    y, m = divmod(int(mi), 12)
    end = pd.Timestamp(year=y, month=m + 1, day=1) + pd.offsets.MonthEnd(0)
    sunday = end - pd.Timedelta(days=(end.weekday() + 1) % 7)
    return sunday - pd.Timedelta(days=6)


def week_month(monday):
    """Month index a week belongs to: the month that holds its Sunday."""
    return mi_of_ts(pd.Timestamp(monday) + pd.Timedelta(days=6))


# ---------------- weekly interest ----------------
def weekly_matrix(df, value, valid=None):
    """weeks x nodes matrix (index = Monday, complete weekly grid); invalid or missing values are NaN."""
    d = df[['node_id', 'week', value]].copy()
    d['week'] = pd.to_datetime(d['week']).dt.normalize()
    if valid is not None:
        d.loc[~valid.to_numpy(), value] = np.nan
    M = d.pivot(index='week', columns='node_id', values=value)
    grid = pd.date_range(M.index.min(), M.index.max(), freq='7D')
    return M.reindex(grid)


def kendall_tau_rolling(A, k):
    """A: weeks x nodes. Mann-Kendall tau of the last k values ending at each week (S / (k(k-1)/2), no tie correction);
    NaN unless all k values are present."""
    n = A.shape[0]
    out = np.full(A.shape, np.nan)
    if n < k:
        return out
    W = sliding_window_view(A, k, axis=0)             # (n-k+1, nodes, k)
    S = np.zeros(W.shape[:2])
    for i in range(k):
        for j in range(i + 1, k):
            S = S + np.sign(W[..., j] - W[..., i])
    out[k - 1:] = S / (k * (k - 1) / 2)
    return out


def _log_pos(x):
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.log(x.where(x > 0))


def weekly_feature_matrices(M, S):
    """The four volume features at every week (as of that week), from a weeks x nodes share matrix.
    NOT IN RECORD: every window must be complete (all 4, 8 or 26 weeks present and valid); otherwise the feature is missing."""
    r, nw = S.recent_weeks, S.normal_weeks
    m4 = M.rolling(r, min_periods=r).mean()
    lm4 = _log_pos(m4)
    dl = lm4 - lm4.shift(r)
    normal = M.shift(1).rolling(nw, min_periods=nw).median()
    ratio = (M / normal.where(normal > 0))
    tau = pd.DataFrame(kendall_tau_rolling(M.to_numpy(float), S.mk_weeks), index=M.index, columns=M.columns)
    return dict(logmean4=lm4, ratio=ratio, dlog4=dl, mk8=tau)


def tone_feature_matrices(Tm, S):
    """Mean tone over the last tone_weeks weeks minus the median over the tone_baseline_weeks weeks before them.
    NOT IN RECORD: complete windows only; the mean of the weekly values (they are already mention-weighted)."""
    r, b = S.tone_weeks, S.tone_baseline_weeks
    mean = Tm.rolling(r, min_periods=r).mean()
    base = Tm.shift(r).rolling(b, min_periods=b).median()
    return mean - base


def _empty_states():
    d = {'node_id': pd.Series(dtype=object), 'origin_mi': pd.Series(dtype='int64')}
    d.update({c: pd.Series(dtype=float) for c in ['shift8', 'lab_sustained', 'lab_intermediate', 'lab_fading', 'shift_size',
                                                  'shift_weeks', 'split_qok']})
    return pd.DataFrame(d)


def shift_states(shifts, sw, source, Ls, S):
    """Real-time shift state per (node, origin month) for one source.
    Ls: {mi: Monday of the last included week}. A shift counts at origin t if its start week is in the last shift_weeks
    weeks up to and including that last week. Its label is given only if the labelling week is on or before the last
    week and the label is one of the three classes (interrupted and censored count as none yet). Size so far = peak
    ratio to normal over the shift's weeks up to the last week; weeks since start = last week - start week, in weeks.
    Never reads seasonal, quality_flag or title_confusion. Also returns split_qok: a quality-ok shift in the window
    (quality_ok is used only to split the scoring, never as a feature)."""
    sh = shifts[shifts.source == source]
    if len(sh) == 0:
        return _empty_states()
    swi = sw[(sw.source == source) & (sw.shift_id >= 0) & (sw.phase.isin(['start', 'in shift']))]
    ratio = {k: dict(zip(g.week, g.ratio)) for k, g in swi.groupby(['node_id', 'shift_id'])}
    mis = np.array(sorted(Ls))
    Lw = np.array([np.datetime64(Ls[m], 'D') for m in mis])
    win = np.timedelta64(7 * (S.shift_weeks - 1), 'D')
    rows = []
    for r in sh.itertuples():
        start = np.datetime64(pd.Timestamp(r.start_week), 'D')
        lo = np.searchsorted(Lw, start, side='left')
        hi = np.searchsorted(Lw, start + win, side='right')
        rt = ratio.get((r.node_id, r.id), {})
        qok = bool(getattr(r, 'quality_ok', True)) if source == 'wikipedia' else False
        for k in range(lo, hi):
            L = pd.Timestamp(Lw[k])
            known = (pd.notna(r.label_week) and pd.Timestamp(r.label_week) <= L and r.label in LABELS)
            vals = [v for w, v in rt.items() if w <= L and np.isfinite(v)]
            rows.append(dict(node_id=r.node_id, origin_mi=int(mis[k]), start=pd.Timestamp(r.start_week), shift8=1.0,
                             lab_sustained=float(known and r.label == 'sustained'),
                             lab_intermediate=float(known and r.label == 'intermediate'),
                             lab_fading=float(known and r.label == 'fading'),
                             shift_size=max(vals) if vals else np.nan,
                             shift_weeks=float((L - pd.Timestamp(r.start_week)).days // 7), qok=qok))
    X = pd.DataFrame(rows)
    if X.empty:
        return _empty_states()
    qk = X.groupby(['node_id', 'origin_mi']).qok.max().rename('split_qok').reset_index()
    X = X.sort_values('start').drop_duplicates(['node_id', 'origin_mi'], keep='last').drop(columns=['start', 'qok'])
    return X.merge(qk, on=['node_id', 'origin_mi'], how='left')


def interest_frame(weekly, shifts, sw, source, origins, S, value='share'):
    """Per (node, origin month): the five volume features of one source.
    weekly: node_id, week, share, partial_week. origins: iterable of month indexes."""
    Ls = {int(m): last_week_monday(m) for m in origins}
    valid = ~weekly.partial_week.astype(bool) if 'partial_week' in weekly.columns else None
    M = weekly_matrix(weekly, value, valid)
    F = weekly_feature_matrices(M, S)
    mis = sorted(Ls)
    idx = pd.DatetimeIndex([Ls[m] for m in mis])
    parts = []
    for name, Mat in F.items():
        sub = Mat.reindex(index=idx)
        sub.index = mis
        parts.append(sub.stack(future_stack=True).rename(name))
    X = pd.concat(parts, axis=1)
    X.index.names = ['origin_mi', 'node_id']
    X = X.reset_index()
    st = shift_states(shifts, sw, source, Ls, S) if shifts is not None else None
    X = X.merge(st, on=['node_id', 'origin_mi'], how='left') if st is not None else X.assign(shift8=np.nan)
    have = X.ratio.notna() | X.shift8.notna()
    for c in ['shift8', 'lab_sustained', 'lab_intermediate', 'lab_fading', 'shift_size', 'shift_weeks']:
        if c not in X.columns:
            X[c] = np.nan
        # NOT IN RECORD: no shift in the window gives 0 for the flag, the labels, the size and the weeks (the flag says
        # "none"); a missing value means the node has no usable interest series at this origin.
        X[c] = np.where(X[c].notna(), X[c], np.where(have, 0.0, np.nan))
    if 'split_qok' not in X.columns:
        X['split_qok'] = np.nan
    X['split_qok'] = X.split_qok.fillna(0.0)
    X['last_week'] = X.origin_mi.map(Ls)
    return X


def tone_frame(gdelt, origins, S):
    Ls = {int(m): last_week_monday(m) for m in origins}
    mis = sorted(Ls)
    idx = pd.DatetimeIndex([Ls[m] for m in mis])
    valid = ~gdelt.partial_week.astype(bool) if 'partial_week' in gdelt.columns else None
    parts = []
    for src, name in [('tone', 't_tone'), ('positive', 't_pos'), ('negative', 't_neg')]:
        Tm = weekly_matrix(gdelt, src, valid)
        sub = tone_feature_matrices(Tm, S).reindex(index=idx)
        sub.index = mis
        parts.append(sub.stack(future_stack=True).rename(name))
    X = pd.concat(parts, axis=1)
    X.index.names = ['origin_mi', 'node_id']
    return X.reset_index()


# ---------------- demand features ----------------
def _shift_cols(A, k):
    """out[:, j] = A[:, j - k] (NaN where j - k is outside); k may be negative (future, used for targets only)."""
    out = np.full(A.shape, np.nan)
    n = A.shape[1]
    if k >= 0:
        if k < n:
            out[:, k:] = A[:, :n - k]
    else:
        if -k < n:
            out[:, :n + k] = A[:, -k:]
    return out


def demand_table(panel, S, h, drop_missing_target=True):
    """Demand-only columns for one panel (one or more formats) and one horizon.
    NOT IN RECORD: a window mean (t-5..t for the 6-month mean; t-11..t and t-23..t-12 for the seasonal naive) uses the
    available months and needs at least half of them; otherwise it is missing."""
    out = []
    nodes_info = panel.drop_duplicates('node_id').set_index('node_id')[['level', 'broad_id']]
    for fmt, P in panel.groupby('format'):
        grid = np.arange(int(P.mi.min()), int(P.mi.max()) + 1)
        Y = P.pivot(index='node_id', columns='mi', values='log_share').reindex(columns=grid)
        SZ = P.pivot(index='node_id', columns='mi', values='size_ok').reindex(columns=grid).fillna(False).astype(bool)
        mo = P.drop_duplicates('mi').set_index('mi')
        tot = mo.total_checkouts.where(mo.month_ok).reindex(grid).to_numpy(float)
        with np.errstate(divide='ignore', invalid='ignore'):
            ltot = np.log(np.where(tot > 0, tot, np.nan))
        dlt = ltot - np.concatenate([[np.nan], ltot[:-1]])
        A = Y.to_numpy(float)
        nm = S.demand_mean_window
        mean6 = Y.T.rolling(nm, min_periods=int(np.ceil(nm / 2))).mean().T.to_numpy()
        m12 = Y.T.rolling(12, min_periods=6).mean().T.to_numpy()
        m12_prev = _shift_cols(m12, 12)
        ly = _shift_cols(A, 12 - h)                  # the target month one year earlier: t + h - 12
        tgt = _shift_cols(A, -h)
        elig = SZ.to_numpy() & np.isfinite(A)
        ii, jj = np.where(elig)
        d = pd.DataFrame(dict(node_id=Y.index.to_numpy()[ii], origin_mi=grid[jj], format=fmt, y=tgt[ii, jj],
                              ls_t=A[ii, jj], ls_t1=_shift_cols(A, 1)[ii, jj], ls_t2=_shift_cols(A, 2)[ii, jj],
                              ls_ly=ly[ii, jj], mean6=mean6[ii, jj], dlog_total=dlt[jj],
                              m12_last=m12[ii, jj], m12_prev=m12_prev[ii, jj]))
        out.append(d)
    D = pd.concat(out, ignore_index=True)
    D['level'] = D.node_id.map(nodes_info.level)
    D['broad_id'] = D.node_id.map(nodes_info.broad_id)
    D['h'] = h
    D['target_mi'] = D.origin_mi + h
    D['tmonth'] = ((D.target_mi % 12) + 1).map('{:02d}'.format)
    D['target_ok'] = D.y.notna()
    if drop_missing_target:
        D = D[D.target_ok].reset_index(drop=True)
    return D


def build_features(panel, nodes, wiki, shifts, sw, gdelt, S, group='seattle', drop_missing_target=True):
    """The full table for one group ('seattle' with the three Seattle formats, or 'librivox')."""
    panel = panel[panel.level.isin(S.levels)]
    parts = [demand_table(panel, S, h, drop_missing_target) for h in S.horizons]
    F = pd.concat(parts, ignore_index=True)
    # interest frames are computed for every month from the first origin to the last (cheap)
    allm = list(range(int(F.origin_mi.min()), int(F.origin_mi.max()) + 1)) if len(F) else []
    W = interest_frame(wiki, shifts, sw, 'wikipedia', allm, S)
    split = W[['node_id', 'origin_mi', 'split_qok', 'last_week']].rename(columns={'split_qok': 'split_qok_shift8'})
    W = W.drop(columns=['split_qok', 'last_week']).rename(columns={c: 'w_' + c for c in INTEREST_SUFFIX})
    F = F.merge(W, on=['node_id', 'origin_mi'], how='left').merge(split, on=['node_id', 'origin_mi'], how='left')
    if gdelt is not None and len(gdelt):
        G = interest_frame(gdelt, shifts, sw, 'gdelt', allm, S).drop(columns=['split_qok', 'last_week'])
        G = G.rename(columns={c: 'g_' + c for c in INTEREST_SUFFIX})
        T = tone_frame(gdelt, allm, S)
        F = F.merge(G, on=['node_id', 'origin_mi'], how='left').merge(T, on=['node_id', 'origin_mi'], how='left')
    else:
        for c in G_NUM + T_NUM:
            F[c] = np.nan
    F['split_qok_shift8'] = F.split_qok_shift8.fillna(0.0)
    F['group'] = group
    F['origin'] = [f'{m // 12:04d}-{m % 12 + 1:02d}' for m in F.origin_mi]
    cols = (['group', 'format', 'level', 'node_id', 'broad_id', 'origin_mi', 'origin', 'h', 'target_mi', 'tmonth', 'target_ok', 'y']
            + D_NUM + ['m12_last', 'm12_prev'] + W_NUM + G_NUM + T_NUM + ['split_qok_shift8', 'last_week'])
    return F[cols].sort_values(['group', 'h', 'origin_mi', 'format', 'node_id']).reset_index(drop=True)
