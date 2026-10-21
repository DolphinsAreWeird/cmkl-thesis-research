#!/usr/bin/env python3
"""Test F, step 23: the demand panels b (the 20,000 AI-sorted works) and c (the same works with their librarian-heading theme strengths).

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (demand_panels):
  b_ai_20k        theme shares per format and month from the 20,000 AI-sorted works: each work's weights (confidence 3, 2, 1 -> 1.0, 0.6,
                  0.3, scaled to sum to 1 over its themes) times its loans, divided by all loans of those 20,000 works in that format and
                  month; excluded months as in the benchmark.
  c_headings_20k  the same 20,000 works with their librarian-heading theme strengths (data/db/taxonomy_v3/work_theme.parquet), same
                  denominator, so that b and c differ only in who sorted the books.
Built with the Study 3 panel code (code/main_study/study3/_build.py: work_month, main_strength, assemble, overlap_pairs, node_table) so the
files have the layout of data/db/study3/demand_panel.parquet (level, node_id, parent, broad_id, label, format, ym, mi, month_ok,
weighted_checkouts, total_checkouts, share, log_share, n_works_month, n_works_24m, median_weighted_24m, months_avail_24m, size_ok) and the
Study 3 code (24_G2_matchmaking.py) reads them unchanged. Formats: the Seattle formats of the Study 3 record (audiobook, ebook, print).
Usable months: month_ok of data/db/study3/demand_panel.parquet for that format and month (the excluded months of the benchmark).
Levels: the AI sorts into narrow themes; a work's middle (and broad) weight is the sum of its narrow weights inside that theme, the same
rule as 'a middle theme is the sum of its narrow themes'. Panel c keeps the stored strengths of each level, as panel a does.
The minimum-size rule of Study 3 is computed inside each panel from its own works (as in panel a), unchanged.
Books with status none, dropped or not sorted keep their loans in the denominator and give no theme (b); in c every one of the 20,000 works
counts with its heading strengths.
HARD RULE: this step writes structural checks only (months, coverage, the size rule), never a theme's demand. In a mock world the panels
are shuffled across themes and months (_testf_analysis.shuffle_panel) before they are written.
Outputs: panel_b.parquet, panel_c.parquet, nodes_b.parquet, nodes_c.parquet, overlap_b.parquet, overlap_c.parquet, panels_meta.json;
report testF_23_panels.md.
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/23_panels.py [--root DIR] [--book-key PATH]
"""
import sys, time, pathlib, argparse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _testf_analysis as T
sys.path.insert(0, str(T.MAIN / 'study3'))
from _settings import SETTINGS as S                           # noqa: E402  (Study 3 record, hash-checked)
import _build as B                                             # noqa: E402
import _files as IO                                            # noqa: E402

TAX = T.D / 'db' / 'taxonomy_v3'
STUDY3_PANEL = T.D / 'db' / 'study3' / 'demand_panel.parquet'
LEVELS = list(S.levels_tested) + list(S.levels_descriptive)
REF_WINDOWS = ['2017-10', '2020-03', '2020-06']


def ai_strengths(AB, works):
    """AI weights -> work_id, node_id, level, strength at narrow, middle and broad levels (strengths sum to 1 per work and level)."""
    par = T.parent_map()
    X = AB[AB.work_id.isin(works)][['work_id', 'code', 'weight']].copy()
    X['s'] = X.weight / X.groupby('work_id').weight.transform('sum')
    nar = X.rename(columns={'code': 'node_id'}).assign(level='narrow')[['work_id', 'node_id', 'level', 's']]
    mid = X.assign(node_id=X.code.map(par)).groupby(['work_id', 'node_id'], as_index=False).s.sum().assign(level='middle')
    brd = X.assign(node_id=X.code.str.split('.').str[0]).groupby(['work_id', 'node_id'], as_index=False).s.sum().assign(level='broad')
    W = pd.concat([nar, mid, brd], ignore_index=True).rename(columns={'s': 'strength'})
    W['work_id'] = W.work_id.astype(np.int64)
    return W[['work_id', 'node_id', 'level', 'strength']]


def heading_strengths(works):
    WT = pd.read_parquet(TAX / 'work_theme.parquet', filters=[('work_id', 'in', [int(w) for w in works])])
    W, how = B.main_strength(WT)
    return W, how


