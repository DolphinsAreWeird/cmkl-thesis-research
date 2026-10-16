# Count panel building on hand-made data: value strengths, the sparse value-month product, month status, dense counts.
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
import _s3
import _panel as PN

B3 = _s3.build


def _ev():
    # work 1: two sources; work 2: one source; work 3: only a value without a node; work 4: lcsh only
    return pd.DataFrame([
        (1, 'lcsh', 'war', 2.0, 'B08.M01'), (1, 'lcsh', 'peace', 1.0, 'B08.M02'), (1, 'gr', 'war', 90.0, 'B08.M01'), (1, 'gr', 'spies', 10.0, 'B08.M03'),
        (2, 'spl', 'war', 1.0, 'B08.M01'),
        (3, 'lcsh', 'orphan', 5.0, None),
        (4, 'lcsh', 'peace', 0.5, 'B08.M02'), (4, 'lcsh', 'war', 0.5, 'B08.M01'),
    ], columns=['work_id', 'source', 'theme', 'weight', 'node_id'])


def test_value_strengths_follow_the_node_rule():
    VS = PN.value_strengths(_ev(), 'work_id').set_index(['work_id', 'theme'])
    s = VS.strength
    assert np.isclose(s[(1, 'war')], (2 / 3 + 0.9) / 2) and np.isclose(s[(1, 'peace')], (1 / 3) / 2) and np.isclose(s[(1, 'spies')], 0.1 / 2)
    assert np.isclose(s[(2, 'war')], 1.0)
    assert (3, 'orphan') not in s.index                              # a value without a node is left out of the shares
    assert np.allclose(VS.groupby('work_id').strength.sum(), 1.0)    # strengths sum to 1 per work
    assert VS.node_id[(1, 'war')] == 'B08.M01'


def test_sparse_product_equals_the_merge_computation():
    VS = PN.value_strengths(_ev(), 'work_id')
    rng = np.random.default_rng(0)
    wm = pd.DataFrame({'work_id': np.repeat([1, 2, 3, 4, 9], 12), 'mi': np.tile(np.arange(100, 112), 5), 'checkouts': rng.integers(0, 6, 60)})
    ok = set(range(100, 112)) - {104}
    themes, D = PN.theme_month_dense(wm, VS, 'work_id', 100, 12, ok)
    x = wm[(wm.checkouts > 0) & wm.mi.isin(ok)].merge(VS, on='work_id')
    x['w'] = x.checkouts * x.strength
    ref = x.groupby(['theme', 'mi']).w.sum()
    for ti, th in enumerate(themes):
        for m in range(100, 112):
            assert np.isclose(D[ti, m - 100], ref.get((th, m), 0.0)), (th, m)
    assert D[:, 4].sum() == 0                                         # the unusable month holds nothing
    # whole identity: weighted checkouts of all values = checkouts of the works that have value evidence
    exp = wm[wm.work_id.isin([1, 2, 4]) & wm.mi.isin(ok)].checkouts.sum()
    assert np.isclose(D.sum(), exp)


def test_node_dense_matches_node_month_and_skips_unusable_months():
    wtl = pd.DataFrame({'work_id': [1, 1, 2], 'node_id': ['n1', 'n2', 'n1'], 'strength': [0.6, 0.4, 1.0]})
    wm = pd.DataFrame({'work_id': [1, 1, 2, 2], 'mi': [10, 11, 10, 11], 'checkouts': [10, 20, 5, 5]})
    D = PN.node_dense(wm, wtl, ['n1', 'n2'], 10, 3, {10})
    assert np.allclose(D, [[11.0, 0.0, 0.0], [4.0, 0.0, 0.0]])


def test_make_counts_marks_unusable_months_nan_and_usable_zero():
    status = pd.DataFrame({'format': 'a', 'mi': [0, 1, 2, 3], 'month_ok': [True, False, True, True], 'total_checkouts': [100.0, 90.0, 120.0, 110.0]})
    long = pd.DataFrame({'level': 'narrow', 'node_id': ['x', 'x'], 'format': 'a', 'mi': [0, 2], 'y': [3.0, 4.0]})
    C = PN.make_counts(long, status, 'narrow', ['x', 'y'], ['a'])
    assert C.Y['a'][0].tolist()[0] == 3.0 and np.isnan(C.Y['a'][0, 1]) and C.Y['a'][0, 3] == 0.0       # usable month without a row is 0
    assert np.isnan(C.Y['a'][1, 1]) and C.Y['a'][1, 0] == 0.0 and np.isnan(C.N['a'][1]) and C.N['a'][0] == 100.0
    assert C.index == {'x': 0, 'y': 1} and C.mi0 == 0 and C.T == 4


def test_sparse_rows_keep_only_positive_counts():
    D = np.array([[0.0, 2.0], [1.5, 0.0], [0.0, 0.0]])
    t = PN.sparse_rows('value', ['a', 'b', 'c'], D, 'print', 24000, keep=np.array([True, True, False]))
    assert t.node_id.tolist() == ['a', 'b'] and t.mi.tolist() == [24001, 24000] and t.y.tolist() == [2.0, 1.5]
