# Conversation sources, talk pages, step 5: report data/reports/talk_edits_interest.md from the talk-edit series, rises, noise
# benchmark and the Wikipedia page-view rises (data/db/interest/shifts.parquet). Interest data only; no borrowing data are read.
import sys, json, pathlib, numpy as np, pandas as pd
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'main_study' / 'interest'))
from _ci import settings, load_taxonomy, D  # noqa: E402
import _shifts as SH  # noqa: E402

S = settings()
OUT = f'{D}/db/interest/talk_edits'
A = pd.read_parquet(f'{D}/db/interest/wiki/articles.parquet')
AS = pd.read_csv(f'{OUT}/article_summary.csv')
Wn = pd.read_parquet(f'{OUT}/weekly_node.parquet')
Wv = pd.read_parquet(f'{OUT}/weekly_value.parquet')
SH_ = pd.read_parquet(f'{OUT}/shifts.parquet')
COV = pd.read_csv(f'{OUT}/coverage.csv')
NZ = pd.read_csv('data/reports/talk_edits_noise_benchmark.csv')
RD = pd.read_csv('data/reports/talk_edits_ratio_distribution.csv')
WS = pd.read_parquet(f'{D}/db/interest/shifts.parquet')
WS = WS[WS.source == 'wikipedia']
WW = pd.read_parquet(f'{D}/db/interest/shift_weekly.parquet')
WW = WW[WW.source == 'wikipedia']
V, N = load_taxonomy()
label = dict(zip(N.node_id, N.label))
LEV = {3: 'narrow', 2: 'middle', 1: 'broad'}
CLS = ['sustained', 'intermediate', 'fading']
md = []


def table(df, floatfmt=None):
    df = df.copy()
    cols = list(df.columns)
    out = ['| ' + ' | '.join(map(str, cols)) + ' |', '| ' + ' | '.join('---' for _ in cols) + ' |']
    for r in df.itertuples(index=False):
        out.append('| ' + ' | '.join((f'{v:.3g}' if isinstance(v, (float, np.floating)) and np.isfinite(v) else ('' if isinstance(v, float) else str(v))) for v in r) + ' |')
    return '\n'.join(out)


# ---- coverage ----
nart = A.canonical.nunique()
h16 = AS.human_edits_2016_on
cov_txt = []
tot_h, tot_b = AS.human_edits.sum(), AS.bot_edits.sum()
md.append('# Wikipedia talk-page edits as an interest source: weekly series and rises\n')
md.append('Interest side only. No borrowing data were read for this report. Fixed settings: `prereg/conversation_sources_settings_2026-10-14.json`. '
          'Code: `code/conversation/01` to `05`. Choices the record does not make are in `prereg/DEVIATIONS.md` (Conversation sources).\n')
md.append('## 1. What was collected\n')
md.append(f'- Source: Wikimedia REST API, `metrics/edits/per-page/en.wikipedia/Talk:<title>/<editor type>/daily`, no key, User-Agent with kwai@cmkl.ac.th, at most 4 requests a second, cached under `data/interim/talk_edits_cache/`. Counts only; the API returns no editor names and none are stored.')
md.append('- Editor types: the API has no single "everything except bots" value, so registered users and anonymous editors were fetched apart and added (human edits); the two bot types (group bots, named bots) were fetched too, only to report their share.')
md.append(f'- Articles: all {nart} English Wikipedia concept articles of `articles.parquet` (canonical titles; {A.theme.nunique()} theme values), one talk page each.')
md.append(f'- Period fetched: 1 Jan 2015 to 30 Sep 2026 (2015 is the start-up period for the 52-week normaliser). Rises are looked for from the first week with a full 26-week normal level, January 2016, to the last full week, 21 Sep 2026.')
md.append(f'- Talk pages with at least one human edit since 2016: {int((h16 > 0).sum())} of {nart} ({(h16 > 0).mean():.1%}); with at least 50 edits since 2016: {int((h16 >= 50).sum())}.')
md.append(f'- Human talk edits in total: {tot_h:,.0f}; bot edits: {tot_b:,.0f} ({tot_b / (tot_h + tot_b):.1%} of all edits to these pages), dropped.\n')
cl = COV.copy()
rows = []
for lvl in (3, 2, 1):
    c = cl[cl.level == lvl]
    rows.append(dict(level=LEV[lvl], nodes_with_articles=len(c), nodes_with_a_usable_week=int((c.usable_weeks > 0).sum()),
                     nodes_usable_80pct_of_weeks=int(c.usable_series.sum()), median_usable_share=c.usable_share.median(),
                     median_weekly_human_edits=c.median_volume.median(), nodes_with_a_rise=int((c.n_shifts > 0).sum())))
