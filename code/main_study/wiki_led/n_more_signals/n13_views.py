#!/usr/bin/env python3
"""n13. Addendum n, part 1, data for AD and LK: daily user views of every AD and LK page not already stored.  DATA ONLY: nothing is
related to loans.

Settings: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json (read-only; SHA-256 asserted), AD_film_and_TV_pages and
LK_linked_pages: daily user views 2015-07-01 to 2026-09-30, Wikimedia per-article service, at most 3 requests a second, one downloader at
a time, pages already stored reused.  Choices the record leaves open, decided 2026-11-25 16:47 +07:00 (09:47 UTC) before this was written
or run, also in data/db/wiki_led/n_more_signals/notes_ad_lk.md:
  V1 Pages: every distinct page of pages_AD.parquet and pages_LK.parquet (n12).  Request: REST per-article, en.wikipedia, all-access,
     agent user, daily, 2015-07-01 to 2026-09-30.  A day missing from an answer counts as 0 views.
  V2 Stores reused, in this order (same request; a page found in one is not looked up in the next): (1) Test F's store
     data/interim/testF_views/ (store_index); (2) data/db/wiki_led/adaptation_daily_views.parquet with adaptation_fetch_status.parquet;
     (3) addendum j's store data/interim/j_linked_views/; (4) data/db/study2r/pv_daily/ (one parquet per title, named by the SHA-1 of the
     title with spaces; the title inside is checked by n14; an empty file is a page with no data); (5) this test's own store
     data/interim/n_views/.
  V3 Download of the rest with Test F's downloader functions (testF/22_download_views.py: url_of, parse_daily, its Http class with the
     cache folder data/interim/n_views_cache/, gap 0.34 s over 4 threads = at most 2.94 requests a second, slower after a 429 or 5xx),
     its refusal while another job with 'wiki', 'view', 'text' or 'download' in its name is running, batches of 500 pages into one
     compressed file batch_<time>_<n>.npz (titles, views int32 pages x 4,110 days, status); 404 or 400 stored as zeros with the status.
     Order: AD pages first, then LK pages, each by number of works linked (more first), then title.  Resumable.  No page cap.
  V4 Output data/db/wiki_led/n_more_signals/views_index.parquet: page, source, status, in_AD, in_LK; n13_summary.json.
Run from handoff/ (detached):  bash jobs/bg.sh n13_views_wiki main_study/wiki_led/n_more_signals/n13_views.py --job-name n13_views_wiki
Options: --limit N (first N pages to fetch only, for a test), --index-only (no download; write the index from the stores).
"""
import sys, os, json, time, hashlib, pathlib, argparse, importlib.util
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent                    # code/main_study/wiki_led/n_more_signals
TESTF = HERE.parent / 'testF'
spec = importlib.util.spec_from_file_location('testf_22_download_views', TESTF / '22_download_views.py')
DL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(DL)                                         # defines only; its main() is not run
T = DL.T                                                            # _testf_analysis
D = T.D
ROOT = D.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
WL = D / 'db' / 'wiki_led'
OUT = WL / 'n_more_signals'
STORE = D / 'interim' / 'n_views'
CACHE = D / 'interim' / 'n_views_cache'
J_STORE = D / 'interim' / 'j_linked_views'
PV = D / 'db' / 'study2r' / 'pv_daily'
STORE.mkdir(parents=True, exist_ok=True)
fid = lambda t: hashlib.sha1(t.encode()).hexdigest()[:16]          # study2r/03_pageviews.py


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


def pages_wanted():
    AD = pd.read_parquet(OUT / 'pages_AD.parquet', columns=['work_id', 'page'])
    LK = pd.read_parquet(OUT / 'pages_LK.parquet', columns=['work_id', 'page'])
    a = AD.groupby('page').work_id.nunique().rename('n').reset_index().assign(grp=0)
    l = LK.groupby('page').work_id.nunique().rename('n').reset_index().assign(grp=1)
    l = l[~l.page.isin(set(a.page))]
    P = pd.concat([a, l], ignore_index=True).sort_values(['grp', 'n', 'page'], ascending=[True, False, True]).reset_index(drop=True)
    P['in_AD'] = P.page.isin(set(AD.page))
    P['in_LK'] = P.page.isin(set(LK.page))
    return P


