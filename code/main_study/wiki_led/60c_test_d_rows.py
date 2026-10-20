# 60c. Test D rows, CORRECTED RERUN (addendum e, prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json): 60_test_d_rows.py reading the
# Wikipedia features of the corrected Test A (data/db/wiki_led/test_a_wiki_features_c.parquet, made by 10c_test_a.py with correction A1:
# weeks before an article's first week with views are missing) and comparing its rows with test_a_rows_c.parquet.  Nothing else changed: the
# sample of works, the loans, the excluded months, the eligibility rule and the checks are those of 60_test_d_rows.py.  Output files carry
# the suffix _c: data/db/wiki_led/test_d_rows_c.parquet and data/reports/wiki_led_test_d_data_c.md (the 1% test mode writes to
# data/interim/wiki_led_test_d_1pct_c/).   Full run: bash jobs/bg.sh wl_test_d_data_c main_study/wiki_led/60c_test_d_rows.py   (from handoff/)
# The original files and this script's source of 60_test_d_rows.py stay on file.
#
# Original header of 60_test_d_rows.py:
# 60. Test D rows (all books, by format): the data for "do the Test A models keep their accuracy on (nearly) all library books,
# and in each format separately?"  Settings: prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json, section test_D_all_books
# (rows), and the build request of 20 Oct 2026.  Test A's definitions (10_test_a.py) are used for L, M6, D, Sg, Y, the history
# features, the excluded months and the origins.
# DATA ONLY: nothing here fits a model or relates a feature to an outcome.  The report has counts and distributions of single columns.
#
# Units: one series per (work, format) for print (the 'book' row files), ebook and audiobook, for a fixed 25% sample of the works in
#   data/db/taxonomy_v3/spl_works.parquet (first hex digit of md5(str(work_id)) is 0, 1, 2 or 3) plus all 7,747 Test A works
#   (data/db/study2r/works.parquet, flag in_test_a).  Monthly loans = sum of checkouts of all records of the work in that format
#   (spl_rows_*.parquet through spl_record_work.parquet).  Months before the series' first loan are missing; later months without
#   a row are 0.  A month is excluded (missing, never an origin or target) when month_ok is False for any format in
#   data/db/study3/demand_panel.parquet (benchmark rule; 2020-04 to 2020-09, 2024-05 to 2024-07, 2025-08).
# Origins t: months 2016-03 to 2026-07 whose t and t+1 are not excluded.  A series is eligible at t when its loans over t-11..t sum
#   to at least 24.  Per row (Test A): L_t, L_next (month t+1), M6 (median of L over t-5..t skipping missing months), h_lt, h_lt1,
#   h_m6, h_m12 (mean over t-11..t skipping missing months), h_lyago, h_age, D, Sg, Y; year = year of the target month.
# Wikipedia features (data/db/wiki_led/test_a_wiki_features_c.parquet, corrected): b_* for Test A works (their article); a_* for any sampled
#   work whose creator_key equals the creator_key of a Test A work with an author article; missing otherwise.
#
# Choices where the request left room (also written to the report):
#   (1) eligibility: the 12-month sum skips excluded months (they are missing inside windows, as for M6 and the 12-month mean).
#       --elig raw sums the recorded loans of all 12 months instead; the report counts the rows that differ between the two.
#   (2) h_lt1 and h_lyago use the recorded loans of month t-1 and t-11 even when that month is excluded (as Test A, whose
#       exclusion mask is applied to the M6 and 12-month windows only); a month before the first loan counts as 0 there.
#   (3) D and Sg are computed in float32 like Test A, so exact doublings (L_next = 2 M6 + 1) follow Test A's rounding.
#   (4) a_* depends on creator_key only, for Test A works too; where one creator_key has several author articles among the Test A
#       works, the article used by most of them is taken (ties: alphabetical).  Flags follow the link, not the weekly data.
#   (5) extra column loans12 = the 12-month loan sum used for the eligibility rule (for checks and stricter cut-offs).
# Output: data/db/wiki_led/test_d_rows_c.parquet, data/reports/wiki_led_test_d_data_c.md
#   python main_study/wiki_led/60c_test_d_rows.py [--test] [--elig masked|raw]      (from code/, with ../.venv/bin/python)
#   --test: 1% sample (first two hex digits 00 to 02, a subset of the 25% sample) plus the Test A works, written to
#           data/interim/wiki_led_test_d_1pct_c/ so the real outputs are untouched.
import sys, os, time, json, math, pathlib, hashlib, argparse, resource, warnings, datetime, gc, ctypes, struct
import numpy as np, pandas as pd
import pyarrow as pa, pyarrow.parquet as pq
import psutil

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D as DATA_DIR

ap = argparse.ArgumentParser()
ap.add_argument('--test', action='store_true')
ap.add_argument('--elig', choices=['masked', 'raw'], default='masked')
ARGS = ap.parse_args()
TEST, ELIG = ARGS.test, ARGS.elig

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
TAXO = DATA / 'db' / 'taxonomy_v3'
WIKI = DATA / 'db' / 'wiki_led'
OUT = WIKI
REP = DATA / 'reports'
if TEST:
    OUT = DATA / 'interim' / 'wiki_led_test_d_1pct_c'
    REP = OUT
OUT.mkdir(parents=True, exist_ok=True)
ROWS_PATH = OUT / 'test_d_rows_c.parquet'
REPORT_PATH = REP / 'wiki_led_test_d_data_c.md'
ADD_D = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_d_v2_all_books_platforms.json'
ADD_D_SHA = '5f7f4ef33070f466951c7e37491c17fc3f746d2cf0abad7c90be58a832ad4585'
assert hashlib.sha256(ADD_D.read_bytes()).hexdigest() == ADD_D_SHA, 'addendum d changed'
ADD_E = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_e_corrections_robustness.json'
assert hashlib.sha256(ADD_E.read_bytes()).hexdigest() == '36f3605286b51b8123d791c1d59a7dc89356ec3bb66bfba6b9667327d31b3e52', 'addendum e changed'

os.nice(5)                       # machine rule: nice, one heavy job at a time
T0 = time.time()
PROC = psutil.Process()
PEAK = [0.0]
PEAK_FP = [0.0]
PHASE = {}


try:
    _LIBPROC = ctypes.CDLL('/usr/lib/libproc.dylib')
except OSError:
    _LIBPROC = None


def footprint_mb():
    """macOS physical footprint now and its lifetime maximum in MB (what `/usr/bin/time -l` calls peak memory footprint)."""
    if _LIBPROC is None:
        return float('nan'), float('nan')
    buf = ctypes.create_string_buffer(512)
    if _LIBPROC.proc_pid_rusage(os.getpid(), 4, buf) != 0:       # RUSAGE_INFO_V4
        return float('nan'), float('nan')
    return struct.unpack_from('<Q', buf, 72)[0] / 2 ** 20, struct.unpack_from('<Q', buf, 240)[0] / 2 ** 20


def log(*a):
    rss = PROC.memory_info().rss / 2 ** 20
    fp_now, fp_max = footprint_mb()
    PEAK[0] = max(PEAK[0], rss)
    PEAK_FP[0] = max(PEAK_FP[0], fp_max if fp_max == fp_max else 0.0)
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s rss {rss:5.0f} fp {fp_now:5.0f}/{fp_max:5.0f} MB', *a, flush=True)


