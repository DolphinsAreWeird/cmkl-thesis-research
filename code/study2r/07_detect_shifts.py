"""Study 2R step 7: detect the shifts of every 2R article with the calibrated rule (interest only; STOPS here, nothing is
joined to borrowing). Rule = the Study 3 rule unchanged (26-week median, ratio >= calibrated value, 8-week Mann-Kendall with
Hamed-Rao, one-sided p < 0.10, armed start, sustained >= 4 weeks, intermediate 3, fading <= 2) via main_study/interest/_shifts,
floor 300 user views a week, rise ratio from data/db/study2r/calibration.json (filed in prereg/addenda_2r/..._b_...).
Quality flags as in main_study/interest/09 and 11 (not tuned): one_day (a day carried >= 50% of the week's views in the first
up to 4 weeks of the shift) and desktop_only (the rise came >= 90% from desktop and >= 25 points above the usual desktop
share; one cached API request per shift). Title-confusion is a hand check and is not run here.
Secondary: the same rule on the author's article. Also writes the sensitivity ratio 1.5 shift counts (addendum a).
Outputs: data/db/study2r/shifts_book.parquet, shifts_author.parquet, shifts_book_ratio1_5.parquet, data/reports/study2r_shifts.md
"""
import sys, pathlib, hashlib, urllib.parse
import numpy as np, pandas as pd
from common import *
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'main_study' / 'interest'))
import _shifts as SH  # noqa: E402
from _ci import settings  # noqa: E402

S0 = settings()
CAL = json.load(open(OUT / 'calibration.json'))
NOTE = pathlib.Path(__file__).resolve().parents[2] / 'prereg' / 'addenda_2r' / '2026-10-14_b_calibration_values.json'
assert NOTE.exists(), 'file the calibration note (06) before detecting shifts'
RATIO, MINV = CAL['chosen_ratio'], CAL['floor_views_per_week']
BASE = dict(normal_weeks=S0['normal_weeks'], mk_weeks=S0['mk_weeks'], rise_ratio=RATIO, quiet_weeks=S0['quiet_weeks'],
            mk_alpha_one_sided=S0['mk_alpha_one_sided'], sustained_min=S0['sustained_min'], sustained_label_week=S0['sustained_label_week'],
            fading_max=S0['fading_max'])
fid = lambda t: hashlib.sha1(t.encode()).hexdigest()[:16]
REST = 'https://wikimedia.org/api/rest_v1/metrics/pageviews'
SINGLE_DAY, DESK_RISE, DESK_GAP = 0.5, 0.9, 0.25
A = pd.read_parquet(OUT / 'articles.parquet')
M = pd.read_parquet(OUT / 'book_matches.parquet')
can = dict(zip(A.requested, A.canonical))
M['canonical'] = M.article.map(can)
works_of = M.groupby('canonical').work_id.apply(lambda s: sorted(int(x) for x in s)).to_dict()


def daily(t):
    f = OUT / 'pv_daily' / f'{fid(t)}.parquet'
    return pd.read_parquet(f).set_index('date').views


