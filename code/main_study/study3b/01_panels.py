# 01. Study 3b count panels: weighted checkouts per category, format and month at the narrow, middle and value levels
# (counts, not shares: the record's model takes Y and the exposure N = all checkouts of the format that month).
#   python 01_panels.py                real build (reads data/db/taxonomy_v3/, data/db/study3/ for one reconciliation)
#   python 01_panels.py --sim DIR      simulated world for tests (_simulate.py)
# Outputs (data/db/study3b/): counts_seattle.parquet, counts_librivox.parquet, month_status.parquet, categories.parquet,
#   panel_meta.json; report data/reports/study3b_01_panels.md.
# HARD RULE: this script prints and writes structural checks only (counts of categories, months, feasibility rates), never
# a category's demand: no weighted checkouts of any category are shown.
# NOT IN RECORD: (1) the value level keeps, per format, only the values with >= 12 nonzero months in that format over all
# time (the record's feasibility threshold; a value below it can never be tested); (2) for values without a node the shares
# of a work are computed among the values placed in a node (as the node assignment does); (3) LibriVox months with views
# are complete (as in Study 3).
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _s3
from _settings import SETTINGS as S
import _paths as IO
import _panel as PN
import _methods as M

B3, I3 = _s3.build, _s3.inputs
REF_MONTHS = ['2017-10', '2020-03', '2020-06']      # months 0 of the three positive controls
NODE_LEVELS = ('narrow', 'middle')


def log(*a):
    print(*a, flush=True)


def ym(mi):
    return B3.ym_of(mi)


# ---------------- Seattle ----------------
def build_seattle(P, src):
    N = I3.load_nodes(src)
    WT, how, info = I3.load_work_theme(P, src)
    api, rw = I3.api_counts(P), I3.load_record_work(P)
    EV = IO.read_parquet(P.taxo_v3 / 'work_theme_value.parquet')
    VS = PN.value_strengths(EV, 'work_id')
    info['values with a node'] = int(VS.theme.nunique())
    info['values without a node (left out of the shares)'] = int(EV[EV.node_id.isna()].theme.nunique())
    info['works with value evidence'] = int(VS.work_id.nunique())
    longs, status, checks = [], [], {}
    for fmt in S.seattle_formats:
        t0 = time.time()
        wm, totals, st, raw = I3.format_month_data(P, S, fmt, rw, api)
        grid0, T = int(st.index.min()), len(st)
        okm = set(st[st.month_ok].index.tolist())
        c = dict(raw, mapped_share=float(wm.checkouts.sum() / max(1, raw['raw_checkouts'])),
                 denominator_equals_raw=bool(int(totals.total_checkouts.sum()) == raw['raw_checkouts']))
        wm_ok = wm[wm.mi.isin(okm)]
        for level in NODE_LEVELS:
            wtl = WT[WT.level == level]
            ids = sorted(wtl.node_id.unique())
            D = PN.node_dense(wm, wtl, ids, grid0, T, okm)
            expect = (wm_ok.merge(wtl.groupby('work_id').strength.sum().rename('s').reset_index(), on='work_id').eval('checkouts * s').sum())
            c[f'weighted_identity_{level}'] = bool(np.isclose(D.sum(), expect, rtol=1e-9))
            c[f'theme_coverage_{level}'] = float(expect / max(1, wm_ok.checkouts.sum()))
            longs.append(PN.sparse_rows(level, ids, D, fmt, grid0))
            del D
        themes, D = PN.theme_month_dense(wm, VS, 'work_id', grid0, T, okm)
        expect = wm_ok.merge(VS.groupby('work_id').strength.sum().rename('s').reset_index(), on='work_id').eval('checkouts * s').sum()
        c['weighted_identity_value'] = bool(np.isclose(D.sum(), expect, rtol=1e-9))
        c['theme_coverage_value'] = float(expect / max(1, wm_ok.checkouts.sum()))
        nz = (D > 0).sum(1)
        keep = nz >= PN.VALUE_MIN_NONZERO
        c['values_with_checkouts'] = int((nz > 0).sum()); c['values_kept'] = int(keep.sum())
        longs.append(PN.sparse_rows('value', themes, D, fmt, grid0, keep))
        del D, wm, wm_ok
        stt = st.reset_index().rename(columns={'mi': 'mi'})[['mi', 'month_ok', 'total_checkouts', 'n_rows', 'reason']]
        stt.insert(0, 'format', fmt)
        status.append(stt)
        checks[fmt] = c
        log(f'{fmt}: rows {raw["raw_rows"]:,}, months {T}, values kept {c["values_kept"]:,}, {time.time() - t0:.0f}s')
    cats = [N[N.level.isin(NODE_LEVELS)][['node_id', 'level', 'parent', 'broad_id', 'label']]]
    V = VS.groupby('theme', as_index=False).node_id.first().rename(columns={'theme': 'node_id', 'node_id': 'parent'})
    V['level'] = 'value'; V['broad_id'] = V.parent.str.split('.').str[0]; V['label'] = V.node_id
    cats.append(V[['node_id', 'level', 'parent', 'broad_id', 'label']])
    return pd.concat(longs, ignore_index=True), pd.concat(status, ignore_index=True), pd.concat(cats, ignore_index=True), checks, how, info, N, WT


