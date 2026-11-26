# o01. Addendum o, step 2: the control inputs C (the same 60 months of loans that Chronos-2 sees, in plain form) and Z_lag (the Chronos-2
# forecasts of the same work and format 12 months earlier).  Settings: prereg/addenda_wiki_led/2026-11-26_o_transformer_inputs_check.json,
# inputs (read-only; SHA-256 checked).
# Series: as n40_chronos.py (copied): per work and format the monthly ln(1 + loans), excluded months and months before the first loan missing.
# Context at origin t: the 60 months t-59..t.  Unspecified details fixed here (logged in DEVIATIONS): c_sd12 is the sample standard deviation
#   (ddof 1); slopes and the 12-month trend use the month number as x.
# Outputs: data/db/wiki_led/o_transformer_check/feat_C.parquet (every row of l_books_in_time/rows.parquet, origins to 2026-08, in its order),
#   feat_Zlag.parquet (rows up to origin 2026-07, in the order of n's feat_Z.parquet).
#   Run from handoff/:  bash jobs/bg.sh o01_controls main_study/wiki_led/o_transformer_check/o01_controls.py
import sys, os, json, time, hashlib, pathlib, warnings
import numpy as np, pandas as pd, pyarrow.parquet as pq

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-26_o_transformer_inputs_check.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'ad6a417b47cc60b21b59742fbf79574a5370150ff78ba617e932c0a8a7fc62d6', 'addendum o changed'
L = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
TAXO = DATA / 'db' / 'taxonomy_v3'
NOUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
OUT = DATA / 'db' / 'wiki_led' / 'o_transformer_check'
OUT.mkdir(parents=True, exist_ok=True)
CTX = 60
ALPHAS = np.array([0.1, 0.2, 0.3, 0.5, 0.7, 0.9])
os.nice(5)
warnings.filterwarnings('ignore', category=RuntimeWarning)
T0 = time.time()


def log(*x):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *x, flush=True)


def mi_of(y, m):
    return y * 12 + m - 1


R = pd.read_parquet(L / 'rows.parquet', columns=['work_id', 'format', 'mi', 'M6', 'h_lt', 'h_lyago'])
R['format'] = R.format.astype(str)
assert R.mi.max() == mi_of(2026, 8)
S_ids = np.sort(pd.read_parquet(L / 'matches.parquet', columns=['work_id']).work_id.to_numpy(np.int64))
NS = len(S_ids)
wpos = pd.Series(np.arange(NS), index=S_ids)

# ---------------------------------------------------------------- monthly loans (copied from n40_chronos.py)
P = pd.read_parquet(DATA / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok']).drop_duplicates(['format', 'mi'])
EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= mi_of(2015, 1)}
MI0, MI1 = mi_of(2005, 4), mi_of(2026, 8)
NM = MI1 - MI0 + 1
rw = pd.read_parquet(TAXO / 'spl_record_work.parquet')
rid, wid = rw.record_id.to_numpy(np.int64), rw.work_id.to_numpy(np.int64)
p = np.searchsorted(S_ids, wid); p[p >= NS] = 0
inS = S_ids[p] == wid
LUT = np.full(int(rid.max()) + 1, -1, np.int32); LUT[rid[inS]] = p[inS]
LOANS = {}
for label, fname in (('print', 'book'), ('ebook', 'ebook'), ('audiobook', 'audiobook')):
    pf = pq.ParquetFile(TAXO / f'spl_rows_{fname}.parquet')
    A = np.zeros((NS, NM), np.float32)
    for g in range(pf.num_row_groups):
        t = pf.read_row_group(g, columns=['record_id', 'year', 'month', 'checkouts'])
        w = LUT[t.column('record_id').to_numpy()]
        mc = t.column('year').to_numpy().astype(np.int32) * 12 + t.column('month').to_numpy().astype(np.int32) - 1 - MI0
        k = w >= 0
        np.add.at(A, (w[k], mc[k]), t.column('checkouts').to_numpy()[k])
    first = (A > 0).argmax(axis=1)
    A = np.log1p(A)
    A[np.arange(NM)[None, :] < first[:, None]] = np.nan
    A[:, [m - MI0 for m in sorted(EXCL) if MI0 <= m <= MI1]] = np.nan
    LOANS[label] = A
    log('loans', label)


# ---------------------------------------------------------------- features of one block of rows
def ols(Y, x):
    """Least-squares slope and intercept per row over the non-missing entries of Y (rows x months), x the month numbers; <3 values -> nan."""
    m = ~np.isnan(Y)
    n = m.sum(1).astype(float)
    xs = np.where(m, x[None, :], 0.0)
    ys = np.where(m, Y, 0.0)
    xb, yb = xs.sum(1) / np.maximum(n, 1), ys.sum(1) / np.maximum(n, 1)
    sxx = (np.where(m, (x[None, :] - xb[:, None]) ** 2, 0.0)).sum(1)
    sxy = (np.where(m, (x[None, :] - xb[:, None]) * (Y - yb[:, None]), 0.0)).sum(1)
    ok = (n >= 3) & (sxx > 0)
    b = np.where(ok, sxy / np.where(sxx > 0, sxx, 1), np.nan)
    return b, yb - b * xb, ok


