#!/usr/bin/env python3
"""Test F, addendum h: the concept-pages-only test, scoring and report.

Settings: prereg/addenda_wiki_led/2026-10-21_h_concept_pages.json (fixed 21 Oct 2026 21:07, public on GitHub at 21:08 before any result).
Reads the outputs of 21 (--series S2C), 24 (--series S2C, with and without --include-flagged) and 25 (--phase chronos --variants aic2).
H1 (decision): panel a, both levels pooled, synthetic control, months 0 to 2, rises of 4 weeks or more: 95% interval above 0; called close
to the hand-checked level if that interval contains 0.088 (the smaller Chapter 6 per-level estimate). Rows beside Chapter 6 and S2.
H2 (descriptive): Chronos-2 + S2C (chronos2_aic2) against Chronos-2 alone, the concept-page covariate (chronos2_cur) and Chronos-2 + S2,
paired MAE ratios with the benchmark's category bootstrap; the Wikipedia-only ranking of S2C (the Test C measure) against the concept
pages and S2. The Test F outputs of 25 are not touched (this script writes h_* files only).
Outputs: h_g3_pairs.csv, h_g3_wikionly.csv, h_summary.json; report data/reports/testF_h_concept_results.md.
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/29_H_concept.py [--root DIR]
"""
import sys, json, time, pathlib, argparse, importlib.util
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _testf_analysis as T

HERE = pathlib.Path(__file__).resolve().parent
ADD_H = T.ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-21_h_concept_pages.json'
CH6_MIN = 0.088                                                  # the smaller Chapter 6 per-level estimate (narrow 0.088, middle 0.105)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pct(x):
    return f'{100 * (np.exp(x) - 1):+.1f}%'


def g2_rows(P, series, sfx=''):
    f = P / f'g2_{series}_pooled{sfx}.csv'
    if not f.exists():
        return None
    d = pd.read_csv(f)
    return d[(d.analysis == 'main') & (d.format == 'all')]


def h1(P):
    d = g2_rows(P, 'S2C')
    if d is None:
        raise SystemExit('g2_S2C_pooled.csv not found: run 24_G2_matchmaking.py --series S2C first')
    dec = d[(d.panel == 'a') & (d.level == 'both') & (d.duration_class == 'sustained')].iloc[0]
    out = dict(sc=float(dec.sc_effect_p_mean), lo=float(dec.sc_effect_p_ci_low), hi=float(dec.sc_effect_p_ci_high),
               es=float(dec.es_effect_p_mean), es_lo=float(dec.es_effect_p_ci_low), es_hi=float(dec.es_effect_p_ci_high),
               tests=int(dec.tests), categories=int(dec.categories))
    out['interval_above_0'] = bool(out['lo'] > 0)
    out['contains_chapter6_level'] = bool(out['lo'] <= CH6_MIN <= out['hi'])
    fl = g2_rows(P, 'S2C', '_with_flagged')
    if fl is not None:
        r = fl[(fl.panel == 'a') & (fl.level == 'both') & (fl.duration_class == 'sustained')].iloc[0]
        out['with_flagged'] = dict(sc=float(r.sc_effect_p_mean), lo=float(r.sc_effect_p_ci_low), hi=float(r.sc_effect_p_ci_high))
    summ = json.loads((P / 'g2_S2C_summary.json').read_text()) if (P / 'g2_S2C_summary.json').exists() else {}
    return out, d, summ


