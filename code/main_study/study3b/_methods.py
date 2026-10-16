# Study 3b methods as pure functions (numpy / pandas / scipy only). The count event study of the record
# (study3b_settings, count_event_study): a quasi-Poisson GLM, joint across the Seattle formats, on the 24 fit months
# ending at month -7:  log E[Y_{c,f,t}] = log N_{f,t} + alpha_f + beta_f * t + month-of-year effects,
# dispersion phi = Pearson chi-square / residual df; mu is predicted for the effect windows;
# tau = log(sum Y / sum mu) and z = tau / sqrt(phi / sum mu), also per format.
# Every window, threshold and seed comes from the parsed settings S. Choices the record does not make are marked
# '# NOT IN RECORD:'. All categories of a level share one design matrix at a given month 0 and format set, so the
# Poisson fits are done in batches (iteratively reweighted least squares for many categories at once).
import math
import numpy as np, pandas as pd
import _s3

# re-used Study 3 pure helpers (called inside the process only, never sent to joblib workers)
bh_q = _s3.methods.bh_q
percentile_ci = _s3.methods.percentile_ci
boot_p_two_sided = _s3.methods.boot_p_two_sided
rel_range = _s3.methods.rel_range
tone_feature = _s3.methods.tone_feature
blocked_weeks = _s3.methods.blocked_weeks
tone_placebo_starts = _s3.methods.tone_placebo_starts
MIN_FIT_SHARE = _s3.methods.MIN_FIT_SHARE        # NOT IN RECORD (addendum c of Study 3): a fit needs 75% of its window's months
EPS = 1e-12
WINDOWS_REL = (-6, 5)                           # months predicted: the pre-trend months -6..-1 and the windows 0..+5


def min_fit(n):
    return math.ceil(MIN_FIT_SHARE * n)


class Counts:
    """Dense count data of one level. Months are integers mi = year * 12 + month - 1 on the grid mi0 .. mi0 + T - 1.
      ids   category ids (length K)
      Y     {format: (K, T) weighted checkouts; NaN where the month is not usable (missing, partial, closure, no rows);
              a usable month with no checkout is 0}
      N     {format: (T,) all checkouts of the format that month (the exposure); NaN where not usable}
      ok    {format: (T,) bool, month usable}"""

    def __init__(self, mi0, ids, Y, N, ok):
        self.mi0, self.ids, self.Y, self.N, self.ok = int(mi0), np.asarray(ids), Y, N, ok
        self.formats = tuple(Y)
        self.T = next(iter(Y.values())).shape[1]
        self.index = {c: i for i, c in enumerate(self.ids)}

    def subset(self, rows):
        return Counts(self.mi0, self.ids[rows], {f: y[rows] for f, y in self.Y.items()}, self.N, self.ok)


# ---------------- Poisson IRLS in batches ----------------
def poisson_irls(X, Y, off, maxit=60, tol=1e-10, chunk=1500):
    """Poisson GLM with log link and offset for many response rows at once. X (n, p) and the offset (n,) are shared;
    Y is (K, n). Returns beta (K, p), mu (K, n) and a converged flag per row. Plain IRLS with step halving."""
    K, n = Y.shape
    p = X.shape[1]
    beta = np.zeros((K, p)); mu = np.zeros((K, n)); conv = np.zeros(K, bool)
    E = np.exp(off)
    for a in range(0, K, chunk):
        y = Y[a:a + chunk]
        k = len(y)
        rate = y.sum(1, keepdims=True) / E.sum()
        m = (y + rate * E) / 2.0
        b = np.zeros((k, p))
        dev = _deviance(y, m)
        done = np.zeros(k, bool)
        for it in range(maxit):
            z = np.log(m) - off + (y - m) / m
            A = np.einsum('np,kn,nq->kpq', X, m, X)
            A += 1e-9 * np.eye(p)[None] * np.maximum(A.diagonal(axis1=1, axis2=2).max(1), 1.0)[:, None, None]
            r = np.einsum('np,kn->kp', X, m * z)
            bn = np.linalg.solve(A, r[..., None])[..., 0]
            for _ in range(6):                                      # step halving where the deviance got worse
                eta = np.clip(bn @ X.T + off, -40, 40)
                mn = np.exp(eta)
                dn = _deviance(y, mn)
                bad = dn > dev * (1 + 1e-9) + 1e-9
                if not bad.any():
                    break
                bn = np.where(bad[:, None], (b + bn) / 2.0, bn)
            conv_now = np.abs(dn - dev) <= tol * (np.abs(dev) + 0.1)
            b, m, dev = bn, mn, dn
            done = conv_now
            if done.all():
                break
        beta[a:a + k], mu[a:a + k], conv[a:a + k] = b, m, done
    return beta, mu, conv


