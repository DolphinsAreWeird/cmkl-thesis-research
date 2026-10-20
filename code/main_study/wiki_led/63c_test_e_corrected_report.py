# 63c. Report: Test E (LibriVox), the original run against the rerun with correction A1 of addendum e.
# Writes data/reports/wiki_led_test_e_corrected.md and .json. Reads stored files only and fits no model of the data:
#   data/reports/wiki_led_test_e.json and wiki_led_test_e_c.json (headline numbers of 62_test_e_models.py and 62c_test_e_models.py),
#   data/db/wiki_led/test_e_preds.parquet and test_e_preds_c.parquet (predictions), test_e_rows.parquet and test_e_rows_c.parquet,
#   test_e_build_info_c.json (the checks of 50c_test_e_data.py), test_a_rows.parquet and test_a_rows_c.parquet (E2's training rows),
#   data/reports/wiki_led_summary_checks.json (stored values for the rows with Wikipedia views, to check this code against).
# Descriptive additions fixed in prereg/DEVIATIONS.md (entry of 20 Oct 2026 21:45 +07) before any corrected number was computed: the
# range of each top-k hit rate over all orders of tied scores, and the measures on the main rows with stored Wikipedia views. Added after
# the corrected results were seen (entry of the same evening, logged there): the share of missing Wikipedia features in E2's training
# rows with a 50-tree LightGBM example on random numbers showing how a missing value is read when a feature had none in training, and
# the table of point readings in section 7. Nothing is chosen or changed by them.
#   nice ../.venv/bin/python main_study/wiki_led/63c_test_e_corrected_report.py      (from code/; about a minute, under 1.5 GB)
import sys, os, json, time, pathlib, resource
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
DB, REP = D / 'db' / 'wiki_led', D / 'reports'
os.nice(10)                                                              # machine rule: nice
T0 = time.time()
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
WC = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS]
HC = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
MODELS = ['E1_W', 'E1_H', 'E1_HW', 'E2_W', 'E2_H', 'E2_HW', 'naive']
WMODELS = ['E1_W', 'E1_HW', 'E2_W', 'E2_HW']                             # the models that use Wikipedia
NAME = {'E1_W': 'E1 W: Wikipedia only, retrained', 'E1_H': 'E1 H: history only, retrained',
        'E1_HW': 'E1 HW: history + Wikipedia, retrained', 'E2_W': 'E2 W: Wikipedia only, Seattle model',
        'E2_H': 'E2 H: history only, Seattle model', 'E2_HW': 'E2 HW: history + Wikipedia, Seattle model',
        'naive': 'naive: repeat last month (persistence rule)'}
LAB = {'main': 'main (no automated-traffic months)', 'all': 'check (all rows)'}


def peak_gb():                                                           # macOS reports ru_maxrss in bytes
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:5.0f}s [peak {peak_gb():.2f} GB]', *a, flush=True)


def same(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return (a == b) | (np.isnan(a) & np.isnan(b))


def f4(x):
    return f'{x:.4f}'


def f3(x):
    return f'{x:.3f}'


def sg(x, d=4):
    return f'{x:+.{d}f}'


def pc(x, d=1):
    return f'{100 * x:.{d}f}%'


def ft(x):
    return f'{int(x):,}'


def yn(b):
    return 'yes' if b else 'no'


def table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '| ' + ' | '.join(['---'] + ['---:'] * (len(header) - 1)) + ' |']
    return '\n'.join(out + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows])


# ---------------------------------------------------------------- shared helpers of 15_summary_checks.py (copied)
def order_pos(df, score, groups, key):
    """Place of each row within its group (0 = highest score); ties broken by `key` ascending."""
    assert df[score].notna().all(), f'missing scores in {score}'
    o = df.sort_values(groups + [score, key], ascending=[True] * len(groups) + [False, True])
    return o.groupby(groups, sort=False).cumcount().reindex(df.index).to_numpy()


def topk(df, score, flag, k, groups, key, pos=None):
    """Mean over groups of the share of the top k with flag 1 (ties by key), with the lowest and highest value over all orders of the
    tied scores at the cut-off and the expected value when ties are ordered at random."""
    if pos is None:
        pos = order_pos(df, score, groups, key)
    gid = df.groupby(groups, sort=True).ngroup().to_numpy()
    s = df[score].to_numpy(np.float64)
    f = df[flag].to_numpy(np.float64)
    G = gid.max() + 1
    kk = np.minimum(k, np.bincount(gid, minlength=G))
    cut = np.full(G, np.nan)
    at = np.flatnonzero(pos == kk[gid] - 1)                              # the k-th highest row of each group
    cut[gid[at]] = s[at]
    c = cut[gid]
    above, tied = (s > c).astype(float), (s == c).astype(float)
    na, ha = np.bincount(gid, above, G), np.bincount(gid, above * f, G)
    nt, ht = np.bincount(gid, tied, G), np.bincount(gid, tied * f, G)
    r = kk - na                                                          # places left for the tied rows
    hits = np.bincount(gid, (pos < k) * f, G)
    return dict(rate=float(np.mean(hits / kk)), random_ties=float(np.mean((ha + r * ht / nt) / kk)),
                lowest=float(np.mean((ha + np.maximum(0, r - (nt - ht))) / kk)), highest=float(np.mean((ha + np.minimum(r, ht)) / kk)),
                groups=int(G), groups_with_ties_at_cut=int(np.sum(nt > 1)))


def month_rank(df, col, groups=('mi',), tgt='D', min_n=20):
    v = [spearmanr(g[col], g[tgt]).statistic for _, g in df.groupby(list(groups)) if g[col].nunique() > 1 and len(g) > min_n]
    return float(np.mean(v))


# ---------------------------------------------------------------- the scoring of 62_test_e_models.py (copied, for the regression check)
def alert62(df, col, k):
    t = df.sort_values(col, ascending=False).groupby('mi', sort=False).head(k)
    return int(t.rose.sum()) / len(t)


def rank62(df, col):
    return float(np.nanmean([spearmanr(g[col], g.D).statistic for _, g in df.groupby('mi')]))


OUT = {}
O = json.loads((REP / 'wiki_led_test_e.json').read_text())
C = json.loads((REP / 'wiki_led_test_e_c.json').read_text())
INFO = json.loads((DB / 'test_e_build_info_c.json').read_text())
T_ORIG = time.strftime('%Y-%m-%d %H:%M', time.localtime((REP / 'wiki_led_test_e.json').stat().st_mtime))
T_CORR = time.strftime('%Y-%m-%d %H:%M', time.localtime((REP / 'wiki_led_test_e_c.json').stat().st_mtime))
T_ROWS_C = time.strftime('%Y-%m-%d %H:%M', time.localtime((DB / 'test_e_rows_c.parquet').stat().st_mtime))

