# 04. Rises (shifts) in the TweetsKB conversation series, interest side only: no borrowing data are read or linked.
# The Study 3 rule is used unchanged (code/main_study/interest/_shifts.py, numbers parsed from prereg/study3_settings_2026-10-13.json);
# the only source-specific number is the minimum normal level of 100 tweets a week in the sample, parsed from the
# conversation-sources record. The parameter-audit noise benchmark (code/parameter_audit/calibrate_interest.py) is repeated
# for TweetsKB: each series is rebuilt from its own quiet-week deviations (circular blocks of 8 weeks) and the unchanged rule is run on it.
# Breaks: no shift may start within 2 weeks of an entity-linker re-run (April 2018, January 2021, September 2022): such starts are
# flagged `near_break` and left out of every count and of the main set.
# Outputs: data/db/interest/tweetskb/shifts.parquet, shift_weekly.parquet, coverage_year.csv, break_check.csv, noise_benchmark.csv,
#          controls.csv ; data/reports/tweetskb_interest.md
# Run: bash jobs/heavy_lock.sh nice -n 10 env OMP_NUM_THREADS=1 .venv/bin/python code/conversation/04_tweetskb_shifts.py
import json, os, re, time, pathlib, numpy as np, pandas as pd
from tk_common import *
import _shifts as SH
from _ci import settings

T0 = time.time()
S = settings()
REC = json.loads((HERE.parents[1] / 'prereg' / 'conversation_sources_settings_2026-10-14.json').read_text())
MINV = float(re.search(r'minimum normal level (\d+) tweets a week', REC['shift_rule']).group(1))
assert MINV == 100
SEED, REPS, BLOCK = 20261014, 20, 8
BREAKS = {'April 2018': pd.Timestamp('2018-04-01'), 'January 2021': pd.Timestamp('2021-01-01'), 'September 2022': pd.Timestamp('2022-09-01')}
brk_week = {k: v - pd.Timedelta(days=v.weekday()) for k, v in BREAKS.items()}
LEV = {1: 'broad', 2: 'middle', 3: 'narrow'}
V, N = load_taxonomy()
label = dict(zip(N.node_id, N.label))

W = pd.read_parquet(f'{TK}/weekly_node.parquet')
T = pd.read_parquet(f'{TK}/weekly_total.parquet')
G = pd.read_parquet(f'{TK}/weekly_article.parquet')
ALL = pd.read_parquet(f'{TK}/weekly_all.parquet') if (pathlib.Path(TK) / 'weekly_all.parquet').exists() else None
if ALL is None:
    # upper bound for "tweets with at least one mapped article": sum over the broad nodes (a tweet in two broad nodes counts twice)
    ALL = W[W.level == 1].groupby('week', as_index=False).agg(tweets=('tweets', 'sum'), total_tweets=('total_tweets', 'first'))
    ALL['share'] = ALL.tweets / ALL.total_tweets.replace(0, np.nan)
    ALL_NOTE = 'sum of the broad nodes (upper bound: a tweet in two broad nodes counts twice)'
else:
    ALL_NOTE = 'exact'
BASE = dict(normal_weeks=S['normal_weeks'], mk_weeks=S['mk_weeks'], rise_ratio=S['rise_ratio'], quiet_weeks=S['quiet_weeks'],
            mk_alpha_one_sided=S['mk_alpha_one_sided'], sustained_min=S['sustained_min'],
            sustained_label_week=S['sustained_label_week'], fading_max=S['fading_max'])
BASE_FULL = dict(S)

# ---------------- label every node series with the unchanged rule ----------------
weekly, shifts = [], []
for (lvl, nid), g in W.groupby(['level', 'node_id']):
    s = g.sort_values('week').rename(columns={'share': 'x', 'tweets': 'v'}).assign(valid=lambda d: ~d.partial_week)[['week', 'x', 'v', 'valid']]
    w, sh = SH.label_series(s, S, MINV)
    w['source'] = 'tweetskb'; w['level'] = lvl; w['node_id'] = nid; w['label'] = g.label.iloc[0]
    weekly.append(w)
    for d in sh:
        d.update(source='tweetskb', level=lvl, node_id=nid, node_label=g.label.iloc[0]); shifts.append(d)
