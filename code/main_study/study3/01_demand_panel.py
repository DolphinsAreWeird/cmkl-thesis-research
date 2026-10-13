# 01. Study 3 demand panel: category x month x format (Seattle audiobook, ebook, print; LibriVox when mapped).
# Demand (record, demand.seattle) = sum over works of checkouts x theme strength, divided by all checkouts in that
# format and month; the panel also keeps the weighted checkouts, the number of works with checkouts, and the
# columns of the minimum-size rule for a window starting in each month (it looks at the 24 months before).
# Levels: narrow and middle (tested) and broad (descriptive). Missing months are missing, never zero.
#
# Inputs (reloaded on every run; another job may still be writing them):
#   data/db/taxonomy_v3/spl_rows_{audiobook,ebook,book}.parquet, spl_record_work.parquet, spl_works.parquet
#   data/db/taxonomy_v3/work_theme.parquet (main assignment, no title words). If it does not exist, the v2 themes
#     are carried onto v3 works by work key as a DEVELOPMENT build that later steps refuse unless told otherwise.
#   theme_nodes.parquet (v3 if present, else v2)
#   data/db/taxonomy_v2/spl_api_counts.parquet (SPL API rows and checkouts per material type and month)
#   data/db/taxonomy_v3/librivox_work_theme.parquet + data/db/listening.parquet (LibriVox; skipped if not mapped)
# Outputs: data/db/study3/demand_panel.parquet, demand_panel_librivox.parquet (if mapped), nodes.parquet,
#   node_overlap.parquet, demand_panel_meta.json; report data/reports/study3_panel_build.md.
# HARD RULE: this script prints and writes structural checks only, never a category's demand.
#   python 01_demand_panel.py            real build
#   python 01_demand_panel.py --sim DIR  simulated world for tests (add --sim-null for a world without effects)
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from _settings import SETTINGS as S
import _files as IO
import _build as B
import _inputs as I
from _interest import status_line

REF_WINDOWS = ['2017-10', '2020-03', '2020-06']   # windows at which the number of categories passing the size rule is shown
LEVELS = list(S.levels_tested) + list(S.levels_descriptive)


def log(*a):
    print(*a, flush=True)


# ---------------- Seattle ----------------
def format_checks(wm, wm_ok, totals, st, raw, works_tab, fmt, api):
    c = dict(raw, denominator_equals_raw=bool(int(totals.total_checkouts.sum()) == raw['raw_checkouts']),
             mapped_share=float(wm.checkouts.sum() / max(1, raw['raw_checkouts'])),
             work_table_reconciles=bool(int(wm.checkouts.sum()) == int(works_tab[f'checkouts_{IO.SEATTLE_FILE[fmt]}'].sum())))
    if fmt in api:
        a = api[fmt].reindex(st.index)
        both = st.n_rows.notna() & a.n_rows.notna()
        c['api_months_compared'] = int(both.sum())
        c['api_months_rows_equal'] = int((st.n_rows[both] == a.n_rows[both]).sum())
        c['api_months_checkouts_equal'] = int((st.total_checkouts[both] == a.checkouts[both]).sum())
    return c


def build_seattle(P, src):
    N = I.load_nodes(src)
    WT, how, info = I.load_work_theme(P, src)
    api = I.api_counts(P)
    rw = I.load_record_work(P)
    works_tab = IO.read_parquet(P.taxo_v3 / 'spl_works.parquet', columns=['work_id'] + [f'checkouts_{IO.SEATTLE_FILE[f]}' for f in S.seattle_formats])
    info['work_theme works missing from the work table'] = int((~WT.work_id.isin(works_tab.work_id)).sum())
    info['work_theme nodes missing from theme_nodes'] = int((~WT.node_id.isin(N.node_id)).sum())
    panels, overlaps, checks, months, works_any = [], [], {}, {}, set()
    for fmt in S.seattle_formats:
        t0 = time.time()
        wm, totals, st, raw = I.format_month_data(P, S, fmt, rw, api)
        wm_ok = wm[wm.mi.isin(st[st.month_ok].index)]
        works_fmt = wm_ok[wm_ok.checkouts > 0].work_id.unique()
        works_any.update(works_fmt.tolist())
        c = format_checks(wm, wm_ok, totals, st, raw, works_tab, fmt, api)
        for level in LEVELS:
            wtl = WT[WT.level == level]
            df = B.assemble(wm, wtl, st, N, fmt, level, S)
            expect = (wm_ok.merge(wtl.groupby('work_id').strength.sum().rename('s').reset_index(), on='work_id')
                      .eval('checkouts * s').sum())
            c[f'weighted_identity_{level}'] = bool(np.isclose(df.weighted_checkouts.sum(), expect, rtol=1e-9))
            c[f'theme_coverage_{level}'] = float(expect / max(1, wm_ok.checkouts.sum()))
            panels.append(df)
            overlaps.append(B.overlap_pairs(wtl, works_fmt, level, fmt))
        months[fmt], checks[fmt] = st, c
        log(f'{fmt}: rows {raw["raw_rows"]:,}, months {len(st)}, {time.time() - t0:.0f}s')
        del wm, wm_ok
    nodes = N.copy()
    for tag, W in (('main', WT), ('with_title', I.load_work_theme(P, src, include_title=True)[0])):
        n = W[W.work_id.isin(works_any)].groupby('node_id').work_id.nunique()
        nodes[f'n_works_{tag}'] = nodes.node_id.map(n).fillna(0).astype(int)
    return pd.concat(panels, ignore_index=True), pd.concat(overlaps, ignore_index=True), nodes, checks, months, how, info


