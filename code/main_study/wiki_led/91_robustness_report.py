# 91. Report of the checks R1 to R7 (addendum e): merges the part files of 90_robustness.py into
#   data/reports/wiki_led_robustness.json  and  data/reports/wiki_led_robustness.md
# Every number in both files is read from the part files; the sentences only choose between fixed wordings by comparing numbers.
# Run from code/ with ../.venv/bin/python main_study/wiki_led/91_robustness_report.py   (after parts b, d, a and a_seeds of 90_robustness.py)
# ROB_TEST_ORIG=PATH: a code test only; uses the original-file Test A part in place of the corrected one and writes to PATH instead of data/reports.
import sys, os, json, time, pathlib, hashlib
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
OUT, REP = D / 'db' / 'wiki_led', D / 'reports'
ADD = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_e_corrections_robustness.json'
ADD_SHA = '36f3605286b51b8123d791c1d59a7dc89356ec3bb66bfba6b9667327d31b3e52'
assert hashlib.sha256(ADD.read_bytes()).hexdigest() == ADD_SHA, 'addendum e changed'
CHECKS = json.loads(ADD.read_text())['robustness_checks']
TEST = os.environ.get('ROB_TEST_ORIG')
OUT_JSON = pathlib.Path(TEST + '.json') if TEST else REP / 'wiki_led_robustness.json'
OUT_MD = pathlib.Path(TEST + '.md') if TEST else REP / 'wiki_led_robustness.md'


def part(name):
    f = OUT / f'robustness_part_{name}.json'
    return json.loads(f.read_text()) if f.exists() else None


PA = part('a_orig' if TEST else 'a')
PS = part('a_seeds')
PB = part('b')
PD = part('d')
PAO = part('a_orig')
missing = [n for n, v in (('a (Test A, corrected)', PA), ('a_seeds (R2)', PS), ('b (Test B)', PB), ('d (Test D)', PD)) if v is None]

NAMES_A = {'Wlgbm_D': 'Wikipedia only (trees)', 'Wrule_D': 'Wikipedia rule (no fitting)', 'Hlgbm_D': 'Library history (trees)',
           'HWlgbm_D': 'Library + Wikipedia (trees)', 'Hnaive_D': 'Repeat last month (naive)', 'Wridge_D': 'Wikipedia only (ridge)'}
NAMES_D = {'W': 'Wikipedia only (trees)', 'H': 'Library history (trees)', 'HW': 'Library + Wikipedia (trees)', 'naive': 'Repeat last month (naive)'}
THR_LABEL = {'rose25': 'rose by 25%', 'rose50': 'rose by 50%', 'rose100': 'rose by 100%', 'surged': 'surged'}
FMTS = ['print', 'ebook', 'audiobook']


# ---------------------------------------------------------------------------------------- formatting
def pc(x, d=1):
    return 'n/a' if x is None else f'{100 * x:.{d}f}%'


def f3(x, d=3):
    return 'n/a' if x is None else f'{x:.{d}f}'


def f2(x):
    return f3(x, 2)


def ci(d, fmt=f3):
    if d is None:
        return 'n/a'
    if d.get('lo') is None:
        return fmt(d['mean'])
    return f"{fmt(d['mean'])} ({fmt(d['lo'])} to {fmt(d['hi'])})"


def cip(d):
    if d is None:
        return 'n/a'
    if d.get('lo') is None:
        return pc(d['mean'])
    return f"{pc(d['mean'])} ({100 * d['lo']:.1f} to {100 * d['hi']:.1f})"


def rate_ci(d):
    """Test D cell: rate with the exact interval."""
    return f"{pc(d['rate'])} ({100 * d['lo']:.1f} to {100 * d['hi']:.1f})"


def table(head, rows, align=None):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '|'.join(['---'] + [' ---: '] * (len(head) - 1)) + '|']
    for r in rows:
        out.append('| ' + ' | '.join(str(c) for c in r) + ' |')
    return '\n'.join(out)


def above0(d):
    return d is not None and d.get('lo') is not None and d['lo'] > 0


L = []          # markdown lines


def w(*s):
    L.extend(s)


# ---------------------------------------------------------------------------------------- the result file
J = {'record': dict(addendum=str(ADD.relative_to(ROOT)), sha256=ADD_SHA, checks=CHECKS),
     'made': time.strftime('%Y-%m-%d %H:%M %z'), 'parts_missing': missing}
if PA:
    J['test_a_files'] = PA['files']
    J['test_a_variant'] = PA['variant']
D_VARIANTS = [k for k in ('original', 'corrected') if PD and PD.get(k)]
J['test_d_variants'] = D_VARIANTS

# ======================================================================================== header
w('# Wikipedia-led tests: how much do the results depend on one choice? (checks R1 to R7)', '',
  'Khant Phyo Wai, 01323050.', '',
  f"Made {J['made']} by `code/main_study/wiki_led/90_robustness.py` (the numbers) and `91_robustness_report.py` (this file). "
  f"The seven checks are fixed in `prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json` (SHA-256 `{ADD_SHA}`). "
  "All numbers are in `data/reports/wiki_led_robustness.json`.", '')
if TEST:
    w('**CODE TEST ONLY: Test A numbers in this file come from the ORIGINAL (uncorrected) Test A files.**', '')
if missing:
    w('**Parts not yet available when this file was made: ' + ', '.join(missing) + '.**', '')
w('## What this is', '',
  'Each check changes one choice and looks at how the reported results move: the size of a rise that counts, the random seed, the test year, '
  'three months of unusual Wikipedia traffic, a stronger library model for new books, and the length of the alert list. '
  'The checks are descriptive. Nothing was tuned, and no setting of any model or alert list was chosen from these numbers.', '',
  '- **Rose by X%**: next month\'s loans are at least X% above the book\'s recent normal (M6, the median of its last six months), compared as '
  'ln(1 + loans) differences like everywhere else in the tests. 50% is the size used in the alert tables so far. **Surged** is the original surge flag '
  '(at least double and at least 5 more loans than normal).',
  '- **Top k list**: the k books with the highest predicted rise in a month (Test D: within each format and month). Ties in the prediction are broken by a fixed random order. '
  '**Hit rate**: the share of list places taken by a book that rose. **Base rate**: the share of all books that rose, which is what a randomly picked list would score.',
  '- **Test A** uses the corrected files (`test_a_rows_c.parquet`, `test_a_preds_c.parquet`: weeks before an article existed are missing, not zero). '
  + ('**Test D** is reported on the original predictions (`test_d_preds.parquet`)' + (' and on the corrected ones (`test_d_preds_c.parquet`).' if 'corrected' in D_VARIANTS else
     '; the corrected predictions did not exist when this file was made, so the Test D numbers are those of the uncorrected run.') if PD else '**Test D** was not available.')
  + ' **Test B** is unaffected by the correction.',
  '- **Intervals** are 95% from 2,000 draws with seed 20261020: blocks of 3 consecutive months for Test A, author clusters for Test B (as `30_test_b.py`), '
  'exact binomial limits over list places for Test D (as addendum d). Months inside one test year are few (8 to 12), so by-year intervals are rough.', '')

# ======================================================================================== R1
w('## R1. How big a rise counts (25%, 50%, 100%)', '',
  'Hit rate of the top 20 and top 50 lists when a rise is counted from 25%, 50% or 100% above the normal. The last row of each block is the base rate.', '')
rows = []
r1 = {}


def cellsA(m, k, fl):
    return PA['lists']['models'][m][f'top{k}'][fl]


if PA:
    for k in (20, 50):
        for m in ['Wlgbm_D', 'Wrule_D', 'Hlgbm_D', 'HWlgbm_D', 'Hnaive_D']:
            rows.append([f'Test A, top {k}', NAMES_A[m]] + [cip(cellsA(m, k, fl)) for fl in ('rose25', 'rose50', 'rose100')])
        rows.append([f'Test A, top {k}', '*base rate (any book)*'] + [pc(PA['lists']['base_monthly_mean'][fl]) for fl in ('rose25', 'rose50', 'rose100')])
    r1['test_a'] = {f'top{k}': {m: {fl: PA['lists']['models'][m][f'top{k}'][fl] for fl in ('rose25', 'rose50', 'rose100')} for m in NAMES_A} for k in (20, 50)}
    r1['test_a']['base_pooled'] = PA['lists']['base_pooled']
    r1['test_a']['base_monthly_mean'] = PA['lists']['base_monthly_mean']
