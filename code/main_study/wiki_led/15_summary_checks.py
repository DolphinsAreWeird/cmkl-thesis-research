# 15. Summary checks (descriptive; added after all results were seen, at the request of the examiner review of 20 Oct 2026,
# data/reports/wiki_led_examiner_review.md, Section 2 and the appendix). One saved script for the numbers that the results summary
# (paper/Wikipedia_Led_Results_2026-10-20_1924.md) and the review quote without a script behind them: the "different books" figures,
# the August 2026 example, a new June to July 2026 example, the persistence rule in Tests A, D and E, Test B's one-column baselines and
# the split by earlier Seattle books, the author-cap check logged in prereg/DEVIATIONS.md (17:07), and every "(check)" number of the
# review's appendix. Fits no model and changes no decision.
# Reads stored files only: data/db/wiki_led/ (predictions and rows of Tests A, B, D and E, and the corrected _c files of addendum e where
# they exist, the October live list, the robustness part files), data/reports/wiki_led_test_d.json, wiki_led_test_e.json and
# wiki_led_test_a_accuracy.csv (stored values to compare with), data/db/study2r/works.parquet (titles for the two examples) and, if the
# clone exists, `git log` of the public repository ~/cmkl-thesis-research (first public time of each settings record).
# Writes data/reports/wiki_led_summary_checks.json and data/reports/wiki_led_summary_checks.md.
# Rules, as in the review's appendix: rose = stored D >= ln 1.5 (Tests D and E: the stored rose column); the top k of a month are its k
# highest scores, ties broken by work_id ascending (book_id in Test E); a hit rate is the mean of the monthly shares (Test D: of the
# format-month shares); rank = Spearman within month (Tests A and E) or within first-month year (Test B), averaged. For every top-k hit
# rate the script also gives the lowest and highest value over all orders of the tied scores at the cut-off and the expected value
# under a random order, so that a gap to a stored value that used another tie order can be told from a real difference. The author
# cap is also repeated exactly as it was logged (each period's rows sorted by score alone with pandas' default sort, which leaves
# tied scores in no fixed order; the cap leaves out books without an author article), which reproduces the six logged numbers.
# Run from code/: ../.venv/bin/python main_study/wiki_led/15_summary_checks.py   (about one to two minutes; peak memory under 1.5 GB)
import sys, os, re, json, time, pathlib, resource, subprocess
from decimal import Decimal, ROUND_HALF_UP
import numpy as np, pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
DB, REP, ROOT = D / 'db' / 'wiki_led', D / 'reports', D.parent
CLONE = pathlib.Path.home() / 'cmkl-thesis-research'
OUT_JSON, OUT_MD = REP / 'wiki_led_summary_checks.json', REP / 'wiki_led_summary_checks.md'
os.nice(10)                                                              # machine rule: nice
T0 = time.time()
LN15 = np.log(1.5)
SEED = 20261020
MEM_LIMIT_GB = 1.5


def peak_gb():                                                           # macOS reports ru_maxrss in bytes
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:5.0f}s [peak {peak_gb():.2f} GB]', *a, flush=True)


def ym(m):
    return f'{m // 12}-{m % 12 + 1:02d}'


V, VC = {}, {}            # computed values on the original files and on the corrected (_c) files, flat keys
TIES, TIES_C = {}, {}     # key -> tie range of a top-k hit rate (original, corrected)
EXAMPLES = {}
INPUTS = {}


def note_input(path):
    INPUTS[str(path.relative_to(ROOT))] = time.strftime('%Y-%m-%d %H:%M', time.localtime(path.stat().st_mtime))
    return path


# ---------------------------------------------------------------- shared helpers
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


def put(store, ties, key, t):
    store[key] = t['rate']
    ties[key] = t


# ---------------------------------------------------------------- titles for the examples
W = pd.read_parquet(note_input(D / 'db' / 'study2r' / 'works.parquet'), columns=['work_id', 'title', 'creator'])
TITLE = {int(w): str(t).split(' / ')[0].strip().rstrip(' :;,.').replace('|', '/')[:70] for w, t in zip(W.work_id, W.title)}
CREATOR = {int(w): (str(c) if isinstance(c, str) else '') for w, c in zip(W.work_id, W.creator)}
del W

# ---------------------------------------------------------------- Test A (existing books)
A_MODELS = {'W': 'Wlgbm_D', 'H': 'Hlgbm_D', 'HW': 'HWlgbm_D', 'naive': 'Hnaive_D', 'Wrule': 'Wrule_D'}


def load_a(suf):
    P = pd.read_parquet(note_input(DB / f'test_a_preds{suf}.parquet'), columns=['work_id', 'mi', 'year', 'D', 'Sg'] + list(A_MODELS.values()))
    R = pd.read_parquet(note_input(DB / f'test_a_rows{suf}.parquet'),
                        columns=['work_id', 'mi', 'L_t', 'L_next', 'M6', 'h_lt', 'h_m6', 'h_age', 'b_lvl4', 'author_article'])
    # first origin month (over all rows from 2016-03) at which the book's own article has views in the last 4 weeks
    first = R[R.b_lvl4.notna() & (R.b_lvl4 > -27)].groupby('work_id').mi.min()
    P = P.merge(R, on=['work_id', 'mi'], how='left', validate='one_to_one')
    del R
    assert P.h_lt.notna().all(), 'a scored row has no row in the rows file'
    P['rose'] = (P.D >= LN15).astype('int8')                             # stored float32 D, as Tests A to E
    P['up'] = (P.h_lt - P.h_m6) >= LN15                                  # already up at the origin (float32, as the stored columns)
    P['young'] = P.h_age < 12
    P['pre_floor'] = P.b_lvl4 <= -27                                     # original files: zero views in the last 4 weeks (the floor of lvl4)
    fm = P.work_id.map(first)
    P['pre_first'] = fm.isna() | (P.mi < fm)                             # either file: before the book's page first has views
    return P


def capped_lists(P, cap, k=20):
    """Wikipedia-only top k per month with at most `cap` books per author (author = author article; a book without one is its own author)."""
    o = P.sort_values(['mi', 'Wlgbm_D', 'work_id'], ascending=[True, False, True])
    akey = o.author_article.fillna('work ' + o.work_id.astype(str))
    if cap:
        keep = o.groupby([o.mi, akey]).cumcount().to_numpy() < cap
        o, akey = o[keep], akey[keep]
    t = o.groupby('mi').head(k)
    return t, akey.loc[t.index]


def cap_as_logged(P, out):
    """The 17:07 check as it was run (it reproduces all six logged numbers): each period's rows sorted by the Wikipedia score alone with
    pandas' default sort, which is not stable, so tied scores keep no fixed order; at most `cap` books per month and author article by
    groupby().head(), which leaves books without an author article out of the capped lists; then each month's top 20."""
    for per, sel in (('2019_2023', P.year.between(2019, 2023)), ('2024_2026', P.year >= 2024)):
        o = P[sel].sort_values('Wlgbm_D', ascending=False)
        for cap in (None, 2, 1):
            t = (o if cap is None else o.groupby(['mi', 'author_article']).head(cap)).groupby('mi').head(20)
            out[f'A.cap_as_logged.{cap or "none"}.{per}.rose'] = float(t.groupby('mi').rose.mean().mean())
            out[f'A.cap_as_logged.{cap or "none"}.{per}.authors'] = float(t.groupby('mi').author_article.nunique().mean())


def example(P, m):
    g = P[P.mi == m]
    res = dict(origin=ym(m), target=ym(m + 1), books=int(len(g)), base_rose=float(g.rose.mean()), base_surge=float(g.Sg.mean()))
    lists = {}
    for name in ('W', 'H', 'HW'):
        o = g.sort_values([A_MODELS[name], 'work_id'], ascending=[False, True])
        for k in (20, 50):
            t = o.head(k)
            res[f'{name}.top{k}.rose'] = int(t.rose.sum())
            res[f'{name}.top{k}.surged'] = int(t.Sg.sum())
        lists[name] = o.head(20)
    t = lists['W']
    vc = t.author_article.value_counts()
    top_a = vc.index[0]
    res.update(top_author=top_a, top_author_books=int(vc.iloc[0]), top_author_rose=int(t.rose[t.author_article == top_a].sum()),
               other_books=int((t.author_article != top_a).sum()), other_rose=int(t.rose[t.author_article != top_a].sum()),
               W_up_at_origin=int(t.up.sum()), W_H_top20_shared=int(t.work_id.isin(lists['H'].work_id).sum()))
    res['W_top20'] = [dict(rank=i + 1, work_id=int(r.work_id), title=TITLE.get(int(r.work_id), ''),
                           author=r.author_article if isinstance(r.author_article, str) else CREATOR.get(int(r.work_id), ''),
                           loans_origin=int(r.L_t), median6=float(r.M6), loans_next=int(r.L_next), rose=int(r.rose), surged=int(r.Sg),
                           up_at_origin=bool(r.up)) for i, r in enumerate(t.itertuples())]
    return res


