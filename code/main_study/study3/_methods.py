# Study 3 methods as pure functions. Inputs are log shares indexed by month index mi (= year * 12 + month - 1);
# a missing or zero category-month is NaN (record addendum b). Every window, threshold, seed and size comes from the
# parsed settings S (_settings.py); the few choices the record does not make are marked '# NOT IN RECORD:'.
import math
import numpy as np, pandas as pd
from scipy.optimize import nnls

# NOT IN RECORD: a fit (event-study regression, synthetic-control weights, tone baseline) needs at least this share
# of its window's months available after missing months are dropped.
MIN_FIT_SHARE = 0.75
# NOT IN RECORD: the smallest donor pool for a synthetic-control test.
MIN_DONORS = 2
# NOT IN RECORD: bootstrap intervals are 95% percentile intervals.
CI_LEVEL = 0.95
EPS = 1e-12


# ---------------- months and windows ----------------
def rel_range(m0, a, b):
    """Absolute month indices of relative months a..b (inclusive) around month 0 = m0."""
    return np.arange(m0 + a, m0 + b + 1, dtype=np.int64)


def last_rel(S):
    """Last relative month any method looks at (secondary window or the carry-over lag window)."""
    return max(S.window_primary[1], S.window_secondary[1], S.carry_lag[1])


def values(y, months):
    return y.reindex(months).to_numpy(dtype=float)


def window_mean(v, min_avail):
    """Mean over the available (non-NaN) values; NaN when fewer than min_avail are available.
    Returns (mean, number available)."""
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    return (float(v.mean()) if len(v) >= min_avail else np.nan), int(len(v))


def min_fit(n_months):
    return math.ceil(MIN_FIT_SHARE * n_months)


# ---------------- event study ----------------
def es_fit_months(m0, S):
    """The 24 months ending at month -7 (record), i.e. relative months -30..-7."""
    return rel_range(m0, S.es_fit_end - S.es_fit_len + 1, S.es_fit_end)


def _es_design(rel, cal, cals):
    """Linear trend plus one dummy per calendar month present in the fit (equivalent to intercept + month effects)."""
    X = np.zeros((len(rel), 1 + len(cals)))
    X[:, 0] = rel
    for j, c in enumerate(cals):
        X[:, 1 + j] = cal == c
    return X


def event_study(y, m0, S):
    """OLS of log share on a linear trend and month-of-year effects, fitted on months -30..-7 (record). Returns the
    effect (mean of actual - predicted log share) over the primary and secondary windows, the pre-trend check
    (months -6..-1) and the monthly gaps.
    NOT IN RECORD: a calendar month never seen in the fit (all its fit months missing) gets no prediction, so that
    month counts as missing in the effect window."""
    fit = es_fit_months(m0, S)
    yf = values(y, fit)
    obs = ~np.isnan(yf)
    out = {'es_ok': False, 'es_fit_n': int(obs.sum()), 'es_fit_months': fit[obs]}
    if obs.sum() < min_fit(len(fit)):
        out['es_reason'] = 'too few fit months'
        return out
    cal = fit % 12
    cals = np.unique(cal[obs])
    X = _es_design(fit[obs] - m0, cal[obs], cals)
    if X.shape[0] <= X.shape[1]:
        out['es_reason'] = 'fewer fit months than parameters'
        return out
    beta = np.linalg.lstsq(X, yf[obs], rcond=None)[0]
    rels = np.arange(S.es_pretrend[0], last_rel(S) + 1)
    pm = m0 + rels
    known = np.isin(pm % 12, cals)
    pred = np.where(known, _es_design(rels, pm % 12, cals) @ beta, np.nan)
    gap = values(y, pm) - pred
    out.update(es_ok=True, es_gaps=dict(zip(rels.tolist(), gap.tolist())))
    for tag, win in (('p', S.window_primary), ('s', S.window_secondary)):
        sel = (rels >= win[0]) & (rels <= win[1])
        out[f'es_effect_{tag}'], out[f'es_n_{tag}'] = window_mean(gap[sel], S.min_window_months)
    sel = (rels >= S.es_pretrend[0]) & (rels <= S.es_pretrend[1])
    out['es_pretrend'], out['es_pretrend_n'] = window_mean(gap[sel], S.min_window_months)
    return out


