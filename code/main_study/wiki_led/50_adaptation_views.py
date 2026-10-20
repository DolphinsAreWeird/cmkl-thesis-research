#!/usr/bin/env python3
"""Adaptation pages, step 1 of 2: screen the English Wikipedia pages of the adaptations of books, then fetch their daily user views.

Settings: prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json, change 5 (views of the adaptation's own article).
Data only: no model is fitted and no feature is related to loans.
Input: data/db/wiki_led/adaptations.parquet (Wikidata items based on a book: book, adapt, article = English Wikipedia title).  Its
publication-date column is not read anywhere (it may have been added after the event).  No filter on the kind of adaptation is
applied (film, television, stage, game, ...); the kinds are kept in the page table (classes, class_labels) so a film and TV subset can be cut later.

Stage 1, screen.  Wikipedia Action API (at most 5 requests per second, batches of 50, prop=pageprops, redirects=1, cached).  A page is
not specific to the adaptation, and is excluded for that book, when:
  disambiguation    the page, after any redirect, is a disambiguation page (pageprops 'disambiguation')
  redirect_to_book  the title is a redirect to the book's own article (the target carries the book's Wikidata item, or is the book's English
                    article in data/db/study2r/works.parquet)
  same_as_book      the title is itself the book's own article
Everything else is kept, including redirects to other pages, missing pages and other namespaces (flagged in the tables, counted in the report).
A page is fetched when it is kept for at least one book.
Outputs (data/db/wiki_led/): adaptation_pairs.parquet (one row per book and page, with keep and reason), adaptation_pages.parquet (one row
per page), adaptation_screen_summary.json.

Stage 2, fetch.  Wikimedia REST per-article, daily, all-access, agent user, 2015-07-01 to 2026-09-30, for the pages to fetch.  The Http class of
_common.py: answers cached on disk (data/interim/wiki_led_cache, so a rerun after any stop continues from the cache), project user agent,
4 threads sharing one limiter (gap 0.30 s, about 3 requests per second), Retry-After honoured, the gap grows by 30% after a 429 and shortens
again after 200 successes.  A 404 means no views in the period and is counted.  A day missing from an answer means 0 views.
Outputs: adaptation_daily_views.parquet (article, date, views; pages sorted, one row group per 250 pages), adaptation_fetch_status.parquet
(one row per page fetched), adaptation_views_summary.json.

Run from handoff/code.  The fetch is long, so detached, and only when no other job is using the REST gateway:
    nice -n 10 bash ../jobs/bg.sh wiki_led_adapt_views main_study/wiki_led/50_adaptation_views.py
Options: --screen-only        stage 1 only (Action API and Wikidata labels only)
         --test N             stage 2 on N kept pages only; every output file gets the suffix _test
         --titles 'A|B|C'     with --test: these titles (underscores or spaces) instead of N evenly spaced ones
         --gap S --threads K  REST gap in seconds and threads (defaults 0.30 and 4)
         --offline            no network at all: a request that is not in the cache raises (tests and reruns from the cache)
         --force              start although a job in REST_JOBS is still running (they share the gateway, which tolerates about 3 requests a second)
Without --offline the script refuses to start while wiki_led_views is running, before it makes any request.
"""
import sys, os, json, time, urllib.parse
import numpy as np, pandas as pd
import pyarrow as pa, pyarrow.parquet as pq
from concurrent.futures import ThreadPoolExecutor
from _common import D, OUT, REP, Http, log, maxlag_check, T0


