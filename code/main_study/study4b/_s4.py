# Loads the Study 4 modules (code/main_study/study4/) for reuse WITHOUT module-name clashes (same method as Study 3b's _s3.py).
# Study 4 and Study 4b both have a module called _settings, and Study 4's modules import each other by bare names
# (_settings, _features, _models, _forecast, _eval). They are imported once with the Study 4 folder first on the path and are
# then taken out of sys.modules again (whatever was there before, such as 4b's own _settings, is put back).
# The caller gets them under short names: s4.settings, s4.features, s4.models, s4.forecast, s4.evalm, s4.sim (test worlds).
# Study 4 functions are only called inside the process; never pass one to multiprocessing (a worker would look the module up
# by its bare name). Study 4b's own modules have distinct names (_b_*.py) apart from _settings.
import sys, importlib, pathlib

HERE = pathlib.Path(__file__).resolve().parent
STUDY4 = HERE.parent / 'study4'
_NAMES = {'settings': '_settings', 'features': '_features', 'models': '_models', 'forecast': '_forecast', 'evalm': '_eval'}
_ALL = ('_settings', '_features', '_models', '_forecast', '_eval', 'sim')


def _load(with_sim=False):
    saved = {n: sys.modules.pop(n) for n in _ALL if n in sys.modules}
    sys.path.insert(0, str(STUDY4))
    if with_sim:
        sys.path.insert(0, str(STUDY4 / 'tests'))
    try:
        mods = {short: importlib.import_module(full) for short, full in _NAMES.items()}
        if with_sim:
            mods['sim'] = importlib.import_module('sim')
    finally:
        for p in (str(STUDY4), str(STUDY4 / 'tests')):
            while p in sys.path:
                sys.path.remove(p)
        for n in _ALL:
            sys.modules.pop(n, None)
        sys.modules.update(saved)
    return mods


_m = _load()
settings, features, models, forecast, evalm = (_m[k] for k in ('settings', 'features', 'models', 'forecast', 'evalm'))


def load_sim():
    """Study 4's simulated-world builder (tests only). Loaded on demand; its _features is the same Study 4 module object."""
    return _load(with_sim=True)['sim']