# ---------------- synthetic control ----------------
def simplex_ls(A, b):
    """min ||A w - b|| subject to w >= 0 and sum(w) = 1. NNLS on the system with a heavily weighted sum-to-one row
    appended, then renormalised (the tests check it against a general constrained solver)."""
    k = A.shape[1]
    if k == 1:
        return np.ones(1)
    M = 1e4 * max(1.0, float(np.abs(A).max()), float(np.abs(b).max()))
    w, _ = nnls(np.vstack([A, np.full((1, k), M)]), np.append(b, M), maxiter=100 * k)
    s = w.sum()
    return w / s if s > 0 else np.full(k, 1.0 / k)


def sc_prepare(Y, treated, donors, m0, S):
    """Months -24..last_rel around m0; the treated unit's values; donor values. Months used are those where the
    treated unit is observed. NOT IN RECORD: a donor must be observed in every one of those months, otherwise it is
    left out of the pool (a convex mix cannot be formed with a missing donor value)."""
    ms = rel_range(m0, S.sc_fit[0], last_rel(S))
    y = values(Y[treated], ms)
    obs = ~np.isnan(y)
    X = Y.reindex(index=ms, columns=list(donors)).to_numpy(dtype=float)
    keep = ~np.isnan(X[obs]).any(axis=0) if len(donors) else np.zeros(0, bool)
    used = [d for d, k in zip(donors, keep) if k]
    return dict(ms=ms, rel=ms - m0, y=y, X=X[:, keep], donors=used, obs=obs)


def sc_fit(y, X, rel, obs, S):
    """Weights on months -24..-3 after demeaning every unit by its own mean over those months (addendum b).
    NOT IN RECORD: the means use the same available months for every unit (months where the treated unit is
    observed), so a month missing for one unit does not shift its mean against the others.
    Returns weights, gaps for all months, fit months and the pre-period RMSPE, or None if the fit is not possible."""
    fit = obs & (rel >= S.sc_fit[0]) & (rel <= S.sc_fit[1])
    if fit.sum() < min_fit(S.sc_fit[1] - S.sc_fit[0] + 1) or X.shape[1] == 0:
        return None
    yd = y - y[fit].mean()
    Xd = X - X[fit].mean(axis=0)
    w = simplex_ls(Xd[fit], yd[fit])
    with np.errstate(invalid='ignore'):
        gap = yd - np.where(np.isnan(Xd), 0.0, Xd) @ w
    gap[~obs] = np.nan
    pre = float(np.sqrt(np.mean(gap[fit] ** 2)))
    return dict(w=w, gap=gap, fit_rel=rel[fit], pre_rmspe=pre)


def window_stats(gap, rel, win, pre_rmspe, S):
    """Effect (mean gap), post RMSPE, ratio and signed ratio over one effect window.
    NOT IN RECORD: 'post' RMSPE is taken over the effect window being tested; the one-sided test ranks the signed
    ratio sign(effect) x post/pre RMSPE, so only a rise counts as extreme."""
    sel = (rel >= win[0]) & (rel <= win[1])
    g = gap[sel]
    g = g[~np.isnan(g)]
    if len(g) < S.min_window_months:
        return dict(effect=np.nan, n=len(g), ratio=np.nan, signed=np.nan)
    eff = float(g.mean())
    ratio = float(np.sqrt(np.mean(g ** 2))) / max(pre_rmspe, EPS)
    return dict(effect=eff, n=len(g), ratio=ratio, signed=float(np.sign(eff)) * ratio)


def rank_p(stat_treated, stat_donors):
    """Rank of the treated statistic among treated + donors (1 = largest, ties count against the treated),
    divided by the number of donors + 1 (record)."""
    s = np.asarray(stat_donors, dtype=float)
    s = s[~np.isnan(s)]
    if np.isnan(stat_treated):
        return np.nan
    return float((1 + np.sum(s >= stat_treated)) / (len(s) + 1))


