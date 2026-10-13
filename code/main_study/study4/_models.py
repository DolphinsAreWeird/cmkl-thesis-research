# Pure functions: baselines, ridge, CatBoost, walk-forward and the metrics. No file or settings access except the
# `S` object passed in (parsed from the fixed record by _settings.py).
import warnings
import numpy as np, pandas as pd
from scipy import stats
from _features import feature_columns


# ======================= baselines =======================
def naive(df):
    """y(t+h) = y(t) (record: y(t+1) = y(t); the same carried to horizon 2)."""
    return df['ls_t'].to_numpy(float)


def seasonal_naive(df):
    """y(t+h) = y(t+h-12) + (mean of y over t-11..t) - (mean of y over t-23..t-12).
    For h = 1 this is the record's formula. NOT IN RECORD: for h = 2 the first term is the target month one year
    earlier, y(t-10); the level adjustment is unchanged."""
    return (df['ls_ly'] + df['m12_last'] - df['m12_prev']).to_numpy(float)


# ======================= ridge =======================
def _design(train, test, num, cat):
    """Standardise numeric columns on the training rows only; missing -> 0 after standardising plus a 0/1 missing
    indicator for every numeric column that has a missing value in the training rows; categoricals one-hot
    (categories from the training rows; an unseen category is all zeros; constant columns are dropped)."""
    Xtr = train[num].to_numpy(float)
    Xte = test[num].to_numpy(float)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)       # all-missing columns (e.g. G outside the GDELT period)
        mu = np.nanmean(Xtr, axis=0)
        sd = np.nanstd(Xtr, axis=0)
    mu = np.where(np.isfinite(mu), mu, 0.0)
    sd = np.where(np.isfinite(sd) & (sd > 0), sd, 1.0)
    ztr, zte = (Xtr - mu) / sd, (Xte - mu) / sd
    miss_cols = np.where(np.isnan(Xtr).any(axis=0))[0]
    blocks_tr = [np.where(np.isnan(ztr), 0.0, ztr), np.isnan(Xtr[:, miss_cols]).astype(float)]
    blocks_te = [np.where(np.isnan(zte), 0.0, zte), np.isnan(Xte[:, miss_cols]).astype(float)]
    for c in cat:
        a_tr = train[c].astype(str).to_numpy()
        a_te = test[c].astype(str).to_numpy()
        cats = sorted(set(a_tr))
        if len(cats) < 2:
            continue
        blocks_tr.append(np.stack([(a_tr == k) for k in cats], axis=1).astype(float))
        blocks_te.append(np.stack([(a_te == k) for k in cats], axis=1).astype(float))
    return np.hstack(blocks_tr), np.hstack(blocks_te)


def _ridge_fit_predict(train, test, num, cat, alpha):
    from sklearn.linear_model import Ridge
    Xtr, Xte = _design(train, test, num, cat)
    m = Ridge(alpha=alpha).fit(Xtr, train['y'].to_numpy(float))
    return m.predict(Xte)