for var in D_VARIANTS:
    tag = 'Test D' + (' (corrected)' if var == 'corrected' else (' (uncorrected run)' if 'corrected' not in D_VARIANTS else ' (original)'))
    S = PD[var]['scopes']['all|2019-2026']
    for k in (20, 50):
        for m in ['W', 'H', 'HW', 'naive']:
            rows.append([f'{tag}, all formats, top {k}', NAMES_D[m]] + [rate_ci(S['lists'][m][f'top{k}'][fl]) for fl in ('rose25', 'rose50', 'rose100')])
        rows.append([f'{tag}, all formats, top {k}', '*base rate (any book)*'] + [pc(S['base'][fl]) for fl in ('rose25', 'rose50', 'rose100')])
    r1[f'test_d_{var}'] = {sc: {'base': v['base'], 'lists': {m: {k: {fl: v['lists'][m][k][fl] for fl in ('rose25', 'rose50', 'rose100')} for k in ('top20', 'top50')} for m in NAMES_D}}
                           for sc, v in PD[var]['scopes'].items()}
w(table(['Data and list', 'Model', 'Rose by 25%', 'Rose by 50%', 'Rose by 100%'], rows), '')
J['R1'] = r1
# reading
if PA:
    f = []
    cells = [(k, fl) for k in (20, 50) for fl in ('rose25', 'rose50', 'rose100')]
    hw_ge_h = sum(cellsA('HWlgbm_D', k, fl)['mean'] >= cellsA('Hlgbm_D', k, fl)['mean'] for k, fl in cells)
    h_gt_w = sum(cellsA('Hlgbm_D', k, fl)['mean'] > cellsA('Wlgbm_D', k, fl)['mean'] for k, fl in cells)
    w_gt_rule = sum(cellsA('Wlgbm_D', k, fl)['mean'] > cellsA('Wrule_D', k, fl)['mean'] for k, fl in cells)
    w_lift = {fl: cellsA('Wlgbm_D', 20, fl)['mean'] / PA['lists']['base_monthly_mean'][fl] for fl in ('rose25', 'rose50', 'rose100')}
    w_above_base = all(cellsA('Wlgbm_D', k, fl)['mean'] > PA['lists']['base_monthly_mean'][fl] for k, fl in cells)
    J['R1']['reading'] = dict(test_a_cells=len(cells), hw_at_least_h=int(hw_ge_h), h_above_w=int(h_gt_w), w_above_rule=int(w_gt_rule), w_top20_lift=w_lift,
                              w_above_base_everywhere=bool(w_above_base))
    w(f"- Test A: the Wikipedia-only list (trees) beats the base rate in {'all' if w_above_base else 'not all'} of the {len(cells)} cells. "
      f"Its top-20 hit rate is {w_lift['rose25']:.1f} times the base rate at 25%, {w_lift['rose50']:.1f} times at 50% and {w_lift['rose100']:.1f} times at 100%, "
      "so a stricter rise makes the Wikipedia list look better relative to chance, even though its hit rate falls.",
      f"- The library list is above the Wikipedia-only list in {h_gt_w} of {len(cells)} cells, the Wikipedia-only list is above the no-fitting rule in {w_gt_rule} of {len(cells)}, "
      f"and library + Wikipedia is at least as high as the library list in {hw_ge_h} of {len(cells)}.")
for var in D_VARIANTS:
    S = PD[var]['scopes']['all|2019-2026']
    cells = [(k, fl) for k in ('top20', 'top50') for fl in ('rose25', 'rose50', 'rose100')]
    hw_ge_h = sum(S['lists']['HW'][k][fl]['rate'] >= S['lists']['H'][k][fl]['rate'] for k, fl in cells)
    w_above = all(S['lists']['W'][k][fl]['rate'] > S['base'][fl] for k, fl in cells)
    lift = {fl: S['lists']['W']['top20'][fl]['rate'] / S['base'][fl] for fl in ('rose25', 'rose50', 'rose100')}
    J['R1'].setdefault('reading_test_d', {})[var] = dict(hw_at_least_h=int(hw_ge_h), cells=len(cells), w_above_base_everywhere=bool(w_above), w_top20_lift=lift)
    w(f"- Test D ({var}, all formats): the Wikipedia-only list beats the base rate in {'all' if w_above else 'not all'} {len(cells)} cells "
      f"(top-20 lift {lift['rose25']:.1f}, {lift['rose50']:.1f} and {lift['rose100']:.1f} times at 25%, 50% and 100%); "
      f"library + Wikipedia is at least as high as the library list in {hw_ge_h} of {len(cells)} cells.")
w('')

# ======================================================================================== R2
w('## R2. Five random seeds (Test A, corrected rows)', '',
  'Wikipedia only (W), library history (H) and library + Wikipedia (HW) were refitted five times with the same settings and walk-forward as `10_test_a.py`, '
  'changing only the seed of the tree models (20261020 to 20261024). Change rank is the mean over months of the Spearman correlation between predicted and actual change; '
  'the top-20 hit rate counts rises of 50%.', '')
if PS and len(PS.get('seeds', {})) > 0:
    sd = PS['seeds']
    seeds = sorted(sd)
    rows = []
    for s in seeds:
        d = sd[s]
        rows.append([s, f3(d['change_rank']['Wlgbm_D']), f3(d['change_rank']['Hlgbm_D']), f3(d['change_rank']['HWlgbm_D']), f3(d['HW_minus_H_change_rank'], 4),
                     pc(d['top20_rose50']['Wlgbm_D']), pc(d['top20_rose50']['Hlgbm_D']), pc(d['top20_rose50']['HWlgbm_D'])])

    def arr(key, m):
        return np.array([sd[s][key][m] for s in seeds])

    summ = {}
    for key in ('change_rank', 'top20_rose50', 'top20_surged', 'surge_ap_ratio'):
        summ[key] = {m: dict(mean=float(arr(key, m).mean()), sd=float(arr(key, m).std(ddof=1)) if len(seeds) > 1 else None, min=float(arr(key, m).min()),
                             max=float(arr(key, m).max()), range=float(arr(key, m).max() - arr(key, m).min())) for m in ('Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D')}
    gap = np.array([sd[s]['HW_minus_H_change_rank'] for s in seeds])
    summ['HW_minus_H'] = dict(mean=float(gap.mean()), min=float(gap.min()), max=float(gap.max()), range=float(gap.max() - gap.min()))
    rows.append(['**mean**', f3(summ['change_rank']['Wlgbm_D']['mean']), f3(summ['change_rank']['Hlgbm_D']['mean']), f3(summ['change_rank']['HWlgbm_D']['mean']), f3(gap.mean(), 4),
                 pc(summ['top20_rose50']['Wlgbm_D']['mean']), pc(summ['top20_rose50']['Hlgbm_D']['mean']), pc(summ['top20_rose50']['HWlgbm_D']['mean'])])
    rows.append(['**lowest to highest**'] + [f"{f3(summ['change_rank'][m]['min'])} to {f3(summ['change_rank'][m]['max'])}" for m in ('Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D')]
                + [f"{f3(gap.min(), 4)} to {f3(gap.max(), 4)}"]
                + [f"{pc(summ['top20_rose50'][m]['min'])} to {pc(summ['top20_rose50'][m]['max'])}" for m in ('Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D')])
    rows.append(['**range (highest minus lowest)**'] + [f3(summ['change_rank'][m]['range']) for m in ('Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D')] + [f3(summ['HW_minus_H']['range'], 4)]
                + [f"{100 * summ['top20_rose50'][m]['range']:.1f} points" for m in ('Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D')])
    w(table(['Seed', 'W change rank', 'H change rank', 'HW change rank', 'HW minus H', 'W top-20 hit', 'H top-20 hit', 'HW top-20 hit'], rows), '')
    J['R2'] = dict(seeds=sd, summary=summ, n_seeds=len(seeds))
    ref = PA['R4_bot_months']['all_months'] if PA else None
    if ref:
        hw = {m: (ref['change_rank'][m]['hi'] - ref['change_rank'][m]['lo']) / 2 for m in ('Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D')}
        hw_gap = (ref['paired']['HW_minus_H']['hi'] - ref['paired']['HW_minus_H']['lo']) / 2
        J['R2']['half_width_of_month_block_interval'] = dict(change_rank=hw, HW_minus_H=hw_gap)
        ratio = summ['change_rank']['Wlgbm_D']['range'] / hw['Wlgbm_D']
        w(f"- The five seeds differ by at most {f3(summ['change_rank']['Wlgbm_D']['range'])} in W change rank, {f3(summ['change_rank']['Hlgbm_D']['range'])} in H and "
          f"{f3(summ['change_rank']['HWlgbm_D']['range'])} in HW. For comparison, the month-block 95% interval of the main run is about plus or minus "
          f"{f3(hw['Wlgbm_D'])} for W, {f3(hw['Hlgbm_D'])} for H and {f3(hw['HWlgbm_D'])} for HW, so the seed spread is {ratio:.2f} times the W half-width.",
          f"- HW minus H is above zero in {int((gap > 0).sum())} of {len(seeds)} seeds (lowest {f3(gap.min(), 4)}, highest {f3(gap.max(), 4)}; the half-width of its month-block interval is {f3(hw_gap, 4)}).",
          f"- The top-20 hit rate moves by up to {100 * summ['top20_rose50']['Wlgbm_D']['range']:.1f} points for W, {100 * summ['top20_rose50']['Hlgbm_D']['range']:.1f} for H "
          f"and {100 * summ['top20_rose50']['HWlgbm_D']['range']:.1f} for HW between seeds.")
    first = sd[seeds[0]]
    if 'max_abs_diff_to_stored' in first:
        w(f"- Check: the refit with seed {seeds[0]} reproduces the stored corrected predictions (largest difference {max(first['max_abs_diff_to_stored'].values()):.2e}).")
    w('')
