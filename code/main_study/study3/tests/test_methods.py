# Methods on small simulated series with known answers: fit windows never touch post or pre-trend months,
# effects are recovered exactly in noise-free data, missing months are skipped, and the inference helpers agree with
# standard implementations.
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from scipy.optimize import minimize
from _settings import SETTINGS as S
import _methods as M

M0 = 2020 * 12 + 2           # 2020-03
GRID = np.arange(2014 * 12, 2024 * 12)


def clean_series(seed=0, lift=0.0, m0=M0, win=S.window_primary):
    """Trend + month-of-year pattern (exactly what the event-study model fits) + optional lift in a window."""
    rng = np.random.default_rng(seed)
    seas = rng.normal(0, 0.1, 12)
    y = -5 + 0.004 * (GRID - GRID[0]) + seas[GRID % 12]
    y = y + lift * ((GRID >= m0 + win[0]) & (GRID <= m0 + win[1]))
    return pd.Series(y, index=GRID)


def factor_panel(n=40, seed=1, noise=0.0):
    """Log shares driven by three common factors; unit 'T' is a convex mix of donors plus its own level."""
    rng = np.random.default_rng(seed)
    F = np.cumsum(rng.normal(0, 0.05, (len(GRID), 3)), axis=0)
    L = rng.uniform(0.2, 1.5, (n, 3))
    Y = pd.DataFrame(F @ L.T + rng.uniform(-6, -3, n) + rng.normal(0, noise, (len(GRID), n)),
                     index=GRID, columns=[f'D{i:02d}' for i in range(n)])
    w = rng.dirichlet(np.ones(4))
    Y['T'] = Y.iloc[:, :4].to_numpy() @ w + 0.7          # a level the donors cannot match without demeaning
    return Y


def test_simplex_ls_matches_a_general_solver():
    rng = np.random.default_rng(3)
    for _ in range(20):
        A = rng.normal(size=(20, int(rng.integers(2, 40)))); b = rng.normal(size=20)
        w = M.simplex_ls(A, b)
        assert np.all(w >= -1e-12) and abs(w.sum() - 1) < 1e-9
        k = A.shape[1]
        r = minimize(lambda x: np.sum((A @ x - b) ** 2), np.full(k, 1 / k), method='SLSQP', bounds=[(0, 1)] * k,
                     constraints=[{'type': 'eq', 'fun': lambda x: x.sum() - 1}], options={'ftol': 1e-14, 'maxiter': 1000})
        assert np.sum((A @ w - b) ** 2) <= r.fun + 1e-6


def test_event_study_fit_window_never_touches_month_minus_6_or_later():
    y = clean_series() + np.random.default_rng(1).normal(0, 0.05, len(GRID))
    for m0 in range(M0 - 30, M0 + 30, 7):
        r = M.event_study(y, m0, S)
        fm = r['es_fit_months']
        assert fm.max() == m0 + S.es_fit_end and fm.min() == m0 + S.es_fit_end - S.es_fit_len + 1
        assert fm.max() < m0 + S.es_pretrend[0]
        # changing every month from -6 on shifts the gaps by exactly that change: the prediction did not move
        bump = pd.Series(np.where(y.index >= m0 + S.es_pretrend[0], np.random.default_rng(m0).normal(0, 1, len(y)), 0.0), index=y.index)
        r2 = M.event_study(y + bump, m0, S)
        for k, g in r['es_gaps'].items():
            assert np.isclose(r2['es_gaps'][k] - g, bump[m0 + k])


def test_event_study_recovers_lift_exactly_without_noise():
    for lift in (0.0, 0.2, -0.1):
        r = M.event_study(clean_series(lift=lift), M0, S)
        assert np.isclose(r['es_effect_p'], lift) and np.isclose(r['es_pretrend'], 0.0, atol=1e-9)
        assert r['es_n_p'] == S.window_primary[1] - S.window_primary[0] + 1