def mi_of(ym):  # 'YYYY-MM' -> month index year*12 + month-1
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def ym_of(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


ORIG0, ORIG1 = mi_of('2016-03'), mi_of('2026-07')
MI0, MI1 = mi_of('2005-04'), mi_of('2026-08')          # month grid of the loan files
NM, NORIG = MI1 - MI0 + 1, ORIG1 - ORIG0 + 1
MIN_LOANS = 24
LN2, LN15 = np.log(2), np.log(1.5)
FORMATS = [('print', 'book'), ('ebook', 'ebook'), ('audiobook', 'audiobook')]   # (label in the output, row-file name)
LABELS = [f for f, _ in FORMATS]
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
EXPECTED_EXCL = {mi_of(x) for x in ['2020-04', '2020-05', '2020-06', '2020-07', '2020-08', '2020-09', '2024-05', '2024-06',
                                   '2024-07', '2025-08']}
log('start', 'TEST (1% sample)' if TEST else 'full build', '| eligibility rule:', ELIG)

# ---------------------------------------------------------------- excluded months (benchmark rule, panel's month_ok)
P = pd.read_parquet(DATA / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok'])
P = P.drop_duplicates(['format', 'mi'])
grid15 = set(range(mi_of('2015-01'), MI1 + 1))
for f in LABELS:       # a month missing from the panel would count as ok without being checked
    assert grid15 <= set(P.loc[P.format == f, 'mi']), f'panel has no total for some month of {f}'
EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= mi_of('2015-01')}
assert EXCL == EXPECTED_EXCL, f'excluded months differ from the request: {sorted(map(ym_of, EXCL))}'
EXMASK = np.isin(np.arange(MI0, MI1 + 1), sorted(EXCL))
ORIGINS = [m for m in range(ORIG0, ORIG1 + 1) if m not in EXCL and (m + 1) not in EXCL]
log('excluded months:', [ym_of(m) for m in sorted(EXCL)], '| origins:', len(ORIGINS))

# ---------------------------------------------------------------- works, sample, Test A links
W = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'creator_key'])
TA = pd.read_parquet(DATA / 'db' / 'study2r' / 'works.parquet', columns=['work_id', 'article', 'author_article'])
assert TA.work_id.is_unique and TA.work_id.isin(W.work_id).all() and TA.article.notna().all()
ids = W.work_id.to_numpy(np.int64)
first2 = np.fromiter((int(hashlib.md5(str(int(w)).encode()).hexdigest()[:2], 16) for w in ids), np.int64, len(ids))   # first two hex digits as a number
if TEST:
    in_sample = first2 < 3                                          # 00, 01, 02: 1% of the works, a subset of the 25% sample
else:
    in_sample = first2 < 64                                         # first hex digit 0, 1, 2 or 3
    assert in_sample.sum() == sum(hashlib.md5(str(int(w)).encode()).hexdigest()[0] in '0123' for w in ids)
S_ids = np.sort(np.union1d(ids[in_sample], TA.work_id.to_numpy(np.int64)))
NS = len(S_ids)
IN_TA = np.isin(S_ids, TA.work_id.to_numpy(np.int64)).astype(np.int8)
n_extra_ta = int((~np.isin(TA.work_id.to_numpy(np.int64), ids[in_sample])).sum())
log(f'works in spl_works {len(W):,}; sample {int(in_sample.sum()):,}; Test A works {len(TA):,} ({n_extra_ta:,} outside the sample); '
    f'sampled works in total {NS:,}')

CK = W.set_index('work_id').creator_key.reindex(S_ids)                   # creator_key of every sampled work
N_WORKS = len(W)
TAk = TA.merge(W, on='work_id', how='left')
taa = TAk[TAk.author_article.notna() & TAk.creator_key.notna() & (TAk.creator_key != '')]
cnt = (taa.groupby(['creator_key', 'author_article']).size().rename('n').reset_index()
       .sort_values(['creator_key', 'n', 'author_article'], ascending=[True, False, True], kind='stable'))
top = cnt.drop_duplicates('creator_key', keep='first')
KEYMAP = dict(zip(top.creator_key, top.author_article))                  # creator_key -> author article used for a_*
nart = cnt.groupby('creator_key').size()
n_conflict_keys = int((nart > 1).sum())
tie_keys = [k for k in nart[nart > 1].index
            if cnt.loc[cnt.creator_key == k, 'n'].iloc[0] == cnt.loc[cnt.creator_key == k, 'n'].iloc[1]]
del W, TAk, taa
gc.collect()
AUTH_NAME = CK.map(KEYMAP)                                               # NaN: no author article (empty or unknown creator_key)
BOOK_NAME = TA.set_index('work_id').article.reindex(S_ids)
HAS_BOOK = BOOK_NAME.notna().to_numpy().astype(np.int8)
HAS_AUTH = AUTH_NAME.notna().to_numpy().astype(np.int8)
own = TA.set_index('work_id').author_article.reindex(S_ids)
link_info = dict(
    keys_with_article=len(KEYMAP), conflict_keys=n_conflict_keys, tie_keys=tie_keys,
    ta_own_differs=int((IN_TA.astype(bool) & own.notna().to_numpy() & (own.to_numpy() != AUTH_NAME.to_numpy())).sum()),
    ta_gain=int((IN_TA.astype(bool) & own.isna().to_numpy() & AUTH_NAME.notna().to_numpy()).sum()),
    sampled_with_author=int(HAS_AUTH.sum()), ta_with_author=int((HAS_AUTH.astype(bool) & IN_TA.astype(bool)).sum()),
    ta_without_author=int((~HAS_AUTH.astype(bool) & IN_TA.astype(bool)).sum()),
    empty_creator_key=int((CK == '').sum()))
log('author links:', link_info)

# ---------------------------------------------------------------- Wikipedia features as dense arrays [article, origin month, feature]
bnames = sorted(TA.article.unique())
anames = sorted(set(KEYMAP.values()))
bpos, apos = {n: i for i, n in enumerate(bnames)}, {n: i for i, n in enumerate(anames)}
FB = np.full((len(bnames) + 1, NORIG, len(FEATS)), np.nan, np.float32)   # last row: no article (all missing)
FA = np.full((len(anames) + 1, NORIG, len(FEATS)), np.nan, np.float32)
have_data = {}
for kind, arr, pos in (('book', FB, bpos), ('author', FA, apos)):    # one kind at a time keeps the table small
    g = pd.read_parquet(WIKI / 'test_a_wiki_features_c.parquet', filters=[('kind', '==', kind)], read_dictionary=['article'])
    have_data[kind] = set(g.article.astype(str).unique())
    g = g[g.article.isin(list(pos))]
    ai = g.article.astype(str).map(pos).to_numpy()
    assert ((g.mi.to_numpy() - ORIG0) >= 0).all() and ((g.mi.to_numpy() - ORIG0) < NORIG).all()
    arr[ai, g.mi.to_numpy() - ORIG0, :] = g[FEATS].to_numpy(np.float32)
    del g, ai
nb_missing = len(set(bnames) - have_data['book'])
author_no_data = sorted(set(anames) - have_data['author'])
BOOK_IDX = np.where(HAS_BOOK == 1, BOOK_NAME.map(bpos).fillna(len(bnames)).to_numpy(), len(bnames)).astype(np.int64)
AUTH_IDX = np.where(HAS_AUTH == 1, AUTH_NAME.map(apos).fillna(len(anames)).to_numpy(), len(anames)).astype(np.int64)
log(f'wiki features: {len(bnames):,} book articles ({nb_missing} without data), {len(anames):,} author articles used '
    f'({len(author_no_data)} without weekly data)')
