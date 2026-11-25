# m04. Addendum m, step 5: scoring, decisions and segments (the plain-language report is written by m05_report.py).
# Settings: prereg/addenda_wiki_led/2026-11-25_m_theme_pages_single_books.json (read-only; SHA-256 checked).
#
# Change rank as l04_backtest.py: Spearman between prediction and D within each format and origin month (within a segment group: over the
#   group's rows), format-months with fewer than 3 rows or a constant prediction skipped; a measure is a ratio of monthly sums
#   (sum of correlations over the number of format-months).  Top 20: within each format and month, stable sort, share that rose.
# Five seeds: each gain is the mean over seeds 20261020..24 of (model a minus model b), both fitted with the same seed.
# Intervals: 2,000 draws of blocks of 3 consecutive scored months, seed 20261020 (the draws of l04), the five-seed mean recomputed in each
#   draw.  One-sided p = (1 + draws <= 0) / 2,001; two-sided p = min(1, 2 x min(one-sided lower, upper)).
# Decisions (record A_theme_pages.decisions); segments (record B_segments): gains within each group and group minus the rest of the
#   family's rows; Benjamini-Hochberg at 0.05 within each comparison over all groups (gains) and separately (differences); groups with
#   fewer than 36 scored months or 1,000 scored rows are too small to judge and left out of the correction.
# Outputs: data/reports/theme_pages_single_books.json, theme_pages_segments.csv
#   Run from code/:  bash ../jobs/bg.sh m04_score main_study/wiki_led/m_theme_pages/m04_score.py
import sys, os, json, time, hashlib, pathlib, resource
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_m_theme_pages_single_books.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'df8a4fd95bb46cec3488ba062b0033156e2ded4d00678cf899471cc201663d7f', 'addendum m changed'
OUT = DATA / 'db' / 'wiki_led' / 'm_theme_pages'
PRED = OUT / 'preds'
REP = DATA / 'reports'
REP_OUT = REP
MOCK = os.environ.get('M04_MOCK')          # test mode: predictions and outputs in a mock folder (fake predictions, never reported)
if MOCK:
    PRED = pathlib.Path(MOCK) / 'preds'
    REP_OUT = pathlib.Path(MOCK)
SEEDS = [20261020 + i for i in range(5)]
B = 2000
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB', *a, flush=True)


K = pd.read_parquet(PRED / 'keys.parquet')
N = len(K)
MONTHS = np.sort(K.mi.unique())
MPOS = {m: i for i, m in enumerate(MONTHS)}
NMON = len(MONTHS)
K['mpos'] = K.mi.map(MPOS).astype(int)
K['fcode'] = K.format.map({'print': 0, 'ebook': 1, 'audiobook': 2}).astype(int)
rng = np.random.default_rng(20261020)                       # the block draws of l04_backtest.py
kb = int(np.ceil(NMON / 3))
BD = np.array([np.concatenate([np.arange(a, a + 3) % NMON for a in rng.choice(NMON, kb)])[:NMON] for _ in range(B)])

_cache = {}


def pred(seed, model):
    k = (seed, model)
    if k not in _cache:
        _cache[k] = np.load(PRED / str(seed) / f'{model}.npy')
        assert len(_cache[k]) == N
    return _cache[k]


# ---------------------------------------------------------------- change rank by group
def grouped_rank(v, gid):
    return pd.Series(v).groupby(gid).rank(method='average').to_numpy()


