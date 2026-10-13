# Shift labelling with the fixed definitions of prereg/study3_settings_2026-10-13.json (all numbers come from
# _ci.settings(); nothing is hard-coded here). Every label uses only weeks up to the week being judged.
#   normal level  = median of the previous 26 weeks (current week excluded); all 26 must be full, valid weeks
#   minimum volume = the median raw volume of those 26 weeks must reach the source's minimum (views or mentions)
#   ratio         = this week's share / normal level
#   rising week   = ratio >= 1.5 and an 8-week Mann-Kendall test (this week included, Hamed-Rao variance) with tau > 0 and
#                   one-sided p < 0.10
#   shift start   = first rising week after at least 8 consecutive weeks with ratio < 1.5. Reading used here: once 8 quiet
#                   weeks have passed, the series is "armed" and the next rising week starts a shift, even if a few elevated
#                   but not yet rising weeks come in between (a sudden jump passes the 8-week test only in its third week).
#                   The strict reading (the 8 quiet weeks directly before the start) is recorded in `strict_start`.
#   duration      = consecutive weeks from the start with ratio >= 1.5; sustained >= 4 (labelled in week 4), intermediate 3,
#                   fading <= 2 (labelled in the week the ratio falls back); size = peak ratio up to the labelling week
#   seasonal      = a start within +/-2 ISO weeks of the same calendar week in at least half of the other years with data
import numpy as np, pandas as pd, pymannkendall as mk, warnings
from scipy.stats import norm
warnings.simplefilter('ignore')


def thresholds(S, scale=None):
    """Duration classes. scale=None gives the fixed (Wikipedia) values; a GDELT scale factor r gives
    round(value * r) with a minimum of 2 weeks (the rule in the record)."""
    if scale is None:
        return dict(sustained_min=S['sustained_min'], label_week=S['sustained_label_week'], fading_max=S['fading_max'])
    smin = max(2, int(round(S['sustained_min'] * scale)))
    fmax = max(2, int(round(S['fading_max'] * scale)))
    conflict = fmax >= smin                      # the minimum of 2 weeks cannot hold for both classes
    if conflict:
        fmax = smin - 1
    return dict(sustained_min=smin, label_week=smin, fading_max=fmax, conflict=conflict)


def classify(d, th):
    if d >= th['sustained_min']:
        return 'sustained'
    if d <= th['fading_max']:
        return 'fading'
    return 'intermediate'


