# 11. Final quality flags on the shifts, the title-confusion check, and the GDELT duration scaling (decisions of 13 Oct 2026).
# quality_flag (text): '' when clean, otherwise one or more of 'one_day', 'desktop_only', 'title_confusion', comma separated.
#   one_day and desktop_only come from 09 as they are (Wikipedia shifts at the tested levels; not tuned).
#   title_confusion comes from a hand check (_title_confusion.py) of every large Wikipedia shift in the main set and of the
#   50 largest other Wikipedia main-set shifts by size: the page(s) carrying the rise and the peak day are looked up, with
#   same-named pages (a TV series, film, game, song or person) that were in the English Wikipedia daily top-500 list on the
#   peak day or the days around it (data/raw/wiki_top_daily.json). Each verdict has a one-line reason.
# quality_ok (bool): True when quality_flag is ''. GDELT shifts get no automatic flag (quality_flag '').
# gdelt_feed_artifact (descriptive, not part of quality_ok): True when a URL sample of the driver code on the shift's start
#   week has at least half of its URLs from one website (gdelt/figurative_url_samples.csv); empty when not sampled.
# GDELT duration scaling (the record's rule) is computed here on the final shifts: main set and quality_ok.
# Outputs: shifts.parquet (columns added), wiki/review_title_confusion.csv, gdelt_duration_scaling.json
import json, re, os, hashlib, functools, numpy as np, pandas as pd
from collections import Counter
from _ci import D, OUT, WK, GD, settings, load_taxonomy, ancestors, save_parquet, save_json
import _shifts as SH_
import _title_confusion as TC

S = settings()
SH = pd.read_parquet(f'{OUT}/shifts.parquet')
for c in ['quality_flag', 'quality_ok', 'gdelt_feed_artifact', 'title_check', 'title_note', 'wiki_driver', 'gdelt_driver']:
    SH = SH.drop(columns=c, errors='ignore')
Q = pd.read_parquet(f'{WK}/shift_quality.parquet')[['source', 'level', 'node_id', 'start_week', 'single_day', 'desktop_rise', 'driver']]
SH = SH.merge(Q, on=['source', 'level', 'node_id', 'start_week'], how='left')

# ---------------- title-confusion check set and evidence ----------------
W = SH[(SH.source == 'wikipedia') & SH.main_set].copy()
check = pd.concat([W[W.large], W[~W.large].sort_values('size', ascending=False).head(50)])
A = pd.read_parquet(f'{WK}/articles.parquet')
V, _ = load_taxonomy()
node_art = {}
for t, nid in zip(V.theme, V.node_id):
    for a in ancestors(nid):
        node_art.setdefault(a, set()).update(A[A.theme == t].canonical.dropna())
RD = pd.read_parquet(f'{WK}/redirects.parquet')
redirs = RD.groupby('canonical').redirect.apply(set).to_dict()


@functools.lru_cache(maxsize=None)
def daily(title):
    d = pd.read_parquet(f'{WK}/pv_daily/{hashlib.sha1(title.encode()).hexdigest()[:16]}.parquet')
    return d.set_index('date').views


SCR = pd.read_parquet(f'{WK}/redirect_screen.parquet')
kept = SCR[SCR.keep == True].groupby('canonical').redirect.apply(list).to_dict()  # noqa: E712


@functools.lru_cache(maxsize=None)
def daily_full(title):
    """page views plus its kept redirects, as in the weekly series (07)"""
    s = daily(title)
    for x in kept.get(title, []):
        s = s.add(daily(x), fill_value=0)
    return s


top = json.load(open(f'{D}/raw/wiki_top_daily.json'))


def norm(t):
    return re.sub(r'\s+', ' ', re.sub(r'\(.*?\)', '', t.replace('_', ' '))).strip().lower()


