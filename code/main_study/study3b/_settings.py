# Fixed Study 3b settings. Two fixed records are checked and read:
#   1) prereg/study3_settings_2026-10-13.json with prereg/addenda/*.json  (loaded by the Study 3 loader, which checks
#      its SHA-256 against prereg/README.md)
#   2) prereg/study3b_settings_2026-10-13.json with prereg/addenda_3b/*.json (SHA-256 checked against the Study 3b
#      line of prereg/README.md)
# Either hash failing stops the run (SettingsError is a SystemExit). The Study 3 loader is reused through _s3.py
# (module-name clashes avoided there). Every number of Study 3b is parsed here from the record's own wording; a parse
# that does not match the wording stops the run, and the "unchanged from Study 3" claims of the record are checked
# against the parsed Study 3 values. Values the record does not give sit next to the code that uses them, marked
# '# NOT IN RECORD:'.
import json, re, hashlib, pathlib
import _s3

S3 = _s3.settings
SettingsError = S3.SettingsError
HERE = pathlib.Path(__file__).resolve().parent
PREREG = HERE.parents[2] / 'prereg'
RECORD = PREREG / 'study3b_settings_2026-10-13.json'
README = PREREG / 'README.md'
ADDENDA = PREREG / 'addenda_3b'
LEVELS = ('narrow', 'middle', 'value')            # data schema: all levels this study can test


