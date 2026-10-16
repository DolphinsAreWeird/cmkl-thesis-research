"""Study 2R step 11: simulation tests of the outcome pipeline (no real data). (1) an injected lift is recovered, (2) at lift 0 about 5% of
tests reach one-sided p < 0.05 and p is about uniform, (3) the bootstrap slope, difference and Hansen threshold recover known truths.
Report: data/reports/study2r_sim_tests.md. Exit code 1 if any check fails."""
import sys
from _lib2r import *
from scipy import stats

mi0, T = 2012 * 12, 15 * 12
rng0 = np.random.default_rng(7)


def sim_counts(K, lift, n_treated, seed, phi=3.0):
    rng = np.random.default_rng(seed)
    fm = ('print', 'ebook')
    ids = np.arange(1, K + 1)
    cal = (mi0 + np.arange(T)) % 12
    N = {'print': 3e5 * (1 + 0.15 * np.sin(2 * np.pi * np.arange(T) / 12)), 'ebook': 1e5 * (1 + 0.5 * np.arange(T) / T)}
    ok = {f: np.ones(T, bool) for f in fm}
    for f in fm:
        ok[f][[40, 41, 100]] = False
    share = np.exp(rng.normal(np.log(4e-4), 0.7, K))
    gam = rng.normal(0, 0.15, (K, 12)); beta = rng.normal(0, 0.1, K)
    t_year = (np.arange(T) - 60) / 12.0
    treat_m0 = np.full(K, -1)
    tr = rng.choice(K, n_treated, replace=False)
    treat_m0[tr] = rng.integers(2019 * 12, 2025 * 12, n_treated)
    Y, Nd = {}, {}
    for f in fm:
        s = share * (0.6 if f == 'print' else 0.4)
        mu = N[f][None, :] * s[:, None] * np.exp(beta[:, None] * t_year[None, :] + gam[:, cal])
        for k in tr:
            a = treat_m0[k] - mi0
            mu[k, a:a + 3] *= (1 + lift)
        kk = np.maximum(mu / (phi - 1), 1e-6)
        y = rng.poisson(mu * rng.gamma(kk, 1 / kk)).astype(float)
        y[:, ~ok[f]] = np.nan
        Y[f] = y
        n = N[f].copy(); n[~ok[f]] = np.nan; Nd[f] = n
    C = M.Counts(mi0, ids, Y, Nd, ok)
    tests = pd.DataFrame(dict(work_id=ids[tr], m0=treat_m0[tr]))
    X = np.zeros((K, T), bool)
    X[tr, treat_m0[tr] - mi0] = True
    return C, tests, X


def run_sim(lift, K=2600, n_treated=700, seed=11):
    C, tests, X = sim_counts(K, lift, n_treated, seed)
    months = sorted(set(tests.m0) | set(range(2017 * 12 + 1, 2026 * 12, 1)))
    months = [m for m in months if m >= C.mi0 + 31 and m < C.mi0 + C.T - 1]
    tabs = build_ztables(C, None, months, workers=2)
    R = run_tests(C, tabs, tests, np.ones(K, bool), np.arange(K), X)
    return R


L = ['# Study 2R: simulation tests of the outcome pipeline', '',
     'Simulated worlds only (no real data): 2,600 works, print and ebook, quasi-Poisson-type overdispersion (phi 3), seasonality, trends, closure months; 700 treated works',
     'with a lift injected in months 0 to +2 (both formats), 200 placebo works per test, the pipeline of `_lib2r.run_tests`.', '']
bad = []


def check(name, cond, detail):
    L.append(f'- {"PASS" if cond else "FAIL"}: {name} ({detail})')
    log(('PASS ' if cond else 'FAIL ') + name, detail)
    if not cond:
        bad.append(name)


