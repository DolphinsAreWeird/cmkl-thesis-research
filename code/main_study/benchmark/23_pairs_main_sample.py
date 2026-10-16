# Method benchmark, stage 2: the model-against-model comparisons and the effect of behavior inside the kinds of month, recomputed on the SAME rows as the main
# tables (the rows on which every pipeline of the 52-pipeline roster has a forecast; the segments of segments.csv). 19_extra_pairs.py used the rows common to
# the few pipelines of each pair, which is a larger sample (39,402 rows against 36,081 at one month), so its model gaps could not be read against the tables.
# Descriptive; no new pipeline, same intervals (category bootstrap, 2,000 resamples, seed 20261015).
# Output: data/db/benchmark/stage2_results/extra_pairs_main_sample.csv
#   ../../../.venv/bin/python 23_pairs_main_sample.py
import sys, time, pathlib, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import _stage2_common as C

_spec = importlib.util.spec_from_file_location('ev', HERE / '03_evaluate.py'); EV = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(EV)
_spec2 = importlib.util.spec_from_file_location('xp', HERE / '19_extra_pairs.py'); XP = importlib.util.module_from_spec(_spec2); _spec2.loader.exec_module(XP)
RES = EV.RES


def main():
    C.check_addendum()
    t0 = time.time()
    w = pd.read_parquet(EV.OUT / 'wide2.parquet')
    _, ROSTER, _ = EV.roster()
    ROSTER = ROSTER + [c for c in w.columns if c.endswith('_DVdem') and c not in ROSTER]
    pe = (w.group == 'seattle') & w.format.isin(['print', 'ebook'])
    rows = []
    for h in (1, 2, 3):
        c = EV.Cmp(w, pe & (w.h == h), ROSTER, f'pairs h{h}', nboot=EV.NBOOT, light=True)
        if not c.ok:
            continue
        print(f'h={h}: {c.rows_n} rows, {c.series_n} series, {len(c.pipes)} pipelines', flush=True)
        for a, b, kind in XP.MODEL_PAIRS:
            if a in c.pipes and b in c.pipes:
                rows.append(dict(segment='all', h=h, kind=kind, rows=c.rows_n, **c.pair(a, b)))
    pipes = [p for p in ROSTER if p in w.columns]
    for sname, smask in (('quiet', w.segment == 'quiet'), ('after short rise', w.segment == 'after_short_rise'), ('after lasting rise', w.segment == 'after_lasting_rise')):
        for h in (1, 2, 3):
            c = EV.Cmp(w, pe & (w.h == h) & smask, pipes, f'pairs {sname} h{h}', min_months=1, nboot=EV.NBOOT, light=True)
            if not c.ok or c.series_n < 20:
                continue
            for a, b in XP.BEHAVIOR_PAIRS:
                if a in c.pipes and b in c.pipes:
                    rows.append(dict(segment=sname, h=h, kind='behavior', rows=c.rows_n, **c.pair(a, b)))
    pd.DataFrame(rows).to_csv(RES / 'extra_pairs_main_sample.csv', index=False)
    print(f'wrote extra_pairs_main_sample.csv ({len(rows)} rows); {(time.time() - t0) / 60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