def test_a(P, pre, out, ties):
    out['A.rows'], out['A.months'] = len(P), int(P.mi.nunique())
    out['A.base_rose'], out['A.base_surge'] = float(P.rose.mean()), float(P.Sg.mean())
    out['A.rise_if_up'], out['A.rise_if_not_up'] = float(P.rose[P.up].mean()), float(P.rose[~P.up].mean())
    out['A.rises_from_up'] = float(P.up[P.rose == 1].mean())
    out['A.mean_next_loans'] = float(P.L_next.astype('float64').mean())
    out['A.median_Lt_2019'] = float(P.L_t.median())
    pos = {m: order_pos(P, c, ['mi'], 'work_id') for m, c in A_MODELS.items()}
    for m, c in A_MODELS.items():
        for k in (20, 50):
            for fl, lab in (('rose', 'rose'), ('Sg', 'surged')):
                put(out, ties, f'A.top{k}.{lab}.{m}', topk(P, c, fl, k, ['mi'], 'work_id', pos[m]))
        g = P[pos[m] < 20].groupby('mi')
        out[f'A.top20.already_up.{m}'] = float(g.up.mean().mean())
        out[f'A.top20.young.{m}'] = float(g.young.mean().mean())
        out[f'A.top20.pre_article.{m}'] = float(g[pre].mean().mean())
        out[f'A.top20.authors.{m}'] = float(g.author_article.nunique().mean())      # a book without an author article is not counted
    # Wikipedia's picks against the library's lists, and the library's next picks
    x = P[['mi', 'rose', 'Sg']].reset_index(drop=True)
    w20 = pos['W'] < 20
    off_h, off_hw = w20 & ~(pos['H'] < 50), w20 & ~(pos['HW'] < 50)
    gm = x.assign(off=off_h, off_r=off_h & (x.rose == 1).to_numpy(), off_s=off_h & (x.Sg == 1).to_numpy()).groupby('mi')[['off', 'off_r', 'off_s']].sum()
    out['A.overlap.share'] = float((gm.off / 20).mean())
    out['A.overlap.books_per_month'] = float(gm.off.mean())
    out['A.overlap.rose_monthly'] = float((gm.off_r / gm.off.replace(0, np.nan)).mean())        # months without such a book are skipped
    out['A.overlap.rose_pooled'] = float(gm.off_r.sum() / gm.off.sum())
    out['A.overlap.surged'] = float((gm.off_s / gm.off.replace(0, np.nan)).mean())

    def band(p, lo, hi, sel=None):
        m_ = (p >= lo) & (p < hi)
        if sel is not None:
            m_ &= sel
        return float(x.rose.where(m_).groupby(x.mi).mean().mean())
    out['A.next.H_21_40'], out['A.next.H_51_70'] = band(pos['H'], 20, 40), band(pos['H'], 50, 70)
    out['A.next.HW_21_40'] = band(pos['HW'], 20, 40)
    out['A.next.W_not_in_HW50'] = band(pos['W'], 0, 20, off_hw)
    wm = x.rose.where(w20).groupby(x.mi).mean()
    out['A.months_W_beats_base'] = int((wm > x.groupby('mi').rose.mean()).sum())
    out['A.months_scored'] = int(len(wm))
    out['A.extra_hits_per_month'] = (out['A.top20.rose.HW'] - out['A.top20.rose.H']) * 20
    out['A.months_per_extra_book'] = 1 / out['A.extra_hits_per_month']
    # young books and rows before the book's article had views
    out['A.young.share_rows'], out['A.young.surge'] = float(P.young.mean()), float(P.Sg[P.young].mean())
    out['A.older.surge'], out['A.young.rose'], out['A.older.rose'] = float(P.Sg[~P.young].mean()), float(P.rose[P.young].mean()), float(P.rose[~P.young].mean())
    out['A.pre.share_rows'], out['A.pre.surge'], out['A.pre.rose'] = float(P[pre].mean()), float(P.Sg[P[pre]].mean()), float(P.rose[P[pre]].mean())
    # rows with at least 24 months of loans whose book article already had views (with this file's rule, and with the first-views rule,
    # which is the only one the corrected file allows, so that original and corrected can be compared on the same rows)
    for tag, rule in (('restricted', pre), ('restricted_first', 'pre_first')):
        S = P[(P.h_age >= 24) & ~P[rule]]
        out[f'A.{tag}.rows'], out[f'A.{tag}.base'] = len(S), float(S.rose.mean())
        for m in ('W', 'H', 'HW'):
            out[f'A.{tag}.rank.{m}'] = month_rank(S, A_MODELS[m])
            put(out, ties, f'A.{tag}.top20.{m}', topk(S, A_MODELS[m], 'rose', 20, ['mi'], 'work_id'))
        del S
    # early warning: books not already up at the origin
    E = P[~P.up]
    out['A.early.base'] = float(E.rose.mean())
    for m in ('W', 'H', 'HW', 'naive'):
        pe = order_pos(E, A_MODELS[m], ['mi'], 'work_id')
        put(out, ties, f'A.early.{m}', topk(E, A_MODELS[m], 'rose', 20, ['mi'], 'work_id', pe))
        if m == 'H':
            out['A.early.H_young'] = float(E.young[pe < 20].groupby(E.mi[pe < 20]).mean().mean())
    del E

    # gain of library + Wikipedia over the library model in the change rank, by book age (months since the first loan)
    def gain(df):
        return float(np.mean([spearmanr(g.HWlgbm_D, g.D).statistic - spearmanr(g.Hlgbm_D, g.D).statistic for _, g in df.groupby('mi') if len(g) > 30]))
    out['A.gain_age.lt12'] = gain(P[P.h_age < 12])
    out['A.gain_age.12_35'] = gain(P[(P.h_age >= 12) & (P.h_age < 36)])
    out['A.gain_age.ge36'] = gain(P[P.h_age >= 36])
    # Wikipedia top 20 in 2024-2026: 3-month block interval (draws as in the review: one set, seed 20261020) against a binomial one
    ms = np.sort(P.mi[P.year >= 2024].unique())
    wv = wm.reindex(ms).to_numpy()
    n, kb = len(ms), int(np.ceil(len(ms) / 3))
    rng = np.random.default_rng(SEED)
    bd = np.array([np.concatenate([np.arange(a, a + 3) % n for a in rng.choice(n, kb)])[:n] for _ in range(2000)])
    b, p_ = wv[bd].mean(1), float(wv.mean())
    se = np.sqrt(p_ * (1 - p_) / (20 * n))
    out['A.interval.months'], out['A.interval.W_2024_2026'] = n, p_
    out['A.interval.block_lo'], out['A.interval.block_hi'] = (float(v) for v in np.percentile(b, [2.5, 97.5]))
    out['A.interval.binom_lo'], out['A.interval.binom_hi'] = p_ - 1.96 * se, p_ + 1.96 * se
    # author cap on the Wikipedia-only list (DEVIATIONS 17:07)
    for cap in (None, 2, 1):
        t, a = capped_lists(P, cap)
        rm, am, yr = t.groupby('mi').rose.mean(), a.groupby(t.mi).nunique(), t.groupby('mi').year.first()
        for name, sel in (('2019_2023', (yr >= 2019) & (yr <= 2023)), ('2024_2026', yr >= 2024), ('all', yr >= 2019)):
            out[f'A.cap.{cap or "none"}.{name}.rose'] = float(rm[sel].mean())
            out[f'A.cap.{cap or "none"}.{name}.authors'] = float(am[sel].mean())
    out['A.cap.months_2019_2023'] = int(((yr >= 2019) & (yr <= 2023)).sum())
    return pos


for suf, out, ties, pre in (('', V, TIES, 'pre_floor'), ('_c', VC, TIES_C, 'pre_first')):
    if not (DB / f'test_a_preds{suf}.parquet').exists():
        log('Test A', suf or 'original', 'not found; skipped')
        continue
    P = load_a(suf)
    test_a(P, pre, out, ties)
    if suf == '':
        # how the two ways of marking "before the article had views" agree on the original file
        V['A.pre.rule_first_share_rows'] = float(P.pre_first.mean())
        V['A.pre.rules_agree'] = float((P.pre_first == P.pre_floor).mean())
        cap_as_logged(P, V)                                              # needs the stored row order of the predictions file
    EXAMPLES[suf or 'orig'] = {'august_2026': example(P, 2026 * 12 + 6), 'june_july_2026': example(P, 2026 * 12 + 5)}
    ex = EXAMPLES[suf or 'orig']['august_2026']
    for k, src in (('books', 'books'), ('base_rose', 'base_rose'), ('base_surge', 'base_surge'), ('W_rose', 'W.top20.rose'),
                   ('W_surged', 'W.top20.surged'), ('H_rose', 'H.top20.rose'), ('H_surged', 'H.top20.surged'), ('HW_rose', 'HW.top20.rose'),
                   ('HW_surged', 'HW.top20.surged'), ('top_author_books', 'top_author_books'), ('top_author_rose', 'top_author_rose'),
                   ('other_books', 'other_books'), ('other_rose', 'other_rose')):
        out[f'A.aug.{k}'] = ex[src]
    out['A.aug.top_author'] = ex['top_author']
    log('Test A', suf or 'original', 'rows', len(P), 'W top 20', round(out['A.top20.rose.W'], 4), 'persistence', round(out['A.top20.rose.naive'], 4))
    del P
acc = pd.read_csv(note_input(REP / 'wiki_led_test_a_accuracy.csv'), index_col=0)
V['A.mean_next_loans_from_panel'] = float(acc.loc['Wikipedia only (trees)', 'MAE_loans'] / acc.loc['Wikipedia only (trees)', 'WAPE'])

# ---------------------------------------------------------------- Test B (new books)
B = pd.read_parquet(note_input(DB / 'test_b_preds.parquet'),
                    columns=['work_id', 'year', 'Y6', 'matched_pre', 'W_lgbm', 'L_lgbm', 'LW_lgbm', 'Lfmt_check', 'LWfmt_check'])
BR = pd.read_parquet(note_input(DB / 'test_b_rows.parquet'), columns=['work_id', 'v6', 'n_prior_works', 'fmt_print', 'fmt_ebook', 'fmt_audiobook'])
B = B.merge(BR, on='work_id', how='left', validate='one_to_one')
del BR
B['nfmt'] = B.fmt_print + B.fmt_ebook + B.fmt_audiobook                # formats borrowed in month 0 (0 to 3)


def yr_rank(df, c):
    v = {int(y): float(spearmanr(g[c], g.Y6).statistic) if g[c].nunique() > 1 else 0.0 for y, g in df.groupby('year')}
    return float(np.mean(list(v.values()))), v


V['B.rows'], V['B.matched_pre.n'], V['B.matched_pre.share'] = len(B), int(B.matched_pre.sum()), float(B.matched_pre.mean())
for key, c in (('matched_pre', 'matched_pre'), ('v6', 'v6'), ('nfmt', 'nfmt'), ('W', 'W_lgbm'), ('L', 'L_lgbm'), ('LW', 'LW_lgbm'),
               ('Lfmt', 'Lfmt_check'), ('LWfmt', 'LWfmt_check')):
    V[f'B.rank.{key}'] = yr_rank(B, c)[0]
