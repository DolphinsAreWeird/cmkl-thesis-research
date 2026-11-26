# o04. Addendum o, step 5: scoring of O1, O2 and the descriptive comparisons.  Settings: prereg/addenda_wiki_led/2026-11-26_o_transformer_inputs_check.json
# (read-only; SHA-256 checked).  The scoring functions of addendum n (n50_score.py, from "copied from m04_score.py" to the results file) are
# read from that file and run unchanged: change rank within format x month (x group) cells, ratio of monthly sums, the 2,000 draws of
# 3-month blocks (rng 20261020), five-seed means inside each draw, p-values, Holm, Benjamini-Hochberg, the 14 families and the too-small rule.
# O1 only: its 10 target months (2025-11 to 2026-08, origins 2025-10 to 2026-07) get their own draws, 4 blocks of 3 consecutive months drawn
#   circularly within them and cut to 10 months, rng 20261126 (record).
# Outputs: data/reports/transformer_check_single_books.json, transformer_check_segments.csv
#   Run from handoff/:  bash jobs/bg.sh o04_score main_study/wiki_led/o_transformer_check/o04_score.py
import sys, os, json, time, hashlib, pathlib, resource
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-26_o_transformer_inputs_check.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'ad6a417b47cc60b21b59742fbf79574a5370150ff78ba617e932c0a8a7fc62d6', 'addendum o changed'
NOUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
OUT = DATA / 'db' / 'wiki_led' / 'o_transformer_check'
MOUT = DATA / 'db' / 'wiki_led' / 'm_theme_pages'
REP = DATA / 'reports'
SEEDS = [20261020 + i for i in range(5)]
B = 2000
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB', *a, flush=True)


K = pd.read_parquet(NOUT / 'preds' / 'keys.parquet')
N = len(K)
MONTHS = np.sort(K.mi.unique()); MPOS = {m: i for i, m in enumerate(MONTHS)}; NMON = len(MONTHS)
K['mpos'] = K.mi.map(MPOS).astype(int)
K['fcode'] = K.format.map({'print': 0, 'ebook': 1, 'audiobook': 2}).astype(int)
rng = np.random.default_rng(20261020)
kb = int(np.ceil(NMON / 3))
BD = np.array([np.concatenate([np.arange(a, a + 3) % NMON for a in rng.choice(NMON, kb)])[:NMON] for _ in range(B)])
yr_of_month = K.groupby('mpos').year.first().reindex(range(NMON)).to_numpy()
M24 = (yr_of_month >= 2024).astype(float)
STORED = {'HM', 'HMW14', 'HMW14Z'}
_cache = {}


def pred(seed, model):
    k = (seed, model)
    if k not in _cache:
        d = NOUT if model in STORED else OUT
        _cache[k] = np.load(d / 'preds' / str(seed) / f'{model}.npy')
        assert len(_cache[k]) == N
    return _cache[k]


src = pathlib.Path(__file__).resolve().parents[1] / 'n_more_signals' / 'n50_score.py'
txt = src.read_text()
block = txt[txt.index('# ---------------------------------------------------------------- copied from m04_score.py'):txt.index("RES_F = REP / 'more_signals_single_books.json'")]
exec(compile(block, 'n50_score.py (scoring functions)', 'exec'), globals())

# check: addendum n's stacking gain is reproduced
res_n = json.loads((REP / 'more_signals_single_books.json').read_text())
_, MM0 = rank_monthly(np.arange(N), np.zeros(N, int), [(s, m) for s in SEEDS for m in ('HMW14', 'HMW14Z')])
g0 = gain_from(MM0, 0, 'HMW14Z', 'HMW14')
assert abs(g0['est'] - res_n['3c']['2019-2026']['pairs']['stacking_gain']['est']) < 1e-12
log('check passed: addendum n stacking gain reproduced', g0['est'])

MODELS = ['HM', 'HMW14', 'HMW14Z', 'HMW14C', 'HMW14CZ', 'HMW14Z1', 'HMW14Z2', 'HMW14Zlag']
PAIRS = {'O2_CZ_minus_C': ('HMW14CZ', 'HMW14C'), 'Z_gain': ('HMW14Z', 'HMW14'), 'C_gain': ('HMW14C', 'HMW14'), 'CZ_gain': ('HMW14CZ', 'HMW14'),
         'Z1_gain': ('HMW14Z1', 'HMW14'), 'Z2_gain': ('HMW14Z2', 'HMW14'), 'Z_minus_moved_dates': ('HMW14Z', 'HMW14Zlag'),
         'Z_minus_C': ('HMW14Z', 'HMW14C')}