def rank_monthly(sel, gkey, models_seeds):
    """sel: row positions; gkey: int group code per selected row (several groups at once; ranks within format x month x group).
    -> {(seed, model): (num, den) arrays shaped (n_groups, NMON)}, plus group sizes."""
    fm = K.fcode.to_numpy()[sel] * 10 ** 6 + K.mi.to_numpy()[sel]
    codes, gk = np.unique(gkey, return_inverse=True)
    cell = pd.factorize(pd.Series(fm) * 1000 + gk)[0]           # format x month x group cell
    ncell = cell.max() + 1
    cnt = np.bincount(cell, minlength=ncell)
    cell_g = np.zeros(ncell, int); cell_g[cell] = gk
    cell_m = np.zeros(ncell, int); cell_m[cell] = K.mpos.to_numpy()[sel]
    ry = grouped_rank(K.D.to_numpy()[sel], cell)
    sy, syy = np.bincount(cell, ry, ncell), np.bincount(cell, ry * ry, ncell)
    out = {}
    for seed, model in models_seeds:
        rx = grouped_rank(pred(seed, model)[sel], cell)
        sx, sxx, sxy = np.bincount(cell, rx, ncell), np.bincount(cell, rx * rx, ncell), np.bincount(cell, rx * ry, ncell)
        n = cnt.astype(float)
        cov = n * sxy - sx * sy
        vx, vy = n * sxx - sx * sx, n * syy - sy * sy
        with np.errstate(invalid='ignore', divide='ignore'):
            r = cov / np.sqrt(vx * vy)
        ok = (cnt >= 3) & (vx > 1e-9 * np.maximum(n * n, 1)) & (vy > 1e-9 * np.maximum(n * n, 1)) & np.isfinite(r)
        num = np.zeros((len(codes), NMON)); den = np.zeros((len(codes), NMON))
        np.add.at(num, (cell_g[ok], cell_m[ok]), r[ok])
        np.add.at(den, (cell_g[ok], cell_m[ok]), 1.0)
        out[(seed, model)] = (num, den)
        out[('rows', seed, model)] = np.bincount(cell_g[ok], weights=cnt[ok], minlength=len(codes))   # scored rows per group
    return codes, out


def top20_monthly(sel, seed, model, k=20):
    q = pd.DataFrame({'f': K.fcode.to_numpy()[sel], 'm': K.mpos.to_numpy()[sel], 'p': pred(seed, model)[sel], 'rose': K.rose.to_numpy()[sel]})
    t = q.sort_values('p', ascending=False, kind='stable').groupby(['f', 'm'], sort=False).head(k)
    g = t.groupby('m').rose.agg(['sum', 'size'])
    num = np.zeros(NMON); den = np.zeros(NMON)
    num[g.index.to_numpy()] = g['sum'].to_numpy(); den[g.index.to_numpy()] = g['size'].to_numpy()
    return num, den


def ratio(num, den):
    return num.sum(-1) / den.sum(-1)


def draws(num, den):
    """num, den (NMON,) -> (B,) ratios on the block draws."""
    return num[BD].sum(1) / den[BD].sum(1)


def summarize(per_seed_pts, per_seed_draws):
    """per_seed_pts: (5,), per_seed_draws: (5, B) -> dict with five-seed mean, interval, p-values, seeds."""
    pts = np.asarray(per_seed_pts); dr = np.asarray(per_seed_draws).mean(0)
    lo_cnt, hi_cnt = int((dr <= 0).sum()), int((dr >= 0).sum())
    p_one = (1 + lo_cnt) / (B + 1)
    p_two = min(1.0, 2 * min((1 + lo_cnt) / (B + 1), (1 + hi_cnt) / (B + 1)))
    return dict(est=float(pts.mean()), lo=float(np.percentile(dr, 2.5)), hi=float(np.percentile(dr, 97.5)), p_one_above=float(p_one),
                p_two=float(p_two), seeds=[float(x) for x in pts], sd=float(pts.std(ddof=1)), min=float(pts.min()), max=float(pts.max()),
                n_above0=int((pts > 0).sum()))


def level_summary(per_seed_pts, per_seed_draws):
    pts = np.asarray(per_seed_pts); dr = np.asarray(per_seed_draws).mean(0)
    return dict(est=float(pts.mean()), lo=float(np.percentile(dr, 2.5)), hi=float(np.percentile(dr, 97.5)), sd=float(pts.std(ddof=1)),
                seeds=[float(x) for x in pts])


