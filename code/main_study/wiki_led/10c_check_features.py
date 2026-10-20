# 10c_check_features.py: check of the corrected feature function (correction A1, addendum e) against the original one.
# Both functions are taken from the code of 10_test_a.py (original) and 10c_test_a.py (corrected) themselves (the function definition and
# the constants it uses are read with ast and run here), so the check is about the code that makes the features, not a copy of it.
#   mode 1 (default): 20 articles drawn with seed 20261020 (5 book and 5 author articles whose first view is in the first week of the data,
#       5 + 5 whose first view is later).  For the first group the corrected and original features must be identical in every origin
#       month; for the second group the table shows where they differ (origin months before the first view, and the first months after
#       it) and from which origin month on they agree again.  The original function is also compared with the stored original file
#       data/db/wiki_led/test_a_wiki_features.parquet (the check that this harness reproduces the pipeline).
#   mode 2 (--full): the same comparison for every article, from the two stored files test_a_wiki_features.parquet and
#       test_a_wiki_features_c.parquet (run after 10c_test_a.py).
# Output: data/reports/wiki_led_features_check_c.md (mode 1), data/reports/wiki_led_features_check_full_c.md (mode 2).
#   python main_study/wiki_led/10c_check_features.py [--full]      (from code/, with ../.venv/bin/python)
import sys, ast, json, pathlib, argparse, time
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
HERE = pathlib.Path(__file__).resolve().parent
WIKI, REP = D / 'db' / 'wiki_led', D / 'reports'
SEED = 20261020
ap = argparse.ArgumentParser()
ap.add_argument('--full', action='store_true')
FULL = ap.parse_args().full
NAMES_ASSIGN = {'ORIG0', 'ORIG1', 'EPS', 'ORIGINS', 'ENDS', 'FEATS'}
NAMES_DEF = {'mi_of', 'month_end', 'article_features'}


def load_namespace(path):
    """Run only the constants and the functions article_features, month_end and mi_of of a script, nothing else."""
    tree = ast.parse(path.read_text())
    keep = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in NAMES_DEF:
            keep.append(node)
        elif isinstance(node, ast.Assign):
            names = {n.id for t in node.targets for n in ast.walk(t) if isinstance(n, ast.Name)}
            if names & NAMES_ASSIGN:
                keep.append(node)
    ns = {'np': np, 'pd': pd}
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(path), 'exec'), ns)
    return ns


NO, NC = load_namespace(HERE / '10_test_a.py'), load_namespace(HERE / '10c_test_a.py')
FEATS = NO['FEATS']
assert FEATS == NC['FEATS'] and NO['EPS'] == NC['EPS'] and np.array_equal(NO['ORIGINS'], NC['ORIGINS']) and np.array_equal(NO['ENDS'], NC['ENDS'])
ORIGINS, ENDS = NO['ORIGINS'], NO['ENDS']


def ym(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


def same(a, b):
    """Exact equality with NaN equal to NaN (arrays of the same shape)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return (a == b) | (np.isnan(a) & np.isnan(b))


def same_tol(a, b, tol=1e-9):
    """Equal up to floating-point rounding (rolling sums start at a different week, so dw can differ in the 15th digit)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return np.isclose(a, b, rtol=tol, atol=tol) | (np.isnan(a) & np.isnan(b))


def table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join([' --- '] + [' ---: '] * (len(header) - 1)) + '|']
    return '\n'.join(out + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows])


W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
SRC = {'book': (D / 'db' / 'study2r' / 'weekly_book.parquet', set(W.article.dropna())),
       'author': (D / 'db' / 'study2r' / 'weekly_author.parquet', set(W.author_article.dropna()))}
WF0 = pd.read_parquet(WIKI / 'test_a_wiki_features.parquet')

