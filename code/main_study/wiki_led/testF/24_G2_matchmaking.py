#!/usr/bin/env python3
"""Test F, step 24, check G2 (and the effect part of G4): rises of the AI theme series and the borrowing that follows, with Chapter 6's code.

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (tests.G2_matchmaking_primary, tests.G4_books_side) and, for everything
Chapter 6 fixed, prereg/study3_settings_2026-10-13.json with its addenda (hash-checked by the Study 3 and interest code that is imported).
Reused unchanged:
  rises      interest/_shifts.py label_series and seasonal_flags with the settings parsed by interest/_ci.settings() (normal level = median of
             the previous 26 weeks; a rising week has ratio >= 1.5 and an 8-week Mann-Kendall rise; a start needs 8 quiet weeks before;
             sustained = 4 weeks or more at >= 1.5, fading = 1 or 2 weeks; minimum normal volume 1,000 weekly views), levels narrow and middle
  adapter    study3/_interest.normalise_shifts (classes, sizes, quality flags, month 0 = the month of the start week's Monday)
  effects    study3/_analysis.Context and test_unit (own trend: event study on months -30 to -7; synthetic control on months -24 to -3 with
             the donor rules; placebo categories and placebo years), 12_shift_effects.plan, add_q and pooled (bootstrap clustered by
             category, 2,000 resamples, seed 20261013, 95% percentile intervals)
  quality    the flags of interest/09_wiki_spike_check.py: 'one_day' (a day carries >= 50% of the theme's weekly views in one of the first
             weeks) and 'desktop_only' (the rise of the page that drives it is >= 90% desktop and >= 25 points above its usual desktop share;
             desktop views from 22_download_views.py --desktop); flagged rises are not tested in the main run and still count in the
             screens (Chapter 6 addendum g); --include-flagged is the robustness run.
Choices NOT IN ADDENDUM (fixed here before any series or rise exists):
  - the series' 'volume' for the minimum-volume rule is its weekly weighted views (the numerator of the share);
  - the page that drives a rise is the theme page with the largest weighted rise (weight x views over the first weeks minus the median day
    of the 26 weeks before times the number of days), as in interest/09; 'title_confusion' (a hand check in Chapter 6) is not applied,
    because the AI sorting is what replaces the title match;
  - donor and placebo-year screens use the rises of the new series (all classes, seasonal and flagged included) together with the stored
    GDELT rises (data/db/interest/shifts.parquet), i.e. 'both sources' of Chapter 6 with the new series in place of the concept pages
    (--screen new to use only the new series, --screen all to add the concept-page rises too);
  - besides Chapter 6's pooled rows (per level), a row pooling both levels is added for each duration class (same bootstrap).
Panels: a = data/db/study3/demand_panel.parquet (+ LibriVox), b and c = panel_b / panel_c of 23_panels.py.
Decision (G2): panel a, rises of 4 weeks or more, pooled months 0 to 2 effect with a 95% interval above 0 (shown for each level and method).
Stages: --stage shifts reads only interest data and writes shifts_<S>.parquet and shift_drivers_<S>.parquet (for the desktop check);
--stage effects reads the panels. In a mock world panel a is shuffled across themes and months before use (b and c are written shuffled),
and --mock-inject L adds L to the log share of a tested theme in months 0 to 2 of each tested lasting rise (a wiring check).
G4 (descriptive): panel b minus panel c on the same rise-by-format tests, pooled with the same clustered bootstrap.
Outputs: shifts_<S>.parquet, shift_drivers_<S>.parquet, g2_<S>_tests_<panel>.parquet, g2_<S>_pooled.csv, g2_<S>_paired_b_minus_c.csv,
g2_<S>_summary.json; reports
testF_24_G2_<S>_shifts.md, testF_24_G2_<S>.md (suffix _with_flagged for the robustness run).
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/24_G2_matchmaking.py --series S2 --stage shifts
                 bash ../jobs/heavy_lock.sh nice -n 10 ../.venv/bin/python main_study/wiki_led/testF/24_G2_matchmaking.py --series S2 --stage effects
"""
import sys, time, json, pathlib, argparse, importlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from scipy import sparse
import _testf_analysis as T
sys.path.insert(0, str(T.MAIN / 'interest'))
sys.path.insert(0, str(T.MAIN / 'study3'))
from _settings import SETTINGS as S                           # noqa: E402  Study 3 record + addenda (hash-checked)
import _files as IO                                            # noqa: E402
import _analysis as A3                                         # noqa: E402
import _methods as M                                           # noqa: E402
from _build import mi_from_ym                                  # noqa: E402
from _interest import normalise_shifts, load_shifts            # noqa: E402
E12 = importlib.import_module('12_shift_effects')              # plan, add_q, pooled, SHIFT_COLS (Chapter 6)
import _ci                                                     # noqa: E402  interest settings (hash-checked)
import _shifts as SH                                           # noqa: E402