# ---------------------------------------------------------------- predictions: same rows, unchanged models
PO = pd.read_parquet(DB / 'test_e_preds.parquet')
PC = pd.read_parquet(DB / 'test_e_preds_c.parquet')
assert list(PO.columns) == list(PC.columns) and len(PO) == len(PC)
CHK = {}
CHK['preds_same_rows_same_order'] = bool((PO.book_id.to_numpy() == PC.book_id.to_numpy()).all() and (PO.mi.to_numpy() == PC.mi.to_numpy()).all())
CHK['preds_outcome_columns_differing'] = {c: int((~same(PO[c], PC[c])).sum()) for c in ['year', 'D', 'Sg', 'Y', 'rose', 'not_yet', 'flag_jump', 'has_book_page', 'has_author_page', 'L_t']}
CHK['preds_max_abs_diff'] = {m: float(np.max(np.abs(PO[m].to_numpy() - PC[m].to_numpy()))) for m in MODELS}
CHK['preds_share_rows_changed'] = {m: float((PO[m].to_numpy() != PC[m].to_numpy()).mean()) for m in MODELS}
assert CHK['preds_same_rows_same_order'] and not any(CHK['preds_outcome_columns_differing'].values())
log('predictions', json.dumps(CHK))

# ---------------------------------------------------------------- rows: which rows changed, stored views, features present
RO = pd.read_parquet(DB / 'test_e_rows.parquet', columns=['book_id', 'mi', 'b_src', 'a_src'] + WC)
RC = pd.read_parquet(DB / 'test_e_rows_c.parquet', columns=['book_id', 'mi', 'b_src', 'a_src'] + WC)
assert (RO.book_id.to_numpy() == RC.book_id.to_numpy()).all() and (RO.mi.to_numpy() == RC.mi.to_numpy()).all()
assert (RO.b_src.to_numpy() == RC.b_src.to_numpy()).all() and (RO.a_src.to_numpy() == RC.a_src.to_numpy()).all()
K = pd.DataFrame({'book_id': RO.book_id, 'mi': RO.mi, 'b_src': RO.b_src, 'a_src': RO.a_src,
                  'wchg': ~np.logical_and.reduce([same(RO[c], RC[c]) for c in WC]),
                  'feat_o': RO[WC].notna().any(axis=1), 'feat_c': RC[WC].notna().any(axis=1),
                  'bfeat_o': RO.b_lvl4.notna(), 'bfeat_c': RC.b_lvl4.notna()})
del RO, RC
PO = PO.merge(K, on=['book_id', 'mi'], how='left', validate='one_to_one')
PC = PC.merge(K, on=['book_id', 'mi'], how='left', validate='one_to_one')
del K
mainO, mainC = PO[PO.flag_jump == 0], PC[PC.flag_jump == 0]
BASE = dict(main=float(mainO.rose.mean()), main_not_yet=float(mainO.rose[mainO.not_yet].mean()), all=float(PO.rose.mean()),
            all_not_yet=float(PO.rose[PO.not_yet].mean()), main_rows=int(len(mainO)), all_rows=int(len(PO)))
assert BASE['main'] == O[LAB['main']]['base_rose'] == C[LAB['main']]['base_rose']
ROWS = dict(all_rows=int(INFO['rows_check']['rows']), all_rows_changed=int(INFO['rows_check']['rows_with_a_differing_wikipedia_value']),
            scored=int(len(PO)), scored_changed=int(PO.wchg.sum()), main=int(len(mainO)), main_changed=int(mainO.wchg.sum()),
            main_book_missing=float(1 - mainC.bfeat_c.mean()), main_book_missing_orig=float(1 - mainO.bfeat_o.mean()),
            main_no_feature=float(1 - mainC.feat_c.mean()), main_no_feature_orig=float(1 - mainO.feat_o.mean()),
            main_changed_books=int(mainO[mainO.wchg].book_id.nunique()))
log('rows', ROWS)

# ---------------------------------------------------------------- E2's training rows (Seattle, Test A rows)
SO = pd.read_parquet(DB / 'test_a_rows.parquet', columns=['work_id', 'mi', 'D'] + HC + WC)
SC = pd.read_parquet(DB / 'test_a_rows_c.parquet', columns=['work_id', 'mi', 'D'] + HC + WC)
SEA = dict(rows=int(len(SO)), same_rows_same_order=bool(len(SO) == len(SC) and (SO.work_id.to_numpy() == SC.work_id.to_numpy()).all() and (SO.mi.to_numpy() == SC.mi.to_numpy()).all()),
           target_and_history_differing={c: int((~same(SO[c], SC[c])).sum()) for c in ['D'] + HC},
           rows_with_a_differing_wikipedia_value=int((~np.logical_and.reduce([same(SO[c], SC[c]) for c in WC])).sum()))
for Y in (2019, 2026):
    tO, tC = SO[(SO.mi + 1) < Y * 12], SC[(SC.mi + 1) < Y * 12]
    SEA[f'train_{Y}'] = dict(rows=int(len(tO)), book_missing_orig=float(tO.b_lvl4.isna().mean()), book_missing_corr=float(tC.b_lvl4.isna().mean()),
                             author_missing_orig=float(tO.a_lvl4.isna().mean()), author_missing_corr=float(tC.a_lvl4.isna().mean()),
                             any_book_feature_missing_orig=float(tO[WC[:9]].isna().any(axis=1).mean()))
SEA['b_lvl4_original'] = dict(p1=float(SO.b_lvl4.quantile(0.01)), median=float(SO.b_lvl4.median()), p99=float(SO.b_lvl4.quantile(0.99)), max=float(SO.b_lvl4.max()))
assert SEA['same_rows_same_order'] and not any(SEA['target_and_history_differing'].values())
del SO, SC, tO, tC
log('Seattle rows', json.dumps(SEA))

# how LightGBM reads a missing value of a feature that had no missing value in training (50 trees on random numbers)
rng = np.random.default_rng(20261020)
xd = pd.DataFrame({'x': rng.normal(-15, 2, 5000)})
yd = (xd.x > -15).astype(float) + rng.normal(0, 0.1, 5000)
toy = lgb.LGBMRegressor(n_estimators=50, verbose=-1, random_state=20261020).fit(xd, yd)
tp = toy.predict(pd.DataFrame({'x': [np.nan, 0.0, -20.0, -10.0]}))
LGBM_NAN = dict(version=lgb.__version__, pred_missing=float(tp[0]), pred_zero=float(tp[1]), pred_minus20=float(tp[2]), pred_minus10=float(tp[3]),
                missing_read_as_zero=bool(tp[0] == tp[1]))
log('LightGBM missing-value example', LGBM_NAN)

# ---------------------------------------------------------------- regression: the stored headline numbers come from these predictions
REG = {}
for tag, P_, J in (('original', PO, O), ('corrected', PC, C)):
    worst = 0.0
    for lk, q in (('main', P_[P_.flag_jump == 0]), ('all', P_)):
        for m in MODELS:
            st = J[LAB[lk]]['models'][m]
            worst = max(worst, abs(rank62(q, m) - st['change_rank']), abs(average_precision_score(q.Sg, q[m]) / q.Sg.mean() - st['surge_ap_ratio']),
                        abs(alert62(q, m, 20) - st['top20']['rose']), abs(alert62(q, m, 50) - st['top50']['rose']),
                        abs(alert62(q[q.not_yet], m, 20) - st['early_top20']['rose']))
    REG[tag] = worst
log('regression against the stored json files, largest difference', REG)

