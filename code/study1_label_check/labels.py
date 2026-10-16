"""Outcome labels for the Study 1 label-window check (record 2026-10-13 plus addendum a).

Month 0 is the release month; month a counts from it. Panels are arrays of shape (n_titles, 12)
holding views in months 1..12 and the calendar month of year (0..11) of each cell.
L0 and L2 need no fitting. L3 and L4 are fitted on training titles only (f, g, omega, theta,
sigma_beta) and then applied to any title using that title's own views only.
Choices the record leaves open are marked '# NOT IN RECORD:' and listed in README.md.
"""
import hashlib, json, re
import numpy as np
from scipy.optimize import brentq

AGES = np.arange(1, 13)
LOGA = np.log(AGES) - np.log(AGES).mean()          # l(a), as in the addendum
WINDOW_END = {'L0': 7, 'L2': 14, 'L3': 12, 'L4': 12}   # last month after release each label needs

# NOT IN RECORD: bounds that keep the penalised fits finite for titles with no or almost no views
ALPHA_MIN, ALPHA_MAX, BETA_CLIP = -6.0, 20.0, 5.0
# NOT IN RECORD: titles with at least this many views in months 1..12 inform theta and sigma_beta
MIN_TOTAL_SIGMA = 100
# NOT IN RECORD: floor for sigma_beta if the method-of-moments estimate is not positive
SIGMA_FLOOR = 0.05
THETA_MAX = 1e4

