#!/usr/bin/env python3
"""Test F, step 91 (tests only): small hand-checkable tests of the Test F analysis functions. No real borrowing is read.

Covers: the answer parser (20), the S2 page choice and its cap, the outcome shuffles of mock worlds, the AI weights of panel b (23), the
monthly rule of the benchmark used by 21, the Test C measure (25) against a copy of the scoring block of 20c_test_c.py, the G1 scores (26)
and the reliability measures (27) on toy data.
Run from code/:  ../.venv/bin/python main_study/wiki_led/testF/91_selftest.py
"""
import sys, pathlib, importlib, importlib.util
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from scipy.stats import spearmanr
import _testf_analysis as T

P20 = importlib.import_module('20_parse_outputs')
P26 = importlib.import_module('26_G1_validation')
P27 = importlib.import_module('27_reliability')
spec = importlib.util.spec_from_file_location('g3', T.HERE / '25_G3_forecast.py'); P25 = importlib.util.module_from_spec(spec); spec.loader.exec_module(P25)
FAILS = []


def check(name, cond):
    print(('ok    ' if cond else 'FAIL  ') + name, flush=True)
    if not cond:
        FAILS.append(name)


def t_parser():
    g = {'B01.M01.N01', 'B01.M01.N02', 'B02.M01.N01', 'B03.M02.N01'}
    pc = P20.parse_codes
    check('none', pc('none', g)[0] == 'none' and pc(' None. ', g)[0] == 'none')
    s, c, n, r = pc('B01.M01.N01:3,B02.M01.N01:1', g)
    check('two codes', s == 'ok' and c == [('B01.M01.N01', 3), ('B02.M01.N01', 1)])
    check('lower case and spaces', pc(' b01.m01.n01 : 2 , B02.M01.N01:1', g)[1] == [('B01.M01.N01', 2), ('B02.M01.N01', 1)])
    check('code not in guide', pc('B01.M01.N01:3,B99.M01.N01:2', g)[0] == 'invalid')
    check('middle code not in guide', pc('B01.M01:3', g)[0] == 'invalid')
    check('confidence 4', pc('B01.M01.N01:4', g)[0] == 'invalid')
    check('malformed', pc('B01.M01.N01-3', g)[0] == 'invalid' and pc('B01.M01.N01', g)[0] == 'invalid')
    s, c, n, r = pc('B01.M01.N01:3,B01.M01.N01:1,B02.M01.N01:2', g)
    check('duplicate code keeps the first', c == [('B01.M01.N01', 3), ('B02.M01.N01', 2)] and n['duplicate_code'] == 1)
    s, c, n, r = pc('B01.M01.N01:3,B01.M01.N02:2,B02.M01.N01:2,B03.M02.N01:1', g)
    check('four codes keep three', len(c) == 3 and n['more_than_3_codes'] == 1)
    check('tab line', P20.split_line('p00001\twork\tnone', 3) == (['p00001', 'work', 'none'], False))
    check('space line', P20.split_line('p00001 work B01.M01.N01:3', 3) == (['p00001', 'work', 'B01.M01.N01:3'], True))
    check('book line', P20.split_line('b00001\tB01.M01.N01:3,B02.M01.N01:2', 2)[0] == ['b00001', 'B01.M01.N01:3,B02.M01.N01:2'])


def t_s2_selection():
    # candidates a, c, d (b has confidence 1 only, e is in the one-day sample); a, c, d have 9, 5, 5 days; c and d tie on days, c has more views
    A = pd.DataFrame({'title': ['a', 'a', 'b', 'c', 'd', 'e'], 'set': ['universe'] * 5 + ['sample1day'], 'conf': [1, 2, 1, 3, 2, 3]})
    td = pd.DataFrame({'title': list('abcde'), 'top_days': [9, 99, 5, 5, 99], 'top_views': [10, 10, 30, 10, 10]})
    old = T.S2_MAX_PAGES
    T.S2_MAX_PAGES = 2
    S = T.s2_selection(A, td)
    T.S2_MAX_PAGES = old
    check('S2 pages: confidence 2 or 3, universe only', set(S.title) == {'a', 'c', 'd'})
    check('S2 cap: most top-500 days, ties by views then title', list(S[S.selected].title) == ['a', 'c'] and S.set_index('title').loc['d', 'selected'] == False)  # noqa: E712
    td2 = td.assign(top_views=[10, 10, 10, 10, 10])
    T.S2_MAX_PAGES = 2
    S2 = T.s2_selection(A, td2)
    T.S2_MAX_PAGES = old
    check('S2 cap: equal days and views go by title', list(S2[S2.selected].title) == ['a', 'c'])