# ---------------------------------------------------------------- headline tables
MEAS = [('change_rank', 'Change rank (Spearman of predicted and actual next-month change, per month, averaged)', f4, sg),
        ('surge_ap_ratio', 'Surge average precision, as a ratio to the base rate', f3, lambda x: sg(x, 3)),
        ('top20', 'Top-20 hit rate (share of each month\'s top 20 that rose at least 50% above the 6-month median)', f4, sg),
        ('top50', 'Top-50 hit rate', f4, sg),
        ('early_top20', 'Early warning: top-20 hit rate among books that had not yet risen', f4, sg)]


def val(J, lk, m, key):
    x = J[LAB[lk]]['models'][m][key]
    return x['rose'] if isinstance(x, dict) else x


HEAD = {}
for lk in ('main', 'all'):
    for m in MODELS:
        for key, *_ in MEAS:
            HEAD[f'{lk}|{m}|{key}'] = dict(original=val(O, lk, m, key), corrected=val(C, lk, m, key))
unchanged_models = [m for m in MODELS if all(HEAD[f'{lk}|{m}|{key}']['original'] == HEAD[f'{lk}|{m}|{key}']['corrected'] for lk in ('main', 'all') for key, *_ in MEAS)]

# ---------------------------------------------------------------- ties at the cut-off of the top-k lists (main rows)
TIES = {}
for tag, P_ in (('original', PO), ('corrected', PC)):
    q = P_[P_.flag_jump == 0]
    qe = q[q.not_yet]
    for m in WMODELS:
        TIES[f'{tag}|{m}|top20'] = topk(q, m, 'rose', 20, ['mi'], 'book_id')
        TIES[f'{tag}|{m}|top50'] = topk(q, m, 'rose', 50, ['mi'], 'book_id')
        TIES[f'{tag}|{m}|early_top20'] = topk(qe, m, 'rose', 20, ['mi'], 'book_id')
log('ties done')

# ---------------------------------------------------------------- the 90% lines (top 20 of HW, at least 0.90)
Q90 = []
for lk in ('main', 'all'):
    for m in ('E1_HW', 'E2_HW'):
        for per, y0 in (('2019-2026', 2019), ('2024-2026', 2024)):
            k = f'q90|{m}|{per}'
            o, c = O[LAB[lk]][k], C[LAB[lk]][k]
            tq = {}
            for tag, P_ in (('original', PO), ('corrected', PC)):
                q = P_ if lk == 'all' else P_[P_.flag_jump == 0]
                tq[tag] = topk(q[q.year >= y0], m, 'rose', 20, ['mi'], 'book_id')
            Q90.append(dict(rows=lk, model=m, period=per, slots=o['slots'], o=o, c=c, ties_o=tq['original'], ties_c=tq['corrected'],
                            changed=o['at_least_90'] != c['at_least_90']))

# ---------------------------------------------------------------- main rows with stored Wikipedia views (examiner review, summary checks)
FEAT = {}
for tag, P_ in (('original', PO), ('corrected', PC)):
    q = P_[P_.flag_jump == 0]
    fr = q[(q.b_src > 0) | (q.a_src > 0)]
    d = dict(rows=int(len(fr)), share_of_main=float(len(fr) / len(q)),
             with_a_feature=float((fr.feat_o if tag == 'original' else fr.feat_c).mean()),
             with_a_book_feature=float((fr.bfeat_o if tag == 'original' else fr.bfeat_c).mean()),
             rows_changed=int(fr.wchg.sum()), base_rose=float(fr.rose.mean()))
    for m in MODELS:
        d[f'rank|{m}'] = month_rank(fr, m)
        d[f'top20|{m}'] = topk(fr, m, 'rose', 20, ['mi'], 'book_id')
    FEAT[tag] = d
SV = json.loads((REP / 'wiki_led_summary_checks.json').read_text())['values_original']
FEAT_REG = {}
for m in ('E1_W', 'E2_W', 'E1_H', 'E1_HW', 'naive'):                     # the models the summary checks scored on these rows
    FEAT_REG[f'rank|{m}'] = (SV[f'E.feat.rank.{m}'], FEAT['original'][f'rank|{m}'])
    FEAT_REG[f'top20|{m}'] = (SV[f'E.feat.top20.{m}'], FEAT['original'][f'top20|{m}']['rate'])
FEAT_REG['rows'] = (SV['E.feat_rows'], FEAT['original']['rows'])
FEAT_REG_MAX = max(abs(a - b) for a, b in FEAT_REG.values())
log('rows with views', {t: {k: v for k, v in d.items() if not isinstance(v, dict)} for t, d in FEAT.items()}, '| check against summary checks', FEAT_REG_MAX)

# ---------------------------------------------------------------- point readings (no intervals exist for Test E's change ranks)
def hv(J, lk, m, key='change_rank'):
    return val(J, lk, m, key)


READ = []


def reading(text, fo, fc, vo, vc):
    READ.append(dict(text=text, original=bool(fo), corrected=bool(fc), value_original=vo, value_corrected=vc, changed=bool(fo) != bool(fc)))


for lk in ('main', 'all'):
    base = O[LAB[lk]]['base_rose']
    sfx = '' if lk == 'main' else ' (all rows)'
    for e in ('E1', 'E2'):
        w = f'{e}_W'
        reading(f'{e} W change rank above 0{sfx}', hv(O, lk, w) > 0, hv(C, lk, w) > 0, f4(hv(O, lk, w)), f4(hv(C, lk, w)))
        reading(f'{e} W surge ratio above 1{sfx}', hv(O, lk, w, 'surge_ap_ratio') > 1, hv(C, lk, w, 'surge_ap_ratio') > 1,
                f3(hv(O, lk, w, 'surge_ap_ratio')), f3(hv(C, lk, w, 'surge_ap_ratio')))
        reading(f'{e} W top-20 hit rate above the base rate ({pc(base, 2)}){sfx}', hv(O, lk, w, 'top20') > base, hv(C, lk, w, 'top20') > base,
                pc(hv(O, lk, w, 'top20'), 2), pc(hv(C, lk, w, 'top20'), 2))
        do, dc = hv(O, lk, f'{e}_HW') - hv(O, lk, f'{e}_H'), hv(C, lk, f'{e}_HW') - hv(C, lk, f'{e}_H')
        reading(f'{e} HW minus H, change rank, above 0{sfx}', do > 0, dc > 0, sg(do), sg(dc))
        to, tc = hv(O, lk, f'{e}_HW', 'top20') - hv(O, lk, f'{e}_H', 'top20'), hv(C, lk, f'{e}_HW', 'top20') - hv(C, lk, f'{e}_H', 'top20')
        reading(f'{e} HW top 20 not below H by 0.5 points or more (tie rule of addendum c){sfx}', to > -0.005, tc > -0.005,
                f'{100 * to:+.2f} points', f'{100 * tc:+.2f} points')
    for mm in ('H', 'HW'):
        reading(f'E2 {mm} change rank below E1 {mm} (the Seattle model transfers worse){sfx}', hv(O, lk, f'E2_{mm}') < hv(O, lk, f'E1_{mm}'),
                hv(C, lk, f'E2_{mm}') < hv(C, lk, f'E1_{mm}'), f'{f4(hv(O, lk, f"E2_{mm}"))} vs {f4(hv(O, lk, f"E1_{mm}"))}',
                f'{f4(hv(C, lk, f"E2_{mm}"))} vs {f4(hv(C, lk, f"E1_{mm}"))}')
