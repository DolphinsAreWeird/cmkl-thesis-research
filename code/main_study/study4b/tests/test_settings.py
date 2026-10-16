# The hash check: both records must match the README; any change stops the run. Addenda are applied in file-name order.
import sys, json, math, pathlib, subprocess
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _settings as ST

STUDY = HERE.parent


def test_record_loads_and_values_are_parsed_from_it():
    B = ST.load_settings()
    assert B.sha256 == ST.readme_hash(ST.README, ST.RECORD.name) == ST.sha256_of(ST.RECORD)
    assert B.sha256 == 'a34ab8e2279d4f13409a8786848a1179bd28964d35766c647acbefd44eab9bb4'
    assert B.sha256_study4 == '040a7c7a7416d4a652b9fe5c52ef947447c1a5653db3839757819164f8917bd6'
    assert B.horizons == (1, 2, 3) and B.h_primary == 2 and B.h_surge == 2
    assert B.feature_sets == ('D', 'D+W', 'D+W+S')
    assert (B.cb_iterations, B.cb_depth, B.cb_learning_rate, B.cb_loss, B.cb_seed) == (600, 6, 0.05, 'RMSE', 20261013)
    assert (B.dm_lag, B.boot_block, B.boot_n, B.boot_seed, B.helps_alpha, B.ci_level) == (3, 3, 2000, 20261013, 0.05, 0.95)
    assert math.isclose(B.surge_change, math.log(1.3)) and B.top_k == 10
    assert B.test_start == '2019-01' and B.sustained_weeks == 8 and B.effect_window == (0, 2)
    assert B.formats_primary == ('print', 'ebook') and B.formats_secondary == ('audiobook',)
    assert [(c['label'], c['formats'], c['origin'], c['target']) for c in B.showcases] == [
        ('Race and racism', ('print', 'ebook'), '2020-04', '2020-06'), ('Epidemics and plagues', ('ebook',), '2020-01', '2020-03')]
    assert B.addenda_study4 and B.addenda_study4[0][0].startswith('2026-10-13_a')       # Study 4's addendum was applied


def _copy_readme(tmp_path, new_hash_for=None, new_hash=None):
    r = tmp_path / 'README.md'
    txt = ST.README.read_text()
    if new_hash_for:
        i = txt.find(new_hash_for)
        j = txt.find('`', txt.find('SHA-256', i)) + 1
        txt = txt[:j] + new_hash + txt[j + 64:]
    r.write_text(txt)
    return r


def test_edited_4b_record_stops(tmp_path):
    bad = tmp_path / ST.RECORD.name
    bad.write_bytes(ST.RECORD.read_bytes().replace(b'"primary": 2', b'"primary": 3'))
    assert bad.read_bytes() != ST.RECORD.read_bytes()
    try:
        ST.load_settings(record=bad)
    except ST.SettingsError as e:
        assert 'SHA-256 mismatch' in str(e) and ST.RECORD.name in str(e)
    else:
        raise AssertionError('an edited 4b record was accepted')


def test_wrong_readme_hash_for_4b_stops(tmp_path):
    r = _copy_readme(tmp_path, ST.RECORD.name, '0' * 64)
    assert r.read_text() != ST.README.read_text()
    try:
        ST.load_settings(readme=r)
    except ST.SettingsError as e:
        assert 'SHA-256 mismatch' in str(e)
    else:
        raise AssertionError('a README with another 4b hash was accepted')


def test_edited_study4_record_stops_the_4b_run(tmp_path):
    bad = tmp_path / ST.S4M.RECORD.name
    bad.write_bytes(ST.S4M.RECORD.read_bytes().replace(b'20261013', b'20261014'))
    try:
        ST.load_settings(study4_record=bad)
    except ST.SettingsError as e:
        assert 'SHA-256 mismatch' in str(e) and 'forecast_settings' in str(e)
    else:
        raise AssertionError('an edited Study 4 record was accepted')


def test_hash_failure_stops_a_script_run(tmp_path):
    """A process that points the settings at an edited record exits with an error before anything runs."""
    bad = tmp_path / ST.RECORD.name
    bad.write_bytes(ST.RECORD.read_bytes().replace(b'20261013', b'20261014'))
    code = (f"import sys; sys.path.insert(0, {str(STUDY)!r}); import _settings as ST, pathlib; "
            f"ST.RECORD = pathlib.Path({str(bad)!r}); ST.settings(); print('RAN')")
    r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    assert r.returncode != 0 and 'RAN' not in r.stdout and 'SHA-256 mismatch' in r.stderr
    for name in ('01_features.py', '02_run.py', '03_evaluate.py'):                     # every entry script goes through settings()
        assert 'ST.settings()' in (STUDY / name).read_text(), name


def test_addenda_4b_applied_in_file_name_order(tmp_path):
    d = tmp_path / 'addenda_4b'
    d.mkdir()
    base = json.loads(ST.RECORD.read_text())['part_b_surges']['surge']
    (d / '2026-10-15_b.json').write_text(json.dumps({'date': '2026-10-15', 'changes': {'part_b_surges.surge': base.replace('log(1.3)', 'log(1.5)')}}))
    (d / '2026-10-15_a.json').write_text(json.dumps({'date': '2026-10-15', 'changes': {'part_b_surges.surge': base.replace('log(1.3)', 'log(1.4)')}}))
    B = ST.load_settings(addenda_dir=d)
    assert B.surge_ratio == 1.5                                   # _b is applied after _a
    assert [x[0] for x in B.addenda] == ['2026-10-15_a.json', '2026-10-15_b.json']
    assert ST.load_settings().surge_ratio == 1.3                  # the real (empty) addenda folder leaves the record as fixed


def test_unparsable_wording_stops(tmp_path):
    rec = json.loads(ST.RECORD.read_text())
    rec['part_b_surges']['surge'] = 'a big change counts'
    try:
        ST.parse(rec, ST.settings().s4)
    except ST.SettingsError:
        pass
    else:
        raise AssertionError('wording that does not match was accepted')
