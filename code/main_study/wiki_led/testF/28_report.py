#!/usr/bin/env python3
"""Test F, step 28: one report of every Test F number, in plain English: data/reports/testF_results.md and testF_results.json.

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json. Reads only the outputs of steps 20 to 27 (and the stored Chapter 6 row
copied there by step 24); computes nothing new except shares and percentages. Parts that have not been run are named as missing.
In a mock world the files go into its reports/ folder and every section says MOCK.
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/28_report.py [--root DIR] [--series S2|S1]
"""
import sys, json, pathlib, argparse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _testf_analysis as T


def jload(P, name):
    f = P / name
    return json.loads(f.read_text()) if f.exists() else None


def csv(P, name):
    f = P / name
    return pd.read_csv(f) if f.exists() else None


def pct_log(x):
    return '' if x is None or x != x else f'{100 * (np.exp(x) - 1):+.1f}%'


def num(x, nd=3):
    return 'n/a' if x is None or (isinstance(x, float) and x != x) else (f'{x:,}' if isinstance(x, (int, np.integer)) else f'{x:.{nd}f}')


def ci(m, lo, hi, nd=3):
    return f'{num(m, nd)} [{num(lo, nd)}, {num(hi, nd)}]'


CHOICES = [
    ('20', 'A line with any code outside the guide (or a malformed token) is invalid as a whole and is re-asked; an item without an answer line '
           'is re-asked too; after the one re-ask a still invalid line is dropped. Codes are read case-insensitively; spaces for tabs are accepted; a '
           'repeated code keeps its first confidence; more than 3 codes keep the first 3. The second pass has no re-ask; judge codes outside the guide are dropped.'),
    ('21', 'S1 has no data before 2016-01-01 and a week with a missing top-500 day is a partial week for S1; S2 uses only page-theme pairs of '
           'confidence 2 or 3; ties at the 40,000-page cut go by top-500 views, then title; the monthly series follow the benchmark rule (monthly_log).'),
    ('22', 'Gap 0.34 s over 4 threads (at most 2.94 requests a second, under the limit of 3); a day missing from an answer is 0 views; the downloader also '
           'refuses while a job named with view, text or download runs.'),
    ('23', 'A work\'s middle weight in panel b is the sum of its narrow weights; months with no loan of the 20,000 works are not usable; works without a '
           'theme stay in the denominator.'),
    ('24', 'The weekly weighted views are the volume for the minimum-volume rule; the driver page is the page with the largest weighted rise; '
           'title_confusion is not applied; donors and placebo years are screened with the new series\' rises and the stored GDELT rises; a row '
           'pooling both levels is added.'),
    ('25', 'Rows without a value of the monthly change get 0 in the no-fitting ranking (as in Test C); G4 uses the main rows\' keys where all three '
           'panels have the change.'),
    ('26', 'Scores at the narrow level (routing pairs on narrow nodes) and the middle level; AI pairs of all confidences and of confidence 2 or 3; '
           'methods compared on the pages every method could route; page-bootstrap intervals.'),
    ('27', 'First-theme agreement and overlap among items both passes put in a theme; none agreement with Cohen\'s kappa over all items.'),
]


