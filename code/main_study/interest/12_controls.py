# 12. Interest-side positive controls, largest shifts per source and year, and the share of shifts found in both sources.
# Descriptive only: no demand data are read. Writes markdown tables for the checkpoint report and CSVs.
# Outputs (data/db/interest/): controls_weekly.csv, controls_summary.csv, top_shifts_by_year.csv, shared_shifts.csv,
#                               checkpoint_tables.md
import numpy as np, pandas as pd
from _ci import OUT, GD, WK, settings, load_taxonomy
import _shifts as SH

S = settings()
W = pd.read_parquet(f'{OUT}/shift_weekly.parquet')
SHF = pd.read_parquet(f'{OUT}/shifts.parquet')
COV = pd.read_csv(f'{OUT}/coverage.csv')
V, N = load_taxonomy()
label = dict(zip(N.node_id, N.label))
MIN = {'wikipedia': S['min_wiki_views'], 'gdelt': S['min_gdelt_mentions']}
GT = pd.read_parquet(f'{GD}/weekly_node.parquet')          # GDELT tone per node and week

CONTROLS = [
    dict(name='Epidemics and plagues, COVID-19', node='B15.M04.N05', values=['plague', 'epidemiology'], show=('2020-01-06', '2020-05-25'),
         expect=('2020-01-13', '2020-04-27'), expected='around March 2020'),
    dict(name='Race and racism, George Floyd and BLM', node='B05.M02.N02', values=['racism'], show=('2020-04-27', '2020-08-03'),
         expect=('2020-05-18', '2020-07-06'), expected='late May to June 2020'),
    dict(name='Sexual and domestic violence, #MeToo', node='B12.M01.N02', values=['sexual violence'], show=('2017-08-28', '2017-12-04'),
         expect=('2017-10-02', '2017-11-13'), expected='October 2017'),
    dict(name='Climate change and weather, climate strikes', node='B09.M07.N02', values=['climate change'], show=('2019-07-29', '2019-11-04'),
         expect=('2019-08-26', '2019-10-14'), expected='September 2019'),
]

# value-level series for the control values (labelled with the same rules)
vw = {'gdelt': pd.read_parquet(f'{GD}/weekly_value.parquet').rename(columns={'mentions': 'v'}),
      'wikipedia': pd.read_parquet(f'{WK}/weekly_value.parquet').rename(columns={'views': 'v'})}
val_weekly, val_shifts = [], []
for c in CONTROLS:
    for v in c['values']:
        for src, df in vw.items():
            g = df[df.value == v]
            if g.empty:
                continue
            s = g.rename(columns={'share': 'x'}).assign(valid=lambda d: ~d.partial_week)[['week', 'x', 'v', 'valid']]
            w, sh = SH.label_series(s, S, MIN[src])
            w['source'] = src; w['series'] = f'value: {v}'; val_weekly.append(w)
            for d in sh:
                d.update(source=src, series=f'value: {v}'); val_shifts.append(d)
VW = pd.concat(val_weekly); VS = pd.DataFrame(val_shifts)


def event(sh, wk):
    """Text for a week: start / label / in shift."""
    out = []
    for r in sh.itertuples():
        if r.start_week == wk:
            out.append('start')
        if r.label_week is not None and pd.notna(r.label_week) and r.label_week == wk:
            out.append(f'{r.label} (size {r.size:.1f})')
    return ', '.join(out)


def fmt(x, d=2):
    return '' if x is None or (isinstance(x, float) and not np.isfinite(x)) else f'{x:.{d}f}'