def opt(name, default, cast=str):
    return cast(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


GAP = opt('--gap', 0.30, float)                   # seconds between two REST requests (0.30 = a little over 3 per second)
THREADS = opt('--threads', 4, int)
TEST = opt('--test', 0, int)
SUF = '_test' if TEST else ''
WP_API = 'https://en.wikipedia.org/w/api.php'
WD_API = 'https://www.wikidata.org/w/api.php'
REST = 'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{t}/daily/20150701/20260930'
REST_JOBS = ('wiki_led_views',)                   # background jobs (data/reports/NAME.pid) that use the same Wikimedia gateway
H = Http({'wp': 0.21, 'wd': 0.21, 'rest': GAP}, adaptive=('rest',), throttle_gap=None, recover=True)
if '--offline' in sys.argv:
    def _no_network(*a, **k):
        raise RuntimeError('offline mode: a request that is not in the cache was attempted')
    H.s.get = _no_network                    # Http.get reaches the network only through this call


def chunks(seq, n=50):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def busy_rest_jobs():
    """Names in REST_JOBS whose process (pid file in data/reports) is still alive."""
    out = []
    for name in REST_JOBS:
        try:
            os.kill(int((REP / f'{name}.pid').read_text()), 0)
        except (FileNotFoundError, ValueError, ProcessLookupError):
            continue
        except PermissionError:
            pass                                          # a live process of another user: treat as running
        out.append(name)
    return out


# ------------------------------------------------------------------------------------------------ stage 1: screen
def resolve(titles):
    """titles (with spaces) -> {title: dict(status, is_redirect, canonical, to_fragment, qid, disambiguation)}.
    status: page, missing, invalid, nonmain (not an article namespace) or unresolved."""
    todo = sorted(set(titles))
    batches = list(chunks(todo))
    log(f'  Action API: {len(todo)} titles in {len(batches)} batches')

    def one(batch):
        st, text = H.get('wp', WP_API, dict(action='query', prop='pageprops', ppprop='disambiguation|wikibase_item', redirects=1,
                                            titles='|'.join(batch), format='json', formatversion=2, maxlag=5), check=maxlag_check)
        if st != 200:
            raise RuntimeError(f'Action API status {st}')
        q = json.loads(text).get('query', {})
        norm = {d['from']: d['to'] for d in q.get('normalized', [])}
        redir = {d['from']: d for d in q.get('redirects', [])}
        pages = {p['title']: p for p in q.get('pages', [])}
        out = {}
        for t in batch:
            cur, hops, frag = norm.get(t, t), 0, ''
            while cur in redir and hops < 10:                       # follow a redirect chain
                frag = redir[cur].get('tofragment') or frag
                cur, hops = redir[cur]['to'], hops + 1
            p = pages.get(cur)
            r = dict(status='unresolved', is_redirect=hops > 0, canonical=None, to_fragment=frag, qid=None, disambiguation=False)
            if p is not None:
                pp = p.get('pageprops', {}) or {}
                if p.get('invalid'):
                    r['status'] = 'invalid'
                elif p.get('missing'):
                    r['status'] = 'missing'
                elif p.get('ns', 0) != 0:
                    r['status'] = 'nonmain'
                else:
                    r['status'] = 'page'
                if r['status'] in ('page', 'nonmain'):
                    r['canonical'] = p['title']
                    r['qid'] = pp.get('wikibase_item')
                    r['disambiguation'] = 'disambiguation' in pp
            out[t] = r
        return out

    res = {}
    with ThreadPoolExecutor(3) as ex:                               # the limiter keeps the rate at 4.7 per second at most
        for i, out in enumerate(ex.map(one, batches)):
            res.update(out)
            if (i + 1) % 20 == 0 or i + 1 == len(batches):
                log(f'  Action API batches {i + 1}/{len(batches)}; network {H.n_net}, cache {H.n_cache}, backoffs {H.n_backoff}')
    return res


def class_labels(qids):
    """English labels of the Wikidata classes (P31 values) that occur in the table."""
    todo = sorted(set(qids))
    out = {}
    for b in chunks(todo):
        st, text = H.get('wd', WD_API, dict(action='wbgetentities', ids='|'.join(b), props='labels', languages='en', format='json', maxlag=5),
                         check=maxlag_check)
        if st != 200:
            raise RuntimeError(f'Wikidata status {st}')
        for q, e in json.loads(text).get('entities', {}).items():
            out[q] = e.get('labels', {}).get('en', {}).get('value', q)
    return out


def classify(P):
    """The exclusion rule.  P has one row per book and page with: book (Wikidata item of the book), qid and canonical (the page after any redirect),
    is_redirect, disambiguation, book_canonical (the book's own English article after any redirect).  Adds reason ('' = kept) and keep."""
    P = P.copy()
    hit = ((P.qid.notna() & (P.qid == P.book)) | (P.canonical.notna() & (P.canonical == P.book_canonical))).fillna(False).astype(bool)
    P['reason'] = np.where(P.disambiguation, 'disambiguation',
                           np.where(hit & P.is_redirect, 'redirect_to_book', np.where(hit, 'same_as_book', '')))
    P['keep'] = P.reason == ''
    return P


def screen():
    A = pd.read_parquet(OUT / 'adaptations.parquet', columns=['book', 'adapt', 'adaptLabel', 'article', 'cls'])
    W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id', 'item', 'article'])
    n_books_all, n_adapt_all = A.book.nunique(), A.adapt.nunique()
    A = A.dropna(subset=['article']).copy()
    A['article'] = A.article.str.replace(' ', '_')
    cls = A.groupby('article').cls.agg(lambda s: ';'.join(sorted(set(s.dropna())))).rename('classes')
    P = A.drop_duplicates(['book', 'adapt', 'article'])[['book', 'adapt', 'adaptLabel', 'article']].reset_index(drop=True)
    P = P.merge(cls, left_on='article', right_index=True, how='left')
    bart = W.drop_duplicates('item').set_index('item').article                  # the book's own English article (one per item)
    P['book_article'] = P.book.map(bart)
    log(f'adaptation pairs {len(P)}: books {P.book.nunique()}, adaptations {P.adapt.nunique()}, pages {P.article.nunique()}')

    R = resolve([t.replace('_', ' ') for t in P.article.unique()] + list(bart[bart.index.isin(P.book)].unique()))
    rp = pd.DataFrame.from_dict({t: R[t.replace('_', ' ')] for t in P.article.unique()}, orient='index')
    rp.index.name = 'article'
    P = P.merge(rp, left_on='article', right_index=True, how='left')
    P['book_canonical'] = P.book_article.map(lambda t: R[t]['canonical'])
    P['book_page_qid'] = P.book_article.map(lambda t: R[t]['qid'])
    P = classify(P)
    P['qid_is_adapt'] = P.qid.notna() & (P.qid == P.adapt)

    # ---- one row per page
    g = P.groupby('article')
    pages = pd.DataFrame({
        'adapt': g.adapt.first(), 'adaptLabel': g.adaptLabel.first(), 'classes': g.classes.first(),
        'books': g.book.agg(lambda s: ';'.join(sorted(set(s)))), 'n_books': g.book.nunique(),
        'n_books_kept': P[P.keep].groupby('article').book.nunique().reindex(g.size().index).fillna(0).astype(int),
        'status': g.status.first(), 'is_redirect': g.is_redirect.first(), 'canonical': g.canonical.first(), 'to_fragment': g.to_fragment.first(),
        'qid': g.qid.first(), 'disambiguation': g.disambiguation.first(), 'qid_is_adapt': g.qid_is_adapt.first(),
        'reasons': g.reason.agg(lambda s: ';'.join(sorted(set(x for x in s if x)))),
    }).reset_index()
    pages['fetch'] = pages.n_books_kept > 0
    pages['redirect_other'] = pages.fetch & pages.is_redirect
    lab = class_labels([c for s in pages.classes.dropna() for c in s.split(';') if c])
    pages['class_labels'] = pages.classes.map(lambda s: '; '.join(lab.get(c, c) for c in s.split(';')) if isinstance(s, str) and s else '')
    P.to_parquet(OUT / 'adaptation_pairs.parquet', index=False)
    pages.to_parquet(OUT / 'adaptation_pages.parquet', index=False)

    # ---- counts
    kept_pairs = P[P.keep]
    works_with = W[W.item.isin(set(A.book))]
    works_kept = W[W.item.isin(set(kept_pairs.book))]
    comp = pages[pages.fetch].classes.dropna().str.split(';').explode().value_counts()          # a page with two classes counts in both
    summ = dict(
        books_with_adaptation_items=int(n_books_all), adaptation_items=int(n_adapt_all),
        books_with_english_article_of_an_adaptation=int(P.book.nunique()), works_of_those_books=int(len(works_with)),
        pairs_book_page=int(len(P)), pages_distinct=int(len(pages)),
        pairs_excluded=int((~P.keep).sum()), pairs_excluded_by_reason=P[~P.keep].reason.value_counts().to_dict(),
        pages_excluded_all_books=int((~pages.fetch).sum()),
        pages_excluded_all_books_by_reason=pages[~pages.fetch].reasons.value_counts().to_dict(),
        pages_kept=int(pages.fetch.sum()), books_with_a_kept_page=int(kept_pairs.book.nunique()), works_with_a_kept_page=int(len(works_kept)),
        works_lost_by_exclusion=int(len(works_with) - len(works_kept)),
        kept_pages_status=pages[pages.fetch].status.value_counts().to_dict(),
        kept_pages_redirect_to_other_page=int(pages.redirect_other.sum()),
        kept_pages_redirect_to_other_page_examples=pages[pages.redirect_other].article.head(10).tolist(),
        kept_pages_qid_differs_from_adaptation_item=int((pages.fetch & ~pages.qid_is_adapt & pages.qid.notna()).sum()),
        kept_pages_linked_to_more_than_one_book=int((pages.fetch & (pages.n_books_kept > 1)).sum()),
        kept_pages_by_class={f'{c} {lab.get(c, c)}': int(n) for c, n in comp.head(25).items()}, n_classes=int(len(comp)),
        network_requests=H.n_net, cache_hits=H.n_cache, backoffs=H.n_backoff, response_codes={str(k): v for k, v in H.codes.items()},
        runtime_s=round(time.time() - T0))
    (OUT / 'adaptation_screen_summary.json').write_text(json.dumps(summ, indent=1))
    log(json.dumps(summ, indent=1))
    return pages


# ------------------------------------------------------------------------------------------------ stage 2: fetch
def fetch(title):
    u = REST.format(t=urllib.parse.quote(title.replace(' ', '_'), safe=''))
    st, text = H.get('rest', u, soft=(400,))
    if st != 200:
        return title, st, None, None
    items = json.loads(text).get('items', [])
    day = pd.to_datetime([it['timestamp'][:8] for it in items], format='%Y%m%d').to_numpy('datetime64[us]')
    return title, 200, day, np.array([int(it['views']) for it in items], dtype=np.int32)


SCHEMA = pa.schema([('article', pa.string()), ('date', pa.timestamp('us')), ('views', pa.int32())])


def fetch_all(titles):
    path = OUT / f'adaptation_daily_views{SUF}.parquet'
    tmp = path.with_suffix('.parquet.part')
    status = []
    buf_t, buf_d, buf_v = [], [], []
    n_rows = 0
    done = 0

    def flush(w):
        nonlocal buf_t, buf_d, buf_v, n_rows
        if buf_t:
            t = pa.table({'article': pa.array(np.concatenate(buf_t)), 'date': pa.array(np.concatenate(buf_d), type=pa.timestamp('us')),
                          'views': pa.array(np.concatenate(buf_v), type=pa.int32())}, schema=SCHEMA)
            w.write_table(t)
            n_rows += t.num_rows
        buf_t, buf_d, buf_v = [], [], []

    with pq.ParquetWriter(tmp, SCHEMA, compression='zstd') as w, ThreadPoolExecutor(THREADS) as ex:
        for title, st, day, v in ex.map(fetch, titles):
            done += 1
            if st == 200 and len(day):
                buf_t.append(np.full(len(day), title, dtype=object)); buf_d.append(day); buf_v.append(v)
                status.append(dict(article=title, status=200, n_days=len(day), first_date=pd.Timestamp(day.min()), last_date=pd.Timestamp(day.max()),
                                   views_total=int(v.sum(dtype=np.int64))))
            else:
                status.append(dict(article=title, status=st if st != 200 else 404, n_days=0, first_date=pd.NaT, last_date=pd.NaT, views_total=0))
            if done % 250 == 0 or done == len(titles):
                flush(w)
                n404 = sum(s['status'] == 404 for s in status)
                log(f'  {done}/{len(titles)} pages; 404 so far {n404}; rows {n_rows}; network {H.n_net}, cache {H.n_cache}, backoffs {H.n_backoff}, '
                    f'gap now {H.rates["rest"]:.2f}s, codes {H.codes}')
    tmp.replace(path)
    S = pd.DataFrame(status)
    S.to_parquet(OUT / f'adaptation_fetch_status{SUF}.parquet', index=False)
    return S, n_rows


def main():
    busy = [] if ('--offline' in sys.argv or '--force' in sys.argv) else busy_rest_jobs()
    if busy:
        raise SystemExit(f'not started: {", ".join(busy)} is still running and shares the Wikimedia gateway (check: bash ../jobs/status.sh). '
                         'Start this when it has stopped, or add --force, or --offline to work from the cache only.')
    pages = screen()
    if '--screen-only' in sys.argv:
        return
    kept = sorted(pages[pages.fetch].article)
    if TEST:
        if '--titles' in sys.argv:
            want = [t.strip().replace(' ', '_') for t in opt('--titles', '').split('|') if t.strip()]
            bad = [t for t in want if t not in set(kept)]
            if bad:
                raise SystemExit(f'not pages to fetch: {bad}')
            titles = want[:TEST]
        else:
            titles = kept[3::max(1, len(kept) // TEST)][:TEST]
    else:
        titles = kept
    log(f'pages to fetch: {len(titles)} (test mode: {bool(TEST)})')
    S, n_rows = fetch_all(titles)
    summ = dict(pages_requested=len(titles), pages_with_views=int((S.status == 200).sum()), pages_404=int((S.status == 404).sum()),
                pages_other_status={str(k): int(v) for k, v in S.status[~S.status.isin([200, 404])].value_counts().items()},
                rows=int(n_rows), date_min=str(S.first_date.min().date()), date_max=str(S.last_date.max().date()),
                network_requests=H.n_net, cache_hits=H.n_cache, backoffs=H.n_backoff, final_gap_s=round(H.rates['rest'], 3),
                threads=THREADS, start_gap_s=GAP, response_codes={str(k): v for k, v in H.codes.items()}, runtime_s=round(time.time() - T0))
    if TEST:
        summ['titles'] = titles
    (OUT / f'adaptation_views_summary{SUF}.json').write_text(json.dumps(summ, indent=1))
    log(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
