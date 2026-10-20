# 80. Improvement round v2 for existing books (Test A): changes 1, 2, 4 and 5 of the research note.
# Settings: prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json (read-only, SHA-256 in prereg/README.md), which adopts
# Section 3 of paper/lit_search/Improvement_Methods_2026-10-20.md. Choices the note leaves open are in prereg/DEVIATIONS.md
# ("Wikipedia-led tests", entries of 2026-10-20 17:27 and 17:29 and later ones), written before any result.
#
# Stages (run from code/ with ../.venv/bin/python):
#   --stage c1      change 1: early-warning ranker on books that have not risen yet (4 variants)
#   --stage c4      change 4: Tweedie count loss (2 variants), gate between library and Wikipedia, split-conformal 80% intervals
#   --stage c2      change 2: burst-shape features (needs data/db/wiki_led/burst_features.parquet)
#   --stage c5      change 5: events and adaptation views (needs data/db/wiki_led/events.parquet, adaptation_features.parquet)
#   --stage imp_c2, imp_c5   descriptive only: which columns the models chosen in c2 or c5 use (gain importance, models for test year 2026)
#   --stage seed_c1, seed_c2, seed_c5   descriptive only: the ranker refitted with four other LightGBM seeds
#   --stage noise_c2, noise_c5          descriptive only: the same models with random columns in place of the new columns
#   (the report data/reports/wiki_led_improve_v2.md and .json is written by 81_improve_v2_report.py from the stage files)
#   --sample 0.05   develop on a random 5% of the books; everything is written to data/interim/wiki_led_v2_sample/
#
# Order of a full rerun (from handoff/; check `bash jobs/status.sh` first, one heavy job at a time; c2, c5 and the seed and importance
# stages read the choice of c1 from data/reports/wiki_led_improve_v2_c1.json):
#   nice -n 10 bash jobs/bg.sh wl_v2_c1 main_study/wiki_led/80_improve_v2.py --stage c1        (about 6 minutes)
#   nice -n 10 bash jobs/bg.sh wl_v2_c4 main_study/wiki_led/80_improve_v2.py --stage c4        (about 1 minute)
#   nice -n 10 bash jobs/bg.sh wl_v2_c2 main_study/wiki_led/80_improve_v2.py --stage c2        (about 10 minutes)
#   nice -n 10 bash jobs/bg.sh wl_v2_c5 main_study/wiki_led/80_improve_v2.py --stage c5        (about 15 minutes, needs the adaptation views)
#   then, from code/: ../.venv/bin/python main_study/wiki_led/81_improve_v2_report.py
# v0 = the stored Test A predictions (data/db/wiki_led/test_a_preds.parquet); nothing is refitted for v0.
# Tuning: test years 2019-2023, walk-forward by year (a model for year Y trains on rows whose target month is before 1 January of Y).
# Test: one run on 2024-2026 of v0 and the chosen variant on the same rows; paired differences by month with 95% intervals from
# 2,000 draws of circular blocks of 3 consecutive scored months (numpy default_rng(20261020)), as in 10_test_a.py.
import sys, json, time, pathlib, hashlib, argparse, resource, warnings
import numpy as np, pandas as pd
from scipy.stats import rankdata
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
ADD = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_d_v2_all_books_platforms.json'
NOTE = ROOT / 'paper' / 'lit_search' / 'Improvement_Methods_2026-10-20.md'
assert hashlib.sha256(ADD.read_bytes()).hexdigest() == '5f7f4ef33070f466951c7e37491c17fc3f746d2cf0abad7c90be58a832ad4585', 'addendum d changed'
assert hashlib.sha256(NOTE.read_bytes()).hexdigest() == '9eaf8ef29ba95cca2c85fd3ad0dd12d2619161d61cc49d739baf4d0cba858655', 'note changed'

ap = argparse.ArgumentParser()
ap.add_argument('--stage', required=True, choices=['c1', 'c4', 'c2', 'c5', 'imp_c2', 'imp_c5', 'seed_c1', 'seed_c2', 'seed_c5', 'noise_c2', 'noise_c5'])
ap.add_argument('--sample', type=float, default=1.0)
ap.add_argument('--dev-force', action='store_true', help='development only (needs --sample): force Tweedie 1.5 and the gate to exercise the code paths')
ARGS = ap.parse_args()
SAMPLE = ARGS.sample
IN = D / 'db' / 'wiki_led'
if SAMPLE < 1:
    OUT = D / 'interim' / 'wiki_led_v2_sample'
    REP = OUT
    OUT.mkdir(parents=True, exist_ok=True)
else:
    OUT, REP = IN, D / 'reports'

SEED = 20261020
T0 = time.time()
LN15, LN2 = np.log(1.5), np.log(2)
SCORE0 = 2019 * 12
TUNE_YEARS, TEST_YEARS = list(range(2019, 2024)), [2024, 2025, 2026]
MAYJUN = (2025 * 12 + 4, 2025 * 12 + 5)           # origin months 2025-05 and 2025-06
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
WCOLS = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS]
HCOLS = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)
V0COLS = ['Wlgbm_D', 'Wlgbm_Y', 'Hlgbm_D', 'Hlgbm_Y', 'HWlgbm_D', 'HWlgbm_Y']


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


def mem_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9      # bytes on macOS


# ====================================================================== data
def load(extra_cols=()):
    """Test A rows (all origins, for training) with the stored v0 predictions of the scored rows."""
    R = pd.read_parquet(IN / 'test_a_rows.parquet')
    PV = pd.read_parquet(IN / 'test_a_preds.parquet', columns=['work_id', 'mi'] + V0COLS)
    R = R.merge(PV, on=['work_id', 'mi'], how='left')
    if SAMPLE < 1:
        works = np.sort(R.work_id.unique())
        keep = np.random.default_rng(5).choice(works, int(round(SAMPLE * len(works))), replace=False)
        R = R[R.work_id.isin(keep)]
    R = R.sort_values(['mi', 'work_id']).reset_index(drop=True)
    R['scored'] = R.mi >= SCORE0
    R['elig'] = (R.h_lt - R.h_m6) < LN15                  # not yet risen at the origin (stored float32 columns, as D and the rise flag)
    R['rose'] = (R.D >= LN15).astype(int)
    R['rel'] = np.where(R.Sg == 1, 2, np.where(R.D >= LN15, 1, 0))
    R['burst_any'] = ((R.b_rmax >= LN2) | (R.a_rmax >= LN2))
    R['burst_book'] = (R.b_rmax >= LN2)
    R['short_hist'] = R.h_age < 12
    R['L_next'] = R.L_next.astype('float64')
    assert R.loc[R.scored, V0COLS].notna().all().all(), 'stored v0 predictions missing for scored rows'
    log('rows', len(R), 'scored', int(R.scored.sum()), 'eligible share of scored', round(float(R.loc[R.scored, 'elig'].mean()), 4))
    return R


def train_rows(R, Y):
    return R[(R.mi + 1) < Y * 12]


def test_rows(R, Y):
    return R[(R.year == Y) & R.scored]


# ====================================================================== fitting helpers
LGB_SEED = [SEED]          # only the seed check changes this


def fit_reg(tr, cols, target, params=None, objective=None):
    p = {**LGB, 'random_state': LGB_SEED[0], **(params or {})}
    if objective:
        p['objective'] = objective
    return lgb.LGBMRegressor(**p).fit(tr[cols], target)


def fit_rank(tr, cols, label, trunc):
    """LGBMRanker, lambdarank, one group per origin month (tr is sorted by month), default label gains."""
    grp = tr.groupby('mi', sort=True).size().values
    m = lgb.LGBMRanker(objective='lambdarank', lambdarank_truncation_level=trunc, **{**LGB, 'random_state': LGB_SEED[0]})
    return m.fit(tr[cols], np.asarray(label).astype(int), group=grp)


def walk_reg(R, cols, target, years, params=None, objective=None, trans=None, rows=None):
    """Walk-forward regression: predictions for the scored rows of each test year (Series aligned to R.index)."""
    out = []
    for Y in years:
        tr, te = train_rows(R, Y), test_rows(R, Y)
        if rows is not None:
            te = te[rows.loc[te.index]]
        m = fit_reg(tr, cols, tr[target], params, objective)
        p = m.predict(te[cols])
        out.append(pd.Series(trans(p) if trans else p, index=te.index))
    return pd.concat(out)


def walk_rank(R, cols, years, trunc, all_rows, label_fn=None, elig_te=True):
    """Walk-forward lambdarank ranker for books not yet risen. all_rows=False: train on eligible rows only;
    True: train on all rows, books already rising labelled 0. Predictions for the eligible scored rows."""
    out = []
    for Y in years:
        tr, te = train_rows(R, Y), test_rows(R, Y)
        te = te[te.elig]
        trn = tr if all_rows else tr[tr.elig]
        lab = trn.rel.where(trn.elig, 0)
        m = fit_rank(trn, cols, lab, trunc)
        out.append(pd.Series(m.predict(te[cols]), index=te.index))
        log(f'  ranker trunc {trunc} all_rows {all_rows}: year {Y} train {len(trn):,} test {len(te):,}')
    return pd.concat(out)


# ====================================================================== month-wise metrics
class Months:
    """Rows sorted by month: one slice per month, so that per-month metrics are fast."""

    def __init__(self, mi):
        mi = np.asarray(mi)
        cut = np.flatnonzero(np.diff(mi)) + 1
        a, b = np.r_[0, cut], np.r_[cut, len(mi)]
        self.months = mi[a]
        self.sl = [slice(x, y) for x, y in zip(a, b)]
        self.pos = np.repeat(np.arange(len(a)), b - a)


def spearman_rank(x, ry):
    rx = rankdata(x)
    rx = rx - rx.mean()
    d = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / d) if d > 0 else 0.0


