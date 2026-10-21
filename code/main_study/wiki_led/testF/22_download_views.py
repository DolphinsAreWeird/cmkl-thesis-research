#!/usr/bin/env python3
"""Test F, step 22: download the full daily user views of the S2 pages; with --desktop, the desktop check of the pages that drive each rise.

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (theme_attention_series.S2_full): Wikimedia REST per-article views,
all-access, user agent, 2015-07-01 to 2026-09-30, at most 3 requests a second, one downloader at a time. Nothing here reads loans.
Pages: universe pages with at least one theme of confidence 2 or 3 in assign_pages.parquet (step 20); if more than 40,000, the 40,000 with
the most top-500 days (ties: more top-500 views, then title). The script may be run while the sorting is still going on: it fetches the
pages selected from the answers parsed so far, most top-500 days first, and a rerun after step 20 adds the new ones (pages already in the
store are never fetched again).
HTTP: the Http class of ../_common.py (project user agent from code/config.py, a shared gap between requests over all threads, Retry-After
honoured, growing pauses after a 429 or 5xx, the gap growing after a 429 and shrinking back after 60 successes). Gap 0.34 s over 4
threads = at most 2.94 requests a second (the addendum's limit is 3 a second; a 0.30 s gap would allow 3.33). A day missing from an
answer counts as 0 views (as in interest/07_wiki_series.py); a title with no data (404) or an invalid title (400) is stored as zeros with
its status.
Store: the views of each batch of 500 pages go into one compressed file batch_<time>_<n>.npz (titles, views int32 pages x 4,110 days,
status) in data/interim/testF_views/ (a mock world: its views_store/); the per-request cache files of a batch are deleted once the batch
file is written, so a stop loses at most the pages of the current batch (they come back from the cache on the rerun).
Refusal: the script stops while any other job whose name contains 'wiki' is RUNNING in bash jobs/status.sh (one Wikimedia downloader at
a time); it never counts itself.
--desktop S1|S2: for every rise of shift_drivers_<S>.parquet (written by 24_G2_matchmaking.py --stage shifts), the desktop and the
all-access user views of the driver page over its window (26 weeks before the start to the end of the first weeks), two requests per
rise, cached; output desktop_<S>.parquet (the 'desktop_only' quality flag of Chapter 6, interest/09_wiki_spike_check.py).
Run from handoff/ (detached):  bash jobs/bg.sh testF_s2_views main_study/wiki_led/testF/22_download_views.py --job-name testF_s2_views
Expected time: about 3 hours 50 minutes for 40,000 pages (2.9 requests a second); the desktop check about 2 requests per rise.
Options: --limit N (first N pages only, for tests), --root DIR, --job-name NAME (the bg.sh name, never counted as another job).
"""
import sys, os, json, time, hashlib, pathlib, argparse, threading, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd
import _testf_analysis as T
sys.path.insert(0, str(T.HERE.parent))                       # code/main_study/wiki_led (for _common.Http)
import _common as C                                           # noqa: E402

REST = 'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/{access}/user/{title}/daily/{a}/{b}'
GAP, THREADS, BATCH = 0.34, 4, 500
CACHE = T.D / 'interim' / 'testF_views_cache'


class Http(C.Http):
    """The Http class of ../_common.py with its own cache folder (deleted batch by batch for the full-period requests)."""

    @staticmethod
    def path(url, params):
        key = json.dumps([url, sorted((params or {}).items())], sort_keys=True)
        h = hashlib.sha1(key.encode()).hexdigest()
        return CACHE / 'http' / h[:2] / (h + '.json.gz')


def url_of(title, access, a, b):
    return REST.format(access=access, title=urllib.parse.quote(title, safe=''), a=a.strftime('%Y%m%d') + '00', b=b.strftime('%Y%m%d') + '00')


DAYIDX = {d.strftime('%Y%m%d'): i for i, d in enumerate(T.DAYS)}


def parse_daily(text, d0, n):
    """Views per day from d0 (n days); days absent from the answer are 0."""
    v = np.zeros(n, dtype=np.int64)
    if not text:
        return v
    off = DAYIDX.get(d0.strftime('%Y%m%d'))
    for it in json.loads(text).get('items', []):
        s = it['timestamp'][:8]
        k = DAYIDX.get(s)
        k = (pd.Timestamp(s) - d0).days if (k is None or off is None) else k - off
        if 0 <= k < n:
            v[k] += int(it['views'])
    return v


def refuse_if_busy(job_name):
    busy = T.running_wiki_jobs(exclude_names=(job_name,) if job_name else ())
    if busy:
        raise SystemExit('another Wikimedia job is running (' + ', '.join(busy) + '); one downloader at a time. Nothing was fetched.')


