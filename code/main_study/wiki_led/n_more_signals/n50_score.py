# n50. Addendum n: scoring of parts 1, 2, 3a, 3b and 3c.  Settings: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json
# (read-only; SHA-256 checked) and addendum m's scoring (m_theme_pages/m04_score.py), whose functions are copied here unchanged: change rank
# within format x month (x group) cells, ratio of monthly sums, the 2,000 block draws of l04, five-seed means inside each draw, p-values,
# Benjamini-Hochberg, the 14 families and the too-small rule.  Seedless Chronos-2 predictions (C2, C2W) are the same for every seed.
# Usage (from code/): ../.venv/bin/python main_study/wiki_led/n_more_signals/n50_score.py PART [PART ...]   (3a, 1, 2, 3b, 3c)
# Outputs: data/reports/more_signals_single_books.json (one section per part, merged with earlier runs), more_signals_segments.csv,
#   more_signals_per_type.csv
import sys, os, json, time, hashlib, pathlib, resource
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
OUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
MOUT = DATA / 'db' / 'wiki_led' / 'm_theme_pages'
PRED = OUT / 'preds'
REP = DATA / 'reports'
SEEDS = [20261020 + i for i in range(5)]
B = 2000
PARTS = sys.argv[1:]
os.nice(5)
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB', *a, flush=True)


K = pd.read_parquet(PRED / 'keys.parquet')
Km = pd.read_parquet(MOUT / 'preds' / 'keys.parquet', columns=['work_id', 'format', 'mi'])
assert (K.work_id.to_numpy() == Km.work_id.to_numpy()).all() and (K.mi.to_numpy() == Km.mi.to_numpy()).all(), 'rows differ from addendum m'
N = len(K)
MONTHS = np.sort(K.mi.unique()); MPOS = {m: i for i, m in enumerate(MONTHS)}; NMON = len(MONTHS)
K['mpos'] = K.mi.map(MPOS).astype(int)
K['fcode'] = K.format.map({'print': 0, 'ebook': 1, 'audiobook': 2}).astype(int)
rng = np.random.default_rng(20261020)
kb = int(np.ceil(NMON / 3))
BD = np.array([np.concatenate([np.arange(a, a + 3) % NMON for a in rng.choice(NMON, kb)])[:NMON] for _ in range(B)])
yr_of_month = K.groupby('mpos').year.first().reindex(range(NMON)).to_numpy()
M24 = (yr_of_month >= 2024).astype(float)
SEEDLESS = {'C2', 'C2W'}
_cache = {}


def pred(seed, model):
    k = model if model in SEEDLESS else (seed, model)
    if k not in _cache:
        _cache[k] = np.load(PRED / f'{model}.npy') if model in SEEDLESS else np.load(PRED / str(seed) / f'{model}.npy')
        assert len(_cache[k]) == N
    return _cache[k]


def have(model):
    return (PRED / f'{model}.npy').exists() if model in SEEDLESS else all((PRED / str(s) / f'{model}.npy').exists() for s in SEEDS)


# ---------------------------------------------------------------- copied from m04_score.py
def grouped_rank(v, gid):
    return pd.Series(v).groupby(gid).rank(method='average').to_numpy()


def rank_monthly(sel, gkey, models_seeds):
    fm = K.fcode.to_numpy()[sel] * 10 ** 6 + K.mi.to_numpy()[sel]
    codes, gk = np.unique(gkey, return_inverse=True)
    cell = pd.factorize(pd.Series(fm) * 1000 + gk)[0]
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
        out[('rows', seed, model)] = np.bincount(cell_g[ok], weights=cnt[ok], minlength=len(codes))
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
    return num[BD].sum(1) / den[BD].sum(1)


def summarize(pts, drs):
    pts = np.asarray(pts); dr = np.asarray(drs).mean(0)
    lo_cnt, hi_cnt = int((dr <= 0).sum()), int((dr >= 0).sum())
    return dict(est=float(pts.mean()), lo=float(np.percentile(dr, 2.5)), hi=float(np.percentile(dr, 97.5)), p_one_above=float((1 + lo_cnt) / (B + 1)),
                p_two=float(min(1.0, 2 * min((1 + lo_cnt) / (B + 1), (1 + hi_cnt) / (B + 1)))), seeds=[float(x) for x in pts],
                sd=float(pts.std(ddof=1)), min=float(pts.min()), max=float(pts.max()), n_above0=int((pts > 0).sum()))


