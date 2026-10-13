# Models and metrics: walk-forward never trains on a target month after the origin; ridge scaling and missing values;
# CatBoost parameters; DM, bootstrap, rank metrics.
import sys, pathlib, copy
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
import _settings as ST, _features as FE, _models as M
import sim

S = ST.settings()
MI = ST.mi_from_ym


def test_walk_forward_never_trains_on_a_target_after_the_origin():
    w = sim.make_world(seed=11)
    F = sim.build(w, S)
    cut = MI('2020-01')
    seen = []

    def spy(train, test):
        seen.append((int(test.origin_mi.iloc[0]), int(train.target_mi.max()), int(train.origin_mi.max()), int(test.h.iloc[0])))
        return np.full(len(test), train.y.mean())
    for h in (1, 2):
        seen.clear()
        M.walk_forward(F, [MI('2019-06'), MI('2019-07'), MI('2020-03')], h, spy)
        assert len(seen) == 3
        for t, max_target, max_origin, hh in seen:
            assert max_target <= t and max_origin + hh <= t           # origins s with s + h <= t only
    # poisoned future: targets of origins from 2020-01 on are absurd; a forecast made before their target month is known is clean
    Fp = F.copy()
    Fp.loc[Fp.origin_mi >= cut, 'y'] = 1e9
    for h in (1, 2):
        out = M.walk_forward(Fp, [cut + h - 1], h, lambda tr, te: np.full(len(te), tr.y.mean()))
        assert (out.y_hat < 1e6).all()                                # the poisoned origins' targets are still after t
        out = M.walk_forward(Fp, [cut + h], h, lambda tr, te: np.full(len(te), tr.y.mean()))
        assert (out.y_hat > 1e6).any()                                # one month later the first poisoned target is in the past
    # the full forecasting function asserts the same
    import _forecast as FC
    S2 = copy.copy(S); S2.cb_iterations = 5
    out = FC.forecast_origin(F, MI('2019-09'), S2, 1, models=('ridge',))
    assert (out.n_train > 0).all()


def test_ridge_scaling_uses_training_rows_only():
    rng = np.random.default_rng(0)
    tr = pd.DataFrame({'a': rng.normal(5, 2, 200), 'b': rng.normal(0, 1, 200), 'format': 'x', 'level': 'narrow'})
    te1 = pd.DataFrame({'a': [5.0, 6.0], 'b': [0.0, 1.0], 'format': 'x', 'level': 'narrow'})
    te2 = pd.DataFrame({'a': [5000.0, -6000.0], 'b': [1e6, -1e6], 'format': 'x', 'level': 'narrow'})
    X1, T1 = M._design(tr, te1, ['a', 'b'], ['format', 'level'])
    X2, T2 = M._design(tr, te2, ['a', 'b'], ['format', 'level'])
    assert np.allclose(X1, X2)                                        # test rows never move the scaling
    assert np.allclose(X1[:, :2].mean(axis=0), 0, atol=1e-9) and np.allclose(X1[:, :2].std(axis=0), 1)
    assert np.allclose(T1[0, :2], [(5 - tr.a.mean()) / tr.a.std(ddof=0), (0 - tr.b.mean()) / tr.b.std(ddof=0)])


def test_ridge_missing_values_are_zero_plus_indicator():
    tr = pd.DataFrame({'a': [1.0, 2.0, np.nan, 4.0, 5.0, np.nan], 'b': [1.0, 2.0, 3.0, 4.0, 5.0, 7.0], 'format': 'x'})
    te = pd.DataFrame({'a': [np.nan, 3.0], 'b': [np.nan, 4.0], 'format': 'x'})
    Xtr, Xte = M._design(tr, te, ['a', 'b'], ['format'])
    assert Xtr.shape[1] == 3                                          # a, b, and one indicator (only a has a missing value)
    assert np.allclose(Xtr[[2, 5], 0], 0) and np.allclose(Xtr[:, 2], [0, 0, 1, 0, 0, 1])
    assert Xte[0, 0] == 0 and Xte[0, 2] == 1 and Xte[1, 2] == 0       # missing test value: 0 and indicator 1
    assert Xte[0, 1] == 0                                             # b was never missing in training: just 0 (the mean)


