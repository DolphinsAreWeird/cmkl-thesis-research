# Shared helpers for the Test F ANALYSIS scripts (20 to 28), AI matchmaking of Wikipedia pages and books into the same book themes.
# Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (read-only; SHA-256 in prereg/README.md), checked on import.
# The data scripts (01 to 03, _testf_common.py) are another agent's; this module only reads their outputs.
#
# Mock mode. A folder with a file named MOCK in it (made by 90_mock_world.py) is a mock world: random theme assignments, and every
# borrowing outcome that a script reads is shuffled across themes and months (shuffle_panel, shuffle_history), so no real effect can be
# seen. Mock runs write their reports into that folder, never into data/reports. Real runs refuse every mock-only option.
import sys, os, re, json, time, zlib, hashlib, pathlib, resource, subprocess
HERE = pathlib.Path(__file__).resolve().parent                 # code/main_study/wiki_led/testF
CODE = HERE.parents[2]                                          # code/
MAIN = HERE.parents[1]                                          # code/main_study/
sys.path.insert(0, str(CODE))
from config import D as _D, UA                                 # noqa: E402
import numpy as np                                              # noqa: E402
import pandas as pd                                             # noqa: E402

D = pathlib.Path(_D)
ROOT = CODE.parent                                              # handoff/
PREREG = ROOT / 'prereg'
ADD = PREREG / 'addenda_wiki_led'
ADDENDUM = ADD / '2026-10-21_g_ai_matchmaking.json'
GUIDE = ADD / '2026-10-21_g_theme_guide.tsv'
FINGERPRINTS = {
    '2026-10-21_g_ai_matchmaking.json': 'f8128eff713ff9a8ac78e68e6a020469b036e4ece9661b7287a1e0dbae3cd7da',
    '2026-10-21_g_prompt_pages.md': 'b044f36598c911e86a294fee2074721857de829ff710a61ff77bfa8002617ae4',
    '2026-10-21_g_prompt_books.md': '6b44099e732b21563647f69e097034dcf3fb5474c3c8b3bfc1139cafa4969cb9',
    '2026-10-21_g_prompt_judge.md': 'bac7e838ad13df93269101a62a476d82c93190a125b51da08aa5e02bba3bbd57',
}
REAL_DIR = D / 'db' / 'wiki_led' / 'testF'
WEEKLY_TOTAL = D / 'db' / 'interest' / 'wiki' / 'weekly_total.parquet'      # the totals the benchmark used (all English Wikipedia user views)
TOP_DAILY = D / 'raw' / 'wiki_top_daily.json'
THEME_NODES = D / 'db' / 'taxonomy_v3' / 'theme_nodes.parquet'

WEIGHT = {3: 1.0, 2: 0.6, 1: 0.3}                               # addendum: confidence 3, 2, 1 count 1.0, 0.6 and 0.3
S2_MAX_PAGES = 40000                                            # addendum: at most 40,000 pages in S2 (the ones with the most top-500 days)
S2_MIN_CONF = 2                                                 # addendum: S2 uses pages assigned with confidence 2 or 3
DAY0, DAY1 = pd.Timestamp('2015-07-01'), pd.Timestamp('2026-09-30')        # S2 download window (addendum)
DAYS = pd.date_range(DAY0, DAY1, freq='D')
NS_PREFIXES = ('Main_Page', 'Special:', 'Wikipedia:', 'Portal:', 'File:', 'Help:', 'Template:', 'Category:', 'User:', 'Talk:', 'Book:',
               'Draft:', 'Module:')                             # as in _testf_common.py (reproduces 139,161 and 84,577)
PROMPT_EXAMPLES = ('The_Bear_(TV_series)', "Ocean's_8", 'Adolescence_(TV_series)')   # left out of every validation score (addendum)
KINDS = ('concept', 'person', 'work', 'event', 'place', 'organization', 'list', 'other')
T0 = time.time()


