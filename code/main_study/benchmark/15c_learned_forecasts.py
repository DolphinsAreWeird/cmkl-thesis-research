# Method benchmark, stage 2f (f1), step 3: forecasts on the learned-category series (demand panel from 15b), horizon 1, demand-only pipelines of addendum b:
# naive, seasonal_naive, revert6, ridge_D, catboost_D, lightgbm_D (level), ridgechg_D, lgbmchg_D, catchg_D (change), chronos (Bolt), chronos2, and median_s2_demand.
# Same walk-forward rules, parameters and code paths as the taxonomy series (Study 4 features D, expanding window, retrained every origin, test origins as the record).
#   ../../../.venv/bin/python 15c_learned_forecasts.py --phase features|models|chronos|assemble|all [--workers 3]      (run under jobs/heavy_lock.sh)
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '1')
import sys, time, copy, pathlib, argparse, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import multiprocessing as mp
import _stage2_common as C
import _features as FT
import _models as M
import _settings as ST

OUT = C.OUT / 'learned'
H = 1
CAT = list(FT.CAT_COLS)
NUM = list(FT.D_NUM)
KL = ['group', 'format', 'level', 'node_id', 'origin_mi', 'h']
_W = {}


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


# ---------------- features ----------------
def phase_features():
    S = ST.settings()
    panel = pd.read_parquet(OUT / 'demand_panel.parquet')
    panel = panel[panel.level.isin(S.levels)]
    S1 = copy.copy(S); S1.horizons = (H,)
    F = FT.demand_table(panel, S1, H, True)
    F['group'] = 'learned'
    F['origin'] = [f'{m // 12:04d}-{m % 12 + 1:02d}' for m in F.origin_mi]
    F['change'] = F.y - F.ls_t
    F.to_parquet(OUT / 'features_learned.parquet', index=False)
    print(f'{time.strftime("%H:%M:%S")} features: {len(F):,} rows, {F.groupby(["format", "level"]).node_id.nunique().to_dict()}', flush=True)


# ---------------- models ----------------
def init_worker():
    F = pd.read_parquet(OUT / 'features_learned.parquet')
    LG = _load('lg', '01_lightgbm.py'); LG.PARAMS['n_jobs'] = 1
    _W.update(F=F, S=ST.settings(), LG=LG)


def run_origin(t):
    t0 = time.time()
    F, S, LG = _W['F'], _W['S'], _W['LG']
    te, tr = M.test_rows(F, t, H), M.training_rows(F, t, H)
    out = []
    if len(te) and len(tr) >= 30:
        assert (tr.origin_mi + H <= t).all()
        base = te[KL + ['tmonth']].copy()
        p, _ = M.fit_predict_ridge(tr, te, 'D', H, S); out.append(base.assign(pipe='ridge_D', y_hat=p))
        out.append(base.assign(pipe='catboost_D', y_hat=M.fit_predict_catboost(tr, te, 'D', S, 1)))
        out.append(base.assign(pipe='lightgbm_D', y_hat=LG.fit_predict(tr, te, 'D')))
        trc = tr.assign(y=tr['change'])
        a = M.choose_alpha(trc, NUM, CAT, H, S)
        out.append(base.assign(pipe='ridgechg_D', y_hat=te.ls_t.to_numpy(float) + M._ridge_fit_predict(trc, te, NUM, CAT, a)))
        out.append(base.assign(pipe='catchg_D', y_hat=te.ls_t.to_numpy(float) + M.fit_predict_catboost_cols(trc, te, NUM, CAT, S, 1)))
        import lightgbm as lgb
        cols = NUM + CAT
        Xtr, Xte = tr[cols].copy(), te[cols].copy()
        for c in CAT:
            cats = sorted(Xtr[c].astype(str).unique())
            Xtr[c] = pd.Categorical(Xtr[c].astype(str), categories=cats); Xte[c] = pd.Categorical(Xte[c].astype(str), categories=cats)
        pm = lgb.LGBMRegressor(**LG.PARAMS).fit(Xtr, tr['change'].to_numpy(float), categorical_feature=CAT).predict(Xte)
        out.append(base.assign(pipe='lgbmchg_D', y_hat=te.ls_t.to_numpy(float) + pm))
    df = pd.concat(out, ignore_index=True) if out else pd.DataFrame()
    p = OUT / 'parts' / f'origin_{ST.ym_of(t)}.parquet'
    df.to_parquet(p.with_suffix('.tmp'), index=False); os.replace(p.with_suffix('.tmp'), p)
    return t, len(df), time.time() - t0


def phase_models(workers):
    parts = OUT / 'parts'; parts.mkdir(exist_ok=True)
    S = ST.settings()
    F = pd.read_parquet(OUT / 'features_learned.parquet', columns=['origin_mi', 'y'])
    lo = ST.mi_from_ym(S.test_start)
    origins = sorted(int(m) for m in F[(F.origin_mi >= lo) & F.y.notna()].origin_mi.unique())
    todo = [m for m in origins if not (parts / f'origin_{ST.ym_of(m)}.parquet').exists()]
    print(f'{time.strftime("%H:%M:%S")} {len(origins)} origins, {len(todo)} to run; workers {workers} x 1 thread', flush=True)
    t0 = time.time()
    if todo:
        with mp.get_context('spawn').Pool(workers, initializer=init_worker) as pool:
            for i, (mi, n, sec) in enumerate(pool.imap_unordered(run_origin, todo), 1):
                el = time.time() - t0
                print(f'{time.strftime("%H:%M:%S")} origin {ST.ym_of(mi)}: {n} forecasts in {sec:.0f}s ({i}/{len(todo)}; {el / 60:.1f} min, about {el / i * (len(todo) - i) / 60:.0f} min left)', flush=True)
    P = pd.concat([pd.read_parquet(f) for f in sorted(parts.glob('origin_*.parquet'))], ignore_index=True)
    P.to_parquet(OUT / 'models_forecasts.parquet', index=False)
    print(f'{time.strftime("%H:%M:%S")} wrote models_forecasts.parquet ({len(P)} rows)', flush=True)