def _deviance(y, mu):
    with np.errstate(divide='ignore', invalid='ignore'):
        t = np.where(y > 0, y * np.log(np.where(y > 0, y, 1.0) / mu), 0.0)
    return 2.0 * np.sum(t - (y - mu), axis=1)


def pearson_phi(Y, mu, df):
    """Pearson chi-square / residual df (record)."""
    return np.sum((Y - mu) ** 2 / np.maximum(mu, 1e-12), axis=1) / df


# ---------------- design ----------------
def _design(fmt_idx, rel, cal, cals, nf):
    """Rows: (format index, relative month, calendar month). Columns: alpha_f (one per format), beta_f x t (one per format,
    t in years centred on the middle of the fit window), then dummies for the calendar months in `cals` except the first
    (the intercepts absorb the reference month)."""
    n = len(rel)
    X = np.zeros((n, 2 * nf + max(len(cals) - 1, 0)))
    t = (rel + 18.5) / 12.0
    X[np.arange(n), fmt_idx] = 1.0
    X[np.arange(n), nf + fmt_idx] = t
    for j, c in enumerate(cals[1:]):
        X[:, 2 * nf + j] = cal == c
    return X


def tau_z(sum_y, sum_mu, phi):
    """tau = log(sum Y / sum mu); z = tau / sqrt(phi / sum mu) (record). sum Y = 0 gives -inf (kept for ranking; callers
    drop it from means). NaN when sum mu <= 0 or the inputs are missing."""
    sum_y, sum_mu, phi = (np.asarray(a, dtype=float) for a in (sum_y, sum_mu, phi))
    with np.errstate(divide='ignore', invalid='ignore'):
        tau = np.where(sum_mu > 0, np.log(sum_y / sum_mu), np.nan)
        z = tau / np.sqrt(np.maximum(phi, EPS) / sum_mu)
    return tau, z


def fit_months(m0, S):
    """The 24 months ending at month -7 (record): relative months -30..-7."""
    return rel_range(m0, S.es_fit_end - S.es_fit_len + 1, S.es_fit_end)


def feasibility(C, m0, S, rows=None):
    """Structure of the fit window at month 0 = m0 (no model is fitted). Per format: the fit months that are usable and,
    per category, the number of nonzero months among them. A format enters a category's joint model when it has >= 75% of
    the 24 fit months usable and >= S.feas_min_nonzero nonzero months (NOT IN RECORD: the record's rule per format, plus the
    Study 3 coverage rule); the category is feasible when at least one format enters (record: nonzero in at least 12 of the
    24 fit months in at least one format). Returns a dict: feasible (K,), code (K,) bit i = i-th format of C enters,
    elig (K, n_formats), nonzero {format: (K,)}, avail {format: (24,) bool}, usable_formats, fm, fi, inside."""
    rows = np.arange(len(C.ids)) if rows is None else np.asarray(rows)
    K = len(rows)
    fm = fit_months(m0, S)
    fi = fm - C.mi0
    inside = (fi >= 0) & (fi < C.T)
    avail, nonzero = {}, {}
    for f in C.formats:
        a = np.zeros(len(fm), bool)
        a[inside] = C.ok[f][fi[inside]]
        avail[f] = a
        yy = np.zeros((K, len(fm)))
        yy[:, inside] = np.nan_to_num(C.Y[f][rows][:, fi[inside]], nan=0.0)
        nonzero[f] = ((yy > 0) & a[None, :]).sum(1)
    usable_f = [f for f in C.formats if avail[f].sum() >= min_fit(len(fm))]
    elig = np.column_stack([nonzero[f] >= S.feas_min_nonzero if f in usable_f else np.zeros(K, bool) for f in C.formats])
    code = (elig * (1 << np.arange(len(C.formats)))).sum(1)
    return dict(feasible=elig.any(1), code=code, elig=elig, nonzero=nonzero, avail=avail, usable_formats=usable_f, fm=fm, fi=fi,
                inside=inside, rows=rows)


