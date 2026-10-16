# Final unseen test, part 1 (addendum c): the forecasts of the final-test pipelines at one origin, frozen before the target months are released.
#   --mode regression --origins 2026-07,2024-06   run the same code at known origins and compare with the stored benchmark forecasts (must agree)
#   --mode timesafety --origin 2026-08            interest features and Chronos-2 covariates at the origin do not change when later weeks are altered
#   --mode final --origin 2026-08                 the frozen forecasts: stops if the origin has an observed target; writes prereg/final_test/*
# Run under the heavy-job lock:  bash jobs/bg.sh NAME main_study/benchmark/_locked.py 25_final_test_forecast.py --mode final --origin 2026-08
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '3')
import sys, json, time, pathlib, argparse, datetime
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import _final_test as FTS
import _stage2_common as C
import _settings as ST
import _features as FT

REPORT = ST.DATA / 'reports' / 'benchmark_final_test_regression.md'


def say(msg):
    print(f'{time.strftime("%H:%M:%S")} {msg}', flush=True)


def prepare():
    BF, B = FTS.load_4b()
    say('building the feature table from the stored panel and interest series (all rows, including those without an observed target)')
    F, inputs = FTS.build_table(BF, B)
    say(f'table: {len(F):,} rows; origins {ST.ym_of(F.origin_mi.min())} to {ST.ym_of(F.origin_mi.max())}')
    worst = FTS.check_against_stored(F)
    say(f'rebuilt rows with a target equal the stored Study 4b table (largest difference over {len(worst)} columns: {max(worst.values()):.2e})')
    return BF, B, F, inputs


def load_models(pipelines):
    c2 = pipe2 = bolt = None
    if any(p in pipelines for p in FTS.CHRONOS2_VARIANTS):
        c2, pipe2 = FTS.load_chronos2()
        say('Chronos-2 loaded')
    else:
        c2 = FTS.load_module('c2', HERE / '09_chronos2.py')
    if 'chronos' in pipelines:
        bolt = FTS.load_bolt()
        say('Chronos-Bolt loaded')
    return c2, pipe2, bolt


def regression(a):
    origins = [ST.mi_from_ym(x) for x in a.origins.split(',')]
    pipelines = a.pipelines.split(',') if a.pipelines else FTS.PIPELINES
    BF, B, F, inputs = prepare()
    S = ST.settings()
    c2, pipe2, bolt = load_models(pipelines)
    covs = c2.load_covariates()
    hist_union = FTS.history([FTS.table_for_history(F)])
    hist4 = FTS.history([FTS.study4_seattle_table(F)])
    stored = pd.read_parquet(ST.DB / 'benchmark' / 'wide2.parquet', columns=C.K + [p for p in pipelines if p != 'naive'] + ['y_t', 'y_true'])
    stored = stored[stored.group == 'seattle']
    lines = ['# Final test, regression check: the final-test code at known origins against the stored benchmark forecasts', '',
             f'Written {time.strftime("%Y-%m-%d %H:%M")}. Code: code/main_study/benchmark/25_final_test_forecast.py (mode regression). The same code that makes the frozen forecasts '
             'is run at origins whose target months are known, and its forecasts are compared row by row with the forecasts stored from the benchmark '
             '(data/db/benchmark/wide2.parquet). Differences are in log-share units.', '',
             '| Origin | Horizon | Pipeline | Rows compared | Rows only in one | Max abs difference | Mean abs difference | Rows differing by more than 1e-4 |',
             '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |']
    ok_all = True
    for t in origins:
        say(f'origin {ST.ym_of(t)}')
        hs = [h for h in FTS.HORIZONS if F[(F.origin_mi == t) & (F.h == h)].y.notna().any()]      # horizons whose target month is known
        L, W, facts = FTS.forecast_origin(F, t, S, c2, pipe2, bolt, covs, hist4, hist_union, thread_count=a.threads, pipelines=pipelines, log=lambda m: say(m), horizons=hs)
        known = F[(F.origin_mi == t) & F.y.notna()][C.K]
        L = L.merge(known, on=C.K, how='inner')                      # compare only rows whose target month is observed (the stored benchmark rows)
        st = stored[stored.origin_mi == t]
        for p in pipelines:
            for h in hs:
                mine = L[(L['pipe'] == p) & (L['h'] == h)][C.K + ['y_hat']]
                if p == 'naive':
                    ref = st[st.h == h][C.K + ['y_t']].rename(columns={'y_t': 'ref'})
                else:
                    ref = st[(st.h == h)][C.K + [p]].rename(columns={p: 'ref'}).dropna(subset=['ref'])
                m = mine.merge(ref, on=C.K, how='outer', indicator=True)
                both = m[m._merge == 'both']
                only = int((m._merge != 'both').sum())
                if len(both) == 0:
                    lines.append(f'| {ST.ym_of(t)} | {h} | {p} | 0 | {only} | | | |')
                    ok_all = False
                    say(f'  NOTHING TO COMPARE: {ST.ym_of(t)} h={h} {p}: mine {len(mine)} rows, stored {len(ref)} rows')
                    continue
                d = (both.y_hat - both.ref).abs()
                bad = int((d > 1e-4).sum())
                lines.append(f'| {ST.ym_of(t)} | {h} | {p} | {len(both):,} | {only:,} | {d.max():.2e} | {d.mean():.2e} | {bad} |')
                if bad or (only and p != 'naive'):
                    ok_all = False
                    say(f'  DIFFERENT: {ST.ym_of(t)} h={h} {p}: {bad} rows differ by more than 1e-4 (max {d.max():.3g}); rows only in one side: {only}')
    lines += ['', 'Result: ' + ('every compared forecast agrees with the stored one within 1e-4.' if ok_all else 'DIFFERENCES FOUND (see the rows above); the final forecasts must not be made until they are explained.'), '']
    REPORT.write_text('\n'.join(lines))
    say(f'wrote {REPORT}; all agree: {ok_all}')
    if not ok_all:
        sys.exit(1)