weekly = pd.concat(weekly, ignore_index=True)
shifts = pd.DataFrame(shifts)
sf = SH.seasonal_flags(shifts, weekly, S)
shifts = shifts.merge(sf, on=['source', 'level', 'node_id', 'start_week'], how='left')
bw = pd.Series(brk_week)
shifts['near_break'] = [bool(((bw - sw).abs() <= pd.Timedelta(weeks=2)).any()) for sw in shifts.start_week]
shifts['break_name'] = [next((k for k, v in brk_week.items() if abs(v - sw) <= pd.Timedelta(weeks=2)), None) for sw in shifts.start_week]
shifts['large'] = shifts['size'] >= S['large_ratio']
shifts['tested_level'] = shifts.level.isin([3, 2])
shifts['in_outcome_period'] = shifts.start_week.between(pd.Timestamp('2016-01-04'), pd.Timestamp('2023-03-27'))
shifts['main_set'] = shifts.tested_level & ~shifts.seasonal & ~shifts.label.isin(['censored', 'interrupted']) & ~shifts.near_break
save_parquet(weekly.drop(columns=['valid']).rename(columns={'x': 'share', 'v': 'tweets'}), f'{TK}/shift_weekly.parquet')
save_parquet(shifts, f'{TK}/shifts.parquet')
print('shifts', len(shifts), shifts.groupby(['level', 'label']).size().to_dict(), 'near break', int(shifts.near_break.sum()), flush=True)

# ---------------- noise benchmark (as code/parameter_audit/calibrate_interest.py) ----------------
SERIES = []
for (lvl, nid), g in W[W.level.isin([2, 3])].groupby(['level', 'node_id']):
    s = g.sort_values('week').rename(columns={'share': 'x', 'tweets': 'v'})
    s = s.assign(valid=~s.partial_week & np.isfinite(s.x) & (s.x > 0))[['week', 'x', 'v', 'valid']].reset_index(drop=True)
    SERIES.append((lvl, nid, s))


def run_rule(s, Sx):
    _, sh = SH.label_series(s, Sx, MINV)
    return [(d['label'], d['start_week']) for d in sh if d['label'] in ('sustained', 'intermediate', 'fading')]


def series_years(s):
    xs = pd.Series(np.where(s.valid, s.x, np.nan)); vs = pd.Series(np.where(s.valid, s.v, np.nan))
    normal = xs.shift(1).rolling(26, min_periods=26).median(); vn = vs.shift(1).rolling(26, min_periods=26).median()
    return float((np.isfinite(normal) & (normal > 0) & (vn >= MINV) & np.isfinite(xs)).sum()) / 52.18


def surrogate(s, rng):
    w, sh = SH.label_series(s, BASE_FULL, MINV)
    quiet = w.usable & (w.shift_id < 0) & np.isfinite(w.ratio) & (w.ratio > 0)
    r = np.log(w.ratio[quiet].to_numpy())
    n = len(s)
    if len(r) < 52:
        return None
    out = np.empty(0)
    while len(out) < n:
        st = rng.integers(0, len(r))
        out = np.concatenate([out, np.take(r, np.arange(st, st + BLOCK), mode='wrap')])
    return pd.DataFrame(dict(week=s.week.to_numpy(), x=np.exp(out[:n]), v=np.full(n, 1e9), valid=np.ones(n, bool)))


rng = np.random.default_rng(SEED)
SUR = []
for lvl, nid, s in SERIES:
    for k in range(REPS):
        z = surrogate(s, rng)
        if z is not None:
            SUR.append((lvl, nid, z))
