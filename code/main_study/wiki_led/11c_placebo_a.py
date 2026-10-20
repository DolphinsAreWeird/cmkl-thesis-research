# 11c. Placebo check of Test A, CORRECTED RERUN (addendum e, prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json):
# 11_placebo_a.py on the corrected Test A rows and features (correction A1: weeks before an article's first week with views are missing,
# made by 10c_test_a.py) and with the donors of correction P1.  The original run and its files stay on file.
# P1 (donors without heavy reuse): books are sorted by their matching value as in addendum b (median lvl4 over origins 2016-03 to
# 2018-12, else over the book's first 12 origins with a value), ties in the matching value broken by a fixed random order
# (numpy default_rng(20261020).permutation over the work ids in ascending order).  Each book in turn, in that sorted order, takes as donor
# the nearest book in the order with a different author key: one step down, then one step up, then two steps down, and so on; a donor may
# serve at most 3 books (a book that already serves 3 is skipped).  Choices the addendum left open, fixed here before the run:
#   - recipients are processed in the sorted order; a book can be both donor and recipient;
#   - the "author key" is the one of 11_placebo_a.py (the author article, else 'creator:' + the creator string);
#   - a donor must also have a different book article than the recipient (4 articles are shared by works with different creator strings,
#     for example two editions of one book with different co-author lists; without this rule such a work could be given its own article).
#     The number of recipients this rule changes is counted and written to the result file;
#   - a book with no book-article matching value is matched on its author-article value in a second pass over the same rule, as in 11.
# Everything else (rows, features swapped at the same origin, walk-forward by year, LightGBM settings and seed, scoring) is as in 11_placebo_a.py.
# Output: data/db/wiki_led/placebo_a_preds_c.parquet, data/reports/wiki_led_placebo_a_c.json
#   full run: bash jobs/bg.sh wl_placebo_a_c main_study/wiki_led/11c_placebo_a.py      (from handoff/)
#
# Original header of 11_placebo_a.py:
# 11. Placebo check of Test A: each book gets the Wikipedia pages (book and author) of a different book with similar traffic.
# Settings: prereg/addenda_wiki_led/2026-10-20_b_placebo_test_a.json (read-only; SHA-256 in prereg/README.md).
# Clarifications: "different author" = a different author_article, or a different creator when either book has no author
# article; a book with no book-article level at all is matched on its author-article level; matching value = median lvl4
# over origins 2016-03 to 2018-12, else over the book's first 12 origins with a value.
import sys, os, json, time, pathlib, hashlib, resource
from collections import Counter
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
ADD = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_b_placebo_test_a.json'
assert hashlib.sha256(ADD.read_bytes()).hexdigest() == '9589a400807417bb7f8c3e381ab0c0bebba6e55af5c14aeee5026809887aad27'
ADD_E = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_e_corrections_robustness.json'
assert hashlib.sha256(ADD_E.read_bytes()).hexdigest() == '36f3605286b51b8123d791c1d59a7dc89356ec3bb66bfba6b9667327d31b3e52', 'addendum e changed'
OUT, REP = D / 'db' / 'wiki_led', D / 'reports'
SEED = 20261020
CAP = 3                                                                  # P1: a donor may serve at most 3 books
T0 = time.time()
os.nice(5)                                                               # machine rule: nice, one heavy job at a time
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
WCOLS = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS]
HCOLS = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)
SCORE0 = 2019 * 12


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


def peak_mb():                                                           # macOS reports ru_maxrss in bytes
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20


R = pd.read_parquet(OUT / 'test_a_rows_c.parquet')
W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
WF = pd.read_parquet(OUT / 'test_a_wiki_features_c.parquet')


# ---------------------------------------------------------------- donors (P1)
def match_value(col):
    x = R[['work_id', 'mi', col]].dropna()
    early = x[(x.mi >= 2016 * 12 + 2) & (x.mi <= 2018 * 12 + 11)].groupby('work_id')[col].median()
    first12 = x.sort_values('mi').groupby('work_id').head(12).groupby('work_id')[col].median()
    return early.combine_first(first12)


