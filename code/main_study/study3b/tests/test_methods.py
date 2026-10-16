# Count event study: agreement with statsmodels, injected effects, calibration on null data at several sizes (including very
# small), comparability of z across sizes, fit windows, missing and closure months, power shortcut, rank p, carry-over model.
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
import statsmodels.api as sm
import _s3
import _methods as M
import _simulate as SM
import _panel as PN
from _settings import SETTINGS as S

B3 = _s3.build
MI0 = 2012 * 12
M0 = MI0 + 80                         # month 0 used in the tests (the fit window is months 50..73 of the grid)


def reference_fit(C, m0, cat, drop=()):
    """Independent quasi-Poisson GLM (statsmodels) on the fit months of one category; returns phi, sum mu and sum Y over months 0..2."""
    fm = M.fit_months(m0, S)
    fi, cal, t, ys, off = [], [], [], [], []
    elig = M.feasibility(C, m0, S, rows=[cat])['elig'][0]          # formats that enter the model of this category
    C = M.Counts(C.mi0, C.ids, {f: y for f, y in C.Y.items() if elig[C.formats.index(f)]}, {f: n for f, n in C.N.items() if elig[C.formats.index(f)]},
                 {f: o for f, o in C.ok.items() if elig[C.formats.index(f)]})
    for k, f in enumerate(C.formats):
        for m in fm:
            i = m - C.mi0
            if C.ok[f][i] and (f, m) not in drop:
                fi.append(k); cal.append(m % 12); t.append((m - m0 + 18.5) / 12); ys.append(C.Y[f][cat, i]); off.append(np.log(C.N[f][i]))
    fi, cal, t = np.array(fi), np.array(cal), np.array(t)
    nf = len(C.formats)
    cols = [np.eye(nf)[fi], np.eye(nf)[fi] * t[:, None]] + [(cal == c)[:, None] for c in sorted(set(cal))[1:]]
    X = np.column_stack(cols).astype(float)
    g = sm.GLM(np.array(ys), X, family=sm.families.Poisson(), offset=np.array(off)).fit(scale='X2')
    sm_mu, sy = 0.0, 0.0
    for k, f in enumerate(C.formats):
        for r in range(0, 3):
            m = m0 + r; i = m - C.mi0
            if C.ok[f][i] and m % 12 in set(cal):
                x = np.concatenate([np.eye(nf)[k], np.eye(nf)[k] * ((r + 18.5) / 12), [float(m % 12 == c) for c in sorted(set(cal))[1:]]])
                sm_mu += float(np.exp(x @ g.params + np.log(C.N[f][i]))); sy += C.Y[f][cat, i]
    return g.scale, sm_mu, sy


def world(sizes, seed=1, **kw):
    return SM.sim_counts(seed, sizes, T=120, mi0=MI0, **kw)[0]


def test_matches_statsmodels_quasi_poisson():
    C = world([0.5, 3, 30, 300], missing=(MI0 + 55,))
    es = M.event_study(C, M0, S)
    assert es['feasible'].all()
    assert es['n_formats'][0] < 3 and es['n_formats'][3] == 3          # a very small category fits only the formats with >= 12 nonzero months
    for k in range(4):
        phi, mu, sy = reference_fit(C, M0, k)
        assert np.isclose(es['phi'][k], phi, rtol=1e-5), (k, es['phi'][k], phi)
        assert np.isclose(es['summu_p'][k], mu, rtol=1e-5)
        assert np.isclose(es['sumy_p'][k], sy)
        tau = np.log(sy / mu) if sy > 0 else -np.inf
        assert np.isclose(es['tau_p'][k], tau)
        if sy > 0:
            assert np.isclose(es['z_p'][k], tau / np.sqrt(phi / mu), rtol=1e-5)          # z = tau / sqrt(phi / sum mu)


def test_per_format_effects_add_up_to_the_joint_sums():
    C = world([20, 200])
    es = M.event_study(C, M0, S)
    for w in ('p', 's', 'pre'):
        assert np.allclose(sum(es[f'sumy_{w}_{f}'] for f in C.formats), es[f'sumy_{w}'])
        assert np.allclose(sum(es[f'summu_{w}_{f}'] for f in C.formats), es[f'summu_{w}'])
    f = C.formats[0]
    assert np.allclose(es['tau_p_' + f], np.log(es['sumy_p_' + f] / es['summu_p_' + f]))
    assert es['nm_p'][0] == 3 and es['nm_s'][0] == 6 and es['nm_pre'][0] == 6