GRID = [('base (record)', None, BASE_FULL)] + [('ratio', v, dict(BASE_FULL, rise_ratio=v)) for v in (1.2, 1.3, 2.0, 2.5, 3.0)]
bench = []
for name, val, Sx in GRID:
    for lvl in (3, 2):
        real = [s for (a, b, s) in SERIES if a == lvl]
        sur = [z for (a, b, z) in SUR if a == lvl]
        yrs_real = sum(series_years(s) for s in real); yrs_sur = sum((len(z) - 26) / 52.18 for z in sur)
        rr = [x for s in real for x in run_rule(s, Sx)]
        ls = [x for z in sur for x in run_rule(z, Sx)]
        lr = [l for l, _ in rr]; lnn = [l for l, _ in ls]
        rr_nb = [l for l, sw in rr if not any(abs(v - sw) <= pd.Timedelta(weeks=2) for v in brk_week.values())]
        d = dict(setting=name, value=val, level=LEV[lvl], real_series=len(real), real_series_years=round(yrs_real, 1), real_shifts=len(lr),
                 real_shifts_not_near_break=len(rr_nb), real_per100y=100 * len(lr) / yrs_real if yrs_real else np.nan,
                 real_sustained=sum(l == 'sustained' for l in lr), noise_series=len(sur), noise_series_years=round(yrs_sur, 1),
                 noise_shifts=len(lnn), noise_per100y=100 * len(lnn) / yrs_sur if yrs_sur else np.nan,
                 noise_sustained=sum(l == 'sustained' for l in lnn))
        d['noise_share_all'] = d['noise_per100y'] / d['real_per100y'] if d['real_per100y'] else np.nan
        rs = 100 * d['real_sustained'] / yrs_real if yrs_real else np.nan
        ns = 100 * d['noise_sustained'] / yrs_sur if yrs_sur else np.nan
        d['noise_share_sustained'] = ns / rs if rs else np.nan
        bench.append(d)
BN = pd.DataFrame(bench)
BN.to_csv(f'{TK}/noise_benchmark.csv', index=False)
print(BN.round(3).to_string(index=False), flush=True)

# ---------------- coverage per year ----------------
full = T[~T.partial_week].copy(); full['year'] = full.week.dt.isocalendar().year.astype(int)
cov = T.assign(year=T.week.dt.isocalendar().year.astype(int)).groupby('year').agg(weeks=('week', 'size'), full_weeks=('partial_week', lambda s: int((~s).sum())),
                                                                                  sample_tweets=('total_tweets', 'sum')).reset_index()
cov['median_weekly_sample_tweets'] = cov.year.map(full.groupby('year').total_tweets.median())
gy = G.assign(year=G.week.dt.isocalendar().year.astype(int))
cov['articles_with_tweets'] = cov.year.map(gy[gy.tweets > 0].groupby('year').article.nunique())
cov['article_tweet_mentions'] = cov.year.map(gy.groupby('year').tweets.sum())
if ALL is not None:
    az = ALL.assign(year=ALL.week.dt.isocalendar().year.astype(int)).groupby('year').tweets.sum()
    cov['tweets_in_broad_nodes_sum'] = cov.year.map(az)
    cov['share_tweets_in_broad_nodes_sum'] = cov.tweets_in_broad_nodes_sum / cov.sample_tweets
wy = weekly.assign(year=weekly.week.dt.isocalendar().year.astype(int))
for lvl in (3, 2, 1):
    g = wy[(wy.level == lvl)].groupby(['year', 'node_id']).agg(usable=('usable', 'mean'), vol=('v', 'median')).reset_index()
    cov[f'{LEV[lvl]}_usable_series'] = cov.year.map(g[g.usable >= 0.8].groupby('year').size()).fillna(0).astype(int)
    cov[f'{LEV[lvl]}_median_weekly_tweets'] = cov.year.map(g.groupby('year').vol.median())
    cov[f'{LEV[lvl]}_series'] = g.node_id.nunique()
cov.to_csv(f'{TK}/coverage_year.csv', index=False)
print(cov.round(3).to_string(index=False), flush=True)

