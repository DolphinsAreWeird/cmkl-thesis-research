# The scripts, end to end, on a simulated world in a temporary folder (never on real data): the step order is
# enforced, every step writes its outputs, the simulated positive controls pass, and record sizes cannot be
# overridden outside simulation.
import sys, json, types, pathlib, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
import _files as IO

STUDY3 = pathlib.Path(__file__).resolve().parents[1]
PY = sys.executable


def run(script, sim, *extra):
    r = subprocess.run([PY, str(STUDY3 / script), '--sim', str(sim), '--workers', '2', *extra],
                       capture_output=True, text=True, cwd=str(STUDY3))
    return r.returncode, r.stdout + r.stderr


def test_scripts_run_in_order_on_a_simulated_world(tmp_path):
    sim = tmp_path / 'sim'
    code, out = run('01_demand_panel.py', sim)
    assert code == 0, out
    code, out = run('11_power.py', sim, '--draws', '5')
    assert code != 0 and 'refuses to run' in out and 'study3_10_positive_controls' in out
    code, out = run('10_positive_controls.py', sim)
    assert code == 0, out
    assert IO.report_field(sim / 'reports' / 'study3_10_positive_controls.md', 'controls status') == 'PASS'
    for script, extra in (('11_power.py', ['--draws', '8']), ('12_shift_effects.py', ['--boot', '50']),
                          ('13_carryover.py', ['--boot', '50']), ('14_tone.py', ['--boot', '20', '--placebos', '20'])):
        code, out = run(script, sim, *extra)
        assert code == 0, f'{script}\n{out}'
    for f in ('positive_controls.csv', 'power_draws.parquet', 'power_summary.csv', 'shift_effects.parquet',
              'pooled_effects.csv', 'carryover_coefs.csv', 'tone_features.parquet', 'tone_models.csv'):
        assert (sim / 'db' / f).exists(), f
    for step in IO.ORDER:
        assert (sim / 'reports' / f'{IO.STEPS[step]}.md').exists(), step
    R = pd.read_parquet(sim / 'db' / 'shift_effects.parquet')
    T = pd.read_parquet(sim / 'db' / 'sim_truth_shifts.parquet')
    T['shift_id'] = T.source + ':' + T.node_id + ':' + pd.to_datetime(T.start_week).dt.strftime('%Y-%m-%d')
    ctrl = json.loads((sim / 'db' / 'sim_truth_controls.json').read_text()).values()
    m = R[R.sc_ok & (R.format == 'audiobook') & ~R.node_id.isin(ctrl)].dropna(subset=['sc_effect_p'])
    m = m.merge(T[['shift_id', 'true_effect']], on='shift_id')
    assert len(m) > 30 and np.corrcoef(m.sc_effect_p, m.true_effect)[0, 1] > 0.7
    big = m[m.true_effect > 0.3]
    assert big.detected_bh.mean() > 0.8


def test_a_new_panel_build_invalidates_later_reports(tmp_path):
    sim = tmp_path / 'sim'
    assert run('01_demand_panel.py', sim)[0] == 0
    assert run('10_positive_controls.py', sim)[0] == 0
    assert run('01_demand_panel.py', sim, '--sim-seed', '1')[0] == 0        # new build id
    code, out = run('11_power.py', sim, '--draws', '5')
    assert code != 0 and 'was made on panel build' in out, out


def test_development_panel_is_refused(tmp_path):
    sim = tmp_path / 'sim'
    assert run('01_demand_panel.py', sim)[0] == 0
    meta = json.loads((sim / 'db' / 'demand_panel_meta.json').read_text())
    meta['development'] = True
    (sim / 'db' / 'demand_panel_meta.json').write_text(json.dumps(meta))
    code, out = run('10_positive_controls.py', sim)
    assert code != 0 and 'development' in out
    assert run('10_positive_controls.py', sim, '--allow-dev-taxonomy')[0] == 0


def test_controls_and_power_need_shifts_unless_flagged(tmp_path):
    sim = tmp_path / 'sim'
    assert run('01_demand_panel.py', sim)[0] == 0
    (sim / 'interest' / 'shifts.parquet').unlink()
    code, out = run('10_positive_controls.py', sim)
    assert code != 0 and '--without-shifts' in out
    code, out = run('10_positive_controls.py', sim, '--without-shifts')
    assert code == 0 and 'NOT APPLIED' in (sim / 'reports' / 'study3_10_positive_controls.md').read_text()


def test_record_sizes_cannot_be_overridden_in_real_runs():
    args = types.SimpleNamespace(sim=None, draws=10)
    try:
        IO.sim_only(args, 'draws', 200)
    except SystemExit as e:
        assert 'only be used with --sim' in str(e)
    else:
        raise AssertionError('override accepted in a real run')
    assert IO.sim_only(types.SimpleNamespace(sim='x', draws=None), 'draws', 200) == 200
