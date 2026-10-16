# Count panels for Study 3b: weighted checkouts per category, format and month at the narrow, middle and value levels,
# plus the usable-month status and exposure (all checkouts of the format that month) of each format.
# Weighted checkouts Y_{c,f,t} = sum over works of theme weight x checkouts (record, demand.counts):
#   narrow and middle: the Study 3 work_theme strength (main assignment, no title words);
#   value: the same rule applied to work_theme_value, i.e. per source the work's value weights become shares (sum 1 over
#   the values placed in a node), and a work's strength for a value is the mean share over the sources that have
#   evidence for the work (as 16_v3_assign.py does for nodes).
# The record-to-work mapping and the missing, partial and closure month rules are the Study 3 ones (the Study 3 functions
# are called, see _s3.py). Counts are stored sparsely: only positive counts in usable months (a usable month with no
# row is a zero). At the value level a format keeps only the values with >= 12 nonzero months in that format over all
# time (NOT IN RECORD): a value below that can never meet the feasibility rule of the record in any 24-month window.
import numpy as np, pandas as pd
from scipy import sparse
import _s3
from _methods import Counts

B3, I3 = _s3.build, _s3.inputs
VALUE_MIN_NONZERO = 12          # NOT IN RECORD: see above; equals the record's feasibility threshold (checked against S)
CHUNK = 36                      # months per sparse product


def value_strengths(EV, id_col):
    """EV: id_col (work_id or book_id), source, theme, weight, node_id. Values without a node are left out of the shares
    (as in the node assignment). Returns id_col, theme, node_id, strength with strength summing to 1 per work."""
    E = EV[EV.node_id.notna()].copy()
    E['share'] = E.weight / E.groupby([id_col, 'source']).weight.transform('sum')
    nsrc = E.groupby(id_col).source.nunique()
    E['strength'] = E.share / E[id_col].map(nsrc)
    out = E.groupby([id_col, 'theme'], as_index=False).agg(strength=('strength', 'sum'), node_id=('node_id', 'first'))
    return out


def theme_month_dense(wm, VS, id_col, grid0, T, ok_months):
    """Weighted checkouts of every value in every month: (n_themes, T) float64, theme order = sorted themes of VS.
    wm: work_id, mi, checkouts. Only usable months (ok_months, a set of mi) are filled; others stay 0 here."""
    themes = np.array(sorted(VS.theme.unique()))
    tcode = pd.Index(themes).get_indexer(VS.theme)
    works = np.sort(VS[id_col].unique())
    wpos = np.searchsorted(works, VS[id_col].to_numpy())
    Wm = sparse.csr_matrix((VS.strength.to_numpy(), (wpos, tcode)), shape=(len(works), len(themes)))
    x = wm[(wm.checkouts > 0) & wm.mi.isin(ok_months) & wm.work_id.isin(works)]
    wi = np.searchsorted(works, x.work_id.to_numpy())
    A = sparse.csc_matrix((x.checkouts.to_numpy(dtype=float), (wi, x.mi.to_numpy() - grid0)), shape=(len(works), T))
    D = np.zeros((len(themes), T))
    WT_ = Wm.T.tocsr()
    for a in range(0, T, CHUNK):
        R = WT_ @ A[:, a:a + CHUNK]
        D[:, a:a + CHUNK] = R.toarray()
    return themes, D


def sparse_rows(level, ids, D, fmt, grid0, keep=None):
    """Long table (level, node_id, format, mi, y) of the positive entries of D (rows = ids) for the kept rows."""
    if keep is not None:
        D, ids = D[keep], np.asarray(ids)[keep]
    r, c = np.nonzero(D > 0)
    return pd.DataFrame({'level': level, 'node_id': np.asarray(ids)[r], 'format': fmt, 'mi': (c + grid0).astype(np.int64),
                         'y': D[r, c]})


def node_dense(wm, wtl, ids, grid0, T, ok_months):
    """Node demand through the Study 3 function (node_month), as a dense (n_nodes, T) matrix."""
    x = wm[wm.mi.isin(ok_months)]
    nm = B3.node_month(x, wtl)
    D = np.zeros((len(ids), T))
    r = pd.Index(ids).get_indexer(nm.node_id)
    D[r, nm.mi.to_numpy() - grid0] = nm.weighted_checkouts.to_numpy()
    return D


# ---------------- dense Counts from the stored tables ----------------
def make_counts(long, status, level, ids, formats):
    """Counts for one level from the long table, the month status table (format, mi, month_ok, total_checkouts) and the
    category ids (order kept). Usable months without a row are zeros; unusable months are NaN."""
    st = status[status.format.isin(formats)]
    mi0, mi1 = int(st.mi.min()), int(st.mi.max())
    T = mi1 - mi0 + 1
    ids = np.asarray(ids)
    Y, N, ok = {}, {}, {}
    pos = pd.Index(ids)
    L = long[(long.level == level)]
    for f in formats:
        s = st[st.format == f].set_index('mi')
        okf = np.zeros(T, bool)
        okf[s.index.to_numpy() - mi0] = s.month_ok.to_numpy()
        n = np.full(T, np.nan)
        n[s.index.to_numpy() - mi0] = s.total_checkouts.to_numpy(dtype=float)
        n[~okf] = np.nan
        y = np.zeros((len(ids), T))
        g = L[L.format == f]
        r = pos.get_indexer(g.node_id)
        keep = r >= 0
        y[r[keep], g.mi.to_numpy()[keep] - mi0] = g.y.to_numpy()[keep]
        y[:, ~okf] = np.nan
        Y[f], N[f], ok[f] = y, n, okf
    return Counts(mi0, ids, Y, N, ok)