for r_ in Q90:
    reading(f'90% line: {r_["model"].replace("_", " ")} top 20 at least 0.90, {r_["period"]}, {r_["rows"]} rows', r_['o']['at_least_90'], r_['c']['at_least_90'],
            f4(r_['o']['hit_rate']), f4(r_['c']['hit_rate']))
fo_, fc_ = FEAT['original'], FEAT['corrected']
for e in ('E1', 'E2'):
    reading(f'rows with stored views: {e} W change rank above 0', fo_[f'rank|{e}_W'] > 0, fc_[f'rank|{e}_W'] > 0, f4(fo_[f'rank|{e}_W']), f4(fc_[f'rank|{e}_W']))
    do, dc = fo_[f'rank|{e}_HW'] - fo_[f'rank|{e}_H'], fc_[f'rank|{e}_HW'] - fc_[f'rank|{e}_H']
    reading(f'rows with stored views: {e} HW minus H, change rank, above 0', do > 0, dc > 0, sg(do), sg(dc))
N_CHANGED = sum(r_['changed'] for r_ in READ)
log('readings', len(READ), 'changed', N_CHANGED, [r_['text'] for r_ in READ if r_['changed']])

OUT.update(base_rates=BASE, checks=CHK, rows=ROWS, seattle_rows=SEA, lightgbm_missing_example=LGBM_NAN, regression=REG, headline=HEAD, unchanged_models=unchanged_models,
           ties=TIES, q90=Q90, rows_with_views=FEAT, rows_with_views_against_summary_checks=FEAT_REG, readings=READ, build_info_checks=dict(
               check=INFO['check'], a1_check=INFO['a1_check'], rows_check={k: v for k, v in INFO['rows_check'].items()}, same_as_original_files=INFO['same_as_original_files']),
           runtime=dict(data_build_s=INFO['runtime_s'], data_build_peak_mb=INFO['peak_rss_mb'], models_s=C['runtime_s'], models_peak_mb=C['peak_rss_mb']))
(REP / 'wiki_led_test_e_corrected.json').write_text(json.dumps(OUT, indent=1, default=float))
log('json written; peak', round(peak_gb(), 2), 'GB')


# ---------------------------------------------------------------- the report
def ho(lk, m, key):
    return HEAD[f'{lk}|{m}|{key}']['original']


def hc(lk, m, key):
    return HEAD[f'{lk}|{m}|{key}']['corrected']


def q90(lk, m, per):
    return next(r_ for r_ in Q90 if r_['rows'] == lk and r_['model'] == m and r_['period'] == per)


# refit noise in Test A (check R2 of addendum e: five seeds, data/reports/wiki_led_robustness.json), a yardstick for small differences
R2S = json.loads((REP / 'wiki_led_robustness.json').read_text())['R2']['seeds'].values()
spread = lambda xs: float(max(xs) - min(xs))
NOISE = dict(seeds=len(R2S), hw_minus_h_rank=spread([s['HW_minus_H_change_rank'] for s in R2S]),
             hw_minus_h_top20=spread([s['top20_rose50']['HWlgbm_D'] - s['top20_rose50']['Hlgbm_D'] for s in R2S]),
             w_rank=spread([s['change_rank']['Wlgbm_D'] for s in R2S]), w_top20=spread([s['top20_rose50']['Wlgbm_D'] for s in R2S]),
             hw_top20=spread([s['top20_rose50']['HWlgbm_D'] for s in R2S]))
OUT['refit_noise_test_a_r2'] = NOISE
(REP / 'wiki_led_test_e_corrected.json').write_text(json.dumps(OUT, indent=1, default=float))
d1o_, d1c_ = ho('main', 'E1_HW', 'change_rank') - ho('main', 'E1_H', 'change_rank'), hc('main', 'E1_HW', 'change_rank') - hc('main', 'E1_H', 'change_rank')
d2o_ = ho('main', 'E2_HW', 'change_rank') - ho('main', 'E2_H', 'change_rank')
assert max(abs(d1o_), abs(d1c_)) < 2 * NOISE['hw_minus_h_rank'] < d2o_                  # E1's differences are noise-sized, E2's original gain is not
assert all(abs(t_[k_] - r_[s_]['hit_rate']) < 1e-9 for r_ in Q90 for t_, s_ in ((r_['ties_o'], 'o'), (r_['ties_c'], 'c')) for k_ in ('lowest', 'highest'))
A1C = INFO['a1_check']
RC_ = INFO['rows_check']
CK = INFO['check']
fo_, fc_ = FEAT['original'], FEAT['corrected']
t20 = lambda tag, m, meas='top20': TIES[f'{tag}|{m}|{meas}']
# the statements of the plain-English sections, checked here so that the text cannot drift from the numbers
assert set(unchanged_models) == {'E1_H', 'E2_H', 'naive'}
assert not any(r_['changed'] for r_ in Q90) and not any(r_['c']['at_least_90'] for r_ in Q90)
assert hc('main', 'E2_W', 'change_rank') < 0 < ho('main', 'E2_W', 'change_rank') and hc('main', 'E2_W', 'surge_ap_ratio') < 1 < ho('main', 'E2_W', 'surge_ap_ratio')
assert t20('corrected', 'E1_W')['highest'] < t20('original', 'E1_W')['lowest']                       # E1 W top-20 drop is larger than the tie effect
assert t20('corrected', 'E1_W')['lowest'] < BASE['main'] < t20('corrected', 'E1_W')['highest']        # and it now straddles the base rate
assert max(abs(h(lk, f'{e}_HW', 'change_rank') - h(lk, f'{e}_H', 'change_rank')) for h in (ho, hc) for lk in ('main', 'all') for e in ('E1', 'E2')) < 0.01
assert max(abs(h(lk, f'{e}_HW', 'top20') - h(lk, f'{e}_H', 'top20')) for h in (ho, hc) for lk in ('main', 'all') for e in ('E1', 'E2')) < 0.01
FLIPS = {'E2 W change rank above 0', 'E2 W surge ratio above 1', 'E1 HW minus H, change rank, above 0', 'E2 HW minus H, change rank, above 0',
         'E2 HW top 20 not below H by 0.5 points or more (tie rule of addendum c)', 'E1 HW minus H, change rank, above 0 (all rows)',
         'E2 HW minus H, change rank, above 0 (all rows)'}
assert {r_['text'] for r_ in READ if r_['changed']} == FLIPS, [r_['text'] for r_ in READ if r_['changed']]
assert all(hc(lk, f'E2_{mm}', 'change_rank') < hc(lk, f'E1_{mm}', 'change_rank') for lk in ('main', 'all') for mm in ('H', 'HW'))
assert fc_['rank|E1_HW'] < fc_['rank|E1_H'] and fc_['rank|E2_HW'] < fc_['rank|E2_H'] + 0.02
assert CK['raw_vs_study2r']['nan_mismatch_without_redirects'] == 0
assert all(v['first_week_rows_only_in_one_file'] == 0 and v['first_week_rows_differing'] == 0 and v['original_code_reproduces_stored_original_file'] for v in A1C.values())
assert LGBM_NAN['missing_read_as_zero'] and SEA['train_2019']['any_book_feature_missing_orig'] == 0 and SEA['train_2026']['any_book_feature_missing_orig'] == 0
assert REG['original'] == 0 and REG['corrected'] == 0 and FEAT_REG_MAX == 0

