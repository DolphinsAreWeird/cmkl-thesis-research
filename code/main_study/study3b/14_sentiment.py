# 14. Sentiment direction (record, sentiment): does negative as well as positive news sentiment carry over into demand, and does
# emotional intensity matter? GDELT tone only (2017-01 to 2021-06 until the backfill; after the backfill the same script is rerun to
# the end with the same settings). Features per shift (first 4 weeks against the 26-week median, Study 3 tone function):
#   delta tone, delta positive, delta negative, delta intensity = delta (positive + negative), negative shift = 1 if delta tone < 0.
# Tests: (1) each feature added to the carry-over regression on its own (outcome tau); (2) negative shift x sustained interaction;
# (3) comparison with 200 placebo windows per category (random non-shift 4-week windows), two-sided: every shift's feature is
# replaced in turn by the feature of one placebo window of its category, the same model is refitted, and the placebo p is the share of
# placebo coefficients with |coef| >= |real coef|.
# NOT IN RECORD: (1) each feature in its own model (the three tone features are collinear); (2) the two-sided placebo p reading above
# (as the Study 3 tone test); (3) a shift blocks max(4 weeks, class bound, real-time count, whole duration) of its category for the
# placebo windows, all sources and classes of that category; the baseline of a window excludes its start week; placebo windows are
# drawn with the bootstrap seed, without replacement when enough exist; (4) the interaction model contains negative shift, the
# sustained class dummy (already in the carry-over design) and their product; the placebo test for it replaces negative shift (and so
# the product) by the placebo window's; (5) models per level on GDELT shifts of the main analysis, non-sparse, sum Y > 0;
# (6) partial GDELT weeks are missing; (7) a descriptive table gives mean tau of negative and non-negative shifts by duration class.
# Needs: the carry-over report, the GDELT weekly tone files. Output: data/db/study3b/sentiment_features.parquet, sentiment_models.csv,
# report study3b_14_sentiment.md
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from _settings import SETTINGS as S
import _paths as IO
import _inference as INF
import _methods as M

FEATURES = ('d_tone', 'd_pos', 'd_neg', 'd_intensity', 'neg_shift')


def load_tone(P):
    """GDELT weekly tone per category: node levels from weekly_node.parquet, values from weekly_value.parquet; partial weeks missing."""
    out = {}
    fn, fv = P.interest / 'gdelt' / 'weekly_node.parquet', P.interest / 'gdelt' / 'weekly_value.parquet'
    for f in (fn, fv):
        if not f.exists():
            raise SystemExit(f'Step 14 refuses to run: {f} does not exist (GDELT weekly tone not delivered yet).')
    N = pd.read_parquet(fn)
    N = N[N.level.isin([2, 3])].assign(lvl=lambda d: d.level.map({2: 'middle', 3: 'narrow'}), key=lambda d: d.node_id)
    V = pd.read_parquet(fv).assign(lvl='value', key=lambda d: d.value)
    T = pd.concat([N[['lvl', 'key', 'week', 'tone', 'positive', 'negative', 'partial_week']], V[['lvl', 'key', 'week', 'tone', 'positive', 'negative', 'partial_week']]])
    T = T.rename(columns={'positive': 'tone_pos', 'negative': 'tone_neg'})
    T['week'] = pd.to_datetime(T.week)
    T.loc[T.partial_week.astype(bool), ['tone', 'tone_pos', 'tone_neg']] = np.nan
    for (lv, k), g in T.groupby(['lvl', 'key']):
        out[(lv, k)] = g.set_index('week').sort_index()[['tone', 'tone_pos', 'tone_neg']]
    return out


def span_weeks(sh):
    bound = {'sustained': S.sustained_min, 'intermediate': S.intermediate_eq, 'fading': S.fading_max}
    vals = [S.tone_weeks, bound.get(sh['duration_class'], 0)]
    for c in ('duration_count', 'whole_duration'):
        if c in sh and pd.notna(sh[c]):
            vals.append(int(sh[c]))
    return max(vals)