else:
    w('*Not yet available.*', '')
    J['R2'] = None

# ======================================================================================== R3
w('## R3. By test year', '',
  'Test A: the headline measures inside each test year (year of the month being predicted; 2019 starts with origin 2019-01; 2026 has origins 2025-12 to 2026-07). '
  'Test B: the same for new books by year of their first library month.', '')
J['R3'] = {}
if PA:
    ys = sorted(PA['R3_years'], key=int)
    rows = []
    for y in ys:
        d = PA['R3_years'][y]
        rows.append([y, d['n_months'], pc(d['base_rose50']), f3(d['change_rank']['Wlgbm_D']['mean']), f3(d['change_rank']['Hlgbm_D']['mean']), f3(d['change_rank']['HWlgbm_D']['mean']),
                     ci(d['paired']['HW_minus_H'], lambda x: f3(x, 4)), f2(d['surge_ap']['Wlgbm_D']['ratio']),
                     pc(d['alert']['top20']['Wlgbm_D']['rose50']['mean']), pc(d['alert']['top20']['HWlgbm_D']['rose50']['mean'])])
    w('**Test A**', '', table(['Year', 'Months', 'Base rate (50%)', 'W change rank', 'H change rank', 'HW change rank', 'HW minus H (interval)', 'W surge AP ratio', 'W top-20 hit', 'HW top-20 hit'], rows), '')
    J['R3']['test_a'] = PA['R3_years']
    n_w = sum(PA['R3_years'][y]['change_rank']['Wlgbm_D']['mean'] > 0 for y in ys)
    n_w_int = sum(above0(PA['R3_years'][y]['change_rank']['Wlgbm_D']) for y in ys)
    n_hw = sum(PA['R3_years'][y]['paired']['HW_minus_H']['mean'] > 0 for y in ys)
    n_hw_int = sum(above0(PA['R3_years'][y]['paired']['HW_minus_H']) for y in ys)
    n_ap = sum(PA['R3_years'][y]['surge_ap']['Wlgbm_D']['ratio'] > 1 for y in ys)
    n_alert = sum(PA['R3_years'][y]['alert']['top20']['Wlgbm_D']['rose50']['mean'] > PA['R3_years'][y]['base_rose50'] for y in ys)
    n_hwh = sum(PA['R3_years'][y]['alert']['top20']['HWlgbm_D']['rose50']['mean'] >= PA['R3_years'][y]['alert']['top20']['Hlgbm_D']['rose50']['mean'] for y in ys)
    wr = [PA['R3_years'][y]['change_rank']['Wlgbm_D']['mean'] for y in ys]
    gp = [PA['R3_years'][y]['paired']['HW_minus_H']['mean'] for y in ys]
    J['R3']['test_a_reading'] = dict(years=len(ys), w_rank_positive=int(n_w), w_rank_interval_above0=int(n_w_int), hw_minus_h_positive=int(n_hw), hw_minus_h_interval_above0=int(n_hw_int),
                                     w_surge_ratio_above1=int(n_ap), w_top20_above_base=int(n_alert), hw_top20_at_least_h=int(n_hwh), w_rank_min=min(wr), w_rank_max=max(wr),
                                     hw_minus_h_min=min(gp), hw_minus_h_max=max(gp))
    w(f"- W change rank is above zero in {n_w} of {len(ys)} years (interval above zero in {n_w_int}); it runs from {f3(min(wr))} ({ys[int(np.argmin(wr))]}) to {f3(max(wr))} ({ys[int(np.argmax(wr))]}).",
      f"- HW minus H is above zero in {n_hw} of {len(ys)} years (interval above zero in {n_hw_int}); it runs from {f3(min(gp), 4)} ({ys[int(np.argmin(gp))]}) to {f3(max(gp), 4)} ({ys[int(np.argmax(gp))]}).",
      f"- The W surge AP ratio is above 1 in {n_ap} of {len(ys)} years; the W top-20 hit rate is above that year's base rate in {n_alert} of {len(ys)}; HW's top-20 hit rate is at least H's in {n_hwh} of {len(ys)}.", '')
if PB:
    S = PB['subsets']['all']
    ys = sorted(S['by_year'], key=int)
    rows = []
    for y in ys:
        d = S['by_year'][y]
        rows.append([y, f"{d['n']:,}", ci(d['models']['W_lgbm']), ci(d['models']['L_lgbm']), ci(d['models']['LW_lgbm']), ci(d['diffs']['LW_minus_L'], lambda x: f3(x, 4)),
                     pc(d['models']['W_lgbm']['top10_precision']), pc(d['models']['L_lgbm']['top10_precision']), pc(d['models']['LW_lgbm']['top10_precision'])])
    rows.append(['**all years**', f"{S['n']['rows']:,}", ci(S['models']['W_lgbm']), ci(S['models']['L_lgbm']), ci(S['models']['LW_lgbm']), ci(S['diffs']['LW_minus_L'], lambda x: f3(x, 4)),
                 pc(S['models']['W_lgbm']['top10_precision']), pc(S['models']['L_lgbm']['top10_precision']), pc(S['models']['LW_lgbm']['top10_precision'])])
    w('**Test B** (Spearman correlation between predicted and actual first-six-month loans; top-10% precision: share of the predicted top 10% that is in the actual top 10%, base rate 10%)', '',
      table(['Year', 'New books', 'W Spearman', 'L Spearman', 'LW Spearman', 'LW minus L', 'W top-10%', 'L top-10%', 'LW top-10%'], rows), '')
    J['R3']['test_b'] = {k: v for k, v in S['by_year'].items()}
    J['R3']['test_b_all_years'] = dict(models={k: S['models'][k] for k in ('W_lgbm', 'L_lgbm', 'LW_lgbm')}, diffs={'LW_minus_L': S['diffs']['LW_minus_L']})
    nb1 = sum(above0(S['by_year'][y]['models']['W_lgbm']) for y in ys)
    nb2 = sum(above0(S['by_year'][y]['diffs']['LW_minus_L']) for y in ys)
    nb2p = sum(S['by_year'][y]['diffs']['LW_minus_L']['mean'] > 0 for y in ys)
    wsp = [S['by_year'][y]['models']['W_lgbm']['spearman'] for y in ys]
    gd = [S['by_year'][y]['diffs']['LW_minus_L']['mean'] for y in ys]
    J['R3']['test_b_reading'] = dict(years=len(ys), w_interval_above0=int(nb1), lw_minus_l_positive=int(nb2p), lw_minus_l_interval_above0=int(nb2), w_min=min(wsp), w_max=max(wsp),
                                     lw_minus_l_min=min(gd), lw_minus_l_max=max(gd))
    w(f"- W Spearman has its interval above zero in {nb1} of {len(ys)} years and runs from {f3(min(wsp))} ({ys[int(np.argmin(wsp))]}) to {f3(max(wsp))} ({ys[int(np.argmax(wsp))]}).",
      f"- LW minus L is above zero in {nb2p} of {len(ys)} years (interval above zero in {nb2}); it runs from {f3(min(gd), 4)} ({ys[int(np.argmin(gd))]}) to {f3(max(gd), 4)} ({ys[int(np.argmax(gd))]}).", '')