def format_data(fmt, works, ok_month):
    """Work x month loans of the 20,000 works in one format, and the month status with the 20,000 works' total as denominator."""
    rw = pd.read_parquet(TAX / 'spl_record_work.parquet')
    rw = rw[rw.work_id.astype(np.int64).isin(works)]
    rows = pd.read_parquet(TAX / f'spl_rows_{IO.SEATTLE_FILE[fmt]}.parquet', columns=['record_id', 'year', 'month', 'checkouts'])
    rows = rows[rows.record_id.astype(np.int64).isin(set(rw.record_id.astype(np.int64)))]
    wm, totals = B.work_month(rows, rw)
    grid = ok_month.index.to_numpy()
    st = pd.DataFrame(index=pd.Index(grid, name='mi'))
    st['total_checkouts'] = totals.total_checkouts.reindex(grid)
    st['n_rows'] = totals.n_rows.reindex(grid)
    st['month_ok'] = ok_month.reindex(grid).fillna(False).astype(bool).to_numpy() & st.total_checkouts.fillna(0).gt(0).to_numpy()
    st['reason'] = np.where(st.month_ok, '', np.where(ok_month.reindex(grid).fillna(False).astype(bool), 'no loans of these works', 'excluded in the Study 3 panel'))
    n_rows = len(rows)
    del rows
    return wm, st, n_rows


def build(name, Wt, wm_by_fmt, st_by_fmt, nodes):
    parts, ovl, checks = [], [], {}
    works_any = set()
    for fmt in S.seattle_formats:
        wm, st = wm_by_fmt[fmt], st_by_fmt[fmt]
        wm_ok = wm[wm.mi.isin(st[st.month_ok].index)]
        works_fmt = wm_ok[wm_ok.checkouts > 0].work_id.unique()
        works_any.update(works_fmt.tolist())
        c = {}
        for level in LEVELS:
            wtl = Wt[Wt.level == level]
            df = B.assemble(wm, wtl, st, nodes, fmt, level, S)
            expect = (wm_ok.merge(wtl.groupby('work_id').strength.sum().rename('s').reset_index(), on='work_id').eval('checkouts * s').sum())
            c[f'weighted_identity_{level}'] = bool(np.isclose(df.weighted_checkouts.sum(), expect, rtol=1e-9))
            c[f'theme_coverage_{level}'] = float(expect / max(1, wm_ok.checkouts.sum()))
            parts.append(df)
            ovl.append(B.overlap_pairs(wtl, works_fmt, level, fmt))
        checks[fmt] = c
    panel = pd.concat(parts, ignore_index=True)
    overlap = pd.concat(ovl, ignore_index=True)
    nd = nodes.copy()
    n = Wt[Wt.work_id.isin(works_any)].groupby('node_id').work_id.nunique()
    nd['n_works_main'] = nd.node_id.map(n).fillna(0).astype(int)
    return panel, overlap, nd, checks


def size_counts(panel):
    rows = []
    for fmt, g in panel.groupby('format'):
        for level in LEVELS:
            h = g[g.level == level]
            r = {'format': fmt, 'level': level, 'categories': h.node_id.nunique()}
            for w in REF_WINDOWS:
                r[f'pass size at {w}'] = int(h[h.ym == w].size_ok.sum()) if (h.ym == w).any() else 'no data'
            rows.append(r)
    return pd.DataFrame(rows)