rows = []
for r in check.itertuples():
    n_w = int(min(max(r.whole_duration, 1), 4)); a = r.start_week; b = a + pd.Timedelta(days=7 * n_w - 1)
    base_a = a - pd.Timedelta(weeks=26)
    rises = {}
    def rise(s):
        base = s[base_a:a - pd.Timedelta(days=1)].reindex(pd.date_range(base_a, a - pd.Timedelta(days=1)), fill_value=0)
        win = s[a:b].reindex(pd.date_range(a, b), fill_value=0)
        return win.sum() - base.median() * len(win)
    for t in node_art.get(r.node_id, []):
        rises[t] = rise(daily_full(t))
    pos = {k: v for k, v in rises.items() if v > 0}
    tot = sum(pos.values()) or 1
    pages = sorted(pos, key=pos.get, reverse=True)[:2]
    ev = []
    for p in pages:
        s = daily_full(p)[a:b]
        peak = s.idxmax() if len(s) else a
        base = daily_full(p)[base_a:a - pd.Timedelta(days=1)].median()
        rr = {x: rise(daily(x)) for x in kept.get(p, [])}
        via = max(rr, key=rr.get) if rr else None
        via_txt = f', {rr[via] / pos[p]:.0%} of it through the redirect "{via}"' if via and rr[via] > 0.3 * pos[p] else ''
        key = norm(p)
        own = {x.replace('_', ' ').lower() for x in redirs.get(p, set()) | {p}}        # the page itself and its redirects, exact titles
        hits, rank = [], None
        for d in [peak - pd.Timedelta(days=1), peak, peak + pd.Timedelta(days=1)]:
            for k, (title, views) in enumerate(top.get(d.strftime('%Y%m%d'), [])):
                nt = norm(title)
                if title.replace('_', ' ').lower() in own:
                    rank = k + 1 if d == peak else rank
                    continue
                if re.search(r'\b' + re.escape(key) + r'\b', nt) and title not in [h[0] for h in hits]:
                    hits.append((title, views, d.strftime('%m-%d')))
        hits = sorted(hits, key=lambda h: -h[1])[:5]
        ev.append(f"{p} {pos[p] / tot:.0%} of rise{via_txt}, peak {peak.date()} ({int(s.max()) if len(s) else 0:,} views vs usual {int(base):,}/day"
                  f"{', top-500 rank ' + str(rank) if rank else ''})" +
                  (f"; same-named pages in top 500: " + '; '.join(f"{h[0]} {h[1]:,} ({h[2]})" for h in hits) if hits else ''))
    key = (r.node_id, str(r.start_week.date()))
    v = TC.VERDICTS.get(key)
    rows.append(dict(node_id=r.node_id, node_label=r.node_label, level=r.level, start_week=r.start_week.date(), size=round(r.size, 2),
                     large=r.large, label=r.label, evidence=' || '.join(ev), verdict=v[0] if v else None, reason=v[1] if v else None,
                     auto_flags=','.join(x for x, y in [('one_day', r.single_day), ('desktop_only', r.desktop_rise)] if y is True)))
RV = pd.DataFrame(rows)
RV.to_csv(f'{WK}/review_title_confusion.csv', index=False)
todo = RV[RV.verdict.isna()]
stale = [k for k in TC.VERDICTS if k not in set(zip(RV.node_id, RV.start_week.astype(str)))]
print('title-confusion check: shifts', len(RV), '| without verdict', len(todo), '| title_confusion', int((RV.verdict == 'title_confusion').sum()),
      '| verdicts no longer matching a checked shift', stale)

# ---------------- quality columns ----------------
tc = {(k[0], pd.Timestamp(k[1])): v for k, v in TC.VERDICTS.items()}
flags = []
for r in SH.itertuples():
    f = []
    if r.source == 'wikipedia':
        if r.single_day is True:
            f.append('one_day')
        if r.desktop_rise is True:
            f.append('desktop_only')
        if tc.get((r.node_id, r.start_week), ('',))[0] == 'title_confusion':
            f.append('title_confusion')
    flags.append(','.join(f))
SH['quality_flag'] = flags
SH['quality_ok'] = SH.quality_flag == ''
SH['title_check'] = [tc.get((n, s), (None,))[0] for n, s in zip(SH.node_id, SH.start_week)]

# GDELT feed artefact (descriptive): URL sample of the driver code on the start week has >= half of its URLs from one site
DRV = pd.read_csv(f'{GD}/driver_codes.csv', parse_dates=['start_week'])
SH = SH.merge(DRV[['level', 'node_id', 'start_week', 'driver']].rename(columns={'driver': 'gdelt_driver'}).assign(source='gdelt'),
              on=['source', 'level', 'node_id', 'start_week'], how='left')
