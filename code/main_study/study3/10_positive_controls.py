# 10. Positive controls (record, positive_controls): COVID-19 (Epidemics and plagues, 2020-03), George Floyd / BLM
# (Race and racism, 2020-06) and #MeToo (Sexual violence and domestic violence, 2017-10), all narrow. They are run
# first; no other Study 3 result is read until they are reported.
# For each control and format: event study, synthetic control with the in-space placebo p-value, event-study
# placebo categories and placebo years (methods in _methods.py, glue in _analysis.py).
# Pass rule: a positive synthetic-control effect over months 0..+2 with one-sided p < 0.05 (the record's
# single-shift rule) in at least one Seattle format. NOT IN RECORD: this reading of "positive demand effect".
# NOT IN RECORD: LibriVox (if built) is shown for the controls but does not decide pass or fail.
# A control category with fewer than 50 works (record) is also run on the flagged title-word backup.
# NOT IN RECORD: the backup run keeps the main donor-overlap table, and a backup PASS is reported as
# 'PASS (flagged title-word backup)' only when the main assignment did not pass.
# Needs: the panel build report. Output: data/db/study3/positive_controls.csv, data/reports/study3_10_positive_controls.md
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from _settings import SETTINGS as S
import _files as IO
import _analysis as A
import _build as B
from _interest import shifts_for_step, status_line

SHOW = ['format', 'skip', 'sc_n_donors', 'es_effect_p', 'es_effect_s', 'es_pretrend', 'sc_effect_p', 'sc_p_p',
        'sc_effect_s', 'sc_p_s', 'pc_es_share_ge_p', 'py_sc_share_ge', 'py_sc_n', 'py_es_share_ge', 'lag_peak']


def find_node(nodes, label, level):
    m = nodes[(nodes.level == level) & (nodes.label.str.lower() == label.lower())]
    if len(m) != 1:
        near = nodes[nodes.label.str.lower().str.contains(label.lower().split()[0], na=False)][['node_id', 'level', 'label']]
        raise SystemExit(f'positive control "{label}" ({level}) not found exactly once in the taxonomy nodes. '
                         f'Similar labels:\n{near.to_string(index=False)}')
    return m.node_id.iloc[0]


def backup_rows(P, node, level):
    """Panel rows of one control category built from the flagged title-word backup (real data only)."""
    import _inputs as I
    src = I.choose_source(P)
    N = I.load_nodes(src)
    WT, how, _ = I.load_work_theme(P, src, include_title=True)
    wtl = WT[(WT.level == level) & (WT.node_id == node)]
    api, rw = I.api_counts(P), I.load_record_work(P)
    parts = []
    for fmt in S.seattle_formats:
        wm, totals, st, raw = I.format_month_data(P, S, fmt, rw, api)
        parts.append(B.assemble(wm, wtl, st, N, fmt, level, S))
    return pd.concat(parts, ignore_index=True)


def run_control(ctx, c, node, formats, backup):
    m0 = B.mi_from_ym(c['shift_month'])
    out = []
    for fmt in formats:
        r = A.test_unit(ctx, c['level'], fmt, node, m0)
        r.update(control=c['name'], title_backup=backup)
        out.append(r)
    return out


def verdict(recs, c):
    tested = [r for r in recs if r['format'] in S.seattle_formats and r.get('skip') == '']
    if not tested:
        return 'NOT TESTABLE (below minimum size)' if c['only_if_size'] else 'FAIL (no format could be tested)'
    hit = [r for r in tested if r.get('sc_effect_p', np.nan) > 0 and r.get('sc_p_p', 1.0) < S.alpha]
    return 'PASS' if hit else 'FAIL'


