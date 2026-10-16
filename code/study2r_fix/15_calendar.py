"""Study 2R step 15 (diagnostic, not in the record): tau of ordinary works (no event) by calendar year of month 0, from the cached z tables:
pool works, feasible, not sparse, finite tau. Shows whether the forecasts of the count model are centred on zero in each year, and where the
tested shifts sit. Writes the section 'calendar' of data/reports/study2r_results.md and study2r_calendar_tau.csv."""
from _pipe2r import *
W = works_table(); C = load_counts(('print', 'ebook'))
tabs = build_ztables(C, 'pe', month_range(C), 1)
pool = pool_mask(C, W, 'book')
rows = []
for m, t in tabs.items():
    k = pool & t['feasible'] & (t['summu_p'] >= S.sparse_below) & np.isfinite(t['tau_p'])
    v = t['tau_p'][k].astype(float)
    rows.append(dict(m0=m, year=m // 12, n=len(v), mean=v.mean(), median=np.median(v), share_pos=float((v > 0).mean())))
R = pd.DataFrame(rows)
Y = R.groupby('year').apply(lambda g: pd.Series(dict(months=len(g), works_per_month=g.n.mean(), mean_tau=np.average(g['mean'], weights=g.n), median_tau=np.average(g['median'], weights=g.n),
                                                     share_tau_above_0=np.average(g.share_pos, weights=g.n)))).reset_index()
E = pd.read_parquet(OUT / 'effects_book.parquet'); E = E[(E.skip == '') & ~E.too_sparse & np.isfinite(E.tau_p)]
Y['tested_shifts'] = Y.year.map(E.assign(year=E.m0 // 12).groupby('year').size()).fillna(0).astype(int)
Y['treated_mean_tau'] = Y.year.map(E.assign(year=E.m0 // 12).groupby('year').tau_p.mean())
Y['placebo_median_same_months'] = Y.year.map(E.assign(year=E.m0 // 12).groupby('year').plc_tau_median.mean())
Y.to_csv(REP / 'study2r_fix_calendar_tau.csv', index=False)
L = ['## Calendar check of the forecasts (diagnostic, not in the record)', '',
     'tau of ordinary placebo-pool works (no event) by calendar year of month 0, over all months of that year (print and ebook joint model; works feasible and not sparse); and the tested shifts of the main set by year.', '']
L += md_table(Y.rename(columns={'works_per_month': 'works/month'}))
put_section('calendar', L)
print('\n'.join(L))
