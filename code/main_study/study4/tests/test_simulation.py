# Simulated worlds: a lagged interest signal that truly drives demand must make D+W beat D; pure-noise interest must not.
import sys, pathlib, copy
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
import _settings as ST, _features as FE, _models as M
import sim

S = ST.settings()
MI = ST.mi_from_ym
S_FAST = copy.copy(S)
S_FAST.cb_iterations = 150            # smaller than the record's 600: the worlds have a few thousand rows


def run(world, models=('ridge', 'catboost'), first='2019-01', last='2022-12', h=1):
    F = sim.build(world, S)
    out = {}
    origins = list(range(MI(first), MI(last) + 1))
    if 'ridge' in models:
        for fs in ('D', 'D+W'):
            out['ridge|' + fs] = M.walk_forward(F, origins, h, lambda tr, te, fs=fs: M.fit_predict_ridge(tr, te, fs, h, S)[0])
    if 'catboost' in models:
        for fs in ('D', 'D+W'):
            out['catboost|' + fs] = M.walk_forward(F, origins, h, lambda tr, te, fs=fs: M.fit_predict_catboost(tr, te, fs, S_FAST, 1))
    return F, out


def compare(out, a, b):
    A, B = out[a], out[b]
    assert (A.origin_mi.to_numpy() == B.origin_mi.to_numpy()).all() and (A.node_id.to_numpy() == B.node_id.to_numpy()).all()
    return M.compare_models(A.origin_mi.to_numpy(), (A.y_hat - A.y).abs().to_numpy(), (B.y_hat - B.y).abs().to_numpy(), S)


def test_lagged_interest_signal_makes_dw_beat_d():
    w = sim.make_world(beta=1.0, seed=21, n_broad=2, n_mid=2, n_narrow=3)
    F, out = run(w)
    r = compare(out, 'ridge|D', 'ridge|D+W')
    assert r['skill'] > 0.3 and M.helps(r, S), r                      # the signal is strong and the ridge can use it
    c = compare(out, 'catboost|D', 'catboost|D+W')
    assert c['skill'] > 0.1 and c['ci_lo'] > 0 and M.helps(c, S), c   # CatBoost finds it too


def test_horizon_two_signal_is_also_found():
    w = sim.make_world(beta=1.0, seed=22)
    F, out = run(w, models=('ridge',), h=2, last='2022-06')
    r = compare(out, 'ridge|D', 'ridge|D+W')
    assert r['skill'] > 0.05, r        # y(t+2) depends on s(t+1) which is not known at t: a smaller but real gain through the AR link


def test_null_world_gives_no_reliable_gain():
    skills = []
    for seed in (31, 32, 33):
        w = sim.make_world(beta=0.0, seed=seed)
        F, out = run(w, last='2022-06')
        r = compare(out, 'ridge|D', 'ridge|D+W')
        c = compare(out, 'catboost|D', 'catboost|D+W')
        skills += [r['skill'], c['skill']]
        assert not M.helps(r, S), (seed, r)
        assert not M.helps(c, S), (seed, c)
        assert abs(r['skill']) < 0.08 and abs(c['skill']) < 0.12, (seed, r['skill'], c['skill'])
    assert np.mean(skills) < 0.02                                        # no systematic gain across worlds


def test_baselines_are_sensible_in_the_signal_world():
    w = sim.make_world(beta=1.0, seed=23)
    F = sim.build(w, S)
    te = F[(F.h == 1) & (F.origin_mi.between(MI('2019-01'), MI('2022-12')))]
    mae_naive = np.abs(M.naive(te) - te.y).mean()
    mae_snaive = np.nanmean(np.abs(M.seasonal_naive(te) - te.y))
    assert np.isfinite(mae_naive) and np.isfinite(mae_snaive) and mae_naive > 0
