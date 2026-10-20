#!/usr/bin/env python3
"""Test B (new books), step 6: one row per work.

Settings: prereg/wiki_led_settings_2026-10-20.json, test_B_new_books.  Data only: no model, no relation between a feature and an outcome.
Run from handoff/code:   nice -n 10 ../.venv/bin/python main_study/wiki_led/04_rows.py
Reads test_b_population, test_b_loans_library, author_match, author_monthly_views (all in data/db/wiki_led/); writes test_b_rows.parquet.

Wikipedia features use only months strictly before first_ym (month index f = the work's first_ym):
  matched = 1 when the first author's name was accepted as a human article (any human)
  v6    = ln(1 + mean views of months f-6 .. f-1)        v12 = ln(1 + mean views of months f-12 .. f-7)
  trend = v6 - v12                                       vmax = ln(1 + max monthly views of months f-12 .. f-1)
  writer_type = 1 when the matched person has a writer occupation
  Unmatched authors, and months with no data, count as 0 views (matched = 0, writer_type = 0 for unmatched).
top10 = Y6 at or above the 90th percentile of Y6 among works with first_ym in the same calendar year (the record's definition; the
  threshold is the plain empirical quantile over all rows of the year, ties at the threshold stay in).
"""
import json
import numpy as np, pandas as pd
from _common import OUT, log, ym_to_idx, T0

IDX0 = int(ym_to_idx(201507))         # first month of the views
IDX1 = int(ym_to_idx(202609))         # last month requested


def main():
    pop = pd.read_parquet(OUT / 'test_b_population.parquet')
    ll = pd.read_parquet(OUT / 'test_b_loans_library.parquet')
    am = pd.read_parquet(OUT / 'author_match.parquet')
    vw = pd.read_parquet(OUT / 'author_monthly_views.parquet')
    df = pop.merge(ll, on=['work_id', 'first_ym'], how='left', validate='1:1')
    assert df.loans6.notna().all() and len(df) == len(pop)
    nokey = df.creator_key == ''
    df.loc[nokey, 'creator_key'] = '__nokey_' + df.loc[nokey, 'work_id'].astype(str)       # 2 works: no author record to pool
    a = am[['display_name', 'enwiki_title', 'qid', 'is_human', 'writer_type']].drop_duplicates('display_name')
    df = df.merge(a, on='display_name', how='left', validate='m:1')
    assert df.is_human.notna().all()
    df['matched'] = df.is_human.astype(int)
    df['writer_type'] = df.writer_type.astype(int)

    # monthly views of the matched titles as a dense matrix (title x month, 2015-07 .. 2026-09); no row = 0 views
    titles = np.sort(vw.enwiki_title.unique())
    trow = {t: i for i, t in enumerate(titles)}
    ncol = IDX1 - IDX0 + 1
    V = np.zeros((len(titles), ncol), np.float64)
    ci = ym_to_idx(vw.ym.to_numpy().astype(np.int64)) - IDX0
    V[vw.enwiki_title.map(trow).to_numpy(), ci] = vw.views.to_numpy()
    f = (ym_to_idx(df.first_ym.to_numpy().astype(np.int64)) - IDX0).astype(np.int64)    # column of the work's first month
    assert f.min() >= 12 and f.max() < ncol
    row = df.enwiki_title.map(trow)
    has = row.notna().to_numpy() & (df.matched.to_numpy() == 1)
    r = row.fillna(-1).astype(int).to_numpy()
    mean6 = np.zeros(len(df)); mean12 = np.zeros(len(df)); vmax = np.zeros(len(df))
    idx = np.flatnonzero(has)
    for s in range(0, len(idx), 20000):
        i = idx[s:s + 20000]
        c6 = f[i][:, None] + np.arange(-6, 0)
        c12 = f[i][:, None] + np.arange(-12, -6)
        rr = r[i][:, None]
        mean6[i] = V[rr, c6].mean(axis=1)
        mean12[i] = V[rr, c12].mean(axis=1)
        vmax[i] = np.maximum(V[rr, c6].max(axis=1), V[rr, c12].max(axis=1))
    df['v6'] = np.log1p(mean6)
    df['v12'] = np.log1p(mean12)
    df['trend'] = df.v6 - df.v12
    df['vmax'] = np.log1p(vmax)
    df['titles_with_no_views_data'] = ((df.matched == 1) & ~has).astype(int)           # matched, but the REST API had no views at all

    thr = df.groupby('test_year').Y6.transform(lambda s: s.quantile(0.9))
    df['top10'] = (df.Y6 >= thr).astype(int)

    cols = ['work_id', 'creator_key', 'display_name', 'first_ym', 'test_year', 'Y6', 'loans6', 'top10', 'fmt_print', 'fmt_ebook',
            'fmt_audiobook', 'n_prior_works', 'ln_prior_loans', 'month', 'matched', 'v6', 'v12', 'trend', 'vmax', 'writer_type',
            'enwiki_title', 'qid', 'flag_months6', 'titles_with_no_views_data']
    out = df[cols].sort_values('work_id').reset_index(drop=True)
    out.to_parquet(OUT / 'test_b_rows.parquet', index=False)
    s = dict(rows=int(len(out)), matched=int(out.matched.sum()), writer_type=int(out.writer_type.sum()),
             matched_nonzero_v6=int(((out.matched == 1) & (out.v6 > 0)).sum()), matched_no_views_data=int(out.titles_with_no_views_data.sum()),
             top10_share_by_year={int(k): round(float(v), 4) for k, v in out.groupby('test_year').top10.mean().items()},
             nulls={c: int(out[c].isna().sum()) for c in cols if c in ('enwiki_title', 'qid') or out[c].isna().any()},
             runtime_s=round(__import__('time').time() - T0))
    (OUT / 'rows_summary.json').write_text(json.dumps(s, indent=1))
    log(json.dumps(s, indent=1))


if __name__ == '__main__':
    main()