V['B.gain.all'] = V['B.rank.LW'] - V['B.rank.L']
V['B.fmt_gain'] = V['B.rank.LWfmt'] - V['B.rank.Lfmt']
M = B[B.matched_pre == 1]
for key, c in (('v6', 'v6'), ('W', 'W_lgbm'), ('L', 'L_lgbm'), ('LW', 'LW_lgbm')):
    V[f'B.matched.rank.{key}'] = yr_rank(M, c)[0]
V['B.gain.matched'] = V['B.matched.rank.LW'] - V['B.matched.rank.L']
for name, sub in (('none', B[B.n_prior_works == 0]), ('some', B[B.n_prior_works > 0])):
    V[f'B.{name}.rows'] = len(sub)
    for key, c in (('W', 'W_lgbm'), ('L', 'L_lgbm'), ('LW', 'LW_lgbm')):
        V[f'B.{name}.{key}'] = yr_rank(sub, c)[0]
    V[f'B.{name}.gain'] = V[f'B.{name}.LW'] - V[f'B.{name}.L']
ylw, yl = yr_rank(B, 'LW_lgbm')[1], yr_rank(B, 'L_lgbm')[1]
gy = {y: ylw[y] - yl[y] for y in sorted(ylw)}
V['B.gain_year'] = {str(k): v for k, v in gy.items()}
V['B.gain_year.min'], V['B.gain_year.max'] = min(gy.values()), max(gy.values())
q99 = M.v6.quantile(0.99)
V['B.no_top1.W'] = yr_rank(B[~((B.matched_pre == 1) & (B.v6 >= q99))], 'W_lgbm')[0]
log('Test B', 'rows', len(B), 'none', V['B.none.rows'], 'gain', round(V['B.none.gain'], 4), 'some', round(V['B.some.gain'], 4))
del B, M

# ---------------------------------------------------------------- Test D (all books, by format)
D_MODELS = ['W', 'H', 'HW', 'naive']
D_PERIODS = {'2019_2026': 2019, '2024_2026': 2024}


def test_d(suf, out, ties):
    f = DB / f'test_d_preds{suf}.parquet'
    if not f.exists():
        return False
    TD = pd.read_parquet(note_input(f), columns=['work_id', 'format', 'mi', 'year', 'rose', 'Sg', 'not_yet', 'in_test_a'] + D_MODELS)
    fc = TD.format.astype('category')
    TD['fmt'] = fc.cat.codes.astype('int8')
    names = dict(enumerate(fc.cat.categories))
    TD = TD.drop(columns='format')
    del fc
    out['D.rows'], out['D.in_test_a'] = len(TD), float(TD.in_test_a.mean())
    for code, fname in names.items():
        out[f'D.base.{fname}'] = float(TD.rose[TD.fmt == code].mean())
    out['D.base.all'] = float(TD.rose.mean())
    for m in D_MODELS:
        pos = order_pos(TD, m, ['fmt', 'mi'], 'work_id')                # whole months, so the same places hold in every period subset
        for per, y0 in D_PERIODS.items():
            for code, fname in list(names.items()) + [(None, 'all')]:
                sel = (TD.year >= y0).to_numpy() & ((TD.fmt == code).to_numpy() if code is not None else True)
                sub = TD[sel]
                put(out, ties, f'D.top20.{m}.{fname}.{per}', topk(sub, m, 'rose', 20, ['fmt', 'mi'], 'work_id', pos[sel]))
                t = sub[pos[sel] < 20]
                out[f'D.top20_testA.{m}.{fname}.{per}'] = float(t.groupby(['fmt', 'mi']).in_test_a.mean().mean())
                del sub, t
        del pos
    E = TD[TD.not_yet]
    for m in D_MODELS:
        put(out, ties, f'D.early.{m}.all', topk(E, m, 'rose', 20, ['fmt', 'mi'], 'work_id'))
    v = [out[f'D.top20_testA.W.{fname}.2019_2026'] for fname in names.values()]
    out['D.W_testA_min'], out['D.W_testA_max'] = min(v), max(v)
    del TD, E
    return True


HAS_D_C = False
for suf, out, ties in (('', V, TIES), ('_c', VC, TIES_C)):
    ok = test_d(suf, out, ties)
    if suf == '_c':
        HAS_D_C = ok
    log('Test D', suf or 'original', 'done' if ok else 'not found; skipped')

# ---------------------------------------------------------------- Test E (LibriVox)
E_MODELS = ['E1_W', 'E2_W', 'E1_H', 'E2_H', 'E1_HW', 'E2_HW', 'naive']
EP = pd.read_parquet(note_input(DB / 'test_e_preds.parquet'), columns=['book_id', 'mi', 'year', 'D', 'rose', 'flag_jump'] + E_MODELS)
ER = pd.read_parquet(note_input(DB / 'test_e_rows.parquet'), columns=['book_id', 'mi', 'L_t', 'b_src', 'a_src'])
V['E.median_Lt_2019'] = float(ER.L_t[ER.mi >= 2019 * 12].median())      # all LibriVox rows from origin 2019-01, as in 51_test_e_report.py
V['E.scale_ratio'] = V['E.median_Lt_2019'] / V['A.median_Lt_2019']
EP = EP.merge(ER[['book_id', 'mi', 'b_src', 'a_src']], on=['book_id', 'mi'], how='left', validate='one_to_one')
del ER
main = EP[EP.flag_jump == 0]
feat = main[(main.b_src > 0) | (main.a_src > 0)]                         # main rows with stored Wikipedia views
V['E.main_rows'], V['E.feat_rows'], V['E.feat_share'] = len(main), len(feat), len(feat) / len(main)
V['E.base_rose.main'] = float(main.rose.mean())
for m in E_MODELS:
    V[f'E.main.rank.{m}'] = month_rank(main, m)
    put(V, TIES, f'E.main.top20.{m}', topk(main, m, 'rose', 20, ['mi'], 'book_id'))
for m in ('E1_W', 'E2_W', 'E1_H', 'E1_HW', 'naive'):
    V[f'E.feat.rank.{m}'] = month_rank(feat, m)
    put(V, TIES, f'E.feat.top20.{m}', topk(feat, m, 'rose', 20, ['mi'], 'book_id'))
for rows_name, df in (('main', main), ('all', EP)):
    for per, y0 in D_PERIODS.items():
        put(V, TIES, f'E.naive.top20.{rows_name}.{per}', topk(df[df.year >= y0], 'naive', 'rose', 20, ['mi'], 'book_id'))
log('Test E', 'main rows', len(main), 'with views', len(feat), 'persistence top 20', round(V['E.naive.top20.main.2019_2026'], 4))
del EP, main, feat

# ---------------------------------------------------------------- October live list
L = pd.read_parquet(note_input(DB / 'live_alert_2026-10_all.parquet'), columns=['work_id', 'author_article', 'rank']).sort_values('rank')
for k in (20, 50):
    V[f'L.top{k}_authors'] = int(L.head(k).author_article.nunique())
vc = L.head(20).author_article.value_counts()
V['L.top20_most'] = {a: int(c) for a, c in vc[vc > 1].items()}
V['L.dillard'], V['L.child'] = int(vc.get('Annie Dillard', 0)), int(vc.get('Lee Child', 0))
del L

# ---------------------------------------------------------------- public timestamps (git log of the public clone, read only)
RECORDS = {'settings': 'prereg/wiki_led_settings_2026-10-20.json', 'a': 'prereg/addenda_wiki_led/2026-10-20_a_test_c_themes.json',
           'b': 'prereg/addenda_wiki_led/2026-10-20_b_placebo_test_a.json', 'c': 'prereg/addenda_wiki_led/2026-10-20_c_improvement_round.json',
           'd': 'prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json', 'e': 'prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json'}
GIT = {}
if (CLONE / '.git').exists():
    for k, p in RECORDS.items():
        r = subprocess.run(['git', '-C', str(CLONE), 'log', '--diff-filter=A', '--format=%ci %h', '--', p], capture_output=True, text=True, timeout=60)
        lines = r.stdout.strip().splitlines()
        GIT[k] = lines[-1] if lines else None                            # the commit that first added the file
        V[f'G.{k}'] = lines[-1].split()[1] if lines else None
log('git', GIT if GIT else 'clone not found')

# ---------------------------------------------------------------- stored values that used another order of tied scores
STORED = {}
RND, UNST = 'one random order, exact threshold', 'unstable sort'
ro = json.loads(note_input(DB / 'robustness_part_a_orig.json').read_text())
STORED['A.top20.rose.naive'] = [('robustness_part_a_orig.json', RND, ro['lists']['models']['Hnaive_D']['top20']['rose50']['mean'])]
rd = json.loads(note_input(DB / 'robustness_part_d.json').read_text())['original']['scopes']
td = json.loads(note_input(REP / 'wiki_led_test_d.json').read_text())
te = json.loads(note_input(REP / 'wiki_led_test_e.json').read_text())
for fmt in ('print', 'ebook', 'audiobook', 'all'):
    for per in D_PERIODS:
        STORED[f'D.top20.naive.{fmt}.{per}'] = [('robustness_part_d.json', RND, rd[f'{fmt}|{per.replace("_", "-")}']['lists']['naive']['top20']['rose50']['rate'])]
    STORED[f'D.top20.naive.{fmt}.2019_2026'].append(('wiki_led_test_d.json', UNST, td['alert'][f'{fmt}|naive']['top20']['rose']))
for rows_name, lab in (('main', 'main (no automated-traffic months)'), ('all', 'check (all rows)')):
    STORED[f'E.naive.top20.{rows_name}.2019_2026'] = [('wiki_led_test_e.json', UNST, te[lab]['models']['naive']['top20']['rose'])]
del ro, rd, td, te