def sc_placebos(prep, S):
    """In-space placebos: each donor in turn treated as if treated, with the other donors as its pool (the treated
    unit is never a donor). Returns per-donor window stats for the primary and secondary windows."""
    X, rel, obs = prep['X'], prep['rel'], prep['obs']
    out = []
    for j in range(X.shape[1]):
        F = sc_fit(X[:, j], np.delete(X, j, axis=1), rel, obs, S)
        if F is None:
            out.append(None); continue
        out.append({tag: window_stats(F['gap'], rel, win, F['pre_rmspe'], S)
                    for tag, win in (('p', S.window_primary), ('s', S.window_secondary))})
    return out


def sc_test(Y, treated, donors, m0, S, placebos=None):
    """Synthetic control for one unit and month 0: weights, gaps, effects for both windows, one-sided rank p-values.
    `placebos` can be passed in when the donor pool is fixed and only the treated series changes (power runs)."""
    prep = sc_prepare(Y, treated, donors, m0, S)
    out = {'sc_ok': False, 'sc_n_donors': len(prep['donors'])}
    if len(prep['donors']) < MIN_DONORS:
        out['sc_reason'] = 'too few donors'
        return out
    T = sc_fit(prep['y'], prep['X'], prep['rel'], prep['obs'], S)
    if T is None:
        out['sc_reason'] = 'too few fit months'
        return out
    pl = sc_placebos(prep, S) if placebos is None else placebos
    out.update(sc_ok=True, sc_fit_n=len(T['fit_rel']), sc_fit_rel=T['fit_rel'], sc_pre_rmspe=T['pre_rmspe'],
               sc_p_min=1.0 / (len(prep['donors']) + 1),
               sc_weights={d: float(w) for d, w in zip(prep['donors'], T['w']) if w > 1e-6},
               sc_gaps=dict(zip(prep['rel'].tolist(), T['gap'].tolist())))
    for tag, win in (('p', S.window_primary), ('s', S.window_secondary)):
        st = window_stats(T['gap'], prep['rel'], win, T['pre_rmspe'], S)
        don = [x[tag] for x in pl if x is not None]
        out[f'sc_effect_{tag}'], out[f'sc_n_{tag}'], out[f'sc_ratio_{tag}'] = st['effect'], st['n'], st['ratio']
        out[f'sc_p_{tag}'] = rank_p(st['signed'], [d['signed'] for d in don])
        out[f'sc_donor_effects_{tag}'] = [d['effect'] for d in don]
    out['_placebos'] = pl
    out['_prep'] = prep
    return out


def sc_effect_only(Y, treated, donors, m0, S):
    """Synthetic-control effects without the placebo p-value (used for placebo years)."""
    prep = sc_prepare(Y, treated, donors, m0, S)
    if len(prep['donors']) < MIN_DONORS:
        return None
    T = sc_fit(prep['y'], prep['X'], prep['rel'], prep['obs'], S)
    if T is None:
        return None
    return {tag: window_stats(T['gap'], prep['rel'], win, T['pre_rmspe'], S)['effect']
            for tag, win in (('p', S.window_primary), ('s', S.window_secondary))}


def peak_lag(gaps, lag_window):
    """Relative month of the largest gap within the lag window (record: 0..+6); NaN when no gap is available."""
    best, at = -np.inf, np.nan
    for r in range(lag_window[0], lag_window[1] + 1):
        g = gaps.get(r, np.nan)
        if g is not None and not np.isnan(g) and g > best:
            best, at = g, r
    return at


def share_at_least(placebo_effects, real):
    """Share of placebo effects >= the real effect (record, placebo years and placebo categories)."""
    v = np.asarray([x for x in placebo_effects if x is not None and not np.isnan(x)], dtype=float)
    if len(v) == 0 or real is None or np.isnan(real):
        return np.nan, len(v)
    return float(np.mean(v >= real)), len(v)