# ---------------- LibriVox ----------------
def librivox_tables(P):
    """LibriVox views as rows of a format 'librivox' (book ids coded as works), the node-level and value-level mappings
    with the same book codes. None when the mapping files are missing."""
    f_node, f_val = P.taxo_v3 / 'librivox_work_theme.parquet', P.taxo_v3 / 'librivox_work_theme_value.parquet'
    if not (f_node.exists() and f_val.exists() and P.librivox_listening.exists()):
        return None
    L = IO.read_parquet(P.librivox_listening)
    WT = IO.read_parquet(f_node).rename(columns={'book_id': 'work_id'})
    VV = IO.read_parquet(f_val).rename(columns={'book_id': 'work_id'})
    uniq = pd.Index(pd.concat([L.book_id, WT.work_id, VV.work_id]).astype(str).unique())
    code = pd.Series(np.arange(len(uniq)), index=uniq)
    rows = pd.DataFrame({'record_id': code.reindex(L.book_id.astype(str)).to_numpy(), 'year': L.period.str[:4].astype(int),
                         'month': L.period.str[5:7].astype(int), 'checkouts': L.listens.astype(np.int64)})
    rw = pd.DataFrame({'record_id': np.arange(len(uniq)), 'work_id': np.arange(len(uniq))})
    WT['work_id'] = code.reindex(WT.work_id.astype(str)).to_numpy()
    VV['work_id'] = code.reindex(VV.work_id.astype(str)).to_numpy()
    return rows, rw, WT[WT.work_id.notna()], VV[VV.work_id.notna()].assign(work_id=lambda d: d.work_id.astype(np.int64))


def build_librivox(P):
    x = librivox_tables(P)
    if x is None:
        return None, None, 'skipped: LibriVox mapping or listening file not found'
    rows, rw, WT, VV = x
    W, how = B3.main_strength(WT)
    wm, totals = B3.work_month(rows, rw)
    st = B3.month_status(totals[totals.total_checkouts > 0])      # NOT IN RECORD (Study 3 choice): every month with views is complete
    grid0, T = int(st.index.min()), len(st)
    okm = set(st[st.month_ok].index.tolist())
    longs = []
    for level in NODE_LEVELS:
        wtl = W[W.level == level]
        ids = sorted(wtl.node_id.unique())
        longs.append(PN.sparse_rows(level, ids, PN.node_dense(wm, wtl, ids, grid0, T, okm), 'librivox', grid0))
    VS = PN.value_strengths(VV, 'work_id')
    themes, D = PN.theme_month_dense(wm, VS, 'work_id', grid0, T, okm)
    keep = (D > 0).sum(1) >= PN.VALUE_MIN_NONZERO
    longs.append(PN.sparse_rows('value', themes, D, 'librivox', grid0, keep))
    stt = st.reset_index()[['mi', 'month_ok', 'total_checkouts', 'n_rows', 'reason']]
    stt.insert(0, 'format', 'librivox')
    V = VS.groupby('theme', as_index=False).node_id.first().rename(columns={'theme': 'node_id', 'node_id': 'parent'})
    V['level'] = 'value'; V['broad_id'] = V.parent.str.split('.').str[0]; V['label'] = V.node_id
    return pd.concat(longs, ignore_index=True), stt, f'built ({how}); values kept {int(keep.sum())}', V