def choose_alpha(train, num, cat, h, S):
    """Alpha from S.ridge_alphas by MAE on the last S.ridge_val_origins training origins (time split): the model for
    each alpha is fitted on the training rows whose target month is on or before the first validation origin.
    NOT IN RECORD: with fewer than 3 x S.ridge_val_origins training origins the validation block is a third of them;
    with fewer than 3 origins in total the middle alpha is used."""
    origins = np.sort(train['origin_mi'].unique())
    n_val = min(S.ridge_val_origins, len(origins) // 3)
    alphas = list(S.ridge_alphas)
    if n_val < 1:
        return alphas[len(alphas) // 2]
    val = origins[-n_val:]
    fit = train[train.origin_mi + h <= val[0]]
    va = train[train.origin_mi.isin(val)]
    if len(fit) < 10 or len(va) < 1:
        return alphas[len(alphas) // 2]
    err = []
    for a in alphas:
        p = _ridge_fit_predict(fit, va, num, cat, a)
        err.append(np.mean(np.abs(p - va['y'].to_numpy(float))))
    return alphas[int(np.argmin(err))]      # ties: the smaller alpha


def fit_predict_ridge(train, test, fset, h, S):
    num, cat = feature_columns(fset)
    a = choose_alpha(train, num, cat, h, S)
    return _ridge_fit_predict(train, test, num, cat, a), a


# ======================= CatBoost =======================
def catboost_params(S, thread_count):
    return dict(iterations=S.cb_iterations, depth=S.cb_depth, learning_rate=S.cb_learning_rate, loss_function=S.cb_loss,
                random_seed=S.cb_seed, thread_count=int(thread_count), verbose=False, allow_writing_files=False)


def fit_predict_catboost_cols(train, test, num, cat, S, thread_count):
    from catboost import CatBoostRegressor
    cols = list(num) + list(cat)

    def prep(d):
        X = d[cols].copy()
        for c in cat:
            X[c] = X[c].astype(str).astype(object)
        return X
    m = CatBoostRegressor(cat_features=list(cat), **catboost_params(S, thread_count))
    m.fit(prep(train), train['y'].to_numpy(float))
    return m.predict(prep(test))


def fit_predict_catboost(train, test, fset, S, thread_count):
    """Pooled CatBoost with the record's parameters; categorical: S.cat_features; no category id."""
    num, cat = feature_columns(fset)
    assert tuple(cat) == tuple(S.cat_features), 'categorical features differ from the record'
    return fit_predict_catboost_cols(train, test, num, cat, S, thread_count)


# ======================= walk-forward =======================
def training_rows(F, origin_mi, h):
    """Rows usable at origin t: origin s with s + h <= t, target observed (record)."""
    return F[(F.h == h) & (F.origin_mi + h <= origin_mi) & F.y.notna()]


def test_rows(F, origin_mi, h):
    return F[(F.h == h) & (F.origin_mi == origin_mi) & F.y.notna() & F.ls_t.notna()]


def walk_forward(F, origins, h, fit_predict):
    """Expanding window, retrained at every origin. fit_predict(train, test) -> y_hat (array). Returns the test rows
    with y_hat. Never trains on a target month after the origin; never scores a missing target."""
    out = []
    for t in origins:
        tr, te = training_rows(F, t, h), test_rows(F, t, h)
        assert (tr.origin_mi + h <= t).all()
        if len(te) == 0 or len(tr) == 0:
            continue
        te = te.copy()
        te['y_hat'] = fit_predict(tr, te)
        out.append(te)
    return pd.concat(out, ignore_index=True) if out else F.iloc[0:0].assign(y_hat=[])


# ======================= metrics =======================
def mae(err):
    e = np.abs(np.asarray(err, float))
    e = e[np.isfinite(e)]
    return float(e.mean()) if len(e) else np.nan


def skill(mae_new, mae_base):
    return 1.0 - mae_new / mae_base if mae_base and np.isfinite(mae_base) and mae_base > 0 else np.nan


def mase(y, f, f_seasonal):
    """MAE of the forecast divided by the MAE of the seasonal naive forecast, on the rows where both exist."""
    y, f, s = (np.asarray(a, float) for a in (y, f, f_seasonal))
    ok = np.isfinite(y) & np.isfinite(f) & np.isfinite(s)
    if not ok.any():
        return np.nan
    den = np.mean(np.abs(y[ok] - s[ok]))
    return float(np.mean(np.abs(y[ok] - f[ok])) / den) if den > 0 else np.nan


def newey_west_lrv(d, lag):
    """Long-run variance of a series with Bartlett weights (Newey-West)."""
    d = np.asarray(d, float)
    T = len(d)
    x = d - d.mean()
    g0 = float(np.dot(x, x) / T)
    lrv = g0
    for l in range(1, min(lag, T - 1) + 1):
        g = float(np.dot(x[l:], x[:-l]) / T)
        lrv += 2 * (1 - l / (lag + 1)) * g
    return lrv


def dm_test(loss_base, loss_new, lag):
    """Diebold-Mariano test on monthly mean losses (here absolute errors), Newey-West variance, one-sided:
    H1 = the new forecast has the smaller loss. d = base - new, so a positive mean favours the new forecast.
    NOT IN RECORD: the p-value uses the standard normal (no small-sample correction). Returns (statistic, p)."""
    d = np.asarray(loss_base, float) - np.asarray(loss_new, float)
    d = d[np.isfinite(d)]
    T = len(d)
    if T < 4:
        return np.nan, np.nan
    lrv = newey_west_lrv(d, lag)
    if not np.isfinite(lrv) or lrv <= 0:
        return np.nan, np.nan
    stat = d.mean() / np.sqrt(lrv / T)
    return float(stat), float(1 - stats.norm.cdf(stat))


def monthly_loss(origin, err):
    """Per-origin sum of absolute errors and row counts -> (origins, sums, counts)."""
    df = pd.DataFrame({'o': np.asarray(origin), 'e': np.abs(np.asarray(err, float))}).dropna()
    g = df.groupby('o').e.agg(['sum', 'count'])
    return g.index.to_numpy(), g['sum'].to_numpy(), g['count'].to_numpy()


def block_bootstrap_skill(sum_base, sum_new, block, n_boot, seed, level=0.95):
    """Moving-block bootstrap over test months. sum_base / sum_new: per-month sums of absolute errors over the same
    rows (equal counts). Resamples blocks of consecutive months (overlapping blocks, not wrapped) until the original
    number of months is reached. Returns (lower, upper, skill draws)."""
    sb, sn = np.asarray(sum_base, float), np.asarray(sum_new, float)
    T = len(sb)
    if T < 2:
        return np.nan, np.nan, np.array([])
    b = min(block, T)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(T / b))
    starts = rng.integers(0, T - b + 1, size=(n_boot, nb))
    idx = (starts[:, :, None] + np.arange(b)[None, None, :]).reshape(n_boot, -1)[:, :T]
    draws = 1.0 - sn[idx].sum(axis=1) / sb[idx].sum(axis=1)
    lo, hi = np.quantile(draws, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi), draws


def compare_models(origin, err_base, err_new, S):
    """Skill of the new model against the base, DM one-sided p, and the bootstrap interval, on the same rows."""
    ok = np.isfinite(err_base) & np.isfinite(err_new)
    o, e0, e1 = np.asarray(origin)[ok], np.abs(np.asarray(err_base, float)[ok]), np.abs(np.asarray(err_new, float)[ok])
    if len(o) == 0:
        return dict(n=0, months=0, mae_base=np.nan, mae_new=np.nan, skill=np.nan, ci_lo=np.nan, ci_hi=np.nan, dm_stat=np.nan, dm_p=np.nan)
    mo, s0, c0 = monthly_loss(o, e0)
    _, s1, _ = monthly_loss(o, e1)
    lo, hi, _ = block_bootstrap_skill(s0, s1, S.boot_block, S.boot_n, S.boot_seed, S.ci_level)
    stat, p = dm_test(s0 / c0, s1 / c0, S.dm_lag)
    return dict(n=int(ok.sum()), months=int(len(mo)), mae_base=float(e0.mean()), mae_new=float(e1.mean()),
                skill=skill(e1.mean(), e0.mean()), ci_lo=lo, ci_hi=hi, dm_stat=stat, dm_p=p)


def helps(row, S):
    """The record's rule: skill > 0, the bootstrap interval above zero, and DM p < alpha."""
    return bool(row['skill'] > 0 and row['ci_lo'] > 0 and row['dm_p'] < S.helps_alpha)


# NOT IN RECORD: rank statistics within a month and format need at least this many categories.
MIN_GROUP = 10


def _groups(df, cols):
    return df.groupby(list(cols), sort=False)


def spearman_within(df, fc_change, act_change, group_cols):
    """Mean over (month, format[, level]) groups of the Spearman correlation between forecast change and actual
    change across categories."""
    vals = []
    for _, g in _groups(df.assign(_f=fc_change, _a=act_change), group_cols):
        g = g[np.isfinite(g._f) & np.isfinite(g._a)]
        if len(g) < MIN_GROUP or g._f.nunique() < 2 or g._a.nunique() < 2:
            continue
        vals.append(stats.spearmanr(g._f, g._a)[0])
    return float(np.mean(vals)) if vals else np.nan


def top_hit_rate(df, fc_change, act_change, group_cols, share):
    """Mean over groups of the share of the k categories with the largest forecast rises that are among the k
    categories with the largest actual rises, k = ceil(share x n). Base rate = share."""
    vals = []
    for _, g in _groups(df.assign(_f=fc_change, _a=act_change), group_cols):
        g = g[np.isfinite(g._f) & np.isfinite(g._a)]
        n = len(g)
        if n < MIN_GROUP:
            continue
        k = max(1, int(np.ceil(share * n)))
        top_f = set(g.index[np.argsort(-g._f.to_numpy(), kind='stable')[:k]])
        top_a = set(g.index[np.argsort(-g._a.to_numpy(), kind='stable')[:k]])
        vals.append(len(top_f & top_a) / k)
    return float(np.mean(vals)) if vals else np.nan


def direction_accuracy(fc_change, act_change, threshold):
    """Share of category-months with |actual change| > threshold whose forecast change has the same sign."""
    f, a = np.asarray(fc_change, float), np.asarray(act_change, float)
    ok = np.isfinite(f) & np.isfinite(a) & (np.abs(a) > threshold)
    return float(np.mean(np.sign(f[ok]) == np.sign(a[ok]))) if ok.any() else np.nan


def auc(score, label):
    """Area under the ROC curve (rank form); NaN when only one class is present."""
    s, y = np.asarray(score, float), np.asarray(label, bool)
    ok = np.isfinite(s)
    s, y = s[ok], y[ok]
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    r = stats.rankdata(s)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
