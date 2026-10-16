# Method benchmark, stage 2: paired comparisons between models (model comparison, not behavior) and the effect of behavior inside the "after a lasting rise" and
# other segments, with the A2 rows and the same intervals (category bootstrap 2,000 resamples, seed 20261015; month block bootstrap for the rank correlation).
# Descriptive additions to addendum b's F2 (which pairs the organizing question at the level of whole comparisons); no new pipeline.
# Output: data/db/benchmark/stage2_results/extra_pairs.csv.
# NOTE (16 Oct 2026): these pairs use the rows common to the pipelines of each pair, a larger sample than the main tables; the numbers quoted in the thesis come from
# 23_pairs_main_sample.py (extra_pairs_main_sample.csv), computed on the main-table rows. See prereg/DEVIATIONS.md, entry of 2026-10-16 08:15.
#   ../../../.venv/bin/python 19_extra_pairs.py
import sys, time, pathlib, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import _stage2_common as C

_spec = importlib.util.spec_from_file_location('ev', HERE / '03_evaluate.py'); EV = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(EV)
RES = EV.RES

MODEL_PAIRS = [('chronos', 'chronos2', 'newer pretrained forecaster against Chronos-Bolt'),
               ('catchg_D', 'chronos2', 'pretrained forecaster against CatBoost on the change (no behavior in either)'),
               ('catchg_D', 'chronos2_cur', 'pretrained forecaster with Wikipedia against CatBoost on the change'),
               ('lgbmchg_D', 'catchg_D', 'CatBoost against LightGBM on the change'),
               ('ridgechg_D', 'catchg_D', 'CatBoost against ridge on the change'),
               ('chronos2', 'median_s2_all', 'median of all learned models against the pretrained forecaster alone'),
               ('chronos2_cur', 'median_s2_all', 'median of all learned models against Chronos-2 with Wikipedia'),
               ('median_all', 'median_s2_all', 'median of all learned models against the stage-1 median'),
               ('catchg_D', 'median_s2_all', 'median of all learned models against CatBoost on the change')]
BEHAVIOR_PAIRS = [('chronos2', 'chronos2_cur'), ('chronos2', 'chronos2_curdw'), ('chronos2', 'chronos2_bk'), ('chronos2_cur', 'chronos2_curdw'),
                  ('catchg_D', 'catchg_DWS'), ('catchg_D', 'catchg_DVcurdw')]


def main():
    C.check_addendum()
    t0 = time.time()
    w = pd.read_parquet(EV.OUT / 'wide2.parquet')
    pe = (w.group == 'seattle') & w.format.isin(['print', 'ebook'])
    rows = []
    pipes = sorted({p for a, b, _ in MODEL_PAIRS for p in (a, b)} | {p for a, b in BEHAVIOR_PAIRS for p in (a, b)} | {'naive'})
    for h in (1, 2, 3):
        c = EV.Cmp(w, pe & (w.h == h), pipes, f'extra h{h}', nboot=EV.NBOOT, nboot_ap=200)
        if not c.ok:
            continue
        c.rise_table(with_mcs=False)
        c.surge_table(boot=False)
        for a, b, kind in MODEL_PAIRS:
            if a in c.pipes and b in c.pipes:
                rows.append(dict(segment='all', h=h, kind=kind, **c.pair(a, b)))
        print(f'{time.strftime("%H:%M:%S")} h={h} all done ({(time.time() - t0) / 60:.1f} min)', flush=True)
    for sname, smask in (('quiet', w.segment == 'quiet'), ('after short rise', w.segment == 'after_short_rise'), ('after lasting rise', w.segment == 'after_lasting_rise')):
        for h in (1, 2, 3):
            c = EV.Cmp(w, pe & (w.h == h) & smask, pipes, f'extra {sname} h{h}', min_months=1, nboot=EV.NBOOT, light=True)
            if not c.ok or c.series_n < 20:
                continue
            for a, b in BEHAVIOR_PAIRS:
                if a in c.pipes and b in c.pipes:
                    rows.append(dict(segment=sname, h=h, kind='behavior', series=c.series_n, rows=c.rows_n, **{k: v for k, v in c.pair(a, b).items() if k not in ('series',)}))
    pd.DataFrame(rows).to_csv(RES / 'extra_pairs.csv', index=False)
    print(f'{time.strftime("%H:%M:%S")} wrote extra_pairs.csv ({len(rows)} rows); {(time.time() - t0) / 60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