def detect(W, ratio, kind, quality):
    S = dict(BASE, rise_ratio=ratio)
    rows = []
    for art, g in W.groupby('article', sort=True):
        g = g.sort_values('week').reset_index(drop=True)
        s = pd.DataFrame(dict(week=g.week, x=g.share, v=g.views, valid=g.valid))
        w, sh = SH.label_series(s, S, MINV)
        for d in sh:
            n_w = int(min(max(d['whole_duration'], 1), 4)); a = d['start_week']; b = a + pd.Timedelta(days=7 * n_w - 1)
            tw = g[(g.week >= a) & (g.week <= b)]
            d.update(article=art, kind=kind, max_top_day_share=float(tw.top_day_share.max()) if len(tw) else np.nan,
                     series_weeks_usable=int(w.usable.sum()))
            rows.append(d)
    X = pd.DataFrame(rows)
    if not len(X):
        return X
    X['single_day'] = X.max_top_day_share >= SINGLE_DAY
    if quality:
        X['desktop_share_base'] = np.nan; X['desktop_share_rise'] = np.nan
        for i, r in X.iterrows():
            n_w = int(min(max(r.whole_duration, 1), 4)); a = r.start_week; b = a + pd.Timedelta(days=7 * n_w - 1); base_a = a - pd.Timedelta(weeks=26)
            t = urllib.parse.quote(r.article.replace(' ', '_'), safe='')
            resp = H.get(f'{REST}/per-article/en.wikipedia/desktop/user/{t}/daily/{base_a:%Y%m%d}00/{b:%Y%m%d}00')
            if resp['status'] not in (200, 404):
                continue
            dd = {} if resp['status'] == 404 else {x['timestamp'][:8]: x['views'] for x in json.loads(resp['text']).get('items', [])}
            dk = pd.Series({pd.Timestamp(k): v for k, v in dd.items()}, dtype=float).reindex(pd.date_range(base_a, b), fill_value=0)
            al = daily(r.article).reindex(pd.date_range(base_a, b), fill_value=0).astype(float)
            bd, ba, wd, wa = dk[:a - pd.Timedelta(days=1)], al[:a - pd.Timedelta(days=1)], dk[a:], al[a:]
            rise_d = wd.sum() - bd.median() * len(wd); rise_a = wa.sum() - ba.median() * len(wa)
            X.at[i, 'desktop_share_base'] = float(bd.sum() / ba.sum()) if ba.sum() else np.nan
            X.at[i, 'desktop_share_rise'] = float(rise_d / rise_a) if rise_a > 0 else np.nan
        X['desktop_only'] = (X.desktop_share_rise >= DESK_RISE) & ((X.desktop_share_rise - X.desktop_share_base) >= DESK_GAP)
    else:
        X['desktop_only'] = False
    X['quality_flag'] = [','.join(f for f, v in (('one_day', a), ('desktop_only', b)) if v) for a, b in zip(X.single_day, X.desktop_only)]
    X['quality_ok'] = X.quality_flag == ''
    X['whole_duration_bin'] = pd.cut(X.whole_duration, [0, 2, 3, 5, 1000], labels=['1-2 weeks', '3 weeks', '4-5 weeks', '6+ weeks']).astype(str)
    X.loc[X.label.isin(['censored', 'interrupted']), 'whole_duration_bin'] = 'not final'
    if kind == 'book':
        X['work_ids'] = X.article.map(lambda a: ','.join(map(str, works_of.get(a, []))))
    return X


def years(W):
    tot = 0.0
    for art, g in W.groupby('article'):
        g = g.sort_values('week'); xs = pd.Series(np.where(g.valid, g.share, np.nan)); vs = pd.Series(np.where(g.valid, g.views, np.nan))
        nm = xs.shift(1).rolling(26, min_periods=26).median(); vn = vs.shift(1).rolling(26, min_periods=26).median()
        tot += float((np.isfinite(nm) & (nm > 0) & (vn >= MINV) & np.isfinite(xs)).sum()) / 52.18
    return tot


WB = pd.read_parquet(OUT / 'weekly_book.parquet')
WA = pd.read_parquet(OUT / 'weekly_author.parquet')
log('rule: ratio', RATIO, 'floor', MINV, '| book articles', WB.article.nunique(), 'author articles', WA.article.nunique())
SB = detect(WB, RATIO, 'book', True); SB.to_parquet(OUT / 'shifts_book.parquet', index=False); log('book shifts', len(SB))
SB15 = detect(WB, 1.5, 'book', False); SB15.to_parquet(OUT / 'shifts_book_ratio1_5.parquet', index=False); log('book shifts at ratio 1.5 (sensitivity, no desktop check)', len(SB15))
SA = detect(WA, RATIO, 'author', True); SA.to_parquet(OUT / 'shifts_author.parquet', index=False); log('author shifts', len(SA))
yb, ya = years(WB), years(WA)


