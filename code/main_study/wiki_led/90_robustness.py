# 90. Checks R1 to R7 of addendum e: how much do the Wikipedia-led results depend on one choice?
# Settings: prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json, section robustness_checks (read-only; SHA-256 in prereg/README.md).
# These are descriptive checks of results already reported. Nothing is tuned and no setting is chosen from them; every number goes to a file.
# Run from code/ with ../.venv/bin/python, or from handoff/ with:  bash jobs/bg.sh wl_rob_PART main_study/wiki_led/90_robustness.py PART
#   PART b          Test B: R3 (by test year) and R5 (library model with catalogue information: L+ and L+W)   -> db/wiki_led/robustness_part_b.json
#   PART d          Test D: R1 (rose thresholds) and R7 (list sizes), original and (when it exists) corrected predictions -> robustness_part_d.json
#   PART a          Test A, corrected files, stored predictions: R1, R3, R4, R6, R7                          -> robustness_part_a.json
#   PART a_orig     the same on the ORIGINAL Test A files; used only to check this code against the numbers already reported -> robustness_part_a_orig.json
#   PART a_seeds    Test A, corrected rows, W, H and HW refitted with 5 seeds: R2                             -> robustness_part_a_seeds.json
# Then 91_robustness_report.py merges the parts into data/reports/wiki_led_robustness.json and wiki_led_robustness.md.
# Rules used everywhere (from the Test A, Test B and Test D scripts): walk-forward predictions are read, never refitted, except in R2 and R5;
# 95% intervals from 2,000 draws (seed 20261020): blocks of 3 consecutive months for Test A, author clusters for Test B, exact binomial for Test D list slots.
# 'Rose' means ln(1 + L(t+1)) - ln(1 + M6) >= ln(1 + threshold), compared exactly (not in single-precision floating point) and with equality counted.
# Lists: the k books with the highest predicted change in each month (Test D: in each format and month); ties are broken by a fixed random order (seed 20261020).
# Review of 20 Oct 2026 (about 21:20 +07; prereg/DEVIATIONS.md, Wikipedia-led tests): part b adds L+0 and Lq to R5 (catalogue features from the records first
# lent in the work's first month, see catalogue_month0) because the features as fixed use records of all years; part d reads each variant's own rows file
# (test_d_rows_c.parquet for the corrected predictions) and adds the base rate averaged over lists; part a adds the month-by-month top-20 places.
# ROB_TAG=_test writes the part files under another name (code tests only).
import sys, os, json, time, pathlib, hashlib, resource
import numpy as np, pandas as pd
from scipy.stats import rankdata, beta
from sklearn.metrics import average_precision_score
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
ADD = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_e_corrections_robustness.json'
ADD_SHA = '36f3605286b51b8123d791c1d59a7dc89356ec3bb66bfba6b9667327d31b3e52'
assert hashlib.sha256(ADD.read_bytes()).hexdigest() == ADD_SHA, 'addendum e changed'
CHECKS = json.loads(ADD.read_text())['robustness_checks']
OUT, REP = D / 'db' / 'wiki_led', D / 'reports'
SEED = 20261020
SEEDS = [20261020 + i for i in range(5)]
NB = int(os.environ.get('ROB_NB', 2000))          # 2,000 draws; a smaller number only for code tests (ROB_NB=50)
T0 = time.time()
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)
THR = [('25%', 0.25), ('50%', 0.5), ('100%', 1.0)]
FLAGS = ['rose25', 'rose50', 'rose100', 'surged']
KS = (10, 20, 50, 100)
BOT_MONTHS = [2025 * 12 + 3, 2025 * 12 + 4, 2025 * 12 + 5]      # origin months 2025-04 to 2025-06 (month index = year * 12 + month - 1)
SCORE0 = 2019 * 12
os.nice(10)


def peak_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9      # bytes on macOS


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s [peak {peak_gb():.2f} GB]', *a, flush=True)


