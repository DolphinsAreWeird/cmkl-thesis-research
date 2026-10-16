# Final unseen test (prereg/addenda_benchmark/2026-10-17_c_final_test_forecasts.json): the forecasts of the final-test pipelines at one origin.
# Everything here reuses the benchmark's own code paths, so that a pipeline at a new origin is the same pipeline as in the main comparison:
#   features and eligibility  Study 4 / Study 4b builders (study4/_features.py, study4b/_b_features.py), the stored demand panel and interest series
#   catchg_D, catchg_DW, catchg_DWS   Study 4 CatBoost on the change, fit_predict_catboost_cols (as study4b/_b_models.py and 10_change_models.py)
#   chronos (Bolt)                    02_chronos.py contexts at horizons 1 and 2, the union-history contexts of 11_level_h3.py at horizon 3
#   chronos2, chronos2_cur, chronos2_curdw, chronos2_bk   09_chronos2.py (inputs, covariates, model revision), horizons 1 to 3 from one call
# The only difference from the benchmark runs: the test rows of the new origin have no observed target yet (the target month is not released),
# so the rows are taken without the `y.notna()` filter of Study 4's test_rows. Training rows are unchanged: origins s with s + h <= t and a known target.
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '3')
import sys, json, copy, time, hashlib, pathlib, importlib, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import _stage2_common as C            # puts study4 first on sys.path: _settings, _features, _models below are Study 4's
import _settings as ST
import _features as FT
import _models as M

STUDY4B = HERE.parent / 'study4b'
ADDENDUM_C = ST.PREREG / 'addenda_benchmark' / '2026-10-17_c_final_test_forecasts.json'
FINAL_DIR = ST.PREREG / 'final_test'
OUT = ST.DB / 'final_test'
SEED = 20261013
HORIZONS = (1, 2, 3)
# the final-test list (addendum b: naive, the stage-1 confidence set, the level and the rise confidence sets of A2) and the added reference chronos2
PIPELINES = ['naive', 'chronos', 'chronos2', 'chronos2_cur', 'chronos2_curdw', 'chronos2_bk', 'catchg_D', 'catchg_DW', 'catchg_DWS']
LIST_PIPELINES = [p for p in PIPELINES if p != 'chronos2']
CHRONOS2_VARIANTS = ['chronos2', 'chronos2_cur', 'chronos2_curdw', 'chronos2_bk']
CATCHG_FSETS = {'catchg_D': list(FT.D_NUM),
                'catchg_DW': list(FT.D_NUM) + list(FT.W_NUM),
                'catchg_DWS': list(FT.D_NUM) + list(FT.W_NUM) + ['s_sustained', 's_resp']}
CAT = list(FT.CAT_COLS)
MIN_TRAIN = 30
K = C.K                                            # group, format, level, node_id, origin_mi, h


# ---------------- loading ----------------
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_4b():
    """Study 4b's feature module and settings (they share module names with Study 4's, so 4b's folder goes last on the path and its settings
    file is loaded under another name)."""
    if str(STUDY4B) not in sys.path:
        sys.path.append(str(STUDY4B))
    import _b_features as BF
    B = load_module('s4b_settings', STUDY4B / '_settings.py').settings()
    return BF, B


def sha256_file(path, block=1 << 22):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def check_addendum_c():
    """The protocol record must be the one printed in prereg/README.md (nothing runs on an edited record)."""
    text = (ST.PREREG / 'README.md').read_text()
    name = ADDENDUM_C.name
    i = text.find(name)
    if i < 0:
        raise SystemExit(f'{name} is not listed in prereg/README.md')
    import re
    m = re.search(r'SHA-256:\s*([0-9a-f]{64})', text[i:i + 600])
    if not m:
        raise SystemExit(f'no SHA-256 printed for {name} in prereg/README.md')
    got = sha256_file(ADDENDUM_C)
    if got != m.group(1):
        raise SystemExit(f'{name} changed: {got} is not the {m.group(1)} in prereg/README.md; nothing runs')
    return json.loads(ADDENDUM_C.read_text()), got


def versions():
    import importlib.metadata as md
    names = ['pandas', 'numpy', 'scikit-learn', 'lightgbm', 'catboost', 'arch', 'torch', 'chronos-forecasting', 'transformers', 'pyarrow', 'scipy']
    v = {n: md.version(n) for n in names}
    v['python'] = sys.version.split()[0]
    return v