def check_fingerprints():
    for name, sha in FINGERPRINTS.items():
        got = hashlib.sha256((ADD / name).read_bytes()).hexdigest()
        if got != sha:
            raise SystemExit(f'{name} changed (SHA-256 {got}, fixed {sha}); nothing runs')
    readme = (PREREG / 'README.md').read_text()
    for sha in FINGERPRINTS.values():
        if sha not in readme:
            raise SystemExit(f'fingerprint {sha} is not in prereg/README.md; nothing runs')


check_fingerprints()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


def peak_gb():
    """Peak resident memory of this process in GB (macOS reports ru_maxrss in bytes)."""
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 2 ** 30 if sys.platform == 'darwin' else r / 2 ** 20


def be_nice(n=10):
    try:
        os.nice(n)
    except OSError:
        pass


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- folders and mock mode
class Paths:
    """root: the Test F data folder (data/db/wiki_led/testF) or a mock world (a folder with a MOCK file)."""

    def __init__(self, root=None):
        self.root = pathlib.Path(root).resolve() if root else REAL_DIR
        self.mock = (self.root / 'MOCK').exists()
        if root and not self.mock and self.root != REAL_DIR.resolve():
            raise SystemExit(f'{self.root} is neither the real Test F folder nor a mock world (no MOCK file)')
        self.root.mkdir(parents=True, exist_ok=True)
        self.rep = self.root / 'reports' if self.mock else D / 'reports'
        self.rep.mkdir(parents=True, exist_ok=True)
        self.views = self.root / 'views_store' if self.mock else D / 'interim' / 'testF_views'      # S2 daily views (large)
        self.views.mkdir(parents=True, exist_ok=True)
        self.mock_seed = int((self.root / 'MOCK').read_text().strip() or 0) if self.mock else None

    def __truediv__(self, name):
        return self.root / name

    def report(self, name):
        return self.rep / name

    def tag(self):
        return 'MOCK WORLD (random themes, borrowing shuffled across themes and months)' if self.mock else 'real data'


def mock_only(P, flag_value, name):
    """Options that only make sense in a mock world (for example injected lifts) are refused on real data."""
    if flag_value and not P.mock:
        raise SystemExit(f'{name} is a mock-test option and is refused on real data')


def add_root_arg(ap):
    ap.add_argument('--root', default=None, help='Test F data folder (default data/db/wiki_led/testF); a folder with a MOCK file is a mock world')
    return ap


# ---------------------------------------------------------------- months and weeks
def mi_of_date(d):
    """Month index year * 12 + month - 1 (the Study 3 panel and the benchmark use this index)."""
    d = pd.to_datetime(pd.Series(d)) if not isinstance(d, pd.Timestamp) else d
    if isinstance(d, pd.Timestamp):
        return d.year * 12 + d.month - 1
    return (d.dt.year * 12 + d.dt.month - 1).to_numpy()


def ym(mi):
    mi = int(mi)
    return f'{mi // 12:04d}-{mi % 12 + 1:02d}'


def monday(d):
    d = pd.to_datetime(d)
    return (d - pd.to_timedelta(d.dt.weekday if hasattr(d, 'dt') else d.weekday, unit='D')).normalize()


def weekly_totals():
    """All English Wikipedia user views per ISO week (Monday), with the partial-week flag: the totals of the benchmark."""
    T = pd.read_parquet(WEEKLY_TOTAL)
    T['week'] = pd.to_datetime(T.week).dt.normalize()
    return T.sort_values('week').reset_index(drop=True)


# ---------------------------------------------------------------- themes
def load_nodes():
    N = pd.read_parquet(THEME_NODES, columns=['node_id', 'level', 'parent', 'label'])
    return N