# ======================================================================================== R4
w('## R4. Without the origin months 2025-04 to 2025-06 (Test A)', '',
  'Wikimedia reported automated traffic counted as user views in those months. The predictions are the same; only the scoring leaves the three origin months out '
  '(the models were not refitted). The last column shows the three months alone (no interval: three months cannot be resampled in blocks of three).', '')
if PA:
    R4 = PA['R4_bot_months']
    A, B, C = R4['all_months'], R4['without_bot_months'], R4['bot_months_only']
    rows = []

    def r4row(label, getter, fmt=f3, dfmt=None):
        a, b, c = getter(A), getter(B), getter(C)
        dfmt = dfmt or fmt
        am = a['mean'] if isinstance(a, dict) else a
        bm = b['mean'] if isinstance(b, dict) else b
        cm = c['mean'] if isinstance(c, dict) else c
        rows.append([label, ci(a, fmt) if isinstance(a, dict) else fmt(a), ci(b, fmt) if isinstance(b, dict) else fmt(b), dfmt(bm - am), fmt(cm)])

    for m, nm in (('Wlgbm_D', 'W'), ('Hlgbm_D', 'H'), ('HWlgbm_D', 'HW'), ('Hnaive_D', 'naive')):
        r4row(f'{nm} change rank', lambda s, m=m: s['change_rank'][m])
    r4row('HW minus H', lambda s: s['paired']['HW_minus_H'], lambda x: f3(x, 4))
    r4row('W minus no-fitting rule', lambda s: s['paired']['W_minus_rule'])
    for m, nm in (('Wlgbm_D', 'W'), ('Hlgbm_D', 'H'), ('HWlgbm_D', 'HW')):
        a, b, c = A['surge_ap'][m], B['surge_ap'][m], C['surge_ap'][m]
        rows.append([f'{nm} surge AP ratio', f"{f2(a['ratio'])} ({f2(a['ratio_lo'])} to {f2(a['ratio_hi'])})", f"{f2(b['ratio'])} ({f2(b['ratio_lo'])} to {f2(b['ratio_hi'])})",
                     f"{b['ratio'] - a['ratio']:+.2f}", f2(c['ratio'])])
    for m, nm in (('Wlgbm_D', 'W'), ('Hlgbm_D', 'H'), ('HWlgbm_D', 'HW')):
        a, b, c = A['alert']['top20'][m]['rose50'], B['alert']['top20'][m]['rose50'], C['alert']['top20'][m]['rose50']
        rows.append([f'{nm} top-20 hit rate (50%)', cip(a), cip(b), f"{100 * (b['mean'] - a['mean']):+.1f} points", pc(c['mean'])])
    rows.append(['Base rate of a 50% rise', pc(A['base_rose50']), pc(B['base_rose50']), f"{100 * (B['base_rose50'] - A['base_rose50']):+.1f} points", pc(C['base_rose50'])])
    rows.append(['Months scored', A['n_months'], B['n_months'], B['n_months'] - A['n_months'], C['n_months']])
    w(table(['Measure', 'All scored months', 'Without 2025-04 to 2025-06', 'Change', 'The three months alone'], rows), '')
    J['R4'] = R4
    a1 = above0(B['change_rank']['Wlgbm_D'])
    a2 = above0(B['paired']['HW_minus_H'])
    a3 = B['surge_ap']['Wlgbm_D']['ratio_lo'] > 1
    wd = B['change_rank']['Wlgbm_D']['mean'] - A['change_rank']['Wlgbm_D']['mean']
    J['R4']['reading'] = dict(a1_holds=bool(a1), a2_holds=bool(a2), a3_holds=bool(a3), w_rank_change=wd)
    w(f"- Without the three months, W change rank moves by {wd:+.4f}, HW minus H by {B['paired']['HW_minus_H']['mean'] - A['paired']['HW_minus_H']['mean']:+.4f} and the W top-20 hit rate by "
      f"{100 * (B['alert']['top20']['Wlgbm_D']['rose50']['mean'] - A['alert']['top20']['Wlgbm_D']['rose50']['mean']):+.1f} points. "
      f"A1 (W interval above zero) {'holds' if a1 else 'does not hold'}, A2 (HW minus H above zero) {'holds' if a2 else 'does not hold'} and A3 (W surge ratio interval above 1) {'holds' if a3 else 'does not hold'}.",
      f"- In the three months alone, W change rank is {f3(C['change_rank']['Wlgbm_D']['mean'])} against {f3(A['change_rank']['Wlgbm_D']['mean'])} over all months, and the W top-20 hit rate is "
      f"{pc(C['alert']['top20']['Wlgbm_D']['rose50']['mean'])} against {pc(A['alert']['top20']['Wlgbm_D']['rose50']['mean'])}.", '')
else:
    J['R4'] = None

# ======================================================================================== R5
w('## R5. A stronger library model for new books (Test B)', '',
  'L+ is the library model of Test B plus catalogue information the library has when it acquires a work: the broad theme (the level-1 theme node with the highest strength in '
  '`work_theme.parquet`, or none), the first year minus the publication year (`pub_year_min`), and whether the creator came only from the title field. '
  'Everything else is as in `30_test_b.py`: same rows, same walk-forward, same tree settings, same author-cluster bootstrap with the same draws. '
  '**Added beside the addendum:** "no theme" models (L-q and L-q+W: L plus the two other catalogue features only), because the theme is built from catalogue records of all years.', '')