class EarlyEval:
    """Early-warning measures on a set of rows (eligible rows): precision@20 of rises and of surges, base rates, NDCG@20, Spearman."""

    def __init__(self, E, min_rows=20):
        self.E = E
        self.min_rows = max(min_rows, 20)
        self.M = Months(E.mi.values)
        self.wid = E.work_id.values
        self.rose = E.rose.values.astype(float)
        self.sg = E.Sg.values.astype(float)
        self.gain = 2.0 ** E.rel.values - 1
        self.Dr = E.D.values.astype('float64')
        self.disc = 1 / np.log2(np.arange(2, 22))

    def month_table(self, score):
        score = np.asarray(score, dtype='float64')
        rows = []
        for mi, s in zip(self.M.months, self.M.sl):
            if s.stop - s.start < self.min_rows:
                rows.append((mi, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, s.stop - s.start))
                continue
            sc = score[s]
            order = np.lexsort((self.wid[s], -sc))[:20]
            g = self.gain[s]
            ideal = np.sort(g)[::-1][:20]
            idcg = float((ideal * self.disc[:len(ideal)]).sum())
            dcg = float((g[order] * self.disc[:len(order)]).sum())
            d = self.Dr[s]
            dr = rankdata(d)
            rows.append((mi, self.rose[s][order].mean(), self.sg[s][order].mean(), self.rose[s].mean(), self.sg[s].mean(),
                         dcg / idcg if idcg > 0 else np.nan, spearman_rank(sc, dr - dr.mean()), s.stop - s.start))
        t = pd.DataFrame(rows, columns=['mi', 'p20_rise', 'p20_surge', 'base_rise', 'base_surge', 'ndcg20', 'spearman', 'n'])
        t['above_base'] = np.where(t.p20_rise.isna(), np.nan, (t.p20_rise > t.base_rise).astype(float))
        return t.set_index('mi')


def early_summary(t):
    """Means over the months of a month table; lift = mean precision@20 / mean base rate."""
    return dict(p20_rise=float(t.p20_rise.mean()), p20_surge=float(t.p20_surge.mean()),
                lift_rise=float(t.p20_rise.mean() / t.base_rise.mean()), lift_surge=float(t.p20_surge.mean() / t.base_surge.mean()),
                base_rise=float(t.base_rise.mean()), base_surge=float(t.base_surge.mean()), ndcg20=float(t.ndcg20.mean()),
                spearman=float(t.spearman.mean()), share_months_above_base=float(t.above_base.mean()), months=int(t.p20_rise.notna().sum()))


EARLY_KEYS = ['p20_rise', 'p20_surge', 'ndcg20', 'spearman']


class LevelEval:
    """Level and change measures for log-scale predictions of ln(1 + next-month loans) on a set of rows sorted by month."""

    def __init__(self, S, min_rows=2):
        self.S = S
        self.min_rows = min_rows
        self.M = Months(S.mi.values)
        self.Y = S.Y.values.astype('float64')
        self.Yf = S.Y.values                          # float32 as stored (the top-10% rule compares it with a float64 threshold)
        self.act = S.L_next.values
        self.m6 = S.h_m6.values.astype('float64')
        self.D = S.D.values.astype('float64')
        self.rose = S.rose.values.astype(float)
        self.sg = S.Sg.values.astype(float)
        self.Ry = []
        self.thr = []
        for s in self.M.sl:
            r = rankdata(self.Y[s])
            self.Ry.append(r - r.mean())
            self.thr.append(np.quantile(self.Y[s], 0.9))
        self.Rd = []
        for s in self.M.sl:
            r = rankdata(self.D[s])
            self.Rd.append(r - r.mean())

    def month_table(self, yhat):
        yhat = np.asarray(yhat, dtype='float64')
        loans = np.expm1(yhat).clip(min=0)
        err = np.abs(loans - self.act)
        errl = np.abs(yhat - self.Y)
        chg = yhat - self.m6
        rows = []
        for k, (mi, s) in enumerate(zip(self.M.months, self.M.sl)):
            n = s.stop - s.start
            kk = int(np.ceil(0.1 * n))
            top = np.argsort(-yhat[s], kind='stable')[:kk]
            hit = float((self.Yf[s][top] >= self.thr[k]).sum())
            order = np.lexsort((np.arange(n), -chg[s]))[:20]
            ok = n >= self.min_rows
            rows.append((mi, n, err[s].sum(), self.act[s].sum(), errl[s].sum(), (err[s] <= 2).sum(), hit, kk,
                         spearman_rank(yhat[s], self.Ry[k]) if ok else np.nan, spearman_rank(chg[s], self.Rd[k]) if ok else np.nan,
                         self.rose[s][order].mean() if ok else np.nan))
        t = pd.DataFrame(rows, columns=['mi', 'n', 'ae', 'act', 'ael', 'w2', 'hit', 'k', 'spearman_level', 'change_rank', 'alert20_all'])
        return t.set_index('mi')


POOLED = {'MAE_loans': ('ae', 'n'), 'MAE_log': ('ael', 'n'), 'WAPE': ('ae', 'act'), 'within2': ('w2', 'n'), 'top10_hit': ('hit', 'k')}
MEANED = ['spearman_level', 'change_rank', 'alert20_all']
LEVEL_KEYS = list(POOLED) + MEANED


def level_summary(t, S=None, yhat=None):
    d = {m: float(t[a].sum() / t[b].sum()) for m, (a, b) in POOLED.items()}
    d.update({m: float(t[m].mean()) for m in MEANED})
    if yhat is not None:
        d['median_err_loans'] = float(np.median(np.abs(np.expm1(np.asarray(yhat)).clip(min=0) - S.L_next.values)))
    d['months'] = int(t.spearman_level.notna().sum())
    return d


def make_BD(n, nb=2000, block=3):
    """Circular blocks of 3 consecutive scored months, as 10_test_a.py."""
    rng = np.random.default_rng(SEED)
    starts = np.arange(n)
    k = int(np.ceil(n / block))
    return np.array([np.concatenate([np.arange(a, a + block) % n for a in rng.choice(starts, k)])[:n] for _ in range(nb)])


def ci_mean(x, BD):
    """Mean over months and 95% interval from the month-block draws; months with a missing value are skipped."""
    x = np.asarray(x, dtype='float64')
    if np.isnan(x).all():
        return dict(value=float('nan'), lo=float('nan'), hi=float('nan'))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        b = np.nanmean(x[BD], axis=1)
    return dict(value=float(np.nanmean(x)), lo=float(np.nanpercentile(b, 2.5)), hi=float(np.nanpercentile(b, 97.5)))


def ci_pooled(t, num, den, BD):
    a, b = t[num].values.astype('float64'), t[den].values.astype('float64')
    bs = a[BD].sum(1) / b[BD].sum(1)
    return dict(value=float(a.sum() / b.sum()), lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)))


def ci_paired_mean(x, y, BD):
    r = ci_mean(np.asarray(x, dtype='float64') - np.asarray(y, dtype='float64'), BD)
    return dict(diff=r['value'], lo=r['lo'], hi=r['hi'])


def ci_paired_pooled(t1, t0, num, den, BD):
    a1, b1 = t1[num].values.astype('float64'), t1[den].values.astype('float64')
    a0, b0 = t0[num].values.astype('float64'), t0[den].values.astype('float64')
    bs = a1[BD].sum(1) / b1[BD].sum(1) - a0[BD].sum(1) / b0[BD].sum(1)
    return dict(diff=float(a1.sum() / b1.sum() - a0.sum() / b0.sum()), lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)))


def ap_draws(y, score, mpos, BD):
    """Average precision over the base rate, for each month-block draw (weighted by how often a month is drawn)."""
    order = np.argsort(-score, kind='stable')
    ys = y[order].astype('float64')
    ms = mpos[order]
    n = BD.shape[1]
    out = np.empty(len(BD))
    for t in range(len(BD)):
        w = np.bincount(BD[t], minlength=n).astype('float64')[ms]
        cw = np.cumsum(w)
        cwy = np.cumsum(w * ys)
        tot = cwy[-1]
        with np.errstate(invalid='ignore', divide='ignore'):          # a draw without any surge in its months gives NaN, skipped by the interval
            out[t] = (np.sum(w * ys * cwy / np.maximum(cw, 1e-12)) / tot) / (tot / cw[-1])
    return out


def ap_ratio(y, score, mpos=None, BD=None):
    """Point value of AP / base rate on pooled rows (sklearn definition) and, if BD is given, draws of it."""
    from sklearn.metrics import average_precision_score
    v = float(average_precision_score(y, score) / np.mean(y))
    if BD is None:
        return v
    d = ap_draws(y, score, mpos, BD)
    return dict(value=v, lo=float(np.nanpercentile(d, 2.5)), hi=float(np.nanpercentile(d, 97.5))), d


def jdump(obj, path):
    pathlib.Path(path).write_text(json.dumps(obj, indent=1, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o)))
    log('wrote', path)


# ====================================================================== placebo donors (rebuilt exactly as in 11_placebo_a.py)
def donor_map():
    R = pd.read_parquet(IN / 'test_a_rows.parquet')
    W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')

    def match_value(col):
        x = R[['work_id', 'mi', col]].dropna()
        early = x[(x.mi >= 2016 * 12 + 2) & (x.mi <= 2018 * 12 + 11)].groupby('work_id')[col].median()
        first12 = x.sort_values('mi').groupby('work_id').head(12).groupby('work_id')[col].median()
        return early.combine_first(first12)

    vb, va = match_value('b_lvl4'), match_value('a_lvl4')
    info = W.set_index('work_id')[['article', 'author_article', 'creator']]
    info['akey'] = info.author_article.fillna('creator:' + info.creator.astype(str))
    donor = {}
    for kind, v in (('book', vb), ('author', va)):
        pool = v.sort_values()
        keys, vals = pool.index.values, pool.values
        for b in info.index:
            if b in donor or (kind == 'author' and b in vb.index):
                continue
            if b not in v.index:
                continue
            i = np.searchsorted(vals, v[b])
            best, bd = None, np.inf
            for j in range(max(0, i - 50), min(len(vals), i + 50)):
                d = keys[j]
                if d == b or info.akey[d] == info.akey[b]:
                    continue
                dist = abs(vals[j] - v[b])
                if dist < bd or (dist == bd and d < best):
                    best, bd = d, dist
            if best is not None:
                donor[b] = best
    log('donors', len(donor), 'of', len(info))
    return donor, info