def load_guide(P=None, strict=None):
    """The codes the sorters may use. The guide file (fixed before any sorting) when it exists, else the 242 narrow themes of
    theme_nodes.parquet (the guide is built from them). strict: refuse a guide that is not fingerprinted in prereg/README.md
    (default: on real data)."""
    N = load_nodes()
    narrow = set(N[N.level == 3].node_id)
    strict = (P is not None and not P.mock) if strict is None else strict
    if GUIDE.exists():
        G = pd.read_csv(GUIDE, sep='\t', dtype=str, keep_default_na=False)
        col = [c for c in G.columns if c.strip().lower() == 'code']
        codes = set(G[col[0] if col else G.columns[0]].str.strip())
        sha = sha256_file(GUIDE)
        fp = sha in (PREREG / 'README.md').read_text()
        if strict and not fp:
            raise SystemExit(f'the theme guide {GUIDE.name} (SHA-256 {sha}) is not fingerprinted in prereg/README.md; nothing runs')
        if codes != narrow:
            raise SystemExit(f'the theme guide codes differ from the narrow themes of theme_nodes.parquet ({len(codes)} vs {len(narrow)})')
        info = dict(source=f'prereg/addenda_wiki_led/{GUIDE.name}', sha256=sha, fingerprinted=fp, codes=len(codes))
    else:
        if strict:
            raise SystemExit(f'the theme guide {GUIDE.name} does not exist yet; real runs need it')
        codes = narrow
        info = dict(source='theme_nodes.parquet level 3 (the guide file does not exist yet)', sha256=None, fingerprinted=False, codes=len(codes))
    return codes, info


def parent_map():
    N = load_nodes()
    return dict(zip(N.node_id, N.parent))


def level_of(node_id):
    return node_id.count('.') + 1


# ---------------------------------------------------------------- the daily top 500
def top_long(titles=None):
    """Long table of the daily top 500 (date, title, views) after the namespace rule, optionally for some titles only, and the set of
    days that have a list."""
    top = json.load(open(TOP_DAILY))
    keep = set(titles) if titles is not None else None
    rows = []
    for day, lst in top.items():
        for t, v in lst:
            if t.startswith(NS_PREFIXES):
                continue
            if keep is not None and t not in keep:
                continue
            rows.append((day, t, v))
    L = pd.DataFrame(rows, columns=['date', 'title', 'views'])
    L['date'] = pd.to_datetime(L.date, format='%Y%m%d')
    L['views'] = L.views.astype(np.int64)
    days = pd.DatetimeIndex(sorted(pd.to_datetime(list(top), format='%Y%m%d')))
    return L, days


def top_days_count():
    """title -> number of different days in the daily top 500 (namespace rule applied)."""
    top = json.load(open(TOP_DAILY))
    cnt, vol = {}, {}
    for day, lst in top.items():
        seen = set()
        for t, v in lst:
            if t in seen or t.startswith(NS_PREFIXES):
                continue
            seen.add(t)
            cnt[t] = cnt.get(t, 0) + 1
            vol[t] = vol.get(t, 0) + int(v)
    return pd.DataFrame({'title': list(cnt), 'top_days': list(cnt.values()), 'top_views': [vol[t] for t in cnt]})


# ---------------------------------------------------------------- keys (ids -> titles, work ids)
def page_key(P):
    """id, title, set ('universe' or 'sample1day'), n_top_days from universe.parquet (data script 01)."""
    f = P / 'universe.parquet'
    if not f.exists():
        raise SystemExit(f'{f} not found (made by 01_universe.py)')
    U = pd.read_parquet(f)
    need = {'id', 'title', 'set'}
    if not need <= set(U.columns):
        raise SystemExit(f'{f.name} lacks columns {need - set(U.columns)}')
    return U