J['R5'] = None
if PB:
    SUBS = [('all', 'all new books'), ('matched', 'author matched to a Wikipedia article before release'), ('writer_type', 'matched author is a writer')]
    MN = {'W_lgbm': 'W (Wikipedia only)', 'L_lgbm': 'L (library, as reported)', 'LW_lgbm': 'L+W as reported (L plus Wikipedia)', 'Lq_lgbm': 'L-q (L + publication year + title-only flag)',
          'LqW_lgbm': 'L-q + Wikipedia', 'Lp_lgbm': 'L+ (L + theme + publication year + title-only flag)', 'LpW_lgbm': 'L+W (L+ plus Wikipedia)'}
    ex = PB['extra_info']
    w(f"New features: {pc(ex['works_with_theme'])} of the works have a theme; {pc(ex['theme_from_goodreads_share'])} of the chosen themes draw on Goodreads data at all; "
      f"{pc(ex['creator_from_title_only_share'])} have the creator from the title only; first year minus publication year is 0 for {ex['age0_counts'].get('0', 0):,} works, "
      f"1 for {ex['age0_counts'].get('1', 0):,} and below 0 for {sum(v for k, v in ex['age0_counts'].items() if int(k) < 0):,}.", '')
    for sub, lab in SUBS:
        S = PB['subsets'][sub]
        rows = [[MN[c], ci(S['models'][c]), pc(S['models'][c]['top10_precision'])] for c in ('W_lgbm', 'L_lgbm', 'Lq_lgbm', 'Lp_lgbm', 'LW_lgbm', 'LqW_lgbm', 'LpW_lgbm')]
        w(f"**{lab}** ({S['n']['rows']:,} books, {S['n']['authors']:,} author clusters)", '', table(['Model', 'Spearman (interval)', 'Top-10% precision'], rows), '')
    rows = []
    for sub, lab in SUBS:
        S = PB['subsets'][sub]
        for name, label in (('LW_minus_L', 'Wikipedia on top of L (as reported)'), ('LqW_minus_Lq', 'Wikipedia on top of L-q (added)'), ('LpW_minus_Lp', 'Wikipedia on top of L+ (R5)')):
            d = S['diffs'][name]
            rows.append([lab, label, ci(d, lambda x: f3(x, 4)), 'yes' if above0(d) else 'no'])
    w('**Does Wikipedia still add?** (paired difference in Spearman, same draws; yes = interval above 0)', '', table(['Books', 'Comparison', 'Difference (interval)', 'Above 0?'], rows), '')
    rows = []
    for sub, lab in SUBS:
        S = PB['subsets'][sub]
        for name, label in (('Lq_minus_L', 'L-q minus L (publication year and title-only flag)'), ('Lp_minus_Lq', 'L+ minus L-q (the theme)'), ('Lp_minus_L', 'L+ minus L (all three)')):
            rows.append([lab, label, ci(S['diffs'][name], lambda x: f3(x, 4))])
    w('**What the extra catalogue information adds to the library model alone**', '', table(['Books', 'Comparison', 'Difference in Spearman (interval)'], rows), '')
    S = PB['subsets']['all']
    gain_old, gain_new = S['diffs']['LW_minus_L'], S['diffs']['LpW_minus_Lp']
    kept = gain_new['mean'] / gain_old['mean']
    J['R5'] = dict(extra_info=ex, subsets=PB['subsets'], refit_check_max_abs_diff=PB['refit_check_max_abs_diff'],
                   reading=dict(all_gain_as_reported=gain_old, all_gain_stronger=gain_new, share_kept=kept,
                                still_adds={sub: above0(PB['subsets'][sub]['diffs']['LpW_minus_Lp']) for sub, _ in SUBS},
                                still_adds_no_theme={sub: above0(PB['subsets'][sub]['diffs']['LqW_minus_Lq']) for sub, _ in SUBS}))
    w(f"- The library model rises from {f3(S['models']['L_lgbm']['spearman'])} to {f3(S['models']['Lp_lgbm']['spearman'])} Spearman with the catalogue information "
      f"({f3(S['models']['Lq_lgbm']['spearman'])} without the theme). Wikipedia's addition falls from {f3(gain_old['mean'], 4)} to {f3(gain_new['mean'], 4)} "
      f"(interval {f3(gain_new['lo'], 4)} to {f3(gain_new['hi'], 4)}), which is {100 * kept:.0f}% of the earlier gain; the interval is {'above' if above0(gain_new) else 'not above'} zero. "
      f"Without the theme the addition is {f3(S['diffs']['LqW_minus_Lq']['mean'], 4)} (interval {f3(S['diffs']['LqW_minus_Lq']['lo'], 4)} to {f3(S['diffs']['LqW_minus_Lq']['hi'], 4)}).", '')

# ======================================================================================== R6
w('## R6. Does Wikipedia catch rises the library list misses? (Test A, incremental early warning)', '',
  'In each month: take the books that rose by 50% next month and were not in the library model\'s top 50. What share of them is in Wikipedia\'s top 50 '
  '(Wikipedia-only trees)? A random list of 50 would catch 50 divided by the number of books that month (about 0.7%). '
  'Two library lists are used: the library history model (trees, the main one) and the naive repeat-last-month ranking (added). Averages are over months, with month-block intervals.', '')
if PA:
    R6 = PA['R6_incremental']
    rows = []
    cols = [('library_trees', 'Library = history model (trees)'), ('library_naive', 'Library = repeat last month')]
    key = 'top50|rose50'

    def r6line(label, getter, fmt=cip):
        rows.append([label] + [fmt(getter(R6[c][key])) for c, _ in cols])

    r6line('Books in a month, on average', lambda d: d['mean_books_per_month'], lambda x: f'{x:,.0f}')
    r6line('Books that rose by 50%, per month', lambda d: d['mean_rises_per_month'], lambda x: f'{x:,.0f}')
    r6line('Share of all rises caught by the library top 50', lambda d: d['library_catches_of_rises'])
    r6line('Share of all rises caught by the Wikipedia top 50', lambda d: d['wikipedia_catches_of_rises'])
    r6line('Share of all rises caught by both lists together', lambda d: d['both_catch_of_rises'])
    r6line('Rises not in the library top 50, per month', lambda d: d['mean_missed_rises_per_month'], lambda x: f'{x:,.0f}')
    r6line('**Share of those caught by the Wikipedia top 50**', lambda d: d['share_caught_by_wikipedia'])
    r6line('Share a random list of 50 would catch (expected)', lambda d: d['share_random_list'])
    r6line('Wikipedia share divided by the random share', lambda d: d['lift_over_random'], lambda d: ci(d, lambda x: f'{x:.2f}'))
    r6line('Months in which Wikipedia beats the random list', lambda d: d['months_wikipedia_beats_random'], pc)
    r6line('Books in both lists, per month', lambda d: d['mean_overlap_of_the_two_lists'], lambda x: f'{x:.1f}')
    r6line('Books in the Wikipedia list not in the library list, per month', lambda d: d['new_books_in_wikipedia_list_mean'], lambda x: f'{x:.1f}')
    r6line('Share of those new books that rose', lambda d: d['precision_of_new_books'])
    r6line('Share of rose among books outside the library top 50', lambda d: d['base_rate_outside_library_list'])
    w(table(['Measure (top 50 lists, rise of 50%)'] + [n for _, n in cols], rows), '')
    J['R6'] = R6
    m0 = R6['library_trees'][key]
    m1 = R6['library_naive'][key]
    t20 = R6['library_trees']['top20|rose50']
    J['R6']['reading'] = dict(share=m0['share_caught_by_wikipedia'], random=m0['share_random_list'], lift=m0['lift_over_random'], lift_interval_above_1=bool(m0['lift_over_random']['lo'] > 1))
    w(f"- Among the rises the library history list missed, Wikipedia's top 50 caught {cip(m0['share_caught_by_wikipedia'])}, against {pc(m0['share_random_list']['mean'], 2)} for a random list "
      f"({m0['lift_over_random']['mean']:.1f} times; interval {m0['lift_over_random']['lo']:.1f} to {m0['lift_over_random']['hi']:.1f}). With the naive list as the library list the share is "
      f"{cip(m1['share_caught_by_wikipedia'])}.",
      f"- Of the {m0['new_books_in_wikipedia_list_mean']:.1f} books per month that Wikipedia's list adds, {pc(m0['precision_of_new_books']['mean'])} rose, against {pc(m0['base_rate_outside_library_list']['mean'])} of the books outside the library list. "
      f"The two lists share {m0['mean_overlap_of_the_two_lists']:.1f} books a month.",
      f"- With lists of 20 the share caught is {cip(t20['share_caught_by_wikipedia'])} (random: {pc(t20['share_random_list']['mean'], 2)}).", '')
else:
    J['R6'] = None

# ======================================================================================== R7
w('## R7. Length of the alert list (top 10, 20, 50, 100)', '',
  'Hit rates for rises of 50% and for surges, by list length. Test D numbers are for all formats (lists drawn within each format and month), 2019 to 2026.', '')
J['R7'] = {}
if PA:
    for fl in ('rose50', 'surged'):
        rows = []
        for m in ['Wlgbm_D', 'Wrule_D', 'Hlgbm_D', 'HWlgbm_D', 'Hnaive_D']:
            rows.append([NAMES_A[m]] + [cip(cellsA(m, k, fl)) for k in (10, 20, 50, 100)])
        rows.append(['*base rate (any book)*'] + [pc(PA['lists']['base_monthly_mean'][fl])] * 4)
        w(f"**Test A, {THR_LABEL[fl]}**", '', table(['Model', 'Top 10', 'Top 20', 'Top 50', 'Top 100'], rows), '')
    ks = (10, 20, 50, 100)
    J['R7']['test_a'] = {m: {f'top{k}': {fl: PA['lists']['models'][m][f'top{k}'][fl] for fl in ('rose50', 'surged')} for k in ks} for m in NAMES_A}
    J['R7']['test_a_base'] = PA['lists']['base_monthly_mean']
    hw_h = sum(cellsA('HWlgbm_D', k, fl)['mean'] >= cellsA('Hlgbm_D', k, fl)['mean'] for k in ks for fl in ('rose50', 'surged'))
    wl = {k: cellsA('Wlgbm_D', k, 'rose50')['mean'] / PA['lists']['base_monthly_mean']['rose50'] for k in ks}
    J['R7']['test_a_reading'] = dict(hw_at_least_h=int(hw_h), cells=8, w_lift_by_k=wl)
    w(f"- Test A: library + Wikipedia is at least as high as the library list in {hw_h} of 8 cells (4 lengths, two outcomes). The Wikipedia-only list is "
      + ', '.join(f"{wl[k]:.1f}" for k in ks) + " times the base rate at 10, 20, 50 and 100 places, so it works best in the shortest lists.", '')