# ---------------- linker breaks: level change of the series across each break ----------------
# January 2021 and September 2022 lie outside the endpoint's data (it ends 2020-12-31). April 2018 is testable only across the
# sample gap (no tweets from 2017-11-29 to 2018-03-31; data restart on 2018-04-01, the first day of Part 7). The comparison is
# the median share in the 8 full weeks before the gap (weeks of 2017-10-02 to 2017-11-20) with the 8 full weeks from 2018-04-02,
# and a placebo of the same shape (two 8-week windows 18 weeks apart, both on the same side of the gap) at every 4th week.
K, GAPW = 8, 18
Wm = W.assign(sh=np.where(W.partial_week, np.nan, W.share), tw=np.where(W.partial_week, np.nan, W.tweets))
Wm = Wm.sort_values('week')
MINW = 30
b0, a0 = pd.Timestamp('2017-11-27'), pd.Timestamp('2018-04-02')
gap_start, gap_end = pd.Timestamp('2017-11-27'), pd.Timestamp('2018-04-02')


def win(s, start):
    x = s[(s.index >= start) & (s.index < start + pd.Timedelta(weeks=K))]
    return x.values if len(x) == K and not np.isnan(x.values).any() else None


def pair_stats(before_start, after_start):
    out = []
    for (lvl, nid), g in Wm.groupby(['level', 'node_id']):
        s = g.set_index('week')
        sh, tw = s.sh, s.tw
        a, b, ta, tb = win(sh, after_start), win(sh, before_start), win(tw, after_start), win(tw, before_start)
        if a is None or b is None or np.median(ta) < MINW or np.median(tb) < MINW or np.median(a) <= 0 or np.median(b) <= 0:
            continue
        out.append((LEV[lvl], np.median(a) / np.median(b)))
    return pd.DataFrame(out, columns=['level', 'jump'])


def total_ratio(before_start, after_start):
    z = ALL.set_index('week').share.where(ALL.set_index('week').total_tweets > 0)
    ok = T.set_index('week').partial_week
    z = z.where(~ok.reindex(z.index).fillna(True))
    a, b = win(z, after_start), win(z, before_start)
    return np.nan if a is None or b is None else np.median(a) / np.median(b)


real_before = b0 - pd.Timedelta(weeks=K)
rp = pair_stats(real_before, a0)
plc = []
wks = [w for w in T.week[T.week >= pd.Timestamp('2015-02-02')]]
for w in wks[::4]:
    a_start = w + pd.Timedelta(weeks=GAPW + K)
    if a_start + pd.Timedelta(weeks=K) > pd.Timestamp('2020-12-21'):
        continue
    one_side = (a_start + pd.Timedelta(weeks=K) <= gap_start) or (w >= gap_end)
    if not one_side:
        continue
    d = pair_stats(w, a_start)
    plc.append((w, d, total_ratio(w, a_start)))
brs = []
for lev in ('narrow', 'middle', 'broad'):
    b = rp[rp.level == lev]
    pm, pc = [], []
    for w, d, _ in plc:
        x = d[d.level == lev]
        if len(x) >= 5:
            pm.append(np.log2(x.jump).median()); pc.append(((x.jump >= 1.5) | (x.jump <= 1 / 1.5)).mean())
    brs.append(dict(level=lev, series=len(b), median_log2_jump=np.log2(b.jump).median() if len(b) else np.nan,
                    share_changed_1_5x=((b.jump >= 1.5) | (b.jump <= 1 / 1.5)).mean() if len(b) else np.nan,
                    share_up_1_5x=(b.jump >= 1.5).mean() if len(b) else np.nan, share_down_1_5x=(b.jump <= 1 / 1.5).mean() if len(b) else np.nan,
                    placebo_pairs=len(pm), placebo_median_log2_jump_p5=np.nanpercentile(pm, 5) if pm else np.nan,
                    placebo_median_log2_jump_p95=np.nanpercentile(pm, 95) if pm else np.nan,
                    placebo_share_changed_median=np.median(pc) if pc else np.nan, placebo_share_changed_p95=np.nanpercentile(pc, 95) if pc else np.nan))
