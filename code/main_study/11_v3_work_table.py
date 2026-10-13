# 11. (v3) Work-level table over all three formats (vectorized; the v2 loop would be too slow for 800k works).
# A work is a normalized title + creator (10); its print records carry library subject headings, and because the
# work key is shared across formats, those headings apply to the same work's audiobook and ebook records too.
# Output (data/db/taxonomy_v3/):
#   spl_works.parquet        one row per work: title, creator, formats, checkouts and first/last month by format
#   spl_record_work.parquet  record id -> work id
#   work_terms.parquet       work x OverDrive subject term (digital records), share of the work's digital checkouts
#   headings.parquet         distinct print subject headings with record, work and checkout counts
#   work_headings.parquet    work x heading, share of the work's print checkouts that carried the heading
import os
os.environ['TAXO'] = 'v3'
import time, numpy as np, pandas as pd
from _common import OUT

t0 = time.time()
R = pd.read_parquet(f'{OUT}/spl_records.parquet', columns=['record_id', 'format', 'title_clean', 'creator', 'subjects', 'pub_year',
                                                            'title_main', 'creator_key', 'work_key', 'creator_from_title'])
R['format'] = R['format'].astype(str)
agg = []
for f in ['audiobook', 'ebook', 'book']:
    x = pd.read_parquet(f'{OUT}/spl_rows_{f}.parquet')
    x['ym'] = x.year.astype(np.int32) * 100 + x.month.astype(np.int32)
    agg.append(x.groupby('record_id').agg(checkouts=('checkouts', 'sum'), n_rows=('ym', 'size'), first_ym=('ym', 'min'), last_ym=('ym', 'max')))
    del x
agg = pd.concat(agg)
R = R.join(agg, on='record_id')
R['work_id'] = pd.factorize(R.work_key)[0].astype(np.int32)
R[['record_id', 'work_id']].to_parquet(f'{OUT}/spl_record_work.parquet', index=False)
print('records', len(R), 'works', R.work_id.max() + 1, round(time.time() - t0), 's', flush=True)

# ---------- work table ----------
# title and creator shown for the work: from its most borrowed record that has a creator (else its most borrowed record)
R['_has_creator'] = R.creator.fillna('') != ''
top = R.sort_values(['work_id', '_has_creator', 'checkouts'], ascending=[True, False, False], kind='mergesort').drop_duplicates('work_id')
W = top[['work_id', 'work_key', 'title_clean', 'creator', 'title_main', 'creator_key']].rename(columns={'title_clean': 'title'}).set_index('work_id')
g = R.groupby(['work_id', 'format']).agg(checkouts=('checkouts', 'sum'), first_ym=('first_ym', 'min'), last_ym=('last_ym', 'max'), n_records=('record_id', 'size'))
for f in ['AUDIOBOOK', 'EBOOK', 'BOOK']:
    gf = g.xs(f, level='format') if f in g.index.get_level_values('format') else pd.DataFrame(columns=g.columns)
    W[f'checkouts_{f.lower()}'] = gf.checkouts.reindex(W.index).fillna(0).astype(np.int64)
    W[f'first_ym_{f.lower()}'] = gf.first_ym.reindex(W.index)
    W[f'last_ym_{f.lower()}'] = gf.last_ym.reindex(W.index)
W['checkouts_total'] = W.checkouts_audiobook + W.checkouts_ebook + W.checkouts_book
W['formats'] = g.reset_index().groupby('work_id').format.agg(lambda s: ','.join(sorted(s))).reindex(W.index)
W['first_ym'] = R.groupby('work_id').first_ym.min().reindex(W.index)
W['last_ym'] = R.groupby('work_id').last_ym.max().reindex(W.index)
W['n_records'] = R.groupby('work_id').size().reindex(W.index)
py = R[R.pub_year > 0].groupby('work_id').pub_year.min()
W['pub_year_min'] = py.reindex(W.index)
W['creator_from_title_only'] = R.groupby('work_id').creator_from_title.min().reindex(W.index)   # True only if every record lacked a creator