def label_series(df, S, min_vol, th=None):
    """df: one series, consecutive weeks, columns week, x (share), v (raw volume), valid (full week).
    Returns (weekly frame with normal, ratio, rising..., list of shift dicts)."""
    th = th or thresholds(S)
    df = df.sort_values('week').reset_index(drop=True)
    x = df.x.to_numpy(float); v = df.v.to_numpy(float); valid = df.valid.to_numpy(bool) & np.isfinite(x)
    W = S['normal_weeks']; K = S['mk_weeks']; R = S['rise_ratio']; Q = S['quiet_weeks']; A = S['mk_alpha_one_sided']
    xs = pd.Series(np.where(valid, x, np.nan)); vs = pd.Series(np.where(valid, v, np.nan))
    normal = xs.shift(1).rolling(W, min_periods=W).median().to_numpy()
    vnorm = vs.shift(1).rolling(W, min_periods=W).median().to_numpy()
    usable = valid & np.isfinite(normal) & (normal > 0) & (vnorm >= min_vol)
    ratio = np.where(usable, x / np.where(normal > 0, normal, np.nan), np.nan)
    n = len(df)
    tau = np.full(n, np.nan); p1 = np.full(n, np.nan); rising = np.zeros(n, bool)
    for t in np.where(usable & (ratio >= R))[0]:
        if t < K - 1 or not valid[t - K + 1:t + 1].all():
            continue
        r = mk.hamed_rao_modification_test(x[t - K + 1:t + 1])
        tau[t] = r.Tau
        p1[t] = 1 - norm.cdf(r.z) if np.isfinite(r.z) else np.nan
        rising[t] = (r.Tau > 0) and (p1[t] < A)
    shift_id = np.full(n, -1); phase = np.array([''] * n, dtype=object)
    shifts = []; quiet = 0; armed = False; act = None; elevated_run = 0
    for t in range(n):
        if act is not None:
            if usable[t] and ratio[t] >= R:
                act['dur'] += 1; act['peak_all'] = max(act['peak_all'], ratio[t])
                if act['label'] is None:
                    act['peak_rt'] = max(act['peak_rt'], ratio[t])
                    if act['dur'] == th['label_week'] and act['dur'] >= th['sustained_min']:
                        act.update(label='sustained', label_week=df.week[t], size=act['peak_rt'], dur_rt=act['dur'])
                shift_id[t] = act['id']; phase[t] = 'in shift'
                continue
            # the shift ends this week (or data stops)
            if act['label'] is None:
                lab = classify(act['dur'], th) if usable[t] else 'interrupted'
                act.update(label=lab, label_week=df.week[t], size=act['peak_rt'], dur_rt=act['dur'])
            act['end_week'] = df.week[t]
            shifts.append(act); act = None; armed = False
            quiet = 1 if (usable[t] and ratio[t] < R) else 0
            elevated_run = 0
            continue
        if not usable[t]:
            quiet = 0; armed = False; elevated_run = 0
            continue
        if ratio[t] < R:
            quiet += 1; elevated_run = 0
            if quiet >= Q:
                armed = True
            continue
        if armed and rising[t]:
            act = dict(id=len(shifts), start_week=df.week[t], start_idx=t, dur=1, peak_rt=ratio[t], peak_all=ratio[t], label=None,
                       label_week=None, size=None, dur_rt=None, strict_start=quiet >= Q, elevated_weeks_before=elevated_run,
                       ratio_start=ratio[t], normal_start=normal[t], volume_normal_start=vnorm[t], mk_tau=tau[t], mk_p1=p1[t])
            shift_id[t] = act['id']; phase[t] = 'start'
            armed = False; quiet = 0; elevated_run = 0
            if th['label_week'] == 1 and th['sustained_min'] <= 1:
                act.update(label='sustained', label_week=df.week[t], size=ratio[t], dur_rt=1)
            continue
        quiet = 0; elevated_run += 1
    if act is not None:
        if act['label'] is None:
            act.update(label='censored', label_week=None, size=act['peak_rt'], dur_rt=act['dur'])
        act['end_week'] = None
        shifts.append(act)
    out = df.assign(normal=normal, volume_normal=vnorm, usable=usable, ratio=ratio, mk_tau=tau, mk_p1=p1, rising=rising,
                    shift_id=shift_id, phase=phase)
    for s in shifts:
        s['whole_duration'] = s.pop('dur'); s['whole_peak'] = s.pop('peak_all'); s.pop('peak_rt', None)
    return out, shifts


def seasonal_flags(shifts, weekly, S):
    """shifts: DataFrame with key columns source,level,node_id,start_week; weekly: frame with the same keys, week, usable.
    A shift is seasonal if, in at least half of the other ISO years with data around the same calendar week (>= 3 of the
    5 weeks usable), the same series has a shift start within +/-2 ISO weeks."""
    win = S['seasonal_window']; share = S['seasonal_share']
    out = []
    wk = weekly[['source', 'level', 'node_id', 'week', 'usable']].copy()
    iso = wk.week.dt.isocalendar(); wk['iy'] = iso.year.to_numpy(); wk['iw'] = iso.week.to_numpy()
    sh = shifts.copy()
    iso = sh.start_week.dt.isocalendar(); sh['iy'] = iso.year.to_numpy(); sh['iw'] = iso.week.to_numpy()

    def cdist(a, b):
        d = abs(a - b) % 52
        return min(d, 52 - d)

    for key, g in sh.groupby(['source', 'level', 'node_id']):
        w = wk[(wk.source == key[0]) & (wk.level == key[1]) & (wk.node_id == key[2])]
        for r in g.itertuples():
            years = [y for y in sorted(w.iy.unique()) if y != r.iy]
            with_data = []; hits = 0
            for y in years:
                wy = w[(w.iy == y) & w.iw.map(lambda z: cdist(z, r.iw) <= win)]
                if wy.usable.sum() >= 3:
                    with_data.append(y)
                    if any((g.iy == y) & g.iw.map(lambda z: cdist(z, r.iw) <= win)):
                        hits += 1
            n = len(with_data)
            out.append(dict(source=key[0], level=key[1], node_id=key[2], start_week=r.start_week, other_years_with_data=n,
                            years_with_start=hits, seasonal=(n >= 1 and hits >= share * n)))
    return pd.DataFrame(out)