def t_shuffles():
    rng = np.random.default_rng(0)
    n = 400
    p = pd.DataFrame({'level': ['narrow'] * n, 'format': ['print'] * (n // 2) + ['ebook'] * (n // 2), 'node_id': np.repeat([f'n{i}' for i in range(20)], 20),
                      'mi': np.tile(np.arange(20), 20), 'month_ok': rng.random(n) > 0.1, 'log_share': rng.normal(-6, 1, n), 'size_ok': rng.random(n) > 0.5})
    p['share'] = np.exp(p.log_share); p['weighted_checkouts'] = p.share * 1e5
    p.loc[~p.month_ok, ['log_share', 'share', 'weighted_checkouts']] = np.nan
    q = T.shuffle_panel(p, 3)
    same = all(np.allclose(np.sort(p[p.format == f].log_share.dropna()), np.sort(q[q.format == f].log_share.dropna())) for f in ('print', 'ebook'))
    check('panel shuffle keeps the values of each format and level', same)
    check('panel shuffle keeps months, missing cells and the size rule', (p.month_ok == q.month_ok).all() and (p.size_ok == q.size_ok).all()
          and (p.log_share.isna() == q.log_share.isna()).all())
    ok = p.log_share.notna()
    check('panel shuffle moves values', abs(np.corrcoef(p.log_share[ok], q.log_share[ok])[0, 1]) < 0.3)
    check('panel shuffle: shares follow the log shares', np.allclose(np.log(q.share.dropna()), q.log_share.dropna()))
    check('panel shuffle does not depend on other formats', np.allclose(T.shuffle_panel(p[p.format == 'print'], 3).log_share.to_numpy(dtype=float),
                                                                     q[q.format == 'print'].log_share.to_numpy(dtype=float), equal_nan=True))
    h = {('s', 'print', 'narrow', f'n{i}'): pd.Series(rng.normal(size=12), index=np.arange(100, 112)) for i in range(5)}
    a, b = T.shuffle_history(h, 1), T.shuffle_history(h, 1)
    check('history shuffle repeatable', all(np.allclose(a[k], b[k]) for k in h))
    check('history shuffle keeps values', np.allclose(np.sort(np.concatenate([v.to_numpy() for v in h.values()])),
                                                      np.sort(np.concatenate([v.to_numpy() for v in a.values()]))))


def t_panel_b_weights():
    spec = importlib.util.spec_from_file_location('p23', T.HERE / '23_panels.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    AB = pd.DataFrame({'work_id': [1, 1, 1, 2], 'code': ['B01.M01.N01', 'B01.M01.N02', 'B02.M01.N01', 'B03.M02.N01'], 'weight': [1.0, 0.6, 0.3, 0.6]})
    W = m.ai_strengths(AB, {1, 2})
    s = W.groupby(['work_id', 'level']).strength.sum()
    check('panel b: strengths sum to 1 per work and level', np.allclose(s.to_numpy(), 1.0))
    w1 = W[(W.work_id == 1) & (W.level == 'narrow')].set_index('node_id').strength
    check('panel b: weights 1.0, 0.6, 0.3 scaled', np.allclose(w1[['B01.M01.N01', 'B01.M01.N02', 'B02.M01.N01']], np.array([1.0, 0.6, 0.3]) / 1.9))
    mid = W[(W.work_id == 1) & (W.level == 'middle')].set_index('node_id').strength
    check('panel b: middle = sum of its narrow weights', np.isclose(mid['B01.M01'], 1.6 / 1.9) and np.isclose(mid['B02.M01'], 0.3 / 1.9))


def t_monthly_rule():
    spec = importlib.util.spec_from_file_location('bm07', T.MAIN / 'benchmark' / '07_stage2_features.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    weeks = pd.date_range('2020-01-06', periods=10, freq='7D')
    w = pd.DataFrame({'node_id': 'x', 'week': weeks, 'views': 1.0, 'share': np.arange(1, 11) / 100, 'partial_week': [False] * 9 + [True]})
    Msh, _ = m.week_matrices(w)
    M = m.monthly_log(Msh)
    jan = [d for d in weeks if (d + pd.Timedelta(days=6)).month == 1]
    want = np.log(np.mean([(k + 1) / 100 for k, d in enumerate(weeks) if d in jan]))
    check('monthly rule: log of the mean of the weeks whose Sunday is in the month', np.isclose(M.loc[2020 * 12 + 0, 'x'], want))
    check('monthly rule: a month with a partial week is missing', np.isnan(M.loc[2020 * 12 + 2, 'x']))


def t_test_c():
    rng = np.random.default_rng(5)
    rows = []
    for o in range(30):
        for f in ('print', 'ebook'):
            for lv in ('narrow', 'middle'):
                for n in range(12):
                    rows.append((o, f, lv, f'{lv}{n}', rng.normal(), rng.normal()))
    s = pd.DataFrame(rows, columns=['origin_mi', 'format', 'level', 'node_id', 'x', 'c'])
    s.loc[s.origin_mi == 3, 'x'] = 0.0                               # a month with a constant x
    got, _ = P25.test_c_scores(s, ['x'])
    # the scoring block of 20c_test_c.py, copied
    grp = s.groupby(['origin_mi', 'format', 'level']); keys = [k for k, g in grp if len(g) >= 10]
    months = np.sort(s.origin_mi.unique()); r_ = np.random.default_rng(20261020); nb = int(np.ceil(len(months) / 3))
    BD = np.array([np.concatenate([np.arange(a, a + 3) % len(months) for a in r_.choice(len(months), nb)])[:len(months)] for _ in range(2000)])
    vals = [(k[0], spearmanr(grp.get_group(k).x, grp.get_group(k).c).statistic if grp.get_group(k).x.nunique() > 1 else 0.0) for k in keys]
    v = pd.DataFrame(vals, columns=['m', 'r'])
    per_m = v.groupby('m').r.agg(['sum', 'count']).reindex(months).fillna(0)
    boots = np.array([per_m['sum'].values[b].sum() / per_m['count'].values[b].sum() for b in BD])
    check('Test C measure equals the 20c scoring block', np.isclose(got['x']['rho'], v.r.mean()) and np.isclose(got['x']['lo'], np.percentile(boots, 2.5))
          and np.isclose(got['x']['hi'], np.percentile(boots, 97.5)))


def t_g1():
    mp = pd.DataFrame({'id': ['p1', 'p1', 'p2'], 'node': ['A', 'B', 'C']})
    jp = pd.DataFrame({'id': ['p1', 'p2', 'p3'], 'node': ['A', 'D', 'E']})
    idx = np.random.default_rng(0).integers(0, 3, size=(50, 3))
    r = P26.score(mp, jp, ['p1', 'p2', 'p3'], {'p1': True, 'p2': False, 'p3': True}, idx)
    check('G1 precision 1/3 and recall 1/3', np.isclose(r['precision'], 1 / 3) and np.isclose(r['recall'], 1 / 3))
    check('G1 misleading: p1 has a theme the judge does not give, p3 none', np.isclose(r['misleading_wrong_share'], 0.5) and r['misleading_pages'] == 2)
    par = {'B01.M01.N01': 'B01.M01', 'B01.M01.N02': 'B01.M01'}
    x, nb = P26.to_middle(pd.DataFrame({'id': ['p1', 'p1', 'p2'], 'node': ['B01.M01.N01', 'B01.M01.N02', 'B05']}), par)
    check('G1 middle level: narrow moved up, broad dropped', len(x) == 1 and x.node.iloc[0] == 'B01.M01' and nb == 1)


def t_reliability():
    first = {'a': ['X', 'Y'], 'b': ['Z'], 'c': [], 'd': ['W'], 'e': []}
    second = {'a': ['X'], 'b': ['Q', 'Z'], 'c': [], 'd': [], 'e': ['V']}
    m = P27.measures(first, second, {'X': 'm1', 'Z': 'm2', 'Q': 'm2', 'W': 'm3'})
    check('reliability: first theme same 1 of 2, overlap 2 of 2', np.isclose(m['first_theme_same'], 0.5) and np.isclose(m['any_overlap'], 1.0))
    check('reliability: none table', m['both_none'] == 1 and m['first_none_only'] == 1 and m['second_none_only'] == 1 and m['both_some'] == 2)
    check('reliability: middle-level first theme', np.isclose(m['first_theme_same_middle'], 1.0))


TESTS = (t_parser, t_s2_selection, t_shuffles, t_panel_b_weights, t_monthly_rule, t_test_c, t_g1, t_reliability)

if __name__ == '__main__':
    import subprocess
    if len(sys.argv) > 1:                       # one test in this process (Study 3 and Study 4 both have a module called _settings)
        dict((f.__name__, f) for f in TESTS)[sys.argv[1]]()
        sys.exit(1 if FAILS else 0)
    bad = 0
    for f in TESTS:
        bad += subprocess.call([sys.executable, __file__, f.__name__]) != 0
    print(f'\n{bad} test groups with failures')
    sys.exit(1 if bad else 0)