def placebo_frame(R, donor, info, extra_tables=()):
    """R with the Test A Wikipedia features (and the extra feature tables, each (frame, key, prefix, cols)) replaced by those of the donor book.
    A book without a donor keeps its own features, as in 11_placebo_a.py."""
    WF = pd.read_parquet(IN / 'test_a_wiki_features.parquet')
    FB = WF[WF.kind == 'book'].drop(columns='kind').rename(columns={c: 'b_' + c for c in FEATS})
    FA = WF[WF.kind == 'author'].drop(columns='kind').rename(columns={c: 'a_' + c for c in FEATS})
    P = R.drop(columns=WCOLS).copy()
    P['donor'] = P.work_id.map(donor)
    P['d_article'] = P.donor.map(info.article)
    P['d_author'] = P.donor.map(info.author_article)
    P = P.merge(FB.rename(columns={'article': 'd_article'}), on=['d_article', 'mi'], how='left')
    P = P.merge(FA.rename(columns={'article': 'd_author'}), on=['d_author', 'mi'], how='left')
    nod = P.donor.isna().values
    P.loc[nod, WCOLS] = R.loc[nod, WCOLS].values
    for tab, kind, cols in extra_tables:
        key = 'd_article' if kind == 'book' else 'd_author'
        pre = 'b_' if kind == 'book' else 'a_'
        x = tab[tab.kind == kind].drop(columns='kind').rename(columns={'article': key, **{c: pre + c for c in cols}})
        P = P.drop(columns=[pre + c for c in cols], errors='ignore').merge(x[[key, 'mi'] + [pre + c for c in cols]], on=[key, 'mi'], how='left')
        own = R.loc[nod, [pre + c for c in cols]].values
        P.loc[nod, [pre + c for c in cols]] = own
    P = P.sort_values(['mi', 'work_id']).reset_index(drop=True)
    return P


# ====================================================================== stage c1: early-warning ranker
C1_VARIANTS = {'R20e': (20, False), 'R100e': (100, False), 'R20a': (20, True), 'R100a': (100, True)}


def eval_early_sets(E, scores):
    """Month tables of the early-warning measures for named scores on the eligible rows E (sorted by month)."""
    ev = EarlyEval(E)
    tabs = {k: ev.month_table(v) for k, v in scores.items()}
    return ev, tabs


def paired_early(tabs, a, b, BD):
    return {k: ci_paired_mean(tabs[a][k].values, tabs[b][k].values, BD) for k in EARLY_KEYS}


