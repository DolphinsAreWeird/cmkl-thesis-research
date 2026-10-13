# 12. (v3) Light profile of the v3 inputs: rows, checkouts and months per format and year, completeness against the
# API counts saved at checkpoint 1 (data/db/taxonomy_v2/spl_api_counts.parquet, read only), and for print books the
# share of rows with subject headings and with a creator, headings per record, and how many digital works got headings.
# Output: data/db/taxonomy_v3/profile/v3_profile.json, v3_by_year_format.csv, v3_month_completeness.csv
import os
os.environ['TAXO'] = 'v3'
import json, numpy as np, pandas as pd
from _common import OUT, OUT_V2, save_json, snapshot

P = f'{OUT}/profile'; os.makedirs(P, exist_ok=True)
api = pd.read_parquet(f'{OUT_V2}/spl_api_counts.parquet'); api['ym'] = api.year * 100 + api.month
api['format'] = api.materialtype.str.lower()
R = pd.read_parquet(f'{OUT}/spl_records.parquet', columns=['record_id', 'format', 'subjects', 'creator_from_title', 'creator'])
R['format'] = R['format'].astype(str)
R['has_subj'] = R.subjects.str.len() > 0
R['n_head'] = np.where(R.has_subj, R.subjects.str.count(', ') + 1, 0)
S = {'snapshot': snapshot()}
yr = []; comp = []
for f in ['audiobook', 'ebook', 'book']:
    x = pd.read_parquet(f'{OUT}/spl_rows_{f}.parquet')
    x = x.merge(R[R.format == f.upper()][['record_id', 'has_subj', 'creator_from_title']], on='record_id', how='left')
    x['ym'] = x.year.astype(np.int32) * 100 + x.month.astype(np.int32)
    g = x.groupby('year').apply(lambda d: pd.Series(dict(rows=len(d), checkouts=int(d.checkouts.sum()), months=d.month.nunique(),
                                                         share_rows_with_subjects=d.has_subj.mean(),
                                                         share_checkouts_with_subjects=(d.checkouts * d.has_subj).sum() / max(1, d.checkouts.sum()),
                                                         share_rows_creator_missing=d.creator_from_title.mean())), include_groups=False).reset_index()
    g['format'] = f; yr.append(g)
    m = x.groupby('ym').agg(rows=('record_id', 'size'), checkouts=('checkouts', 'sum')).reset_index()
    a = api[api.format == f][['ym', 'n_rows', 'checkouts']].rename(columns={'checkouts': 'api_checkouts'})
    c = a.merge(m, on='ym', how='left').fillna({'rows': 0, 'checkouts': 0})
    c['row_ratio'] = c.rows / c.n_rows; c['format'] = f
    c['status'] = np.where(c.row_ratio >= 0.9999, 'complete', np.where(c.rows == 0, 'missing in snapshot', 'partial'))
    comp.append(c)
    S[f] = dict(rows=int(len(x)), checkouts=int(x.checkouts.sum()), first_month=int(x.ym.min()), last_month=int(x.ym.max()), months=int(x.ym.nunique()),
                api_rows=int(a.n_rows.sum()), share_of_api_rows=round(len(x) / a.n_rows.sum(), 4),
                months_complete=int((c.status == 'complete').sum()), months_partial=int((c.status == 'partial').sum()),
                months_missing_in_snapshot=int((c.status == 'missing in snapshot').sum()),
                complete_through=int(c[c.status == 'complete'].ym.max()) if (c.status == 'complete').any() else None)
    del x
Y = pd.concat(yr); Y.round(4).to_csv(f'{P}/v3_by_year_format.csv', index=False)
C = pd.concat(comp); C.to_csv(f'{P}/v3_month_completeness.csv', index=False)
b = R[R.format == 'BOOK']
S['book_records'] = dict(records=int(len(b)), with_subjects=int(b.has_subj.sum()), creator_taken_from_title=int(b.creator_from_title.sum()),
                         creator_still_empty=int((b.creator.fillna('') == '').sum()), headings_per_record_mean=round(float(b[b.has_subj].n_head.mean()), 2))
H = pd.read_parquet(f'{OUT}/headings.parquet', columns=['heading', 'n_works']) if os.path.exists(f'{OUT}/headings.parquet') else None
if H is not None:
    S['headings'] = dict(distinct=int(len(H)), on_10_or_more_works=int((H.n_works >= 10).sum()))
W = pd.read_parquet(f'{OUT}/spl_works.parquet', columns=['formats', 'n_headings', 'checkouts_audiobook', 'checkouts_ebook'])
dg = W[W.formats.str.contains('AUDIOBOOK|EBOOK')]
S['works'] = dict(total=int(len(W)), by_formats=W.formats.value_counts().to_dict(), digital=int(len(dg)),
                  digital_with_print_headings=int((dg.n_headings > 0).sum()),
                  digital_checkouts_share_with_print_headings=round(float((dg[dg.n_headings > 0][['checkouts_audiobook', 'checkouts_ebook']].sum().sum())
                                                                         / dg[['checkouts_audiobook', 'checkouts_ebook']].sum().sum()), 4))
save_json(S, f'{P}/v3_profile.json')
print(json.dumps({k: v for k, v in S.items() if k != 'snapshot'}, indent=1, default=str)[:4000])
