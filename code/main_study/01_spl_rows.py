# 01. Stream the SPL raw files once (line by line, frozen line count for the growing ebook file) and write
# compact Parquet tables that every later script reads:
#   spl_records.parquet  one row per distinct source record (format, raw title, creator, subjects, publisher,
#                        publication year, isbn) with normalized title / creator / work key
#   spl_rows.parquet     one row per raw line: record id, year, month, checkouts, usage class
# Raw files are only read, never written.
import array, time, pandas as pd, numpy as np, pyarrow as pa, pyarrow.parquet as pq
from _common import OUT, snapshot, iter_rows, clean_title, title_parts, norm_creator, creator_match_key, assign_work_keys

t0 = time.time()
snap = snapshot()
print('snapshot', snap, flush=True)
rec_index = {}     # key tuple -> record id (shared across formats so ids are unique)
rec_list = []
for fmt in ['AUDIOBOOK', 'EBOOK']:
    rid = array.array('i'); yr = array.array('h'); mo = array.array('b'); co = array.array('i'); uc = array.array('b')
    ucls = {}
    for n, r in enumerate(iter_rows(fmt, snap)):
        key = (fmt, r.get('title') or '', r.get('creator') or '', r.get('subjects') or '', r.get('publisher') or '',
               r.get('publicationyear') or '', r.get('isbn') or '')
        i = rec_index.get(key)
        if i is None:
            i = len(rec_list); rec_index[key] = i; rec_list.append(key)
        rid.append(i)
        try:
            yr.append(int(r.get('checkoutyear') or 0)); mo.append(int(r.get('checkoutmonth') or 0))
        except ValueError:
            yr.append(0); mo.append(0)
        co.append(int(float(r.get('checkouts') or 0)))
        u = r.get('usageclass') or ''
        uc.append(ucls.setdefault(u, len(ucls)))
        if n % 1000000 == 0:
            print(fmt, n, len(rec_list), round(time.time() - t0), 's', flush=True)
    inv = {v: k for k, v in ucls.items()}
    t = pa.table({'record_id': pa.array(np.frombuffer(rid, dtype=np.int32)),
                  'year': pa.array(np.frombuffer(yr, dtype=np.int16)),
                  'month': pa.array(np.frombuffer(mo, dtype=np.int8)),
                  'checkouts': pa.array(np.frombuffer(co, dtype=np.int32)),
                  'usageclass': pa.DictionaryArray.from_arrays(pa.array(np.frombuffer(uc, dtype=np.int8)), pa.array([inv[k] for k in range(len(inv))])),
                  'format': pa.DictionaryArray.from_arrays(pa.array(np.zeros(len(rid), dtype=np.int8)), pa.array([fmt]))})
    pq.write_table(t, f'{OUT}/spl_rows_{fmt.lower()}.parquet')
    print(fmt, 'rows', len(rid), 'records so far', len(rec_list), round(time.time() - t0), 's', flush=True)
    del rid, yr, mo, co, uc, t

R = pd.DataFrame(rec_list, columns=['format', 'title', 'creator', 'subjects', 'publisher', 'publicationyear', 'isbn'])
R.insert(0, 'record_id', np.arange(len(R), dtype=np.int32))
del rec_index, rec_list
R['title_clean'] = R.title.map(clean_title)
tp = [title_parts(t) for t in R.title]
R['title_main'] = [x[0] for x in tp]; R['title_sub'] = [x[1] for x in tp]
R['creator_key'] = R.creator.map(norm_creator)
R['creator_match'] = R.creator_key.map(creator_match_key)     # first + last name: middle names and initials do not split a work
R['work_key'] = assign_work_keys(R.title_main, R.title_sub, R.creator_match)
for c in ['format']:
    R[c] = R[c].astype('category')
R.to_parquet(f'{OUT}/spl_records.parquet', index=False)
print('records', len(R), 'works', R.work_key.nunique(), round(time.time() - t0), 's', flush=True)
