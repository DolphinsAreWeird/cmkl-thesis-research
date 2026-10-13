# 10. (v3) Stream all three SPL files (audiobook, full ebook, print books up to the frozen line count) into compact
# Parquet tables in data/db/taxonomy_v3/:
#   spl_rows_{audiobook,ebook,book}.parquet   one row per raw line: record id, year, month, checkouts
#   spl_records.parquet                       one row per distinct source record, with normalized title, creator and
#                                             the work key shared across formats (so print headings reach the same
#                                             work's audiobook and ebook records)
# Print rows have no ISBN, and about half have no creator: then the creator is taken from the title's statement of
# responsibility ('A dangerous friend / Ward Just.'). Print records are keyed by title, creator and subjects only
# (publisher and year vary by copy and are not needed), and new records are written out in parts so memory stays low.
import os
os.environ['TAXO'] = 'v3'
import re, json, array, time, glob
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq
from _common import OUT, snapshot, iter_rows, clean_title, title_parts, norm_creator, creator_match_key, assign_work_keys, FILES

t0 = time.time()
snap = snapshot()
print('snapshot', snap, flush=True)
PARTS = f'{OUT}/_record_parts'; os.makedirs(PARTS, exist_ok=True)
for f in glob.glob(f'{PARTS}/*.parquet'):
    os.remove(f)


def pubyear(x):
    m = re.search(r'(1[5-9]\d\d|20[0-3]\d)', str(x or ''))
    return int(m.group(1)) if m else -1


def creator_from_title(t):
    """'A dangerous friend / Ward Just.' -> 'Ward Just'; '... / story and pictures by Maurice Sendak.' -> 'Maurice Sendak';
    '... / taken from accounts by his own hand ; collected by M.T. Anderson of Boston.' -> 'M.T. Anderson'.
    The first part of the statement (before ';') that names a person wins, so translators and illustrators are skipped."""
    if ' / ' not in str(t):
        return ''
    found = ''
    for seg in re.split(r'\s*[;=]\s*', str(t).split(' / ', 1)[1]):
        seg = re.sub(r'\[.*?\]', '', seg).strip()
        m = re.search(r'\bby\s+(.+)$', seg)
        if m and m.group(1)[:1].isupper():
            found = m.group(1); break
        if not m and seg[:1].isupper():
            found = seg; break
    r = re.split(r'\s*,\s*(?:illustrated|translated|edited|with|and)\b|\s+(?:with|and)\s+(?:illustrations|photographs|pictures)\b', found, maxsplit=1)[0]
    r = re.sub(r'\s+of\s+[A-Z][a-z]+\.?$', '', r.strip())
    r = re.sub(r'\b(?:et al|and others)\b.*$', '', r, flags=re.I)
    return r.strip(' .,:')


def write_part(recs, k):
    if not recs:
        return
    d = pd.DataFrame(recs, columns=['record_id', 'format', 'title', 'creator', 'creator_from_title', 'subjects', 'publisher', 'publicationyear', 'isbn', 'pub_year'])
    tp = [title_parts(t) for t in d.title]
    d['title_clean'] = [clean_title(t) for t in d.title]
    d['title_main'] = [x[0] for x in tp]; d['title_sub'] = [x[1] for x in tp]
    d['creator_key'] = d.creator.map(norm_creator)
    d['creator_match'] = d.creator_key.map(creator_match_key)
    d.to_parquet(f'{PARTS}/part_{k:04d}.parquet', index=False)