def timesafety(a):
    """Alter every weekly value after the last included week of the origin month; the interest features of that origin and the monthly covariates
    that Chronos-2 receives must not change."""
    t = ST.mi_from_ym(a.origin)
    BF, B = FTS.load_4b()
    S = ST.settings()
    D = ST.DB
    wiki = pd.read_parquet(D / 'interest' / 'wiki' / 'weekly_node.parquet')
    shifts = pd.read_parquet(D / 'interest' / 'shifts.parquet')
    sw = pd.read_parquet(D / 'interest' / 'shift_weekly.parquet')
    L = FT.last_week_monday(t)
    rng = np.random.default_rng(20261017)
    # (1) weekly interest series and shift states
    w2, sw2, sh2 = wiki.copy(), sw.copy(), shifts.copy()
    late = pd.to_datetime(w2.week) > L
    noise = rng.uniform(0.2, 5.0, size=int(late.sum()))
    for c in ('share', 'views'):
        w2.loc[late, c] = w2.loc[late, c].to_numpy() * noise
    lw = pd.to_datetime(sw2.week) > L
    sw2.loc[lw, 'ratio'] = sw2.loc[lw, 'ratio'].to_numpy() * rng.uniform(0.2, 5.0, size=int(lw.sum()))
    lab_late = pd.to_datetime(sh2.label_week) > L
    sh2.loc[lab_late, 'label'] = rng.choice(['sustained', 'intermediate', 'fading'], size=int(lab_late.sum()))
    start_late = pd.to_datetime(sh2.start_week) > L
    sh2.loc[start_late, 'start_week'] = pd.to_datetime(sh2.loc[start_late, 'start_week']) + pd.Timedelta(days=7)
    a1 = FT.interest_frame(wiki[wiki.source == 'wikipedia'], shifts, sw, 'wikipedia', [t], S)
    a2 = FT.interest_frame(w2[w2.source == 'wikipedia'], sh2, sw2, 'wikipedia', [t], S)
    cols = [c for c in a1.columns if c not in ('last_week', 'node_id')]
    x1, x2 = a1.set_index('node_id')[cols].sort_index(), a2.set_index('node_id')[cols].sort_index()
    same = x1.shape == x2.shape and (x1.index == x2.index).all() and np.allclose(x1.to_numpy(float), x2.to_numpy(float), equal_nan=True)
    say(f'interest features of {ST.ym_of(t)} unchanged when weeks after {L.date()} are altered: {same} ({len(x1)} nodes)')
    ok = same
    # (2) S features
    f_a = BF.sustained_flags(shifts, [t], B)
    f_b = BF.sustained_flags(sh2, [t], B)
    same_s = set(map(tuple, f_a[['node_id', 'origin_mi']].to_numpy())) == set(map(tuple, f_b[['node_id', 'origin_mi']].to_numpy()))
    say(f's_sustained at {ST.ym_of(t)} unchanged: {same_s} ({len(f_a)} nodes flagged)')
    ok &= same_s
    # (3) monthly covariates of Chronos-2 and the duration-weighted interest, through 07_stage2_features' own self test
    s2 = FTS.load_module('s2', HERE / '07_stage2_features.py')
    weeklies = {n: s2.load_weekly(n) for n in ('cur', 'bkb', 'bka')}
    s2.selftest(weeklies, origins_test=(a.origin,))
    say('Chronos-2 covariates (curated series, duration-weighted interest, book and author series) unchanged by later weeks: True')
    if not ok:
        sys.exit(1)