# ---------------- multiple testing ----------------
def bh_q(p):
    """Benjamini-Hochberg q-values (NaN p-values stay NaN and do not count toward the number of tests)."""
    p = np.asarray(p, dtype=float)
    q = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    m = int(ok.sum())
    if m == 0:
        return q
    ps = p[ok]
    order = np.argsort(ps, kind='mergesort')
    ranked = ps[order] * m / np.arange(1, m + 1)
    qs = np.minimum(np.minimum.accumulate(ranked[::-1])[::-1], 1.0)
    out = np.empty(m)
    out[order] = qs
    q[ok] = out
    return q


# ---------------- bootstrap clustered by category ----------------
def cluster_bootstrap(df, cluster, stat, n, seed):
    """Resample whole clusters with replacement n times; stat(sub_df) is computed on each resample.
    Returns a list of n results (scalars, or Series for model coefficients)."""
    rng = np.random.default_rng(seed)
    idx = df.groupby(cluster, sort=True).indices
    groups = [idx[k] for k in sorted(idx)]
    res = []
    for _ in range(n):
        pick = rng.integers(0, len(groups), len(groups))
        rows = np.concatenate([groups[i] for i in pick])
        res.append(stat(df.iloc[rows]))
    return res


def percentile_ci(v, level=CI_LEVEL):
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return np.nan, np.nan
    a = (1 - level) / 2 * 100
    return float(np.percentile(v, a)), float(np.percentile(v, 100 - a))


def boot_p_two_sided(v):
    """Two-sided bootstrap p for 'coefficient = 0': twice the smaller tail share (NOT IN RECORD; descriptive)."""
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return np.nan
    return float(min(1.0, 2 * min(np.mean(v <= 0), np.mean(v >= 0))))


# ---------------- injected-lift power ----------------
def inject_lift(y, m0, win, lift):
    """Multiply the share by (1 + lift) in the window months, i.e. add log(1 + lift) to the log share."""
    y2 = y.copy()
    ms = rel_range(m0, win[0], win[1])
    hit = y2.index.isin(ms)
    y2[hit] = y2[hit] + np.log1p(lift)
    return y2


def power_summary(draws, S):
    """Detection rate per lift (one-sided p < S.power_alpha) and the minimum detectable effect: the smallest lift
    detected in >= S.power_rate of draws (record)."""
    d = pd.DataFrame(draws)
    d = d[d.p.notna()]
    if d.empty:
        return pd.DataFrame(columns=['lift', 'draws', 'detected', 'rate', 'mean_effect', 'true_log_lift']), np.nan
    g = d.groupby('lift').agg(draws=('p', 'size'), detected=('p', lambda p: int(np.sum(p < S.power_alpha))),
                              mean_effect=('effect', 'mean')).reset_index()
    g['rate'] = g.detected / g.draws
    g['true_log_lift'] = np.log1p(g.lift)
    ok = g[(g.rate >= S.power_rate) & (g.lift > 0)]
    return g, (float(ok.lift.min()) if len(ok) else np.nan)


# ---------------- carry-over regression ----------------
def carry_design(df, S, extra=()):
    """Design for the carry-over model (record): log(size), duration class (reference S.carry_ref_class), broad
    category fixed effects, format, classic vs modern; plus any extra columns (tone). Columns that are constant in
    the data at hand are dropped."""
    X = pd.DataFrame(index=df.index)
    X['const'] = 1.0
    X['log_size'] = np.log(df['size'].astype(float))
    for c in sorted(set(df.duration_class) - {S.carry_ref_class}):
        X[f'class_{c}'] = (df.duration_class == c).astype(float)
    for v in sorted(df.broad_id.unique())[1:]:
        X[f'broad_{v}'] = (df.broad_id == v).astype(float)
    # Seattle formats get dummies among themselves (reference: the first in sort order); LibriVox rows are 0 on all
    # of them and are separated by 'classic', so format and modern-vs-classic are not the same column.
    classic = df['classic'].astype(bool) if 'classic' in df else pd.Series(False, index=df.index)
    for v in sorted(df.loc[~classic, 'format'].unique())[1:]:
        X[f'format_{v}'] = ((df.format == v) & ~classic).astype(float)
    if classic.nunique() > 1:
        X['classic'] = classic.astype(float)
    for e in extra:
        X[e] = df[e].astype(float)
    keep = ['const'] + [c for c in X.columns if c != 'const' and X[c].nunique() > 1]
    return X[keep]


