# Backlist robustness for Study 3b (addendum prereg/addenda_3b/2026-10-14_b_backlist_robustness.json): demand restricted to
# works whose first checkout in any Seattle format is at least 13 months before month 0 of the test. Everything else as in 3b.
# The works that count depend on month 0, so the panel is built per month 0. Works are sorted by first-checkout month; the
# eligible works of a month 0 are a prefix of that order, so the weighted counts of all categories are built by adding the
# newly eligible works to a running sum (one pass over the data in total, not one per month 0).
# NOT IN RECORD (logged in prereg/DEVIATIONS.md, Study 3b table):
#  1. first checkout = the first month with checkouts > 0 for the work in any Seattle format, in any month of the data
#     (also months that are unusable as demand months); works already borrowed when the data start count from the data start;
#  2. exposure N is unchanged (all checkouts of the format that month); only Y is restricted;
#  3. the restriction applies to the treated category, the placebo categories and the placebo years alike, each at its own month 0;
#  4. LibriVox is not run (the restriction is defined on Seattle first checkouts);
#  5. the z tables of the backlist run are cached apart (ztables_backlist/).
import re, json, pathlib
import numpy as np, pandas as pd
from scipy import sparse
import _s3
import _inference as INF
import _methods as M
import _panel as PN

HERE = pathlib.Path(__file__).resolve().parent
ADDENDUM = HERE.parents[2] / 'prereg' / 'addenda_3b' / '2026-10-14_b_backlist_robustness.json'


def backlist_months():
    """The 13 of 'at least 13 months before month 0', read from the addendum's own wording."""
    t = json.loads(ADDENDUM.read_text())['changes']['robustness.backlist']
    m = re.search(r'at least (\d+) months before month 0', t)
    if not m:
        raise SystemExit('backlist addendum wording not understood (expected "at least N months before month 0")')
    return int(m.group(1))


BACKLIST_MONTHS = backlist_months()


def first_months(wms):
    """First month with checkouts > 0 per work over the given work-month tables (any format, any month of the data)."""
    parts = [w[w.checkouts > 0].groupby('work_id').mi.min() for w in wms]
    return pd.concat(parts).groupby(level=0).min()


def eligible_cut(first_sorted, m0, lag=None):
    """Number of works (a prefix of the works sorted by first month) with first checkout <= m0 - lag, that is at least
    `lag` months before month 0 (12 months before: excluded; 13: included). Works never borrowed (NaN, sorted last) never count."""
    lag = BACKLIST_MONTHS if lag is None else lag
    return int(np.searchsorted(first_sorted, m0 - lag, side='right'))


class Cumulative:
    """Running weighted counts of one level over the first `cut` works of the sorted order.
    Wm (works x categories, rows sorted by first month), A {format: (works x T) checkouts in usable months}."""

    def __init__(self, Wm, A, T, step=20000):
        self.Wm, self.A, self.T, self.step = Wm.tocsr(), {f: a.tocsr() for f, a in A.items()}, T, step
        self.reset()

    def reset(self):
        self.cut = 0
        self.D = {f: np.zeros((self.Wm.shape[1], self.T)) for f in self.A}

    def advance(self, cut):
        if cut < self.cut:
            self.reset()
        for a in range(self.cut, cut, self.step):
            b = min(cut, a + self.step)
            WT_ = self.Wm[a:b].T.tocsr()
            for f, A in self.A.items():
                self.D[f] += (WT_ @ A[a:b]).toarray()
        self.cut = cut
        return self.D

    def series(self, j, cut, f):
        """One category's weighted checkouts per month over the first `cut` works (no running state)."""
        if not hasattr(self, 'Wc'):
            self.Wc = self.Wm.tocsc()
        lo, hi = self.Wc.indptr[j], self.Wc.indptr[j + 1]
        rows, vals = self.Wc.indices[lo:hi], self.Wc.data[lo:hi]
        keep = rows < cut
        if not keep.any():
            return np.zeros(self.T)
        return np.asarray(vals[keep] @ self.A[f][rows[keep]].toarray()).ravel()


