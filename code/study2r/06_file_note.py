"""Study 2R step 6: file the dated calibration note prereg/addenda_2r/2026-10-14_b_calibration_values.json from the two
calibration outputs (05 and 05b). Refuses to overwrite an existing note. Does not edit the record or addendum a."""
import sys
from common import *
OUTF = pathlib.Path(__file__).resolve().parents[2] / 'prereg' / 'addenda_2r' / '2026-10-14_b_calibration_values.json'
if OUTF.exists():
    raise SystemExit(f'{OUTF} already exists; not overwriting')
C = json.load(open(OUT / 'calibration.json')); Fz = json.load(open(OUT / 'feasibility.json'))
w = Fz['works_needed']
grid = {f"floor_{int(r['floor'])}_ratio_{r['ratio']}": dict(articles_kept=r['articles_kept'], works_kept=r['works_kept'], real_sustained_shifts=r['real_sustained'],
        noise_sustained_shifts=r['noise_sustained'], sustained_noise_share=None if r['noise_share_sustained'] != r['noise_share_sustained'] else round(r['noise_share_sustained'], 3))
        for r in C['grid']}
note = {
    'date': time.strftime('%Y-%m-%d'),
    'results_seen': False,
    'results_seen_note': 'Interest data and checkout placebo windows only. No Study 2R borrowing outcome around any event has been computed or read. The first run (floor 300) showed that no ratio reached a sustained noise share of 0.30 (best 0.52 at ratio 4.0); the grid over floors 300, 1000 and 3000 was then run, under the rule written below, before any shift was joined to borrowing.',
    'changes': {
        'events.selection_rule_verbatim': C['pre_declared_rule'],
        'events.chosen': f"floor {int(C['floor_views_per_week'])} user views a week, rise ratio {C['chosen_ratio']}; sustained-shift noise share {C['noise_share_sustained']:.3f}; rule branch: {C['rule_applied']}",
        'events.grid_floor_x_ratio': grid,
        'events.noise_benchmark': f"block-resampled series from each article's own quiet weeks, 8-week blocks, {C['surrogates_per_article']} per article, seed {C['seed']}, as in code/parameter_audit/calibrate_book_series.py; code/study2r/05_calibrate_ratio.py",
        'events.book_set': f"{C['n_works_matched']} Seattle works matched to {C['n_book_articles']} English Wikipedia book articles; at the chosen floor {C['n_articles_kept']} articles ({C['n_works']} works) reach the floor with a 26-week normal level; {C['real_series_years']:.0f} real series-years above the floor",
        'inference.equivalence_feasibility': {
            'basis': f"{Fz['placebo_tests']} placebo windows (random month 0, no attention data) on works of the kept 2R list with at least 500 print and ebook checkouts ({Fz['works_with_500_print_ebook']} works), method of code/parameter_audit/calibrate_2r_noise.py, seed {Fz['seed']}",
            'placebo_tau_sd': round(Fz['sd_tau'], 4), 'placebo_tau_robust_sd': round(Fz['robust_sd_tau'], 4), 'placebo_tau_mean': round(Fz['mean_tau'], 4),
            'works_needed_upper_bound_below_log_1_10_true_effect_0': round(w['sd_true0pct']),
            'works_needed_robust_sd_true_effect_0': round(w['robust_sd_true0pct']),
            'works_needed_true_effect_3pct': round(w['sd_true3pct']), 'works_needed_true_effect_5pct': round(w['sd_true5pct']),
            'rule': 'a duration class with fewer works than works_needed_upper_bound_below_log_1_10_true_effect_0 (the SD-based figure) is reported as inconclusive, with the largest lift ruled out, and gets no "no meaningful effect" verdict',
        },
    },
    'reason': 'Addendum a requires the rise ratio and the feasibility numbers to be fixed from interest data and checkout placebo windows before any 2R outcome is computed. At floor 300 no ratio reached the 0.30 noise target, so a pre-declared rule over higher floors was applied; these are the resulting values.',
}
json.dump(note, open(OUTF, 'w'), indent=2, ensure_ascii=False); open(OUTF, 'a').write('\n')
log('filed', OUTF)
