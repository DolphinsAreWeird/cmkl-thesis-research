# Pure functions that turn checkout rows and theme strengths into the category x month x format demand panel.
# Used by 01_demand_panel.py (real and LibriVox panels), 10_positive_controls.py (title-word backup) and the tests.
# Months are integers mi = year * 12 + (month - 1), so month arithmetic is plain integer arithmetic.
import numpy as np, pandas as pd
from scipy import sparse
from _files import LEVEL_NAME

# NOT IN RECORD: the size rule's median needs at least half of the 24 months before the window to be available
# (format-wide missing months, such as the digital gaps of 2024 and 2025, are skipped, not counted as zero).
MIN_SIZE_SHARE = 0.5


def min_size_months(lookback):
    return max(1, int(np.ceil(MIN_SIZE_SHARE * lookback)))


# ---------------- months ----------------
def mi_of(year, month):
    return np.asarray(year, dtype=np.int64) * 12 + np.asarray(month, dtype=np.int64) - 1


def mi_from_ym(ym):
    """'2020-03' (or a list of them) -> month index."""
    if isinstance(ym, str):
        y, m = ym.split('-')
        return int(y) * 12 + int(m) - 1
    return np.array([mi_from_ym(x) for x in ym], dtype=np.int64)


def ym_of(mi):
    mi = int(mi)
    return f'{mi // 12:04d}-{mi % 12 + 1:02d}'


def month_of_date(dates):
    """Calendar month index of each date (e.g. the Monday that starts a shift week)."""
    d = pd.to_datetime(pd.Series(dates))
    return (d.dt.year * 12 + d.dt.month - 1).astype(np.int64).to_numpy()


# ---------------- theme strengths ----------------
def main_strength(WT, include_title=False):
    """Work x node strengths for the main assignment (record: 'main assignment without title-word evidence').
    When the table keeps per-source shares (s_<source>) and the list of sources with evidence for each work
    ('sources', comma separated), the strength is recomputed as the mean share over the work's non-title sources,
    the same combination rule as code/main_study/07_assign_works.py. Works whose only evidence is title words
    drop out. include_title=True returns the stored strength (the flagged backup for small positive controls).
    Returns work_id, node_id, level (broad/middle/narrow), strength > 0, and how strength was obtained."""
    W = WT.copy()
    W['level'] = W['level'].map(LEVEL_NAME)
    if W['level'].isna().any():
        raise ValueError('unknown level values in work_theme')
    src_cols = [c for c in W.columns if c.startswith('s_') and c != 's_title']
    how = 'stored strength'
    if not include_title and 's_title' in W.columns and 'sources' in W.columns and src_cols:
        srcs = W['sources'].fillna('').str.split(',')
        num = np.zeros(len(W)); den = np.zeros(len(W))
        for c in src_cols:
            has = srcs.map(lambda s, n=c[2:]: n in s).to_numpy()
            num += W[c].fillna(0).to_numpy() * has
            den += has
        W['strength'] = np.where(den > 0, num / np.maximum(den, 1), 0.0)
        how = 'recomputed without title-word evidence (mean share over ' + ', '.join(c[2:] for c in src_cols) + ')'
    W = W[W.strength > 0][['work_id', 'node_id', 'level', 'strength']].drop_duplicates(['work_id', 'node_id'])
    W['work_id'] = W.work_id.astype(np.int64)
    return W.reset_index(drop=True), how


def with_title_backup(WT, TB):
    """Flagged backup strengths for a small positive-control category (record taxonomy.assignment): the v3 main table
    (per-source shares s_<source>, sources per work) combined with the separate title-word table (s_title) by the
    taxonomy's own rule, the mean share over the sources that have evidence for the work, title words counted as one
    more source. Returns work_id, node_id, level, strength > 0."""
    src_cols = [c for c in WT.columns if c.startswith('s_') and c != 's_title']
    A = WT[['work_id', 'node_id', 'level', 'sources'] + src_cols].copy()
    T = TB[['work_id', 'node_id', 'level', 's_title']].copy()
    X = A.merge(T, on=['work_id', 'node_id', 'level'], how='outer')
    srcs = WT.groupby('work_id').sources.first()
    X['sources'] = X.work_id.map(srcs).fillna('')
    has_title = X.work_id.isin(set(TB.work_id)).to_numpy()
    num = X.s_title.fillna(0).to_numpy() * has_title
    den = has_title.astype(float)
    for c in src_cols:
        has = X.sources.str.split(',').map(lambda s, n=c[2:]: n in s).to_numpy()
        num = num + X[c].fillna(0).to_numpy() * has
        den = den + has
    X['strength'] = np.where(den > 0, num / np.maximum(den, 1), 0.0)
    X['level'] = X.level.map(LEVEL_NAME)
    X = X[X.strength > 0][['work_id', 'node_id', 'level', 'strength']]
    X['work_id'] = X.work_id.astype(np.int64)
    return X.reset_index(drop=True)