# ---------------- structural report ----------------
def find_node(nodes, label, level):
    m = nodes[(nodes.level == level) & (nodes.label.str.lower() == label.lower())]
    if len(m) != 1:
        raise SystemExit(f'positive control "{label}" ({level}) not found exactly once in the taxonomy nodes')
    return m.node_id.iloc[0]


def structure(counts_by_level, cats, formats, tag):
    """Feasibility structure at the control months: per level the number of categories with any data, the number
    feasible under the record's rule (and by number of formats entering). Only counts of categories, no demand."""
    rows = []
    for level, C in counts_by_level.items():
        for m in REF_MONTHS:
            fz = M.feasibility(C, B3.mi_from_ym(m), S)
            nf = fz['elig'].sum(1)
            r = dict(kind=tag, level=level, month0=m, categories=len(C.ids), feasible=int(fz['feasible'].sum()),
                     feasible_share=float(fz['feasible'].mean()), usable_formats=','.join(fz['usable_formats']) or 'none')
            for k in range(1, len(formats) + 1):
                r[f'in_{k}_formats'] = int((nf == k).sum())
            rows.append(r)
    return pd.DataFrame(rows)


def control_rows(counts, nodes, cats, formats, tag, level_label=True):
    """Per control and format: usable fit months and nonzero months of the 24 (structure only), and whether the format
    enters the joint model and the control is feasible. Values inside each control node: how many are feasible."""
    rows = []
    C = counts['narrow']
    for c in S.controls:
        node = find_node(nodes, c['label'], c['level'])
        i = C.index.get(node)
        m0 = B3.mi_from_ym(c['shift_month'])
        if i is None:
            rows.append(dict(kind=tag, control=c['name'], month0=c['shift_month'], format='-', note='category has no checkouts at all'))
            continue
        fz = M.feasibility(C, m0, S, rows=[i])
        for j, f in enumerate(C.formats):
            rows.append(dict(kind=tag, control=c['name'], month0=c['shift_month'], format=f, usable_fit_months=int(fz['avail'][f].sum()),
                             nonzero_fit_months=int(fz['nonzero'][f][0]), enters_model=bool(fz['elig'][0, j]), control_feasible=bool(fz['feasible'][0])))
        V = counts.get('value')
        if V is not None:
            vids = cats[(cats.level == 'value') & (cats.parent == node)].node_id.to_numpy()
            vi = np.array([V.index[v] for v in vids if v in V.index], dtype=int)
            fv = M.feasibility(V, m0, S, rows=vi) if len(vi) else None
            rows.append(dict(kind=tag, control=c['name'], month0=c['shift_month'], format='value level',
                             note=f'{len(vids)} values placed in the node, {len(vi)} with any stored counts, '
                                  f'{int(fv["feasible"].sum()) if fv is not None else 0} feasible'))
    return pd.DataFrame(rows)


def month_lines(status):
    out = []
    for fmt, g in status.groupby('format', sort=False):
        bad = g[~g.month_ok]
        reasons = {r: ', '.join(ym(m) for m in h.mi) for r, h in bad.groupby('reason')}
        out.append(f'- {fmt}: {ym(g.mi.min())} to {ym(g.mi.max())}, {len(g)} months, {int(g.month_ok.sum())} usable; '
                   + ('; '.join(f'{r}: {v}' for r, v in reasons.items()) if len(bad) else 'no unusable months'))
    return out