# ---------------------------------------------------------------- numbers quoted in the review (R), the results summary (S) and DEVIATIONS
R_, S_, DV = 'review', 'results summary', 'DEVIATIONS 17:07'
EXP = [  # key, what, quoted in, quoted value, decimals printed, unit (pct = share shown in %, num, int, time)
    ('A.overlap.share', "Test A: Wikipedia's top 20 not on the library model's top 50", R_, 77.7, 1, 'pct'),
    ('A.overlap.share', "Test A: Wikipedia's top 20 not on the library model's top 50", S_, 78, 0, 'pct'),
    ('A.overlap.rose_monthly', 'Test A: of those books, share that rose (mean of monthly shares)', R_, 48.1, 1, 'pct'),
    ('A.overlap.rose_monthly', 'Test A: of those books, share that rose (mean of monthly shares)', S_, 48, 0, 'pct'),
    ('A.overlap.surged', 'Test A: of those books, share that surged', R_, 25.6, 1, 'pct'),
    ('A.overlap.surged', 'Test A: of those books, share that surged', S_, 26, 0, 'pct'),
    ('A.top20.already_up.H', 'Test A: library top 20 already up at the origin', R_, 90.1, 1, 'pct'),
    ('A.top20.already_up.H', 'Test A: library top 20 already up at the origin', S_, 90, 0, 'pct'),
    ('A.top20.already_up.HW', 'Test A: library + Wikipedia top 20 already up', R_, 87.6, 1, 'pct'),
    ('A.top20.already_up.W', 'Test A: Wikipedia top 20 already up', R_, 47.0, 1, 'pct'),
    ('A.top20.already_up.W', 'Test A: Wikipedia top 20 already up', S_, 47, 0, 'pct'),
    ('A.top20.already_up.naive', 'Test A: persistence-rule top 20 already up', R_, 98.7, 1, 'pct'),
    ('A.rise_if_up', 'Test A: rise rate of book-months already up', R_, 41.9, 1, 'pct'),
    ('A.rise_if_not_up', 'Test A: rise rate of the other book-months', R_, 8.9, 1, 'pct'),
    ('A.rises_from_up', 'Test A: share of rises from books already up', R_, 27.2, 1, 'pct'),
    ('A.top20.rose.naive', 'Test A: persistence-rule top 20 that rose (check)', R_, 89.2, 1, 'pct'),
    ('A.top20.rose.naive', 'Test A: persistence-rule top 20 that rose (quoted from robustness_part_a_orig.json)', R_, 89.6, 1, 'pct'),
    ('A.next.H_51_70', 'Test A: library picks ranked 51 to 70 that rose', R_, 74.1, 1, 'pct'),
    ('A.next.HW_21_40', 'Test A: library + Wikipedia picks ranked 21 to 40 that rose', R_, 83.1, 1, 'pct'),
    ('A.next.W_not_in_HW50', 'Test A: Wikipedia picks off the combined top 50 that rose', R_, 41.2, 1, 'pct'),
    ('A.early.W', 'Test A early warning (books not yet up): Wikipedia top 20 rose', R_, 31.3, 1, 'pct'),
    ('A.early.W', 'Test A early warning: Wikipedia top 20 rose (Q4)', R_, 31, 0, 'pct'),
    ('A.early.H', 'Test A early warning: library top 20 rose', R_, 59.2, 1, 'pct'),
    ('A.early.HW', 'Test A early warning: library + Wikipedia top 20 rose', R_, 59.9, 1, 'pct'),
    ('A.early.naive', 'Test A early warning: persistence-rule top 20 rose', R_, 19.4, 1, 'pct'),
    ('A.early.base', 'Test A early warning: base rate', R_, 8.9, 1, 'pct'),
    ('A.early.base', 'Test A early warning: base rate (Q4)', R_, 9, 0, 'pct'),
    ('A.early.H_young', "Test A early warning: library list under 12 months old", R_, 55.5, 1, 'pct'),
    ('A.early.H_young', "Test A early warning: library list under 12 months old (Q6)", R_, 55, 0, 'pct'),
    ('A.restricted.rows', 'Test A restricted (24+ months of loans, article already had views): rows', R_, 493677, 0, 'int'),
    ('A.restricted.rank.W', 'Test A restricted: rank, Wikipedia', R_, 0.120, 3, 'num'),
    ('A.restricted.rank.H', 'Test A restricted: rank, library', R_, 0.324, 3, 'num'),
    ('A.restricted.rank.HW', 'Test A restricted: rank, library + Wikipedia', R_, 0.335, 3, 'num'),
    ('A.restricted.top20.W', 'Test A restricted: Wikipedia top 20 rose', R_, 55.7, 1, 'pct'),
    ('A.restricted.top20.H', 'Test A restricted: library top 20 rose', R_, 89.9, 1, 'pct'),
    ('A.restricted.top20.HW', 'Test A restricted: library + Wikipedia top 20 rose', R_, 91.5, 1, 'pct'),
    ('A.restricted.base', 'Test A restricted: base rate', R_, 11.4, 1, 'pct'),
    ('A.gain_age.lt12', 'Test A: gain from Wikipedia, books under 12 months', R_, -0.003, 3, 'num'),
    ('A.gain_age.12_35', 'Test A: gain from Wikipedia, 12 to 35 months', R_, 0.003, 3, 'num'),
    ('A.gain_age.ge36', 'Test A: gain from Wikipedia, 36 months or more', R_, 0.011, 3, 'num'),
    ('A.young.share_rows', 'Test A: rows under 12 months old', R_, 3.1, 1, 'pct'),
    ('A.young.surge', 'Test A: surge rate of those rows', R_, 7.0, 1, 'pct'),
    ('A.older.surge', 'Test A: surge rate of older rows', R_, 2.6, 1, 'pct'),
    ('A.pre.share_rows', "Test A: rows before the book's article had views", R_, 7.0, 1, 'pct'),
    ('A.pre.surge', 'Test A: surge rate of those rows', R_, 4.5, 1, 'pct'),
    ('A.top20.authors.W', 'Test A: distinct authors in the Wikipedia top 20 (about 13)', R_, 13, 0, 'num'),
    ('A.top20.authors.H', 'Test A: distinct authors in the library top 20 (about 18)', R_, 18, 0, 'num'),
    ('A.interval.W_2024_2026', 'Test A: Wikipedia top 20 rose, 2024 to 2026', R_, 59.4, 1, 'pct'),
    ('A.interval.block_lo', 'Test A: 3-month block interval, lower end', R_, 52.9, 1, 'pct'),
    ('A.interval.block_hi', 'Test A: 3-month block interval, upper end', R_, 65.8, 1, 'pct'),
    ('A.interval.binom_lo', 'Test A: binomial interval, lower end', R_, 55.2, 1, 'pct'),
    ('A.interval.binom_hi', 'Test A: binomial interval, upper end', R_, 63.6, 1, 'pct'),
    ('A.months_W_beats_base', 'Test A: months in which the Wikipedia top 20 beat the base rate (of 78)', R_ + '; ' + S_, 78, 0, 'int'),
    ('A.aug.books', 'August 2026 example: books', S_, 7650, 0, 'int'),
    ('A.aug.W_rose', 'August 2026: Wikipedia top 20 that rose', R_ + '; ' + S_, 8, 0, 'int'),
    ('A.aug.W_surged', 'August 2026: Wikipedia top 20 that surged', R_ + '; ' + S_, 6, 0, 'int'),
    ('A.aug.H_rose', 'August 2026: library top 20 that rose', R_ + '; ' + S_, 20, 0, 'int'),
    ('A.aug.H_surged', 'August 2026: library top 20 that surged', R_ + '; ' + S_, 17, 0, 'int'),
    ('A.aug.HW_rose', 'August 2026: library + Wikipedia top 20 that rose', R_ + '; ' + S_, 20, 0, 'int'),
    ('A.aug.HW_surged', 'August 2026: library + Wikipedia top 20 that surged', R_ + '; ' + S_, 18, 0, 'int'),
    ('A.aug.base_rose', 'August 2026: all books that rose', R_ + '; ' + S_, 11.7, 1, 'pct'),
    ('A.aug.base_surge', 'August 2026: all books that surged', R_ + '; ' + S_, 2.4, 1, 'pct'),
    ('A.aug.top_author_books', 'August 2026: Laura Ingalls Wilder books in the Wikipedia top 20', R_ + '; ' + S_, 9, 0, 'int'),
    ('A.aug.top_author_rose', 'August 2026: of those, books that rose', R_ + '; ' + S_, 0, 0, 'int'),
    ('A.aug.other_rose', 'August 2026: other books in the top 20 that rose (of 11)', R_ + '; ' + S_, 8, 0, 'int'),
    ('A.top20.rose.W', 'Test A alert list: Wikipedia top 20 rose', S_, 58.7, 1, 'pct'),
    ('A.top20.rose.W', 'Test A alert list: Wikipedia top 20 rose (Q1)', R_, 59, 0, 'pct'),
    ('A.top20.surged.W', 'Test A alert list: Wikipedia top 20 surged', S_, 39.7, 1, 'pct'),
    ('A.top50.rose.W', 'Test A alert list: Wikipedia top 50 rose', S_, 48.1, 1, 'pct'),
    ('A.top50.surged.W', 'Test A alert list: Wikipedia top 50 surged', S_, 30.1, 1, 'pct'),
    ('A.top20.rose.H', 'Test A alert list: library top 20 rose', S_ + '; ' + R_, 92.1, 1, 'pct'),
    ('A.top20.surged.H', 'Test A alert list: library top 20 surged', S_, 79.9, 1, 'pct'),
    ('A.top50.rose.H', 'Test A alert list: library top 50 rose', S_, 84.8, 1, 'pct'),
    ('A.top50.surged.H', 'Test A alert list: library top 50 surged', S_, 64.7, 1, 'pct'),
    ('A.top20.rose.HW', 'Test A alert list: library + Wikipedia top 20 rose', S_ + '; ' + R_, 93.3, 1, 'pct'),
    ('A.top20.surged.HW', 'Test A alert list: library + Wikipedia top 20 surged', S_, 80.8, 1, 'pct'),
    ('A.top50.rose.HW', 'Test A alert list: library + Wikipedia top 50 rose', S_, 86.4, 1, 'pct'),
    ('A.top50.surged.HW', 'Test A alert list: library + Wikipedia top 50 surged', S_, 65.9, 1, 'pct'),
    ('A.base_rose', 'Test A: all books that rose', S_ + '; ' + R_, 11, 0, 'pct'),
    ('A.base_surge', 'Test A: all books that surged', S_, 3, 0, 'pct'),
    ('A.months_per_extra_book', 'Test A: Wikipedia adds one more hit to the library top 20 every ... months (Q13)', R_, 4, 0, 'num'),
    ('A.mean_next_loans', 'Test A: next-month loans per book (a book averages 22 a month)', S_, 22, 0, 'num'),
    ('A.mean_next_loans', 'Test A: next-month loans per book (MAE 15.77 / WAPE 0.717)', R_, 22.0, 1, 'num'),
    ('A.cap.none.2019_2023.rose', 'Author cap: Wikipedia top 20 rose, no cap, 2019 to 2023', DV, 58.3, 1, 'pct'),
    ('A.cap.2.2019_2023.rose', 'Author cap: two books per author, 2019 to 2023', DV, 56.2, 1, 'pct'),
    ('A.cap.1.2019_2023.rose', 'Author cap: one book per author, 2019 to 2023', DV, 55.9, 1, 'pct'),
    ('A.cap.none.2024_2026.rose', 'Author cap: no cap, 2024 to 2026', DV + '; ' + S_, 59.4, 1, 'pct'),
    ('A.cap.2.2024_2026.rose', 'Author cap: two books per author, 2024 to 2026', DV + '; ' + S_, 57.7, 1, 'pct'),
    ('A.cap.1.2024_2026.rose', 'Author cap: one book per author, 2024 to 2026', DV + '; ' + S_, 55.2, 1, 'pct'),
    ('A.cap.none.all.authors', 'Author cap: distinct authors per top 20, no cap (13 to 20)', DV + '; ' + S_, 13, 0, 'num'),
    ('A.cap.1.all.authors', 'Author cap: distinct authors per top 20, one per author (13 to 20)', DV + '; ' + S_, 20, 0, 'num'),
    ('A.median_Lt_2019', 'Test A: median monthly loans of a book (rows from 2019-01)', R_, 9, 0, 'num'),
    ('B.rows', 'Test B: scored new books', S_, 134970, 0, 'int'),
    ('B.matched_pre.n', "Test B: books whose author's article had views before the first loan", S_, 46318, 0, 'int'),
    ('B.matched_pre.share', 'Test B: share of those books', R_, 34, 0, 'pct'),
    ('B.rank.matched_pre', 'Test B: "author has an article" alone', R_, 0.109, 3, 'num'),
    ('B.rank.v6', "Test B: author's 6-month view level alone", R_, 0.118, 3, 'num'),
    ('B.rank.nfmt', 'Test B: formats borrowed in month 0 alone', R_, 0.585, 3, 'num'),
    ('B.rank.W', 'Test B: Wikipedia model', R_ + '; ' + S_, 0.127, 3, 'num'),
    ('B.rank.L', 'Test B: library model', S_, 0.349, 3, 'num'),
    ('B.rank.LW', 'Test B: library + Wikipedia', S_, 0.372, 3, 'num'),
    ('B.gain.all', 'Test B: gain from Wikipedia, all new books', S_, 0.024, 3, 'num'),
    ('B.matched.rank.v6', 'Test B, authors with an article: view level alone', R_, 0.094, 3, 'num'),
    ('B.matched.rank.W', 'Test B, authors with an article: Wikipedia model', R_ + '; ' + S_, 0.127, 3, 'num'),
    ('B.matched.rank.L', 'Test B, authors with an article: library model', S_, 0.342, 3, 'num'),
    ('B.matched.rank.LW', 'Test B, authors with an article: library + Wikipedia', S_, 0.393, 3, 'num'),
    ('B.gain.matched', 'Test B, authors with an article: gain from Wikipedia', S_, 0.050, 3, 'num'),
    ('B.none.rows', 'Test B, no earlier Seattle work by the author: books', R_, 45303, 0, 'int'),
    ('B.none.W', 'Test B, no earlier work: Wikipedia', R_, 0.090, 3, 'num'),
    ('B.none.L', 'Test B, no earlier work: library', R_, 0.045, 3, 'num'),
    ('B.none.LW', 'Test B, no earlier work: both', R_, 0.101, 3, 'num'),
    ('B.none.gain', 'Test B, no earlier work: gain from Wikipedia', R_, 0.056, 3, 'num'),
    ('B.some.W', 'Test B, earlier works: Wikipedia', R_, 0.115, 3, 'num'),
    ('B.some.L', 'Test B, earlier works: library', R_, 0.423, 3, 'num'),
    ('B.some.LW', 'Test B, earlier works: both', R_, 0.443, 3, 'num'),
    ('B.some.gain', 'Test B, earlier works: gain from Wikipedia', R_, 0.020, 3, 'num'),
    ('B.gain_year.min', 'Test B: gain from Wikipedia by year, lowest', R_, 0.020, 3, 'num'),
    ('B.gain_year.max', 'Test B: gain from Wikipedia by year, highest', R_, 0.034, 3, 'num'),
    ('B.no_top1.W', 'Test B: Wikipedia without the top 1% most-viewed authors', R_, 0.128, 3, 'num'),
    ('B.rank.Lfmt', 'Test B: library model with the format flags', R_ + '; ' + S_, 0.611, 3, 'num'),
    ('B.rank.LWfmt', 'Test B: library + Wikipedia with the format flags', R_ + '; ' + S_, 0.618, 3, 'num'),
    ('B.fmt_gain', 'Test B: gain from Wikipedia with the format flags', R_, 0.007, 3, 'num'),
    ('D.in_test_a', 'Test D: rows that are Test A books', R_, 48.9, 1, 'pct'),
    ('D.W_testA_min', 'Test D: Wikipedia top 20 that are Test A books, lowest format (99.7% to 100%)', R_, 99.7, 1, 'pct'),
    ('D.W_testA_max', 'Test D: Wikipedia top 20 that are Test A books, highest format (99.7% to 100%)', R_, 100, 0, 'pct'),
    ('D.top20_testA.HW.print.2019_2026', 'Test D: library + Wikipedia top 20 that are Test A books, print', R_, 40, 0, 'pct'),
    ('D.top20_testA.HW.ebook.2019_2026', 'Test D: same, ebook', R_, 63, 0, 'pct'),
    ('D.top20_testA.HW.audiobook.2019_2026', 'Test D: same, audiobook', R_, 69, 0, 'pct'),
    ('D.top20.naive.print.2024_2026', 'Test D: persistence-rule top 20 rose, print, 2024 to 2026', R_, 79.2, 1, 'pct'),
    ('D.top20.naive.ebook.2024_2026', 'Test D: persistence rule, ebook, 2024 to 2026', R_, 90.6, 1, 'pct'),
    ('D.top20.naive.ebook.2024_2026', 'Test D: persistence rule, ebook, 2024 to 2026 (Q4)', R_, 91, 0, 'pct'),
    ('D.top20.naive.audiobook.2024_2026', 'Test D: persistence rule, audiobook, 2024 to 2026', R_, 91.0, 1, 'pct'),
    ('D.top20.naive.audiobook.2024_2026', 'Test D: persistence rule, audiobook, 2024 to 2026 (Q4)', R_, 91, 0, 'pct'),
    ('D.top20.naive.all.2019_2026', 'Test D: persistence rule, all formats, 2019 to 2026 (from wiki_led_test_d.json)', R_, 84.1, 1, 'pct'),
    ('D.early.W.all', 'Test D early warning: Wikipedia top 20 rose', S_, 23.3, 1, 'pct'),
    ('D.early.naive.all', 'Test D early warning: repeat-last-month top 20 rose', S_, 15.7, 1, 'pct'),
    ('D.early.H.all', 'Test D early warning: library top 20 rose', S_, 43.7, 1, 'pct'),
    ('E.main_rows', 'Test E: main rows', R_, 433424, 0, 'int'),
    ('E.feat_rows', 'Test E: main rows with stored Wikipedia views', R_, 88752, 0, 'int'),
    ('E.feat_share', 'Test E: share of main rows with stored views', R_ + '; ' + S_, 20.5, 1, 'pct'),
    ('E.feat.rank.E1_W', 'Test E rows with views: Wikipedia alone, retrained', R_, 0.055, 3, 'num'),
    ('E.feat.rank.E2_W', 'Test E rows with views: Wikipedia alone, Seattle model', R_, 0.053, 3, 'num'),
    ('E.feat.rank.E1_H', 'Test E rows with views: listening history', R_, 0.364, 3, 'num'),
    ('E.feat.rank.E1_HW', 'Test E rows with views: history + Wikipedia', R_, 0.356, 3, 'num'),
    ('E.base_rose.main', 'Test E: all books that rose', S_, 7.0, 1, 'pct'),
    ('E.main.rank.E1_W', 'Test E: Wikipedia only, retrained, rank', S_, 0.028, 3, 'num'),
    ('E.main.top20.E1_W', 'Test E: Wikipedia only, retrained, top 20', S_, 8.8, 1, 'pct'),
    ('E.main.rank.E2_W', 'Test E: Wikipedia only, Seattle model, rank', S_, 0.016, 3, 'num'),
    ('E.main.top20.E2_W', 'Test E: Wikipedia only, Seattle model, top 20', S_, 11.7, 1, 'pct'),
    ('E.main.rank.E1_H', 'Test E: listening history, retrained, rank', S_, 0.349, 3, 'num'),
    ('E.main.top20.E1_H', 'Test E: listening history, retrained, top 20', S_, 80.4, 1, 'pct'),
    ('E.main.rank.E2_H', 'Test E: listening history, Seattle model, rank', S_, 0.278, 3, 'num'),
    ('E.main.top20.E2_H', 'Test E: listening history, Seattle model, top 20', S_, 68.9, 1, 'pct'),
    ('E.main.rank.E1_HW', 'Test E: history + Wikipedia, retrained, rank', S_, 0.348, 3, 'num'),
    ('E.main.top20.E1_HW', 'Test E: history + Wikipedia, retrained, top 20', S_, 80.4, 1, 'pct'),
    ('E.main.rank.E2_HW', 'Test E: history + Wikipedia, Seattle model, rank', S_, 0.284, 3, 'num'),
    ('E.main.top20.E2_HW', 'Test E: history + Wikipedia, Seattle model, top 20', S_, 68.7, 1, 'pct'),
    ('E.main.rank.naive', 'Test E: repeat last month, rank', S_, 0.349, 3, 'num'),
    ('E.naive.top20.main.2019_2026', 'Test E: persistence-rule top 20 rose (main rows)', S_, 77.5, 1, 'pct'),
    ('E.median_Lt_2019', 'Test E: median monthly listens of a book (rows from 2019-01)', R_, 125, 0, 'num'),
    ('E.scale_ratio', 'Test E against Test A: listening counts about 14 times larger', R_, 14, 0, 'num'),
    ('L.top20_authors', 'Live list: distinct authors in the top 20', R_, 17, 0, 'int'),
    ('L.top50_authors', 'Live list: distinct authors in the top 50', R_, 35, 0, 'int'),
    ('L.dillard', 'Live list: Annie Dillard books in the top 20', R_, 3, 0, 'int'),
    ('L.child', 'Live list: Lee Child books in the top 20', R_, 2, 0, 'int'),
    ('G.settings', 'Public repo: settings record first published', R_, '17:01:20', 0, 'time'),
    ('G.a', 'Public repo: addendum a first published', R_, '17:01:20', 0, 'time'),
    ('G.b', 'Public repo: addendum b first published', R_, '17:01:20', 0, 'time'),
    ('G.c', 'Public repo: addendum c first published', R_, '17:41:05', 0, 'time'),
    ('G.d', 'Public repo: addendum d first published', R_, '17:41:05', 0, 'time'),
    ('G.e', 'Public repo: addendum e first published', R_, '20:35:55', 0, 'time'),
]
# the summary's Test D table (top 20 that rose, 2019-2026 by format; library + Wikipedia also 2024-2026)
for fmt, base, w, h, hw, hw24 in (('print', 13.3, 44.0, 87.5, 87.2, 85.0), ('ebook', 10.6, 50.4, 85.8, 88.0, 92.1),
                                  ('audiobook', 11.0, 47.8, 88.7, 88.6, 92.7), ('all', 11.6, 47.4, 87.3, 87.9, 89.9)):
    EXP += [(f'D.base.{fmt}', f'Test D table: all books that rose, {fmt}', S_, base, 1, 'pct'),
            (f'D.top20.W.{fmt}.2019_2026', f'Test D table: Wikipedia only, {fmt}', S_, w, 1, 'pct'),
            (f'D.top20.H.{fmt}.2019_2026', f'Test D table: library record, {fmt}', S_ + ('; ' + R_ if fmt in ('print', 'all') else ''), h, 1, 'pct'),
            (f'D.top20.HW.{fmt}.2019_2026', f'Test D table: library + Wikipedia, {fmt}', S_ + ('; ' + R_ if fmt in ('print', 'all') else ''), hw, 1, 'pct'),
            (f'D.top20.HW.{fmt}.2024_2026', f'Test D table: library + Wikipedia, {fmt}, 2024 to 2026', S_, hw24, 1, 'pct')]


