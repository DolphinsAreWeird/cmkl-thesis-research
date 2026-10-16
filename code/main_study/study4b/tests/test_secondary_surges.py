# Secondary surge definitions: the base-rate cut-off is computed on training rows only (no leakage), and the 20% definition is fixed.
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
from helpers import *
import _b_surge2 as SG
import _s4
from test_leakage import _base_world, _perturb, ORIGIN, BL


def _toy():
    rng = np.random.default_rng(3)
    rows = []
    for f in ('print', 'ebook'):
        for lv in ('narrow', 'middle'):
            for o in range(100, 140):
                for n in range(6):
                    rows.append(dict(format=f, level=lv, node_id=f'{lv}{n}', origin_mi=o, h=2, y=0.0, ls_t=0.0,
                                     change=rng.normal(0, 0.1) + (0.05 if f == 'print' else 0.0)))
    return pd.DataFrame(rows)


def test_base_rate_cutoff_equals_training_percentile_by_format_and_level():
    d = _toy()
    cut, fb = SG.surge_cutoffs(d, 'base98')
    for (f, lv), g in d.groupby(['format', 'level']):
        thr = float(cut[(cut.format == f) & (cut.level == lv)].thr.iloc[0])
        assert abs(thr - np.quantile(g.change, 0.98)) < 1e-12
    thr, lab = SG.apply_cutoffs(d, cut, fb)
    assert abs(np.nanmean(lab) - 0.02) < 0.01          # about 2% of the training rows by construction
    assert len(set(np.round(thr, 6))) == 4              # one cut-off per format and level


def test_cutoff_ignores_rows_that_are_not_training_rows():
    """Training rows of origin t are those with s + h <= t. Changing the change of any later row must not move the cut-off."""
    d = _toy()
    t = 130
    tr = _s4.models.training_rows(d, t, 2)
    late = d[(d.origin_mi + 2 > t)].index
    assert len(late) > 0 and len(tr) < len(d)
    d2 = d.copy(); d2.loc[late, 'change'] = 5.0
    c1, f1 = SG.surge_cutoffs(_s4.models.training_rows(d, t, 2), 'base98')
    c2, f2 = SG.surge_cutoffs(_s4.models.training_rows(d2, t, 2), 'base98')
    assert c1.equals(c2) and f1 == f2
    # a test row's own change does not enter its cut-off
    te = d2[d2.origin_mi == t]
    thr1, _ = SG.apply_cutoffs(te, c1, f1)
    thr2, _ = SG.apply_cutoffs(te.assign(change=9.0), c1, f1)
    assert (thr1 == thr2).all()


def test_pct20_is_log_1_2_everywhere():
    d = _toy()
    cut, fb = SG.surge_cutoffs(d, 'pct20')
    thr, lab = SG.apply_cutoffs(d, cut, fb)
    assert (thr == np.log(1.2)).all()
    assert (lab == (d.change >= np.log(1.2)).astype(float)).all()


def test_forecasts_and_cutoffs_at_an_origin_do_not_change_when_the_future_is_perturbed():
    w, e = _base_world()
    w2, e2 = _perturb(w, e)
    F1, F2 = features(w, e, BL), features(w2, e2, BL)
    for defn in SG.DEFS:
        f1 = SG.forecast_origin_surge(F1, ORIGIN, BL, defn, 1)
        f2 = SG.forecast_origin_surge(F2, ORIGIN, BL, defn, 1)
        assert len(f1) == len(f2) > 0 and set(f1.model) == {'catboost_clf', 'logistic'} and set(f1.h) == {2}
        k = ['model', 'fset', 'format', 'node_id']
        m = f1.merge(f2, on=k, suffixes=('_1', '_2'), validate='one_to_one')
        assert len(m) == len(f1)
        assert (m.thr_1 == m.thr_2).all() and (m.pred_1 == m.pred_2).all()
        assert not (m.target_1 == m.target_2).all()           # the future did change
