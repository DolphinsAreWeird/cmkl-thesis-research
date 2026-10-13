# Settings: the record loads, its hash is checked (a mismatch stops the run), addenda are applied in file-name order.
import sys, json, pathlib, subprocess
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _settings as ST


def test_record_loads_and_hash_matches_readme():
    S = ST.load_settings()
    assert S.sha256 == ST.readme_hash(ST.README) == ST.sha256_of(ST.RECORD)
    raw = json.loads(ST.RECORD.read_text())
    assert S.cb_seed == S.boot_seed == 20261013
    assert (S.cb_iterations, S.cb_depth, S.cb_learning_rate, S.cb_loss) == (600, 6, 0.05, 'RMSE')
    assert S.cat_features == ('format', 'level', 'broad_id', 'tmonth')
    assert S.ridge_alphas == (0.1, 1.0, 10.0, 100.0) and S.ridge_val_origins == 12
    assert (S.dm_lag, S.boot_block, S.boot_n) == (3, 3, 2000)
    assert (S.test_start, S.gdelt_end) == ('2019-01', '2021-05')
    assert S.horizons == (1, 2) and S.size_lookback == 24
    assert (S.recent_weeks, S.normal_weeks, S.mk_weeks, S.shift_weeks) == (4, 26, 8, 8)
    assert S.flow_lags == (1, 2, 3, 4, 5, 6, 7, 8, 52) and S.flow_ratio == 1.5
    assert [c['label'] for c in S.showcases] == ['Race and racism', 'Epidemics and plagues']
    assert S.showcases[1]['origins'] == ('2020-02', '2020-03') and S.showcases[0]['formats'] == ('ebook', 'audiobook')
    assert raw['fixed_on'] == S.fixed_on


def test_wrong_hash_stops(tmp_path):
    bad = tmp_path / ST.RECORD.name
    bad.write_bytes(ST.RECORD.read_bytes().replace(b'"random_seed 20261013', b'"random_seed 20261014').replace(b'iterations 600', b'iterations 601'))
    assert bad.read_bytes() != ST.RECORD.read_bytes()
    try:
        ST.load_settings(record=bad)
    except ST.SettingsError as e:
        assert 'SHA-256 mismatch' in str(e)
    else:
        raise AssertionError('a changed record was accepted')
    readme = tmp_path / 'README.md'
    readme.write_text(ST.README.read_text().replace(ST.readme_hash(ST.README), '0' * 64))
    try:
        ST.load_settings(readme=readme)
    except ST.SettingsError:
        pass
    else:
        raise AssertionError('a README with another hash was accepted')


def test_hash_failure_stops_the_script_run(tmp_path):
    """A process that points the settings at an edited record exits with an error before anything runs."""
    bad = tmp_path / ST.RECORD.name
    bad.write_bytes(ST.RECORD.read_bytes().replace(b'20261013', b'20261014'))
    code = (f"import sys; sys.path.insert(0, {str(HERE.parent)!r}); import _settings as ST, pathlib; "
            f"ST.RECORD = pathlib.Path({str(bad)!r}); ST.settings(); print('RAN')")
    r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    assert r.returncode != 0 and 'RAN' not in r.stdout and 'SHA-256 mismatch' in r.stderr
    # the entry scripts take their settings only through _settings.settings()
    for name in ('01_features.py', '02_forecast.py', '03_evaluate.py', '04_interest_flow.py'):
        assert 'ST.settings()' in (HERE.parent / name).read_text(), name


def test_addenda_applied_in_file_name_order(tmp_path):
    d = tmp_path / 'addenda_forecast'
    d.mkdir()
    (d / '2026-11-02_b.json').write_text(json.dumps({'date': '2026-11-02', 'changes': {
        'models.ridge': 'pooled; alpha chosen from {1, 10} on the last 6 training origins (time split); features standardised on training rows only'}}))
    (d / '2026-11-01_a.json').write_text(json.dumps({'date': '2026-11-01', 'changes': {
        'models.ridge': 'pooled; alpha chosen from {5, 50} on the last 9 training origins (time split); features standardised on training rows only'}}))
    S = ST.load_settings(addenda_dir=d)
    assert [a[0] for a in S.addenda] == ['2026-11-01_a.json', '2026-11-02_b.json']      # file-name order
    assert S.ridge_alphas == (1.0, 10.0) and S.ridge_val_origins == 6                    # the later file wins
    assert ST.load_settings(addenda_dir=tmp_path / 'none').addenda == []                  # no folder, no addenda
    S0 = ST.load_settings()
    assert S0.ridge_alphas == (0.1, 1.0, 10.0, 100.0)
    assert not list(ST.PREREG.glob('*.tmp'))


def test_thread_plan_respects_the_machine_budget():
    for w in (1, 2, 3):
        workers, th = ST.thread_plan(w)
        assert workers * th <= ST.THREAD_BUDGET
    try:
        ST.thread_plan(5)
    except ST.SettingsError:
        pass
    else:
        raise AssertionError('more workers than the record allows were accepted')