md.append('Series by level. A week is usable when the 26-week normal level exists and its median raw volume reaches 20 human talk edits a week.\n')
md.append(table(pd.DataFrame(rows)) + '\n')
# compare with Wikipedia page-view coverage
wc = pd.read_csv(f'{D}/db/interest/coverage.csv')
wc = wc[wc.source == 'wikipedia']
md.append('For comparison, Wikipedia page views: ' + ', '.join(f'{LEV[l]} {int(wc[(wc.level == l)].usable_series.sum())} usable of {int((wc.level == l).sum())}' for l in (3, 2, 1)) + ' nodes.\n')

md.append('## 2. Normalisation\n')
md.append('The Wikimedia `edits/aggregate` endpoint returns totals by editor type and by page type, but the page types are only all, content and non-content. '
          'There is no talk-namespace total (non-content mixes in user, project, file and other pages), so the record\'s first choice, '
          'division by all English Wikipedia talk-page edits that week, is not available. **Used: the record\'s fallback, the theme\'s own trailing 52-week mean** '
          '(mean of the same series over the previous 52 full weeks, at least 26 of them, current week left out). Share = human talk edits this week / that mean. '
          'The rule then runs on this share as it runs on page-view shares.\n')
md.append('Consequence to keep in mind: the denominator is the series\' own history, so a series that has been rising for months is damped, and the share has no meaning across themes (every series is near 1 in quiet weeks). It is a ratio to the own recent past, which is what the rise rule needs.\n')

md.append('## 3. Noise benchmark (interest data only)\n')
md.append('Same method as `code/parameter_audit/calibrate_interest.py`: each series is rebuilt from its own quiet-week deviations in 8-week blocks, so it keeps ordinary variation but holds no real event; the unchanged rule is run on real and rebuilt series. '
          'Noise share = rises per 100 series-years in rebuilt series / rises per 100 series-years in real series.\n')
b = NZ[(NZ.setting == 'ratio') & (NZ.value == 1.5)]
md.append(table(b[['level', 'real_series', 'real_series_years', 'real_shifts', 'real_per100y', 'noise_shifts', 'noise_per100y', 'noise_share_all', 'real_sustained', 'noise_sustained', 'noise_share_sustained']]) + '\n')
wn = pd.read_csv('data/reports/parameter_register_rule_noise_benchmark.csv')
wn = wn[(wn.setting == 'ratio') & (wn.value == 1.5) & (wn.source == 'wikipedia')]
md.append('Wikipedia page views, same benchmark (parameter audit): ' + '; '.join(f'{r.level} all {r.noise_share_all:.2f}, sustained {r.noise_share_sustained:.2f}' for r in wn.itertuples()) + '.\n')
md.append('Grid (ratio, Mann-Kendall alpha, quiet weeks) for talk edits:\n')
md.append(table(NZ[['setting', 'value', 'level', 'real_shifts', 'noise_shifts', 'noise_share_all', 'real_sustained', 'noise_sustained', 'noise_share_sustained']]) + '\n')
md.append('Share of usable weeks at or above each ratio to normal:\n')
md.append(table(RD) + '\n')