def locate(pages):
    """page -> (source, status) from the stores of V2; pages in none are missing from the result."""
    found = {}
    idxF = T.store_index(StoreP(T.Paths().views))
    for t, st in zip(idxF.title, idxF.status):
        if t in pages and t not in found:
            found[t] = ('testF', int(st))
    AS = pd.read_parquet(WL / 'adaptation_fetch_status.parquet', columns=['article', 'status'])
    for t, st in zip(AS.article, AS.status):
        if t in pages and t not in found:
            found[t] = ('adaptation', int(st))
    if J_STORE.exists():
        idxJ = T.store_index(StoreP(J_STORE))
        for t, st in zip(idxJ.title, idxJ.status):
            if t in pages and t not in found:
                found[t] = ('j', int(st))
    for t in pages:
        if t in found:
            continue
        f = PV / f'{fid(t.replace("_", " "))}.parquet'
        if f.exists():
            n = pd.read_parquet(f, columns=['views']).shape[0]
            found[t] = ('study2r', 200 if n else 404)
    idxO = T.store_index(StoreP(STORE))
    for t, st in zip(idxO.title, idxO.status):
        if t in pages and t not in found:
            found[t] = ('n13', int(st))
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--job-name', default=None)
    ap.add_argument('--index-only', action='store_true')
    a = ap.parse_args()
    T.be_nice(5)
    P = pages_wanted()
    pages = set(P.page)
    found = locate(pages)
    todo = [t for t in P.page if t not in found]
    by_src = pd.Series([v[0] for v in found.values()]).value_counts().to_dict()
    T.log(f'pages {len(P):,} (AD {int(P.in_AD.sum()):,}, LK {int(P.in_LK.sum()):,}); stored {len(found):,} {by_src}; to fetch {len(todo):,} '
          f'(about {len(todo) * DL.GAP / 3600:.2f} h at {1 / DL.GAP:.2f} requests a second)')
    done = 0
    H = None
    if todo and not a.index_only:
        DL.refuse_if_busy(a.job_name)
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
        with ThreadPoolExecutor(DL.THREADS) as ex:
            for i in range(0, len(todo), DL.BATCH):
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
        found = locate(pages)
    VI = P[['page', 'in_AD', 'in_LK']].copy()
    VI['source'] = VI.page.map(lambda t: found.get(t, (None, None))[0])
    VI['status'] = VI.page.map(lambda t: found.get(t, (None, -1))[1]).astype('int32')
    VI.to_parquet(OUT / 'views_index.parquet', index=False)
    summ = dict(pages=len(P), AD_pages=int(P.in_AD.sum()), LK_pages=int(P.in_LK.sum()),
                by_source={str(k): int(v) for k, v in VI.source.fillna('missing').value_counts().items()},
                by_status={str(k): int(v) for k, v in VI.status.value_counts().items()},
                AD_by_source={str(k): int(v) for k, v in VI[VI.in_AD].source.fillna('missing').value_counts().items()},
                LK_by_source={str(k): int(v) for k, v in VI[VI.in_LK].source.fillna('missing').value_counts().items()},
                downloaded_now=done, http=None if H is None else dict(network=H.n_net, cache=H.n_cache, backoffs=H.n_backoff,
                                                                    codes={str(k): v for k, v in H.codes.items()}),
                gap_s=DL.GAP, threads=DL.THREADS, limit=a.limit, finished=time.strftime('%Y-%m-%d %H:%M:%S %z'))
    T.write_json(summ, OUT / 'n13_summary.json')
    T.log(json.dumps(summ))
    T.log(f'peak memory {T.peak_gb():.2f} GB; done')


if __name__ == '__main__':
    main()