def book_key(P, path=None):
    """id, work_id (and title when present) of the 20,000 books. The first existing of the named file or of books.parquet,
    book_key.parquet, books_key.parquet, book_universe.parquet, key_books.parquet; any parquet with columns id and work_id whose ids
    start with 'b' is accepted as a last resort."""
    cands = [pathlib.Path(path)] if path else [P / n for n in ('books.parquet', 'book_key.parquet', 'books_key.parquet', 'book_universe.parquet',
                                                              'key_books.parquet', 'book_text.parquet')]
    for f in cands:
        if f.exists():
            B = pd.read_parquet(f)
            if {'id', 'work_id'} <= set(B.columns):
                return B, f.name
    for f in sorted(P.root.glob('*.parquet')):
        try:
            cols = set(pd.read_parquet(f, columns=None).columns) if f.stat().st_size < 50e6 else set()
        except Exception:
            continue
        if {'id', 'work_id'} <= cols:
            B = pd.read_parquet(f)
            if B.id.astype(str).str.startswith('b').all():
                return B, f.name
    raise SystemExit(f'no book key (id, work_id) found in {P.root}; pass --book-key')


def prompt_example_titles(P):
    """The three example pages of the page instructions and every universe title that leads to one of them: the prompt_example flag of
    pages.parquet (05_chunks.py) when it exists, else the final titles of page_text.parquet."""
    ex = set(PROMPT_EXAMPLES)
    fp = P / 'pages.parquet'
    if fp.exists():
        Pg = pd.read_parquet(fp, columns=['title', 'prompt_example'])
        return ex | set(Pg[Pg.prompt_example.astype(bool)].title)
    f = P / 'page_text.parquet'
    if f.exists():
        T = pd.read_parquet(f, columns=['title', 'final_title'])
        fin = {t.replace(' ', '_') for t in ex} | {t.replace('_', ' ') for t in ex}
        ex |= set(T[T.final_title.isin(fin)].title)
    return ex


# ---------------------------------------------------------------- assignments
def read_assign(P, kind):
    f = P / f'assign_{kind}.parquet'
    if not f.exists():
        raise SystemExit(f'{f} not found: run 20_parse_outputs.py first')
    return pd.read_parquet(f)


def s2_selection(A, topdays):
    """Pages of S2 (addendum): universe pages with at least one assignment of confidence 2 or 3; if more than 40,000, the 40,000 with
    the most top-500 days. NOT IN ADDENDUM: ties at the cut are broken by total views in the top-500 lists (more first), then by title.
    A: assign_pages (title, set, conf); topdays: title, top_days, top_views. Returns title, top_days, top_views, rank, selected."""
    t = A[(A.set == 'universe') & (A.conf >= S2_MIN_CONF)].title.drop_duplicates()
    S = topdays[topdays.title.isin(set(t))].sort_values(['top_days', 'top_views', 'title'], ascending=[False, False, True]).reset_index(drop=True)
    S['rank'] = np.arange(1, len(S) + 1)
    S['selected'] = S['rank'] <= S2_MAX_PAGES
    return S


# ---------------------------------------------------------------- the S2 daily-view store (written by 22, read by 21 and 24)
def store_index(P):
    """title -> (batch file, row, status) for every page in the S2 store."""
    rows = []
    for f in sorted(P.views.glob('batch_*.npz')):
        with np.load(f, allow_pickle=False) as z:
            for i, (t, st) in enumerate(zip(z['titles'], z['status'])):
                rows.append((str(t), f.name, i, int(st)))
    I = pd.DataFrame(rows, columns=['title', 'file', 'row', 'status'])
    return I.drop_duplicates('title', keep='last').reset_index(drop=True)


def store_matrix(P, titles):
    """Daily user views (all access) of the given titles, int32 array (len(titles) x days of 2015-07-01..2026-09-30), and the status
    of each (200 page found, 404 no page, -1 not in the store: all zero)."""
    idx = store_index(P).set_index('title')
    out = np.zeros((len(titles), len(DAYS)), dtype=np.int32)
    status = np.full(len(titles), -1, dtype=np.int32)
    pos = {t: i for i, t in enumerate(titles)}
    have = idx[idx.index.isin(pos)]
    for f, g in have.groupby('file'):
        with np.load(P.views / f, allow_pickle=False) as z:
            V = z['views']
            for t, r, st in zip(g.index, g.row, g.status):
                out[pos[t]] = V[r]
                status[pos[t]] = st
    return out, status