next_id = 0; part = 0
# ---------- digital formats: every field is part of the record key, as in v2 ----------
for fmt in ['AUDIOBOOK', 'EBOOK']:
    idx = {}; recs = []
    rid = array.array('i'); yr = array.array('h'); mo = array.array('b'); co = array.array('i')
    for n, r in enumerate(iter_rows(fmt, snap)):
        key = (r.get('title') or '', r.get('creator') or '', r.get('subjects') or '', r.get('publisher') or '',
               r.get('publicationyear') or '', r.get('isbn') or '')
        i = idx.get(key)
        if i is None:
            i = next_id; next_id += 1; idx[key] = i
            recs.append((i, fmt, key[0], key[1], False, key[2], key[3], key[4], key[5], pubyear(key[4])))
            if len(recs) >= 200000:
                write_part(recs, part); part += 1; recs = []
        rid.append(i); yr.append(int(r.get('checkoutyear') or 0)); mo.append(int(r.get('checkoutmonth') or 0))
        co.append(int(float(r.get('checkouts') or 0)))
        if n % 2000000 == 0:
            print(fmt, n, next_id, round(time.time() - t0), 's', flush=True)
    write_part(recs, part); part += 1
    pq.write_table(pa.table({'record_id': np.frombuffer(rid, dtype=np.int32), 'year': np.frombuffer(yr, dtype=np.int16),
                             'month': np.frombuffer(mo, dtype=np.int8), 'checkouts': np.frombuffer(co, dtype=np.int32)}),
                   f'{OUT}/spl_rows_{fmt.lower()}.parquet')
    print(fmt, 'rows', len(rid), 'records', len(idx), round(time.time() - t0), 's', flush=True)
    del idx, rid, yr, mo, co

# ---------- print books: key = title, creator, subjects; 64-bit hash of the key -> record id ----------
fmt = 'BOOK'
idx = {}; recs = []
rid = array.array('i'); yr = array.array('h'); mo = array.array('b'); co = array.array('i')
for n, r in enumerate(iter_rows(fmt, snap)):
    t = r.get('title') or ''; c = r.get('creator') or ''; s = r.get('subjects') or ''
    h = hash((t, c, s))
    i = idx.get(h)
    if i is None:
        i = next_id; next_id += 1; idx[h] = i
        cf = c == ''
        recs.append((i, fmt, t, c or creator_from_title(t), cf, s, '', r.get('publicationyear') or '', '', pubyear(r.get('publicationyear'))))
        if len(recs) >= 200000:
            write_part(recs, part); part += 1; recs = []
    rid.append(i); yr.append(int(r.get('checkoutyear') or 0)); mo.append(int(r.get('checkoutmonth') or 0))
    co.append(int(float(r.get('checkouts') or 0)))
    if n % 2000000 == 0:
        print(fmt, n, len(idx), round(time.time() - t0), 's', flush=True)
write_part(recs, part); part += 1
pq.write_table(pa.table({'record_id': np.frombuffer(rid, dtype=np.int32), 'year': np.frombuffer(yr, dtype=np.int16),
                         'month': np.frombuffer(mo, dtype=np.int8), 'checkouts': np.frombuffer(co, dtype=np.int32)}),
               f'{OUT}/spl_rows_book.parquet')
print(fmt, 'rows', len(rid), 'records', len(idx), round(time.time() - t0), 's', flush=True)
del idx, rid, yr, mo, co

# ---------- all records together: work keys shared across formats ----------
R = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f'{PARTS}/*.parquet'))], ignore_index=True).sort_values('record_id').reset_index(drop=True)
R['work_key'] = assign_work_keys(R.title_main, R.title_sub, R.creator_match)
# Records with no creator at all (about half of the print records, mostly 2005-2006 rows) would each form a separate
# 'title |' work. Such a record joins a work that has a creator when (a) exactly one work with a creator has the same
# full title (main + subtitle) and (b) that work was already being borrowed while the creator-less record was.
span = []
for f in ['audiobook', 'ebook', 'book']:
    x = pd.read_parquet(f'{OUT}/spl_rows_{f}.parquet', columns=['record_id', 'year', 'month'])
    x['ym'] = x.year.astype(np.int32) * 100 + x.month.astype(np.int32)
    span.append(x.groupby('record_id').ym.agg(['min', 'max']))
    del x
