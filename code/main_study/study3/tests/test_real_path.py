# The real-data code path of 01 (readers, reconciliation, report) and the title-word backup of 10, run on a small
# fake taxonomy folder written to a temporary directory. No real demand file is opened.
import sys, json, pathlib, importlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from _settings import SETTINGS as S
import _files as IO
import _inputs as I
import _build as B

MONTHS = [(y, m) for y in (2023, 2024, 2025) for m in range(1, 13)]
REC_WORK = {1: 100, 2: 101, 3: 102, 4: 103, 5: 104}          # record 6 has no work


def fake_taxonomy(P):
    rng = np.random.default_rng(0)
    T = P.taxo_v3
    T.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({'node_id': ['X', 'X.M1', 'X.M2', 'X.M1.A', 'X.M1.B', 'X.M2.C'], 'level': [1, 2, 2, 3, 3, 3],
                  'parent': [None, 'X', 'X', 'X.M1', 'X.M1', 'X.M2'],
                  'label': ['Broad', 'Mid 1', 'Mid 2', 'Narrow A', 'Narrow B', 'Narrow C']}).to_parquet(T / 'theme_nodes.parquet')
    rows, api, works = {}, [], []
    miss = set(S.missing_months)
    for f, file in IO.SEATTLE_FILE.items():
        r = []
        for y, m in MONTHS:
            ym = f'{y}-{m:02d}'
            if (f in S.digital_formats and ym in miss) or (f == 'print' and ym > '2025-06'):
                continue
            for rec in range(1, 7):
                r.append((rec, y, m, int(rng.integers(1, 50))))
        d = pd.DataFrame(r, columns=['record_id', 'year', 'month', 'checkouts']).astype({'record_id': 'int32', 'year': 'int16', 'month': 'int8', 'checkouts': 'int32'})
        d.to_parquet(T / f'spl_rows_{file}.parquet')
        rows[f] = d
        a = d.groupby(['year', 'month']).agg(n_rows=('checkouts', 'size'), checkouts=('checkouts', 'sum')).reset_index()
        if f == 'print':
            a.loc[(a.year == 2024) & (a.month == 2), 'n_rows'] += 5          # SPL API has more rows: partial month
        a['materialtype'] = {'audiobook': 'AUDIOBOOK', 'ebook': 'EBOOK', 'print': 'BOOK'}[f]
        api.append(a)
    pd.concat(api).to_parquet(T / 'spl_api_counts.parquet')
    pd.DataFrame({'record_id': list(REC_WORK), 'work_id': list(REC_WORK.values())}).to_parquet(T / 'spl_record_work.parquet')
    W = pd.DataFrame({'work_id': sorted(set(REC_WORK.values())), 'work_key': [f'k{i}' for i in range(5)]})
    for f, file in IO.SEATTLE_FILE.items():
        d = rows[f].assign(work_id=rows[f].record_id.map(REC_WORK)).dropna()
        W[f'checkouts_{file}'] = W.work_id.map(d.groupby('work_id').checkouts.sum()).fillna(0).astype(int)
    W.to_parquet(T / 'spl_works.parquet')
    main = [(100, 'X.M1.A', 3, 1.0), (100, 'X.M1', 2, 1.0), (100, 'X', 1, 1.0),
            (101, 'X.M1.A', 3, 0.5), (101, 'X.M2.C', 3, 0.5), (101, 'X.M1', 2, 0.5), (101, 'X.M2', 2, 0.5), (101, 'X', 1, 1.0),
            (102, 'X.M1.B', 3, 1.0), (102, 'X.M1', 2, 1.0), (102, 'X', 1, 1.0),
            (103, 'X.M2.C', 3, 1.0), (103, 'X.M2', 2, 1.0), (103, 'X', 1, 1.0)]
    WT = pd.DataFrame(main, columns=['work_id', 'node_id', 'level', 'strength'])
    WT['s_spl'] = WT.strength; WT['s_lcsh'] = 0.0; WT['s_gr'] = 0.0; WT['sources'] = 'spl'
    WT.to_parquet(T / 'work_theme.parquet')
    TB = pd.DataFrame([(104, 'X.M1.A', 3, 1.0), (104, 'X.M1', 2, 1.0), (104, 'X', 1, 1.0), (100, 'X.M1.B', 3, 1.0)],
                      columns=['work_id', 'node_id', 'level', 's_title'])
    TB['strength'] = TB.s_title; TB['sources'] = 'title'; TB['flag'] = 'backup'
    TB.to_parquet(T / 'work_theme_title_backup.parquet')
    return rows