def features(R, shifts, series, n_placebo, rng):
    """Real features per shift, and placebo features per category: arrays of n_placebo windows per feature."""
    real = []
    for sid, g in R.groupby('shift_id'):
        r = g.iloc[0]
        s = series.get((r.level, r.node_id))
        rec = dict(shift_id=sid)
        rec.update(M.sentiment_features(s, r.start_week, S) if s is not None else {k: np.nan for k in FEATURES})
        real.append(rec)
    plac = {}
    for (lv, node), _ in R.groupby(['level', 'node_id']):
        s = series.get((lv, node))
        if s is None:
            continue
        own = shifts[(shifts.level == lv) & (shifts.node_id == node)]
        blocked = M.blocked_weeks([(x.start_week, span_weeks(x)) for _, x in own.iterrows()])
        starts = M.tone_placebo_starts(s.index, blocked, S, rng)[:n_placebo]
        feats = [M.sentiment_features(s, w, S) for w in starts]
        plac[(lv, node)] = {k: np.array([f[k] for f in feats], dtype=float) for k in FEATURES}
    return pd.DataFrame(real), plac


def design(d, feat):
    """Carry-over design with the feature (or, for 'interaction', negative shift and its product with the sustained class)."""
    return M.carry_design(d, S, extra=feat)


def with_interaction(d):
    d = d.copy()
    d['neg_x_sustained'] = d.neg_shift * (d.duration_class == 'sustained').astype(float)
    return d


def placebo_coefs(d, plac, feat_cols, coef, interaction=False):
    """Coefficient `coef` when every shift's feature is replaced by its category's b-th placebo window (b = 0..n-1)."""
    n = max((len(v[feat_cols[0]]) for v in plac.values()), default=0)
    out = []
    for b in range(n):
        db = d.copy()
        for c in feat_cols:
            src = 'neg_shift' if c == 'neg_x_sustained' else c
            db[src] = [plac[(lv, nd)][src][b] if (lv, nd) in plac and b < len(plac[(lv, nd)][src]) else np.nan for lv, nd in zip(db.level, db.node_id)]
        if interaction:
            db['neg_x_sustained'] = db.neg_shift * (db.duration_class == 'sustained').astype(float)
        db = db.replace([np.inf, -np.inf], np.nan).dropna(subset=list(dict.fromkeys(['neg_shift' if c == 'neg_x_sustained' else c for c in feat_cols])) + ['tau_p'])
        if len(db) <= 12:
            continue
        X = M.carry_design(db, S, extra=tuple(feat_cols))
        out.append(M.ols_fit(db.tau_p, X).get(coef, np.nan))
    return np.asarray(out, dtype=float)


