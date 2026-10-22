#!/usr/bin/env python3
"""J1 of addendum j, downloader: the full daily user views of the selected book-linked pages that are not stored yet.

Settings: prereg/addenda_wiki_led/2026-10-22_j_combined_alerts.json, linked_page_attention (read-only): Wikimedia REST per-article, en.wikipedia,
all-access, user agent, daily, 2015-07-01 to 2026-09-30, at most 3 requests a second, one downloader at a time, pages already in the Test F store
reused.  Nothing here reads loans.
Pages: the selected pages of data/db/wiki_led/dirs/j_links/pages_wanted.parquet (j1_links.py --stage links; at most 30,000 by link type), in
their order (link type adaptation, subject, event_period, person, place, character, series; then pages linked to more works first), minus the
pages already in the Test F store (data/interim/testF_views/), in the adaptation views (data/db/wiki_led/adaptation_daily_views.parquet,
adaptation_fetch_status.parquet) or in this test's store.
Everything else is Test F's downloader (testF/22_download_views.py), whose functions are reused: its Http class (the Http class of ../_common.py:
project user agent from code/config.py, a shared gap between requests over all threads, Retry-After honoured, growing pauses after a 429 or 5xx,
the gap growing after a 429 and shrinking back after 60 successes), gap 0.34 s over 4 threads = at most 2.94 requests a second, url_of and
parse_daily (a day missing from an answer counts as 0 views; a 404 or an invalid title (400) is stored as zeros with its status), the refusal
while another job whose name contains 'wiki', 'view', 'text' or 'download' is running (one Wikimedia downloader at a time), batches of 500 pages
into one compressed file batch_<time>_<n>.npz (titles, views int32 pages x 4,110 days, status), the per-request cache files of a batch deleted
once the batch file is written.  Only the store and the cache folders differ: data/interim/j_linked_views/ and data/interim/j_linked_views_cache/.
Time rule of the record: no new batch is started after --until (default 2026-10-22 15:00 +07); the bursts are then built from the pages stored.
Run from handoff/ (detached):  bash jobs/bg.sh j_linked_views main_study/wiki_led/dirs/j1_download_views.py --job-name j_linked_views
Options: --limit N (first N pages only, for tests), --until 'YYYY-MM-DD HH:MM' (local time), --job-name NAME (the bg.sh name).
"""
import sys, os, json, time, hashlib, pathlib, argparse, importlib.util, datetime
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent                    # code/main_study/wiki_led/dirs
TESTF = HERE.parent / 'testF'
spec = importlib.util.spec_from_file_location('testf_22_download_views', TESTF / '22_download_views.py')
DL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(DL)                                         # defines only; its main() is not run
T = DL.T                                                            # _testf_analysis
D = T.D
WL = D / 'db' / 'wiki_led'
JL = WL / 'dirs' / 'j_links'
STORE = D / 'interim' / 'j_linked_views'
CACHE = D / 'interim' / 'j_linked_views_cache'
STORE.mkdir(parents=True, exist_ok=True)


class Http(DL.Http):
    """Test F's Http class with this test's own cache folder."""

    @staticmethod
    def path(url, params):
        key = json.dumps([url, sorted((params or {}).items())], sort_keys=True)
        h = hashlib.sha1(key.encode()).hexdigest()
        return CACHE / 'http' / h[:2] / (h + '.json.gz')


class StoreP:
    def __init__(self, views):
        self.views = views


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--job-name', default=None)
    ap.add_argument('--until', default='2026-10-22 15:00')
    a = ap.parse_args()
    until = datetime.datetime.strptime(a.until, '%Y-%m-%d %H:%M').timestamp()
    DL.refuse_if_busy(a.job_name)
    T.be_nice(5)
    PW = pd.read_parquet(JL / 'pages_wanted.parquet')
    want = PW[PW.selected].sort_values('order')
    haveF = set(T.store_index(StoreP(T.Paths().views)).title)
    haveA = set(pd.read_parquet(WL / 'adaptation_fetch_status.parquet', columns=['article']).article)
    haveO = set(T.store_index(StoreP(STORE)).title)
    todo = [t for t in want.page_title if t not in haveF and t not in haveA and t not in haveO]
    T.log(f'selected {len(want):,}; in the Test F store {int(want.page_title.isin(haveF).sum()):,}; in the adaptation views '
          f'{int((want.page_title.isin(haveA) & ~want.page_title.isin(haveF)).sum()):,}; in this store {int(want.page_title.isin(haveO).sum()):,}; '
          f'to fetch {len(todo):,} (about {len(todo) * DL.GAP / 3600:.1f} h at {1 / DL.GAP:.2f} requests a second); stop starting batches at {a.until}')
    if a.limit:
        todo = todo[:a.limit]
    H = Http({'wm': DL.GAP}, adaptive=('wm',), recover=True)
    n = len(T.DAYS)
    t0 = time.time()

    def one(title):
        u = DL.url_of(title, 'all-access', T.DAY0, T.DAY1)
        st, text = H.get('wm', u, soft=(400,))
        return title, st, DL.parse_daily(text, T.DAY0, n), u

    from concurrent.futures import ThreadPoolExecutor
    done = 0
    stopped = False
    with ThreadPoolExecutor(DL.THREADS) as ex:
        for i in range(0, len(todo), DL.BATCH):
            if time.time() >= until:
                stopped = True
                T.log(f'time rule: {a.until} reached; no new batch ({done:,} of {len(todo):,} fetched)')
                break
            chunk = todo[i:i + DL.BATCH]
            res = list(ex.map(one, chunk))
            V = np.vstack([r[2] for r in res])
            if V.max(initial=0) > np.iinfo(np.int32).max:
                raise SystemExit('a daily count does not fit int32')
            f = STORE / f'batch_{time.strftime("%Y%m%d%H%M%S")}_{i // DL.BATCH:04d}.npz'
            tmp = f.with_suffix('.tmp.npz')
            np.savez_compressed(tmp, titles=np.array([r[0] for r in res]), views=V.astype(np.int32), status=np.array([r[1] for r in res], dtype=np.int16))
            os.replace(tmp, f)
            for r in res:
                try:
                    Http.path(r[3], None).unlink()
                except FileNotFoundError:
                    pass
            done += len(chunk)
            el = time.time() - t0
            T.log(f'{done:,}/{len(todo):,} pages ({el / 60:.1f} min, {H.n_net / max(el, 1e-9):.2f} network requests a second, ETA '
                  f'{(len(todo) - done) / max(done / max(el, 1e-9), 1e-9) / 60:.0f} min); statuses {H.codes}; back-offs {H.n_backoff}')
    idx = T.store_index(StoreP(STORE))
    T.write_json(dict(selected=len(want), in_testF=int(want.page_title.isin(haveF).sum()), in_adaptation=int((want.page_title.isin(haveA) & ~want.page_title.isin(haveF)).sum()),
                      to_fetch=len(todo), fetched_now=done, own_store_total=len(idx), own_store_status={str(k): int(v) for k, v in idx.status.value_counts().items()},
                      stopped_by_time_rule=stopped, http_codes={str(k): v for k, v in H.codes.items()}, backoffs=H.n_backoff, network=H.n_net, cache=H.n_cache,
                      gap_s=DL.GAP, threads=DL.THREADS, finished=time.strftime('%Y-%m-%d %H:%M:%S'), limit=a.limit), JL / 'download_summary.json')
    T.log(f'network requests {H.n_net:,}, from cache {H.n_cache:,}, back-offs {H.n_backoff}; own store {len(idx):,} pages; peak memory {T.peak_gb():.2f} GB')


if __name__ == '__main__':
    main()
