"""Study 2R step 10: monthly checkouts per matched work and format (print = spl_rows_book, ebook, audiobook). Read only the needed columns,
one format at a time. Output data/db/study2r/counts_work.parquet (work_id, format, mi, y: positive months only; zeros and unusable
months are made in _lib2r.load_counts with the Study 3b month status) and works.parquet (work, article, author article).
No borrowing around any event is computed here."""
import pyarrow.dataset as ds
from _lib2r import *

M2 = pd.read_parquet(OUT / 'book_matches.parquet')
A = pd.read_parquet(OUT / 'articles.parquet')
M2['article_c'] = M2.article.map(dict(zip(A.requested, A.canonical)))
BA = pd.read_parquet(OUT / 'book_author_articles.parquet')
M2['author_article'] = M2.item.map(dict(zip(BA.item, BA.author_article)))
M2[['work_id', 'title', 'creator', 'checkouts_2016_2026', 'item', 'article_c', 'author_article']].rename(columns={'article_c': 'article'}).to_parquet(OUT / 'works.parquet', index=False)
RW = pd.read_parquet(TAXO / 'spl_record_work.parquet')
RW = RW[RW.work_id.isin(set(M2.work_id))]
rids = list(RW.record_id.astype('int64').unique())
log('works', M2.work_id.nunique(), 'records', len(rids))
parts = []
for f, fmt in (('book', 'print'), ('ebook', 'ebook'), ('audiobook', 'audiobook')):
    t = ds.dataset(TAXO / f'spl_rows_{f}.parquet').to_table(filter=ds.field('record_id').isin(rids), columns=['record_id', 'year', 'month', 'checkouts']).to_pandas()
    t['mi'] = t.year.astype(np.int64) * 12 + t.month.astype(np.int64) - 1
    t = t.merge(RW, on='record_id').groupby(['work_id', 'mi'], as_index=False).checkouts.sum()
    t['format'] = fmt
    parts.append(t.rename(columns={'checkouts': 'y'}))
    log(fmt, len(t), 'work-months')
Y = pd.concat(parts, ignore_index=True)
Y = Y[Y.y > 0]
Y['work_id'] = Y.work_id.astype(np.int64); Y['mi'] = Y.mi.astype(np.int64)
Y.to_parquet(OUT / 'counts_work.parquet', index=False)
log('written', len(Y), 'rows; works with any rows', Y.work_id.nunique())
