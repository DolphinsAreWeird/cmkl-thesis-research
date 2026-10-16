# The script chain on a simulated world: order and refusals, outputs, a recovered effect, placebo rules, a stale panel.
import sys, subprocess, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
import _s3
import _paths as IO
import _simulate as SM
import _inference as INF
from _settings import SETTINGS as S

HERE = pathlib.Path(__file__).resolve().parents[1]
B3 = _s3.build


def run(script, sim, *args, ok=True):
    p = subprocess.run([sys.executable, str(HERE / script), '--sim', str(sim), *args], capture_output=True, text=True, cwd=str(HERE))
    if ok:
        assert p.returncode == 0, (script, p.stdout[-800:], p.stderr[-1500:])
    return p


def test_inference_rules_on_a_simulated_world(tmp_path):
    P = IO.Paths(tmp_path)
    meta = SM.write_world(P, S, seed=3)
    shifts = INF.load_shifts(P, S)
    assert set(shifts.level) == {'narrow', 'middle', 'value'} and shifts.shift_id.is_unique
    W = INF.World(P, S, shifts)
    # placebo mask: same level, feasible, not the category, not its parent's family, no shift start in months -6..+6
    ctrl = meta['controls']['George Floyd / BLM']
    m0 = B3.mi_from_ym('2020-06') - 36            # a month with room for the fit window in the simulated grid
    m0 = max(m0, B3.mi_from_ym('2017-03'))
    tab = W.ztable('seattle', 'narrow', m0)
    mask = W.placebo_mask('seattle', 'narrow', m0, ctrl, tab)
    C = W.C[('seattle', 'narrow')]
    ids = C.ids[mask]
    assert ctrl not in ids and not any(W.cats['narrow'].parent[i] == W.cats['narrow'].parent[ctrl] for i in ids)
    for i in ids:
        assert not W.shifted_near('narrow', i, m0, S.placebo_cat_no_shift)
    assert mask.sum() > 3
    # a test uses the same placebo set and rank formula
    r = INF.test_unit(W, 'seattle', 'narrow', ctrl, m0, tab)
    assert r['skip'] == '' and r['n_placebos'] == int(mask.sum())
    pl = tab['z_p'][mask]
    assert np.isclose(r['p_cat_p'], (1 + np.sum(pl >= r['z_p'])) / (len(pl) + 1), atol=1e-9)
    # placebo years never use a year with a shift of the category in the window, nor the treated year
    years = json.loads(r['py_years'])
    assert (m0 // 12) not in years and all(y >= S.placebo_year_from for y in years)
    # the z table is cached on disk and reused
    assert (W.zdir / f'seattle_narrow_{m0}.npz').exists()
    tab2 = W.ztable('seattle', 'narrow', m0)
    assert np.array_equal(tab['z_p'], tab2['z_p'], equal_nan=True)
    # a table made on another panel build is not reused
    W.build_id = 'other'
    f = W.zdir / f'seattle_narrow_{m0}.npz'
    t0 = f.stat().st_mtime_ns
    W.ztable('seattle', 'narrow', m0)
    assert f.stat().st_mtime_ns != t0


def test_chain_order_refusals_and_outputs(tmp_path):
    sim = tmp_path / 'w'
    run('10_controls.py', sim, ok=False)                                         # nothing exists yet
    p = run('10_controls.py', sim, ok=False)
    assert p.returncode != 0 and 'No count panel found' in (p.stderr + p.stdout)
    run('01_panels.py', sim)
    p = run('10_controls.py', sim, ok=False)
    assert p.returncode != 0 and 'report of step 02' in (p.stderr + p.stdout)
    run('02_value_shifts.py', sim)
    for later in ('11_power.py', '12_shifts.py', '13_carryover.py', '14_sentiment.py'):
        p = run(later, sim, '--workers', '1', ok=False)
        assert p.returncode != 0 and 'refuses to run' in (p.stderr + p.stdout), later
    run('10_controls.py', sim, '--workers', '1')
    p = run('12_shifts.py', sim, '--workers', '1', ok=False)
    assert p.returncode != 0 and 'report of step 11' in (p.stderr + p.stdout)
    p = run('11_power.py', sim, '--draws', '25', '--workers', '1')
    assert (sim / 'db' / 'power_summary.csv').exists()
    p = run('13_carryover.py', sim, '--boot', '50', ok=False)
    assert p.returncode != 0 and 'report of step 12' in (p.stderr + p.stdout)
    run('12_shifts.py', sim, '--workers', '2', '--boot', '100')
    run('13_carryover.py', sim, '--boot', '60')
    run('14_sentiment.py', sim, '--boot', '60', '--placebos', '20')
    for name in ('controls.csv', 'power_draws.parquet', 'shift_effects.parquet', 'pooled_effects.csv', 'carryover_coefs.csv', 'sentiment_models.csv', 'sentiment_features.parquet'):
        assert (sim / 'db' / name).exists(), name
    for step in ('study3b_01_panels', 'study3b_02_value_shifts', 'study3b_10_controls', 'study3b_11_power', 'study3b_12_shifts', 'study3b_13_carryover', 'study3b_14_sentiment'):
        assert (sim / 'reports' / f'{step}.md').exists(), step
    # record sizes cannot be overridden outside simulation runs
    p = subprocess.run([sys.executable, str(HERE / '11_power.py'), '--draws', '5'], capture_output=True, text=True, cwd=str(HERE))
    assert p.returncode != 0
    # a new panel build makes every later report stale
    run('01_panels.py', sim, '--sim-seed', '5')
    p = run('10_controls.py', sim, '--workers', '1', ok=False)
    assert p.returncode != 0 and 'Rerun step 02' in (p.stderr + p.stdout)           # shifts_value.parquet was rewritten by the new world
    run('02_value_shifts.py', sim)
    run('10_controls.py', sim, '--workers', '1')
    p = run('12_shifts.py', sim, '--workers', '1', ok=False)
    assert p.returncode != 0 and 'refuses to run' in (p.stderr + p.stdout)


def test_controls_with_injected_effects_pass_and_effects_are_recovered(tmp_path):
    sim = tmp_path / 'w'
    run('01_panels.py', sim, '--sim-seed', '1'); run('02_value_shifts.py', sim)
    run('10_controls.py', sim, '--workers', '1')
    txt = (sim / 'reports' / 'study3b_10_controls.md').read_text()
    assert '- controls status: PASS' in txt
    C = pd.read_csv(sim / 'db' / 'controls.csv')
    seattle = C[C.kind == 'seattle']
    assert (seattle.tau_p > 0.25).all() and (seattle.p_cat_p < 0.05).all()           # +80% lifts were injected at the control months
    run('11_power.py', sim, '--draws', '20', '--workers', '1')
    run('12_shifts.py', sim, '--workers', '1', '--boot', '50')
    R = pd.read_parquet(sim / 'db' / 'shift_effects.parquet')
    assert {'tau_p', 'z_p', 'p_cat_p', 'bh_q', 'too_sparse', 'analysis'} <= set(R.columns)
    # BH is within level and family, over non-sparse tests only
    fam = R[(R.skip == '') & ~R.too_sparse & R.p_cat_p.notna()]
    assert fam.bh_q.notna().all() and R[R.too_sparse].bh_q.isna().all()
    assert (R.bh_q.dropna() >= R.loc[R.bh_q.notna(), 'p_cat_p'] - 1e-12).all()