def sha256_of(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def readme_hash(readme_path=README):
    """SHA-256 in the Study 3b section of prereg/README.md (the file also holds the other studies' hashes)."""
    text = pathlib.Path(readme_path).read_text()
    i = text.find('## Study 3b')
    if i < 0:
        raise SettingsError(f'no Study 3b section in {readme_path}')
    sec = text[i:].split('\n## ', 1)[0]
    m = re.search(r'SHA-256:\s*`([0-9a-f]{64})`', sec)
    if not m:
        raise SettingsError(f'no SHA-256 line in the Study 3b section of {readme_path}')
    return m.group(1)


def _find(pattern, text, what):
    m = re.search(pattern, text)
    if not m:
        raise SettingsError(f'cannot parse {what}: /{pattern}/ not found in: {text!r}')
    return m


def _num(pattern, text, what, cast=float):
    return cast(_find(pattern, text, what).group(1).replace(',', ''))


def _require(phrase, text, what):
    if phrase not in text:
        raise SettingsError(f'{what}: expected the phrase {phrase!r} in: {text!r}')


class Settings:
    """Parsed values (attributes). Holds every Study 3 attribute too (copied), plus the Study 3b ones."""

    def __repr__(self):
        return 'Settings(' + ', '.join(f'{k}={v!r}' for k, v in vars(self).items() if k != 'record') + ')'


def _controls(pc):
    out = []
    for text in pc['controls']:
        m = _find(r'^(.*?): (.*?) \((narrow|middle|broad)\), (\d{4}-\d{2})$', text, 'positive control')
        out.append(dict(name=m.group(1).strip(), label=m.group(2).strip(), level=m.group(3), shift_month=m.group(4)))
    return tuple(out)


def parse(rec, s3):
    """Study 3b values from the record `rec` (addenda applied); `s3` is the parsed Study 3 Settings."""
    S = Settings()
    for k, v in vars(s3).items():                  # copied values only (no Study 3 objects), so the class stays ours
        setattr(S, k, v)
    S.record3 = s3.record
    S.record = rec
    S.fixed_on = rec['fixed_on']
    lv, ns, dm = rec['levels'], rec['no_size_threshold'], rec['demand']
    ce, inf, pc = rec['count_event_study'], rec['inference'], rec['positive_controls']
    pw, al, se = rec['power'], rec['all_shifts'], rec['sentiment']

    # levels
    S.levels_tested = tuple(lv['tested'])
    if S.levels_tested != ('narrow', 'middle', 'value'):
        raise SettingsError(f'levels tested differ from narrow, middle, value: {S.levels_tested}')
    _require('work_theme_value', lv['value_level'], 'value level')
    S.levels_descriptive = ()

    # no size threshold, feasibility and sparse rule
    S.feas_min_nonzero, S.fit_len_check = (_num(r'at least (\d+) of the (\d+) fit months', ns, 'feasibility', int),
                                          _num(r'at least \d+ of the (\d+) fit months', ns, 'fit months', int))
    S.sparse_below = _num(r'fewer than ([\d.]+) expected weighted checkouts over the primary window', ns, 'sparse rule')
    _require('nonzero weighted checkout', ns, 'feasibility'); _require('in at least one format', ns, 'feasibility')

    # demand
    _require('sum over works of theme weight x checkouts', dm['counts'], 'counts')
    _require('exposure N_{f,t} = all checkouts in format f, month t', dm['counts'], 'exposure')
    _require('jointly in one model per test', dm['formats'], 'formats')
    _require('LibriVox is analysed separately with its own exposure (all LibriVox views)', dm['formats'], 'LibriVox')

    # count event study
    _require('quasi-Poisson GLM', ce['model'], 'model')
    _require('log E[Y_{c,f,t}] = log N_{f,t} + alpha_f + beta_f * t + sum_k gamma_k 1[month(t) = k]', ce['model'], 'model')
    _require('Pearson chi-square / residual df', ce['model'], 'dispersion')
    _require('log( sum over formats and window months of Y / sum of mu )', ce['effect'], 'tau')
    _require('log(sum Y) - log(sum mu) ) / sqrt( phi / sum mu )', ce['standardised_gap'], 'z')

    # inference
    S.alpha = _num(r'one-sided p < ([\d.]+) for a single test', inf['detected'], 'single-test significance')
    S.bh_q = _num(r'BH q < ([\d.]+) within each level', inf['detected'], 'BH threshold')
    _require('no interest shift start in months -6..+6 and does not share its parent', inf['placebo_categories'], 'placebo categories')
    _require('one-sided p = rank of the treated z', inf['placebo_categories'], 'placebo p')
    _require('every other year from 2017', inf['placebo_years'], 'placebo years')
    _require('share of placebo z at or above the treated z', inf['placebo_years'], 'placebo years')
    S.placebo_cat_no_shift = (-6, 6)

    # positive controls
    _require('tau > 0 with one-sided placebo-category p < 0.05', pc['rule'], 'control rule')
    S.controls = _controls(pc)
    if tuple((c['label'], c['shift_month']) for c in S.controls) != tuple((c['label'], c['shift_month']) for c in s3.controls):
        raise SettingsError('the three positive controls differ from Study 3 although the record says they are unchanged')

    # power
    _require('(1 + L) in months 0..+2', pw['method'], 'power window')
    S.power_lifts = tuple(float(x) for x in pw['lift_sizes'])
    if S.power_lifts != tuple(sorted(S.power_lifts)):
        raise SettingsError('lift sizes not in increasing order')
    S.power_draws = _num(r'^(\d+) per size and size band', pw['draws'], 'draws', int)
    _require('quartiles of the expected weighted checkouts over the primary window (sum of mu)', pw['size_bands'], 'size bands')
    S.power_bands = 4
    S.power_rate = _num(r'detected in at least (\d+)% of draws', pw['minimum_detectable_effect'], 'MDE rate') / 100.0
    S.power_seed = int(pw['seed'])
    S.power_alpha = S.alpha
    S.power_window = S.window_primary

    # all shifts and sentiment
    _require('quality-ok main-set shifts (labelled, not seasonal)', al['set'], 'shift set')
    _require('bootstrap clustered by category', al['pooled'], 'pooled bootstrap')
    _require('with tau from this model as the outcome', al['carry_over'], 'carry-over')
    S.sent_features = tuple(se['features'])
    _require('delta tone (mean of the first 4 weeks minus the 26-week median)', S.sent_features[0], 'tone feature')
    _require('delta intensity = delta (positive + negative)', S.sent_features[3], 'intensity feature')
    _require('negative shift = 1 if delta tone < 0', S.sent_features[4], 'negative shift')
    S.sent_placebo_n = _num(r'comparison with (\d+) placebo windows per category, two-sided', ' '.join(se['tests']), 'placebo windows', int)
    _require('negative shift x sustained interaction', ' '.join(se['tests']), 'interaction')
    _require('GDELT tone only', se['source'], 'sentiment source')
    S.sent_placebo_len = s3.tone_placebo_len      # the placebo windows have the Study 3 length (4 weeks)

    # the record's "unchanged from Study 3" list must agree with the parsed Study 3 values
    un = ' | '.join(rec['unchanged_from_study3'])
    _require(f'{s3.es_fit_len} months ending at month {s3.es_fit_end}', un, 'unchanged fit window')
    _require(f'{s3.boot_n:,}, seed {s3.boot_seed}', un, 'unchanged bootstrap')
    _require(f'BH q < {s3.bh_q:.2f}', un, 'unchanged BH')
    if S.window_primary != (0, 2) or S.window_secondary != (0, 5):
        raise SettingsError('effect windows differ from months 0..+2 and 0..+5')
    if S.es_fit_len != S.fit_len_check:
        raise SettingsError('the feasibility rule counts a different number of fit months than the fit window')
    if S.power_seed != S.boot_seed:
        raise SettingsError('power seed differs from the bootstrap seed; check the record')
    return S


def load(record=RECORD, readme=README, addenda_dir=ADDENDA, s3_record=None, s3_readme=None, s3_addenda=None):
    """Check both hashes, apply both addenda folders, parse. Any hash mismatch raises SettingsError (stops the run).
    The s3_* arguments exist for the tests; real runs use the Study 3 defaults."""
    kw = {}
    if s3_record is not None:
        kw['record'] = s3_record
    if s3_readme is not None:
        kw['readme'] = s3_readme
    if s3_addenda is not None:
        kw['addenda_dir'] = s3_addenda
    s3 = S3.load(**kw)                              # Study 3 record: hash check + addenda a..i
    expected, got = readme_hash(readme), sha256_of(record)
    if got != expected:
        raise SettingsError(f'SHA-256 of {pathlib.Path(record).name} is {got}, but prereg/README.md says {expected}. '
                            'The fixed Study 3b settings were changed or replaced; nothing runs until this is resolved.')
    rec = json.loads(pathlib.Path(record).read_text())
    files = sorted(pathlib.Path(addenda_dir).glob('*.json')) if addenda_dir and pathlib.Path(addenda_dir).exists() else []
    applied = S3.apply_addenda(rec, files)
    S = parse(rec, s3)
    S.sha256 = got
    S.sha256_study3 = s3.sha256
    S.addenda = tuple(s3.addenda) + tuple(applied)       # Study 3 addenda first, then the Study 3b ones
    S.addenda_3b = tuple(applied)
    return S


SETTINGS = load()


if __name__ == '__main__':
    for k, v in vars(SETTINGS).items():
        if k not in ('record', 'record3'):
            print(f'{k:24s} {v}')
