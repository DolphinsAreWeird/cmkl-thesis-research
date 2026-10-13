# Panel building on tiny hand-made data with known answers: weighted shares, missing months, zero months,
# the rolling 24-month size rule, partial months, title-word handling and donor overlap.
import sys, types, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from _settings import SETTINGS
import _build as B


def fake_S(**kw):
    s = types.SimpleNamespace(**{k: v for k, v in vars(SETTINGS).items()})
    for k, v in kw.items():
        setattr(s, k, v)
    return s


def tiny():
    """Months 2020-01..2020-06. Record 1 -> work 10, record 2 -> work 11, record 3 has no work."""
    ck = {1: [4, 6, 9, 0, 2, 0], 2: [10, 0, 5, 1, 0, 3], 3: [100, 100, 100, 100, 100, 100]}
    rows = pd.DataFrame([(r, 2020, m + 1, c) for r, cs in ck.items() for m, c in enumerate(cs) if c > 0 or r == 3],
                        columns=['record_id', 'year', 'month', 'checkouts'])
    rw = pd.DataFrame({'record_id': [1, 2], 'work_id': [10, 11]})
    wt = pd.DataFrame({'work_id': [10, 10, 11], 'node_id': ['A', 'B', 'A'], 'level': 'narrow', 'strength': [0.5, 0.5, 1.0]})
    nodes = pd.DataFrame({'node_id': ['A', 'B'], 'parent': ['P', 'P'], 'broad_id': ['X', 'X'], 'label': ['a', 'b']})
    return ck, rows, rw, wt, nodes


def test_weighted_shares_missing_and_zero_months():
    ck, rows, rw, wt, nodes = tiny()
    S = fake_S(size_lookback=2, min_works=1, min_median_weighted=0.0)
    wm, totals = B.work_month(rows, rw)
    st = B.month_status(totals, missing=('2020-03',))
    df = B.assemble(wm, wt, st, nodes, 'ebook', 'narrow', S).set_index(['node_id', 'ym'])
    for m in range(6):
        ym = f'2020-{m + 1:02d}'
        tot = ck[1][m] + ck[2][m] + ck[3][m]
        a = 0.5 * ck[1][m] + 1.0 * ck[2][m]
        b = 0.5 * ck[1][m]
        if ym == '2020-03':      # listed as missing: missing for every category, never zero
            assert not df.loc[('A', ym), 'month_ok'] and np.isnan(df.loc[('A', ym), 'weighted_checkouts'])
            assert np.isnan(df.loc[('A', ym), 'share']) and np.isnan(df.loc[('B', ym), 'log_share'])
            continue
        assert np.isclose(df.loc[('A', ym), 'weighted_checkouts'], a) and np.isclose(df.loc[('A', ym), 'share'], a / tot)
        assert np.isclose(df.loc[('B', ym), 'share'], b / tot)
        if b == 0:               # zero weighted checkouts: share 0 kept, log share missing (addendum b)
            assert df.loc[('B', ym), 'share'] == 0 and np.isnan(df.loc[('B', ym), 'log_share'])
        else:
            assert np.isclose(df.loc[('B', ym), 'log_share'], np.log(b / tot))
        assert df.loc[('A', ym), 'n_works_month'] == (ck[1][m] > 0) + (ck[2][m] > 0)


def test_rolling_distinct_works_matches_brute_force():
    rng = np.random.default_rng(0)
    L = 5
    grid = np.arange(100, 160)
    wm = pd.DataFrame([(w, m, int(rng.integers(1, 5))) for w in range(30) for m in grid if rng.random() < 0.15],
                      columns=['work_id', 'mi', 'checkouts'])
    wt = pd.DataFrame({'work_id': np.arange(30), 'node_id': np.where(np.arange(30) < 18, 'A', 'B'), 'strength': 1.0})
    wt = pd.concat([wt, pd.DataFrame({'work_id': [3, 4], 'node_id': ['B', 'B'], 'strength': 0.5})])
    got = B.rolling_distinct_works(wm, wt, grid, L)
    for node in ['A', 'B']:
        works = set(wt[wt.node_id == node].work_id)
        for t in grid:
            act = wm[(wm.mi >= t - L) & (wm.mi <= t - 1) & wm.work_id.isin(works) & (wm.checkouts > 0)].work_id.nunique()
            assert got.loc[node, t] == act, (node, t)


