#!/usr/bin/env python3
"""Test B (new books), step 5: monthly English Wikipedia views of every accepted author article.

Settings: prereg/wiki_led_settings_2026-10-20.json, test_B_new_books.wikipedia_features (Wikimedia REST per-article, monthly, all-access,
user agents only, from 2015-07).  A 404 means no views in the period: nothing is stored for that title and it is counted.
Data only: no model, no outcome.

Run from handoff/code (a long download, so detached):
    bash ../jobs/bg.sh wiki_led_views main_study/wiki_led/03_author_views.py
Options: --test N  uses only N titles and writes *_test files.
Every response is cached under data/interim/wiki_led_cache/.  REST: at most 10 requests per second in total (6 threads share one
limiter set to about 9 per second), back-off on 429/503.
"""
import sys, json, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from _common import OUT, Http, log, T0

GAP = float(sys.argv[sys.argv.index('--gap') + 1]) if '--gap' in sys.argv else 0.11       # seconds between two requests (0.11 = about 9 per second, the stated ceiling)
THREADS = int(sys.argv[sys.argv.index('--threads') + 1]) if '--threads' in sys.argv else 6
# After the first 429/503 the rate drops to 50 per second (gap 0.02 s) for the rest of the run; a later, separate 429/503 episode halves it again.
# The server's Retry-After pause is always honoured by all threads.
H = Http({'rest': GAP}, adaptive=('rest',), throttle_gap=0.02, recover=False)
URL = 'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{t}/monthly/2015070100/2026093000'
TEST = int(sys.argv[sys.argv.index('--test') + 1]) if '--test' in sys.argv else 0
SUF = '_test' if TEST else ''


def fetch(title):
    u = URL.format(t=urllib.parse.quote(title.replace(' ', '_'), safe=''))
    st, text = H.get('rest', u, soft=(400,))
    if st != 200:
        return title, st, []
    items = json.loads(text).get('items', [])
    return title, 200, [(int(it['timestamp'][:6]), int(it['views'])) for it in items]


def main():
    am = pd.read_parquet(OUT / f'author_match{SUF}.parquet')
    titles = sorted(am[am.is_human].enwiki_title.unique())
    if TEST:
        titles = titles[3:: max(1, len(titles) // TEST)][:TEST]
    log(f'accepted titles to fetch: {len(titles)}')
    rows_t, rows_ym, rows_v = [], [], []
    n404 = []
    n400 = []
    done = 0
    with ThreadPoolExecutor(THREADS) as ex:
        for title, st, items in ex.map(fetch, titles):
            done += 1
            if st == 404:
                n404.append(title)
            elif st != 200:
                n400.append(title)
            for ym, v in items:
                rows_t.append(title); rows_ym.append(ym); rows_v.append(v)
            if done % 500 == 0 or done == len(titles):
                log(f'  {done}/{len(titles)} titles; 404 so far {len(n404)}; network {H.n_net}, cache {H.n_cache}, backoffs {H.n_backoff}, gap now {H.rates["rest"]:.2f}s, codes {H.codes}')
    df = pd.DataFrame(dict(enwiki_title=rows_t, ym=pd.array(rows_ym, dtype='int32'), views=pd.array(rows_v, dtype='int32')))
    df.to_parquet(OUT / f'author_monthly_views{SUF}.parquet', index=False)
    summ = dict(titles=len(titles), titles_with_views=int(df.enwiki_title.nunique()), titles_404=len(n404), titles_400=len(n400),
                titles_400_examples=n400[:10], rows=int(len(df)), ym_min=int(df.ym.min()), ym_max=int(df.ym.max()),
                network_requests=H.n_net, cache_hits=H.n_cache, backoffs=H.n_backoff, final_gap_s=round(H.rates['rest'], 3), throttle_episodes=H.episodes['rest'], threads=THREADS, start_gap_s=GAP, response_codes={str(k): v for k, v in H.codes.items()}, runtime_s=round(time.time() - T0))
    (OUT / f'author_views_summary{SUF}.json').write_text(json.dumps(summ, indent=1))
    log(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
