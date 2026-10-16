# Method benchmark, stage 2f (f1), step 4: score the demand-only pipelines on the learned-category series and, for comparison, on the subject-heading themes
# (same pipelines, same months, same level and format group), with the metrics of addendum b. Descriptive: the two category sets have different series, so their
# values are compared side by side, not tested against each other. Output: data/db/benchmark/stage2_results/learned_*.csv and data/reports/benchmark_stage2_learned.md.
#   ../../../.venv/bin/python 15d_learned_report.py
import sys, time, pathlib, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import _stage2_common as C

_spec = importlib.util.spec_from_file_location('ev', HERE / '03_evaluate.py'); EV = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(EV)
OUT = C.OUT / 'learned'
RES = EV.RES
PIPES = ['naive', 'seasonal_naive', 'revert6', 'ridge_D', 'catboost_D', 'lightgbm_D', 'ridgechg_D', 'lgbmchg_D', 'catchg_D', 'chronos', 'chronos2', 'median_s2_demand']


def main():
    C.check_addendum()
    RES.mkdir(parents=True, exist_ok=True)
    wl = pd.read_parquet(OUT / 'wide_learned.parquet')
    wt = pd.read_parquet(EV.OUT / 'wide2.parquet')
    wt = wt[wt.group == 'seattle']
    out, meta = {}, []
    for gname, fm in (('print and ebook', ['print', 'ebook']), ('audiobooks', ['audiobook'])):
        for lev in ('middle', 'narrow'):
            for src, w in (('learned from book text', wl), ('subject-heading themes', wt)):
                mask = w.format.isin(fm) & (w.level == lev) & (w.h == 1)
                c = EV.Cmp(w, mask, PIPES, f'{src} | {gname} | {lev}', nboot=EV.NBOOT)
                if not c.ok:
                    continue
                T = EV.full_table(c, boot_ap=True, with_mcs=True)
                key = f'{src}|{gname}|{lev}'
                out[key] = T
                T.assign(source=src, formats=gname, level=lev).to_csv(RES / f'learned_{src.split()[0]}_{gname.split()[0]}_{lev}.csv')
                meta.append(dict(source=src, formats=gname, level=lev, series=c.series_n, rows=c.rows_n, months=c.months_n, dropped=';'.join(c.dropped)))
                print(f'{time.strftime("%H:%M:%S")} {key}: {c.series_n} series, {c.rows_n} rows', flush=True)
    L = ['# Learned categories against subject-heading themes (stage 2f, demand-only pipelines, horizon 1)', '',
         f'Written {time.strftime("%Y-%m-%d %H:%M")}. Settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json (2f, f1). The two category sets have different series; values are compared side by side only.', '',
         pd.DataFrame(meta).to_csv(index=False, sep='|').replace('|', ' | '), '']
    for gname in ('print and ebook', 'audiobooks'):
        for lev in ('middle', 'narrow'):
            a, b = out.get(f'learned from book text|{gname}|{lev}'), out.get(f'subject-heading themes|{gname}|{lev}')
            if a is None or b is None:
                continue
            J = pd.DataFrame({'learned AvgRelMAE': a.AvgRelMAE, 'subject AvgRelMAE': b.AvgRelMAE, 'learned volume-weighted': a.VW_AvgRelMAE, 'subject volume-weighted': b.VW_AvgRelMAE,
                              'learned rank corr.': a.rho, 'subject rank corr.': b.rho, 'learned surge AP': a.AP, 'subject surge AP': b.AP,
                              'learned error %': a.mae_pct, 'subject error %': b.mae_pct}).reindex(PIPES)
            L += [f'## {gname}, {lev} themes', '', J.round(3).to_csv(sep='|').replace('|', ' | '), '']
            for nm, T in (('learned', a), ('subject-heading', b)):
                L.append(f'- confidence set, level task ({nm}): ' + ', '.join(T.index[T.in_MCS_level.fillna(False).astype(bool)]))
            L.append('')
    pathlib.Path(C.ST.DATA / 'reports' / 'benchmark_stage2_learned.md').write_text('\n'.join(L) + '\n')
    print('wrote benchmark_stage2_learned.md', flush=True)


if __name__ == '__main__':
    main()