md = []
rows_weekly, rows_summary = [], []
for c in CONTROLS:
    a, b = pd.Timestamp(c['show'][0]), pd.Timestamp(c['show'][1])
    ea, eb = pd.Timestamp(c['expect'][0]), pd.Timestamp(c['expect'][1])
    series = [('node', 'wikipedia'), ('node', 'gdelt')] + [(f'value: {v}', s) for v in c['values'][:1] for s in ('wikipedia', 'gdelt')]
    tab = {}
    for kind, src in series:
        if kind == 'node':
            w = W[(W.source == src) & (W.node_id == c['node'])]; sh = SHF[(SHF.source == src) & (SHF.node_id == c['node'])]
        else:
            w = VW[(VW.source == src) & (VW.series == kind)]; sh = VS[(VS.source == src) & (VS.series == kind)] if len(VS) else VS
        w = w[w.week.between(a, b)].set_index('week')
        tab[(kind, src)] = (w, sh)
        hit = sh[sh.start_week.between(ea, eb)] if len(sh) else sh
        ongoing = sh[(sh.start_week < ea) & ((sh.end_week.isna()) | (sh.end_week >= ea))] if len(sh) else sh
        r0 = hit.iloc[0] if len(hit) else (ongoing.iloc[0] if len(ongoing) else None)
        ww = w[w.index.to_series().between(ea, eb)]
        rows_summary.append(dict(control=c['name'], series=kind if kind != 'node' else f"node {c['node']}", source=src,
                                 expected=c['expected'], shift_in_window=r0 is not None,
                                 start_week=None if r0 is None else r0.start_week.date(), label=None if r0 is None else r0.label,
                                 label_week=None if r0 is None or pd.isna(r0.label_week) else pd.Timestamp(r0.label_week).date(),
                                 size=None if r0 is None else round(float(r0['size']), 2),
                                 whole_peak=None if r0 is None else round(float(r0.whole_peak), 2),
                                 whole_duration=None if r0 is None else int(r0.whole_duration),
                                 seasonal=None if r0 is None or 'seasonal' not in r0 else r0.seasonal,
                                 quality_flag=None if r0 is None or 'quality_flag' not in r0 else r0.quality_flag,
                                 max_ratio_in_window=round(float(ww.ratio.max()), 2) if ww.ratio.notna().any() else None,
                                 usable_weeks_in_window=int(ww.usable.sum()), weeks_in_window=len(ww)))
    weeks = pd.date_range(a, b, freq='7D')
    md.append(f"\n**{c['name']}** (node {c['node']}, {label[c['node']]}; expected {c['expected']}). Ratio = share / median of the previous 26 weeks.\n")
    hdr = ['Week'] + [f"{'W' if s == 'wikipedia' else 'G'} {('node' if k == 'node' else k.replace('value: ', ''))}" for k, s in series] + ['Events (W node / G node)', 'G tone']
    md.append('| ' + ' | '.join(hdr) + ' |'); md.append('|' + ' --- |' * len(hdr))
    for wk in weeks:
        cells = [str(wk.date())]
        for k, s in series:
            w, sh = tab[(k, s)]
            r = w.loc[wk] if wk in w.index else None
            cells.append('' if r is None else (fmt(r.ratio) + ('*' if r.rising else '')) if r.usable else ('' if r is None else 'n/a'))
        ev = [event(tab[('node', s)][1], wk) for s in ('wikipedia', 'gdelt')]
        cells.append(' | '.join(e or '-' for e in ev).replace(' | ', ' / '))
        h = GT[GT.node_id == c['node']].set_index('week').tone
        prev = h[(h.index < wk) & (h.index >= wk - pd.Timedelta(weeks=26))]
        tone = (h.get(wk, np.nan) - prev.median()) if len(prev) >= 20 else np.nan
        cells.append(fmt(tone))
        md.append('| ' + ' | '.join(cells) + ' |')
        rows_weekly.append(dict(control=c['name'], week=wk.date(), **{f'{s}_{k}': ('' if tab[(k, s)][0].empty or wk not in tab[(k, s)][0].index else tab[(k, s)][0].loc[wk].ratio) for k, s in series}))
    md.append('\n`*` = rising week (ratio >= 1.5 and 8-week Mann-Kendall tau > 0, one-sided p < 0.10). G tone = GDELT tone of the node minus its median of the previous 26 weeks (negative = more negative coverage).\n')