def shown(x, dec, unit):
    return x * 100 if unit == 'pct' else x


def compare(e):
    key, what, src, q, dec, unit = e
    v = V.get(key)
    row = dict(key=key, what=what, quoted_in=src, quoted=q, decimals=dec, unit=unit, value=v, value_corrected=VC.get(key))
    if v is None:
        row.update(status='not computed', why='input missing')
        return row
    if unit == 'time':
        row.update(status='matches' if v == q else 'differs', difference=None, why='' if v == q else 'different commit time')
        return row
    x = shown(v, dec, unit)
    ok = round(x) == q if unit == 'int' else float(f'{x:.{dec}f}') == float(f'{q:.{dec}f}')
    row.update(status='matches' if ok else 'differs', difference=x - q, why='')
    if not ok:
        t = TIES.get(key)
        half = 0.5 * 10 ** -dec
        logged = V.get(key.replace('A.cap.', 'A.cap_as_logged.')) if key.startswith('A.cap.') and key.endswith('.rose') else None
        once = Decimal(f'{x:.{dec + 1}f}').quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP)
        cut = Decimal(f'{x:.{dec + 1}f}').quantize(Decimal(1).scaleb(-dec), rounding='ROUND_DOWN')
        if t and shown(t['lowest'], dec, unit) - half <= q <= shown(t['highest'], dec, unit) + half and t['lowest'] < t['highest']:
            row['why'] = (f"order of tied scores: any order gives {shown(t['lowest'], dec, unit):.{dec + 1}f} to "
                          f"{shown(t['highest'], dec, unit):.{dec + 1}f}, a random order {shown(t['random_ties'], dec, unit):.{dec + 1}f}")
        elif logged is not None and float(f'{shown(logged, dec, unit):.{dec}f}') == q:
            row['why'] = (f"the 17:07 check left ties in no fixed order and its cap dropped books without an author article; "
                          f"done that way: {shown(logged, dec, unit):.{dec + 1}f}")
        elif float(once) == q:
            row['why'] = f'rounded twice: {x:.{dec + 2}f} printed as {x:.{dec + 1}f}, then rounded up'
        elif float(cut) == q:
            row['why'] = f'cut, not rounded: {x:.{dec + 1}f} written as {q}'
        else:
            row['why'] = 'not explained by ties or rounding'
    return row


