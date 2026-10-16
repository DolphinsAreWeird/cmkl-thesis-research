# The script chain on a simulated world: 02 is resumable and checks its inputs; 03 writes the report and CSVs.
import sys, os, subprocess, pathlib, json, time
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
from helpers import *

STUDY = HERE.parent


def _world_features():
    w = world(beta=1.0, seed=91, n_broad=2, n_mid=2, n_narrow=3)
    w['nodes'].loc[w['nodes'].node_id == 'B01.M01', 'label'] = 'Race and racism'
    w['nodes'].loc[w['nodes'].node_id == 'B01.M02', 'label'] = 'Epidemics and plagues'
    n = w['leaf'][0]
    start = pd.Timestamp('2020-01-06')
    sim.add_shift(w, n, start, 'sustained', start + pd.Timedelta(weeks=3), [2.0, 2.5, 3.0, 2.8])
    e = add_effect(empty_effects(), n, 'print', MI('2019-02'), 0.3)
    return w, features(w, e)


def _run(script, *args):
    r = subprocess.run([sys.executable, str(STUDY / script), *args], capture_output=True, text=True, env=dict(os.environ))
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-3000:]
    return r.stdout


def test_02_runs_resumes_and_refuses_other_inputs(tmp_path):
    w, F = _world_features()
    feat = tmp_path / 'features.parquet'
    F.to_parquet(feat, index=False)
    out = tmp_path / 'out'
    log = _run('02_run.py', '--features', str(feat), '--out-dir', str(out), '--workers', '2', '--limit-origins', '2')
    assert '2 test origins (2019-01 to 2019-02)' in log and 'wrote' in log
    parts = sorted((out / 'forecast_parts').glob('origin_*.parquet'))
    assert [p.stem for p in parts] == ['origin_2019-01', 'origin_2019-02']
    fc = pd.read_parquet(out / 'forecasts.parquet')
    assert set(fc.part) == {'A', 'B'} and set(fc.h) == {1, 2, 3}
    assert set(fc[fc.part == 'B'].h) == {2} and set(fc[fc.part == 'A'].model) == {'zero', 'ridge', 'catboost'}
    assert set(fc[fc.part == 'B'].model) == {'catboost_clf', 'logistic'}
    assert fc.target.notna().all() and fc.pred.notna().all() and fc.origin_mi.between(MI('2019-01'), MI('2019-02')).all()
    assert fc[fc.part == 'B'].pred.between(0, 1).all()
    mt = [p.stat().st_mtime for p in parts]
    time.sleep(1.1)
    log2 = _run('02_run.py', '--features', str(feat), '--out-dir', str(out), '--workers', '2', '--limit-origins', '2')
    assert '0 to run' in log2 and [p.stat().st_mtime for p in parts] == mt             # resume: nothing re-run
    log3 = _run('02_run.py', '--features', str(feat), '--out-dir', str(out), '--workers', '2', '--limit-origins', '3')
    assert '2 already saved, 1 to run' in log3 and len(list((out / 'forecast_parts').glob('origin_*.parquet'))) == 3
    F2 = F.copy(); F2.loc[F2.index[0], 'ls_t'] += 1.0
    other = tmp_path / 'other.parquet'
    F2.to_parquet(other, index=False)
    r = subprocess.run([sys.executable, str(STUDY / '02_run.py'), '--features', str(other), '--out-dir', str(out), '--limit-origins', '1'],
                       capture_output=True, text=True)
    assert r.returncode != 0 and '--reset' in (r.stderr + r.stdout)
    assert subprocess.run([sys.executable, str(STUDY / '02_run.py'), '--workers', '5', '--features', str(feat), '--out-dir', str(tmp_path / 'o2')],
                          capture_output=True, text=True).returncode != 0             # the record allows at most 4 workers


def test_03_writes_report_and_csvs(tmp_path):
    w, F = _world_features()
    b = fast_settings(60)
    Fc = run_origins(F, b, '2019-01', '2020-08')
    fcp, rep = tmp_path / 'forecasts.parquet', tmp_path / 'rep'
    Fc.to_parquet(fcp, index=False)
    feat, nodes = tmp_path / 'features.parquet', tmp_path / 'nodes.parquet'
    F.to_parquet(feat, index=False)
    w['nodes'].to_parquet(nodes, index=False)
    _run('03_evaluate.py', '--forecasts', str(fcp), '--features', str(feat), '--reports-dir', str(rep), '--nodes', str(nodes),
         '--study4-forecasts', str(tmp_path / 'none.parquet'))
    md = (rep / 'study4b_evaluation.md').read_text()
    for s in ('## Part A', '### Verdicts', '## Part B', 'AP difference', '## Showcases', 'Race and racism', 'Epidemics and plagues'):
        assert s in md, s
    for n in ('a_interest_comparison', 'a_vs_zero', 'a_mae', 'b_surge_metrics', 'b_ap_difference', 'showcases'):
        assert (rep / f'study4b_{n}.csv').exists(), n
    t = pd.read_csv(rep / 'study4b_a_interest_comparison.csv')
    assert set(t.h) == {1, 2, 3} and {'helps', 'skill', 'ci_lo', 'dm_p'} <= set(t.columns)
    sh = pd.read_csv(rep / 'study4b_showcases.csv')
    assert (sh.origin == '2020-04').any() and (sh.origin == '2020-01').any()
    assert 'chg catboost|D+W+S' in sh.columns and 'p catboost_clf|D' in sh.columns
