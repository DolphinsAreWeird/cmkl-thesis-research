# The script chain on simulated data: 01 report holds no target values; 02 is resumable and respects the origin rules;
# 03 and 04 write their reports and CSVs.
import sys, os, re, subprocess, importlib, pathlib, copy, time
HERE = pathlib.Path(__file__).resolve().parent
STUDY = HERE.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(STUDY))
import numpy as np, pandas as pd
import _settings as ST, _features as FE, _forecast as FC
import sim

S = ST.settings()
MI = ST.mi_from_ym


def _world_features():
    w = sim.make_world(beta=1.0, seed=41, with_gdelt=True)
    w['nodes'].loc[w['nodes'].node_id == 'B01.M01', 'label'] = 'Race and racism'
    w['nodes'].loc[w['nodes'].node_id == 'B01.M02.N01', 'label'] = 'Epidemics and plagues'
    F = sim.build(w, S)
    lw = sim.make_world(beta=1.0, seed=42, formats=('librivox',), start='2017-01')
    L = sim.build(lw, S, group='librivox')
    return w, pd.concat([F, L], ignore_index=True)


def _run(script, *args):
    env = dict(os.environ)
    r = subprocess.run([sys.executable, str(STUDY / script), *args], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-3000:]
    return r.stdout


def test_01_report_has_counts_only():
    mod = importlib.import_module('01_features')
    w, F = _world_features()
    rep = mod.make_report(F, S, {'build_id': 'sim'}, {1: 5, 2: 7})
    assert '## Rows' in rep and '## Missing rate per feature' in rep and 'w_logmean4' in rep
    assert not re.search(r'-\d+\.\d{2,}', rep)                         # no negative decimals: no log-share target values
    assert 'y_true' not in rep and '| y |' not in rep
    for v in F.y.dropna().sample(30, random_state=0):
        assert f'{v:.3f}' not in rep


def test_02_forecast_runs_resumes_and_scores_only_observed_months(tmp_path):
    w, F = _world_features()
    feat = tmp_path / 'features.parquet'
    F.to_parquet(feat, index=False)
    out = tmp_path / 'out'
    t0 = time.time()
    log = _run('02_forecast.py', '--features', str(feat), '--out-dir', str(out), '--workers', '2', '--limit-origins', '2')
    assert '2 test origins (2019-01 to 2019-02)' in log and 'wrote' in log
    parts = sorted((out / 'forecast_parts').glob('origin_*.parquet'))
    assert [p.stem for p in parts] == ['origin_2019-01', 'origin_2019-02']
    fc = pd.read_parquet(out / 'forecasts.parquet')
    assert set(fc.group) == {'seattle', 'librivox'} and set(fc.h) == {1, 2}
    assert set(fc.model) == {'naive', 'seasonal_naive', 'ridge', 'catboost'}
    assert set(fc[fc.model == 'catboost'].fset) == set(S.feature_sets)          # GDELT sets run at origins up to 2021-05
    assert fc.y_true.notna().all() and fc.y_t.notna().all()
    assert ((fc.origin_mi + fc.h) > fc.origin_mi).all() and fc.origin_mi.between(MI('2019-01'), MI('2019-02')).all()
    # resume: a second run does no work
    mt = [p.stat().st_mtime for p in parts]
    log2 = _run('02_forecast.py', '--features', str(feat), '--out-dir', str(out), '--workers', '2', '--limit-origins', '2')
    assert '2 already saved, 0 to run' in log2 and [p.stat().st_mtime for p in parts] == mt
    # one more origin is added to the saved ones
    log3 = _run('02_forecast.py', '--features', str(feat), '--out-dir', str(out), '--workers', '2', '--limit-origins', '3')
    assert '2 already saved, 1 to run' in log3
    assert pd.read_parquet(out / 'forecasts.parquet').origin.nunique() == 3
    # changed features: refuse to mix with saved parts
    F2 = F.copy(); F2.loc[F2.index[0], 'ls_t'] += 1
    f2 = tmp_path / 'features2.parquet'; F2.to_parquet(f2, index=False)
    r = subprocess.run([sys.executable, str(STUDY / '02_forecast.py'), '--features', str(f2), '--out-dir', str(out), '--limit-origins', '2'],
                       capture_output=True, text=True)
    assert r.returncode != 0 and 'reset' in (r.stderr + r.stdout)


def test_gdelt_sets_stop_after_the_gdelt_period():
    assert FC.feature_sets_for(MI('2021-05'), S) == list(S.feature_sets)
    assert FC.feature_sets_for(MI('2021-06'), S) == ['D', 'D+W']
    assert FC.feature_sets_for(MI('2019-01'), S) == list(S.feature_sets)