res = dict(record='prereg/addenda_wiki_led/2026-11-26_o_transformer_inputs_check.json', rows=N)
w, MM = whole(MODELS, PAIRS)
w['top'] = tops(['HMW14', 'HMW14Z', 'HMW14C', 'HMW14CZ'], {k: PAIRS[k] for k in ('O2_CZ_minus_C', 'Z_gain', 'C_gain')})
res['whole'] = w
log('whole', {k: round(v['est'], 4) for k, v in w['2019-2026']['pairs'].items()})

# ---------------------------------------------------------------- O1: the 10 months after Chronos-2's release
WIN = np.flatnonzero(MONTHS >= 2025 * 12 + 9)                      # origins 2025-10 to 2026-07 = targets 2025-11 to 2026-08
assert len(WIN) == 10 and MONTHS[WIN[-1]] == 2026 * 12 + 6
rngw = np.random.default_rng(20261126)
BDW = np.array([np.concatenate([np.arange(a, a + 3) % 10 for a in rngw.choice(10, 4)])[:10] for _ in range(B)])


def win_summary(MMx, gi, a, b=None):
    pts, drs = [], []
    for s in SEEDS:
        na, da = MMx[(s, a)][0][gi][WIN], MMx[(s, a)][1][gi][WIN]
        pa, dra = na.sum() / da.sum(), na[BDW].sum(1) / da[BDW].sum(1)
        if b is None:
            pts.append(pa); drs.append(dra); continue
        nb, db = MMx[(s, b)][0][gi][WIN], MMx[(s, b)][1][gi][WIN]
        pts.append(pa - nb.sum() / db.sum()); drs.append(dra - nb[BDW].sum(1) / db[BDW].sum(1))
    return summarize(pts, drs) if b is not None else level_summary(pts, drs)


O1 = dict(months=[f'{(MONTHS[i] + 1) // 12}-{(MONTHS[i] + 1) % 12 + 1:02d}' for i in WIN], rows=int(K.mpos.isin(WIN).sum()),
          levels={m: win_summary(MM, 0, m) for m in MODELS},
          pairs={k: win_summary(MM, 0, a, b) for k, (a, b) in PAIRS.items()})
fc, MMf = rank_monthly(np.arange(N), K.fcode.to_numpy(), [(s, m) for s in SEEDS for m in ('HMW14', 'HMW14Z', 'HMW14C', 'HMW14CZ')])
O1['by_format'] = {['print', 'ebook', 'audiobook'][c]: {k: win_summary(MMf, gi, *PAIRS[k]) for k in ('Z_gain', 'O2_CZ_minus_C')} for gi, c in enumerate(fc)}
res['O1_window'] = O1
log('O1 window', {k: round(v['est'], 4) for k, v in O1['pairs'].items()})

# ---------------------------------------------------------------- decision
o1, o2 = O1['pairs']['Z_gain'], w['2019-2026']['pairs']['O2_CZ_minus_C']
h = holm({'O1': o1['p_one_above'], 'O2': o2['p_one_above']}, {'O1': o1['est'], 'O2': o2['est']})
dec = {X: dict(est=d['est'], lo=d['lo'], hi=d['hi'], p_one=d['p_one_above'], holm=bool(h[X]), passed=bool(h[X] and d['est'] > 0 and d['lo'] > 0))
       for X, d in (('O1', o1), ('O2', o2))}
dec['confirmed_on_past_data'] = bool(dec['O1']['passed'] and dec['O2']['passed'])
res['decisions'] = dec
log('decisions', dec)
RES_F = REP / 'transformer_check_single_books.json'
RES_F.write_text(json.dumps(res, indent=1, default=float))

# ---------------------------------------------------------------- by kind of book (descriptive)
S = segment_table({'Z': ('HMW14Z', 'HMW14'), 'CZ_vs_C': ('HMW14CZ', 'HMW14C')})
S.to_csv(REP / 'transformer_check_segments.csv', index=False)
res['segments'] = {c: dict(groups=int(((S.comparison == c) & ~S.too_small).sum()), found=int(((S.comparison == c) & S.gain_found).sum()),
                           differs=int(((S.comparison == c) & S.differs).sum())) for c in S.comparison.unique()}
res['runtime_s'] = round(time.time() - T0)
RES_F.write_text(json.dumps(res, indent=1, default=float))
log('done')