def ses(Y):
    """Simple exponential smoothing over the non-missing months, alpha by smallest mean squared one-step error; <3 values -> last value."""
    n = Y.shape[0]
    lev = np.full((len(ALPHAS), n), np.nan)
    sse = np.zeros((len(ALPHAS), n)); cnt = np.zeros(n)
    last = np.full(n, np.nan)
    for k in range(Y.shape[1]):
        v = Y[:, k]; ok = ~np.isnan(v)
        started = ~np.isnan(lev[0])
        upd = ok & started
        e = v[None, :] - lev
        sse[:, upd] += e[:, upd] ** 2
        lev[:, upd] += ALPHAS[:, None] * e[:, upd]
        cnt[upd] += 1
        new = ok & ~started
        lev[:, new] = v[new]
        last[ok] = v[ok]
    navail = (~np.isnan(Y)).sum(1)
    best = np.argmin(np.where(cnt[None, :] > 0, sse / np.maximum(cnt, 1)[None, :], np.inf), axis=0)
    fc = lev[best, np.arange(n)]
    return np.where(navail >= 3, fc, last)


def features(Y, m6):
    """Y: rows x 60 months (oldest first, last column = t)."""
    o = {}
    for k in range(24):
        o[f'c_y{k}'] = Y[:, CTX - 1 - k]
    for n in (24, 36, 60):
        o[f'c_mean{n}'] = np.nanmean(Y[:, CTX - n:], axis=1)
    for n in (12, 36):
        o[f'c_slope{n}'] = ols(Y[:, CTX - n:], np.arange(n, dtype=float))[0]
    Y12 = Y[:, CTX - 12:]
    n12 = (~np.isnan(Y12)).sum(1)
    o['c_sd12'] = np.where(n12 >= 3, np.nanstd(Y12, axis=1, ddof=1), np.nan)
    o['c_zero12'] = np.where(n12 > 0, np.nansum(Y12 == 0, axis=1) / np.maximum(n12, 1), np.nan)
    o['c_n60'] = (~np.isnan(Y)).sum(1).astype(float)
    lm6 = np.log1p(m6)
    o['c_ses'] = ses(Y) - lm6
    o['c_snaive'] = Y[:, CTX - 1 - 11] - lm6
    b, a_, ok = ols(Y12, np.arange(12, dtype=float))
    o['c_trend12'] = np.where(ok, a_ + b * 12, np.nan) - lm6
    return o


COLS = None
out = {}
BLK = 100_000
wi_all = wpos.reindex(R.work_id.to_numpy()).to_numpy()
assert not np.isnan(wi_all.astype(float)).any()
for f in ('print', 'ebook', 'audiobook'):
    ixf = np.flatnonzero(R.format.to_numpy() == f)
    A = LOANS[f]
    for b0 in range(0, len(ixf), BLK):
        ix = ixf[b0:b0 + BLK]
        j1 = R.mi.to_numpy()[ix] - MI0
        J = j1[:, None] - np.arange(CTX - 1, -1, -1)[None, :]
        Y = A[wi_all[ix][:, None], np.clip(J, 0, None)].astype(np.float64)
        Y[J < 0] = np.nan
        o = features(Y, R.M6.to_numpy()[ix].astype(np.float64))
        if COLS is None:
            COLS = list(o)
            out = {c: np.full(len(R), np.nan, np.float32) for c in COLS}
        for c in COLS:
            out[c][ix] = o[c]
    log('features', f, len(ixf))

C = pd.DataFrame({'work_id': R.work_id.to_numpy(), 'format': R.format.to_numpy(), 'mi': R.mi.to_numpy(), **out})
# checks: the context's last month is the row's own month, and t-11 is the series' value a year before the target month
d0 = np.abs(C.c_y0.to_numpy() - R.h_lt.to_numpy())
chk = dict(rows=len(C), c_y0_equals_h_lt=float(np.mean(d0[~np.isnan(d0)] < 1e-5)), c_y0_missing=float(np.isnan(C.c_y0).mean()),
           missing_share={c: round(float(np.isnan(C[c]).mean()), 4) for c in COLS})
log('checks', chk)
assert chk['c_y0_equals_h_lt'] > 0.999
C.to_parquet(OUT / 'feat_C.parquet', index=False)

# ---------------------------------------------------------------- Z_lag
Z = pd.read_parquet(NOUT / 'feat_Z.parquet')
Z['format'] = Z.format.astype(str)
lag = Z[['work_id', 'format', 'mi', 'Z_c2', 'Z_c2w']].rename(columns={'Z_c2': 'Zl_c2', 'Z_c2w': 'Zl_c2w'})
lag['mi'] = lag.mi + 12
ZL = Z[['work_id', 'format', 'mi']].merge(lag, on=['work_id', 'format', 'mi'], how='left', validate='one_to_one')
assert len(ZL) == len(Z) and (ZL.work_id.to_numpy() == Z.work_id.to_numpy()).all() and (ZL.mi.to_numpy() == Z.mi.to_numpy()).all()
ZL.to_parquet(OUT / 'feat_Zlag.parquet', index=False)
chk['Zlag_missing_share'] = round(float(ZL.Zl_c2.isna().mean()), 4)
(OUT / 'controls_check.json').write_text(json.dumps(chk, indent=1))
log('done', chk['Zlag_missing_share'])
