# n31. Addendum n, part 3b: HM and HMW14 fitted separately within each group of four families of kinds of book, five seeds.
# Settings: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json, part_3_models.3b (read-only; SHA-256 checked).
# Families and groups as addendum m (m04_score.py): F3 popularity thirds, F4 fiction or nonfiction, F6 format, F9 own Wikipedia article.
#   Training rows take their group the same way at their own origin; popularity thirds per format and target year over the series with a
#   row in that year (all rows up to origin 2026-07, not only scored rows, since training rows need them), by loans in the year before
#   (excluded months skipped), ties by work id.  F9: book article feature at t, else author article only, else neither.
# LightGBM settings and walk-forward of addendum l; within a group, training rows are the group's rows whose target month ended before
#   January of the test year.  A group-year with fewer than 1,000 training rows is fitted on the pooled training rows instead (counted).
# Outputs: data/db/wiki_led/n_more_signals/preds/<seed>/PT_<family>_HM.npy, PT_<family>_HMW14.npy (scored rows in keys order);
#   per_type_groups.parquet (group of every scored row, per family).
#   Run from handoff/:  bash jobs/bg.sh n31_per_type main_study/wiki_led/n_more_signals/n31_per_type.py
import sys, os, json, time, hashlib, pathlib, resource
import numpy as np, pandas as pd, pyarrow.parquet as pq
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
L = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
TAXO = DATA / 'db' / 'taxonomy_v3'
OUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
PRED = OUT / 'preds'
SEEDS = [20261020 + i for i in range(5)]
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB', *a, flush=True)


FMTS = ['print', 'ebook', 'audiobook']
F14 = ['lvl4', 'r4', 'r1', 'run', 'dw', 'chg', 'valid4']
W14C = ['b_' + c for c in F14] + ['a_' + c for c in F14]
HMC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'fmt', 'cal_month', 'cal_days']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEEDS[0], n_jobs=4, verbose=-1)

R = pd.read_parquet(L / 'rows.parquet')
R = R[R.mi <= 2026 * 12 + 6].reset_index(drop=True)
R['format'] = R.format.astype(str)
R['fmt'] = R.format.map({f: i for i, f in enumerate(FMTS)}).astype('int8')

# ---------------------------------------------------------------- groups
SW = pd.read_parquet(OUT.parent / 'm_theme_pages' / 'seg_works.parquet', columns=['work_id', 'form']).set_index('work_id')
G = {}
G['F4_fiction'] = R.work_id.map(SW.form).fillna('other (mixed or unknown)').to_numpy()
G['F6_format'] = R.format.to_numpy()
hb, ha = R.has_book_page.to_numpy() == 1, R.has_author_page.to_numpy() == 1
G['F9_own_article'] = np.where(hb, 'book article', np.where(ha, 'author article only', 'neither'))
# popularity: loans per work, format and calendar year (excluded months skipped)
P = pd.read_parquet(DATA / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok']).drop_duplicates(['format', 'mi'])
EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= 2015 * 12}
S_ids = np.sort(pd.read_parquet(L / 'matches.parquet', columns=['work_id']).work_id.to_numpy(np.int64))
NS = len(S_ids)
rw = pd.read_parquet(TAXO / 'spl_record_work.parquet')
rid, wid = rw.record_id.to_numpy(np.int64), rw.work_id.to_numpy(np.int64)
p = np.searchsorted(S_ids, wid); p[p >= NS] = 0
inS = S_ids[p] == wid
LUT = np.full(int(rid.max()) + 1, -1, np.int32); LUT[rid[inS]] = p[inS]
Y0, Y1 = 2015, 2025
pops = []
for label, fname in (('print', 'book'), ('ebook', 'ebook'), ('audiobook', 'audiobook')):
    pf = pq.ParquetFile(TAXO / f'spl_rows_{fname}.parquet')
    A = np.zeros((NS, Y1 - Y0 + 1), np.float64)
    for g in range(pf.num_row_groups):
        t = pf.read_row_group(g, columns=['record_id', 'year', 'month', 'checkouts'])
        w = LUT[t.column('record_id').to_numpy()]
        yr = t.column('year').to_numpy().astype(np.int32); mo = t.column('month').to_numpy().astype(np.int32)
        k = (w >= 0) & (yr >= Y0) & (yr <= Y1) & ~np.isin(yr * 12 + mo - 1, list(EXCL))
        np.add.at(A, (w[k], yr[k] - Y0), t.column('checkouts').to_numpy()[k])
    for y in range(Y0, Y1 + 1):
        pops.append(pd.DataFrame({'work_id': S_ids, 'format': label, 'year': y + 1, 'loans_prev_year': A[:, y - Y0]}))