COMP = [compare(e) for e in EXP]
n_match = sum(r['status'] == 'matches' for r in COMP)
n_diff = sum(r['status'] == 'differs' for r in COMP)
n_unexpl = sum(r['status'] == 'differs' and r['why'].startswith('not explained') for r in COMP)
log('compared', len(COMP), 'matches', n_match, 'differs', n_diff, 'unexplained', n_unexpl)

# ---------------------------------------------------------------- JSON
PEAK = peak_gb()


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o):
        return None
    return o


res = dict(script='code/main_study/wiki_led/15_summary_checks.py', written=time.strftime('%Y-%m-%d %H:%M:%S %z'),
           rules=dict(rose='stored D >= ln 1.5 (Tests D and E: stored rose column)', top_k='k highest scores of a month (Test D: of a format and month), '
                      'ties broken by work_id ascending (Test E: book_id)', hit_rate='mean of the monthly shares (Test D: of the format-month shares)',
                      rank='Spearman within month (Tests A and E; months with more than 20 rows and more than one score value) or within '
                      'first-month year (Test B), averaged', tie_range='lowest and highest hit rate over all orders of the tied scores at the '
                      'cut-off, and the expected value under a random order', corrected='the _c files of addendum e (correction A1); in them '
                      'the weeks before an article had views are missing, so rows "before the article had views" are those before the first '
                      'origin month at which the book page has views (pre_first); on the original files the review used lvl4 at its floor '
                      '(pre_floor)'),
           inputs=INPUTS, corrected_test_d_available=HAS_D_C, values_original=V, values_corrected=VC, tie_ranges_original=TIES,
           tie_ranges_corrected=TIES_C, stored_other_tie_order=STORED, examples=EXAMPLES, public_commits=GIT, comparisons=COMP,
           summary=dict(compared=len(COMP), matches=n_match, differs=n_diff, differs_not_explained=n_unexpl),
           peak_memory_gb=round(PEAK, 3), runtime_s=round(time.time() - T0, 1))
OUT_JSON.write_text(json.dumps(clean(res), indent=1, ensure_ascii=False))

# ---------------------------------------------------------------- Markdown
def pc(x, d=1):
    return '' if x is None else f'{100 * x:.{d}f}%'


def nm(x, d=3):
    return '' if x is None else f'{x:.{d}f}'


def qv(r):
    u, q = r['unit'], r['quoted']
    return f'{q}%' if u == 'pct' else f'{q:,}' if u == 'int' else str(q)


def cv(r):
    u, d, v = r['unit'], r['decimals'], r['value']
    if u == 'pct':
        return f'{100 * v:.{d + 2}f}%'
    if u == 'int':
        return f'{v:,.0f}'
    if u == 'time':
        return str(v)
    return f'{v:.{d + 2}f}'


def dv(r):
    if r['difference'] is None:
        return ''
    u, d = r['unit'], r['decimals']
    return f"{r['difference']:+.{d + 2}f}" + (' points' if u == 'pct' else '')


md = []
w = md.append
w('# Summary checks for the Wikipedia-led results\n')
w(f"Khant Phyo Wai, student ID 01323050. Written by `code/main_study/wiki_led/15_summary_checks.py` on {time.strftime('%d %B %Y at %H:%M')} (+07); "
  f"all numbers are in `data/reports/wiki_led_summary_checks.json`.\n")
w('## What this is\n')
w('One saved script for the numbers that the results summary (`paper/Wikipedia_Led_Results_2026-10-20_1924.md`) and the examiner review '
  '(`data/reports/wiki_led_examiner_review.md`) quote without a script behind them: the "different books" figures, the August 2026 example, '
  'a new June to July 2026 example, the persistence rule in Tests A, D and E, Test B\'s one-column baselines and the split by earlier Seattle '
  'books, the author-cap check of `prereg/DEVIATIONS.md` (17:07), and every "(check)" number of the review\'s appendix. It reads stored '
  'predictions only, fits no model and was written after all results were seen, so it is descriptive and changes no decision. '
  'Corrected files (addendum e) are used where they exist: Test A' + (' and Test D' if HAS_D_C else '') + '. '
  + ('' if HAS_D_C else 'Test D has no corrected predictions yet (`test_d_preds_c.parquet` is missing); rerun this script when it exists. ')
  + 'Tests B and E have no corrected files.\n')