def level_summary(pts, drs):
    pts = np.asarray(pts); dr = np.asarray(drs).mean(0)
    return dict(est=float(pts.mean()), lo=float(np.percentile(dr, 2.5)), hi=float(np.percentile(dr, 97.5)), sd=float(pts.std(ddof=1)), seeds=[float(x) for x in pts])


def gain_from(mm, gi, a, b, mask=None):
    pts, drs = [], []
    for s in SEEDS:
        na, da = mm[(s, a)][0][gi], mm[(s, a)][1][gi]
        nb, db = mm[(s, b)][0][gi], mm[(s, b)][1][gi]
        if mask is not None:
            na, da, nb, db = na * mask, da * mask, nb * mask, db * mask
        pts.append(ratio(na, da) - ratio(nb, db)); drs.append(draws(na, da) - draws(nb, db))
    return summarize(pts, drs)


def level_from(mm, gi, a, mask=None):
    pts, drs = [], []
    for s in SEEDS:
        na, da = mm[(s, a)][0][gi], mm[(s, a)][1][gi]
        if mask is not None:
            na, da = na * mask, da * mask
        pts.append(ratio(na, da)); drs.append(draws(na, da))
    return level_summary(pts, drs)


def bh(p):
    p = np.asarray(p, float); n = len(p)
    if n == 0:
        return p
    o = np.argsort(p)
    adj = np.minimum.accumulate((p[o] * n / np.arange(1, n + 1))[::-1])[::-1]
    out = np.empty(n); out[o] = np.minimum(adj, 1.0)
    return out


def holm(pv, est):
    order = sorted(pv, key=pv.get); res = {}; ok_prev = True
    for i, X in enumerate(order):
        rej = bool(ok_prev and pv[X] <= 0.05 / (len(order) - i))
        res[X] = rej and est[X] > 0
        ok_prev = rej
    return res


# ---------------------------------------------------------------- segment labels (addendum m's 14 families)
def segment_labels():
    W = pd.read_parquet(MOUT / 'seg_works.parquet').set_index('work_id')
    POP = pd.read_parquet(MOUT / 'seg_pop.parquet')
    wk = K.work_id
    has_item = wk.map(W.has_item).fillna(0).to_numpy() == 1
    mi = K.mi.to_numpy()
    lab = {}
    fol = wk.map(W.follows).fillna(0).to_numpy() == 1
    npm = wk.map(W.next_pub_mi).to_numpy(float)
    lab['Series (asked for by Khant)'] = np.where(~has_item, None, np.where(fol | (npm <= mi), 'in a series, known at the time', 'no series link known at the time'))
    adm = wk.map(W.adapt_mi).to_numpy(float)
    lab['Film or TV adaptation (asked for by Khant)'] = np.where(~has_item, None, np.where(adm <= mi, 'film or TV version already out', 'no film or TV version out yet'))
    ser = K[['work_id', 'format', 'year']].drop_duplicates().merge(POP.rename(columns={'test_year': 'year'}), on=['work_id', 'format', 'year'], how='left')
    ser = ser.sort_values(['format', 'year', 'loans_prev_year', 'work_id'])
    ser['r'] = ser.groupby(['format', 'year']).cumcount(); ser['n'] = ser.groupby(['format', 'year']).work_id.transform('size')
    ser['tert'] = np.floor(3 * ser.r / ser.n).astype(int).map({0: 'low', 1: 'middle', 2: 'high'})
    lab['Popularity in the year before (asked for by Khant)'] = K[['work_id', 'format', 'year']].merge(ser[['work_id', 'format', 'year', 'tert']], on=['work_id', 'format', 'year'], how='left').tert.to_numpy()
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
    return {k: pd.Series(v, dtype=object).where(pd.notna(v), None).to_numpy() for k, v in lab.items()}


