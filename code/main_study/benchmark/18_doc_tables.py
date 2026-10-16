# Method benchmark, stage 2: markdown tables for the benchmark document, from the result tables of 03_evaluate.py --stage2.
# Writes data/db/benchmark/stage2_results/doc_tables.md (tables only; the text around them is written by hand).
#   ../../../.venv/bin/python 18_doc_tables.py
import sys, pathlib, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import numpy as np, pandas as pd
import _settings as ST

_spec = importlib.util.spec_from_file_location('fig', HERE / '16_figure_stage2.py'); FIG = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(FIG)
RES = ST.DB / 'benchmark' / 'stage2_results'
pretty, family = FIG.pretty, FIG.family


def yn(v):
    return 'yes' if (isinstance(v, (bool, np.bool_)) and bool(v)) else ('no' if isinstance(v, (bool, np.bool_)) else '')


def f3(x, d=3):
    return '' if (x is None or (isinstance(x, float) and np.isnan(x))) else f'{x:.{d}f}'


def ci3(r, c, lo, hi, d=3):
    return '' if pd.isna(r[c]) else (f'{r[c]:.{d}f} ({r[lo]:.{d}f} to {r[hi]:.{d}f})' if pd.notna(r.get(lo)) else f'{r[c]:.{d}f}')


