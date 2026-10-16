"""Run from code/:  ../.venv/bin/python -m unittest discover -s study1_label_check/tests -v"""
import json, os, shutil, sys, tempfile, unittest
import numpy as np
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import labels as L
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))

def simulate(n=3000, seed=1, theta=3.0, sd_hi=0.15, sd_lo=0.5, mean_lo=0.4, mean_hi=-0.2):
    """Titles with known lasting level alpha and decay slope beta. Low-view titles decay differently
    (slower on average and with more spread) than high-view titles."""
    rng = np.random.default_rng(seed)
    alpha = rng.normal(2.0, 1.4, n)
    low = alpha < 2.0
    beta = np.where(low, rng.normal(mean_lo, sd_lo, n), rng.normal(mean_hi, sd_hi, n))
    rel_month = rng.integers(0, 12, n)
    ages = np.arange(1, 15)
    moy = (rel_month[:, None] + ages[None, :12]) % 12
    f = np.array([1.2, 0.7, 0.45, 0.3, 0.2, 0.1, 0.05, 0.0, -0.05, -0.1, -0.1, -0.15, -0.15, -0.15])
    g = 0.25 * np.sin(2 * np.pi * np.arange(12) / 12)
    la = np.log(ages) - np.log(np.arange(1, 13)).mean()
    moy14 = (rel_month[:, None] + ages[None, :]) % 12
    mu = np.exp(alpha[:, None] + f[None, :] + beta[:, None] * la[None, :] + g[moy14])
    counts = rng.negative_binomial(theta, theta / (theta + mu))
    return counts.astype(float), moy, alpha, beta, g

class TestL4(unittest.TestCase):
    def test_l4_beats_l0_when_low_view_titles_decay_differently(self):
        counts, moy, alpha, beta, _ = simulate()
        tr = np.arange(2000); te = np.arange(2000, 3000)
        out = L.step_labels(counts, moy, tr)
        r4 = spearmanr(out['L4'][te], alpha[te]).correlation
        r0 = spearmanr(out['L0'][te], alpha[te]).correlation
        low = te[alpha[te] < 2.0]
        r4_low = spearmanr(out['L4'][low], alpha[low]).correlation
        r0_low = spearmanr(out['L0'][low], alpha[low]).correlation
        print(f'\n  all test titles: L4 {r4:.3f} vs L0 {r0:.3f};  low-view titles: L4 {r4_low:.3f} vs L0 {r0_low:.3f}')
        self.assertGreater(r4, r0); self.assertGreater(r4_low, r0_low)

    def test_estimates_are_near_truth(self):
        counts, moy, alpha, beta, g = simulate(n=4000, seed=2)
        p = L.fit_L4(counts[:, :12], moy)
        print(f"\n  theta {p['theta']:.2f} (true 3.0), sigma_beta {p['sigma_beta']:.2f}, g range {np.ptp(p['g']):.2f} (true {np.ptp(g):.2f})")
        self.assertTrue(1.5 < p['theta'] < 6.0)
        self.assertLess(abs(np.ptp(p['g']) - np.ptp(g)), 0.15)
        self.assertTrue(p['f'][0] > p['f'][-1])

    def test_shrinkage_pulls_slopes_to_zero(self):
        counts, moy, *_ = simulate(n=1500, seed=3)
        p = L.fit_L4(counts[:, :12], moy)
        loose = dict(p, sigma_beta=5.0); tight = dict(p, sigma_beta=0.02)
        bl = L.apply_L4(loose, counts[:, :12], moy)['beta']; bt = L.apply_L4(tight, counts[:, :12], moy)['beta']
        self.assertLess(np.abs(bt).mean(), 0.1 * np.abs(bl).mean())

class TestNoLeakage(unittest.TestCase):
    def test_test_title_labels_ignore_other_test_titles(self):
        counts, moy, *_ = simulate(n=1200, seed=4)
        tr = np.arange(800); te = np.arange(800, 1200)
        base = L.step_labels(counts, moy, tr)
        c2 = counts.copy(); other = te[1:]                      # scramble every other test title
        rng = np.random.default_rng(0); c2[other] = rng.integers(0, 5000, c2[other].shape)
        alt = L.step_labels(c2, moy, tr)
        for k in ['L0', 'L2', 'L3', 'L4', 'launch']:
            self.assertTrue(np.array_equal(base[k][te[0]], alt[k][te[0]]), k)
        # fitted parameters depend on training titles only
        self.assertTrue(np.array_equal(base['p4']['f'], alt['p4']['f']) and base['p4']['theta'] == alt['p4']['theta'])
        self.assertTrue(np.array_equal(base['p3']['omega'], alt['p3']['omega']))

    def test_parameters_change_when_a_training_title_changes(self):
        counts, moy, *_ = simulate(n=1200, seed=4)
        tr = np.arange(800)
        base = L.step_labels(counts, moy, tr)
        c2 = counts.copy(); c2[5] = c2[5] * 50 + 100
        alt = L.step_labels(c2, moy, tr)
        self.assertFalse(np.array_equal(base['p4']['f'], alt['p4']['f']))   # the check can detect a real dependence

class TestRecordHash(unittest.TestCase):
    def test_real_record_matches_readme(self):
        rec = os.path.join(ROOT, 'prereg', 'study1_label_check_2026-10-13.json')
        exp = L.expected_hash_from_readme(os.path.join(ROOT, 'prereg', 'README.md'))
        self.assertEqual(L.verify_record(rec, exp), exp)

    def test_changed_record_fails(self):
        rec = os.path.join(ROOT, 'prereg', 'study1_label_check_2026-10-13.json')
        exp = L.expected_hash_from_readme(os.path.join(ROOT, 'prereg', 'README.md'))
        d = tempfile.mkdtemp(); p = os.path.join(d, 'copy.json')
        try:
            shutil.copy(rec, p); os.chmod(p, 0o600); L.verify_record(p, exp)
            with open(p) as fh: txt = fh.read().replace('2.9 times', '2.8 times')
            with open(p, 'w') as fh: fh.write(txt)
            with self.assertRaises(RuntimeError): L.verify_record(p, exp)
        finally:
            shutil.rmtree(d)

if __name__ == '__main__':
    unittest.main(verbosity=2)