def reconcile_with_study3(P, long, N):
    """Narrow and middle weighted checkouts must equal the Study 3 panel's (same inputs, same functions). Structural
    identity check; only the maximum difference is shown."""
    f = P.study3 / 'demand_panel.parquet'
    if not f.exists():
        return 'Study 3 panel not found, not compared'
    old = IO.read_parquet(f, columns=['level', 'node_id', 'format', 'mi', 'month_ok', 'weighted_checkouts'])
    old = old[old.level.isin(NODE_LEVELS) & old.month_ok & (old.weighted_checkouts > 0)]
    new = long[long.level.isin(NODE_LEVELS) & (long.format != 'librivox')]
    m = old.merge(new, on=['level', 'node_id', 'format', 'mi'], how='outer')
    only = int((m.weighted_checkouts.isna() | m.y.isna()).sum())
    d = float((m.weighted_checkouts - m.y).abs().max()) if len(m) else 0.0
    return (f'narrow and middle weighted checkouts equal the Study 3 panel: {only == 0 and d < 1e-6} '
            f'({len(m):,} category-format-months compared, {only} present in only one table, largest absolute difference {d:.2e})')


def report(P, meta, how, info, lv_msg, checks, status, cats, long, counts_s, counts_l, struct, ctrl, changed, s3note, interest_note):
    L = ['## Source', f'- taxonomy: {meta["taxonomy"]}', f'- theme strength (narrow, middle): {how}']
    L += [f'- {k}: {v:,}' for k, v in info.items()]
    if changed:
        L += [f'- **WARNING**: inputs changed while the panel was being built; rerun this step: {", ".join(changed)}']
    L += ['', '## Months covered (all categories share the format calendar)'] + month_lines(status)
    L += ['', '## Reconciliation (whole-format totals and identities only)']
    for fmt, c in checks.items():
        L.append(f'- {fmt}: raw rows {c["raw_rows"]:,}; rows whose record has no work {c["unmapped_records"]:,}; denominator equals raw '
                 f'checkouts: {c["denominator_equals_raw"]}; checkouts on records with a work {100 * c["mapped_share"]:.2f}%; ' +
                 '; '.join(f'{lv}: weighted-sum identity {c[f"weighted_identity_{lv}"]}, theme coverage {100 * c[f"theme_coverage_{lv}"]:.1f}% of checkouts'
                           for lv in ('narrow', 'middle', 'value')) + f'; values with any checkout {c["values_with_checkouts"]:,}, kept (>= {PN.VALUE_MIN_NONZERO} nonzero months in the format) {c["values_kept"]:,}')
    L += [f'- {s3note}']
    L += ['', '## Panel size']
    for level in S.levels_tested:
        n_tot = int((cats.level == level).sum())
        L.append(f'- {level}: {len(counts_s[level].ids):,} categories in the Seattle count panel (of {n_tot:,} in the taxonomy)'
                 + (f'; LibriVox {len(counts_l[level].ids):,}' if counts_l and level in counts_l else ''))
    L += [f'- rows in counts_seattle.parquet: {int(((long.format != "librivox")).sum()):,}', f'- LibriVox: {lv_msg}']
    L += ['', f'## Feasibility (record: nonzero weighted checkout in >= {S.feas_min_nonzero} of the {S.es_fit_len} fit months in at least one format; '
          'a format enters the joint model only with that many nonzero months itself and >= 75% of the fit months usable)']
    L += IO.md_table(IO.tidy(struct))
    L += ['', '## The three control categories (structure of the fit window only)'] + IO.md_table(IO.tidy(ctrl))
    L += ['', '## Interest series at the value level', f'- {interest_note}']
    L += ['', 'No category demand series, count, effect or p-value is shown here (hard rule).']
    return L


def run_sim(P, args):
    import _simulate
    meta = _simulate.write_world(P, S, seed=args.sim_seed, null=args.sim_null)
    IO.write_report(P, '01', 'Study 3b count panels (simulated)', ['## Panel', '- simulated world, no structural report'], S, meta)
    log('simulated world written to', P.db)


