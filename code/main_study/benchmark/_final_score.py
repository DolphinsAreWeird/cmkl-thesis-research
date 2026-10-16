# Scoring functions of the final unseen test (also used by the dry run on known months). Pure functions on a table with one row per
# (series, origin, horizon): keys, the observed log share y_true, the origin value y_t and one column per pipeline (log-share forecast).
# Intervals resample categories (node_id: all formats, levels, origins and horizons of a node together) 2,000 times with seed 20261015 (the record's
# bootstrap), because with one to three test months a month bootstrap has nothing to resample.
import numpy as np, pandas as pd
from scipy import stats

SEED, N_BOOT = 20261015, 2000
PRINT_EBOOK = ('print', 'ebook')


def _abs_err(df, p):
    return (df[p] - df['y_true']).abs().to_numpy(float)


def _node_index(df):
    codes, uniq = pd.factorize(df['node_id'])
    return codes, len(uniq)


def _boot_ratio(num_by_node, den_by_node, n_boot=N_BOOT, seed=SEED):
    """Interval of sum(num) / sum(den) over resampled nodes."""
    rng = np.random.default_rng(seed)
    n = len(num_by_node)
    idx = rng.integers(0, n, size=(n_boot, n))
    r = num_by_node[idx].sum(axis=1) / den_by_node[idx].sum(axis=1)
    return np.quantile(r, [0.025, 0.975])


def pooled_ratio(df, p, q='naive', n_boot=N_BOOT):
    """Sum of absolute errors of p / of q over the rows where both have a forecast and the target exists; node-bootstrap 95% interval."""
    ok = df[p].notna() & df[q].notna() & df['y_true'].notna()
    d = df[ok]
    if len(d) == 0:
        return dict(rows=0, ratio=np.nan, lo=np.nan, hi=np.nan, nodes=0)
    codes, n = _node_index(d)
    ep, eq = _abs_err(d, p), _abs_err(d, q)
    sp = np.bincount(codes, weights=ep, minlength=n)
    sq = np.bincount(codes, weights=eq, minlength=n)
    lo, hi = _boot_ratio(sp, sq, n_boot) if (n_boot and sq.sum() > 0) else (np.nan, np.nan)
    return dict(rows=int(len(d)), ratio=float(sp.sum() / sq.sum()) if sq.sum() > 0 else np.nan, lo=float(lo), hi=float(hi), nodes=int(n),
                mae_p=float(ep.mean()), mae_q=float(eq.mean()))


def avg_rel_mae(df, p, q='naive', n_boot=N_BOOT):
    """Record's AvgRelMAE: geometric mean over series (format, level, node) of MAE(p) / MAE(q) over the series' scored rows; series with MAE(q) = 0 are
    left out (and counted); node-bootstrap 95% interval."""
    ok = df[p].notna() & df[q].notna() & df['y_true'].notna()
    d = df[ok].copy()
    if len(d) == 0:
        return dict(series=0, value=np.nan, lo=np.nan, hi=np.nan, dropped=0)
    d['sid'] = d['format'].astype(str) + '|' + d['level'].astype(str) + '|' + d['node_id'].astype(str)
    d['e_p'], d['e_q'] = _abs_err(d, p), _abs_err(d, q)
    s = d.groupby('sid').agg(e_p=('e_p', 'mean'), e_q=('e_q', 'mean'), node=('node_id', 'first'))
    dropped = int((s['e_q'] <= 0).sum())
    s = s[(s['e_q'] > 0) & (s['e_p'] > 0)]
    if len(s) == 0:
        return dict(series=0, value=np.nan, lo=np.nan, hi=np.nan, dropped=dropped)
    s['l'] = np.log(s['e_p'] / s['e_q'])
    codes, uniq = pd.factorize(s.node)
    n = len(uniq)
    L = np.bincount(codes, weights=s.l.to_numpy(), minlength=n)
    C = np.bincount(codes, minlength=n).astype(float)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, n, size=(n_boot, n))
    v = np.exp(L[idx].sum(axis=1) / C[idx].sum(axis=1))
    lo, hi = np.quantile(v, [0.025, 0.975])
    return dict(series=int(len(s)), value=float(np.exp(s.l.mean())), lo=float(lo), hi=float(hi), dropped=dropped)