def test_zero_counts_give_minus_infinity_and_keep_rank_order():
    tau, z = M.tau_z(np.array([0.0, 5.0]), np.array([4.0, 4.0]), np.array([1.0, 1.0]))
    assert np.isneginf(tau[0]) and np.isneginf(z[0]) and np.isclose(tau[1], np.log(1.25))
    assert M.rank_p(-np.inf, [-np.inf, 0.0, 1.0]) == 1.0           # ties count against the treated category
    assert M.rank_p(5.0, [0.0, 1.0, 2.0, -np.inf]) == 1 / 5


def test_rank_p_many_equals_rank_p():
    rng = np.random.default_rng(0)
    pl = np.append(rng.normal(size=50), [np.nan, np.inf, -np.inf])
    t = np.array([-3.0, 0.1, 0.1, 4.0, np.nan])
    a = M.rank_p_many(t, pl)
    b = [M.rank_p(x, pl) for x in t]
    assert np.allclose(a, b, equal_nan=True)


# ---------------- injected effect in a small-count category ----------------
def test_recovers_injected_effect_in_a_small_count_category():
    """A category with about 12 expected weighted checkouts over months 0..+2 and a +100% lift: the mean of tau over many
    simulated worlds is close to log 2, and the placebo-category rank detects it more often than the 5% of the null."""
    n_cat, taus, hits, null_hits = 300, [], 0, 0
    reps = 60
    for rep in range(reps):
        sizes = np.append(1.4, 10 ** np.random.default_rng(rep).uniform(-0.3, 2.0, n_cat))        # category 0: ~1.4 per format-month
        C = world(sizes, seed=100 + rep, effects=[(0, M0, 1.0)])
        es = M.event_study(C, M0, S)
        ok = es['feasible'] & ~np.isnan(es['z_p'])
        if not ok[0]:
            continue
        taus.append(es['tau_p'][0])
        pl = ok.copy(); pl[0] = False
        hits += M.rank_p(es['z_p'][0], es['z_p'][pl]) < 0.05
        k = 1 + (rep % n_cat)
        if ok[k]:
            pk = ok.copy(); pk[k] = False
            null_hits += M.rank_p(es['z_p'][k], es['z_p'][pk]) < 0.05
    taus = np.array(taus)
    taus = taus[np.isfinite(taus)]
    assert len(taus) >= 50
    assert abs(taus.mean() - np.log(2.0)) < 0.2, taus.mean()
    assert hits / len(taus) > 0.35, hits / len(taus)               # clearly above the 5% of a null category
    assert null_hits / len(taus) < 0.15


def test_recovers_injected_effect_in_a_large_category_exactly_enough():
    sizes = np.append(500.0, np.full(40, 300.0))
    C = world(sizes, seed=3, effects=[(0, M0, 0.5)])
    es = M.event_study(C, M0, S)
    assert abs(es['tau_p'][0] - np.log(1.5)) < 0.12
    assert abs(es['tau_p'][1:]).mean() < 0.12


# ---------------- null data: calibration and comparability across sizes ----------------
def _null_world(seed=5, K=3000):
    rng = np.random.default_rng(seed)
    sizes = 10 ** rng.uniform(-0.5, 3.0, K)
    C = world(sizes, seed=seed + 1)
    zs = []
    for m0 in (M0, M0 + 6, M0 + 11):
        es = M.event_study(C, m0, S)
        zs.append((es['z_p'], es['summu_p'], es['feasible'] & ~np.isnan(es['z_p'])))
    return zs


def _rank_p_all(z, ok):
    """Placebo-category rank p of every category among all the others (one-sided, as in a test)."""
    s = np.sort(z[ok])
    ge = len(s) - np.searchsorted(s, z[ok], side='left') - 1           # others at or above (its own value excluded)
    return (1 + ge) / len(s)