def gain_from(mm, gi, a, b, month_mask=None):
    pts, drs = [], []
    for s in SEEDS:
        na, da = mm[(s, a)][0][gi], mm[(s, a)][1][gi]
        nb, db = mm[(s, b)][0][gi], mm[(s, b)][1][gi]
        if month_mask is not None:
            na, da, nb, db = na * month_mask, da * month_mask, nb * month_mask, db * month_mask
        pts.append(ratio(na, da) - ratio(nb, db))
        drs.append(draws(na, da) - draws(nb, db))
    return summarize(pts, drs)


def level_from(mm, gi, a, month_mask=None):
    pts, drs = [], []
    for s in SEEDS:
        na, da = mm[(s, a)][0][gi], mm[(s, a)][1][gi]
        if month_mask is not None:
            na, da = na * month_mask, da * month_mask
        pts.append(ratio(na, da)); drs.append(draws(na, da))
    return level_summary(pts, drs)


ALLM = ['HM', 'HMW14', 'HMW14C', 'HMW14A', 'HMW14C_donor', 'HMW14A_donor', 'HMW14C_lag', 'HMW14A_lag', 'HMC', 'HMA', 'C_alone', 'A_alone',
        'C_donor_alone', 'A_donor_alone', 'HMW14K', 'HMW14KC', 'HMW14KA']
for s in SEEDS:
    for m in ALLM:
        assert (PRED / str(s) / f'{m}.npy').exists(), f'missing predictions {s} {m}'
res = dict(record='prereg/addenda_wiki_led/2026-11-25_m_theme_pages_single_books.json', rows=N, months=NMON)

# ---------------------------------------------------------------- whole main set
ALL = np.arange(N)
yr_of_month = K.groupby('mpos').year.first().reindex(range(NMON)).to_numpy()
M24 = (yr_of_month >= 2024).astype(float)
_, MM = rank_monthly(ALL, np.zeros(N, int), [(s, m) for s in SEEDS for m in ALLM])
# checks against l04 and l07
l04 = json.loads((REP / 'wiki_led_l_backtest.json').read_text())['by_period']['2019-2026']['all']
for m in ('HM', 'HMW14'):
    mine = ratio(*MM[(SEEDS[0], m)])[0]
    log('check:', m, 'change rank', mine, 'l04', l04[m]['rank']['est'])
    assert abs(mine - l04[m]['rank']['est']) < 1e-9, 'change rank does not reproduce l04'
    d_l04 = draws(MM[(SEEDS[0], m)][0][0], MM[(SEEDS[0], m)][1][0])
    assert abs(np.percentile(d_l04, 2.5) - l04[m]['rank']['lo']) < 1e-9, 'block draws do not reproduce l04'
fs = json.loads((REP / 'five_seeds_main.json').read_text())['seeds']
for s in SEEDS:
    g = ratio(*MM[(s, 'HMW14')])[0] - ratio(*MM[(s, 'HM')])[0]
    assert abs(g - fs[str(s)]['2019-2026']['L2a_HMW14_minus_HM_rank']) < 1e-9, 'five-seed gain does not reproduce l07'
log('checks passed: l04 change ranks and intervals, l07 five-seed gains')

PAIRS = {
    'own_pages_gain': ('HMW14', 'HM'),
    'C_gain': ('HMW14C', 'HMW14'), 'A_gain': ('HMW14A', 'HMW14'),
    'C_vs_donor': ('HMW14C', 'HMW14C_donor'), 'A_vs_donor': ('HMW14A', 'HMW14A_donor'),
    'C_vs_lag': ('HMW14C', 'HMW14C_lag'), 'A_vs_lag': ('HMW14A', 'HMW14A_lag'),
    'C_alone_vs_donor_alone': ('C_alone', 'C_donor_alone'), 'A_alone_vs_donor_alone': ('A_alone', 'A_donor_alone'),
    'C_without_own_pages': ('HMC', 'HM'), 'A_without_own_pages': ('HMA', 'HM'),
    'C_beyond_theme_borrowing': ('HMW14KC', 'HMW14K'), 'A_beyond_theme_borrowing': ('HMW14KA', 'HMW14K'),
    'theme_borrowing_gain': ('HMW14K', 'HMW14'),
}
whole = {'2019-2026': {}, '2024-2026': {}}
for per, mask in (('2019-2026', None), ('2024-2026', M24)):
    whole[per]['levels'] = {m: level_from(MM, 0, m, mask) for m in ALLM}
    whole[per]['pairs'] = {k: gain_from(MM, 0, a, b, mask) for k, (a, b) in PAIRS.items()}