for var in D_VARIANTS:
    tag = 'Test D' + (' (corrected)' if var == 'corrected' else (' (uncorrected run)' if 'corrected' not in D_VARIANTS else ' (original)'))
    S = PD[var]['scopes']['all|2019-2026']
    rows = []
    for m in ['W', 'H', 'HW', 'naive']:
        rows.append([NAMES_D[m]] + [rate_ci(S['lists'][m][f'top{k}']['rose50']) for k in (10, 20, 50, 100)])
    rows.append(['*base rate (any book)*'] + [pc(S['base']['rose50'])] * 4)
    w(f"**{tag}, all formats, {THR_LABEL['rose50']}**", '', table(['Model', 'Top 10', 'Top 20', 'Top 50', 'Top 100'], rows), '')
    rows = []
    for sc in ['print', 'ebook', 'audiobook']:
        for period in ('2019-2026', '2024-2026'):
            T = PD[var]['scopes'][f'{sc}|{period}']
            rows.append([sc, period] + [rate_ci(T['lists']['HW'][f'top{k}']['rose50']) + (' *' if T['lists']['HW'][f'top{k}']['rose50']['rate'] >= 0.9 else '') for k in (10, 20, 50, 100)])
    T = PD[var]['scopes']['all|2024-2026']
    rows.append(['all formats', '2024-2026'] + [rate_ci(T['lists']['HW'][f'top{k}']['rose50']) + (' *' if T['lists']['HW'][f'top{k}']['rose50']['rate'] >= 0.9 else '') for k in (10, 20, 50, 100)])
    S0 = PD[var]['scopes']['all|2019-2026']
    rows.append(['all formats', '2019-2026'] + [rate_ci(S0['lists']['HW'][f'top{k}']['rose50']) + (' *' if S0['lists']['HW'][f'top{k}']['rose50']['rate'] >= 0.9 else '') for k in (10, 20, 50, 100)])
    w(f"**{tag}: library + Wikipedia by format and period, {THR_LABEL['rose50']}** (* = at least 90%)", '', table(['Format', 'Years', 'Top 10', 'Top 20', 'Top 50', 'Top 100'], rows), '')
    n90 = {f'top{k}': sum(PD[var]['scopes'][f'{sc}|{p}']['lists']['HW'][f'top{k}']['rose50']['rate'] >= 0.9 for sc in FMTS for p in ('2019-2026', '2024-2026')) for k in (10, 20, 50, 100)}
    J['R7'][f'test_d_{var}'] = {sc: {'base': v['base'], 'lists': v['lists']} for sc, v in PD[var]['scopes'].items()}
    J['R7'][f'test_d_{var}_reading'] = dict(hw_formats_periods_at_least_90=n90, of=6)
    w(f"- {tag}: library + Wikipedia reaches 90% in " + ', '.join(f"{n90[f'top{k}']} of 6 format and period cells at {k} places" for k in (10, 20, 50, 100)) + '.', '')

# ======================================================================================== decisions
w('## Does any conclusion depend on a single choice?', '')
J['decisions'] = []
TIE = 0.005      # alert-list differences under 0.5 points count as ties (the tie rule of addendum c)


def add(decision, items):
    """items: (column of the table below, what was compared, holds, detail)."""
    J['decisions'].append(dict(decision=decision, checks=[dict(column=col, check=c, holds=bool(h), detail=t) for col, c, h, t in items]))


if PA:
    B = PA['R4_bot_months']['all_months']
    nb = PA['R4_bot_months']['without_bot_months']
    ys = sorted(PA['R3_years'], key=int)
    sd = PS['seeds'] if PS and PS.get('seeds') else None
    base = PA['lists']['base_monthly_mean']
    R3 = PA['R3_years']
    # A1
    it = [('main', 'all months', above0(B['change_rank']['Wlgbm_D']), f"W change rank {ci(B['change_rank']['Wlgbm_D'])}"),
          ('R4', 'without 2025-04 to 2025-06', above0(nb['change_rank']['Wlgbm_D']), f"{ci(nb['change_rank']['Wlgbm_D'])}"),
          ('R3', 'each test year', all(R3[y]['change_rank']['Wlgbm_D']['mean'] > 0 for y in ys),
           f"point value above 0 in {sum(R3[y]['change_rank']['Wlgbm_D']['mean'] > 0 for y in ys)} of {len(ys)} years, interval above 0 in {sum(above0(R3[y]['change_rank']['Wlgbm_D']) for y in ys)}")]
    if sd:
        v = [sd[s]['change_rank']['Wlgbm_D'] for s in sorted(sd)]
        it.append(('R2', 'each seed', all(x > 0 for x in v), f"{f3(min(v))} to {f3(max(v))} over {len(v)} seeds"))
    add('A1: Wikipedia alone ranks which books will rise (Test A, interval of W change rank above 0)', it)
    # A2
    it = [('main', 'all months', above0(B['paired']['HW_minus_H']), f"HW minus H {ci(B['paired']['HW_minus_H'], lambda x: f3(x, 4))}"),
          ('R4', 'without 2025-04 to 2025-06', above0(nb['paired']['HW_minus_H']), f"{ci(nb['paired']['HW_minus_H'], lambda x: f3(x, 4))}"),
          ('R3', 'each test year', all(R3[y]['paired']['HW_minus_H']['mean'] > 0 for y in ys),
           f"point value above 0 in {sum(R3[y]['paired']['HW_minus_H']['mean'] > 0 for y in ys)} of {len(ys)} years, interval above 0 in {sum(above0(R3[y]['paired']['HW_minus_H']) for y in ys)}")]
    if sd:
        v = [sd[s]['HW_minus_H_change_rank'] for s in sorted(sd)]
        it.append(('R2', 'each seed', all(x > 0 for x in v), f"{f3(min(v), 4)} to {f3(max(v), 4)} over {len(v)} seeds"))
    add('A2: Wikipedia adds to library history (Test A, HW minus H above 0)', it)
    # A3
    sa, sn = B['surge_ap']['Wlgbm_D'], nb['surge_ap']['Wlgbm_D']
    it = [('main', 'all months', sa['ratio_lo'] > 1, f"W surge AP ratio {f2(sa['ratio'])} ({f2(sa['ratio_lo'])} to {f2(sa['ratio_hi'])})"),
          ('R4', 'without 2025-04 to 2025-06', sn['ratio_lo'] > 1, f"{f2(sn['ratio'])} ({f2(sn['ratio_lo'])} to {f2(sn['ratio_hi'])})"),
          ('R3', 'each test year', all(R3[y]['surge_ap']['Wlgbm_D']['ratio'] > 1 for y in ys),
           f"ratio above 1 in {sum(R3[y]['surge_ap']['Wlgbm_D']['ratio'] > 1 for y in ys)} of {len(ys)} years")]
    if sd:
        v = [sd[s]['surge_ap_ratio']['Wlgbm_D'] for s in sorted(sd)]
        it.append(('R2', 'each seed', all(x > 1 for x in v), f"{f2(min(v))} to {f2(max(v))} over {len(v)} seeds"))
    add('A3: Wikipedia alone flags surges (Test A, interval of the W surge AP ratio above 1)', it)
    # alert lists
    cells = [(k, fl) for k in (20, 50) for fl in ('rose25', 'rose50', 'rose100')]
    n_wb = sum(cellsA('Wlgbm_D', k, fl)['mean'] > base[fl] for k, fl in cells)
    ks4 = (10, 20, 50, 100)
    n_wk = sum(cellsA('Wlgbm_D', k, fl)['mean'] > base[fl] for k in ks4 for fl in ('rose50', 'surged'))
    n_wy = sum(R3[y]['alert']['top20']['Wlgbm_D']['rose50']['mean'] > R3[y]['base_rose50'] for y in ys)
    it = [('R1', 'rise of 25%, 50%, 100%; top 20 and 50', n_wb == len(cells), f"above the base rate in {n_wb} of {len(cells)} cells"),
          ('R7', 'top 10, 20, 50, 100; rose 50% and surged', n_wk == 8, f"above the base rate in {n_wk} of 8 cells"),
          ('R3', 'each test year (top 20)', n_wy == len(ys), f"above the year's base rate in {n_wy} of {len(ys)} years"),
          ('R4', 'without 2025-04 to 2025-06 (top 20)', nb['alert']['top20']['Wlgbm_D']['rose50']['mean'] > nb['base_rose50'],
           f"{pc(nb['alert']['top20']['Wlgbm_D']['rose50']['mean'])} against a base rate of {pc(nb['base_rose50'])}")]
    if sd:
        v = [sd[s]['top20_rose50']['Wlgbm_D'] for s in sorted(sd)]
        it.append(('R2', 'each seed (top 20)', all(x > base['rose50'] for x in v), f"top-20 hit rate {pc(min(v))} to {pc(max(v))} over {len(v)} seeds"))
    add('Alert list: the Wikipedia-only list beats the base rate (Test A)', it)
    n_hh = sum(cellsA('HWlgbm_D', k, fl)['mean'] >= cellsA('Hlgbm_D', k, fl)['mean'] - TIE for k, fl in cells)
    n_hk = sum(cellsA('HWlgbm_D', k, fl)['mean'] >= cellsA('Hlgbm_D', k, fl)['mean'] - TIE for k in ks4 for fl in ('rose50', 'surged'))
    n_hy = sum(R3[y]['alert']['top20']['HWlgbm_D']['rose50']['mean'] >= R3[y]['alert']['top20']['Hlgbm_D']['rose50']['mean'] - TIE for y in ys)
    it = [('R1', 'rise of 25%, 50%, 100%; top 20 and 50', n_hh == len(cells), f"HW not more than 0.5 points below H in {n_hh} of {len(cells)} cells"),
          ('R7', 'top 10, 20, 50, 100; rose 50% and surged', n_hk == 8, f"HW not more than 0.5 points below H in {n_hk} of 8 cells"),
          ('R3', 'each test year (top 20)', n_hy == len(ys), f"HW not more than 0.5 points below H in {n_hy} of {len(ys)} years"),
          ('R4', 'without 2025-04 to 2025-06 (top 20)',
           nb['alert']['top20']['HWlgbm_D']['rose50']['mean'] >= nb['alert']['top20']['Hlgbm_D']['rose50']['mean'] - TIE,
           f"HW {pc(nb['alert']['top20']['HWlgbm_D']['rose50']['mean'])}, H {pc(nb['alert']['top20']['Hlgbm_D']['rose50']['mean'])}")]
    if sd:
        v = [(sd[s]['top20_rose50']['HWlgbm_D'] - sd[s]['top20_rose50']['Hlgbm_D']) for s in sorted(sd)]
        it.append(('R2', 'each seed (top 20)', all(x >= -TIE for x in v), f"HW minus H in the top-20 hit rate: {100 * min(v):+.1f} to {100 * max(v):+.1f} points over {len(v)} seeds"))
    add('Alert list: adding Wikipedia to the library list does not lower the hit rate (Test A; differences under 0.5 points are ties)', it)
    m0 = PA['R6_incremental']['library_trees']['top50|rose50']
    m1 = PA['R6_incremental']['library_naive']['top50|rose50']
    add("Wikipedia's list catches rises that the library list misses (Test A)",
        [('R6', 'library history list, top 50', m0['lift_over_random']['lo'] > 1, f"{cip(m0['share_caught_by_wikipedia'])} caught against {pc(m0['share_random_list']['mean'], 2)} for a random list of 50"),
         ('R6', 'naive library list, top 50', m1['lift_over_random']['lo'] > 1, f"{cip(m1['share_caught_by_wikipedia'])} caught against {pc(m1['share_random_list']['mean'], 2)}")])
