# 93. Report of the five-seed reruns (record: prereg/DEVIATIONS.md, "Five-seed reruns asked for by the advisor (20 November 2026)").
# Reads data/reports/five_seeds_main.json (l07) and five_seeds_b.json (92), and the values fixed in advance with their 95% intervals
#   (data/reports/wiki_led_l_backtest.json; data/db/wiki_led/robustness_part_b.json).  Writes data/reports/five_seeds.md.
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/93_five_seeds_report.py
import sys, json, time, pathlib
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D                                        # noqa: E402

D = pathlib.Path(D)
REP = D / 'reports'
MA = json.loads((REP / 'five_seeds_main.json').read_text())
MB = json.loads((REP / 'five_seeds_b.json').read_text())
LB = json.loads((REP / 'wiki_led_l_backtest.json').read_text())
RB = json.loads((D / 'db' / 'wiki_led' / 'robustness_part_b.json').read_text())
SEEDS = sorted(MA['seeds'])
assert SEEDS == sorted(MB['seeds']), 'seed lists differ'


def summ(vals):
    v = np.array(vals, float)
    return dict(mean=v.mean(), sd=v.std(ddof=1), lo=v.min(), hi=v.max(), above0=int((v > 0).sum()))


def ci(d, k='est'):
    return f'{d[k]:.4f} [{d["lo"]:.4f}, {d["hi"]:.4f}]'


rows = []                                                     # (section, label, fixed-in-advance text, values, is_gain)
for period in ('2019-2026', '2024-2026'):
    A = LB['by_period'][period]['all']
    sec = f'Main set, books chosen in time (addendum l), all formats, {period}'
    get = lambda f: [f(MA['seeds'][s][period]) for s in SEEDS]
    if period == '2019-2026':
        rows += [(sec, 'Wikipedia alone (W14), change rank', ci(A['W14']['rank']), get(lambda x: x['W14']['rank']), False),
                 (sec, 'Library model (HM), change rank', ci(A['HM']['rank']), get(lambda x: x['HM']['rank']), False),
                 (sec, 'Library + Wikipedia (HMW14), change rank', ci(A['HMW14']['rank']), get(lambda x: x['HMW14']['rank']), False)]
    rows += [(sec, 'Gain from Wikipedia, change rank (L2a)', ci(A['_diff']['L2a_HMW14_minus_HM_rank']),
              get(lambda x: x['L2a_HMW14_minus_HM_rank']), True),
             (sec, 'Gain from Wikipedia, early-warning top 20 (L2b)', ci(A['_diff']['L2b_HMW14_minus_HM_early_top20']),
              get(lambda x: x['L2b_HMW14_minus_HM_early_top20']), True),
             (sec, 'Gain from Wikipedia, top 20 that rose', ci(A['_diff']['HMW14_minus_HM_top20']),
              get(lambda x: x['HMW14_minus_HM_top20']), True)]
for lab, name in (('all', 'all new books'), ('matched', 'author article viewed before the first loan')):
    S = RB['subsets'][lab]
    sec = f'New books (Test B), {name}, rank correlation within test year'
    getm = lambda c: [MB['seeds'][s][lab]['models'][c] for s in SEEDS]
    getd = lambda k: [MB['seeds'][s][lab]['diffs'][k] for s in SEEDS]
    m = lambda c: f'{S["models"][c]["spearman"]:.4f} [{S["models"][c]["lo"]:.4f}, {S["models"][c]["hi"]:.4f}]'
    d = lambda k: ci(S['diffs'][k], 'mean')
    if lab == 'all':
        rows += [(sec, 'Wikipedia alone (W)', m('W_lgbm'), getm('W_lgbm'), False),
                 (sec, 'Library model (L)', m('L_lgbm'), getm('L_lgbm'), False),
                 (sec, 'Library + Wikipedia (LW)', m('LW_lgbm'), getm('LW_lgbm'), False)]
    rows += [(sec, 'Gain from Wikipedia over L', d('LW_minus_L'), getd('LW_minus_L'), True),
             (sec, 'Gain over L0, catalogue facts known at first loan (exploratory)', d('L0W_minus_L0'), getd('L0W_minus_L0'), True),
             (sec, 'Gain over Lq, the same without the theme (exploratory)', d('LqW_minus_Lq'), getd('LqW_minus_Lq'), True)]