def table(X, title):
    L = [f'### {title}', '']
    if not len(X):
        return L + ['(none)', '']
    cls = ['sustained', 'intermediate', 'fading', 'censored', 'interrupted']
    L += ['| Class | All shifts | Quality OK (no flag) | Articles |', '|---|---|---|---|']
    for c in cls:
        x = X[X.label == c]
        L.append(f'| {c} | {len(x)} | {int(x.quality_ok.sum())} | {x.article.nunique()} |')
    L.append(f'| **total** | {len(X)} | {int(X.quality_ok.sum())} | {X.article.nunique()} |')
    F = X[X.label.isin(['sustained', 'intermediate', 'fading'])]
    L += ['', f'Flags among the three final classes ({len(F)}): one_day {int(F.single_day.sum())}, desktop_only {int(F.desktop_only.sum())}, any {int((~F.quality_ok).sum())}.', '',
          'By whole duration (known only after the shift ends; used for the confirmatory duration test):', '', '| Whole duration | Shifts | Quality OK |', '|---|---|---|']
    for b in ['1-2 weeks', '3 weeks', '4-5 weeks', '6+ weeks', 'not final']:
        x = X[X.whole_duration_bin == b]
        L.append(f'| {b} | {len(x)} | {int(x.quality_ok.sum())} |')
    return L + ['']


# interest-side sanity of the seven controls: first shift within 8 weeks of the release date (interest only)
REL = {"The Queen's Gambit (novel)": '2020-10-23', 'The Duke and I': '2020-12-25', 'Dune (novel)': '2021-10-22', 'Where the Crawdads Sing': '2022-07-15',
       'American Prometheus': '2023-07-21', 'Killers of the Flower Moon': '2023-10-20', 'Shōgun (novel)': '2024-02-27'}
CT = pd.read_csv(OUT / 'positive_control_matches.csv')
CT = CT[CT.matched == True]  # noqa: E712
L = ['# Study 2R: detected shifts (interest side only)', '',
     f'Built {time.strftime("%Y-%m-%d %H:%M")} by code/study2r/07_detect_shifts.py. Rule: Study 3 rule unchanged, rise ratio **{RATIO}**, floor **{int(MINV)}** user views a week '
     '(prereg/addenda_2r/2026-10-14_b_calibration_values.json, filed before this run). Nothing here is joined to borrowing; no borrowing effect around any event was computed.', '',
     f'Series: {WB.article.nunique():,} book articles ({yb:.0f} series-years at or above the floor); {WA.article.nunique():,} author articles ({ya:.0f} series-years).', '']
L += table(SB, f'Book articles, ratio {RATIO}') + table(SB15, 'Book articles, sensitivity ratio 1.5 (floor 300; no desktop check)') + table(SA, f'Author articles (secondary), ratio {RATIO}')
L += ['### Positive controls on the interest side', '', 'Book article, release date used (month of the record, day approximate), shifts starting within 8 weeks before or after it.', '',
      '| Control article | Release | Shifts within +/- 8 weeks (start week, class, size, whole duration, flag) |', '|---|---|---|']
for art, rel in REL.items():
    c = can.get(art, art); rel = pd.Timestamp(rel)
    x = SB[(SB.article == c) & ((SB.start_week - rel).abs() <= pd.Timedelta(weeks=8))] if len(SB) else SB
    txt = '; '.join(f'{r.start_week:%Y-%m-%d}, {r.label}, x{r.size:.1f}, {r.whole_duration} wk, {r.quality_flag or "ok"}' for r in x.itertuples()) if len(x) else 'none detected'
    L.append(f'| {c} | {rel:%Y-%m-%d} | {txt} |')
(REP / 'study2r_shifts.md').write_text('\n'.join(L) + '\n')
log('wrote study2r_shifts.md; seconds', int(time.time() - T0))