def test_size_rule_looks_only_at_months_before_the_window():
    S = fake_S(size_lookback=4, min_works=1, min_median_weighted=10.0)
    assert B.min_size_months(4) == 2
    if True:
        df = pd.DataFrame({'node_id': 'A', 'mi': np.arange(10), 'n_works_24m': 5,
                           'weighted_checkouts': [0, 0, 0, 0, 50, 50, np.nan, 50, 0, 0.0]})
        out = B.size_columns(df, S).set_index('mi')
        # a window starting at t uses months t-4..t-1; a missing month is skipped, zero months count as zero
        assert out.loc[4, 'median_weighted_24m'] == 0 and not out.loc[4, 'size_ok']           # months 0..3: 0,0,0,0
        assert out.loc[6, 'median_weighted_24m'] == 25 and out.loc[6, 'size_ok']              # months 2..5: 0,0,50,50
        assert out.loc[7, 'median_weighted_24m'] == 50 and out.loc[7, 'months_avail_24m'] == 3  # months 3..6: 0,50,50,missing
        assert out.loc[5, 'median_weighted_24m'] == 0                                           # months 1..4: 0,0,0,50
        # the month itself never enters its own window: changing month 6's value leaves t=6 unchanged
        df2 = df.copy(); df2.loc[df2.mi == 6, 'weighted_checkouts'] = 1e6
        assert B.size_columns(df2, S).set_index('mi').loc[6, 'median_weighted_24m'] == 25


def test_partial_month_against_api_is_missing():
    totals = pd.DataFrame({'total_checkouts': [10, 20, 30], 'n_rows': [5, 6, 7]}, index=pd.Index([0, 1, 2], name='mi'))
    api = pd.DataFrame({'n_rows': [5, 9, 7], 'checkouts': [10, 40, 30]}, index=[0, 1, 2])
    st = B.month_status(totals, api=api)
    assert list(st.month_ok) == [True, False, True] and 'partial' in st.loc[1, 'reason']



def test_closure_months_from_library_totals():
    # addendum e: 14 normal months of 100, then a closure (0, 3, 30) and a recovery at 80 (the median adapts, no flag)
    vals = [100.0] * 14 + [0.0, 3.0, 30.0, 80.0]
    totals = pd.DataFrame({'total_checkouts': vals, 'n_rows': [10] * len(vals)}, index=pd.Index(range(len(vals)), name='mi'))
    st = B.month_status(totals, closure=(0.5, 12, 6))
    assert list(st.month_ok) == [True] * 14 + [False, False, False, True]
    assert (st.loc[14:16, 'reason'] == 'library-wide total below closure threshold').all()
    assert st.loc[:5, 'closure_ratio'].isna().all()          # fewer than 6 earlier months: no reference, never flagged

def test_main_strength_drops_title_words():
    WT = pd.DataFrame({'work_id': [1, 1, 2], 'node_id': ['A', 'B', 'A'], 'level': [3, 3, 3], 'strength': [0.75, 0.25, 1.0],
                       's_spl': [1.0, 0.0, 0.0], 's_gr': [0.0, 0.0, 0.0], 's_title': [0.5, 0.5, 1.0],
                       'sources': ['spl,title', 'spl,title', 'title']})
    W, how = B.main_strength(WT)
    assert list(zip(W.work_id, W.node_id, W.strength)) == [(1, 'A', 1.0)] and 'without title' in how
    W2, _ = B.main_strength(WT, include_title=True)
    assert len(W2) == 3 and (W2.level == 'narrow').all()


def test_title_backup_combines_like_the_taxonomy_rule():
    main = pd.DataFrame({'work_id': [1], 'node_id': ['A'], 'level': [3], 'strength': [1.0], 's_spl': [1.0],
                         's_lcsh': [0.0], 's_gr': [0.0], 'sources': ['spl']})
    tb = pd.DataFrame({'work_id': [1, 2], 'node_id': ['B', 'A'], 'level': [3, 3], 's_title': [1.0, 1.0]})
    W = B.with_title_backup(main, tb).set_index(['work_id', 'node_id']).strength
    assert np.isclose(W[(1, 'A')], 0.5) and np.isclose(W[(1, 'B')], 0.5) and np.isclose(W[(2, 'A')], 1.0)


def test_overlap_is_share_of_treated_works():
    wt = pd.DataFrame({'work_id': [1, 2, 3, 4, 4, 5, 6], 'node_id': ['A', 'A', 'A', 'A', 'B', 'B', 'B']})
    O = B.overlap_pairs(wt, works_in_format=[1, 2, 3, 4, 5], level='narrow', fmt='ebook').set_index(['node_a', 'node_b'])
    assert np.isclose(O.loc[('A', 'B'), 'share_of_a'], 1 / 4) and np.isclose(O.loc[('B', 'A'), 'share_of_a'], 1 / 2)