def main():
    ap = T.add_root_arg(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    ap.add_argument('--series', default=None, help='which G2 run to report (default: S2 if it exists, else S1)')
    a = ap.parse_args()
    P = T.Paths(a.root)
    out, L = {'mock': P.mock, 'written': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}, []
    L += ['# Test F: AI matchmaking of Wikipedia pages and books into the same themes, results', '',
          f'Written {out["written"]} from the outputs of code/main_study/wiki_led/testF/ (steps 20 to 27). Settings: '
          'prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (fixed 21 Oct 2026, 01:55, before any sorting).', '']
    if P.mock:
        L += ['**MOCK WORLD. The themes are random and the borrowing was shuffled across themes and months. These numbers test the code and '
              'say nothing about real borrowing.**', '']
    # ---------------- sorting
    ps = jload(P, 'parse_summary.json')
    out['sorting'] = ps
    L += ['## 1. The sorting', '']
    if ps:
        for k in ('pages', 'books'):
            s = ps.get(k)
            if not s:
                L.append(f'- {k}: not parsed'); continue
            fin = s['final']
            n = s['items_in_key']
            L.append(f'- {k.capitalize()}: {n:,} in the key; with at least one theme {fin.get("themes", 0):,} ({fin.get("themes", 0) / n:.1%}), none '
                     f'{fin.get("none", 0):,}, still invalid after the re-ask (dropped) {fin.get("dropped_invalid", 0):,}, waiting for the re-ask '
                     f'{fin.get("invalid", 0) + fin.get("missing", 0):,}, not sorted yet {fin.get("not_sorted", 0):,}. Theme pairs {s["pairs"]:,} '
                     f'(confidence 3, 2, 1: {s["pairs_by_conf"].get("3", s["pairs_by_conf"].get(3, 0)):,}, {s["pairs_by_conf"].get("2", s["pairs_by_conf"].get(2, 0)):,}, '
                     f'{s["pairs_by_conf"].get("1", s["pairs_by_conf"].get(1, 0)):,}).')
        it = P / 'items_pages.parquet'
        if it.exists():
            I = pd.read_parquet(it)
            cov = I[I.status.isin(['themes', 'none'])].groupby('set').status.apply(lambda s: float((s == 'themes').mean())).to_dict()
            out['coverage_check'] = cov
            L.append(f'- Coverage check (pages sorted, share given a theme): universe {cov.get("universe", float("nan")):.1%}, one-day sample '
                     f'{cov.get("sample1day", float("nan")):.1%}. The one-day sample is never used in G2 to G4.')
    else:
        L.append('- not run (step 20)')
    # ---------------- reliability
    rs = jload(P, 'reliability_summary.json')
    out['reliability'] = rs
    L += ['', '## 2. Two independent sorting passes', '']
    if rs and any(isinstance(rs.get(k), dict) and rs[k].get('items_both_usable') for k in ('pages', 'books')):
        for k in ('pages', 'books'):
            r = rs.get(k)
            if not r or not r.get('items_both_usable'):
                L.append(f'- {k}: no second pass'); continue
            L.append(f'- {k.capitalize()} ({r["items_both_usable"]:,} in both passes): same first theme {r["first_theme_same"]:.1%} (same middle theme '
                     f'{r["first_theme_same_middle"]:.1%}), at least one shared theme {r["any_overlap"]:.1%}, agreement on none or some '
                     f'{r["none_agreement"]:.1%} (kappa {r["none_kappa"]:.2f}); both none {r["both_none"]}, only the first none {r["first_none_only"]}, '
                     f'only the second none {r["second_none_only"]}.')
    else:
        L.append('- not run (step 27)')
    # ---------------- G1
    g1 = jload(P, 'g1_summary.json')
    G1 = csv(P, 'g1_scores.csv')
    out['G1'] = dict(summary=g1, scores=G1.to_dict('records') if G1 is not None else None)
    L += ['', '## 3. Check G1: agreement with an independent judge', '']
    if g1 is not None and G1 is not None:
        L.append(f'- {g1["pages_scored"]} judged pages scored ({g1["prompt_examples_left_out"]} example pages left out); every method could route '
                 f'{g1["common_pages"]} of them; the judge gave no theme to {g1["judge_none"]} and marked {g1["misleading_pages"]} titles as misleading.')
        L.append('- Precision is the share of a method\'s page-theme pairs the judge also gives; recall the share of the judge\'s pairs the method gives; '
                 'the last column is the share of misleading-title pages the method sends to a theme the judge does not give (lower is better).')
        L.append('')
        sel = G1[(G1.scope == 'common pages') & (G1.group == 'all')]
        tab = sel.assign(precision=[ci(m, lo, hi) for m, lo, hi in zip(sel.precision, sel.precision_lo, sel.precision_hi)],
                         recall=[ci(m, lo, hi) for m, lo, hi in zip(sel.recall, sel.recall_lo, sel.recall_hi)],
                         misleading=[ci(m, lo, hi) for m, lo, hi in zip(sel.misleading_wrong_share, sel.misleading_wrong_share_lo, sel.misleading_wrong_share_hi)])
        L += T.md_table(tab[['method', 'level', 'pages', 'method_pairs', 'judge_pairs', 'precision', 'recall', 'misleading']])
        L.append('')
        L.append('Scores by part of the judged set (hard cases, random part, sources of hard cases) are in g1_scores.csv and data/reports/testF_26_G1.md.')
    else:
        L.append('- not run (step 26)')
    # ---------------- series
    si = jload(P, 'series_info.json')
    out['series'] = si
    L += ['', '## 4. The theme attention series', '']
    if si:
        if 'S1' in si:
            s1 = si['S1']
            L.append(f'- S1 (views on top-500 days, all confidences): {s1["pages"]:,} pages, {s1["pairs"]:,} page-theme pairs; {len(s1["top_list_days_missing"])} days '
                     f'without a top-500 list make {s1["weeks_partial_for_s1"]} weeks partial (with the weeks before 2016).')
        if 'S2' in si:
            s2 = si['S2']
            L.append(f'- S2 (full daily views, confidence 2 or 3): {s2["pages_with_conf2plus"]:,} pages with such a theme, {s2["selected"]:,} selected '
                     f'(cap of 40,000 applied: {"yes" if s2["cap_applied"] else "no"}); stored {s2["stored"]:,}, missing {s2["not_stored"]:,}; '
                     f'built: {"yes" if s2.get("built") else "no"}' + ('' if not s2.get('built') else f' ({"complete" if s2.get("complete") else "INCOMPLETE"})') + '.')
    else:
        L.append('- not run (step 21)')
    # ---------------- G2
    series = a.series or ('S2' if (P / 'g2_S2_summary.json').exists() else 'S1')
    g2 = jload(P, f'g2_{series}_summary.json')
    G2 = csv(P, f'g2_{series}_pooled.csv')
    g2f = jload(P, f'g2_{series}_summary_with_flagged.json')
    out['G2'] = dict(series=series, summary=g2, pooled=G2.to_dict('records') if G2 is not None else None, with_flagged=g2f)
    L += ['', f'## 5. Check G2: borrowing after rises of the AI theme series ({series})', '']
    if g2 and G2 is not None:
        sh = g2['shifts']
        L.append(f'- Rises found: {sh["total"]:,}, of which labelled {sh["labelled"]:,} (by class {sh["by_class"]}); quality flags {sh["quality_flags"]}. '
                 f'Desktop flag {g2["desktop_flag"]}; donor screen {g2["screen"]}; bootstrap {g2["boot"]} resamples.')
        L.append('- Effect = mean difference in the log share of borrowing in months 0 to 2 (the month of the rise and the two after), against the theme\'s '
                 'own trend (event study) and against a synthetic control of other themes; pooled over rises and formats with intervals from a '
                 'bootstrap clustered by theme. A log effect of 0.088 is about 9.2% more borrowing.')
        if g2.get('mock_inject'):
            L.append(f'- **A lift of {g2["mock_inject"]} (log share) was injected after every tested lasting rise in this mock run (a wiring check).**')
        L += ['', '**Decision (fixed): panel a, rises of 4 weeks or more, interval above 0.**', '']
        for k, d in g2['decision_G2_panel_a_lasting'].items():
            lv, meth = k.split('|')
            L.append(f'- {"both levels pooled" if lv == "both" else lv + " level"}, {meth.replace("_", " ")}: {ci(d["effect"], d["ci_low"], d["ci_high"])} '
                     f'({pct_log(d["effect"])}), {d["tests"]} tests in {d["categories"]} themes; interval above 0: {"yes" if d["interval_above_0"] else "no"}.')
        L += ['', 'Pooled effects (all formats; sc = synthetic control, es = own trend; Chapter 6 = the stored result of the hand-checked concept pages):', '']
        keep = G2[(G2.get('format') == 'all') & G2.duration_class.isin(['sustained', 'fading']) & ((G2.get('analysis') == 'main') | (G2.panel == 'chapter6_concept_pages'))].copy() \
            if 'format' in G2 else G2
        if len(keep):
            keep['synthetic control'] = [ci(m, lo, hi) for m, lo, hi in zip(keep.sc_effect_p_mean, keep.sc_effect_p_ci_low, keep.sc_effect_p_ci_high)]
            keep['own trend'] = [ci(m, lo, hi) for m, lo, hi in zip(keep.es_effect_p_mean, keep.es_effect_p_ci_low, keep.es_effect_p_ci_high)]
            keep['rises'] = keep.duration_class.map({'sustained': '4 weeks or more', 'fading': '1 or 2 weeks'})
            keep['level'] = keep.level.replace({'both': 'both levels'})
            for c in ('tests', 'categories'):
                keep[c] = keep[c].astype('Int64').astype(str)
            keep = keep.sort_values(['duration_class', 'level', 'panel'], ascending=[False, True, True])
            L += T.md_table(keep[['panel', 'level', 'rises', 'tests', 'categories', 'synthetic control', 'own trend']])
        L += ['', 'Panels: a = all Seattle works with librarian headings (the Chapter 6 panel, plus LibriVox); b = the 20,000 AI-sorted works; '
              'c = the same 20,000 works with librarian headings.']
        for k, v in g2['panels'].items():
            L.append(f'- panel {k}: {v["rises_tested"]:,} rises tested in {v["tests"]:,} rise-by-format tests ({v["tests_ok"]:,} with a synthetic control); '
                     f'single tests with one-sided p < 0.05: {v["single_p_lt_alpha"]}; Benjamini-Hochberg q < 0.10: {v["bh_detected"]}.')
        if g2f:
            L.append(f'- A robustness run with the flagged rises included exists (g2_{series}_pooled_with_flagged.csv).')
    else:
        L.append('- not run (step 24)')
    # ---------------- G3
    g3 = jload(P, 'g3_summary.json')
    LT, PR, WO, G4 = csv(P, 'g3_level_rise.csv'), csv(P, 'g3_pairs.csv'), csv(P, 'g3_wikionly.csv'), csv(P, 'g4_wikionly.csv')
    out['G3'] = dict(summary=g3, level_rise=LT.to_dict('records') if LT is not None else None, pairs=PR.to_dict('records') if PR is not None else None,
                     wikionly=WO.to_dict('records') if WO is not None else None)
    L += ['', '## 6. Check G3: forecasts with the AI theme series', '']
    if g3 and LT is not None:
        d = g3['decision_G3']
        L.append(f'- Main rows of the benchmark: {g3["rows"]:,} forecasts of printed books and ebooks one month ahead ({g3["series"]} theme series, '
                 f'{g3["months"]} months).' + (' New forecasts were partly filled with noise (mock).' if g3.get('mock_fill') else ''))
        L += ['', f'**Decision (fixed): Chronos-2 + S2 against Chronos-2 alone, interval of the paired difference below 0.** MAE ratio '
              f'{ci(d["mae_ratio"], d["lo"], d["hi"], 4)}, a change of {100 * (d["mae_ratio"] - 1):+.2f}%; interval below 1 (difference below 0): '
              f'{"yes" if d["interval_below_1"] else "no"}.', '']
        t = LT.copy()
        t['AvgRelMAE'] = [ci(m, lo, hi, 4) for m, lo, hi in zip(t.AvgRelMAE, t.ci_lo, t.ci_hi)]
        t['rank correlation'] = [ci(m, lo, hi, 4) for m, lo, hi in zip(t.rho, t.rho_lo, t.rho_hi)]
        L += T.md_table(t[['pipeline', 'AvgRelMAE', 'share_beats_naive', 'rank correlation']], '{:.3f}')
        L += ['', 'AvgRelMAE below 1 beats repeating last month; the rank correlation is between the forecast change and the actual change within '
              'month, format and level. Paired comparisons (ratio of MAE, other over base, by series):', '']
        if PR is not None:
            for r in PR.itertuples():
                L.append(f'- {r.other} against {r.base}: {ci(r.mae_ratio, r.mae_lo, r.mae_hi, 4)} ({100 * (r.mae_ratio - 1):+.2f}%); better in '
                         f'{r.share_series_better:.0%} of series' + (f'; rank correlation {r.rho_diff:+.4f} [{r.rho_diff_lo:+.4f}, {r.rho_diff_hi:+.4f}]'
                                                                      if 'rho_diff' in PR and r.rho_diff == r.rho_diff else '') + '.')
        if WO is not None:
            L += ['', 'Wikipedia-only ranking with no fitting (the monthly change of a theme\'s series against the next month\'s change in borrowing, '
                  'the Test C measure):', '']
            for r in WO.itertuples():
                L.append(f'- {r.series}: rank correlation {ci(r.rho, r.lo, r.hi, 4)} over {r.groups} groups; rows with a value {r.rows_with_value:.0%}.')
            for p in g3.get('wikionly_pairs', []):
                L.append(f'- {p["other"]} minus {p["base"]}: {p["diff"]:+.4f} [{p["lo"]:+.4f}, {p["hi"]:+.4f}].')
        tm = g3.get('chronos_timing') or {}
        if tm:
            L += ['', 'Chronos-2 run time on this Mac: ' + '; '.join(f'{k}: {v["tasks"]:,} tasks in {v["seconds"]:.0f} s (full run about {v["full_run_estimate_min"]} min)'
                                                              for k, v in tm.items()) + '.']
    else:
        L.append('- not run (step 25)')
    # ---------------- G4
    L += ['', '## 7. Check G4: does it help when the same AI sorted the books too?', '']
    out['G4'] = dict(wikionly=G4.to_dict('records') if G4 is not None else None, pairs=g3.get('g4_pairs') if g3 else None)
    if G2 is not None and 'panel' in G2:
        b_c = G2[(G2.panel.isin(['b', 'c'])) & (G2.get('analysis') == 'main') & (G2.get('format') == 'all') & (G2.duration_class == 'sustained')]
        for r in b_c.sort_values(['level', 'panel']).itertuples():
            lvl = 'both levels' if r.level == 'both' else r.level
            L.append(f'- G2, panel {r.panel}, {lvl}, rises of 4 weeks or more: synthetic control {ci(r.sc_effect_p_mean, r.sc_effect_p_ci_low, r.sc_effect_p_ci_high)}, '
                     f'own trend {ci(r.es_effect_p_mean, r.es_effect_p_ci_low, r.es_effect_p_ci_high)} ({int(r.tests)} tests).')
    if g2 and g2.get('g4_paired_b_minus_c'):
        L.append('- G2, panel b minus panel c on the same rises and formats (positive: the AI-sorted books show the larger rise after a theme\'s rise):')
        for r in g2['g4_paired_b_minus_c']:
            if r['duration_class'] in ('sustained', 'fading') and r['tests']:
                L.append(f'  - {"both levels" if r["level"] == "both" else r["level"]}, {"rises of 4 weeks or more" if r["duration_class"] == "sustained" else "rises of 1 or 2 weeks"}: synthetic control '
                         f'{ci(r.get("d_sc_mean"), r.get("d_sc_ci_low"), r.get("d_sc_ci_high"))}, own trend {ci(r.get("d_es_mean"), r.get("d_es_ci_low"), r.get("d_es_ci_high"))} '
                         f'({r["tests"]} tests in {r["categories"]} themes)')
    if G4 is not None and g3:
        L.append(f'- Wikipedia-only ranking on {g3["g4_rows"]:,} rows that all three panels share:')
        for r in G4.itertuples():
            L.append(f'  - {r.series}, panel {r.panel}: {ci(r.rho, r.lo, r.hi, 4)}')
        for p in g3.get('g4_pairs', []):
            L.append(f'  - {p["series"]}: {p["other"]} minus {p["base"]}: {p["diff"]:+.4f} [{p["lo"]:+.4f}, {p["hi"]:+.4f}]')
    if G4 is None and G2 is None:
        L.append('- not run (steps 24 and 25)')
    pm = jload(P, 'panels_meta.json')
    out['panels'] = pm
    # ---------------- choices and files
    L += ['', '## 8. Choices the addendum did not fix (written into the code before any result)', '']
    L += [f'- Step {s}: {t}' for s, t in CHOICES]
    L += ['', '## 9. Files', '', f'- Test F folder: {P.root}', '- step reports: testF_20_parse.md, testF_21_series.md, testF_23_panels.md, '
          f'testF_24_G2_{series}_shifts.md, testF_24_G2_{series}.md, testF_25_G3.md, testF_26_G1.md, testF_27_reliability.md (in {P.rep})']
    text = '\n'.join(L) + '\n'
    assert '—' not in text, 'an em dash slipped into the report'
    T.write_text(text, P.report('testF_results.md'))
    T.write_json(out, P.report('testF_results.json'))
    T.log(f'wrote {P.report("testF_results.md")} and .json')


if __name__ == '__main__':
    main()