def test_event_study_skips_missing_months():
    y = clean_series(lift=0.3)
    for m in (M0 - 20, M0 - 12, M0 - 9):        # missing months in the fit window
        y[m] = np.nan
    y[M0 + 1] = np.nan                          # one missing month in the effect window
    r = M.event_study(y, M0, S)
    assert r['es_ok'] and np.isclose(r['es_effect_p'], 0.3) and r['es_n_p'] == 2
    y[M0 + 2] = np.nan                          # now only one month left: not estimated
    r = M.event_study(y, M0, S)
    assert np.isnan(r['es_effect_p']) and r['es_n_p'] == 1
    z = clean_series()
    z[(z.index >= M0 - 30) & (z.index <= M0 - 16)] = np.nan   # most of the fit window missing
    assert not M.event_study(z, M0, S)['es_ok']


def test_synthetic_control_fit_window_never_touches_month_minus_2_or_later():
    Y = factor_panel(noise=0.03)
    donors = [c for c in Y.columns if c != 'T']
    r = M.sc_test(Y, 'T', donors, M0, S)
    assert r['sc_fit_rel'].min() >= S.sc_fit[0] and r['sc_fit_rel'].max() <= S.sc_fit[1]
    Y2 = Y.copy()
    late = Y2.index >= M0 + S.sc_fit[1] + 1
    Y2.loc[late] += np.random.default_rng(5).normal(0, 1, (late.sum(), Y2.shape[1]))
    r2 = M.sc_test(Y2, 'T', donors, M0, S)
    assert r2['sc_weights'].keys() == r['sc_weights'].keys()
    assert all(np.isclose(r2['sc_weights'][k], v) for k, v in r['sc_weights'].items())
    assert np.isclose(r2['sc_pre_rmspe'], r['sc_pre_rmspe'])
    for k in range(S.sc_fit[0], S.sc_fit[1] + 1):
        assert np.isclose(r2['sc_gaps'][k], r['sc_gaps'][k])


def test_synthetic_control_recovers_lift_with_demeaning():
    Y = factor_panel()
    donors = [c for c in Y.columns if c != 'T']
    win = (M0 + S.window_secondary[0] <= Y.index) & (Y.index <= M0 + S.window_secondary[1])
    Y.loc[win, 'T'] += 0.25
    r = M.sc_test(Y, 'T', donors, M0, S)
    assert np.isclose(r['sc_effect_p'], 0.25, atol=1e-4) and np.isclose(r['sc_effect_s'], 0.25, atol=1e-4)
    assert r['sc_pre_rmspe'] < 1e-4
    assert r['sc_p_p'] == r['sc_p_min'] == 1 / (len(donors) + 1)


def test_synthetic_control_missing_months():
    Y = factor_panel()
    donors = [c for c in Y.columns if c != 'T']
    win = (M0 + S.window_primary[0] <= Y.index) & (Y.index <= M0 + S.window_primary[1])
    Y.loc[win, 'T'] += 0.25
    Y.loc[M0 + 1, :] = np.nan                       # a month missing for everyone (as in the digital outages)
    Y.loc[M0 - 10, :] = np.nan
    Y.loc[M0 - 5, 'D03'] = np.nan                   # a donor missing a month the treated unit has: left out
    r = M.sc_test(Y, 'T', donors, M0, S)
    assert r['sc_n_donors'] == len(donors) - 1 and 'D03' not in r['sc_weights']
    assert r['sc_n_p'] == 2 and np.isclose(r['sc_effect_p'], 0.25, atol=0.02)
    Y.loc[M0 + 2, 'T'] = np.nan                     # one available month left in the primary window
    r = M.sc_test(Y, 'T', donors, M0, S)
    assert np.isnan(r['sc_effect_p']) and np.isnan(r['sc_p_p'])


def test_window_mean_needs_minimum_months():
    assert np.isnan(M.window_mean([np.nan, 1.0, np.nan], S.min_window_months)[0])
    assert M.window_mean([np.nan, 1.0, 3.0], S.min_window_months) == (2.0, 2)


def test_rank_p_counts_ties_against_the_treated():
    assert M.rank_p(5.0, [1, 2, 3]) == 0.25
    assert M.rank_p(2.0, [1, 2, 3]) == 0.75
    assert M.rank_p(-1.0, [1, 2, 3]) == 1.0


