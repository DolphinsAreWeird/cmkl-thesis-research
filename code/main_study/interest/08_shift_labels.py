# 08. Shift labels per node and source with the fixed definitions (prereg/study3_settings_2026-10-13.json, via _ci.settings),
# seasonal flags and coverage (no demand data are read). The GDELT duration scaling is computed in 11 on the final shifts.
# Partial weeks are treated as missing. Levels: narrow and middle are the tested levels; broad is descriptive only.
# Outputs (data/db/interest/): shift_weekly.parquet, shifts.parquet, coverage.csv
import json, numpy as np, pandas as pd
from _ci import OUT, GD, WK, settings, save_parquet, save_json
import _shifts as SH

S = settings()
print('settings', S['fixed_on'], S['sha256'][:12], flush=True)
G = pd.read_parquet(f'{GD}/weekly_node.parquet').rename(columns={'mentions': 'volume'})
Wk = pd.read_parquet(f'{WK}/weekly_node.parquet').rename(columns={'views': 'volume'})
MIN = {'wikipedia': S['min_wiki_views'], 'gdelt': S['min_gdelt_mentions']}
OVERLAP = (pd.Timestamp('2017-01-02'), pd.Timestamp('2021-06-21'))      # full GDELT weeks


def run(df, source, th=None):
    weekly, shifts = [], []
    for (lvl, nid), g in df.groupby(['level', 'node_id']):
        s = g.rename(columns={'share': 'x', 'volume': 'v'}).assign(valid=lambda d: ~d.partial_week)[['week', 'x', 'v', 'valid']]
        w, sh = SH.label_series(s, S, MIN[source], th)
        w['source'] = source; w['level'] = lvl; w['node_id'] = nid; w['label'] = g.label.iloc[0]
        weekly.append(w)
        for d in sh:
            d.update(source=source, level=lvl, node_id=nid, node_label=g.label.iloc[0]); shifts.append(d)
    return pd.concat(weekly, ignore_index=True), pd.DataFrame(shifts)


ww, sw = run(Wk, 'wikipedia')
wg, sg = run(G, 'gdelt')
weekly = pd.concat([ww, wg], ignore_index=True)
shifts = pd.concat([sw, sg], ignore_index=True)
sf = SH.seasonal_flags(shifts, weekly, S)
shifts = shifts.merge(sf, on=['source', 'level', 'node_id', 'start_week'], how='left')
shifts['large'] = shifts['size'] >= S['large_ratio']
shifts['tested_level'] = shifts.level.isin([3, 2])
shifts['main_set'] = shifts.tested_level & ~shifts.seasonal & ~shifts.label.isin(['censored', 'interrupted'])
shifts['in_overlap'] = shifts.start_week.between(*OVERLAP)

# GDELT duration scaling is computed in 11_quality_flags.py on the final shifts (after the quality flags).

# ---- coverage: usable weeks per node and source ----
period = {'wikipedia': (pd.Timestamp('2016-01-04'), pd.Timestamp('2026-09-21')), 'gdelt': (pd.Timestamp('2017-07-03'), pd.Timestamp('2021-06-21'))}
cov = []
for (src, lvl, nid), g in weekly.groupby(['source', 'level', 'node_id']):
    a, b = period[src]
    gg = g[g.week.between(a, b)]
    cov.append(dict(source=src, level=lvl, node_id=nid, label=g.label.iloc[0], weeks=len(gg), usable_weeks=int(gg.usable.sum()),
                    usable_share=float(gg.usable.mean()), median_volume=float(gg.v.median()),
                    n_shifts=int(((shifts.source == src) & (shifts.node_id == nid)).sum())))
cov = pd.DataFrame(cov)
cov['usable_series'] = cov.usable_share >= 0.8
cov.to_csv(f'{OUT}/coverage.csv', index=False)

save_parquet(weekly.drop(columns=['valid']).rename(columns={'x': 'share', 'v': 'volume'}), f'{OUT}/shift_weekly.parquet')
save_parquet(shifts, f'{OUT}/shifts.parquet')
print('shifts by source and label', shifts.groupby(['source', 'label']).size().to_dict())
print('main set by source', shifts[shifts.main_set].groupby('source').size().to_dict(), '| seasonal', shifts.groupby('source').seasonal.sum().to_dict())
print('usable series (>= 80% usable weeks) by source and level', cov[cov.usable_series].groupby(['source', 'level']).size().to_dict())
print('starts preceded by elevated weeks', shifts.groupby('source').elevated_weeks_before.apply(lambda s: (s > 0).mean()).round(3).to_dict(),
      '| strict starts', shifts.groupby('source').strict_start.mean().round(3).to_dict())
