# Glue between the count panels and the methods: the world of a run (counts per kind and level, categories, shift screens),
# the cached z tables (one per kind, level and month 0: the quasi-Poisson fit of every category), one full test of a
# category at a month 0 (joint model, per-format effects, placebo-category rank, placebo years), power draws by injected lifts.
# kind: 'seattle' (the formats modelled jointly) or 'librivox' (its own exposure, a one-format model).
# Used by 10 to 14 and the tests. Worker processes load their own World (see run_tasks); nothing big is pickled.
import os, json, time
import numpy as np, pandas as pd
import _s3
import _methods as M
import _panel as PN
from _settings import SETTINGS as S0

B3, INT3 = _s3.build, _s3.interest
ZFIELDS = ('z_p', 'z_s', 'summu_p', 'sumy_p', 'phi', 'nm_p')


# ---------------- shifts ----------------
def load_shifts(P, S, need=True):
    """All interest shifts of the tested levels in one table: Study 3's shifts.parquet (narrow and middle) and the value-level
    table of step 02 (level 'value'), both through the Study 3 adapter (checks Mondays, classes, thresholds; adds m0, labelled,
    quality_ok). Returns None when a file is missing and need is False."""
    f3, fv = P.interest / INT3.SHIFTS_FILE, P.shifts_value
    for f in (f3, fv):
        if not f.exists():
            if need:
                raise SystemExit(f'{f} does not exist (interest side or step 02 not finished)')
            return None
    X3 = INT3.normalise_shifts(pd.read_parquet(f3), S)
    X3 = X3[X3.level.isin(['narrow', 'middle'])]
    V = pd.read_parquet(fv)
    Xv = INT3.normalise_shifts(V.assign(level=3), S)           # the Study 3 adapter knows levels 1 to 3 only
    Xv['level'] = 'value'
    Xv['shift_id'] = 'value:' + Xv.shift_id
    X = pd.concat([X3, Xv], ignore_index=True)
    if (X.source == 'gdelt').any() and S.gdelt_durations is None:
        raise SystemExit('refuses to run: no addendum carries the GDELT durations (record: appended before any demand data are read)')
    return X


# ---------------- the world of a run ----------------
class LazyDict(dict):
    """A dict whose values are made on first access; membership and iteration work on the declared keys without loading."""

    def __init__(self, make, keys):
        super().__init__()
        self._make, self._keys = make, list(keys)

    def __missing__(self, k):
        if k not in self._keys:
            raise KeyError(k)
        self[k] = self._make(k)
        return self[k]

    def __contains__(self, k):
        return k in self._keys

    def __iter__(self):
        return iter(self._keys)

    def keys(self):
        return list(self._keys)