# ---------- OverDrive terms (digital records) ----------
d = R[(R.format != 'BOOK') & (R.subjects != '')][['work_id', 'subjects', 'checkouts']].copy()
d['term'] = d.subjects.str.split(', ')
d = d.explode('term')
d['term'] = d.term.str.strip(); d = d[d.term != '']
wt = d.groupby(['work_id', 'term'], as_index=False).checkouts.sum()
dig = R[R.format != 'BOOK'].groupby('work_id').checkouts.sum()
wt['share'] = (wt.checkouts / wt.work_id.map(dig)).fillna(0).clip(upper=1.0).round(4)
wt[['work_id', 'term', 'share']].to_parquet(f'{OUT}/work_terms.parquet', index=False)
W['n_terms'] = wt.groupby('work_id').size().reindex(W.index).fillna(0).astype(int)
del d

# ---------- print headings ----------
p = R[(R.format == 'BOOK') & (R.subjects != '')][['work_id', 'record_id', 'subjects', 'checkouts']].copy()
p['heading'] = p.subjects.str.split(', ')
p = p.explode('heading')
p['heading'] = p.heading.str.strip(); p = p[p.heading != '']
# accented letters in the print subjects were written in the old DOS code page 850 and read as Windows-1252 / Latin-1
# ('Pok‚mon', 'Doppelg„ngers', 'Yucat n'); every non-ASCII character in the field follows this pattern, so it is reversed
def fix_cp850(s):
    if s.isascii():
        return s
    out = []
    for ch in s:
        if ch.isascii():
            out.append(ch); continue
        try:
            b = ch.encode('cp1252')
        except UnicodeEncodeError:
            b = bytes([ord(ch)]) if ord(ch) < 256 else None
        out.append(b.decode('cp850') if b is not None and len(b) == 1 else ch)
    return ''.join(out)
uh = pd.Series(p.heading.unique()); fixed = dict(zip(uh, uh.map(fix_cp850)))
print('headings with repaired accents', sum(a != b for a, b in fixed.items()), flush=True)
p['heading'] = p.heading.map(fixed)
H = p.groupby('heading').agg(n_records=('record_id', 'nunique'), n_works=('work_id', 'nunique'), checkouts=('checkouts', 'sum')).reset_index()
H = H.sort_values(['n_works', 'heading'], ascending=[False, True]).reset_index(drop=True)
H['heading_id'] = np.arange(len(H), dtype=np.int32)
H.to_parquet(f'{OUT}/headings.parquet', index=False)
p = p.merge(H[['heading', 'heading_id']], on='heading')
wh = p.groupby(['work_id', 'heading_id'], as_index=False).checkouts.sum()
prt = R[R.format == 'BOOK'].groupby('work_id').checkouts.sum()
wh['share'] = (wh.checkouts / wh.work_id.map(prt)).fillna(0).clip(upper=1.0).round(4)
wh[['work_id', 'heading_id', 'share']].to_parquet(f'{OUT}/work_headings.parquet', index=False)
W['n_headings'] = wh.groupby('work_id').size().reindex(W.index).fillna(0).astype(int)
del p
W = W.reset_index()
W.to_parquet(f'{OUT}/spl_works.parquet', index=False)
fm = W.formats.value_counts()
print('works', len(W), fm.to_dict(), flush=True)
dg = W[W.formats.str.contains('AUDIOBOOK|EBOOK')]
print('digital works', len(dg), 'with print headings', int((dg.n_headings > 0).sum()),
      'share of digital checkouts', round(dg[dg.n_headings > 0][['checkouts_audiobook', 'checkouts_ebook']].sum().sum() / dg[['checkouts_audiobook', 'checkouts_ebook']].sum().sum(), 4), flush=True)
print('distinct headings', len(H), 'heading-work pairs', len(wh), round(time.time() - t0), 's', flush=True)
