"""Study 2R: assembling the tests (works, shifts, screens, placebo pools) from the stored tables. Uses _lib2r."""
from _lib2r import *

CLASSES = ('sustained', 'intermediate', 'fading')       # final duration classes of the Study 3 rule; interrupted shifts have none


def works_table():
    W = pd.read_parquet(OUT / 'works.parquet')
    return W


def author_floor_articles(floor=300.0):
    """Author articles with at least one week whose 26-week normal level (previous 26 valid weeks, median of views) is at or above the
    floor: only for these is 'no shift' meaningful (as for book articles kept at the floor)."""
    WA = pd.read_parquet(OUT / 'weekly_author.parquet')
    keep = []
    for art, g in WA.groupby('article'):
        g = g.sort_values('week')
        vs = pd.Series(np.where(g.valid, g.views, np.nan))
        vn = vs.shift(1).rolling(26, min_periods=26).median()
        if (vn >= floor).any():
            keep.append(art)
    return set(keep)


def shift_mi(sh):
    return mi_of(sh.start_week)


def by_article(sh):
    """article -> sorted month indices of every shift (any class, any flag) in the table."""
    d = {}
    for a, g in sh.groupby('article'):
        d[a] = np.sort(shift_mi(g))
    return d


def screens(C, W, kind, sh_book, sh_author=None):
    """Screen matrix (shift starts on the work's own article; for the author run also on its author article)."""
    ab = by_article(sh_book)
    sw = {}
    for w, a in zip(W.work_id, W.article):
        arr = ab.get(a)
        if arr is not None:
            sw[int(w)] = arr
    if kind == 'author' and sh_author is not None:
        aa = by_article(sh_author)
        for w, a in zip(W.work_id, W.author_article):
            arr = aa.get(a) if isinstance(a, str) else None
            if arr is not None:
                sw[int(w)] = np.concatenate([sw.get(int(w), np.zeros(0, int)), arr])
    return screen_matrix(C, sw)


def book_tests(sh, W, C, quality_only=True, labelled_only=True):
    """One row per work and shift: month 0 = month of the start week; shifts with a final duration class, quality OK, from 2017-01; works
    sharing an article each get their own row; several shifts of a work in one month 0 share one test (the earliest start week)."""
    s = sh[sh.label.isin(CLASSES)] if labelled_only else sh
    if quality_only:
        s = s[s.quality_ok]
    s = s.assign(m0=shift_mi(s))
    s = s[s.m0 >= STUDY_START]
    rows = []
    for r in s.itertuples(index=False):
        for w in str(r.work_ids).split(','):
            if w:
                rows.append(dict(work_id=int(w), article=r.article, start_week=r.start_week, m0=int(r.m0), label=r.label, size=r.size,
                                 whole_peak=r.whole_peak, whole_duration=int(r.whole_duration), duration_bin=r.whole_duration_bin,
                                 quality_flag=r.quality_flag))
    T = pd.DataFrame(rows)
    T = T.sort_values('start_week').drop_duplicates(['work_id', 'm0']).reset_index(drop=True)
    return T[T.work_id.isin(set(C.ids))].reset_index(drop=True)


def author_tests(sh, W, C):
    s = sh[sh.label.isin(CLASSES) & sh.quality_ok].assign(m0=lambda d: shift_mi(d))
    s = s[s.m0 >= STUDY_START]
    wa = W.dropna(subset=['author_article']).groupby('author_article').work_id.apply(list).to_dict()
    rows = []
    for r in s.itertuples(index=False):
        for w in wa.get(r.article, []):
            rows.append(dict(work_id=int(w), article=r.article, start_week=r.start_week, m0=int(r.m0), label=r.label, size=r.size,
                             whole_peak=r.whole_peak, whole_duration=int(r.whole_duration), duration_bin=r.whole_duration_bin,
                             quality_flag=r.quality_flag))
    T = pd.DataFrame(rows).sort_values('start_week').drop_duplicates(['work_id', 'm0']).reset_index(drop=True)
    return T[T.work_id.isin(set(C.ids))].reset_index(drop=True)


def pool_mask(C, W, kind):
    """Placebo pool: matched works whose own book article reached the 300 views floor (its shifts are then known); for the author run
    also whose author article reached the floor."""
    kept = set(pd.read_parquet(OUT / 'kept_articles.parquet').article)
    Wi = W.set_index('work_id').reindex(C.ids)
    m = Wi.article.isin(kept).to_numpy().copy()
    if kind == 'author':
        m &= Wi.author_article.isin(author_floor_articles()).to_numpy()
    return m


def art_codes(C, W):
    Wi = W.set_index('work_id').reindex(C.ids)
    return pd.factorize(Wi.article.fillna(pd.Series(C.ids.astype(str), index=Wi.index)))[0]