def event_study(C, m0, S, rows=None, detail=False):
    """Count event study for the categories `rows` (default all) of Counts C at month 0 = m0.
    Per category: a format enters the joint model when it has >= S.feas_min_nonzero nonzero months among its available
    fit months and the format has >= 75% of the fit window available (see feasibility); the category is feasible when at
    least one format enters. A window needs S.min_window_months available months, and a calendar month never seen in the
    fit gets no prediction (its Y is then left out of the window sums too, so Y and mu always cover the same
    format-months).
    Returns a dict of arrays (length K):
      feasible, n_formats, formats (code: bit i = i-th format of C), phi, df, converged,
      for w in pre, p, s: sumy_w, summu_w, tau_w, z_w, nm_w (available months in the window) and per format
      sumy_w_<f>, summu_w_<f>, tau_w_<f>, z_w_<f>.
    With detail=True also det_rel (relative months -6..+5), det_y and det_mu (K, 12): observed and expected summed over the
    formats of the model, month by month (descriptive, for the control reports)."""
    fz = feasibility(C, m0, S, rows)
    rows, K, fm, fi, avail = fz['rows'], len(fz['rows']), fz['fm'], fz['fi'], fz['avail']
    out = {'feasible': fz['feasible'].copy(), 'n_formats': fz['elig'].sum(1), 'formats': fz['code'],
           'phi': np.full(K, np.nan), 'df': np.full(K, np.nan), 'converged': np.zeros(K, bool)}
    wins = {'pre': S.es_pretrend, 'p': S.window_primary, 's': S.window_secondary}
    for w in wins:
        for key in ('sumy', 'summu', 'tau', 'z'):
            out[f'{key}_{w}'] = np.full(K, np.nan)
            for f in C.formats:
                out[f'{key}_{w}_{f}'] = np.full(K, np.nan)
        out[f'nm_{w}'] = np.zeros(K, int)
    code = fz['code']
    pre_rel = np.arange(WINDOWS_REL[0], WINDOWS_REL[1] + 1)
    if detail:
        out['det_rel'] = pre_rel
        out['det_y'] = np.full((K, len(pre_rel)), np.nan); out['det_mu'] = np.full((K, len(pre_rel)), np.nan)
    pm = m0 + pre_rel
    pi = pm - C.mi0
    pin = (pi >= 0) & (pi < C.T)
    for c in np.unique(code[code > 0]):
        sel = np.flatnonzero(code == c)
        fl = [f for j, f in enumerate(C.formats) if c >> j & 1]
        nf = len(fl)
        # fit rows
        fmt_idx, rel, cal, off, cols = [], [], [], [], []
        for k, f in enumerate(fl):
            a = np.flatnonzero(avail[f])
            fmt_idx += [k] * len(a); rel += (fm[a] - m0).tolist(); cal += (fm[a] % 12).tolist()
            off += np.log(C.N[f][fi[a]]).tolist(); cols += [(f, ai) for ai in fi[a]]
        fmt_idx, rel, cal, off = (np.asarray(x) for x in (fmt_idx, rel, cal, off))
        cals = np.unique(cal)
        X = _design(fmt_idx, rel.astype(float), cal, cals, nf)
        n, p = X.shape
        if n - p < 1 or np.linalg.matrix_rank(X) < p:
            out['feasible'][sel] = False
            continue
        Yfit = np.stack([C.Y[f][rows[sel], ai] for f, ai in cols], axis=1)
        beta, mu, conv = poisson_irls(X, Yfit, off)
        phi = pearson_phi(Yfit, mu, n - p)
        out['phi'][sel], out['df'][sel], out['converged'][sel] = phi, n - p, conv
        # prediction rows: every format of the model x month -6..+5 that is usable and has a known calendar month
        pf, pr, pc, po, pidx = [], [], [], [], []
        for k, f in enumerate(fl):
            ok_m = pin.copy()
            ok_m[pin] = C.ok[f][pi[pin]]
            ok_m &= np.isin(pm % 12, cals)
            a = np.flatnonzero(ok_m)
            pf += [k] * len(a); pr += pre_rel[a].tolist(); pc += (pm[a] % 12).tolist()
            po += np.log(C.N[f][pi[a]]).tolist(); pidx += [(f, ai) for ai in pi[a]]
        pf, pr, pc, po = (np.asarray(x) for x in (pf, pr, pc, po))
        Xp = _design(pf, pr.astype(float), pc, cals, nf)
        mup = np.exp(np.clip(beta @ Xp.T + po, -40, 40))                       # (k, n_pred)
        yp = np.stack([C.Y[f][rows[sel], ai] for f, ai in pidx], axis=1)
        if detail:
            for j, r_ in enumerate(pre_rel):
                mm = pr == r_
                if mm.any():
                    out['det_y'][sel, j], out['det_mu'][sel, j] = yp[:, mm].sum(1), mup[:, mm].sum(1)
        for w, (a, b) in wins.items():
            m = (pr >= a) & (pr <= b)
            out[f'nm_{w}'][sel] = len(np.unique(pr[m]))
            sy, sm = yp[:, m].sum(1), mup[:, m].sum(1)
            out[f'sumy_{w}'][sel], out[f'summu_{w}'][sel] = sy, sm
            out[f'tau_{w}'][sel], out[f'z_{w}'][sel] = tau_z(sy, sm, phi)
            for k, f in enumerate(fl):
                mf = m & (pf == k)
                if mf.any():
                    sy, sm = yp[:, mf].sum(1), mup[:, mf].sum(1)
                    out[f'sumy_{w}_{f}'][sel], out[f'summu_{w}_{f}'][sel] = sy, sm
                    out[f'tau_{w}_{f}'][sel], out[f'z_{w}_{f}'][sel] = tau_z(sy, sm, phi)
    for w, (a, b) in wins.items():
        if w == 'pre':
            continue
        short = out[f'nm_{w}'] < S.min_window_months          # addendum b analogue: a window with < 2 available months is not estimated
        for key in ('sumy', 'summu', 'tau', 'z'):
            out[f'{key}_{w}'][short] = np.nan
    return out