def test_rank_p_values_about_uniform_on_null_data_at_all_sizes_including_very_small():
    ps, sm = [], []
    for z, mu, ok in _null_world():
        ps.append(_rank_p_all(z, ok)); sm.append(mu[ok])
    p, mu = np.concatenate(ps), np.concatenate(sm)
    bands = [(0.0, 2.0), (2.0, 5.0), (5.0, 20.0), (20.0, 100.0), (100.0, 600.0), (600.0, 1e9)]
    for lo, hi in bands:
        s = (mu >= lo) & (mu < hi)
        assert s.sum() > 150, (lo, hi, s.sum())
        rej = float(np.mean(p[s] < 0.05))
        assert rej < 0.09, f'false positives inflated for sum mu {lo}-{hi}: {rej:.3f}'            # never anti-conservative by much, also for tiny categories
        if lo >= 5:
            assert rej > 0.01, f'implausibly conservative for sum mu {lo}-{hi}: {rej:.3f}'
            for q, tol in ((0.25, 0.10), (0.5, 0.12), (0.75, 0.12)):
                assert abs(float(np.mean(p[s] < q)) - q) < tol, (lo, hi, q, float(np.mean(p[s] < q)))


def test_z_is_comparable_across_sizes_from_5_expected_checkouts():
    """The record's z (Poisson scale only) is not N(0,1) because the trend is extrapolated, but its spread is the same at every size
    from 5 expected checkouts, which is what the placebo rank needs; below 5 the discreteness makes it different (reported as too sparse)."""
    zs, mus = [], []
    for z, mu, ok in _null_world():
        zs.append(z[ok]); mus.append(mu[ok])
    z, mu = np.concatenate(zs), np.concatenate(mus)
    sds, means = [], []
    for lo, hi in ((5, 20), (20, 100), (100, 500), (500, 5000), (5000, 1e9)):
        s = (mu >= lo) & (mu < hi) & np.isfinite(z)
        assert s.sum() > 100
        sds.append(z[s].std()); means.append(z[s].mean())
    assert max(sds) / min(sds) < 1.4, sds
    assert max(abs(m) for m in means) < 0.9, means
    tiny = (mu < 0.5) & np.isfinite(z)
    assert tiny.sum() > 5 and abs(z[tiny].mean() - np.mean(means)) > 0.5      # very small categories do behave differently (hence the flag)
    assert np.all(M.too_sparse(np.array([4.9, 5.0, 5.1]), S) == [True, False, False])


# ---------------- windows, missing and closure months ----------------
def test_fit_windows_never_touch_months_from_minus_6():
    C = world([5, 50, 500], seed=11)
    base = M.event_study(C, M0, S)
    keys = ('phi', 'df')
    def run(shift_rel, factor):
        C2 = world([5, 50, 500], seed=11)
        for f in C2.formats:
            i = M0 + shift_rel - C2.mi0
            C2.Y[f][:, i] = C2.Y[f][:, i] * factor + 777
        return M.event_study(C2, M0, S)
    for rel in range(-6, 6):                                           # months -6..+5: the fit must not change at all
        e = run(rel, 40.0)
        for k in keys:
            assert np.array_equal(e[k], base[k]), (rel, k)
        for w in ('p', 's'):                                           # the window sums of mu do not depend on Y
            assert np.array_equal(e[f'summu_{w}'], base[f'summu_{w}']), (rel, w)
    changed = run(-7, 40.0)                                            # month -7 is the last fit month
    assert not np.allclose(changed['phi'], base['phi'])
    assert not np.allclose(changed['summu_p'], base['summu_p'])
    first = run(-30, 40.0)                                             # month -30 is the first fit month
    assert not np.allclose(first['summu_p'], base['summu_p'])
    for rel in (-31, -40):                                             # months before the fit window are not used either
        e = run(rel, 40.0)
        assert np.array_equal(e['phi'], base['phi'])


def test_missing_months_drop_out_of_fit_and_window():
    miss_fit, miss_win = M0 - 20, M0 + 1
    C = world([40, 400], seed=21, missing=(miss_fit, miss_win))
    es = M.event_study(C, M0, S)
    drop = {(f, miss_fit) for f in C.formats}
    phi, mu, sy = reference_fit(C, M0, 0, drop=set())           # reference already skips months that are not usable
    assert np.isclose(es['phi'][0], phi, rtol=1e-5) and np.isclose(es['summu_p'][0], mu, rtol=1e-5) and np.isclose(es['sumy_p'][0], sy)
    assert es['nm_p'][0] == 2 and es['nm_s'][0] == 5              # month +1 is gone from the window
    # whatever number sits in an unusable month is ignored: dirty values give the identical result
    C2 = world([40, 400], seed=21, missing=(miss_fit, miss_win))
    for f in C2.formats:
        C2.Y[f][:, [miss_fit - MI0, miss_win - MI0]] = 1e6
    e2 = M.event_study(C2, M0, S)
    for k in ('phi', 'summu_p', 'sumy_p', 'z_p', 'summu_s'):
        assert np.array_equal(e2[k], es[k]), k
    # a window with fewer than 2 usable months is not estimated (addendum b)
    C3 = world([40], seed=22, missing=(M0, M0 + 1))
    e3 = M.event_study(C3, M0, S)
    assert np.isnan(e3['z_p'][0]) and np.isfinite(e3['z_s'][0])


