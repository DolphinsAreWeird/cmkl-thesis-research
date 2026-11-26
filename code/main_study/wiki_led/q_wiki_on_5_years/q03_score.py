# q03. Addendum q, step 4: scoring of Q1, Q2 and the descriptive comparisons.  Settings: prereg/addenda_wiki_led/2026-11-26_q_wikipedia_on_top_of_5_years.json
# (read-only; SHA-256 checked).  The scoring functions of addendum n (n50_score.py, from "copied from m04_score.py" to the results file) are read
# from that file and run unchanged, as o04_score.py does: change rank within format x month (x group) cells, ratio of monthly sums, the 2,000
# draws of 3-month blocks (rng 20261020), five-seed means inside each draw, p-values, Holm, Benjamini-Hochberg, the 14 families, too-small rule.
# Books with a page: has_book_page or has_author_page (as p03_page_books_scores.py); ranked within those rows only.
# Outputs: data/reports/wiki_on_5_years.json, wiki_on_5_years_segments.csv
#   Run from handoff/:  bash jobs/bg.sh q03_score main_study/wiki_led/q_wiki_on_5_years/q03_score.py
import sys, os, json, time, hashlib, pathlib, resource
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-26_q_wikipedia_on_top_of_5_years.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f4dffc8f803fd86e6914db73d32924052e044a1b9050b0d02b48d6dae0c77c4a', 'addendum q changed'
NOUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
OOUT = DATA / 'db' / 'wiki_led' / 'o_transformer_check'
OUT = DATA / 'db' / 'wiki_led' / 'q_wiki_on_5_years'
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
SRC = {'HM': NOUT, 'HMW14': NOUT, 'HMW14C': OOUT, 'HM60': OUT}
_cache = {}


def pred(seed, model):
    k = (seed, model)
    if k not in _cache:
        _cache[k] = np.load(SRC[model] / 'preds' / str(seed) / f'{model}.npy')
        assert len(_cache[k]) == N
    return _cache[k]


src = pathlib.Path(__file__).resolve().parents[1] / 'n_more_signals' / 'n50_score.py'
txt = src.read_text()
block = txt[txt.index('# ---------------------------------------------------------------- copied from m04_score.py'):txt.index("RES_F = REP / 'more_signals_single_books.json'")]
exec(compile(block, 'n50_score.py (scoring functions)', 'exec'), globals())

# check: addendum o's gain of the plain 60 months is reproduced
res_o = json.loads((REP / 'transformer_check_single_books.json').read_text())
_, MM0 = rank_monthly(np.arange(N), np.zeros(N, int), [(s, m) for s in SEEDS for m in ('HMW14C', 'HMW14')])
g0 = gain_from(MM0, 0, 'HMW14C', 'HMW14')
assert abs(g0['est'] - res_o['whole']['2019-2026']['pairs']['C_gain']['est']) < 1e-12
log('check passed: addendum o C gain reproduced', g0['est'])

MODELS = ['HM', 'HMW14', 'HM60', 'HMW14C']
PAIRS = {'Q_wiki_on_5y': ('HMW14C', 'HM60'), 'W_wiki_on_1y': ('HMW14', 'HM'), 'C_without_wiki': ('HM60', 'HM'), 'C_with_wiki': ('HMW14C', 'HMW14')}
BOOK = K.has_book_page.astype(bool).to_numpy(); AUTH = K.has_author_page.astype(bool).to_numpy()
SAMPLES = {'all_books': None, 'books_with_a_page': BOOK | AUTH, 'own_book_page': BOOK, 'author_page_only': ~BOOK & AUTH, 'no_page': ~BOOK & ~AUTH}


def share_and_diff(MM):
    """Share of the 1-year Wikipedia gain left on top of 5 years, and the difference of the two gains (2019-2026)."""
    pq_, dq_, pw_, dw_ = [], [], [], []
    for s in SEEDS:
        for (a, b), P_, D_ in ((PAIRS['Q_wiki_on_5y'], pq_, dq_), (PAIRS['W_wiki_on_1y'], pw_, dw_)):
            na, da, nb, db = MM[(s, a)][0][0], MM[(s, a)][1][0], MM[(s, b)][0][0], MM[(s, b)][1][0]
            P_.append(ratio(na, da) - ratio(nb, db)); D_.append(draws(na, da) - draws(nb, db))
    Pq, Pw = np.mean(pq_), np.mean(pw_)
    Dq, Dw = np.mean(dq_, axis=0), np.mean(dw_, axis=0)
    with np.errstate(divide='ignore', invalid='ignore'):
        sd = Dq / Dw
    share = dict(est=float(Pq / Pw), lo=float(np.nanpercentile(sd, 2.5)), hi=float(np.nanpercentile(sd, 97.5)), draws_with_gain_1y_at_or_below_0=int((Dw <= 0).sum()))
    diff = summarize([a - b for a, b in zip(pq_, pw_)], [a - b for a, b in zip(dq_, dw_)])
    return share, diff


res = dict(record='prereg/addenda_wiki_led/2026-11-26_q_wikipedia_on_top_of_5_years.json', rows=N,
           sample_rows={k: int(N if v is None else v.sum()) for k, v in SAMPLES.items()})
for name, mask in SAMPLES.items():
    w, MM = whole(MODELS, PAIRS, sel=mask)
    w['share_left'], w['difference_of_gains'] = share_and_diff(MM)
    if name in ('all_books', 'books_with_a_page'):
        w['top'] = tops(MODELS, {k: PAIRS[k] for k in ('Q_wiki_on_5y', 'W_wiki_on_1y')}, sel=mask)
    res[name] = w
    log(name, {k: round(v['est'], 4) for k, v in w['2019-2026']['pairs'].items()}, 'share left', round(w['share_left']['est'], 3))

q1, q2 = res['all_books']['2019-2026']['pairs']['Q_wiki_on_5y'], res['books_with_a_page']['2019-2026']['pairs']['Q_wiki_on_5y']
h = holm({'Q1': q1['p_one_above'], 'Q2': q2['p_one_above']}, {'Q1': q1['est'], 'Q2': q2['est']})
dec = {X: dict(est=d['est'], lo=d['lo'], hi=d['hi'], p_one=d['p_one_above'], holm=bool(h[X]), passed=bool(h[X] and d['est'] > 0 and d['lo'] > 0))
       for X, d in (('Q1', q1), ('Q2', q2))}
res['decisions'] = dec
log('decisions', dec)
RES_F = REP / 'wiki_on_5_years.json'
RES_F.write_text(json.dumps(res, indent=1, default=float))

# ---------------------------------------------------------------- by kind of book (descriptive), all books
S = segment_table({'Q': ('HMW14C', 'HM60'), 'W': ('HMW14', 'HM')})
S.to_csv(REP / 'wiki_on_5_years_segments.csv', index=False)
res['segments'] = {c: dict(groups=int(((S.comparison == c) & ~S.too_small).sum()), found=int(((S.comparison == c) & S.gain_found).sum()),
                           differs=int(((S.comparison == c) & S.differs).sum())) for c in S.comparison.unique()}
res['runtime_s'] = round(time.time() - T0)
RES_F.write_text(json.dumps(res, indent=1, default=float))
log('done')
