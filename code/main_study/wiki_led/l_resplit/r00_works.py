# r00. Five-seed reruns, part 2 (re-drawn samples of works): the works of each quarter of the catalogue.
# Record: prereg/DEVIATIONS.md, "Five-seed reruns asked for by the advisor (20 November 2026)", part 2 rules 1 and 2 (written first).
# Quarters by the first hex digit of md5(str(work_id)): q0 0-3 (the main set), q1 4-7, q2 8-b, q3 c-f.  Works of a quarter: works of
#   spl_works.parquet in it, without the placeholder works, with at least one row under the row rule of l03_rows.py (copied below:
#   12-month loans with excluded months skipped >= 24, six-month median, this month's and next month's loans present) at an origin
#   from 2016-03 to 2026-07.  DATA ONLY: loans are read for the row rule; no model, no outcome relation.
# Check: q0 must give exactly the 43,298 works of the main set (data/db/wiki_led/l_books_in_time/work_articles.parquet).
# Output: data/db/wiki_led/l_resplit/q<k>/works.parquet (work_id), data/db/wiki_led/l_resplit/works_summary.json
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/l_resplit/r00_works.py
import sys, os, time, json, hashlib, pathlib, warnings
import numpy as np, pandas as pd, pyarrow.parquet as pq

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
TAXO = DATA / 'db' / 'taxonomy_v3'
OUT = DATA / 'db' / 'wiki_led' / 'l_resplit'
QUARTERS = {0: '0123', 1: '4567', 2: '89ab', 3: 'cdef'}
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


# ---------------------------------------------------------------- constants of l03_rows.py
ORIG0, ORIG1, OFREEZE = mi_of('2016-03'), mi_of('2026-07'), mi_of('2026-08')
MI0, MI1 = mi_of('2005-04'), mi_of('2026-08')
NM = MI1 - MI0 + 1
MIN_LOANS = 24
FORMATS = [('print', 'book'), ('ebook', 'ebook'), ('audiobook', 'audiobook')]
P = pd.read_parquet(DATA / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok']).drop_duplicates(['format', 'mi'])
EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= mi_of('2015-01')}
assert EXCL == {mi_of(x) for x in ['2020-04', '2020-05', '2020-06', '2020-07', '2020-08', '2020-09', '2024-05', '2024-06', '2024-07', '2025-08']}
EXMASK = np.isin(np.arange(MI0, MI1 + 1), sorted(EXCL))
ORIGINS = [m for m in range(ORIG0, ORIG1 + 1) if m not in EXCL and (m + 1) not in EXCL]     # backtest origins only (to 2026-07)


def median_skipna(x):
    s = np.sort(x, axis=1)
    n = (~np.isnan(x)).sum(axis=1)
    r = np.arange(len(x))
    med = (s[r, np.maximum(n - 1, 0) // 2] + s[r, n // 2]) / np.float32(2)
    med[n == 0] = np.nan
    return med.astype(np.float32)


W = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id'])
ph = set(pd.read_csv(TAXO / 'quality' / 'placeholder_works.csv').work_id)
W['q'] = [int(hashlib.md5(str(int(w)).encode()).hexdigest()[0], 16) // 4 for w in W.work_id]
rw = pd.read_parquet(TAXO / 'spl_record_work.parquet')
rid_all, wid_all = rw.record_id.to_numpy(np.int64), rw.work_id.to_numpy(np.int64)
del rw
summ = dict(catalogue_works=int(len(W)), placeholder_works=len(ph), quarters={})
for q, digits in QUARTERS.items():
    S_ids = np.sort(W.loc[(W.q == q) & ~W.work_id.isin(ph), 'work_id'].to_numpy(np.int64))
    NS = len(S_ids)
    p = np.searchsorted(S_ids, wid_all); p[p >= NS] = 0
    inS = S_ids[p] == wid_all
    LUT = np.full(int(rid_all.max()) + 1, -1, np.int32); LUT[rid_all[inS]] = p[inS]
    has_row = np.zeros(NS, bool)
    for label, fname in FORMATS:
        pf = pq.ParquetFile(TAXO / f'spl_rows_{fname}.parquet')
        A = np.zeros((NS, NM), np.float32)
        for g in range(pf.num_row_groups):
            t = pf.read_row_group(g, columns=['record_id', 'year', 'month', 'checkouts'])
            w = LUT[t.column('record_id').to_numpy()]
            mc = t.column('year').to_numpy().astype(np.int32) * 12 + t.column('month').to_numpy().astype(np.int32) - 1 - MI0
            k = w >= 0
            if k.any():
                np.add.at(A, (w[k], mc[k]), t.column('checkouts').to_numpy()[k])
        first = (A > 0).argmax(axis=1)
        A[np.arange(NM)[None, :] < first[:, None]] = np.nan
        for m in ORIGINS:
            j = m - MI0
            win = A[:, j - 11:j + 1]
            ex12 = EXMASK[j - 11:j + 1]
            masked12 = np.nansum(win[:, ~ex12], axis=1, dtype=np.float64) if ex12.any() else np.nansum(win, axis=1, dtype=np.float64)
            idx = np.flatnonzero(masked12 >= MIN_LOANS)
            if len(idx) == 0:
                continue
            S12 = A[idx, j - 11:j + 1]
            w12 = S12.copy(); w12[:, ex12] = np.nan
            M6 = median_skipna(w12[:, 6:])
            Lt = S12[:, 11]
            Ln = A[idx, j + 1]
            good = ~np.isnan(M6) & ~np.isnan(Lt) & ~np.isnan(Ln)
            has_row[idx[good]] = True
        log('quarter', q, label, 'works with a row so far', int(has_row.sum()))
        del A
    works = S_ids[has_row]
    (OUT / f'q{q}').mkdir(parents=True, exist_ok=True)
    pd.DataFrame({'work_id': works}).to_parquet(OUT / f'q{q}' / 'works.parquet', index=False)
    summ['quarters'][str(q)] = dict(digits=digits, catalogue_works_without_placeholders=int(NS), works_with_a_row=int(len(works)))
    log('quarter', q, summ['quarters'][str(q)])

main = set(pd.read_parquet(DATA / 'db' / 'wiki_led' / 'l_books_in_time' / 'work_articles.parquet').work_id.astype(int))
q0 = set(pd.read_parquet(OUT / 'q0' / 'works.parquet').work_id.astype(int))
summ['check_q0'] = dict(main_set_works=len(main), q0_works=len(q0), only_main=len(main - q0), only_q0=len(q0 - main))
summ['runtime_s'] = round(time.time() - T0)
(OUT / 'works_summary.json').write_text(json.dumps(summ, indent=1))
log('check q0 against the main set', summ['check_q0'])
assert main == q0, 'q0 does not reproduce the main set'
log('done')
