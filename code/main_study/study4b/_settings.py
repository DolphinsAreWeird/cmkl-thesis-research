# Fixed Study 4b settings, read from the dated record in prereg/ (read-only, never edited here).
# 1) Both records must match the SHA-256 printed in prereg/README.md: the Study 4b record (this study) and the Study 4 record
#    that it builds on (checked through Study 4's own loader, which also applies prereg/addenda_forecast/). Any mismatch stops
#    the run (SettingsError is a SystemExit).
# 2) prereg/addenda_4b/*.json are applied to the 4b record in file-name order (same format as Study 4: {"date", "changes"}).
# 3) Every number used here is parsed from the record's own wording; a parse that does not match stops the run.
# Study 4's modules come through _s4 (no module-name clash with this file). Values the record does not give sit next to the
# code that uses them, marked '# NOT IN RECORD:'.
import json, re, pathlib, math
from datetime import datetime
import _s4

S4M = _s4.settings                      # Study 4's settings module
SettingsError = S4M.SettingsError
sha256_of, apply_addenda = S4M.sha256_of, S4M.apply_addenda
mi_from_ym, ym_of = S4M.mi_from_ym, S4M.ym_of
_text, _find, _num, _require = S4M._text, S4M._find, S4M._num, S4M._require

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREREG = ROOT / 'prereg'
RECORD = PREREG / 'study4b_settings_2026-10-14.json'
README = PREREG / 'README.md'
ADDENDA = PREREG / 'addenda_4b'
DATA, DB, REPORTS = ROOT / 'data', ROOT / 'data' / 'db', ROOT / 'data' / 'reports'
OUT = DB / 'study4b'
S4_FEATURES = DB / 'study4' / 'features.parquet'
S4_FORECASTS = DB / 'study4' / 'forecasts.parquet'

def readme_hash(readme_path, record_name):
    """The SHA-256 printed in the README section of this record. The Study 4b line reads 'SHA-256: `...`' (Study 4's reads
    'SHA-256 of the record: `...`'), so both forms are accepted; the search stops at the next '## ' heading."""
    text = pathlib.Path(readme_path).read_text()
    i = text.find(record_name)
    if i < 0:
        raise SettingsError(f'{record_name} is not named in {readme_path}')
    j = text.find('\n## ', i)
    m = re.search(r'SHA-256(?: of the record)?:\s*`([0-9a-f]{64})`', text[i:j if j > 0 else None])
    if not m:
        raise SettingsError(f'no SHA-256 line found for {record_name} in {readme_path}')
    return m.group(1)


# NOT IN RECORD: same machine rule as Study 4 (8 cores, 8 GB RAM): 3 workers by default, 3 threads in all.
DEFAULT_WORKERS = S4M.DEFAULT_WORKERS
THREAD_BUDGET = S4M.THREAD_BUDGET


class Settings:
    def __repr__(self):
        return 'Settings(' + ', '.join(f'{k}={v!r}' for k, v in vars(self).items() if k not in ('record', 's4')) + ')'


def _months(text):
    return [datetime.strptime(f'{a} {b}', '%B %Y').strftime('%Y-%m')
            for a, b in re.findall(r'\b(January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})\b', text)]