if not FULL:
    # ------------------------------------------------------------ draw the 20 articles
    series, first_view = {}, {}
    for kind, (path, names) in SRC.items():
        X = pd.read_parquet(path, columns=['article', 'week', 'views', 'share', 'valid'])
        X = X[X.article.isin(names)]
        X['week'] = pd.to_datetime(X['week'])
        fv = X[X.views > 0].groupby('article').week.min()
        t0 = X.week.min()
        first_view[kind] = pd.DataFrame({'first_view': fv, 'in_week1': fv == t0})
        series[kind] = X
        first_view[kind] = first_view[kind][first_view[kind].index.isin(WF0[WF0.kind == kind].article.unique())]
    rng = np.random.default_rng(SEED)
    picks = []
    for kind in ('book', 'author'):
        fvk = first_view[kind]
        for week1 in (True, False):
            pool = np.sort(fvk.index[fvk.in_week1 == week1].to_numpy())
            for a in rng.choice(pool, 5, replace=False):
                picks.append((kind, str(a), week1))
    # ------------------------------------------------------------ compare
    rows, detail = [], []
    n_week1_identical = n_week1 = n_stored_ok = 0
    for kind, a, week1 in picks:
        g = series[kind][series[kind].article == a]
        o, c = NO['article_features'](g), NC['article_features'](g)
        st = WF0[(WF0.kind == kind) & (WF0.article == a)].sort_values('mi').reset_index(drop=True)
        o_ok = len(o) == len(st) and np.array_equal(o.mi.to_numpy(), st.mi.to_numpy()) and bool(same(o[FEATS].to_numpy(), st[FEATS].to_numpy()).all())
        n_stored_ok += int(o_ok)
        m = o.merge(c, on='mi', how='left', suffixes=('_o', '_c'), indicator=True)   # origin months of the original run, corrected values beside
        has_c = (m['_merge'] == 'both').to_numpy()
        eq = same(m[[f + '_o' for f in FEATS]].to_numpy(), m[[f + '_c' for f in FEATS]].to_numpy()).all(axis=1) & has_c
        fvw = first_view[kind].loc[a, 'first_view']
        wend = (pd.Series(ENDS[np.searchsorted(ORIGINS, m.mi.to_numpy())])).to_numpy()
        weeks_after = ((wend - np.datetime64(fvw)) / np.timedelta64(7, 'D')).astype(float)    # weeks from the first view week to the origin month's end
        before = weeks_after < 1                                                              # origin months that end before the first view week is complete
        differ = ~eq
        eq_tol = same_tol(m[[f + '_o' for f in FEATS]].to_numpy(), m[[f + '_c' for f in FEATS]].to_numpy()).all(axis=1) & has_c
        differ_tol = ~eq_tol                                                                  # differing by more than rounding (1e-9)
        last_diff = m.mi[differ_tol].max() if differ_tol.any() else None
        if week1:
            n_week1 += 1
            ident = len(c) == len(o) and bool(eq.all())
            n_week1_identical += int(ident)
        else:
            ident = None
        fin = np.isfinite(m[[f + '_o' for f in FEATS]].to_numpy()) & np.isfinite(m[[f + '_c' for f in FEATS]].to_numpy())
        dd = np.abs(m[[f + '_o' for f in FEATS]].to_numpy() - m[[f + '_c' for f in FEATS]].to_numpy())
        maxdiff = float(np.nanmax(np.where(fin, dd, np.nan))) if fin.any() else float('nan')
        n_before_o = int((~has_c).sum())
        lvl_before = m.loc[~has_c, 'lvl4_o']
        rows.append([kind, a[:34], str(fvw.date()), 'yes' if week1 else 'no', len(o), len(c), int(eq.sum()), int(differ.sum()),
                     '-' if ident is None else ('yes' if ident else 'NO'), f'{maxdiff:.3g}',
                     f'{n_before_o}' + (f' (lvl4 {lvl_before.median():.2f} -> missing)' if n_before_o else ''),
                     '-' if last_diff is None else f'{ym(int(last_diff))} ({weeks_after[m.mi.to_numpy() == last_diff][0]:.0f} wk after first view)',
                     int((differ & eq_tol).sum())])
    hdr = ['kind', 'article', 'first week with views', 'first view in week 1 of the data', 'origin months, original', 'corrected', 'identical origin months',
           'differing origin months', 'all identical (week-1 articles)', 'largest difference where both are finite', 'origin months with no corrected row (original lvl4 -> corrected)',
           'last origin month differing by more than 1e-9', 'origin months differing only by rounding (below 1e-9)']
    L = ['# Check of the corrected feature function on 20 articles (correction A1, addendum e)', '',
         'Written by `code/main_study/wiki_led/10c_check_features.py`. The two functions are the `article_features` of `10_test_a.py` (original) and `10c_test_a.py` (corrected), '
         'read from the files with `ast` and run on the weekly series of 20 articles drawn with seed 20261020: 5 book and 5 author articles whose first week with views is the first week of the data '
         '(29 June 2015), and 5 + 5 whose first view is later. Each article has one row per origin month from 2016-03 to 2026-07 for which a week had ended.', '',
         table(hdr, rows), '',
         f'- The original function reproduces the stored original features (`test_a_wiki_features.parquet`) exactly for {n_stored_ok} of {len(picks)} articles.',
         f'- Articles whose first view is in the first week of the data: corrected and original features are identical in every origin month for {n_week1_identical} of {n_week1} '
         '(same origin months, same values, NaN equal to NaN, no tolerance).',
         '- Articles whose first view is later: the origin months that end before the article has a complete week of views have no corrected row (all nine features missing; the original gave '
         'the floor value of lvl4 and zero-based ratios there), the first months after the first view differ because the original compared the new article with weeks of zero views, and '
         'from the month after the one named in the second-last column onward the two agree (differences below 1e-9 are floating-point rounding: a rolling sum that starts in a different week '
         'carries a different rounding error in the 15th digit; they are not counted as differences there).']
    out = REP / 'wiki_led_features_check_c.md'
    out.write_text('\n'.join(L) + '\n')
    print('\n'.join(L))
    assert n_stored_ok == len(picks), 'the original function does not reproduce the stored features'
    assert n_week1_identical == n_week1, 'corrected and original features differ for an article whose first view is in the first week'
    print('wrote', out)