def too_sparse(summu_p, S):
    """Record: a test with fewer than 5 expected weighted checkouts over the primary window is too sparse."""
    return np.asarray(summu_p) < S.sparse_below


# ---------------- rank p-values ----------------
def rank_p(z_treated, z_placebos):
    """One-sided rank p of the treated z among treated and placebo z values: (1 + number of placebo z >= treated z) /
    (number of placebos + 1) (record). Ties count against the treated category. NaN placebos are left out."""
    s = np.asarray(z_placebos, dtype=float)
    s = s[~np.isnan(s)]
    if z_treated is None or np.isnan(z_treated):
        return np.nan
    return float((1 + np.sum(s >= z_treated)) / (len(s) + 1))


def rank_p_many(z_treated, z_placebos):
    """rank_p for several treated z values against the same placebos (sorted once)."""
    s = np.sort(np.asarray(z_placebos, dtype=float)[~np.isnan(z_placebos)])
    z = np.asarray(z_treated, dtype=float)
    ge = len(s) - np.searchsorted(s, z, side='left')
    return np.where(np.isnan(z), np.nan, (1 + ge) / (len(s) + 1))


def share_at_least(placebo_z, real_z):
    """Share of placebo z at or above the treated z (record, placebo years)."""
    v = np.asarray([x for x in placebo_z if x is not None and not np.isnan(x)], dtype=float)
    if len(v) == 0 or real_z is None or np.isnan(real_z):
        return np.nan, len(v)
    return float(np.mean(v >= real_z)), len(v)