# by format
byf = {}
codes_f, MMf = rank_monthly(ALL, K.fcode.to_numpy(), [(s, m) for s in SEEDS for m in ALLM])
for gi, c in enumerate(codes_f):
    f = ['print', 'ebook', 'audiobook'][c]
    byf[f] = {per: dict(levels={m: level_from(MMf, gi, m, mask) for m in ALLM}, pairs={k: gain_from(MMf, gi, a, b, mask) for k, (a, b) in PAIRS.items()})
              for per, mask in (('2019-2026', None), ('2024-2026', M24))}
res['whole'] = whole
res['by_format'] = byf
log('whole set scored')

# top 20 lists (all rows, and rows not yet risen)
top = {}
NYm = K.not_yet.to_numpy()
TOPM = ('HM', 'HMW14', 'HMW14C', 'HMW14A')
for fl in ('all', 'print', 'ebook', 'audiobook'):
    fsel = np.ones(N, bool) if fl == 'all' else (K.format.to_numpy() == fl)
    for lab, sel in (('top20', np.flatnonzero(fsel)), ('early_top20', np.flatnonzero(fsel & NYm))):
        tm = {(s, m): top20_monthly(sel, s, m) for s in SEEDS for m in TOPM}
        for per, mask in (('2019-2026', np.ones(NMON)), ('2024-2026', M24)):
            d = top.setdefault(per, {}).setdefault(fl, {}).setdefault(lab, {})
            mt = {k: (v[0] * mask, v[1] * mask) for k, v in tm.items()}
            for m in TOPM:
                d[m] = level_summary([ratio(*mt[(s, m)]) for s in SEEDS], [draws(*mt[(s, m)]) for s in SEEDS])
            for k_, (a, b) in (('own_pages_gain', ('HMW14', 'HM')), ('C_gain', ('HMW14C', 'HMW14')), ('A_gain', ('HMW14A', 'HMW14'))):
                d[k_] = summarize([ratio(*mt[(s, a)]) - ratio(*mt[(s, b)]) for s in SEEDS], [draws(*mt[(s, a)]) - draws(*mt[(s, b)]) for s in SEEDS])
res['top20'] = top
log('top-20 lists scored')

# ---------------------------------------------------------------- decisions
P1 = whole['2019-2026']['pairs']
pv = {X: P1[f'{X}_gain']['p_one_above'] for X in ('C', 'A')}
order = sorted(pv, key=pv.get)
holm = {}
ok_prev = True
for i, X in enumerate(order):                                   # Holm's step-down on the p-values alone; the estimate must also be above 0
    thr = 0.05 / (len(order) - i)
    rej = bool(ok_prev and pv[X] <= thr)
    holm[X] = rej and P1[f'{X}_gain']['est'] > 0
    ok_prev = rej
dec = {}
for X in ('C', 'A'):
    m2 = P1[f'{X}_vs_donor']['lo'] > 0
    m3 = P1[f'{X}_vs_lag']['lo'] > 0
    dec[X] = dict(M1_adds=holm[X], M1_p_one=pv[X], M2_beats_other_theme=bool(m2), M3_beats_moved_dates=bool(m3),
                  passed=bool(holm[X] and m2 and m3))
res['decisions'] = dec
log('decisions', dec)

