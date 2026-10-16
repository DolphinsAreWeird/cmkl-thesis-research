# 02. Value-level interest shifts (interest data only: no demand is read or written).
# Series: weekly Wikipedia share and weekly GDELT share per theme value, from data/db/interest/wiki/weekly_value.parquet
# (07_wiki_series.py: the value's pages, own views plus kept redirects, over total English Wikipedia user views) and
# data/db/interest/gdelt/weekly_value.parquet (03_gdelt_series.py). A check recomputes a few Wikipedia value series from the
# daily page views and the totals, the way 07 does, and compares them with the stored file.
# Detector: the Study 3 interest code (interest/_shifts.py, label_series and seasonal_flags) with the fixed thresholds read from
# the record by interest/_ci.settings(), the armed reading of addendum d, and the GDELT durations of addendum h (ratio 1.0, so
# the Wikipedia thresholds), exactly as 08_shift_labels.py applies them to nodes.
# Automatic quality flags, as 09 and 11 give them to node shifts (addenda g and i):
#   one_day        from the weekly top_day_share of the value series (>= 50% in a week of the first 4 weeks of the shift);
#   desktop_only   the driver page's rise is almost only desktop views (official per-article API). Answers are read from
#                  wiki/_desktop_cache.json (read only) where the same page and window exist; new answers are requested at
#                  most one per second with the project user agent (code/config.py) and kept in
#                  data/db/study3b/_desktop_cache_value.json;
#   title_confusion  only where the same page and about the same week carry a verdict in wiki/review_title_confusion.csv;
#   single_site    (GDELT) only where the driver code and day have a sampled URL list in gdelt/figurative_url_samples.csv.
# Nothing is checked by hand. What could not be screened is counted in the report.
# NOT IN RECORD: (1) value level = level 4 in the table (node_id holds the value, `parent_node` its placed node);
# (2) title_confusion verdicts are matched on the same page and a start week within 2 weeks; (3) a shift whose driver page has no
# verdict stays unscreened for title confusion; (4) desktop_only is computed for labelled shifts from 2017-01 (the tested set);
# (5) the driver of a value shift is the value's page with the largest rise over the first weeks (as in 09), using the page's
# own daily views.
# Output: data/db/study3b/shifts_value.parquet (layout of interest/shifts.parquet), _desktop_cache_value.json,
# report data/reports/study3b_02_value_shifts.md
#   python 02_value_shifts.py [--skip-api]
import sys, os, re, json, hashlib, functools, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from _settings import SETTINGS as S
import _paths as IO
INTEREST = pathlib.Path(__file__).resolve().parents[1] / 'interest'
sys.path.append(str(INTEREST))
import _ci                                  # interest helpers (settings from the record, polite_get with the project user agent)
import _shifts as SH

SINGLE_DAY, DESK_RISE, DESK_GAP = 0.5, 0.9, 0.25      # the flag rules of interest/09_wiki_spike_check.py, used as written
REST = 'https://wikimedia.org/api/rest_v1/metrics/pageviews'
STUDY_START = pd.Timestamp(f'{S.study_start}-01')
OVERLAP = (pd.Timestamp('2017-01-02'), pd.Timestamp('2021-06-21'))
VALUE_LEVEL = 4


def log(*a):
    print(*a, flush=True)


# ---------------- settings agreement ----------------
def check_settings(Sci):
    """The interest code parses the same fixed record on its own; every value must equal the Study 3b settings copy."""
    pairs = [('normal_weeks', S.normal_weeks), ('large_ratio', S.large_ratio), ('sustained_min', S.sustained_min),
             ('intermediate_eq', S.intermediate_eq), ('fading_max', S.fading_max)]
    for k, v in pairs:
        if Sci[k] != v:
            raise SystemExit(f'interest settings differ from the Study 3 record on {k}: {Sci[k]} vs {v}')
    if S.gdelt_durations and S.gdelt_durations.get('values', {}).get('ratio') != 1.0:
        raise SystemExit('addendum h gives a GDELT duration ratio other than 1.0; this script applies the Wikipedia thresholds to GDELT only for ratio 1.0')