# ---- rise counts ----
md.append('## 4. Rises (Study 3 rule unchanged, minimum 20 talk edits a week)\n')
md.append('Counts of shift starts by duration class. `main set` = narrow and middle nodes, not seasonal, not censored or interrupted (the set Study 3b tests). Classes: sustained 4 weeks or more, intermediate 3, fading 2 or fewer.\n')
rows = []
for lvl in (3, 2, 1):
    s = SH_[SH_.level == lvl]
    d = dict(level=LEV[lvl], all_starts=len(s))
    for c in CLS + ['censored', 'interrupted']:
        d[c] = int((s.label == c).sum())
    d['seasonal'] = int(s.seasonal.sum())
    for c in CLS:
        d[f'main_set_{c}'] = int(((s.label == c) & s.main_set).sum())
    d['large (size>=3)'] = int(s.large.sum())
    rows.append(d)
md.append(table(pd.DataFrame(rows)) + '\n')
ms = SH_[SH_.main_set]
yr = ms.assign(year=ms.start_week.dt.year).groupby('year').size()
md.append('Main-set rises by start year: ' + ', '.join(f'{y} {n}' for y, n in yr.items()) + '.\n')
md.append(f'Main-set rises with a start in 2016-01 to 2026-03 (the window for month 0 in the record): {int(ms.start_week.between("2016-01-01", "2026-03-31").sum())}.\n')

# sensitivity (NOT in the record): the same rule with a lower minimum, counts only, to show how much the 20-edit minimum removes
md.append('Sensitivity, not part of the record and not used downstream: the same rule with a lower minimum normal level (counts of all starts by class, narrow and middle nodes, not seasonal).\n')
rows = []
for mv in (20, 10, 5):
    rr = []
    for (lvl, nid), g in Wn[Wn.level.isin([2, 3])].groupby(['level', 'node_id']):
        s_ = g.rename(columns={'share': 'x', 'edits': 'v'}).assign(valid=lambda d: ~d.partial_week & np.isfinite(d.x))[['week', 'x', 'v', 'valid']]
        w_, sh_ = SH.label_series(s_, S, float(mv))
        rr += [dict(level=lvl, label=d['label']) for d in sh_]
    rr = pd.DataFrame(rr, columns=['level', 'label'])
    for lvl in (3, 2):
        q = rr[rr.level == lvl]
        rows.append(dict(minimum=mv, level=LEV[lvl], **{c: int((q.label == c).sum()) for c in CLS}))
md.append(table(pd.DataFrame(rows)) + '\n')

# ---- controls ----
md.append('## 5. Positive controls\n')
md.append('Events: COVID-19 declared a pandemic 11 Mar 2020; George Floyd died 25 May 2020; #MeToo hashtag went viral 15 Oct 2017. A control rise is the first rise whose start week lies from 2 weeks before to 8 weeks after the event. '
          'Series: the control node and the control theme values (value series labelled with the same rule and the same minimum).\n')
EV = [('COVID-19 (Mar 2020)', '2020-03-11', 'B15.M04.N05', ['plague', 'epidemiology']),
      ('George Floyd (Jun 2020)', '2020-05-25', 'B05.M02.N02', ['racism']),
      ('#MeToo (Oct 2017)', '2017-10-15', 'B12.M01.N02', ['sexual violence'])]
rows = []
MINE = 20.0


def first_rise(sh, ev):
    lo, hi = pd.Timestamp(ev) - pd.Timedelta(weeks=2), pd.Timestamp(ev) + pd.Timedelta(weeks=8)
    g = sh[(sh.start_week >= lo) & (sh.start_week <= hi)].sort_values('start_week')
    return g.iloc[0] if len(g) else None