later = sum(v['articles_first_view_later'] for v in A1C.values())
nbook = A1C['book_study2r']['articles'] + A1C['book_raw']['articles']
md = []
w = md.append
w('# Test E (LibriVox) rerun with correction A1\n')
w(f"Khant Phyo Wai, 01323050. Written {time.strftime('%Y-%m-%d %H:%M')} by `code/main_study/wiki_led/63c_test_e_corrected_report.py` from stored files only; it fits no model of the data (section 8 uses one small example on random numbers). "
  f"Original run: `50_test_e_data.py` and `62_test_e_models.py` (result file of {T_ORIG}). Corrected run: `50c_test_e_data.py` (rows of {T_ROWS_C}; {INFO['runtime_s']} s, peak {INFO['peak_rss_mb']} MB) and "
  f"`62c_test_e_models.py` (result file of {T_CORR}; {C['runtime_s']} s, peak {C['peak_rss_mb']} MB), both started with `jobs/bg.sh wl_test_e_c` and run under `nice`. "
  "The reason and the plan were written into `prereg/DEVIATIONS.md` (section \"Wikipedia-led tests\", entry of 20 Oct 2026 21:45 +07) before anything was computed. The original files are untouched; every new file has the suffix `_c`.\n")

w('## Short answer\n')
w(f"No conclusion about Test E changes. Wikipedia alone is still close to chance on LibriVox, it still adds nothing to listening history, and the 90% target is still missed in all eight lines (the closest is {pc(max(r_['c']['hit_rate'] for r_ in Q90))}). "
  f"Listening history alone (E1 H, E2 H) and the persistence rule do not move at all, as they should not. "
  f"The largest change is in the Seattle model with Wikipedia only (E2 W): change rank {f4(ho('main', 'E2_W', 'change_rank'))} to {f4(hc('main', 'E2_W', 'change_rank'))}, surge ratio {f3(ho('main', 'E2_W', 'surge_ap_ratio'))} to {f3(hc('main', 'E2_W', 'surge_ap_ratio'))}, so it is now at chance rather than just above it (section 8 explains why E2 moves more than E1). "
  f"The retrained Wikipedia-only list (E1 W) loses {100 * (ho('main', 'E1_W', 'top20') - hc('main', 'E1_W', 'top20')):.1f} points in its top 20 ({pc(ho('main', 'E1_W', 'top20'))} to {pc(hc('main', 'E1_W', 'top20'))}), which leaves it at the base rate of all books ({pc(BASE['main'])}).\n")
w('The Test E table of the results draft, original and corrected (main rows; change rank, and share of each month\'s top 20 that rose):\n')
rows_ = []
for nm, m1, m2 in (('Wikipedia only', 'E1_W', 'E2_W'), ('Listening history', 'E1_H', 'E2_H'), ('History + Wikipedia', 'E1_HW', 'E2_HW'), ('Repeat last month (persistence)', 'naive', None)):
    r_ = [nm, f"{f3(ho('main', m1, 'change_rank'))} / {f3(hc('main', m1, 'change_rank'))}", f"{pc(ho('main', m1, 'top20'))} / {pc(hc('main', m1, 'top20'))}"]
    r_ += ([f"{f3(ho('main', m2, 'change_rank'))} / {f3(hc('main', m2, 'change_rank'))}", f"{pc(ho('main', m2, 'top20'))} / {pc(hc('main', m2, 'top20'))}"] if m2 else ['', ''])
    rows_.append(r_)
w(table(['Model (original / corrected)', 'Retrained: rank', 'Retrained: top 20', 'Seattle unchanged: rank', 'Seattle unchanged: top 20'], rows_) + '\n')
w(f"Other numbers of the draft's Test E paragraph: rows with stored Wikipedia views {pc(fo_['share_of_main'])} of main rows (unchanged; {pc(fc_['with_a_feature'])} of them still have at least one feature after the correction, against {pc(fo_['with_a_feature'])}); "
  f"the 90% target: {pc(q90('main', 'E1_HW', '2019-2026')['o']['hit_rate'])} to {pc(q90('main', 'E1_HW', '2019-2026')['c']['hit_rate'])}, and {pc(q90('main', 'E1_HW', '2024-2026')['o']['hit_rate'])} to {pc(q90('main', 'E1_HW', '2024-2026')['c']['hit_rate'])} in 2024 to 2026; "
  f"with all months included {pc(q90('all', 'E1_HW', '2019-2026')['o']['hit_rate'])} to {pc(q90('all', 'E1_HW', '2019-2026')['c']['hit_rate'])} (retrained) and {pc(q90('all', 'E2_HW', '2019-2026')['o']['hit_rate'])} to {pc(q90('all', 'E2_HW', '2019-2026')['c']['hit_rate'])} (Seattle model). "
  f"On the rows with stored views (the examiner review's figures): Wikipedia alone {f3(fo_['rank|E1_W'])} to {f3(fc_['rank|E1_W'])} (retrained) and {f3(fo_['rank|E2_W'])} to {f3(fc_['rank|E2_W'])} (Seattle model), history {f3(fo_['rank|E1_H'])} (unchanged), history + Wikipedia {f3(fo_['rank|E1_HW'])} to {f3(fc_['rank|E1_HW'])}.\n")

w('## 1. What was corrected\n')
w(f"- **The correction (A1 of addendum e).** A Wikipedia article that did not exist yet was stored as an article with zero views, so its first weeks looked like a huge rise and a tree model could tell \"this page will exist later\" from \"no page\". In the corrected run the weeks before an article's first week with at least one view are missing: they are removed before any rolling computation, with the same code as the corrected Test A (`10c_test_a.py`). Addendum e named Tests A, C, D and the placebo; Test E was left out, so its LibriVox rows still had the zeros, and so did the Seattle rows its E2 models are trained on.")
w(f"- **How much of Test E it touches.** Of the {nbook} book articles with a stored weekly series, {later} have their first view after the first week of their series ({A1C['book_study2r']['articles_first_view_later']} of {A1C['book_study2r']['articles']} Study 2R series, which start on {A1C['book_study2r']['first_week_of_series'][:10]}, and {A1C['book_raw']['articles_first_view_later']} of {A1C['book_raw']['articles']} series built from the raw daily file, which start in the week of {A1C['book_raw']['first_week_of_series'][:10]}); "
  f"all {A1C['author_study2r']['articles']} author articles have their first view in the first week, so no author feature changes. {ft(ROWS['all_rows_changed'])} of {ft(ROWS['all_rows'])} rows ({pc(ROWS['all_rows_changed'] / ROWS['all_rows'])}) have a different Wikipedia value; among the main scored rows {ft(ROWS['main_changed'])} of {ft(ROWS['main'])} ({pc(ROWS['main_changed'] / ROWS['main'])}), from {ROWS['main_changed_books']} books. "
  f"Main rows with a book-page feature: {pc(1 - ROWS['main_book_missing_orig'])} before, {pc(1 - ROWS['main_book_missing'])} after; with any Wikipedia feature: {pc(1 - ROWS['main_no_feature_orig'])} before, {pc(1 - ROWS['main_no_feature'])} after.")
