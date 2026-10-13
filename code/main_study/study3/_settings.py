# Fixed Study 3 settings, read from the dated record in prereg/ (read-only, never edited here).
# 1) The record's SHA-256 must equal the value printed in prereg/README.md; otherwise nothing runs.
# 2) The addenda in prereg/addenda/*.json are applied in file-name order (see apply_addenda for the rules).
# 3) Every number the Study 3 code uses is parsed here from the record's own wording. A parse that does not match
#    the wording stops the run, so no script hard-codes a threshold, window, seed or size that is in the record.
# Values that the code needs but the record does not give are NOT here: they sit next to the code that uses them,
# marked '# NOT IN RECORD:'.
import json, re, hashlib, pathlib
from datetime import datetime

HERE = pathlib.Path(__file__).resolve().parent
PREREG = HERE.parents[2] / 'prereg'
RECORD = PREREG / 'study3_settings_2026-10-13.json'
README = PREREG / 'README.md'
ADDENDA = PREREG / 'addenda'
LEVELS = ('broad', 'middle', 'narrow')          # taxonomy levels 1, 2, 3 (data schema, not a setting)


class SettingsError(SystemExit):
    """Raised when the record cannot be trusted or parsed. Subclass of SystemExit so scripts stop with the message."""


def sha256_of(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def readme_hash(readme_path):
    m = re.search(r'SHA-256 of the record:\s*`([0-9a-f]{64})`', pathlib.Path(readme_path).read_text())
    if not m:
        raise SettingsError(f'no SHA-256 line found in {readme_path}')
    return m.group(1)


def _text(x):
    """A record entry is a string, or a dict made by an addendum that extended a string (original under 'text')."""
    return x['text'] if isinstance(x, dict) else x


def _set_path(rec, path, value):
    """Set a dotted path. A string on the way is turned into {'text': string} so it can carry sub-keys.
    A last key ending in '_add' appends to the list named without the suffix, if that list exists."""
    keys = path.split('.')
    node = rec
    for k in keys[:-1]:
        if k not in node:
            node[k] = {}
        elif isinstance(node[k], str):
            node[k] = {'text': node[k]}
        node = node[k]
    last = keys[-1]
    if last.endswith('_add') and isinstance(node.get(last[:-4]), list):
        node[last[:-4]].append(value)
    else:
        node[last] = value


def apply_addenda(rec, files):
    """Apply addenda in file-name order; returns the list of (file name, sha256, date, demand_data_seen)."""
    applied = []
    for f in sorted(files, key=lambda p: pathlib.Path(p).name):
        A = json.loads(pathlib.Path(f).read_text())
        for path, value in A['changes'].items():
            _set_path(rec, path, value)
        applied.append((pathlib.Path(f).name, sha256_of(f), A.get('date'), A.get('demand_data_seen')))
    return applied


# ---------------- parsing helpers ----------------
def _find(pattern, text, what):
    m = re.search(pattern, text)
    if not m:
        raise SettingsError(f'cannot parse {what}: /{pattern}/ not found in: {text!r}')
    return m


def _num(pattern, text, what, cast=float):
    return cast(_find(pattern, text, what).group(1).replace(',', ''))


def _window(pattern, text, what):
    m = _find(pattern, text, what)
    return int(m.group(1)), int(m.group(2))


def _require(phrase, text, what):
    if phrase not in text:
        raise SettingsError(f'{what}: expected the phrase {phrase!r} in: {text!r}')


def _months_named(text):
    """'May 2024, June 2024 and August 2025 ...' -> ('2024-05', '2024-06', '2025-08')"""
    out = []
    for name, year in re.findall(r'\b(January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})\b', text):
        out.append(datetime.strptime(f'{name} {year}', '%B %Y').strftime('%Y-%m'))
    if not out:
        raise SettingsError(f'no months found in: {text!r}')
    return tuple(out)


def _controls(pc):
    out = []
    for c in pc['controls']:
        m = _find(r'^(.*?) \((narrow|middle|broad)(?:, (.*))?\)$', c['category'], 'positive-control category')
        _find(r'^\d{4}-\d{2}$', c['shift_month'], 'positive-control shift month')
        out.append(dict(name=c['name'], label=m.group(1).strip(), level=m.group(2), note=m.group(3) or '',
                        shift_month=c['shift_month'], expected=c['expected'],
                        only_if_size='if the category passes the minimum size' in c['expected']))
    return tuple(out)


def _gdelt_durations(sd):
    """Values appended by an addendum under shift_definitions.gdelt_durations (as sub-keys) or as sibling keys whose
    names start with 'gdelt_durations'; None when nothing has been appended."""
    out = {k: v for k, v in sd.items() if k.startswith('gdelt_durations') and k != 'gdelt_durations'}
    g = sd.get('gdelt_durations')
    if isinstance(g, dict):
        out.update({k: v for k, v in g.items() if k != 'text'})
    return out or None


def find_key(obj, key):
    """First value stored under `key` anywhere inside nested dicts (used to read appended GDELT thresholds)."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find_key(v, key)
            if r is not None:
                return r
    return None


class Settings:
    """Parsed values (attributes) plus the record with addenda applied (.record)."""

    def __repr__(self):
        keys = [k for k in vars(self) if k not in ('record',)]
        return 'Settings(' + ', '.join(f'{k}={getattr(self, k)!r}' for k in keys) + ')'


def parse(rec):
    S = Settings()
    S.record = rec
    S.fixed_on = rec['fixed_on']
    tx, per, dm, ts = rec['taxonomy'], rec['period'], rec['demand'], rec['tests']
    sd, it, pw, co, tn = rec['shift_definitions'], rec['interest'], rec['power'], rec['which_shifts_carry_over'], rec['tone']

    # taxonomy and period
    S.levels_tested = tuple(tx['levels_tested'])
    _require('descriptive only', tx['broad_level'], 'broad level')
    S.levels_descriptive = ('broad',)
    S.title_backup_max_works = _num(r'fewer than (\d+) works', tx['assignment'], 'title-word backup size', int)
    _require('without title-word evidence', tx['assignment'], 'main assignment')
    S.study_start = _find(r'^(\d{4}-\d{2})$', per['study_start'], 'study start').group(1)

    # demand
    S.seattle_formats = tuple(x.strip() for x in _find(r'format \(([^)]*)\)', dm['seattle'], 'Seattle formats').group(1).split(','))
    _require('divided by all checkouts in that format that month', dm['seattle'], 'Seattle demand')
    _require('divided by all LibriVox views that month', dm['librivox'], 'LibriVox demand')
    S.missing_months = _months_named(dm['missing_months'])
    _require('no digital Seattle rows', dm['missing_months'], 'missing months')
    _require('never as zero', dm['missing_months'], 'missing months')
    S.digital_formats = tuple(f for f in S.seattle_formats if f != 'print')
    S.min_works = _num(r'>= (\d+) works with checkouts', dm['minimum_size'], 'minimum works', int)
    S.min_median_weighted = _num(r'median of >= ([\d,.]+) weighted checkouts per month', dm['minimum_size'], 'minimum median')
    S.size_lookback = _num(r'in the (\d+) months before the window', dm['minimum_size'], 'size look-back', int)
    _require('log of the share', dm['transform'], 'transform')
    zm = dm.get('zero_or_missing')
    if zm is None:
        raise SettingsError('addendum b (zero or missing months) not applied')
    _require('treated as missing', zm, 'zero or missing'); _require('never as log(0)', zm, 'zero or missing')
    S.min_window_months = _num(r'fewer than (\d+) available months', zm, 'minimum available months', int)
    cm = dm.get('closure_months')
    if cm is None:
        raise SettingsError('addendum e (closure months) not applied')
    S.closure_frac = _num(r'below (\d+)% of', cm, 'closure threshold') / 100
    S.closure_lookback = _num(r'previous (\d+) months with rows', cm, 'closure look-back', int)
    S.closure_min = _num(r'at least (\d+) needed', cm, 'closure minimum months', int)
    _require('treated as missing', cm, 'closure months')

    # tests
    _require('month 0 is in the post period', ts['month_zero'], 'month zero')
    _require('calendar month containing the shift start week', ts['month_zero'], 'month zero')
    S.window_primary = _window(r'months (-?\d+) to \+(\d+)', ts['primary_effect_window'], 'primary window')
    S.window_secondary = _window(r'months (-?\d+) to \+(\d+)', ts['secondary_effect_window'], 'secondary window')
    es = ts['event_study']
    _require('linear trend', es, 'event study'); _require('month-of-year effects', es, 'event study')
    S.es_fit_len, S.es_fit_end = _window(r'fitted on the (\d+) months ending at month (-\d+)', es, 'event-study fit')
    S.es_pretrend = _window(r'months (-\d+) to (-\d+) shown as a pre-trend', es, 'pre-trend months')
    sc = ts['synthetic_control']; sct = _text(sc)
    S.donor_no_shift = _window(r'no shift start in months (-\d+) to \+(\d+)', sct, 'donor shift exclusion')
    _require('not sharing a parent node', sct, 'donor parent rule')
    S.donor_max_overlap = _num(r'sharing <= (\d+)% of their works', sct, 'donor overlap') / 100.0
    _require('non-negative weights summing to 1', sct, 'weights')
    S.sc_fit = _window(r'fitted on log share for months (-\d+) to (-\d+)', sct, 'synthetic-control fit')
    _require('divided by (number of donors + 1)', sct, 'rank p-value')
    dem = sc.get('demeaning') if isinstance(sc, dict) else None
    if dem is None:
        raise SettingsError('addendum b (demeaned synthetic control) not applied')
    S.sc_demean = True
    S.sc_demean_window = _window(r'months (-\d+) to (-\d+)', dem, 'demeaning window')
    if S.sc_demean_window != S.sc_fit:
        raise SettingsError('demeaning window differs from the synthetic-control fit window; check the addendum')
    S.placebo_year_from = _num(r'every other year from (\d{4})', ts['placebo_years'], 'placebo years', int)
    _require('no shift in that window', ts['placebo_years'], 'placebo years')
    S.boot_n = _num(r'([\d,]+) resamples', ts['pooled_inference'], 'bootstrap resamples', int)
    S.boot_seed = _num(r'seed (\d+)', ts['pooled_inference'], 'bootstrap seed', int)
    _require('clustered by category', ts['pooled_inference'], 'bootstrap clusters')
    S.bh_q = _num(r'q < ([\d.]+)', ts['multiple_testing'], 'BH threshold')
    S.alpha = _num(r'one-sided p < ([\d.]+)', ts['significance'], 'single-shift significance')

    # positive controls
    S.controls = _controls(rec['positive_controls'])

    # power
    _require('months 0 to +2', pw['method'], 'power window')
    S.power_window = _window(r'months (\d+) to \+(\d+) after', pw['method'], 'power window')
    S.power_lifts = tuple(float(x) for x in pw['lift_sizes'])
    S.power_draws = int(pw['draws_per_size'])
    S.power_alpha = _num(r'one-sided p < ([\d.]+)', pw['detection'], 'power detection')
    S.power_rate = _num(r'>= (\d+)% of draws', pw['minimum_detectable_effect'], 'MDE rate') / 100.0
    S.power_seed = int(pw['seed'])

    # carry-over
    S.carry_window = _window(r'months (\d+) to \+(\d+)', co['outcome'], 'carry-over outcome window')
    S.carry_ref_class = _find(r'duration class \(reference: (\w+)\)', co['model'], 'carry-over reference class').group(1)
    _require('broad category fixed effects', co['model'], 'carry-over model')
    _require('clustered by category', co['model'], 'carry-over bootstrap')
    S.carry_lag = _window(r'within (\d+) to \+(\d+)', co['lag'], 'carry-over lag window')

    # tone
    S.tone_weeks = _num(r'over the first (\d+) weeks', tn['feature'], 'tone weeks', int)
    S.tone_baseline_weeks = _num(r"(\d+)-week median tone", tn['feature'], 'tone baseline weeks', int)
    S.tone_placebo_n = _num(r'from (\d+) random non-shift', tn['test'], 'tone placebo count', int)
    S.tone_placebo_len = _num(r'non-shift (\d+)-week windows', tn['test'], 'tone placebo window', int)
    _require('added to the carry-over model', tn['test'], 'tone test')

    # shift labels (used only to validate the interest input)
    S.large_ratio = _num(r'size >= ([\d.]+)', sd['large_shift'], 'large shift')
    S.sustained_min = _num(r'duration_count >= (\d+)', sd['sustained'], 'sustained', int)
    S.intermediate_eq = _num(r'duration_count == (\d+)', sd['intermediate'], 'intermediate', int)
    S.fading_max = _num(r'duration_count <= (\d+)', sd['fading'], 'fading', int)
    S.normal_weeks = _num(r'median of the previous (\d+) weeks', sd['normal_level'], 'normal level', int)
    S.primary_source, S.secondary_source = it['primary_source'], it['secondary_source']
    # GDELT durations: the record says the values computed from interest data are appended to it before any demand
    # data are read. None until an addendum carries them (any change under shift_definitions.gdelt_durations...).
    _require('appended to this record before any demand data are read', _text(sd['gdelt_durations']), 'GDELT durations')
    S.gdelt_durations = _gdelt_durations(sd)
    _require('Monday start', it['week'], 'week definition')

    # consistency checks between parsed parts of the record
    if S.carry_window != S.window_primary or S.power_window != S.window_primary:
        raise SettingsError('carry-over or power window differs from the primary window; check the record')
    if S.power_lifts != tuple(sorted(S.power_lifts)):
        raise SettingsError('lift sizes not in increasing order')
    return S


def load(record=RECORD, readme=README, addenda_dir=ADDENDA):
    """Load, verify, apply addenda, parse. Raises SettingsError (stops the script) on a hash mismatch."""
    expected = readme_hash(readme)
    got = sha256_of(record)
    if got != expected:
        raise SettingsError(f'SHA-256 of {pathlib.Path(record).name} is {got}, but prereg/README.md says {expected}. '
                            'The fixed settings were changed or replaced; nothing runs until this is resolved.')
    rec = json.loads(pathlib.Path(record).read_text())
    files = sorted(pathlib.Path(addenda_dir).glob('*.json')) if addenda_dir and pathlib.Path(addenda_dir).exists() else []
    applied = apply_addenda(rec, files)
    S = parse(rec)
    S.sha256 = got
    S.addenda = tuple(applied)
    return S


SETTINGS = load()


if __name__ == '__main__':
    for k, v in vars(SETTINGS).items():
        if k != 'record':
            print(f'{k:24s} {v}')