def test_closure_months_are_missing_not_zero():
    """A library closure (addendum e: total below 50% of the median of the previous 12 months) is found by the Study 3 month rule,
    becomes NaN in the dense counts, and does not enter the fit as a zero."""
    rng = np.random.default_rng(0)
    mis = np.arange(MI0, MI0 + 120)
    tot = rng.integers(90_000, 110_000, 120).astype(float)
    closed = M0 - 10
    tot[closed - MI0] = 2_000.0
    totals = pd.DataFrame({'total_checkouts': tot, 'n_rows': 500}, index=pd.Index(mis, name='mi'))
    st = B3.month_status(totals, closure=(S.closure_frac, S.closure_lookback, S.closure_min))
    assert not st.loc[closed, 'month_ok'] and st.month_ok.drop(closed).all()
    status = st.reset_index()[['mi', 'month_ok', 'total_checkouts']].assign(format='audiobook')
    long = pd.DataFrame({'level': 'narrow', 'node_id': 'a', 'format': 'audiobook', 'mi': mis, 'y': rng.poisson(40, 120) + 1.0})
    C = PN.make_counts(long, status, 'narrow', ['a'], ['audiobook'])
    assert np.isnan(C.Y['audiobook'][0, closed - MI0]) and np.isnan(C.N['audiobook'][closed - MI0]) and not C.ok['audiobook'][closed - MI0]
    e1 = M.event_study(C, M0, S)
    long2 = long.copy(); long2.loc[long2.mi == closed, 'y'] = 0.0               # a zero in the closure month changes nothing
    e2 = M.event_study(PN.make_counts(long2, status, 'narrow', ['a'], ['audiobook']), M0, S)
    assert np.array_equal(e1['phi'], e2['phi']) and np.array_equal(e1['summu_p'], e2['summu_p'])
    fz = M.feasibility(C, M0, S)
    assert fz['avail']['audiobook'].sum() == 23


def test_feasibility_rule_and_format_inclusion():
    C = world([30, 30, 30], seed=2)
    # category 1: only 11 nonzero months in the audiobook fit window; category 2: none in any format
    fm = M.fit_months(M0, S) - MI0
    for f in C.formats:
        C.Y[f][2, fm] = 0.0
    C.Y['audiobook'][1, fm] = 0.0
    C.Y['audiobook'][1, fm[:11]] = 1.0
    fz = M.feasibility(C, M0, S)
    assert fz['feasible'].tolist() == [True, True, False]
    assert fz['elig'][0].tolist() == [True, True, True] and fz['elig'][1].tolist() == [False, True, True]
    es = M.event_study(C, M0, S)
    assert es['formats'].tolist()[:2] == [7, 6] and es['n_formats'][1] == 2 and np.isnan(es['z_p'][2])
    C.Y['audiobook'][1, fm[:12]] = 1.0
    assert M.feasibility(C, M0, S)['elig'][1].tolist() == [True, True, True]          # exactly 12 nonzero months is enough


# ---------------- power by injected lifts ----------------
def test_lifted_z_equals_a_refit_with_the_lift_injected():
    sizes = np.append(60.0, np.full(30, 40.0))
    C = world(sizes, seed=9)
    es = M.event_study(C, M0, S)
    for lift in (0.1, 0.5, 1.0):
        C2 = world(sizes, seed=9)
        for f in C2.formats:
            C2.Y[f][0, M0 - MI0:M0 - MI0 + 3] *= 1 + lift                   # observed Y multiplied by (1 + lift) in months 0..+2
        e2 = M.event_study(C2, M0, S)
        z = M.lifted_z(es['z_p'][0], es['summu_p'][0], es['phi'][0], es['sumy_p'][0], lift)
        assert np.isclose(z, e2['z_p'][0], rtol=1e-9), (lift, z, e2['z_p'][0])
    assert np.isneginf(M.lifted_z(-np.inf, 5.0, 1.0, 0.0, 1.0))