# ---------------- LibriVox ----------------
def build_librivox(P, N):
    x = I.librivox_inputs(P)
    if x is None:
        return None, 'skipped: librivox_work_theme.parquet not found in taxonomy_v3 (LibriVox is not yet mapped into the taxonomy)'
    rows, rw, WT = x
    W, how = B.main_strength(WT[WT.work_id.notna()])
    wm, totals = B.work_month(rows, rw)
    # NOT IN RECORD: every LibriVox month with views is treated as complete; months without views are missing.
    st = B.month_status(totals[totals.total_checkouts > 0])
    works = wm[wm.checkouts > 0].work_id.unique()
    parts, ov = [], []
    for level in LEVELS:
        wtl = W[W.level == level]
        if wtl.empty:
            continue
        # NOT IN RECORD: the Seattle minimum-size rule is applied to LibriVox with recordings as works and views
        # as checkouts.
        parts.append(B.assemble(wm, wtl, st, N, 'librivox', level, S))
        ov.append(B.overlap_pairs(wtl, works, level, 'librivox'))
    return (pd.concat(parts, ignore_index=True), pd.concat(ov, ignore_index=True), st), f'built ({how})'


# ---------------- report (structural only) ----------------
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


def month_lines(months):
    out = []
    for fmt, st in months.items():
        bad = st[~st.month_ok]
        reasons = {r: ', '.join(B.ym_of(m) for m in g.index) for r, g in bad.groupby('reason')}
        first, last = B.ym_of(st.index.min()), B.ym_of(st.index.max())
        out.append(f'- {fmt}: {first} to {last}, {len(st)} months, {int(st.month_ok.sum())} usable; '
                   + ('; '.join(f'{r}: {v}' for r, v in reasons.items()) if len(bad) else 'no unusable months'))
    return out


def check_line(fmt, c):
    api = (f'SPL API months compared {c["api_months_compared"]}, rows equal {c["api_months_rows_equal"]}, '
           f'checkouts equal {c["api_months_checkouts_equal"]}' if 'api_months_compared' in c else 'no SPL API counts')
    lv = '; '.join(f'{lv}: weighted-sum identity {c[f"weighted_identity_{lv}"]}, theme coverage '
                   f'{100 * c[f"theme_coverage_{lv}"]:.1f}% of checkouts' for lv in LEVELS)
    return (f'- {fmt}: raw rows {c["raw_rows"]:,}; rows whose record has no work {c["unmapped_records"]:,}; '
            f'denominator equals raw checkouts: {c["denominator_equals_raw"]}; checkouts on records with a work '
            f'{100 * c["mapped_share"]:.2f}%; work table reconciles: {c["work_table_reconciles"]}; {api}; {lv}')


