"""Study 2R outcome side: shared helpers (counts, z tables, one test per work and shift, placebo works, placebo years,
pooled statistics, bootstrap tools). The outcome model is the Study 3b count event study, imported unchanged from
code/main_study/study3b/_methods.py (quasi-Poisson, 24 fit months ending at month -7, tau and z over months 0 to +2 and 0 to +5).
Settings: prereg/study2r_settings_2026-10-14.json (its SHA-256 is checked against prereg/README.md) with addenda_2r/; the
numeric values of the model (windows, 2,000 resamples, seed 20261013, BH 0.10) are those of the Study 3b settings parsed by its loader.
Choices the record does not make are marked '# NOT IN RECORD:' and listed in prereg/DEVIATIONS.md (Study 2R section).
Run from handoff/code with:  bash ../jobs/heavy_lock.sh nice -n 10 ../.venv/bin/python study2r/NAME.py
"""
import sys, os, re, json, time, hashlib, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / 'main_study' / 'study3b'))
sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
import _methods as M                       # Study 3b
import _panel as PN                        # Study 3b (make_counts)
from _settings import SETTINGS as S        # Study 3b settings (hash checked)

D = ROOT / 'data'
OUT = D / 'db' / 'study2r'
REP = D / 'reports'
TAXO = D / 'db' / 'taxonomy_v3'
ZDIR = OUT / 'ztables'
PREREG = ROOT / 'prereg'
RECORD = PREREG / 'study2r_settings_2026-10-14.json'
ADDENDA = sorted((PREREG / 'addenda_2r').glob('*.json'))
SEED = 20261013
N_BOOT = 2000
N_PLACEBO = 200
BH_Q = 0.10
ALPHA = 0.05
FEAS_WORKS = 299                           # addendum b: works needed for the upper bound to fall below log(1.10) under zero effect
LOG110 = float(np.log(1.10))
STUDY_START = 2017 * 12                    # month index of 2017-01 (Study 3 record; also S.study_start)
for p in (OUT, ZDIR, REP):
    p.mkdir(parents=True, exist_ok=True)


def check_record():
    """The 2R record must match its SHA-256 line in prereg/README.md; the Study 3b numbers used must equal the 2R record's."""
    text = (PREREG / 'README.md').read_text()
    i = text.find('## Study 2R')
    m = re.search(r'SHA-256:\s*`([0-9a-f]{64})`', text[i:].split('\n## ', 1)[0])
    got = hashlib.sha256(RECORD.read_bytes()).hexdigest()
    if not m or m.group(1) != got:
        raise SystemExit('the Study 2R record does not match its SHA-256 in prereg/README.md; nothing runs')
    rec = json.loads(RECORD.read_text())
    assert S.boot_n == N_BOOT and S.boot_seed == SEED and abs(S.bh_q - BH_Q) < 1e-12 and S.window_primary == (0, 2) and S.window_secondary == (0, 5)
    assert S.es_fit_len == 24 and S.es_fit_end == -7
    return rec


REC = check_record()


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def mi_of(ts):
    d = pd.to_datetime(pd.Series(ts))
    return (d.dt.year * 12 + d.dt.month - 1).astype(np.int64).to_numpy()