class World:
    """Counts per (kind, level), categories, and shift screens. Built from the files of a run (Paths P)."""

    def __init__(self, P, S, shifts):
        self.P, self.S = P, S
        cats = pd.read_parquet(P.categories)
        self.cats = {lv: cats[cats.level == lv].set_index('node_id') for lv in S.levels_tested}
        self._status = pd.read_parquet(P.months)
        self._ll = pd.read_parquet(P.counts_librivox) if P.counts_librivox.exists() else None
        keys = [('seattle', lv) for lv in S.levels_tested]
        if self._ll is not None:
            keys += [('librivox', lv) for lv in S.levels_tested if (self._ll.level == lv).any()]
        self.C = LazyDict(self._load_counts, keys)           # a level is loaded when first used (8 GB machine, 3 workers)
        self.parent_arr = LazyDict(lambda k: self.cats[k[1]].parent.reindex(self.C[k].ids).to_numpy(), keys)
        self.shift_m0 = {}
        self.has_shifts = shifts is not None
        if shifts is not None:
            for (lv, n), g in shifts.groupby(['level', 'node_id']):
                self.shift_m0[(lv, n)] = np.sort(g.m0.to_numpy())
        # values with an interest series (Wikipedia or GDELT): only for these is 'no shift start' known. The record's placebos are all
        # categories without a detected shift; p_cat_p_screened (value level) ranks among the placebo values that have a series.
        self.interest_ids = {lv: None for lv in S.levels_tested}
        vals = set()
        for f in (P.interest / 'wiki' / 'weekly_value.parquet', P.interest / 'gdelt' / 'weekly_value.parquet'):
            if f.exists():
                vals |= set(pd.read_parquet(f, columns=['value']).value.unique())
        if vals:
            self.interest_ids['value'] = vals
        self.build_id = json.loads(P.meta.read_text())['build_id']
        self.zdir = P.db / 'ztables'

    def _load_counts(self, key):
        kind, lv = key
        S, P = self.S, self.P
        if kind == 'seattle':
            long = pd.read_parquet(P.counts, filters=[('level', '==', lv)])
            return PN.make_counts(long, self._status, lv, sorted(self.cats[lv].index), list(S.seattle_formats))
        sub = self._ll[self._ll.level == lv]
        return PN.make_counts(sub, self._status, lv, sorted(set(sub.node_id)), ['librivox'])

    def last_month(self, kind, level):
        C = self.C[(kind, level)]
        return int(C.mi0 + C.T - 1)

    # ---- screens ----
    def near_mask(self, kind, level, m0, win=None):
        """Boolean over the categories of (kind, level): any shift start (any source, any class, seasonal and flagged
        included; NOT IN RECORD: the Study 3 reading of 'interest shift') in months win around m0."""
        win = win or self.S.placebo_cat_no_shift
        C = self.C[(kind, level)]
        out = np.zeros(len(C.ids), bool)
        for (lv, n), arr in self.shift_m0.items():
            if lv != level:
                continue
            i = C.index.get(n)
            if i is not None and np.any((arr >= m0 + win[0]) & (arr <= m0 + win[1])):
                out[i] = True
        return out

    def shifted_near(self, level, node, m0, win):
        arr = self.shift_m0.get((level, node))
        return arr is not None and bool(np.any((arr >= m0 + win[0]) & (arr <= m0 + win[1])))

    # ---- z tables ----
    def ztable(self, kind, level, m0, save=True):
        """Compact fit results of every category at month 0 = m0 (cached on disk; the file records the panel build)."""
        f = self.zdir / f'{kind}_{level}_{m0}.npz'
        if f.exists():
            try:
                z = np.load(f, allow_pickle=False)
                if str(z['build_id']) == self.build_id and str(z['settings']) == self.S.sha256:
                    return {k: z[k] for k in ('feasible',) + ZFIELDS}
            except Exception:
                pass
        es = M.event_study(self.C[(kind, level)], m0, self.S)
        tab = {'feasible': es['feasible'] & ~np.isnan(es['z_p'])}
        for k in ZFIELDS:
            tab[k] = es[k].astype(np.float32)
        if save:
            self.zdir.mkdir(parents=True, exist_ok=True)
            tmp = str(f) + '.tmp.npz'
            np.savez(tmp, build_id=self.build_id, settings=self.S.sha256, **tab)
            os.replace(tmp, f)
        return tab

    def placebo_mask(self, kind, level, m0, node, tab, screened=False):
        """Placebo categories of a test (record): same level, feasible, no shift start in months -6..+6, not sharing the
        parent of the treated category, not the category itself. NOT IN RECORD: too-sparse categories stay in the pool; at the value
        level values without an interest series count as shift-free (screened=True keeps only values with a series)."""
        C = self.C[(kind, level)]
        i = C.index[node]
        par = self.parent_arr[(kind, level)]
        m = tab['feasible'].copy()
        m[i] = False
        if par[i] is not None and not (isinstance(par[i], float) and np.isnan(par[i])):
            m &= (par != par[i])
        m &= ~self.near_mask(kind, level, m0)
        if screened and self.interest_ids.get(level) is not None:
            m &= np.isin(C.ids, list(self.interest_ids[level]))
        return m