def segment_table(COMP, sel_all=None, families=None):
    """COMP: {name: (a, b)}; sel_all: optional boolean mask of rows that may be scored (Amazon). -> DataFrame, as m04."""
    lab = segment_labels()
    models = sorted({m for ab in COMP.values() for m in ab})
    rows = []
    for fam, L_ in lab.items():
        if families is not None and fam not in families:
            continue
        inpop = np.array([x is not None for x in L_])
        if sel_all is not None:
            inpop &= sel_all
        sel = np.flatnonzero(inpop)
        groups = sorted(set(L_[sel]))
        gcode = pd.Series(L_[sel]).map({g: i for i, g in enumerate(groups)}).to_numpy()
        codes, MMg = rank_monthly(sel, gcode, [(s, m) for s in SEEDS for m in models])
        for gi, c in enumerate(codes):
            g = groups[c]
            base_m = list(COMP.values())[0][1]                  # the comparison's base model (HMW14 for parts 1 and 2, HM for 3a)
            n_rows = int(MMg[('rows', SEEDS[0], base_m)][gi])
            n_months = int((MMg[(SEEDS[0], base_m)][1][gi] > 0).sum())
            if len(groups) == 2:
                MMr, ri = MMg, 1 - gi
            else:
                _, MMr = rank_monthly(sel, (gcode == c).astype(int), [(s, m) for s in SEEDS for m in models]); ri = 0
            small = n_months < 36 or n_rows < 1000
            for cname, (a, b) in COMP.items():
                gin = gain_from(MMg, gi, a, b)
                pts, drs = [], []
                for s in SEEDS:
                    ga = ratio(*[x[gi] for x in MMg[(s, a)]]) - ratio(*[x[gi] for x in MMg[(s, b)]])
                    gr = ratio(*[x[ri] for x in MMr[(s, a)]]) - ratio(*[x[ri] for x in MMr[(s, b)]])
                    da = draws(*[x[gi] for x in MMg[(s, a)]]) - draws(*[x[gi] for x in MMg[(s, b)]])
                    dr_ = draws(*[x[ri] for x in MMr[(s, a)]]) - draws(*[x[ri] for x in MMr[(s, b)]])
                    pts.append(ga - gr); drs.append(da - dr_)
                diff = summarize(pts, drs)
                base = level_from(MMg, gi, b)
                rows.append(dict(family=fam, group=g, comparison=cname, rows=n_rows, months=n_months, too_small=small, base_rank=base['est'],
                                 gain=gin['est'], gain_lo=gin['lo'], gain_hi=gin['hi'], gain_p=gin['p_two'], gain_sd=gin['sd'], gain_min=gin['min'],
                                 gain_max=gin['max'], gain_n_above0=gin['n_above0'], diff=diff['est'], diff_lo=diff['lo'], diff_hi=diff['hi'], diff_p=diff['p_two']))
        log('  family', fam)
    S = pd.DataFrame(rows)
    S['gain_p_bh'] = np.nan; S['diff_p_bh'] = np.nan
    for cname in COMP:
        m = (S.comparison == cname) & ~S.too_small
        S.loc[m, 'gain_p_bh'] = bh(S.loc[m, 'gain_p']); S.loc[m, 'diff_p_bh'] = bh(S.loc[m, 'diff_p'])
    S['gain_found'] = (~S.too_small) & (S.gain > 0) & (S.gain_p_bh < 0.05)
    S['differs'] = (~S.too_small) & (S.diff_p_bh < 0.05)
    return S


def whole(models, pairs, sel=None):
    sel = np.arange(N) if sel is None else np.flatnonzero(sel)
    _, MM = rank_monthly(sel, np.zeros(len(sel), int), [(s, m) for s in SEEDS for m in models])
    out = {}
    for per, mask in (('2019-2026', None), ('2024-2026', M24)):
        out[per] = dict(levels={m: level_from(MM, 0, m, mask) for m in models}, pairs={k: gain_from(MM, 0, a, b, mask) for k, (a, b) in pairs.items()})
    fc, MMf = rank_monthly(sel, K.fcode.to_numpy()[sel], [(s, m) for s in SEEDS for m in models])
    out['by_format'] = {['print', 'ebook', 'audiobook'][c]: {k: gain_from(MMf, gi, a, b) for k, (a, b) in pairs.items()} for gi, c in enumerate(fc)}
    out['by_format_levels'] = {['print', 'ebook', 'audiobook'][c]: {m: level_from(MMf, gi, m) for m in models} for gi, c in enumerate(fc)}
    return out, MM


def tops(models, pairs, sel=None):
    base = np.ones(N, bool) if sel is None else sel
    out = {}
    for lab_, s2 in (('top20', base), ('early_top20', base & K.not_yet.to_numpy())):
        ix = np.flatnonzero(s2)
        tm = {(s, m): top20_monthly(ix, s, m) for s in SEEDS for m in models}
        out[lab_] = {m: level_summary([ratio(*tm[(s, m)]) for s in SEEDS], [draws(*tm[(s, m)]) for s in SEEDS]) for m in models}
        for k, (a, b) in pairs.items():
            out[lab_][k] = summarize([ratio(*tm[(s, a)]) - ratio(*tm[(s, b)]) for s in SEEDS], [draws(*tm[(s, a)]) - draws(*tm[(s, b)]) for s in SEEDS])
    return out


