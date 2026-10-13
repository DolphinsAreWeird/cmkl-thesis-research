# 09. Descriptive sanity view only (no modelling): monthly SPL checkouts by format for works in four narrow themes,
# around the month where a change would be expected. For each theme two work sets are shown:
#   all     every work assigned to the theme now (includes books published after the event)
#   before  only works that already had a checkout in that format at least 12 months before the event month
# Values are checkouts and checkouts per 10,000 checkouts of that format in that month (to remove overall growth).
# Output: data/db/taxonomy_v2/sanity_monthly.parquet (full monthly series), quality/sanity_window.csv (event windows)
import numpy as np, pandas as pd
from _common import OUT

WT = pd.read_parquet(f'{OUT}/work_theme.parquet'); EV = pd.read_parquet(f'{OUT}/work_theme_value.parquet')
N = pd.read_parquet(f'{OUT}/theme_nodes.parquet')


def node_of(value):
    return N[(N.level == 3) & N['values'].map(lambda v: value in list(v))].node_id.iloc[0]


THEMES = [  # name, narrow node (via a member value), the single value used for the narrower version, event month
    ('epidemics and plagues', node_of('plague'), 'plague', 202003),
    ('race and racism', node_of('racism'), 'racism', 202006),
    ('sexual violence', node_of('sexual violence'), 'sexual violence', 201710),
    ('climate change', node_of('climate change'), 'climate change', 201909),
]
rw = pd.read_parquet(f'{OUT}/spl_record_work.parquet')
rows = pd.concat([pd.read_parquet(f'{OUT}/spl_rows_{f}.parquet', columns=['record_id', 'year', 'month', 'checkouts', 'format']) for f in ['audiobook', 'ebook']])
rows['format'] = rows['format'].astype(str)
rows = rows.merge(rw, on='record_id')
rows['ym'] = rows.year.astype(int) * 100 + rows.month.astype(int)
tot = rows.groupby(['format', 'ym']).checkouts.sum().rename('format_total')
first = rows.groupby(['work_id', 'format']).ym.min().rename('first_ym').reset_index()
out = []
for name, nid, val, ev in THEMES:
    sets = {'node': set(WT[(WT.node_id == nid)].work_id), 'value': set(EV[EV.theme == val].work_id)}
    for setname, works in sets.items():
        r = rows[rows.work_id.isin(works)]
        for subset in ['all', 'before']:
            if subset == 'before':
                y, m = divmod(ev, 100); cutoff = (y - 1) * 100 + m
                ok = first[(first.work_id.isin(works)) & (first.first_ym <= cutoff)][['work_id', 'format']]
                rr = r.merge(ok, on=['work_id', 'format'])
            else:
                rr = r
            g = rr.groupby(['format', 'ym']).agg(checkouts=('checkouts', 'sum'), works=('work_id', 'nunique')).reset_index()
            g = g.merge(tot.reset_index(), on=['format', 'ym'], how='right').fillna({'checkouts': 0, 'works': 0})
            g['per_10k'] = g.checkouts / g.format_total * 1e4
            g['theme'] = name; g['node_id'] = nid; g['work_set'] = 'narrow node' if setname == 'node' else f'value "{val}" only'
            g['subset'] = subset; g['event_ym'] = ev; g['n_works_in_set'] = len(works)
            out.append(g)
M = pd.concat(out, ignore_index=True)
M.to_parquet(f'{OUT}/sanity_monthly.parquet', index=False)

# event windows: 6 months before to 6 months after, and the same months one year earlier
win = []
for (name, wset, subset, fmt), g in M.groupby(['theme', 'work_set', 'subset', 'format']):
    ev = g.event_ym.iloc[0]
    p = pd.Period(f'{ev // 100}-{ev % 100:02d}', 'M')
    g = g.set_index('ym')
    def val(per, col):
        k = per.year * 100 + per.month
        return float(g.loc[k, col]) if k in g.index else np.nan
    pre = [p - k for k in range(1, 7)]; post = [p + k for k in range(0, 6)]
    rec = dict(theme=name, work_set=wset, subset=subset, format=fmt, event=str(p), n_works_in_set=int(g.n_works_in_set.iloc[0]),
               pre6_checkouts=np.nansum([val(x, 'checkouts') for x in pre]) / 6, post6_checkouts=np.nansum([val(x, 'checkouts') for x in post]) / 6,
               pre6_per_10k=np.nanmean([val(x, 'per_10k') for x in pre]), post6_per_10k=np.nanmean([val(x, 'per_10k') for x in post]),
               year_before_post6_per_10k=np.nanmean([val(x - 12, 'per_10k') for x in post]),
               event_month_per_10k=val(p, 'per_10k'), prev_month_per_10k=val(p - 1, 'per_10k'))
    rec['post_vs_pre'] = rec['post6_per_10k'] / rec['pre6_per_10k'] if rec['pre6_per_10k'] else np.nan
    rec['post_vs_year_before'] = rec['post6_per_10k'] / rec['year_before_post6_per_10k'] if rec['year_before_post6_per_10k'] else np.nan
    win.append(rec)
WIN = pd.DataFrame(win).round(3)
WIN.to_csv(f'{OUT}/quality/sanity_window.csv', index=False)
pd.set_option('display.width', 250)
print(WIN[['theme', 'work_set', 'subset', 'format', 'n_works_in_set', 'pre6_checkouts', 'post6_checkouts', 'pre6_per_10k', 'post6_per_10k', 'post_vs_pre', 'post_vs_year_before']].to_string(index=False))
