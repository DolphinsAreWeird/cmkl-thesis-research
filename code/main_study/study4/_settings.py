# Fixed Study 4 settings, read from the dated record in prereg/ (read-only, never edited here).
# 1) The record's SHA-256 must equal the value printed in prereg/README.md (Study 4 section); otherwise nothing runs.
# 2) The addenda in prereg/addenda_forecast/*.json are applied in file-name order (same format as Study 3:
#    {"date": ..., "changes": {"dotted.path": value}}).
# 3) Every number the Study 4 code uses is parsed here from the record's own wording. A parse that does not match the
#    wording stops the run, so no script hard-codes a threshold, window, seed or size that is in the record.
# Values the code needs but the record does not give sit next to the code that uses them, marked '# NOT IN RECORD:'.
import json, re, hashlib, pathlib
from datetime import datetime

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]                      # .../handoff
PREREG = ROOT / 'prereg'
RECORD = PREREG / 'forecast_settings_2026-10-13.json'
README = PREREG / 'README.md'
ADDENDA = PREREG / 'addenda_forecast'
DATA = ROOT / 'data'
DB = DATA / 'db'
REPORTS = DATA / 'reports'
OUT = DB / 'study4'

# NOT IN RECORD: the record says "at most 4" workers; the machine rule for this build is 3 (8 cores, 8 GB RAM).
DEFAULT_WORKERS = 3
THREAD_BUDGET = 3          # total threads for the whole run (workers x CatBoost threads)


class SettingsError(SystemExit):
    """The record cannot be trusted or parsed. Subclass of SystemExit so scripts stop with the message."""


