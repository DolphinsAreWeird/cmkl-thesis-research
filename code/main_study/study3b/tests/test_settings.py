# Settings: both records load, both hashes are checked (a failure stops the run, also at script level), Study 3 values carry over.
import sys, json, shutil, pathlib, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import _settings as ST

STUDY3B = pathlib.Path(__file__).resolve().parents[1]
CODE = STUDY3B.parents[1]


def test_records_load_and_hashes_match_readme():
    S = ST.load()
    assert S.sha256 == ST.readme_hash(ST.README) == ST.sha256_of(ST.RECORD)
    assert S.sha256_study3 == ST.S3.readme_hash(ST.S3.README) == ST.S3.sha256_of(ST.S3.RECORD)
    raw = json.loads(ST.RECORD.read_text())
    assert list(S.power_lifts) == raw['power']['lift_sizes'] and S.power_draws == 200 and S.power_seed == S.boot_seed == 20261013
    assert S.levels_tested == ('narrow', 'middle', 'value') and S.feas_min_nonzero == 12 and S.sparse_below == 5.0
    assert (S.es_fit_len, S.es_fit_end) == (24, -7) and S.window_primary == (0, 2) and S.window_secondary == (0, 5)
    assert S.alpha == 0.05 and S.bh_q == 0.10 and S.boot_n == 2000 and S.placebo_year_from == 2017
    # Study 3 values are carried over, including the addenda (closure months, GDELT durations)
    assert S.closure_frac == 0.5 and S.gdelt_durations is not None and S.missing_months == ('2024-05', '2024-06', '2025-08')
    assert [c['shift_month'] for c in S.controls] == ['2020-03', '2020-06', '2017-10']
    assert S.sent_placebo_n == 200 and len(S.sent_features) == 5


def test_no_study3_object_inside_settings():
    S = ST.SETTINGS
    assert type(S).__module__ == '_settings' and type(S) is ST.Settings        # our class, not the Study 3 one
    import _s3
    assert ST.Settings is not _s3.settings.Settings


def test_module_names_do_not_clash():
    import _s3, _methods
    assert _s3.methods is not _methods and _s3.settings is not ST
    assert sys.modules['_settings'] is ST and sys.modules['_methods'] is _methods      # Study 3 modules left out of sys.modules
    assert _s3.methods.event_study is not getattr(_methods, 'event_study')


def test_wrong_hash_stops(tmp_path):
    bad = tmp_path / ST.RECORD.name
    bad.write_bytes(ST.RECORD.read_bytes().replace(b'"seed": 20261013', b'"seed": 20261014'))
    for kw in (dict(record=bad),):
        try:
            ST.load(**kw)
        except ST.SettingsError as e:
            assert 'SHA-256' in str(e)
        else:
            raise AssertionError('a changed Study 3b record was accepted')
    readme = tmp_path / 'README.md'
    readme.write_text(ST.README.read_text().replace(ST.readme_hash(ST.README), '0' * 64))
    try:
        ST.load(readme=readme)
    except ST.SettingsError:
        pass
    else:
        raise AssertionError('a README with another Study 3b hash was accepted')
    bad3 = tmp_path / ST.S3.RECORD.name
    bad3.write_bytes(ST.S3.RECORD.read_bytes().replace(b'"seed": 20261013', b'"seed": 20261014'))
    try:
        ST.load(s3_record=bad3)
    except ST.SettingsError as e:
        assert 'SHA-256' in str(e)
    else:
        raise AssertionError('a changed Study 3 record was accepted')


def test_unchanged_claims_are_checked(tmp_path):
    """The record's 'unchanged from Study 3' list must agree with the parsed Study 3 values (a different list stops the run)."""
    rec = json.loads(ST.RECORD.read_text())
    rec['unchanged_from_study3'] = [x.replace('24 months ending at month -7', '24 months ending at month -6') for x in rec['unchanged_from_study3']]
    try:
        ST.parse(rec, ST.S3.load())
    except ST.SettingsError as e:
        assert 'unchanged' in str(e)
    else:
        raise AssertionError('a changed unchanged-list was accepted')


def test_hash_failure_stops_a_script(tmp_path):
    """A script run against a copy of the project with a changed Study 3b record stops with the hash message."""
    root = tmp_path / 'proj'
    ign = shutil.ignore_patterns('__pycache__', 'tests', '*.pyc')
    (root / 'code' / 'main_study').mkdir(parents=True)
    shutil.copy(CODE / 'config.py', root / 'code' / 'config.py')
    for d in ('study3', 'study3b'):
        shutil.copytree(CODE / 'main_study' / d, root / 'code' / 'main_study' / d, ignore=ign)
    shutil.copytree(CODE.parent / 'prereg', root / 'prereg', copy_function=shutil.copyfile)      # copies are writable (the originals are read-only)
    rec = root / 'prereg' / ST.RECORD.name
    rec.write_bytes(rec.read_bytes().replace(b'"seed": 20261013', b'"seed": 20261014'))
    for study_hash in (False, True):
        if study_hash:
            shutil.copyfile(CODE.parent / 'prereg' / ST.RECORD.name, rec)
            r3 = root / 'prereg' / ST.S3.RECORD.name
            r3.write_bytes(r3.read_bytes().replace(b'"seed": 20261013', b'"seed": 20261014'))
        p = subprocess.run([sys.executable, str(root / 'code' / 'main_study' / 'study3b' / '01_panels.py'), '--sim', str(tmp_path / 'sim')],
                           capture_output=True, text=True, cwd=str(root))
        assert p.returncode != 0 and 'SHA-256' in (p.stderr + p.stdout), p.stderr[-500:]
        assert not (tmp_path / 'sim' / 'db' / 'counts_seattle.parquet').exists()
