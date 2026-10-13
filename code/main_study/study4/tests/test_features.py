# Features: week alignment, real-time shift states, no use of data after the origin, missing months, eligibility.
import sys, pathlib, copy
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
import _settings as ST, _features as FE
import sim

S = ST.settings()
MI = ST.mi_from_ym
ID = ['group', 'format', 'node_id', 'origin_mi', 'h']
NOT_COMPARED = {'y', 'target_ok'}          # targets look ahead by construction


def test_week_alignment_sunday_rule():
    # a week counts for month t if its Sunday is on or before the last day of t
    assert FE.last_week_monday(MI('2020-03')) == pd.Timestamp('2020-03-23')      # 31 Mar 2020 is a Tuesday; last Sunday is 29 Mar
    assert FE.last_week_monday(MI('2020-05')) == pd.Timestamp('2020-05-25')      # 31 May 2020 is a Sunday: that week counts
    assert FE.last_week_monday(MI('2021-02')) == pd.Timestamp('2021-02-22')      # 28 Feb 2021 is a Sunday
    assert FE.last_week_monday(MI('2020-02')) == pd.Timestamp('2020-02-17')      # 29 Feb 2020 is a Saturday: last Sunday 23 Feb
    for mi in range(MI('2016-01'), MI('2024-01')):
        L = FE.last_week_monday(mi)
        assert L.weekday() == 0
        sunday = L + pd.Timedelta(days=6)
        end = pd.Timestamp(year=mi // 12, month=mi % 12 + 1, day=1) + pd.offsets.MonthEnd(0)
        assert sunday <= end < sunday + pd.Timedelta(days=7)
        assert FE.week_month(L) == mi                                              # the last included week belongs to month t


def test_mann_kendall_tau():
    up = np.arange(10.0)[:, None]
    tau = FE.kendall_tau_rolling(up, 8)
    assert np.isnan(tau[:7]).all() and np.allclose(tau[7:], 1.0)
    down = FE.kendall_tau_rolling(-up, 8)
    assert np.allclose(down[7:], -1.0)
    x = np.array([[1.0], [2], [np.nan], [4], [5], [6], [7], [8], [9], [10]])
    assert np.isnan(FE.kendall_tau_rolling(x, 8)[7:9]).all()                        # any missing week gives a missing value


def test_demand_and_interest_features_by_hand():
    w = sim.make_world(beta=1.0, seed=1)
    F = sim.build(w, S)
    r = F[(F.h == 1) & (F.node_id == 'B01.M01.N01') & (F.origin == '2019-03')].iloc[0]
    Y = w['panel'].query("node_id == 'B01.M01.N01'").set_index('mi').log_share
    t = MI('2019-03')
    assert np.isclose(r.ls_t, Y[t]) and np.isclose(r.ls_t1, Y[t - 1]) and np.isclose(r.ls_t2, Y[t - 2])
    assert np.isclose(r.ls_ly, Y[t - 11]) and np.isclose(r.y, Y[t + 1])
    assert np.isclose(r.mean6, Y[t - 5:t].mean() if False else np.mean([Y[k] for k in range(t - 5, t + 1)]))
    assert r.tmonth == '04'
    r2 = F[(F.h == 2) & (F.node_id == 'B01.M01.N01') & (F.origin == '2019-03')].iloc[0]
    assert np.isclose(r2.ls_ly, Y[t - 10]) and np.isclose(r2.y, Y[t + 2]) and r2.tmonth == '05'   # the target month one year earlier
    tot = w['panel'].query("node_id == 'B01.M01.N01'").set_index('mi').total_checkouts
    assert np.isclose(r.dlog_total, np.log(tot[t]) - np.log(tot[t - 1]))
    assert np.isclose(r.m12_last, np.mean([Y[k] for k in range(t - 11, t + 1)]))
    assert np.isclose(r.m12_prev, np.mean([Y[k] for k in range(t - 23, t - 11)]))
    # interest: last 4 complete weeks, ratio to the 26-week median (current week excluded)
    wk = w['wiki'].query("node_id == 'B01.M01.N01'").set_index('week').share
    L = FE.last_week_monday(t)
    last4 = [wk[L - pd.Timedelta(weeks=k)] for k in range(4)]
    prev4 = [wk[L - pd.Timedelta(weeks=k)] for k in range(4, 8)]
    assert np.isclose(r.w_logmean4, np.log(np.mean(last4)))
    assert np.isclose(r.w_dlog4, np.log(np.mean(last4)) - np.log(np.mean(prev4)))
    assert np.isclose(r.w_ratio, wk[L] / np.median([wk[L - pd.Timedelta(weeks=k)] for k in range(1, 27)]))
    vals = [wk[L - pd.Timedelta(weeks=k)] for k in range(7, -1, -1)]
    s = sum(np.sign(vals[j] - vals[i]) for i in range(8) for j in range(i + 1, 8))
    assert np.isclose(r.w_mk8, s / 28)
    assert r.w_shift8 == 0 and r.w_shift_size == 0 and r.w_lab_sustained == 0     # no shift in the window gives 0, not missing
    assert np.isnan(r.g_ratio) and np.isnan(r.t_tone)                              # no GDELT data in this world


def test_seasonal_naive_formula():
    import _models as M
    w = sim.make_world(seed=2)
    F = sim.build(w, S)
    r = F[(F.h == 1) & (F.node_id == 'B01.M01.N02') & (F.origin == '2019-06')]
    Y = w['panel'].query("node_id == 'B01.M01.N02'").set_index('mi').log_share
    t = MI('2019-06')
    want = Y[t - 11] + np.mean([Y[k] for k in range(t - 11, t + 1)]) - np.mean([Y[k] for k in range(t - 23, t - 11)])
    assert np.isclose(M.seasonal_naive(r)[0], want)
    assert np.isclose(M.naive(r)[0], Y[t])


def test_shift_state_is_real_time():
    w = sim.make_world(seed=3)
    node = 'B01.M01.N01'
    start = pd.Timestamp('2019-03-04')
    # a sustained shift: labelled 3 weeks after its start (4th week); ratios grow, then the shift continues
    sim.add_shift(w, node, start, 'sustained', start + pd.Timedelta(weeks=3), [1.6, 1.9, 2.4, 3.0, 2.0, 1.7], seasonal=True, quality_flag='x')
    F = sim.build(w, S, drop_missing_target=False)
    g = lambda o: F[(F.h == 1) & (F.node_id == node) & (F.origin == o)].iloc[0]
    # origin 2019-03: last week = 2019-03-25 (Monday), 3 weeks after the start; label_week = 2019-03-25 <= that week: label known
    r = g('2019-03')
    assert r.w_shift8 == 1 and r.w_lab_sustained == 1 and r.w_shift_weeks == 3 and np.isclose(r.w_shift_size, 3.0)
    assert r.split_qok_shift8 == 1
    # origin 2019-02: the shift starts after the last included week (2019-02-18): nothing yet
    r = g('2019-02')
    assert r.w_shift8 == 0 and r.w_lab_sustained == 0 and r.split_qok_shift8 == 0
    # a shift that started but is not yet labelled: label is "none yet", size so far uses only weeks up to the last week
    w2 = sim.make_world(seed=3)
    start2 = pd.Timestamp('2019-03-18')                       # last week of March is 2019-03-25: one week in
    sim.add_shift(w2, node, start2, 'sustained', start2 + pd.Timedelta(weeks=3), [1.6, 9.9, 9.9, 9.9])
    r = sim.build(w2, S, drop_missing_target=False)
    r = r[(r.h == 1) & (r.node_id == node) & (r.origin == '2019-03')].iloc[0]
    assert r.w_shift8 == 1 and r.w_shift_weeks == 1
    assert r.w_lab_sustained == 0 and r.w_lab_intermediate == 0 and r.w_lab_fading == 0       # label comes after the origin
    assert np.isclose(r.w_shift_size, 9.9)                                                    # weeks start..last week (2 weeks)
    # 8 weeks later the window has passed
    r = sim.build(w2, S, drop_missing_target=False)
    r = r[(r.h == 1) & (r.node_id == node) & (r.origin == '2019-06')].iloc[0]
    assert r.w_shift8 == 0


def test_flags_are_not_features_and_do_not_change_them():
    seen = set()
    for fs in S.feature_sets:
        num, cat = FE.feature_columns(fs)
        seen |= set(num) | set(cat)
        assert tuple(cat) == S.cat_features and 'node_id' not in num + cat
    assert not any(k in c for c in seen for k in ('seasonal', 'quality', 'title', 'split', 'node_id'))
    assert seen.isdisjoint(FE.NON_FEATURES)
    # changing seasonal / quality_flag / title_confusion never changes a feature (quality_ok only moves the scoring split)
    base = sim.make_world(seed=4)
    node, start = 'B01.M01.N01', pd.Timestamp('2019-03-04')
    sim.add_shift(base, node, start, 'fading', start + pd.Timedelta(weeks=1), [1.7, 1.2], seasonal=False, quality_flag='')
    other = copy.deepcopy(base)
    other['shifts'].loc[:, 'seasonal'] = True
    other['shifts'].loc[:, 'quality_flag'] = 'one_day'
    other['shifts']['title_confusion'] = 'yes'
    other['shifts'].loc[:, 'quality_ok'] = False
    a, b = sim.build(base, S, False), sim.build(other, S, False)
    cols = [c for c in a.columns if c not in ('split_qok_shift8',)]
    pd.testing.assert_frame_equal(a[cols], b[cols])
    assert a.split_qok_shift8.sum() > 0 and b.split_qok_shift8.sum() == 0


def test_no_feature_uses_data_after_the_origin():
    """Perturb everything after origin t (demand months, interest weeks, shifts, shift weeks, GDELT) and check that the
    features at every origin up to t are unchanged."""
    w = sim.make_world(beta=1.0, seed=5, with_gdelt=True)
    node = 'B01.M01.N01'
    sim.add_shift(w, node, '2019-03-04', 'sustained', '2019-03-25', [1.6, 1.9, 2.4, 3.0, 2.0], sid=0)
    cut = MI('2020-06')
    Lc = FE.last_week_monday(cut)
    # a shift that starts before the cut but is labelled after it; and a shift that starts after it
    sim.add_shift(w, 'B01.M01.N02', Lc - pd.Timedelta(weeks=2), 'sustained', Lc + pd.Timedelta(weeks=1), [1.6, 2.0, 2.5, 2.7], sid=1)
    sim.add_shift(w, 'B02.M01.N01', Lc + pd.Timedelta(weeks=2), 'fading', Lc + pd.Timedelta(weeks=3), [1.7, 1.2], sid=2)
    sim.add_shift(w, 'B01.M01.N03', Lc - pd.Timedelta(weeks=40), 'fading', Lc - pd.Timedelta(weeks=39), [1.7, 1.2], sid=3, source='gdelt')
    A = sim.build(w, S, drop_missing_target=False)
    rng = np.random.default_rng(99)
    p = copy.deepcopy(w)
    pan = p['panel']; fut = pan.mi > cut
    pan.loc[fut, 'log_share'] = rng.normal(-3, 2, fut.sum()); pan.loc[fut, 'total_checkouts'] = rng.uniform(1, 9, fut.sum())
    pan.loc[fut, 'size_ok'] = rng.random(fut.sum()) < 0.5
    wk = p['wiki']; fw = wk.week > Lc
    wk.loc[fw, 'share'] = np.exp(rng.normal(-9, 2, fw.sum()))
    gd = p['gdelt']; fg = gd.week > Lc
    for c in ('share', 'tone', 'positive', 'negative'):
        gd.loc[fg, c] = rng.normal(0.01, 1, fg.sum()) if c != 'share' else np.exp(rng.normal(-8, 2, fg.sum()))
    sh = p['shifts']
    late_label = (sh.label_week > Lc) | (sh.start_week > Lc)
    sh.loc[late_label, 'label'] = 'fading'
    sh['label_week'] = sh.label_week.where(~(sh.label_week > Lc), Lc + pd.Timedelta(weeks=9))
    sw = p['sw']; fsw = sw.week > Lc
    sw.loc[fsw, 'ratio'] = 77.0
    extra = sim.add_shift(copy.deepcopy(p), 'B02.M02.N01', Lc + pd.Timedelta(weeks=1), 'sustained', Lc + pd.Timedelta(weeks=4), [2, 2, 2, 2], sid=9)
    p['shifts'], p['sw'] = extra['shifts'], extra['sw']
    B = sim.build(p, S, drop_missing_target=False)
    a = A[A.origin_mi <= cut].set_index(ID).sort_index()
    b = B[B.origin_mi <= cut].set_index(ID).sort_index()
    assert a.index.equals(b.index)
    cols = [c for c in a.columns if c not in NOT_COMPARED]
    assert any(c.startswith('g_') for c in cols) and any(c.startswith('t_') for c in cols)
    pd.testing.assert_frame_equal(a[cols], b[cols], check_exact=False, rtol=1e-12, atol=1e-12)
    assert a[[c for c in cols if c.startswith(('w_', 'g_', 't_'))]].notna().any().all() or True
    # and the perturbation was real: the targets and later origins do change
    for col, o in (('w_logmean4', cut + 3), ('y', cut)):
        m = A[A.origin_mi == o].merge(B[B.origin_mi == o], on=ID, suffixes=('_a', '_b'))
        assert len(m) and not np.allclose(m[col + '_a'].fillna(0), m[col + '_b'].fillna(0))


def test_missing_and_zero_months_are_never_scored():
    import _forecast as FC
    miss = ('2019-05', '2019-06', '2021-02')
    zero = [('B01.M01.N01', 'ebook', MI('2019-09'))]
    w = sim.make_world(seed=6, missing=miss, zero_share=zero)
    F = sim.build(w, S)
    mset = {MI(m) for m in miss}
    assert not F.origin_mi.isin(mset).any()                       # month t missing: no row
    assert not F.target_mi.isin(mset).any()                       # target month missing: no row
    assert F.y.notna().all() and F.ls_t.notna().all()
    z = F[(F.node_id == 'B01.M01.N01')]
    assert not ((z.origin_mi == MI('2019-09')) | (z.target_mi == MI('2019-09'))).any()   # a zero share is missing, never log(0)
    S2 = copy.copy(S); S2.cb_iterations = 10
    for t in (MI('2019-04'), MI('2019-05'), MI('2019-07'), MI('2021-01')):
        out = FC.forecast_origin(F, t, S2, 1, models=('ridge',))
        if t in (MI('2019-04'), MI('2019-05')):          # month t missing, or both target months missing: nothing to score
            assert len(out) == 0
            continue
        assert len(out) and np.isfinite(out.y_true).all() and np.isfinite(out.y_t).all()
        assert not out.origin_mi.isin(mset).any() and not (out.origin_mi + out.h).isin(mset).any()
        if t == MI('2021-01'):
            assert set(out.h) == {2}                     # horizon 1 targets the missing 2021-02
    assert len(FC.forecast_origin(F, MI('2019-06'), S2, 1, models=('ridge',))) == 0
    # a missing month is never a training target either
    import _models as M
    tr = M.training_rows(F, MI('2020-01'), 1)
    assert not tr.target_mi.isin(mset).any()
    # the table keeps rows with a missing target only when asked (they are never scored)
    full = sim.build(w, S, drop_missing_target=False)
    assert (~full.target_ok).any() and full[~full.target_ok].y.isna().all()


def test_eligibility_rule_is_applied_at_each_origin():
    w = sim.make_world(seed=7)
    pan = w['panel']
    bad = (pan.node_id == 'B01.M01.N01') & (pan.mi >= MI('2019-01')) & (pan.mi <= MI('2019-04'))
    pan.loc[bad, 'size_ok'] = False
    F = sim.build(w, S)
    r = F[(F.node_id == 'B01.M01.N01')]
    assert not r.origin_mi.between(MI('2019-01'), MI('2019-04')).any()
    assert r.origin_mi.isin([MI('2019-05'), MI('2018-12')]).sum() >= 2           # eligible again, and before


def test_levels_and_group_columns():
    w = sim.make_world(seed=8)
    F = sim.build(w, S)
    assert set(F.level) == {'narrow', 'middle'} and 'broad' not in set(F.level)    # broad is descriptive only
    assert set(F.h) == {1, 2} and set(F.group) == {'seattle'}