SI = _ci.settings()
SINGLE_DAY, DESK_RISE, DESK_GAP = 0.5, 0.9, 0.25              # interest/09_wiki_spike_check.py (not tuned)
STUDY3 = T.D / 'db' / 'study3'


# ---------------------------------------------------------------- stage 1: rises (interest data only)
def detect(w):
    weekly, shifts = [], []
    for (lvl, nid), g in w[w.level.isin([2, 3])].groupby(['level', 'node_id']):
        s = g.sort_values('week').rename(columns={'share': 'x', 'views': 'v'}).assign(valid=lambda d: ~d.partial_week.astype(bool))[['week', 'x', 'v', 'valid']]
        wl, sh = SH.label_series(s, SI, SI['min_wiki_views'])
        wl['source'] = 'wikipedia'; wl['level'] = lvl; wl['node_id'] = nid
        weekly.append(wl[['source', 'level', 'node_id', 'week', 'usable', 'ratio']])
        for d in sh:
            d.update(source='wikipedia', level=int(lvl), node_id=nid)
            shifts.append(d)
    weekly = pd.concat(weekly, ignore_index=True)
    X = pd.DataFrame(shifts)
    if X.empty:
        return X, weekly
    sf = SH.seasonal_flags(X, weekly, SI)
    X = X.merge(sf, on=['source', 'level', 'node_id', 'start_week'], how='left')
    X['large'] = X['size'] >= SI['large_ratio']
    X['tested_level'] = X.level.isin([3, 2])
    X['main_set'] = X.tested_level & ~X.seasonal.astype(bool) & ~X.label.isin(['censored', 'interrupted'])
    return X, weekly


def page_daily(P, series, A):
    """Pages, their theme weights and their daily views (rows = pages, columns = days of T.DAYS), as used by the series."""
    if series in ('S2', 'S2C'):
        sel = pd.read_parquet(P / ('s2_pages.parquet' if series == 'S2' else 's2c_pages.parquet'))
        use = set(sel[sel.selected & sel.stored].title)
        pairs = A[(A.set == 'universe') & (A.conf >= T.S2_MIN_CONF) & A.title.isin(use)][['title', 'code', 'weight']]
        titles = sorted(pairs.title.unique())
        V, _ = T.store_matrix(P, titles)                          # dense int32 (40,000 pages: 0.66 GB); sliced row block by row block
    else:
        pairs = A[A.set == 'universe'][['title', 'code', 'weight']]
        titles = sorted(pairs.title.unique())
        L, _ = T.top_long(titles=set(titles))
        pos = {t: i for i, t in enumerate(titles)}
        col = (L.date - T.DAY0).dt.days.to_numpy()
        V = sparse.csr_matrix((L.views.to_numpy(dtype=np.int64), (L.title.map(pos).to_numpy(), col)), shape=(len(titles), len(T.DAYS)))
    return pairs, titles, V


def block(V, rows, c0, c1):
    """Rows x days block as floats from a dense array (S2) or a sparse matrix (S1)."""
    if sparse.issparse(V):
        return V[rows][:, c0:c1].toarray().astype(float)
    return V[rows, c0:c1].astype(float)


