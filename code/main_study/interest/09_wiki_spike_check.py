# 09. Data-quality flags for Wikipedia shifts (descriptive; labels are not changed).
# Wikipedia "user" views still contain some automated traffic, and a page can spike for an unrelated reason (a TV series
# with the same title). For every Wikipedia shift at the tested levels:
#   driver article  = the node article with the largest rise over the first weeks of the shift (start to week 4 or the end)
#                     against its median week in the 26 weeks before the start;
#   single_day      = in some of those weeks one day carried >= 50% of the node's weekly views;
#   desktop_rise    = the driver's rise came almost only from desktop (>= 90%, and >= 25 points above its usual desktop
#                     share), a common sign of automated traffic labelled as user. Desktop views come from the official
#                     per-article API (access=desktop, agent=user), one request per shift, cached.
# A shift with either flag is "suspect". The report lists them; whether to drop suspect shifts is a decision for the student.
# Set SKIP_API=1 to use cached answers only. Output: data/db/interest/wiki/shift_quality.parquet
import os, json, hashlib, urllib.parse, functools, numpy as np, pandas as pd
from _ci import OUT, WK, load_taxonomy, ancestors, polite_get, save_json, save_parquet

REST = 'https://wikimedia.org/api/rest_v1/metrics/pageviews'
SINGLE_DAY, DESK_RISE, DESK_GAP = 0.5, 0.9, 0.25
SH = pd.read_parquet(f'{OUT}/shifts.parquet')
SH = SH[(SH.source == 'wikipedia') & SH.level.isin([2, 3])].copy()
WN = pd.read_parquet(f'{WK}/weekly_node.parquet')
A = pd.read_parquet(f'{WK}/articles.parquet')
V, _ = load_taxonomy()
node_art = {}
for t, nid in zip(V.theme, V.node_id):
    for a in ancestors(nid):
        node_art.setdefault(a, set()).update(A[A.theme == t].canonical.dropna())


@functools.lru_cache(maxsize=None)
def daily(title):
    d = pd.read_parquet(f'{WK}/pv_daily/{hashlib.sha1(title.encode()).hexdigest()[:16]}.parquet')
    return d.set_index('date').views


cache_f = f'{WK}/_desktop_cache.json'
cache = json.load(open(cache_f)) if os.path.exists(cache_f) else {}
skip_api = bool(os.environ.get('SKIP_API'))
rows = []
for i, r in enumerate(SH.itertuples()):
    n_w = int(min(max(r.whole_duration, 1), 4))
    a = r.start_week; b = a + pd.Timedelta(days=7 * n_w - 1)
    base_a = a - pd.Timedelta(weeks=26)
    best, rises = None, {}
    for t in node_art.get(r.node_id, []):
        s = daily(t)
        base = s[base_a:a - pd.Timedelta(days=1)].reindex(pd.date_range(base_a, a - pd.Timedelta(days=1)), fill_value=0)
        win = s[a:b].reindex(pd.date_range(a, b), fill_value=0)
        rises[t] = win.sum() - base.median() * len(win)
    pos = {k: v for k, v in rises.items() if v > 0}
    driver = max(rises, key=rises.get) if rises else None
    wk = WN[(WN.node_id == r.node_id) & WN.week.between(a, b)]
    out = dict(source='wikipedia', level=r.level, node_id=r.node_id, start_week=r.start_week, driver=driver,
               driver_share_of_rise=(pos.get(driver, 0) / sum(pos.values())) if pos else np.nan,
               max_top_day_share=float(wk.top_day_share.max()) if len(wk) else np.nan)
    if driver:
        key = f'{driver}|{base_a.date()}|{b.date()}'
        if key not in cache and not skip_api:
            t = urllib.parse.quote(driver.replace(' ', '_'), safe='')
            resp = polite_get(f'{REST}/per-article/en.wikipedia/desktop/user/{t}/daily/{base_a:%Y%m%d}00/{b:%Y%m%d}00')
            if resp is not None:
                cache[key] = {} if resp.status_code == 404 else {x['timestamp'][:8]: x['views'] for x in resp.json().get('items', [])}
        if key in cache:
            dk = pd.Series({pd.Timestamp(k): v for k, v in cache[key].items()}, dtype=float).reindex(pd.date_range(base_a, b), fill_value=0)
            al = daily(driver).reindex(pd.date_range(base_a, b), fill_value=0)
            bd, ba = dk[:a - pd.Timedelta(days=1)], al[:a - pd.Timedelta(days=1)]
            wd, wa = dk[a:], al[a:]
            rise_d = wd.sum() - bd.median() * len(wd); rise_a = wa.sum() - ba.median() * len(wa)
            out.update(desktop_share_base=float(bd.sum() / ba.sum()) if ba.sum() else np.nan,
                       desktop_share_rise=float(rise_d / rise_a) if rise_a > 0 else np.nan)
    rows.append(out)
    if (i + 1) % 100 == 0:
        save_json(cache, cache_f); print('shifts checked', i + 1, flush=True)
save_json(cache, cache_f)
Q = pd.DataFrame(rows)
Q['single_day'] = Q.max_top_day_share >= SINGLE_DAY
Q['desktop_rise'] = (Q.desktop_share_rise >= DESK_RISE) & ((Q.desktop_share_rise - Q.desktop_share_base) >= DESK_GAP)
Q['suspect'] = Q.single_day | Q.desktop_rise
save_parquet(Q, f'{WK}/shift_quality.parquet')
print('Wikipedia shifts checked', len(Q), '| single-day', int(Q.single_day.sum()), '| desktop-only rise', int(Q.desktop_rise.sum()),
      '| suspect', int(Q.suspect.sum()), '| without desktop data', int(Q.desktop_share_rise.isna().sum()))
