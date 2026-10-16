"""Study 2R step 4b: weekly interest series per article. Daily user views = canonical title + redirects kept by the screen
(03), summed to ISO weeks (Monday start) and divided by the total English Wikipedia user views of that week (reuses
data/db/interest/wiki/weekly_total.parquet). A day missing from the API answer counts as 0 views (as in
main_study/interest/07). valid = full 7-day week, not a partial week of the site total, and views > 0 (as in
parameter_audit/calibrate_book_series.py). top_day_share = largest day / weekly views (the one-day flag).
Outputs: data/db/study2r/weekly_book.parquet, weekly_author.parquet (secondary), article_summary.csv
"""
import hashlib
import numpy as np, pandas as pd
from common import *

fid = lambda t: hashlib.sha1(t.encode()).hexdigest()[:16]
DAYS = pd.date_range('2015-07-01', '2026-09-30', freq='D')
TOT = pd.read_parquet(WK / 'weekly_total.parquet').set_index('week')
wk = DAYS - pd.to_timedelta(DAYS.weekday, unit='D')
A = pd.read_parquet(OUT / 'articles.parquet')
RS = pd.read_parquet(OUT / 'redirect_screen.parquet')
kept = RS[RS.keep == True].groupby('canonical').redirect.apply(list).to_dict()  # noqa: E712


def load(t):
    f = OUT / 'pv_daily' / f'{fid(t)}.parquet'
    if not f.exists():
        return None
    d = pd.read_parquet(f)
    return d.set_index('date').views.reindex(DAYS, fill_value=0).astype(float)


def build(titles, with_redirects):
    frames, summ = [], []
    for t in titles:
        own = load(t)
        if own is None:
            summ.append(dict(article=t, fetched=False)); continue
        s = own.copy(); nred = 0
        if with_redirects:
            for r in kept.get(t, []):
                x = load(r)
                if x is not None:
                    s = s + x; nred += 1
        df = pd.DataFrame({'week': wk, 'v': s.to_numpy()})
        g = df.groupby('week').v.agg(['sum', 'max', 'size']).reset_index()
        g = g[g.week.isin(TOT.index)]
        tt = TOT.loc[g.week]
        g['article'] = t; g['views'] = g['sum'].to_numpy(); g['share'] = g['sum'].to_numpy() / tt.total_views.to_numpy()
        g['top_day_share'] = np.where(g['sum'] > 0, g['max'] / g['sum'].replace(0, np.nan), np.nan)
        g['valid'] = ((g['size'] == 7) & ~tt.partial_week.to_numpy() & (g['sum'] > 0)).to_numpy()
        frames.append(g[['article', 'week', 'views', 'share', 'top_day_share', 'valid']])
        summ.append(dict(article=t, fetched=True, n_redirects_kept=nred, redirect_share=1 - own.sum() / s.sum() if s.sum() else np.nan,
                         median_weekly_views=float(g['sum'].median()), last_year_median_weekly_views=float(g['sum'].iloc[-52:].median()),
                         total_views=float(s.sum())))
    return pd.concat(frames, ignore_index=True), pd.DataFrame(summ)


bt = sorted(set(A[A.kind == 'book'].canonical.dropna()))
WB, SB = build(bt, True)
WB.to_parquet(OUT / 'weekly_book.parquet', index=False)
SB.assign(kind='book').to_csv(OUT / 'article_summary.csv', index=False)
log('book articles with weekly series', WB.article.nunique(), 'of', len(bt), '| rows', len(WB))
AA = pd.read_parquet(OUT / 'book_author_articles.parquet')
at = sorted(set(A[A.requested.isin(AA.author_article)].canonical.dropna()) - set(bt))
WA, SA = build(at, False)
WA.to_parquet(OUT / 'weekly_author.parquet', index=False)
log('author articles with weekly series', WA.article.nunique(), 'of', len(at))
