# Inference on simulated panels: an injected effect is recovered at about the right size, p-values are about
# uniform when nothing happened, the donor rules hold, placebo years skip shift years, and power behaves.
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from scipy import stats
from _settings import SETTINGS as S
import _methods as M
import _analysis as A
import _sim
from _build import mi_from_ym

_W = {}


def world(null=True, seed=11):
    if (null, seed) not in _W:
        _W[(null, seed)] = _sim.sim_world(S, seed=seed, null=null, librivox=False)
    return _W[(null, seed)]


def ctx_of(W, shifts=None):
    return A.Context(W['panel'], W['nodes'], W['overlap'], shifts, S)


def random_units(ctx, rng, n, key=('narrow', 'audiobook'), lo='2018-01', hi='2025-06'):
    cand = [(u, m) for u, m in A.power_candidates(ctx, *key) if mi_from_ym(lo) <= m <= mi_from_ym(hi)]
    return [cand[i] for i in rng.choice(len(cand), n, replace=False)]


def test_injected_effect_recovered_at_the_right_size():
    ctx = ctx_of(world())
    rng = np.random.default_rng(0)
    lift = 0.3
    es, sc, p = [], [], []
    for node, m0 in random_units(ctx, rng, 40):
        Y = ctx.Y[('narrow', 'audiobook')].copy()
        Y[node] = M.inject_lift(Y[node], m0, S.window_primary, lift)
        e = M.event_study(Y[node], m0, S)
        r = M.sc_test(Y, node, ctx.donors('narrow', 'audiobook', node, m0), m0, S)
        es.append(e['es_effect_p']); sc.append(r['sc_effect_p']); p.append(r['sc_p_p'])
    target = np.log1p(lift)
    assert abs(np.nanmean(sc) - target) < 0.03, (np.nanmean(sc), target)
    assert abs(np.nanmean(es) - target) < 0.05, (np.nanmean(es), target)
    assert np.nanmean(np.array(p) < S.alpha) > 0.8


def test_null_p_values_are_about_uniform():
    ctx = ctx_of(world())
    rng = np.random.default_rng(1)
    p, es = [], []
    for node, m0 in random_units(ctx, rng, 300):
        r = M.sc_test(ctx.Y[('narrow', 'audiobook')], node, ctx.donors('narrow', 'audiobook', node, m0), m0, S)
        p.append(r['sc_p_p']); es.append(r['sc_effect_p'])
    p = np.array(p)
    p = p[~np.isnan(p)]
    assert len(p) > 280
    assert abs(p.mean() - 0.5) < 0.06, p.mean()
    assert np.mean(p < S.alpha) < 0.09 and abs(np.mean(p < 0.5) - 0.5) < 0.08
    assert stats.kstest(p, 'uniform').statistic < 0.09
    assert abs(np.nanmean(es)) < 0.02                     # no effect -> mean estimate near zero


def test_donor_rules():
    W = world()
    N = W['nodes']
    narrow = N[N.level == 'narrow'].node_id.tolist()
    t = narrow[10]
    sib = [n for n in narrow if N.set_index('node_id').parent[n] == N.set_index('node_id').parent[t] and n != t]
    other = [n for n in narrow if n not in sib and n != t]
    ov = pd.DataFrame([('narrow', 'audiobook', t, other[0], 100, 30, 0.30), ('narrow', 'audiobook', t, other[1], 100, 10, 0.10)],
                      columns=W['overlap'].columns)
    m0 = mi_from_ym('2021-05')
    sh = pd.DataFrame({'node_id': [other[2], other[3]], 'm0': [m0 + S.donor_no_shift[1], m0 + S.donor_no_shift[1] + 1]})
    ctx = A.Context(W['panel'], N, ov, sh, S)
    d = ctx.donors('narrow', 'audiobook', t, m0)
    assert t not in d and not set(sib) & set(d)
    assert other[0] not in d and other[1] in d                    # > 10% overlap out, exactly 10% kept
    assert other[2] not in d and other[3] in d                    # shift at +6 out, at +7 kept
    small = [n for n in narrow if not ctx.size_ok('narrow', 'audiobook', n, m0)]
    assert small and not set(small) & set(d)


def test_placebo_years_skip_the_shift_year_and_years_with_shifts():
    W = world()
    node = W['nodes'][W['nodes'].level == 'narrow'].node_id.iloc[5]
    m0 = mi_from_ym('2021-04')
    sh = pd.DataFrame({'node_id': [node, node], 'm0': [m0, mi_from_ym('2019-02')]})   # 2019-04 is within +/-6 months
    ctx = A.Context(W['panel'], W['nodes'], W['overlap'], sh, S)
    r = A.placebo_years(ctx, 'narrow', 'audiobook', node, m0, {'es_effect_p': 0.0, 'sc_effect_p': 0.0})
    assert 2021 not in r['py_years'] and 2019 not in r['py_years'] and 2018 in r['py_years']
    assert min(r['py_years']) >= S.placebo_year_from


def test_power_rises_with_lift_and_is_unbiased():
    ctx = ctx_of(world())
    rng = np.random.default_rng(2)
    draws = []
    for node, m0 in random_units(ctx, rng, 25):
        draws += A.power_draw(ctx, 'narrow', 'ebook', node, m0, S.power_lifts)
    tab, mde = M.power_summary(draws, S)
    assert tab.rate.is_monotonic_increasing or tab.rate.diff().min() > -0.1
    assert np.allclose(tab.mean_effect, tab.true_log_lift, atol=0.03)
    assert tab.rate.iloc[-1] > 0.8 and not np.isnan(mde)


def test_simulated_shift_effects_track_the_truth():
    W = world(null=False, seed=5)
    sh = W['shifts']
    ctx = ctx_of(W, sh)
    s = sh[(sh.level == 'narrow') & ~sh.seasonal & ~sh.node_id.isin(W['controls'].values())].head(30)
    est, true = [], []
    for _, x in s.iterrows():
        r = A.test_unit(ctx, 'narrow', 'audiobook', x.node_id, int(x.m0), placebo_years_on=False)
        if r.get('skip') == '' and not np.isnan(r['sc_effect_p']):     # a window hit by the 2024 outage is not estimated
            est.append(r['sc_effect_p']); true.append(x.true_effect)
    est, true = np.array(est), np.array(true)
    assert len(est) >= 15 and np.corrcoef(est, true)[0, 1] > 0.8