# ---------------------------------------------------------------- record check
def sha256_file(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()

def expected_hash_from_readme(readme_path, marker='Study 1 label-window check'):
    """The SHA-256 listed under the Study 1 heading in prereg/README.md."""
    with open(readme_path, encoding='utf-8') as fh:
        txt = fh.read()
    sec = txt.split(marker, 1)[1]
    return re.search(r'SHA-256[^`]*`([0-9a-f]{64})`', sec).group(1)

def verify_record(path, expected):
    got = sha256_file(path)
    if got != expected:
        raise RuntimeError(f'record {path} has SHA-256 {got}, expected {expected}')
    return got

# ---------------------------------------------------------------- panels
def month_index(period):
    return period.year * 12 + period.month - 1

def build_panel(views, rel_periods):
    """views: list of dicts {'YYYYMM': n}; rel_periods: pandas Periods (month 0).
    Returns counts (n,24) for months 1..24 (NaN where the month is past the data end is not
    needed here because callers only use complete windows), and moy (n,12) for months 1..12."""
    n = len(views)
    counts = np.zeros((n, 14))
    moy = np.zeros((n, 12), dtype=int)
    for i, (v, p) in enumerate(zip(views, rel_periods)):
        for a in range(1, 15):
            counts[i, a - 1] = v.get((p + a).strftime('%Y%m'), 0)
        for a in range(1, 13):
            moy[i, a - 1] = (p + a).month - 1
    return counts, moy

# ---------------------------------------------------------------- L0, L2
def label_L0(counts14):   # months 2..7
    return np.log1p(counts14[:, 1:7]).mean(axis=1)

def label_L2(counts14):   # months 9..14
    return np.log1p(counts14[:, 8:14]).mean(axis=1)

# ---------------------------------------------------------------- L3
def _backfit_fg(Y, moy, n_iter=60):
    """Two-way additive fit Y[i,a] = alpha_i + f(a) + g(moy) by backfitting (unweighted)."""
    n = Y.shape[0]
    f = np.zeros(12); g = np.zeros(12)
    for _ in range(n_iter):
        R = Y - f[None, :] - g[moy]
        alpha = R.mean(axis=1)
        R = Y - alpha[:, None] - g[moy]
        f_new = R.mean(axis=0)
        R = Y - alpha[:, None] - f_new[None, :]
        g_new = np.array([R[moy == k].mean() if (moy == k).any() else 0.0 for k in range(12)])
        d = np.abs(f_new - f).max() + np.abs(g_new - g).max(); f, g = f_new, g_new
        if d < 1e-9: break
    g = g - g.mean(); f = f - f.mean()
    return f, g

def fit_L3(counts, moy):
    """counts (n,12) views in months 1..12 of TRAINING titles."""
    Y = np.log1p(counts)
    f, g = _backfit_fg(Y, moy)
    alpha = (Y - f[None, :] - g[moy]).mean(axis=1)
    res = Y - alpha[:, None] - f[None, :] - g[moy]
    # NOT IN RECORD: residual variance by age taken about zero with n-1 divisor (title effect removed)
    var_a = (res ** 2).sum(axis=0) / max(len(Y) - 1, 1)
    return dict(f=f, g=g, omega=1.0 / np.maximum(var_a, 1e-6))

def apply_L3(p, counts, moy):
    Y = np.log1p(counts) - p['f'][None, :] - p['g'][moy]
    w = p['omega'][None, :]
    return (w * Y).sum(axis=1) / w.sum()

# ---------------------------------------------------------------- L4
def _nb_ll(v, mu, theta):
    from scipy.special import gammaln
    return (gammaln(v + theta) - gammaln(theta) - gammaln(v + 1) + theta * np.log(theta / (theta + mu))
            + v * np.log(mu / (theta + mu)))

def fit_titles(counts, offset, theta, sigma_beta=None, n_iter=60, alpha0=None):
    """Penalised ML of (alpha_i, beta_i) for each row by Fisher scoring, vectorised over titles.
    log mu[i,a] = alpha_i + offset[i,a] + beta_i * LOGA[a]; penalty (beta_i/sigma_beta)^2 / 2.
    sigma_beta=None means no penalty (a tiny ridge keeps the 2x2 information invertible).
    Returns alpha, beta, var_beta (from the inverse information)."""
    n = counts.shape[0]
    alpha = np.full(n, np.log(counts.mean(axis=1) + 0.5)) if alpha0 is None else alpha0.copy()
    alpha = np.clip(alpha, ALPHA_MIN, ALPHA_MAX); beta = np.zeros(n)
    pen = 1e-8 if sigma_beta is None else 1.0 / sigma_beta ** 2
    for _ in range(n_iter):
        eta = np.clip(alpha[:, None] + offset + beta[:, None] * LOGA[None, :], -30, 30)
        mu = np.exp(eta); w = mu / (1.0 + mu / theta); r = (counts - mu) / (1.0 + mu / theta)
        s0 = r.sum(1); s1 = (r * LOGA).sum(1) - pen * beta
        i00 = w.sum(1) + 1e-8; i01 = (w * LOGA).sum(1); i11 = (w * LOGA ** 2).sum(1) + pen + 1e-8
        det = i00 * i11 - i01 ** 2
        da = (i11 * s0 - i01 * s1) / det; db = (-i01 * s0 + i00 * s1) / det
        da = np.clip(da, -2, 2); db = np.clip(db, -2, 2)
        alpha = np.clip(alpha + da, ALPHA_MIN, ALPHA_MAX); beta = np.clip(beta + db, -BETA_CLIP, BETA_CLIP)
        if max(np.abs(da).max(), np.abs(db).max()) < 1e-7: break
    eta = np.clip(alpha[:, None] + offset + beta[:, None] * LOGA[None, :], -30, 30)
    mu = np.exp(eta); w = mu / (1.0 + mu / theta)
    i00 = w.sum(1) + 1e-8; i01 = (w * LOGA).sum(1); i11 = (w * LOGA ** 2).sum(1) + pen + 1e-8
    var_beta = i00 / (i00 * i11 - i01 ** 2)
    return alpha, beta, var_beta

def _fit_common_curve(counts, moy, theta, f, g, n_outer=40):
    """f(a), g(month of year) by NB IRLS with a free title level alpha_i (beta_i = 0)."""
    n = counts.shape[0]; N = n * 12
    A = np.tile(np.eye(12), (n, 1))                     # age one-hot per cell (row-major cells)
    M = np.eye(12)[moy.reshape(-1)]
    X = np.hstack([A, M]); v = counts.reshape(-1)
    alpha = np.log(counts.mean(1) + 0.5); ll_old = -np.inf
    for _ in range(n_outer):
        for _ in range(3):   # title levels
            eta = alpha[:, None] + f[None, :] + g[moy]
            mu = np.exp(np.clip(eta, -30, 30)); w = mu / (1 + mu / theta); r = (counts - mu) / (1 + mu / theta)
            alpha = np.clip(alpha + np.clip(r.sum(1) / (w.sum(1) + 1e-8), -2, 2), ALPHA_MIN, ALPHA_MAX)
        for _ in range(2):   # curve
            eta = alpha[:, None] + f[None, :] + g[moy]
            mu = np.exp(np.clip(eta, -30, 30)); w = (mu / (1 + mu / theta)).reshape(-1)
            r = ((counts - mu) / (1 + mu / theta)).reshape(-1)
            XtWX = X.T @ (X * w[:, None]) + 1e-6 * np.eye(24)
            step = np.linalg.solve(XtWX, X.T @ r)
            step = np.clip(step, -1, 1)
            f = f + step[:12]; g = g + step[12:]
        eta = alpha[:, None] + f[None, :] + g[moy]
        ll = _nb_ll(counts, np.exp(np.clip(eta, -30, 30)), theta).sum()
        if abs(ll - ll_old) < 1e-6 * abs(ll) + 1e-6: break
        ll_old = ll
    # normalise: sum g = 0, sum f = 0 (the level moves into alpha, which is refitted later anyway)
    f = f + g.mean(); g = g - g.mean(); f = f - f.mean()
    return f, g

def _theta_pearson(counts, mu, df):
    """Pearson moment estimator: sum (v-mu)^2 / (mu + mu^2/theta) = df."""
    def h(lt):
        th = np.exp(lt); return (((counts - mu) ** 2) / (mu + mu ** 2 / th)).sum() - df
    lo, hi = np.log(0.02), np.log(THETA_MAX)
    if h(hi) < 0: return THETA_MAX          # no overdispersion left
    if h(lo) > 0: return 0.02
    return float(np.exp(brentq(h, lo, hi)))

def fit_L4(counts, moy, n_rounds=4):
    """Estimate f, g, theta, sigma_beta on TRAINING titles only. counts (n,12)."""
    keep = counts.sum(1) > 0                     # NOT IN RECORD: all-zero titles carry no information about f, g
    C, Mo = counts[keep], moy[keep]
    f = np.zeros(12); g = np.zeros(12); theta = 1.0; sigma = 0.3
    big = C.sum(1) >= MIN_TOTAL_SIGMA
    if big.sum() < 20: raise RuntimeError('too few training titles with enough views')
    for _ in range(n_rounds):
        f, g = _fit_common_curve(C, Mo, theta, f, g)
        off = f[None, :] + g[Mo]
        a, b, vb = fit_titles(C[big], off[big], theta, None)
        mu = np.exp(np.clip(a[:, None] + off[big] + b[:, None] * LOGA[None, :], -30, 30))
        # NOT IN RECORD: theta from the Pearson moment estimator with degrees of freedom
        # (cells - 2 per title - 24 curve terms) instead of raw ML, which is biased by the title-level fits.
        df = big.sum() * 12 - 2 * big.sum() - 22
        theta = _theta_pearson(C[big], mu, df)
        # recompute sampling variance of the slopes with the new theta, then method of moments
        a, b, vb = fit_titles(C[big], off[big], theta, None, alpha0=a)
        s2 = b.var(ddof=1) - vb.mean()
        sigma = float(np.sqrt(s2)) if s2 > SIGMA_FLOOR ** 2 else SIGMA_FLOOR
    return dict(f=f, g=g, theta=theta, sigma_beta=sigma)

def apply_L4(p, counts, moy):
    """Per-title fit with f, g, theta fixed and the slope penalty. Returns dict with alpha, beta,
    mu (n,12) and launch strength. Uses only that title's own counts."""
    off = p['f'][None, :] + p['g'][moy]
    alpha, beta, _ = fit_titles(counts, off, p['theta'], p['sigma_beta'])
    mu = np.exp(np.clip(alpha[:, None] + off + beta[:, None] * LOGA[None, :], -30, 30))
    # NOT IN RECORD: +0.5 on both counts so log() is defined when months 1-2 have no views
    launch = np.log(counts[:, :2].sum(1) + 0.5) - np.log(mu[:, :2].sum(1) + 0.5)
    return dict(alpha=alpha, beta=beta, mu=mu, launch=launch)

# ---------------------------------------------------------------- one walk-forward step
def step_labels(counts14, moy, train_idx):
    """All four labels for every title; L3 and L4 parameters come from counts14[train_idx] only.
    counts14 (n,14): views in months 1..14; moy (n,12)."""
    c12 = counts14[:, :12]
    p3 = fit_L3(c12[train_idx], moy[train_idx])
    p4 = fit_L4(c12[train_idx], moy[train_idx])
    r4 = apply_L4(p4, c12, moy)
    return dict(L0=label_L0(counts14), L2=label_L2(counts14), L3=apply_L3(p3, c12, moy),
                L4=r4['alpha'], launch=r4['launch'], beta=r4['beta'], p3=p3, p4=p4)