# ---------------------------------------------------------------- segments
W = pd.read_parquet(OUT / 'seg_works.parquet').set_index('work_id')
POP = pd.read_parquet(OUT / 'seg_pop.parquet')
wk = K.work_id
has_item = wk.map(W.has_item).fillna(0).to_numpy() == 1
mi = K.mi.to_numpy()
lab = {}
fol = wk.map(W.follows).fillna(0).to_numpy() == 1
npm = wk.map(W.next_pub_mi).to_numpy(float)
lab['Series (Khant)'] = np.where(~has_item, None, np.where(fol | (npm <= mi), 'in a series, known at the time', 'no series link known at the time'))
adm = wk.map(W.adapt_mi).to_numpy(float)
lab['Film or TV adaptation (Khant)'] = np.where(~has_item, None, np.where(adm <= mi, 'film or TV version already out', 'no film or TV version out yet'))
# popularity tertiles: series (work, format) with a scored row in test year Y, by loans in Y-1, within format and Y
ser = K[['work_id', 'format', 'year']].drop_duplicates().merge(POP.rename(columns={'test_year': 'year'}), on=['work_id', 'format', 'year'], how='left')
assert ser.loans_prev_year.notna().all()
ser = ser.sort_values(['format', 'year', 'loans_prev_year', 'work_id'])
ser['r'] = ser.groupby(['format', 'year']).cumcount()
ser['n'] = ser.groupby(['format', 'year']).work_id.transform('size')
ser['tert'] = np.floor(3 * ser.r / ser.n).astype(int).map({0: 'low', 1: 'middle', 2: 'high'})
lab['Popularity in the year before (Khant)'] = K[['work_id', 'format', 'year']].merge(ser[['work_id', 'format', 'year', 'tert']], on=['work_id', 'format', 'year'],
                                                                                       how='left').tert.to_numpy()
lab['Fiction or nonfiction'] = wk.map(W.form).to_numpy()
lab['Audience'] = wk.map(W.audience).to_numpy()
lab['Format'] = K.format.to_numpy()
age = K.h_age.to_numpy()
lab['Time since first Seattle loan'] = np.where(age < 12, 'under 1 year', np.where(age < 60, '1 to 5 years', '5 years or more'))
lab["Author's earlier Seattle books"] = wk.map(W.author_earlier).to_numpy()
hb, ha = K.has_book_page.to_numpy() == 1, K.has_author_page.to_numpy() == 1
lab['Own Wikipedia article'] = np.where(hb, 'book article', np.where(ha, 'author article only', 'neither'))
awm = wk.map(W.award_mi).to_numpy(float)
lab['Award'] = np.where(~has_item, None, np.where(awm <= mi, 'award won by then', 'no award known by then'))
tr = wk.map(W.translated).to_numpy(float)
lab['Translated'] = np.where(~has_item | np.isnan(tr), None, np.where(tr == 1, 'translated', 'written in English'))
py = wk.map(W.pub_year).to_numpy(float)
lab['Public-domain classic'] = np.where(~has_item | np.isnan(py), None, np.where(py < 1930, 'first published before 1930', '1930 or later'))
lab['Genre (broad theme)'] = wk.map(W.genre).to_numpy()
lab['Has a theme'] = wk.map(W.has_theme).to_numpy()
for k_, v in lab.items():
    lab[k_] = pd.Series(v, dtype=object).where(pd.notna(v), None).to_numpy()