RES_F = REP / 'more_signals_single_books.json'
res = json.loads(RES_F.read_text()) if RES_F.exists() else {}
res['record'] = 'prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json'
res['rows'] = N

# check: the stored library and own-page scores of addendum l and m are reproduced
l04 = json.loads((REP / 'wiki_led_l_backtest.json').read_text())['by_period']['2019-2026']['all']
_, MM0 = rank_monthly(np.arange(N), np.zeros(N, int), [(SEEDS[0], 'HM'), (SEEDS[0], 'HMW14')])
for m in ('HM', 'HMW14'):
    assert abs(ratio(*MM0[(SEEDS[0], m)])[0] - l04[m]['rank']['est']) < 1e-9
log('check passed: l04 change ranks reproduced')

if '3a' in PARTS:
    models = ['HM', 'HMW14', 'HMB', 'HMA', 'HMB_donor', 'HMA_donor']
    pairs = {'book_page_gain': ('HMB', 'HM'), 'author_page_gain': ('HMA', 'HM'), 'book_vs_donor': ('HMB', 'HMB_donor'), 'author_vs_donor': ('HMA', 'HMA_donor'),
             'author_beyond_book': ('HMW14', 'HMB'), 'book_beyond_author': ('HMW14', 'HMA'), 'both_pages_gain': ('HMW14', 'HM')}
    w, _ = whole(models, pairs)
    P1 = w['2019-2026']['pairs']
    h = holm({'book': P1['book_page_gain']['p_one_above'], 'author': P1['author_page_gain']['p_one_above']},
             {'book': P1['book_page_gain']['est'], 'author': P1['author_page_gain']['est']})
    dec = {X: dict(adds=h[X], p_one=P1[f'{X}_page_gain']['p_one_above'], beats_donor=bool(P1[f'{X}_vs_donor']['lo'] > 0),
                   passed=bool(h[X] and P1[f'{X}_vs_donor']['lo'] > 0)) for X in ('book', 'author')}
    S3a = segment_table({'Book page': ('HMB', 'HM'), 'Author page': ('HMA', 'HM')}, families=['Own Wikipedia article'])
    S3a.to_csv(REP / 'more_signals_book_author_by_article.csv', index=False)
    res['3a'] = dict(whole=w, decisions=dec)
    log('3a', dec)

if '1' in PARTS or '2' in PARTS:
    sigs = [X for X in ('N', 'AD', 'LK', 'OL', 'AZ') if have(f'HMW14{X}')]
    p12 = res.get('12', {})
    azsel = None
    if 'AZ' in sigs:
        az = json.loads((OUT / 'amazon' / 'amazon_summary.json').read_text()) if (OUT / 'amazon' / 'amazon_summary.json').exists() else \
            json.loads((OUT / 'amazon_summary.json').read_text())
        last = az.get('last_usable_mi')
        azsel = K.mi.to_numpy() <= int(last)
        p12['amazon_last_usable_mi'] = int(last)
    for X in sigs:
        models = ['HM', 'HMW14', f'HMW14{X}', f'{X}_alone', f'HMW14{X}_lag']
        pairs = {'gain': (f'HMW14{X}', 'HMW14'), 'vs_moved_dates': (f'HMW14{X}', f'HMW14{X}_lag')}
        sel = azsel if X == 'AZ' else None
        w, _ = whole(models, pairs, sel)
        w['top'] = tops(['HMW14', f'HMW14{X}'], {'gain': (f'HMW14{X}', 'HMW14')}, sel)
        p12[X] = w
        log('signal', X, w['2019-2026']['pairs']['gain'])
    if have('HMW14_ALL'):
        w, _ = whole(['HMW14', 'HMW14_ALL', 'ALL_lag'], {'gain': ('HMW14_ALL', 'HMW14'), 'vs_moved_dates': ('HMW14_ALL', 'ALL_lag')})
        w['top'] = tops(['HMW14', 'HMW14_ALL'], {'gain': ('HMW14_ALL', 'HMW14')})
        p12['ALL'] = w
    allfive = ['N', 'AD', 'LK', 'OL', 'AZ']
    pv = {X: (p12[X]['2019-2026']['pairs']['gain']['p_one_above'] if X in p12 else 1.0) for X in allfive}
    est = {X: (p12[X]['2019-2026']['pairs']['gain']['est'] if X in p12 else 0.0) for X in allfive}
    h = holm(pv, est)
    p12['decisions'] = {X: dict(available=X in p12, adds=h[X], p_one=pv[X],
                                beats_moved_dates=bool(X in p12 and p12[X]['2019-2026']['pairs']['vs_moved_dates']['lo'] > 0),
                                passed=bool(X in p12 and h[X] and p12[X]['2019-2026']['pairs']['vs_moved_dates']['lo'] > 0)) for X in allfive}
    res['12'] = p12
    log('decisions', p12['decisions'])
    # segments: each signal's gain and the combined set
    COMP = {X: (f'HMW14{X}', 'HMW14') for X in sigs if X != 'AZ'}
    if have('HMW14_ALL'):
        COMP['ALL'] = ('HMW14_ALL', 'HMW14')
    segs = [segment_table(COMP)] if COMP else []
    if 'AZ' in sigs:
        segs.append(segment_table({'AZ': ('HMW14AZ', 'HMW14')}, azsel))
    if segs:
        pd.concat(segs, ignore_index=True).to_csv(REP / 'more_signals_segments.csv', index=False)