def gaps_table(recs):
    """Monthly gaps (months -6..+6) from both methods, descriptive (record: covid_mix_note)."""
    rows = []
    for r in recs:
        if r.get('skip') != '':
            continue
        es = json.loads(r.get('es_gaps') or '{}'); sc = json.loads(r.get('sc_gaps') or '{}')
        for m in range(S.es_pretrend[0], S.carry_lag[1] + 1):
            rows.append(dict(format=r['format'], month=m, es_gap=es.get(str(m)), sc_gap=sc.get(str(m))))
    if not rows:
        return []
    G = pd.DataFrame(rows).astype({'es_gap': float, 'sc_gap': float})
    W = G.pivot(index='month', columns='format', values=['es_gap', 'sc_gap'])
    W.columns = [f'{a}_{b}' for a, b in W.columns]
    return IO.md_table(W.reset_index())


def main():
    ap = IO.parser('Study 3 positive controls')
    ap.add_argument('--without-shifts', action='store_true', help='run without the shift part of the donor rule (flagged)')
    args, P, meta, warn = IO.start('10', ap)
    panel, nodes, overlap = IO.load_panels(P), IO.read_parquet(P.nodes), IO.read_parquet(P.overlap)
    shifts, shift_note = shifts_for_step(P, S, args.without_shifts, '10')
    ctx = A.Context(panel, nodes, overlap, shifts, S)
    formats = sorted(panel.format.unique())
    recs, status, lines = [], {}, []
    for c in S.controls:
        node = find_node(nodes, c['label'], c['level'])
        n_main = int(nodes.set_index('node_id').get('n_works_main', pd.Series(dtype=int)).get(node, -1))
        rs = run_control(ctx, c, node, formats, backup=False)
        v = verdict(rs, c)
        note = f'{c["name"]}: {c["label"]} ({c["level"]}, {node}), month 0 = {c["shift_month"]}, works in main assignment: {n_main if n_main >= 0 else "n/a"}'
        if 0 <= n_main < S.title_backup_max_works:
            if P.sim:
                note += '; title-word backup needed but not available in a simulated run'
            else:
                bp = panel[~((panel.node_id == node) & panel.format.isin(S.seattle_formats))]
                ctx_b = A.Context(pd.concat([bp, backup_rows(P, node, c['level'])], ignore_index=True), nodes, overlap, shifts, S)
                rb = run_control(ctx_b, c, node, [f for f in formats if f in S.seattle_formats], backup=True)
                vb = verdict(rb, c)
                note += f'; FLAGGED title-word backup run: {vb}'
                if not v.startswith('PASS') and vb == 'PASS':
                    v = 'PASS (flagged title-word backup)'
                rs += rb
        status[c['name']] = v
        recs += rs
        lines += [f'### {c["name"]}: {v}', '', note, '']
        lines += IO.md_table(pd.DataFrame(rs).reindex(columns=['title_backup'] + SHOW))
        lines += ['', 'Monthly gaps (log share), months -6 to +6, descriptive:', ''] + gaps_table([r for r in rs if not r['title_backup']]) + ['']
    ok = all(v.startswith('PASS') or v.startswith('NOT TESTABLE') for v in status.values())
    R = pd.DataFrame(recs)
    IO.save_csv(R, P.out('positive_controls.csv'))
    head = [f'- controls status: {"PASS" if ok else "FAIL"}'] + [f'- control {k}: {v}' for k, v in status.items()]
    head += [f'- shift part of the donor rule: {shift_note}', f'- {status_line(P)}'] + [f'- WARNING: {w}' for w in warn]
    head += ['', f'Pass rule: positive synthetic-control effect over months {S.window_primary[0]} to +{S.window_primary[1]} with '
             f'one-sided rank p < {S.alpha} in at least one Seattle format. Columns: _p = months {S.window_primary[0]} to '
             f'+{S.window_primary[1]}, _s = months {S.window_secondary[0]} to +{S.window_secondary[1]}; pc_ = share of donor '
             'categories with an event-study effect >= the real one; py_ = share of placebo years with an effect >= the real one.', '']
    if not ok:
        head += ['If a control fails (record): check data and mappings for errors only; log any fix in prereg/DEVIATIONS.md; '
                 'do not tune thresholds on other categories. Step 11 refuses to run until --accept-failed-controls is given.', '']
    path = IO.write_report(P, '10', 'Study 3 positive controls', head + lines, S, meta)
    print('\n'.join(head))
    print('report:', path)


if __name__ == '__main__':
    main()