vb, va = match_value('b_lvl4'), match_value('a_lvl4')
info = W.set_index('work_id')[['article', 'author_article', 'creator']]
info['akey'] = info.author_article.fillna('creator:' + info.creator.astype(str))
rank = pd.Series(np.random.default_rng(SEED).permutation(len(info)), index=np.sort(info.index.values))   # fixed random order for ties


def assign(v, recipients, donor, served, steps, article_rule=True):
    """v: matching value by work_id.  The books of v are put in the order (value, fixed random order).  Each recipient (in that order)
    that has no donor yet takes the nearest book in the order, searching one step down, one step up, two steps down, and so on,
    with a different author key (and, if article_rule, a different book article) that serves fewer than CAP books."""
    pool = pd.DataFrame({'v': v, 'r': rank.reindex(v.index)}).sort_values(['v', 'r'])
    keys = pool.index.to_numpy()
    n = len(keys)
    ak, ar = info.akey.reindex(keys).to_numpy(), info.article.reindex(keys).to_numpy()
    for i in range(n):
        b = keys[i]
        if b not in recipients or b in donor:
            continue
        hit = None
        for step in range(1, n):
            for j in (i - step, i + step):                               # one step down, then one step up
                if 0 <= j < n and ak[j] != ak[i] and (not article_rule or ar[j] != ar[i]) and served[keys[j]] < CAP:
                    hit = j
                    break
            if hit is not None:
                break
        if hit is not None:
            donor[b] = keys[hit]
            served[keys[hit]] += 1
            steps[b] = step


def build(article_rule):
    donor, served, steps = {}, Counter(), {}
    assign(vb, set(vb.index), donor, served, steps, article_rule)                              # pass 1: matched on the book article
    assign(va, set(va.index) - set(vb.index), donor, served, steps, article_rule)              # pass 2: no book value, matched on the author article
    return donor, served, steps


donor, served, steps = build(True)
donor_letter, _, _ = build(False)                                        # without the different-article rule, only to count what it changes


def build_bruteforce():
    """Independent check of the donor search: for every recipient the whole order is ranked by distance (the book below before the book above at
    the same distance) and the first eligible book is taken; the result must equal the donors found by the stepwise search above."""
    don, srv = {}, Counter()
    for v_, rec in ((vb, set(vb.index)), (va, set(va.index) - set(vb.index))):
        pool = pd.DataFrame({'v': v_, 'r': rank.reindex(v_.index)}).sort_values(['v', 'r'])
        keys = pool.index.to_numpy()
        ak, ar = info.akey.reindex(keys).to_numpy(), info.article.reindex(keys).to_numpy()
        pos = np.arange(len(keys))
        for i in range(len(keys)):
            b = keys[i]
            if b not in rec or b in don:
                continue
            for j in np.lexsort((pos > i, np.abs(pos - i))):
                if j != i and ak[j] != ak[i] and ar[j] != ar[i] and srv[keys[j]] < CAP:
                    don[b] = keys[j]
                    srv[keys[j]] += 1
                    break
    return don


