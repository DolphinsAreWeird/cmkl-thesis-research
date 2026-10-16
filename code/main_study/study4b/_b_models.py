# Study 4b models and metrics. Part A: zero change, ridge and CatBoost on the change. Part B: CatBoost classifier and logistic
# regression for surges. Reuses Study 4's ridge design, alpha choice, CatBoost trainer and the DM / bootstrap code (through _s4).
import warnings
import numpy as np, pandas as pd
import _s4
from _b_features import feature_columns

M4 = _s4.models

# NOT IN RECORD: a model is fitted only if the training set has at least this many rows (as in Study 4); the zero-change
# forecast is always made.
MIN_TRAIN_ROWS = 30


# ---------------- Part A ----------------
def as_change_target(df):
    """A copy whose `y` is the change d(t+h) - d(t), so that Study 4's trainers (which fit df['y']) fit the change."""
    return df.assign(y=df['change'])


def zero_change(df):
    return np.zeros(len(df))


def fit_predict_ridge_change(train, test, fset, h, B):
    """Ridge on the change; alpha from the Study 4 grid and rule (last validation origins, MAE, ties to the smaller alpha)."""
    num, cat = feature_columns(fset)
    tr = as_change_target(train)
    a = M4.choose_alpha(tr, num, cat, h, B.s4)
    return M4._ridge_fit_predict(tr, test, num, cat, a), a


def fit_predict_catboost_change(train, test, fset, B, thread_count):
    num, cat = feature_columns(fset)
    assert tuple(cat) == tuple(B.cat_features), 'categorical features differ from the record'
    return M4.fit_predict_catboost_cols(as_change_target(train), test, num, cat, B.s4, thread_count)


# ---------------- Part B ----------------
def fit_predict_catboost_surge(train, test, fset, B, thread_count):
    """CatBoost classifier, logloss, the record's tree settings and categorical features. Returns P(surge)."""
    from catboost import CatBoostClassifier
    num, cat = feature_columns(fset)
    cols = list(num) + list(cat)
    y = train['surge'].to_numpy(float).astype(int)
    if y.min() == y.max():                      # NOT IN RECORD: one class in the training rows -> the training base rate
        return np.full(len(test), float(y.mean()))

    def prep(d):
        X = d[cols].copy()
        for c in cat:
            X[c] = X[c].astype(str).astype(object)
        return X
    p = dict(iterations=B.cb_iterations, depth=B.cb_depth, learning_rate=B.cb_learning_rate, loss_function='Logloss',
             random_seed=B.cb_seed, thread_count=int(thread_count), verbose=False, allow_writing_files=False)
    m = CatBoostClassifier(cat_features=list(cat), **p)
    m.fit(prep(train), y)
    return m.predict_proba(prep(test))[:, 1]


# NOT IN RECORD: logistic regression with L2 penalty, C = 1.0 (the scikit-learn default, not tuned), lbfgs, max_iter 2000;
# the same design as Study 4's ridge (numeric standardised on training rows, 0 plus a missing indicator, one-hot categoricals).
LOGIT_C, LOGIT_MAX_ITER = 1.0, 2000


def fit_predict_logistic_surge(train, test, fset, B):
    from sklearn.linear_model import LogisticRegression
    num, cat = feature_columns(fset)
    y = train['surge'].to_numpy(float).astype(int)
    if y.min() == y.max():
        return np.full(len(test), float(y.mean()))
    Xtr, Xte = M4._design(train, test, num, cat)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        m = LogisticRegression(C=LOGIT_C, max_iter=LOGIT_MAX_ITER).fit(Xtr, y)
    return m.predict_proba(Xte)[:, 1]


# ---------------- Part B metrics ----------------
def average_precision(y, s):
    """Average precision = sum over positives of precision at that rank / number of positives (ranks by descending score,
    ties broken by input order). NaN with no positives."""
    y, s = np.asarray(y, float), np.asarray(s, float)
    ok = np.isfinite(y) & np.isfinite(s)
    y, s = y[ok], s[ok]
    npos = y.sum()
    if npos == 0:
        return np.nan
    yy = y[np.argsort(-s, kind='stable')]
    tp = np.cumsum(yy)
    return float((tp / np.arange(1, len(yy) + 1) * yy).sum() / npos)


def brier(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    ok = np.isfinite(y) & np.isfinite(p)
    return float(np.mean((p[ok] - y[ok]) ** 2)) if ok.any() else np.nan


def top_k_recall(df, score_col, k, group_cols):
    """Recall among the k highest-scored category-formats per group (origin and format): hits / surges, summed over groups.
    Also the expectation under random ranking, sum of surges x min(k, n) / n over the same groups. Groups with no surge add
    nothing to either. Returns (recall, random recall, surges, groups with a surge)."""
    hits = rnd = tot = 0.0
    ng = 0
    for _, g in df.groupby(list(group_cols), sort=False):
        pos = g['surge'].to_numpy(float)
        n_pos = pos.sum()
        if n_pos == 0:
            continue
        order = np.argsort(-g[score_col].to_numpy(float), kind='stable')[:k]
        hits += pos[order].sum()
        rnd += n_pos * min(k, len(g)) / len(g)
        tot += n_pos
        ng += 1
    return (hits / tot, rnd / tot, int(tot), ng) if tot else (np.nan, np.nan, 0, 0)


def ap_diff_bootstrap(origin, y, s_base, s_new, block, n_boot, seed, level=0.95):
    """Moving-block bootstrap over test months (overlapping blocks of `block` consecutive months, not wrapped, until the
    original number of months is reached; same scheme as the Study 4 skill bootstrap). Returns the interval of AP(new) - AP(base)
    and the draws. All rows of a drawn month enter the resample."""
    origin, y = np.asarray(origin), np.asarray(y, float)
    s0, s1 = np.asarray(s_base, float), np.asarray(s_new, float)
    months = np.unique(origin)
    T = len(months)
    if T < 2:
        return np.nan, np.nan, np.array([])
    rows = [np.where(origin == m)[0] for m in months]
    b = min(block, T)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(T / b))
    starts = rng.integers(0, T - b + 1, size=(n_boot, nb))
    idx = (starts[:, :, None] + np.arange(b)[None, None, :]).reshape(n_boot, -1)[:, :T]
    draws = np.full(n_boot, np.nan)
    for i in range(n_boot):
        r = np.concatenate([rows[j] for j in idx[i]])
        a0, a1 = average_precision(y[r], s0[r]), average_precision(y[r], s1[r])
        draws[i] = a1 - a0
    d = draws[np.isfinite(draws)]
    if len(d) == 0:
        return np.nan, np.nan, draws
    lo, hi = np.quantile(d, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi), draws