def stage_c1():
    R = load()
    res = dict(stage='c1', sample=SAMPLE)
    Sc = R[R.scored]
    res['n'] = dict(scored_rows=int(len(Sc)), eligible_rows=int(Sc.elig.sum()), eligible_share=float(Sc.elig.mean()),
                    books=int(Sc.work_id.nunique()))
    # ------------------------------------------------ tuning 2019-2023
    log('tuning: four ranker variants on', TUNE_YEARS)
    TP = {}
    for v, (trunc, allr) in C1_VARIANTS.items():
        TP[v] = walk_rank(R, WCOLS, TUNE_YEARS, trunc, allr)
        log('tuned', v)
    E = R.loc[TP['R20e'].index]
    E = E.sort_values(['mi', 'work_id'])
    scores = {'v0': E.Wlgbm_D.values, **{v: TP[v].loc[E.index].values for v in C1_VARIANTS}}
    ev, tabs = eval_early_sets(E, scores)
    res['tuning_2019_2023'] = {k: early_summary(t) for k, t in tabs.items()}
    tuned = {v: res['tuning_2019_2023'][v]['p20_rise'] for v in C1_VARIANTS}
    chosen = max(C1_VARIANTS, key=lambda v: (tuned[v], -list(C1_VARIANTS).index(v)))
    gain = tuned[chosen] - res['tuning_2019_2023']['v0']['p20_rise']
    res['choice'] = dict(chosen=chosen, tuning_p20_rise=tuned[chosen], v0_tuning_p20_rise=res['tuning_2019_2023']['v0']['p20_rise'],
                         gain=float(gain), adopted=bool(gain > 0), rule='highest mean precision@20 of rises over the 52 months of 2019-2023; adopted if above v0 on the same rows')
    log('choice', res['choice'])
    # ------------------------------------------------ one run on 2024-2026
    trunc, allr = C1_VARIANTS[chosen]
    TQ = walk_rank(R, WCOLS, TEST_YEARS, trunc, allr)
    Eq = R.loc[TQ.index].sort_values(['mi', 'work_id'])
    sc = {'v0': Eq.Wlgbm_D.values, 'v1': TQ.loc[Eq.index].values}
    ev, tabs = eval_early_sets(Eq, sc)
    BD = make_BD(len(ev.M.months))
    res['test_2024_2026'] = dict(chosen=chosen, adopted=res['choice']['adopted'], months=int(len(ev.M.months)),
                                 v0=early_summary(tabs['v0']), v1=early_summary(tabs['v1']))
    res['test_2024_2026']['paired_v1_minus_v0'] = paired_early(tabs, 'v1', 'v0', BD)
    res['test_2024_2026']['months_v1_above_v0'] = float((tabs['v1'].p20_rise.values > tabs['v0'].p20_rise.values).mean())
    ci_each = {}
    for name in ('v0', 'v1'):
        ci_each[name] = {k: ci_mean(tabs[name][k].values, BD) for k in EARLY_KEYS}
    res['test_2024_2026']['intervals'] = ci_each
    mj = tabs['v1'].index.isin(MAYJUN)
    res['may_june_2025'] = dict(months=[int(m) for m in tabs['v1'].index[mj]],
                                v0=early_summary(tabs['v0'][mj]) if mj.any() else None, v1=early_summary(tabs['v1'][mj]) if mj.any() else None)
    ex = ~mj
    res['excluding_may_june_2025'] = dict(v0=early_summary(tabs['v0'][ex]), v1=early_summary(tabs['v1'][ex]),
                                          paired_v1_minus_v0={k: float((tabs['v1'][k][ex] - tabs['v0'][k][ex]).mean()) for k in EARLY_KEYS})
    res['by_year_2024_2026'] = {int(y): dict(v0=early_summary(tabs['v0'][(tabs['v0'].index + 1) // 12 == y]),
                                              v1=early_summary(tabs['v1'][(tabs['v1'].index + 1) // 12 == y])) for y in TEST_YEARS}
    # ------------------------------------------------ placebo of the chosen variant
    donor, info = donor_map()
    P = placebo_frame(R, donor, info)
    assert (P.work_id.values == R.work_id.values).all() and (P.mi.values == R.mi.values).all()
    P['elig'] = R.elig.values
    PQ = []
    for Y in TEST_YEARS:
        tr, te = train_rows(P, Y), test_rows(P, Y)
        te = te[te.elig]
        trn = tr if allr else tr[tr.elig]
        m = fit_rank(trn, WCOLS, trn.rel.where(trn.elig, 0), trunc)
        PQ.append(pd.Series(m.predict(te[WCOLS]), index=te.index))
        log('placebo ranker year', Y)
    PQ = pd.concat(PQ)
    Pe = P.loc[PQ.index].copy()
    Pe['score'] = PQ.values
    # placebo of v0 W_lgbm: the stored placebo predictions of 11_placebo_a.py (pW_D) on the same rows
    pl = pd.read_parquet(IN / 'placebo_a_preds.parquet', columns=['work_id', 'mi', 'pW_D'])
    Pe = Pe.merge(pl, on=['work_id', 'mi'], how='left')
    assert Pe.pW_D.notna().all()
    evp = EarlyEval(Pe)
    tp = {'placebo_v0_W': evp.month_table(Pe.pW_D.values), 'placebo_v1': evp.month_table(Pe.score.values)}
    res['placebo'] = dict(v0_placebo=early_summary(tp['placebo_v0_W']), v1_placebo=early_summary(tp['placebo_v1']),
                          paired_v1_minus_v0_placebo=paired_early(tp, 'placebo_v1', 'placebo_v0_W', BD), donors=len(donor),
                          note='each book is given the Wikipedia features of a similar-traffic book (donor map of 11_placebo_a.py); both should be near the eligible base rate')
    # ------------------------------------------------ save predictions
    keep = ['work_id', 'mi', 'year', 'D', 'Sg', 'rose', 'rel', 'Wlgbm_D']
    parts = []
    for v in C1_VARIANTS:
        parts.append(R.loc[TP[v].index, keep].assign(phase='tuning', variant=v, score=TP[v].values))
    parts.append(R.loc[TQ.index, keep].assign(phase='test', variant=chosen, score=TQ.values))
    pd.concat(parts, ignore_index=True).to_parquet(OUT / 'improve_v2_c1_preds.parquet', index=False)
    res['runtime_s'] = round(time.time() - T0)
    res['peak_memory_gb'] = round(mem_gb(), 2)
    jdump(res, REP / 'wiki_led_improve_v2_c1.json')


# ====================================================================== stage c4: count loss, gate, intervals
def mean_rank(table, higher_better):
    """table: {candidate: {metric: value}}; rank 1 = best per metric; returns {candidate: mean rank}."""
    cands = list(table)
    ranks = {c: [] for c in cands}
    for m, hb in higher_better.items():
        vals = np.array([table[c][m] for c in cands])
        order = rankdata(-vals if hb else vals, method='min')
        for c, r in zip(cands, order):
            ranks[c].append(float(r))
    return {c: float(np.mean(v)) for c, v in ranks.items()}


C4_METRICS = {'MAE_loans': False, 'MAE_log': False, 'spearman_level': True}


def tuning_summary(S, yhat):
    """The three tuning metrics of change 4 on rows S (all rows of the tuning years): pooled MAE in loans and in ln(1+loans), mean Spearman."""
    le = LevelEval(S)
    t = le.month_table(yhat)
    return dict(MAE_loans=float(t.ae.sum() / t.n.sum()), MAE_log=float(t.ael.sum() / t.n.sum()), spearman_level=float(t.spearman_level.mean()),
                WAPE=float(t.ae.sum() / t.act.sum()), top10_hit=float(t.hit.sum() / t.k.sum()), change_rank=float(t.change_rank.mean()),
                alert20_all=float(t.alert20_all.mean()), within2=float(t.w2.sum() / t.n.sum()), months=int(len(t)))


def gate_design(df, pH, pW, cuts):
    h, w = pH.loc[df.index].values, pW.loc[df.index].values
    s1 = df.short_hist.values.astype(float)
    s2 = df.burst_any.values.astype(float)
    s3 = ((df.h_m6.values >= cuts[0]) & (df.h_m6.values < cuts[1])).astype(float)
    s4 = (df.h_m6.values >= cuts[1]).astype(float)
    cols = [h, w]
    for s in (s1, s2, s3, s4):
        cols += [h * s, w * s]
    return np.column_stack(cols)


def gate_predictions(S, pH, pW, years):
    """Gate predictions (log scale) for the test years, each fitted on the out-of-sample predictions of the 3 years before (as many as exist).
    The first year with no earlier predictions uses equal weights. S: scored rows; pH, pW: Series aligned to S.index covering all years used."""
    out, info = [], {}
    for Y in years:
        te = S[S.year == Y]
        prev = [y for y in range(Y - 3, Y) if y >= SCORE0 // 12]
        if not prev:
            out.append(pd.Series(((pH.loc[te.index] + pW.loc[te.index]) / 2).values, index=te.index))
            info[Y] = 'equal weights (no earlier predictions)'
            continue
        tr = S[S.year.isin(prev)]
        cuts = np.quantile(tr.h_m6.values, [1 / 3, 2 / 3])
        Xtr, Xte = gate_design(tr, pH, pW, cuts), gate_design(te, pH, pW, cuts)
        sc = StandardScaler().fit(Xtr)
        m = Ridge(alpha=1.0).fit(sc.transform(Xtr), tr.Y.values)
        out.append(pd.Series(m.predict(sc.transform(Xte)), index=te.index))
        info[Y] = f'ridge on years {prev}'
    return pd.concat(out), info


def conformal(S, yhat, years, level=0.8):
    """Split-conformal 80% intervals on the log scale: for test year Y the 10th and 90th percentiles of the signed errors of the previous
    year's out-of-sample predictions of the same model. Returns a frame with lo, hi (loans) and the log errors' quantiles per year."""
    lo, hi, q = [], [], {}
    a = (1 - level) / 2
    for Y in years:
        cal = S[S.year == Y - 1]
        if len(cal) == 0 or yhat.loc[cal.index].isna().any():
            continue
        e = cal.Y.values - yhat.loc[cal.index].values
        q10, q90 = np.quantile(e, [a, 1 - a])
        te = S[S.year == Y]
        p = yhat.loc[te.index].values
        lo.append(pd.Series(np.expm1(p + q10).clip(min=0), index=te.index))
        hi.append(pd.Series(np.expm1(p + q90).clip(min=0), index=te.index))
        q[Y] = (float(q10), float(q90))
    return pd.concat(lo), pd.concat(hi), q


def coverage_table(S, lo, hi, groups):
    """Coverage and median width (loans) by test year, overall and for subgroups."""
    out = {}
    Sx = S.loc[lo.index]
    cov = ((Sx.L_next.values >= lo.values - 1e-9) & (Sx.L_next.values <= hi.values + 1e-9))
    width = (hi - lo).values
    df = pd.DataFrame({'year': Sx.year.values, 'cov': cov, 'w': width, **{g: Sx[g].values for g in groups}})
    for g in ['all'] + list(groups):
        d = df if g == 'all' else df[df[g]]
        by = d.groupby('year').agg(coverage=('cov', 'mean'), median_width=('w', 'median'), rows=('cov', 'size'))
        out[g] = {int(y): dict(coverage=float(r.coverage), median_width=float(r.median_width), rows=int(r.rows)) for y, r in by.iterrows()}
    return out


def stage_c4():
    R = load()
    res = dict(stage='c4', sample=SAMPLE)
    S = R[R.scored].copy()
    Stune = S[S.year.isin(TUNE_YEARS)]
    # ------------------------------------------------ count loss: tuning
    fams = {'H': HCOLS, 'HW': HCOLS + WCOLS}
    v0col = {'H': 'Hlgbm_Y', 'HW': 'HWlgbm_Y'}
    T = {}
    for fam, cols in fams.items():
        for pw in (1.2, 1.5):
            T[(fam, pw)] = walk_reg(R, cols, 'L_next', TUNE_YEARS, params=dict(tweedie_variance_power=pw), objective='tweedie', trans=np.log1p)
            log('tuned tweedie', fam, pw)
    res['tuning_2019_2023'] = {}
    chosen = {}
    for fam in fams:
        table = {'v0': tuning_summary(Stune, Stune[v0col[fam]].values)}
        for pw in (1.2, 1.5):
            table[f'tweedie_{pw}'] = tuning_summary(Stune, T[(fam, pw)].loc[Stune.index].values)
        mr = mean_rank({c: {m: table[c][m] for m in C4_METRICS} for c in table}, C4_METRICS)
        best = min(table, key=lambda c: (mr[c], list(table).index(c)))
        if ARGS.dev_force:
            assert SAMPLE < 1
            best = 'tweedie_1.5'
        chosen[fam] = best
        res['tuning_2019_2023'][fam] = dict(candidates=table, mean_rank=mr, chosen=best, rule='lowest mean rank over MAE in loans, MAE in ln(1+loans), within-month Spearman; ties go to v0 then 1.2')
        log('count-loss choice', fam, best, mr)
    # ------------------------------------------------ gate: tuning on 2020-2023 (2019 shown)
    def chosen_series(fam):
        c = chosen[fam]
        return S[v0col[fam]] if c == 'v0' else T[(fam, float(c.split('_')[1]))]

    pH_t = chosen_series('H')
    pHW_t = chosen_series('HW')
    pW_t = S['Wlgbm_Y']
    gate_t, ginfo = gate_predictions(Stune, pH_t.reindex(Stune.index), pW_t.reindex(Stune.index), TUNE_YEARS)
    eq_t = (pH_t.reindex(Stune.index) + pW_t.reindex(Stune.index)) / 2
    hw_t = pHW_t.reindex(Stune.index)
    cands = {'HW': hw_t, 'equal_weights': eq_t, 'gate': gate_t.reindex(Stune.index)}
    yr = Stune.year.values
    res['gate_tuning'] = {}
    for label, mask in (('2020_2023', yr >= 2020), ('2019_2023', yr >= 2019)):
        Sm = Stune[mask]
        tab = {c: tuning_summary(Sm, v.loc[Sm.index].values) for c, v in cands.items()}
        mr = mean_rank({c: {m: tab[c][m] for m in C4_METRICS} for c in tab}, C4_METRICS)
        res['gate_tuning'][label] = dict(candidates=tab, mean_rank=mr)
    mr = res['gate_tuning']['2020_2023']['mean_rank']
    gbest = min(cands, key=lambda c: (mr[c], list(cands).index(c)))
    if ARGS.dev_force:
        assert SAMPLE < 1
        gbest = 'gate'
    res['gate_tuning']['chosen'] = gbest
    res['gate_tuning']['adopted'] = bool(gbest == 'gate')
    res['gate_tuning']['rule'] = 'lowest mean rank over the three metrics among HW (chosen count loss), equal weights, gate, on 2020-2023; a tie goes to the one listed first'
    res['gate_tuning']['gate_fit_notes'] = {int(k): v for k, v in ginfo.items()}
    log('gate choice', gbest, mr)
    # ------------------------------------------------ one run on 2024-2026
    Q = {}
    for fam, cols in fams.items():
        c = chosen[fam]
        if c == 'v0':
            Q[fam] = S[v0col[fam]].loc[S.year.isin(TEST_YEARS)]
        else:
            pw = float(c.split('_')[1])
            Q[fam] = walk_reg(R, cols, 'L_next', TEST_YEARS, params=dict(tweedie_variance_power=pw), objective='tweedie', trans=np.log1p)
            log('test fit', fam, c)
    pH_all = S['Hlgbm_Y'] if chosen['H'] == 'v0' else pd.concat([pH_t, Q['H']]).reindex(S.index)
    pHW_all = S['HWlgbm_Y'] if chosen['HW'] == 'v0' else pd.concat([pHW_t, Q['HW']]).reindex(S.index)
    pW_all = S['Wlgbm_Y']
    gate_all, ginfo2 = gate_predictions(S, pH_all, pW_all, TUNE_YEARS + TEST_YEARS)
    eq_all = (pH_all + pW_all) / 2
    Stest = S[S.year.isin(TEST_YEARS)]
    models = {'v0_H': S['Hlgbm_Y'], 'v0_HW': S['HWlgbm_Y'], 'v1_H': pH_all, 'v1_HW': pHW_all, 'equal_weights': eq_all, 'gate': gate_all.reindex(S.index)}
    v1_level = 'gate' if res['gate_tuning']['adopted'] else 'v1_HW'
    models['v1'] = models[v1_level]
    res['test_2024_2026'] = dict(v1_is=v1_level, count_loss_chosen=chosen, gate_adopted=res['gate_tuning']['adopted'],
                                 gate_fit_notes={int(k): v for k, v in ginfo2.items() if k >= 2024})
    le = LevelEval(Stest)
    BD = make_BD(len(le.M.months))
    tabs = {k: le.month_table(v.loc[Stest.index].values) for k, v in models.items()}
    res['test_2024_2026']['months'] = int(len(le.M.months))
    res['test_2024_2026']['metrics'] = {}
    for k, t in tabs.items():
        d = {m: ci_pooled(t, a, b, BD) for m, (a, b) in POOLED.items()}
        d.update({m: ci_mean(t[m].values, BD) for m in MEANED})
        d['median_err_loans'] = float(np.median(np.abs(np.expm1(models[k].loc[Stest.index].values).clip(min=0) - Stest.L_next.values)))
        res['test_2024_2026']['metrics'][k] = d
    ref = 'v0_HW'
    res['test_2024_2026']['paired_vs_v0_HW'] = {}
    for k in tabs:
        if k == ref:
            continue
        d = {m: ci_paired_pooled(tabs[k], tabs[ref], a, b, BD) for m, (a, b) in POOLED.items()}
        d.update({m: ci_paired_mean(tabs[k][m].values, tabs[ref][m].values, BD) for m in MEANED})
        res['test_2024_2026']['paired_vs_v0_HW'][k] = d
    # subgroups and May-June 2025
    res['subgroups_2024_2026'] = {}
    for g in ('burst_any', 'short_hist'):
        Sg_ = Stest[Stest[g]]
        leg = LevelEval(Sg_)
        t = {k: leg.month_table(v.loc[Sg_.index].values) for k, v in models.items() if k in ('v0_HW', 'v1', 'gate', 'v1_HW')}
        res['subgroups_2024_2026'][g] = dict(rows=int(len(Sg_)), share=float(len(Sg_) / len(Stest)),
                                             metrics={k: level_summary(tt) for k, tt in t.items()})
    mj = Stest.mi.isin(MAYJUN)
    res['may_june_2025'] = {}
    if mj.any():
        Sm = Stest[mj]
        lem = LevelEval(Sm)
        res['may_june_2025'] = {k: level_summary(lem.month_table(v.loc[Sm.index].values)) for k, v in models.items() if k in ('v0_HW', 'v1', 'gate', 'v1_HW')}
        res['may_june_2025']['months'] = [int(m) for m in lem.M.months]
    Sx = Stest[~mj]
    lex = LevelEval(Sx)
    res['excluding_may_june_2025'] = {k: level_summary(lex.month_table(v.loc[Sx.index].values)) for k, v in models.items() if k in ('v0_HW', 'v1', 'gate', 'v1_HW')}
    # ------------------------------------------------ split-conformal 80% intervals
    res['intervals'] = {}
    for k in ('v0_HW', 'v1_HW', 'gate'):
        lo, hi, q = conformal(S, models[k], TUNE_YEARS + TEST_YEARS)
        if k == 'gate':                                     # the gate's 2019 predictions are the equal-weight fallback: start in 2021
            lo, hi = lo[S.loc[lo.index].year >= 2021], hi[S.loc[hi.index].year >= 2021]
        res['intervals'][k] = dict(quantiles_ln=q, coverage=coverage_table(S, lo, hi, ['burst_any', 'short_hist']),
                                   overall_2020_2023=None, overall_2024_2026=None)
        yy = S.year.reindex(lo.index).values
        for lab, ys in (('overall_2020_2023', range(2020, 2024)), ('overall_2024_2026', TEST_YEARS)):
            sel = np.isin(yy, list(ys))
            if sel.any():
                idx = lo.index[sel]
                Sx2 = S.loc[idx]
                cov = (Sx2.L_next.values >= lo.loc[idx].values - 1e-9) & (Sx2.L_next.values <= hi.loc[idx].values + 1e-9)
                res['intervals'][k][lab] = dict(coverage=float(cov.mean()), median_width=float(np.median((hi.loc[idx] - lo.loc[idx]).values)))
    # ------------------------------------------------ save
    pr = S[['work_id', 'mi', 'year', 'Y', 'L_next']].copy()
    for k, v in models.items():
        pr[k] = v.reindex(S.index).values
    pr.to_parquet(OUT / 'improve_v2_c4_preds.parquet', index=False)
    res['runtime_s'] = round(time.time() - T0)
    res['peak_memory_gb'] = round(mem_gb(), 2)
    jdump(res, REP / 'wiki_led_improve_v2_c4.json')



# ====================================================================== generic stage for new Wikipedia features (changes 2 and 5)
class ChangeEval:
    """Change-ranking measures for predictions of D on rows sorted by month: Spearman with D and the top-20 hit rate (share that rose)."""

    def __init__(self, S, min_rows=2):
        self.S = S
        self.min_rows = min_rows
        self.M = Months(S.mi.values)
        self.rose = S.rose.values.astype(float)
        D_ = S.D.values.astype('float64')
        self.Rd = []
        for s in self.M.sl:
            r = rankdata(D_[s])
            self.Rd.append(r - r.mean())

    def month_table(self, dhat):
        dhat = np.asarray(dhat, dtype='float64')
        rows = []
        for k, (mi, s) in enumerate(zip(self.M.months, self.M.sl)):
            n = s.stop - s.start
            if n < max(self.min_rows, 20):
                rows.append((mi, np.nan, np.nan, n))
                continue
            sc = dhat[s]
            order = np.lexsort((np.arange(n), -sc))[:20]
            rows.append((mi, spearman_rank(sc, self.Rd[k]), self.rose[s][order].mean(), n))
        return pd.DataFrame(rows, columns=['mi', 'change_rank', 'alert20_all', 'n']).set_index('mi')


LEVEL_POOLED_COLS = ['n', 'ae', 'act', 'ael', 'w2', 'hit', 'k']


def reidx(t, months):
    """Put a month table on the full list of months (months without rows: pooled counts 0, other measures missing)."""
    t = t.reindex(months)
    for c in LEVEL_POOLED_COLS:
        if c in t.columns:
            t[c] = t[c].fillna(0)
    return t


def paired_block(tabs, a, b, keys, BD):
    out = {}
    for k in keys:
        d = ci_paired_mean(tabs[a][k].values, tabs[b][k].values, BD)
        x = tabs[a][k].values - tabs[b][k].values
        d['share_months_positive'] = float(np.mean(x[~np.isnan(x)] > 0)) if (~np.isnan(x)).any() else float('nan')
        out[k] = d
    return out


def bundle(Sx, Dm, Ym, Rm, months, BD, min_rows, pairs):
    """All measures of one row set Sx (rows sorted by month) for named predictions.
    Dm: {name: predicted change D for every row of Sx}; Ym: {name: predicted ln(1 + L(t+1))}; Rm: {name: ranker score for the eligible rows of Sx}.
    pairs: list of (kind, name_a, name_b) with kind 'D' (change measures and early list of the D model), 'R' (early list of rankers: names
    of Rm, or 'W:'+name of Dm) or 'Y'. Intervals: 3-month blocks (BD) over the months of the full test list; months with too few rows are skipped."""
    out = dict(rows=int(len(Sx)), eligible_rows=int(Sx.elig.sum()))
    pos = np.searchsorted(months, Sx.mi.values)
    ce = ChangeEval(Sx, min_rows)
    tD = {k: reidx(ce.month_table(v), months) for k, v in Dm.items()}
    E = Sx[Sx.elig]
    em = Sx.elig.values
    ee = EarlyEval(E, min_rows)
    tE = {'W:' + k: reidx(ee.month_table(np.asarray(v)[em]), months) for k, v in Dm.items()}
    tE.update({'R:' + k: reidx(ee.month_table(v), months) for k, v in Rm.items()})
    out['change'], out['early'], out['level'] = {}, {}, {}
    yr_of = (np.asarray(months) + 1) // 12
    out['early_by_year'] = {int(y): {k: float(np.nanmean(t.p20_rise.values[yr_of == y])) if np.isfinite(t.p20_rise.values[yr_of == y]).any() else float('nan')
                                     for k, t in tE.items()} for y in sorted(set(yr_of))}
    apd = {}
    for k, v in Dm.items():
        r = dict(change_rank=ci_mean(tD[k].change_rank.values, BD), alert20_all=ci_mean(tD[k].alert20_all.values, BD))
        if Sx.Sg.sum() > 0:
            ci, d = ap_ratio(Sx.Sg.values, np.asarray(v, dtype='float64'), pos, BD)
            r['surge_ap_ratio'] = ci
            apd[k] = d
        out['change'][k] = r
    for k, t in tE.items():
        r = {m: ci_mean(t[m].values, BD) for m in EARLY_KEYS}
        r['summary'] = early_summary(t.dropna(subset=['p20_rise']))
        out['early'][k] = r
    if Ym:
        le = LevelEval(Sx, min_rows)
        tY = {k: reidx(le.month_table(v), months) for k, v in Ym.items()}
        for k, t in tY.items():
            r = {m: ci_pooled(t, a, b, BD) for m, (a, b) in POOLED.items() if m in ('MAE_loans', 'MAE_log', 'WAPE')}
            r['spearman_level'] = ci_mean(t.spearman_level.values, BD)
            out['level'][k] = r
    out['paired'] = {}
    for kind, a, b in pairs:
        key = f'{kind}:{a}-{b}'
        if kind == 'D':
            d = {'change_rank': ci_paired_mean(tD[a].change_rank.values, tD[b].change_rank.values, BD),
                 'alert20_all': ci_paired_mean(tD[a].alert20_all.values, tD[b].alert20_all.values, BD)}
            if a in apd and b in apd:
                dd = apd[a] - apd[b]
                d['surge_ap_ratio'] = dict(diff=float(out['change'][a]['surge_ap_ratio']['value'] - out['change'][b]['surge_ap_ratio']['value']),
                                           lo=float(np.nanpercentile(dd, 2.5)), hi=float(np.nanpercentile(dd, 97.5)))
            out['paired'][key] = d
        elif kind == 'R':
            out['paired'][key] = paired_block(tE, a, b, EARLY_KEYS, BD)
        elif kind == 'Y':
            d = {'spearman_level': ci_paired_mean(tY[a].spearman_level.values, tY[b].spearman_level.values, BD)}
            d.update({m: ci_paired_pooled(tY[a], tY[b], x, y, BD) for m, (x, y) in POOLED.items() if m in ('MAE_loans', 'MAE_log', 'WAPE')})
            out['paired'][key] = d
    return out


def point_summary(Sx, Dm, Ym, Rm):
    """Point values only (no intervals) of the same measures on a small row set (May to June 2025)."""
    out = dict(rows=int(len(Sx)), months=[int(m) for m in np.unique(Sx.mi.values)], change={}, early={}, level={})
    ce = ChangeEval(Sx)
    for k, v in Dm.items():
        t = ce.month_table(v)
        r = dict(change_rank=float(t.change_rank.mean()), alert20_all=float(t.alert20_all.mean()))
        r['surge_ap_ratio'] = ap_ratio(Sx.Sg.values, np.asarray(v, dtype='float64')) if Sx.Sg.sum() > 0 else None
        out['change'][k] = r
    E = Sx[Sx.elig]
    ee = EarlyEval(E)
    em = Sx.elig.values
    for k, v in Dm.items():
        out['early']['W:' + k] = early_summary(ee.month_table(np.asarray(v)[em]))
    for k, v in Rm.items():
        out['early']['R:' + k] = early_summary(ee.month_table(v))
    if Ym:
        le = LevelEval(Sx)
        for k, v in Ym.items():
            out['level'][k] = level_summary(le.month_table(v))
    return out


def variant_stage(tag, R, variants, subgroup, placebo_frame_fn, label, placebo_mode='donor'):
    """Generic stage: baseline v0 = Test A's W_lgbm (and the change-1 ranker) on the 18 Test A features; each variant adds columns.
    Tuning on 2019-2023 chooses one W variant (by the mean within-month Spearman of D) and one ranker variant (by precision@20 of rises on
    eligible rows); both are then run once on 2024-2026 beside v0 on the same rows; the placebo reruns them with another book's pages."""
    c1 = json.loads((REP / 'wiki_led_improve_v2_c1.json').read_text())
    rk_name = c1['choice']['chosen']
    trunc, allr = C1_VARIANTS[rk_name]
    res = dict(stage=tag, label=label, sample=SAMPLE, ranker_config=dict(variant=rk_name, truncation=trunc, all_rows=allr, adopted_in_c1=c1['choice']['adopted']),
               variants={k: v for k, v in variants.items()})
    S = R[R.scored]
    Stune = S[S.year.isin(TUNE_YEARS)]
    allcols = sorted({c for v in variants.values() for c in v})
    res['missing_share_scored_rows'] = {c: float(S[c].isna().mean()) for c in allcols}
    # ---------------- tuning
    pD, pY, pR = {}, {}, {}
    pR['base'] = walk_rank(R, WCOLS, TUNE_YEARS, trunc, allr)
    for v, cols in variants.items():
        feats = WCOLS + cols
        pD[v] = walk_reg(R, feats, 'D', TUNE_YEARS)
        pY[v] = walk_reg(R, feats, 'Y', TUNE_YEARS)
        pR[v] = walk_rank(R, feats, TUNE_YEARS, trunc, allr)
        log('tuned', tag, v)
    ce = ChangeEval(Stune)
    le = LevelEval(Stune)
    E = Stune[Stune.elig]
    ee = EarlyEval(E)
    em = Stune.elig.values
    tune = {}
    names = ['v0'] + list(variants)
    for k in names:
        dhat = Stune.Wlgbm_D.values if k == 'v0' else pD[k].loc[Stune.index].values
        yhat = Stune.Wlgbm_Y.values if k == 'v0' else pY[k].loc[Stune.index].values
        tc = ce.month_table(dhat)
        te_ = ee.month_table(dhat[em])
        tl = le.month_table(yhat)
        d = dict(change_rank=float(tc.change_rank.mean()), alert20_all=float(tc.alert20_all.mean()),
                 surge_ap_ratio=ap_ratio(Stune.Sg.values, dhat),
                 early_w=early_summary(te_), level=dict(spearman_level=float(tl.spearman_level.mean()),
                                                      MAE_log=float(tl.ael.sum() / tl.n.sum()), MAE_loans=float(tl.ae.sum() / tl.n.sum())))
        if subgroup:
            for sg_name, col in subgroup.items():
                m_ = Stune[col].values
                Sg_ = Stune[m_]
                tcs = ChangeEval(Sg_, 40).month_table(dhat[m_])
                Eg = Sg_[Sg_.elig]
                tes = EarlyEval(Eg, 40).month_table(dhat[m_][Sg_.elig.values])
                d[f'sub_{sg_name}'] = dict(rows=int(len(Sg_)), change_rank=float(tcs.change_rank.mean()),
                                           early_p20_rise=float(tes.p20_rise.mean()), early_months=int(tes.p20_rise.notna().sum()))
        tune[k] = d
    tune['ranker_base'] = dict(early=early_summary(ee.month_table(pR['base'].loc[E.index].values)))
    for v in variants:
        tune['ranker_' + v] = dict(early=early_summary(ee.month_table(pR[v].loc[E.index].values)))
        if subgroup:
            for sg_name, col in subgroup.items():
                Eg = E[E[col].values]
                tes = EarlyEval(Eg, 40).month_table(pR[v].loc[Eg.index].values)
                tune['ranker_' + v][f'sub_{sg_name}'] = dict(rows=int(len(Eg)), early_p20_rise=float(tes.p20_rise.mean()))
    res['tuning_2019_2023'] = tune
    order = list(variants)
    wv = max(order, key=lambda v: (tune[v]['change_rank'], -order.index(v)))
    rv = max(order, key=lambda v: (tune['ranker_' + v]['early']['p20_rise'], -order.index(v)))
    res['choice'] = dict(
        W=dict(chosen=wv, tuning_change_rank=tune[wv]['change_rank'], v0_change_rank=tune['v0']['change_rank'],
               gain=tune[wv]['change_rank'] - tune['v0']['change_rank'], adopted=bool(tune[wv]['change_rank'] > tune['v0']['change_rank'])),
        ranker=dict(chosen=rv, tuning_p20_rise=tune['ranker_' + rv]['early']['p20_rise'], base_p20_rise=tune['ranker_base']['early']['p20_rise'],
                    gain=tune['ranker_' + rv]['early']['p20_rise'] - tune['ranker_base']['early']['p20_rise'],
                    adopted=bool(tune['ranker_' + rv]['early']['p20_rise'] > tune['ranker_base']['early']['p20_rise'])),
        rule='W variant: highest mean within-month Spearman of D over 2019-2023; ranker variant: highest mean precision@20 of rises on eligible rows; adopted if above the same model without the new features')
    log('choice', res['choice'])
    # ---------------- one run on 2024-2026
    Stest = S[S.year.isin(TEST_YEARS)]
    months = np.sort(Stest.mi.unique())
    BD = make_BD(len(months))
    tD_ = walk_reg(R, WCOLS + variants[wv], 'D', TEST_YEARS)
    tY_ = walk_reg(R, WCOLS + variants[wv], 'Y', TEST_YEARS)
    tR_ = walk_rank(R, WCOLS + variants[rv], TEST_YEARS, trunc, allr)
    tR0 = walk_rank(R, WCOLS, TEST_YEARS, trunc, allr)
    ix = Stest.index
    Dm = {'v0': Stest.Wlgbm_D.values, 'v2': tD_.loc[ix].values}
    Ym = {'v0': Stest.Wlgbm_Y.values, 'v2': tY_.loc[ix].values}
    eix = Stest.index[Stest.elig.values]
    Rm = {'ranker_c1': tR0.loc[eix].values, 'ranker_v2': tR_.loc[eix].values}
    pairs = [('D', 'v2', 'v0'), ('Y', 'v2', 'v0'), ('R', 'W:v2', 'W:v0'), ('R', 'R:ranker_v2', 'R:ranker_c1'), ('R', 'R:ranker_v2', 'W:v0'),
             ('R', 'R:ranker_c1', 'W:v0')]
    res['test_2024_2026'] = dict(W_variant=wv, ranker_variant=rv, adopted_W=res['choice']['W']['adopted'], adopted_ranker=res['choice']['ranker']['adopted'],
                                 months=int(len(months)), all_rows=bundle(Stest, Dm, Ym, Rm, months, BD, 2, pairs))
    if subgroup:
        res['test_2024_2026']['subgroups'] = {}
        for sg_name, col in subgroup.items():
            m_ = Stest[col].values
            Sg_ = Stest[m_]
            Dg = {k: v[m_] for k, v in Dm.items()}
            Yg = {k: v[m_] for k, v in Ym.items()}
            eg = Sg_.elig.values
            gx = Sg_.index[eg]
            Rg = {'ranker_c1': tR0.loc[gx].values, 'ranker_v2': tR_.loc[gx].values}
            res['test_2024_2026']['subgroups'][sg_name] = bundle(Sg_, Dg, Yg, Rg, months, BD, 40, pairs)
    mj = Stest.mi.isin(MAYJUN).values
    if mj.any():
        Sm = Stest[mj]
        gx = Sm.index[Sm.elig.values]
        res['may_june_2025'] = point_summary(Sm, {k: v[mj] for k, v in Dm.items()}, {k: v[mj] for k, v in Ym.items()},
                                             {'ranker_c1': tR0.loc[gx].values, 'ranker_v2': tR_.loc[gx].values})
    Sx = Stest[~mj]
    gx = Sx.index[Sx.elig.values]
    res['excluding_may_june_2025'] = point_summary(Sx, {k: v[~mj] for k, v in Dm.items()}, {k: v[~mj] for k, v in Ym.items()},
                                                   {'ranker_c1': tR0.loc[gx].values, 'ranker_v2': tR_.loc[gx].values})
    # ---------------- placebo
    # donor mode: every Wikipedia feature of a book is replaced by that of a similar-traffic book (placebo of v0 = the stored pW_D);
    # shift mode: only the new columns are moved 12 months later and the baseline is the real v0 and the real ranker of change 1.
    P = placebo_frame_fn(R, variants[wv], variants[rv])
    assert (P.work_id.values == R.work_id.values).all() and (P.mi.values == R.mi.values).all()
    P['elig'] = R.elig.values
    pl_D = walk_reg(P, WCOLS + variants[wv], 'D', TEST_YEARS)
    pl_Y = walk_reg(P, WCOLS + variants[wv], 'Y', TEST_YEARS)
    pl_R = walk_rank(P, WCOLS + variants[rv], TEST_YEARS, trunc, allr)
    Pt = P.loc[Stest.index]
    pgx = Pt.index[Pt.elig.values]
    if placebo_mode == 'donor':
        pl_R0 = walk_rank(P, WCOLS, TEST_YEARS, trunc, allr)
        pla = pd.read_parquet(IN / 'placebo_a_preds.parquet', columns=['work_id', 'mi', 'pW_D', 'pW_Y']).set_index(['work_id', 'mi'])
        key = pd.MultiIndex.from_arrays([Stest.work_id.values, Stest.mi.values])
        pl0, pl0Y = pla.pW_D.reindex(key).values, pla.pW_Y.reindex(key).values
        assert not np.isnan(pl0).any() and not np.isnan(pl0Y).any()
        rk0_series = pl_R0
        rk0 = pl_R0.loc[pgx].values
        note = 'placebo features of another book (donor map of 11_placebo_a.py) for every feature of the variant; the gain over placebo v0 should vanish'
    else:
        pl0, pl0Y = Stest.Wlgbm_D.values, Stest.Wlgbm_Y.values
        rk0_series = tR0
        rk0 = tR0.loc[pgx].values
        note = 'the new columns moved 12 months later (value at origin t taken from origin t - 12) with the Test A features left as they are; the gain over the real v0 should vanish'
    Dm_p = {'placebo_v0': pl0, 'placebo_v2': pl_D.loc[Pt.index].values}
    Ym_p = {'placebo_v0': pl0Y, 'placebo_v2': pl_Y.loc[Pt.index].values}
    Rm_p = {'placebo_ranker_c1': rk0, 'placebo_ranker_v2': pl_R.loc[pgx].values}
    pairs_p = [('D', 'placebo_v2', 'placebo_v0'), ('Y', 'placebo_v2', 'placebo_v0'), ('R', 'W:placebo_v2', 'W:placebo_v0'), ('R', 'R:placebo_ranker_v2', 'R:placebo_ranker_c1')]
    res['placebo'] = bundle(Pt, Dm_p, Ym_p, Rm_p, months, BD, 2, pairs_p)
    res['placebo']['note'] = note
    res['placebo']['mode'] = placebo_mode
    if subgroup:                                   # the same placebo on the rows of the subgroup (flags from the real data)
        res['placebo']['subgroups'] = {}
        for sg_name, col in subgroup.items():
            m_ = Stest[col].values
            Sg_ = Pt[m_]
            gx_ = Sg_.index[Sg_.elig.values]
            Rg_ = {'placebo_ranker_c1': rk0_series.loc[gx_].values, 'placebo_ranker_v2': pl_R.loc[gx_].values}
            res['placebo']['subgroups'][sg_name] = bundle(Sg_, {k: v[m_] for k, v in Dm_p.items()}, {k: v[m_] for k, v in Ym_p.items()}, Rg_, months, BD, 40, pairs_p)
    # ---------------- save
    parts = [R.loc[pD[v].index, ['work_id', 'mi', 'year', 'D']].assign(phase='tuning', model='W_D_' + v, score=pD[v].values) for v in variants]
    parts.append(R.loc[tD_.index, ['work_id', 'mi', 'year', 'D']].assign(phase='test', model='W_D_' + wv, score=tD_.values))
    parts.append(R.loc[tY_.index, ['work_id', 'mi', 'year', 'D']].assign(phase='test', model='W_Y_' + wv, score=tY_.values))
    parts.append(R.loc[tR_.index, ['work_id', 'mi', 'year', 'D']].assign(phase='test', model='R_' + rv, score=tR_.values))
    pd.concat(parts, ignore_index=True).to_parquet(OUT / f'improve_v2_{tag}_preds.parquet', index=False)
    res['runtime_s'] = round(time.time() - T0)
    res['peak_memory_gb'] = round(mem_gb(), 2)
    jdump(res, REP / f'wiki_led_improve_v2_{tag}.json')


# ====================================================================== stage c2: burst-shape features
DAILY7 = ['pk28', 'dpk', 'pre7', 'dec', 'hi28', 'rec', 'top500']


def merge_burst(R, B):
    for kind, key, pre, cols in (('book', 'article', 'b_', DAILY7 + ['corr28', 'co', 'same_name', 'other_r4']), ('author', 'author_article', 'a_', DAILY7)):
        use = [c for c in cols if c in B.columns]
        x = B[B.kind == kind][['article', 'mi'] + use].rename(columns={'article': key, **{c: pre + c for c in use}})
        R = R.merge(x, on=[key, 'mi'], how='left')
    return R.sort_values(['mi', 'work_id']).reset_index(drop=True)


def c2_setup():
    """Frame with the burst columns merged, the variants and notes (shared by stage c2 and the importance stage)."""
    B = pd.read_parquet(IN / 'burst_features.parquet')
    R = merge_burst(load(), B)
    v1 = ['b_' + c for c in DAILY7] + ['a_' + c for c in DAILY7] + ['b_corr28', 'b_co']
    v2 = [p + '_' + c for c in ('pk28', 'pre7', 'hi28', 'rec') for p in ('b', 'a')] + ['b_co']
    variants = {'B1_all': v1, 'B2_reduced': v2}
    notes = {}
    if 'same_name' in B.columns and 'other_r4' in B.columns:
        bk = B[B.kind == 'book']
        complete = bool(bk.same_name.notna().all())
        notes['B3'] = f'same_name and other_r4 present; complete for every book article: {complete}'
        if complete:
            variants['B3_same_name'] = v1 + ['b_same_name', 'b_other_r4']
    else:
        notes['B3'] = 'not run: same_name and other_r4 are not in burst_features.parquet (they need the Wikimedia REST API)'
    return R, B, variants, notes


def stage_c2():
    path = IN / 'burst_features.parquet'
    if not path.exists():
        jdump(dict(stage='c2', status='not run: data/db/wiki_led/burst_features.parquet does not exist'), REP / 'wiki_led_improve_v2_c2.json')
        return
    R, B, variants, notes = c2_setup()
    log('variants', {k: len(v) for k, v in variants.items()}, notes)
    donor, info = donor_map()
    burst_tab = B

    def pf(Rx, wcols, rcols):
        cols_b = sorted({c[2:] for c in wcols + rcols if c.startswith('b_')})
        cols_a = sorted({c[2:] for c in wcols + rcols if c.startswith('a_')})
        return placebo_frame(Rx, donor, info, extra_tables=[(burst_tab, 'book', cols_b), (burst_tab, 'author', cols_a)])

    variant_stage('c2', R, variants, {'burst_book': 'burst_book'}, pf, 'burst-shape and noise features (change 2)')
    f = REP / 'wiki_led_improve_v2_c2.json'
    r = json.loads(f.read_text())
    r['notes'] = notes
    jdump(r, f)


# ====================================================================== stage c5: dated events and adaptation views
def build_event_columns(R, EV, EL, PG, AD):
    """Merge the event columns onto R. EV: events.parquet; EL: events_long.parquet; PG: adaptation_page_features (has_data per page and origin) or None;
    AD: adaptation_features.parquet or None. Returns (R, notes)."""
    notes = {}
    ev = EV[['work_id', 'mi', 'died', 'award', 'ad_rel', 'months_since_event']].copy()
    ev['ad_rel'] = ev.ad_rel.astype(float)
    if PG is not None and EL is not None:
        a = EL[(EL.event == 'adaptation') & EL.type_group.isin(['film', 'tv']) & EL.mi_event.notna()].copy()
        a['page'] = a.en_title.astype(str).str.replace(' ', '_')
        rows = [a[['subject', 'page']].assign(mi=(a.mi_event.astype(int) + k)) for k in (-1, 0, 1)]
        X = pd.concat(rows, ignore_index=True)                       # origin months t in which this adaptation is released within t-1..t+1
        has = PG[['article', 'mi', 'has_data']].rename(columns={'article': 'page'})
        X = X.merge(has, on=['page', 'mi'], how='left')
        pub = X[X.has_data == True][['subject', 'mi']].drop_duplicates()
        pub['public'] = 1.0
        item = EV[['work_id', 'item']].drop_duplicates('work_id')
        ev = ev.merge(item, on='work_id', how='left').merge(pub.rename(columns={'subject': 'item'}), on=['item', 'mi'], how='left').drop(columns='item')
        ev['public'] = ev.public.fillna(0.0)
        if 'ad_rel_public' in EV.columns and EV.ad_rel_public.notna().any():       # a column filled by another job: compare, but use the one computed here
            other = EV[['work_id', 'mi', 'ad_rel', 'ad_rel_public']].merge(ev[['work_id', 'mi', 'public']], on=['work_id', 'mi'])
            on = other[other.ad_rel > 0]
            notes['ad_rel_public_in_file'] = f"agrees with the one computed here in {float(((on.ad_rel_public > 0).astype(float) == on.public).mean()):.4f} of the {len(on):,} work-months with a release in t-1..t+1"
        n_raw = int(ev.ad_rel.sum())
        ev['ad_rel'] = ev.ad_rel * ev.public
        notes['ad_rel'] = f"ad_rel requires that the adaptation article already had views before the end of t: {n_raw:,} work-months with a release in t-1..t+1 become {int(ev.ad_rel.sum()):,}"
        ev = ev.drop(columns='public')
    else:
        notes['ad_rel'] = 'ad_rel uses the release date only (the adaptation-page views were not available, so the public check could not be made)'
    ev = ev.rename(columns={'died': 'e_died', 'award': 'e_award', 'ad_rel': 'e_ad_rel', 'months_since_event': 'e_since'})
    R = R.merge(ev, on=['work_id', 'mi'], how='left')
    if AD is not None:
        R = R.merge(AD[['work_id', 'mi', 'ad_lvl4', 'ad_r4', 'ad_rmax']], on=['work_id', 'mi'], how='left')
    # rows within 2 months of an event: an event month e of the book or its author (death, dated award, film or tv release) with t-2 <= e <= t+2
    near = pd.DataFrame(columns=['work_id', 'mi'])
    if EL is not None:
        L2 = EL[EL.mi_event.notna() & ((EL.event != 'adaptation') | EL.type_group.isin(['film', 'tv']))][['subject', 'mi_event']]
        W2 = EV[['work_id', 'item', 'author_item']].drop_duplicates('work_id')
        pairs = pd.concat([W2[['work_id', 'item']].rename(columns={'item': 'subject'}), W2[['work_id', 'author_item']].rename(columns={'author_item': 'subject'})]).dropna()
        pe = pairs.merge(L2, on='subject')[['work_id', 'mi_event']].drop_duplicates()
        near = pd.concat([pe.assign(mi=pe.mi_event.astype(int) + k) for k in range(-2, 3)])[['work_id', 'mi']].drop_duplicates()
    near['near_event'] = True
    R = R.merge(near, on=['work_id', 'mi'], how='left')
    R['near_event'] = R.near_event.fillna(False).astype(bool)
    notes['near_event_share_of_rows'] = float(R.near_event.mean())
    return R.sort_values(['mi', 'work_id']).reset_index(drop=True), notes


def shift_columns(R, cols, k=12):
    """Value of each column at origin t taken from origin t - k of the same work (the placebo: events moved k months later)."""
    x = R[['work_id', 'mi'] + cols].copy()
    x['mi'] = x['mi'] + k
    P = R.drop(columns=cols).merge(x, on=['work_id', 'mi'], how='left')
    return P.sort_values(['mi', 'work_id']).reset_index(drop=True)


def c5_setup():
    """Frame with the event and adaptation columns merged, the variants and notes (shared by stage c5 and the importance stage)."""
    EV = pd.read_parquet(IN / 'events.parquet')
    el_path, pg_path, ad_path = IN / 'events_long.parquet', IN / 'adaptation_page_features.parquet', IN / 'adaptation_features.parquet'
    EL = pd.read_parquet(el_path) if el_path.exists() else None
    have_views = pg_path.exists() and ad_path.exists()
    PG = pd.read_parquet(pg_path) if have_views else None
    AD = pd.read_parquet(ad_path) if have_views else None
    R, notes = build_event_columns(load(), EV, EL, PG, AD)
    flags = ['e_died', 'e_award', 'e_ad_rel', 'e_since']
    variants = {'E1_flags': flags}
    if have_views:
        variants['E2_flags_views'] = flags + ['ad_lvl4', 'ad_r4', 'ad_rmax']
    else:
        notes['E2'] = 'not run: the adaptation-page views (adaptation_features.parquet) were not complete'
    sc = R.loc[R.scored]
    notes['rows_with_flag'] = {c: int((sc[c] > 0).sum()) for c in ('e_died', 'e_award', 'e_ad_rel')}
    return R, variants, notes


def stage_c5():
    if not (IN / 'events.parquet').exists():
        jdump(dict(stage='c5', status='not run: data/db/wiki_led/events.parquet does not exist'), REP / 'wiki_led_improve_v2_c5.json')
        return
    R, variants, notes = c5_setup()
    log('variants', {k: len(v) for k, v in variants.items()}, notes)

    def pf(Rx, wcols, rcols):
        return shift_columns(Rx, sorted(set(c for c in wcols + rcols)), 12)

    variant_stage('c5', R, variants, {'event': 'near_event'}, pf, 'dated events and adaptation views (change 5)', placebo_mode='shift')
    f = REP / 'wiki_led_improve_v2_c5.json'
    r = json.loads(f.read_text())
    r['notes'] = notes
    jdump(r, f)


# ====================================================================== descriptive: which columns the chosen models use
def stage_importance(tag):
    """Gain importance (share of the total) of the columns in the models chosen in stage `tag`, fitted for test year 2026 (training rows with
    target months before 1 January 2026). Descriptive only: not part of any choice."""
    r = json.loads((REP / f'wiki_led_improve_v2_{tag}.json').read_text())
    if tag == 'c2':
        R, _, variants, _ = c2_setup()
    else:
        R, variants, _ = c5_setup()
    wv, rv = r['choice']['W']['chosen'], r['choice']['ranker']['chosen']
    trunc, allr = r['ranker_config']['truncation'], r['ranker_config']['all_rows']
    tr = train_rows(R, 2026)
    out = dict(stage=tag + '_importance', note='gain importance, share of total, models fitted for test year 2026; descriptive only')
    m = fit_reg(tr, WCOLS + variants[wv], tr.D)
    g = pd.Series(m.booster_.feature_importance('gain'), index=WCOLS + variants[wv])
    out['W_model_change'] = {k: float(v) for k, v in (g / g.sum()).sort_values(ascending=False).items()}
    trn = tr if allr else tr[tr.elig]
    mr = fit_rank(trn, WCOLS + variants[rv], trn.rel.where(trn.elig, 0), trunc)
    g = pd.Series(mr.booster_.feature_importance('gain'), index=WCOLS + variants[rv])
    out['ranker'] = {k: float(v) for k, v in (g / g.sum()).sort_values(ascending=False).items()}
    out['new_columns_share'] = dict(W_model=float(sum(out['W_model_change'][c] for c in variants[wv])), ranker=float(sum(out['ranker'][c] for c in variants[rv])))
    jdump(out, REP / f'wiki_led_improve_v2_{tag}_importance.json')


# ====================================================================== descriptive: does the ranker result depend on the LightGBM seed?
def stage_seed_check(tag):
    """Refit the ranker(s) of stage `tag` for 2024-2026 with four other seeds (rows and columns are subsampled by LightGBM) and give the
    precision@20 of rises on the eligible rows. c1: the change-1 ranker against v0; c2 and c5: the ranker with and without the new columns.
    Descriptive only: nothing is chosen or changed by it."""
    c1 = json.loads((REP / 'wiki_led_improve_v2_c1.json').read_text())
    trunc, allr = C1_VARIANTS[c1['choice']['chosen']]
    if tag == 'c1':
        R = load()
        extra = None
    else:
        r = json.loads((REP / f'wiki_led_improve_v2_{tag}.json').read_text())
        if tag == 'c2':
            R, _, variants, _ = c2_setup()
        else:
            R, variants, _ = c5_setup()
        extra = variants[r['choice']['ranker']['chosen']]
    S = R[R.scored]
    Stest = S[S.year.isin(TEST_YEARS)]
    E = Stest[Stest.elig].sort_values(['mi', 'work_id'])
    ee = EarlyEval(E)
    out = dict(stage=tag + '_seed_check', note='descriptive: precision@20 of rises on the eligible rows of 2024-2026 for different LightGBM seeds', seeds={})
    v0 = ee.month_table(E.Wlgbm_D.values).p20_rise.mean()
    out['v0_W_lgbm_p20_rise'] = float(v0)
    for seed in (SEED, 1, 2, 3, 4):
        LGB_SEED[0] = seed
        a = walk_rank(R, WCOLS, TEST_YEARS, trunc, allr).loc[E.index].values
        d = dict(ranker_without_new_columns=float(ee.month_table(a).p20_rise.mean()))
        if extra:
            b = walk_rank(R, WCOLS + extra, TEST_YEARS, trunc, allr).loc[E.index].values
            d['ranker_with_new_columns'] = float(ee.month_table(b).p20_rise.mean())
            d['difference'] = d['ranker_with_new_columns'] - d['ranker_without_new_columns']
        else:
            d['difference_from_v0'] = d['ranker_without_new_columns'] - float(v0)
        out['seeds'][str(seed)] = d
        log('seed', seed, d)
    LGB_SEED[0] = SEED
    key = 'difference' if extra else 'difference_from_v0'
    vals = np.array([v[key] for v in out['seeds'].values()])
    out['summary'] = dict(key=key, mean=float(vals.mean()), min=float(vals.min()), max=float(vals.max()))
    jdump(out, REP / f'wiki_led_improve_v2_{tag}_seed_check.json')


# ====================================================================== descriptive: what does adding columns with no information do?
def stage_noise_check(tag, seeds=(SEED, 1, 2)):
    """Refit the Wikipedia model of the change and the ranker for 2024-2026 with columns of random numbers in place of the new columns of
    stage `tag` (same number of columns), for three LightGBM seeds, and compare each with the same model without extra columns and the same seed.
    This shows how much the change ranking and precision@20 move when columns with no information are added (LightGBM subsamples
    columns and rows, so any change of the column set changes the trees). Descriptive only."""
    c1 = json.loads((REP / 'wiki_led_improve_v2_c1.json').read_text())
    trunc, allr = C1_VARIANTS[c1['choice']['chosen']]
    r = json.loads((REP / f'wiki_led_improve_v2_{tag}.json').read_text())
    if tag == 'c2':
        R, _, variants, _ = c2_setup()
    else:
        R, variants, _ = c5_setup()
    wv, rv = r['choice']['W']['chosen'], r['choice']['ranker']['chosen']
    n_w, n_r = len(variants[wv]), len(variants[rv])
    rng = np.random.default_rng(777)
    names = [f'noise{i}' for i in range(max(n_w, n_r))]
    for c in names:
        R[c] = rng.standard_normal(len(R))
    S = R[R.scored]
    Stest = S[S.year.isin(TEST_YEARS)]
    ce = ChangeEval(Stest)
    E = Stest[Stest.elig].sort_values(['mi', 'work_id'])
    ee = EarlyEval(E)
    em = Stest.elig.values
    out = dict(stage=tag + '_noise_check', n_noise_columns=dict(W_model=n_w, ranker=n_r), seeds={},
               note='descriptive: random columns added in place of the new columns; same seed for the model with and without them')
    for seed in seeds:
        LGB_SEED[0] = seed
        d0 = walk_reg(R, WCOLS, 'D', TEST_YEARS).loc[Stest.index].values
        d1 = walk_reg(R, WCOLS + names[:n_w], 'D', TEST_YEARS).loc[Stest.index].values
        r0 = walk_rank(R, WCOLS, TEST_YEARS, trunc, allr).loc[E.index].values
        r1 = walk_rank(R, WCOLS + names[:n_r], TEST_YEARS, trunc, allr).loc[E.index].values
        row = dict(change_rank_without=float(ce.month_table(d0).change_rank.mean()), change_rank_with_noise=float(ce.month_table(d1).change_rank.mean()),
                   early_p20_W_without=float(ee.month_table(d0[em]).p20_rise.mean()),
                   early_p20_W_with_noise=float(ee.month_table(d1[em]).p20_rise.mean()),
                   ranker_p20_without=float(ee.month_table(r0).p20_rise.mean()), ranker_p20_with_noise=float(ee.month_table(r1).p20_rise.mean()))
        row['change_rank_diff'] = row['change_rank_with_noise'] - row['change_rank_without']
        row['early_p20_W_diff'] = row['early_p20_W_with_noise'] - row['early_p20_W_without']
        row['ranker_p20_diff'] = row['ranker_p20_with_noise'] - row['ranker_p20_without']
        out['seeds'][str(seed)] = row
        log('noise check seed', seed, row)
    LGB_SEED[0] = SEED
    for k in ('change_rank_diff', 'early_p20_W_diff', 'ranker_p20_diff'):
        v = np.array([x[k] for x in out['seeds'].values()])
        out[k] = dict(mean=float(v.mean()), min=float(v.min()), max=float(v.max()))
    jdump(out, REP / f'wiki_led_improve_v2_{tag}_noise_check.json')


STAGES = {'c1': stage_c1, 'c4': stage_c4, 'c2': stage_c2, 'c5': stage_c5,
          'imp_c2': lambda: stage_importance('c2'), 'imp_c5': lambda: stage_importance('c5'),
          'seed_c1': lambda: stage_seed_check('c1'), 'seed_c2': lambda: stage_seed_check('c2'), 'seed_c5': lambda: stage_seed_check('c5'),
          'noise_c2': lambda: stage_noise_check('c2'), 'noise_c5': lambda: stage_noise_check('c5')}

if __name__ == '__main__':
    STAGES[ARGS.stage]()
