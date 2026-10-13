# 10. Driver codes of GDELT shifts and the evidence for the figurative-use check (decision of 13 Oct 2026).
# For each GDELT shift at the tested levels in the main set, the driver is the code with the largest rise in mentions over
# the first weeks of the shift (start to week 4, or to the end if earlier) against its median week in the 26 weeks before.
# For every distinct driver code the evidence for a hand check is:
#   - its three highest-volume weeks (largest share of all mentions), with its ratio to its own 26-week median;
#   - in each of those weeks, the codes that rose most against their own normal (codes with >= 2,000 mentions a week on
#     average), which show what the news was about that week;
#   - the codes whose weekly share is most correlated with it over all weeks (its usual company).
# Hand verdicts go into _gdelt_review.FIGURATIVE; a code whose rises are driven by figurative use ("witch hunt") is dropped
# by 02. This script lists drivers that have no verdict yet (gdelt/figurative_todo.csv); after a rerun of 02 to 08 new
# drivers can appear, so the loop is repeated until the list is empty. Interest data only.
# Outputs: data/db/interest/gdelt/driver_codes.csv (one row per shift), gdelt/driver_evidence.csv, gdelt/figurative_todo.csv
import numpy as np, pandas as pd, pyarrow.parquet as pq
from _ci import D, OUT, GD
import _gdelt_review as RV

raw = pq.read_table(f'{D}/raw/gdelt_weekly_2017_2021H1.parquet', columns=['week', 'theme', 'mentions']).to_pandas(ignore_metadata=True)
raw['week'] = pd.to_datetime(raw.week)
tot = pd.read_parquet(f'{GD}/weekly_total.parquet').set_index('week')
full_weeks = tot.index[~tot.partial_week]
M = pd.read_parquet(f'{GD}/code_map.parquet')
C = pd.read_parquet(f'{GD}/codes.parquet').set_index('code')
SH = pd.read_parquet(f'{OUT}/shifts.parquet')
G = SH[(SH.source == 'gdelt') & SH.main_set].copy()
col = {3: 'narrow_id', 2: 'mid_id'}

rows = []
for r in G.itertuples():
    codes = list(M[M[col[r.level]] == r.node_id].code)
    g = raw[raw.theme.isin(codes)]
    a = r.start_week; n_w = int(min(max(r.whole_duration, 1), 4)); b = a + pd.Timedelta(weeks=n_w - 1)
    base = g[g.week.between(a - pd.Timedelta(weeks=26), a - pd.Timedelta(days=1))].pivot_table(
        index='week', columns='theme', values='mentions', aggfunc='sum').reindex(columns=codes).fillna(0).median()
    win = g[g.week.between(a, b)].groupby('theme').mentions.sum().reindex(codes).fillna(0)
    rise = (win - base * n_w).sort_values(ascending=False)
    pos = rise[rise > 0]
    rows.append(dict(level=r.level, node_id=r.node_id, node_label=r.node_label, start_week=a, size=r.size,
                     driver=rise.index[0], driver_share_of_rise=float(pos.iloc[0] / pos.sum()) if len(pos) else np.nan,
                     second=rise.index[1] if len(rise) > 1 else None))
DR = pd.DataFrame(rows)
DR.to_csv(f'{GD}/driver_codes.csv', index=False)

# evidence per distinct driver code
big = raw.groupby('theme').mentions.sum()
big = big[big >= 2000 * len(full_weeks)].index                      # codes with >= 2,000 mentions a week on average
P = raw[raw.theme.isin(big)].pivot_table(index='week', columns='theme', values='mentions', aggfunc='sum').reindex(full_weeks).fillna(0)
P = P.div(tot.loc[full_weeks, 'total_mentions'], axis=0)             # shares
norm = P.shift(1).rolling(26, min_periods=20).median()
ratio = P / norm
text = C.text.to_dict()
ev = []
for code in sorted(DR.driver.unique()):
    s = raw[raw.theme == code].set_index('week').mentions.reindex(full_weeks).fillna(0) / tot.loc[full_weeks, 'total_mentions']
    own_ratio = s / s.shift(1).rolling(26, min_periods=20).median()
    topw = s.sort_values(ascending=False).index[:3]
    weeks = []
    for w in topw:
        rr = ratio.loc[w].drop(code, errors='ignore').replace([np.inf], np.nan).dropna().sort_values(ascending=False).head(6)
        weeks.append(f"{w.date()} (x{own_ratio.get(w, np.nan):.1f}): " + '; '.join(f"{text.get(k, k)} x{v:.1f}" for k, v in rr.items()))
    if code in P.columns:
        cor = P.corrwith(P[code]).drop(code).sort_values(ascending=False).head(6)
    else:
        cor = P.corrwith(s).sort_values(ascending=False).head(6)
    ev.append(dict(code=code, text=text.get(code), value=M.set_index('code').value.get(code), shifts_driven=int((DR.driver == code).sum()),
                   top_weeks=' || '.join(weeks), most_correlated='; '.join(f"{text.get(k, k)} {v:.2f}" for k, v in cor.items()),
                   verdict=RV.FIGURATIVE.get(code, (None, None))[0], reason=RV.FIGURATIVE.get(code, (None, None))[1]))
EV = pd.DataFrame(ev)
EV.to_csv(f'{GD}/driver_evidence.csv', index=False)
todo = EV[EV.verdict.isna()]
todo.to_csv(f'{GD}/figurative_todo.csv', index=False)
print('GDELT main-set shifts', len(DR), '| distinct driver codes', EV.code.nunique(), '| without a figurative verdict', len(todo),
      '| judged figurative', int((EV.verdict == 'figurative').sum()))