# ---------------- one test ----------------
FIELDS_WIN = ('sumy', 'summu', 'tau', 'z')


def _flat(es, C, S):
    """One category's event-study result (arrays of length 1) as a flat record."""
    r = dict(feasible=bool(es['feasible'][0]), n_formats=int(es['n_formats'][0]),
             formats=','.join(f for j, f in enumerate(C.formats) if int(es['formats'][0]) >> j & 1),
             phi=float(es['phi'][0]), df=float(es['df'][0]), converged=bool(es['converged'][0]))
    for w in ('pre', 'p', 's'):
        for k in FIELDS_WIN:
            r[f'{k}_{w}'] = float(es[f'{k}_{w}'][0])
        r[f'nm_{w}'] = int(es[f'nm_{w}'][0])
        for f in C.formats:
            for k in FIELDS_WIN:
                r[f'{k}_{w}_{f}'] = float(es[f'{k}_{w}_{f}'][0])
    return r


def test_unit(world, kind, level, node, m0, tab=None, placebo_years_on=True):
    """Full test of one category at month 0 = m0: joint model (or one format for LibriVox), per-format effects,
    placebo-category rank p on z (primary and secondary windows), and the share of placebo years with z at or above."""
    S = world.S
    C = world.C[(kind, level)]
    rec = dict(kind=kind, level=level, node_id=node, m0=int(m0), month0=B3.ym_of(m0), label=world.cats[level].label.get(node),
               broad_id=world.cats[level].broad_id.get(node), parent=world.cats[level].parent.get(node))
    i = C.index.get(node)
    if i is None:
        rec['skip'] = 'no counts'
        return rec
    es = M.event_study(C, m0, S, rows=[i])
    rec.update(_flat(es, C, S))
    if not rec['feasible']:
        rec['skip'] = 'not feasible'
        return rec
    if np.isnan(rec['z_p']):
        rec['skip'] = 'window too short'
        return rec
    rec['skip'] = ''
    rec['too_sparse'] = bool(rec['summu_p'] < S.sparse_below)
    rec['y_zero'] = bool(rec['sumy_p'] == 0)
    if tab is None:
        tab = world.ztable(kind, level, m0)
    pm = world.placebo_mask(kind, level, m0, node, tab)
    rec['n_placebos'] = int(pm.sum())
    rec['p_cat_p'] = M.rank_p(rec['z_p'], tab['z_p'][pm])
    rec['p_cat_s'] = M.rank_p(rec['z_s'], tab['z_s'][pm]) if not np.isnan(rec['z_s']) else np.nan
    rec['p_min'] = 1.0 / (rec['n_placebos'] + 1)
    if level == 'value' and world.interest_ids.get('value') is not None:
        ps = world.placebo_mask(kind, level, m0, node, tab, screened=True)
        rec['n_placebos_screened'] = int(ps.sum())
        rec['p_cat_p_screened'] = M.rank_p(rec['z_p'], tab['z_p'][ps])
    if placebo_years_on:
        rec.update(getattr(world, 'placebo_years_fn', None) and world.placebo_years_fn(world, kind, level, node, m0, rec['z_p'])
                   or placebo_years(world, kind, level, node, m0, rec['z_p']))   # backlist run (15) swaps in its own placebo years
    return rec


