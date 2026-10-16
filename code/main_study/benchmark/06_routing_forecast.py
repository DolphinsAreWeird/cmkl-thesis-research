# Benchmark stage 2a: forecasts with the four volume features from the hand-curated routing (Wv_cur) and from the
# embedding routing of the daily top-500 pages (Wv_top); ridge and LightGBM, Seattle, horizon 1, Study 4 walk-forward
# rows. Then scoring with the benchmark evaluation. Rule: prereg/addenda_benchmark/2026-10-15_a_top_pages_routing.json.
import os
os.environ.setdefault('OMP_NUM_THREADS', '3')
import sys, time, pathlib, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import numpy as np, pandas as pd
import _settings as ST
import _models as M
import _features as FT

OUT = ST.DB / 'benchmark'
VOL = ['logmean4', 'ratio', 'dlog4', 'mk8']
KEYS = ['group', 'format', 'level', 'node_id', 'origin_mi', 'origin', 'h', 'tmonth']
_spec = importlib.util.spec_from_file_location('lg', HERE / '01_lightgbm.py'); LG = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(LG)
_spec = importlib.util.spec_from_file_location('ev', HERE / '03_evaluate.py'); EV = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(EV)


def vol_features(weekly, origins, S, prefix):
    X = FT.interest_frame(weekly[['node_id', 'week', 'share', 'partial_week']], None, None, 'wikipedia', origins, S)
    return X[['node_id', 'origin_mi'] + VOL].rename(columns={c: f'{prefix}_{c}' for c in VOL})


def lgbm(tr, te, num, cat):
    import lightgbm as lgb
    cols = num + cat
    Xtr = tr[cols].copy(); Xte = te[cols].copy()
    for c in cat:
        cats = sorted(Xtr[c].astype(str).unique())
        Xtr[c] = pd.Categorical(Xtr[c].astype(str), categories=cats); Xte[c] = pd.Categorical(Xte[c].astype(str), categories=cats)
    return lgb.LGBMRegressor(**LG.PARAMS).fit(Xtr, tr.y.to_numpy(float), categorical_feature=cat).predict(Xte)


def main():
    t0 = time.time()
    S = ST.settings()
    F = pd.read_parquet(ST.OUT / 'features.parquet')
    F = F[(F.group == 'seattle') & (F.h == 1)].copy()
    origins = sorted(F.origin_mi.unique())
    cur = pd.read_parquet(ST.DB / 'interest' / 'wiki' / 'weekly_node.parquet')
    cur = cur[cur.source == 'wikipedia']
    top = pd.read_parquet(OUT / 'top_routing' / 'weekly_node.parquet')
    for w, p in ((cur, 'cur'), (top, 'top')):
        F = F.merge(vol_features(w, origins, S, p), on=['node_id', 'origin_mi'], how='left')
    print(f'{time.strftime("%H:%M:%S")} features: cur present {F.cur_ratio.notna().mean():.0%}, top present {F.top_ratio.notna().mean():.0%}', flush=True)
    num_d, cat = FT.feature_columns('D')
    sets = {'Wcur': num_d + [f'cur_{c}' for c in VOL], 'Wtop': num_d + [f'top_{c}' for c in VOL]}
    lo = ST.mi_from_ym(S.test_start)
    tests = [m for m in origins if m >= lo and F[(F.origin_mi == m) & F.y.notna()].shape[0]]
    out = []
    for i, t in enumerate(tests, 1):
        te = M.test_rows(F, t, 1); tr = M.training_rows(F, t, 1)
        if len(te) == 0 or len(tr) < 30:
            continue
        base = te[KEYS].copy(); base['y_true'] = te.y.to_numpy(); base['y_t'] = te.ls_t.to_numpy()
        for nm, num in sets.items():
            a = M.choose_alpha(tr, num, cat, 1, S)
            out.append(base.assign(pipe=f'ridge_{nm}', y_hat=M._ridge_fit_predict(tr, te, num, cat, a)))
            out.append(base.assign(pipe=f'lightgbm_{nm}', y_hat=lgbm(tr, te, num, cat)))
        if i % 10 == 0:
            print(f'{time.strftime("%H:%M:%S")} {i}/{len(tests)} origins ({(time.time()-t0)/60:.1f} min)', flush=True)
    R = pd.concat(out, ignore_index=True)
    R.to_parquet(OUT / 'routing_forecasts.parquet', index=False)
    # scoring
    w = pd.read_parquet(OUT / 'wide.parquet')
    w = w[(w.group == 'seattle') & (w.h == 1)][EV.K + ['tmonth', 'y_true', 'y_t', 'naive', 'ridge_D', 'lightgbm_D']]
    w = w.merge(R.pivot_table(index=EV.K, columns='pipe', values='y_hat').reset_index(), on=EV.K, how='left')
    pipes = ['naive', 'ridge_D', 'ridge_Wcur', 'ridge_Wtop', 'lightgbm_D', 'lightgbm_Wcur', 'lightgbm_Wtop']
    tabs, metas = [], []
    for name, mask in (('R1. Print and ebook, horizon 1', w.format.isin(['print', 'ebook'])), ('R2. Seattle audiobooks, horizon 1', w.format == 'audiobook')):
        T, meta, _ = EV.comparison(w, name, mask, pipes)
        tabs.append(T); metas.append(meta)
    rep = []
    for model in ('ridge', 'lightgbm'):
        for a, b in ((f'{model}_D', f'{model}_Wcur'), (f'{model}_D', f'{model}_Wtop'), (f'{model}_Wcur', f'{model}_Wtop')):
            Sx, _ = EV.series_scores(w[w.format.isin(['print', 'ebook'])], ['naive', a, b])
            T = EV.avg_rel(pd.DataFrame({'naive': Sx[a], 'x': Sx[b]}), ['x'])
            rep.append(dict(base=a, other=b, ratio=T.AvgRelMAE.iloc[0], ci_lo=T.ci_lo.iloc[0], ci_hi=T.ci_hi.iloc[0],
                            share_other_better=T.share_beats_naive.iloc[0], series=len(Sx)))
    rep = pd.DataFrame(rep)
    pd.concat(tabs).to_csv(OUT / 'routing_summary.csv'); rep.to_csv(OUT / 'routing_paired.csv', index=False)
    p = ST.DATA / 'reports' / 'benchmark_top_routing.md'
    L = [p.read_text(), '', '## Forecasts with each routing (four volume features, no shift states)', '',
         pd.DataFrame(metas).to_csv(index=False, sep='|').replace('|', ' | ')]
    for T in tabs:
        L += [f'### {T.comparison.iloc[0]}', '', EV.fmt(T), '']
    L += ['### Paired ratios (print and ebook): geometric mean of MAE(other) / MAE(base)', '', rep.round(3).to_csv(index=False, sep='|').replace('|', ' | '),
          '', f'Run time {(time.time()-t0)/60:.1f} min.']
    p.write_text('\n'.join(L) + '\n')
    print(f'{time.strftime("%H:%M:%S")} wrote {p}', flush=True)


if __name__ == '__main__':
    main()