def table1(T, nmax=16):
    order = FIG.select_rows(T).index.tolist()
    if 'seasonal_naive' in T.index:
        order.append('seasonal_naive')
    L = ['| Pipeline | Error against repeating last month (95% interval) | In level set | Rank correlation of change (95% interval) | In rise set | Surge average precision | Error, % | Direction right |',
         '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for p in order:
        r = T.loc[p]
        L.append(f'| {pretty(p)} | {ci3(r, "AvgRelMAE", "ci_lo", "ci_hi")} | {yn(r.in_MCS_level)} | {ci3(r, "rho", "rho_lo", "rho_hi")} | {yn(r.in_MCS_rise)} | {f3(r.AP)} | {f3(r.mae_pct, 2)} | {f3(r.direction_acc, 3)} |')
    return '\n'.join(L) + '\n'


def table_pairs(P, kind, title_rows=True):
    P = P[P.kind == kind].copy()
    L = ['| Model | Added to it | Error change (95% interval) | Rank correlation change | Surge precision change |', '| --- | --- | --- | --- | --- |']
    for _, r in P.iterrows():
        mdl = pretty(r.base) if r.base.split('_')[0] not in ('chronos2',) else 'Chronos-2'
        mdl = {'ridgechg': 'Ridge on the change', 'lgbmchg': 'LightGBM on the change', 'catchg': 'CatBoost on the change'}.get(r.base.split('_')[0], mdl)
        add = FIG.FSET.get(r.other.split('_', 1)[1], r.other) if not r.other.startswith('chronos2') else FIG.SPECIAL.get(r.other, r.other).replace('Chronos-2 ', '')
        pc = lambda x: f'{(x - 1) * 100:+.1f}%'
        mae = f'{pc(r.mae_ratio)} ({pc(r.mae_lo)} to {pc(r.mae_hi)})'
        rho = f'{r.rho_diff:+.3f} ({r.rho_diff_lo:+.3f} to {r.rho_diff_hi:+.3f})' if 'rho_diff' in r and pd.notna(r.get('rho_diff')) else ''
        ap = f'{r.ap_diff:+.3f} ({r.ap_diff_lo:+.3f} to {r.ap_diff_hi:+.3f})' if 'ap_diff' in r and pd.notna(r.get('ap_diff')) else ''
        L.append(f'| {mdl} | {add} | {mae} | {rho} | {ap} |')
    return '\n'.join(L) + '\n'


ROUT_ROWS = [('Wikipedia concept pages, volume (hand-checked)', 'DVcur', 'chronos2_cur'),
             ('Wikipedia concept pages, all ten features', 'DW', None),
             ('Wikipedia concept pages, with the lasting-rise state', 'DWS', None),
             ('Wikipedia concept pages, duration-weighted', 'DVcurdw', 'chronos2_curdw'),
             ('Book and author articles (routed through the books)', 'DVbk', 'chronos2_bk'),
             ('Top pages read in context (zero-shot classifier)', 'DVnli', 'chronos2_nli'),
             ('Top pages routed by embedding similarity', 'DVtop', 'chronos2_top'),
             ('Articles weighted by past demand (demand-aligned)', 'DVdem', None)]
MODELS = [('Chronos-2', None), ('CatBoost on the change', 'catchg'), ('LightGBM on the change', 'lgbmchg'), ('Ridge on the change', 'ridgechg')]


def table_routing(P):
    Q = P[P.kind == 'behavior against no behavior'].set_index(['base', 'other'])
    pc = lambda x: f'{(x - 1) * 100:+.1f}%'

    def cell(base, other):
        if (base, other) not in Q.index:
            return ''
        r = Q.loc[(base, other)]
        return f'{pc(r.mae_ratio)} ({pc(r.mae_lo)} to {pc(r.mae_hi)})'
    L = ['| Behavior input | ' + ' | '.join(m for m, _ in MODELS) + ' | Rank correlation, Chronos-2 |', '| --- |' + ' --- |' * (len(MODELS) + 1)]
    for name, fs, ch in ROUT_ROWS:
        cells = []
        for m, key in MODELS:
            cells.append(cell('chronos2', ch) if key is None and ch else (cell(f'{key}_D', f'{key}_{fs}') if key else ''))
        rho = ''
        if ch and ('chronos2', ch) in Q.index:
            r = Q.loc[('chronos2', ch)]
            rho = f'{r.rho_diff:+.3f} ({r.rho_diff_lo:+.3f} to {r.rho_diff_hi:+.3f})'
        L.append(f'| {name} | ' + ' | '.join(cells) + f' | {rho} |')
    return '\n'.join(L) + '\n'


SEG_PIPES = ['chronos2_cur', 'chronos2_curdw', 'chronos2_bk', 'chronos2', 'chronos', 'catchg_D', 'catchg_DWS', 'median_s2_all', 'seasonal_naive']
SEG_NAMES = [('quiet', 'Quiet months'), ('after short rise', 'After a short rise'), ('after lasting rise', 'After a lasting rise'), ('surge months (outcome-defined)', 'Surge months (picked by the outcome)')]


def table_segments(S, h):
    S = S.reset_index(names='pipeline')
    L = ['| Pipeline | ' + ' | '.join(n for _, n in SEG_NAMES) + ' |', '| --- |' + ' --- |' * len(SEG_NAMES)]
    head = []
    for key, name in SEG_NAMES:
        g = S[S.segment == f'h{h} {key}']
        head.append('' if 'series' not in g or g.series.isna().all() else f'{int(g.series.dropna().iloc[0])} series, {int(g.rows.dropna().iloc[0]):,} forecasts')
    L.append('| Size of the segment | ' + ' | '.join(head) + ' |')
    for p in SEG_PIPES:
        cells = []
        for key, name in SEG_NAMES:
            g = S[(S.segment == f'h{h} {key}') & (S.pipeline == p)]
            cells.append('' if len(g) == 0 or pd.isna(g.AvgRelMAE.iloc[0]) else f'{g.AvgRelMAE.iloc[0]:.3f} ({g.ci_lo.iloc[0]:.3f} to {g.ci_hi.iloc[0]:.3f})')
        L.append(f'| {pretty(p)} | ' + ' | '.join(cells) + ' |')
    return '\n'.join(L) + '\n'


HZ_PIPES = ['chronos2_cur', 'chronos2', 'chronos', 'catchg_D', 'median_s2_all', 'median_all']
HZ_COLS = [('A2', 'Print and ebook, 1 month'), ('B2', 'Print and ebook, 2 months'), ('C2', 'Print and ebook, 3 months'),
           ('D2_h1', 'Audiobooks, 1 month'), ('D2_h2', 'Audiobooks, 2 months'), ('D2_h3', 'Audiobooks, 3 months'), ('E2_h1', 'LibriVox, 1 month'), ('E2_h2', 'LibriVox, 2 months')]


def table_horizons():
    # rows = the library/format and the horizon, columns = pipelines; * = in the 90% confidence set of the level task of that comparison
    tabs = {k: pd.read_csv(RES / f'{k}_table.csv', index_col=0) for k, _ in HZ_COLS if (RES / f'{k}_table.csv').exists()}
    L = ['| Library and horizon | ' + ' | '.join(pretty(p) for p in HZ_PIPES) + ' | Error of repeating last month, % of a theme\'s share |',
         '| --- |' + ' --- |' * (len(HZ_PIPES) + 1)]
    for k, n in HZ_COLS:
        if k not in tabs:
            continue
        T = tabs[k]
        cells = []
        for p in HZ_PIPES:
            if p not in T.index:
                cells.append('')
                continue
            r = T.loc[p]
            cells.append(f'{r.AvgRelMAE:.3f}' + ('*' if (isinstance(r.in_MCS_level, (bool, np.bool_)) and bool(r.in_MCS_level)) else ''))
        nm = f'{T.loc["naive", "mae_pct"]:.1f}%' if 'naive' in T.index else ''
        L.append(f'| {n} | ' + ' | '.join(cells) + f' | {nm} |')
    return '\n'.join(L) + '\n'


LRN_PIPES = [('chronos2', 'Chronos-2'), ('chronos', 'Chronos-Bolt'), ('median_s2_demand', 'Median of the models (borrowing history only)'),
             ('lgbmchg_D', 'LightGBM on the change'), ('catchg_D', 'CatBoost on the change'), ('ridgechg_D', 'Ridge on the change'), ('revert6', 'Mean of last 6 months')]
LRN_GROUPS = [('print', 'Print and ebook'), ('audiobooks', 'Audiobooks')]


def table_learned():
    """Themes learned from book text against subject-heading themes, demand-only pipelines, one month ahead (15d_learned_report.py outputs)."""
    meta = {}
    cols = [(g, lev, src) for g, _ in LRN_GROUPS for lev in ('middle', 'narrow') for src in ('learned', 'subject-heading')]
    tabs = {}
    for g, lev, src in cols:
        f = RES / f'learned_{src}_{g}_{lev}.csv'
        if f.exists():
            tabs[(g, lev, src)] = pd.read_csv(f, index_col=0)
    if not tabs:
        return ''
    head = ['Pipeline'] + [f'{dict(LRN_GROUPS)[g]}, {lev}: {"learned" if src == "learned" else "subject-heading"}' for g, lev, src in cols if (g, lev, src) in tabs]
    L = ['| ' + ' | '.join(head) + ' |', '| --- |' + ' --- |' * (len(head) - 1)]
    ser = {}
    rep = ST.DATA / 'reports' / 'benchmark_stage2_learned.md'
    if rep.exists():
        for line in rep.read_text().splitlines():
            parts = [x.strip() for x in line.split('|')]
            if len(parts) >= 6 and parts[0] in ('learned from book text', 'subject-heading themes') and parts[3].isdigit():
                ser[(('print' if parts[1] == 'print and ebook' else 'audiobooks'), parts[2], 'learned' if parts[0].startswith('learned') else 'subject-heading')] = int(parts[3])
    L.append('| Series | ' + ' | '.join(str(ser.get(k, '')) for k in cols if k in tabs) + ' |')
    L.append("| Error of repeating last month, % of a theme's share | " + ' | '.join(f'{tabs[k].loc["naive", "mae_pct"]:.1f}%' for k in cols if k in tabs) + ' |')
    for p, name in LRN_PIPES:
        cells = []
        for k in cols:
            if k not in tabs:
                continue
            T = tabs[k]
            r = T.loc[p]
            cells.append(f'{r.AvgRelMAE:.3f}' + ('\u2020' if (isinstance(r.in_MCS_level, (bool, np.bool_)) and bool(r.in_MCS_level)) else ''))
        L.append(f'| {name} | ' + ' | '.join(cells) + ' |')
    return '\n'.join(L) + '\n'


def main():
    out = []
    A = pd.read_csv(RES / 'A2_table.csv', index_col=0)
    out += ['## Table A2 (main)', '', table1(A)]
    pp = RES / 'A2_pairs.csv'
    if pp.exists():
        P = pd.read_csv(pp)
        for kind in P.kind.unique():
            out += [f'## Pairs: {kind}', '', table_pairs(P, kind)]
    if pp.exists():
        out += ['## Routing table', '', table_routing(pd.read_csv(pp))]
    sp = RES / 'segments.csv'
    if sp.exists():
        S = pd.read_csv(sp, index_col=0)
        for h in (1, 2, 3):
            out += [f'## Segments, horizon {h}', '', table_segments(S, h)]
    out += ['## Horizons and formats', '', table_horizons()]
    lt = table_learned()
    if lt:
        out += ['## Learned categories', '', lt]
    (RES / 'doc_tables.md').write_text('\n'.join(out))
    print('wrote', RES / 'doc_tables.md')


if __name__ == '__main__':
    main()