def drivers(X, w, pairs, titles, V):
    """Driver page and the one-day flag of every rise at a tested level (interest/09 rules, weighted pages)."""
    par = T.parent_map()
    tpos = {t: i for i, t in enumerate(titles)}
    pn = pairs.assign(node=pairs.code)
    pm = pairs.assign(node=pairs.code.map(par))
    node_pages = {n: g.groupby('title').weight.sum() for n, g in pd.concat([pn, pm]).groupby('node')}
    tds = w.set_index(['node_id', 'week']).top_day_share
    out = []
    for r in X[X.tested_level].itertuples():
        n_w = int(min(max(r.whole_duration, 1), 4))
        a = pd.Timestamp(r.start_week); b = a + pd.Timedelta(days=7 * n_w - 1); base_a = a - pd.Timedelta(weeks=26)
        weeks = pd.date_range(a, periods=n_w, freq='7D')
        mx = tds.reindex(pd.MultiIndex.from_arrays([[r.node_id] * n_w, weeks])).max()
        rec = dict(level=r.level, node_id=r.node_id, start_week=a, base_a=base_a, b=b, max_top_day_share=float(mx) if mx == mx else np.nan,
                   single_day=bool(mx >= SINGLE_DAY) if mx == mx else False, driver=None, driver_share_of_rise=np.nan)
        pg = node_pages.get(r.node_id)
        if pg is not None and len(pg):
            rows = np.array([tpos[t] for t in pg.index])
            ia, i0, ib = (base_a - T.DAY0).days, (a - T.DAY0).days, (b - T.DAY0).days
            lo = max(ia, 0)
            Bm = block(V, rows, lo, i0)
            if ia < 0:                                            # days before the data count as 0 views (interest/09 reindexes with 0)
                Bm = np.hstack([np.zeros((len(rows), -ia)), Bm])
            Wn = block(V, rows, i0, ib + 1)
            rise = pg.to_numpy() * (Wn.sum(axis=1) - np.median(Bm, axis=1) * Wn.shape[1])
            k = int(np.argmax(rise))
            pos = rise[rise > 0].sum()
            rec.update(driver=pg.index[k] if rise[k] > 0 else None, driver_share_of_rise=float(rise[k] / pos) if pos > 0 else np.nan)
        out.append(rec)
    return pd.DataFrame(out)


def stage_shifts(P, a):
    w = pd.read_parquet(P / f'series_weekly_{a.series}.parquet')
    w['week'] = pd.to_datetime(w.week)
    X, weekly = detect(w)
    if X.empty:
        raise SystemExit('no rise was detected in any theme')
    Apg = T.read_assign(P, 'pages')
    pairs, titles, V = page_daily(P, a.series, Apg)
    Dv = drivers(X, w, pairs, titles, V)
    X = X.merge(Dv, on=['level', 'node_id', 'start_week'], how='left')
    X['series'] = a.series
    T.write_parquet(X, P / f'shifts_{a.series}.parquet')
    T.write_parquet(Dv, P / f'shift_drivers_{a.series}.parquet')
    tested = X[X.main_set & (pd.to_datetime(X.start_week) >= pd.Timestamp(S.study_start + '-01'))]
    tab = X.groupby(['level', 'label', 'seasonal']).size().rename('rises').reset_index()
    lines = [f'# Test F, step 24, rises of {a.series} ({P.tag()}; interest data only)', '',
             f'- written {pd.Timestamp.now():%Y-%m-%d %H:%M}; interest settings record `{SI["sha256"][:12]}`',
             f'- themes with a weekly series: narrow {w[w.level == 3].node_id.nunique()}, middle {w[w.level == 2].node_id.nunique()}; '
             f'rises found {len(X):,}; in the main set (labelled, not seasonal) {int(X.main_set.sum()):,}; of them from {S.study_start}: {len(tested):,}',
             f'- one-day flag (a day >= 50% of a weekly sum in the first weeks): {int(X.single_day.fillna(False).sum()):,}; rises with a driver page: '
             f'{int(Dv.driver.notna().sum()):,} (the desktop check needs 22_download_views.py --desktop {a.series})', ''] + T.md_table(tab)
    T.write_text('\n'.join(lines) + '\n', P.report(f'testF_24_G2_{a.series}_shifts.md'))
    T.log(f'rises: {len(X):,} (main set {int(X.main_set.sum()):,}); drivers {int(Dv.driver.notna().sum()):,}')