for lift in (0.0, 0.10, 0.30):
    R = run_sim(lift)
    ok = R[(R.skip == '') & R.p_p.notna() & ~R.too_sparse]
    tau = ok.tau_p.replace([np.inf, -np.inf], np.nan).dropna()
    rate = float((ok.p_p < 0.05).mean())
    se = np.sqrt(0.05 * 0.95 / len(ok))
    L.append(f'## Lift {lift:.0%}: {len(R)} tests, {len(ok)} usable and not too sparse; mean tau {tau.mean():.3f} (log(1+lift) = {np.log1p(lift):.3f}); share p < 0.05 = {rate:.3f}; mean p {ok.p_p.mean():.3f}; median placebos {ok.n_placebos.median():.0f}')
    if lift == 0:
        z0 = ok.z_p.replace([np.inf, -np.inf], np.nan).dropna()
        q95 = float(np.quantile(z0, 0.95)); null_ok = ok.copy()
    else:
        # expected detection: shift each null test's z by log(1+L)/sqrt(phi/sum mu) (the power shortcut of Study 3b) and compare with the
        # 95th percentile of the null z of the treated tests (the placebo z spread is wider than N(0,1): the forecast error of the trend is not in phi)
        sh = np.log1p(lift) / np.sqrt(null_ok.phi / null_ok.summu_p)
        exp_rate = float(((null_ok.z_p + sh) > q95).mean())
        L.append(f'  expected detection from the null z spread and the shift of z: {exp_rate:.3f}')
        check(f'lift {lift:.0%}: detection rate close to the shortcut prediction', abs(rate - exp_rate) < 0.08, f'observed {rate:.3f}, expected {exp_rate:.3f}')
    if lift == 0:
        check('lift 0: mean tau near 0', abs(tau.mean()) < 0.03, f'{tau.mean():.3f}')
        check('lift 0: about 5% of tests reach p < 0.05', 0.05 - 3.5 * se < rate < 0.05 + 3.5 * se, f'{rate:.3f} among {len(ok)} tests, 3.5 SE band {0.05 - 3.5 * se:.3f} to {0.05 + 3.5 * se:.3f}')
        ks = stats.kstest(ok.p_p, 'uniform')
        check('lift 0: p roughly uniform (rank p is discrete, KS statistic below 0.06)', ks.statistic < 0.06, f'KS {ks.statistic:.3f}')
        ps = ok.py_share_ge.dropna()
        check('lift 0: placebo-year share at or above the treated z is about 0.5 on average', 0.4 < ps.mean() < 0.6, f'{ps.mean():.3f} over {len(ps)} tests')
    elif lift == 0.10:
        L.append(f'  (descriptive) detection at +10%: {rate:.3f}')
        check('lift +10%: mean tau near log 1.10', abs(tau.mean() - np.log(1.10)) < 0.04, f'{tau.mean():.3f}')
    else:
        check('lift +30%: mean tau near log 1.30', abs(tau.mean() - np.log(1.30)) < 0.04, f'{tau.mean():.3f}')
        check('detection rises with the lift (+30% well above the 5% null)', rate > 0.25, f'{rate:.3f}')

# bootstrap tools on known truths
rng = np.random.default_rng(3)
n, G = 3000, 1500
cl = rng.integers(0, G, n)
dur = np.where(rng.random(n) < 0.7, rng.integers(1, 3, n), rng.integers(3, 14, n))
eff = rng.normal(0, 0.4, G)[cl]
tau = 0.05 + 0.10 * np.log2(dur) + eff + rng.normal(0, 0.7, n)
est, B = boot_ols(np.column_stack([np.ones(n), np.log2(dur)]), tau, cl)
lo, hi = pct(B[:, 1])
check('H1 slope recovered by the clustered bootstrap (truth 0.10)', lo < 0.10 < hi and (B[:, 1] <= 0).mean() < 0.01, f'est {est[1]:.3f}, 95% interval {lo:.3f} to {hi:.3f}')
tau0 = 0.0 + eff + rng.normal(0, 0.7, n)
est0, B0 = boot_ols(np.column_stack([np.ones(n), np.log2(dur)]), tau0, cl)
check('H1 slope with no true slope: one-sided p not tiny', (B0[:, 1] <= 0).mean() > 0.01 or abs(est0[1]) < 0.05, f'est {est0[1]:.3f}, p {(B0[:, 1] <= 0).mean():.3f}')
d, Bd = boot_diff(tau, dur >= 6, dur <= 2, cl)
dl, dh = pct(Bd)
check('H2 difference recovered (truth about 0.10 * (log2 mean(dur>=6) - log2 mean(dur<=2)) )', dl > 0 and np.isfinite(dh), f'diff {d:.3f}, interval {dl:.3f} to {dh:.3f}')
step = np.where(dur <= 5, 0.0, 0.25) + eff + rng.normal(0, 0.5, n)
h = hansen(dur, step, cl)
check('Hansen threshold recovered (step after 5 weeks)', h['gamma'] in (4, 5, 6) and h['gamma_ci_low'] <= 5 <= h['gamma_ci_high'], f"gamma {h['gamma']}, bootstrap interval {h['gamma_ci_low']} to {h['gamma_ci_high']}, LR set {h['lr_set']}")
q = M.bh_q(np.array([0.001, 0.2, 0.9, 0.004]))
check('BH helper returns q-values', len(q) == 4 and q[0] <= q[3] <= 0.2, str(np.round(q, 4)))
L += ['', f'Result: {"ALL PASS" if not bad else "FAILED: " + ", ".join(bad)}']
(REP / 'study2r_sim_tests.md').write_text('\n'.join(L) + '\n')
sys.exit(1 if bad else 0)