donor_bf = build_bruteforce()
assert donor_bf == donor, 'the stepwise donor search and the brute-force search disagree'
log('donor search checked against an independent brute-force search: identical for', len(donor), 'books')
log('donors', len(donor), 'of', len(info), '| books with a book-article value', len(vb), '| matched on the author article only', len(set(va.index) - set(vb.index)))
d_map = pd.Series(donor)
assert (info.akey.reindex(d_map.index).to_numpy() != info.akey.reindex(d_map.values).to_numpy()).all(), 'a donor has the same author key'
assert (info.article.reindex(d_map.index).to_numpy() != info.article.reindex(d_map.values).to_numpy()).all(), 'a donor has the same book article'
assert max(served.values()) <= CAP
dl = pd.Series(donor_letter)
n_same_article_letter = int((info.article.reindex(dl.index).to_numpy() == info.article.reindex(dl.values).to_numpy()).sum())
n_donor_differs_letter = int(sum(donor[b] != donor_letter.get(b) for b in donor))
d1 = d_map[d_map.index.isin(vb.index)]                                  # recipients matched on the book article (pass 1)
gap = vb.reindex(d1.index).to_numpy() - vb.reindex(d1.values).to_numpy()   # matching-value gap between recipient and donor
reuse = {int(k): int(v) for k, v in pd.Series(served).value_counts().sort_index().items()}   # donors by number of books served (plain ints for json)
log('donor reuse (donors serving n books):', reuse, '| recipients whose donor differs without the different-article rule', n_donor_differs_letter,
    '| recipients that would have had their own article', n_same_article_letter)
log('search steps: median', float(np.median(list(steps.values()))), 'max', max(steps.values()), '| matching-value gap: median |gap|', float(np.median(np.abs(gap))))

# ---------------------------------------------------------------- swap the Wikipedia features
FB = WF[WF.kind == 'book'].drop(columns='kind').rename(columns={c: 'b_' + c for c in FEATS})
FA = WF[WF.kind == 'author'].drop(columns='kind').rename(columns={c: 'a_' + c for c in FEATS})
P = R.drop(columns=WCOLS).copy()
P['donor'] = P.work_id.map(donor)
P['d_article'] = P.donor.map(info.article)
P['d_author'] = P.donor.map(info.author_article)
P = P.merge(FB.rename(columns={'article': 'd_article'}), on=['d_article', 'mi'], how='left')
P = P.merge(FA.rename(columns={'article': 'd_author'}), on=['d_author', 'mi'], how='left')
nod = P.donor.isna()
P.loc[nod, WCOLS] = R.loc[nod.values, WCOLS].values                   # books without a donor keep their own (counted)
log('rows', len(P), 'without donor', int(nod.sum()))
n_rows_donor_used = int((~nod).sum())
# check: the swapped features are the donor's features at the same origin month (2,000 random rows, book and author article)
fb_idx, fa_idx = FB.set_index(['article', 'mi'])['b_lvl4'], FA.set_index(['article', 'mi'])['a_lvl4']
smp = P[~nod].sample(2000, random_state=SEED)
exp_b = np.array([fb_idx.get((a, m), np.nan) for a, m in zip(smp.d_article, smp.mi)], float)
exp_a = np.array([fa_idx.get((a, m), np.nan) if isinstance(a, str) else np.nan for a, m in zip(smp.d_author, smp.mi)], float)
assert np.array_equal(smp.b_lvl4.to_numpy(float), exp_b, equal_nan=True) and np.array_equal(smp.a_lvl4.to_numpy(float), exp_a, equal_nan=True), 'swapped features are not the donor\'s'
log('placebo features checked against the donor\'s features at the same origin on 2,000 random rows')
# rows served by the most-used donor (the audit found one donor for 19% of the scored rows in the original run)
top_donor_rows = int(P.loc[P.mi >= SCORE0].donor.value_counts().iloc[0])


def walk(df, cols, tgt):
    out = []
    for Y in range(2019, 2027):
        te = df[(df.year == Y) & (df.mi >= SCORE0)]
        if te.empty:
            continue
        tr = df[(df.mi + 1) < Y * 12]
        m = lgb.LGBMRegressor(**LGB).fit(tr[cols], tr[tgt])
        out.append(pd.Series(m.predict(te[cols]), index=te.index))
    return pd.concat(out)


