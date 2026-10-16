# S features, responsiveness, change target and surge label; no look-ahead in any of them.
import sys, pathlib, math
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
from helpers import *
import _b_features as BF
import _s4

FE = _s4.features


def keys(node, fmt, origins):
    return pd.DataFrame(dict(node_id=node, format=fmt, origin_mi=[MI(o) for o in origins]))


def test_responsiveness_uses_only_shifts_whose_effect_window_ended_by_the_origin():
    e = empty_effects()
    e = add_effect(e, 'N1', 'print', MI('2020-01'), 0.30)        # window 2020-01..03: usable from origin 2020-03
    e = add_effect(e, 'N1', 'print', MI('2020-06'), -0.10)       # usable from 2020-08
    e = add_effect(e, 'N1', 'ebook', MI('2020-01'), 0.9)         # other format: never used for print
    e = add_effect(e, 'N2', 'print', MI('2020-01'), 0.9)         # other category
    e = add_effect(e, 'N1', 'print', MI('2020-01'), 0.9, source='gdelt')
    e = add_effect(e, 'N1', 'print', MI('2020-01'), 0.9, analysis='seasonal')
    e = add_effect(e, 'N1', 'print', MI('2020-01'), 0.9, sc_ok=False)
    eff = BF.prepare_effects(e, B)
    k = keys('N1', 'print', ['2020-02', '2020-03', '2020-07', '2020-08', '2021-01'])
    r = BF.responsiveness(k, eff)
    assert np.allclose(r, [0.0, 0.30, 0.30, 0.10, 0.10]), r      # (0.30 + -0.10) / 2 = 0.10 from 2020-08
    assert BF.responsiveness(keys('N3', 'print', ['2021-01']), eff)[0] == 0.0     # none -> 0
    assert BF.responsiveness(k, BF.prepare_effects(empty_effects(), B)).sum() == 0


def test_responsiveness_ignores_perturbed_future_shifts():
    base = empty_effects()
    for m0, v in [('2019-03', 0.2), ('2019-09', 0.4), ('2020-02', -0.2)]:
        base = add_effect(base, 'N1', 'print', MI(m0), v)
    t = MI('2020-03')                                             # the 2020-02 shift ends 2020-04: not usable at 2020-03
    k = keys('N1', 'print', ['2020-03'])
    r0 = BF.responsiveness(k, BF.prepare_effects(base, B))[0]
    pert = base.copy()
    pert.loc[pert.m0 >= t - 1, 'sc_effect_p'] = 123.0             # change every shift whose window is not over at t
    r1 = BF.responsiveness(k, BF.prepare_effects(pert, B))[0]
    assert r0 == r1 == np.mean([0.2, 0.4])
    for extra in range(1, 6):                                      # added future shifts change nothing either
        base = add_effect(base, 'N1', 'print', t - 1 + extra, 50.0)
    assert BF.responsiveness(k, BF.prepare_effects(base, B))[0] == r0


def test_responsiveness_on_the_real_effects_matches_a_brute_force_rule():
    import ST_real
    se = ST_real.effects()
    eff = BF.prepare_effects(se, B)
    sample = eff.drop_duplicates(['node_id', 'format']).head(25)
    for r in sample.itertuples():
        for origin in range(MI('2018-01'), MI('2026-07'), 7):
            got = BF.responsiveness(pd.DataFrame(dict(node_id=[r.node_id], format=[r.format], origin_mi=[origin])), eff)[0]
            rows = se[(se.source == 'wikipedia') & (se.analysis == 'main') & (se.node_id == r.node_id) & (se.format == r.format)
                      & se.sc_ok.fillna(False).astype(bool) & se.sc_effect_p.notna() & (se.m0 + 2 <= origin)]
            want = rows.sc_effect_p.mean() if len(rows) else 0.0
            assert math.isclose(got, want, abs_tol=1e-12), (r.node_id, r.format, origin, got, want)


def _shift_frame(rows):
    cols = ['source', 'node_id', 'id', 'start_week', 'label', 'label_week', 'quality_ok']
    d = pd.DataFrame(rows, columns=cols)
    d['start_week'] = pd.to_datetime(d.start_week).astype('datetime64[us]')
    d['label_week'] = pd.to_datetime(d.label_week).astype('datetime64[us]')
    return d


