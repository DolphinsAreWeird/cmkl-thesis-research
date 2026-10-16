# Simulated worlds. Signal world: interest drives the change, so D+W beats D (Part A) and finds surges (Part B). Null world: interest
# is noise, so nothing helps. Fewer CatBoost trees than the record (tests only).
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
from helpers import *

BF_ = fast_settings(150, horizons=(2,))


def _fc(w, first='2019-01', last='2021-06'):
    F = features(w, b=BF_)
    return F, run_origins(F, BF_, first, last)


def test_signal_world_dw_beats_d_and_zero_change_for_part_a():
    F, Fc = _fc(world(beta=1.0, seed=51, n_broad=2, n_mid=2, n_narrow=3))
    Wa, _ = EV.wide_a(Fc)
    for cls in ('ridge', 'catboost'):
        t = EV.compare_a(Wa, f'{cls}|D', f'{cls}|D+W', 2, BF_)
        pooled = t[t.scope.str.startswith(EV.POOLED)]
        assert len(pooled) == 2 and pooled.skill.min() > 0.05, (cls, pooled)
        assert pooled.helps.all(), (cls, pooled)
        tz = EV.compare_a(Wa, 'zero', f'{cls}|D+W', 2, BF_)
        assert tz[tz.scope.str.startswith(EV.POOLED)].helps.all(), cls          # and beats zero change
    # D+W+S has no shifts or effects in this world, so S is constant and cannot hurt much
    t = EV.compare_a(Wa, 'ridge|D+W', 'ridge|D+W+S', 2, BF_)
    assert abs(t[t.scope.str.startswith(EV.POOLED)].skill).max() < 0.05


def test_signal_world_dw_finds_surges_better_than_d_for_part_b():
    F, Fc = _fc(world(beta=1.0, seed=52, n_broad=2, n_mid=2, n_narrow=3))
    Wb, _ = EV.wide_b(Fc, BF_)
    assert Wb.surge.sum() > 30
    pairs = [('logistic', 'logistic|D', 'logistic|D+W'), ('catboost_clf', 'catboost_clf|D', 'catboost_clf|D+W')]
    t = EV.ap_diff_table(Wb, pairs, BF_)
    pooled = t[t.scope.str.startswith(EV.POOLED)]
    assert (pooled.ap_diff > 0).all() and pooled.helps.any(), pooled
    s = EV.surge_table(Wb, ['logistic|D', 'logistic|D+W'], BF_)
    d, dw = (s[(s.scope.str.startswith(EV.POOLED)) & (s.model == m)].ap.mean() for m in ('logistic|D', 'logistic|D+W'))
    assert dw > d


def test_null_world_gives_no_reliable_gain_in_either_part():
    for seed in (61, 62, 63):
        F, Fc = _fc(world(beta=0.0, seed=seed, noise=0.2), last='2021-03')
        Wa, _ = EV.wide_a(Fc)
        Wb, _ = EV.wide_b(Fc, BF_)
        for cls in ('ridge', 'catboost'):
            t = EV.compare_a(Wa, f'{cls}|D', f'{cls}|D+W', 2, BF_)
            assert not t[t.scope.str.startswith(EV.POOLED)].helps.any(), (seed, cls, t)
            assert abs(t[t.scope.str.startswith(EV.POOLED)].skill).max() < 0.12, (seed, cls)
        if Wb.surge.sum() >= 5:
            t = EV.ap_diff_table(Wb, [('logistic', 'logistic|D', 'logistic|D+W'), ('catboost_clf', 'catboost_clf|D', 'catboost_clf|D+W')], BF_)
            assert not t[t.scope.str.startswith(EV.POOLED)].helps.any(), (seed, t)


def test_responsiveness_feature_is_used_when_it_carries_the_signal():
    """A world where effects, not interest, tell which categories react: D+W+S must not do worse than D+W by the S column's presence."""
    w = world(beta=0.0, seed=71)
    F = features(w, b=BF_)
    assert (F.s_resp == 0).all() and (F.s_sustained == 0).all()
    num, _ = BF.feature_columns('D+W+S')
    assert all(c in F.columns for c in num)