else:
    # ------------------------------------------------------------ all articles, from the stored files
    WFc = pd.read_parquet(WIKI / 'test_a_wiki_features_c.parquet')
    fvs = []
    for kind, (path, names) in SRC.items():
        X = pd.read_parquet(path, columns=['article', 'week', 'views'])
        X = X[X.article.isin(names)]
        X['week'] = pd.to_datetime(X['week'])
        t0 = X.week.min()
        fv = X[X.views > 0].groupby('article').week.min()
        fvs.append(pd.DataFrame({'kind': kind, 'article': fv.index.astype(str), 'first_view': fv.values, 'week1': (fv == t0).values}))
        n_no_views = X.article.nunique() - len(fv)
        print(kind, 'articles without any view:', n_no_views)
    FV = pd.concat(fvs, ignore_index=True)
    m = WF0.merge(WFc, on=['kind', 'article', 'mi'], how='left', suffixes=('_o', '_c'), indicator=True)
    m = m.merge(FV, on=['kind', 'article'], how='left')
    eq = same(m[[f + '_o' for f in FEATS]].to_numpy(), m[[f + '_c' for f in FEATS]].to_numpy()).all(axis=1) & (m['_merge'] == 'both').to_numpy()
    m['same_exact'] = eq
    m['eq_tol'] = same_tol(m[[f + '_o' for f in FEATS]].to_numpy(), m[[f + '_c' for f in FEATS]].to_numpy()).all(axis=1) & (m['_merge'] == 'both').to_numpy()
    wend = ENDS[np.searchsorted(ORIGINS, m.mi.to_numpy())]
    m['weeks_after'] = (wend - m.first_view.to_numpy().astype('datetime64[ns]')) / np.timedelta64(7, 'D')
    m['no_c_row'] = m['_merge'] != 'both'
    res = {}
    for kind in ('book', 'author'):
        q = m[m.kind == kind]
        w1 = q[q.week1 == True]       # noqa: E712
        later = q[q.week1 == False]   # noqa: E712
        nov = q[q.first_view.isna()]
        d = later[~later.eq_tol]                      # rows that differ by more than floating-point rounding (1e-9)
        last = d.groupby('article').weeks_after.max()
        res[kind] = dict(
            articles_original=int(q.article.nunique()),
            week1_articles=int(w1.article.nunique()), week1_rows=int(len(w1)), week1_rows_differing=int((~w1.same_exact).sum()),
            week1_articles_differing=int(w1[~w1.same_exact].article.nunique()),
            later_articles=int(later.article.nunique()), later_rows=int(len(later)), later_rows_identical=int(later.same_exact.sum()), later_rows_equal_within_1e9=int(later.eq_tol.sum()),
            later_rows_no_corrected_row=int(later.no_c_row.sum()),
            later_articles_with_a_difference=int(d.article.nunique()),
            weeks_after_first_view_of_last_difference_median=float(last.median()) if len(last) else None,
            weeks_after_first_view_of_last_difference_p99=float(last.quantile(0.99)) if len(last) else None,
            weeks_after_first_view_of_last_difference_max=float(last.max()) if len(last) else None,
            no_view_articles=int(nov.article.nunique()), no_view_rows=int(len(nov)),
            no_view_rows_with_corrected_row=int((~nov.no_c_row).sum()))
    # rows of the corrected file that are not in the original file (must be none)
    extra = WFc.merge(WF0[['kind', 'article', 'mi']], on=['kind', 'article', 'mi'], how='left', indicator=True)
    res['corrected_rows_not_in_original'] = int((extra['_merge'] == 'left_only').sum())
    res['rows_original'], res['rows_corrected'] = int(len(WF0)), int(len(WFc))
    # features of the corrected file that are missing although the original has a value, by feature, on rows both have
    both = m[m['_merge'] == 'both']
    res['finite_in_original_missing_in_corrected_rows_that_exist'] = {f: int((np.isfinite(both[f + '_o']) & both[f + '_c'].isna()).sum()) for f in FEATS}
    rows = []
    for kind in ('book', 'author'):
        r = res[kind]
        rows.append([kind, f"{r['articles_original']:,}", f"{r['week1_articles']:,}", f"{r['week1_rows']:,}", f"{r['week1_rows_differing']:,}",
                     f"{r['later_articles']:,}", f"{r['later_rows']:,}", f"{r['later_rows_identical']:,}", f"{r['later_rows_equal_within_1e9']:,}", f"{r['later_rows_no_corrected_row']:,}",
                     f"{r['later_articles_with_a_difference']:,}",
                     '-' if r['weeks_after_first_view_of_last_difference_median'] is None else f"{r['weeks_after_first_view_of_last_difference_median']:.0f} / {r['weeks_after_first_view_of_last_difference_p99']:.0f} / {r['weeks_after_first_view_of_last_difference_max']:.0f}",
                     f"{r['no_view_articles']}"])
    hdr = ['kind', 'articles with original features', 'articles whose first view is in week 1', 'their origin-month rows', 'of these rows differing',
           'other articles', 'their rows', 'rows exactly identical', 'rows equal within 1e-9', 'rows with no corrected row', 'articles with at least one row differing by more than 1e-9',
           'weeks after the first view week of the last such row: median / 99th percentile / max', 'articles with no view at all']
    L = ['# Check of the corrected features for every article (correction A1, addendum e)', '',
         'Written by `code/main_study/wiki_led/10c_check_features.py --full`: the stored original features (`test_a_wiki_features.parquet`) against the corrected ones '
         '(`test_a_wiki_features_c.parquet`), row by row on (kind, article, origin month); exact equality with NaN equal to NaN.', '',
         table(hdr, rows), '',
         f"- Rows in the original file {res['rows_original']:,}, in the corrected file {res['rows_corrected']:,}; rows in the corrected file that are not in the original: {res['corrected_rows_not_in_original']}.",
         f"- Features that are finite in the original and missing in the corrected file on rows that exist in both (by feature): {res['finite_in_original_missing_in_corrected_rows_that_exist']}."]
    out = REP / 'wiki_led_features_check_full_c.md'
    out.write_text('\n'.join(L) + '\n')
    (REP / 'wiki_led_features_check_full_c.json').write_text(json.dumps(res, indent=1))
    print('\n'.join(L))
    assert res['book']['week1_rows_differing'] == 0 and res['author']['week1_rows_differing'] == 0, 'articles with first view in week 1 differ'
    print('wrote', out)
