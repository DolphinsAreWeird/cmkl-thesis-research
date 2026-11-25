# n40. Addendum n, part 3c: Chronos-2 (pretrained Transformer, zero-shot, CPU) forecasts of each row's next month.
# Settings: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json, part_3_models.3c (read-only; SHA-256 checked).
# Context at origin t: the work-format's monthly log(1 + loans) over up to 60 months ending at t; excluded months and months before the
#   first loan missing (leading missing months dropped).  C2: no covariates.  C2W: past covariates b and a = the book's and the author's
#   article lvl4 at each context month (log mean share of the 4 weeks ending by that month's end; l_books_in_time/wiki_features.parquet;
#   missing before 2016-03 or without an article; a covariate missing in the whole context is dropped, as the theme benchmark).
# Predicted change = median forecast of t+1 minus log(1 + M6).  No random part, so no seeds.
# Speed rule (record): the first 10,000 rows are timed; if all 1,773,531 rows of one setting would take more than 24 hours, only scored
#   rows (origins from 2019-01) are forecast and the stacking (HMW14Z) is dropped; the script stops after the timing so that the choice can
#   be written in DEVIATIONS first (rerun with --rows scored or --rows all).
# Outputs: data/db/wiki_led/n_more_signals/chronos/<variant>/chunk_*.parquet; feat_Z.parquet (Z_c2, Z_c2w aligned with rows up to 2026-07,
#   when all rows were forecast); preds/C2.npy, preds/C2W.npy (scored rows in keys order).
#   Run from handoff/:  bash jobs/bg.sh n40_chronos main_study/wiki_led/n_more_signals/n40_chronos.py --time      (timing only)
#                       bash jobs/bg.sh n40_chronos main_study/wiki_led/n_more_signals/n40_chronos.py --rows all|scored
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '4')
import sys, json, time, hashlib, pathlib, argparse
import numpy as np, pandas as pd, pyarrow.parquet as pq, torch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
L = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
TAXO = DATA / 'db' / 'taxonomy_v3'
OUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
CH = OUT / 'chronos'
MODEL, REVISION = 'amazon/chronos-2', '29ec3766d36d6f73f0696f85560a422f50e8498c'
CHUNK, BATCH, CTX = 4096, 256, 60
torch.set_num_threads(4)
os.nice(10)
ap = argparse.ArgumentParser()
ap.add_argument('--time', action='store_true')
ap.add_argument('--rows', choices=['all', 'scored'])
a = ap.parse_args()
T0 = time.time()


def log(*x):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *x, flush=True)


def mi_of(y, m):
    return y * 12 + m - 1


R = pd.read_parquet(L / 'rows.parquet', columns=['work_id', 'format', 'mi', 'M6'])
R = R[R.mi <= mi_of(2026, 7)].reset_index(drop=True)
R['format'] = R.format.astype(str)
WA = pd.read_parquet(L / 'work_articles.parquet')
S_ids = np.sort(pd.read_parquet(L / 'matches.parquet', columns=['work_id']).work_id.to_numpy(np.int64))
NS = len(S_ids)
wpos = pd.Series(np.arange(NS), index=S_ids)

# monthly loans per work and format (as l03), log1p, excluded months and months before the first loan missing
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

# covariates: article lvl4 by month
WF = pd.read_parquet(L / 'wiki_features.parquet', columns=['article', 'kind', 'mi', 'lvl4'])
COV = {}
for kind, col in (('book', 'book_canonical'), ('author', 'author_canonical')):
    g = WF[WF.kind == kind]
    arts = sorted(g.article.unique()); apos = {x: i for i, x in enumerate(arts)}
    M = np.full((len(arts) + 1, NM), np.nan, np.float32)
    M[g.article.map(apos).to_numpy(), g.mi.to_numpy() - MI0] = g.lvl4.to_numpy(np.float32)
    idx = WA.set_index('work_id')[col].map(apos).reindex(S_ids).fillna(len(arts)).astype(int).to_numpy()
    COV[kind] = (M, idx)
del WF

rows_sel = np.arange(len(R)) if a.rows != 'scored' else np.flatnonzero((R.mi >= mi_of(2019, 1)).to_numpy())
if a.time:
    rows_sel = rows_sel[:10000]