# ---------------- power by injected lifts ----------------
def lifted_z(z, summu_p, phi, sumy_p, lift):
    """z after multiplying the observed Y by (1 + lift) in months 0..+2 (the fit months are untouched, so mu and phi do
    not change): z + log(1 + lift) / sqrt(phi / sum mu); a category with sum Y = 0 stays at -inf."""
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(np.asarray(sumy_p) > 0, np.asarray(z) + np.log1p(lift) / np.sqrt(np.maximum(phi, EPS) / summu_p), -np.inf)


def size_bands(summu_p, n_bands=4):
    """Band edges from the quartiles of sum mu (record): returns the edges (n_bands + 1) and a band index per value."""
    v = np.asarray(summu_p, dtype=float)
    v = v[~np.isnan(v)]
    edges = np.quantile(v, np.linspace(0, 1, n_bands + 1))
    return edges


def band_of(summu_p, edges):
    b = np.searchsorted(edges[1:-1], np.asarray(summu_p, dtype=float), side='right')
    return np.where(np.isnan(summu_p), -1, b)


def power_summary(draws, S):
    """Detection rate per lift (one-sided rank p < S.power_alpha) and the minimum detectable lift: the smallest lift
    detected in >= S.power_rate of draws (record). `draws` is a DataFrame with columns lift and p."""
    d = pd.DataFrame(draws)
    d = d[d.p.notna()]
    if d.empty:
        return pd.DataFrame(columns=['lift', 'draws', 'detected', 'rate']), np.nan
    g = d.groupby('lift').agg(draws=('p', 'size'), detected=('p', lambda p: int(np.sum(p < S.power_alpha)))).reset_index()
    g['rate'] = g.detected / g.draws
    ok = g[(g.rate >= S.power_rate) & (g.lift > 0)]
    return g, (float(ok.lift.min()) if len(ok) else np.nan)


# ---------------- pooled means with a bootstrap clustered by category ----------------
def cluster_boot_mean(values, clusters, n, seed, level=0.95):
    """Mean of `values` with a bootstrap that resamples whole clusters (categories) with replacement n times.
    Returns mean, low, high (percentile interval) and the share of resamples at or below 0 (descriptive)."""
    v = np.asarray(values, dtype=float)
    keep = np.isfinite(v)
    v, cl = v[keep], np.asarray(clusters)[keep]
    if len(v) == 0:
        return dict(mean=np.nan, low=np.nan, high=np.nan, n=0, clusters=0)
    codes, uniq = pd.factorize(cl, sort=True)
    G = len(uniq)
    sums = np.bincount(codes, weights=v, minlength=G)
    cnt = np.bincount(codes, minlength=G).astype(float)
    out = dict(mean=float(v.mean()), n=int(len(v)), clusters=int(G))
    if G < 2:
        out.update(low=np.nan, high=np.nan)
        return out
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, G, size=(n, G))
    bm = sums[pick].sum(1) / cnt[pick].sum(1)
    out['low'], out['high'] = percentile_ci(bm, level)
    out['boot_p'] = boot_p_two_sided(bm)
    return out


# ---------------- carry-over regression with tau as the outcome ----------------
def carry_design(df, S, extra=()):
    """Design of the carry-over regression (record: the Study 3 regression): log(size), duration class (reference
    S.carry_ref_class), broad category fixed effects, plus any extra columns. There is no format term because the
    count model is joint across formats. Columns constant in the data at hand are dropped."""
    X = pd.DataFrame(index=df.index)
    X['const'] = 1.0
    X['log_size'] = np.log(df['size'].astype(float))
    for c in sorted(set(df.duration_class) - {S.carry_ref_class}):
        X[f'class_{c}'] = (df.duration_class == c).astype(float)
    for v in sorted(df.broad_id.unique())[1:]:
        X[f'broad_{v}'] = (df.broad_id == v).astype(float)
    for e in extra:
        X[e] = df[e].astype(float)
    keep = ['const'] + [c for c in X.columns if c != 'const' and X[c].nunique() > 1]
    return X[keep]