# ---------------------------------------------------------------- stage 2: effects
def desktop_flags(P, X, series):
    f = P / f'desktop_{series}.parquet'
    if not f.exists():
        return None
    Dk = pd.read_parquet(f)
    Dk['date'] = pd.to_datetime(Dk.date)
    g = {k: v.set_index('date') for k, v in Dk.groupby(['driver', 'base_a', 'b'])}
    share_b, share_r = [], []
    for r in X.itertuples():
        k = (r.driver, pd.Timestamp(r.base_a), pd.Timestamp(r.b)) if isinstance(r.driver, str) else None
        d = g.get(k) if k else None
        if d is None:
            share_b.append(np.nan); share_r.append(np.nan); continue
        a = pd.Timestamp(r.start_week)
        dk, al = d.desktop.astype(float), d.all_access.astype(float)
        bd, ba = dk[dk.index < a], al[al.index < a]
        wd, wa = dk[dk.index >= a], al[al.index >= a]
        rise_d = wd.sum() - bd.median() * len(wd)
        rise_a = wa.sum() - ba.median() * len(wa)
        share_b.append(float(bd.sum() / ba.sum()) if ba.sum() else np.nan)
        share_r.append(float(rise_d / rise_a) if rise_a > 0 else np.nan)
    X = X.copy()
    X['desktop_share_base'], X['desktop_share_rise'] = share_b, share_r
    X['desktop_rise'] = (X.desktop_share_rise >= DESK_RISE) & ((X.desktop_share_rise - X.desktop_share_base) >= DESK_GAP)
    have = set(g)
    X['desktop_checked'] = [isinstance(d, str) and (d, pd.Timestamp(a_), pd.Timestamp(b_)) in have for d, a_, b_ in zip(X.driver, X.base_a, X.b)]
    return X


def load_panel(P, name):
    if name == 'a':
        P3 = IO.Paths()
        panel, nodes, overlap = IO.load_panels(P3), IO.read_parquet(P3.nodes), IO.read_parquet(P3.overlap)
        if P.mock:
            panel = T.shuffle_panel(panel, P.mock_seed + 3)
    else:
        panel = pd.read_parquet(P / f'panel_{name}.parquet')
        nodes = pd.read_parquet(P / f'nodes_{name}.parquet')
        overlap = pd.read_parquet(P / f'overlap_{name}.parquet')
        meta = json.loads((P / 'panels_meta.json').read_text())
        if P.mock and not meta['panels'][name].get('shuffled'):
            raise SystemExit(f'mock world: panel {name} was not shuffled when written')
    return panel, nodes, overlap


def inject(panel, Xn, lift):
    """Mock worlds only: add `lift` to the log share of each tested lasting rise's theme in months 0 to +2 (all formats)."""
    p = panel.copy()
    t = Xn[Xn.labelled & Xn.quality_ok & (Xn.duration_class == 'sustained') & Xn.level.isin(S.levels_tested) & ~Xn.seasonal
           & (Xn.m0 >= mi_from_ym(S.study_start))]
    key = pd.MultiIndex.from_frame(p[['level', 'node_id', 'mi']])
    want = sorted({(lv, nid, int(m0) + k) for lv, nid, m0 in zip(t.level, t.node_id, t.m0)
                   for k in range(S.window_primary[0], S.window_primary[1] + 1)})
    hit = key.isin(pd.MultiIndex.from_tuples(want)) if want else np.zeros(len(p), bool)
    p.loc[hit, 'log_share'] = p.loc[hit, 'log_share'] + lift
    return p, int(hit.sum())


def both_levels(R, n_boot):
    rows = []
    ok = R[R.sc_ok == True]  # noqa: E712
    for (an, src), g0 in ok.groupby(['analysis', 'source']):
        for cls in ('all', 'sustained', 'intermediate', 'fading'):
            g = g0 if cls == 'all' else g0[g0.duration_class == cls]
            if g.empty:
                continue
            r = dict(analysis=an, source=src, level='both', format='all', duration_class=cls, tests=len(g), shifts=g.shift_id.nunique(),
                     categories=g.node_id.nunique())
            for col in ('sc_effect_p', 'es_effect_p', 'sc_effect_s', 'es_effect_s'):
                v = g.dropna(subset=[col])
                r[f'{col}_mean'] = float(v[col].mean()) if len(v) else np.nan
                if v.node_id.nunique() >= 2:
                    bs = M.cluster_bootstrap(v.reset_index(drop=True), 'node_id', lambda d, c=col: float(d[c].mean()), n_boot, S.boot_seed)
                    r[f'{col}_ci_low'], r[f'{col}_ci_high'] = M.percentile_ci(bs)
            rows.append(r)
    return pd.DataFrame(rows)