# ---------------- pretrained forecasters ----------------
def phase_chronos():
    os.environ['OMP_NUM_THREADS'] = '3'
    import torch
    torch.set_num_threads(3); torch.manual_seed(C.SEED)
    F = pd.read_parquet(OUT / 'features_learned.parquet')
    S = ST.settings()
    lo = ST.mi_from_ym(S.test_start)
    ser = ['group', 'format', 'level', 'node_id']
    hist = {k: g.droplevel(list(range(4))) for k, g in F.dropna(subset=['ls_t']).drop_duplicates(ser + ['origin_mi']).set_index(ser + ['origin_mi']).ls_t.sort_index().groupby(level=list(range(4)))}
    test = F[(F.origin_mi >= lo) & F.y.notna() & F.ls_t.notna()]
    keys = test[ser + ['origin_mi']].drop_duplicates().reset_index(drop=True)
    ctx, keep = [], []
    for r in keys.itertuples(index=False):
        s = hist.get((r.group, r.format, r.level, r.node_id))
        if s is None:
            continue
        s = s[s.index <= r.origin_mi]
        if len(s) == 0 or s.index.max() != r.origin_mi:
            continue
        ctx.append(s.reindex(np.arange(int(s.index.min()), int(r.origin_mi) + 1)).to_numpy(np.float32)[-512:]); keep.append(r)
    T = pd.DataFrame(keep, columns=ser + ['origin_mi'])
    print(f'{time.strftime("%H:%M:%S")} {len(T)} series-origins', flush=True)
    from chronos import BaseChronosPipeline, Chronos2Pipeline
    c2 = _load('c2', '09_chronos2.py'); c2.patch_loader()
    bolt = BaseChronosPipeline.from_pretrained('amazon/chronos-bolt-small', device_map='cpu', torch_dtype=torch.float32)
    pb = np.full(len(ctx), np.nan)
    for i in range(0, len(ctx), 256):
        q, _ = bolt.predict_quantiles([torch.tensor(x) for x in ctx[i:i + 256]], prediction_length=1, quantile_levels=[0.5])
        pb[i:i + 256] = q[..., 0].numpy()[:, 0]
    pipe = Chronos2Pipeline.from_pretrained(c2.MODEL, device_map='cpu', dtype=torch.float32, revision=c2.REVISION)
    p2 = np.full(len(ctx), np.nan)
    for i in range(0, len(ctx), 2048):
        q, _ = pipe.predict_quantiles([{'target': x} for x in ctx[i:i + 2048]], prediction_length=1, quantile_levels=[0.5], batch_size=128)
        p2[i:i + 2048] = np.array([x[0, 0, 0].item() for x in q])
    base = test[KL + ['tmonth']]
    for name, p in (('chronos', pb), ('chronos2', p2)):
        L = T.assign(y_hat=p, pipe=name)
        R = base.merge(L[ser + ['origin_mi', 'y_hat']], on=ser + ['origin_mi'], how='inner').assign(pipe=name)
        R.to_parquet(OUT / f'{name}_forecasts.parquet', index=False)
        print(f'{time.strftime("%H:%M:%S")} wrote {name}_forecasts.parquet ({len(R)} rows)', flush=True)


# ---------------- assemble ----------------
def phase_assemble():
    F = pd.read_parquet(OUT / 'features_learned.parquet')
    S = ST.settings()
    lo = ST.mi_from_ym(S.test_start)
    w = F[(F.origin_mi >= lo) & F.y.notna() & F.ls_t.notna()][KL + ['tmonth', 'y', 'ls_t', 'mean6', 'ls_ly', 'm12_last', 'm12_prev']].rename(columns={'y': 'y_true', 'ls_t': 'y_t'})
    w['naive'] = w.y_t
    w['seasonal_naive'] = w.ls_ly + w.m12_last - w.m12_prev
    w['revert6'] = w.mean6
    L = pd.concat([pd.read_parquet(f) for f in (OUT / 'models_forecasts.parquet', OUT / 'chronos_forecasts.parquet', OUT / 'chronos2_forecasts.parquet')], ignore_index=True)
    Wd = L.pivot_table(index=KL, columns='pipe', values='y_hat', aggfunc='first').reset_index()
    w = w.merge(Wd, on=KL, how='left')
    ds = ['ridge_D', 'lightgbm_D', 'catboost_D', 'ridgechg_D', 'lgbmchg_D', 'catchg_D', 'chronos2']
    w['median_s2_demand'] = w[ds].median(axis=1, skipna=False)
    w = w.drop(columns=['mean6', 'ls_ly', 'm12_last', 'm12_prev'])
    w['segment'] = None; w['surge'] = (w.y_true - w.y_t) >= np.log(1.3)
    w.to_parquet(OUT / 'wide_learned.parquet', index=False)
    print(f'{time.strftime("%H:%M:%S")} wrote wide_learned.parquet ({len(w):,} rows; pipelines with forecasts on all rows: {[c for c in ds + ["chronos"] if w[c].notna().all()]})', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', default='all')
    ap.add_argument('--workers', type=int, default=3)
    a = ap.parse_args()
    C.check_addendum()
    OUT.mkdir(parents=True, exist_ok=True)
    for ph in (['features', 'models', 'chronos', 'assemble'] if a.phase == 'all' else a.phase.split(',')):
        {'features': phase_features, 'models': lambda: phase_models(a.workers), 'chronos': phase_chronos, 'assemble': phase_assemble}[ph]()