def h2(P):
    G3 = load_module('g3', HERE / '25_G3_forecast.py')
    EV = G3.load_module('bm03', G3.BENCH / '03_evaluate.py')
    s = G3.main_rows()
    for v in ('chronos2_ais2', 'chronos2_aic2'):
        f = P / 'chronos2_out' / f'{v}_forecasts.parquet'
        if not f.exists():
            raise SystemExit(f'{f.name} not found: run 25_G3_forecast.py --phase chronos --variants {v.split("_")[1]}')
        F = pd.read_parquet(f)
        F = F[F.h == 1][['group', 'format', 'level', 'node_id', 'origin_mi', 'y_hat']].rename(columns={'y_hat': v})
        s = s.merge(F, on=['group', 'format', 'level', 'node_id', 'origin_mi'], how='left')
        if s[v].isna().any():
            raise SystemExit(f'{v}: {int(s[v].isna().sum()):,} main rows have no forecast')
    pipes = ['naive', 'chronos2', 'chronos2_cur', 'chronos2_nli', 'chronos2_ais2', 'chronos2_aic2']
    c = EV.Cmp(s, pd.Series(True, index=s.index), pipes, 'H2', nboot=EV.NBOOT)
    if c.dropped or c.rows_n != 36081:
        raise SystemExit(f'the scoring class dropped pipelines or rows: {c.dropped}, {c.rows_n} rows')
    LT = c.level_table(with_mcs=False).join(c.rise_table(with_mcs=False))
    LT.index.name = 'pipeline'
    pairs = [('chronos2', 'chronos2_aic2'), ('chronos2_cur', 'chronos2_aic2'), ('chronos2_ais2', 'chronos2_aic2')]
    PR = pd.DataFrame([c.pair(x, y) for x, y in pairs])
    PR.to_csv(P / 'h_g3_pairs.csv', index=False)
    s['c'] = s.y_true - s.y_t
    M = pd.read_parquet(P / 'series_monthly.parquet')
    MC = pd.read_parquet(G3.MCOV)
    xs = {}
    for name, (frame, col) in {'S2C (AI concept pages)': (M, 'aic2_wlog'), 'S2 (AI pages)': (M, 'ais2_wlog'), 'concept pages': (MC, 'cur_wlog')}.items():
        xn = 'x_' + col
        s = G3.attach_x(s, G3.changes(frame, col), xn)
        xs[name] = xn
    W3, D3 = G3.test_c_scores(s, list(xs.values()))
    WO = pd.DataFrame([dict(series=k, **W3[v]) for k, v in xs.items()])
    WO.to_csv(P / 'h_g3_wikionly.csv', index=False)
    wpairs = [G3.paired(D3, W3, xs[b_], xs[a_]) | dict(base=b_, other=a_) for a_, b_ in
              (('S2C (AI concept pages)', 'concept pages'), ('S2C (AI concept pages)', 'S2 (AI pages)'))]
    return LT, PR, WO, wpairs