def report(P, meta, panel, nodes, overlap, checks, months, how, info, lv_msg, lv_months, changed):
    L = ['## Source', f'- taxonomy: {meta["taxonomy"]}', f'- theme strength: {how}']
    L += [f'- {k}: {v:,}' for k, v in info.items()]
    if meta['development']:
        L += ['- **DEVELOPMENT BUILD**: taxonomy_v3/work_theme.parquet does not exist yet. Rebuild this panel when it '
              'does; steps 10 to 14 refuse a development panel unless --allow-dev-taxonomy is passed.']
    if changed:
        L += [f'- **WARNING**: these inputs changed while the panel was being built; rerun this step: {", ".join(changed)}']
    L += ['- ' + status_line(P), '', '## Months covered (all categories share the format calendar)']
    L += month_lines(months) + (month_lines({'librivox': lv_months}) if lv_months is not None else [])
    L += ['', '## Reconciliation (whole-format totals only)'] + [check_line(f, c) for f, c in checks.items()]
    L += ['', '## Panel size', f'- rows: {len(panel):,}; donor-overlap pairs: {len(overlap):,}']
    for level in LEVELS:
        L.append(f'- {level}: {panel[panel.level == level].node_id.nunique()} categories with data '
                 f'(of {int((nodes.level == level).sum())} nodes)')
    L += ['', f'## Categories passing the minimum-size rule (>= {S.min_works} works with checkouts and median >= '
          f'{S.min_median_weighted:g} weighted checkouts per month in the {S.size_lookback} months before the window)']
    L += IO.md_table(size_counts(panel))
    L += ['', f'- LibriVox: {lv_msg}', '',
          'No category demand series, effect or p-value is shown here (hard rule until the positive controls are run).']
    return L


def run_sim(P, args):
    import _sim
    W = _sim.sim_world(S, seed=args.sim_seed, null=args.sim_null)
    _sim.write_world(P, W, S)
    meta = dict(build_id=IO.build_id(['sim', args.sim_seed, args.sim_null]), taxonomy='simulated', development=False,
                settings_sha256=S.sha256, formats=sorted(W['panel'].format.unique()), simulated=True, inputs={})
    IO.save_json(meta, P.meta)
    st = {}
    for f, g in pd.concat([W['panel'], W['librivox']]).groupby('format'):
        st[f] = pd.DataFrame({'month_ok': g.groupby('mi').month_ok.first()})
        st[f]['reason'] = np.where(st[f].month_ok, '', 'missing in record')
    IO.write_report(P, '01', 'Study 3 demand panel build (simulated)',
                    ['## Months'] + month_lines(st) + ['', '## Size rule'] + IO.md_table(size_counts(W['panel'])), S, meta)
    log('simulated world written to', P.db)


def main():
    ap = IO.parser('Build the Study 3 demand panel')
    ap.add_argument('--sim-seed', type=int, default=0)
    ap.add_argument('--sim-null', action='store_true', help='simulated world without any effects')
    args = ap.parse_args()
    P = IO.Paths(args.sim)
    if args.sim:
        return run_sim(P, args)
    src = I.choose_source(P)
    log('taxonomy source:', src['taxonomy'])
    t_in = I.mtimes(I.input_files(P, S, src))
    panel, overlap, nodes, checks, months, how, info = build_seattle(P, src)
    lv, lv_msg = build_librivox(P, nodes)
    lv_months = None
    if lv is not None:
        lvp, lvo, lv_months = lv
        IO.save_parquet(lvp, P.panel_librivox)
        overlap = pd.concat([overlap, lvo], ignore_index=True)
    elif P.panel_librivox.exists():
        P.panel_librivox.unlink()           # a stale LibriVox panel must not be mixed with a new build
    changed = I.changed_since(t_in)
    meta = dict(build_id=IO.build_id([src['taxonomy'], len(panel), S.sha256]), taxonomy=src['taxonomy'],
                development=src['development'], settings_sha256=S.sha256, formats=list(S.seattle_formats),
                librivox=lv is not None, theme_strength=how, created=time.strftime('%Y-%m-%d %H:%M:%S'),
                months={f: [B.ym_of(st.index.min()), B.ym_of(st.index.max())] for f, st in months.items()},
                inputs=t_in, inputs_changed_during_build=changed)
    IO.save_parquet(panel, P.panel)
    IO.save_parquet(overlap, P.overlap)
    IO.save_parquet(nodes, P.nodes)
    IO.save_json(meta, P.meta)
    L = report(P, meta, panel, nodes, overlap, checks, months, how, info, lv_msg, lv_months, changed)
    path = IO.write_report(P, '01', 'Study 3 demand panel build (structural checks only)', L, S, meta)
    log('\n'.join(L))
    log('report:', path)


if __name__ == '__main__':
    main()
