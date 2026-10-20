#!/usr/bin/env python3
"""Test B (new books): independent re-computation of the row features, as a check of 01b_loans_library.py and 04_rows.py.

Library features (loans6, n_prior_works, prior_loans) are recomputed with plain pandas from the raw record-level rows for a random
sample of works plus works of the most prolific creators; the Wikipedia features (v6, v12, trend, vmax) are recomputed from the long
views file for a sample of matched and unmatched rows.  Data only: it compares two computations of the same feature, it relates nothing
to an outcome.
Run from handoff/code:   nice -n 10 ../.venv/bin/python main_study/wiki_led/06_checks.py
"""
import json
import numpy as np, pandas as pd, pyarrow.parquet as pq
from _common import TAXO, OUT, log


def idx(ym):
    return (ym // 100) * 12 + ym % 100 - 1


def main():
    r = pd.read_parquet(OUT / 'test_b_rows.parquet')
    ll = pd.read_parquet(OUT / 'test_b_loans_library.parquet', columns=['work_id', 'prior_loans'])
    r = r.merge(ll, on='work_id')
    res = {}

    # ---- library features from the raw rows
    wa = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'creator_key', 'first_ym'])
    rw = pd.read_parquet(TAXO / 'spl_record_work.parquet')
    s = r[~r.creator_key.str.startswith('__nokey_')].sample(60, random_state=3)
    big = r.groupby('creator_key').size().sort_values().tail(3).index
    s = pd.concat([s, r[r.creator_key.isin(big)].sample(10, random_state=1)]).drop_duplicates('work_id')
    works = wa[wa.creator_key.isin(set(s.creator_key))]
    recs = rw[rw.work_id.isin(works.work_id)]
    parts = []
    for f in ['book', 'ebook', 'audiobook']:
        pf = pq.ParquetFile(TAXO / f'spl_rows_{f}.parquet')
        for b in pf.iter_batches(batch_size=3_000_000, columns=['record_id', 'year', 'month', 'checkouts']):
            d = b.to_pandas()
            parts.append(d[d.record_id.isin(recs.record_id)])
    x = pd.concat(parts).merge(recs, on='record_id').merge(works[['work_id', 'creator_key']], on='work_id')
    x['year'] = x.year.astype('int64'); x['month'] = x.month.astype('int64')
    x['ym'] = x.year * 100 + x.month
    x['i'] = x.year * 12 + x.month - 1
    bad = 0
    for _, w in s.iterrows():
        g = x[x.creator_key == w.creator_key]
        prior = int(g[g.ym < w.first_ym].checkouts.sum())
        nprior = int((works[works.creator_key == w.creator_key].first_ym < w.first_ym).sum())
        wm = g[g.work_id == w.work_id]
        f = int(idx(w.first_ym))
        l6 = int(wm[(wm.i >= f) & (wm.i <= f + 5)].checkouts.sum())
        if prior != w.prior_loans or nprior != w.n_prior_works or l6 != w.loans6:
            bad += 1
    res['library_checked'] = int(len(s)); res['library_mismatches'] = bad
    log('library features checked', len(s), 'mismatches', bad)

    # ---- Wikipedia features from the long views file
    vw = pd.read_parquet(OUT / 'author_monthly_views.parquet')
    vw['i'] = idx(vw.ym.astype('int64'))
    g = {t: d.set_index('i').views for t, d in vw.groupby('enwiki_title')}
    s = pd.concat([r[r.matched == 1].sample(400, random_state=5), r[r.matched == 0].sample(50, random_state=5)])
    bad = 0
    for _, w in s.iterrows():
        f = int(idx(w.first_ym))
        if w.matched == 1 and w.enwiki_title in g:
            sr = g[w.enwiki_title]
            m6 = np.mean([sr.get(f - k, 0) for k in range(1, 7)])
            m12 = np.mean([sr.get(f - k, 0) for k in range(7, 13)])
            mx = max(sr.get(f - k, 0) for k in range(1, 13))
        else:
            m6 = m12 = mx = 0
        v6, v12, vm = np.log1p(m6), np.log1p(m12), np.log1p(mx)
        if not (np.isclose(v6, w.v6) and np.isclose(v12, w.v12) and np.isclose(vm, w.vmax) and np.isclose(v6 - v12, w.trend)):
            bad += 1
    res['wikipedia_checked'] = int(len(s)); res['wikipedia_mismatches'] = bad
    u = r[r.matched == 0]
    res['unmatched_rows_with_nonzero_wikipedia_feature'] = int((u[['v6', 'v12', 'trend', 'vmax', 'writer_type']] != 0).any(axis=1).sum())
    res['matched_rows_without_title'] = int(((r.matched == 1) & r.enwiki_title.isna()).sum())
    log('wikipedia features checked', len(s), 'mismatches', bad)
    (OUT / 'checks_summary.json').write_text(json.dumps(res, indent=1))
    log(json.dumps(res))


if __name__ == '__main__':
    main()
