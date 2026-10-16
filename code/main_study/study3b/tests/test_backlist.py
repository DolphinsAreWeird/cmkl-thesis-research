# Tests of the backlist filter (_backlist.py): a work first borrowed 12 months before month 0 is excluded, 13 months before included.
import sys, pathlib, types
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
import _backlist as BL
import _methods as M

MI0, T, M0 = 1000, 40, 1030


def _build(firsts, formats=('print',)):
    """One category 'c' to which every work contributes with strength 1; each work is borrowed 5 times a month from its first month on."""
    works = np.arange(len(firsts), dtype=np.int64) + 10
    rows = [dict(work_id=int(w), mi=mi, checkouts=5) for w, f in zip(works, firsts) if f is not None for mi in range(f, MI0 + T)]
    wm = pd.DataFrame(rows)
    status = pd.DataFrame([dict(format=f, mi=MI0 + i, month_ok=True, total_checkouts=1000, n_rows=10, reason='') for f in formats for i in range(T)])
    S = types.SimpleNamespace(seattle_formats=formats)
    first = BL.first_months([wm])
    strength = {'narrow': pd.DataFrame(dict(work_id=works, node_id='c', strength=1.0))}
    okm = {f: (set(range(MI0, MI0 + T)), MI0, T) for f in formats}
    cats = {'narrow': pd.DataFrame(index=pd.Index(['c'], name='node_id'))}
    b = BL.assemble(S, strength, works, {f: wm for f in formats}, okm, first, status, cats)
    return b, works


def test_lag_is_read_from_the_addendum():
    assert BL.BACKLIST_MONTHS == 13


def test_work_first_borrowed_12_months_before_is_excluded_13_included():
    b, works = _build([M0 - 12, M0 - 13])            # work 10: 12 months before month 0 (excluded); work 11: 13 months before (included)
    C = b.counts('narrow', M0)
    y = C.Y['print'][0]
    assert np.all(y[: (M0 - 13) - MI0] == 0)         # nothing before the included work's first month
    assert np.all(y[(M0 - 13) - MI0:] == 5.0), y     # only work 11 counts, in every month from its first month on (also after month 0)
    b2, _ = _build([M0 - 12, M0 - 13])
    assert BL.eligible_cut(b2.first_sorted, M0) == 1
    assert BL.eligible_cut(b2.first_sorted, M0 + 1) == 2     # one month later the 12-month work has aged into the backlist


def test_later_works_and_never_borrowed_works_are_excluded_older_included():
    b, _ = _build([M0 - 14, M0 - 13, M0 - 12, M0 - 1, M0 + 3, None])
    y = b.counts('narrow', M0).Y['print'][0]
    assert y[-1] == 10.0                              # the two works first borrowed at least 13 months before


def test_running_sum_and_single_category_series_agree_and_reset_on_going_back():
    b, _ = _build([M0 - 30, M0 - 20, M0 - 13, M0 - 5, M0 + 2])
    full = {m: b.counts('narrow', m).Y['print'][0].copy() for m in (M0 - 10, M0, M0 + 10)}
    for m, y in full.items():
        r = b.row_counts('narrow', 'c', m).Y['print'][0]
        assert np.allclose(r, y), m
    back = b.counts('narrow', M0 - 10).Y['print'][0]          # going back in time rebuilds from scratch
    assert np.allclose(back, full[M0 - 10])
    assert full[M0 + 10][-1] > full[M0][-1] > full[M0 - 10][-1]


def test_unusable_months_are_nan_and_exposure_is_not_restricted():
    b, _ = _build([M0 - 20])
    b.ok['print'][5] = False
    C = b.counts('narrow', M0)
    assert np.isnan(C.Y['print'][0, 5]) and np.allclose(C.N['print'][~np.isnan(C.N['print'])], 1000.0)