def full_period(P, a, H):
    A = T.read_assign(P, 'pages')
    sel = T.s2_selection(A, T.top_days_count())
    if a.series == 'S2C':                                         # addendum h: every concept page with a theme of confidence 2 or 3, no cap
        c = T.s2c_titles(A)
        sel = pd.DataFrame({'title': sorted(c)}).assign(selected=True)
    want = sel[sel.selected]
    have = set(T.store_index(P).title)
    todo = [t for t in want.title if t not in have]
    if a.limit:
        todo = todo[:a.limit]
    T.log(f'S2 pages: {len(sel):,} with a theme of confidence 2 or 3 (universe); selected {len(want):,} (cap {T.S2_MAX_PAGES:,}); '
          f'already stored {len(want) - len([t for t in want.title if t not in have]):,}; to fetch now {len(todo):,}; '
          f'about {len(todo) * GAP / 3600:.1f} h at {1 / GAP:.2f} requests a second')
    n = len(T.DAYS)
    t0 = time.time()

    def one(title):
        u = url_of(title, 'all-access', T.DAY0, T.DAY1)
        st, text = H.get('wm', u, soft=(400,))
        return title, st, parse_daily(text, T.DAY0, n), u

    done = 0
    with ThreadPoolExecutor(THREADS) as ex:
        for i in range(0, len(todo), BATCH):
            chunk = todo[i:i + BATCH]
            res = list(ex.map(one, chunk))
            V = np.vstack([r[2] for r in res])
            if V.max(initial=0) > np.iinfo(np.int32).max:
                raise SystemExit('a daily count does not fit int32')
            f = P.views / f'batch_{time.strftime("%Y%m%d%H%M%S")}_{i // BATCH:04d}.npz'
            tmp = f.with_suffix('.tmp.npz')
            np.savez_compressed(tmp, titles=np.array([r[0] for r in res]), views=V.astype(np.int32), status=np.array([r[1] for r in res], dtype=np.int16))
            os.replace(tmp, f)
            for r in res:                                           # the batch file holds the data now: drop the per-request cache files
                try:
                    Http.path(r[3], None).unlink()
                except FileNotFoundError:
                    pass
            done += len(chunk)
            el = time.time() - t0
            rate = H.n_net / max(el, 1e-9)
            T.log(f'{done:,}/{len(todo):,} pages ({el / 60:.1f} min, {rate:.2f} network requests a second, ETA '
                  f'{(len(todo) - done) / max(done / max(el, 1e-9), 1e-9) / 60:.0f} min); statuses {H.codes}; back-offs {H.n_backoff}')
    idx = T.store_index(P)
    st = idx[idx.title.isin(set(want.title))].status.value_counts().to_dict()
    T.write_json(dict(selected=len(want), stored=int(idx.title.isin(set(want.title)).sum()), status=st, http_codes={str(k): v for k, v in H.codes.items()},
                      backoffs=H.n_backoff, network=H.n_net, cache=H.n_cache, gap_s=GAP, threads=THREADS, finished=time.strftime('%Y-%m-%d %H:%M:%S'),
                      limit=a.limit), P / ('s2c_download_summary.json' if a.series == 'S2C' else 's2_download_summary.json'))
    T.log(f'store now holds {int(idx.title.isin(set(want.title)).sum()):,} of {len(want):,} selected pages; statuses {st}')


def desktop(P, a, H):
    f = P / f'shift_drivers_{a.desktop}.parquet'
    if not f.exists():
        raise SystemExit(f'{f.name} not found: run 24_G2_matchmaking.py --series {a.desktop} --stage shifts first')
    R = pd.read_parquet(f)
    R = R[R.driver.notna()].drop_duplicates(['driver', 'base_a', 'b'])
    if a.limit:
        R = R.head(a.limit)
    T.log(f'desktop check: {len(R):,} driver windows, {2 * len(R):,} requests, about {2 * len(R) * GAP / 60:.0f} min')
    rows = []
    lock = threading.Lock()

    def one(r):
        a_, b_ = pd.Timestamp(r.base_a), pd.Timestamp(r.b)
        n = (b_ - a_).days + 1
        out = {}
        for acc in ('desktop', 'all-access'):
            st, text = H.get('wm', url_of(r.driver, acc, a_, b_), soft=(400,))
            out[acc] = (st, parse_daily(text, a_, n))
        dates = pd.date_range(a_, b_)
        with lock:
            for k, d in enumerate(dates):
                rows.append((r.driver, a_, b_, d, int(out['desktop'][1][k]), int(out['all-access'][1][k]), out['desktop'][0], out['all-access'][0]))

    with ThreadPoolExecutor(THREADS) as ex:
        list(ex.map(one, list(R.itertuples(index=False))))
    O = pd.DataFrame(rows, columns=['driver', 'base_a', 'b', 'date', 'desktop', 'all_access', 'status_desktop', 'status_all'])
    T.write_parquet(O, P / f'desktop_{a.desktop}.parquet')
    T.log(f'wrote desktop_{a.desktop}.parquet ({len(O):,} driver-days); statuses {H.codes}')


def main():
    ap = T.add_root_arg(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--job-name', default=None)
    ap.add_argument('--desktop', choices=['S1', 'S2', 'S2C'], default=None)
    ap.add_argument('--series', choices=['S2', 'S2C'], default='S2', help='S2C: the concept pages of addendum h')
    a = ap.parse_args()
    P = T.Paths(a.root)
    refuse_if_busy(a.job_name)
    T.be_nice(5)
    H = Http({'wm': GAP}, adaptive=('wm',), recover=True)
    T.log(f'{P.tag()}; store {P.views}; gap {GAP}s over {THREADS} threads')
    if a.desktop:
        desktop(P, a, H)
    else:
        full_period(P, a, H)
    T.log(f'network requests {H.n_net:,}, from cache {H.n_cache:,}, back-offs {H.n_backoff}; peak memory {T.peak_gb():.2f} GB')


if __name__ == '__main__':
    main()