BRS = pd.DataFrame(brs); BRS.to_csv(f'{TK}/break_check.csv', index=False)
tr = [r for _, _, r in plc if np.isfinite(r)]
extra = [dict(comparison='April 2018 (across the gap)', tweets_in_broad_nodes_share_after_over_before=total_ratio(real_before, a0),
              placebo_p5=np.percentile(tr, 5) if tr else np.nan, placebo_p95=np.percentile(tr, 95) if tr else np.nan, placebo_pairs=len(tr)),
         dict(comparison='January 2021', tweets_in_broad_nodes_share_after_over_before=np.nan),
         dict(comparison='September 2022', tweets_in_broad_nodes_share_after_over_before=np.nan)]
pd.DataFrame(extra).to_csv(f'{TK}/break_check_totals.csv', index=False)
print(BRS.round(3).to_string(index=False)); print(pd.DataFrame(extra).round(3).to_string(index=False), flush=True)

# ---------------- positive controls: first rise within 8 weeks of the event, in the control theme ----------------
CONTROLS = [('COVID-19, March 2020', 'B15.M04.N05', pd.Timestamp('2020-03-11')),
            ('George Floyd, June 2020', 'B05.M02.N02', pd.Timestamp('2020-05-25')),
            ('#MeToo, October 2017', 'B12.M01.N02', pd.Timestamp('2017-10-15'))]
crow = []
for name, nid, ev in CONTROLS:
    lvl = nid.count('.') + 1
    chain = [a for a in ancestors(nid)]                   # narrow, middle, broad of the control theme
    for node in chain:
        sh = shifts[shifts.node_id == node]
        w = weekly[weekly.node_id == node].set_index('week')
        win = w[(w.index >= ev - pd.Timedelta(weeks=8)) & (w.index <= ev + pd.Timedelta(weeks=8))]
        hit = sh[(sh.start_week >= ev - pd.Timedelta(weeks=8)) & (sh.start_week <= ev + pd.Timedelta(weeks=8))].sort_values('start_week')
        r0 = hit.iloc[0] if len(hit) else None
        crow.append(dict(control=name, event_date=ev.date(), node_id=node, level=LEV[node.count('.') + 1], node_label=label[node],
                         rise_found=r0 is not None, start_week=None if r0 is None else r0.start_week.date(),
                         weeks_from_event=None if r0 is None else int((r0.start_week - ev).days / 7),
                         duration_class=None if r0 is None else r0.label, size=None if r0 is None else round(float(r0['size']), 2),
                         whole_peak=None if r0 is None else round(float(r0.whole_peak), 2),
                         weeks_ge_1_5=None if r0 is None else int(r0.whole_duration), near_break=None if r0 is None else bool(r0.near_break),
                         seasonal=None if r0 is None else bool(r0.seasonal), n_rises_in_window=len(hit),
                         max_ratio_in_window=round(float(win.ratio.max()), 2) if win.ratio.notna().any() else None,
                         usable_weeks_in_window=int(win.usable.sum()), median_weekly_tweets=float(w.v.median())))
CT = pd.DataFrame(crow); CT.to_csv(f'{TK}/controls.csv', index=False)
print(CT.to_string(index=False), flush=True)

# ---------------- rise counts ----------------
def counts(df, by):
    t = df.groupby(by + ['label']).size().unstack('label', fill_value=0)
    for c in ('sustained', 'intermediate', 'fading', 'censored', 'interrupted'):
        if c not in t:
            t[c] = 0
    t['all'] = t[['sustained', 'intermediate', 'fading', 'censored', 'interrupted']].sum(axis=1)
    return t[['sustained', 'intermediate', 'fading', 'censored', 'interrupted', 'all']]


shifts['level_name'] = shifts.level.map(LEV)
ok = shifts[~shifts.near_break]
c_all = counts(ok, ['level_name'])
c_out = counts(ok[ok.in_outcome_period], ['level_name'])
c_main = counts(shifts[shifts.main_set & shifts.in_outcome_period], ['level_name'])
c_seas = ok.groupby('level_name').seasonal.sum()
print(c_all, c_out, c_main, sep='\n')

