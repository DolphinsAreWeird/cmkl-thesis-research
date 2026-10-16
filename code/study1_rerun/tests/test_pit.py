"""Run from code/:  ../.venv/bin/python -m unittest discover -s study1_rerun/tests -v"""
import os, sys, unittest
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from pit import narrator_pit_count
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))

class T(unittest.TestCase):
    def test_never_counts_later_release(self):
        t = pd.to_datetime(['2018-01-01', '2019-01-01', '2020-01-01', '2021-01-01'], utc=True)
        c = narrator_pit_count(['a'] * 4, t)
        self.assertTrue(np.allclose(c, np.log1p([0, 1, 2, 3])))      # target of 2018 sees none of the 3 later recordings

    def test_later_recordings_do_not_change_earlier_count(self):
        t = list(pd.to_datetime(['2018-01-01', '2019-06-01'], utc=True))
        base = narrator_pit_count(['a', 'a'], t)[1]
        more = narrator_pit_count(['a'] * 6, t + list(pd.to_datetime(['2020-01-01'] * 4, utc=True)))[1]
        self.assertEqual(base, more)

    def test_ties_and_other_narrators_and_missing(self):
        t = pd.to_datetime(['2018-01-01', '2018-01-01', '2017-01-01', None], utc=True)
        c = narrator_pit_count(['a', 'a', 'b', 'a'], t)
        self.assertEqual(c[0], 0); self.assertEqual(c[1], 0)       # same-time recordings are not 'before'
        self.assertEqual(c[2], 0); self.assertEqual(c[3], 0)       # other narrator ignored; missing date gives 0

    def test_random_bruteforce(self):
        rng = np.random.default_rng(0); n = 300
        nar = rng.integers(0, 15, n); t = pd.Timestamp('2016-01-01', tz='UTC') + pd.to_timedelta(rng.integers(0, 3000, n), unit='D')
        c = narrator_pit_count(nar, t)
        for i in range(n):
            self.assertAlmostEqual(c[i], np.log1p(((nar == nar[i]) & (t.values < t.values[i])).sum()))

    @unittest.skipUnless(os.path.exists(os.path.join(ROOT, 'data', 'processed', 'labels.parquet')), 'needs data')
    def test_real_data_no_later_counted(self):
        L = pd.read_parquet(os.path.join(ROOT, 'data', 'processed', 'labels.parquet'))
        c = narrator_pit_count(L.narrator_id, L.publicdate)
        k = np.rint(np.expm1(c)).astype(int)
        t = pd.to_datetime(L.publicdate, utc=True)
        for i in np.random.default_rng(1).choice(len(L), 40, replace=False):
            if pd.isna(L.narrator_id.iloc[i]) or pd.isna(t.iloc[i]): continue
            same = (L.narrator_id == L.narrator_id.iloc[i]).values
            self.assertEqual(k[i], int((same & (t < t.iloc[i]).values).sum()))
            self.assertLessEqual(k[i], int((same & (t <= t.iloc[i]).values).sum()) - 1)

if __name__ == '__main__': unittest.main()
