# 03. Clean title-level SPL table: one row per normalized work (title + creator), with formats, subject
# terms (with the share of the work's checkouts that carried each term, since OverDrive changed its terms over
# time), first and last checkout month, and checkouts by format.
# Output: data/db/taxonomy_v2/spl_works.parquet
import re, collections, numpy as np, pandas as pd
from _common import OUT, split_subjects, snapshot

R = pd.read_parquet(f'{OUT}/spl_records.parquet'); R['format'] = R['format'].astype(str)
rows = pd.concat([pd.read_parquet(f'{OUT}/spl_rows_{f}.parquet', columns=['record_id', 'year', 'month', 'checkouts']) for f in ['audiobook', 'ebook']])
rows['ym'] = rows.year.astype(np.int32) * 100 + rows.month.astype(np.int32)
per = rows.groupby('record_id').agg(checkouts=('checkouts', 'sum'), n_rows=('ym', 'size'), first_ym=('ym', 'min'), last_ym=('ym', 'max')).reset_index()
del rows
R = R.merge(per, on='record_id', how='left')


def pubyear(x):
    m = re.search(r'(1[5-9]\d\d|20[0-3]\d)', str(x or ''))
    return int(m.group(1)) if m else np.nan


R['pub_year'] = R.publicationyear.map(pubyear)
R['terms'] = R.subjects.map(split_subjects)

out = []
for wk, g in R.groupby('work_key', sort=False):
    tot = g.checkouts.sum()
    tw = collections.Counter()
    for ts, c in zip(g.terms, g.checkouts):
        for t in ts:
            tw[t] += c
    terms = sorted(tw, key=lambda t: -tw[t])
    rec = dict(work_key=wk,
               title=g.groupby('title_clean').checkouts.sum().idxmax(),
               creator=g.groupby('creator').checkouts.sum().idxmax(),
               title_main=g.title_main.iloc[0], creator_key=g.creator_key.iloc[0],
               formats=','.join(sorted(g.format.unique())),
               subject_terms=terms, subject_term_share=[round(tw[t] / tot, 4) if tot else 0.0 for t in terms],
               n_subject_strings=g.subjects.nunique(), n_records=len(g), n_raw_titles=g.title.nunique(),
               first_ym=int(g.first_ym.min()), last_ym=int(g.last_ym.max()),
               checkouts_total=int(tot), pub_year_min=g.pub_year.min(),
               publishers=list(g.groupby('publisher').checkouts.sum().sort_values(ascending=False).index[:3]),
               isbns=sorted({i for s in g.isbn for i in re.split(r'[,; ]+', s) if i})[:10])
    for f in ['AUDIOBOOK', 'EBOOK']:
        gf = g[g.format == f]
        rec[f'checkouts_{f.lower()}'] = int(gf.checkouts.sum())
        rec[f'first_ym_{f.lower()}'] = int(gf.first_ym.min()) if len(gf) else None
        rec[f'last_ym_{f.lower()}'] = int(gf.last_ym.max()) if len(gf) else None
    out.append(rec)
W = pd.DataFrame(out)
W.insert(0, 'work_id', np.arange(len(W), dtype=np.int32))
W.attrs['ebook_snapshot'] = str(snapshot()['EBOOK'])
W.to_parquet(f'{OUT}/spl_works.parquet', index=False)
# record -> work id lookup, used by later scripts for monthly series
R[['record_id', 'work_key']].merge(W[['work_key', 'work_id']], on='work_key')[['record_id', 'work_id']].to_parquet(f'{OUT}/spl_record_work.parquet', index=False)
print(W.shape)
print(W.formats.value_counts())
print(W[['checkouts_total', 'checkouts_audiobook', 'checkouts_ebook', 'n_records', 'n_subject_strings']].describe().round(1).to_string())
print(W.sort_values('checkouts_total', ascending=False).head(15)[['title', 'creator', 'formats', 'checkouts_audiobook', 'checkouts_ebook', 'subject_terms']].to_string())