pr = P[(P.mi >= SCORE0)][['work_id', 'mi', 'D', 'Sg', 'Y', 'L_t']].copy()
for name, cols in (('pW', WCOLS), ('pHW', HCOLS + WCOLS)):
    for tgt in ('D', 'Y'):
        pr[f'{name}_{tgt}'] = walk(P, cols, tgt)
        log('fitted', name, tgt)
real = pd.read_parquet(OUT / 'test_a_preds_c.parquet')
pr = pr.merge(real[['work_id', 'mi', 'Wlgbm_D', 'HWlgbm_D', 'Hlgbm_D', 'Wlgbm_Y', 'HWlgbm_Y']], on=['work_id', 'mi'], how='inner')
pr.to_parquet(OUT / 'placebo_a_preds_c.parquet', index=False)

months = np.sort(pr.mi.unique())
rng = np.random.default_rng(SEED)
n, k = len(months), int(np.ceil(len(months) / 3))
BD = np.array([np.concatenate([np.arange(a, a + 3) % n for a in rng.choice(n, k)])[:n] for _ in range(2000)])
g = {m: pr[pr.mi == m] for m in months}
sp = lambda c: np.array([spearmanr(g[m][c], g[m].D).statistic for m in months])
res = {}
S = {c: sp(c) for c in ['Wlgbm_D', 'pW_D', 'HWlgbm_D', 'pHW_D', 'Hlgbm_D']}
for c, v in S.items():
    b = v[BD].mean(1)
    res[c] = dict(change_rank=float(v.mean()), lo=float(np.percentile(b, 2.5)), hi=float(np.percentile(b, 97.5)),
                  surge_ap_ratio=float(average_precision_score(pr.Sg, pr[c]) / pr.Sg.mean()))
for a, b_ in (('Wlgbm_D', 'pW_D'), ('HWlgbm_D', 'pHW_D'), ('pHW_D', 'Hlgbm_D')):
    d = S[a] - S[b_]
    bb = d[BD].mean(1)
    res[f'{a}_minus_{b_}'] = dict(mean=float(d.mean()), lo=float(np.percentile(bb, 2.5)), hi=float(np.percentile(bb, 97.5)))
act = np.expm1(pr.Y)
for c in ['Wlgbm_Y', 'pW_Y']:
    e = (np.expm1(pr[c]).clip(lower=0) - act).abs()
    res[c] = dict(mae_loans=float(e.mean()), wape=float(e.sum() / act.sum()),
                  level_rank=float(np.mean([spearmanr(g[m][c], g[m].Y).statistic for m in months])))
res['donors'] = len(donor)
res['rows_without_donor'] = int(nod.sum())
res['p1_donors'] = dict(cap=CAP, donors_used=int(len(served)), donor_reuse_counts=reuse, max_books_per_donor=int(max(served.values())),
                        rows_of_most_used_donor_scored=top_donor_rows, scored_rows=int((P.mi >= SCORE0).sum()), share_of_scored_rows_of_most_used_donor=top_donor_rows / int((P.mi >= SCORE0).sum()),
                        median_search_steps=float(np.median(list(steps.values()))), max_search_steps=int(max(steps.values())),
                        median_abs_gap_matching_value=float(np.median(np.abs(gap))), p90_abs_gap_matching_value=float(np.percentile(np.abs(gap), 90)),
                        recipients_second_pass=int(len(set(va.index) - set(vb.index))),
                        recipients_whose_donor_changes_with_different_article_rule=n_donor_differs_letter,
                        recipients_that_would_get_their_own_article_without_that_rule=n_same_article_letter)
res['runtime_s'] = round(time.time() - T0)
res['peak_rss_mb'] = round(peak_mb())
res['correction'] = 'A1 through test_a_rows_c / test_a_wiki_features_c; P1 donors (sorted by matching value, nearest different author key alternating down/up, random ties seed 20261020, at most 3 books per donor)'
(REP / 'wiki_led_placebo_a_c.json').write_text(json.dumps(res, indent=1))
for k_, v in res.items():
    log(k_, v)
