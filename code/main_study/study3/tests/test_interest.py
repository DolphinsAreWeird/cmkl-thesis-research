# The interest adapter: the interest side's own layout and the minimal layout give the same normalised table,
# GDELT rows use the scaled labels, bad tables are refused, and steps refuse while the record lacks the appended
# GDELT durations.
import sys, json, types, shutil, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
import _settings as ST
from _settings import SETTINGS as S
import _interest as IN


def real_layout():
    return pd.DataFrame({
        'id': [0, 1, 2, 3], 'source': ['wikipedia', 'gdelt', 'wikipedia', 'gdelt'], 'level': [3, 3, 2, 2],
        'node_id': ['B15.M04.N05', 'B15.M04.N05', 'B05.M02', 'B05.M02'],
        'start_week': pd.to_datetime(['2020-01-27', '2020-01-20', '2020-05-25', '2019-03-11']),
        'label': ['sustained', 'fading', 'interrupted', 'intermediate'], 'size': [7.7, 2.0, 1.6, 1.9],
        'dur_rt': [4, 2, 1, 3], 'seasonal': [False, None, True, False], 'large': [True, False, False, False],
        'label_gdelt_scaled': [None, 'sustained', None, 'intermediate'], 'size_gdelt_scaled': [np.nan, 3.5, np.nan, 1.9],
        'whole_duration': [14, 17, 1, 3]})


def test_interest_layout_is_mapped():
    X = IN.normalise_shifts(real_layout(), S)
    assert list(X.duration_class) == ['sustained', 'sustained', 'interrupted', 'intermediate']   # GDELT row 1 scaled
    assert X.loc[1, 'size'] == 3.5 and X.loc[1, 'large'] == (3.5 >= S.large_ratio) and np.isnan(X.loc[1, 'duration_count'])
    assert list(X.labelled) == [True, True, False, True] and not X.loc[1, 'seasonal']            # NaN seasonal -> False
    assert list(X.level) == ['narrow', 'narrow', 'middle', 'middle']
    assert X.loc[0, 'm0'] == 2020 * 12 and X.loc[0, 'shift_id'] == 'wikipedia:B15.M04.N05:2020-01-27'


def test_minimal_layout_gives_the_same_table():
    a = IN.normalise_shifts(real_layout(), S)
    b = a[['source', 'node_id', 'level', 'start_week', 'duration_class', 'size', 'large', 'seasonal', 'duration_count']]
    b = IN.normalise_shifts(b, S)
    for c in ('shift_id', 'm0', 'duration_class', 'labelled', 'size', 'large', 'seasonal'):
        assert (a[c].astype(str) == b[c].astype(str)).all(), c


def _refused(df, text):
    try:
        IN.normalise_shifts(df, S)
    except SystemExit as e:
        assert text in str(e), str(e)
    else:
        raise AssertionError('bad shifts table accepted')


def test_bad_tables_are_refused():
    d = real_layout(); d.loc[0, 'start_week'] = pd.Timestamp('2020-01-28')
    _refused(d, 'Mondays')
    d = real_layout(); d.loc[0, 'label'] = 'spiky'
    _refused(d, 'unknown duration classes')
    d = real_layout(); d.loc[0, 'dur_rt'] = 2
    _refused(d, 'real-time count')
    d = real_layout(); d.loc[3, 'source'] = 'wikipedia'; d.loc[3, 'node_id'] = 'B15.M04.N05'
    d.loc[3, 'start_week'] = pd.Timestamp('2020-01-27')
    _refused(d, 'duplicate')


def test_tone_layout_and_partial_weeks():
    T = pd.DataFrame({'source': 'gdelt', 'level': 3, 'node_id': 'A', 'week': pd.date_range('2020-01-06', periods=3, freq='7D'),
                      'tone': [1.0, 2.0, 3.0], 'positive': 2.0, 'negative': 1.0, 'mentions': 10, 'partial_week': [False, True, False]})
    t = IN.normalise_tone(T)
    assert np.isnan(t.tone[1]) and t.tone_pos[0] == 2.0 and (t.level == 'narrow').all()


def test_steps_refuse_without_the_gdelt_durations_addendum(tmp_path):
    X = IN.normalise_shifts(real_layout(), S)
    s = types.SimpleNamespace(gdelt_durations=None)
    try:
        IN.require_gdelt_durations(s, X, '10')
    except SystemExit as e:
        assert 'appended' in str(e)
    else:
        raise AssertionError('GDELT shifts accepted without the appended durations')
    IN.require_gdelt_durations(s, X, '10', sim=True)                        # simulated runs read no real demand
    IN.require_gdelt_durations(s, X[X.source != 'gdelt'], '10')            # no GDELT shifts: nothing to check
    # an addendum carrying the values is picked up by the settings loader
    add = tmp_path / 'addenda'
    shutil.copytree(ST.ADDENDA, add)
    (add / '2026-10-14_c_gdelt_durations.json').write_text(json.dumps({'date': '2026-10-14', 'demand_data_seen': False,
        'changes': {'shift_definitions.gdelt_durations.values': {'ratio': 1.0, 'sustained_min': 4, 'fading_max': 2}}}))
    S2 = ST.load(addenda_dir=add)
    assert S2.gdelt_durations == {'values': {'ratio': 1.0, 'sustained_min': 4, 'fading_max': 2}}
    assert IN.gdelt_thresholds(S2) == (4, 2)
    IN.require_gdelt_durations(S2, X, '10')