def sha256_of(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def readme_hash(readme_path=README, record_name=RECORD.name):
    """The SHA-256 printed in the README line for this record (the README also holds the Study 3 hash)."""
    text = pathlib.Path(readme_path).read_text()
    i = text.find(record_name)
    if i < 0:
        raise SettingsError(f'{record_name} is not named in {readme_path}')
    m = re.search(r'SHA-256 of the record:\s*`([0-9a-f]{64})`', text[i:])
    if not m:
        raise SettingsError(f'no SHA-256 line found after {record_name} in {readme_path}')
    return m.group(1)


def _set_path(rec, path, value):
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
    """Apply addenda in file-name order; returns [(file name, sha256, date)]."""
    applied = []
    for f in sorted(files, key=lambda p: pathlib.Path(p).name):
        A = json.loads(pathlib.Path(f).read_text())
        for path, value in A['changes'].items():
            _set_path(rec, path, value)
        applied.append((pathlib.Path(f).name, sha256_of(f), A.get('date')))
    return applied


def _text(x):
    return x['text'] if isinstance(x, dict) else x


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


def _months_named(text):
    out = []
    for name, year in re.findall(r'\b(January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})\b', text):
        out.append(datetime.strptime(f'{name} {year}', '%B %Y').strftime('%Y-%m'))
    return tuple(out)


def mi_from_ym(ym):
    y, m = ym.split('-')
    return int(y) * 12 + int(m) - 1


def ym_of(mi):
    mi = int(mi)
    return f'{mi // 12:04d}-{mi % 12 + 1:02d}'


class Settings:
    def __repr__(self):
        keys = [k for k in vars(self) if k not in ('record',)]
        return 'Settings(' + ', '.join(f'{k}={getattr(self, k)!r}' for k in keys) + ')'


def parse(rec):
    S = Settings()
    S.record = rec
    S.fixed_on = rec['fixed_on']
    un, tg, ins, ft, md = rec['units'], rec['target'], rec['information_set'], rec['features'], rec['models']
    tt, me, fl, sc = rec['training_and_testing'], rec['metrics'], rec['interest_flow'], rec['showcases']

    # ---- units
    S.seattle_formats = tuple(un['formats'])
    S.librivox_format = 'librivox'                              # data schema (panel file), not a setting
    _require('narrow and middle', _text(un['categories']), 'categories')
    _require('broad descriptive only', _text(un['categories']), 'categories')
    S.levels = ('narrow', 'middle')
    S.size_lookback = _num(r'over the (\d+) months before the origin month', _text(un['eligibility']), 'size look-back', int)
    _require('Study 3 minimum-size rule', _text(un['eligibility']), 'eligibility')
    _require('secondary series, reported separately', _text(un['librivox']), 'LibriVox')

    # ---- targets and horizons
    _require('horizon 1', _text(tg['main']), 'main target')
    _require('horizon 2', _text(tg['secondary_horizon']), 'horizon 2')
    S.horizons = (1, 2)
    _require('never scored', _text(tg['missing']), 'missing months')
    _require('both available', _text(tg['missing']), 'missing months')

    # ---- information set and features
    _require('Monday start', _text(ins['interest']), 'interest information set')
    _require('Sunday falls on or before the last day', _text(ins['interest']), 'interest information set')
    d = ' '.join(ft['demand_only_D'])
    _require('log share at t, t-1, t-2', d, 'D features')
    S.year_lag = _num(r'log share at t-(\d+) \(the target month one year earlier\)', d, 'year lag', int)
    S.demand_mean_window = _num(r'mean log share over t-(\d+)\.\.t', d, 'demand mean window', int) + 1
    _require('change in log of all checkouts in the format, t vs t-1', d, 'D features')
    w = ' '.join(ft['interest_W_wikipedia'])
    S.recent_weeks = _num(r'last (\d+) weeks', w, 'recent weeks', int)
    S.normal_weeks = _num(r'\((\d+)-week median\)', w, 'normal weeks', int)
    S.mk_weeks = _num(r'(\d+)-week Mann-Kendall', w, 'Mann-Kendall weeks', int)
    S.shift_weeks = _num(r'a shift started in the last (\d+) weeks', w, 'shift window', int)
    _require('weeks since its start', w, 'W features')
    _require('same five features from GDELT volume', _text(ft['interest_G_gdelt']), 'G features')
    t = _text(ft['tone_T'])
    S.tone_weeks = _num(r'over the last (\d+) weeks', t, 'tone weeks', int)
    S.tone_baseline_weeks = _num(r'previous (\d+) weeks', t, 'tone baseline weeks', int)
    _require('ridge uses 0 plus a missing indicator', _text(ft['missing_interest']), 'missing interest')

    # ---- models
    _require('y(t+1) = y(t)', _text(md['naive']), 'naive')
    _require('y(t-11) + (mean of y over t-11..t) - (mean of y over t-23..t-12)', _text(md['seasonal_naive']), 'seasonal naive')
    r = _text(md['ridge'])
    S.ridge_alphas = tuple(float(x) for x in _find(r'\{([^}]*)\}', r, 'ridge alphas').group(1).split(','))
    S.ridge_val_origins = _num(r'last (\d+) training origins', r, 'ridge validation origins', int)
    _require('standardised on training rows only', r, 'ridge')
    c = _text(md['catboost_main'])
    S.cb_iterations = _num(r'iterations (\d+)', c, 'iterations', int)
    S.cb_depth = _num(r'depth (\d+)', c, 'depth', int)
    S.cb_learning_rate = _num(r'learning_rate ([\d.]+)', c, 'learning rate')
    S.cb_loss = _find(r'loss (\w+)', c, 'loss').group(1)
    S.cb_seed = _num(r'random_seed (\d+)', c, 'seed', int)
    cats = _find(r'categorical: ([^;]*);', c, 'categorical').group(1)
    names = [x.strip() for x in cats.split(',')]
    colmap = {'format': 'format', 'level': 'level', 'broad category': 'broad_id', 'target month': 'tmonth'}
    if any(n not in colmap for n in names):
        raise SettingsError(f'unknown categorical feature in {cats!r}')
    S.cat_features = tuple(colmap[n] for n in names)
    _require('no category id', c, 'catboost')
    S.feature_sets = tuple(md['feature_sets'])
    if S.feature_sets != ('D', 'D+W', 'D+W+G', 'D+W+G+T'):
        raise SettingsError(f'unexpected feature sets {S.feature_sets}')
    _require('CatBoost D+W against CatBoost D', _text(md['main_comparison']), 'main comparison')

    # ---- scheme and test origins
    _require('expanding window', _text(tt['scheme']), 'scheme')
    _require('s+h', _text(tt['scheme']), 'scheme')
    S.test_start = _find(r'^(\d{4}-\d{2}) to the last origin', _text(tt['test_origins_main']), 'test start').group(1)
    m = _find(r'^(\d{4}-\d{2}) to (\d{4}-\d{2}) for D\+W\+G and D\+W\+G\+T', _text(tt['test_origins_gdelt']), 'GDELT origins')
    S.gdelt_start, S.gdelt_end = m.group(1), m.group(2)
    S.max_workers_record = _num(r'at most (\d+)', _text(tt['workers']), 'workers', int)

    # ---- metrics
    inf = _text(me['inference'])
    S.dm_lag = _num(r'lag (\d+)', inf, 'Newey-West lag', int)
    _require('one-sided', inf, 'DM')
    S.boot_block = _num(r'block (\d+) months', inf, 'block length', int)
    S.boot_n = _num(r'([\d,]+) resamples', inf, 'resamples', int)
    S.boot_seed = _num(r'seed (\d+)', inf, 'bootstrap seed', int)
    h = _text(me['helps_rule'])
    S.helps_alpha = _num(r'DM p < ([\d.]+)', h, 'helps p')
    S.ci_level = _num(r'(\d+)% bootstrap interval', h, 'interval level') / 100
    _require('skill > 0', h, 'helps rule')
    _require('all formats pooled at each level', h, 'helps rule')
    sec = ' '.join(me['secondary'])
    S.top_share = _num(r'top-(\d+)% hit rate', sec, 'top share') / 100
    S.direction_min = _num(r'actual change exceeds ([\d.]+)', sec, 'direction threshold')
    S.cond_shift_weeks = _num(r'started in the (\d+) weeks before the origin', _text(me['conditional']), 'conditional window', int)
    _require('quality-ok', _text(me['conditional']), 'conditional')

    # ---- interest flow
    S.flow_recent_weeks = _num(r'naive \(last (\d+) weeks', _text(fl['models']), 'flow naive weeks', int)
    m = _find(r'weekly lags (\d+)-(\d+) and (\d+)', _text(fl['models']), 'flow lags')
    S.flow_lags = tuple(range(int(m.group(1)), int(m.group(2)) + 1)) + (int(m.group(3)),)
    S.flow_ratio = _num(r'at least ([\d.]+) times', _text(fl['metrics']), 'flow ratio')
    S.flow_test_start = _find(r'origins (\d{4}-\d{2}) onward', _text(fl['same_scheme']), 'flow test start').group(1)

    # ---- showcases
    cases = []
    for s in sc['cases']:
        m = _find(r'^(.*?), ([a-z ]+): origins? (.*)$', s, 'showcase case')
        fmts = tuple(x.strip() for x in m.group(2).split(' and '))
        origins = _months_named(m.group(3).split(', target')[0])
        if not origins:
            raise SettingsError(f'no origin month in showcase {s!r}')
        cases.append(dict(label=m.group(1).strip(), formats=fmts, origins=origins, text=s))
    S.showcases = tuple(cases)
    return S


def load_settings(record=None, readme=None, addenda_dir=None):
    """Load the record, stop if its SHA-256 differs from the README, apply addenda, parse."""
    record = pathlib.Path(record or RECORD)
    readme = pathlib.Path(readme or README)
    addenda_dir = pathlib.Path(addenda_dir or ADDENDA)
    want, got = readme_hash(readme, RECORD.name), sha256_of(record)
    if want != got:
        raise SettingsError(f'SHA-256 mismatch: {record.name} is {got} but {readme.name} says {want}. '
                            'The record may have been edited; nothing will run.')
    rec = json.loads(record.read_text())
    files = sorted(addenda_dir.glob('*.json')) if addenda_dir.exists() else []
    applied = apply_addenda(rec, files)
    S = parse(rec)
    S.sha256 = got
    S.addenda = applied
    return S


_CACHE = {}


def settings():
    if 'S' not in _CACHE:
        _CACHE['S'] = load_settings()
    return _CACHE['S']


def thread_plan(workers):
    """(workers, CatBoost threads per worker) so that workers x threads stays within THREAD_BUDGET."""
    S = settings()
    workers = int(workers)
    if workers < 1 or workers > S.max_workers_record:
        raise SettingsError(f'--workers must be between 1 and {S.max_workers_record} (record)')
    return workers, max(1, THREAD_BUDGET // workers)
