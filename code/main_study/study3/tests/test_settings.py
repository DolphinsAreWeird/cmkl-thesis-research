# Settings: the record loads, its hash is checked, addenda are applied in order, and scripts hard-code nothing.
import re, sys, json, shutil, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import _settings as ST

STUDY3 = pathlib.Path(__file__).resolve().parents[1]


def test_record_loads_and_hash_matches_readme():
    S = ST.load()
    assert S.sha256 == ST.readme_hash(ST.README) == ST.sha256_of(ST.RECORD)
    raw = json.loads(ST.RECORD.read_text())
    assert f'{S.boot_n:,}' in raw['tests']['pooled_inference'] and str(S.boot_seed) in raw['tests']['pooled_inference']
    assert list(S.power_lifts) == raw['power']['lift_sizes'] and S.power_draws == raw['power']['draws_per_size']
    # windows are ordered as the design needs: event-study fit ends before the pre-trend months, which end before
    # month 0; the synthetic-control fit ends before month 0
    assert S.es_fit_end < S.es_pretrend[0] <= S.es_pretrend[1] < S.window_primary[0] == 0
    assert S.sc_fit[0] < S.sc_fit[1] < S.window_primary[0] and S.window_primary[1] <= S.window_secondary[1]


def test_wrong_hash_stops(tmp_path):
    bad = tmp_path / ST.RECORD.name
    bad.write_bytes(ST.RECORD.read_bytes().replace(b'"seed": 20261013', b'"seed": 20261014'))
    try:
        ST.load(record=bad)
    except ST.SettingsError as e:
        assert 'SHA-256' in str(e)
    else:
        raise AssertionError('a changed record was accepted')
    readme = tmp_path / 'README.md'
    readme.write_text(ST.README.read_text().replace(ST.readme_hash(ST.README), '0' * 64))
    try:
        ST.load(readme=readme)
    except ST.SettingsError:
        pass
    else:
        raise AssertionError('a README with another hash was accepted')


def test_addenda_applied_in_file_name_order_and_required(tmp_path):
    S = ST.load()
    names = [a[0] for a in S.addenda]
    assert names == sorted(p.name for p in ST.ADDENDA.glob('*.json'))
    assert S.sc_demean and S.sc_demean_window == S.sc_fit and S.min_window_months >= 1
    empty = tmp_path / 'addenda'
    empty.mkdir()
    try:
        ST.load(addenda_dir=empty)
    except ST.SettingsError as e:
        assert 'addendum' in str(e)
    else:
        raise AssertionError('settings loaded without the synthetic-control addendum')


def test_set_path_rules():
    rec = {'a': {'b': 'text', 'l': [1]}}
    ST._set_path(rec, 'a.b.c', 5)
    ST._set_path(rec, 'a.l_add', 2)
    ST._set_path(rec, 'a.new_add', 3)
    assert rec['a']['b'] == {'text': 'text', 'c': 5} and rec['a']['l'] == [1, 2] and rec['a']['new_add'] == 3


def _numbers(path):
    """Numeric literals in code (comments and strings, docstrings included, are skipped); a minus sign directly in
    front of a number is kept with it."""
    import tokenize, io
    toks = list(tokenize.generate_tokens(io.StringIO(path.read_text()).readline))
    out = []
    for i, t in enumerate(toks):
        if t.type == tokenize.NUMBER:
            neg = i > 0 and toks[i - 1].type == tokenize.OP and toks[i - 1].string == '-'
            out.append((t.start[0], ('-' if neg else '') + t.string))
    return out


def test_no_record_values_hard_coded():
    """Seed, resample count, lift sizes, draws and the main windows and thresholds must come from the settings.
    _sim.py is exempt: its numbers describe the simulated world, not the analysis."""
    S = ST.load()
    banned = {str(S.boot_seed), str(S.boot_n), str(S.power_draws), '0.43', '0.24', '0.10', '0.1', '-24', '-7', '-6',
              '-3', '2_000', '20_261_013'}
    hits = []
    for f in sorted(STUDY3.glob('*.py')):
        if f.name in ('_settings.py', '_sim.py'):
            continue
        hits += [f'{f.name}:{line}: {num}' for line, num in _numbers(f) if num in banned]
    assert not hits, 'record values in code:\n' + '\n'.join(hits)