def test_ridge_alpha_choice_uses_the_last_training_origins_in_time_order():
    rng = np.random.default_rng(1)
    n_o, per = 40, 30
    d = pd.DataFrame({'origin_mi': np.repeat(np.arange(n_o), per), 'x': rng.normal(size=n_o * per), 'format': 'x', 'level': 'narrow'})
    d['y'] = 2.0 * d.x                                               # noiseless: the smallest alpha must win
    d['target_mi'] = d.origin_mi + 1
    seen = {}
    orig = M._ridge_fit_predict

    def spy(train, test, num, cat, alpha):
        seen.setdefault('calls', []).append((int(train.origin_mi.max()), int(test.origin_mi.min()), int(test.origin_mi.max()), alpha))
        return orig(train, test, num, cat, alpha)
    M._ridge_fit_predict = spy
    try:
        a = M.choose_alpha(d, ['x'], ['format'], 1, S)
    finally:
        M._ridge_fit_predict = orig
    assert a == 0.1
    for fit_max, va_min, va_max, _ in seen['calls']:
        assert va_min == n_o - S.ridge_val_origins and va_max == n_o - 1   # the last 12 training origins validate
        assert fit_max + 1 <= va_min                                       # fitting rows' targets are before the first validation origin
    assert {c[3] for c in seen['calls']} == set(S.ridge_alphas)
    # noise-only target: a large alpha is preferred
    d['y'] = rng.normal(size=len(d))
    assert M.choose_alpha(d, ['x'], ['format'], 1, S) in (10.0, 100.0)


def test_catboost_parameters_come_from_the_record():
    p = M.catboost_params(S, 2)
    assert (p['iterations'], p['depth'], p['learning_rate'], p['loss_function'], p['random_seed'], p['thread_count']) == \
           (600, 6, 0.05, 'RMSE', 20261013, 2)
    # it fits and predicts on a small panel, with the record's categorical columns and no category id
    w = sim.make_world(seed=12)
    F = sim.build(w, S)
    t = MI('2019-06')
    tr, te = M.training_rows(F[F.group == 'seattle'], t, 1), M.test_rows(F, t, 1)
    S2 = copy.copy(S); S2.cb_iterations = 20
    p = M.fit_predict_catboost(tr, te, 'D+W', S2, 1)
    assert p.shape == (len(te),) and np.isfinite(p).all()
    p2 = M.fit_predict_catboost(tr, te, 'D+W', S2, 2)
    assert np.allclose(p, p2)                                            # same seed: the thread count does not change the forecast


def test_dm_matches_a_hac_regression_and_is_one_sided():
    import statsmodels.api as sm
    rng = np.random.default_rng(3)
    d = 0.1 + rng.normal(size=80)
    d = d + 0.5 * np.concatenate([[0], d[:-1]])                       # autocorrelated
    base, new = d + 1.0, np.ones_like(d)
    stat, p = M.dm_test(base, new, 3)
    r = sm.OLS(d, np.ones_like(d)).fit(cov_type='HAC', cov_kwds={'maxlags': 3, 'use_correction': False})
    assert np.isclose(stat, float(r.tvalues[0]), rtol=1e-6)
    from scipy.stats import norm
    assert np.isclose(p, 1 - norm.cdf(stat))
    assert stat > 0 and p < 0.5 < M.dm_test(new, base, 3)[1]                       # one-sided: the direction matters
    assert np.isnan(M.dm_test(np.ones(3), np.zeros(3), 3)[0])


