#!/usr/bin/env python3
"""Test F data, step 2: the text of every page (short description and first sentence of the lead).

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (page_text).  Data only: no loans are read, nothing is sorted.
Input: data/db/wiki_led/testF/universe.parquet (step 1): the 84,577 universe pages and the 3,000 one-day pages.
Source: the Wikipedia Action API, https://en.wikipedia.org/w/api.php, one GET per batch of at most 20 titles:
    action=query&redirects=1&prop=pageprops|extracts&ppprop=wikibase-shortdesc&exintro=1&explaintext=1&exsentences=1&exlimit=20
    &titles=...&format=json&formatversion=2&maxlag=5
(the titles with spaces for underscores; a batch also stops before its encoded titles pass 6,000 characters).  A 'continue' in the answer
is followed until the batch is complete.  The Http class of ../_common.py: the project user agent (code/config.py), every answer cached on
disk (data/interim/testF_cache, so a rerun after any stop continues from the cache), one shared limiter of 0.34 s between two requests
(at most 2.9 a second) over 2 threads, Retry-After honoured, a pause after a 429 or 5xx that grows with each attempt, the gap growing by
30% after a 429 and shrinking again after 60 successes, maxlag answers waited out.
Per title: the final title after normalisation and redirects (a chain is followed), whether it was a redirect, the section it points to,
the status (page, missing, invalid, unresolved), the namespace number, the short description (pageprops wikibase-shortdesc) and the first
sentence (TextExtracts).  Cleaned texts: one line, control characters (tabs, newlines) turned into spaces, runs of spaces made one, the first
sentence cut at 300 characters.  A page with neither text is sorted on its title alone (flag text_kind = 'title_only').
Outputs: data/db/wiki_led/testF/page_text.parquet (one row per title of the universe file), page_text_summary.json.
Run from handoff/ (detached, about 25 to 40 minutes):  nice -n 10 bash jobs/bg.sh testF_text main_study/wiki_led/testF/02_page_text.py
Options: --test N   only the first N batches, outputs with the suffix _test
         --offline  no network: a request that is not in the cache raises
"""
import sys, json, time, pathlib, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd
import _testf_common as F

API = 'https://en.wikipedia.org/w/api.php'
GAP, THREADS, MAX_TITLES, MAX_ENC = 0.34, 2, 20, 6000
TEST = int(sys.argv[sys.argv.index('--test') + 1]) if '--test' in sys.argv else 0
SUF = '_test' if TEST else ''
H = F.Http({'wp': GAP}, adaptive=('wp',), throttle_gap=None, recover=True)
if '--offline' in sys.argv:
    def _no_network(*a, **k):
        raise RuntimeError('offline mode: a request that is not in the cache was attempted')
    H.s.get = _no_network
BASE = dict(action='query', format='json', formatversion=2, redirects=1, prop='pageprops|extracts', ppprop='wikibase-shortdesc',
            exintro=1, explaintext=1, exsentences=1, exlimit=20, maxlag=5)
WARN = {'n': 0, 'examples': []}


def batches(titles):
    """Greedy batches in the given order: at most 20 titles and at most 6,000 characters of URL-encoded titles."""
    out, cur, size = [], [], 0
    for t in titles:
        enc = len(urllib.parse.quote(t.replace('_', ' '), safe='')) + 3
        if cur and (len(cur) == MAX_TITLES or size + enc > MAX_ENC):
            out.append(cur)
            cur, size = [], 0
        cur.append(t)
        size += enc
    if cur:
        out.append(cur)
    return out