def ols_fit(y, X):
    """Least-squares coefficients (NaN when there are not more rows than columns)."""
    if len(y) <= X.shape[1]:
        return pd.Series(np.nan, index=X.columns)
    return pd.Series(np.linalg.lstsq(X.to_numpy(float), np.asarray(y, dtype=float), rcond=None)[0], index=X.columns)


def carry_fit(df, S, outcome='tau_p', extra=(), cluster='node_id', n_boot=None, seed=None, design=None):
    """OLS of `outcome` on the carry-over design with a bootstrap clustered by category (record). Returns a table
    (term, coef, ci_low, ci_high, boot_p, boot_valid), the number of tests and of categories. A resample that makes a
    column constant gives NaN for that column. `design` may be a function (df) -> DataFrame to use another design."""
    d = df.dropna(subset=[outcome, 'size']).replace([np.inf, -np.inf], np.nan).dropna(subset=[outcome]).reset_index(drop=True)
    make = design or (lambda x: carry_design(x, S, extra))
    X = make(d)
    est = ols_fit(d[outcome], X)
    n_boot = S.boot_n if n_boot is None else n_boot
    seed = S.boot_seed if seed is None else seed
    cols = list(X.columns)
    Xa, ya = X.to_numpy(float), d[outcome].to_numpy(float)
    codes, uniq = pd.factorize(d[cluster], sort=True)
    groups = [np.flatnonzero(codes == g) for g in range(len(uniq))]
    rng = np.random.default_rng(seed)
    B = np.full((n_boot, len(cols)), np.nan)
    for b in range(n_boot):
        pick = rng.integers(0, len(groups), len(groups))
        r = np.concatenate([groups[i] for i in pick])
        xs, ys = Xa[r], ya[r]
        keep = np.flatnonzero((np.ptp(xs, axis=0) > 0) | (np.arange(len(cols)) == 0))
        if len(r) <= len(keep):
            continue
        B[b, keep] = np.linalg.lstsq(xs[:, keep], ys, rcond=None)[0]
    rows = []
    for j, c in enumerate(cols):
        lo, hi = percentile_ci(B[:, j])
        rows.append(dict(term=c, coef=est[c], ci_low=lo, ci_high=hi, boot_p=boot_p_two_sided(B[:, j]),
                         boot_valid=int(np.isfinite(B[:, j]).sum())))
    return pd.DataFrame(rows), len(d), d[cluster].nunique()


# ---------------- sentiment ----------------
def sentiment_features(series, start, S):
    """The record's five features for one shift. `series` is a frame indexed by Monday dates with columns tone, tone_pos,
    tone_neg. delta tone = mean tone of the first S.tone_weeks weeks minus the median of the S.tone_baseline_weeks weeks
    before the start (Study 3 function); delta positive and delta negative the same; delta intensity = delta of
    (positive + negative); negative shift = 1 if delta tone < 0 (NaN when delta tone is missing)."""
    dt = tone_feature(series['tone'], start, S)
    dp = tone_feature(series['tone_pos'], start, S)
    dn = tone_feature(series['tone_neg'], start, S)
    di = tone_feature(series['tone_pos'] + series['tone_neg'], start, S)
    return dict(d_tone=dt, d_pos=dp, d_neg=dn, d_intensity=di, neg_shift=(np.nan if np.isnan(dt) else float(dt < 0)))


def placebo_two_sided(real, placebo_coefs):
    """Two-sided placebo p: share of placebo coefficients with |coef| >= |real| (record: comparison with 200 placebo
    windows per category, two-sided; this reading, with the Study 3 tone test, is NOT IN RECORD)."""
    c = np.asarray(placebo_coefs, dtype=float)
    c = c[np.isfinite(c)]
    if len(c) == 0 or not np.isfinite(real):
        return np.nan
    return float(np.mean(np.abs(c) >= abs(real)))