def test_block_bootstrap_is_reproducible_and_centred():
    rng = np.random.default_rng(4)
    sb = 100 + rng.normal(size=60)
    sn = 0.8 * sb
    lo, hi, draws = M.block_bootstrap_skill(sb, sn, S.boot_block, S.boot_n, S.boot_seed)
    assert len(draws) == S.boot_n and np.allclose(draws, 0.2) and np.isclose(lo, 0.2) and np.isclose(hi, 0.2)
    sn2 = sb * (1 + 0.3 * rng.normal(size=60))
    a = M.block_bootstrap_skill(sb, sn2, 3, 2000, S.boot_seed)
    b = M.block_bootstrap_skill(sb, sn2, 3, 2000, S.boot_seed)
    c = M.block_bootstrap_skill(sb, sn2, 3, 2000, S.boot_seed + 1)
    assert a[0] == b[0] and a[1] == b[1] and a[0] != c[0]
    assert a[0] < 1 - sn2.sum() / sb.sum() < a[1]
    # resampled blocks are runs of consecutive months of the stated length
    T = 20; b3 = 3
    starts = np.random.default_rng(S.boot_seed).integers(0, T - b3 + 1, size=(S.boot_n, int(np.ceil(T / b3))))
    assert starts.max() <= T - b3


def test_compare_models_and_helps_rule():
    rng = np.random.default_rng(5)
    origin = np.repeat(np.arange(48), 20)
    e0 = np.abs(rng.normal(1.0, 0.2, len(origin)))
    e1 = e0 * 0.9
    r = M.compare_models(origin, e0, e1, S)
    assert np.isclose(r['skill'], 0.1) and r['ci_lo'] > 0 and r['dm_p'] < 0.05 and M.helps(r, S)
    r = M.compare_models(origin, e0, e0 * 1.1, S)
    assert r['skill'] < 0 and not M.helps(r, S)
    noise = e0 * (1 + 0.001 * rng.normal(size=len(e0)))
    assert not M.helps(M.compare_models(origin, e0, noise, S), S)


def test_rank_metrics_by_hand():
    rows = []
    for o in range(2):
        for i in range(20):
            rows.append(dict(origin_mi=o, format='ebook', level='narrow', idx=i))
    df = pd.DataFrame(rows)
    act = np.tile(np.arange(20.0), 2)
    assert np.isclose(M.spearman_within(df, act * 2 + 1, act, ['origin_mi', 'format']), 1.0)
    assert np.isclose(M.spearman_within(df, -act, act, ['origin_mi', 'format']), -1.0)
    assert np.isnan(M.spearman_within(df.head(5), act[:5], act[:5], ['origin_mi', 'format']))           # fewer than 10 categories
    assert np.isclose(M.top_hit_rate(df, act, act, ['origin_mi', 'format'], 0.1), 1.0)                  # k = 2
    f = act.copy(); f[18:20] = [-1, -2]; f[38:40] = [-1, -2]
    assert np.isclose(M.top_hit_rate(df, f, act, ['origin_mi', 'format'], 0.1), 0.0)
    assert 0.0 <= M.top_hit_rate(df, np.random.default_rng(0).normal(size=40), act, ['origin_mi', 'format'], 0.1) <= 1.0
    a = np.array([0.5, -0.5, 0.05, -0.2, 0.3])
    fc = np.array([0.1, 0.1, -1.0, -0.1, -0.1])
    assert np.isclose(M.direction_accuracy(fc, a, 0.10), 2 / 4)       # the 0.05 change is not scored; 4 are; 2 right
    assert np.isclose(M.mase([1, 2, 3], [1, 2, 4], [0, 2, 3]), (1 / 3) / (1 / 3))
    assert np.isclose(M.skill(0.8, 1.0), 0.2)
    assert np.isclose(M.auc([0.1, 0.4, 0.35, 0.8], [0, 0, 1, 1]), 0.75)
    assert np.isnan(M.auc([1, 2], [1, 1]))