US = pd.read_csv(f'{GD}/figurative_url_samples.csv') if os.path.exists(f'{GD}/figurative_url_samples.csv') else pd.DataFrame(columns=['code', 'day', 'urls'])


def top_site_share(urls):
    doms = [re.sub(r'^https?://(www\.)?([^/]+).*$', r'\2', u) for u in json.loads(urls)]
    return Counter(doms).most_common(1)[0][1] / len(doms) if doms else np.nan


US['top_site_share'] = US.urls.map(top_site_share)
share = dict(zip(zip(US.code, US.day), US.top_site_share))
SH['gdelt_feed_artifact'] = [None if (s != 'gdelt' or not isinstance(d, str)) else
                             (None if (d, str((w + pd.Timedelta(days=2)).date())) not in share else share[(d, str((w + pd.Timedelta(days=2)).date()))] >= 0.5)
                             for s, d, w in zip(SH.source, SH.gdelt_driver, SH.start_week)]
SH = SH.drop(columns=['single_day', 'desktop_rise']).rename(columns={'driver': 'wiki_driver'})
save_parquet(SH, f'{OUT}/shifts.parquet')

# ---------------- GDELT duration scaling on the final shifts ----------------
OV = (pd.Timestamp('2017-01-02'), pd.Timestamp('2021-06-21'))
fin = SH[SH.main_set & SH.quality_ok]
scal = {}
for name, sel in [('final: main set and quality_ok, Jul 2017 to Jun 2021', fin[fin.start_week.between(*OV)]),
                  ('final, Wikipedia all years', fin), ('all completed non-seasonal shifts, Jul 2017 to Jun 2021 (earlier definition)',
                   SH[SH.tested_level & ~SH.seasonal & (SH.label != 'censored') & SH.start_week.between(*OV)])]:
    g = sel[sel.source == 'gdelt'].whole_duration; w = sel[sel.source == 'wikipedia'].whole_duration
    if name == 'final, Wikipedia all years':
        g = fin[(fin.source == 'gdelt') & fin.start_week.between(*OV)].whole_duration
    r = float(g.median() / w.median())
    th = SH_.thresholds(S, r)
    scal[name] = dict(gdelt_n=int(len(g)), gdelt_median=float(g.median()), gdelt_mean=round(float(g.mean()), 2),
                      wikipedia_n=int(len(w)), wikipedia_median=float(w.median()), wikipedia_mean=round(float(w.mean()), 2),
                      ratio_of_medians=r, ratio_of_means=round(float(g.mean() / w.mean()), 3),
                      scaled=dict(sustained_min=th['sustained_min'], label_week=th['label_week'],
                                  intermediate=list(range(th['fading_max'] + 1, th['sustained_min'])), fading_max=th['fading_max'],
                                  conflict_with_minimum_2=bool(th['conflict'])))
scal['proposed'] = 'final: main set and quality_ok, Jul 2017 to Jun 2021'
scal['computed_on'] = '2026-10-13'
scal['demand_data_read'] = False
save_json(scal, f'{OUT}/gdelt_duration_scaling.json')
p = scal[scal['proposed']]
same = p['scaled']['sustained_min'] == S['sustained_min'] and p['scaled']['fading_max'] == S['fading_max']
print('GDELT duration ratio (final shifts):', p['ratio_of_medians'], '| means', p['ratio_of_means'], '| scaled thresholds',
      p['scaled'], '| same as Wikipedia:', same)
if not same:
    print('WARNING: scaled GDELT thresholds differ from Wikipedia; GDELT labels must be recomputed with them')
m = SH[SH.main_set]
print('main set', m.groupby('source').size().to_dict(), '| quality_ok in main set', m[m.quality_ok].groupby('source').size().to_dict(),
      '| large in main set', m[m.large].groupby('source').size().to_dict(), '| large and quality_ok', m[m.large & m.quality_ok].groupby('source').size().to_dict())
print('quality flags in main set', m.quality_flag.value_counts().to_dict())