for name, ev, node, vals in EV:
    items = [('node ' + node + ' ' + label[node], SH_[SH_.node_id == node], COV[COV.node_id == node], 'talk')]
    for v in vals:
        g = Wv[Wv.value == v]
        s = g.rename(columns={'share': 'x', 'edits': 'v'}).assign(valid=lambda d: ~d.partial_week & np.isfinite(d.x))[['week', 'x', 'v', 'valid']]
        w, sh = SH.label_series(s, S, MINE)
        sh = pd.DataFrame(sh)
        win = w[(w.week >= pd.Timestamp(ev) - pd.Timedelta(weeks=26)) & (w.week <= pd.Timestamp(ev) + pd.Timedelta(weeks=8))]
        items.append(('value ' + v, sh if len(sh) else pd.DataFrame(columns=['start_week', 'label', 'size']), win, 'value'))
    for nm, sh, cv, kind in items:
        r = first_rise(sh, ev) if len(sh) else None
        if kind == 'talk':
            wk = Wn[(Wn.node_id == node)]
            wk = wk[(wk.week >= pd.Timestamp(ev) - pd.Timedelta(weeks=8)) & (wk.week <= pd.Timestamp(ev) + pd.Timedelta(weeks=8))]
            vol = f'{wk.edits.median():.0f}'
            peak = np.nanmax(SH_[SH_.node_id == node].size.where(SH_.start_week.between(pd.Timestamp(ev) - pd.Timedelta(weeks=2), pd.Timestamp(ev) + pd.Timedelta(weeks=8)), np.nan)) if r is not None else np.nan
            ww = WW[(WW.node_id == node)]
            wr = first_rise(WS[WS.node_id == node], ev)
        else:
            gg = Wv[Wv.value == nm.split(' ', 1)[1]]
            gg = gg[(gg.week >= pd.Timestamp(ev) - pd.Timedelta(weeks=8)) & (gg.week <= pd.Timestamp(ev) + pd.Timedelta(weeks=8))]
            vol = f'{gg.edits.median():.0f}'
            wr = None
        why = ''
        if r is None:
            if kind == 'talk':
                u = cv.usable_weeks.iloc[0] if len(cv) else 0
                why = 'series has no usable week' if u == 0 else 'no rise start in the window'
            else:
                why = 'no usable week (volume below 20 or no normal level)' if not cv.usable.any() else 'no rise start in the window'
        src = Wn[Wn.node_id == node] if kind == 'talk' else Wv[Wv.value == nm.split(' ', 1)[1]]
        ev_w = src[(src.week >= pd.Timestamp(ev) - pd.Timedelta(weeks=2)) & (src.week <= pd.Timestamp(ev) + pd.Timedelta(weeks=8))]
        peak_edits = float(ev_w.edits.max())
        s5 = src.rename(columns={'share': 'x', 'edits': 'v'}).assign(valid=lambda d: ~d.partial_week & np.isfinite(d.x))[['week', 'x', 'v', 'valid']]
        _, sh5 = SH.label_series(s5, S, 5.0)
        r5 = first_rise(pd.DataFrame(sh5), ev) if len(sh5) else None
        at5 = f'{r5.start_week.date()} {r5.label}' if r5 is not None else 'no rise (or normal volume below 5)'
        rows.append({'control': name, 'series': nm, 'median_weekly_edits_around_event': vol, 'peak_weekly_edits_event_window': peak_edits,
                     'first_rise_at_minimum_5 (not in record)': at5,
                     'first_rise_start': r.start_week.date() if r is not None else '', 'class': r.label if r is not None else why,
                     'size': float(r['size']) if r is not None and r['size'] is not None else np.nan,
                     'wikipedia_node_rise_start': (wr.start_week.date() if wr is not None else '') if kind == 'talk' else ''})
CT = pd.DataFrame(rows)
md.append(table(CT) + '\n')
md.append('With the record\'s minimum of 20 edits a week none of the three control series has a usable week, so none can be tested; the column "first_rise_at_minimum_5" is a descriptive look at the same rule with a lower minimum and is not part of the record.\n')