def paired_bc(Rb, Rc, n_boot):
    """G4 (descriptive): panel b minus panel c on the same rise-by-format tests (both with a synthetic control), main analysis; mean
    difference with the bootstrap clustered by theme, per level, both levels, and duration class."""
    k = ['shift_id', 'format']
    cols = k + ['node_id', 'level', 'duration_class', 'analysis', 'sc_effect_p', 'es_effect_p']
    m = Rb[Rb.sc_ok][cols].merge(Rc[Rc.sc_ok][k + ['sc_effect_p', 'es_effect_p']], on=k, suffixes=('_b', '_c'))
    m = m[m.analysis == 'main']
    m['d_sc'] = m.sc_effect_p_b - m.sc_effect_p_c
    m['d_es'] = m.es_effect_p_b - m.es_effect_p_c
    rows = []
    for lv in ('narrow', 'middle', 'both'):
        for cls in ('sustained', 'fading', 'all'):
            g = m if lv == 'both' else m[m.level == lv]
            g = g if cls == 'all' else g[g.duration_class == cls]
            r = dict(level=lv, duration_class=cls, tests=len(g), categories=g.node_id.nunique())
            for c in ('d_sc', 'd_es'):
                v = g.dropna(subset=[c]).reset_index(drop=True)
                r[f'{c}_mean'] = float(v[c].mean()) if len(v) else np.nan
                if v.node_id.nunique() >= 2:
                    bs = M.cluster_bootstrap(v, 'node_id', lambda d, c_=c: float(d[c_].mean()), n_boot, S.boot_seed)
                    r[f'{c}_ci_low'], r[f'{c}_ci_high'] = M.percentile_ci(bs)
            rows.append(r)
    return pd.DataFrame(rows)


def chapter6_rows(P):
    """The stored Chapter 6 result (concept pages): pooled rows of data/db/study3/pooled_effects.csv. Not read in a mock world."""
    if P.mock:
        return pd.DataFrame([dict(panel='chapter6_concept_pages', note='not read in a mock world')])
    C6 = pd.read_csv(STUDY3 / 'pooled_effects.csv')
    C6 = C6[(C6.analysis == 'main') & (C6.source == 'wikipedia') & (C6.format == 'all') & C6.level.isin(['narrow', 'middle'])]
    return C6.assign(panel='chapter6_concept_pages')