def main():
    ap = T.add_root_arg(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    a = ap.parse_args()
    P = T.Paths(a.root)
    T.be_nice(10)
    t0 = time.time()
    sha = T.sha256_file(ADD_H)
    d1, D, summ = h1(P)
    S2 = g2_rows(P, 'S2')
    LT, PR, WO, wpairs = h2(P)
    info = json.loads((P / 'series_info.json').read_text()).get('S2C', {}) if (P / 'series_info.json').exists() else {}
    res = dict(addendum='2026-10-21_h_concept_pages.json', sha256=sha, H1=d1, series=info, H2_pairs=PR.to_dict('records'),
               H2_wikionly=WO.to_dict('records'), H2_wikionly_pairs=wpairs, g2_panels={k: v for k, v in summ.get('panels', {}).items()},
               seconds=round(time.time() - t0))
    T.write_json(res, P / 'h_summary.json')
    L = [f'# Test F, addendum h: the AI\'s concept pages only ({P.tag()})', '',
         f'- written {pd.Timestamp.now():%Y-%m-%d %H:%M}; record prereg/addenda_wiki_led/2026-10-21_h_concept_pages.json (SHA-256 {sha[:12]}..., '
         'fixed 21 Oct 21:07, public on GitHub 21:08, before any result)',
         f'- series S2C: {info.get("pages", "?"):,} concept pages with a theme of confidence 2 or 3, {info.get("pairs", "?"):,} page-theme pairs, '
         f'complete: {info.get("complete")}', '',
         '## H1: borrowing after lasting rises of the concept-page series (decision fixed in advance)', '',
         f'- panel a, both levels pooled, synthetic control, months 0 to 2, rises of 4 weeks or more: {d1["sc"]:.3f} [{d1["lo"]:.3f}, {d1["hi"]:.3f}] '
         f'({pct(d1["sc"])}), {d1["tests"]} tests in {d1["categories"]} themes; interval above 0: {"yes" if d1["interval_above_0"] else "no"}',
         f'- own trend: {d1["es"]:.3f} [{d1["es_lo"]:.3f}, {d1["es_hi"]:.3f}] ({pct(d1["es"])})',
         f'- close to the hand-checked level (interval contains {CH6_MIN}): {"yes" if d1["contains_chapter6_level"] else "no"}']
    if 'with_flagged' in d1:
        w = d1['with_flagged']
        L += [f'- with flagged rises included: {w["sc"]:.3f} [{w["lo"]:.3f}, {w["hi"]:.3f}] ({pct(w["sc"])})']
    L += ['', '## Beside S2 (all AI pages) and Chapter 6 (hand-checked concept pages), rises of 4 weeks or more', '',
          '| series | panel | level | tests | themes | synthetic control | own trend |', '| --- | --- | --- | --- | --- | --- | --- |']
    for nm, X in (('S2C concept pages', D), ('S2 all pages', S2)):
        if X is None:
            continue
        for r in X[X.duration_class == 'sustained'].sort_values(['panel', 'level']).itertuples():
            if r.panel == 'chapter6_concept_pages' and nm != 'S2C concept pages':
                continue
            lab = 'Chapter 6 concept pages' if r.panel == 'chapter6_concept_pages' else nm
            L.append(f'| {lab} | {"a" if r.panel == "chapter6_concept_pages" else r.panel} | {r.level} | {int(r.tests)} | {int(r.categories)} | '
                     f'{r.sc_effect_p_mean:.3f} [{r.sc_effect_p_ci_low:.3f}, {r.sc_effect_p_ci_high:.3f}] | {r.es_effect_p_mean:.3f} [{r.es_effect_p_ci_low:.3f}, {r.es_effect_p_ci_high:.3f}] |')
    L += ['', 'Rises of 1 or 2 weeks (S2C):', '']
    for r in D[(D.duration_class == 'fading') & (D.panel != 'chapter6_concept_pages')].sort_values(['panel', 'level']).itertuples():
        L.append(f'- panel {r.panel}, {r.level}: synthetic control {r.sc_effect_p_mean:.3f} [{r.sc_effect_p_ci_low:.3f}, {r.sc_effect_p_ci_high:.3f}], '
                 f'own trend {r.es_effect_p_mean:.3f} [{r.es_effect_p_ci_low:.3f}, {r.es_effect_p_ci_high:.3f}] ({int(r.tests)} tests)')
    for k, v in res['g2_panels'].items():
        L.append(f'- panel {k}: {v.get("rises_tested", "?"):,} rises tested in {v.get("tests", 0):,} tests ({v.get("tests_ok", 0):,} with a synthetic control); '
                 f'single one-sided p < 0.05: {v.get("single_p_lt_alpha")}; Benjamini-Hochberg q < 0.10: {v.get("bh_detected")}')
    L += ['', '## H2: forecasts (descriptive)', '', '| pipeline | AvgRelMAE | rank correlation |', '| --- | --- | --- |']
    for p_, r in LT.iterrows():
        L.append(f'| {p_} | {r.AvgRelMAE:.4f} [{r.ci_lo:.4f}, {r.ci_hi:.4f}] | {r.rho:.4f} |' if 'rho' in LT else f'| {p_} | {r.AvgRelMAE:.4f} | |')
    L += ['', 'Paired (MAE ratio other / base; below 1 = the other is better):']
    for r in PR.itertuples():
        L.append(f'- {r.other} against {r.base}: {r.mae_ratio:.4f} [{r.mae_lo:.4f}, {r.mae_hi:.4f}] ({100 * (r.mae_ratio - 1):+.2f}%)')
    L += ['', 'Wikipedia-only ranking, no fitting (the Test C measure):'] + \
         [f'- {r.series}: {r.rho:.4f} [{r.lo:.4f}, {r.hi:.4f}]' for r in WO.itertuples()] + \
         [f'- {p["other"]} minus {p["base"]}: {p["diff"]:+.4f} [{p["lo"]:+.4f}, {p["hi"]:+.4f}]' for p in wpairs]
    T.write_text('\n'.join(L) + '\n', P.report('testF_h_concept_results.md'))
    T.log(f'wrote testF_h_concept_results.md and h_summary.json in {res["seconds"]}s')


if __name__ == '__main__':
    main()