# ---------------- checkout rows ----------------
def work_month(rows, record_work):
    """rows: record_id, year, month, checkouts (one format). Returns
    wm      work_id, mi, checkouts (summed over the work's records; records without a work are left out),
    totals  mi -> total_checkouts and n_rows over ALL rows of the format (the share's denominator)."""
    r = pd.DataFrame({'record_id': rows['record_id'].to_numpy().astype(np.int64),
                      'mi': mi_of(rows['year'], rows['month']),
                      'checkouts': rows['checkouts'].to_numpy().astype(np.int64)})
    totals = r.groupby('mi').agg(total_checkouts=('checkouts', 'sum'), n_rows=('checkouts', 'size'))
    rw = pd.Series(record_work['work_id'].to_numpy().astype(np.int64), index=record_work['record_id'].to_numpy().astype(np.int64))
    rw = rw[~rw.index.duplicated()]
    r['work_id'] = rw.reindex(r.record_id.to_numpy()).to_numpy()
    mapped = r[r.work_id.notna()]
    wm = mapped.groupby(['work_id', 'mi'], as_index=False).checkouts.sum()
    wm['work_id'] = wm.work_id.astype(np.int64)
    return wm, totals


def month_status(totals, missing=(), api=None, closure=None):
    """One row per month from the first to the last month with rows: month_ok is False for a month listed as missing
    in the record, a month without rows, or (when SPL API counts are given) a month whose rows are fewer than the
    API's count, i.e. a month only partly downloaded.
    NOT IN RECORD: the API comparison; a partly downloaded month is treated as missing, never as complete."""
    grid = np.arange(int(totals.index.min()), int(totals.index.max()) + 1)
    st = pd.DataFrame(index=pd.Index(grid, name='mi'))
    st['total_checkouts'] = totals.total_checkouts.reindex(grid)
    st['n_rows'] = totals.n_rows.reindex(grid)
    st['reason'] = ''
    miss = set(mi_from_ym(list(missing))) if len(missing) else set()
    st.loc[st.index.isin(miss), 'reason'] = 'missing in record'
    st.loc[st.n_rows.isna() & (st.reason == ''), 'reason'] = 'no rows'
    if api is not None:
        a = api.reindex(grid)
        short = st.n_rows.notna() & a.n_rows.notna() & (st.n_rows < a.n_rows)
        st.loc[short & (st.reason == ''), 'reason'] = 'fewer rows than SPL API (partial)'
        st['api_rows'] = a.n_rows; st['api_checkouts'] = a.checkouts
    if closure is not None:
        # addendum e: a month whose library-wide total is below frac x the median of the previous `lookback` months with
        # rows (at least `min_periods` of them) is a closure month, treated as missing.
        frac, lookback, min_periods = closure
        base = st.total_checkouts.where(st.n_rows.notna())
        ref = base.shift(1).rolling(lookback, min_periods=min_periods).median()
        st['closure_ratio'] = base / ref
        low = st.closure_ratio.notna() & (st.closure_ratio < frac)
        st.loc[low & (st.reason == ''), 'reason'] = 'library-wide total below closure threshold'
    st['month_ok'] = st.reason == ''
    return st


# ---------------- node x month ----------------
def node_month(wm, wt_level):
    """Weighted checkouts (sum of checkouts x strength) and number of works with checkouts per node and month."""
    x = wm[wm.checkouts > 0].merge(wt_level[['work_id', 'node_id', 'strength']], on='work_id')
    x['w'] = x.checkouts * x.strength
    return x.groupby(['node_id', 'mi']).agg(weighted_checkouts=('w', 'sum'), n_works_month=('work_id', 'nunique')).reset_index()


def rolling_distinct_works(wm, wt_level, grid, lookback):
    """Distinct works of each node with at least one checkout in months t-lookback .. t-1, for every t in grid.
    A run of active months with gaps <= lookback covers windows ending at first+1 .. last+lookback."""
    a = wm[wm.checkouts > 0][['work_id', 'mi']].drop_duplicates().sort_values(['work_id', 'mi'])
    nodes = sorted(wt_level.node_id.unique())
    out = np.zeros((len(nodes), len(grid)), dtype=np.int64)
    if a.empty:
        return pd.DataFrame(out, index=nodes, columns=grid)
    new_run = (a.work_id.diff() != 0) | (a.mi.diff() > lookback)
    a['run'] = new_run.cumsum()
    runs = a.groupby('run').agg(work_id=('work_id', 'first'), first=('mi', 'min'), last=('mi', 'max'))
    runs['start'] = runs['first'] + 1; runs['end'] = runs['last'] + lookback
    x = runs.merge(wt_level[['work_id', 'node_id']].drop_duplicates(), on='work_id')
    g0, g1 = int(grid[0]), int(grid[-1])
    x = x[(x.end >= g0) & (x.start <= g1)]
    ni = pd.Index(nodes).get_indexer(x.node_id)
    s = np.clip(x.start.to_numpy(), g0, g1 + 1) - g0
    e = np.clip(x.end.to_numpy(), g0 - 1, g1) - g0
    diff = np.zeros((len(nodes), len(grid) + 1), dtype=np.int64)
    np.add.at(diff, (ni, s), 1)
    np.add.at(diff, (ni, e + 1), -1)
    out = np.cumsum(diff[:, :-1], axis=1)
    return pd.DataFrame(out, index=nodes, columns=grid)


