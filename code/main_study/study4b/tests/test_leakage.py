# Future-perturbation leakage check: change everything after the origin (interest weeks, demand months, shifts and their labels,
# Study 3 effects whose window is not over) and every forecast made at the origin must stay the same, to the last digit.
import sys, pathlib, copy
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
from helpers import *
import _s4

FE = _s4.features
BL = fast_settings(60)
ORIGIN = MI('2020-06')


def _base_world():
    w = world(beta=1.0, seed=81, n_broad=2, n_mid=2, n_narrow=3)
    n1, n2 = w['leaf'][0], w['leaf'][1]
    L = FE.last_week_monday(ORIGIN)
    s1 = L - pd.Timedelta(weeks=5)                             # sustained, labelled before the origin
    sim.add_shift(w, n1, s1, 'sustained', s1 + pd.Timedelta(weeks=3), [2.0, 2.4, 3.0, 2.8, 2.5, 2.2])
    s2 = L - pd.Timedelta(weeks=1)                             # labelled after the origin
    sim.add_shift(w, n2, s2, 'sustained', s2 + pd.Timedelta(weeks=3), [2.0, 2.4, 3.0, 2.8], sid=1)
    e = empty_effects()
    for node in (n1, n2):
        for fmt in ('print', 'ebook'):
            for m0, v in [('2019-02', 0.2), ('2019-10', -0.1), ('2020-03', 0.3), ('2020-05', 0.4), ('2020-09', 0.5)]:
                e = add_effect(e, node, fmt, MI(m0), v)
    return w, e


def _perturb(w, e, seed=5):
    """Return a copy with everything after the origin changed."""
    rng = np.random.default_rng(seed)
    w2 = {k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in w.items()}
    L = FE.last_week_monday(ORIGIN)
    wk = w2['wiki']
    late = pd.to_datetime(wk.week) > L                         # weeks whose Sunday is after the origin month's last included week
    wk.loc[late, 'share'] = wk.loc[late, 'share'] * np.exp(rng.normal(0, 2.0, late.sum()))
    p = w2['panel']
    fut = p.mi > ORIGIN
    p.loc[fut, 'log_share'] = p.loc[fut, 'log_share'] + rng.normal(0, 1.0, fut.sum())
    p.loc[fut, 'total_checkouts'] = p.loc[fut, 'total_checkouts'] * np.exp(rng.normal(0, 0.5, fut.sum()))
    sh = w2['shifts']
    sh.loc[sh.label_week > L, 'label'] = 'fading'             # a label given after the origin changes
    sh['label_week'] = sh.label_week
    sim.add_shift(w2, w['leaf'][2], L + pd.Timedelta(weeks=1), 'sustained', L + pd.Timedelta(weeks=4), [3.0, 3.0, 3.0])   # a new shift after
    e2 = e.copy()
    e2.loc[e2.m0 + 2 > ORIGIN, 'sc_effect_p'] = 9.0
    return w2, e2


def test_origin_forecasts_do_not_change_when_the_future_is_perturbed():
    w, e = _base_world()
    w2, e2 = _perturb(w, e)
    F1, F2 = features(w, e, BL), features(w2, e2, BL)
    # every feature of every row whose origin is not after ORIGIN is unchanged
    a = F1[F1.origin_mi <= ORIGIN].sort_values(['h', 'origin_mi', 'format', 'node_id']).reset_index(drop=True)
    b = F2[F2.origin_mi <= ORIGIN].sort_values(['h', 'origin_mi', 'format', 'node_id']).reset_index(drop=True)
    assert len(a) == len(b) and (a[['h', 'origin_mi', 'format', 'node_id']] == b[['h', 'origin_mi', 'format', 'node_id']]).all().all()
    feat_cols = FE.D_NUM + FE.W_NUM + BF.S_NUM + ['m12_last', 'm12_prev', 'split_qok_shift8']
    for c in feat_cols:
        assert np.allclose(a[c].to_numpy(float), b[c].to_numpy(float), equal_nan=True, atol=0, rtol=0), c
    # something did change in the future, so the test is not vacuous
    assert not np.allclose(F1[F1.origin_mi == ORIGIN + 3].s_resp, F2[F2.origin_mi == ORIGIN + 3].s_resp) or \
        not np.allclose(F1[F1.origin_mi == ORIGIN + 2].ls_t, F2[F2.origin_mi == ORIGIN + 2].ls_t)
    # forecasts at the origin from every model, both parts, all horizons
    f1 = BR.forecast_origin(F1, ORIGIN, BL, 1)
    f2 = BR.forecast_origin(F2, ORIGIN, BL, 1)
    assert len(f1) == len(f2) > 0
    assert set(f1.part) == {'A', 'B'} and set(f1.model) == {'zero', 'ridge', 'catboost', 'catboost_clf', 'logistic'} and set(f1.h) == {1, 2, 3}
    k = ['part', 'model', 'fset', 'h', 'format', 'node_id']
    m = f1.merge(f2, on=k, suffixes=('_1', '_2'), validate='one_to_one')
    assert len(m) == len(f1)
    assert (m.pred_1 == m.pred_2).all(), m[m.pred_1 != m.pred_2][k + ['pred_1', 'pred_2']].head()
    assert (m.ls_t_1 == m.ls_t_2).all()
    assert not (m.target_1 == m.target_2).all()                  # the realised changes (the future) did change


def test_training_rows_only_use_targets_observed_by_the_origin():
    w, e = _base_world()
    F = features(w, e, BL)
    for h in B.horizons:
        tr = _s4.models.training_rows(F, ORIGIN, h)
        assert (tr.origin_mi + h <= ORIGIN).all() and (tr.target_mi <= ORIGIN).all() and tr.change.notna().all()
        te = _s4.models.test_rows(F, ORIGIN, h)
        assert (te.origin_mi == ORIGIN).all()