# ---- agreement with Wikipedia ----
md.append('## 6. Agreement with Wikipedia page-view rises\n')
md.append('For each talk-edit rise (sustained, intermediate or fading; censored and interrupted left out) in a node that also has a Wikipedia series: is there a Wikipedia rise start in the same node within 2 weeks (either direction, any class)? '
          '"Chance" is the share of usable talk weeks in the same node that lie within 2 weeks of some Wikipedia start, averaged over the talk rises: the agreement expected if the two sets of start dates were unrelated. '
          'Lead-lag is the median of (talk start minus the nearest Wikipedia start) in weeks over matched rises; positive means talk edits rose later. The reverse column is the share of Wikipedia rises, in weeks where the talk series is usable, that have a talk rise within 2 weeks.\n')
TW = SH_[SH_.label.isin(CLS)].copy()
WSa = WS.copy()
wk_all = SH_.__class__
wusable = pd.read_parquet(f'{OUT}/shift_weekly.parquet')[['node_id', 'week', 'usable']]
wusable = wusable[wusable.usable]
by_node_wiki = {n: g.start_week.sort_values().to_numpy() for n, g in WSa.groupby('node_id')}
uw = {n: g.week.to_numpy() for n, g in wusable.groupby('node_id')}
TWIN = np.timedelta64(14, 'D')


def near(starts, t):
    if starts is None or len(starts) == 0:
        return None
    d = (starts - t)
    k = np.argmin(np.abs(d))
    return d[k]


res = []
for r in TW.itertuples():
    st = by_node_wiki.get(r.node_id)
    nd = near(st, np.datetime64(r.start_week))
    chance = np.nan
    if st is not None and r.node_id in uw:
        wks = uw[r.node_id]
        ok = np.zeros(len(wks), bool)
        for s_ in st:
            ok |= np.abs(wks - s_) <= TWIN
        chance = ok.mean()
    res.append(dict(level=r.level, label=r.label, main_set=r.main_set, has_wiki_series=st is not None, match=(nd is not None and abs(nd) <= TWIN),
                    lag_weeks=(-nd / np.timedelta64(7, 'D')) if nd is not None and abs(nd) <= TWIN else np.nan, chance=chance))
R = pd.DataFrame(res)
R = R[R.has_wiki_series]
rows = []
for nm, f in [('all levels', R), ('narrow', R[R.level == 3]), ('middle', R[R.level == 2]), ('broad', R[R.level == 1]), ('main set', R[R.main_set]),
              ('sustained', R[R.label == 'sustained']), ('intermediate', R[R.label == 'intermediate']), ('fading', R[R.label == 'fading'])]:
    rows.append(dict(group=nm, talk_rises=len(f), with_wikipedia_rise_within_2_weeks=int(f.match.sum()), share=f.match.mean() if len(f) else np.nan,
                     chance=f.chance.mean() if len(f) else np.nan, median_lag_weeks=f.lag_weeks.median() if len(f) else np.nan))
md.append(table(pd.DataFrame(rows)) + '\n')
rev = []
for lvl in (3, 2, 1):
    n_all = n_hit = 0
    for r in WSa[WSa.level == lvl].itertuples():
        if r.node_id not in uw or not np.any(np.abs(uw[r.node_id] - np.datetime64(r.start_week)) <= np.timedelta64(0, 'D')):
            continue
        n_all += 1
        t = TW[TW.node_id == r.node_id].start_week.to_numpy()
        n_hit += bool(len(t) and np.any(np.abs(t - np.datetime64(r.start_week)) <= TWIN))
    rev.append(dict(level=LEV[lvl], wikipedia_rises_in_usable_talk_weeks=n_all, with_talk_rise_within_2_weeks=n_hit, share=n_hit / n_all if n_all else np.nan))
md.append(table(pd.DataFrame(rev)) + '\n')
tt = TW[TW.node_id.isin(by_node_wiki)]
md.append(f'Talk rises in nodes with a Wikipedia series: {len(tt)} of {len(TW)}.\n')
open('data/reports/talk_edits_interest.md', 'w').write('\n'.join(md))
R.to_csv(f'{OUT}/agreement_with_wikipedia.csv', index=False)
CT.to_csv(f'{OUT}/controls.csv', index=False)
print('written')