span = pd.concat(span)
R['first_ym'] = R.record_id.map(span['min']); R['last_ym'] = R.record_id.map(span['max'])
# old rows often lost the colon between title and subtitle, so titles are compared flattened (main + subtitle as one
# string); a creator-less record without a subtitle may also match on the main title alone
R['full_title'] = (R.title_main + ' ' + R.title_sub).str.strip()
noc = R.creator_match.isin(['', 'various', 'various authors', 'anonymous', 'unknown', 'anon'])
wfirst = R[~noc].groupby('work_key').first_ym.min()
def unique_targets(keycol):
    c = R[~noc].groupby(keycol).agg(n_works=('work_key', 'nunique'), work_key=('work_key', 'first'))
    return c[c.n_works == 1].work_key
t_full = unique_targets('full_title'); t_main = unique_targets('title_main')
m = R[noc].copy()
m['target'] = m.full_title.map(t_full)
alt = m.target.isna() & (m.title_sub == '')
m.loc[alt, 'target'] = m.loc[alt, 'title_main'].map(t_main)
m = m[m.target.notna()]
ok = m.target.map(wfirst) <= m.last_ym
R.loc[m.index[ok.values], 'work_key'] = m.target[ok].values
R['merged_no_creator'] = False; R.loc[m.index[ok.values], 'merged_no_creator'] = True
print('creator-less records', int(noc.sum()), 'joined to a work with a creator', int(ok.sum()), flush=True)
# Creator-less records that found no such work stay on the bare 'title |' key. For print records this put different books
# with the same short title together (first run: 'Legacy' had 42 records with 33 different first headings and picked up
# 36 narrow themes; the placeholder title '<Unknown Title>' had 2,644 records). So (a) a placeholder title is one work per
# record, whatever the creator; (b) a creator-less print record that was not joined is grouped by title + its first subject
# heading (editions of one book usually share the first heading; splitting one book in two does no harm to its themes,
# merging two books does); (c) a creator-less digital record joins the print group with the same title only when there is
# exactly one such group, otherwise it stays on its own.
base = R.work_key.copy()
left = noc & ~R.merged_no_creator
isbook = R['format'].astype(str) == 'BOOK'
placeholder = R.title_main.str.strip().isin(['', 'unknown title', 'untitled', 'title unknown'])
first_head = R.subjects.fillna('').str.split(', ').str[0].fillna('').str.strip().str.lower()
pb = left & isbook & ~placeholder
R.loc[pb, 'work_key'] = base[pb] + ' #h ' + first_head[pb]
R.loc[placeholder, 'work_key'] = base[placeholder] + ' #r ' + R.loc[placeholder, 'record_id'].astype(str)
grp = pd.DataFrame({'base': base[pb], 'key': R.work_key[pb]}).groupby('base').key.agg(['nunique', 'first'])
one = grp[grp['nunique'] == 1]['first']
pdg = left & ~isbook & ~placeholder
tgt = base[pdg].map(one)
R.loc[tgt[tgt.notna()].index, 'work_key'] = tgt[tgt.notna()].values
R['no_creator_rule'] = ''
R.loc[R.merged_no_creator, 'no_creator_rule'] = 'joined a work with a creator'
R.loc[pb, 'no_creator_rule'] = 'print: title + first heading'
R.loc[tgt[tgt.notna()].index, 'no_creator_rule'] = 'digital: joined the one print group'
R.loc[pdg & R.no_creator_rule.eq(''), 'no_creator_rule'] = 'digital: title only'
R.loc[placeholder, 'no_creator_rule'] = 'placeholder title: one work per record'
print('creator-less rules', R.no_creator_rule.value_counts().to_dict(), flush=True)
R = R.drop(columns=['first_ym', 'last_ym', 'full_title'])
R['format'] = R['format'].astype('category')
R.to_parquet(f'{OUT}/spl_records.parquet', index=False)
for f in glob.glob(f'{PARTS}/*.parquet'):
    os.remove(f)
os.rmdir(PARTS)
print('records', len(R), R.groupby('format', observed=True).size().to_dict(), 'works', R.work_key.nunique(), round(time.time() - t0), 's', flush=True)
