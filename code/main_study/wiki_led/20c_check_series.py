# 20c_check_series.py: check of correction A1 in Test C.  The function monthly() of 20_test_c.py (original) and of 20c_test_c.py (corrected)
# are read from the files with ast and run on the weekly series of every book and author article of Test A (no model is fitted).
# Expected: for an article whose first view is in the first week of the data, the corrected monthly series x(t) equals the original in
# every month; for the others, the months before the first view month are missing in the corrected series, the first view month and the
# next one differ (the first month has fewer weeks; the next month's change is taken against it) and all later months are identical.
# Output: data/reports/wiki_led_test_c_series_check_c.md
#   python main_study/wiki_led/20c_check_series.py      (from code/, with ../.venv/bin/python)
import sys, ast, pathlib
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
HERE = pathlib.Path(__file__).resolve().parent
REP = D / 'reports'


def load_monthly(path):
    tree = ast.parse(path.read_text())
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name == 'monthly')
            or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'EPS' for t in n.targets))]
    ns = {'np': np, 'pd': pd}
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(path), 'exec'), ns)
    return ns['monthly']


m0, m1 = load_monthly(HERE / '20_test_c.py'), load_monthly(HERE / '20c_test_c.py')
W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
lines = ['# Check of correction A1 in Test C: the monthly candidate series, original and corrected', '',
         'Written by `code/main_study/wiki_led/20c_check_series.py`. `monthly()` of `20_test_c.py` and of `20c_test_c.py` are read from the files with `ast` and run on the weekly series of every Test A book and author article; '
         'x(t) is the month-on-month change of ln(mean weekly share). Exact equality with NaN equal to NaN.', '']
rows = []
ok_all = True
for kind, fname, names in (('book', 'weekly_book.parquet', set(W.article.dropna())), ('author', 'weekly_author.parquet', set(W.author_article.dropna()))):
    X = pd.read_parquet(D / 'db' / 'study2r' / fname, columns=['article', 'week', 'views', 'share'])
    X = X[X.article.isin(names)].copy()
    X['week'] = pd.to_datetime(X['week'])
    o = m0(X[['article', 'week', 'share']], 'article')
    c = m1(X, 'article', a1=True)
    fv = X[X.views > 0].groupby('article').week.min()
    t0 = X.week.min()
    first_mi = (fv + pd.Timedelta(days=6)).dt.year * 12 + (fv + pd.Timedelta(days=6)).dt.month - 1     # month of the first week's Sunday end, as in monthly()
    cols = o.columns
    assert list(c.columns) == list(cols) or set(c.columns) <= set(cols)
    c = c.reindex(index=o.index, columns=cols)
    eq = (o.to_numpy() == c.to_numpy()) | (np.isnan(o.to_numpy()) & np.isnan(c.to_numpy()))
    eqdf = pd.DataFrame(eq, index=o.index, columns=cols)
    mi = np.array(cols)
    week1 = fv.index[(fv == t0).to_numpy()]
    w1 = eqdf.loc[eqdf.index.isin(week1)]
    later = [a for a in eqdf.index if a in fv.index and fv[a] != t0]
    n_before_ok = n_before = n_after_ok = n_after = 0
    for a in later:
        f0 = int(first_mi[a])
        r_o, r_c = o.loc[a].to_numpy(), c.loc[a].to_numpy()
        before = mi < f0
        n_before += int(before.sum())
        n_before_ok += int(np.isnan(r_c[before]).sum())
        after = mi >= f0 + 2
        n_after += int(after.sum())
        n_after_ok += int(eqdf.loc[a].to_numpy()[after].sum())
    ok = bool(w1.to_numpy().all()) and n_before_ok == n_before and n_after_ok == n_after
    ok_all &= ok
    rows.append([kind, f'{len(o):,}', f'{len(week1):,}', f'{int((~w1.to_numpy()).sum())}', f'{len(later):,}', f'{n_before_ok:,} of {n_before:,}', f'{n_after_ok:,} of {n_after:,}',
                 f'{len(o) - fv.index.size}', 'yes' if ok else 'NO'])
lines += ['| kind | articles | first view in week 1 | differing months among them | other articles | months before the first view month that are missing in the corrected series | months from two months after the first view month that are identical | articles without any view | as expected |',
          '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |'] + ['| ' + ' | '.join(r) + ' |' for r in rows]
(REP / 'wiki_led_test_c_series_check_c.md').write_text('\n'.join(lines) + '\n')
print('\n'.join(lines))
assert ok_all, 'the corrected monthly series do not behave as expected'
