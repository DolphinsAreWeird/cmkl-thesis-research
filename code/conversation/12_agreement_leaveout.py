# Conversation sources, step 12: (a) secondary measures: agreement of each source's rises with Wikipedia page-view rises within 2 weeks
# and lead-lag (method of 05_talk_report.py; interest data only); (b) a leave-out check of H1/H2 without the George Floyd rise
# (post-outcome, descriptive). Appends sections 6 and 7 to data/reports/conversation_sources_results.md. Needs step 11.
import sys, pathlib, importlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import conv_common as C
from conv_common import S, IO
T11 = importlib.import_module('11_tests')
ROOT = C.ROOT
CLS = ['sustained', 'intermediate', 'fading']
TWIN = np.timedelta64(14, 'D')


def near(starts, t):
    if starts is None or len(starts) == 0:
        return None
    d = starts - t
    return d[np.argmin(np.abs(d))]


def agreement(src):
    X = C.conv_shifts(src)
    Xl = X[X.duration_class.isin(CLS)].copy()
    Xl['tested'] = Xl.index.isin(C.tested_set(X, src).index)
    W = pd.read_parquet(ROOT / 'data/db/interest/shifts.parquet')
    W = W[W.source == 'wikipedia']
    wst = {n: g.start_week.sort_values().to_numpy() for n, g in W.groupby('node_id')}
    sw = pd.read_parquet(ROOT / f'data/db/interest/{"tweetskb" if src == "tweetskb" else "talk_edits"}/shift_weekly.parquet')[['node_id', 'week', 'usable']]
    uw = {n: g.week.to_numpy() for n, g in sw[sw.usable].groupby('node_id')}
    rows = []
    for r in Xl.itertuples():
        st = wst.get(r.node_id)
        if st is None:
            continue
        nd = near(st, np.datetime64(r.start_week))
        chance = np.nan
        if r.node_id in uw:
            ok = np.zeros(len(uw[r.node_id]), bool)
            for s_ in st:
                ok |= np.abs(uw[r.node_id] - s_) <= TWIN
            chance = ok.mean()
        hit = abs(nd) <= TWIN
        rows.append(dict(level=r.level, cls=r.duration_class, tested=r.tested, match=bool(hit), lag=(-nd / np.timedelta64(7, 'D')) if hit else np.nan, chance=chance))
    R = pd.DataFrame(rows)
    out = []
    for nm, f in [('all levels', R), ('narrow', R[R.level == 'narrow']), ('middle', R[R.level == 'middle']), ('broad', R[R.level == 'broad']), ('tested set', R[R.tested]),
                  ('tested set, sustained', R[R.tested & (R.cls == 'sustained')]), ('tested set, fading', R[R.tested & (R.cls == 'fading')])]:
        out.append(dict(source=src, group=nm, rises=len(f), matched_within_2_weeks=int(f.match.sum()), share=f.match.mean() if len(f) else np.nan,
                        chance=f.chance.mean() if len(f) else np.nan, median_lag_weeks=f.lag.median() if f.match.any() else np.nan))
    return pd.DataFrame(out)


def main():
    A = pd.concat([agreement(s) for s in C.SOURCES], ignore_index=True)
    A.to_csv(C.OUTDIR / 'agreement.csv', index=False)
    L = ['', '## 6. Secondary: agreement with Wikipedia page-view rises and lead-lag (interest data only)', '',
         'A conversation rise (sustained, intermediate or fading, in a node that has a Wikipedia series) agrees when a Wikipedia rise of any class starts in the same node within 14 days. '
         '"Chance" is the share of the source\'s usable weeks in that node that lie within 14 days of some Wikipedia start. Lead-lag = conversation start minus nearest Wikipedia start in weeks, median over agreeing rises; positive means the conversation source rose later. '
         '"Tested set" is the set used for H1 and H2 (narrow and middle, not seasonal, not near a break, month 0 in the period). The talk-edit rows for all levels equal the talk-edit interest report.', '']
    A2 = A.copy()
    for c in ('share', 'chance', 'median_lag_weeks'):
        A2[c] = A2[c].map(lambda x: T11.fmt(x, 3 if c != 'median_lag_weeks' else 1))
    L += IO.md_table(A2) + ['']
    # leave-out
    R = pd.read_parquet(C.OUTDIR / 'shift_effects.parquet')
    R['start_week'] = pd.to_datetime(R.start_week)
    floyd = (R.source == 'tweetskb') & (R.start_week == '2020-05-25') & R.node_id.isin(['B05.M02', 'B05.M02.N02'])
    L += ['## 7. Check after the results were seen: TweetsKB without the George Floyd rise (descriptive, not part of the record)', '',
          'The two largest TweetsKB sustained effects are the George Floyd rise of 25 May 2020 (narrow Race and racism and its middle parent). The same H1 and H2 computation is repeated without them.', '']
    rows = []
    for (s, lv), g in R[(R.source == 'tweetskb') & ~floyd].groupby(['source', 'level']):
        c = T11.contributing(g)
        sus, fad = c[c.duration_class == 'sustained'], c[c.duration_class == 'fading']
        h1 = T11.boot_diff(sus, fad, C.BOOT_N, C.BOOT_SEED)
        h2 = C.M.cluster_boot_mean(sus.tau_p.to_numpy(), sus.node_id.to_numpy(), C.BOOT_N, C.BOOT_SEED)
        rows.append(dict(source=s, level=lv, sustained=len(sus), fading=len(fad), H1_diff=T11.fmt(h1['diff']), H1_low=T11.fmt(h1['low']), H1_high=T11.fmt(h1['high']),
                         H2_mean=T11.fmt(h2['mean']), H2_low=T11.fmt(h2.get('low')), H2_high=T11.fmt(h2.get('high'))))
    L += IO.md_table(pd.DataFrame(rows)) + ['']
    txt = C.REPORT.read_text().split('<!-- AGREEMENT -->')[0]
    C.REPORT.write_text(txt + '<!-- AGREEMENT -->' + '\n'.join(L) + '\n')
    print(A.to_string()); print(pd.DataFrame(rows).to_string())


if __name__ == '__main__':
    main()