def test_03_evaluate_and_04_interest_flow(tmp_path):
    w, F = _world_features()
    S2 = copy.copy(S); S2.cb_iterations = 25
    F1 = F[F.group == 'seattle']
    parts = []
    for t in range(MI('2019-01'), MI('2021-08')):
        parts.append(FC.forecast_origin(F, t, S2, 1))
    fc = pd.concat(parts, ignore_index=True)
    d = tmp_path
    fc.to_parquet(d / 'forecasts.parquet', index=False); F.to_parquet(d / 'features.parquet', index=False)
    w['nodes'].to_parquet(d / 'nodes.parquet', index=False)
    rep = d / 'reports'
    _run('03_evaluate.py', '--forecasts', str(d / 'forecasts.parquet'), '--features', str(d / 'features.parquet'),
         '--reports-dir', str(rep), '--nodes', str(d / 'nodes.parquet'))
    md = (rep / 'study4_03_evaluation.md').read_text()
    for head in ('## 1. Main comparison', '## 2. Helps-rule verdicts', '## 3. Secondary metrics', '## 4. Conditional split',
                 '## 5. Horizon 2', '## 6. GDELT and tone', '## 7. LibriVox', '## 8. Showcase cases'):
        assert head in md, head
    assert '—' not in md and '–' not in md                                     # no em or en dashes in the report
    main = pd.read_csv(rep / 'study4_03_main_comparison.csv')
    assert {'format x level', 'formats pooled', 'all pooled'} == set(main.scope)
    assert (main.loc[main.scope == 'formats pooled', 'level']).tolist() == ['middle', 'narrow']
    assert {'skill', 'ci_lo', 'ci_hi', 'dm_p', 'helps'} <= set(main.columns)
    # the pooled skill equals 1 - MAE(D+W) / MAE(D) computed directly on the same rows
    s = fc[(fc.group == 'seattle') & (fc.h == 1) & (fc.model == 'catboost') & fc.fset.isin(['D', 'D+W'])]
    s = s.assign(e=(s.y_hat - s.y_true).abs()).pivot_table(index=['node_id', 'origin_mi'], columns='fset', values='e')
    allp = main[main.scope == 'all pooled'].iloc[0]
    assert np.isclose(allp.skill, 1 - s['D+W'].mean() / s['D'].mean())
    for name in ('secondary', 'conditional', 'horizon2', 'gdelt_tone', 'librivox', 'showcases', 'baselines'):
        assert (rep / f'study4_03_{name}.csv').exists(), name
    sh = pd.read_csv(rep / 'study4_03_showcases.csv')
    assert (sh.category == 'Race and racism').any() and (sh.category == 'Epidemics and plagues').any()
    got = sh[(sh.category == 'Race and racism') & (sh.format == 'ebook')].iloc[0]
    assert got.origin == '2020-05' and got.target == '2020-06' and np.isfinite(got['catboost_D+W'])
    # LibriVox is reported separately and never enters the Seattle tables
    assert set(pd.read_csv(rep / 'study4_03_librivox.csv').format) <= {'librivox', 'all'}
    # 04: interest flow on the simulated weekly series
    idir = d / 'interest'; (idir / 'wiki').mkdir(parents=True)
    w['wiki'].to_parquet(idir / 'wiki' / 'weekly_node.parquet', index=False)
    w['shifts'].to_parquet(idir / 'shifts.parquet', index=False); w['sw'].to_parquet(idir / 'shift_weekly.parquet', index=False)
    _run('04_interest_flow.py', '--interest-dir', str(idir), '--nodes', str(d / 'nodes.parquet'), '--reports-dir', str(rep),
         '--out-dir', str(d / 'out4'), '--workers', '2', '--limit-origins', '3')
    t = pd.read_csv(rep / 'study4_04_interest_flow.csv')
    assert set(t.level) == {'middle', 'narrow', 'all'} and np.isfinite(t.skill).all()
    assert {'spearman', 'auc_naive', 'auc_catboost', 'base_rate'} <= set(t.columns)
    assert (rep / 'study4_04_interest_flow.md').exists()


def test_interest_flow_target_and_features_are_real_time():
    import _flow as FL
    w = sim.make_world(beta=0.0, seed=43)
    T = FL.flow_table(w['wiki'], w['shifts'], w['sw'], w['nodes'], S)
    node = 'B01.M01.N01'
    r = T[(T.node_id == node) & (T.origin == '2019-03')].iloc[0]
    wk = w['wiki'].query("node_id == @node").set_index('week').share
    weeks_apr = [d for d in wk.index if FE.week_month(d) == MI('2019-04')]           # weeks whose Sunday is in April
    assert np.isclose(r.y, np.log(wk[weeks_apr].mean()))
    L = FE.last_week_monday(MI('2019-03'))
    assert np.isclose(r.naive, np.log(np.mean([wk[L - pd.Timedelta(weeks=k)] for k in range(4)])))
    assert np.isclose(r.lag1, np.log(wk[L - pd.Timedelta(weeks=1)])) and np.isclose(r.lag52, np.log(wk[L - pd.Timedelta(weeks=52)]))
    assert np.isclose(r.normal, np.median([wk[L - pd.Timedelta(weeks=k)] for k in range(1, 27)]))
    # perturbing weeks after the last included week leaves the features of that origin unchanged
    p = copy.deepcopy(w)
    p['wiki'].loc[p['wiki'].week > L, 'share'] *= 7.0
    T2 = FL.flow_table(p['wiki'], p['shifts'], p['sw'], p['nodes'], S, drop_missing_target=False)
    T1 = FL.flow_table(w['wiki'], w['shifts'], w['sw'], w['nodes'], S, drop_missing_target=False)
    a = T1[T1.origin_mi <= MI('2019-03')].set_index(['node_id', 'origin_mi']).sort_index().drop(columns=['y', 'target_mi'])
    b = T2[T2.origin_mi <= MI('2019-03')].set_index(['node_id', 'origin_mi']).sort_index().drop(columns=['y', 'target_mi'])
    pd.testing.assert_frame_equal(a, b)