def ols(y, X):
    """OLS coefficients (least squares); NaN for a design with fewer rows than columns."""
    if len(y) <= X.shape[1]:
        return pd.Series(np.nan, index=X.columns)
    beta = np.linalg.lstsq(X.to_numpy(float), np.asarray(y, dtype=float), rcond=None)[0]
    return pd.Series(beta, index=X.columns)


def carry_fit(df, S, outcome='sc_effect_p', extra=(), cluster='node_id', n_boot=None, seed=None):
    """Carry-over model with a bootstrap clustered by category. Returns a table: coefficient, CI, bootstrap p, n."""
    d = df.dropna(subset=[outcome, 'size']).reset_index(drop=True)
    X = carry_design(d, S, extra)
    est = ols(d[outcome], X)
    n_boot = S.boot_n if n_boot is None else n_boot
    seed = S.boot_seed if seed is None else seed

    def stat(sub):
        Xs = carry_design(sub, S, extra)
        return ols(sub[outcome], Xs)
    B = pd.DataFrame(cluster_bootstrap(d, cluster, stat, n_boot, seed)).reindex(columns=X.columns)
    rows = []
    for c in X.columns:
        lo, hi = percentile_ci(B[c])
        rows.append(dict(term=c, coef=est[c], ci_low=lo, ci_high=hi, boot_p=boot_p_two_sided(B[c]),
                         boot_valid=int(B[c].notna().sum())))
    return pd.DataFrame(rows), len(d), d[cluster].nunique()


# ---------------- tone ----------------
def tone_feature(series, start, S):
    """Mean tone over the first S.tone_weeks weeks from `start` minus the median of the S.tone_baseline_weeks weeks
    before `start` (record). `series` is indexed by Monday dates.
    NOT IN RECORD: the baseline excludes the start week (as the shift 'normal level' does), and the feature needs
    MIN_FIT_SHARE of both the shift weeks and the baseline weeks to be available."""
    start = pd.Timestamp(start)
    wk = pd.date_range(start, periods=S.tone_weeks, freq='7D')
    base = pd.date_range(start - pd.Timedelta(weeks=S.tone_baseline_weeks), periods=S.tone_baseline_weeks, freq='7D')
    a = series.reindex(wk).dropna()
    b = series.reindex(base).dropna()
    if len(a) < min_fit(S.tone_weeks) or len(b) < min_fit(S.tone_baseline_weeks):
        return np.nan
    return float(a.mean() - b.median())


def blocked_weeks(spans):
    """Set of Monday dates covered by any (start, n_weeks) span."""
    out = set()
    for start, n in spans:
        out.update(pd.date_range(pd.Timestamp(start), periods=int(n), freq='7D'))
    return out


def tone_placebo_starts(weeks, blocked, S, rng):
    """Start weeks of S.tone_placebo_n random non-shift windows of S.tone_placebo_len weeks: the window may not touch
    any blocked week, and the full baseline must lie inside the series. NOT IN RECORD: drawn without replacement
    when enough windows exist, otherwise with replacement."""
    weeks = pd.DatetimeIndex(sorted(weeks))
    if len(weeks) == 0:
        return []
    first, last = weeks[0], weeks[-1]
    L = S.tone_placebo_len
    cand = []
    for w in weeks:
        if w - pd.Timedelta(weeks=S.tone_baseline_weeks) < first or w + pd.Timedelta(weeks=L - 1) > last:
            continue
        if any(x in blocked for x in pd.date_range(w, periods=L, freq='7D')):
            continue
        cand.append(w)
    if not cand:
        return []
    n = S.tone_placebo_n
    idx = rng.choice(len(cand), size=n, replace=len(cand) < n)
    return [cand[i] for i in idx]