# ---------------- feature table ----------------
def build_table(BF, B, panel_months_upto=None):
    """The Study 4b feature table for Seattle, horizons 1 to 3, built from the stored panel and interest series, INCLUDING rows whose target month is
    not observed (drop_missing_target=False). Returns (full table with S features, change and surge, inputs used)."""
    D = ST.DB
    panel = pd.read_parquet(D / 'study3' / 'demand_panel.parquet')
    nodes = pd.read_parquet(D / 'study3' / 'nodes.parquet')
    meta = json.loads((D / 'study3' / 'demand_panel_meta.json').read_text())
    if meta.get('development') or meta.get('settings_sha256') != ST.sha256_of(ST.PREREG / 'study3_settings_2026-10-13.json'):
        raise SystemExit('the demand panel is a development build or was built with another Study 3 record')
    wiki = pd.read_parquet(D / 'interest' / 'wiki' / 'weekly_node.parquet')
    shifts = pd.read_parquet(D / 'interest' / 'shifts.parquet')
    sw = pd.read_parquet(D / 'interest' / 'shift_weekly.parquet')
    effects = pd.read_parquet(D / 'study3' / 'shift_effects.parquet')
    S4 = B.s4
    S4h = copy.copy(S4)
    S4h.horizons = B.horizons
    if tuple(B.horizons) != HORIZONS:
        raise SystemExit(f'4b horizons are {B.horizons}, expected {HORIZONS}')
    if panel_months_upto is not None:
        panel = panel[panel.mi <= panel_months_upto]
    full = FT.build_features(panel[panel.format.isin(S4.seattle_formats)], nodes, wiki, shifts, sw, None, S4h, 'seattle', drop_missing_target=False)
    keep = ['group', 'format', 'level', 'node_id', 'broad_id', 'origin_mi', 'origin', 'h', 'target_mi', 'tmonth', 'target_ok', 'y'] \
        + FT.D_NUM + ['m12_last', 'm12_prev'] + FT.W_NUM + ['split_qok_shift8', 'last_week']
    F = BF.add_s_and_targets(full[keep], shifts, effects, B)
    F = F.sort_values(['h', 'origin_mi', 'format', 'node_id']).reset_index(drop=True)
    inputs = dict(panel=D / 'study3' / 'demand_panel.parquet', nodes=D / 'study3' / 'nodes.parquet', weekly_node=D / 'interest' / 'wiki' / 'weekly_node.parquet',
                  shifts=D / 'interest' / 'shifts.parquet', shift_weekly=D / 'interest' / 'shift_weekly.parquet', shift_effects=D / 'study3' / 'shift_effects.parquet',
                  features_study4=D / 'study4' / 'features.parquet', features_study4b=D / 'study4b' / 'features.parquet',
                  monthly_cov=C.OUT / 'monthly_cov.parquet')
    return F, inputs


def check_against_stored(F, atol=1e-9):
    """Rows of the rebuilt table that have an observed target must equal the stored Study 4b table (every feature, S feature and target)."""
    old = pd.read_parquet(ST.DB / 'study4b' / 'features.parquet')
    keys = ['group', 'format', 'level', 'node_id', 'origin_mi', 'h']
    new = F[F.target_ok]
    if len(new) != len(old):
        raise SystemExit(f'rebuilt table has {len(new):,} rows with a target, the stored 4b table has {len(old):,}')
    cols = [c for c in old.columns if c not in keys and old[c].dtype.kind in 'fiub']
    m = old[keys + cols].merge(new[keys + cols], on=keys, suffixes=('_a', '_b'), validate='one_to_one')
    if len(m) != len(old):
        raise SystemExit('rebuilt and stored tables have different keys')
    worst = {}
    for c in cols:
        a, b = m[c + '_a'].to_numpy(float), m[c + '_b'].to_numpy(float)
        if not np.allclose(a, b, atol=atol, equal_nan=True):
            raise SystemExit(f'rebuilt column {c} differs from the stored Study 4b table (max {np.nanmax(np.abs(a - b)):.3g})')
        worst[c] = float(np.nanmax(np.abs(a - b))) if len(a) else 0.0
    return worst


# ---------------- histories (contexts of the pretrained forecasters) ----------------
def history(tables):
    """{(group, format, level, node_id): Series of the log share at every origin where a row exists in any of the tables} (as _stage2_common.history,
    on the given tables; rows of different tables for the same series and origin must agree)."""
    H = pd.concat([t[C.SER + ['origin_mi', 'ls_t']] for t in tables], ignore_index=True).dropna(subset=['ls_t'])
    chk = H.groupby(C.SER + ['origin_mi']).ls_t.agg(['min', 'max'])
    assert (chk['max'] - chk['min']).abs().max() < 1e-9, 'ls_t differs between tables for the same series and origin'
    H = H.drop_duplicates(C.SER + ['origin_mi']).set_index(C.SER + ['origin_mi']).ls_t.sort_index()
    return {k: g.droplevel(list(range(len(C.SER)))) for k, g in H.groupby(level=list(range(len(C.SER))))}