def stage_effects(P, a):
    t0 = time.time()
    X = pd.read_parquet(P / f'shifts_{a.series}.parquet')
    X['start_week'] = pd.to_datetime(X.start_week)
    Xd = desktop_flags(P, X, a.series)
    if Xd is None and not a.no_desktop_flag:
        raise SystemExit(f'desktop_{a.series}.parquet not found: run 22_download_views.py --desktop {a.series}, or pass --no-desktop-flag '
                         '(the report then says that the desktop_only flag was not applied)')
    desktop_note = 'applied' if Xd is not None else 'NOT APPLIED (--no-desktop-flag)'
    if Xd is not None:
        unchecked = int((Xd.driver.notna() & ~Xd.desktop_checked).sum())
        if unchecked and not P.mock and not a.no_desktop_flag:
            raise SystemExit(f'{unchecked} rises with a driver page have no desktop views in desktop_{a.series}.parquet; rerun '
                             f'22_download_views.py --desktop {a.series} (or pass --no-desktop-flag)')
        desktop_note = f'applied ({int(Xd.desktop_checked.sum()):,} rises checked, {unchecked:,} without desktop data, '
        desktop_note += f'{int(Xd.desktop_rise.fillna(False).sum()):,} flagged)'
    X = Xd if Xd is not None else X.assign(desktop_rise=False)
    flags = []
    for sd, dr in zip(X.single_day.fillna(False), X.desktop_rise.fillna(False)):
        flags.append(','.join(f for f, on in (('one_day', sd), ('desktop_only', dr)) if on))
    X['quality_flag'] = flags
    X['quality_ok'] = X.quality_flag == ''
    Xn = normalise_shifts(X.drop(columns=[c for c in ('m0',) if c in X.columns]), S)
    Xn['series'] = a.series
    # shifts for the donor and placebo-year screens
    screen = [Xn]
    if a.screen in ('new+gdelt', 'all'):
        G = load_shifts(IO.Paths(), S)
        screen.append(G[G.source == 'gdelt'] if a.screen == 'new+gdelt' else G)
    Xs = pd.concat(screen, ignore_index=True)
    n_boot = S.boot_n if a.boot is None else a.boot
    T.mock_only(P, a.boot is not None, '--boot')
    T.mock_only(P, a.mock_inject, '--mock-inject')
    sfx = '_with_flagged' if a.include_flagged else ''
    tests, pooled_all, summ = {}, [], dict(series=a.series, screen=a.screen, desktop_flag=desktop_note, include_flagged=a.include_flagged,
                                              boot=n_boot, mock=P.mock, mock_inject=a.mock_inject, panels={})
    for name in a.panels.split(','):
        panel, nodes, overlap = load_panel(P, name)
        if a.mock_inject:
            panel, nh = inject(panel, Xn, a.mock_inject)
            summ['panels'].setdefault(name, {})['injected_cells'] = nh
        ctx = A3.Context(panel, nodes, overlap, Xs, S)
        s, items = E12.plan(Xn, ctx, a.include_flagged)
        res = A3.run_parallel(A3.test_unit, ctx, items, a.workers)
        Tt = pd.DataFrame(res)
        R = s[E12.SHIFT_COLS].merge(Tt.drop(columns=['broad_id', 'label']), on=['level', 'node_id', 'm0'], how='inner')
        R['broad_id'] = R.node_id.map(ctx.broad)
        R['analysis'] = np.where(R.seasonal, 'seasonal', 'main')
        R['sc_ok'] = R.sc_ok.fillna(False).astype(bool)
        R = E12.add_q(R)
        R['panel'] = name
        tests[name] = R
        T.write_parquet(R.drop(columns=[c for c in R.columns if R[c].dtype == object and R[c].map(lambda v: isinstance(v, (list, dict))).any()]),
                        P / f'g2_{a.series}_tests_{name}{sfx}.parquet')
        Pt = pd.concat([E12.pooled(R, n_boot), both_levels(R, n_boot)], ignore_index=True)
        Pt.insert(0, 'panel', name)
        pooled_all.append(Pt)
        t = R[R.sc_ok]
        summ['panels'].setdefault(name, {}).update(
            rises_tested=int(s.shift_id.nunique()), tests=len(R), tests_ok=int(R.sc_ok.sum()), formats=sorted(R.format.unique()),
            skips=R.skip.replace('', 'tested').value_counts().to_dict(),
            single_p_lt_alpha=int(t.significant_single.sum()), bh_detected=int(t.detected_bh.sum()))
        T.log(f'panel {name}: {s.shift_id.nunique():,} rises, {len(R):,} tests ({int(R.sc_ok.sum()):,} with a synthetic control); {time.time() - t0:.0f}s')
    PT = pd.concat(pooled_all + [chapter6_rows(P)], ignore_index=True)
    PT.to_csv(P / f'g2_{a.series}_pooled{sfx}.csv', index=False)
    if 'b' in tests and 'c' in tests:
        BC = paired_bc(tests['b'], tests['c'], n_boot)
        BC.to_csv(P / f'g2_{a.series}_paired_b_minus_c{sfx}.csv', index=False)
        summ['g4_paired_b_minus_c'] = BC.to_dict('records')
    # decision (panel a, lasting rises, months 0 to +2)
    dec = {}
    pa = PT[(PT.panel == 'a') & (PT.analysis == 'main') & (PT.format == 'all') & (PT.duration_class == 'sustained')]
    for lv in ('narrow', 'middle', 'both'):
        r = pa[pa.level == lv]
        for meth, col in (('synthetic_control', 'sc_effect_p'), ('own_trend', 'es_effect_p')):
            if len(r) and f'{col}_ci_low' in r:
                lo, hi, m = (float(r[f'{col}_ci_low'].iloc[0]), float(r[f'{col}_ci_high'].iloc[0]), float(r[f'{col}_mean'].iloc[0]))
                dec[f'{lv}|{meth}'] = dict(effect=m, ci_low=lo, ci_high=hi, interval_above_0=bool(lo > 0), tests=int(r.tests.iloc[0]),
                                           categories=int(r.categories.iloc[0]))
    summ['decision_G2_panel_a_lasting'] = dec
    summ['shifts'] = dict(total=len(Xn), labelled=int(Xn.labelled.sum()), quality_flags=Xn.quality_flag.replace('', 'clean').value_counts().to_dict(),
                          by_class=Xn[Xn.labelled].groupby('duration_class').size().to_dict(), screen_rises=len(Xs))
    summ['seconds'] = round(time.time() - t0)
    summ['peak_gb'] = round(T.peak_gb(), 2)
    T.write_json(summ, P / f'g2_{a.series}_summary{sfx}.json')
    write_report(P, a, PT, summ, sfx)
    T.log(f'done in {summ["seconds"]}s; peak memory {summ["peak_gb"]} GB')


