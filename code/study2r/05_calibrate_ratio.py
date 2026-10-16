"""Study 2R step 5a: choose the rise ratio from interest data only, exactly as prereg/addenda_2r/2026-10-14_a says.
Floors 300, 1000 and 3000 user views a week are all run (extension of 14 Oct, before anything was filed). Real series: the final 2R book-article list (weekly series from 04).
For each ratio in {1.5, 2.0, 2.5, 3.0, 4.0, 5.0}: sustained-shift noise share = (sustained shifts per series-year in
block-resampled series) / (the same in the real series). Surrogates: each article's own quiet usable weeks (no shift,
ratio > 0), log ratios resampled in blocks of 8 weeks, 2 surrogates per article, seed 20261014, as in
parameter_audit/calibrate_book_series.py (whose rule code, main_study/interest/_shifts.label_series, is used unchanged;
only the Mann-Kendall call is memoised, which does not change any value). Chosen ratio = smallest with noise share <= 0.30,
else the lowest noise share. No borrowing data are read.
Outputs: data/db/study2r/calibration.json, data/reports/study2r_ratio_calibration.csv
"""
import sys, pathlib
import numpy as np, pandas as pd
from common import *
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'main_study' / 'interest'))
import _shifts as SH  # noqa: E402
from _ci import settings  # noqa: E402

S0 = settings()          # reads the fixed Study 3 record and checks its SHA-256
BASE = dict(normal_weeks=26, mk_weeks=8, rise_ratio=1.5, quiet_weeks=8, mk_alpha_one_sided=0.10, sustained_min=4,
            sustained_label_week=4, fading_max=2)
for k in BASE:
    key = {'sustained_label_week': 'sustained_label_week'}.get(k, k)
    assert S0[key] == BASE[k] or k == 'rise_ratio', (k, S0[key], BASE[k])
BLOCK, REPS = 8, 2
FLOORS = (300.0, 1000.0, 3000.0)
RATIOS = (1.5, 2.0, 2.5, 3.0, 4.0, 5.0)

# memoise the Mann-Kendall test (same window -> same answer), so repeated ratios cost nothing
_orig = SH.mk.hamed_rao_modification_test
_cache = {}


def _mk(x):
    k = np.asarray(x, float).tobytes()
    if k not in _cache:
        if len(_cache) > 3_000_000:
            _cache.clear()
        _cache[k] = _orig(x)
    return _cache[k]


SH.mk.hamed_rao_modification_test = _mk

W = pd.read_parquet(OUT / 'weekly_book.parquet')
M = pd.read_parquet(OUT / 'book_matches.parquet')
SER = []
for art, g in W.groupby('article', sort=True):
    g = g.sort_values('week')
    if len(g) >= 104:
        SER.append((art, pd.DataFrame(dict(week=g.week.to_numpy(), x=g.share.to_numpy(), v=g.views.to_numpy(), valid=g.valid.to_numpy()))))
log('book article series (>= 104 weeks)', len(SER))


def years(s, MINV):
    xs = pd.Series(np.where(s.valid, s.x, np.nan)); vs = pd.Series(np.where(s.valid, s.v, np.nan))
    nm = xs.shift(1).rolling(26, min_periods=26).median(); vn = vs.shift(1).rolling(26, min_periods=26).median()
    return float((np.isfinite(nm) & (nm > 0) & (vn >= MINV) & np.isfinite(xs)).sum()) / 52.18


def surrogate(s, rng, MINV):
    w, _ = SH.label_series(s, BASE, MINV)
    q = w.usable & (w.shift_id < 0) & np.isfinite(w.ratio) & (w.ratio > 0)
    r = np.log(w.ratio[q].to_numpy())
    if len(r) < 52:
        return None
    out = np.empty(0)
    while len(out) < len(s):
        st = rng.integers(0, len(r)); out = np.concatenate([out, np.take(r, np.arange(st, st + BLOCK), mode='wrap')])
    return pd.DataFrame(dict(week=s.week.to_numpy(), x=np.exp(out[:len(s)]), v=np.full(len(s), 1e9), valid=True))