def placebo_years(world, kind, level, node, m0, real_z):
    """Same category and calendar months in every other year from the record's first placebo year that has a full primary
    window and a fit window, a feasible fit, and no shift of the category in months -6..+6 around the placebo month 0.
    Returns the share of placebo z at or above the treated z (record) and the number of placebo years.
    NOT IN RECORD: the 'no shift' window is -6..+6, the placebo fit must be feasible with a full primary window, primary window only."""
    S = world.S
    C = world.C[(kind, level)]
    i = C.index[node]
    y0, cal = divmod(m0, 12)
    last = world.last_month(kind, level)
    zs, years = [], []
    for yr in range(S.placebo_year_from, last // 12 + 1):
        m = yr * 12 + cal
        if yr == y0 or m + S.window_primary[1] > last or m + (S.es_fit_end - S.es_fit_len + 1) < C.mi0:
            continue
        if world.has_shifts and world.shifted_near(level, node, m, S.placebo_cat_no_shift):
            continue
        es = M.event_study(C, m, S, rows=[i])
        if es['feasible'][0] and not np.isnan(es['z_p'][0]):
            zs.append(float(es['z_p'][0])); years.append(yr)
    share, n = M.share_at_least(zs, real_z)
    return dict(py_years=json.dumps(years), py_share_ge=share, py_n=n)


# ---------------- power ----------------
def power_candidates(world, kind, level, lo, hi, tabs):
    """(category index, m0, sum mu) of every placebo unit: month 0 in lo..hi with a feasible fit and a primary window
    (sum mu defined), and no shift of the category in months -6..+6."""
    ids, ms, sm = [], [], []
    for m0 in range(lo, hi + 1):
        t = tabs.get(m0)
        if t is None:
            continue
        ok = t['feasible'] & ~np.isnan(t['summu_p']) & ~world.near_mask(kind, level, m0)
        k = np.flatnonzero(ok)
        ids.append(k); ms.append(np.full(len(k), m0)); sm.append(t['summu_p'][k].astype(float))
    if not ids:
        return np.zeros(0, int), np.zeros(0, int), np.zeros(0)
    return np.concatenate(ids), np.concatenate(ms), np.concatenate(sm)


def power_draws(world, kind, level, draws, tabs, lifts):
    """Detection of each injected lift for each drawn (category index, m0): the lifted z is ranked among the other placebo
    categories of that month (same exclusions as a real test). Returns a DataFrame with one row per draw and lift."""
    S = world.S
    C = world.C[(kind, level)]
    rows = []
    for (i, m0, band) in draws:
        t = tabs[m0]
        node = C.ids[i]
        pm = world.placebo_mask(kind, level, m0, node, t)
        zp = t['z_p'][pm].astype(float)
        for lift in lifts:
            zl = M.lifted_z(float(t['z_p'][i]), float(t['summu_p'][i]), float(t['phi'][i]), float(t['sumy_p'][i]), lift)
            rows.append(dict(level=level, kind=kind, node_id=node, m0=int(m0), band=int(band), lift=lift,
                             summu_p=float(t['summu_p'][i]), n_placebos=int(pm.sum()), p=M.rank_p(float(zl), zp)))
    return pd.DataFrame(rows)


# ---------------- parallel runs ----------------
_WORLD = {}


def _get_world(spec):
    """Each worker process builds its own World once (nothing big is pickled)."""
    key = json.dumps(spec, sort_keys=True)
    if key not in _WORLD:
        import _paths as IO
        from _settings import SETTINGS as S
        P = IO.Paths(spec.get('sim'))
        shifts = load_shifts(P, S, need=False)
        _WORLD.clear()
        _WORLD[key] = World(P, S, shifts)
    return _WORLD[key]


def _task(spec, kind, what, level, m0, nodes):
    w = _get_world(spec)
    if what == 'z':
        w.ztable(kind, level, m0)
        return (kind, level, m0, None)
    tab = w.ztable(kind, level, m0)
    return (kind, level, m0, [test_unit(w, kind, level, n, m0, tab) for n in nodes])


def run_tasks(spec, tasks, workers):
    """tasks: (kind, what, level, m0, nodes) tuples; what is 'z' (fill the z-table cache) or 'unit' (test the nodes).
    Results come back in task order. Workers load their own World; with one worker everything runs in this process."""
    tasks = list(tasks)
    if workers <= 1 or len(tasks) < 2:
        return [_task(spec, *t) for t in tasks]
    from joblib import Parallel, delayed
    return Parallel(n_jobs=workers)(delayed(_task)(spec, *t) for t in tasks)
