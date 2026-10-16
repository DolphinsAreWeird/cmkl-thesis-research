# Conversation sources, talk pages, step 4: parameter-audit noise benchmark for the talk-edit series, from interest data only
# (no borrowing data are read). Same method as code/parameter_audit/calibrate_interest.py section 3: each series is rebuilt from
# its own quiet-week deviations from normal (weeks outside detected shifts), resampled in circular blocks of 8 weeks (2 rebuilt
# series per real series, seed 20261013); the unchanged rule runs on real and rebuilt series for the record settings and for the
# audit's grid of ratio, Mann-Kendall alpha and quiet weeks. Noise share = shifts per 100 series-years in rebuilt series divided
# by shifts per 100 series-years in the real series (all classes, and sustained only). Series: narrow and middle nodes whose median
# normal volume reaches 20 edits a week for at least part of the period (the others cannot be usable).
# Also: share of usable weeks with ratio >= 1.2 ... 3.0 and weekly variability, by level.
# Outputs: data/reports/talk_edits_noise_benchmark.csv, talk_edits_ratio_distribution.csv. Run:
#   bash jobs/heavy_lock.sh nice -n 10 env OMP_NUM_THREADS=1 .venv/bin/python code/conversation/04_talk_noise.py   (from handoff/)
import sys, pathlib, numpy as np, pandas as pd
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'main_study' / 'interest'))
import _shifts as SH  # noqa: E402

BASE = dict(normal_weeks=26, mk_weeks=8, rise_ratio=1.5, quiet_weeks=8, mk_alpha_one_sided=0.10, sustained_min=4, sustained_label_week=4, fading_max=2)
MINV = 20.0
SEED, REPS, BLOCK = 20261013, 2, 8
W = pd.read_parquet('data/db/interest/talk_edits/weekly_node.parquet')
W = W[W.level.isin([2, 3])]
SERIES = []
for (lvl, nid), g in W.groupby(['level', 'node_id']):
    s = g.sort_values('week').rename(columns={'share': 'x', 'edits': 'v'})
    s = s.assign(valid=~s.partial_week & np.isfinite(s.x) & (s.x > 0))[['week', 'x', 'v', 'valid']].reset_index(drop=True)
    SERIES.append((lvl, nid, s))
print('series', len(SERIES), flush=True)


def vol_ok(s):
    vs = pd.Series(np.where(s.valid, s.v, np.nan))
    vn = vs.shift(1).rolling(26, min_periods=26).median()
    return (vn >= MINV).to_numpy()


# keep only series that ever reach the minimum (the rest contribute no usable weeks to either side)
SERIES = [(l, n, s) for l, n, s in SERIES if vol_ok(s).any()]
print('series reaching the minimum at some point', len(SERIES), {l: sum(1 for a, _, _ in SERIES if a == l) for l in (2, 3)}, flush=True)

rows = []
for lvl, nid, s in SERIES:
    xs = pd.Series(np.where(s.valid, s.x, np.nan))
    normal = xs.shift(1).rolling(26, min_periods=26).median()
    ok = vol_ok(s) & np.isfinite(xs / normal) & (normal > 0)
    rows.append(pd.DataFrame(dict(level=lvl, node_id=nid, ratio=(xs / normal)[ok].to_numpy())))
R = pd.concat(rows, ignore_index=True)
R['lev'] = R.level.map({2: 'middle', 3: 'narrow'})
tab = []
for lev, g in R.groupby('lev'):
    r = g.ratio.to_numpy()
    d = dict(level=lev, weeks=len(r), series=g.node_id.nunique())
    for t in (1.2, 1.3, 1.5, 2.0, 3.0):
        d[f'share_ge_{t}'] = (r >= t).mean()
    for q in (90, 95, 97.5, 99):
        d[f'p{q}'] = np.percentile(r, q)
    tab.append(d)
T1 = pd.DataFrame(tab)
print(T1.round(4).to_string(index=False), flush=True)
T1.to_csv('data/reports/talk_edits_ratio_distribution.csv', index=False)


def run_rule(s, S):
    _, sh = SH.label_series(s, S, MINV)
    return [d['label'] for d in sh if d['label'] in ('sustained', 'intermediate', 'fading')]


def series_years(s):
    xs = pd.Series(np.where(s.valid, s.x, np.nan))
    normal = xs.shift(1).rolling(26, min_periods=26).median()
    return float((np.isfinite(normal) & (normal > 0) & vol_ok(s) & np.isfinite(xs)).sum()) / 52.18


def surrogate(s, rng):
    w, sh = SH.label_series(s, BASE, MINV)
    quiet = w.usable & (w.shift_id < 0) & np.isfinite(w.ratio) & (w.ratio > 0)
    r = np.log(w.ratio[quiet].to_numpy())
    n = len(s)
    if len(r) < 52:
        return None
    out = np.empty(0)
    while len(out) < n:
        st = rng.integers(0, len(r))
        out = np.concatenate([out, np.take(r, np.arange(st, st + BLOCK), mode='wrap')])
    return pd.DataFrame(dict(week=s.week.to_numpy(), x=np.exp(out[:n]), v=np.full(n, 1e9), valid=np.ones(n, bool)))


GRID = [('ratio', v, dict(BASE, rise_ratio=v)) for v in (1.2, 1.3, 1.5, 2.0, 2.5, 3.0)]
GRID += [('mk_alpha', v, dict(BASE, mk_alpha_one_sided=v)) for v in (0.05, 0.20, 1.0)]
GRID += [('quiet_weeks', v, dict(BASE, quiet_weeks=v)) for v in (4, 12)]
rng = np.random.default_rng(SEED)
SUR = []
for lvl, nid, s in SERIES:
    for k in range(REPS):
        z = surrogate(s, rng)
        if z is not None:
            SUR.append((lvl, nid, k, z))
print('rebuilt series', len(SUR), flush=True)
out = []
for name, val, S in GRID:
    for lvl in (3, 2):
        real = [s for (b, c, s) in SERIES if b == lvl]
        sur = [z for (b, c, k, z) in SUR if b == lvl]
        yrs_real = sum(series_years(s) for s in real)
        yrs_sur = sum((len(z) - 26) / 52.18 for z in sur)
        lr = [l for s in real for l in run_rule(s, S)]
        ls = [l for z in sur for l in run_rule(z, S)]
        d = dict(setting=name, value=val, source='talk_edits', level={3: 'narrow', 2: 'middle'}[lvl], real_series=len(real), noise_series=len(sur),
                 real_series_years=round(yrs_real, 1), real_shifts=len(lr), real_per100y=100 * len(lr) / yrs_real if yrs_real else np.nan,
                 real_sustained=sum(l == 'sustained' for l in lr), noise_series_years=round(yrs_sur, 1), noise_shifts=len(ls),
                 noise_per100y=100 * len(ls) / yrs_sur if yrs_sur else np.nan, noise_sustained=sum(l == 'sustained' for l in ls))
        d['noise_share_all'] = d['noise_per100y'] / d['real_per100y'] if d['real_per100y'] else np.nan
        rs = 100 * d['real_sustained'] / yrs_real if yrs_real else np.nan
        ns = 100 * d['noise_sustained'] / yrs_sur if yrs_sur else np.nan
        d['noise_share_sustained'] = ns / rs if rs else np.nan
        out.append(d)
        print(name, val, lvl, 'real', len(lr), 'noise', len(ls), flush=True)
T3 = pd.DataFrame(out)
print(T3.round(3).to_string(index=False))
T3.to_csv('data/reports/talk_edits_noise_benchmark.csv', index=False)
print('DONE')