class Builder:
    """Everything needed to build backlist Counts for any month 0, per level; loaded once."""

    def __init__(self, levels, cats, status, formats, cum, first_sorted, cat_pos, keep=None):
        self.keep = keep or {}                       # keep[level][format]: bool per category row (value level: >= 12 nonzero months over all time, as in 01)
        self.levels, self.cats, self.status, self.formats = levels, cats, status, list(formats)
        self.cum, self.first_sorted, self.cat_pos = cum, first_sorted, cat_pos     # cat_pos[level]: category id -> row of the cumulative D (or -1)
        st = status[status.format.isin(self.formats)]
        self.mi0, self.mi1 = int(st.mi.min()), int(st.mi.max())
        self.T = self.mi1 - self.mi0 + 1
        self.N, self.ok = {}, {}
        for f in self.formats:
            s = st[st.format == f].set_index('mi')
            okf = np.zeros(self.T, bool)
            okf[s.index.to_numpy() - self.mi0] = s.month_ok.to_numpy()
            n = np.full(self.T, np.nan)
            n[s.index.to_numpy() - self.mi0] = s.total_checkouts.to_numpy(dtype=float)
            n[~okf] = np.nan
            self.N[f], self.ok[f] = n, okf

    def counts(self, level, m0):
        """Counts of all categories of the level at month 0 = m0 (the same category order as the main 3b panel)."""
        D = self.cum[level].advance(eligible_cut(self.first_sorted, m0))
        ids = np.asarray(sorted(self.cats[level].index))
        pos = self.cat_pos[level].reindex(ids).fillna(-1).to_numpy().astype(int)
        Y = {}
        for f in self.formats:
            y = np.zeros((len(ids), self.T))
            have = pos >= 0
            y[have] = D[f][pos[have]]
            kp = self.keep.get(level, {}).get(f)
            if kp is not None:
                y[have] *= kp[pos[have]][:, None]
            y[:, ~self.ok[f]] = np.nan
            Y[f] = y
        return M.Counts(self.mi0, ids, Y, self.N, self.ok)

    def row_counts(self, level, node, m0):
        """Counts of one category at month 0 = m0 (placebo years): the same fit as the full table gives for that row."""
        cum = self.cum[level]
        cut = eligible_cut(self.first_sorted, m0)
        j = self.cat_pos[level].get(node, -1)
        Y = {}
        for f in self.formats:
            y = np.zeros((1, self.T)) if j < 0 else cum.series(j, cut, f)[None, :]
            kp = self.keep.get(level, {}).get(f)
            if kp is not None and j >= 0 and not kp[j]:
                y = np.zeros((1, self.T))
            y[:, ~self.ok[f]] = np.nan
            Y[f] = y
        return M.Counts(self.mi0, np.asarray([node]), Y, self.N, self.ok)


def build_real(P, S, load_cats=True):
    """Builder from the real inputs (the same reading steps as 01_panels.build_seattle)."""
    I3, B3 = _s3.inputs, _s3.build
    src = I3.choose_source(P)
    WT, how, info = I3.load_work_theme(P, src)
    api, rw = I3.api_counts(P), I3.load_record_work(P)
    import _paths as IO
    EV = IO.read_parquet(P.taxo_v3 / 'work_theme_value.parquet')
    VS = PN.value_strengths(EV, 'work_id')
    status = pd.read_parquet(P.months)
    cats = pd.read_parquet(P.categories)
    cats = {lv: cats[cats.level == lv].set_index('node_id') for lv in S.levels_tested}
    strength = {lv: WT[WT.level == lv][['work_id', 'node_id', 'strength']] for lv in ('narrow', 'middle')}
    strength['value'] = VS.drop(columns='node_id').rename(columns={'theme': 'node_id'})[['work_id', 'node_id', 'strength']]
    works = np.sort(pd.concat([s.work_id for s in strength.values()]).astype(np.int64).unique())
    wms, okm = {}, {}
    for fmt in S.seattle_formats:
        wm, totals, st, raw = I3.format_month_data(P, S, fmt, rw, api)
        wms[fmt] = wm
        okm[fmt] = (set(st[st.month_ok].index.tolist()), int(st.index.min()), len(st))
    first = first_months(list(wms.values()))
    return assemble(S, strength, works, wms, okm, first, status, cats)