def inputs_for(ix, with_cov):
    out = []
    wi = wpos.reindex(R.work_id.to_numpy()[ix]).to_numpy()
    for r, w in zip(ix, wi):
        f = R.format.iat[r]; t = int(R.mi.iat[r])
        j1 = t - MI0
        j0 = max(0, j1 - CTX + 1)
        y = LOANS[f][w, j0:j1 + 1]
        ok = np.flatnonzero(~np.isnan(y))
        y = y[ok[0]:] if len(ok) else y
        d = {'target': y.astype(np.float32)}
        if with_cov:
            pc = {}
            for kind, nm in (('book', 'b'), ('author', 'a')):
                M, idx = COV[kind]
                v = M[idx[w], j0:j1 + 1][(ok[0] if len(ok) else 0):]
                if np.isfinite(v).any():
                    pc[nm] = v.astype(np.float32)
            if pc:
                d['past_covariates'] = pc
        out.append(d)
    return out


import chronos.chronos2.pipeline as CP                      # noqa: E402
from torch.utils.data import DataLoader as _DL              # noqa: E402


def _dl(dataset, **kw):                                      # as the theme benchmark: no worker process, same data and order
    kw['num_workers'] = 0; kw['pin_memory'] = False
    return _DL(dataset, **kw)


CP.DataLoader = _dl
from chronos import Chronos2Pipeline                        # noqa: E402
pipe = Chronos2Pipeline.from_pretrained(MODEL, device_map='cpu', dtype=torch.float32, revision=REVISION)
log('rows to forecast', len(rows_sel), '| time only' if a.time else '')
for variant, with_cov in (('C2', False), ('C2W', True)):
    d = CH / variant
    d.mkdir(parents=True, exist_ok=True)
    t1 = time.time()
    for ci in range(0, len(rows_sel), CHUNK):
        fp = d / f'chunk_{ci // CHUNK:05d}.parquet'
        if fp.exists() and not a.time:
            continue
        ix = rows_sel[ci:ci + CHUNK]
        q, _ = pipe.predict_quantiles(inputs_for(ix, with_cov), prediction_length=1, quantile_levels=[0.5], batch_size=BATCH)
        yhat = np.array([x[0, 0, 0].item() for x in q], np.float32)
        o = pd.DataFrame({'row': ix, 'yhat': yhat, 'dhat': yhat - np.log1p(R.M6.to_numpy()[ix]).astype(np.float32)})
        if not a.time:
            o.to_parquet(fp.with_suffix('.tmp'), index=False); os.replace(fp.with_suffix('.tmp'), fp)
        if (ci // CHUNK) % 10 == 0:
            log(variant, min(ci + CHUNK, len(rows_sel)), 'of', len(rows_sel))
    el = time.time() - t1
    if a.time:
        per = el / len(rows_sel)
        est = dict(variant=variant, seconds_10000=round(el, 1), hours_all_rows=round(per * len(R) / 3600, 2),
                   hours_scored_rows=round(per * int((R.mi >= mi_of(2019, 1)).sum()) / 3600, 2))
        log('timing', est)
        (OUT / f'chronos_timing_{variant}.json').write_text(json.dumps(est))
if a.time:
    sys.exit(0)

# assemble
K = pd.read_parquet(OUT / 'preds' / 'keys.parquet', columns=['work_id', 'format', 'mi'])
for variant in ('C2', 'C2W'):
    Z = pd.concat([pd.read_parquet(f) for f in sorted((CH / variant).glob('chunk_*.parquet'))], ignore_index=True).sort_values('row')
    assert Z.row.is_unique and len(Z) == len(rows_sel)
    full = np.full(len(R), np.nan, np.float32); full[Z.row.to_numpy()] = Z.dhat.to_numpy()
    R['Z_' + variant.lower()] = full
    kk = K.merge(R[['work_id', 'format', 'mi', 'Z_' + variant.lower()]], on=['work_id', 'format', 'mi'], how='left', validate='one_to_one')
    assert kk['Z_' + variant.lower()].notna().all()
    np.save(OUT / 'preds' / f'{variant}.npy', kk['Z_' + variant.lower()].to_numpy(np.float64))
if a.rows == 'all':
    R[['work_id', 'format', 'mi', 'Z_c2', 'Z_c2w']].to_parquet(OUT / 'feat_Z.parquet', index=False)
log('done')