def study4_seattle_table(F, t_new=None):
    """The rows of the Study 4 table (horizons 1 and 2) on which the stage-1 Chronos-Bolt context was built: the stored Study 4 rows, plus, for a new origin
    t_new whose target months are not observed, the rebuilt rows at h = 1, 2 of that origin only (rows of older origins whose target is missing stay out,
    as in the benchmark: a month enters a context only where a row of the table exists)."""
    old = pd.read_parquet(ST.DB / 'study4' / 'features.parquet', columns=C.SER + ['origin_mi', 'h', 'ls_t'])
    old = old[old.group == 'seattle']
    if t_new is None:
        return old
    new = F[(F.h.isin((1, 2))) & (F.origin_mi == t_new)][C.SER + ['origin_mi', 'h', 'ls_t']]
    return pd.concat([old, new], ignore_index=True)


def table_for_history(F, t_new=None):
    """Rows of the rebuilt table that make up the union history (the stored Study 4b rows, which have an observed target, plus the rows of the new origin)."""
    return F[F.target_ok | (F.origin_mi == t_new)] if t_new is not None else F[F.target_ok]


# ---------------- the pipelines ----------------
def test_rows_open(F, t, h):
    """Rows at origin t and horizon h: the target need not be observed (the benchmark's test_rows also asks for y)."""
    return F[(F.h == h) & (F.origin_mi == t) & F.ls_t.notna()]


def forecast_catchg(F, t, S, thread_count=1, fsets=None, horizons=HORIZONS):
    """CatBoost on the change at origin t for horizons 1 to 3 and the feature sets D, D+W, D+W+S; level forecast = y(t) + predicted change.
    Training rows: origins s with s + h <= t and a known target (study4/_models.training_rows). Returns long rows: keys + pipe + y_hat + n_train."""
    out = []
    for h in horizons:
        te = test_rows_open(F, t, h)
        tr = M.training_rows(F, t, h)
        if len(te) == 0 or len(tr) < MIN_TRAIN:
            continue
        assert (tr.origin_mi + h <= t).all() and (tr.target_mi <= t).all() and tr.change.notna().all()
        trc = tr.assign(y=tr['change'])
        base = te[K].copy()
        base['n_train'] = len(tr)
        for pipe, num in CATCHG_FSETS.items():
            if fsets and pipe not in fsets:
                continue
            p = M.fit_predict_catboost_cols(trc, te, num, CAT, S, thread_count)
            out.append(base.assign(pipe=pipe, y_hat=te.ls_t.to_numpy(float) + p))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def bolt_contexts(hist, keys, t, max_len=512):
    """Contexts as 02_chronos.py: the series' log share up to and including month t (missing months stay missing), at most the last 512 months."""
    ctx, keep = [], []
    for r in keys.itertuples(index=False):
        s = hist.get((r.group, r.format, r.level, r.node_id))
        if s is None:
            continue
        s = s[s.index <= t]
        if len(s) == 0 or s.index.max() != t:
            continue
        ctx.append(s.reindex(range(int(s.index.min()), int(t) + 1)).to_numpy(float)[-max_len:])
        keep.append(r)
    return pd.DataFrame(keep, columns=list(keys.columns)), ctx


def forecast_bolt(pipe, hist4, hist_union, rows_keys, t, batch=256):
    """Chronos-Bolt (small, zero-shot, univariate): horizons 1 and 2 from the Study 4 history contexts, horizon 3 from the union-history contexts."""
    import torch
    out = []
    keys4, ctx4 = bolt_contexts(hist4, rows_keys, t)
    preds = np.full((len(ctx4), 2), np.nan)
    for i in range(0, len(ctx4), batch):
        q, _ = pipe.predict_quantiles([torch.tensor(c, dtype=torch.float32) for c in ctx4[i:i + batch]], prediction_length=2, quantile_levels=[0.5])
        preds[i:i + batch] = q[..., 0].numpy()
    for h in (1, 2):
        out.append(keys4.assign(h=h, y_hat=preds[:, h - 1]))
    keys3, ctx3 = bolt_contexts(hist_union, rows_keys, t)
    p3 = np.full(len(ctx3), np.nan)
    for i in range(0, len(ctx3), batch):
        q, _ = pipe.predict_quantiles([torch.tensor(c, dtype=torch.float32) for c in ctx3[i:i + batch]], prediction_length=3, quantile_levels=[0.5])
        p3[i:i + batch] = q[..., 0].numpy()[:, 2]
    out.append(keys3.assign(h=3, y_hat=p3))
    R = pd.concat(out, ignore_index=True)
    R['origin_mi'] = t
    R['pipe'] = 'chronos'
    return R