def clean(o):
    """numpy values to plain Python; NaN and infinity to None, so the file is valid JSON."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return clean(o.tolist())
    return o


TAG = os.environ.get('ROB_TAG', '')               # code tests only: ROB_TAG=_test writes robustness_part_NAME_test.json instead


def save_part(name, obj):
    f = OUT / f'robustness_part_{name}{TAG}.json'
    f.write_text(json.dumps(clean(obj), indent=1))
    log('wrote', f.name)


# ====================================================================== shared tools
def block_draws(n, block=3, nb=None):
    """Circular blocks of 3 consecutive months, as 10_test_a.py (a fresh generator at the seed, so the draws repeat for a given n)."""
    nb = nb or NB
    rng = np.random.default_rng(SEED)
    k = int(np.ceil(n / block))
    starts = np.arange(n)
    out = np.empty((nb, n), dtype=np.int64)
    for t in range(nb):
        s = rng.choice(starts, k)
        out[t] = np.concatenate([np.arange(a, a + block) % n for a in s])[:n]
    return out


def ci_mean(x, BD):
    """Mean of x and its 95% interval over the month-block draws BD (NaN months skipped). With fewer than 6 months there is no interval."""
    x = np.asarray(x, dtype=np.float64)
    if BD.shape[1] < 6:
        return dict(mean=float(np.nanmean(x)), lo=None, hi=None)
    b = np.nanmean(x[BD], axis=1)
    return dict(mean=float(np.nanmean(x)), lo=float(np.percentile(b, 2.5)), hi=float(np.percentile(b, 97.5)))


def cp(k, n):
    """Exact (Clopper-Pearson) 95% interval for k hits in n list slots."""
    lo = beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return float(lo), float(hi)


def rose_matrix(L_next, M6, Sg):
    """Columns: rose at 25%, 50% and 100% above M6, and surged. Exact comparison, equality counted."""
    L_next = np.asarray(L_next, dtype=np.float64)
    M6 = np.asarray(M6, dtype=np.float64)
    cols = [(1.0 + L_next) >= (1.0 + t) * (1.0 + M6) - 1e-9 for _, t in THR]
    cols.append(np.asarray(Sg) == 1)
    return np.stack(cols, axis=1)


def ap_ratio(score, y, mid=None, BD=None, M=None):
    """Average precision of `score` for the 0/1 vector y divided by the base rate (pooled rows).
    With BD (draws x months, positions 0..M-1) and mid (month position of each row) it returns that ratio for every month-block draw,
    using month weights: the same value as average_precision_score on the concatenated resample (ties are one threshold)."""
    order = np.argsort(-score, kind='stable')
    s, yo = score[order], y[order].astype(np.float64)
    n = len(s)
    last = np.r_[np.flatnonzero(s[1:] != s[:-1]), n - 1]              # last row of each group of tied scores
    if BD is None:
        ctp, cw = np.cumsum(yo), np.arange(1, n + 1, dtype=np.float64)
        tp, w = ctp[last], cw[last]
        return float((np.diff(np.r_[0.0, tp]) * (tp / w)).sum() / tp[-1] / (tp[-1] / w[-1]))
    mo = mid[order]
    out = np.empty(len(BD))
    for t in range(len(BD)):
        wt = np.bincount(BD[t], minlength=M).astype(np.float64)[mo]
        cw, ctp = np.cumsum(wt), np.cumsum(wt * yo)
        tp, w = ctp[last], cw[last]
        prec = np.divide(tp, w, out=np.zeros_like(tp), where=w > 0)
        out[t] = (np.diff(np.r_[0.0, tp]) * prec).sum() / tp[-1] / (tp[-1] / w[-1])
    return out


class Panel:
    """Rows sorted by list group (a month, or a format and a month), the group boundaries, a fixed random tie-break and the 0/1 flags."""

    def __init__(self, df, group_cols, models):
        df = df.sort_values(group_cols + ['work_id'], kind='stable').reset_index(drop=True)
        g = df.groupby(group_cols, sort=True).ngroup().to_numpy()
        self.starts = np.flatnonzero(np.r_[True, g[1:] != g[:-1]])
        self.ends = np.r_[self.starts[1:], len(df)]
        self.sizes = self.ends - self.starts
        self.models = list(models)
        self.score = {m: df[m].to_numpy(dtype=np.float64) for m in models}
        self.Dv = df['D'].to_numpy(dtype=np.float64)
        self.flags = rose_matrix(df['L_next'], df['M6'], df['Sg'])
        self.tb = np.random.default_rng(SEED).random(len(df))
        self.gmi = df['mi'].to_numpy()[self.starts]
        self.gyear = df['year'].to_numpy()[self.starts]
        self.df = df
        counts = np.add.reduceat(self.flags.astype(np.int64), self.starts, axis=0)
        self.base_g = counts / self.sizes[:, None]               # base rate of each flag in each group

    def top(self, model, a, b, k):
        s = self.score[model][a:b]
        return np.lexsort((self.tb[a:b], -s))[:k]

    def hits(self, model, ks=KS):
        """(groups x list sizes x flags): how many of the top k of each group carry each flag."""
        out = np.zeros((len(self.starts), len(ks), self.flags.shape[1]), dtype=np.int64)
        kmax = max(ks)
        assert self.sizes.min() >= kmax, 'a group has fewer rows than the longest list'
        for i, (a, b) in enumerate(zip(self.starts, self.ends)):
            cs = np.cumsum(self.flags[a:b][self.top(model, a, b, kmax)], axis=0)
            for j, k in enumerate(ks):
                out[i, j] = cs[k - 1]
        return out

    def spearman(self, model):
        """Spearman correlation of the prediction with the actual change D inside each group (0 when the prediction is constant)."""
        out = np.zeros(len(self.starts))
        for i, (a, b) in enumerate(zip(self.starts, self.ends)):
            x = self.score[model][a:b]
            if x.min() != x.max():
                out[i] = np.corrcoef(rankdata(x), rankdata(self.Dv[a:b]))[0, 1]
        return out


# ====================================================================== PART d: Test D (R1 and R7)
FMT_CODE = {'print': 0, 'ebook': 1, 'audiobook': 2}
FMT_NAME = {v: k for k, v in FMT_CODE.items()}


def d_rows(fn):
    rows = pd.read_parquet(OUT / fn, columns=['work_id', 'format', 'mi', 'L_next', 'M6'])
    rows['fmt'] = rows.format.astype(str).map(FMT_CODE).astype('int8')
    return rows.drop(columns='format')


def part_d():
    res = {}
    # each variant reads L_next and M6 from its own rows file (review, 20 Oct 2026: the corrected predictions come from test_d_rows_c.parquet)
    for label, fn, rows_fn in (('original', 'test_d_preds.parquet', 'test_d_rows.parquet'), ('corrected', 'test_d_preds_c.parquet', 'test_d_rows_c.parquet')):
        f = OUT / fn
        if not f.exists():
            log('Test D', label, 'predictions not found:', fn)
            res[label] = None
            continue
        rows = d_rows(rows_fn)
        rows_check = None
        if label == 'corrected':                     # the correction changes only Wikipedia features: loans must equal the original rows
            r0 = d_rows('test_d_rows.parquet')
            m = rows.merge(r0, on=['work_id', 'fmt', 'mi'], how='outer', suffixes=('', '_orig'), indicator=True)
            both = m['_merge'] == 'both'
            rows_check = dict(rows=int(len(rows)), rows_original=int(len(r0)), only_here=int((m['_merge'] == 'left_only').sum()),
                              only_original=int((m['_merge'] == 'right_only').sum()),
                              max_abs_diff_L_next=float((m.L_next[both] - m.L_next_orig[both]).abs().max()),
                              max_abs_diff_M6=float((m.M6[both] - m.M6_orig[both]).abs().max()))
            log('Test D corrected rows against the original rows:', rows_check)
            del r0, m
        P = pd.read_parquet(f, columns=['work_id', 'format', 'mi', 'year', 'D', 'Sg', 'rose', 'W', 'H', 'HW', 'naive'])
        P['fmt'] = P.format.astype(str).map(FMT_CODE).astype('int8')
        P = P.drop(columns='format').merge(rows, on=['work_id', 'fmt', 'mi'], how='left', validate='one_to_one')
        del rows
        assert P.L_next.notna().all() and P.M6.notna().all()
        models = ['W', 'H', 'HW', 'naive']
        pan = Panel(P, ['fmt', 'mi'], models)
        del P
        # the 50% flag must agree with the stored 'rose' column (up to a few rows on the boundary)
        stored = pan.df['rose'].to_numpy().astype(bool)
        n_diff = int((stored != pan.flags[:, 1]).sum())
        log('Test D', label, 'rows', len(pan.df), 'groups', len(pan.starts), 'rows where exact 50% flag differs from stored rose:', n_diff)
        gfmt = pan.df['fmt'].to_numpy()[pan.starts]
        H = {m: pan.hits(m) for m in models}
        log('Test D', label, 'lists done')
        out = {'rows': int(len(pan.df)), 'groups': int(len(pan.starts)), 'rows_exact50_differs_from_stored_rose': n_diff,
               'files': dict(preds=fn, rows=rows_fn), 'rows_check_against_original': rows_check, 'scopes': {}}
        for scope in ['all', 'print', 'ebook', 'audiobook']:
            for period in ['2019-2026', '2024-2026']:
                gm = np.ones(len(pan.starts), bool)
                if scope != 'all':
                    gm &= gfmt == FMT_CODE[scope]
                if period == '2024-2026':
                    gm &= pan.gyear >= 2024
                rm = np.repeat(gm, pan.sizes)
                base = {FLAGS[i]: float(pan.flags[rm, i].mean()) for i in range(4)}
                # added in review: the base rate averaged over the format-month lists (each list counts once, as in the hit rates)
                base_gm = {FLAGS[i]: float(pan.base_g[gm, i].mean()) for i in range(4)}
                ng = int(gm.sum())
                lists = {}
                for m in models:
                    lists[m] = {}
                    for j, k in enumerate(KS):
                        cell = {}
                        for i, fl in enumerate(FLAGS):
                            hits = int(H[m][gm, j, i].sum())
                            slots = ng * k
                            lo, hi = cp(hits, slots)
                            cell[fl] = dict(rate=hits / slots, lo=lo, hi=hi, hits=hits, slots=slots)
                        lists[m][f'top{k}'] = cell
                out['scopes'][f'{scope}|{period}'] = dict(rows=int(rm.sum()), list_groups=ng, base=base, base_group_mean=base_gm, lists=lists)
        res[label] = out
        del pan, H
    save_part('d', res)


# ====================================================================== PART a / a_orig: Test A from the stored predictions
A_MODELS = ['Wlgbm_D', 'Wrule_D', 'Hlgbm_D', 'HWlgbm_D', 'Hnaive_D', 'Wridge_D']
AP_MODELS = ['Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D', 'Hnaive_D']


def load_test_a(variant):
    rows_f, preds_f = (('test_a_rows_c.parquet', 'test_a_preds_c.parquet') if variant == 'corrected'
                       else ('test_a_rows.parquet', 'test_a_preds.parquet'))
    PR = pd.read_parquet(OUT / preds_f)
    RW = pd.read_parquet(OUT / rows_f, columns=['work_id', 'mi', 'L_next', 'M6'])
    PR = PR.drop(columns=[c for c in ['M6', 'L_next'] if c in PR.columns]).merge(RW, on=['work_id', 'mi'], how='left', validate='one_to_one')
    assert PR.L_next.notna().all()
    assert np.abs(np.log1p(PR.L_next.to_numpy(dtype=np.float64)) - PR.Y.to_numpy(dtype=np.float64)).max() < 1e-5
    return PR, preds_f, rows_f


AP_CI_MODELS = ['Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D']


def set_scores(pan, sp, hit, sel, with_ap_ci, models=A_MODELS):
    """Headline measures of Test A on the months selected by the boolean vector `sel` (month-block intervals inside the selection)."""
    idx = np.flatnonzero(sel)
    n = len(idx)
    BD = block_draws(n)
    if n < 6:                                            # blocks of 3 months cannot vary in so few months: no interval is given
        with_ap_ci = False
    rowsel = np.repeat(sel, pan.sizes)
    out = dict(n_months=int(n), n_rows=int(rowsel.sum()),
               base_rose50=float(pan.flags[rowsel, 1].mean()), base_surged=float(pan.flags[rowsel, 3].mean()),
               change_rank={}, paired={}, surge_ap={}, alert={})
    for m in models:
        d = ci_mean(sp[m][idx], BD)
        d['months_above_0'] = float((sp[m][idx] > 0).mean())
        out['change_rank'][m] = d
    out['paired']['HW_minus_H'] = ci_mean(sp['HWlgbm_D'][idx] - sp['Hlgbm_D'][idx], BD)
    out['paired']['W_minus_rule'] = ci_mean(sp['Wlgbm_D'][idx] - sp['Wrule_D'][idx], BD)
    y = pan.flags[rowsel, 3]
    mid = np.repeat(np.arange(n), pan.sizes[idx])
    for m in AP_MODELS:
        ap_all = ap_ratio(pan.score[m][rowsel], y)
        d = dict(ratio=ap_all, base=out['base_surged'])
        if with_ap_ci and m in AP_CI_MODELS:
            b = ap_ratio(pan.score[m][rowsel], y, mid=mid, BD=BD, M=n)
            d['ratio_lo'], d['ratio_hi'] = float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))
        out['surge_ap'][m] = d
    j20, j50 = KS.index(20), KS.index(50)
    for k, j in ((20, j20), (50, j50)):
        out['alert'][f'top{k}'] = {}
        for m in models:
            cell = {}
            for fl, i in (('rose50', 1), ('surged', 3)):
                share = hit[m][idx, j, i] / k
                cell[fl] = ci_mean(share, BD)
            cell['rose50']['months_beating_base'] = float((hit[m][idx, j, 1] / k > pan.base_g[idx, 1]).mean())
            out['alert'][f'top{k}'][m] = cell
    return out


def r6_block(pan, wiki, lib, k, flag_i):
    """Rises not in the library model's top k that Wikipedia's top k catches, month by month."""
    G = len(pan.starts)
    cols = ['N', 'rises', 'lib_catch', 'wiki_catch', 'union_catch', 'missed', 'caught', 'overlap', 'new_in_wiki', 'new_hits', 'outside_n', 'outside_rises']
    A = np.zeros((G, len(cols)))
    for g, (a, b) in enumerate(zip(pan.starts, pan.ends)):
        N = b - a
        rose = pan.flags[a:b, flag_i]
        inL = np.zeros(N, bool)
        inL[pan.top(lib, a, b, k)] = True
        inW = np.zeros(N, bool)
        inW[pan.top(wiki, a, b, k)] = True
        missed = rose & ~inL
        new = inW & ~inL
        A[g] = [N, rose.sum(), (rose & inL).sum(), (rose & inW).sum(), (rose & (inL | inW)).sum(), missed.sum(), (missed & inW).sum(),
                (inL & inW).sum(), new.sum(), (new & rose).sum(), (~inL).sum(), (rose & ~inL).sum()]
    return dict(zip(cols, A.T))


def r6_summary(r, k, BD):
    share = np.where(r['missed'] > 0, r['caught'] / np.maximum(r['missed'], 1), np.nan)
    rnd = k / r['N']                                           # a random list of k catches k/N of any set of books, in expectation
    lift = np.where(np.isfinite(share), share / rnd, np.nan)
    inc_prec = np.where(r['new_in_wiki'] > 0, r['new_hits'] / np.maximum(r['new_in_wiki'], 1), np.nan)
    base_out = r['outside_rises'] / r['outside_n']
    return dict(
        months=int(len(share)), mean_rises_per_month=float(r['rises'].mean()), mean_books_per_month=float(r['N'].mean()),
        library_catches_of_rises=ci_mean(r['lib_catch'] / np.maximum(r['rises'], 1), BD),
        wikipedia_catches_of_rises=ci_mean(r['wiki_catch'] / np.maximum(r['rises'], 1), BD),
        both_catch_of_rises=ci_mean(r['union_catch'] / np.maximum(r['rises'], 1), BD),
        mean_missed_rises_per_month=float(r['missed'].mean()),
        share_caught_by_wikipedia=ci_mean(share, BD),
        share_caught_pooled=float(r['caught'].sum() / r['missed'].sum()),
        share_random_list=ci_mean(rnd, BD),
        share_random_list_pooled_expected=float((r['missed'] * rnd).sum() / r['missed'].sum()),
        lift_over_random=ci_mean(lift, BD),
        months_wikipedia_beats_random=float(np.nanmean((share > rnd)[np.isfinite(share)])),
        mean_overlap_of_the_two_lists=float(r['overlap'].mean()),
        new_books_in_wikipedia_list_mean=float(r['new_in_wiki'].mean()),
        precision_of_new_books=ci_mean(inc_prec, BD),
        base_rate_outside_library_list=ci_mean(base_out, BD))


def part_a(variant):
    PR, preds_f, rows_f = load_test_a(variant)
    log('Test A', variant, 'predictions', preds_f, PR.shape, 'rows file', rows_f)
    pan = Panel(PR, ['mi'], A_MODELS)
    del PR
    G = len(pan.starts)
    months = pan.gmi
    log('months', G, 'rows', len(pan.df), 'list sizes ok (min month size', int(pan.sizes.min()), ')')
    sp = {m: pan.spearman(m) for m in A_MODELS}
    hit = {m: pan.hits(m) for m in A_MODELS}
    log('per-month Spearman and list hits done')
    res = dict(variant=variant, files=dict(preds=preds_f, rows=rows_f), n=dict(rows=int(len(pan.df)), months=int(G)))
    # ---- R1 and R7: the list tables (all scored months)
    BD = block_draws(G)
    base_rows = {fl: float(pan.flags[:, i].mean()) for i, fl in enumerate(FLAGS)}
    base_month = {fl: float(pan.base_g[:, i].mean()) for i, fl in enumerate(FLAGS)}
    lists = {}
    for m in A_MODELS:
        lists[m] = {}
        for j, k in enumerate(KS):
            cell = {}
            for i, fl in enumerate(FLAGS):
                share = hit[m][:, j, i] / k
                d = ci_mean(share, BD)
                d['months_beating_base'] = float((share > pan.base_g[:, i]).mean())
                cell[fl] = d
            lists[m][f'top{k}'] = cell
    res['lists'] = dict(base_pooled=base_rows, base_monthly_mean=base_month, models=lists)
    # added in review: places in each month's top 20 taken by a book that rose by 50% (to show the month-to-month spread behind R3)
    j20 = KS.index(20)
    res['per_month_top20_rose50'] = dict(origin_month=[f'{m // 12}-{m % 12 + 1:02d}' for m in months], test_year=[int(y) for y in pan.gyear],
                                         **{m: hit[m][:, j20, 1].tolist() for m in ('Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D')})
    log('R1 and R7 lists done')
    # ---- R3 (years), R4 (bot months)
    years = sorted(set(pan.gyear.tolist()))
    res['R3_years'] = {}
    for y in years:
        res['R3_years'][str(y)] = set_scores(pan, sp, hit, pan.gyear == y, with_ap_ci=False)
    log('R3 done')
    bot = np.isin(months, BOT_MONTHS)
    assert bot.sum() == 3, 'the three bot months must all be scored origins'
    res['R4_bot_months'] = dict(
        all_months=set_scores(pan, sp, hit, np.ones(G, bool), with_ap_ci=True),
        without_bot_months=set_scores(pan, sp, hit, ~bot, with_ap_ci=True),
        bot_months_only=set_scores(pan, sp, hit, bot, with_ap_ci=False))
    log('R4 done')
    # ---- R6
    res['R6_incremental'] = {}
    for libname, lib in (('library_trees', 'Hlgbm_D'), ('library_naive', 'Hnaive_D')):
        res['R6_incremental'][libname] = {}
        for k in (50, 20):
            for fl, i in (('rose50', 1), ('rose25', 0), ('rose100', 2)):
                r = r6_block(pan, 'Wlgbm_D', lib, k, i)
                res['R6_incremental'][libname][f'top{k}|{fl}'] = r6_summary(r, k, BD)
    log('R6 done')
    save_part('a' if variant == 'corrected' else 'a_orig', res)


# ====================================================================== PART a_seeds: R2
def part_a_seeds():
    R = pd.read_parquet(OUT / 'test_a_rows_c.parquet')
    stored = pd.read_parquet(OUT / 'test_a_preds_c.parquet', columns=['work_id', 'mi', 'Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D'])
    FE = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
    WCOLS = ['b_' + c for c in FE] + ['a_' + c for c in FE]
    HCOLS = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
    SETS = {'Wlgbm_D': WCOLS, 'Hlgbm_D': HCOLS, 'HWlgbm_D': HCOLS + WCOLS}
    scored = R[R.mi >= SCORE0].reset_index(drop=True)          # the file's own row order is kept (LightGBM's row sampling depends on it)
    assert len(scored) == len(stored), 'scored rows differ from the stored corrected predictions'
    part_f = OUT / f'robustness_part_a_seeds{TAG}.json'
    res = json.loads(part_f.read_text()) if part_f.exists() else {'seeds': {}}
    for seed in SEEDS:
        if str(seed) in res['seeds']:
            log('seed', seed, 'already done')
            continue
        P = scored[['work_id', 'mi', 'year', 'D', 'Sg', 'Y', 'L_next', 'M6']].copy()
        for name in SETS:
            P[name] = np.nan
        for Y in range(2019, 2027):
            sel = (scored.year == Y).to_numpy()
            if not sel.any():
                continue
            tr = R[(R.mi + 1) < Y * 12]
            te = scored[sel]
            for name, cols in SETS.items():
                m = lgb.LGBMRegressor(**{**LGB, 'random_state': seed}).fit(tr[cols], tr['D'])
                P.loc[sel, name] = m.predict(te[cols])
            log('seed', seed, 'year', Y, 'train', len(tr), 'test', int(sel.sum()))
        pan = Panel(P, ['mi'], list(SETS))
        G = len(pan.starts)
        sp = {m: pan.spearman(m) for m in SETS}
        hit = {m: pan.hits(m, ks=(20,)) for m in SETS}
        d = dict(change_rank={m: float(sp[m].mean()) for m in SETS},
                 top20_rose50={m: float((hit[m][:, 0, 1] / 20).mean()) for m in SETS},
                 top20_surged={m: float((hit[m][:, 0, 3] / 20).mean()) for m in SETS},
                 surge_ap_ratio={m: ap_ratio(pan.score[m], pan.flags[:, 3]) for m in SETS},
                 HW_minus_H_change_rank=float((sp['HWlgbm_D'] - sp['Hlgbm_D']).mean()), months=int(G))
        if seed == SEED:                                          # the first seed must reproduce the stored corrected predictions
            S = pan.df[['work_id', 'mi'] + list(SETS)].merge(stored, on=['work_id', 'mi'], suffixes=('', '_stored'), validate='one_to_one')
            d['max_abs_diff_to_stored'] = {m: float((S[m] - S[m + '_stored']).abs().max()) for m in SETS}
            log('seed', seed, 'refit vs stored corrected predictions, max abs difference', d['max_abs_diff_to_stored'])
        res['seeds'][str(seed)] = d
        res['runtime_s'] = round(time.time() - T0)
        res['peak_gb'] = round(peak_gb(), 2)
        part_f.write_text(json.dumps(clean(res), indent=1))
        log('seed', seed, 'done', d['change_rank'], d['top20_rose50'])
        del P, pan
    save_part('a_seeds', res)


# ====================================================================== PART b: Test B (R3 and R5)
def ym_add(ym, k):
    i = (ym // 100) * 12 + ym % 100 - 1 + k
    return (i // 12) * 100 + i % 12 + 1


def fix_cp850(s):
    """Copied unchanged from code/main_study/11_v3_work_table.py (the print headings were written in code page 850 and read as Latin-1)."""
    if s.isascii():
        return s
    out = []
    for ch in s:
        if ch.isascii():
            out.append(ch); continue
        try:
            b = ch.encode('cp1252')
        except UnicodeEncodeError:
            b = bytes([ord(ch)]) if ord(ch) < 256 else None
        out.append(b.decode('cp850') if b is not None and len(b) == 1 else ch)
    return ''.join(out)


def catalogue_month0(R):
    """R5, added in the review of 20 Oct 2026. The three catalogue features of addendum e come from records of all years: spl_works.parquet
    takes pub_year_min and creator_from_title_only over every record of the work, and work_theme.parquet weighs the subjects of every record by
    its loans over all months. A record enters the Seattle data only when it is first lent, so a record first lent after the work's first month
    was not visibly held when the work arrived, and its arrival can follow loans inside the six-month outcome window. Here the same three
    features are computed only from the records first lent in the work's first month (month 0): the level-1 (B-level) theme node with the highest
    strength, built as in 11_v3_work_table.py and 16_v3_assign.py from the OverDrive terms of digital records and the subject headings of print
    records, each record counting once (no loans used) and without Goodreads shelves; the smallest publication year of those records; and
    whether every one of those records lacks a creator. The replication is checked first: from all records with loans over all months as
    weights it must give work_theme.parquet's top node for works without Goodreads evidence."""
    TX = D / 'db' / 'taxonomy_v3'
    W0 = R[['work_id', 'first_ym']].drop_duplicates('work_id')
    RW = pd.read_parquet(TX / 'spl_record_work.parquet')
    RW = RW[RW.work_id.isin(W0.work_id)]
    recs = np.unique(RW.record_id.to_numpy())
    first, cko = [], []
    for f in ('book', 'ebook', 'audiobook'):
        x = pd.read_parquet(TX / f'spl_rows_{f}.parquet', columns=['record_id', 'year', 'month', 'checkouts'])
        x = x[np.isin(x.record_id.to_numpy(), recs)]
        ym = x.year.astype(np.int32) * 100 + x.month.astype(np.int32)
        first.append(ym.groupby(x.record_id).min())
        cko.append(x.checkouts.groupby(x.record_id).sum())
        del x, ym
    rfirst = pd.concat(first).groupby(level=0).min()
    rcko = pd.concat(cko).groupby(level=0).sum()
    SR = pd.read_parquet(TX / 'spl_records.parquet', columns=['record_id', 'format', 'creator_from_title', 'subjects', 'pub_year'])
    SR = SR[np.isin(SR.record_id.to_numpy(), recs)].copy()
    SR['format'] = SR.format.astype(str)
    SR = SR.merge(RW, on='record_id', how='left', validate='one_to_one').merge(W0, on='work_id', how='left', validate='many_to_one')
    SR['rec_first'] = SR.record_id.map(rfirst)
    SR['cko'] = SR.record_id.map(rcko).astype(float)
    SR['one'] = 1.0
    lag = ((SR.rec_first // 100) * 12 + SR.rec_first % 100) - ((SR.first_ym // 100) * 12 + SR.first_ym % 100)
    assert SR.rec_first.notna().all() and (lag.groupby(SR.work_id).min() == 0).all(), 'each work must have a record first lent in its first month'
    SR['m0'] = lag == 0
    SR['after5'] = lag > 5
    # theme evidence maps, as in 16_v3_assign.py
    P2 = pd.read_parquet(D / 'db' / 'taxonomy_v2' / 'phrases.parquet', columns=['source', 'raw', 'components_json'])
    spl_th = {r: th for r, c in zip(P2.raw[P2.source == 'spl'], P2.components_json[P2.source == 'spl'])
              if (th := [v for f, v in json.loads(c) if f == 'theme'])}
    HP = pd.read_parquet(TX / 'headings_parsed.parquet', columns=['heading_id', 'components_json'])
    hth = {h: th for h, cj in zip(HP.heading_id, HP.components_json)
           if (th := [(v, 1.0 if f == 'core_theme' else 0.5) for f, v in json.loads(cj) if f in ('core_theme', 'theme')])}
    HH = pd.read_parquet(TX / 'headings.parquet', columns=['heading', 'heading_id'])
    hid_of = dict(zip(HH.heading, HH.heading_id))
    VN = pd.read_parquet(TX / 'theme_value_node.parquet', columns=['theme', 'node_id'])
    v2node = dict(zip(VN.theme, VN.node_id))
    del P2, HP, HH, VN

    def top_theme(X, wcol):
        X = X[X.subjects.fillna('').str.strip() != '']
        ev = []
        d = X[X.format != 'BOOK'][['work_id', 'subjects', wcol]]
        d = d.assign(term=d.subjects.str.split(', ')).explode('term')
        d['term'] = d.term.str.strip()
        d = d[d.term != ''].groupby(['work_id', 'term'], as_index=False)[wcol].sum()
        for wid, t, wt in zip(d.work_id, d.term, d[wcol]):
            for v in spl_th.get(t, ()):
                ev.append((wid, 'spl', v, wt / len(spl_th[t])))
        p = X[X.format == 'BOOK'][['work_id', 'subjects', wcol]]
        p = p.assign(h=p.subjects.str.split(', ')).explode('h')
        p['h'] = p.h.str.strip()
        p = p[p.h != '']
        p['hid'] = p.h.map(lambda s: hid_of.get(fix_cp850(s)))
        p = p[p.hid.notna()].groupby(['work_id', 'hid'], as_index=False)[wcol].sum()
        for wid, hid, wt in zip(p.work_id, p.hid, p[wcol]):
            for v, k in hth.get(int(hid), ()):
                ev.append((wid, 'lcsh', v, wt * k))
        E = pd.DataFrame(ev, columns=['work_id', 'source', 'theme', 'weight']).groupby(['work_id', 'source', 'theme'], as_index=False).weight.sum()
        E['node'] = E.theme.map(v2node)
        E = E[E.node.notna()].copy()
        E['share'] = E.weight / E.groupby(['work_id', 'source']).weight.transform('sum')
        E['b'] = E.node.str.split('.').str[0]
        nsrc = E.groupby('work_id').source.nunique()
        T = E.groupby(['work_id', 'b'], as_index=False).share.sum()
        T['strength'] = T.share / T.work_id.map(nsrc)
        T = T.sort_values(['work_id', 'strength', 'b'], ascending=[True, False, True], kind='mergesort').drop_duplicates('work_id')
        return T.set_index('work_id').b

    works = pd.Index(W0.work_id)
    WT = pd.read_parquet(TX / 'work_theme.parquet', columns=['work_id', 'node_id', 'level', 'rank_in_level', 'sources'])
    WT = WT[(WT.level == 1) & (WT.rank_in_level == 1) & WT.work_id.isin(works)].drop_duplicates('work_id').set_index('work_id')
    orig, src = WT.node_id.reindex(works), WT.sources.reindex(works).fillna('')
    rep = top_theme(SR, 'cko').reindex(works)
    nogr = ~src.str.contains('gr')
    rep_same = float((orig.fillna('-') == rep.fillna('-'))[nogr].mean())
    log('replication of work_theme.parquet (all records, loans as weights, works without Goodreads evidence): same top node', round(rep_same, 5))
    assert rep_same > 0.99, 'the theme replication does not match work_theme.parquet'
    M0 = SR[SR.m0]
    th0 = top_theme(M0, 'one').reindex(works)
    g = M0.groupby('work_id')
    py0 = M0.pub_year.where(M0.pub_year > 0).groupby(M0.work_id).min().reindex(works)
    C = pd.DataFrame({'theme_m0': th0.to_numpy(), 'pub_year_m0': py0.to_numpy(),
                      'cft_m0': g.creator_from_title.min().reindex(works).astype(float).to_numpy()}, index=works)
    pyall = SR.pub_year.where(SR.pub_year > 0).groupby(SR.work_id).min().reindex(works)
    cftall = SR.groupby('work_id').creator_from_title.min().reindex(works).astype(float)
    nrec = SR.groupby('work_id').size().reindex(works)
    info = dict(
        works=int(len(works)), records=int(len(SR)),
        works_with_records_first_lent_after_month0=float((nrec > g.size().reindex(works)).mean()),
        works_with_records_first_lent_after_month5=float(SR.groupby('work_id').after5.any().reindex(works).mean()),
        theme_replication_same_top_node_no_goodreads=rep_same, theme_replication_works_compared=int(nogr.sum()),
        theme_present_as_fixed=float(orig.notna().mean()), theme_present_month0=float(th0.notna().mean()),
        theme_same_node=float((orig.fillna('-') == th0.fillna('-')).mean()),
        theme_only_from_later_records=int((orig.notna() & th0.isna()).sum()),
        theme_only_month0=int((orig.isna() & th0.notna()).sum()),
        theme_different_node=int((orig.notna() & th0.notna() & (orig != th0)).sum()),
        pub_year_differs=int(((pyall != py0) & py0.notna()).sum()), pub_year_missing_month0=int(py0.isna().sum()),
        creator_flag_differs=int((cftall != C.cft_m0).sum()))
    log('month-0 catalogue features', info)
    del SR, M0, RW, rfirst, rcko
    return C, info


def part_b():
    # --- rows with the corrections of 30_test_b.py, copied unchanged (time-safe matched and writer_type, left-out shifted books, merged clusters)
    R = pd.read_parquet(OUT / 'test_b_rows.parquet')
    R['fm'] = (R.first_ym // 100) * 12 + R.first_ym % 100 - 1
    R['year'] = R.first_ym // 100
    V = pd.read_parquet(OUT / 'author_monthly_views.parquet')
    first_view = V[V.views > 0].groupby('enwiki_title').ym.min()
    fv = R.enwiki_title.map(first_view)
    R['matched_pre'] = ((R.matched == 1) & fv.notna() & (fv < R.first_ym)).astype(int)
    R['writer_type_pre'] = (R.writer_type * R.matched_pre).astype(int)
    PM = pd.read_parquet(D / 'db' / 'study3' / 'demand_panel.parquet', columns=['ym', 'month_ok']).drop_duplicates()
    EXCL = {int(s.replace('-', '')) for s in PM.loc[~PM.month_ok, 'ym'].unique()}
    R['shifted'] = R.first_ym.map(lambda y: ym_add(y, -1) in EXCL).astype(int)
    R['flag_wide'] = R.first_ym.map(lambda y: any(ym_add(y, k) in EXCL for k in range(-1, 6))).astype(int)
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for ck, t in R.loc[R.matched == 1, ['creator_key', 'enwiki_title']].drop_duplicates().itertuples(index=False):
        a, b = find('k:' + ck), find('t:' + str(t))
        if a != b:
            parent[a] = b
    R['cluster'] = R.creator_key.map(lambda k: find('k:' + k))
    n_all, n_shift = len(R), int(R.shifted.sum())
    R = R[R.shifted == 0].copy()
    log('Test B rows', n_all, 'shifted books left out', n_shift, 'kept', len(R), 'clusters', R.cluster.nunique())
    # --- R5 extra catalogue information, available when the library acquires the work
    WT = pd.read_parquet(D / 'db' / 'taxonomy_v3' / 'work_theme.parquet', columns=['work_id', 'node_id', 'level', 'strength', 'rank_in_level', 'sources'])
    L1 = WT[WT.level == 1]
    nodes = sorted(L1.node_id.unique())
    top = L1[L1.rank_in_level == 1].drop_duplicates('work_id')       # the node with the highest strength (ties: the file's own rank_in_level)
    assert np.isclose(top.merge(L1.groupby('work_id').strength.max().rename('mx'), on='work_id').eval('strength - mx').abs().max(), 0)
    R['theme'] = pd.Categorical(R.work_id.map(top.set_index('work_id').node_id), categories=nodes)
    SW = pd.read_parquet(D / 'db' / 'taxonomy_v3' / 'spl_works.parquet', columns=['work_id', 'pub_year_min', 'creator_from_title_only'])
    R = R.merge(SW, on='work_id', how='left', validate='many_to_one')
    R['age0'] = R.first_ym // 100 - R.pub_year_min
    R['cft_only'] = R.creator_from_title_only.astype(float)
    # added in review: the same three features from the records first lent in the work's first month (see catalogue_month0)
    C0, m0_info = catalogue_month0(R)
    R = R.join(C0, on='work_id')
    R['theme_m0'] = pd.Categorical(R.theme_m0, categories=nodes)
    R['age0_m0'] = R.first_ym // 100 - R.pub_year_m0
    fp = R.fmt_print == 1
    y6 = np.expm1(R.Y6)

    def loans_by(col):
        return {str(k): dict(works=int(len(v)), mean_loans6=float(v.mean()), median_loans6=float(v.median())) for k, v in y6.groupby(R[col].astype(str))}

    def loans_by_mask(y, mask):
        return {k: dict(works=int(m.sum()), mean_loans6=float(y[m].mean()), median_loans6=float(y[m].median())) for k, m in (('yes', mask), ('no', ~mask))}

    extra_info = dict(
        works_with_theme=float(R.theme.notna().mean()), themes=nodes,
        theme_from_goodreads_share=float(top.set_index('work_id').loc[R.work_id[R.theme.notna()].unique(), 'sources'].str.contains('gr').mean()),
        age0_missing=float(R.age0.isna().mean()), age0_counts={int(k): int(v) for k, v in R.age0.value_counts().sort_index().items()},
        creator_from_title_only_share=float(R.cft_only.mean()),
        month0=m0_info,
        works_with_theme_m0=float(R.theme_m0.notna().mean()), creator_from_title_only_share_m0=float(R.cft_m0.mean()),
        age0_m0_counts={int(k): int(v) for k, v in R.age0_m0.value_counts().sort_index().items()}, age0_m0_missing=int(R.age0_m0.isna().sum()),
        # descriptive: is the theme tied to print loans in month 0 (the information correction B2 of the code audit took out of L)?
        theme_present_if_print_loans_month0=dict(as_fixed=float(R.theme[fp].notna().mean()), month0=float(R.theme_m0[fp].notna().mean())),
        theme_present_if_no_print_loans_month0=dict(as_fixed=float(R.theme[~fp].notna().mean()), month0=float(R.theme_m0[~fp].notna().mean())),
        # descriptive: loans in the first six months by publication-year gap, creator flag and theme presence (all kept works, all years)
        loans6_by_age0=loans_by('age0'), loans6_by_age0_m0=loans_by('age0_m0'),
        loans6_by_theme_present=dict(as_fixed=loans_by_mask(y6, R.theme.notna()), month0=loans_by_mask(y6, R.theme_m0.notna())))
    log('extra features', {k: v for k, v in extra_info.items() if k not in ('themes', 'month0')})
    WCOLS = ['matched_pre', 'v6', 'v12', 'trend', 'vmax', 'writer_type_pre']
    LCOLS = ['n_prior_works', 'ln_prior_loans', 'month']
    LPCOLS = LCOLS + ['theme', 'age0', 'cft_only']          # L+ of addendum e, as fixed (features from records of all years)
    L0COLS = LCOLS + ['theme_m0', 'age0_m0', 'cft_m0']     # added in review: the same three features from the records first lent in month 0
    LQCOLS = LCOLS + ['age0_m0', 'cft_m0']                 # added: no theme (month-0 records); the theme is the feature that moves most with the record set
    MODELS = ['W_lgbm', 'L_lgbm', 'LW_lgbm', 'Lp_lgbm', 'LpW_lgbm', 'L0_lgbm', 'L0W_lgbm', 'Lq_lgbm', 'LqW_lgbm']
    SETS = {'W_lgbm': WCOLS, 'L_lgbm': LCOLS, 'LW_lgbm': LCOLS + WCOLS, 'Lp_lgbm': LPCOLS, 'LpW_lgbm': LPCOLS + WCOLS,
            'L0_lgbm': L0COLS, 'L0W_lgbm': L0COLS + WCOLS, 'Lq_lgbm': LQCOLS, 'LqW_lgbm': LQCOLS + WCOLS}
    preds = []
    for Y in range(2019, 2027):
        te = R[R.year == Y]
        tr = R[R.fm + 5 < Y * 12]
        if te.empty:
            continue
        p = te[['work_id', 'cluster', 'year', 'Y6', 'loans6', 'matched_pre', 'writer_type_pre']].copy()
        p['N0'] = tr.Y6.mean()
        for name, cols in SETS.items():
            p[name] = lgb.LGBMRegressor(**LGB).fit(tr[cols], tr.Y6).predict(te[cols])
        preds.append(p)
        log('year', Y, 'train', len(tr), 'test', len(te))
    P = pd.concat(preds, ignore_index=True).rename(columns={'cluster': 'creator_key'})
    P.to_parquet(OUT / f'robustness_b_preds{TAG}.parquet', index=False)
    # --- the refit of W, L and LW must equal the stored predictions of 30_test_b.py
    S = pd.read_parquet(OUT / 'test_b_preds.parquet', columns=['work_id', 'W_lgbm', 'L_lgbm', 'LW_lgbm'])
    M = P[['work_id', 'W_lgbm', 'L_lgbm', 'LW_lgbm']].merge(S, on='work_id', suffixes=('', '_stored'), validate='one_to_one')
    check = {c: float((M[c] - M[c + '_stored']).abs().max()) for c in ['W_lgbm', 'L_lgbm', 'LW_lgbm']}
    log('refit vs stored Test B predictions: max abs difference', check, 'rows compared', len(M), 'of', len(P))
    years = sorted(P.year.unique())

    def point_by_year(df, c):
        sp, t10 = [], []
        for y in years:
            g = df[df.year == y]
            sp.append(float(np.corrcoef(rankdata(g[c]), rankdata(g.Y6))[0, 1]) if g[c].nunique() > 1 else 0.0)
            a = g.Y6 >= g.Y6.quantile(0.9)
            pr = g[c] >= g[c].quantile(0.9) if g[c].nunique() > 1 else pd.Series(False, index=g.index)
            t10.append(float((a & pr).sum() / max(pr.sum(), 1)))
        return np.array(sp), np.array(t10)

    DIFFS = [('LW_minus_L', 'LW_lgbm', 'L_lgbm'), ('LpW_minus_Lp', 'LpW_lgbm', 'Lp_lgbm'), ('L0W_minus_L0', 'L0W_lgbm', 'L0_lgbm'),
             ('LqW_minus_Lq', 'LqW_lgbm', 'Lq_lgbm'), ('Lp_minus_L', 'Lp_lgbm', 'L_lgbm'), ('L0_minus_L', 'L0_lgbm', 'L_lgbm'),
             ('Lq_minus_L', 'Lq_lgbm', 'L_lgbm'), ('L0_minus_Lq', 'L0_lgbm', 'Lq_lgbm'), ('Lp_minus_L0', 'Lp_lgbm', 'L0_lgbm'),
             ('LpW_minus_LW', 'LpW_lgbm', 'LW_lgbm')]

    def boot(df, label):
        """Author-cluster bootstrap as 30_test_b.py: same seed, same draws, Spearman within test year averaged over years; the per-year
        values of every draw are kept, so the by-year intervals and the paired differences come from the same draws."""
        rng = np.random.default_rng(SEED)
        keys = df.creator_key.values
        uk, inv = np.unique(keys, return_inverse=True)
        rows_of = pd.Series(np.arange(len(df))).groupby(inv).apply(np.array).values
        yr, y6 = df.year.values, df.Y6.values
        X = {c: df[c].values for c in MODELS}
        Vd = {c: np.full((NB, len(years)), np.nan) for c in MODELS}
        for b in range(NB):
            pick = rng.integers(0, len(uk), len(uk))
            idx = np.concatenate(rows_of[pick])
            yy, yi = y6[idx], yr[idx]
            xs = {c: X[c][idx] for c in MODELS}
            for j, y in enumerate(years):
                m = yi == y
                if m.sum() > 10:
                    ry = rankdata(yy[m])
                    for c in MODELS:
                        Vd[c][b, j] = np.corrcoef(rankdata(xs[c][m]), ry)[0, 1]
            if b % 500 == 0:
                log('  bootstrap', label, b)
        out = dict(n=dict(rows=int(len(df)), authors=int(len(uk))), models={}, diffs={}, by_year={})
        pt = {c: point_by_year(df, c) for c in MODELS}
        for c in MODELS:
            mb = np.nanmean(Vd[c], axis=1)
            out['models'][c] = dict(spearman=float(pt[c][0].mean()), lo=float(np.percentile(mb, 2.5)), hi=float(np.percentile(mb, 97.5)),
                                    top10_precision=float(pt[c][1].mean()))
        for name, a, b in DIFFS:
            d = np.nanmean(Vd[a] - Vd[b], axis=1)
            out['diffs'][name] = dict(mean=float(pt[a][0].mean() - pt[b][0].mean()), lo=float(np.percentile(d, 2.5)), hi=float(np.percentile(d, 97.5)))
        for j, y in enumerate(years):
            g = df[df.year == y]
            cell = dict(n=int(len(g)), authors=int(g.creator_key.nunique()), top10_base=float((g.Y6 >= g.Y6.quantile(0.9)).mean()), models={}, diffs={})
            for c in MODELS:
                cell['models'][c] = dict(spearman=float(pt[c][0][j]), lo=float(np.nanpercentile(Vd[c][:, j], 2.5)),
                                         hi=float(np.nanpercentile(Vd[c][:, j], 97.5)), top10_precision=float(pt[c][1][j]))
            for name, a, b in DIFFS:
                d = Vd[a][:, j] - Vd[b][:, j]
                cell['diffs'][name] = dict(mean=float(pt[a][0][j] - pt[b][0][j]), lo=float(np.nanpercentile(d, 2.5)), hi=float(np.nanpercentile(d, 97.5)))
            out['by_year'][str(y)] = cell
        return out

    res = dict(extra_info=extra_info, refit_check_max_abs_diff=check, rows_compared=int(len(M)), models=MODELS,
               rows=dict(read=int(n_all), shifted_left_out=n_shift, kept=int(len(R))), subsets={})
    for label, df in (('all', P), ('matched', P[P.matched_pre == 1].reset_index(drop=True)),
                      ('writer_type', P[P.writer_type_pre == 1].reset_index(drop=True))):
        res['subsets'][label] = boot(df, label)
        part = dict(res)
        part['runtime_s'] = round(time.time() - T0)
        part['peak_gb'] = round(peak_gb(), 2)
        save_part('b', part)
        log(label, {c: round(res['subsets'][label]['models'][c]['spearman'], 4) for c in MODELS},
            {k: (round(v['mean'], 4), round(v['lo'], 4), round(v['hi'], 4)) for k, v in res['subsets'][label]['diffs'].items()})
    res['runtime_s'] = round(time.time() - T0)
    res['peak_gb'] = round(peak_gb(), 2)
    save_part('b', res)


# ====================================================================== dispatch
if __name__ == '__main__':
    part = sys.argv[1] if len(sys.argv) > 1 else ''
    log('part', part, 'draws', NB)
    if part == 'b':
        part_b()
    elif part == 'd':
        part_d()
    elif part == 'a':
        part_a('corrected')
    elif part == 'a_orig':
        part_a('original')
    elif part == 'a_seeds':
        part_a_seeds()
    else:
        raise SystemExit(__doc__)
    log('done; peak memory', round(peak_gb(), 2), 'GB')
