# 18. (v3) Control categories: definitions, sizes and the fixed minimum-size rule. No demand series or sanity view is
# produced any more: after checkpoint 2 the control series are not viewed again (coordinator, 13 Oct 2026).
#   definitions  works in the category (main assignment; and extra works from the title-word backup), values in the node
#   sizes        works with checkouts by year and format (checkout totals are kept in the CSV but not reported)
#   min size     the fixed rule: >= 20 works with checkouts in the format, and a median of >= 200 strength-weighted
#                checkouts per month over the 24 months before the shift month (missing months skipped, never zero)
# Missing months come from the Study 3 code (code/main_study/study3: _settings.load() and _build.month_status), so the
# rule lives in one place: the digital gap months of the fixed settings, partly downloaded months (fewer rows than the
# SPL API count) and closure months (addendum e: library-wide total below 50% of the median of the previous 12 months).
# Output: quality/control_definitions.csv, quality/control_sizes_by_year.csv, quality/control_min_size.csv
import os, sys
os.environ['TAXO'] = 'v3'
import json, re, numpy as np, pandas as pd
from _common import OUT, OUT_V2
import _review_v3 as RV3
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'study3'))
import _settings as ST3          # noqa: E402  (Study 3 settings: fixed record + addenda)
import _build as B3              # noqa: E402  (Study 3 month status)

S3 = ST3.load()
Q = f'{OUT}/quality'; os.makedirs(Q, exist_ok=True)
N = pd.read_parquet(f'{OUT}/theme_nodes.parquet')
VN = pd.read_parquet(f'{OUT}/theme_value_node.parquet')
LOG = pd.read_csv(f'{OUT}/profile/placement_log.csv', low_memory=False)
def node_of(v):
    return VN.set_index('theme').node_id[v]
climate_rule = [r for r in RV3.PLACE_RULES if r[2] == 'climate change'][0][0]
climate_values = {'climate change'} | {t for t in LOG.theme if re.search(climate_rule, t)}
CONTROLS = [  # name, node, event month (shift month in prereg), value filter (None = whole node)
    ('Epidemics and plagues', node_of('plague'), 202003, None),
    ('Race and racism', node_of('racism'), 202006, None),
    ('Sexual violence and domestic violence', node_of('sexual violence'), 201710, None),
    ('Climate change and weather (node)', node_of('climate change'), 201909, None),
    ('Climate change (climate values only)', node_of('climate change'), 201909, climate_values),
]
WT = pd.read_parquet(f'{OUT}/work_theme.parquet', columns=['work_id', 'node_id', 'strength'])
EV = pd.read_parquet(f'{OUT}/work_theme_value.parquet')
TB = pd.read_parquet(f'{OUT}/work_theme_title_backup.parquet', columns=['work_id', 'node_id', 'strength'])
defs = []; sets = {}
for name, nid, ev, vals in CONTROLS:
    if vals is None:
        main = WT[WT.node_id == nid].groupby('work_id').strength.max()
    else:   # strength of the climate values only: their share within each source, averaged like the main strength
        e = EV[EV.node_id.notna()].copy(); e['share'] = e.weight / e.groupby(['work_id', 'source']).weight.transform('sum')
        nsrc = e.groupby('work_id').source.nunique()
        main = e[e.theme.isin(vals)].groupby('work_id').share.sum() / nsrc
        main = main.dropna()
    tb = TB[TB.node_id == nid].groupby('work_id').strength.max()
    tb = tb[~tb.index.isin(main.index)]
    sets[name] = (main, tb)
    defs.append(dict(category=name, node_id=nid, label=N.set_index('node_id').label[nid], event_month=ev, works_main=len(main),
                     works_title_backup_extra=len(tb), values_in_node=int((VN.node_id == nid).sum())))
D = pd.DataFrame(defs); D.to_csv(f'{Q}/control_definitions.csv', index=False)
print(D.to_string(index=False), flush=True)