def main():
    ap = IO.parser('Study 3b sentiment direction')
    ap.add_argument('--boot', type=int, default=None, help='simulation runs only: bootstrap resamples')
    ap.add_argument('--placebos', type=int, default=None, help='simulation runs only: placebo windows per category')
    args, P, meta, warn = IO.start('14', ap)
    n_boot = IO.sim_only(args, 'boot', S.boot_n)
    n_pl = IO.sim_only(args, 'placebos', S.sent_placebo_n)
    series = load_tone(P)
    shifts = INF.load_shifts(P, S)
    R = IO.read_parquet(P.out('shift_effects.parquet'))
    R = R[(R.analysis == 'main') & (R.skip == '') & (R.source == 'gdelt') & ~R.too_sparse.fillna(False).astype(bool)].replace([np.inf, -np.inf], np.nan).dropna(subset=['tau_p']).copy()
    rng = np.random.default_rng(S.boot_seed)
    F, plac = features(R, shifts, series, n_pl, rng)
    d_all = R.merge(F, on='shift_id', how='left')
    IO.save_parquet(d_all[['shift_id', 'node_id', 'level', 'source', 'tau_p'] + list(FEATURES)], P.out('sentiment_features.parquet'))
    rows = []
    for level, g in d_all.groupby('level'):
        for feat in FEATURES:
            d = g.dropna(subset=[feat]).reset_index(drop=True)
            if d.node_id.nunique() < 3 or len(d) < 15:
                continue
            tab, n, ncl = M.carry_fit(d, S, outcome='tau_p', extra=(feat,), n_boot=n_boot)
            t = tab.set_index('term').loc[feat]
            real = float(t.coef)
            pc = placebo_coefs(d, plac, [feat], feat)
            rows.append(dict(level=level, model=f'{feat} alone', term=feat, coef=real, ci_low=t.ci_low, ci_high=t.ci_high, boot_p=t.boot_p,
                             placebo_p=M.placebo_two_sided(real, pc), placebo_fits=int(np.isfinite(pc).sum()), n_tests=n, n_categories=ncl))
        d = with_interaction(g.dropna(subset=['neg_shift']).reset_index(drop=True))
        if d.node_id.nunique() >= 3 and len(d) >= 15:
            tab, n, ncl = M.carry_fit(d, S, outcome='tau_p', extra=('neg_shift', 'neg_x_sustained'), n_boot=n_boot)
            for term in ('neg_shift', 'neg_x_sustained', 'class_sustained'):
                if term in set(tab.term):
                    t = tab.set_index('term').loc[term]
                    pc = placebo_coefs(d, plac, ['neg_shift', 'neg_x_sustained'], term, interaction=True) if term != 'class_sustained' else np.array([])
                    rows.append(dict(level=level, model='negative shift x sustained', term=term, coef=float(t.coef), ci_low=t.ci_low, ci_high=t.ci_high,
                                     boot_p=t.boot_p, placebo_p=M.placebo_two_sided(float(t.coef), pc) if len(pc) else np.nan, placebo_fits=int(np.isfinite(pc).sum()),
                                     n_tests=n, n_categories=ncl))
    Mdl = pd.DataFrame(rows)
    IO.save_csv(Mdl, P.out('sentiment_models.csv'))
    desc = []
    for (level, cls, neg), g in d_all.dropna(subset=['neg_shift']).groupby(['level', 'duration_class', 'neg_shift']):
        b = M.cluster_boot_mean(g.tau_p.to_numpy(), g.node_id.to_numpy(), n_boot, S.boot_seed)
        desc.append(dict(level=level, duration_class=cls, negative_shift=int(neg), tests=b['n'], categories=b['clusters'], mean_tau=b['mean'], ci_low=b.get('low'), ci_high=b.get('high')))
    L = [f'- GDELT shifts in the main analysis (non-sparse, sum Y > 0): {R.shift_id.nunique()}; with a complete delta tone: {int(d_all.d_tone.notna().sum())}; '
         f'placebo windows per category: {n_pl} (record {S.sent_placebo_n})',
         f'- bootstrap: {n_boot} resamples (record {S.boot_n}); seed {S.boot_seed}; 95% percentile intervals',
         '- placebo_p: share of placebo-feature coefficients with |coef| >= |real coef| (two-sided)',
         f'- tone data end: {max((s.index.max() for s in series.values()), default=None)}'] + [f'- WARNING: {w}' for w in warn]
    L += ['', '## Sentiment features added to the carry-over regression'] + (IO.md_table(Mdl) if len(Mdl) else ['(no model could be fitted)'])
    L += ['', '## Mean tau of negative (1) and non-negative (0) shifts by duration class (descriptive)'] + (IO.md_table(pd.DataFrame(desc)) if desc else ['(none)'])
    path = IO.write_report(P, '14', 'Study 3b sentiment direction', L, S, meta)
    print('\n'.join(L))
    print('report:', path)


if __name__ == '__main__':
    main()