w(f"- **E2's training rows.** E2 applies the Seattle Test A models, so it is now trained on the corrected Test A rows (`test_a_rows_c.parquet`): the same {ft(SEA['rows'])} rows in the same order with the same target and history columns (0 differing values), of which {ft(SEA['rows_with_a_differing_wikipedia_value'])} ({pc(SEA['rows_with_a_differing_wikipedia_value'] / SEA['rows'])}) have new Wikipedia values. This choice was fixed in `prereg/DEVIATIONS.md` before the run.")
w('- **Unchanged:** rows, outcomes, excluded months, the 2018 break rule, the automated-traffic filter, models, settings, seeds and the scoring code.\n')

w('## 2. Checks: same rows, same models, and identical features where nothing should change\n')
w(f"- **The feature function.** The copy of the corrected function in `50c_test_e_data.py` gives exactly the corrected Test A features (`test_a_wiki_features_c.parquet`) on the {CK['study2r_book']['articles']} book and {CK['study2r_author']['articles']} author articles the two tests share ({ft(CK['study2r_book']['rows'])} and {ft(CK['study2r_author']['rows'])} origin-month rows): largest difference {CK['study2r_book']['max_abs_diff']:.0f}, no difference in which values are missing or in which origin months have features.")
w("- **The original code first.** The original `article_features`, read from `50_test_e_data.py` itself and run again on today's inputs, reproduces the stored original features (`test_e_wiki_features.parquet`) exactly for all three sources. So the inputs have not changed since the original run and every difference below comes from A1.")
w("- **Articles whose first view is in the first week of their series: identical.** For them the correction removes nothing, and the corrected features equal the original ones exactly: the same origin months, the same values, missing equal to missing, no tolerance.\n")
rows_ = []
for nm, key in (('book articles, Study 2R series', 'book_study2r'), ('book articles, raw daily file', 'book_raw'), ('author articles, Study 2R series', 'author_study2r')):
    v = A1C[key]
    wk = v['later_weeks_after_first_view_of_last_differing_row']
    rows_.append([nm, v['first_week_of_series'][:10], v['articles'], v['articles_first_view_in_first_week'], ft(v['first_week_rows_original']),
                  v['first_week_rows_only_in_one_file'] + v['first_week_rows_differing'], v['articles_first_view_later'],
                  f"{ft(v['later_rows_original'])} / {ft(v['later_rows_corrected'])}" if v['articles_first_view_later'] else '-',
                  ft(v['later_rows_differing']) if v['articles_first_view_later'] else '-',
                  f"{wk['median']:.0f} / {wk['max']:.0f}" if v['articles_first_view_later'] else '-'])
w(table(['source', 'first week of the series', 'articles', 'first view in that week', 'their origin-month rows', 'of these differing or missing in one file',
         'first view later', 'their rows, original / corrected', 'rows differing beyond rounding', 'last differing row, weeks after first view (median / max)'], rows_) + '\n')
wkmax = max(A1C[k_]['later_weeks_after_first_view_of_last_differing_row']['max'] for k_ in ('book_study2r', 'book_raw'))
w(f"  For the articles whose first view is later, the origin months that end before the article has a complete week of views lose all nine features ({ft(A1C['book_study2r']['later_rows_without_corrected_features'] + A1C['book_raw']['later_rows_without_corrected_features'])} origin-month rows), and the first months after the first view differ because the original compared the new page with weeks of zeros. The last origin month that differs is at most {wkmax:.0f} weeks after the first view; after that the two agree (differences below 1e-9 are rounding: {ft(A1C['book_raw']['later_rows_equal_within_1e9'] + A1C['book_study2r']['later_rows_equal_within_1e9'])} rows). The corrected file has no origin month that the original lacks.")
w(f"- **Rows.** The corrected rows file has the same {ft(RC_['rows'])} rows in the same order; the {RC_['other_columns_compared']} columns other than the 18 Wikipedia features are identical (0 differing values). The links table, the months table and the list of articles still needed, recomputed by `50c`, equal the stored originals ({', '.join(k for k, v in INFO['same_as_original_files'].items() if v)}), so they were not written again.")
n_e2h = round(CHK['preds_share_rows_changed']['E2_H'] * len(PO))
w(f"- **Models without Wikipedia.** E1 H and the persistence rule give exactly the original predictions; E2 H differs on {n_e2h} of {ft(len(PO))} rows, by at most {CHK['preds_max_abs_diff']['E2_H']:.0e} (thread order inside LightGBM). Their headline numbers are identical to every digit. The models with Wikipedia are refitted on changed features, so all their predictions shift a little (largest change of a single prediction: E1 W {CHK['preds_max_abs_diff']['E1_W']:.2f}, E2 W {CHK['preds_max_abs_diff']['E2_W']:.2f}, on the scale of D).")
w(f"- **The result files come from these predictions.** Every headline number of `wiki_led_test_e.json` and `wiki_led_test_e_c.json` was recomputed here from the stored predictions with the scoring code of `62_test_e_models.py`: largest difference {REG['original']:.0f} and {REG['corrected']:.0f}. The figures on the rows with stored views (section 6) reproduce `wiki_led_summary_checks.json` exactly (largest difference {FEAT_REG_MAX:.0f}).")
w(f"- **Side check (does not touch the rows).** For the {CK['raw_vs_study2r']['articles']} book articles stored in both sources, the raw daily series and the Study 2R series still give the same features on the {CK['raw_vs_study2r']['articles_without_redirects']} articles without redirects (largest difference {CK['raw_vs_study2r']['max_abs_diff_without_redirects']:.1e}). With A1, {CK['raw_vs_study2r']['nan_mismatch']} cells now differ in being missing, all in articles whose Study 2R series also counts the views of redirects ({CK['raw_vs_study2r']['nan_mismatch_without_redirects']} in articles without redirects), where the two series can have different first weeks with views. Test E uses the Study 2R series for these articles.\n")

w('## 3. Headline numbers, original and corrected\n')
w(f"Main rows: {ft(BASE['main_rows'])} book-months without automated-traffic months, 2019 to 2026; {pc(BASE['main'], 2)} of them rose at least 50% above the 6-month median ({pc(BASE['main_not_yet'], 2)} among books that had not yet risen, the base of the early-warning list). "
  f"All rows (the check): {ft(BASE['all_rows'])} book-months; {pc(BASE['all'], 2)} rose ({pc(BASE['all_not_yet'], 2)} among books not yet risen). The same rows in both runs. Difference = corrected minus original.\n")
for key, title, fmt, dfmt in MEAS:
    w(f'### {title}\n')
    rows_ = []
    for m in MODELS:
        rows_.append([NAME[m], fmt(ho('main', m, key)), fmt(hc('main', m, key)), dfmt(hc('main', m, key) - ho('main', m, key)),
                      fmt(ho('all', m, key)), fmt(hc('all', m, key)), dfmt(hc('all', m, key) - ho('all', m, key))])
    w(table(['model', 'main: original', 'main: corrected', 'difference', 'all rows: original', 'all rows: corrected', 'difference'], rows_) + '\n')