def ym(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


# ---------------- counts ----------------
def load_counts(formats, works=None):
    """Counts (study3b class) with one 'category' per Seattle work: Y = monthly checkouts of the work in each format, exposure N = all
    checkouts of the format that month, closure/partial/missing months NaN (month_status of Study 3b)."""
    long = pd.read_parquet(OUT / 'counts_work.parquet')
    long = long[long.format.isin(formats)]
    ids = np.sort(long.work_id.unique() if works is None else np.asarray(works))
    st = pd.read_parquet(D / 'db' / 'study3b' / 'month_status.parquet')
    lg = long.rename(columns={'work_id': 'node_id'}).assign(level='work')
    return PN.make_counts(lg, st, 'work', ids, list(formats))


# ---------------- z tables ----------------
BASE = ['phi', 'sumy_p', 'summu_p', 'tau_p', 'z_p', 'nm_p', 'sumy_s', 'summu_s', 'tau_s', 'z_s', 'nm_s']


def fields_of(formats):
    return BASE + [f'{k}_p_{f}' for f in formats for k in ('tau', 'z', 'sumy', 'summu')]


def z_one(C, m0):
    """Fit of every work at month 0 = m0: the compact table used for treated results and for placebo works and placebo years."""
    es = M.event_study(C, m0, S)
    tab = {'feasible': es['feasible'] & ~np.isnan(es['z_p'])}
    for k in fields_of(C.formats):
        tab[k] = es[k].astype(np.float32)
    # primary format of the work: the format with more checkouts in the 24 fit months (print or ebook; audiobook alone is its own)
    fi = M.fit_months(m0, S) - C.mi0
    ok = (fi >= 0) & (fi < C.T)
    tot = np.zeros((len(C.ids), len(C.formats)))
    for j, f in enumerate(C.formats):
        tot[:, j] = np.nansum(C.Y[f][:, fi[ok]], axis=1)
    tab['pf'] = tot.argmax(1).astype(np.int8)
    return tab


def _z_chunk(C, months):
    return [(m, z_one(C, m)) for m in months]


def build_ztables(C, name, months, workers=2):
    """z tables of months m0 in `months`, cached in data/db/study2r/ztables/<name>_<m0>.npz. Returns {m0: table}."""
    tabs, todo = {}, []
    for m in months:
        f = ZDIR / f'{name}_{m}.npz'
        if f.exists():
            z = np.load(f, allow_pickle=False)
            tabs[m] = {k: z[k] for k in z.files}
        else:
            todo.append(m)
    if todo:
        if workers > 1 and len(todo) > 6:
            from joblib import Parallel, delayed
            chunks = [todo[i::workers] for i in range(workers)]
            res = Parallel(n_jobs=workers)(delayed(_z_chunk)(C, c) for c in chunks)
            res = [x for r in res for x in r]
        else:
            res = _z_chunk(C, todo)
        for m, t in res:
            tabs[m] = t
            if name:
                np.savez(ZDIR / f'{name}_{m}.npz', **t)
    return tabs


def month_range(C, lo=STUDY_START):
    """Months m0 with at least 2 months of the primary window... in the data: lo .. last month - 1."""
    return list(range(max(lo, C.mi0 + 31), C.mi0 + C.T - 1))


# ---------------- shift screens ----------------
def screen_matrix(C, shifts_by_work):
    """(works, months) bool: a shift (any class, any quality flag) starts in that month, on the work's own article(s)."""
    X = np.zeros((len(C.ids), C.T), bool)
    for w, arr in shifts_by_work.items():
        i = C.index.get(w)
        if i is None:
            continue
        a = np.asarray(arr) - C.mi0
        a = a[(a >= 0) & (a < C.T)]
        X[i, a] = True
    return X


def near(X, C, m0, win=S.placebo_cat_no_shift):
    """Per work: any shift start in months m0+win[0] .. m0+win[1]."""
    a, b = m0 + win[0] - C.mi0, m0 + win[1] - C.mi0 + 1
    a, b = max(a, 0), min(b, C.T)
    return X[:, a:b].any(1) if b > a else np.zeros(len(C.ids), bool)


def near_one(row, C, m0, win=S.placebo_cat_no_shift):
    a, b = max(m0 + win[0] - C.mi0, 0), min(m0 + win[1] - C.mi0 + 1, C.T)
    return bool(row[a:b].any()) if b > a else False


def deciles(x):
    edges = np.quantile(x, np.linspace(0, 1, 11))
    return edges[1:-1]


# ---------------- tests ----------------
OUTCOLS = ['feasible', 'phi', 'sumy_p', 'summu_p', 'tau_p', 'z_p', 'nm_p', 'sumy_s', 'summu_s', 'tau_s', 'z_s', 'nm_s', 'pf']


def run_tests(C, tabs, tests, pool, art_code, X, n_placebo=N_PLACEBO, seed=SEED, with_years=True):
    """One test per row of `tests` (columns work_id, m0, any others are carried). Per test: tau and z over months 0..+2 (p) and
    0..+5 (s) from the joint model, one-sided placebo-work rank p (200 works drawn at random from `pool`: feasible at m0, same
    primary format, expected count over the primary window in the same decile (deciles of the pool's feasible works at m0), no shift
    start on their own article in months -6..+6 [screen matrix X], not the same work or article), and placebo years.
    pool: bool over C.ids; art_code: int per work (same article = same code); X: screen matrix."""
    rows = []
    last = C.mi0 + C.T - 1
    fmts = C.formats
    cache = {}
    for r in tests.itertuples(index=False):
        rec = r._asdict()
        w, m0 = int(r.work_id), int(r.m0)
        i = C.index.get(w)
        rec.update(skip='', n_placebos=0, plc_tau_median=np.nan, plc_tau_mean=np.nan, p_p=np.nan, p_s=np.nan, py_n=0, py_share_ge=np.nan, too_sparse=False, y_zero=False)
        if i is None or m0 not in tabs:
            rec['skip'] = 'no counts'; rows.append(rec); continue
        t = tabs[m0]
        for k in OUTCOLS:
            rec[k] = t[k][i] if k in t else np.nan
        for f in fmts:
            for k in ('tau', 'z', 'sumy', 'summu'):
                rec[f'{k}_p_{f}'] = t[f'{k}_p_{f}'][i]
        if not t['feasible'][i]:
            rec['skip'] = 'not feasible'; rows.append(rec); continue
        rec['too_sparse'] = bool(rec['summu_p'] < S.sparse_below)
        rec['y_zero'] = bool(rec['sumy_p'] == 0)
        if m0 not in cache:
            edges = deciles(t['summu_p'][pool & t['feasible']].astype(float))
            cache[m0] = (pool & t['feasible'] & ~near(X, C, m0), np.searchsorted(edges, np.nan_to_num(t['summu_p'].astype(float)), side='right'))
        ok0, dec = cache[m0]
        ok = ok0.copy()
        ok[i] = False
        ok &= art_code != art_code[i]
        cand = np.flatnonzero(ok & (t['pf'] == t['pf'][i]) & (dec == dec[i]))
        rng = np.random.default_rng([seed, w, m0])
        pick = cand if len(cand) <= n_placebo else rng.choice(cand, n_placebo, replace=False)
        rec['n_placebos'] = int(len(pick))
        pt = t['tau_p'][pick].astype(float); pt = pt[np.isfinite(pt)]
        if len(pt):                       # diagnostic only (not in the record): what the matched placebo works did in the same months
            rec['plc_tau_median'], rec['plc_tau_mean'] = float(np.median(pt)), float(pt.mean())
        if len(pick):
            rec['p_p'] = M.rank_p(float(t['z_p'][i]), t['z_p'][pick].astype(float))
            rec['p_s'] = M.rank_p(float(t['z_s'][i]), t['z_s'][pick].astype(float)) if not np.isnan(t['z_s'][i]) else np.nan
        if with_years:
            zs = []
            y0, cal = divmod(m0, 12)
            for yr in range(S.placebo_year_from, last // 12 + 1):
                m = yr * 12 + cal
                if yr == y0 or m not in tabs or m + S.window_primary[1] > last:
                    continue
                if near_one(X[i], C, m):
                    continue
                tt = tabs[m]
                if tt['feasible'][i]:
                    zs.append(float(tt['z_p'][i]))
            share, n = M.share_at_least(zs, float(rec['z_p']))
            rec['py_n'], rec['py_share_ge'] = n, share
        rows.append(rec)
    R = pd.DataFrame(rows)
    return R


# ---------------- bootstrap tools ----------------
def cluster_stats_ols(X, y, cl):
    """Per-cluster X'X (p,p) and X'y (p,) for a clustered bootstrap of OLS; returns (G,p,p), (G,p), n per cluster."""
    codes, uniq = pd.factorize(cl, sort=True)
    G, p = len(uniq), X.shape[1]
    xtx = np.zeros((G, p, p)); xty = np.zeros((G, p)); n = np.bincount(codes, minlength=G).astype(float)
    for a in range(p):
        xty[:, a] = np.bincount(codes, weights=X[:, a] * y, minlength=G)
        for b in range(p):
            xtx[:, a, b] = np.bincount(codes, weights=X[:, a] * X[:, b], minlength=G)
    return xtx, xty, n


def boot_ols(X, y, cl, n_boot=N_BOOT, seed=SEED, chunk=250):
    """OLS coefficients with a bootstrap that resamples whole clusters. Returns (estimate (p,), boot (n_boot,p)). A resample whose
    X'X is singular gives NaN."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    xtx, xty, n = cluster_stats_ols(X, y, np.asarray(cl))
    G, p = xty.shape
    est = np.linalg.lstsq(xtx.sum(0), xty.sum(0), rcond=None)[0]
    rng = np.random.default_rng(seed)
    B = np.full((n_boot, p), np.nan)
    for a in range(0, n_boot, chunk):
        k = min(chunk, n_boot - a)
        pick = rng.integers(0, G, size=(k, G))
        A = xtx[pick].sum(1); b = xty[pick].sum(1)
        for j in range(k):
            try:
                B[a + j] = np.linalg.solve(A[j], b[j])
            except np.linalg.LinAlgError:
                pass
    return est, B


def pct(b, lo=2.5, hi=97.5):
    b = np.asarray(b, float); b = b[np.isfinite(b)]
    return (float(np.percentile(b, lo)), float(np.percentile(b, hi))) if len(b) else (np.nan, np.nan)


def boot_diff(y, grp_hi, grp_lo, cl, n_boot=N_BOOT, seed=SEED, chunk=250):
    """Mean of y in grp_hi minus mean in grp_lo (boolean arrays), cluster bootstrap. Returns est, boot array."""
    y = np.asarray(y, float)
    codes, uniq = pd.factorize(np.asarray(cl), sort=True)
    G = len(uniq)
    st = []
    for g in (grp_hi, grp_lo):
        g = np.asarray(g, bool)
        st += [np.bincount(codes, weights=y * g, minlength=G), np.bincount(codes, weights=g.astype(float), minlength=G)]
    sh, nh, sl, nl = st
    est = sh.sum() / nh.sum() - sl.sum() / nl.sum()
    rng = np.random.default_rng(seed)
    B = np.empty(n_boot)
    for a in range(0, n_boot, chunk):
        k = min(chunk, n_boot - a)
        pick = rng.integers(0, G, size=(k, G))
        with np.errstate(invalid='ignore', divide='ignore'):
            B[a:a + k] = sh[pick].sum(1) / nh[pick].sum(1) - sl[pick].sum(1) / nl[pick].sum(1)
    return float(est), B


# ---------------- Hansen (2000) threshold regression of tau on duration ----------------
CANDS = tuple(range(2, 11))


def _thr_stats(dur, y, cl, cands):
    """Per cluster and candidate g: n, sum, sum of squares of y for duration <= g (low) and > g (high)."""
    codes, uniq = pd.factorize(np.asarray(cl), sort=True)
    G = len(uniq)
    out = np.zeros((G, len(cands), 6))
    for j, g in enumerate(cands):
        lo = dur <= g
        for s, (m, v) in enumerate(((lo, 1.0), (~lo, 1.0))):
            out[:, j, 3 * s + 0] = np.bincount(codes, weights=m * 1.0, minlength=G)
            out[:, j, 3 * s + 1] = np.bincount(codes, weights=m * y, minlength=G)
            out[:, j, 3 * s + 2] = np.bincount(codes, weights=m * y * y, minlength=G)
    return out


def _ssr(T, min_n):
    """T (..., cands, 6) summed stats -> SSR per candidate (inf where a regime has fewer than min_n tests)."""
    n1, s1, q1, n2, s2, q2 = (T[..., i] for i in range(6))
    with np.errstate(invalid='ignore', divide='ignore'):
        ssr = (q1 - s1 ** 2 / n1) + (q2 - s2 ** 2 / n2)
    return np.where((n1 >= min_n) & (n2 >= min_n), ssr, np.inf)


def hansen(dur, y, cl, cands=CANDS, n_boot=N_BOOT, seed=SEED, chunk=250):
    """Threshold (mean-shift) regression: tau = a1 for duration <= gamma, a2 above; gamma over integer weeks `cands`, chosen by least
    squares; each regime needs at least max(20, 5% of the tests) (Hansen's trimming; NOT IN RECORD). Bootstrap clustered by work:
    gamma is re-estimated in every resample; interval = 2.5 and 97.5 percentiles of gamma-hat. Also the likelihood-ratio confidence
    set of Hansen (2000) with the homoskedastic LR (critical value 7.35 at 95%)."""
    dur, y = np.asarray(dur, float), np.asarray(y, float)
    cands = tuple(cands)
    st = _thr_stats(dur, y, np.asarray(cl), cands)
    min_n = max(20, int(0.05 * len(y)))
    T = st.sum(0)
    ssr = _ssr(T, min_n)
    j = int(np.argmin(ssr)) if np.isfinite(ssr).any() else None
    if j is None:
        return dict(gamma=np.nan)
    sse0 = float(((y - y.mean()) ** 2).sum())
    lr = len(y) * (ssr - ssr[j]) / ssr[j]
    conf = [int(c) for c, v in zip(cands, lr) if np.isfinite(v) and v <= 7.35]
    G = len(st)
    rng = np.random.default_rng(seed)
    gam = np.full(n_boot, np.nan); dif = np.full(n_boot, np.nan)
    for a in range(0, n_boot, chunk):
        k = min(chunk, n_boot - a)
        pick = rng.integers(0, G, size=(k, G))
        Tb = st[pick].sum(1)                                  # (k, cands, 6)
        ss = _ssr(Tb, max(20, int(0.05 * len(y))))
        okr = np.isfinite(ss).any(1)
        jj = np.argmin(np.where(np.isfinite(ss), ss, np.inf), 1)
        for r in range(k):
            if okr[r]:
                gam[a + r] = cands[jj[r]]
                t = Tb[r, jj[r]]
                dif[a + r] = t[4] / t[3] - t[1] / t[0]
    lo, hi = pct(gam)
    dlo, dhi = pct(dif)
    n1, s1, _, n2, s2, _ = T[j]
    return dict(gamma=int(cands[j]), gamma_ci_low=lo, gamma_ci_high=hi, lr_set=conf, mean_low=float(s1 / n1), mean_high=float(s2 / n2),
                n_low=int(n1), n_high=int(n2), diff=float(s2 / n2 - s1 / n1), diff_ci_low=dlo, diff_ci_high=dhi,
                ssr_reduction=float(1 - ssr[j] / sse0), ssr_by_gamma=dict(zip(cands, [float(v) for v in ssr])),
                boot_gamma_dist=pd.Series(gam).value_counts(normalize=True).sort_index().round(3).to_dict(), min_regime=min_n)


# ---------------- report sections ----------------
def md_table(df, floatfmt='{:.3f}'):
    cols = list(df.columns)
    out = ['| ' + ' | '.join(map(str, cols)) + ' |', '|' + '---|' * len(cols)]
    for r in df.itertuples(index=False):
        out.append('| ' + ' | '.join(floatfmt.format(v) if isinstance(v, (float, np.floating)) and np.isfinite(v)
                                     else ('' if isinstance(v, (float, np.floating)) else str(v)) for v in r) + ' |')
    return out


def put_section(name, lines, path=REP / 'study2r_results.md', title='# Study 2R results'):
    """Replace or add a named section of the results report."""
    a, b = f'<!-- begin {name} -->', f'<!-- end {name} -->'
    text = path.read_text() if path.exists() else title + '\n'
    block = '\n'.join([a] + lines + [b])
    if a in text:
        i, j = text.index(a), text.index(b) + len(b)
        text = text[:i] + block + text[j:]
    else:
        text = text.rstrip('\n') + '\n\n' + block + '\n'
    path.write_text(text)
