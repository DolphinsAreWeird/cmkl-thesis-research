# 14. Tone (record, tone): GDELT tone only. Feature = mean tone over the first 4 weeks of the shift minus the
# category's 26-week median tone; the same for positive and negative tone. Each feature is added to the carry-over
# model and its coefficient is compared with the coefficients obtained when every shift's feature is replaced by a
# placebo feature from one of 200 random non-shift 4-week windows of the same category.
# NOT IN RECORD: (1) each of the three tone features is added in its own model, because GDELT tone is positive minus
# negative tone and the three together are collinear; (2) the placebo p-value is the share of placebo coefficients
# at least as large in absolute value as the real one (two-sided); (3) a shift blocks the longest of its real-time
# count (or class bound), its whole-course duration and 4 weeks from its start for the placebo windows; (4) placebo windows are
# drawn with the record's bootstrap seed, since the tone section gives none.
# Needs: the carry-over report and data/db/interest/gdelt_tone_weekly.parquet.
# Output: data/db/study3/tone_features.parquet, tone_models.csv, data/reports/study3_14_tone.md
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from _settings import SETTINGS as S
import _files as IO
import _methods as M
from _interest import load_tone, load_shifts, TONE_FILE

FEATURES = {'tone': 'tone_change', 'tone_pos': 'tone_pos_change', 'tone_neg': 'tone_neg_change'}


def span_weeks(sh):
    """Weeks a shift blocks for placebo windows: the longest of its real-time count (or class bound), its
    whole-course duration when known, and the tone window."""
    bound = {'sustained': S.sustained_min, 'intermediate': S.intermediate_eq, 'fading': S.fading_max}
    vals = [S.tone_weeks, bound.get(sh['duration_class'], 0)]
    for c in ('duration_count', 'whole_duration'):
        if c in sh and pd.notna(sh[c]):
            vals.append(int(sh[c]))
    return max(vals)


def features(R, shifts, T, n_placebo, rng):
    """Real tone features per shift, and placebo features per category (n_placebo windows)."""
    series = {n: g.set_index('week') for n, g in T.groupby('node_id')}
    real = []
    for sid, g in R.groupby('shift_id'):
        r = g.iloc[0]
        s = series.get(r.node_id)
        rec = dict(shift_id=sid)
        for col, name in FEATURES.items():
            rec[name] = M.tone_feature(s[col], r.start_week, S) if s is not None else np.nan
        real.append(rec)
    plac = {}
    for node in sorted(R.node_id.unique()):
        s = series.get(node)
        if s is None:
            continue
        own = shifts[shifts.node_id == node]
        blocked = M.blocked_weeks([(x.start_week, span_weeks(x)) for _, x in own.iterrows()])
        starts = M.tone_placebo_starts(s.index, blocked, S, rng)[:n_placebo]
        plac[node] = {name: np.array([M.tone_feature(s[col], w, S) for w in starts]) for col, name in FEATURES.items()}
    return pd.DataFrame(real), plac


def percentile(row, plac, name):
    p = plac.get(row.node_id, {}).get(name)
    if p is None or len(p) == 0 or np.isnan(row[name]):
        return np.nan
    p = p[~np.isnan(p)]
    return float(np.mean(p <= row[name])) if len(p) else np.nan


def placebo_test(d, plac, name, n_placebo):
    """Real coefficient of one tone feature against coefficients with placebo features (same model)."""
    X = M.carry_design(d, S, extra=(name,))
    real = M.ols(d.sc_effect_p, X)[name]
    coefs = []
    for b in range(n_placebo):
        db = d.copy()
        db[name] = [plac[n][name][b] if n in plac and b < len(plac[n][name]) else np.nan for n in db.node_id]
        db = db.dropna(subset=[name])
        if len(db) <= X.shape[1]:
            continue
        coefs.append(M.ols(db.sc_effect_p, M.carry_design(db, S, extra=(name,))).get(name, np.nan))
    c = np.asarray(coefs, dtype=float)
    c = c[~np.isnan(c)]
    p = float(np.mean(np.abs(c) >= abs(real))) if len(c) and not np.isnan(real) else np.nan
    return real, p, len(c)


def main():
    ap = IO.parser('Study 3 tone')
    ap.add_argument('--boot', type=int, default=None, help='simulation runs only: bootstrap resamples')
    ap.add_argument('--placebos', type=int, default=None, help='simulation runs only: placebo windows per category')
    args, P, meta, warn = IO.start('14', ap)
    n_boot = IO.sim_only(args, 'boot', S.boot_n)
    n_pl = IO.sim_only(args, 'placebos', S.tone_placebo_n)
    T = load_tone(P)
    if T is None:
        raise SystemExit(f'Step 14 refuses to run: {P.interest / TONE_FILE} does not exist (GDELT weekly tone not delivered yet).')
    shifts = load_shifts(P, S)
    R = IO.read_parquet(P.out('shift_effects.parquet'))
    R = R[(R.analysis == 'main') & R.sc_ok].copy()
    R['classic'] = R.format == 'librivox'
    rng = np.random.default_rng(S.boot_seed)
    F, plac = features(R, shifts, T, n_pl, rng)
    d_all = R.merge(F, on='shift_id', how='left')
    for name in FEATURES.values():
        d_all[f'{name}_placebo_pct'] = [percentile(r, plac, name) for _, r in d_all.iterrows()]
    IO.save_parquet(d_all[['shift_id', 'node_id', 'level', 'source', 'format'] + list(FEATURES.values())
                          + [f'{n}_placebo_pct' for n in FEATURES.values()]], P.out('tone_features.parquet'))
    rows = []
    for (src, level), g in d_all.groupby(['source', 'level']):
        for name in FEATURES.values():
            d = g.dropna(subset=[name, 'sc_effect_p', 'size']).reset_index(drop=True)
            if d.node_id.nunique() < 3:
                continue
            tab, n, ncl = M.carry_fit(d, S, extra=(name,), n_boot=n_boot)
            t = tab.set_index('term').loc[name]
            real, p_pl, n_ok = placebo_test(d, plac, name, n_pl)
            rows.append(dict(source=src, level=level, feature=name, coef=t.coef, ci_low=t.ci_low, ci_high=t.ci_high,
                             boot_p=t.boot_p, placebo_p=p_pl, placebo_fits=n_ok, n_tests=n, n_categories=ncl))
    Mdl = pd.DataFrame(rows)
    IO.save_csv(Mdl, P.out('tone_models.csv'))
    L = [f'- tone features for {F.shift_id.nunique()} shifts; placebo windows per category: {n_pl} (record {S.tone_placebo_n})',
         f'- bootstrap: {n_boot} resamples (record {S.boot_n}); seed {S.boot_seed}',
         '- placebo_p: share of placebo-feature coefficients with |coef| >= |real coef|'] + [f'- WARNING: {w}' for w in warn]
    L += ['', '## Tone added to the carry-over model'] + (IO.md_table(Mdl) if len(Mdl) else ['(no model could be fitted)'])
    pct = d_all[[f'{n}_placebo_pct' for n in FEATURES.values()]]
    L += ['', '## Shift tone features against their own category\'s placebo windows (share of shifts outside the 5-95% range)']
    L += [f'- {c}: {float(((pct[c] < 0.05) | (pct[c] > 0.95)).mean()):.3f} of {int(pct[c].notna().sum())}' for c in pct.columns]
    path = IO.write_report(P, '14', 'Study 3 tone', L, S, meta)
    print('\n'.join(L))
    print('report:', path)


if __name__ == '__main__':
    main()