COMP = {'Own and author pages': ('HMW14', 'HM'), 'Theme pages, hand-reviewed': ('HMW14C', 'HMW14'), 'Theme pages, AI-sorted': ('HMW14A', 'HMW14')}
SEGM = ['HM', 'HMW14', 'HMW14C', 'HMW14A']
rows = []
for fam, L_ in lab.items():
    inpop = np.array([x is not None for x in L_])
    sel = np.flatnonzero(inpop)
    groups = sorted(set(L_[sel]))
    # gains within each group (one pass: ranks within format x month x group)
    gcode = pd.Series(L_[sel]).map({g: i for i, g in enumerate(groups)}).to_numpy()
    codes, MMg = rank_monthly(sel, gcode, [(s, m) for s in SEEDS for m in SEGM])
    for gi, c in enumerate(codes):
        g = groups[c]
        n_rows = int(MMg[('rows', SEEDS[0], 'HMW14')][gi])         # scored rows (format-months that were scored)
        n_rows_all = int((gcode == c).sum())
        n_months = int((MMg[(SEEDS[0], 'HMW14')][1][gi] > 0).sum())
        # the rest of the family's rows: ranks within format x month x (in g / not in g)
        if len(groups) == 2:
            rest_ix = 1 - gi
            MMr, ri = MMg, rest_ix
        else:
            _, MMr = rank_monthly(sel, (gcode == c).astype(int), [(s, m) for s in SEEDS for m in SEGM])
            ri = 0                                            # code 0 = not in g
        small = n_months < 36 or n_rows < 1000
        for cname, (a, b) in COMP.items():
            gin = gain_from(MMg, gi, a, b)
            # group minus rest, paired on the same draws
            pts, drs = [], []
            for s in SEEDS:
                ga = ratio(MMg[(s, a)][0][gi], MMg[(s, a)][1][gi]) - ratio(MMg[(s, b)][0][gi], MMg[(s, b)][1][gi])
                gr = ratio(MMr[(s, a)][0][ri], MMr[(s, a)][1][ri]) - ratio(MMr[(s, b)][0][ri], MMr[(s, b)][1][ri])
                da = draws(MMg[(s, a)][0][gi], MMg[(s, a)][1][gi]) - draws(MMg[(s, b)][0][gi], MMg[(s, b)][1][gi])
                dr_ = draws(MMr[(s, a)][0][ri], MMr[(s, a)][1][ri]) - draws(MMr[(s, b)][0][ri], MMr[(s, b)][1][ri])
                pts.append(ga - gr); drs.append(da - dr_)
            diff = summarize(pts, drs)
            base = level_from(MMg, gi, b)
            rows.append(dict(family=fam, group=g, comparison=cname, rows=n_rows, rows_all=n_rows_all, months=n_months, too_small=small,
                             base_rank=base['est'], gain=gin['est'], gain_lo=gin['lo'], gain_hi=gin['hi'], gain_p=gin['p_two'], gain_sd=gin['sd'],
                             gain_min=gin['min'], gain_max=gin['max'], gain_n_above0=gin['n_above0'],
                             diff=diff['est'], diff_lo=diff['lo'], diff_hi=diff['hi'], diff_p=diff['p_two']))
    log('family', fam, 'groups', len(groups))
S = pd.DataFrame(rows)


def bh(p):
    p = np.asarray(p, float); n = len(p)
    if n == 0:
        return p
    o = np.argsort(p)
    adj = np.minimum.accumulate((p[o] * n / np.arange(1, n + 1))[::-1])[::-1]
    out = np.empty(n); out[o] = np.minimum(adj, 1.0)
    return out


S['gain_p_bh'] = np.nan; S['diff_p_bh'] = np.nan
for cname in COMP:
    m = (S.comparison == cname) & ~S.too_small
    S.loc[m, 'gain_p_bh'] = bh(S.loc[m, 'gain_p'])
    S.loc[m, 'diff_p_bh'] = bh(S.loc[m, 'diff_p'])
S['gain_found'] = (~S.too_small) & (S.gain > 0) & (S.gain_p_bh < 0.05)
S['differs'] = (~S.too_small) & (S.diff_p_bh < 0.05)
S.to_csv(REP_OUT / 'theme_pages_segments.csv', index=False)
res['segments_summary'] = {c: dict(groups=int((S.comparison == c).sum()), judged=int(((S.comparison == c) & ~S.too_small).sum()),
                                   gains_found=int(S[(S.comparison == c)].gain_found.sum()), differences_found=int(S[(S.comparison == c)].differs.sum()))
                           for c in COMP}
res['runtime_s'] = round(time.time() - T0)
(REP_OUT / 'theme_pages_single_books.json').write_text(json.dumps(res, indent=1, default=float))
log('segments scored', res['segments_summary'])
log('done')