pd.DataFrame(rows_weekly).to_csv(f'{OUT}/controls_weekly.csv', index=False)
CS = pd.DataFrame(rows_summary); CS.to_csv(f'{OUT}/controls_summary.csv', index=False)
md_summary = ['| Control | Series | Source | Shift starts in expected window | Start | Label (week) | Size | Whole-course peak | Weeks >= 1.5 | Max ratio in window | quality_flag |',
              '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
def _s(x):
    return '' if x is None or (isinstance(x, float) and not np.isfinite(x)) or (not isinstance(x, (str, bool)) and pd.isna(x)) else str(x)


for r in CS.itertuples():
    lab = _s(r.label) + (f' ({_s(r.label_week)})' if _s(r.label_week) else '')
    dur = '' if pd.isna(r.whole_duration) else str(int(r.whole_duration))
    srcname = {'wikipedia': 'Wikipedia', 'gdelt': 'GDELT'}[r.source]
    md_summary.append(f"| {r.control} | {r.series} | {srcname} | {'yes' if r.shift_in_window else 'no'} | {_s(r.start_week)} | {lab} | "
                      f"{_s(r.size)} | {_s(r.whole_peak)} | {dur} | {_s(r.max_ratio_in_window)} | {'' if r.series.startswith('value') or not r.shift_in_window else (_s(r.quality_flag) or 'none')} |")

# ---- largest shifts per source and year (main set: tested levels, non-seasonal, completed) ----
X = SHF[SHF.main_set].copy()
X['year'] = X.start_week.dt.year
top = X.sort_values('size', ascending=False).groupby(['source', 'year']).head(10).sort_values(['source', 'year', 'size'], ascending=[True, True, False])
top['driver'] = np.where(top.source == 'wikipedia', top.wiki_driver, top.gdelt_driver)
top.to_csv(f'{OUT}/top_shifts_by_year.csv', index=False)
md_top = []
for (src, yr), g in top.groupby(['source', 'year']):
    md_top.append(f"\n**{ {'wikipedia': 'Wikipedia', 'gdelt': 'GDELT'}[src] }, {yr}** (non-seasonal shifts at narrow and middle levels, by size)\n")
    if src == 'wikipedia':
        md_top.append('| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |')
    else:
        md_top.append('| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver code | Feed artefact (URL sample) |')
    md_top.append('| --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    for r in g.itertuples():
        row = f"| {r.node_label} ({r.node_id}) | {'narrow' if r.level == 3 else 'middle'} | {r.start_week.date()} | {r.label} | {r.size:.1f} | {r.whole_peak:.1f} | {r.whole_duration} |"
        if src == 'wikipedia':
            row += f" {r.driver if isinstance(r.driver, str) else ''} | {r.quality_flag.replace(',', ', ')} |"
        else:
            fa = '' if r.gdelt_feed_artifact is None or (isinstance(r.gdelt_feed_artifact, float) and np.isnan(r.gdelt_feed_artifact)) else ('yes' if r.gdelt_feed_artifact else 'no')
            row += f" `{r.driver}` | {fa} |"
        md_top.append(row)

# ---- shifts found in both sources (2017-07 to 2021-06, nodes usable in both; main set, and main set with quality_ok) ----
ok = COV[COV.usable_series].groupby(['level', 'node_id']).source.nunique()
both_nodes = set(ok[ok == 2].index.get_level_values(1))
P0 = X[X.node_id.isin(both_nodes) & X.start_week.between('2017-07-03', '2021-06-21')]
res = []
for setname, P in [('main set', P0), ('main set, quality_ok', P0[P0.quality_ok])]:
    for tol in (2, 4):
        for a_, b_, large in [('wikipedia', 'gdelt', False), ('gdelt', 'wikipedia', False), ('wikipedia', 'gdelt', True), ('gdelt', 'wikipedia', True)]:
            A_ = P[(P.source == a_) & (P.large | (not large))]; B_ = P[P.source == b_]
            m = [((B_.node_id == r.node_id) & ((B_.start_week - r.start_week).abs() <= pd.Timedelta(weeks=tol))).any() for r in A_.itertuples()]
            res.append(dict(shift_set=setname, tolerance_weeks=tol, shifts_in=a_ + (' (large only)' if large else ''), also_in=b_, n=len(A_),
                            matched=int(sum(m)), share=round(float(np.mean(m)) if m else np.nan, 3)))
SB = pd.DataFrame(res); SB['nodes_usable_in_both'] = len(both_nodes); SB.to_csv(f'{OUT}/shared_shifts.csv', index=False)
md_both = ['| Shift set | Shifts in | Also in | Tolerance (weeks) | Shifts | Matched | Share |', '| --- | --- | --- | --- | --- | --- | --- |']
for r in SB.itertuples():
    nm = lambda x: x.replace('wikipedia', 'Wikipedia').replace('gdelt', 'GDELT')
    md_both.append(f'| {r.shift_set} | {nm(r.shifts_in)} | {nm(r.also_in)} | +/-{r.tolerance_weeks} | {r.n} | {r.matched} | {r.share:.2f} |')

with open(f'{OUT}/checkpoint_tables.md', 'w') as f:
    f.write('## Control summary\n\n' + '\n'.join(md_summary) + '\n\n## Control weeks\n' + '\n'.join(md) +
            f'\n\n## Shifts found in both sources ({len(both_nodes)} nodes usable in both, starts 2017-07 to 2021-06)\n\n' + '\n'.join(md_both) +
            '\n\n## Largest shifts by source and year\n' + '\n'.join(md_top) + '\n')
print(CS[['control', 'series', 'source', 'shift_in_window', 'start_week', 'label', 'size', 'whole_peak', 'max_ratio_in_window']].to_string())
print(SB.to_string())