w('## 4. The 90% lines: is the top-20 hit rate of history + Wikipedia at least 0.90?\n')
rows_ = []
for r_ in Q90:
    rows_.append([r_['rows'], r_['model'].replace('_', ' '), r_['period'], ft(r_['slots']), f4(r_['o']['hit_rate']), f"[{f4(r_['o']['ci'][0])}, {f4(r_['o']['ci'][1])}]", yn(r_['o']['at_least_90']),
                  f4(r_['c']['hit_rate']), f"[{f4(r_['c']['ci'][0])}, {f4(r_['c']['ci'][1])}]", yn(r_['c']['at_least_90']), sg(r_['c']['hit_rate'] - r_['o']['hit_rate']), 'YES' if r_['changed'] else 'no'])
w(table(['rows', 'model', 'period', 'list slots', 'original', 'exact 95% interval', 'at least 0.90', 'corrected', 'exact 95% interval', 'at least 0.90', 'difference', 'answer changed'], rows_) + '\n')
r24 = q90('main', 'E1_HW', '2024-2026')
w(f"The answer is no in all eight lines in both runs, and no interval reaches 0.90. The largest move is the retrained model in 2024 to 2026, {f4(r24['o']['hit_rate'])} to {f4(r24['c']['hit_rate'])}: {round(r24['o']['hit_rate'] * r24['slots'])} and {round(r24['c']['hit_rate'] * r24['slots'])} of {r24['slots']} list slots. Ties do not affect these lists (lowest and highest value over all orders of tied scores equal the stored value in every line).\n")

w('## 5. Ties at the cut-off of the top-k lists (main rows)\n')
w("`62_test_e_models.py` takes each month's top k with an unstable sort, so books with exactly the same score at the cut-off enter in an order that depends on the data. The Wikipedia-only models give many books the same score (every book without a Wikipedia feature gets one value), so their stored top-k rates can move without any real change. "
  "The table gives the stored value, the value expected when tied books are taken in random order, and the lowest and highest value over all orders of the tied scores (code of `15_summary_checks.py`). The history models (H) and the persistence rule are not listed: their predictions did not change.\n")
rows_ = []
for m in WMODELS:
    for meas, nm in (('top20', 'top 20'), ('top50', 'top 50'), ('early_top20', 'early warning, top 20')):
        o, c = t20('original', m, meas), t20('corrected', m, meas)
        rows_.append([m.replace('_', ' '), nm, f4(ho('main', m, meas)), f4(o['random_ties']), f"{f4(o['lowest'])} to {f4(o['highest'])}",
                      f4(hc('main', m, meas)), f4(c['random_ties']), f"{f4(c['lowest'])} to {f4(c['highest'])}", sg(c['random_ties'] - o['random_ties'])])
w(table(['model', 'list', 'original: stored', 'original: random tie order', 'original: range over tie orders', 'corrected: stored', 'corrected: random tie order', 'corrected: range over tie orders', 'difference (random tie order)'], rows_) + '\n')
o1, c1 = t20('original', 'E1_W'), t20('corrected', 'E1_W')
o2, c2 = t20('original', 'E2_W'), t20('corrected', 'E2_W')
w(f"Reading: the drop of E1 W's top 20 is larger than anything tie order can do: its range was {pc(o1['lowest'], 2)} to {pc(o1['highest'], 2)} and is now {pc(c1['lowest'], 2)} to {pc(c1['highest'], 2)}, which contains the base rate ({pc(BASE['main'], 2)}). "
  f"The moves of E2 W lie inside its tie ranges ({pc(o2['lowest'], 2)} to {pc(o2['highest'], 2)} before, {pc(c2['lowest'], 2)} to {pc(c2['highest'], 2)} after), so they say nothing. "
  f"E2 HW's early-warning list also has ties at the cut-off in {t20('corrected', 'E2_HW', 'early_top20')['groups_with_ties_at_cut']} of {t20('corrected', 'E2_HW', 'early_top20')['groups']} months, and its move ({sg(t20('corrected', 'E2_HW', 'early_top20')['random_ties'] - t20('original', 'E2_HW', 'early_top20')['random_ties'])}) lies inside its tie ranges. The other HW lists have almost no ties, so their small moves come from the refitted models, not from tie order.\n")

w('## 6. Rows with stored Wikipedia views\n')
w(f"The examiner review restated the Test E result on the main rows whose book or author article has a stored weekly series: {ft(fo_['rows'])} rows, {pc(fo_['share_of_main'])} of the main rows, the same set in both runs ({pc(fo_['base_rose'], 2)} of them rose). "
  f"After the correction {pc(fc_['with_a_feature'])} of them still have at least one Wikipedia feature ({pc(fo_['with_a_feature'])} before) and {pc(fc_['with_a_book_feature'])} a book-page feature ({pc(fo_['with_a_book_feature'])} before); {ft(fc_['rows_changed'])} of them changed. "
  "Change rank and top-20 hit rate as in `15_summary_checks.py` (Spearman within month for months with more than 20 rows, averaged; ties in the top 20 broken by book_id, with the range over all tie orders for the Wikipedia-only models).\n")
rows_ = []
for m in MODELS:
    a_, b_ = fo_[f'top20|{m}'], fc_[f'top20|{m}']
    rng_ = f" ({f4(a_['lowest'])} to {f4(a_['highest'])} / {f4(b_['lowest'])} to {f4(b_['highest'])})" if m in ('E1_W', 'E2_W') else ''
    rows_.append([NAME[m], f4(fo_[f'rank|{m}']), f4(fc_[f'rank|{m}']), sg(fc_[f'rank|{m}'] - fo_[f'rank|{m}']), f"{f4(a_['rate'])} / {f4(b_['rate'])}{rng_}"])
w(table(['model', 'change rank: original', 'corrected', 'difference', 'top 20 that rose: original / corrected (range over tie orders)'], rows_) + '\n')
w(f"The restated claim (\"there it ranks weakly and adds nothing to listening history\") holds: Wikipedia alone {f3(fc_['rank|E1_W'])} retrained and {f3(fc_['rank|E2_W'])} with the Seattle model (was {f3(fo_['rank|E1_W'])} and {f3(fo_['rank|E2_W'])}); history + Wikipedia {f3(fc_['rank|E1_HW'])} against {f3(fc_['rank|E1_H'])} for history alone (was {f3(fo_['rank|E1_HW'])}).\n")

w('## 7. Does any conclusion change?\n')
w(f"Test E has no intervals for its change ranks, so its readings are point readings. The table lists {len(READ)} of them: the yes-or-no lines of the 90% question, and the signs behind the statements in the results draft and the examiner review. {N_CHANGED} change.\n")
rows_ = [[r_['text'], yn(r_['original']), yn(r_['corrected']), r_['value_original'], r_['value_corrected'], 'YES' if r_['changed'] else 'no'] for r_ in READ]
w(table(['reading', 'original', 'corrected', 'value, original', 'value, corrected', 'changed'], rows_) + '\n')
d1o, d1c = ho('main', 'E1_HW', 'change_rank') - ho('main', 'E1_H', 'change_rank'), hc('main', 'E1_HW', 'change_rank') - hc('main', 'E1_H', 'change_rank')
d2o, d2c = ho('main', 'E2_HW', 'change_rank') - ho('main', 'E2_H', 'change_rank'), hc('main', 'E2_HW', 'change_rank') - hc('main', 'E2_H', 'change_rank')
w("**What the changes mean.** No statement in the results draft or the examiner review changes; only some of their numbers do.\n")
w(f"- \"Wikipedia alone is close to chance\" holds, more firmly than before: change rank {f4(hc('main', 'E1_W', 'change_rank'))} retrained (was {f4(ho('main', 'E1_W', 'change_rank'))}) and {f4(hc('main', 'E2_W', 'change_rank'))} with the Seattle model (was {f4(ho('main', 'E2_W', 'change_rank'))}); "
  f"surge ratio {f3(hc('main', 'E1_W', 'surge_ap_ratio'))} and {f3(hc('main', 'E2_W', 'surge_ap_ratio'))} (was {f3(ho('main', 'E1_W', 'surge_ap_ratio'))} and {f3(ho('main', 'E2_W', 'surge_ap_ratio'))}); the retrained top 20 rose {pc(hc('main', 'E1_W', 'top20'))} of the time against {pc(BASE['main'])} for all books (was {pc(ho('main', 'E1_W', 'top20'))}). "
  "Two of the flipped readings belong here: E2 W's change rank is no longer above 0 and its surge ratio no longer above 1. That is a move from just above chance to chance, not a change of conclusion.")