rw = pd.read_parquet(f'{OUT}/spl_record_work.parquet')
allw = set().union(*[set(m.index) | set(t.index) for m, t in sets.values()])
recs = rw[rw.work_id.isin(allw)]
api = pd.read_parquet(f'{OUT_V2}/spl_api_counts.parquet')
STUDY3_FMT = {'audiobook': 'audiobook', 'ebook': 'ebook', 'book': 'print'}
mon = []; ok_months = {}; status = []
for fmt in ['audiobook', 'ebook', 'book']:
    x = pd.read_parquet(f'{OUT}/spl_rows_{fmt}.parquet')
    x['ym'] = x.year.astype(np.int32) * 100 + x.month.astype(np.int32)
    x['mi'] = B3.mi_of(x.year, x.month)
    totals = x.groupby('mi').agg(total_checkouts=('checkouts', 'sum'), n_rows=('checkouts', 'size'))
    a = api[api.materialtype == fmt.upper()].copy(); a['mi'] = B3.mi_of(a.year, a.month); a = a.set_index('mi')[['n_rows', 'checkouts']]
    f3 = STUDY3_FMT[fmt]
    st = B3.month_status(totals, S3.missing_months if f3 in S3.digital_formats else (), a,
                         closure=(S3.closure_frac, S3.closure_lookback, S3.closure_min))
    ok_months[fmt] = {int(m // 12) * 100 + int(m % 12) + 1 for m in st.index[st.month_ok]}
    status.append(st.reset_index().assign(format=fmt)[['format', 'mi', 'reason']])
    y = x[x.record_id.isin(recs.record_id)].merge(recs, on='record_id')
    mon.append(y.groupby(['work_id', 'ym']).checkouts.sum().reset_index().assign(format=fmt))
    del x, y
MON = pd.concat(mon, ignore_index=True)
ST = pd.concat(status); ST = ST[ST.reason != '']
ST['ym'] = ST.mi.map(lambda m: B3.ym_of(m))
print('months not usable (from the Study 3 rule):', ST.groupby(['format', 'reason']).ym.agg(['size', 'min', 'max']).to_string(), flush=True)

sizes = []; mins = []
for name, nid, ev, vals in CONTROLS:
    main, tb = sets[name]
    for variant, strength in [('main', main), ('main + title backup', pd.concat([main, tb]))]:
        m = MON[MON.work_id.isin(strength.index)].copy()
        m['w_checkouts'] = m.checkouts * m.work_id.map(strength)
        y = m.assign(year=m.ym // 100).groupby(['format', 'year']).agg(works=('work_id', 'nunique'), checkouts=('checkouts', 'sum'),
                                                                        weighted_checkouts=('w_checkouts', 'sum')).reset_index()
        y['category'] = name; y['variant'] = variant; y['works_in_category'] = len(strength)
        sizes.append(y)
        y0, m0 = divmod(ev, 100); p = pd.Period(f'{y0}-{m0:02d}', 'M')
        pre = [(p - k).year * 100 + (p - k).month for k in range(1, S3.size_lookback + 1)]
        for fmt in ['audiobook', 'ebook', 'book']:
            mf = m[m.format == fmt]
            g = mf.groupby('ym').w_checkouts.sum()
            avail = [x for x in pre if x in ok_months[fmt]]
            vals_ = [float(g.get(x, 0.0)) for x in avail]            # zero months count as zero, missing months are skipped
            med = float(np.median(vals_)) if vals_ else np.nan
            n_works_fmt = int(mf.work_id.nunique())
            need = B3.min_size_months(S3.size_lookback)
            mins.append(dict(category=name, variant=variant, format=fmt, shift_month=ev, works_with_checkouts_in_format=n_works_fmt,
                             months_available=len(avail), months_needed=need,
                             passes_min_size=bool(n_works_fmt >= S3.min_works and len(avail) >= need and med >= S3.min_median_weighted),
                             median_weighted_checkouts=round(med, 1) if vals_ else np.nan))
SZ = pd.concat(sizes, ignore_index=True); SZ.to_csv(f'{Q}/control_sizes_by_year.csv', index=False)
MS = pd.DataFrame(mins); MS.to_csv(f'{Q}/control_min_size.csv', index=False)
for old in ['controls_monthly.parquet', 'quality/control_windows.csv']:     # sanity-view outputs of the snapshot run
    if os.path.exists(f'{OUT}/{old}'):
        os.remove(f'{OUT}/{old}')
pd.set_option('display.width', 250)
print(MS[MS.variant == 'main'][['category', 'format', 'works_with_checkouts_in_format', 'months_available', 'passes_min_size']].to_string(index=False))