ALL, kept_sets = [], {}
for MINV in FLOORS:
    rng = np.random.default_rng(SEED)
    yrs = {art: years(s, MINV) for art, s in SER}
    reach = [a for a in yrs if yrs[a] > 0]
    SUR, n_sur_art = [], 0
    for art, s in SER:
        got = 0
        for _ in range(REPS):
            z = surrogate(s, rng, MINV)
            if z is not None:
                SUR.append(z); got += 1
        n_sur_art += got > 0
    yr = sum(yrs.values()); ys = sum((len(z) - 26) / 52.18 for z in SUR)
    works_kept = int(M.article.isin(set(reach)).sum()) if False else None
    kept_sets[MINV] = reach
    log(f'floor {MINV:.0f}: articles reaching the floor {len(reach)}; with surrogates {n_sur_art}; real series-years {yr:.0f}; surrogate years {ys:.0f}')
    for R_ in RATIOS:
        S = dict(BASE, rise_ratio=R_)
        lr = [d['label'] for _, s in SER for d in SH.label_series(s, S, MINV)[1] if d['label'] in ('sustained', 'intermediate', 'fading')]
        ls = [d['label'] for z in SUR for d in SH.label_series(z, S, MINV)[1] if d['label'] in ('sustained', 'intermediate', 'fading')]
        rs, ns = sum(l == 'sustained' for l in lr), sum(l == 'sustained' for l in ls)
        ALL.append(dict(floor=MINV, ratio=R_, articles_kept=len(reach), articles_with_surrogates=n_sur_art, real_series_years=round(yr, 1),
                        real_shifts=len(lr), real_sustained=rs, noise_sustained=ns,
                        noise_share_all=(len(ls) / ys) / (len(lr) / yr) if lr else np.nan,
                        noise_share_sustained=(ns / ys) / (rs / yr) if rs else np.nan))
        log('floor', int(MINV), 'ratio', R_, 'real shifts', len(lr), 'sustained', rs, '| noise sustained', ns, '| share', round(ALL[-1]['noise_share_sustained'], 3))
O = pd.DataFrame(ALL)
# works kept per floor (several works can share an article)
O['works_kept'] = [int(M.article.map(lambda a: a).isin([]).sum()) for _ in range(len(O))]
can = dict(zip(pd.read_parquet(OUT / 'articles.parquet').requested, pd.read_parquet(OUT / 'articles.parquet').canonical))
M['canonical'] = M.article.map(can)
O['works_kept'] = [int(M.canonical.isin(set(kept_sets[f])).sum()) for f in O.floor]
O.to_csv(REP / 'study2r_ratio_calibration.csv', index=False)
RULE = ('Pre-declared rule: if any floor >= 1000 has a ratio with sustained noise share <= 0.30, choose the lowest such floor and the smallest '
        'qualifying ratio there; otherwise keep floor 300 and ratio 4.0, the addendum-a fallback (no ratio reached 0.30 at floor 300; 4.0 had the lowest share).')
q = O[(O.floor >= 1000) & (O.noise_share_sustained <= 0.30)]
if len(q):
    f0 = q.floor.min(); pick = q[q.floor == f0].sort_values('ratio').iloc[0]; rule = 'floor >= 1000 qualified: lowest such floor, smallest qualifying ratio'
else:
    pick = O[(O.floor == 300.0) & (O.ratio == 4.0)].iloc[0]; rule = 'no floor >= 1000 reached 0.30: floor 300 and ratio 4.0 (addendum-a fallback)'
cf = float(pick.floor)
pd.DataFrame({'article': kept_sets[cf]}).to_parquet(OUT / 'kept_articles.parquet', index=False)
res = dict(chosen_ratio=float(pick.ratio), floor_views_per_week=cf, noise_share_sustained=float(pick.noise_share_sustained), rule_applied=rule, pre_declared_rule=RULE,
           n_works_matched=int(len(M)), n_book_articles=int(M.article.nunique()), n_works=int(pick.works_kept), n_articles_kept=int(pick.articles_kept),
           n_article_series=len(SER), n_articles_reaching_floor=int(pick.articles_kept), n_articles_with_surrogates=int(pick.articles_with_surrogates),
           real_series_years=float(pick.real_series_years), grid=O.round(4).to_dict('records'), seed=SEED, block_weeks=BLOCK, surrogates_per_article=REPS)
json.dump(res, open(OUT / 'calibration.json', 'w'), indent=1)
log('CHOSEN floor', int(cf), 'ratio', res['chosen_ratio'], 'noise share', round(res['noise_share_sustained'], 3), '|', rule, '| seconds', int(time.time() - T0))