if PB:
    S = PB['subsets']['all']
    ysb = sorted(S['by_year'], key=int)
    add('B1: Wikipedia alone predicts the early demand of new books (Test B, interval of W Spearman above 0)',
        [('main', 'all years', above0(S['models']['W_lgbm']), f"W Spearman {ci(S['models']['W_lgbm'])}"),
         ('R3', 'each test year', all(above0(S['by_year'][y]['models']['W_lgbm']) for y in ysb), f"interval above 0 in {sum(above0(S['by_year'][y]['models']['W_lgbm']) for y in ysb)} of {len(ysb)} years")])
    nsets = sum(above0(PB['subsets'][s_]['diffs']['LpW_minus_Lp']) for s_ in ('all', 'matched', 'writer_type'))
    add('B2: Wikipedia adds to the library model for new books (Test B, LW minus L above 0)',
        [('main', 'all years', above0(S['diffs']['LW_minus_L']), f"LW minus L {ci(S['diffs']['LW_minus_L'], lambda x: f3(x, 4))}"),
         ('R3', 'each test year', all(above0(S['by_year'][y]['diffs']['LW_minus_L']) for y in ysb),
          f"interval above 0 in {sum(above0(S['by_year'][y]['diffs']['LW_minus_L']) for y in ysb)} of {len(ysb)} years, point value above 0 in {sum(S['by_year'][y]['diffs']['LW_minus_L']['mean'] > 0 for y in ysb)}"),
         ('R5', 'library model L+ (with the theme)', nsets == 3, f"L+W minus L+ {ci(S['diffs']['LpW_minus_Lp'], lambda x: f3(x, 4))} (all books); interval above 0 in {nsets} of 3 book sets"),
         ('R5', 'library model L-q (no theme, added)', all(above0(PB['subsets'][s_]['diffs']['LqW_minus_Lq']) for s_ in ('all', 'matched', 'writer_type')),
          f"LqW minus Lq {ci(S['diffs']['LqW_minus_Lq'], lambda x: f3(x, 4))} (all books)")])
for var in D_VARIANTS:
    S = PD[var]['scopes']
    lbl = 'Test D' + (' (corrected)' if var == 'corrected' else (' (uncorrected run)' if 'corrected' not in D_VARIANTS else ' (original)'))
    cells = [(k, fl) for k in ('top20', 'top50') for fl in ('rose25', 'rose50', 'rose100')]
    s0 = S['all|2019-2026']
    n_h = sum(s0['lists']['HW'][k][fl]['rate'] >= s0['lists']['H'][k][fl]['rate'] - TIE for k, fl in cells)
    n_w = sum(s0['lists']['W'][k][fl]['rate'] > s0['base'][fl] for k, fl in cells)
    n_hk = sum(s0['lists']['HW'][f'top{k}']['rose50']['rate'] >= s0['lists']['H'][f'top{k}']['rose50']['rate'] - TIE for k in (10, 20, 50, 100))
    n_wk = sum(s0['lists']['W'][f'top{k}']['rose50']['rate'] > s0['base']['rose50'] for k in (10, 20, 50, 100))
    add(f'{lbl}: Wikipedia alone beats the base rate; library + Wikipedia is not below the library list (differences under 0.5 points are ties)',
        [('R1', 'rise of 25%, 50%, 100%; top 20 and 50', n_h == len(cells) and n_w == len(cells), f"HW not more than 0.5 points below H in {n_h} of {len(cells)} cells; W above the base rate in {n_w} of {len(cells)}"),
         ('R7', 'top 10, 20, 50, 100 (rise of 50%)', n_hk == 4 and n_wk == 4, f"HW not more than 0.5 points below H at {n_hk} of 4 lengths; W above the base rate at {n_wk} of 4")])

    def q90(fl, k, per):
        return all(S[f'{sc}|{per}']['lists']['HW'][f'top{k}'][fl]['rate'] >= 0.9 for sc in FMTS)

    def nfmt(fl, k, per):
        return sum(S[f'{sc}|{per}']['lists']['HW'][f'top{k}'][fl]['rate'] >= 0.9 for sc in FMTS)

    main90 = {per: q90('rose50', 20, per) for per in ('2019-2026', '2024-2026')}
    r1_ok = all(q90(fl, 20, per) == main90[per] for fl in ('rose25', 'rose100') for per in main90)
    r7_ok = all(q90('rose50', k, per) == main90[per] for k in (10, 50, 100) for per in main90)
    add(f'{lbl}: the 90% question (library + Wikipedia, top 20, rise of 50%: at least 90% in every format; answer for 2019-2026 and 2024-2026)',
        [('main', 'top 20, rise of 50%', True, '; '.join(f"{per}: {'yes' if main90[per] else 'no'} ({nfmt('rose50', 20, per)} of 3 formats)" for per in main90)),
         ('R1', 'rise of 25% and 100% (top 20)', r1_ok, '; '.join(f"{lab} {per}: {'yes' if q90(fl, 20, per) else 'no'} ({nfmt(fl, 20, per)} of 3)" for fl, lab in (('rose25', '25%'), ('rose100', '100%')) for per in main90)),
         ('R7', 'top 10, 50, 100 (rise of 50%)', r7_ok, '; '.join(f"top {k} {per}: {'yes' if q90('rose50', k, per) else 'no'} ({nfmt('rose50', k, per)} of 3)" for k in (10, 50, 100) for per in main90))])
    J['R7'][f'test_d_{var}_90'] = {f'top{k}|{fl}|{per}': dict(formats_at_least_90=nfmt(fl, k, per), of=3) for k in (10, 20, 50, 100) for fl in ('rose25', 'rose50', 'rose100') for per in main90}