# ---------------- series ----------------
def weekly_frames(P):
    wk = pd.read_parquet(P.interest / 'wiki' / 'weekly_value.parquet')
    gd = pd.read_parquet(P.interest / 'gdelt' / 'weekly_value.parquet')
    return wk.rename(columns={'views': 'volume'}), gd.rename(columns={'mentions': 'volume'})


def run_detector(df, source, Sci, min_vol):
    weekly, shifts = [], []
    for value, g in df.groupby('value'):
        s = g.rename(columns={'share': 'x', 'volume': 'v'}).assign(valid=lambda d: ~d.partial_week)[['week', 'x', 'v', 'valid']]
        w, sh = SH.label_series(s, Sci, min_vol, None)
        w['source'] = source; w['level'] = VALUE_LEVEL; w['node_id'] = value; w['label'] = value
        weekly.append(w)
        for d in sh:
            d.update(source=source, level=VALUE_LEVEL, node_id=value, node_label=value)
            shifts.append(d)
    return pd.concat(weekly, ignore_index=True), pd.DataFrame(shifts)


# ---------------- check against the daily views ----------------
def recompute_check(P, n_check=8):
    """Recompute the weekly views of a few values from the page views (07's rule) and compare with the stored file."""
    WK = P.interest / 'wiki'
    A = pd.read_parquet(WK / 'articles.parquet')
    S_ = pd.read_parquet(WK / 'redirect_screen.parquet') if (WK / 'redirect_screen.parquet').exists() else pd.DataFrame(columns=['canonical', 'redirect', 'keep'])
    kept = S_[S_.keep == True].groupby('canonical').redirect.apply(list).to_dict()  # noqa: E712
    days = pd.date_range(pd.Timestamp('2015-07-01'), pd.Timestamp('2026-09-30'), freq='D')
    wkd = days - pd.to_timedelta(days.weekday, unit='D')

    def load(t):
        f = WK / 'pv_daily' / f'{hashlib.sha1(t.encode()).hexdigest()[:16]}.parquet'
        return pd.read_parquet(f).set_index('date').views.reindex(days, fill_value=0).astype(float) if f.exists() else None
    stored = pd.read_parquet(WK / 'weekly_value.parquet')
    vals = sorted(A.theme.unique())
    pick = vals[::max(1, len(vals) // n_check)][:n_check]
    worst = 0.0
    for v in pick:
        titles = list(dict.fromkeys(A[A.theme == v].canonical.dropna()))
        s = None
        for t in titles:
            x = load(t)
            if x is None:
                continue
            for r in kept.get(t, []):
                y = load(r)
                if y is not None:
                    x = x + y
            s = x if s is None else s + x
        if s is None:
            continue
        mine = pd.DataFrame({'week': wkd, 'v': s.values}).groupby('week').v.sum()
        ref = stored[stored.value == v].set_index('week').views
        j = mine.index.intersection(ref.index)
        worst = max(worst, float((mine[j] - ref[j]).abs().max() / max(1.0, ref[j].max())))
    return len(pick), worst


# ---------------- quality flags ----------------
def wiki_quality(P, shifts, wk_weekly, args):
    """one_day, desktop_only and the driver page for Wikipedia value shifts in the tested set."""
    WK = P.interest / 'wiki'
    A = pd.read_parquet(WK / 'articles.parquet')
    arts = A.groupby('theme').canonical.apply(lambda s: list(dict.fromkeys(s.dropna()))).to_dict()
    old = json.load(open(WK / '_desktop_cache.json')) if (WK / '_desktop_cache.json').exists() else {}
    new_f = P.out('_desktop_cache_value.json')
    new = json.load(open(new_f)) if new_f.exists() else {}

    @functools.lru_cache(maxsize=None)
    def daily(t):
        f = WK / 'pv_daily' / f'{hashlib.sha1(t.encode()).hexdigest()[:16]}.parquet'
        return pd.read_parquet(f).set_index('date').views if f.exists() else None

    top = wk_weekly.set_index(['value', 'week']).top_day_share
    rows, n_req, n_hit_old, n_hit_new = [], 0, 0, 0
    todo = shifts[(shifts.source == 'wikipedia') & shifts.labelled & (shifts.start_week >= STUDY_START)]
    for i, r in enumerate(todo.itertuples()):
        n_w = int(min(max(r.whole_duration, 1), 4))
        a = r.start_week; b = a + pd.Timedelta(days=7 * n_w - 1); base_a = a - pd.Timedelta(weeks=26)
        wks = [a + pd.Timedelta(weeks=k) for k in range(n_w)]
        tds = [top.get((r.node_id, w), np.nan) for w in wks]
        max_top = float(np.nanmax(tds)) if np.isfinite(tds).any() else np.nan
        rises = {}
        for t in arts.get(r.node_id, []):
            s = daily(t)
            if s is None:
                continue
            base = s[base_a:a - pd.Timedelta(days=1)].reindex(pd.date_range(base_a, a - pd.Timedelta(days=1)), fill_value=0)
            win = s[a:b].reindex(pd.date_range(a, b), fill_value=0)
            rises[t] = win.sum() - base.median() * len(win)
        pos = {k: v for k, v in rises.items() if v > 0}
        driver = max(rises, key=rises.get) if rises else None
        out = dict(source='wikipedia', node_id=r.node_id, start_week=r.start_week, wiki_driver=driver,
                   max_top_day_share=max_top, driver_share_of_rise=(pos.get(driver, 0) / sum(pos.values())) if pos else np.nan)
        if driver:
            key = f'{driver}|{base_a.date()}|{b.date()}'
            got = old.get(key) if key in old else new.get(key)
            if key in old:
                n_hit_old += 1
            elif key in new:
                n_hit_new += 1
            elif not args.skip_api:
                import urllib.parse
                t = urllib.parse.quote(driver.replace(' ', '_'), safe='')
                resp = _ci.polite_get(f'{REST}/per-article/en.wikipedia/desktop/user/{t}/daily/{base_a:%Y%m%d}00/{b:%Y%m%d}00', min_gap=1.0)
                if resp is not None:
                    new[key] = {} if resp.status_code == 404 else {x['timestamp'][:8]: x['views'] for x in resp.json().get('items', [])}
                    got = new[key]; n_req += 1
                    if n_req % 50 == 0:
                        _ci.save_json(new, str(new_f))
                        log(f'  desktop requests made: {n_req}')
            if got is not None:
                dk = pd.Series({pd.Timestamp(k): v for k, v in got.items()}, dtype=float).reindex(pd.date_range(base_a, b), fill_value=0)
                al = daily(driver).reindex(pd.date_range(base_a, b), fill_value=0)
                bd, ba, wd, wa = dk[:a - pd.Timedelta(days=1)], al[:a - pd.Timedelta(days=1)], dk[a:], al[a:]
                rise_d = wd.sum() - bd.median() * len(wd); rise_a = wa.sum() - ba.median() * len(wa)
                out.update(desktop_share_base=float(bd.sum() / ba.sum()) if ba.sum() else np.nan,
                           desktop_share_rise=float(rise_d / rise_a) if rise_a > 0 else np.nan)
        rows.append(out)
    _ci.save_json(new, str(new_f))
    Q = pd.DataFrame(rows)
    Q['single_day'] = Q.max_top_day_share >= SINGLE_DAY
    Q['desktop_rise'] = (Q.desktop_share_rise >= DESK_RISE) & ((Q.desktop_share_rise - Q.desktop_share_base) >= DESK_GAP)
    no_desktop = int(Q.desktop_share_rise.isna().sum()) if 'desktop_share_rise' in Q else len(Q)
    return Q, dict(requests=n_req, cache_hits_old=n_hit_old, cache_hits_new=n_hit_new, checked=len(Q), no_desktop=no_desktop)


def title_verdicts(P):
    """(page, start week) pairs with a title_confusion verdict, and with an ok verdict, from the existing hand check."""
    f = P.interest / 'wiki' / 'review_title_confusion.csv'
    if not f.exists():
        return {}, {}
    R = pd.read_csv(f, parse_dates=['start_week'])
    bad, ok = {}, {}
    for r in R.itertuples():
        pages = re.findall(r'(?:^|\|\| )(.+?) \d+% of rise', str(r.evidence))
        for p in pages[:2]:
            (bad if r.verdict == 'title_confusion' else ok).setdefault(p.strip().lower(), set()).add(pd.Timestamp(r.start_week))
    return bad, ok


def match_title(page, start, table, tol_days=14):
    if page is None:
        return False
    return any(abs((start - w).days) <= tol_days for w in table.get(str(page).lower(), ()))


def gdelt_quality(P, shifts):
    """Driver code of each GDELT value shift (largest rise in mentions over the first weeks, as in interest/10) and the
    single-site check where the driver code and day have a sampled URL list."""
    raw_f = pathlib.Path(_ci.D) / 'raw' / 'gdelt_weekly_2017_2021H1.parquet'
    import pyarrow.parquet as pq
    raw = pq.read_table(raw_f, columns=['week', 'theme', 'mentions']).to_pandas(ignore_metadata=True)
    raw['week'] = pd.to_datetime(raw.week)
    M = pd.read_parquet(P.interest / 'gdelt' / 'code_map.parquet')
    codes_of = M.groupby('value').code.apply(list).to_dict()
    todo = shifts[(shifts.source == 'gdelt') & shifts.labelled & (shifts.start_week >= STUDY_START)]
    US = pd.read_csv(P.interest / 'gdelt' / 'figurative_url_samples.csv') if (P.interest / 'gdelt' / 'figurative_url_samples.csv').exists() else pd.DataFrame(columns=['code', 'day', 'urls'])

    def top_site_share(urls):
        from collections import Counter
        doms = [re.sub(r'^https?://(www\.)?([^/]+).*$', r'\2', u) for u in json.loads(urls)]
        return Counter(doms).most_common(1)[0][1] / len(doms) if doms else np.nan
    US['top_site_share'] = US.urls.map(top_site_share)
    share = dict(zip(zip(US.code, US.day), US.top_site_share))
    import _gdelt_review as RV
    rows = []
    for r in todo.itertuples():
        codes = codes_of.get(r.node_id, [])
        a = r.start_week; n_w = int(min(max(r.whole_duration, 1), 4)); b = a + pd.Timedelta(weeks=n_w - 1)
        g = raw[raw.theme.isin(codes)]
        base = g[g.week.between(a - pd.Timedelta(weeks=26), a - pd.Timedelta(days=1))].pivot_table(index='week', columns='theme', values='mentions', aggfunc='sum').reindex(columns=codes).fillna(0).median()
        win = g[g.week.between(a, b)].groupby('theme').mentions.sum().reindex(codes).fillna(0)
        rise = (win - base * n_w).sort_values(ascending=False)
        driver = rise.index[0] if len(rise) else None
        day = str((a + pd.Timedelta(days=2)).date())
        art = share.get((driver, day))
        rows.append(dict(source='gdelt', node_id=r.node_id, start_week=a, gdelt_driver=driver,
                         gdelt_feed_artifact=(None if art is None or np.isnan(art) else bool(art >= 0.5)),
                         driver_has_verdict=driver in RV.FIGURATIVE if driver else False))
    return pd.DataFrame(rows)


# ---------------- main ----------------
def main():
    ap = IO.parser('Value-level interest shifts (interest data only)')
    ap.add_argument('--skip-api', action='store_true', help='use cached desktop answers only, make no request')
    ap.add_argument('--limit', type=int, default=None, help='development only: first N values of each source')
    args = ap.parse_args()
    P = IO.Paths(args.sim)
    if args.sim:                                    # simulated world: the value shifts were written by _simulate.py
        sha = hashlib.sha256(P.shifts_value.read_bytes()).hexdigest()
        meta = dict(IO.load_meta(P), build_id='n/a')
        IO.write_report(P, '02', 'Study 3b value-level interest shifts (simulated)', ['- simulated world, shifts_value.parquet written by _simulate.py'], S, meta,
                        extra={'shifts_value file SHA-256': f'`{sha}`'})
        return
    Sci = _ci.settings()
    check_settings(Sci)
    wk, gd = weekly_frames(P)
    if args.limit:
        wk = wk[wk.value.isin(sorted(wk.value.unique())[:args.limit])]
        gd = gd[gd.value.isin(sorted(gd.value.unique())[:args.limit])]
    log(f'value series: Wikipedia {wk.value.nunique()}, GDELT {gd.value.nunique()}')
    n_chk, worst = recompute_check(P) if not args.limit else (0, 0.0)
    log(f'recomputed {n_chk} Wikipedia value series from the daily views: largest relative difference {worst:.2e}')
    MIN = {'wikipedia': Sci['min_wiki_views'], 'gdelt': Sci['min_gdelt_mentions']}
    ww, sw = run_detector(wk, 'wikipedia', Sci, MIN['wikipedia'])
    wg, sg = run_detector(gd, 'gdelt', Sci, MIN['gdelt'])
    weekly = pd.concat([ww, wg], ignore_index=True)
    shifts = pd.concat([sw, sg], ignore_index=True)
    sf = SH.seasonal_flags(shifts, weekly, Sci)
    shifts = shifts.merge(sf, on=['source', 'level', 'node_id', 'start_week'], how='left')
    shifts['large'] = shifts['size'] >= Sci['large_ratio']
    shifts['tested_level'] = True
    shifts['main_set'] = ~shifts.seasonal.fillna(False).astype(bool) & ~shifts.label.isin(['censored', 'interrupted'])
    shifts['in_overlap'] = shifts.start_week.between(*OVERLAP)
    shifts['labelled'] = shifts.label.isin(['sustained', 'intermediate', 'fading'])
    log('shifts by source and label', shifts.groupby(['source', 'label']).size().to_dict())
    # quality flags
    Q, qinfo = wiki_quality(P, shifts, wk, args)
    GQ = gdelt_quality(P, shifts)
    bad, ok = title_verdicts(P)
    shifts = shifts.merge(Q[['source', 'node_id', 'start_week', 'wiki_driver', 'max_top_day_share', 'single_day', 'desktop_rise']],
                          on=['source', 'node_id', 'start_week'], how='left')
    shifts = shifts.merge(GQ[['source', 'node_id', 'start_week', 'gdelt_driver', 'gdelt_feed_artifact', 'driver_has_verdict']],
                          on=['source', 'node_id', 'start_week'], how='left')
    flags, tcheck = [], []
    for r in shifts.itertuples():
        f, tc = [], None
        if r.source == 'wikipedia' and r.labelled and r.start_week >= STUDY_START:
            if r.single_day is True or r.single_day == True:  # noqa: E712
                f.append('one_day')
            if r.desktop_rise is True or r.desktop_rise == True:  # noqa: E712
                f.append('desktop_only')
            if match_title(r.wiki_driver, r.start_week, bad):
                f.append('title_confusion'); tc = 'title_confusion'
            elif match_title(r.wiki_driver, r.start_week, ok):
                tc = 'ok'
        flags.append(','.join(f)); tcheck.append(tc)
    shifts['quality_flag'] = flags
    shifts['quality_ok'] = shifts.quality_flag == ''
    shifts['title_check'] = tcheck
    shifts['parent_node'] = shifts.node_id.map(parent_of(P))
    shifts = shifts.drop(columns=['single_day', 'desktop_rise', 'driver_has_verdict', 'max_top_day_share'], errors='ignore')
    shifts['gdelt_feed_artifact'] = shifts.gdelt_feed_artifact.astype(object)
    for c in ('id',):
        shifts[c] = shifts[c].astype('int64')
    ref_cols = list(pd.read_parquet(P.interest / 'shifts.parquet').columns) if (P.interest / 'shifts.parquet').exists() else []
    cols = [c for c in ref_cols if c in shifts.columns] + [c for c in shifts.columns if c not in ref_cols]
    shifts = shifts[cols]
    IO.save_parquet(shifts, P.shifts_value)
    sha = hashlib.sha256(P.shifts_value.read_bytes()).hexdigest()
    L = report(shifts, Q, GQ, qinfo, n_chk, worst, sha, wk, gd)
    meta = IO.load_meta(P) if P.meta.exists() else {'build_id': 'n/a', 'taxonomy': 'n/a'}
    meta = dict(meta, build_id='n/a')           # interest only: independent of the demand panel build
    path = IO.write_report(P, '02', 'Study 3b value-level interest shifts (interest data only)', L, S, meta,
                           extra={'shifts_value file SHA-256': f'`{sha}`'})
    log('\n'.join(L))
    log('report:', path)


def parent_of(P):
    f = P.categories
    if f.exists():
        c = pd.read_parquet(f)
        return dict(zip(c[c.level == 'value'].node_id, c[c.level == 'value'].parent))
    return {}


def report(shifts, Q, GQ, qinfo, n_chk, worst, sha, wk, gd):
    s = shifts
    t = s[s.labelled & (s.start_week >= STUDY_START)]
    L = ['## What was done',
         f'- value series: Wikipedia {wk.value.nunique()}, GDELT {gd.value.nunique()} (files weekly_value.parquet of the interest side)',
         f'- Wikipedia value series recomputed from the daily page views for {n_chk} values; largest relative difference to the stored weekly views {worst:.2e}',
         f'- thresholds from the record (Study 3, addenda d and h): normal level {S.normal_weeks} weeks, large size >= {S.large_ratio}, sustained >= {S.sustained_min}, '
         f'intermediate == {S.intermediate_eq}, fading <= {S.fading_max} weeks; GDELT durations ratio {S.gdelt_durations["values"]["ratio"]}',
         '', '## Shifts', f'- all value-level shifts found: {len(s)}; labelled (sustained, intermediate or fading): {int(s.labelled.sum())}; '
         f'labelled and from {S.study_start}: {len(t)}']
    L += IO.md_table(s.groupby(['source', 'label']).size().rename('shifts').reset_index())
    L += ['', '## Tested set (labelled, from 2017-01) by source and quality']
    rows = []
    for src, g in t.groupby('source'):
        main = g[~g.seasonal.fillna(False).astype(bool)]
        rows.append(dict(source=src, labelled_from_2017=len(g), seasonal=int(g.seasonal.fillna(False).astype(bool).sum()), main_set=len(main),
                         main_quality_ok=int(main.quality_ok.sum()), all_quality_ok=int(g.quality_ok.sum()), large_main=int(main.large.sum())))
    L += IO.md_table(pd.DataFrame(rows))
    w = t[t.source == 'wikipedia']
    flags = {k: int(w.quality_flag.str.contains(k).sum()) for k in ('one_day', 'desktop_only', 'title_confusion')}
    L += ['', '## Quality flags (Wikipedia, tested set)', f'- flags: {flags}; flagged in total {int((~w.quality_ok).sum())} of {len(w)}',
          f'- desktop check: {qinfo["checked"]} shifts examined; cached answers of the interest side used {qinfo["cache_hits_old"]}, own cache {qinfo["cache_hits_new"]}, new requests {qinfo["requests"]}',
          f'- Wikipedia shifts without any desktop answer (desktop_only not screened): {qinfo["no_desktop"]}']
    unscr = w[w.title_check.isna()]
    L += [f'- title confusion: verdict found for the same page and week on {int(w.title_check.notna().sum())} shifts '
          f'({int((w.title_check == "title_confusion").sum())} title_confusion, {int((w.title_check == "ok").sum())} ok); NOT screened (no verdict for the page): {len(unscr)} '
          f'of {len(w)} ({int(unscr.large.sum())} of them large)']
    g_ = t[t.source == 'gdelt']
    L += ['', '## GDELT (tested set)', f'- shifts {len(g_)}; single-site check available for {int(g_.gdelt_feed_artifact.notna().sum())}, flagged single_site {int((g_.gdelt_feed_artifact == True).sum())}; '  # noqa: E712
          f'not screened (no sampled URL list for the driver code and day): {int(g_.gdelt_feed_artifact.isna().sum())}',
          f'- driver code without a hand verdict on figurative use (not checked, no new hand check): {int((~g_.merge(GQ[["node_id", "start_week", "driver_has_verdict"]], on=["node_id", "start_week"], how="left").driver_has_verdict.fillna(False).astype(bool)).sum())}']
    L += ['', '## NOT IN RECORD (interest side, value level)',
          '- value level is level 4 in the table; node_id holds the value, parent_node its placed node',
          '- title_confusion verdicts matched on the same page and a start week within 2 weeks; shifts without a verdict stay unscreened',
          '- desktop_only and one_day computed only for labelled shifts from 2017-01 (the tested set); others get no flag',
          '- single_site only where a URL sample exists for the driver code and day; no new URL samples were drawn',
          '- GDELT quality_ok carries only the single_site flag (as for nodes)',
          '', f'- shifts_value.parquet SHA-256: `{sha}`']
    return L


if __name__ == '__main__':
    main()