def write_report(P, a, PT, summ, sfx):
    pct = lambda x: '' if x != x else f'{100 * (np.exp(x) - 1):+.1f}%'    # noqa: E731
    L = [f'# Test F, check G2: borrowing after rises of the AI theme series {a.series} ({P.tag()})' + (' (robustness run with flagged rises)' if sfx else ''), '',
         f'- written {pd.Timestamp.now():%Y-%m-%d %H:%M}; Study 3 record `{S.sha256[:12]}`; bootstrap {summ["boot"]} resamples, seed {S.boot_seed}',
         f'- donor and placebo-year screen: {a.screen}; desktop flag {summ["desktop_flag"]}; run time {summ["seconds"]}s',
         f'- rises: {summ["shifts"]}', '']
    if P.mock:
        L += ['**MOCK WORLD: random themes and borrowing shuffled across themes and months; these numbers mean nothing about real borrowing.**'
              + (f' A lift of {a.mock_inject} was injected after every tested lasting rise (wiring check).' if a.mock_inject else ''), '']
    L += ['## Decision (panel a, rises of 4 weeks or more, mean effect in months 0 to 2, log share; 95% interval)', '']
    for k, d in summ['decision_G2_panel_a_lasting'].items():
        lv, meth = k.split('|')
        L.append(f'- {lv}, {meth.replace("_", " ")}: {d["effect"]:+.3f} [{d["ci_low"]:+.3f}, {d["ci_high"]:+.3f}] ({pct(d["effect"])}), '
                 f'{d["tests"]} tests in {d["categories"]} themes; interval above 0: {"yes" if d["interval_above_0"] else "no"}')
    L += ['', '## Pooled effects by panel (all formats; months 0 to 2; sc = synthetic control, es = own trend)', '']
    cols = ['panel', 'level', 'duration_class', 'tests', 'categories', 'sc_effect_p_mean', 'sc_effect_p_ci_low', 'sc_effect_p_ci_high',
            'es_effect_p_mean', 'es_effect_p_ci_low', 'es_effect_p_ci_high']
    sel = PT[(PT.get('analysis') == 'main') & (PT.get('format') == 'all') & PT.duration_class.isin(['sustained', 'fading', 'all'])] if 'analysis' in PT else PT
    sel = sel.reindex(columns=cols)
    for c in ('tests', 'categories'):
        sel[c] = sel[c].astype('Int64').astype(str)
    L += T.md_table(sel)
    L += ['', 'panel chapter6_concept_pages = the stored Chapter 6 result (hand-checked concept pages), for comparison.', '']
    if summ.get('g4_paired_b_minus_c'):
        L += ['## G4: panel b minus panel c on the same rises and formats (descriptive)', '']
        L += T.md_table(pd.DataFrame(summ['g4_paired_b_minus_c']).reindex(columns=['level', 'duration_class', 'tests', 'categories', 'd_sc_mean', 'd_sc_ci_low',
                                                                                  'd_sc_ci_high', 'd_es_mean', 'd_es_ci_low', 'd_es_ci_high']))
        L.append('')
    L += ['## Tests per panel', '']
    for k, v in summ['panels'].items():
        L.append(f'- panel {k}: {v}')
    T.write_text('\n'.join(L) + '\n', P.report(f'testF_24_G2_{a.series}{sfx}.md'))


def main():
    ap = T.add_root_arg(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    ap.add_argument('--series', choices=['S1', 'S2', 'S2C'], required=True)
    ap.add_argument('--stage', choices=['shifts', 'effects', 'all'], default='all')
    ap.add_argument('--panels', default='a,b,c')
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--screen', choices=['new+gdelt', 'new', 'all'], default='new+gdelt')
    ap.add_argument('--include-flagged', action='store_true')
    ap.add_argument('--no-desktop-flag', action='store_true')
    ap.add_argument('--boot', type=int, default=None, help='mock worlds only: bootstrap resamples')
    ap.add_argument('--mock-inject', type=float, default=0.0, help='mock worlds only: lift added after each tested lasting rise')
    a = ap.parse_args()
    a.workers = max(1, min(a.workers, 4))
    P = T.Paths(a.root)
    T.be_nice(10)
    T.log(f'{P.tag()}; series {a.series}; stage {a.stage}')
    if a.stage in ('shifts', 'all'):
        stage_shifts(P, a)
    if a.stage in ('effects', 'all'):
        stage_effects(P, a)


if __name__ == '__main__':
    main()