def assemble(S, strength, works, wms, okm, first, status, cats, formats=None):
    """Sort the works by first-checkout month and build the sparse pieces. strength[level]: work_id, node_id, strength.
    wms[format]: work_id, mi, checkouts; okm[format]: (usable months set, first month of the grid, number of months)."""
    formats = list(formats or S.seattle_formats)
    fw = first.reindex(works)
    order = np.argsort(fw.fillna(np.inf).to_numpy(), kind='stable')
    works_s = works[order]
    first_sorted = fw.to_numpy()[order].astype(float)
    first_sorted[np.isnan(first_sorted)] = np.inf
    st = status[status.format.isin(formats)]
    mi0, T = int(st.mi.min()), int(st.mi.max()) - int(st.mi.min()) + 1
    A = {}
    for f in formats:
        ok_set, g0, _ = okm[f]
        x = wms[f][(wms[f].checkouts > 0) & wms[f].mi.isin(ok_set) & wms[f].work_id.isin(works_s)]
        idx = np.argsort(works_s, kind='stable')               # works_s is sorted by first month, not by id
        wi = idx[np.searchsorted(works_s[idx], x.work_id.to_numpy())]
        A[f] = sparse.csr_matrix((x.checkouts.to_numpy(dtype=float), (wi, x.mi.to_numpy() - mi0)), shape=(len(works_s), T))
    cum, cat_pos, keep = {}, {}, {}
    idx = np.argsort(works_s, kind='stable')
    for lv, s in strength.items():
        nodes = np.array(sorted(s.node_id.unique()))
        r = idx[np.searchsorted(works_s[idx], s.work_id.to_numpy().astype(np.int64))]
        c = pd.Index(nodes).get_indexer(s.node_id)
        Wm = sparse.csr_matrix((s.strength.to_numpy(dtype=float), (r, c)), shape=(len(works_s), len(nodes)))
        cum[lv] = Cumulative(Wm, A, T)
        cat_pos[lv] = pd.Series(np.arange(len(nodes)), index=nodes)
        if lv == 'value':                    # the 3b panel keeps a value in a format only with >= 12 nonzero months over all time (01_panels)
            D = cum[lv].advance(len(works_s))
            keep[lv] = {f: (D[f] > 0).sum(1) >= PN.VALUE_MIN_NONZERO for f in formats}
            cum[lv].reset()
    return Builder(list(strength), cats, status, formats, cum, first_sorted, cat_pos, keep)


# ---------------- the world of a backlist run ----------------
class _CurMap(dict):
    """world.C for a backlist world: the Counts of a level at the world's current month 0 (one level held at a time)."""

    def __init__(self, world, keys):
        super().__init__()
        self.w, self._keys = world, list(keys)

    def __getitem__(self, k):
        if k not in self._keys:
            raise KeyError(k)
        return self.w.counts_at(k[1])

    def __contains__(self, k):
        return k in self._keys

    def __iter__(self):
        return iter(self._keys)

    def keys(self):
        return list(self._keys)


class BacklistWorld(INF.World):
    """The 3b World with demand restricted to backlist works at each month 0 (Seattle only)."""

    def __init__(self, P, S, shifts, builder):
        super().__init__(P, S, shifts)
        self.bl = builder
        self.zdir = P.db / 'ztables_backlist'
        self.m0cur, self._held = None, {}
        keys = [('seattle', lv) for lv in S.levels_tested]
        self.C = _CurMap(self, keys)
        self.parent_arr = INF.LazyDict(lambda k: self.cats[k[1]].parent.reindex(np.asarray(sorted(self.cats[k[1]].index))).to_numpy(), keys)
        self.placebo_years_fn = self._placebo_years

    def set_m0(self, m0):
        self.m0cur = int(m0)

    def counts_at(self, level):
        h = self._held.get(level)
        if h is None or h[0] != self.m0cur:
            self._held.pop(level, None)
            self._held[level] = (self.m0cur, self.bl.counts(level, self.m0cur))
        return self._held[level][1]

    def last_month(self, kind, level):
        return int(self.bl.mi1)

    def ztable(self, kind, level, m0, save=True):
        self.set_m0(m0)
        return super().ztable(kind, level, m0, save)

    def _placebo_years(self, world, kind, level, node, m0, real_z):
        S = self.S
        last = self.bl.mi1
        zs, years = [], []
        for yr in range(S.placebo_year_from, last // 12 + 1):
            m = yr * 12 + m0 % 12
            if yr == m0 // 12 or m + S.window_primary[1] > last or m + (S.es_fit_end - S.es_fit_len + 1) < self.bl.mi0:
                continue
            if self.has_shifts and self.shifted_near(level, node, m, S.placebo_cat_no_shift):
                continue
            C1 = self.bl.row_counts(level, node, m)
            es = M.event_study(C1, m, S, rows=[0])
            if es['feasible'][0] and not np.isnan(es['z_p'][0]):
                zs.append(float(es['z_p'][0])); years.append(yr)
        share, n = M.share_at_least(zs, real_z)
        return dict(py_years=json.dumps(years), py_share_ge=share, py_n=n)
