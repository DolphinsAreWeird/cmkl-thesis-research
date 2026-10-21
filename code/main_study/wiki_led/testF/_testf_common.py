# Shared helpers for the Test F data scripts (AI matchmaking; settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json).
# Data only: nothing here reads loans, fits a model or sorts a page or a book into a theme.
# Paths and the user agent come from code/config.py through ../_common.py (the Http class with its on-disk cache and back-off is reused;
# only the cache folder differs: data/interim/testF_cache).
import sys, os, re, json, gzip, time, hashlib, pathlib, unicodedata, html
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))                     # code/main_study/wiki_led (for _common)
import numpy as np                                         # noqa: E402
import _common as C                                        # noqa: E402
from config import ROOT                                    # noqa: E402  (handoff/; _common has put code/ on the path)

D = C.D
REP = pathlib.Path(os.environ.get('TESTF_REP', str(C.REP)))              # the environment overrides are for dry runs only
OUT = pathlib.Path(os.environ.get('TESTF_OUT', str(D / 'db' / 'wiki_led' / 'testF')))
CACHE = pathlib.Path(os.environ.get('TESTF_CACHE', str(D / 'interim' / 'testF_cache')))
PREREG = pathlib.Path(ROOT) / 'prereg' / 'addenda_wiki_led'
ADDENDUM = PREREG / '2026-10-21_g_ai_matchmaking.json'
GUIDE = PREREG / '2026-10-21_g_theme_guide.tsv'
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)

SEED_ORDER = 20261021        # one-day sample, page and book order (ids)
SEED_REL = 20261022          # reliability sets
SEED_JUDGE = 20261023        # judge set for check G1
CHUNK = 2500

# the namespace rule of the addendum (page_universe), applied as prefixes to the titles as they appear in data/raw/wiki_top_daily.json.
# Main_Page is a prefix too (it also drops 'Main_Page/'), which reproduces the addendum's counts (139,161 titles, 84,577 on 2 days or more).
NS_PREFIXES = ('Main_Page', 'Special:', 'Wikipedia:', 'Portal:', 'File:', 'Help:', 'Template:', 'Category:', 'User:', 'Talk:', 'Book:', 'Draft:',
               'Module:')
# the three pages named as examples in the page instructions; left out of every validation set (with every title that redirects to them)
PROMPT_EXAMPLES = ('The_Bear_(TV_series)', "Ocean's_8", 'Adolescence_(TV_series)')

log = C.log


def excluded_title(t):
    return t.startswith(NS_PREFIXES)


class Http(C.Http):
    """The Http class of ../_common.py with its cache in data/interim/testF_cache (one gzip file per request)."""

    @staticmethod
    def path(url, params):
        key = json.dumps([url, sorted((params or {}).items())], sort_keys=True)
        h = hashlib.sha1(key.encode()).hexdigest()
        return CACHE / 'http' / h[:2] / (h + '.json.gz')


maxlag_check = C.maxlag_check

_WS = re.compile(r'\s+')
_TAG = re.compile(r'<[^>]{0,200}>')


def clean(s, cut=None):
    """One line of plain text: control characters (tabs and newlines among them) become spaces, runs of white space become one space,
    the ends are trimmed; with cut, the text is cut at that many characters (and trimmed again)."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ''
    s = str(s)
    s = ''.join(' ' if unicodedata.category(ch) == 'Cc' else ch for ch in s)
    s = _WS.sub(' ', s).strip()
    if cut and len(s) > cut:
        s = s[:cut].rstrip()
    return s


def clean_html(s, cut=None):
    """For Goodreads descriptions: HTML entities decoded and tags removed before clean()."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ''
    s = html.unescape(str(s))
    s = _TAG.sub(' ', s)
    return clean(s, cut)


def write_tsv(path, header, rows):
    """Plain tab-separated file, UTF-8, LF, one header line, no quoting.  Every field must already be one line without tabs."""
    path = pathlib.Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\t'.join(header) + '\n')
        for r in rows:
            r = ['' if v is None else str(v) for v in r]
            for v in r:
                if '\t' in v or '\n' in v or '\r' in v:
                    raise ValueError(f'tab or newline in a field of {path.name}: {v[:80]!r}')
            if len(r) != len(header):
                raise ValueError(f'{path.name}: {len(r)} fields, header has {len(header)}')
            f.write('\t'.join(r) + '\n')
    os.replace(tmp, path)


def read_tsv(path):
    """Read a file written by write_tsv back as a list of lists of strings (header first), checking the field count of every line."""
    with open(path, encoding='utf-8', newline='\n') as f:
        lines = f.read().split('\n')
    assert lines[-1] == '', f'{path}: no final newline'
    rows = [ln.split('\t') for ln in lines[:-1]]
    n = len(rows[0])
    bad = [i for i, r in enumerate(rows) if len(r) != n]
    assert not bad, f'{path}: lines with a wrong number of fields: {bad[:5]}'
    return rows


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def page_universe():
    """From data/raw/wiki_top_daily.json: per title the number of different days in the daily top 500 and the first and last day.
    Returns (universe, one_day): dicts title -> (n_days, first_day, last_day) after the namespace rule; universe has 2 days or more."""
    top = json.load(open(D / 'raw' / 'wiki_top_daily.json'))
    info = {}
    for day in sorted(top):
        seen = set()
        for t, _ in top[day]:
            if t in seen:
                continue
            seen.add(t)
            if t in info:
                n, first, _last = info[t]
                info[t] = (n + 1, first, day)
            else:
                info[t] = (1, day, day)
    kept = {t: v for t, v in info.items() if not excluded_title(t)}
    uni = {t: v for t, v in kept.items() if v[0] >= 2}
    one = {t: v for t, v in kept.items() if v[0] == 1}
    return uni, one, len(info), len(kept), (min(top), max(top), len(top))