w(f"- \"It adds nothing to listening history\" holds. HW minus H in change rank is {sg(d1c)} retrained (was {sg(d1o)}) and {sg(d2c)} with the Seattle model (was {sg(d2o)}); the top 20 of HW rose {pc(hc('main', 'E1_HW', 'top20'))} against {pc(hc('main', 'E1_H', 'top20'))} for H retrained, and {pc(hc('main', 'E2_HW', 'top20'))} against {pc(hc('main', 'E2_H', 'top20'))} with the Seattle model. "
  f"Five of the flipped readings are about these differences: their signs in both row sets, and the 0.5-point tie rule for E2's top 20 ({100 * (hc('main', 'E2_HW', 'top20') - hc('main', 'E2_H', 'top20')):+.2f} points, was {100 * (ho('main', 'E2_HW', 'top20') - ho('main', 'E2_H', 'top20')):+.2f}). "
  f"For E1 the differences are the size of refit noise: in Test A, changing only the seed of the trees moved HW minus H by up to {NOISE['hw_minus_h_rank']:.4f} in change rank and by up to {100 * NOISE['hw_minus_h_top20']:.1f} points in the top-20 rate ({NOISE['seeds']} seeds, check R2 of `wiki_led_robustness.md`), so the sign carries no weight before or after. "
  f"For E2 the original gain ({sg(d2o)}) was larger than that noise, and it is gone after the correction (section 8 gives a likely reason). That makes \"adds nothing\" firmer, not weaker.")
w(f"- \"The 90% target is not met\" holds in all eight lines (section 4).")
w(f"- \"The Seattle model transfers worse than the retrained one\" holds: E2 is below E1 for H and for HW in both row sets.")
w(f"- On the rows with stored views, \"a weak signal that adds nothing to listening history\" holds (section 6).\n")

w('## 8. Why E2 moves more than E1\n')
s19, s26 = SEA['train_2019'], SEA['train_2026']
w(f"E1 sees one change: {ft(ROWS['main_changed'])} of its {ft(ROWS['main'])} main rows have new Wikipedia values. E2 sees a second one: its Seattle training rows are the corrected Test A rows, {pc(SEA['rows_with_a_differing_wikipedia_value'] / SEA['rows'])} of which have new values. "
  f"The second change also alters how E2 reads LibriVox books that have no book page, which is {pc(ROWS['main_book_missing'])} of the main rows.\n")
w(f"- In the original Seattle rows a book-page feature was never missing ({pc(s19['any_book_feature_missing_orig'])} of the training rows for 2019 and for 2026): every Test A work has its own article, and the stored zeros filled the time before the article existed.")
w(f"- When a feature had no missing value in training, LightGBM reads a missing value as 0. Checked here with the installed LightGBM {LGBM_NAN['version']} on 50 trees fitted to random numbers: the prediction for a missing value equals the prediction for 0 ({LGBM_NAN['pred_missing']:.4f} and {LGBM_NAN['pred_zero']:.4f}).")
w(f"- For the book-page level (lvl4, the log of the page's share of all Wikipedia views; median {SEA['b_lvl4_original']['median']:.1f} in the original Seattle rows, 99th percentile {SEA['b_lvl4_original']['p99']:.1f}, highest {SEA['b_lvl4_original']['max']:.1f}), 0 means a page with all of Wikipedia's views; the other eight book-page features were read as 0 too. "
  f"So in the original run the Seattle models scored the {pc(ROWS['main_book_missing_orig'])} of LibriVox main rows without a book page as if that page had a larger share of views than any real page.")
w(f"- In the corrected Seattle rows {pc(s26['book_missing_corr'])} of the training rows for 2026 ({pc(s19['book_missing_corr'])} for 2019) have no book-page feature yet, so the models have learned a branch for \"no page\", and LibriVox books without a page now follow it.\n")
w(f"This run does not separate the two changes. E1, which has only the first, moves its Wikipedia-only change rank by {sg(hc('main', 'E1_W', 'change_rank') - ho('main', 'E1_W', 'change_rank'))}; E2 moves by {sg(hc('main', 'E2_W', 'change_rank') - ho('main', 'E2_W', 'change_rank'))}. "
  "So part of the original E2 numbers with Wikipedia may have come from how the model filled in a missing page it had never seen in training; in the corrected run it has seen such pages.\n")

w('## 9. Files and choices\n')
w("- New code (in `code/main_study/wiki_led/`): `50c_test_e_data.py` and `62c_test_e_models.py` (copies of `50` and `62` with only the changes listed in their headers), and this report script `63c_test_e_corrected_report.py`.")
w("- New data: `data/db/wiki_led/test_e_rows_c.parquet`, `test_e_wiki_features_c.parquet`, `test_e_build_info_c.json` (all checks of `50c`), `test_e_preds_c.parquet`; results `data/reports/wiki_led_test_e_c.json`; this report and `wiki_led_test_e_corrected.json`; log `data/reports/wl_test_e_c.log`.")
w("- Choices made while coding, none changed after a result: (1) `b_src` and `a_src` (which stored series an article has) are read from the stored series, not from the feature table, so that a page with a stored series but no corrected feature keeps its source; the values equal the original ones. (2) E2 trains on the corrected Seattle rows (fixed in `DEVIATIONS.md` before the run). (3) `62c` reads only the columns the models use from the Seattle file, to keep memory low; rows and order are unchanged. (4) The unchanged links, months and needed-articles tables are compared with the stored ones instead of being written again.")
w("- How it was run: `50c` was started three times. The first run stopped in its own row check (a text-column comparison that failed under pandas 3; fixed in the check, not in the build); the third added one count to the side check of section 2 (the missing-value cells by redirects). The code that builds the features and rows did not change between the runs. `62c` ran once.")
w("- Added after the corrected results were seen (logged in `prereg/DEVIATIONS.md`; descriptive, nothing chosen from them): the missing-feature shares of E2's training rows and the LightGBM example (section 8), the table of point readings (section 7), and the base rates of the early-warning list.\n")
(REP / 'wiki_led_test_e_corrected.md').write_text('\n'.join(md) + '\n')
log('report written', REP / 'wiki_led_test_e_corrected.md', '| peak', round(peak_gb(), 2), 'GB')