POP = pd.concat(pops, ignore_index=True)
ser = R[['work_id', 'format', 'year']].drop_duplicates().merge(POP, on=['work_id', 'format', 'year'], how='left')
assert ser.loans_prev_year.notna().all(), 'popularity missing for some series-years'
ser = ser.sort_values(['format', 'year', 'loans_prev_year', 'work_id'])
ser['r'] = ser.groupby(['format', 'year']).cumcount()
ser['n'] = ser.groupby(['format', 'year']).work_id.transform('size')
ser['tert'] = np.floor(3 * ser.r / ser.n).astype(int).map({0: 'low', 1: 'middle', 2: 'high'})
G['F3_popularity'] = R[['work_id', 'format', 'year']].merge(ser[['work_id', 'format', 'year', 'tert']], on=['work_id', 'format', 'year'], how='left').tert.to_numpy()
log('groups built', {k: pd.Series(v).value_counts().to_dict() for k, v in G.items()})

TEST = [(Y, np.flatnonzero(((R.year == Y) & (R.mi >= 2019 * 12)).to_numpy())) for Y in range(2019, 2027)]
TEST = [(Y, ix) for Y, ix in TEST if len(ix)]
allix = np.concatenate([ix for _, ix in TEST])
keys = pd.read_parquet(PRED / 'keys.parquet', columns=['work_id', 'format', 'mi'])
assert (keys.work_id.to_numpy() == R.work_id.to_numpy()[allix]).all() and (keys.mi.to_numpy() == R.mi.to_numpy()[allix]).all()
pd.DataFrame({f: v[allix] for f, v in G.items()}).to_parquet(OUT / 'per_type_groups.parquet', index=False)
pos_in_keys = np.full(len(R), -1); pos_in_keys[allix] = np.arange(len(allix))
mi_ = R.mi.to_numpy()


def fit(tr, te, cols, seed):
    cat = ['cal_month'] if 'cal_month' in cols else 'auto'
    m = lgb.LGBMRegressor(**{**LGB, 'random_state': seed}).fit(R.loc[tr, cols], R.loc[tr, 'D'], categorical_feature=cat)
    return m.predict(R.loc[te, cols])


fallback = {}
for seed in SEEDS:
    for fam, grp in G.items():
        for mname, cols in (('HM', HMC), ('HMW14', HMC + W14C)):
            fp = PRED / str(seed) / f'PT_{fam}_{mname}.npy'
            if fp.exists():
                continue
            out = np.full(len(allix), np.nan)
            t1 = time.time()
            for Y, ix in TEST:
                pooled_tr = np.flatnonzero((mi_ + 1) < Y * 12)
                for g in np.unique(grp[ix]):
                    te = ix[grp[ix] == g]
                    tr = pooled_tr[grp[pooled_tr] == g]
                    if len(tr) < 1000:
                        fallback[f'{fam}|{g}|{Y}'] = int(len(tr)); tr = pooled_tr
                    out[pos_in_keys[te]] = fit(tr, te, cols, seed)
            assert not np.isnan(out).any()
            np.save(fp, out)
            log('seed', seed, fam, mname, f'{time.time() - t1:.0f}s')
(OUT / 'per_type_fallback.json').write_text(json.dumps(fallback, indent=1))
log('done; fallbacks', fallback)