def forecast_chronos2(pipe, c2, hist_union, covs, rows_keys, t, variants=CHRONOS2_VARIANTS, chunk=2048, batch=128):
    """Chronos-2 (zero-shot) with and without past covariates, via 09_chronos2.py's own build_tasks; one call gives t+1, t+2, t+3."""
    out, info = [], {}
    base = rows_keys.assign(origin_mi=t)
    for v in variants:
        T, inputs = c2.build_tasks(base, hist_union, covs, v)
        Y = []
        for i in range(0, len(inputs), chunk):
            q, _ = pipe.predict_quantiles(inputs[i:i + chunk], prediction_length=3, quantile_levels=[0.5], batch_size=batch)
            Y.append(np.stack([x[0, :, 0].numpy() for x in q]))
        Y = np.concatenate(Y) if Y else np.zeros((0, 3))
        for h in HORIZONS:
            out.append(T.assign(h=h, y_hat=Y[:, h - 1], pipe=v))
        info[v] = {int(k): int(n) for k, n in T.ncov.value_counts().sort_index().items()}
    R = pd.concat(out, ignore_index=True)
    return R[C.K + ['pipe', 'y_hat', 'ncov']], info


def load_chronos2():
    c2 = load_module('c2', HERE / '09_chronos2.py')
    import torch
    torch.set_num_threads(3)
    torch.manual_seed(SEED)
    c2.patch_loader()
    from chronos import Chronos2Pipeline
    pipe = Chronos2Pipeline.from_pretrained(c2.MODEL, device_map='cpu', dtype=torch.float32, revision=c2.REVISION)
    return c2, pipe


def load_bolt():
    import torch
    torch.set_num_threads(3)
    torch.manual_seed(SEED)
    from chronos import BaseChronosPipeline
    return BaseChronosPipeline.from_pretrained('amazon/chronos-bolt-small', device_map='cpu', torch_dtype=torch.float32)


def forecast_origin(F, t, S, c2, pipe2, bolt, covs, hist4, hist_union, thread_count=1, pipelines=PIPELINES, log=print, horizons=HORIZONS):
    """All final-test pipelines at origin t, for every row of the table at that origin (horizons 1 to 3). Returns the long table (K + pipe + y_hat),
    the wide table and a dict of facts (training sizes, covariate counts)."""
    rows = F[(F.origin_mi == t) & F.ls_t.notna()]
    keys = rows[C.SER].drop_duplicates().reset_index(drop=True)
    parts, facts = [], {}
    t0 = time.time()
    if 'naive' in pipelines:
        for h in horizons:
            te = test_rows_open(F, t, h)
            parts.append(te[K].assign(pipe='naive', y_hat=te.ls_t.to_numpy(float)))
    if 'chronos' in pipelines:
        R = forecast_bolt(bolt, hist4, hist_union, keys, t)[K + ['pipe', 'y_hat']]
        parts.append(R[R.h.isin(horizons)])
        log(f'  chronos done ({time.time() - t0:.0f}s)')
    v2 = [v for v in CHRONOS2_VARIANTS if v in pipelines]
    if v2:
        R, info = forecast_chronos2(pipe2, c2, hist_union, covs, keys, t, v2)
        parts.append(R[R.h.isin(horizons)][K + ['pipe', 'y_hat']])
        facts['covariates_per_task'] = info
        log(f'  chronos2 variants done ({time.time() - t0:.0f}s): {info}')
    cg = [p for p in CATCHG_FSETS if p in pipelines]
    if cg:
        R = forecast_catchg(F, t, S, thread_count, fsets=cg, horizons=horizons)
        parts.append(R[K + ['pipe', 'y_hat']])
        facts['n_train'] = {int(h): int(g.n_train.iloc[0]) for h, g in R.groupby('h')}
        log(f'  catchg done ({time.time() - t0:.0f}s): training rows {facts["n_train"]}')
    L = pd.concat(parts, ignore_index=True)
    dup = L.duplicated(K + ['pipe'], keep=False)
    if dup.any():
        raise SystemExit(f'{int(dup.sum())} duplicate forecasts for the same row and pipeline')
    W = L.pivot_table(index=K, columns='pipe', values='y_hat', aggfunc='first').reset_index()
    meta = F[(F.origin_mi == t)][K + ['broad_id', 'origin', 'target_mi', 'tmonth', 'ls_t', 'y']]
    W = meta.merge(W, on=K, how='left')
    return L, W, facts