def test_bh_matches_statsmodels():
    from statsmodels.stats.multitest import multipletests
    p = np.random.default_rng(2).uniform(size=50) ** 2
    q = M.bh_q(p)
    assert np.allclose(q, multipletests(p, method='fdr_bh')[1])
    p2 = np.append(p, np.nan)
    assert np.isnan(M.bh_q(p2)[-1]) and np.allclose(M.bh_q(p2)[:-1], q)


def test_cluster_bootstrap_is_reproducible_and_resamples_whole_clusters():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({'c': np.repeat(np.arange(30), 4), 'x': np.repeat(rng.normal(0, 1, 30), 4)})
    a = M.cluster_bootstrap(df, 'c', lambda d: float(d.x.mean()), 200, S.boot_seed)
    b = M.cluster_bootstrap(df, 'c', lambda d: float(d.x.mean()), 200, S.boot_seed)
    assert a == b
    sizes = M.cluster_bootstrap(df, 'c', lambda d: (len(d), d.groupby('c').size().min()), 50, 1)
    assert all(n == 120 and k >= 4 and k % 4 == 0 for n, k in sizes)
    lo, hi = M.percentile_ci(a)
    assert lo < df.x.mean() < hi


def test_peak_lag_and_lift_injection():
    assert M.peak_lag({0: 0.1, 1: np.nan, 2: 0.5, 3: 0.2, 7: 9.0}, S.carry_lag) == 2
    y = pd.Series(0.0, index=GRID)
    z = M.inject_lift(y, M0, S.power_window, 0.3)
    hit = (z.index >= M0 + S.power_window[0]) & (z.index <= M0 + S.power_window[1])
    assert np.allclose(np.exp(z[hit]), 1.3) and (z[~hit] == 0).all()


def test_tone_feature_and_placebo_windows():
    weeks = pd.date_range('2018-01-01', periods=300, freq='7D')
    s = pd.Series(1.0, index=weeks)
    start = weeks[100]
    s[start:start + pd.Timedelta(weeks=S.tone_weeks - 1)] = 3.0
    s[weeks[100 - S.tone_baseline_weeks]:weeks[99]] = np.linspace(0, 2, S.tone_baseline_weeks)
    assert np.isclose(M.tone_feature(s, start, S), 3.0 - 1.0)
    blocked = M.blocked_weeks([(start, 6), (weeks[200], 4)])
    starts = M.tone_placebo_starts(weeks, blocked, S, np.random.default_rng(0))
    assert len(starts) == S.tone_placebo_n
    for w in starts:
        win = set(pd.date_range(w, periods=S.tone_placebo_len, freq='7D'))
        assert not (win & blocked) and w - pd.Timedelta(weeks=S.tone_baseline_weeks) >= weeks[0]


def test_carry_over_model_recovers_coefficients():
    rng = np.random.default_rng(4)
    n = 600
    d = pd.DataFrame({'node_id': rng.integers(0, 120, n).astype(str), 'size': 1.5 + rng.lognormal(0, 0.5, n),
                      'duration_class': rng.choice(['fading', 'intermediate', 'sustained'], n),
                      'format': rng.choice(['audiobook', 'ebook', 'print', 'librivox'], n)})
    d['broad_id'] = 'B' + (d.node_id.astype(int) % 4).astype(str)
    d['classic'] = d.format == 'librivox'
    d['sc_effect_p'] = (0.02 + 0.15 * np.log(d['size']) + 0.1 * (d.duration_class == 'sustained')
                        + 0.05 * (d.broad_id == 'B2') - 0.04 * d.classic + rng.normal(0, 0.03, n))
    tab, n_used, n_cl = M.carry_fit(d, S, n_boot=200, seed=1)
    t = tab.set_index('term')
    assert abs(t.loc['log_size', 'coef'] - 0.15) < 0.02 and abs(t.loc['class_sustained', 'coef'] - 0.1) < 0.02
    assert abs(t.loc['classic', 'coef'] + 0.04) < 0.02 and t.loc['log_size', 'ci_low'] < 0.15 < t.loc['log_size', 'ci_high']
    assert 'format_librivox' not in t.index and n_used == n and n_cl == d.node_id.nunique()