if '3b' in PARTS:
    G = pd.read_parquet(OUT / 'per_type_groups.parquet')
    rows = []
    for fam in G.columns:
        lab = G[fam].to_numpy()
        groups = sorted(set(lab))
        gcode = pd.Series(lab).map({g: i for i, g in enumerate(groups)}).to_numpy()
        codes, MMg = rank_monthly(np.arange(N), gcode, [(s, m) for s in SEEDS for m in ('HM', 'HMW14', f'PT_{fam}_HM', f'PT_{fam}_HMW14')])
        for gi, c in enumerate(codes):
            for cname, (a, b) in (('per-type minus pooled, library model', (f'PT_{fam}_HM', 'HM')),
                                  ('per-type minus pooled, library + own pages', (f'PT_{fam}_HMW14', 'HMW14'))):
                d = gain_from(MMg, gi, a, b)
                rows.append(dict(family=fam, group=groups[c], comparison=cname, est=d['est'], lo=d['lo'], hi=d['hi'], p=d['p_two'], sd=d['sd']))
            pts, drs = [], []
            for s in SEEDS:
                f_ = lambda m: (ratio(*[x[gi] for x in MMg[(s, m)]]), draws(*[x[gi] for x in MMg[(s, m)]]))
                (a1, a1d), (b1, b1d), (a2, a2d), (b2, b2d) = f_(f'PT_{fam}_HMW14'), f_(f'PT_{fam}_HM'), f_('HMW14'), f_('HM')
                pts.append((a1 - b1) - (a2 - b2)); drs.append((a1d - b1d) - (a2d - b2d))
            d = summarize(pts, drs)
            rows.append(dict(family=fam, group=groups[c], comparison='own-page gain, per-type minus pooled', est=d['est'], lo=d['lo'], hi=d['hi'], p=d['p_two'], sd=d['sd'],
                             gain_pooled=gain_from(MMg, gi, 'HMW14', 'HM')['est'], gain_per_type=gain_from(MMg, gi, f'PT_{fam}_HMW14', f'PT_{fam}_HM')['est'],
                             rows=int(MMg[('rows', SEEDS[0], 'HMW14')][gi])))
        log('3b family', fam)
    S = pd.DataFrame(rows)
    S['p_bh'] = np.nan
    for cname in S.comparison.unique():
        m = S.comparison == cname
        S.loc[m, 'p_bh'] = bh(S.loc[m, 'p'])
    S.to_csv(REP / 'more_signals_per_type.csv', index=False)
    fb = json.loads((OUT / 'per_type_fallback.json').read_text()) if (OUT / 'per_type_fallback.json').exists() else {}
    res['3b'] = dict(n_rows=len(S), fallbacks=fb, significant={c: int(((S.comparison == c) & (S.p_bh < 0.05)).sum()) for c in S.comparison.unique()})

if '3c' in PARTS:
    models = ['HM', 'HMW14'] + [m for m in ('C2', 'C2W', 'HMW14Z') if have(m)]
    pairs = {'C2_minus_HM': ('C2', 'HM'), 'C2W_minus_HMW14': ('C2W', 'HMW14'), 'C2W_minus_C2': ('C2W', 'C2')}
    if have('HMW14Z'):
        pairs['stacking_gain'] = ('HMW14Z', 'HMW14')
    pairs = {k: v for k, v in pairs.items() if all(m in models for m in v)}
    w, _ = whole(models, pairs)
    w['top'] = tops(models, {k: v for k, v in pairs.items()})
    res['3c'] = w

res['runtime_s_last'] = round(time.time() - T0)
RES_F.write_text(json.dumps(res, indent=1, default=float))
log('done', PARTS)