L = ['# Five-seed reruns of the headline results', '',
     f'Made by `code/main_study/wiki_led/93_five_seeds_report.py` on {time.strftime("%Y-%m-%d %H:%M %z")}. Record: `prereg/DEVIATIONS.md`, '
     '"Five-seed reruns asked for by the advisor (20 November 2026)", written before the reruns. Asked for by Dr. Fawad Asadi on 20 November 2026.', '',
     f'Each model was refitted with five LightGBM seeds ({", ".join(SEEDS)}); rows, features, test years and all other settings are unchanged. '
     'The first seed is the one used for the published results, and its refit reproduced the stored predictions '
     f'(largest difference {max(MA["check"]["max_abs_diff"].values()):.1e} for the main set, '
     f'{max(list(MB["check"]["vs_test_b"].values()) + list(MB["check"]["vs_robustness_b"].values())):.1e} for new books). '
     'The test years are fixed by time, so the seed changes only the random sampling of rows and columns inside the boosted trees. '
     'Re-drawn samples of works for the main set (part 2 of the record) are in their own section below once they are run. New books use every new book, so they have no sample to re-draw.', '',
     'The "fixed in advance" column is the published value with its 95% interval (blocks of 3 months for the main set, author clusters for new books). '
     'SD is the standard deviation over the five seeds (n - 1).', '']
sec_now = None
for sec, lab, fixed, vals, gain in rows:
    if sec != sec_now:
        L += ['', f'## {sec}', '', '| Value | Fixed in advance [95% interval] | ' + ' | '.join(f'Seed {s[-2:]}' for s in SEEDS) +
              ' | Mean ± SD | Smallest to largest | Gains above 0 |', '| --- | --- |' + ' ---: |' * len(SEEDS) + ' ---: | ---: | ---: |']
        sec_now = sec
    s = summ(vals)
    L.append(f'| {lab} | {fixed} | ' + ' | '.join(f'{v:.4f}' for v in vals) +
             f' | {s["mean"]:.4f} ± {s["sd"]:.4f} | {s["lo"]:.4f} to {s["hi"]:.4f} | {str(s["above0"]) + " of 5" if gain else ""} |')

# plain summary: seed spread against the width of the published interval
g = [r for r in rows if r[4]]
L += ['', '## In short', '']
for sec, lab, fixed, vals, _ in g:
    s = summ(vals)
    lo, hi = [float(x) for x in fixed.split('[')[1].rstrip(']').split(', ')]
    L.append(f'- {sec.split(", rank correlation")[0]}: {lab[0].lower() + lab[1:]}: mean {s["mean"]:.4f} ± {s["sd"]:.4f}; above zero with {s["above0"]} of 5 seeds; '
             f'the seeds spread over {s["hi"] - s["lo"]:.4f}, against a published interval {hi - lo:.4f} wide.')
fr = REP / 'five_seeds_resplit.json'
if fr.exists():                                               # part 2: re-drawn samples of works (main set)
    RS_ = json.loads(fr.read_text())
    A = LB['by_period']['2019-2026']['all']
    L += ['', '## Part 2: five re-drawn 25% samples of works (main set, all formats, 2019 to 2026)', '',
          f'The pool is every work with rows in any of the four quarters of the catalogue ({RS_["pool_works"]:,} works). Each sample draws a quarter of '
          'them at random with its own seed, which is also the LightGBM seed. The quarters on their own are four samples with no work in common; '
          'q0 is the published main set (its rerun equals the published values).', '',
          '| Value | Published (q0) | ' + ' | '.join(f'Sample {k}' for k in range(1, 6)) + ' | Mean ± SD | Smallest to largest | Gains above 0 | '
          + ' | '.join(f'q{q}' for q in range(4)) + ' |',
          '| --- | --- |' + ' ---: |' * 5 + ' ---: | ---: | ---: |' + ' ---: |' * 4]
    for lab, key, fixed, gain in (('Wikipedia alone (W14), change rank', ('W14', 'rank'), ci(A['W14']['rank']), False),
                                  ('Library model (HM), change rank', ('HM', 'rank'), ci(A['HM']['rank']), False),
                                  ('Gain from Wikipedia, change rank (L2a)', 'L2a_HMW14_minus_HM_rank', ci(A['_diff']['L2a_HMW14_minus_HM_rank']), True),
                                  ('Gain from Wikipedia, early-warning top 20 (L2b)', 'L2b_HMW14_minus_HM_early_top20',
                                   ci(A['_diff']['L2b_HMW14_minus_HM_early_top20']), True)):
        pick = (lambda d: d[key[0]][key[1]]) if isinstance(key, tuple) else (lambda d: d[key])
        sv = [pick(RS_['samples'][f'sample_{k}']['by_period']['2019-2026']) for k in range(1, 6)]
        qv = [pick(RS_['quarters'][f'q{q}']['by_period']['2019-2026']) for q in range(4)]
        s = summ(sv)
        L.append(f'| {lab} | {fixed} | ' + ' | '.join(f'{v:.4f}' for v in sv) + f' | {s["mean"]:.4f} ± {s["sd"]:.4f} | {s["lo"]:.4f} to {s["hi"]:.4f} | '
                 f'{str(s["above0"]) + " of 5" if gain else ""} | ' + ' | '.join(f'{v:.4f}' for v in qv) + ' |')
(REP / 'five_seeds.md').write_text('\n'.join(L) + '\n')
print('\n'.join(L[-len(g):]))