COLS = ['main', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7']
changes = [dict(decision=dd['decision'], column=c['column'], check=c['check'], detail=c['detail']) for dd in J['decisions'] for c in dd['checks'] if not c['holds']]
J['any_conclusion_changes'] = changes
n_cells = sum(len(dd['checks']) for dd in J['decisions'])
def short(d):
    return d.split(':')[0] if d.split(':')[0][:1] in 'AB' and len(d.split(':')[0]) <= 3 else d.split(' (')[0]


affected = [dd['decision'] for dd in J['decisions'] if any(not c['holds'] for c in dd['checks'])]
clean_ = [dd['decision'] for dd in J['decisions'] if all(c['holds'] for c in dd['checks'])]
J['decisions_unchanged'] = clean_
J['decisions_with_a_change'] = affected
if not changes:
    w(f"**No.** Every decision rule of the records and every headline alert result comes out the same way under each of the {n_cells} alternative choices checked.", '')
else:
    w(f"Of {n_cells} comparisons, {n_cells - len(changes)} come out the same way as the main result and {len(changes)} do not. "
      f"Results with no change in any check: {'; '.join(short(d) for d in clean_) if clean_ else 'none'}. "
      f"Results with at least one change: {'; '.join(short(d) for d in affected)}. The changes are listed under the table.", '')
w('Each row is a decision rule of the records or a headline result of the alert lists. A cell says "holds" when the result comes out the same way under the alternative choice of that check, '
  '"**changes**" when it does not, and is empty when the check does not apply. Details follow the table.', '')
rows = []
for dd in J['decisions']:
    cells_ = []
    for col in COLS:
        its = [c for c in dd['checks'] if c['column'] == col]
        cells_.append('' if not its else ('holds' if all(c['holds'] for c in its) else '**changes**'))
    rows.append([dd['decision']] + cells_)
w(table(['Decision or result'] + COLS, rows), '')
if changes:
    w('**Where a result changes**', '')
    for c in changes:
        w(f"- {c['decision']} | {c['column']}, {c['check']}: {c['detail']}")
    w('')
w('**Detail of every comparison**', '')
rows = []
for dd in J['decisions']:
    for c in dd['checks']:
        rows.append([dd['decision'], c['column'], c['check'], 'holds' if c['holds'] else '**changes**', c['detail']])
w(table(['Decision or result', 'Check', 'Compared', 'Result', 'Detail'], rows), '')

# ======================================================================================== notes
w('## Notes', '')
notes = []
if PAO:
    # reproduction of the already reported alert list by this code, on the original files
    ref = pd.read_csv(REP / 'wiki_led_test_a_alert_list.csv', index_col=[0, 1])
    pairs = [('Wlgbm_D', 'Wikipedia only'), ('Wrule_D', 'Wikipedia rule (no fitting)'), ('Hlgbm_D', 'Library record'), ('HWlgbm_D', 'Library + Wikipedia')]
    diffs = []
    for m, nm in pairs:
        for k in (20, 50):
            diffs.append(abs(PAO['lists']['models'][m][f'top{k}']['rose50']['mean'] - float(ref.loc[(nm, str(k)), 'rose'])))
            diffs.append(abs(PAO['lists']['models'][m][f'top{k}']['surged']['mean'] - float(ref.loc[(nm, str(k)), 'surged'])))
    J['code_check_test_a_original_alert_list'] = dict(max_abs_diff=float(max(diffs)), cells=len(diffs))
    notes.append(f"Code check: run on the original Test A files, this code reproduces the stored alert list (`wiki_led_test_a_alert_list.csv`, top 20 and top 50, 'rose' and 'surged', four models) to within {max(diffs):.4f} "
                 "(the small gaps come from the order of tied predictions).")
if PD and PD.get('original'):
    st = json.loads((REP / 'wiki_led_test_d.json').read_text())
    d2 = []
    for m in ('W', 'H', 'HW', 'naive'):
        for k in (20, 50):
            d2.append(abs(PD['original']['scopes']['all|2019-2026']['lists'][m][f'top{k}']['rose50']['rate'] - st['alert'][f'all|{m}'][f'top{k}']['rose']))
    J['code_check_test_d'] = dict(max_abs_diff=float(max(d2)), rows_exact50_differs_from_stored_rose=PD['original']['rows_exact50_differs_from_stored_rose'], rows=PD['original']['rows'])
    notes.append(f"Code check: Test D hit rates at 50% (all formats, top 20 and top 50, four models) agree with `wiki_led_test_d.json` to within {max(d2):.4f}; "
                 f"the exact 50% rise flag differs from the stored `rose` column in {PD['original']['rows_exact50_differs_from_stored_rose']} of {PD['original']['rows']:,} rows.")
if PB:
    stb = json.loads((REP / 'wiki_led_test_b.json').read_text())['all']['LW_minus_L']
    mine = PB['subsets']['all']['diffs']['LW_minus_L']
    J['code_check_test_b'] = dict(refit_max_abs_diff=PB['refit_check_max_abs_diff'], stored=stb, here=mine)
    notes.append(f"Code check: the refitted W, L and LW predictions of Test B equal the stored ones (largest difference {max(PB['refit_check_max_abs_diff'].values()):.1e}), "
                 f"and the LW minus L interval here ({f3(mine['lo'], 4)} to {f3(mine['hi'], 4)}) {'equals' if abs(mine['lo'] - stb['lo']) < 1e-9 and abs(mine['hi'] - stb['hi']) < 1e-9 else 'differs from'} "
                 f"the stored one ({f3(stb['lo'], 4)} to {f3(stb['hi'], 4)}).")
notes.append('Beyond the text of addendum e (descriptive additions, not used for any choice): the top-50 and top-100 lists and the surge outcome in R1 and R7; the naive library list and the 25% and 100% rises in R6 (the latter in the JSON only); '
             'the "no theme" models in R5; the matched and writer subsets in R5 (the sets of decision B3); the three months alone in R4.')
notes.append('R5: the theme is built from catalogue subject records that are not dated. Any look-ahead in it makes the library model stronger, which works against Wikipedia, so R5 is hard on Wikipedia on this point.')
for n in notes:
    w('- ' + n)
w('')
w(f"Run time and memory are in the part files (`data/db/wiki_led/robustness_part_*.json`).", '')

J['peak_gb'] = {n: (v or {}).get('peak_gb') for n, v in (('b', PB), ('a_seeds', PS))}
OUT_MD.write_text('\n'.join(L))
from json import dumps


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


OUT_JSON.write_text(dumps(clean(J), indent=1))
print('wrote', OUT_MD, 'and', OUT_JSON, '| conclusions that change:', len(J['any_conclusion_changes']))