def final(a):
    t = ST.mi_from_ym(a.origin)
    addendum, addendum_sha = FTS.check_addendum_c()
    BF, B, F, inputs = prepare()
    S = ST.settings()
    at = F[F.origin_mi == t]
    if len(at) == 0:
        raise SystemExit(f'no rows at origin {a.origin}: the stored demand panel does not reach it')
    if at.y.notna().any() or F[F.target_mi > t].y.notna().any() or F.origin_mi.max() != t:
        raise SystemExit(f'origin {a.origin} is not the last origin without an observed target; the final forecasts are made only at such an origin')
    pipelines = FTS.PIPELINES
    c2, pipe2, bolt = load_models(pipelines)
    covs = c2.load_covariates()
    hist_union = FTS.history([FTS.table_for_history(F, t)])
    hist4 = FTS.history([FTS.study4_seattle_table(F, t)])
    say(f'forecasting origin {a.origin}: {len(at):,} rows ({at.groupby("h").size().to_dict()}), pipelines {pipelines}')
    L, W, facts = FTS.forecast_origin(F, t, S, c2, pipe2, bolt, covs, hist4, hist_union, thread_count=a.threads, pipelines=pipelines, log=say)
    missing = {p: int(W[p].isna().sum()) for p in pipelines}
    say(f'forecasts missing per pipeline (rows without a forecast): {missing}')
    W = W.copy()
    W['target_month'] = [ST.ym_of(m) for m in W.target_mi]
    out_cols = ['group', 'format', 'level', 'node_id', 'broad_id', 'origin', 'h', 'target_month', 'ls_t'] + pipelines
    out = W[out_cols].sort_values(['h', 'format', 'level', 'node_id']).reset_index(drop=True)
    FTS.FINAL_DIR.mkdir(parents=True, exist_ok=True)
    FTS.OUT.mkdir(parents=True, exist_ok=True)
    csv = FTS.FINAL_DIR / f'forecasts_origin_{a.origin}.csv'
    out.to_csv(csv, index=False, float_format='%.10g')
    W.to_parquet(FTS.OUT / f'forecasts_origin_{a.origin}_wide.parquet', index=False)
    L.to_parquet(FTS.OUT / f'forecasts_origin_{a.origin}_long.parquet', index=False)
    csv_sha = FTS.sha256_file(csv)
    meta = dict(
        what='Frozen forecasts of the final-test pipelines (addendum c) at one origin, for target months that were not released when they were made.',
        origin=a.origin, horizons=list(FTS.HORIZONS), targets=sorted(out.target_month.unique()),
        made_at=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        addendum=ADD_NAME, addendum_sha256=addendum_sha, csv=csv.name, csv_sha256=csv_sha,
        rows=int(len(out)), rows_by_horizon_format_level={f'h{h}_{f}_{l}': int(n) for (h, f, l), n in out.groupby(['h', 'format', 'level']).size().items()},
        pipelines=pipelines, missing_forecasts=missing, facts=facts,
        last_demand_month=ST.ym_of(int(pd.read_parquet(ST.DB / 'study3' / 'demand_panel.parquet', columns=['mi']).mi.max())),
        last_complete_interest_week=str(pd.read_parquet(ST.DB / 'interest' / 'wiki' / 'weekly_total.parquet').query('not partial_week').week.max().date()),
        interest_weeks_used_up_to=str(FT.last_week_monday(t).date()),
        input_sha256={k: FTS.sha256_file(v) for k, v in inputs.items()}, software=FTS.versions(),
        settings=dict(study4_record_sha256=B.sha256_study4, study4b_record_sha256=B.sha256, catboost=dict(iterations=S.cb_iterations, depth=S.cb_depth, learning_rate=S.cb_learning_rate,
                      loss=S.cb_loss, seed=S.cb_seed), chronos2_model=c2.MODEL, chronos2_revision=c2.REVISION, bolt_model='amazon/chronos-bolt-small', seed=FTS.SEED),
        note='Forecasts are log shares of a theme in a format (Study 4 target). The target months are scored once, as addendum d will fix; nothing about them was looked at.')
    (FTS.FINAL_DIR / f'forecasts_origin_{a.origin}_meta.json').write_text(json.dumps(meta, indent=1))
    say(f'wrote {csv} ({len(out):,} rows, sha256 {csv_sha}) and the meta file')


ADD_NAME = FTS.ADDENDUM_C.name

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', required=True, choices=['regression', 'timesafety', 'final'])
    ap.add_argument('--origins', default='2026-07')
    ap.add_argument('--origin', default='2026-08')
    ap.add_argument('--pipelines', default=None)
    ap.add_argument('--threads', type=int, default=1, help='CatBoost threads')
    a = ap.parse_args()
    {'regression': regression, 'timesafety': timesafety, 'final': final}[a.mode](a)