w('**Rules** (as in the review\'s appendix). A book "rose" when next month\'s loans are at least 1.5 times the median of the last 6 months '
  '(stored D at least ln 1.5). A month\'s top k are its k highest scores, ties broken by work_id (book_id in Test E). A hit rate is the mean of the '
  'monthly shares (Test D: of the format-month shares). Rank is Spearman within month, or within first-month year in Test B, averaged. For each '
  'top-k hit rate the JSON also holds the lowest and highest value over all orders of tied scores and the value expected under a random order.\n')
w('## Result\n')
w(f"{len(COMP)} quoted numbers were compared (review, results summary, DEVIATIONS): {n_match} match after rounding to the printed decimals and "
  f"{n_diff} differ. " + ('Every difference comes from the order of tied scores, from how the quoted text rounded, or (author cap) from leaving '
                          'out books without an author article; none changes what the summary or the review says. '
                          if n_unexpl == 0 else f'{n_unexpl} of them are not explained by ties or rounding (see the table). '))
GROUPS = {'A': 'Test A', 'B': 'Test B', 'D': 'Test D', 'E': 'Test E', 'L': 'live list', 'G': 'public timestamps'}
w('By group, matches of compared: ' + '; '.join(
    f"{lab} {sum(r['status'] == 'matches' for r in COMP if r['key'][0] == g)} of {sum(r['key'][0] == g for r in COMP)}" for g, lab in GROUPS.items())
  + f". Peak memory {PEAK:.2f} GB, run time {time.time() - T0:.0f} s.\n")
w('## Main numbers (original files, ties by id)\n')
w(f"- **Different books (Test A).** {pc(V['A.overlap.share'])} of Wikipedia's monthly top 20 are not on the library model's top 50; {pc(V['A.overlap.rose_monthly'])} "
  f"of those rose and {pc(V['A.overlap.surged'])} surged (base {pc(V['A.base_rose'])} and {pc(V['A.base_surge'])}). The library's next picks, ranked 51 to 70, rose "
  f"{pc(V['A.next.H_51_70'])}; library + Wikipedia picks ranked 21 to 40 rose {pc(V['A.next.HW_21_40'])}; Wikipedia picks off the combined top 50 rose "
  f"{pc(V['A.next.W_not_in_HW50'])}.\n"
  f"- **Already up in the origin month (Test A top 20).** Library {pc(V['A.top20.already_up.H'])}, library + Wikipedia {pc(V['A.top20.already_up.HW'])}, "
  f"Wikipedia {pc(V['A.top20.already_up.W'])}, persistence rule {pc(V['A.top20.already_up.naive'])}. Books already up rose next month {pc(V['A.rise_if_up'])} of the time, "
  f"the others {pc(V['A.rise_if_not_up'])}; {pc(V['A.rises_from_up'])} of all rises came from books already up.\n"
  f"- **Persistence rule, top 20 that rose.** Test A {pc(V['A.top20.rose.naive'])}; Test D 2024 to 2026: print {pc(V['D.top20.naive.print.2024_2026'])}, ebook "
  f"{pc(V['D.top20.naive.ebook.2024_2026'])}, audiobook {pc(V['D.top20.naive.audiobook.2024_2026'])}; Test D all formats 2019 to 2026 {pc(V['D.top20.naive.all.2019_2026'])}; "
  f"Test E main rows {pc(V['E.naive.top20.main.2019_2026'])} (2024 to 2026: {pc(V['E.naive.top20.main.2024_2026'])}).\n"
  f"- **Early warning (Test A, books not yet up).** Top 20 that rose: Wikipedia {pc(V['A.early.W'])}, library {pc(V['A.early.H'])}, library + Wikipedia "
  f"{pc(V['A.early.HW'])}, persistence rule {pc(V['A.early.naive'])}, base {pc(V['A.early.base'])}; {pc(V['A.early.H_young'])} of the library's early list are books under 12 months old.\n"
  f"- **Restricted Test A rows** (24 or more months of loans, article already had views; {V['A.restricted.rows']:,} rows). Rank: Wikipedia {nm(V['A.restricted.rank.W'])}, "
  f"library {nm(V['A.restricted.rank.H'])}, library + Wikipedia {nm(V['A.restricted.rank.HW'])}; top 20 rose {pc(V['A.restricted.top20.W'])}, {pc(V['A.restricted.top20.H'])} "
  f"and {pc(V['A.restricted.top20.HW'])} against {pc(V['A.restricted.base'])}.\n"
  f"- **Test B, one column alone.** \"Author has an article\" {nm(V['B.rank.matched_pre'])}, the author's 6-month view level {nm(V['B.rank.v6'])}, formats borrowed in month 0 "
  f"{nm(V['B.rank.nfmt'])}, the Wikipedia model {nm(V['B.rank.W'])}; among authors with an article, view level {nm(V['B.matched.rank.v6'])} and model {nm(V['B.matched.rank.W'])}.\n"
  f"- **Test B, by earlier Seattle works.** None ({V['B.none.rows']:,} books): Wikipedia {nm(V['B.none.W'])}, library {nm(V['B.none.L'])}, both {nm(V['B.none.LW'])}, gain "
  f"{V['B.none.gain']:+.3f}. Some ({V['B.some.rows']:,} books): {nm(V['B.some.W'])}, {nm(V['B.some.L'])}, {nm(V['B.some.LW'])}, gain {V['B.some.gain']:+.3f}.\n"
  f"- **Coverage.** Test D rows that are Test A books {pc(V['D.in_test_a'])}; Test E main rows with stored views {pc(V['E.feat_share'])} ({V['E.feat_rows']:,} of "
  f"{V['E.main_rows']:,}), where Wikipedia alone ranks at {nm(V['E.feat.rank.E1_W'])} (retrained) and {nm(V['E.feat.rank.E2_W'])} (Seattle model), history at "
  f"{nm(V['E.feat.rank.E1_H'])} and history + Wikipedia at {nm(V['E.feat.rank.E1_HW'])}.\n")
w('## Numbers that differ\n')
w('Difference = this script minus the quoted value, in the printed unit.\n')
w('| Number | Quoted in | Quoted | This script | Difference | Why |')
w('| --- | --- | ---: | ---: | ---: | --- |')
for r in COMP:
    if r['status'] != 'matches':
        w(f"| {r['what']} | {r['quoted_in']} | {qv(r)} | {cv(r)} | {dv(r)} | {r['why']} |")
w('')

# persistence rule
w('## Persistence rule: share of the top 20 that rose\n')
w('The rule ranks books by this month\'s loans against their own 6-month median; it uses no model and no Wikipedia. "Random order" is the value '
  'expected when tied scores are ordered at random; the stored robustness files drew one random order and compare the threshold exactly, '
  'the stored test reports used the order of an unstable sort.\n')
w('| Test and rows | Period | Ties by id | Random order | Range over tie orders | Stored value |')
w('| --- | --- | ---: | ---: | --- | --- |')


def prow(label, per, key, ties=TIES):
    t = ties.get(key)
    if not t:
        return
    st = '; '.join(f'{pc(v)} in `{f}` ({how})' for f, how, v in STORED.get(key, []))
    w(f"| {label} | {per} | {pc(t['rate'])} | {pc(t['random_ties'])} | {pc(t['lowest'])} to {pc(t['highest'])} | {st} |")


prow('Test A, all rows', '2019 to 2026', 'A.top20.rose.naive')
for fmt in ('print', 'ebook', 'audiobook', 'all'):
    for per in D_PERIODS:
        prow(f'Test D, {fmt}' + (' formats' if fmt == 'all' else ''), per.replace('_', ' to '), f'D.top20.naive.{fmt}.{per}')
for rows_name, lab in (('main', 'main rows'), ('all', 'all rows')):
    for per in D_PERIODS:
        prow(f'Test E, {lab}', per.replace('_', ' to '), f'E.naive.top20.{rows_name}.{per}')
prow('Test E, main rows with stored views (new)', '2019 to 2026', 'E.feat.top20.naive')
w('\nTest A\'s persistence rule uses library loans only, so the corrected files give the same value '
  f"({pc(VC.get('A.top20.rose.naive'))})" + (f"; so do Test D's corrected files ({pc(VC.get('D.top20.naive.all.2019_2026'))} for all formats, 2019 to 2026)" if HAS_D_C else '') + '.\n')

# corrected against original
w('## Corrected files against the original ones (Test A' + (', Test D' if HAS_D_C else '') + ')\n')
w('Addendum e, correction A1: weeks before an article had views are missing, not zero. Only the Wikipedia models change; the library model and '
  'the persistence rule do not (unchanged rows are left out here; every number is in the JSON). In the corrected files the rows "before the '
  'article had views" are those before the first month at which the '
  f"book's own page has views; on the original files this marks {pc(V['A.pre.rule_first_share_rows'])} of rows against {pc(V['A.pre.share_rows'])} "
  f"for the review's rule (lvl4 at its floor), and the two rules agree on {pc(V['A.pre.rules_agree'], 2)} of rows. The restricted rows below use "
  + (f"the first-views rule on both files ({V['A.restricted_first.rows']:,} rows in each).\n"
     if V['A.restricted_first.rows'] == VC.get('A.restricted_first.rows') else
     f"the first-views rule on both files ({V['A.restricted_first.rows']:,} and {VC.get('A.restricted_first.rows', 0):,} rows).\n"))