def main():
    ap = T.add_root_arg(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    ap.add_argument('--book-key', default=None)
    a = ap.parse_args()
    P = T.Paths(a.root)
    T.be_nice(10)
    t0 = time.time()
    BK, bname = T.book_key(P, a.book_key)
    works = set(BK.work_id.astype(np.int64))
    if not P.mock and len(works) != 20000:
        raise SystemExit(f'the book key has {len(works):,} works; the addendum fixes 20,000')
    AB = T.read_assign(P, 'books')
    AB['work_id'] = AB.work_id.astype(np.int64)
    N = pd.read_parquet(TAX / 'theme_nodes.parquet')
    nodes = B.node_table(N)
    p3 = pd.read_parquet(STUDY3_PANEL, columns=['format', 'mi', 'month_ok']).drop_duplicates()
    assert not p3.duplicated(['format', 'mi']).any(), 'month_ok differs between themes of the Study 3 panel'
    wm_by_fmt, st_by_fmt, info = {}, {}, {}
    for fmt in S.seattle_formats:
        ok = p3[p3.format == fmt].set_index('mi').month_ok.sort_index()
        wm, st, nr = format_data(fmt, works, ok)
        wm_by_fmt[fmt], st_by_fmt[fmt] = wm, st
        bad = st[~st.month_ok]
        info[fmt] = dict(rows=nr, months=len(st), usable=int(st.month_ok.sum()), first=T.ym(st.index.min()), last=T.ym(st.index.max()),
                         works_with_loans=int(wm[wm.checkouts > 0].work_id.nunique()),
                         unusable={r: ', '.join(T.ym(m) for m in g.index) for r, g in bad.groupby('reason')})
        T.log(f'{fmt}: {nr:,} rows of the 20,000 works; {info[fmt]["usable"]} usable months of {len(st)}')
    Wb = ai_strengths(AB, works)
    Wc, how_c = heading_strengths(works)
    meta = dict(created=time.strftime('%Y-%m-%d %H:%M:%S'), book_key=bname, works=len(works), mock=P.mock, settings_sha256=S.sha256,
                formats=list(S.seattle_formats), months=info, works_with_ai_theme=int(Wb.work_id.nunique()),
                works_with_heading_theme=int(Wc.work_id.nunique()), heading_strength=how_c, panels={})
    lines = [f'# Test F, step 23: demand panels b and c ({P.tag()}; structural checks only)', '',
             f'- written {pd.Timestamp.now():%Y-%m-%d %H:%M}; code main_study/wiki_led/testF/23_panels.py; Study 3 record `{S.sha256[:12]}`',
             f'- works: {len(works):,} (key {bname}); with an AI theme {meta["works_with_ai_theme"]:,}; with a heading theme {meta["works_with_heading_theme"]:,} ({how_c})', '',
             '## Months (usable = month_ok of the Study 3 panel and at least one loan of these works)']
    for fmt, d in info.items():
        lines.append(f'- {fmt}: {d["first"]} to {d["last"]}, {d["months"]} months, {d["usable"]} usable; works with loans {d["works_with_loans"]:,}; '
                     + ('; '.join(f'{r}: {v}' for r, v in d['unusable'].items()) or 'no unusable months'))
    for name, Wt in (('b', Wb), ('c', Wc)):
        panel, overlap, nd, checks = build(name, Wt, wm_by_fmt, st_by_fmt, nodes)
        if P.mock:
            panel = T.shuffle_panel(panel, P.mock_seed + (1 if name == 'b' else 2))
        T.write_parquet(panel, P / f'panel_{name}.parquet')
        T.write_parquet(overlap, P / f'overlap_{name}.parquet')
        T.write_parquet(nd, P / f'nodes_{name}.parquet')
        meta['panels'][name] = dict(rows=len(panel), checks=checks, shuffled=P.mock)
        lines += ['', f'## Panel {name} ({"AI-sorted works" if name == "b" else "librarian headings"})',
                  f'- rows {len(panel):,}; donor-overlap pairs {len(overlap):,}' + ('; SHUFFLED across themes and months (mock world)' if P.mock else '')]
        for fmt, c in checks.items():
            lines.append(f'- {fmt}: ' + '; '.join(f'{lv}: weighted-sum identity {c[f"weighted_identity_{lv}"]}, theme coverage '
                                                f'{100 * c[f"theme_coverage_{lv}"]:.1f}% of loans' for lv in LEVELS))
        lines += [f'- categories passing the minimum-size rule (>= {S.min_works} works with loans and median >= {S.min_median_weighted:g} weighted loans '
                  f'a month in the {S.size_lookback} months before the window):'] + T.md_table(size_counts(panel))
        T.log(f'panel {name}: {len(panel):,} rows')
    meta['seconds'] = round(time.time() - t0)
    meta['peak_gb'] = round(T.peak_gb(), 2)
    T.write_json(meta, P / 'panels_meta.json')
    lines += ['', 'No theme demand series, effect or p-value is shown here.', f'- run time {meta["seconds"]}s; peak memory {meta["peak_gb"]} GB']
    T.write_text('\n'.join(lines) + '\n', P.report('testF_23_panels.md'))
    T.log(f'done; peak memory {T.peak_gb():.2f} GB')


if __name__ == '__main__':
    main()