def parse(rec, S4):
    B = Settings()
    B.record, B.s4 = rec, S4
    B.fixed_on = rec['fixed_on']
    un, pa, pb = rec['units'], rec['part_a_change_forecasts'], rec['part_b_surges']

    # ---- units
    B.levels = tuple(un['levels'])
    if B.levels != ('narrow', 'middle') or B.levels != tuple(S4.levels):
        raise SettingsError(f'unexpected levels {B.levels}')
    B.formats_primary, B.formats_secondary = tuple(un['formats_primary']), tuple(un['formats_secondary'])
    if B.formats_primary != ('print', 'ebook') or B.formats_secondary != ('audiobook',):
        raise SettingsError('unexpected formats')
    _require('Study 3 minimum-size rule', _text(un['eligibility']), 'eligibility')

    # ---- Part A
    _require('d(t+h) - d(t)', _text(pa['target']), 'target')
    hz = pa['horizons']
    B.h_primary = int(hz['primary'])
    B.horizons = tuple(sorted({B.h_primary, *[int(x) for x in hz['secondary']]}))
    if B.h_primary != 2 or B.horizons != (1, 2, 3):
        raise SettingsError(f'unexpected horizons {hz}')
    _require('zero change', ' '.join(pa['models']), 'models')
    _require('ridge on the change', ' '.join(pa['models']), 'models')
    c = _text(pa['catboost'])
    B.cb_iterations = _num(r'iterations (\d+)', c, 'iterations', int)
    B.cb_depth = _num(r'depth (\d+)', c, 'depth', int)
    B.cb_learning_rate = _num(r'learning_rate ([\d.]+)', c, 'learning rate')
    B.cb_loss = _find(r'loss (\w+)', c, 'loss').group(1)
    B.cb_seed = _num(r'random_seed (\d+)', c, 'seed', int)
    _require('thread_count per Study 4', c, 'catboost')
    same = (B.cb_iterations, B.cb_depth, B.cb_learning_rate, B.cb_loss, B.cb_seed) == \
           (S4.cb_iterations, S4.cb_depth, S4.cb_learning_rate, S4.cb_loss, S4.cb_seed)
    if not same:
        raise SettingsError('the CatBoost settings of the 4b record differ from Study 4 (the code reuses the Study 4 trainer)')
    B.cat_features = tuple(S4.cat_features)
    fs = pa['feature_sets']
    B.feature_sets = tuple(fs.keys())
    if B.feature_sets != ('D', 'D+W', 'D+W+S'):
        raise SettingsError(f'unexpected feature sets {B.feature_sets}')
    _require('Study 4 demand-only features', fs['D'], 'D')
    _require('Wikipedia interest features', fs['D+W'], 'W')
    s = fs['D+W+S']
    B.sustained_weeks = _num(r'started in the (\d+) weeks before the origin', s, 'S shift window', int)
    if B.sustained_weeks != S4.shift_weeks:
        raise SettingsError('the S shift window differs from the Study 4 shift window')
    _require('sustained by its fourth week', s, 'S feature 1')
    _require('mean Study 3 synthetic-control effect', s, 'S feature 2')
    m = _find(r'months (\d+) to \+(\d+)\) ended on or before the origin', s, 'effect window')
    B.effect_window = (int(m.group(1)), int(m.group(2)))                 # (0, 2): known once month 0 + 2 is over
    _require('0 when none', s, 'S feature 2')
    sc = _text(pa['scheme'])
    _require('expanding window', sc, 'scheme')
    _require('retrained at every origin', sc, 'scheme')
    B.test_start = _find(r'test origins (\d{4}-\d{2}) to the last origin', sc, 'test start').group(1)
    me = _text(pa['metrics'])
    B.dm_lag = _num(r'Newey-West lag (\d+)', me, 'Newey-West lag', int)
    m = _find(r'block (\d+), ([\d,]+), seed (\d+)', me, 'bootstrap')
    B.boot_block, B.boot_n, B.boot_seed = int(m.group(1)), int(m.group(2).replace(',', '')), int(m.group(3))
    _require('skill = 1 - MAE(new) / MAE(base)', me, 'metrics')
    _require('one-sided', me, 'DM')
    hr = _text(pa['helps_rule'])
    B.helps_alpha = _num(r'DM p < ([\d.]+)', hr, 'helps p')
    _require('skill > 0', hr, 'helps rule')
    _require('bootstrap interval above zero', hr, 'helps rule')
    _require('print and ebook pooled at each level', hr, 'helps rule')
    _require('compared with zero change', hr, 'helps rule')
    B.ci_level = 0.95                                                    # the record says "bootstrap interval"; Part B says 95%

    # ---- Part B
    su = _text(pb['surge'])
    B.surge_ratio = _num(r'log\(([\d.]+)\)', su, 'surge ratio')
    B.surge_change = math.log(B.surge_ratio)
    B.h_surge = _num(r'primary h = (\d+)', su, 'surge horizon', int)
    if B.h_surge != B.h_primary:
        raise SettingsError('surge horizon differs from the primary horizon')
    _require('CatBoost classifier (logloss', _text(pb['models']), 'Part B models')
    _require('logistic regression', _text(pb['models']), 'Part B models')
    mt = _text(pb['metrics'])
    _require('average precision (primary)', mt, 'Part B metrics')
    B.top_k = _num(r'(\d+) highest-scored', mt, 'top k', int)
    _require('Brier score', mt, 'Part B metrics')
    inf = _text(pb['inference'])
    m = _find(r'block (\d+) months, ([\d,]+), seed (\d+)', inf, 'Part B bootstrap')
    if (int(m.group(1)), int(m.group(2).replace(',', '')), int(m.group(3))) != (B.boot_block, B.boot_n, B.boot_seed):
        raise SettingsError('Part B bootstrap settings differ from Part A')
    B.ci_level = _num(r'(\d+)% interval', inf, 'Part B interval', float) / 100
    cases = []
    for t in pb['showcases']:
        m = _find(r'^(.*?), ([a-z ]+), origin ([A-Z][a-z]+ \d{4}) \(target ([A-Z][a-z]+ \d{4})\)$', t, 'showcase')
        o, tg = _months(m.group(3))[0], _months(m.group(4))[0]
        if mi_from_ym(tg) - mi_from_ym(o) != B.h_surge:
            raise SettingsError(f'showcase target is not origin + {B.h_surge}: {t!r}')
        cases.append(dict(label=m.group(1).strip(), formats=tuple(x.strip() for x in m.group(2).split(' and ')), origin=o, target=tg, text=t))
    B.showcases = tuple(cases)
    return B


def load_settings(record=None, readme=None, addenda_dir=None, study4_record=None, study4_addenda=None):
    """Both hashes are checked first (Study 4's record through Study 4's loader, then the 4b record); then the 4b addenda are
    applied and the record is parsed. Any mismatch raises SettingsError."""
    record = pathlib.Path(record or RECORD)
    readme = pathlib.Path(readme or README)
    addenda_dir = pathlib.Path(addenda_dir or ADDENDA)
    S4 = S4M.load_settings(record=study4_record, readme=readme, addenda_dir=study4_addenda)     # Study 4 hash + its addenda
    want, got = readme_hash(readme, RECORD.name), sha256_of(record)
    if want != got:
        raise SettingsError(f'SHA-256 mismatch: {record.name} is {got} but {readme.name} says {want}. '
                            'The record may have been edited; nothing will run.')
    rec = json.loads(record.read_text())
    files = sorted(addenda_dir.glob('*.json')) if addenda_dir.exists() else []
    applied = apply_addenda(rec, files)
    B = parse(rec, S4)
    B.sha256, B.addenda = got, applied
    B.sha256_study4, B.addenda_study4 = S4.sha256, S4.addenda
    return B


_CACHE = {}


def settings():
    if 'B' not in _CACHE:
        _CACHE['B'] = load_settings()
    return _CACHE['B']


def thread_plan(workers):
    """(workers, CatBoost threads per worker) with workers x threads within THREAD_BUDGET (same rule as Study 4)."""
    B = settings()
    workers = int(workers)
    if workers < 1 or workers > B.s4.max_workers_record:
        raise SettingsError(f'--workers must be between 1 and {B.s4.max_workers_record} (Study 4 record)')
    return workers, max(1, THREAD_BUDGET // workers)