def main():
    ap = IO.parser('Build the Study 3b count panels')
    ap.add_argument('--sim-seed', type=int, default=0)
    ap.add_argument('--sim-null', action='store_true')
    args = ap.parse_args()
    P = IO.Paths(args.sim)
    if args.sim:
        return run_sim(P, args)
    src = I3.choose_source(P)
    if src['development']:
        raise SystemExit('01 refuses to run: taxonomy_v3/work_theme.parquet is missing (development fallback is not allowed in Study 3b)')
    inputs = I3.mtimes(I3.input_files(P, S, src) + [str(P.taxo_v3 / 'work_theme_value.parquet'), str(P.taxo_v3 / 'librivox_work_theme_value.parquet')])
    long, status, cats, checks, how, info, N, WT = build_seattle(P, src)
    lv_long, lv_status, lv_msg, lv_V = build_librivox(P)
    s3note = reconcile_with_study3(P, long, N)
    if lv_long is not None:
        IO.save_parquet(lv_long, P.counts_librivox)
        cats = pd.concat([cats, lv_V[['node_id', 'level', 'parent', 'broad_id', 'label']]], ignore_index=True).drop_duplicates(['level', 'node_id'])
        status = pd.concat([status, lv_status], ignore_index=True)
    elif P.counts_librivox.exists():
        P.counts_librivox.unlink()
    changed = I3.changed_since(inputs)
    IO.save_parquet(long, P.counts)
    IO.save_parquet(status, P.months)
    # categories actually present in each level's count panel (value level: kept values only)
    present = {lv: sorted(set(long[long.level == lv].node_id) | set(lv_long[lv_long.level == lv].node_id if lv_long is not None else [])) for lv in S.levels_tested}
    keep = pd.concat([pd.DataFrame({'level': lv, 'node_id': ids}) for lv, ids in present.items()])
    cats = cats.merge(keep, on=['level', 'node_id'], how='inner').drop_duplicates(['level', 'node_id'])
    IO.save_parquet(cats, P.categories)
    meta = dict(build_id=IO.build_id([len(long), S.sha256, S.sha256_study3]), taxonomy='v3', formats=list(S.seattle_formats), librivox=lv_long is not None,
                created=time.strftime('%Y-%m-%d %H:%M:%S'), inputs=inputs, inputs_changed_during_build=changed,
                months={f: [ym(g.mi.min()), ym(g.mi.max())] for f, g in status.groupby('format')})
    IO.save_json(meta, P.meta)
    counts_s = {lv: PN.make_counts(long, status, lv, sorted(cats[cats.level == lv].node_id), list(S.seattle_formats)) for lv in S.levels_tested}
    counts_l = {}
    if lv_long is not None:
        counts_l = {lv: PN.make_counts(lv_long, lv_status, lv, sorted(set(lv_long[lv_long.level == lv].node_id)), ['librivox']) for lv in S.levels_tested}
    nodes = N[N.level.isin(NODE_LEVELS)]
    struct = structure(counts_s, cats, list(S.seattle_formats), 'Seattle joint model')
    if counts_l:
        struct = pd.concat([struct, structure(counts_l, cats, ['librivox'], 'LibriVox')], ignore_index=True)
    ctrl = control_rows(counts_s, nodes, cats, list(S.seattle_formats), 'Seattle')
    interest_note = value_interest_note(P, cats)
    L = report(P, meta, how, info, lv_msg, checks, status, cats, long, counts_s, counts_l, struct, ctrl, changed, s3note, interest_note)
    path = IO.write_report(P, '01', 'Study 3b count panels (structural checks only)', L, S, meta)
    log('\n'.join(L))
    log('report:', path)


def value_interest_note(P, cats):
    """How many of the value-level interest series belong to values that are in the demand count panel (structure only)."""
    out = []
    v = set(cats[cats.level == 'value'].node_id)
    for name, f in (('Wikipedia', P.interest / 'wiki' / 'weekly_value.parquet'), ('GDELT', P.interest / 'gdelt' / 'weekly_value.parquet')):
        if f.exists():
            vals = set(pd.read_parquet(f, columns=['value']).value.unique())
            out.append(f'{name}: {len(vals)} value series, {len(vals & v)} of them have a demand count panel row set (>= {PN.VALUE_MIN_NONZERO} nonzero months in some format)')
        else:
            out.append(f'{name}: value series not found')
    return '; '.join(out)


if __name__ == '__main__':
    main()