gc.collect()

# ---------------------------------------------------------------- record -> position in S_ids
rw = pd.read_parquet(TAXO / 'spl_record_work.parquet')
rid_all, wid_all = rw.record_id.to_numpy(np.int64), rw.work_id.to_numpy(np.int64)
p = np.searchsorted(S_ids, wid_all)
p[p >= NS] = 0
inS = S_ids[p] == wid_all
LUT = np.full(int(rid_all.max()) + 1, -1, np.int32)
LUT[rid_all[inS]] = p[inS]
log(f'records {len(rw):,}, of them in sampled works {int(inS.sum()):,}')
del rw, rid_all, wid_all, p, inS

# ---------------------------------------------------------------- output writer
f32 = pa.float32()
SCHEMA = pa.schema(
    [('work_id', pa.int64()), ('format', pa.dictionary(pa.int8(), pa.string())), ('mi', pa.int32()), ('year', pa.int16()),
     ('in_test_a', pa.int8()), ('has_book_page', pa.int8()), ('has_author_page', pa.int8())]
    + [(c, f32) for c in ['L_t', 'L_next', 'M6', 'h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'D']]
    + [('Sg', pa.int8()), ('Y', f32), ('loans12', f32)]
    + [('b_' + c, f32) for c in FEATS] + [('a_' + c, f32) for c in FEATS])
COLNAMES = SCHEMA.names
PART_PATH = ROWS_PATH.parent / (ROWS_PATH.name + '.part')      # written aside and renamed when complete, so readers never see half a file
writer = pq.ParquetWriter(PART_PATH, SCHEMA, compression='zstd')


def flush(buf, fi):
    if not buf:
        return 0
    cols = {k: np.concatenate([b[k] for b in buf]) for k in buf[0]}
    n = len(cols['work_id'])
    fmt = pa.DictionaryArray.from_arrays(pa.array(np.full(n, fi, np.int8)), pa.array(LABELS))
    arrays = [fmt if name == 'format' else pa.array(cols[name], type=SCHEMA.field(name).type) for name in COLNAMES]
    writer.write_table(pa.Table.from_arrays(arrays, schema=SCHEMA), row_group_size=500_000)
    buf.clear()
    return n


def median_skipna(x):
    """Median of the non-NaN values of each row (float32 in, float32 out; NaN if a row has none). Exact for half-integers."""
    s = np.sort(x, axis=1)                                  # NaN sorts last
    n = (~np.isnan(x)).sum(axis=1)
    r = np.arange(len(x))
    lo, hi = s[r, np.maximum(n - 1, 0) // 2], s[r, n // 2]
    med = (lo + hi) / np.float32(2)
    med[n == 0] = np.nan
    return med.astype(np.float32)


# ---------------------------------------------------------------- one format at a time
STAT = {}
TA_LOANS = {}                  # per format: (Test A work ids with loans, their monthly loans) for the check against counts_work
TA_FMT_WORKS = {}
for fi, (label, fname) in enumerate(FORMATS):
    t_fmt = time.time()
    pf = pq.ParquetFile(TAXO / f'spl_rows_{fname}.parquet')
    A = np.zeros((NS, NM), np.float32)                                # sampled works x months: loans of this format (whole numbers, exact in float32)
    n_read = n_keep = checkouts_kept = 0
    first_data_col = NM
    for g in range(pf.num_row_groups):
        t = pf.read_row_group(g, columns=['record_id', 'year', 'month', 'checkouts'])
        w = LUT[t.column('record_id').to_numpy()]
        mc_all = t.column('year').to_numpy().astype(np.int32) * 12 + t.column('month').to_numpy().astype(np.int32) - 1 - MI0
        first_data_col = min(first_data_col, int(mc_all.min()))        # first month of the whole row file
        k = w >= 0
        n_read += len(w)
        n_keep += int(k.sum())
        if k.any():
            c = t.column('checkouts').to_numpy()[k]
            assert mc_all[k].min() >= 0 and mc_all[k].max() < NM
            np.add.at(A, (w[k], mc_all[k]), c)                        # records of one work add up inside a (work, month) cell
            checkouts_kept += int(c.sum())
        del t, mc_all, w, k
    pos = A > 0
    has = pos.any(axis=1)                                             # sampled works with at least one loan in this format
    first = pos.argmax(axis=1)                                        # first month with a loan (0 for works without loans)
    n_dup = n_keep - int(pos.sum())                                   # record-month rows merged into an earlier (work, month) cell
    del pos
    A[np.arange(NM)[None, :] < first[:, None]] = np.nan               # months before the first loan are not in the collection
    first_mi = (first + MI0).astype(np.int64)
    pa.default_memory_pool().release_unused()
    n_ser = int(has.sum())
    wid_f, inta_f, hb_f, ha_f, bidx_f, aidx_f = S_ids, IN_TA, HAS_BOOK, HAS_AUTH, BOOK_IDX, AUTH_IDX   # rows of A follow S_ids
    sel = np.flatnonzero(IN_TA)                                       # Test A works (S_ids is sorted, so their ids ascend)
    TA_LOANS[label] = (S_ids[sel], np.nan_to_num(A[sel]))
    TA_FMT_WORKS[label] = set(S_ids[sel][has[sel]].tolist())
    log(f'{label}: {n_read:,} record-month rows read, {n_keep:,} in sampled works ({n_dup:,} merged into earlier (work, month) cells); '
        f'{n_ser:,} series with loans; matrix {A.nbytes / 2 ** 20:.0f} MB')

    st = dict(rows_read=n_read, rows_sampled=n_keep, checkouts_sampled=checkouts_kept, merged_cells=n_dup, series_with_loans=n_ser,
              first_data_month=ym_of(first_data_col + MI0), series_first_at_start=int(((first == first_data_col) & has).sum()),
              elig_masked=0, elig_raw=0, elig_raw_only=0, dropped_no_m6=0, rows=0)
    buf, buf_n = [], 0
    for m in ORIGINS:
        j = m - MI0
        win = A[:, j - 11:j + 1]
        raw12 = np.nansum(win, axis=1, dtype=np.float64)
        ex12 = EXMASK[j - 11:j + 1]
        masked12 = np.nansum(win[:, ~ex12], axis=1, dtype=np.float64) if ex12.any() else raw12
        ok_m, ok_r = masked12 >= MIN_LOANS, raw12 >= MIN_LOANS
        st['elig_masked'] += int(ok_m.sum())
        st['elig_raw'] += int(ok_r.sum())
        st['elig_raw_only'] += int((ok_r & ~ok_m).sum())
        idx = np.flatnonzero(ok_m if ELIG == 'masked' else ok_r)
        if len(idx) == 0:
            continue
        loans12 = (masked12 if ELIG == 'masked' else raw12)[idx].astype(np.float32)
        S12 = A[idx, j - 11:j + 1]                                    # raw loans t-11..t (float32), NaN before the first loan
        w12 = S12.copy()
        w12[:, ex12] = np.nan                                         # excluded months are missing inside the windows
        M6 = median_skipna(w12[:, 6:])
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            m12 = np.nanmean(w12, axis=1)
        Lt, Ln = S12[:, 11].copy(), A[idx, j + 1].copy()
        Lt1, Lya = np.nan_to_num(S12[:, 10]), np.nan_to_num(S12[:, 0])
        good = ~np.isnan(M6) & ~np.isnan(Ln) & ~np.isnan(Lt)
        if not good.all():
            st['dropped_no_m6'] += int((~good).sum())
            idx, loans12, Lt, Ln, Lt1, Lya, M6, m12 = idx[good], loans12[good], Lt[good], Ln[good], Lt1[good], Lya[good], M6[good], m12[good]
        n = len(idx)
        if n == 0:
            continue
        Dv = np.log1p(Ln) - np.log1p(M6)                              # float32, as Test A
        row = {
            'work_id': wid_f[idx], 'mi': np.full(n, m, np.int32), 'year': np.full(n, (m + 1) // 12, np.int16),
            'in_test_a': inta_f[idx], 'has_book_page': hb_f[idx], 'has_author_page': ha_f[idx],
            'L_t': Lt, 'L_next': Ln, 'M6': M6, 'h_lt': np.log1p(Lt), 'h_lt1': np.log1p(Lt1), 'h_m6': np.log1p(M6),
            'h_m12': np.log1p(m12), 'h_lyago': np.log1p(Lya), 'h_age': (m - first_mi[idx]).astype(np.float32),
            'D': Dv, 'Sg': ((Dv >= LN2) & ((Ln - M6) >= 5)).astype(np.int8), 'Y': np.log1p(Ln), 'loans12': loans12}
        fbv, fav = FB[bidx_f[idx], m - ORIG0], FA[aidx_f[idx], m - ORIG0]
        for k, c in enumerate(FEATS):
            row['b_' + c] = fbv[:, k]
            row['a_' + c] = fav[:, k]
        buf.append(row)
        buf_n += n
        st['rows'] += n
        if buf_n >= 400_000:
            flush(buf, fi)
            buf_n = 0
    flush(buf, fi)
    st['seconds'] = round(time.time() - t_fmt)
    STAT[label] = st
    log(f'{label}: {st["rows"]:,} rows; eligible series-origin pairs under the masked sum {st["elig_masked"]:,}, raw sum {st["elig_raw"]:,}; '
        f'dropped for no M6: {st["dropped_no_m6"]}; {st["seconds"]}s')
    del A, win, first, first_mi, has
    gc.collect()
    pa.default_memory_pool().release_unused()
writer.close()
os.replace(PART_PATH, ROWS_PATH)
PHASE['build'] = round(time.time() - T0)
meta = pq.ParquetFile(ROWS_PATH).metadata
log(f'wrote {ROWS_PATH} ({meta.num_rows:,} rows, {meta.num_columns} columns, {ROWS_PATH.stat().st_size / 2 ** 20:.0f} MB)')
assert meta.num_rows == sum(s['rows'] for s in STAT.values())

# ---------------------------------------------------------------- checks against Test A's own tables
CHK = {}
C = pd.read_parquet(DATA / 'db' / 'study2r' / 'counts_work.parquet')
ta_sorted = np.sort(TA.work_id.to_numpy(np.int64))
for label in LABELS:               # (1) the monthly loans of the Test A works, per format, equal counts_work cell by cell
    mine = np.zeros((len(ta_sorted), NM))
    wids, mat = TA_LOANS[label]
    mine[np.searchsorted(ta_sorted, wids)] = mat
    theirs = np.zeros((len(ta_sorted), NM))
    c = C[C.format == label]
    theirs[np.searchsorted(ta_sorted, c.work_id.to_numpy(np.int64)), c.mi.to_numpy() - MI0] = c.y.to_numpy()
    CHK[f'loans_{label}'] = dict(cells_different=int((mine != theirs).sum()), total_mine=int(mine.sum()), total_counts_work=int(theirs.sum()))
del C, mine, theirs, TA_LOANS
log('loans vs counts_work:', {k: v['cells_different'] for k, v in CHK.items()})

BC, AC = ['b_' + c for c in FEATS], ['a_' + c for c in FEATS]
NUMC = ['L_t', 'L_next', 'M6', 'h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'D', 'Sg', 'Y']
n_fmt_of = pd.Series({w: sum(w in TA_FMT_WORKS[f] for f in LABELS) for w in set().union(*TA_FMT_WORKS.values())})
single_all = sorted(int(w) for w in n_fmt_of.index[n_fmt_of == 1])
TAr = pd.read_parquet(WIKI / 'test_a_rows_c.parquet', columns=['work_id', 'mi'] + NUMC + BC + AC, filters=[('work_id', 'in', single_all)])
TD = pd.read_parquet(ROWS_PATH, filters=[('work_id', 'in', single_all)])
for label in LABELS:               # (2) for Test A works with loans in one format only, Test D rows equal Test A rows where both exist
    single = set(n_fmt_of.index[(n_fmt_of == 1)].intersection(TA_FMT_WORKS[label]))
    td = TD[(TD.format == label) & TD.work_id.isin(single)]
    ta = TAr[TAr.work_id.isin(single)]
    mg = td.merge(ta, on=['work_id', 'mi'], how='outer', suffixes=('', '_a'), indicator=True)
    both = mg[mg['_merge'] == 'both']
    res = dict(works=len(single), rows_test_d=len(td), rows_test_a=len(ta), both=len(both),
               only_test_d=int((mg['_merge'] == 'left_only').sum()), only_test_a=int((mg['_merge'] == 'right_only').sum()))
    for c in NUMC:
        x, y = both[c].to_numpy(np.float64), both[c + '_a'].to_numpy(np.float64)
        res[c] = int((~((x == y) | (np.isnan(x) & np.isnan(y)))).sum())
    for cols in (BC, AC):
        x = both[cols].to_numpy(np.float32)
        y = both[[c + '_a' for c in cols]].to_numpy(np.float64).astype(np.float32)
        res['b_features' if cols is BC else 'a_features'] = int((~((x == y) | (np.isnan(x) & np.isnan(y)))).any(axis=1).sum())
    CHK[f'rows_{label}'] = res
    log('rows vs Test A', label, res)
del TAr, TD
gc.collect()

# ---------------------------------------------------------------- rules inside the written file (all rows, batch by batch)
FMTC = {f: i for i, f in enumerate(LABELS)}
FAILS = {}


def add(name, ok):
    FAILS[name] = FAILS.get(name, 0) + int((~np.asarray(ok)).sum())


n_checked, prev = 0, None
for b in pq.ParquetFile(ROWS_PATH).iter_batches(batch_size=500_000):
    x = b.to_pandas()
    n_checked += len(x)
    Lt_, Ln_, M6_ = x.L_t.to_numpy(), x.L_next.to_numpy(), x.M6.to_numpy()
    Dv_ = np.log1p(Ln_) - np.log1p(M6_)
    bn, an = x[BC].isna().sum(axis=1), x[AC].isna().sum(axis=1)
    fc = x['format'].astype(str).map(FMTC).to_numpy()
    key = x.mi.to_numpy(np.int64) * (1 << 32) + x.work_id.to_numpy(np.int64)
    if prev is not None:                                              # join the batches: put the last row of the previous one in front
        fc, key = np.concatenate([[prev[0]], fc]), np.concatenate([[prev[1]], key])
    prev = (fc[-1], key[-1])
    add('rows ordered by format, then origin month, then work_id', (fc[1:] > fc[:-1]) | ((fc[1:] == fc[:-1]) & (key[1:] > key[:-1])))
    add('eligible: loans12 is at least 24', x.loans12 >= MIN_LOANS)
    add('origin month is one of the allowed origins', x.mi.isin(ORIGINS))
    add('year is the year of the target month', x.year == (x.mi + 1) // 12)
    add('h_lt, h_m6, Y and D equal their formulas', (x.h_lt.to_numpy() == np.log1p(Lt_)) & (x.h_m6.to_numpy() == np.log1p(M6_))
        & (x.Y.to_numpy() == np.log1p(Ln_)) & (x.D.to_numpy() == Dv_))
    add('Sg equals its rule', x.Sg.to_numpy() == ((Dv_ >= LN2) & ((Ln_ - M6_) >= 5)).astype(np.int8))
    add('no missing value in the measures', x[['L_t', 'L_next', 'M6', 'h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'D', 'Y', 'loans12']].notna().all(axis=1))
    add('loans are whole numbers, M6 is a multiple of 0.5', (Lt_ >= 0) & (Ln_ >= 0) & (Lt_ == np.floor(Lt_)) & (Ln_ == np.floor(Ln_)) & ((M6_ * 2) == np.floor(M6_ * 2)))
    add('h_age is a whole number from 0 to the length of the month grid', (x.h_age >= 0) & (x.h_age < NM) & (x.h_age == np.floor(x.h_age)))
    add('flags are 0 or 1 and the book page flag equals in_test_a', x[['in_test_a', 'has_book_page', 'has_author_page', 'Sg']].isin([0, 1]).all(axis=1) & (x.has_book_page == x.in_test_a))
    # corrected features (A1): an article's first months have some features missing (r4, r1, rmax need 13 weeks, chg 5 weeks) and the months before
    # its first view have none, so "all present or all missing" no longer holds; the rules are: features exist only for works with the page,
    # and lvl4 is missing exactly when the whole set is missing
    add('b_ features are all missing for works without a book page', (x.has_book_page == 1) | (bn == len(FEATS)))
    add('a_ features are all missing for works without an author page', (x.has_author_page == 1) | (an == len(FEATS)))
    add('b_lvl4 is missing exactly when all b_ features are missing', x.b_lvl4.isna().to_numpy() == (bn == len(FEATS)).to_numpy())
    add('a_lvl4 is missing exactly when all a_ features are missing', x.a_lvl4.isna().to_numpy() == (an == len(FEATS)).to_numpy())
log('rules inside the file:', {k: v for k, v in FAILS.items() if v})
del x, b
gc.collect()


# ---------------------------------------------------------------- plain-Python recomputation of random series from the raw row files
def plain_series_rows(d):
    """Eligible rows of one series by plain loops over the request text. d: {month index: loans} for the months with a loan."""
    first = min(d)
    raw = lambda m: d.get(m, 0)                                       # only used for months from the first loan on
    avail = lambda m: m >= first and m not in EXCL
    out = []
    for t in ORIGINS:
        win = [m for m in range(t - 11, t + 1) if avail(m)]
        tot = sum(raw(m) for m in win) if ELIG == 'masked' else sum(raw(m) for m in range(max(t - 11, first), t + 1))
        if tot < MIN_LOANS:
            continue
        w6 = sorted(raw(m) for m in range(t - 5, t + 1) if avail(m))
        if not w6:
            continue
        k = len(w6)
        m6 = w6[k // 2] if k % 2 else (w6[k // 2 - 1] + w6[k // 2]) / 2
        lt, ln = raw(t), raw(t + 1)
        out.append(dict(mi=t, L_t=lt, L_next=ln, M6=m6, h_lt=math.log1p(lt), h_lt1=math.log1p(raw(t - 1) if t - 1 >= first else 0),
                        h_m6=math.log1p(m6), h_m12=math.log1p(sum(raw(m) for m in win) / len(win)),
                        h_lyago=math.log1p(raw(t - 11) if t - 11 >= first else 0), h_age=t - first,
                        D=math.log1p(ln) - math.log1p(m6), Y=math.log1p(ln), loans12=tot))
    return out


rng = np.random.default_rng(7)
ser = pd.read_parquet(ROWS_PATH, columns=['work_id', 'format', 'in_test_a']).drop_duplicates(['work_id', 'format'])
ser['format'] = ser['format'].astype(str)
pick = []
for f in LABELS:                   # 150 series of works outside Test A and 40 of Test A works per format
    for flag, n in ((0, 150), (1, 40)):
        pool = ser[(ser['format'] == f) & (ser.in_test_a == flag)].work_id.to_numpy()
        pick += [(int(w), f, flag) for w in rng.choice(pool, min(n, len(pool)), replace=False)]
del ser
works_pick = sorted({w for w, _, _ in pick})
rwp = pd.read_parquet(TAXO / 'spl_record_work.parquet')
rwp = rwp[rwp.work_id.isin(works_pick)]
rec2work = dict(zip(rwp.record_id.astype(int), rwp.work_id.astype(int)))
loans_by = {}
for label, fname in FORMATS:
    t = pq.read_table(TAXO / f'spl_rows_{fname}.parquet', columns=['record_id', 'year', 'month', 'checkouts'],
                      filters=[('record_id', 'in', list(rec2work))]).to_pandas()
    t['work'] = t.record_id.map(rec2work)
    t['m'] = t.year.astype(int) * 12 + t.month.astype(int) - 1
    for (w, m), v in t.groupby(['work', 'm']).checkouts.sum().items():
        loans_by.setdefault((int(w), label), {})[int(m)] = int(v)
CMP = ['L_t', 'L_next', 'M6', 'h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'D', 'Y', 'loans12']
Rk = pd.read_parquet(ROWS_PATH, filters=[('work_id', 'in', works_pick)], columns=['work_id', 'format', 'mi', 'Sg'] + CMP)
Rk['format'] = Rk['format'].astype(str)
groups = {k: g.sort_values('mi') for k, g in Rk.groupby(['work_id', 'format'])}
IND = dict(series=len(pick), series_outside_test_a=sum(1 for _, _, fl in pick if fl == 0), rows=0, row_set_differs=0, boundary_rows=0,
           sg_differs=0, differing={c: 0 for c in CMP}, other_series=0, other_eligible=0)
for w, f, _ in pick:
    mine, g = plain_series_rows(loans_by[(w, f)]), groups.get((w, f))
    if g is None or [r['mi'] for r in mine] != g.mi.tolist():
        IND['row_set_differs'] += 1
        continue
    for r, (_, row) in zip(mine, g.iterrows()):
        IND['rows'] += 1
        for c in CMP:
            if not math.isclose(r[c], float(row[c]), rel_tol=2e-6, abs_tol=2e-6):
                IND['differing'][c] += 1
        if abs(r['D'] - math.log(2)) < 2e-6:
            IND['boundary_rows'] += 1                                 # exact doubling: the label follows float32 rounding, not compared
        elif (1 if (r['D'] >= math.log(2) and r['L_next'] - r['M6'] >= 5) else 0) != int(row['Sg']):
            IND['sg_differs'] += 1
have = {(int(w), f) for (w, f) in groups}
for (w, f), d in loans_by.items():                                    # series of the same works that are not in the file
    if (w, f) not in have:
        IND['other_series'] += 1
        IND['other_eligible'] += int(len(plain_series_rows(d)) > 0)
log('plain-Python recomputation:', IND)
del Rk, groups, loans_by, rwp, rec2work
gc.collect()

# ---------------------------------------------------------------- report numbers from the written file
cols = ['work_id', 'format', 'mi', 'year', 'in_test_a', 'has_book_page', 'has_author_page', 'Sg', 'D', 'b_lvl4', 'a_lvl4']
R = pd.read_parquet(ROWS_PATH, columns=cols)
R['fmt'] = R['format'].astype('category')
R['bfeat'] = R.b_lvl4.notna()
R['afeat'] = R.a_lvl4.notna()
R['rise15'] = (R.D >= LN15)
R['scored'] = R.mi >= mi_of('2019-01')
R = R.drop(columns=['D', 'b_lvl4', 'a_lvl4', 'format'])
gc.collect()


def pct(x, d=1):
    return f'{100 * x:.{d}f}%'


def n_(x):
    return f'{int(x):,}'


def table(header, rows, left=1):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join([' --- '] * left + [' ---: '] * (len(header) - left)) + '|']
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def per_format(g):
    return dict(rows=len(g), series=g.work_id.nunique(), ta_rows=int(g.in_test_a.sum()), ta_series=g.loc[g.in_test_a == 1, 'work_id'].nunique(),
                months=g.mi.nunique(), hb=g.has_book_page.mean(), bf=g.bfeat.mean(), ha=g.has_author_page.mean(), af=g.afeat.mean(),
                sg=g.Sg.mean(), r15=g.rise15.mean())


by_f = {f: per_format(R[R.fmt == f]) for f in LABELS}
by_f['all'] = per_format(R)
by_f['all']['series'] = len(R.drop_duplicates(['work_id', 'fmt']))
n_works_any = R.work_id.nunique()
n_works_ta = R.loc[R.in_test_a == 1, 'work_id'].nunique()
n_flag_nodata = int(((R.has_author_page == 1) & ~R.afeat).sum())
n_flag = int((R.has_author_page == 1).sum())
top_nodata = TA.author_article[TA.author_article.isin(author_no_data)].value_counts().head(3).index.tolist()
by_fy = {}
for (f, y), g in R.groupby(['fmt', 'year'], observed=True):
    by_fy[(f, int(y))] = per_format(g)
months_in_year = R.groupby('year').mi.nunique()
month_tab = R.groupby(['mi', 'fmt'], observed=True).size().unstack('fmt').reindex(columns=LABELS).fillna(0).astype(int)
sc = {f: per_format(R[(R.fmt == f) & R.scored]) for f in LABELS}
sc['all'] = per_format(R[R.scored])
n_rows_total = len(R)
del R

Q = [0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
qrows = []
QD = pd.read_parquet(ROWS_PATH, columns=['format', 'L_t', 'L_next', 'M6', 'loans12', 'h_age', 'D', 'Sg'])
_ln, _m6, _sg = QD.L_next.to_numpy(np.float64), QD.M6.to_numpy(np.float64), QD.Sg.to_numpy()
_bnd = (_ln == 2 * _m6 + 1) & ((_ln - _m6) >= 5)                      # exact doubling that also passes the 5-loan condition
BND = dict(n=int(_bnd.sum()), share=float(_bnd.mean()), sg_share=float(_sg[_bnd].mean()), sg_all=float(_sg.mean()),
           sg_if_all=float(((_sg == 1) | _bnd).mean()))
del _ln, _m6, _sg, _bnd
for label in LABELS:
    g = QD[QD['format'] == label]
    for c in ['L_t', 'L_next', 'M6', 'loans12', 'h_age', 'D']:
        qs = g[c].quantile(Q).to_numpy()
        qrows.append([label, c] + [f'{v:.2f}' if c == 'D' else f'{v:.1f}' for v in qs] + [f'{g[c].mean():.2f}'])
del QD, g
test_a_json = json.loads((DATA / 'reports' / 'wiki_led_test_a_c.json').read_text())
PHASE['report_numbers'] = round(time.time() - T0)

# ---------------------------------------------------------------- report
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
size_mb = ROWS_PATH.stat().st_size / 2 ** 20
peak_rss = max(PEAK[0], resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20)
peak_fp = max(PEAK_FP[0], footprint_mb()[1] if footprint_mb()[1] == footprint_mb()[1] else 0.0)
L = []
L.append('# Test D rows (all books, by format): data build' + (' (TEST RUN, 1% sample)' if TEST else ''))
L.append('')
L.append(f'Built {now} by `code/main_study/wiki_led/60c_test_d_rows.py` (corrected rerun, addendum e: the Wikipedia features are those of the corrected Test A, '
         'in which the weeks before an article\'s first week with views are missing)' + (' with `--test`, so the file is under `data/interim/wiki_led_test_d_1pct_c/`. ' if TEST else '. ')
         + f'Rows file: `{"data/interim/wiki_led_test_d_1pct_c" if TEST else "data/db/wiki_led"}/test_d_rows_c.parquet` ({n_rows_total:,} rows, '
           f'{len(COLNAMES)} columns, {size_mb:.0f} MB, float32 for all measures and features, rows ordered by format, origin month and work_id). '
           'Data only: no model was fitted and no feature was related to an outcome; every number below is a count or the distribution of one column. '
           f'Settings: addendum d of 20 Oct 2026 (SHA-256 checked in the script), section test_D_all_books. '
         f'Rebuild: `bash jobs/bg.sh wl_test_d_data_c main_study/wiki_led/60c_test_d_rows.py` (add `--elig raw` for the other reading of the 12-month sum, see the choices at the end).')
L.append('')
L.append('## What the rows are')
L.append('')
L.append(f'- **Works.** {int(in_sample.sum()):,} works from the fixed 25% sample of the {N_WORKS:,} works in `spl_works.parquet` '
         '(first hex digit of md5(str(work_id)) is 0, 1, 2 or 3)' + (' (test run: the 1% subset with the first two hex digits 00 to 02)' if TEST else '')
         + f', plus all {len(TA):,} Test A works ({n_extra_ta:,} of them were not in the sample), {NS:,} works in all. {n_works_any:,} of them have at least one row.')
L.append('- **Series.** One per work and format: `print` (the `spl_rows_book` files), `ebook`, `audiobook`. Monthly loans are the checkouts of all records of the work in that format. '
         'Months before the series\' first loan are missing (not in the collection); later months without a loan are 0.')
L.append(f'- **Excluded months** (missing in every window, never an origin or a target; `month_ok` is False for any format in `demand_panel.parquet`, equal to the list in the request): '
         + ', '.join(ym_of(m) for m in sorted(EXCL)) + '.')
L.append(f'- **Origins.** {len(ORIGINS)} months from 2016-03 to 2026-07 (125 months minus the {125 - len(ORIGINS)} whose month t or t+1 is excluded). `mi` = year x 12 + month - 1 of the origin month t; `year` is the year of the target month t+1.')
L.append(f'- **Eligible** at t when the loans over t-11..t sum to at least 24 ({"excluded months and months before the first loan add nothing to the sum" if ELIG == "masked" else "recorded loans of all 12 months, including excluded ones"}).')
L.append('- **Columns** (as Test A): `L_t`, `L_next` (month t+1), `M6` (median of L over t-5..t, missing months skipped), `h_lt` = ln(1+L_t), `h_lt1` = ln(1+L(t-1)), `h_m6` = ln(1+M6), '
         '`h_m12` = ln(1 + mean of L over t-11..t, missing months skipped), `h_lyago` = ln(1+L(t-11)), `h_age` = t minus the month of the first loan, `D` = ln(1+L_next) - ln(1+M6), '
         '`Sg` = 1 when D >= ln 2 and L_next - M6 >= 5, `Y` = ln(1+L_next). Also `work_id`, `format`, `mi`, `year`, `in_test_a`, `has_book_page`, `has_author_page`, '
         'the Wikipedia features `b_*` and `a_*` (lvl4, r4, r1, rmax, nrise8, run, dw, chg, valid4 as in `test_a_wiki_features_c.parquet`), and the extra column `loans12` (the 12-month loan sum used for eligibility).')
L.append(f'- **Wikipedia features.** `b_*` for the {len(TA):,} Test A works (their own article); `a_*` for any sampled work whose `creator_key` equals the `creator_key` of a Test A work that has an author article; missing for all other rows.')
L.append('')
L.append('## Counts by format')
L.append('')
rows = []
for f in LABELS + ['all']:
    b, s = by_f[f], STAT.get(f)
    rows.append([f if f != 'all' else 'all formats', n_(s['series_with_loans']) if s else n_(sum(x['series_with_loans'] for x in STAT.values())),
                 n_(b['series']), n_(b['rows']), n_(b['ta_series']) if f != 'all' else n_(sum(by_f[x]['ta_series'] for x in LABELS)),
                 n_(b['ta_rows']), f'{b["rows"] / b["months"]:,.0f}'])
L.append(table(['format', 'series with any loan in the sample', 'series with at least one row', 'rows', 'of these Test A series', 'Test A rows', 'rows per origin month'], rows))
L.append('')
L.append(f'{n_works_any:,} distinct works have rows in at least one format ({n_works_ta:,} of the {len(TA):,} Test A works and {n_works_any - n_works_ta:,} other sampled works). A series enters the file only if it was eligible at some origin; '
         'the second column counts every series that has any loan in the sample. '
         f'The Test A works are {pct(len(TA) / NS)} of the sampled works but {pct(by_f["all"]["ta_rows"] / by_f["all"]["rows"])} of the rows ({", ".join(f"{f} {pct(by_f[f]["ta_rows"] / by_f[f]["rows"])}" for f in LABELS)}), '
         'because a series needs 24 loans in 12 months and most library books borrow less than that.')
L.append('')
L.append('## Counts by format and year of the target month')
L.append('')
L.append('Rows per month is the rows of that year divided by the number of origin months of that year that are in the file. Shares are shares of rows.')
L.append('')
rows = []
for f in LABELS:
    for y in sorted(y for (ff, y) in by_fy if ff == f):
        b = by_fy[(f, y)]
        rows.append([f, y, n_(b['series']), n_(b['rows']), b['months'], f'{b["rows"] / b["months"]:,.0f}', pct(b['hb']), pct(b['bf']), pct(b['ha']), pct(b['af']), pct(b['sg'], 2), pct(b['r15'], 1)])
    b = by_f[f]
    rows.append([f'**{f}**', '**all**', f'**{n_(b["series"])}**', f'**{n_(b["rows"])}**', f'**{b["months"]}**', f'**{b["rows"] / b["months"]:,.0f}**', f'**{pct(b["hb"])}**',
                 f'**{pct(b["bf"])}**', f'**{pct(b["ha"])}**', f'**{pct(b["af"])}**', f'**{pct(b["sg"], 2)}**', f'**{pct(b["r15"], 1)}**'])
L.append(table(['format', 'year', 'series', 'rows', 'origin months', 'rows per month', 'book page flag', 'b_ features present', 'author page flag', 'a_ features present', 'surge rate (Sg)', 'D >= ln 1.5'], rows))
L.append('')
L.append('## Surge rate and share of rises by format')
L.append('')
L.append('Sg = 1 when D >= ln 2 and L_next - M6 >= 5; the rise share is the share of rows with D >= ln 1.5. "From 2019-01" is the period Test A scored.')
L.append('')
rows = []
for f in LABELS + ['all']:
    a, s = by_f[f], sc[f]
    rows.append([f if f != 'all' else 'all formats', n_(a['rows']), pct(a['sg'], 2), pct(a['r15'], 1), n_(s['rows']), pct(s['sg'], 2), pct(s['r15'], 1)])
L.append(table(['format', 'all rows', 'surge rate', 'D >= ln 1.5', 'rows from 2019-01', 'surge rate from 2019-01', 'D >= ln 1.5 from 2019-01'], rows))
L.append('')
L.append(f'For reference, Test A (all formats added together, {test_a_json["n"]["rows"]:,} scored rows) had a surge rate of {pct(test_a_json["n"]["surge_rate"], 2)}.')
L.append('')
L.append('## Eligible rows per origin month')
L.append('')
rows = []
for mi in month_tab.index:
    r = month_tab.loc[mi]
    rows.append([ym_of(mi)] + [n_(r[f]) for f in LABELS] + [n_(r.sum())])
L.append(table(['origin month', 'print', 'ebook', 'audiobook', 'all'], rows))
L.append('')
L.append('## Wikipedia features')
L.append('')
rows = []
for f in LABELS + ['all']:
    b = by_f[f]
    rows.append([f if f != 'all' else 'all formats', pct(b['hb']), pct(b['bf']), pct(b['ha']), pct(b['af'])])
L.append(table(['format', 'rows with a book page', 'rows with b_ features', 'rows with an author page', 'rows with a_ features'], rows))
L.append('')
L.append(f'- Author links: {link_info["keys_with_article"]:,} `creator_key` values map to an author article ({link_info["sampled_with_author"]:,} of the {NS:,} sampled works have one; '
         f'{link_info["ta_with_author"]:,} Test A works have one and {link_info["ta_without_author"]:,} do not). {link_info["empty_creator_key"]:,} sampled works have an empty `creator_key` and never get author features.')
L.append(f'- {link_info["conflict_keys"]} `creator_key` values have more than one author article among the Test A works; the article used by most of those works is taken '
         f'({len(link_info["tie_keys"])} tie{"" if len(link_info["tie_keys"]) == 1 else "s"} between two articles' + (f', for `{", ".join(link_info["tie_keys"])}`' if link_info["tie_keys"] else '') + '; the alphabetically first article is taken). '
         f'{link_info["ta_own_differs"]} Test A works therefore get a different author article than Test A gave them, and {link_info["ta_gain"]} Test A works that had none now get one.')
L.append(f'- {len(author_no_data)} of the {len(anames):,} author articles in use have no features in the corrected file (no weekly view data, no view at all, or a first view only after the last origin month; the most frequent among the Test A works are {", ".join(top_nodata)}), '
         f'so their works carry the author page flag with `a_*` missing: {n_(n_flag_nodata)} of the {n_(n_flag)} rows with the flag ({pct(n_flag_nodata / max(1, n_flag), 1)}). {nb_missing} of the {len(bnames):,} book articles have no features in the corrected file (no view at all, or a first view only after the last origin month).')
L.append('')
L.append('## Distributions of single columns (all rows)')
L.append('')
L.append(table(['format', 'column', '5%', '25%', '50%', '75%', '95%', '99%', 'mean'], qrows, left=2))
L.append('')
L.append('## Checks (no model involved)')
L.append('')
L.append('1. **Loans.** For the Test A works, the monthly loans per format built here equal `study2r/counts_work.parquet` cell by cell: '
         + '; '.join(f'{f}: {n_(CHK[f"loans_{f}"]["cells_different"])} differing cells (loans {n_(CHK[f"loans_{f}"]["total_mine"])} here, {n_(CHK[f"loans_{f}"]["total_counts_work"])} there)' for f in LABELS) + '.')
L.append('2. **Rows.** For Test A works with loans in one format only, the rows here are compared with `test_a_rows_c.parquet` on (work_id, origin month). '
         'Test D rows are a subset of Test A rows (an eligible row needs 24 loans, Test A needed one); where both exist the values are compared exactly (float32).')
rows = []
for f in LABELS:
    r = CHK[f'rows_{f}']
    rows.append([f, n_(r['works']), n_(r['rows_test_d']), n_(r['rows_test_a']), n_(r['both']), n_(r['only_test_d']),
                 n_(sum(r[c] for c in NUMC)), n_(r['b_features']), n_(r['a_features'])])
L.append('')
L.append(table(['format', 'Test A works in one format', 'Test D rows', 'Test A rows', 'rows in both', 'only in Test D', 'differing values in L, M6, h_*, D, Sg, Y', 'rows with a differing b_ value', 'rows with a differing a_ value'], rows))
L.append('')
L.append(f'3. **Rules inside the file.** Every one of the {n_checked:,} rows was tested against the rules below (rows that fail each rule are counted); '
         f'rows dropped during the build because M6 had no available month: {sum(s["dropped_no_m6"] for s in STAT.values())}.')
L.append('')
L.append(table(['rule', 'rows failing'], [[k, n_(v)] for k, v in FAILS.items()]))
L.append('')
L.append(f'4. **Plain-Python recomputation.** {IND["series"]} random series ({IND["series_outside_test_a"]} of works outside Test A, the rest of Test A works; up to 150 and 40 per format) were rebuilt from the raw row files '
         f'with simple loops written from the request text, and the {n_(IND["rows"])} rows compared with the file. Series whose set of origin months differs: {IND["row_set_differs"]}. '
         f'Rows with a differing value: ' + ', '.join(f'{c} {IND["differing"][c]}' for c in CMP) + f', Sg {IND["sg_differs"]} (the {IND["boundary_rows"]} rows on the D = ln 2 boundary are left out of the Sg comparison, see choice 3). '
         f'{IND["other_series"]} further series of the same works are not in the file; {IND["other_eligible"]} of them have an eligible origin by the recomputation.')
L.append(f'5. **Excluded months** equal the list in the request ({len(EXCL)} months); the panel has a total for every month of every format from 2015-01.')
L.append('')
L.append('## Choices where the request left room')
L.append('')
tot = {k: sum(s[k] for s in STAT.values()) for k in ['elig_masked', 'elig_raw', 'elig_raw_only']}
_pre, _a = month_tab.loc[mi_of('2020-02')], month_tab.loc[mi_of('2020-10')]
_low = month_tab.loc[mi_of('2020-10'):mi_of('2021-08')].min()
L.append(f'1. **Eligibility and excluded months.** The 12-month sum of 24 loans skips excluded months, like M6 and the 12-month mean (the request says excluded months are missing inside windows). '
         f'Summing the recorded loans of all 12 months instead would make {n_(tot["elig_raw_only"])} more series-origin pairs eligible ({pct(tot["elig_raw_only"] / max(1, tot["elig_masked"]), 1)} on top of {n_(tot["elig_masked"])}); '
         'they all sit at origins whose 12-month window contains an excluded month. Run the script with `--elig raw` to build that version. '
         'A consequence of skipping the excluded months: the number of eligible rows dips at origins whose window contains them, also for formats whose loans were not affected '
         f'(rows per origin month in 2020-02, 2020-10 and the lowest month from 2020-10 to 2021-08: ' + '; '.join(f'{f} {n_(_pre[f])}, {n_(_a[f])}, {n_(_low[f])}' for f in LABELS) + '; the monthly table below has all months).' if ELIG == 'masked' else
         f'The 12-month sum of 24 loans uses the recorded loans of all 12 months (`--elig raw`); skipping excluded months would leave {n_(tot["elig_masked"])} instead of {n_(tot["elig_raw"])} eligible series-origin pairs.')
L.append('2. **Test A\'s handling of single months.** `h_lt1` and `h_lyago` use the recorded loans of month t-1 and t-11 even if that month is excluded (Test A applies the exclusion to the M6 and 12-month windows only); a month before the first loan counts as 0 there. `L_t` and `L_next` are never excluded months.')
L.append('3. **Rounding.** D and Sg are computed in float32 as in Test A. Exact doublings (L_next = 2 x M6 + 1, with L_next - M6 >= 5) sit on the boundary D = ln 2: '
         f'{n_(BND["n"])} rows ({pct(BND["share"], 2)} of all rows); float32 rounding labels {pct(BND["sg_share"], 1)} of them as surges and the rest as not, the same rule as in Test A. '
         f'The pooled surge rate is {pct(BND["sg_all"], 2)} and would be {pct(BND["sg_if_all"], 2)} if every one of them counted as a surge.')
L.append('4. **First loan.** The first loan month of a series is its first month with a recorded loan in that format. Series already in the collection when the data begin (2005-04 for print, 2005-09 for ebook and audiobook) have a first loan month equal to the first data month, so `h_age` is cut off at the start of the data (sampled series whose first loan is the first data month: '
         + ', '.join(f'{f} {n_(STAT[f]["series_first_at_start"])}' for f in LABELS) + ').')
L.append('5. **Flags.** `has_book_page` is 1 for the Test A works; `has_author_page` is 1 when the work\'s `creator_key` maps to an author article, whether or not that article has weekly data. The share of rows with the features present is in the Wikipedia table above.')
L.append('6. **Extra column.** `loans12` is not in the request; it holds the loan sum used for the eligibility rule so stricter cut-offs can be applied without a rebuild.')
L.append('7. **Format labels.** `print`, `ebook`, `audiobook` (the labels of `counts_work.parquet` and the demand panel); the print row files are named `spl_rows_book`.')
L.append('8. **Same name, different person.** `creator_key` is a normalised name, so two authors with the same name share author features.')
L.append('')
L.append('## Memory and runtime')
L.append('')
L.append(f'- Peak memory of the build process: {peak_fp:,.0f} MB physical footprint (what `time -l` reports as peak memory footprint) and {peak_rss:,.0f} MB resident (limit set for the job: 3,000 MB). One format at a time; the biggest object is the matrix of sampled works by month with the loans of the format (float32, {NS * NM * 4 / 2 ** 20:,.0f} MB, rebuilt for each format).')
L.append(f'- Runtime {time.time() - T0:,.0f} s in all: ' + ', '.join(f'{f} {STAT[f]["seconds"]} s' for f in LABELS) + f'; the rest is set-up, the checks and this report. The job ran with `nice` 5.')
L.append('')
REPORT_PATH.with_name(REPORT_PATH.name + '.part').write_text('\n'.join(L))
os.replace(REPORT_PATH.with_name(REPORT_PATH.name + '.part'), REPORT_PATH)
log('report written', REPORT_PATH, f'| peak memory: footprint {peak_fp:.0f} MB, resident {peak_rss:.0f} MB | total {time.time() - T0:.0f}s')
