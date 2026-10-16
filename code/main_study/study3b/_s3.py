# Loads the Study 3 modules (code/main_study/study3/) for reuse WITHOUT module-name clashes.
# Study 3 and Study 3b both have modules called _settings, _methods and so on. Study 3's modules import each other by
# those bare names, so they are imported once with the Study 3 folder first on the path, and are then taken out of
# sys.modules again (whatever was there before is put back). The caller gets them under short names:
#   s3.settings, s3.files, s3.build, s3.inputs, s3.interest, s3.methods
# Study 3b's own modules of the same name stay importable as usual. Study 3 functions are only called inside the
# process; never pass a Study 3 function or object to joblib (a worker would look the module up by its bare name).
import sys, importlib, pathlib, types

HERE = pathlib.Path(__file__).resolve().parent
STUDY3 = HERE.parent / 'study3'
_NAMES = {'settings': '_settings', 'files': '_files', 'build': '_build', 'inputs': '_inputs', 'interest': '_interest',
          'methods': '_methods'}
_ALL = ('_settings', '_files', '_build', '_inputs', '_interest', '_methods', '_analysis', '_sim')


def _load():
    saved = {n: sys.modules.pop(n) for n in _ALL if n in sys.modules}
    sys.path.insert(0, str(STUDY3))
    try:
        mods = {short: importlib.import_module(full) for short, full in _NAMES.items()}
    finally:
        sys.path.remove(str(STUDY3))
        for n in _ALL:
            sys.modules.pop(n, None)
        sys.modules.update(saved)
    return mods


_m = _load()
settings, files, build, inputs, interest, methods = (_m[k] for k in ('settings', 'files', 'build', 'inputs', 'interest', 'methods'))
