#!/usr/bin/env python3
"""Test F data, step 1: the page universe and the page ids.

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (page_universe).  Data only: no loans are read, nothing is sorted.
Input: data/raw/wiki_top_daily.json (the English Wikipedia daily top 500, 2016-01-01 to 2026-09-30, titles as the Pageviews API gives them).
Rule: a title counts on a day when it is in that day's list; titles that start with Main_Page, Special:, Wikipedia:, Portal:, File:, Help:,
Template:, Category:, User:, Talk:, Book:, Draft: or Module: are left out (the list of the addendum, each used as a prefix, which reproduces
its counts: 'Main_Page/' goes, while 'Main_page', 'main_page' and other namespaces such as User_talk: stay in and are flagged later from
the API answer).
  universe          titles on at least 2 different days (expected 84,577)
  sample1day        a fixed random 3,000 of the titles on exactly 1 day: numpy default_rng(20261021).choice over the one-day titles sorted
                    by code point, without replacement; coverage check only
Ids: the universe titles sorted by code point and put in a fixed random order with numpy default_rng(20261021).permutation get p00001 to
p84577 in that order; the one-day sample continues with p84578 to p87577 in the order drawn.
Output: data/db/wiki_led/testF/universe.parquet (id, title, set, n_top_days, first_day, last_day, order).
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/01_universe.py
"""
import sys, json, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _testf_common as F

t0 = time.time()
uni, one, n_all, n_kept, (d0, d1, ndays) = F.page_universe()
F.log(f'top-500 file: {ndays} days ({d0} to {d1}); {n_all:,} titles; {n_kept:,} after the namespace rule; '
      f'{len(uni):,} on 2 days or more; {len(one):,} on exactly 1 day')
assert len(uni) == 84577, f'universe has {len(uni)} titles, the addendum expects 84,577'
assert n_kept == 139161

u_sorted = sorted(uni)
perm = np.random.default_rng(F.SEED_ORDER).permutation(len(u_sorted))
u_order = [u_sorted[i] for i in perm]

o_sorted = sorted(one)
pick = np.random.default_rng(F.SEED_ORDER).choice(len(o_sorted), 3000, replace=False)
o_order = [o_sorted[i] for i in pick]

rows = []
for k, t in enumerate(u_order):
    n, first, last = uni[t]
    rows.append(('p%05d' % (k + 1), t, 'universe', n, first, last))
for k, t in enumerate(o_order):
    n, first, last = one[t]
    rows.append(('p%05d' % (len(u_order) + k + 1), t, 'sample1day', n, first, last))
U = pd.DataFrame(rows, columns=['id', 'title', 'set', 'n_top_days', 'first_day', 'last_day'])
U['order'] = np.arange(len(U))
assert U.id.is_unique and U.title.is_unique
U.to_parquet(F.OUT / 'universe.parquet', index=False)

s = U[U.set == 'universe']
F.log(f'wrote universe.parquet: {len(s):,} universe pages (top-500 days: median {s.n_top_days.median():.0f}, max {s.n_top_days.max()}), '
      f'{(U.set == "sample1day").sum():,} one-day pages; {time.time() - t0:.0f}s')
json.dump(dict(n_days=ndays, first_day=d0, last_day=d1, n_titles_all=n_all, n_titles_after_namespace_rule=n_kept, n_universe=len(uni),
               n_one_day=len(one), n_sample1day=len(o_order), seconds=round(time.time() - t0, 1)),
          open(F.OUT / 'universe_summary.json', 'w'), indent=1)