def spearman_rise(df, p, group=('origin_mi', 'h', 'format', 'level'), min_group=10, n_boot=N_BOOT):
    """Rise task: Spearman correlation across series between the forecast change (forecast - y_t) and the actual change (y_true - y_t), computed within each
    (origin, horizon, format, level) group of at least min_group series and averaged over groups. Node-bootstrap 95% interval."""
    d = df[df[p].notna() & df['y_true'].notna() & df['y_t'].notna()].copy()
    d['fc'] = d[p] - d['y_t']
    d['ac'] = d['y_true'] - d['y_t']

    def value(x):
        v = []
        for _, g in x.groupby(list(group)):
            if len(g) < min_group or g.fc.nunique() < 2 or g.ac.nunique() < 2:
                continue
            v.append(stats.spearmanr(g.fc, g.ac)[0])
        return float(np.mean(v)) if v else np.nan, len(v)
    val, ng = value(d)
    if ng == 0 or n_boot == 0:
        return dict(groups=ng, value=val, lo=np.nan, hi=np.nan)
    nodes = d.node_id.unique()
    by = {n: g for n, g in d.groupby('node_id')}
    rng = np.random.default_rng(SEED)
    out = []
    for _ in range(min(n_boot, 500)):
        pick = rng.choice(nodes, size=len(nodes), replace=True)
        x = pd.concat([by[n] for n in pick], ignore_index=True)
        out.append(value(x)[0])
    lo, hi = np.nanquantile(out, [0.025, 0.975])
    return dict(groups=ng, value=val, lo=float(lo), hi=float(hi))


def direction_accuracy(df, p, threshold=0.10):
    d = df[df[p].notna() & df['y_true'].notna() & df['y_t'].notna()]
    a = (d['y_true'] - d['y_t']).to_numpy(float)
    f = (d[p] - d['y_t']).to_numpy(float)
    k = np.abs(a) > threshold
    return float(np.mean(np.sign(f[k]) == np.sign(a[k]))) if k.any() else np.nan


def score_table(df, pipes, n_boot=N_BOOT, with_spearman=False):
    """One row per pipeline: pooled ratio and AvgRelMAE against naive with intervals, mean absolute error x100, direction accuracy."""
    rows = []
    for p in pipes:
        pr = pooled_ratio(df, p, 'naive', n_boot) if p != 'naive' else dict(rows=int(df.y_true.notna().sum()), ratio=1.0, lo=1.0, hi=1.0, nodes=df.node_id.nunique(),
                                                                         mae_p=float(_abs_err(df[df.y_true.notna()], 'naive').mean()), mae_q=np.nan)
        ar = avg_rel_mae(df, p, 'naive', n_boot) if p != 'naive' else dict(series=np.nan, value=1.0, lo=1.0, hi=1.0, dropped=0)
        r = dict(pipeline=p, rows=pr['rows'], pooled_ratio=pr['ratio'], pooled_lo=pr['lo'], pooled_hi=pr['hi'], avg_rel_mae=ar['value'], avg_lo=ar['lo'], avg_hi=ar['hi'],
                 series=ar['series'], mae_x100=pr.get('mae_p', np.nan) * 100, direction_accuracy=direction_accuracy(df, p) if p != 'naive' else np.nan)
        if with_spearman:
            sp = spearman_rise(df, p, n_boot=n_boot)
            r.update(spearman=sp['value'], spearman_lo=sp['lo'], spearman_hi=sp['hi'], spearman_groups=sp['groups'])
        rows.append(r)
    return pd.DataFrame(rows)