# ---------------- report ----------------
def md(df, floatfmt=3):
    d = df.copy()
    cols = list(d.columns)
    out = ['| ' + ' | '.join(str(c) for c in cols) + ' |', '|' + ' --- |' * len(cols)]
    for r in d.itertuples(index=False):
        cells = []
        for v in r:
            if isinstance(v, (float, np.floating)):
                cells.append('' if not np.isfinite(v) else (f'{v:,.{floatfmt}f}' if abs(v) < 1000 else f'{v:,.0f}'))
            elif v is None or (not isinstance(v, str) and pd.isna(v)):
                cells.append('')
            else:
                cells.append(str(v))
        out.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(out)


E_ = pd.read_parquet(f'{TK}/entities.parquet')
n_art = E_.article.nunique(); n_art_in = E_[E_.exists_in_tweetskb].article.nunique()
have0 = T[~T.partial_week].week.min().date(); have1 = T[~T.partial_week].week.max().date()
npart_in = int(T[(T.week >= pd.Timestamp('2015-01-05')) & (T.week <= pd.Timestamp('2020-12-28'))].partial_week.sum())
rep = [f"""# TweetsKB conversation series: interest side

Written by `code/conversation/04_tweetskb_shifts.py`. Settings: `prereg/conversation_sources_settings_2026-10-14.json` (not edited). Implementation choices the record does not make are in `prereg/DEVIATIONS.md` (Conversation sources section). No borrowing data were read or linked. Counts only: no tweet text, tweet IDs or user fields were requested or stored.

## What the endpoint holds (read this first)

The public 5% endpoint contains tweets only from {have0} to {have1}: its earliest tweet is 2015-01-01 and its latest 2020-12-31 (checked with a count by year and a min/max query). It has no tweets for February 2013 to December 2014 or for January 2021 to June 2023, so the record's period (February 2013 to June 2023) cannot be built from the endpoint. Within 2015 to 2020, {npart_in} weeks have fewer than 7 days of sample data (outages in 2017 and 2018) and are treated as missing. Two of the three linker breaks (January 2021, September 2022) fall outside the data, so they cannot be checked; only April 2018 can. Series for 2013 to 2014 and 2021 to 2023 would need the monthly files (Zenodo parts 1 to 3, GESIS parts 10 to 12), which are large downloads that need Khant's permission and were not made. Everything below covers 2015 to 2020 only.

## What was built

- Entities: {n_art} English Wikipedia concept articles mapped to theme values (the articles of `data/db/interest/wiki/articles.parquet`), with {int((E_.kind == 'redirect').sum())} redirect titles that the Wikipedia series also adds to an article. {int(E_.exists_in_tweetskb.sum())} DBpedia IRIs of {len(E_)} exist in TweetsKB; {n_art_in} of {n_art} articles have at least one IRI there. The {n_art - n_art_in} articles with none (mostly very general or disambiguated titles) have no TweetsKB series.
- Source: the public TweetsKB SPARQL endpoint (5% sample), graph `http://data.gesis.org/tweetskb`, one query every 3 seconds, User-Agent with kwai@cmkl.ac.th, every answer cached in `data/interim/tweetskb_cache/`.
- Weekly series: ISO weeks starting Monday, weeks of the sample only (see above). For a node: distinct tweets that mention any of its articles (each tweet once per node), divided by all tweets in the sample that week. Tone: mean positive and mean negative score of those tweets (0 to 1).
- Nodes: {W[W.level == 3].node_id.nunique()} narrow, {W[W.level == 2].node_id.nunique()} middle, {W[W.level == 1].node_id.nunique()} broad. Files: `data/db/interest/tweetskb/weekly_node.parquet`, `weekly_article.parquet`, `shifts.parquet`.
- Partial weeks (fewer than 7 days of sample data): {int(T.partial_week.sum())} of {len(T)}; they count as missing.

## Coverage per year

Sample tweets are the denominator. The column on tweets in broad nodes is an upper bound for the tweets that mention at least one mapped article (a tweet in two broad nodes counts twice). "Usable series" = nodes whose weeks are usable (26 full weeks behind them and a normal level of at least {MINV:.0f} tweets a week) in at least 80% of the year's weeks.

{md(cov.rename(columns={c: c.replace('_', ' ') for c in cov.columns}), 3)}
"""]
rep.append(f"""
## The linker breaks and 2021 to 2023

Coverage of 2021 to June 2023: none. The endpoint has no tweet after 2020-12-31, so there are no 2021 to 2023 series and the January 2021 and September 2022 breaks cannot be checked.

April 2018: the sample has no tweets from 2017-11-29 to 2018-03-31 and restarts on 2018-04-01, the first day of Part 7 (new linker dump). A before-and-after comparison at the break is therefore possible only across the gap. The table compares the median share in the 8 full weeks before the gap (weeks of 2017-10-02 to 2017-11-20) with the 8 full weeks from 2018-04-02, for series with at least 30 tweets a week in both windows. The placebo columns give the same statistic for pairs of 8-week windows 18 weeks apart (the same distance) that lie on one side of the gap, every 4th week: the 5th and 95th percentile of the median log2 jump across series, and the share of series that changed by a factor of 1.5 either way. A seasonal difference (October to November against April) and the gap itself are not separated from a linker effect.

{md(BRS, 3)}

Share of sample tweets in the broad nodes (sum), after over before, with the placebo range:

{md(pd.DataFrame(extra), 3)}

A median jump outside the placebo range, or a changed-share above the placebo 95th percentile, would point to a level shift at the break. Rises that start within 2 weeks of a break week are flagged and left out of every count below ({int(shifts.near_break.sum())} of {len(shifts)} starts).
""")
rep.append(f"""
## Noise benchmark (parameter-audit method, interest data only)

Each narrow and middle series is rebuilt {REPS} times from its own quiet-week deviations from normal (circular blocks of 8 weeks, seed {SEED}), so it keeps ordinary week-to-week variation and holds no real event. The unchanged rule is run on the real and the rebuilt series. Noise share = rises found per 100 series-years in the rebuilt series divided by rises per 100 series-years in the real series. The base row is the record's rule (ratio 1.5); the other rows change only the ratio, for context.

{md(BN[['setting', 'value', 'level', 'real_series', 'real_series_years', 'real_shifts', 'real_shifts_not_near_break', 'real_sustained', 'noise_series_years', 'noise_shifts', 'noise_sustained', 'noise_share_all', 'noise_share_sustained']], 3)}
""")
rep.append(f"""
## Rises by duration class

The Study 3 rule is unchanged: sustained = at least 4 weeks at ratio 1.5 or more, intermediate = 3, fading = 2 or fewer. Censored = still running when data end, interrupted = data became unusable. Starts within 2 weeks of a break are excluded.

All starts (data 2015 to 2020):

{md(c_all.reset_index(), 0)}

Starts in the outcome period (week of 4 January 2016 to week of 27 March 2023):

{md(c_out.reset_index(), 0)}

Main set (narrow and middle, not seasonal, completed, outside the break windows, outcome period): {md(c_main.reset_index(), 0)}

Seasonal rises (all starts, outside breaks) by level: {c_seas.to_dict()}.
""")
CTs = CT.drop(columns=['median_weekly_tweets', 'usable_weeks_in_window'])
rep.append(f"""
## Control themes

For each event, the first rise that starts within 8 weeks (before or after) of the event date, in the control theme's narrow node and in its middle and broad parents. Event dates: COVID-19 declared a pandemic 2020-03-11, George Floyd's death 2020-05-25, #MeToo hashtag 2017-10-15. Size = peak ratio to the 26-week normal up to the labelling week.

{md(CTs, 2)}
""")
rep.append(f"\nRun time of this step: {(time.time() - T0) / 60:.1f} minutes.\n")
open(os.environ.get('TK_TEST_REPORT', f'{REP}/tweetskb_interest.md'), 'w').write('\n'.join(rep))
print('report written', flush=True)