def fetch(batch):
    names = [t.replace('_', ' ') for t in batch]
    params = dict(BASE, titles='|'.join(names))
    norm, redir, pages, interwiki = {}, {}, {}, set()
    cont, n_req = {}, 0
    while True:
        st, text = H.get('wp', API, dict(params, **cont), check=F.maxlag_check)
        n_req += 1
        if st != 200:
            raise RuntimeError(f'Action API status {st} for a batch starting {batch[0]!r}')
        j = json.loads(text)
        if 'warnings' in j:
            WARN['n'] += 1
            if len(WARN['examples']) < 5:
                WARN['examples'].append(json.dumps(j['warnings'])[:300])
        q = j.get('query', {})
        for x in q.get('normalized', []):
            norm[x['from']] = x['to']
        for x in q.get('redirects', []):
            redir[x['from']] = x
        for x in q.get('interwiki', []):
            interwiki.add(x.get('title'))
        for pg in q.get('pages', []):
            cur = pages.setdefault(pg['title'], {})
            for k, v in pg.items():
                if k == 'pageprops':
                    cur.setdefault('pageprops', {}).update(v)
                elif k == 'extract':
                    if v or 'extract' not in cur:
                        cur['extract'] = v
                else:
                    cur[k] = v
        if 'continue' in j:
            if n_req > 20:
                raise RuntimeError(f'more than 20 continuations for a batch starting {batch[0]!r}')
            cont = j['continue']
            continue
        break
    rows = []
    for t, nm in zip(batch, names):
        cur, hops, frag = norm.get(nm, nm), 0, ''
        while cur in redir and hops < 10:
            frag = redir[cur].get('tofragment') or frag
            cur, hops = redir[cur]['to'], hops + 1
        pg = pages.get(cur)
        r = dict(title=t, final_title=cur, normalized=norm.get(nm, nm) != nm, is_redirect=hops > 0, redirect_hops=hops, to_fragment=frag,
                 status='unresolved', ns=None, pageid=None, description_raw='', first_sentence_raw='', has_pageprops=False, has_extract=False)
        if pg is None:
            if nm in interwiki or cur in interwiki:
                r['status'] = 'interwiki'
        elif pg.get('invalid'):
            r['status'] = 'invalid'
        elif pg.get('missing'):
            r['status'] = 'missing'
            r['ns'] = pg.get('ns')
        else:
            r['status'] = 'page'
            r['ns'] = pg.get('ns')
            r['pageid'] = pg.get('pageid')
            pp = pg.get('pageprops') or {}
            r['has_pageprops'] = 'wikibase-shortdesc' in pp
            r['description_raw'] = pp.get('wikibase-shortdesc') or ''
            r['has_extract'] = 'extract' in pg
            r['first_sentence_raw'] = pg.get('extract') or ''
        rows.append(r)
    return rows, n_req


def main():
    t0 = time.time()
    U = pd.read_parquet(F.OUT / 'universe.parquet').sort_values('order')
    B = batches(U.title.tolist())
    if TEST:
        B = B[:TEST]
    F.log(f'{len(U):,} titles in {len(B):,} batches (sizes: {min(map(len, B))} to {max(map(len, B))}); gap {GAP}s, {THREADS} threads')
    rows, n_req = [], 0
    with ThreadPoolExecutor(THREADS) as ex:
        for i, (rr, nr) in enumerate(ex.map(fetch, B)):
            rows.extend(rr)
            n_req += nr
            if (i + 1) % 100 == 0 or i + 1 == len(B):
                el = time.time() - t0
                F.log(f'batches {i + 1:,}/{len(B):,} ({el / 60:.1f} min, {H.n_net / max(el, 1e-9):.2f} network requests a second); '
                      f'network {H.n_net:,}, cache {H.n_cache:,}, back-offs {H.n_backoff}, codes {H.codes}')
    P = pd.DataFrame(rows)
    assert P.title.is_unique, 'a title came back twice'
    P = U[['id', 'title', 'set']].merge(P, on='title', how='inner', validate='one_to_one')
    if not TEST:
        assert len(P) == len(U), f'{len(U) - len(P)} titles without a row'
    P['description'] = [F.clean(x) for x in P.description_raw]
    P['first_sentence'] = [F.clean(x, 300) for x in P.first_sentence_raw]
    P['first_sentence_cut'] = [len(F.clean(x)) > 300 for x in P.first_sentence_raw]
    P['text_kind'] = np.select([(P.description != '') & (P.first_sentence != ''), P.description != '', P.first_sentence != ''],
                               ['both', 'description_only', 'sentence_only'], 'title_only')
    P['disambiguation_like'] = P.description.str.lower().isin(['topics referred to by the same term', 'wikimedia disambiguation page',
                                                               'disambiguation page providing links to topics that could be referred to by the same search term'])
    P.to_parquet(F.OUT / f'page_text{SUF}.parquet', index=False)
    el = time.time() - t0
    summ = dict(titles=len(P), batches=len(B), requests=n_req, network_requests=H.n_net, cached_requests=H.n_cache, backoffs=H.n_backoff,
                status_codes={str(k): v for k, v in H.codes.items()}, warnings=WARN, seconds=round(el, 1),
                gap_seconds=GAP, threads=THREADS, user_agent='project user agent from code/config.py (not printed)',
                status=P.status.value_counts().to_dict(), text_kind=P.text_kind.value_counts().to_dict(),
                redirects=int(P.is_redirect.sum()), started=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t0)),
                finished=time.strftime('%Y-%m-%d %H:%M:%S'))
    json.dump(summ, open(F.OUT / f'page_text_summary{SUF}.json', 'w'), indent=1, default=str)
    F.log(f'wrote page_text{SUF}.parquet: {len(P):,} titles; status {summ["status"]}; text {summ["text_kind"]}; redirects {summ["redirects"]:,}; '
          f'{el / 60:.1f} min')


if __name__ == '__main__':
    main()
