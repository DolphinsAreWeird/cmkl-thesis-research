# Conversation sources, talk pages, step 3: rises (shifts) in the weekly talk-edit series with the Study 3 rule UNCHANGED
# (code/main_study/interest/_shifts.py, numbers from prereg/study3_settings_2026-10-13.json through _ci.settings()). The only
# source-specific setting is the minimum normal level of 20 human talk edits a week (prereg/conversation_sources_settings_2026-10-14.json;
# the rule needs the median raw weekly volume of the previous 26 weeks to reach it). Partial weeks count as missing.
# Same columns and flags as data/db/interest/shifts.parquet (seasonal, large, tested_level, main_set), source = 'talk_edits'.
# Rises are looked for from the first week with a full 26-week normal level (January 2016); 2015 is burn-in.
# Outputs (data/db/interest/talk_edits/): shifts.parquet, shift_weekly.parquet, coverage.csv
import sys, re, json, pathlib, numpy as np, pandas as pd
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'main_study' / 'interest'))
from _ci import settings, save_parquet, D, PREREG  # noqa: E402
import _shifts as SH  # noqa: E402

S = settings()
REC = json.loads((PREREG / 'conversation_sources_settings_2026-10-14.json').read_text())
MIN_EDITS = float(re.search(r'(\d+) talk edits a week', REC['shift_rule']).group(1))
assert MIN_EDITS == 20 and 'Study 3 rule unchanged' in REC['shift_rule']
OUT = f'{D}/db/interest/talk_edits'
W = pd.read_parquet(f'{OUT}/weekly_node.parquet')
print('settings', S['fixed_on'], S['sha256'][:12], 'min edits', MIN_EDITS, flush=True)

weekly, shifts = [], []
for (lvl, nid), g in W.groupby(['level', 'node_id']):
    s = g.rename(columns={'share': 'x', 'edits': 'v'}).assign(valid=lambda d: ~d.partial_week & np.isfinite(d.x))[['week', 'x', 'v', 'valid']]
    w, sh = SH.label_series(s, S, MIN_EDITS)
    w['source'] = 'talk_edits'; w['level'] = lvl; w['node_id'] = nid; w['label'] = g.label.iloc[0]
    weekly.append(w)
    for d in sh:
        d.update(source='talk_edits', level=lvl, node_id=nid, node_label=g.label.iloc[0]); shifts.append(d)
weekly = pd.concat(weekly, ignore_index=True)
shifts = pd.DataFrame(shifts)
sf = SH.seasonal_flags(shifts, weekly, S)
shifts = shifts.merge(sf, on=['source', 'level', 'node_id', 'start_week'], how='left')
shifts['large'] = shifts['size'] >= S['large_ratio']
shifts['tested_level'] = shifts.level.isin([3, 2])
shifts['main_set'] = shifts.tested_level & ~shifts.seasonal & ~shifts.label.isin(['censored', 'interrupted'])
shifts['min_edits'] = MIN_EDITS

a, b = pd.Timestamp('2016-01-04'), pd.Timestamp('2026-09-21')
cov = []
for (lvl, nid), g in weekly.groupby(['level', 'node_id']):
    gg = g[g.week.between(a, b)]
    cov.append(dict(source='talk_edits', level=lvl, node_id=nid, label=g.label.iloc[0], weeks=len(gg), usable_weeks=int(gg.usable.sum()),
                    usable_share=float(gg.usable.mean()), median_volume=float(gg.v.median()), n_shifts=int((shifts.node_id == nid).sum())))
cov = pd.DataFrame(cov)
cov['usable_series'] = cov.usable_share >= 0.8
cov.to_csv(f'{OUT}/coverage.csv', index=False)
save_parquet(weekly.drop(columns=['valid']).rename(columns={'x': 'share', 'v': 'edits'}), f'{OUT}/shift_weekly.parquet')
save_parquet(shifts, f'{OUT}/shifts.parquet')
print('shifts by level and label', shifts.groupby(['level', 'label']).size().to_dict())
print('main set by level', shifts[shifts.main_set].groupby('level').size().to_dict(), '| seasonal', int(shifts.seasonal.sum()))
print('series with any usable week by level', cov[cov.usable_weeks > 0].groupby('level').size().to_dict(),
      '| usable (>= 80%)', cov[cov.usable_series].groupby('level').size().to_dict())