def test_size_bands_are_quartiles_and_cover_everything():
    v = np.random.default_rng(0).lognormal(3, 2, 1000)
    edges = M.size_bands(v, 4)
    b = M.band_of(v, edges)
    assert set(b) == {0, 1, 2, 3} and all(abs(np.mean(b == k) - 0.25) < 0.01 for k in range(4))


def test_power_summary_minimum_detectable_lift():
    d = pd.DataFrame({'lift': np.repeat([0.1, 0.2, 0.5], 10), 'p': np.concatenate([[0.01] * 3 + [0.5] * 7, [0.01] * 7 + [0.5] * 3, [0.01] * 9 + [0.5]])})
    tab, mde = M.power_summary(d, S)
    assert mde == 0.5 and tab.rate.tolist() == [0.3, 0.7, 0.9]


# ---------------- pooling, BH, carry-over ----------------
def test_cluster_bootstrap_mean_resamples_whole_categories():
    rng = np.random.default_rng(0)
    cl = np.repeat(np.arange(40), 5)
    v = np.repeat(rng.normal(0.3, 0.5, 40), 5) + rng.normal(0, 0.05, 200)          # almost all variance between categories
    b = M.cluster_boot_mean(v, cl, 500, 1)
    naive = v.std() / np.sqrt(len(v))
    assert (b['high'] - b['low']) / 3.92 > 2 * naive                               # clustered interval is wider than the naive one
    assert b['low'] < b['mean'] < b['high'] and b['clusters'] == 40
    assert M.cluster_boot_mean(v, cl, 500, 1) == b                                  # same seed, same answer
    assert M.cluster_boot_mean([np.nan, np.inf], [1, 2], 10, 1)['n'] == 0


def test_bh_q_values():
    q = M.bh_q(np.array([0.001, 0.01, 0.04, 0.5, np.nan]))
    assert np.allclose(q[:4], [0.004, 0.02, 0.0533333, 0.5], atol=1e-6) and np.isnan(q[4])


def test_carry_over_regression_recovers_known_coefficients():
    rng = np.random.default_rng(4)
    n = 400
    d = pd.DataFrame({'node_id': rng.integers(0, 120, n).astype(str), 'size': np.exp(rng.normal(1.2, 0.4, n)),
                      'duration_class': rng.choice(['fading', 'intermediate', 'sustained'], n), 'broad_id': 'B01'})
    d['broad_id'] = 'B' + (d.node_id.astype(int) % 3).astype(str)
    d['tau_p'] = 0.1 + 0.2 * np.log(d['size']) + 0.3 * (d.duration_class == 'sustained') + rng.normal(0, 0.1, n)
    tab, nt, nc = M.carry_fit(d, S, outcome='tau_p', n_boot=300, seed=1)
    t = tab.set_index('term')
    assert abs(t.loc['log_size', 'coef'] - 0.2) < 0.06 and abs(t.loc['class_sustained', 'coef'] - 0.3) < 0.06
    assert t.loc['class_sustained', 'ci_low'] < 0.3 < t.loc['class_sustained', 'ci_high']
    assert nt == n and 'class_intermediate' in t.index and 'format_print' not in t.index        # no format term in Study 3b


def test_sentiment_features_use_the_first_four_weeks_against_the_26_week_median():
    weeks = pd.date_range('2018-01-01', periods=60, freq='7D')
    base = np.zeros(60); base[40:44] = [2, 2, 2, 2]
    pos = pd.Series(3.0 + base, index=weeks); neg = pd.Series(4.0 + 2 * base, index=weeks)
    s = pd.DataFrame({'tone': pos - neg, 'tone_pos': pos, 'tone_neg': neg})
    f = M.sentiment_features(s, weeks[40], S)
    assert np.isclose(f['d_pos'], 2.0) and np.isclose(f['d_neg'], 4.0) and np.isclose(f['d_tone'], -2.0)
    assert np.isclose(f['d_intensity'], 6.0) and f['neg_shift'] == 1.0
    assert np.isnan(M.sentiment_features(s, weeks[10], S)['d_tone'])                # not enough baseline weeks