# ---------------------------------------------------------------- mock worlds: outcome shuffling
def shuffle_panel(panel, seed):
    """Mock worlds only. Within each (level, format), the borrowing of every usable category-month (weighted checkouts, share and log
    share together) is moved to a random other usable category-month, so themes and months are scrambled and no real effect remains.
    The structure (months, sizes, the minimum-size rule) is kept."""
    p = panel.copy()
    for (lv, fmt), idx in p.groupby(['level', 'format']).groups.items():
        rng = np.random.default_rng([int(seed), zlib.crc32(f'{lv}|{fmt}'.encode())])     # one stream per group: same shuffle whatever else is loaded
        sub = p.loc[idx]
        ok = sub.index[sub.month_ok.astype(bool) & np.isfinite(sub.log_share.to_numpy(dtype=float))]
        perm = rng.permutation(len(ok))
        for c in ('weighted_checkouts', 'share', 'log_share'):
            if c in p.columns:
                p.loc[ok, c] = p.loc[ok, c].to_numpy()[perm]
    return p


def shuffle_history(hist, seed):
    """Mock worlds only. hist: {(group, format, level, node_id): Series of log share by month}. Within each (group, format, level) every
    observed value is moved to a random (series, month) cell of the same pool."""
    rng = np.random.default_rng(seed)
    pools = {}
    for k, s in hist.items():
        pools.setdefault(k[:3], []).append(k)
    out = {}
    for pk, keys in sorted(pools.items()):
        keys = sorted(keys)
        vals = np.concatenate([hist[k].to_numpy(dtype=float) for k in keys])
        perm = rng.permutation(len(vals))
        vals = vals[perm]
        i = 0
        for k in keys:
            n = len(hist[k])
            out[k] = pd.Series(vals[i:i + n], index=hist[k].index)
            i += n
    return out


# ---------------------------------------------------------------- jobs
DOWNLOAD_WORDS = ('wiki', 'view', 'text', 'download')       # 'wiki' is the rule asked for; the others catch testF_text (the Action API download)


def running_wiki_jobs(exclude_names=()):
    """Names of jobs shown as RUNNING by jobs/status.sh whose name contains 'wiki' (or 'view', 'text', 'download', so that the Test F
    page-text download, job testF_text, also counts), except this process (its pid or its parent's, as jobs/bg.sh records the caffeinate
    wrapper) and the names given."""
    try:
        out = subprocess.run(['bash', str(ROOT / 'jobs' / 'status.sh'), '0'], capture_output=True, text=True, timeout=60).stdout
    except Exception as e:
        raise SystemExit(f'could not run jobs/status.sh ({e}); refusing to download')
    me = {os.getpid(), os.getppid()}
    busy = []
    for line in out.splitlines():
        m = re.match(r'^\[(.+?)\] RUNNING pid (\d+)', line.strip())
        if not m:
            continue
        name, pid = m.group(1), int(m.group(2))
        if any(w in name.lower() for w in DOWNLOAD_WORDS) and pid not in me and name not in exclude_names:
            busy.append(f'{name} (pid {pid})')
    return busy


def write_json(obj, path):
    path = pathlib.Path(path)
    tmp = path.with_suffix(path.suffix + '.part')
    tmp.write_text(json.dumps(obj, indent=1, default=lambda x: x.item() if hasattr(x, 'item') else str(x)))
    os.replace(tmp, path)


def write_parquet(df, path):
    path = pathlib.Path(path)
    tmp = path.with_suffix(path.suffix + '.part')
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)


def write_text(text, path):
    path = pathlib.Path(path)
    tmp = path.with_suffix(path.suffix + '.part')
    tmp.write_text(text)
    os.replace(tmp, path)


def md_table(df, floatfmt='{:.3f}'):
    cols = list(df.columns)
    out = ['| ' + ' | '.join(map(str, cols)) + ' |', '|' + ' --- |' * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append('' if v != v else floatfmt.format(v))
            else:
                cells.append(str(v))
        out.append('| ' + ' | '.join(cells) + ' |')
    return out