w('| Number | Original | Corrected | Change |')
w('| --- | ---: | ---: | ---: |')
CMP_KEYS = [('A.overlap.share', "Wikipedia's top 20 not on the library top 50", 'pct'), ('A.overlap.rose_monthly', 'of those, rose', 'pct'),
            ('A.top20.rose.W', 'Wikipedia top 20 rose', 'pct'), ('A.top50.rose.W', 'Wikipedia top 50 rose', 'pct'),
            ('A.top20.rose.HW', 'Library + Wikipedia top 20 rose', 'pct'), ('A.top20.already_up.W', 'Wikipedia top 20 already up', 'pct'),
            ('A.next.W_not_in_HW50', 'Wikipedia picks off the combined top 50, rose', 'pct'), ('A.early.W', 'Early warning: Wikipedia top 20 rose', 'pct'),
            ('A.early.HW', 'Early warning: library + Wikipedia top 20 rose', 'pct'),
            ('A.restricted_first.rank.W', 'Restricted rows (first-views rule on both): rank, Wikipedia', 'num'),
            ('A.restricted_first.top20.W', 'Restricted rows (first-views rule on both): Wikipedia top 20 rose', 'pct'),
            ('A.gain_age.lt12', 'Gain from Wikipedia, books under 12 months', 'num'), ('A.interval.W_2024_2026', 'Wikipedia top 20 rose, 2024 to 2026', 'pct'),
            ('A.interval.block_lo', 'block interval, lower end', 'pct'), ('A.interval.block_hi', 'block interval, upper end', 'pct'),
            ('A.months_W_beats_base', 'Months above the base rate (of 78)', 'int'), ('A.cap.2.2024_2026.rose', 'Author cap, 2024 to 2026: two per author', 'pct'),
            ('A.cap.1.2024_2026.rose', 'Author cap, 2024 to 2026: one per author', 'pct')]
if HAS_D_C:
    CMP_KEYS += [(f'D.top20.{m}.all.2019_2026', f'Test D, all formats: {lab} top 20 rose', 'pct') for m, lab in (('W', 'Wikipedia'), ('HW', 'library + Wikipedia'))]
    CMP_KEYS += [(f'D.top20.HW.{f}.2024_2026', f'Test D, {f}, 2024 to 2026: library + Wikipedia', 'pct') for f in ('print', 'ebook', 'audiobook')]


def f3(x, kind):
    if x is None:
        return ''
    return {'pct': pc(x), 'num': nm(x, 4), 'num1': nm(x, 1), 'int': f'{x:,.0f}'}[kind]


def change(a, c, kind):
    if a is None or c is None:
        return ''
    s = {'pct': f'{100 * (c - a):+.1f} points', 'int': f'{c - a:+,.0f}', 'num1': f'{c - a:+.1f}', 'num': f'{c - a:+.4f}'}[kind]
    return re.sub(r'^[+-](0(?:\.0+)?)(?=$| )', r'\1', s)              # no sign on a change that rounds to zero


for k, lab, kind in CMP_KEYS:
    a, c = V.get(k), VC.get(k)
    w(f'| {lab} | {f3(a, kind)} | {f3(c, kind)} | {change(a, c, kind)} |')
w('')


# examples
def ex_md(title, key, new):
    e, ec = EXAMPLES['orig'][key], EXAMPLES.get('_c', {}).get(key)
    w(f'## {title}\n')
    if new:
        w('No earlier text (results summary, review, DEVIATIONS, live-list README, reports) gives this example; the numbers are new.\n')
    w(f"Origin {e['origin']}, predicting {e['target']}; {e['books']:,} books, of which {pc(e['base_rose'])} rose and {pc(e['base_surge'])} surged. "
      f"Top 20 that rose (surged): Wikipedia {e['W.top20.rose']} ({e['W.top20.surged']}), library {e['H.top20.rose']} ({e['H.top20.surged']}), "
      f"library + Wikipedia {e['HW.top20.rose']} ({e['HW.top20.surged']}). Top 50: Wikipedia {e['W.top50.rose']} rose ({pc(e['W.top50.rose'] / 50, 0)}) and "
      f"{e['W.top50.surged']} surged ({pc(e['W.top50.surged'] / 50, 0)}); library {e['H.top50.rose']} and {e['H.top50.surged']}; library + Wikipedia "
      f"{e['HW.top50.rose']} and {e['HW.top50.surged']}. The author with most books in Wikipedia's top 20 is {e['top_author']} "
      f"({e['top_author_books']} books, {e['top_author_rose']} rose); {e['other_rose']} of the other {e['other_books']} rose. "
      f"{e['W_up_at_origin']} of Wikipedia's 20 were already up at the origin, and {e['W_H_top20_shared']} are also in the library's top 20.\n")
    if ec:
        same = len({r['work_id'] for r in ec['W_top20']} & {r['work_id'] for r in e['W_top20']})
        w(f"Corrected files: Wikipedia {ec['W.top20.rose']} rose ({ec['W.top20.surged']} surged) in the top 20 and {ec['W.top50.rose']} "
          f"({ec['W.top50.surged']}) in the top 50; {same} of the 20 books are the same; library + Wikipedia {ec['HW.top20.rose']} ({ec['HW.top20.surged']}).\n")
    w(f"Wikipedia's top 20 (original files). Loans in {e['origin']}, median of the 6 months to {e['origin']}, loans in {e['target']}:\n")
    w(f"| # | Book | Author | {e['origin']} | 6-month median | {e['target']} | Rose | Surged |")
    w('| ---: | --- | --- | ---: | ---: | ---: | --- | --- |')
    for r in e['W_top20']:
        w(f"| {r['rank']} | {r['title']} | {r['author']} | {r['loans_origin']} | {r['median6']:g} | {r['loans_next']} | "
          f"{'yes' if r['rose'] else 'no'} | {'yes' if r['surged'] else 'no'} |")
    w('')


ex_md('August 2026 example (origin July 2026)', 'august_2026', False)
ex_md('June to July 2026 example (origin June 2026)', 'june_july_2026', True)

# author cap
w('## Author cap on the Wikipedia-only list (DEVIATIONS 17:07)\n')
w("At most one or two books per author (author = the author's article), then each month's top 20 that rose. Main rule: ties by work_id, and a "
  "book without an author article counts as its own author. \"As logged\" repeats the 17:07 check exactly: each period's rows sorted by score "
  "alone with pandas' default sort, which keeps no fixed order for tied scores, and a cap that leaves out books without an author article. It "
  "reproduces all six logged numbers; the gaps to the main rule (up to 0.6 points) come from those two choices, and the cap lowers the share "
  "under both.\n")
LOGGED = {'none': (58.3, 59.4), '2': (56.2, 57.7), '1': (55.9, 55.2)}
w('| Cap | Main rule: 2019 to 2023, 2024 to 2026 | As logged | Logged in DEVIATIONS | Distinct authors per list, 2019 to 2026 | Corrected files, main rule |')
w('| --- | --- | --- | --- | ---: | --- |')
for cap, lab in (('none', 'none'), ('2', 'two per author'), ('1', 'one per author')):
    w(f"| {lab} | {pc(V[f'A.cap.{cap}.2019_2023.rose'])}, {pc(V[f'A.cap.{cap}.2024_2026.rose'])} | "
      f"{pc(V.get(f'A.cap_as_logged.{cap}.2019_2023.rose'))}, {pc(V.get(f'A.cap_as_logged.{cap}.2024_2026.rose'))} | "
      f"{LOGGED[cap][0]}%, {LOGGED[cap][1]}% | {nm(V[f'A.cap.{cap}.all.authors'], 1)} | "
      f"{pc(VC.get(f'A.cap.{cap}.2019_2023.rose'))}, {pc(VC.get(f'A.cap.{cap}.2024_2026.rose'))} |")
w('')

# other new numbers
w('## Other numbers worth knowing (not quoted before)\n')
w(f"- Test A: library picks ranked 21 to 40 rose {pc(V['A.next.H_21_40'])}; Wikipedia's off-list picks average {nm(V['A.overlap.books_per_month'], 1)} books a month; "
  f"pooled over months, {pc(V['A.overlap.rose_pooled'])} of them rose (the {pc(V['A.overlap.rose_monthly'])} above is the mean of monthly shares).\n"
  f"- Test A: the no-fitting Wikipedia rule's top 20 rose {pc(V['A.top20.rose.Wrule'])} (corrected files: {pc(VC.get('A.top20.rose.Wrule'))}).\n"
  f"- Test E, main rows with stored Wikipedia views: the persistence rule's top 20 rose {pc(V['E.feat.top20.naive'])}, history + Wikipedia {pc(V['E.feat.top20.E1_HW'])}, "
  f"Wikipedia alone {pc(V['E.feat.top20.E1_W'])}.\n"
  f"- Test D, 2024 to 2026: {pc(V['D.top20_testA.W.audiobook.2024_2026'])} of Wikipedia's audiobook top 20 are Test A books, a little below the 99.7% to 100% of 2019 to 2026.\n"
  f"- Test B gain from Wikipedia by year: " + ', '.join(f'{y} {g:+.3f}' for y, g in V['B.gain_year'].items()) + '.\n')

# not recomputable
w('## Not recomputable from stored predictions\n')
w('- "The strongest features are the author\'s and the book\'s views relative to normal" (results summary, Test A). The Test A models were not '
  'saved, so their feature importances need a refit; the stored importance files belong to the improvement-round models. This script fits no model.\n'
  '- The two-months-ahead comparison (library 0.336 against Wikipedia 0.138, 2019 to 2023; review, Threat 9 and Q3) comes from '
  '`wiki_led_test_a_horizon_2019_2023.csv`, an exploratory refit at another horizon with no script. It needs new model fits.\n'
  '- Numbers that the review or the summary take from files written by other scripts (for example `wiki_led_test_a.json`, `wiki_led_test_b.json`, '
  '`wiki_led_test_d.json`, the robustness files) already have a source and are repeated here only where they show the tie rule.\n')
w('## Inputs\n')
w('Read only: ' + ', '.join(f'`{k}` ({v})' for k, v in INPUTS.items()) + (f'; `git log` of `~/cmkl-thesis-research`.' if GIT else '.') + '\n')
OUT_MD.write_text('\n'.join(md))
log('wrote', OUT_JSON.name, 'and', OUT_MD.name, f'peak memory {PEAK:.2f} GB')
if PEAK > MEM_LIMIT_GB:
    log(f'WARNING: peak memory above {MEM_LIMIT_GB} GB')