def share_of(rows, f, ym, weights):
    y, m = map(int, ym.split('-'))
    d = rows[f][(rows[f].year == y) & (rows[f].month == m)].set_index('record_id').checkouts
    return sum(w * d.get(r, 0) for r, w in weights.items()) / d.sum()


def test_real_build_path_on_a_fake_taxonomy(tmp_path):
    P = IO.Paths(tmp_path / 'sim')
    rows = fake_taxonomy(P)
    mod = importlib.import_module('01_demand_panel')
    src = I.choose_source(P)
    assert src['taxonomy'] == 'v3' and not src['development']
    panel, overlap, nodes, checks, months, how, info = mod.build_seattle(P, src)
    for f, c in checks.items():
        assert c['denominator_equals_raw'] and c['work_table_reconciles'] and c['unmapped_records'] > 0
        assert all(c[f'weighted_identity_{lv}'] for lv in ('narrow', 'middle', 'broad'))
    ok = {f: set(B.ym_of(m) for m in st[st.month_ok].index) for f, st in months.items()}
    assert not set(S.missing_months) & ok['audiobook'] and '2024-02' not in ok['print'] and '2024-03' in ok['print']
    pn = panel.set_index(['format', 'node_id', 'ym'])
    for f in ('audiobook', 'print'):
        for ym in ('2023-07', '2025-03'):
            assert np.isclose(pn.loc[(f, 'X.M1.A', ym), 'share'], share_of(rows, f, ym, {1: 1.0, 2: 0.5}))
            assert np.isclose(pn.loc[(f, 'X.M1', ym), 'share'], share_of(rows, f, ym, {1: 1.0, 2: 0.5, 3: 1.0}))
    assert np.isnan(pn.loc[('ebook', 'X.M1.A', '2024-05'), 'share'])
    nd = nodes.set_index('node_id')
    assert nd.loc['X.M1.A', 'n_works_main'] == 2 and nd.loc['X.M1.A', 'n_works_with_title'] == 3
    ov = overlap[(overlap.level == 'narrow') & (overlap.format == 'ebook')].set_index(['node_a', 'node_b']).share_of_a
    assert np.isclose(ov[('X.M1.A', 'X.M2.C')], 0.5) and np.isclose(ov[('X.M2.C', 'X.M1.A')], 0.5)
    meta = dict(taxonomy='v3', development=False)
    L = mod.report(P, meta, panel, nodes, overlap, checks, months, how, info, 'skipped', None, [])
    assert any('pass size at 2020-03' in x for x in L)
    text = '\n'.join(L)                      # structural only: no category is named in the build report
    assert not any(lbl in text for lbl in nodes.label) and not any(n in text for n in nodes.node_id if '.' in n)
    # title-word backup of step 10: work 100 now has two sources (spl, title) -> 0.5 on A; work 104 (title only) -> 1.0
    ctl = importlib.import_module('10_positive_controls')
    bk = ctl.backup_rows(P, 'X.M1.A', 'narrow').set_index(['format', 'ym'])
    for f in ('ebook', 'print'):
        assert np.isclose(bk.loc[(f, '2023-07'), 'share'], share_of(rows, f, '2023-07', {1: 0.5, 2: 0.5, 5: 1.0}))


def test_librivox_builder_on_fake_listening(tmp_path):
    P = IO.Paths(tmp_path / 'sim')
    fake_taxonomy(P)
    mod = importlib.import_module('01_demand_panel')
    assert mod.build_librivox(P, I.load_nodes(I.choose_source(P)))[0] is None        # no mapping yet: skipped
    L = pd.DataFrame([(b, f'2020-{m:02d}', v) for b, v in (('lv1', 300), ('lv2', 100), ('lv3', 600)) for m in range(1, 13)],
                     columns=['book_id', 'period', 'listens'])
    L.to_parquet(P.librivox_listening)
    pd.DataFrame({'book_id': ['lv1', 'lv2'], 'node_id': ['X.M1.A', 'X.M1.A'], 'level': ['narrow', 'narrow'],
                  'strength': [1.0, 0.5]}).to_parquet(P.taxo_v3 / 'librivox_work_theme.parquet')
    (lvp, lvo, st), msg = mod.build_librivox(P, I.load_nodes(I.choose_source(P)))
    assert 'built' in msg and np.allclose(lvp[lvp.node_id == 'X.M1.A'].share, (300 + 50) / 1000)
    assert (lvp.format == 'librivox').all()
