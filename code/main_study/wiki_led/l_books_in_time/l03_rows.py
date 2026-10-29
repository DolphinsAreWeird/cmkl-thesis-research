# l03. Addendum l, step 2: rows and features of the frame "books chosen in time".  Settings: prereg/addenda_wiki_led/
# 2026-10-30_l_books_in_time.json, L1 rows, L2 (read-only; SHA-256 checked).  DATA ONLY: nothing is fitted; the report has counts.
#
# Rows: the definitions of code/main_study/wiki_led/60c_test_d_rows.py (one series per work and format; eligible at origin t when its
#   loans over t-11..t, excluded months skipped, sum to at least 24; L_t, L_next, M6, h_lt, h_lt1, h_m6, h_m12, h_lyago, h_age, D, Sg, Y,
#   loans12; months before a series' first loan missing; excluded months missing inside windows), copied, for the sampled works of
#   step 1 only (Test D's 25% sample without the placeholder works; no Test A work outside the sample).  Origins 2016-03 to 2026-08:
#   2026-08 only for the frozen forecasts (no target exists, so L_next, D, Sg and Y are missing there).
#   Check: on origins to 2026-07 every row and value must equal data/db/wiki_led/test_d_rows_c.parquet restricted to these works.
# Wikipedia features: b_* from the work's book article and a_* from its author article (step 1, work_articles.parquet), from
#   data/db/wiki_led/l_books_in_time/wiki_features.parquet; missing when the work has no article or no features at that origin.
# Calendar (L2): cal_month = calendar month of the target month t+1 (1 to 12), cal_days = its number of days.
# Output: data/db/wiki_led/l_books_in_time/rows.parquet; report data/reports/wiki_led_l_rows.md
#   Run from code/:  bash ../jobs/bg.sh wl_l03 main_study/wiki_led/l_books_in_time/l03_rows.py
import sys, os, time, json, calendar, hashlib, pathlib, warnings
import numpy as np, pandas as pd, pyarrow.parquet as pq

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-30_l_books_in_time.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == '36778f86ced0550c90e8578813ae476c6ae1d4d7220c430ef140244e5d5e028a', 'addendum l changed'
TAXO = DATA / 'db' / 'taxonomy_v3'
OUT = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
REP = DATA / 'reports'
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def ym_of(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


ORIG0, ORIG1, OFREEZE = mi_of('2016-03'), mi_of('2026-07'), mi_of('2026-08')
MI0, MI1 = mi_of('2005-04'), mi_of('2026-08')
NM, NORIG = MI1 - MI0 + 1, OFREEZE - ORIG0 + 1
MIN_LOANS = 24
LN2 = np.log(2)
FORMATS = [('print', 'book'), ('ebook', 'ebook'), ('audiobook', 'audiobook')]
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
HIST = ['L_t', 'L_next', 'M6', 'h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'D', 'Sg', 'Y', 'loans12']

P = pd.read_parquet(DATA / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok']).drop_duplicates(['format', 'mi'])
EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= mi_of('2015-01')}
assert EXCL == {mi_of(x) for x in ['2020-04', '2020-05', '2020-06', '2020-07', '2020-08', '2020-09', '2024-05', '2024-06', '2024-07', '2025-08']}
EXMASK = np.isin(np.arange(MI0, MI1 + 1), sorted(EXCL))
ORIGINS = [m for m in range(ORIG0, OFREEZE + 1) if m not in EXCL and (m + 1) not in EXCL]

WA = pd.read_parquet(OUT / 'work_articles.parquet')
S_ids = np.sort(WA.work_id.to_numpy(np.int64))
NS = len(S_ids)
WA = WA.set_index('work_id').reindex(S_ids)
WF = pd.read_parquet(OUT / 'wiki_features.parquet')
arrs = {}
for kind, col in (('book', 'book_canonical'), ('author', 'author_canonical')):
    g = WF[WF.kind == kind]
    names = sorted(g.article.unique()); pos = {n: i for i, n in enumerate(names)}
    arr = np.full((len(names) + 1, NORIG, len(FEATS)), np.nan, np.float32)
    arr[g.article.map(pos).to_numpy(), g.mi.to_numpy() - ORIG0, :] = g[FEATS].to_numpy(np.float32)
    idx = WA[col].map(pos).fillna(len(names)).to_numpy(np.int64)
    arrs[kind] = (arr, idx)
    log(kind, 'articles with features', len(names), '| works linked', int((idx < len(names)).sum()))
del WF

rw = pd.read_parquet(TAXO / 'spl_record_work.parquet')
rid_all, wid_all = rw.record_id.to_numpy(np.int64), rw.work_id.to_numpy(np.int64)
p = np.searchsorted(S_ids, wid_all); p[p >= NS] = 0
inS = S_ids[p] == wid_all
LUT = np.full(int(rid_all.max()) + 1, -1, np.int32); LUT[rid_all[inS]] = p[inS]
del rw, rid_all, wid_all, p, inS


def median_skipna(x):
    s = np.sort(x, axis=1)
    n = (~np.isnan(x)).sum(axis=1)
    r = np.arange(len(x))
    med = (s[r, np.maximum(n - 1, 0) // 2] + s[r, n // 2]) / np.float32(2)
    med[n == 0] = np.nan
    return med.astype(np.float32)


parts = []
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
    pos = A > 0
    first = pos.argmax(axis=1)
    A[np.arange(NM)[None, :] < first[:, None]] = np.nan
    first_mi = (first + MI0).astype(np.int64)
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
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            m12 = np.nanmean(w12, axis=1)
        Lt = S12[:, 11].copy()
        Ln = A[idx, j + 1].copy() if j + 1 < NM else np.full(len(idx), np.nan, np.float32)
        Lt1, Lya = np.nan_to_num(S12[:, 10]), np.nan_to_num(S12[:, 0])
        good = ~np.isnan(M6) & ~np.isnan(Lt) & (~np.isnan(Ln) if m < OFREEZE else True)
        idx, Lt, Ln, Lt1, Lya, M6, m12 = idx[good], Lt[good], Ln[good], Lt1[good], Lya[good], M6[good], m12[good]
        l12 = masked12[idx].astype(np.float32)
        n = len(idx)
        if n == 0:
            continue
        Dv = np.log1p(Ln) - np.log1p(M6)
        tm = (m + 1) % 12 + 1
        row = {'work_id': S_ids[idx], 'format': label, 'mi': np.full(n, m, np.int32), 'year': np.full(n, (m + 1) // 12, np.int16),
               'L_t': Lt, 'L_next': Ln, 'M6': M6, 'h_lt': np.log1p(Lt), 'h_lt1': np.log1p(Lt1), 'h_m6': np.log1p(M6),
               'h_m12': np.log1p(m12), 'h_lyago': np.log1p(Lya), 'h_age': (m - first_mi[idx]).astype(np.float32),
               'D': Dv, 'Sg': np.where(np.isnan(Ln), -1, ((Dv >= LN2) & ((Ln - M6) >= 5))).astype(np.int8), 'Y': np.log1p(Ln),
               'loans12': l12, 'cal_month': np.full(n, tm, np.int8),
               'cal_days': np.full(n, calendar.monthrange((m + 1) // 12, tm)[1], np.int8)}
        for kind, pre in (('book', 'b_'), ('author', 'a_')):
            arr, aidx = arrs[kind]
            v = arr[aidx[idx], m - ORIG0]
            for k, c in enumerate(FEATS):
                row[pre + c] = v[:, k]
        parts.append(pd.DataFrame(row))
    log(label, 'rows so far', sum(len(x) for x in parts))
    del A
R = pd.concat(parts, ignore_index=True)
R['format'] = R.format.astype('category')
R['has_book_page'] = R[[f'b_{c}' for c in FEATS]].notna().any(axis=1).astype(np.int8)
R['has_author_page'] = R[[f'a_{c}' for c in FEATS]].notna().any(axis=1).astype(np.int8)
R.to_parquet(OUT / 'rows.parquet', index=False)

# ---------------------------------------------------------------- check against Test D's stored rows (origins to 2026-07)
TD = pd.read_parquet(DATA / 'db' / 'wiki_led' / 'test_d_rows_c.parquet', columns=['work_id', 'format', 'mi'] + HIST)
TD = TD[TD.work_id.isin(S_ids)]
TD['format'] = TD.format.astype(str)
mine = R[R.mi <= ORIG1].assign(format=lambda x: x.format.astype(str))
key = ['work_id', 'format', 'mi']
cm = mine[key + HIST].merge(TD, on=key, how='outer', suffixes=('', '_td'), indicator=True)
only_mine, only_td = int((cm._merge == 'left_only').sum()), int((cm._merge == 'right_only').sum())
both = cm[cm._merge == 'both']
maxdiff = max(float(np.nanmax(np.abs(both[c].astype(float) - both[c + '_td'].astype(float)))) for c in HIST)
log('check against Test D: rows here', len(mine), '| Test D rows of these works', len(TD), '| only here', only_mine, '| only Test D', only_td,
    '| largest difference', maxdiff)
assert only_mine == 0 and only_td == 0 and maxdiff == 0.0, 'rows do not reproduce Test D'

sc = R[(R.mi >= mi_of('2019-01')) & (R.mi <= ORIG1)]
fz = R[R.mi == OFREEZE]
summ = dict(works=NS, rows=len(R), rows_backtest=int((R.mi <= ORIG1).sum()), rows_scored=len(sc), rows_freeze=len(fz),
            by_format=R.format.value_counts().to_dict(), works_with_rows=int(R.work_id.nunique()),
            scored_rows_with_book_feature=int(sc.has_book_page.sum()), scored_rows_with_author_feature=int(sc.has_author_page.sum()),
            scored_rows_with_either=int((sc.has_book_page | sc.has_author_page).sum()),
            freeze_rows_with_either=int((fz.has_book_page | fz.has_author_page).sum()),
            check=dict(only_here=only_mine, only_test_d=only_td, max_diff=maxdiff), runtime_s=round(time.time() - T0))
(OUT / 'rows_summary.json').write_text(json.dumps(summ, indent=1, default=str))
pc = lambda k, n: f'{k:,} of {n:,} ({100 * k / max(n, 1):.1f}%)'
Lr = ['# Addendum l, step 2: rows of the frame "books chosen in time"', '',
      f'Made by `code/main_study/wiki_led/l_books_in_time/l03_rows.py` on {time.strftime("%Y-%m-%d %H:%M")} (local time, UTC+06:30). '
      'Data only: counts, no model and no relation between a feature and an outcome.', '',
      f'- Works: {NS:,} (Test D\'s 25% sample without the placeholder works); works with at least one row: {summ["works_with_rows"]:,}.',
      f'- Rows: {len(R):,}; backtest origins 2016-03 to 2026-07: {summ["rows_backtest"]:,}, of which scored (origins from 2019-01): {len(sc):,}; '
      f'origin 2026-08 (frozen forecasts only): {len(fz):,}. By format: {summ["by_format"]}.',
      f'- Scored rows with a book-article feature: {pc(summ["scored_rows_with_book_feature"], len(sc))}; with an author-article feature: '
      f'{pc(summ["scored_rows_with_author_feature"], len(sc))}; with either: {pc(summ["scored_rows_with_either"], len(sc))}.',
      f'- Rows at origin 2026-08 with either: {pc(summ["freeze_rows_with_either"], len(fz))}.',
      f'- Check: on origins to 2026-07 the rows and the values of {", ".join(HIST)} equal Test D\'s stored rows for these works '
      f'(rows only here {only_mine}, only in Test D {only_td}, largest difference {maxdiff}).',
      f'- Run time {summ["runtime_s"]} s.']
(REP / 'wiki_led_l_rows.md').write_text('\n'.join(Lr) + '\n')
log(json.dumps(summ, default=str))
