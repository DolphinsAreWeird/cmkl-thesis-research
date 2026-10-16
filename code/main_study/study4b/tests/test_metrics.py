# Part B metrics and the AP bootstrap on known cases.
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
from helpers import *


def test_average_precision_matches_scikit_learn_without_ties():
    from sklearn.metrics import average_precision_score
    rng = np.random.default_rng(0)
    for _ in range(5):
        y = (rng.random(400) < 0.1).astype(float)
        s = rng.random(400) + 0.5 * y
        assert abs(BM.average_precision(y, s) - average_precision_score(y, s)) < 1e-12
    assert BM.average_precision([1, 0, 0], [3, 2, 1]) == 1.0
    assert abs(BM.average_precision([0, 1, 0, 1], [4, 3, 2, 1]) - (1 / 2 + 2 / 4) / 2) < 1e-12
    assert np.isnan(BM.average_precision([0, 0], [1, 2]))


def test_brier_and_top_k_recall():
    assert BM.brier([1, 0], [1.0, 0.0]) == 0 and abs(BM.brier([1, 0], [0.5, 0.5]) - 0.25) < 1e-12
    df = pd.DataFrame(dict(origin_mi=[1] * 6 + [2] * 6, format='print', surge=[1, 0, 0, 0, 0, 1] + [0] * 6, score=[9, 8, 7, 1, 2, 3] + list(range(6))))
    rec, rnd, n, ng = BM.top_k_recall(df, 'score', 2, ['origin_mi', 'format'])
    assert (rec, n, ng) == (0.5, 2, 1)           # one of the two surges ranks in the top 2
    assert abs(rnd - (2 * 2 / 6) / 2) < 1e-12


def test_ap_difference_bootstrap_detects_a_better_score_and_not_a_noise_score():
    rng = np.random.default_rng(1)
    months = np.repeat(np.arange(60), 40)
    y = (rng.random(len(months)) < 0.08).astype(float)
    good = y * 1.5 + rng.random(len(y))
    noise_a, noise_b = rng.random(len(y)), rng.random(len(y))
    lo, hi, d = BM.ap_diff_bootstrap(months, y, noise_a, good, 3, 400, 7)
    assert lo > 0 and len(d) == 400
    lo, hi, _ = BM.ap_diff_bootstrap(months, y, noise_a, noise_b, 3, 400, 7)
    assert lo < 0 < hi
    assert BM.ap_diff_bootstrap(months, y, noise_a, good, 3, 100, 7)[:2] == BM.ap_diff_bootstrap(months, y, noise_a, good, 3, 100, 7)[:2]   # seeded


def test_helps_rule_needs_all_three_conditions():
    base = dict(skill=0.05, ci_lo=0.01, dm_p=0.01)
    assert M4h(base) and not M4h({**base, 'skill': -0.01}) and not M4h({**base, 'ci_lo': -0.01}) and not M4h({**base, 'dm_p': 0.06})


def M4h(r):
    return EV.M4.helps(r, B)