def test_sustained_flag_rules():
    L = FE.last_week_monday(MI('2020-06'))                        # last included week of the origin month
    start = L - pd.Timedelta(weeks=3)                             # started 3 weeks before L; labelled in its 4th week (= L)
    rows = [('wikipedia', 'A', 0, start, 'sustained', start + pd.Timedelta(weeks=3), True),
            ('wikipedia', 'B', 0, start, 'sustained', start + pd.Timedelta(weeks=3), False),    # not quality_ok
            ('wikipedia', 'C', 0, start, 'fading', start + pd.Timedelta(weeks=1), True),        # other label
            ('gdelt', 'D', 0, start, 'sustained', start + pd.Timedelta(weeks=3), True),         # other source
            ('wikipedia', 'E', 0, L - pd.Timedelta(weeks=8), 'sustained', L - pd.Timedelta(weeks=5), True),   # started 8 weeks before L: outside the 8-week window
            ('wikipedia', 'F', 0, L - pd.Timedelta(weeks=7), 'sustained', L - pd.Timedelta(weeks=4), True),   # 7 weeks before: inside
            ('wikipedia', 'G', 0, L - pd.Timedelta(weeks=2), 'sustained', L + pd.Timedelta(weeks=1), True),   # labelled after L: not yet known
            ('wikipedia', 'H', 0, L + pd.Timedelta(weeks=1), 'sustained', L + pd.Timedelta(weeks=4), True)]  # starts after L
    f = BF.sustained_flags(_shift_frame(rows), [MI('2020-06')], B)
    assert sorted(f.node_id) == ['A', 'F'], f
    f2 = BF.sustained_flags(_shift_frame(rows), [MI('2020-07')], B)
    assert 'G' in set(f2.node_id) and 'A' in set(f2.node_id) and 'H' in set(f2.node_id)       # known / inside later


def test_sustained_flag_in_the_table_is_zero_not_missing_and_no_leak():
    w = world(beta=0.0, seed=3)
    n = w['leaf'][0]
    start = FE.last_week_monday(MI('2020-06')) - pd.Timedelta(weeks=2)
    sim.add_shift(w, n, start, 'sustained', start + pd.Timedelta(weeks=3), [2.0, 2.5, 3.0, 2.8])
    F = features(w)
    r = F[(F.node_id == n) & (F.format == 'print') & (F.h == 2)].set_index('origin_mi')
    assert r.s_sustained.notna().all()
    assert r.loc[MI('2020-06'), 's_sustained'] == 0.0             # labelled one week after the origin's last week
    assert r.loc[MI('2020-07'), 's_sustained'] == 1.0
    assert r.loc[:MI('2020-05'), 's_sustained'].sum() == 0.0


def test_change_target_and_surge_label():
    w = world(beta=1.0, seed=4)
    F = features(w)
    assert np.allclose(F.change, F.y - F.ls_t) and F.change.notna().all()
    assert ((F.change >= math.log(1.3)).astype(float) == F.surge).all()
    assert F.surge.mean() > 0
    edge = F.iloc[:1].copy()
    e = pd.Series([math.log(1.3), math.log(1.3) - 1e-9, math.log(1.3) + 1e-9])
    assert list((e >= B.surge_change)) == [True, False, True]
    # the level forecast is ls_t + predicted change; the zero change forecast is the naive forecast
    te = F[(F.h == 2) & (F.origin_mi == MI('2019-06'))]
    assert (BM.zero_change(te) == 0).all() and np.allclose(te.ls_t + BM.zero_change(te), te.ls_t)


def test_feature_sets_contain_only_known_columns():
    for fs, extra in (('D', []), ('D+W', FE.W_NUM), ('D+W+S', FE.W_NUM + BF.S_NUM)):
        num, cat = BF.feature_columns(fs)
        assert set(num) == set(FE.D_NUM + extra), fs
        assert cat == ['format', 'level', 'broad_id', 'tmonth']
        assert not set(num + cat) & set(BF.NON_FEATURES) - {'tmonth_int'}, fs
    assert 'change' in BF.NON_FEATURES and 'surge' in BF.NON_FEATURES and 'y' in BF.NON_FEATURES