def size_columns(df, S):
    """Per node: median weighted checkouts over the previous S.size_lookback months (missing months skipped, zero
    months kept as zero), number of available months, and the size rule for a window starting at this month."""
    L = S.size_lookback
    need = min_size_months(L)
    df = df.sort_values(['node_id', 'mi']).copy()
    prev = df.groupby('node_id').weighted_checkouts.shift(1)
    df['_prev'] = prev
    g = df.groupby('node_id')['_prev']
    df['median_weighted_24m'] = g.transform(lambda s: s.rolling(L, min_periods=need).median())
    df['months_avail_24m'] = g.transform(lambda s: s.notna().astype(float).rolling(L, min_periods=1).sum()).astype(int)
    df['size_ok'] = ((df.n_works_24m >= S.min_works) & (df.median_weighted_24m >= S.min_median_weighted)
                     & (df.months_avail_24m >= need))
    return df.drop(columns='_prev')


def assemble(wm, wt_level, status, nodes, fmt, level, S):
    """Full node x month grid for one format and level, with shares, logs, counts and the size rule."""
    ok = status[status.month_ok].index.to_numpy()
    wm = wm[wm.mi.isin(ok)]
    grid = status.index.to_numpy()
    nm = node_month(wm, wt_level)
    ids = sorted(wt_level.node_id.unique())
    full = pd.MultiIndex.from_product([ids, grid], names=['node_id', 'mi']).to_frame(index=False)
    df = full.merge(nm, on=['node_id', 'mi'], how='left')
    df['month_ok'] = df.mi.map(status.month_ok)
    df['total_checkouts'] = df.mi.map(status.total_checkouts).where(df.month_ok)
    df['weighted_checkouts'] = df.weighted_checkouts.fillna(0.0).where(df.month_ok)
    df['n_works_month'] = df.n_works_month.fillna(0).astype(np.int64)
    df['share'] = df.weighted_checkouts / df.total_checkouts
    with np.errstate(divide='ignore'):
        df['log_share'] = np.where(df.share > 0, np.log(df.share.where(df.share > 0)), np.nan)   # zero or missing -> missing
    dw = rolling_distinct_works(wm, wt_level, grid, S.size_lookback)
    df['n_works_24m'] = dw.stack().reindex(pd.MultiIndex.from_frame(df[['node_id', 'mi']])).fillna(0).astype(np.int64).to_numpy()
    df = size_columns(df, S)
    df['format'] = fmt; df['level'] = level
    df['ym'] = [ym_of(m) for m in df.mi]
    df = df.merge(nodes[['node_id', 'parent', 'broad_id', 'label']], on='node_id', how='left')
    cols = ['level', 'node_id', 'parent', 'broad_id', 'label', 'format', 'ym', 'mi', 'month_ok', 'weighted_checkouts',
            'total_checkouts', 'share', 'log_share', 'n_works_month', 'n_works_24m', 'median_weighted_24m',
            'months_avail_24m', 'size_ok']
    return df[cols].sort_values(['node_id', 'mi']).reset_index(drop=True)


# ---------------- donor overlap ----------------
def overlap_pairs(wt_level, works_in_format, level, fmt):
    """For every ordered pair of nodes (a, b) at one level that share works: share_of_a = works in both / works in a.
    Works of a node = works assigned to it (strength > 0) with checkouts in that format.
    NOT IN RECORD: works are counted per format, over all months of data."""
    w = wt_level[wt_level.work_id.isin(works_in_format)][['work_id', 'node_id']].drop_duplicates()
    if w.empty:
        return pd.DataFrame(columns=['level', 'format', 'node_a', 'node_b', 'n_works_a', 'n_shared', 'share_of_a'])
    ni, nodes = pd.factorize(w.node_id)
    wi, _ = pd.factorize(w.work_id)
    B = sparse.csr_matrix((np.ones(len(w)), (ni, wi)), shape=(len(nodes), wi.max() + 1))
    C = (B @ B.T).tocoo()
    n = np.asarray(B.sum(axis=1)).ravel()
    m = C.row != C.col
    out = pd.DataFrame({'node_a': np.asarray(nodes)[C.row[m]], 'node_b': np.asarray(nodes)[C.col[m]],
                        'n_works_a': n[C.row[m]].astype(np.int64), 'n_shared': C.data[m].astype(np.int64)})
    out['share_of_a'] = out.n_shared / out.n_works_a
    out.insert(0, 'format', fmt); out.insert(0, 'level', level)
    return out


def node_table(N):
    """node_id, level name, parent, broad_id, label from theme_nodes."""
    T = N[['node_id', 'level', 'parent', 'label']].copy()
    T['level'] = T.level.map(LEVEL_NAME)
    T['broad_id'] = T.node_id.str.split('.').str[0]
    return T
