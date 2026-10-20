# 91. Report of the checks R1 to R7 (addendum e): merges the part files of 90_robustness.py into
#   data/reports/wiki_led_robustness.json  and  data/reports/wiki_led_robustness.md
# Every number in both files is read from the part files; the sentences only choose between fixed wordings by comparing numbers.
# Run from code/ with ../.venv/bin/python main_study/wiki_led/91_robustness_report.py   (after parts b, d, a and a_seeds of 90_robustness.py)
# ROB_OUT=PATH: a code test only; writes PATH.json and PATH.md instead of the two files in data/reports.
# Review of 20 Oct 2026 (about 21:30 +07): a short plain-English answer at the top; Test D original and corrected side by side; R5 also
# with the catalogue features rebuilt from the records first lent in the work's first month (L+0) and without the theme (Lq), because the
# features as fixed use records of all years; wording of R1 and R4 to R7 re-read against the numbers.
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
TEST = os.environ.get('ROB_OUT')
OUT_JSON = pathlib.Path(TEST + '.json') if TEST else REP / 'wiki_led_robustness.json'
OUT_MD = pathlib.Path(TEST + '.md') if TEST else REP / 'wiki_led_robustness.md'
TIE = 0.005      # alert-list differences under 0.5 points count as ties (the tie rule of addendum c)


def part(name):
    f = OUT / f'robustness_part_{name}.json'
    return json.loads(f.read_text()) if f.exists() else None


PA = part('a')
PS = part('a_seeds')
PB = part('b')
PD = part('d')
PAO = part('a_orig')
missing = [n for n, v in (('a (Test A, corrected)', PA), ('a_seeds (R2)', PS), ('b (Test B)', PB), ('d (Test D)', PD)) if v is None]
assert PB is None or 'L0_lgbm' in PB['models'], 'part b predates the review (no L0 model): rerun 90_robustness.py b'

NAMES_A = {'Wlgbm_D': 'Wikipedia only (W)', 'Wrule_D': 'Wikipedia rule (no fitting)', 'Hlgbm_D': 'Library history (H)',
           'HWlgbm_D': 'Library + Wikipedia (HW)', 'Hnaive_D': 'Repeat last month (naive)', 'Wridge_D': 'Wikipedia only (ridge)'}
NAMES_D = {'W': 'Wikipedia only (W)', 'H': 'Library history (H)', 'HW': 'Library + Wikipedia (HW)', 'naive': 'Repeat last month (naive)'}
THR_LABEL = {'rose25': 'rose by 25%', 'rose50': 'rose by 50%', 'rose100': 'rose by 100%', 'surged': 'surged'}
FMTS = ['print', 'ebook', 'audiobook']
PERIODS = ('2019-2026', '2024-2026')
KS = (10, 20, 50, 100)
THR3 = ('rose25', 'rose50', 'rose100')


# ---------------------------------------------------------------------------------------- formatting
def pc(x, d=1):
    return 'n/a' if x is None else f'{100 * x:.{d}f}%'


def f3(x, d=3):
    return 'n/a' if x is None else f'{x:.{d}f}'


def f2(x):
    return f3(x, 2)


def f4(x):
    return f3(x, 4)


def sg(x, d=4):
    """Signed number that never prints as -0.000."""
    v = round(float(x), d)
    return f'{0:.{d}f}' if v == 0 else f'{v:+.{d}f}'


def pts(x, d=1):
    """A difference between two shares, in points, signed."""
    return sg(100 * x, d) + ' points'


def ci(d, fmt=f3):
    if d is None:
        return 'n/a'
    m = d['mean'] if 'mean' in d else d['spearman']
    if d.get('lo') is None:
        return fmt(m)
    return f"{fmt(m)} ({fmt(d['lo'])} to {fmt(d['hi'])})"


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
    """Markdown table; align is a string with one letter per column: l, r or c (default: first column left, the others right)."""
    align = align or 'l' + 'r' * (len(head) - 1)
    sep = {'l': ':---', 'r': '---:', 'c': ':---:'}
    out = ['| ' + ' | '.join(head) + ' |', '| ' + ' | '.join(sep[a] for a in align) + ' |']
    for r in rows:
        out.append('| ' + ' | '.join(str(c) for c in r) + ' |')
    return '\n'.join(out)


def above0(d):
    return d is not None and d.get('lo') is not None and d['lo'] > 0


def has_ci(d):
    return d.get('lo') is not None


L = []          # markdown lines of the body
TOP = []        # the short answer, written last and placed at the top


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
J['test_d_files'] = {v: PD[v].get('files') for v in D_VARIANTS}
J['test_d_rows_check_corrected_against_original'] = PD['corrected'].get('rows_check_against_original') if 'corrected' in D_VARIANTS else None
BOTH = len(D_VARIANTS) == 2
DV_HEAD = ' / '.join(D_VARIANTS)          # 'original / corrected'


def dlabel(var):
    return 'Test D, corrected' if var == 'corrected' else ('Test D, original' if BOTH else 'Test D, original run')


def dcell(get, fmt=pc):
    """One value per Test D variant, side by side: 'original / corrected'."""
    return ' / '.join(fmt(get(PD[v])) for v in D_VARIANTS)


def cellsA(m, k, fl):
    return PA['lists']['models'][m][f'top{k}'][fl]


def dscope(v, sc='all', per='2019-2026'):
    return PD[v]['scopes'][f'{sc}|{per}']


# ======================================================================================== header
HEAD = ['# Wikipedia-led tests: how much do the results depend on one choice? (checks R1 to R7)', '',
        'Khant Phyo Wai, 01323050.', '',
        f"Made {J['made']} by `code/main_study/wiki_led/90_robustness.py` (the numbers) and `91_robustness_report.py` (this file). "
        f"The seven checks are fixed in `prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json` (SHA-256 `{ADD_SHA}`). "
        "Every number is in `data/reports/wiki_led_robustness.json`.", '']
if TEST:
    HEAD += ['**CODE TEST OUTPUT, not the final file.**', '']
if missing:
    HEAD += ['**Parts not yet available when this file was made: ' + ', '.join(missing) + '.**', '']
d_text = ('**Test D** was not available.' if not PD else
          ('**Test D** is shown for the original predictions (`test_d_preds.parquet`) and the corrected ones (`test_d_preds_c.parquet`, rows `test_d_rows_c.parquet`) side by side, written "original / corrected".' if BOTH else
           '**Test D** is reported on the original predictions (`test_d_preds.parquet`) only: the corrected predictions did not exist when this file was made, so the Test D numbers are those of the uncorrected run.'))
w('## What this is', '',
  'Each check changes one choice and looks at how the reported results move: the size of a rise that counts, the random seed, the test year, '
  'three months of unusual Wikipedia traffic, a stronger library model for new books, and the length of the alert list. '
  'The checks are descriptive. Nothing was tuned, and no setting of any model or alert list was chosen from these numbers.', '',
  '- **Models.** W: Wikipedia features only (tree model, no library input). H: the book\'s own library history only (trees). HW: both. In Test B, L is the library model, W Wikipedia and LW both. '
  '"Naive" repeats last month\'s change; "rule" is the no-fitting Wikipedia rule of Test A.',
  '- **Measures.** Change rank: the mean over months of the Spearman correlation between predicted and actual change in loans (Test B: Spearman between predicted and actual loans in the first six months, inside each test year). '
  'Surge AP ratio: average precision for surges divided by the share of surges, so 1 means no better than chance.',
  '- **Rose by X%** means next month\'s loans are at least X% above the book\'s recent normal (M6, the median of its last six months), compared as ln(1 + loans) differences like everywhere else in the tests; 50% is the size used in the alert tables so far. '
  '**Surged** is the original surge flag (at least double and at least 5 more loans than normal).',
  '- **Top k list** is the k books with the highest predicted rise in a month (Test D: within each format and month). **Hit rate** is the share of list places taken by a book that rose. '
  '**Base rate** is the share of all books that rose, which is what a randomly picked list would score (Test A: averaged over months; Test D: over all rows, as in the Test D report).',
  '- **Data.** **Test A** uses the corrected files (`test_a_rows_c.parquet`, `test_a_preds_c.parquet`: weeks before an article existed are missing, not zero). ' + d_text + ' **Test B** is unaffected by the correction.',
  '- **Intervals** are 95% from 2,000 draws with seed 20261020: blocks of 3 consecutive months for Test A, author clusters for Test B (as `30_test_b.py`), exact binomial limits over list places for Test D (as addendum d). '
  'A test year holds 5 to 12 scored months, so by-year intervals are rough; a set of fewer than 6 months gets no interval.',
  '- **Choices the addendum leaves open**, fixed here before looking: ties in a prediction are broken by one fixed random order (seed 20261020); the rise threshold is compared exactly, with equality counted '
  '(the stored single-precision flag differs from this in 3 of 1,984,302 Test D rows at 50%); R1 uses the top 20 and top 50 lists, the sizes of the earlier alert tables; '
  'in R6 the library model is the library-only tree model (H).', '')

# ======================================================================================== R1
w('## R1. How big a rise counts (25%, 50%, 100%)', '',
  'Hit rate of the top 20 and top 50 lists when a rise is counted from 25%, 50% or 100% above the normal. The last row of each block is the base rate.', '')
r1 = {}
if PA:
    rows = []
    for k in (20, 50):
        for m in ['Wlgbm_D', 'Wrule_D', 'Hlgbm_D', 'HWlgbm_D', 'Hnaive_D']:
            rows.append([f'top {k}', NAMES_A[m]] + [cip(cellsA(m, k, fl)) for fl in THR3])
        rows.append([f'top {k}', '*base rate (any book)*'] + [pc(PA['lists']['base_monthly_mean'][fl]) for fl in THR3])
    w('**Test A**', '', table(['List', 'Model', 'Rose by 25%', 'Rose by 50%', 'Rose by 100%'], rows, 'llrrr'), '')
    r1['test_a'] = {f'top{k}': {m: {fl: PA['lists']['models'][m][f'top{k}'][fl] for fl in THR3} for m in NAMES_A} for k in (20, 50)}
    r1['test_a']['base_pooled'] = PA['lists']['base_pooled']
    r1['test_a']['base_monthly_mean'] = PA['lists']['base_monthly_mean']
if D_VARIANTS:
    rows = []
    for k in (20, 50):
        for m in ['W', 'H', 'HW', 'naive']:
            rows.append([f'top {k}', NAMES_D[m]] + [dcell(lambda P, m=m, k=k, fl=fl: P['scopes']['all|2019-2026']['lists'][m][f'top{k}'][fl]['rate']) for fl in THR3])
        rows.append([f'top {k}', '*base rate (any book)*'] + [dcell(lambda P, fl=fl: P['scopes']['all|2019-2026']['base'][fl]) for fl in THR3])
    hwd = {k: max((c['hi'] - c['lo']) / 2 for v in D_VARIANTS for m in NAMES_D for fl in THR3 for c in [dscope(v)['lists'][m][f'top{k}'][fl]]) for k in (20, 50)}
    r1['test_d_max_half_width'] = hwd
    w(f"**Test D, all formats, 2019-2026** ({DV_HEAD}; the exact 95% intervals, in the JSON, are at most plus or minus {100 * hwd[20]:.1f} points for a top 20 and {100 * hwd[50]:.1f} for a top 50)", '',
      table(['List', 'Model', 'Rose by 25%', 'Rose by 50%', 'Rose by 100%'], rows, 'llrrr'), '')
    for var in D_VARIANTS:
        r1[f'test_d_{var}'] = {sc: {'base': v['base'], 'base_group_mean': v.get('base_group_mean'),
                                    'lists': {m: {k: {fl: v['lists'][m][k][fl] for fl in THR3} for k in ('top20', 'top50')} for m in NAMES_D}}
                               for sc, v in PD[var]['scopes'].items()}
J['R1'] = r1
if PA:
    cells = [(k, fl) for k in (20, 50) for fl in THR3]
    hw_ge_h = sum(cellsA('HWlgbm_D', k, fl)['mean'] >= cellsA('Hlgbm_D', k, fl)['mean'] - TIE for k, fl in cells)
    hw_gt_h = sum(cellsA('HWlgbm_D', k, fl)['mean'] > cellsA('Hlgbm_D', k, fl)['mean'] for k, fl in cells)
    h_gt_w = sum(cellsA('Hlgbm_D', k, fl)['mean'] > cellsA('Wlgbm_D', k, fl)['mean'] for k, fl in cells)
    w_gt_rule = sum(cellsA('Wlgbm_D', k, fl)['mean'] > cellsA('Wrule_D', k, fl)['mean'] for k, fl in cells)
    w_lift = {fl: cellsA('Wlgbm_D', 20, fl)['mean'] / PA['lists']['base_monthly_mean'][fl] for fl in THR3}
    w_above_base = all(cellsA('Wlgbm_D', k, fl)['mean'] > PA['lists']['base_monthly_mean'][fl] for k, fl in cells)
    rising = w_lift['rose25'] < w_lift['rose50'] < w_lift['rose100']
    J['R1']['reading'] = dict(test_a_cells=len(cells), hw_not_below_h=int(hw_ge_h), hw_above_h=int(hw_gt_h), h_above_w=int(h_gt_w), w_above_rule=int(w_gt_rule),
                              w_top20_lift=w_lift, w_above_base_everywhere=bool(w_above_base), lift_rises_with_threshold=bool(rising))
    w(f"- Test A: the Wikipedia-only list is above the base rate in {'all' if w_above_base else 'not all'} {len(cells)} cells. "
      f"Its top-20 hit rate is {w_lift['rose25']:.1f} times the base rate at 25%, {w_lift['rose50']:.1f} times at 50% and {w_lift['rose100']:.1f} times at 100%"
      + (", so a stricter rise makes the list look better against chance even though its hit rate falls." if rising else "."),
      f"- Test A: the library list (H) is above the Wikipedia-only list in {h_gt_w} of {len(cells)} cells, and the Wikipedia-only list is above the no-fitting rule in {w_gt_rule} of {len(cells)}. "
      f"Library + Wikipedia is above the library list in {hw_gt_h} of {len(cells)} cells (and not more than 0.5 points below it in {hw_ge_h} of {len(cells)}).")
for var in D_VARIANTS:
    S = dscope(var)
    cells = [(k, fl) for k in ('top20', 'top50') for fl in THR3]
    hw_ge_h = sum(S['lists']['HW'][k][fl]['rate'] >= S['lists']['H'][k][fl]['rate'] - TIE for k, fl in cells)
    w_above = all(S['lists']['W'][k][fl]['rate'] > S['base'][fl] for k, fl in cells)
    lift = {fl: S['lists']['W']['top20'][fl]['rate'] / S['base'][fl] for fl in THR3}
    J['R1'].setdefault('reading_test_d', {})[var] = dict(hw_not_below_h=int(hw_ge_h), cells=len(cells), w_above_base_everywhere=bool(w_above), w_top20_lift=lift)
if D_VARIANTS:
    rd = J['R1']['reading_test_d']
    w(("- Test D, all formats: the Wikipedia-only list is above the base rate in every cell of " + ' and of '.join(f'the {v} run' for v in D_VARIANTS)
       if all(rd[v]['w_above_base_everywhere'] for v in D_VARIANTS) else "- Test D, all formats: the Wikipedia-only list is not above the base rate in every cell")
      + ' (top-20 hit rate over the base rate at 25%, 50% and 100%: ' + '; '.join(f"{v} {rd[v]['w_top20_lift']['rose25']:.1f}, {rd[v]['w_top20_lift']['rose50']:.1f} and {rd[v]['w_top20_lift']['rose100']:.1f} times" for v in D_VARIANTS)
      + '). Library + Wikipedia is not more than 0.5 points below the library list in ' + ' and '.join(f"{rd[v]['hw_not_below_h']} of {rd[v]['cells']} cells ({v})" for v in D_VARIANTS) + '.')
    if BOTH:
        Wo, Wc = dscope('original')['lists']['W']['top20']['rose50']['rate'], dscope('corrected')['lists']['W']['top20']['rose50']['rate']
        Ho, Hc = dscope('original')['lists']['H']['top20']['rose50']['rate'], dscope('corrected')['lists']['H']['top20']['rose50']['rate']
        J['R1']['test_d_correction'] = dict(W_top20_rose50=dict(original=Wo, corrected=Wc), H_top20_rose50=dict(original=Ho, corrected=Hc))
        w(f"- The correction moves the Wikipedia-only top 20 from {pc(Wo)} to {pc(Wc)} at a 50% rise. The library list is the same in both runs ({pc(Ho)} and {pc(Hc)}), as it should be: it uses no Wikipedia input.")
w('')

# ======================================================================================== R2
w('## R2. Five random seeds (Test A, corrected rows)', '',
  'W, H and HW were refitted five times with the same settings and walk-forward as `10_test_a.py`, changing only the seed of the tree models (20261020 to 20261024). '
  'The top-20 hit rate counts rises of 50%.', '')
sd = PS['seeds'] if PS and PS.get('seeds') else None
summ = None
if sd:
    seeds = sorted(sd)
    M3 = ('Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D')
    rows = []
    for s in seeds:
        d = sd[s]
        rows.append([s] + [f4(d['change_rank'][m]) for m in M3] + [f4(d['HW_minus_H_change_rank'])] + [pc(d['top20_rose50'][m]) for m in M3])

    def arr(key, m):
        return np.array([sd[s][key][m] for s in seeds])

    summ = {}
    for key in ('change_rank', 'top20_rose50', 'top20_surged', 'surge_ap_ratio'):
        summ[key] = {m: dict(mean=float(arr(key, m).mean()), sd=float(arr(key, m).std(ddof=1)) if len(seeds) > 1 else None, min=float(arr(key, m).min()),
                             max=float(arr(key, m).max()), range=float(arr(key, m).max() - arr(key, m).min())) for m in M3}
    gap = np.array([sd[s]['HW_minus_H_change_rank'] for s in seeds])
    summ['HW_minus_H'] = dict(mean=float(gap.mean()), min=float(gap.min()), max=float(gap.max()), range=float(gap.max() - gap.min()))
    rows.append(['**mean**'] + [f4(summ['change_rank'][m]['mean']) for m in M3] + [f4(gap.mean())] + [pc(summ['top20_rose50'][m]['mean']) for m in M3])
    rows.append(['**range (highest minus lowest)**'] + [f4(summ['change_rank'][m]['range']) for m in M3] + [f4(summ['HW_minus_H']['range'])]
                + [f"{100 * summ['top20_rose50'][m]['range']:.1f} points" for m in M3])
    w(table(['Seed', 'W change rank', 'H change rank', 'HW change rank', 'HW minus H', 'W top-20 hit', 'H top-20 hit', 'HW top-20 hit'], rows, 'lrrrrrrr'), '')
    J['R2'] = dict(seeds=sd, summary=summ, n_seeds=len(seeds))
    if len(seeds) < 5:
        w(f"*Only {len(seeds)} of 5 seeds were finished when this file was made.*", '')
    ref = PA['R4_bot_months']['all_months'] if PA else None
    if ref:
        hwid = {m: (ref['change_rank'][m]['hi'] - ref['change_rank'][m]['lo']) / 2 for m in M3}
        hw_gap = (ref['paired']['HW_minus_H']['hi'] - ref['paired']['HW_minus_H']['lo']) / 2
        ratio = summ['change_rank']['Wlgbm_D']['range'] / hwid['Wlgbm_D']
        J['R2']['half_width_of_month_block_interval'] = dict(change_rank=hwid, HW_minus_H=hw_gap)
        J['R2']['w_seed_range_over_half_width'] = ratio
        w(f"- The {len(seeds)} seeds differ by at most {f4(summ['change_rank']['Wlgbm_D']['range'])} in W change rank, {f4(summ['change_rank']['Hlgbm_D']['range'])} in H and "
          f"{f4(summ['change_rank']['HWlgbm_D']['range'])} in HW. The month-block 95% interval of the main run is about plus or minus "
          f"{f3(hwid['Wlgbm_D'])} for W, {f3(hwid['Hlgbm_D'])} for H and {f3(hwid['HWlgbm_D'])} for HW, so the seed spread in W is {ratio:.2f} times that half-width.",
          f"- HW minus H is above zero in {int((gap > 0).sum())} of {len(seeds)} seeds (lowest {f4(gap.min())}, highest {f4(gap.max())}; the half-width of its month-block interval is {f4(hw_gap)}).",
          f"- The top-20 hit rate moves by up to {100 * summ['top20_rose50']['Wlgbm_D']['range']:.1f} points for W, {100 * summ['top20_rose50']['Hlgbm_D']['range']:.1f} for H "
          f"and {100 * summ['top20_rose50']['HWlgbm_D']['range']:.1f} for HW between seeds; the W surge AP ratio runs from {f2(summ['surge_ap_ratio']['Wlgbm_D']['min'])} to {f2(summ['surge_ap_ratio']['Wlgbm_D']['max'])}.")
    first = sd[seeds[0]]
    if 'max_abs_diff_to_stored' in first:
        w(f"- Check: the refit with seed {seeds[0]} reproduces the stored corrected predictions (largest difference {max(first['max_abs_diff_to_stored'].values()):.1e}).")
    w('')
else:
    w('*Not yet available.*', '')
    J['R2'] = None

# ======================================================================================== R3
w('## R3. By test year', '',
  'Test A: the headline measures inside each test year (the year of the month being predicted; 2019 starts with origin 2019-01; 2026 has origins 2025-12 to 2026-07). '
  'Test B: the same for new books, by year of their first library month.', '')
J['R3'] = {}
pm_note = None
if PA:
    R3 = PA['R3_years']
    ys = sorted(R3, key=int)
    rows = []
    for y in ys:
        d = R3[y]
        rows.append([y, d['n_months'], pc(d['base_rose50']), f3(d['change_rank']['Wlgbm_D']['mean']), f3(d['change_rank']['Hlgbm_D']['mean']), f3(d['change_rank']['HWlgbm_D']['mean']),
                     ci(d['paired']['HW_minus_H'], f4), f2(d['surge_ap']['Wlgbm_D']['ratio']),
                     pc(d['alert']['top20']['Wlgbm_D']['rose50']['mean']), pc(d['alert']['top20']['Hlgbm_D']['rose50']['mean']), pc(d['alert']['top20']['HWlgbm_D']['rose50']['mean'])])
    w('**Test A**', '', table(['Year', 'Months', 'Base rate (50%)', 'W change rank', 'H change rank', 'HW change rank', 'HW minus H (interval)', 'W surge AP ratio', 'W top-20 hit', 'H top-20 hit', 'HW top-20 hit'], rows,
                              'lrrrrrrrrrr'), '')
    J['R3']['test_a'] = R3
    short_years = [y for y in ys if R3[y]['n_months'] < 8]
    n_w = sum(R3[y]['change_rank']['Wlgbm_D']['mean'] > 0 for y in ys)
    with_ci = [y for y in ys if has_ci(R3[y]['change_rank']['Wlgbm_D'])]
    n_w_int = sum(above0(R3[y]['change_rank']['Wlgbm_D']) for y in with_ci)
    n_hw = sum(R3[y]['paired']['HW_minus_H']['mean'] > 0 for y in ys)
    n_hw_int = sum(above0(R3[y]['paired']['HW_minus_H']) for y in with_ci)
    n_ap = sum(R3[y]['surge_ap']['Wlgbm_D']['ratio'] > 1 for y in ys)
    n_alert = sum(R3[y]['alert']['top20']['Wlgbm_D']['rose50']['mean'] > R3[y]['base_rose50'] for y in ys)
    below = [(y, 100 * (R3[y]['alert']['top20']['HWlgbm_D']['rose50']['mean'] - R3[y]['alert']['top20']['Hlgbm_D']['rose50']['mean']), R3[y]['n_months'])
             for y in ys if R3[y]['alert']['top20']['HWlgbm_D']['rose50']['mean'] < R3[y]['alert']['top20']['Hlgbm_D']['rose50']['mean']]
    wr = [R3[y]['change_rank']['Wlgbm_D']['mean'] for y in ys]
    gp = [R3[y]['paired']['HW_minus_H']['mean'] for y in ys]
    J['R3']['test_a_reading'] = dict(years=len(ys), years_with_interval=len(with_ci), w_rank_positive=int(n_w), w_rank_interval_above0=int(n_w_int), hw_minus_h_positive=int(n_hw),
                                     hw_minus_h_interval_above0=int(n_hw_int), w_surge_ratio_above1=int(n_ap), w_top20_above_base=int(n_alert),
                                     hw_top20_below_h=[dict(year=y, points=p, months=n) for y, p, n in below], w_rank_min=min(wr), w_rank_max=max(wr), hw_minus_h_min=min(gp), hw_minus_h_max=max(gp))
    if short_years:
        w(f"Months: {', '.join(f'{y} has {R3[y]['n_months']}' for y in short_years)} (library months with missing or near-empty data are not scored); "
          f"{'a year' if len(with_ci) == len(ys) - 1 else 'years'} with fewer than 6 months gets no interval.", '')
    w(f"- W change rank is above zero in {n_w} of {len(ys)} years (interval above zero in {n_w_int} of the {len(with_ci)} years that have one); it runs from {f3(min(wr))} ({ys[int(np.argmin(wr))]}) to {f3(max(wr))} ({ys[int(np.argmax(wr))]}).",
      f"- HW minus H is above zero in {n_hw} of {len(ys)} years (interval above zero in {n_hw_int} of {len(with_ci)}); it runs from {f4(min(gp))} ({ys[int(np.argmin(gp))]}) to {f4(max(gp))} ({ys[int(np.argmax(gp))]}).",
      f"- The W surge AP ratio is above 1 in {n_ap} of {len(ys)} years, and the W top-20 hit rate is above that year's base rate in {n_alert} of {len(ys)}.")
    if below:
        w("- HW's top-20 hit rate is below H's in " + ' and in '.join(f"{y} by {abs(p):.1f} points ({n} scored months{', under 0.5 points, a tie by the rule of addendum c' if abs(p) < 100 * TIE else ''})" for y, p, n in below) + '.')
    else:
        w("- HW's top-20 hit rate is at least H's in every year.")
    # month-by-month detail of the top-20 lists (added in review)
    PM = PA.get('per_month_top20_rose50')
    if PM:
        yr = np.array(PM['test_year'])
        dH = np.array(PM['HWlgbm_D']) - np.array(PM['Hlgbm_D'])
        J['R3']['test_a_per_month_hw_minus_h_top20_places'] = dict(origin_month=PM['origin_month'], test_year=PM['test_year'], places=dH.tolist())
        n_lo, n_eq, n_hi = int((dH < 0).sum()), int((dH == 0).sum()), int((dH > 0).sum())
        n_def2 = int((dH <= -2).sum())
        J['R3']['test_a_months_hw_vs_h_top20'] = dict(below=n_lo, same=n_eq, above=n_hi, months=int(len(dH)), hw_2_or_more_places_behind=n_def2)
        # months of the six-month window behind M6 that are not excluded (excluded months are missing in M6, as in 10c_test_a.py)
        excl = set(json.loads((REP / 'wiki_led_test_a_c.json').read_text())['excluded_months'])

        def m6_months(mo):
            i = int(mo[:4]) * 12 + int(mo[5:7]) - 1
            return sum(f'{j // 12}-{j % 12 + 1:02d}' not in excl for j in range(i - 5, i + 1))

        om = np.array(PM['origin_month'])
        for y, p, n in below:
            sel = yr == int(y)
            seq = ', '.join(f"{mo} {int(v):+d}" if v else f"{mo} 0" for mo, v in zip(om[sel], dH[sel]))
            neg = [dict(origin_month=mo, places=int(v), months_in_m6_window=m6_months(mo)) for mo, v in zip(om[sel], dH[sel]) if v < 0]
            J['R3'].setdefault('per_month_years_below', {})[y] = dict(origin_month=om[sel].tolist(), places=dH[sel].tolist(), months_behind=neg,
                                                                       months_2_or_more_behind=int((dH[sel] <= -2).sum()),
                                                                       hw_places=int(np.array(PM['HWlgbm_D'])[sel].sum()), h_places=int(np.array(PM['Hlgbm_D'])[sel].sum()),
                                                                       list_places=int(20 * sel.sum()), gap_places=int(-dH[sel].sum()))
            w(f"  - {y}, places taken by a book that rose, HW minus H, by origin month: {seq} (list places: {20 * int(sel.sum())}).")
        w(f"- Over all {len(dH)} scored months, the HW top 20 holds more rising books than the H top 20 in {n_hi} months, as many in {n_eq} and fewer in {n_lo}; "
          f"HW is 2 or more places behind in {n_def2} months.")
        pm_note = (n_lo, n_eq, n_hi, len(dH), n_def2)
    w('')
if PB:
    S = PB['subsets']['all']
    ys = sorted(S['by_year'], key=int)
    rows = []
    for y in ys:
        d = S['by_year'][y]
        rows.append([y, f"{d['n']:,}", ci(d['models']['W_lgbm']), ci(d['models']['L_lgbm']), ci(d['models']['LW_lgbm']), ci(d['diffs']['LW_minus_L'], f4),
                     pc(d['models']['W_lgbm']['top10_precision']), pc(d['models']['L_lgbm']['top10_precision']), pc(d['models']['LW_lgbm']['top10_precision'])])
    rows.append(['**all years**', f"{S['n']['rows']:,}", ci(S['models']['W_lgbm']), ci(S['models']['L_lgbm']), ci(S['models']['LW_lgbm']), ci(S['diffs']['LW_minus_L'], f4),
                 pc(S['models']['W_lgbm']['top10_precision']), pc(S['models']['L_lgbm']['top10_precision']), pc(S['models']['LW_lgbm']['top10_precision'])])
    w('**Test B** (top-10% precision: share of the predicted top 10% that is in the actual top 10%; the base rate is 10%)', '',
      table(['Year', 'New books', 'W Spearman', 'L Spearman', 'LW Spearman', 'LW minus L', 'W top-10%', 'L top-10%', 'LW top-10%'], rows, 'lrrrrrrrr'), '')
    J['R3']['test_b'] = {k: v for k, v in S['by_year'].items()}
    J['R3']['test_b_all_years'] = dict(models={k: S['models'][k] for k in ('W_lgbm', 'L_lgbm', 'LW_lgbm')}, diffs={'LW_minus_L': S['diffs']['LW_minus_L']})
    nb1 = sum(above0(S['by_year'][y]['models']['W_lgbm']) for y in ys)
    nb2 = sum(above0(S['by_year'][y]['diffs']['LW_minus_L']) for y in ys)
    nb2p = sum(S['by_year'][y]['diffs']['LW_minus_L']['mean'] > 0 for y in ys)
    wsp = [S['by_year'][y]['models']['W_lgbm']['spearman'] for y in ys]
    gd = [S['by_year'][y]['diffs']['LW_minus_L']['mean'] for y in ys]
    J['R3']['test_b_reading'] = dict(years=len(ys), w_interval_above0=int(nb1), lw_minus_l_positive=int(nb2p), lw_minus_l_interval_above0=int(nb2), w_min=min(wsp), w_max=max(wsp),
                                     lw_minus_l_min=min(gd), lw_minus_l_max=max(gd))
    w(f"- W Spearman has its interval above zero in {nb1} of {len(ys)} years and runs from {f3(min(wsp))} ({ys[int(np.argmin(wsp))]}) to {f3(max(wsp))} ({ys[int(np.argmax(wsp))]}). "
      f"The 2026 books are few ({S['by_year'][ys[-1]]['n']:,}, first months January and February 2026).",
      f"- LW minus L is above zero in {nb2p} of {len(ys)} years (interval above zero in {nb2}); it runs from {f4(min(gd))} ({ys[int(np.argmin(gd))]}) to {f4(max(gd))} ({ys[int(np.argmax(gd))]}).", '')

# ======================================================================================== R4
w('## R4. Without the origin months 2025-04 to 2025-06 (Test A)', '',
  'Wikimedia reported automated traffic counted as user views in those months. The predictions are the same; only the scoring leaves the three origin months out '
  '(the models were not refitted). The last column shows the three months alone, without an interval (three months cannot be resampled in blocks of three).', '')
if PA:
    R4 = PA['R4_bot_months']
    A, B, C = R4['all_months'], R4['without_bot_months'], R4['bot_months_only']
    rows = []
    chg = {}

    def r4row(label, getter, fmt=f3, d=4):
        a, b, c = getter(A), getter(B), getter(C)
        chg[label] = b['mean'] - a['mean']
        rows.append([label, ci(a, fmt), ci(b, fmt), sg(b['mean'] - a['mean'], d), fmt(c['mean'])])

    for m, nm in (('Wlgbm_D', 'W'), ('Hlgbm_D', 'H'), ('HWlgbm_D', 'HW'), ('Hnaive_D', 'naive')):
        r4row(f'{nm} change rank', lambda s, m=m: s['change_rank'][m])
    r4row('HW minus H', lambda s: s['paired']['HW_minus_H'], f4)
    r4row('W minus no-fitting rule', lambda s: s['paired']['W_minus_rule'])
    for m, nm in (('Wlgbm_D', 'W'), ('Hlgbm_D', 'H'), ('HWlgbm_D', 'HW')):
        a, b, c = A['surge_ap'][m], B['surge_ap'][m], C['surge_ap'][m]
        chg[f'{nm} surge AP ratio'] = b['ratio'] - a['ratio']
        rows.append([f'{nm} surge AP ratio', f"{f2(a['ratio'])} ({f2(a['ratio_lo'])} to {f2(a['ratio_hi'])})", f"{f2(b['ratio'])} ({f2(b['ratio_lo'])} to {f2(b['ratio_hi'])})",
                     sg(b['ratio'] - a['ratio'], 2), f2(c['ratio'])])
    for m, nm in (('Wlgbm_D', 'W'), ('Hlgbm_D', 'H'), ('HWlgbm_D', 'HW')):
        a, b, c = A['alert']['top20'][m]['rose50'], B['alert']['top20'][m]['rose50'], C['alert']['top20'][m]['rose50']
        chg[f'{nm} top-20 hit rate (50%)'] = b['mean'] - a['mean']
        rows.append([f'{nm} top-20 hit rate (50%)', cip(a), cip(b), pts(b['mean'] - a['mean']), pc(c['mean'])])
    chg['Base rate of a 50% rise'] = B['base_rose50'] - A['base_rose50']
    rows.append(['Base rate of a 50% rise', pc(A['base_rose50']), pc(B['base_rose50']), pts(B['base_rose50'] - A['base_rose50']), pc(C['base_rose50'])])
    rows.append(['Months scored', A['n_months'], B['n_months'], f"{B['n_months'] - A['n_months']:+d}", C['n_months']])
    w(table(['Measure', 'All scored months', 'Without 2025-04 to 2025-06', 'Change', 'The three months alone'], rows), '')
    J['R4'] = dict(R4)
    J['R4']['changes'] = chg
    a1, a2, a3 = above0(B['change_rank']['Wlgbm_D']), above0(B['paired']['HW_minus_H']), B['surge_ap']['Wlgbm_D']['ratio_lo'] > 1
    wd = B['change_rank']['Wlgbm_D']['mean'] - A['change_rank']['Wlgbm_D']['mean']
    J['R4']['reading'] = dict(a1_holds=bool(a1), a2_holds=bool(a2), a3_holds=bool(a3), w_rank_change=wd)
    w(f"- Without the three months, W change rank moves by {sg(wd)}, HW minus H by {sg(B['paired']['HW_minus_H']['mean'] - A['paired']['HW_minus_H']['mean'])} and the W top-20 hit rate by "
      f"{pts(B['alert']['top20']['Wlgbm_D']['rose50']['mean'] - A['alert']['top20']['Wlgbm_D']['rose50']['mean'])}. "
      f"A1 (W change-rank interval above zero) {'holds' if a1 else 'does not hold'}, A2 (HW minus H interval above zero) {'holds' if a2 else 'does not hold'} and A3 (W surge-ratio interval above 1) {'holds' if a3 else 'does not hold'}.",
      f"- In the three months alone, W change rank is {f3(C['change_rank']['Wlgbm_D']['mean'])} against {f3(A['change_rank']['Wlgbm_D']['mean'])} over all months, and the W top-20 hit rate is "
      f"{pc(C['alert']['top20']['Wlgbm_D']['rose50']['mean'])} against {pc(A['alert']['top20']['Wlgbm_D']['rose50']['mean'])}. Three months are too few to read this as a real difference.",
      "- Limit: the inflated weeks also enter the 26-week normal behind r4, r1 and rmax for about six months after June 2025, and the 2026 models were trained on rows that include the three months; "
      "this check removes only the three origin months from the scoring, as the addendum fixes.", '')
else:
    J['R4'] = None

# ======================================================================================== R5
w('## R5. A stronger library model for new books (Test B)', '',
  'L+ is the library model of Test B plus catalogue information the library has when it acquires a work, as fixed in the addendum: the broad theme (the level-1, or B-level, theme node with the highest strength in '
  '`work_theme.parquet`, or none; where nodes tie, the file\'s own first rank), the first year minus the publication year (`pub_year_min`), and whether the creator came only from the title field. '
  'L+W adds the Wikipedia features. Everything else is as in `30_test_b.py`: the same rows (books whose first month a data gap may have shifted are left out), the same walk-forward, '
  'the same tree settings and the same author-cluster bootstrap with the same draws.', '')
J['R5'] = None
if PB:
    ex = PB['extra_info']
    m0 = ex['month0']
    m0['pub_year_differs_share'] = m0['pub_year_differs'] / m0['works']
    m0['creator_flag_differs_share'] = m0['creator_flag_differs'] / m0['works']
    rd = PB['rows']
    lb, lb0, lbt = ex['loans6_by_age0'], ex['loans6_by_age0_m0'], ex['loans6_by_theme_present']
    w('**Are the three features known when a book arrives? Not fully (found in the review of 20 Oct 2026).** '
      f"They are built from the work's catalogue records, and a record shows up in the Seattle data only when it is first lent. {pc(m0['works_with_records_first_lent_after_month0'])} of the works have a record first lent after the work's first month "
      f"({pc(m0['works_with_records_first_lent_after_month5'])} after month 5, that is after the six-month outcome window), and the features as fixed use records of all years:", '',
      f"- **Theme:** {pc(ex['works_with_theme'])} of the works have one as fixed, but only {pc(ex['works_with_theme_m0'])} when it is built from the records first lent in the work's first month. "
      f"{m0['theme_only_from_later_records']:,} works get their theme only from later records and {m0['theme_different_node']:,} get a different one. Having a theme as fixed goes with more early loans: "
      f"works with a theme had a median of {lbt['as_fixed']['yes']['median_loans6']:.0f} loans in their first six months and works without one {lbt['as_fixed']['no']['median_loans6']:.0f}; "
      f"with the first-month theme the medians are {lbt['month0']['yes']['median_loans6']:.0f} and {lbt['month0']['no']['median_loans6']:.0f}. So the theme as fixed partly carries the outcome.",
      f"- **Publication year:** the gap differs for {m0['pub_year_differs']:,} works ({pc(m0['pub_year_differs_share'])}). **Title-only creator:** differs for {m0['creator_flag_differs']:,} works ({pc(m0['creator_flag_differs_share'])}).", '',
      '**Two added library models, therefore** (descriptive, logged in `prereg/DEVIATIONS.md`): **L+0** builds the same three features only from the records first lent in the work\'s first month '
      '(theme as in `16_v3_assign.py`, but each record counts once, no loans are used and Goodreads shelves are left out; the code reproduces '
      f"`work_theme.parquet`'s top node for {pc(m0['theme_replication_same_top_node_no_goodreads'], 2)} of the works without Goodreads evidence when it is given all records and their loans). "
      'L+0 is still not clean: a first-month record is visible only because it was lent in month 0, which is inside the outcome window, and the theme depends mainly on the subject headings of print records: '
      f"works with print loans in month 0 have a first-month theme {pc(ex['theme_present_if_print_loans_month0']['month0'])} of the time, against {pc(ex['theme_present_if_no_print_loans_month0']['month0'])} without. "
      'That is the month-0 format information that correction B2 of the code audit took out of L. **Lq** leaves the theme out (L plus the first-month publication-year gap and title-only flag) and is the cleanest of the three.', '')
    SUBS = [('all', 'all new books'), ('matched', 'author matched to a Wikipedia article before release'), ('writer_type', 'matched author is a writer')]
    MN = {'W_lgbm': 'W (Wikipedia only)', 'L_lgbm': 'L (library, as in Test B)', 'LW_lgbm': 'LW (L + Wikipedia, as in Test B)',
          'Lp_lgbm': 'L+ (L + theme, publication-year gap, title-only flag; as fixed)', 'LpW_lgbm': 'L+W',
          'L0_lgbm': 'L+0 (the same three from first-month records; added)', 'L0W_lgbm': 'L+0 W (added)',
          'Lq_lgbm': 'Lq (L + first-month publication-year gap and title-only flag, no theme; added)', 'LqW_lgbm': 'Lq W (added)'}
    ORDER = ('W_lgbm', 'L_lgbm', 'LW_lgbm', 'Lq_lgbm', 'LqW_lgbm', 'L0_lgbm', 'L0W_lgbm', 'Lp_lgbm', 'LpW_lgbm')
    for sub, lab in SUBS:
        S = PB['subsets'][sub]
        rows = [[MN[c], ci(S['models'][c]), pc(S['models'][c]['top10_precision'])] for c in ORDER]
        w(f"**{lab}** ({S['n']['rows']:,} books, {S['n']['authors']:,} author clusters)", '', table(['Model', 'Spearman (interval)', 'Top-10% precision'], rows), '')
    GAINS = (('LW_minus_L', 'on top of L (as in Test B)'), ('LqW_minus_Lq', 'on top of Lq (no theme)'), ('L0W_minus_L0', 'on top of L+0 (first-month records)'), ('LpW_minus_Lp', 'on top of L+ (as fixed)'))
    rows = []
    for sub, lab in SUBS:
        S = PB['subsets'][sub]
        for name, label in GAINS:
            d = S['diffs'][name]
            rows.append([lab, 'Wikipedia ' + label, ci(d, f4), 'yes' if above0(d) else 'no'])
    w('**Does Wikipedia still add?** (paired difference in Spearman, same draws; yes = interval above 0)', '', table(['Books', 'Comparison', 'Difference (interval)', 'Above 0?'], rows, 'llrr'), '')
    rows = []
    for sub, lab in SUBS:
        S = PB['subsets'][sub]
        for name, label in (('Lq_minus_L', 'Lq minus L (publication-year gap and title-only flag)'), ('L0_minus_Lq', 'L+0 minus Lq (the first-month theme)'),
                            ('Lp_minus_L0', 'L+ minus L+0 (records first lent later)'), ('Lp_minus_L', 'L+ minus L (all of it, as fixed)')):
            rows.append([lab, label, ci(S['diffs'][name], f4)])
    w('**What the catalogue information adds to the library model alone**', '', table(['Books', 'Comparison', 'Difference in Spearman (interval)'], rows, 'llr'), '')
    S = PB['subsets']['all']
    g_old = S['diffs']['LW_minus_L']
    gains = {k: S['diffs'][k] for k in ('LpW_minus_Lp', 'L0W_minus_L0', 'LqW_minus_Lq')}
    kept = {k: v['mean'] / g_old['mean'] for k, v in gains.items()}
    still = {k: {sub: above0(PB['subsets'][sub]['diffs'][k]) for sub, _ in SUBS} for k in gains}
    J['R5'] = dict(extra_info=ex, subsets=PB['subsets'], refit_check_max_abs_diff=PB['refit_check_max_abs_diff'],
                   reading=dict(all_gain_as_in_test_b=g_old, gains=gains, share_of_test_b_gain=kept, still_adds=still,
                                all_sets_all_versions_above0=bool(all(all(v.values()) for v in still.values()))))
    w(f"- The library model rises from {f3(S['models']['L_lgbm']['spearman'])} (L) to {f3(S['models']['Lq_lgbm']['spearman'])} without the theme (Lq), "
      f"{f3(S['models']['L0_lgbm']['spearman'])} with the first-month theme (L+0) and {f3(S['models']['Lp_lgbm']['spearman'])} with the features as fixed (L+). "
      f"So most of the gain comes with the publication-year gap and the title-only flag ({sg(S['diffs']['Lq_minus_L']['mean'])}), the first-month theme adds {sg(S['diffs']['L0_minus_Lq']['mean'])}, "
      f"and the records first lent later add {sg(S['diffs']['Lp_minus_L0']['mean'])} (L+ minus L+0). The gap matters on its own: books first lent in the year after their publication year had a median of "
      f"{lb0['1.0']['median_loans6']:.0f} loans in their first six months, against {lb0['0.0']['median_loans6']:.0f} for books first lent in their publication year (first-month records).",
      f"- Wikipedia's addition, {f4(g_old['mean'])} over L, becomes {f4(gains['LqW_minus_Lq']['mean'])} over Lq ({100 * kept['LqW_minus_Lq']:.0f}%), {f4(gains['L0W_minus_L0']['mean'])} over L+0 ({100 * kept['L0W_minus_L0']:.0f}%) "
      f"and {f4(gains['LpW_minus_Lp']['mean'])} over L+ ({100 * kept['LpW_minus_Lp']:.0f}%). "
      + ("Its interval is above zero for all three stronger models in all three sets of books (all, matched authors, writers)." if J['R5']['reading']['all_sets_all_versions_above0'] else
         "Its interval is not above zero in every one of these cases (see the table)."), '')

# ======================================================================================== R6
w('## R6. Does Wikipedia catch rises the library list misses? (Test A, incremental early warning)', '',
  'In each month: take the books that rose by 50% next month and were not in the library model\'s top 50. What share of them is in Wikipedia\'s top 50 '
  '(W, Wikipedia only)? A random list of 50 would catch 50 divided by the number of books that month (about 0.7%). '
  'The library list is the library-only tree model H (main) and, added, the naive repeat-last-month ranking. Averages are over months, with month-block intervals.', '')
if PA:
    R6 = PA['R6_incremental']
    rows = []
    cols = [('library_trees', 'Library list = H (trees)'), ('library_naive', 'Library list = repeat last month')]
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
    r6line('Share a random list of 50 would catch (expected)', lambda d: d['share_random_list']['mean'], lambda x: pc(x, 2))
    r6line('Wikipedia share divided by the random share', lambda d: d['lift_over_random'], lambda d: ci(d, lambda x: f'{x:.2f}'))
    r6line('Months in which Wikipedia beats the random list', lambda d: d['months_wikipedia_beats_random'], pc)
    r6line('Books in both lists, per month', lambda d: d['mean_overlap_of_the_two_lists'], lambda x: f'{x:.1f}')
    r6line('Books in the Wikipedia list that are not in the library list, per month', lambda d: d['new_books_in_wikipedia_list_mean'], lambda x: f'{x:.1f}')
    r6line('Share of those books that rose', lambda d: d['precision_of_new_books'])
    r6line('Share of the books outside the library top 50 that rose', lambda d: d['base_rate_outside_library_list'])
    w(table(['Measure (top 50 lists, rise of 50%)'] + [n for _, n in cols], rows), '')
    J['R6'] = R6
    m0_, m1, t20 = R6['library_trees'][key], R6['library_naive'][key], R6['library_trees']['top20|rose50']
    r25, r100 = R6['library_trees']['top50|rose25'], R6['library_trees']['top50|rose100']
    J['R6']['reading'] = dict(share=m0_['share_caught_by_wikipedia'], random=m0_['share_random_list'], lift=m0_['lift_over_random'], lift_interval_above_1=bool(m0_['lift_over_random']['lo'] > 1))
    w(f"- Among the rises the library history list (H) missed, Wikipedia's top 50 caught {cip(m0_['share_caught_by_wikipedia'])}, against {pc(m0_['share_random_list']['mean'], 2)} for a random list "
      f"({m0_['lift_over_random']['mean']:.1f} times; interval {m0_['lift_over_random']['lo']:.1f} to {m0_['lift_over_random']['hi']:.1f}). With the naive list as the library list the share is "
      f"{cip(m1['share_caught_by_wikipedia'])}, {m1['lift_over_random']['mean']:.1f} times the random share.",
      f"- Of the {m0_['new_books_in_wikipedia_list_mean']:.1f} books per month that Wikipedia's list adds to the library list, {pc(m0_['precision_of_new_books']['mean'])} rose, against {pc(m0_['base_rate_outside_library_list']['mean'])} of the books outside the library list. "
      f"The two lists share {m0_['mean_overlap_of_the_two_lists']:.1f} books a month.",
      f"- With lists of 20 the share caught is {cip(t20['share_caught_by_wikipedia'])} (random: {pc(t20['share_random_list']['mean'], 2)}; {t20['lift_over_random']['mean']:.1f} times). "
      f"Counting rises of 25% or 100% instead, the top-50 share is {pc(r25['share_caught_by_wikipedia']['mean'])} ({r25['lift_over_random']['mean']:.1f} times random) and "
      f"{pc(r100['share_caught_by_wikipedia']['mean'])} ({r100['lift_over_random']['mean']:.1f} times).", '')
else:
    J['R6'] = None

# ======================================================================================== R7
w('## R7. Length of the alert list (top 10, 20, 50, 100)', '',
  'Hit rates for rises of 50% and for surges, by list length. Test D numbers are for all formats (lists drawn within each format and month), 2019 to 2026, unless a period is shown.', '')
J['R7'] = {}
if PA:
    for fl in ('rose50', 'surged'):
        rows = []
        for m in ['Wlgbm_D', 'Wrule_D', 'Hlgbm_D', 'HWlgbm_D', 'Hnaive_D']:
            rows.append([NAMES_A[m]] + [cip(cellsA(m, k, fl)) for k in KS])
        rows.append(['*base rate (any book)*'] + [pc(PA['lists']['base_monthly_mean'][fl])] * 4)
        w(f"**Test A, {THR_LABEL[fl]}**", '', table(['Model', 'Top 10', 'Top 20', 'Top 50', 'Top 100'], rows), '')
    J['R7']['test_a'] = {m: {f'top{k}': {fl: PA['lists']['models'][m][f'top{k}'][fl] for fl in ('rose50', 'surged')} for k in KS} for m in NAMES_A}
    J['R7']['test_a_base'] = PA['lists']['base_monthly_mean']
    hw_h = sum(cellsA('HWlgbm_D', k, fl)['mean'] >= cellsA('Hlgbm_D', k, fl)['mean'] - TIE for k in KS for fl in ('rose50', 'surged'))
    hw_h_strict = sum(cellsA('HWlgbm_D', k, fl)['mean'] > cellsA('Hlgbm_D', k, fl)['mean'] for k in KS for fl in ('rose50', 'surged'))
    wl = {k: cellsA('Wlgbm_D', k, 'rose50')['mean'] / PA['lists']['base_monthly_mean']['rose50'] for k in KS}
    falling = all(wl[a] > wl[b] for a, b in zip(KS[:-1], KS[1:]))
    J['R7']['test_a_reading'] = dict(hw_not_below_h=int(hw_h), hw_above_h=int(hw_h_strict), cells=8, w_lift_by_k=wl)
    rule = {k: cellsA('Wrule_D', k, 'rose50')['mean'] for k in KS}
    J['R7']['test_a_reading']['rule_by_k'] = rule
    w(f"- Test A: library + Wikipedia is above the library list in {hw_h_strict} of 8 cells (4 lengths, two outcomes). The Wikipedia-only list is "
      + ', '.join(f"{wl[k]:.1f}" for k in KS) + " times the base rate at 10, 20, 50 and 100 places" + (", so it works best in the shortest lists." if falling else ".")
      + (f" The no-fitting rule is the exception: its hit rate is lowest in the shortest list ({pc(rule[10])} at 10 places, {pc(max(rule.values()))} at its best)." if rule[10] == min(rule.values()) else ''), '')
if D_VARIANTS:
    rows = []
    for m in ['W', 'H', 'HW', 'naive']:
        rows.append([NAMES_D[m]] + [dcell(lambda P, m=m, k=k: P['scopes']['all|2019-2026']['lists'][m][f'top{k}']['rose50']['rate']) for k in KS])
    rows.append(['*base rate (any book)*'] + [dcell(lambda P: P['scopes']['all|2019-2026']['base']['rose50'])] * 4)
    w(f"**Test D, all formats, {THR_LABEL['rose50']}** ({DV_HEAD})", '', table(['Model', 'Top 10', 'Top 20', 'Top 50', 'Top 100'], rows), '')
    rows = []
    for sc in FMTS + ['all']:
        for per in PERIODS:
            cells = []
            for k in KS:
                vals = [dscope(v, sc, per)['lists']['HW'][f'top{k}']['rose50']['rate'] for v in D_VARIANTS]
                cells.append(' / '.join(pc(x) + ('*' if x >= 0.9 else '') for x in vals))
            rows.append([sc if sc != 'all' else 'all formats', per] + cells)
    w(f"**Library + Wikipedia (HW) by format and period, {THR_LABEL['rose50']}** ({DV_HEAD}; * = at least 90%)", '', table(['Format', 'Years', 'Top 10', 'Top 20', 'Top 50', 'Top 100'], rows, 'llrrrr'), '')
    for var in D_VARIANTS:
        n90 = {f'top{k}': sum(dscope(var, sc, p)['lists']['HW'][f'top{k}']['rose50']['rate'] >= 0.9 for sc in FMTS for p in PERIODS) for k in KS}
        J['R7'][f'test_d_{var}'] = {sc: {'base': v['base'], 'base_group_mean': v.get('base_group_mean'), 'lists': v['lists']} for sc, v in PD[var]['scopes'].items()}
        J['R7'][f'test_d_{var}_reading'] = dict(hw_formats_periods_at_least_90=n90, of=6)
    n90s = {v: J['R7'][f'test_d_{v}_reading']['hw_formats_periods_at_least_90'] for v in D_VARIANTS}
    w(f"- Library + Wikipedia reaches 90% in this many of the 6 format and period cells ({DV_HEAD}): "
      + '; '.join(f"top {k}: " + ' / '.join(str(n90s[v][f'top{k}']) for v in D_VARIANTS) for k in KS) + '.')
    if BOTH:
        a = dscope('original', 'all', '2024-2026')['lists']['HW']['top20']['rose50']['rate']
        b = dscope('corrected', 'all', '2024-2026')['lists']['HW']['top20']['rose50']['rate']
        pr = dscope('corrected', 'print', '2024-2026')['lists']['HW']['top20']['rose50']['rate']
        J['R7']['test_d_all_formats_2024_2026_top20'] = dict(original=a, corrected=b, print_corrected=pr)
        w(f"- Pooled over the three formats, the 2024-2026 top 20 is {pc(a)} in the original run and {pc(b)} in the corrected one, right on the line; "
          f"the question of addendum d asks for every format, and print stays at {pc(pr)}.")
    w('')

# ======================================================================================== decisions
w('## Every comparison: does the result come out the same way?', '')
J['decisions'] = []


def add(code, decision, items):
    """items: (column of the table below, what was compared, holds, detail)."""
    J['decisions'].append(dict(code=code, decision=decision, checks=[dict(column=col, check=c, holds=bool(h), detail=t) for col, c, h, t in items]))


if PA:
    B = PA['R4_bot_months']['all_months']
    nb = PA['R4_bot_months']['without_bot_months']
    R3 = PA['R3_years']
    ys = sorted(R3, key=int)
    with_ci = [y for y in ys if has_ci(R3[y]['change_rank']['Wlgbm_D'])]
    base = PA['lists']['base_monthly_mean']
    # A1
    it = [('main', 'all months', above0(B['change_rank']['Wlgbm_D']), f"W change rank {ci(B['change_rank']['Wlgbm_D'])}"),
          ('R4', 'without 2025-04 to 2025-06', above0(nb['change_rank']['Wlgbm_D']), f"{ci(nb['change_rank']['Wlgbm_D'])}"),
          ('R3', 'each test year', all(R3[y]['change_rank']['Wlgbm_D']['mean'] > 0 for y in ys) and all(above0(R3[y]['change_rank']['Wlgbm_D']) for y in with_ci),
           f"point value above 0 in {sum(R3[y]['change_rank']['Wlgbm_D']['mean'] > 0 for y in ys)} of {len(ys)} years; interval above 0 in {sum(above0(R3[y]['change_rank']['Wlgbm_D']) for y in with_ci)} of the {len(with_ci)} years that have one")]
    if sd:
        v = [sd[s]['change_rank']['Wlgbm_D'] for s in sorted(sd)]
        it.append(('R2', 'each seed', all(x > 0 for x in v), f"{f4(min(v))} to {f4(max(v))} over {len(v)} seeds"))
    add('A1', 'A1 (Test A): Wikipedia alone ranks which books rise; interval of W change rank above 0', it)
    # A2
    it = [('main', 'all months', above0(B['paired']['HW_minus_H']), f"HW minus H {ci(B['paired']['HW_minus_H'], f4)}"),
          ('R4', 'without 2025-04 to 2025-06', above0(nb['paired']['HW_minus_H']), f"{ci(nb['paired']['HW_minus_H'], f4)}"),
          ('R3', 'each test year', all(R3[y]['paired']['HW_minus_H']['mean'] > 0 for y in ys) and all(above0(R3[y]['paired']['HW_minus_H']) for y in with_ci),
           f"point value above 0 in {sum(R3[y]['paired']['HW_minus_H']['mean'] > 0 for y in ys)} of {len(ys)} years; interval above 0 in {sum(above0(R3[y]['paired']['HW_minus_H']) for y in with_ci)} of the {len(with_ci)} years that have one")]
    if sd:
        v = [sd[s]['HW_minus_H_change_rank'] for s in sorted(sd)]
        it.append(('R2', 'each seed', all(x > 0 for x in v), f"{f4(min(v))} to {f4(max(v))} over {len(v)} seeds"))
    add('A2', 'A2 (Test A): Wikipedia adds to library history; HW minus H above 0', it)
    # A3
    sa, sn = B['surge_ap']['Wlgbm_D'], nb['surge_ap']['Wlgbm_D']
    it = [('main', 'all months', sa['ratio_lo'] > 1, f"W surge AP ratio {f2(sa['ratio'])} ({f2(sa['ratio_lo'])} to {f2(sa['ratio_hi'])})"),
          ('R4', 'without 2025-04 to 2025-06', sn['ratio_lo'] > 1, f"{f2(sn['ratio'])} ({f2(sn['ratio_lo'])} to {f2(sn['ratio_hi'])})"),
          ('R3', 'each test year', all(R3[y]['surge_ap']['Wlgbm_D']['ratio'] > 1 for y in ys), f"ratio above 1 in {sum(R3[y]['surge_ap']['Wlgbm_D']['ratio'] > 1 for y in ys)} of {len(ys)} years")]
    if sd:
        v = [sd[s]['surge_ap_ratio']['Wlgbm_D'] for s in sorted(sd)]
        it.append(('R2', 'each seed', all(x > 1 for x in v), f"{f2(min(v))} to {f2(max(v))} over {len(v)} seeds"))
    add('A3', 'A3 (Test A): Wikipedia alone flags surges; interval of the W surge AP ratio above 1', it)
    # alert lists
    cells = [(k, fl) for k in (20, 50) for fl in THR3]
    n_wb = sum(cellsA('Wlgbm_D', k, fl)['mean'] > base[fl] for k, fl in cells)
    n_wk = sum(cellsA('Wlgbm_D', k, fl)['mean'] > base[fl] for k in KS for fl in ('rose50', 'surged'))
    n_wy = sum(R3[y]['alert']['top20']['Wlgbm_D']['rose50']['mean'] > R3[y]['base_rose50'] for y in ys)
    it = [('R1', 'rise of 25%, 50%, 100%; top 20 and 50', n_wb == len(cells), f"above the base rate in {n_wb} of {len(cells)} cells"),
          ('R7', 'top 10, 20, 50, 100; rose 50% and surged', n_wk == 8, f"above the base rate in {n_wk} of 8 cells"),
          ('R3', 'each test year (top 20)', n_wy == len(ys), f"above the year's base rate in {n_wy} of {len(ys)} years"),
          ('R4', 'without 2025-04 to 2025-06 (top 20)', nb['alert']['top20']['Wlgbm_D']['rose50']['mean'] > nb['base_rose50'],
           f"{pc(nb['alert']['top20']['Wlgbm_D']['rose50']['mean'])} against a base rate of {pc(nb['base_rose50'])}")]
    if sd:
        v = [sd[s]['top20_rose50']['Wlgbm_D'] for s in sorted(sd)]
        it.append(('R2', 'each seed (top 20)', all(x > base['rose50'] for x in v), f"top-20 hit rate {pc(min(v))} to {pc(max(v))} over {len(v)} seeds"))
    add('Alert A (W)', 'Alert list (Test A): the Wikipedia-only list beats the base rate', it)
    n_hh = sum(cellsA('HWlgbm_D', k, fl)['mean'] >= cellsA('Hlgbm_D', k, fl)['mean'] - TIE for k, fl in cells)
    n_hk = sum(cellsA('HWlgbm_D', k, fl)['mean'] >= cellsA('Hlgbm_D', k, fl)['mean'] - TIE for k in KS for fl in ('rose50', 'surged'))
    below = [(y, 100 * (R3[y]['alert']['top20']['HWlgbm_D']['rose50']['mean'] - R3[y]['alert']['top20']['Hlgbm_D']['rose50']['mean']), R3[y]['n_months'])
             for y in ys if R3[y]['alert']['top20']['HWlgbm_D']['rose50']['mean'] < R3[y]['alert']['top20']['Hlgbm_D']['rose50']['mean'] - TIE]
    it = [('R1', 'rise of 25%, 50%, 100%; top 20 and 50', n_hh == len(cells), f"HW not more than 0.5 points below H in {n_hh} of {len(cells)} cells"),
          ('R7', 'top 10, 20, 50, 100; rose 50% and surged', n_hk == 8, f"HW not more than 0.5 points below H in {n_hk} of 8 cells"),
          ('R3', 'each test year (top 20)', not below,
           f"HW not more than 0.5 points below H in {len(ys) - len(below)} of {len(ys)} years" + (''.join(f"; below in {y} by {abs(p):.1f} points ({n} scored months)" for y, p, n in below) if below else '')),
          ('R4', 'without 2025-04 to 2025-06 (top 20)', nb['alert']['top20']['HWlgbm_D']['rose50']['mean'] >= nb['alert']['top20']['Hlgbm_D']['rose50']['mean'] - TIE,
           f"HW {pc(nb['alert']['top20']['HWlgbm_D']['rose50']['mean'])}, H {pc(nb['alert']['top20']['Hlgbm_D']['rose50']['mean'])}")]
    if sd:
        v = [(sd[s]['top20_rose50']['HWlgbm_D'] - sd[s]['top20_rose50']['Hlgbm_D']) for s in sorted(sd)]
        it.append(('R2', 'each seed (top 20)', all(x >= -TIE for x in v), f"HW minus H in the top-20 hit rate: {sg(100 * min(v), 1)} to {sg(100 * max(v), 1)} points over {len(v)} seeds"))
    add('Alert A (HW vs H)', 'Alert list (Test A): adding Wikipedia to the library list does not lower the hit rate (under 0.5 points counts as a tie)', it)
    e0, e1 = PA['R6_incremental']['library_trees']['top50|rose50'], PA['R6_incremental']['library_naive']['top50|rose50']
    add('Early warning', "Early warning (Test A): Wikipedia's list catches rises that the library list misses",
        [('R6', 'library list H, top 50', e0['lift_over_random']['lo'] > 1, f"{cip(e0['share_caught_by_wikipedia'])} caught against {pc(e0['share_random_list']['mean'], 2)} for a random list of 50"),
         ('R6', 'naive library list, top 50', e1['lift_over_random']['lo'] > 1, f"{cip(e1['share_caught_by_wikipedia'])} caught against {pc(e1['share_random_list']['mean'], 2)}")])
if PB:
    S = PB['subsets']['all']
    ysb = sorted(S['by_year'], key=int)
    add('B1', 'B1 (Test B): Wikipedia alone predicts the early demand of new books; interval of W Spearman above 0',
        [('main', 'all years', above0(S['models']['W_lgbm']), f"W Spearman {ci(S['models']['W_lgbm'])}"),
         ('R3', 'each test year', all(above0(S['by_year'][y]['models']['W_lgbm']) for y in ysb), f"interval above 0 in {sum(above0(S['by_year'][y]['models']['W_lgbm']) for y in ysb)} of {len(ysb)} years")])
    it = [('main', 'all years', above0(S['diffs']['LW_minus_L']), f"LW minus L {ci(S['diffs']['LW_minus_L'], f4)}"),
          ('R3', 'each test year', all(above0(S['by_year'][y]['diffs']['LW_minus_L']) for y in ysb),
           f"interval above 0 in {sum(above0(S['by_year'][y]['diffs']['LW_minus_L']) for y in ysb)} of {len(ysb)} years, point value above 0 in {sum(S['by_year'][y]['diffs']['LW_minus_L']['mean'] > 0 for y in ysb)}")]
    for name, label in (('LpW_minus_Lp', 'stronger library model L+, as fixed'), ('L0W_minus_L0', 'L+0, first-month records (added)'), ('LqW_minus_Lq', 'Lq, no theme (added)')):
        n_ok = sum(above0(PB['subsets'][s_]['diffs'][name]) for s_ in ('all', 'matched', 'writer_type'))
        it.append(('R5', label, n_ok == 3, f"{ci(S['diffs'][name], f4)} (all books); interval above 0 in {n_ok} of 3 book sets"))
    add('B2', 'B2 (Test B): Wikipedia adds to the library model for new books; LW minus L above 0', it)
for var in D_VARIANTS:
    S = PD[var]['scopes']
    lbl = dlabel(var)
    cells = [(k, fl) for k in ('top20', 'top50') for fl in THR3]
    s0 = S['all|2019-2026']
    n_h = sum(s0['lists']['HW'][k][fl]['rate'] >= s0['lists']['H'][k][fl]['rate'] - TIE for k, fl in cells)
    n_w = sum(s0['lists']['W'][k][fl]['rate'] > s0['base'][fl] for k, fl in cells)
    n_hk = sum(s0['lists']['HW'][f'top{k}']['rose50']['rate'] >= s0['lists']['H'][f'top{k}']['rose50']['rate'] - TIE for k in KS)
    n_wk = sum(s0['lists']['W'][f'top{k}']['rose50']['rate'] > s0['base']['rose50'] for k in KS)
    add(f'Alert D {var}', f'Alert list ({lbl}): W beats the base rate and HW is not below H (under 0.5 points counts as a tie)',
        [('R1', 'rise of 25%, 50%, 100%; top 20 and 50', n_h == len(cells) and n_w == len(cells), f"HW not more than 0.5 points below H in {n_h} of {len(cells)} cells; W above the base rate in {n_w} of {len(cells)}"),
         ('R7', 'top 10, 20, 50, 100 (rise of 50%)', n_hk == 4 and n_wk == 4, f"HW not more than 0.5 points below H at {n_hk} of 4 lengths; W above the base rate at {n_wk} of 4")])

    def q90(fl, k, per, S=S):
        return all(S[f'{sc}|{per}']['lists']['HW'][f'top{k}'][fl]['rate'] >= 0.9 for sc in FMTS)

    def nfmt(fl, k, per, S=S):
        return sum(S[f'{sc}|{per}']['lists']['HW'][f'top{k}'][fl]['rate'] >= 0.9 for sc in FMTS)

    main90 = {per: q90('rose50', 20, per) for per in PERIODS}
    r1_ok = all(q90(fl, 20, per) == main90[per] for fl in ('rose25', 'rose100') for per in main90)
    r7_ok = all(q90('rose50', k, per) == main90[per] for k in (10, 50, 100) for per in main90)
    add(f'D 90% {var}', f'90% question ({lbl}): HW top 20, rise of 50%, at least 90% in every format; answer for 2019-2026 and 2024-2026',
        [('main', 'top 20, rise of 50%', True, '; '.join(f"{per}: {'yes' if main90[per] else 'no'} ({nfmt('rose50', 20, per)} of 3 formats)" for per in main90)),
         ('R1', 'rise of 25% and 100% (top 20)', r1_ok, '; '.join(f"{lab} {per}: {'yes' if q90(fl, 20, per) else 'no'} ({nfmt(fl, 20, per)} of 3)" for fl, lab in (('rose25', '25%'), ('rose100', '100%')) for per in main90)),
         ('R7', 'top 10, 50, 100 (rise of 50%)', r7_ok, '; '.join(f"top {k} {per}: {'yes' if q90('rose50', k, per) else 'no'} ({nfmt('rose50', k, per)} of 3)" for k in (10, 50, 100) for per in main90))])
    J['R7'][f'test_d_{var}_90'] = {f'top{k}|{fl}|{per}': dict(formats_at_least_90=nfmt(fl, k, per), of=3) for k in KS for fl in THR3 for per in main90}

COLS = ['main', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7']
changes = [dict(code=dd['code'], decision=dd['decision'], column=c['column'], check=c['check'], detail=c['detail']) for dd in J['decisions'] for c in dd['checks'] if not c['holds']]
J['any_conclusion_changes'] = changes
n_cells = sum(len(dd['checks']) for dd in J['decisions'])
affected = [dd['code'] for dd in J['decisions'] if any(not c['holds'] for c in dd['checks'])]
clean_ = [dd['code'] for dd in J['decisions'] if all(c['holds'] for c in dd['checks'])]
J['decisions_unchanged'] = clean_
J['decisions_with_a_change'] = affected
J['n_comparisons'] = n_cells
if not changes:
    w(f"**No.** Every decision rule of the records and every headline alert result comes out the same way under each of the {n_cells} alternative choices checked.", '')
else:
    w(f"Of {n_cells} comparisons, {n_cells - len(changes)} come out the same way as the main result and {len(changes)} do not. "
      f"No change in any check: {'; '.join(clean_) if clean_ else 'none'}. At least one change: {'; '.join(affected)}. The changes are listed under the table.", '')
w('Each row is a decision rule of the records or a headline result of the alert lists. A cell says "holds" when the result comes out the same way under the alternative choice of that check, '
  '"**changes**" when it does not, and is empty when the check does not apply. Details follow the table.', '')
rows = []
for dd in J['decisions']:
    cells_ = []
    for col in COLS:
        its = [c for c in dd['checks'] if c['column'] == col]
        cells_.append('' if not its else ('holds' if all(c['holds'] for c in its) else '**changes**'))
    rows.append([dd['decision']] + cells_)
w(table(['Decision or result'] + COLS, rows, 'l' + 'c' * len(COLS)), '')
if changes:
    w('**Where a result changes**', '')
    for c in changes:
        w(f"- {c['code']}, {c['column']}, {c['check']}: {c['detail']}")
    w('')
w('**Detail of every comparison**', '')
rows = []
for dd in J['decisions']:
    for c in dd['checks']:
        rows.append([dd['code'], c['column'], c['check'], 'holds' if c['holds'] else '**changes**', c['detail']])
w(table(['Result', 'Check', 'Compared', 'Outcome', 'Detail'], rows, 'lllll'), '')

# ======================================================================================== notes
w('## Notes', '')
notes = []
if PAO:
    ref = pd.read_csv(REP / 'wiki_led_test_a_alert_list.csv', index_col=[0, 1])
    pairs = [('Wlgbm_D', 'Wikipedia only'), ('Wrule_D', 'Wikipedia rule (no fitting)'), ('Hlgbm_D', 'Library record'), ('HWlgbm_D', 'Library + Wikipedia')]
    diffs = []
    for m, nm in pairs:
        for k in (20, 50):
            diffs.append(abs(PAO['lists']['models'][m][f'top{k}']['rose50']['mean'] - float(ref.loc[(nm, str(k)), 'rose'])))
            diffs.append(abs(PAO['lists']['models'][m][f'top{k}']['surged']['mean'] - float(ref.loc[(nm, str(k)), 'surged'])))
    J['code_check_test_a_original_alert_list'] = dict(max_abs_diff=float(max(diffs)), cells=len(diffs))
    notes.append(f"Code check: run on the original Test A files, this code reproduces the stored alert list (`wiki_led_test_a_alert_list.csv`: top 20 and top 50, rose and surged, four models) to within {max(diffs):.4f}; "
                 "the small gaps come from the order of tied predictions.")
tc = J.setdefault('code_check_test_d', {})
for var, fn in (('original', 'wiki_led_test_d.json'), ('corrected', 'wiki_led_test_d_c.json')):
    if var in D_VARIANTS and (REP / fn).exists():
        st = json.loads((REP / fn).read_text())
        d2 = [abs(PD[var]['scopes']['all|2019-2026']['lists'][m][f'top{k}']['rose50']['rate'] - st['alert'][f'all|{m}'][f'top{k}']['rose']) for m in ('W', 'H', 'HW', 'naive') for k in (20, 50)]
        tc[var] = dict(max_abs_diff=float(max(d2)), rows_exact50_differs_from_stored_rose=PD[var]['rows_exact50_differs_from_stored_rose'], rows=PD[var]['rows'], stored_file=fn)
if tc:
    notes.append('Code check: Test D hit rates at 50% (all formats, top 20 and top 50, four models) agree with the stored files ('
                 + '; '.join(f"{v}: `{tc[v]['stored_file']}`, within {tc[v]['max_abs_diff']:.4f}" for v in tc) + '); '
                 f"the exact 50% rise flag differs from the stored `rose` column in {PD['original']['rows_exact50_differs_from_stored_rose']} of {PD['original']['rows']:,} rows.")
if BOTH and PD['corrected'].get('rows_check_against_original'):
    rc = PD['corrected']['rows_check_against_original']
    notes.append(f"Test D, corrected: its rows file (`test_d_rows_c.parquet`, {rc['rows']:,} rows) has the same rows as the original ({rc['only_here']} only in one, {rc['only_original']} only in the other) "
                 f"and the same loans (largest difference in next-month loans {rc['max_abs_diff_L_next']:.1f}, in M6 {rc['max_abs_diff_M6']:.1f}); only the Wikipedia features differ, so H and the naive list score the same in both runs.")
if PB:
    stb = json.loads((REP / 'wiki_led_test_b.json').read_text())['all']['LW_minus_L']
    mine = PB['subsets']['all']['diffs']['LW_minus_L']
    J['code_check_test_b'] = dict(refit_max_abs_diff=PB['refit_check_max_abs_diff'], stored=stb, here=mine)
    same = abs(mine['lo'] - stb['lo']) < 1e-9 and abs(mine['hi'] - stb['hi']) < 1e-9
    notes.append(f"Code check: the refitted W, L and LW predictions of Test B equal the stored ones (largest difference {max(PB['refit_check_max_abs_diff'].values()):.1e}), "
                 f"and the LW minus L interval here ({f4(mine['lo'])} to {f4(mine['hi'])}) {'equals' if same else 'differs from'} the stored one ({f4(stb['lo'])} to {f4(stb['hi'])}).")
notes.append('Additions beyond the text of addendum e, all descriptive and not used to choose anything: the surge outcome and the top 50 and top 100 lists in R1 and R7; the naive library list, the 25% and 100% rises and the top 20 list in R6; '
             'the matched-author and writer sets in R5 (the sets of decision B3); the three months alone in R4; the by-format and by-period table for the 90% question in R7; '
             'and, from the review of 20 Oct 2026, the models L+0 and Lq in R5 (first-month records), the month-by-month top-20 places in R3, and the Test D corrected run beside the original.')
notes.append('R3 and R4 reuse the stored predictions; only R2 (Test A) and R5 (Test B) refit models.')
if not BOTH:
    notes.append('Test D: the corrected predictions (`test_d_preds_c.parquet`) did not exist yet. Rerun `90_robustness.py d` and `91_robustness_report.py` when they do.')
for n in notes:
    w('- ' + n)
w('')
w('Run times and peak memory are in the part files (`data/db/wiki_led/robustness_part_*.json`) and the job logs (`data/reports/wl_rob_*.log`).', '')

# ======================================================================================== the short answer (top of the file)
SUM = {}
if PA and PB and D_VARIANTS:
    B_ = PA['R4_bot_months']['all_months']
    nb_ = PA['R4_bot_months']['without_bot_months']
    R3 = PA['R3_years']
    ys = sorted(R3, key=int)
    wr = {y: R3[y]['change_rank']['Wlgbm_D']['mean'] for y in ys}
    gpy = {y: R3[y]['paired']['HW_minus_H']['mean'] for y in ys}
    base50 = PA['lists']['base_monthly_mean']['rose50']
    sb = PB['subsets']['all']
    ysb = sorted(sb['by_year'], key=int)
    wb = {y: sb['by_year'][y]['models']['W_lgbm']['spearman'] for y in ysb}
    v_last = D_VARIANTS[-1]
    hw20 = {per: [dscope(v_last, sc, per)['lists']['HW']['top20']['rose50']['rate'] for sc in FMTS] for per in PERIODS}
    hw10 = [dscope(v_last, sc, per)['lists']['HW']['top10']['rose50']['rate'] for sc in FMTS for per in PERIODS]
    hw50 = [dscope(v_last, sc, per)['lists']['HW'][f'top{k}']['rose50']['rate'] for sc in FMTS for per in PERIODS for k in (50, 100)]
    y20 = '2020'
    d20 = R3[y20]['alert']['top20']
    rr = J['R5']['reading']['gains']
    SUM = dict(w_rank=B_['change_rank']['Wlgbm_D'], hw_minus_h=B_['paired']['HW_minus_H'], w_surge=B_['surge_ap']['Wlgbm_D'], w_top20=cellsA('Wlgbm_D', 20, 'rose50'), base_rose50=base50,
               hw_top20=cellsA('HWlgbm_D', 20, 'rose50'), h_top20=cellsA('Hlgbm_D', 20, 'rose50'), year2020=dict(hw=d20['HWlgbm_D']['rose50']['mean'], h=d20['Hlgbm_D']['rose50']['mean'], months=R3[y20]['n_months']),
               b1=sb['models']['W_lgbm'], b2=sb['diffs']['LW_minus_L'], b2_stronger=rr, test_d_variant_for_90=v_last, hw_top20_by_format=hw20, hw_top10_min=min(hw10), hw_top50_100_max=max(hw50))
    J['short_answer_numbers'] = SUM
    pw = J['R3'].get('per_month_years_below', {}).get(y20)
    TOP.append('## Does any conclusion depend on a single choice?')
    TOP.append('')
    TOP.append('**Short answer: no decision rule depends on a single choice.** A1, A2 and A3 (Test A) and B1 and B2 (Test B) come out the same way under every check that applies to them, '
               'and so do the two alert-list results that matter most: the Wikipedia-only list beats chance, and it catches rises the library list misses. '
               'Two results do depend on one choice: in one short test year (2020) adding Wikipedia to the library list lowered its hit rate, and the answer to the 90% question of Test D depends on the length of the list. '
               'Each line gives the main result first, then the range it takes under the checks.')
    TOP.append('')
    sr = (summ or {}).get('change_rank', {})
    TOP.append(f"- **Wikipedia alone ranks which books will rise (A1, Test A): holds.** Change rank {ci(SUM['w_rank'])}. With each of five seeds {f3(sr['Wlgbm_D']['min'])} to {f3(sr['Wlgbm_D']['max'])}; "
               f"above zero in every test year, from {f3(min(wr.values()))} ({min(wr, key=wr.get)}) to {f3(max(wr.values()))} ({max(wr, key=wr.get)}); {f3(nb_['change_rank']['Wlgbm_D']['mean'])} without the three bot months.")
    gs = (summ or {}).get('HW_minus_H', {})
    TOP.append(f"- **Wikipedia adds to the library's own history (A2): holds.** HW minus H {ci(SUM['hw_minus_h'], f4)}. Seeds {f4(gs['min'])} to {f4(gs['max'])}; "
               f"above zero in every year, {f4(min(gpy.values()))} ({min(gpy, key=gpy.get)}) to {f4(max(gpy.values()))} ({max(gpy, key=gpy.get)}); {f4(nb_['paired']['HW_minus_H']['mean'])} without the bot months.")
    sa_ = (summ or {}).get('surge_ap_ratio', {})
    TOP.append(f"- **Wikipedia alone flags surges (A3): holds.** Surge AP ratio {f2(SUM['w_surge']['ratio'])} ({f2(SUM['w_surge']['ratio_lo'])} to {f2(SUM['w_surge']['ratio_hi'])}). "
               f"Seeds {f2(sa_['Wlgbm_D']['min'])} to {f2(sa_['Wlgbm_D']['max'])}; above 1 in all {len(ys)} years; {f2(nb_['surge_ap']['Wlgbm_D']['ratio'])} without the bot months.")
    l1 = J['R1']['reading']['w_top20_lift']
    l7 = J['R7']['test_a_reading']['w_lift_by_k']
    TOP.append(f"- **The Wikipedia-only alert list beats a random pick: holds.** In its top 20, {pc(SUM['w_top20']['mean'])} of the books rose by 50% the next month, against {pc(base50)} of all books. "
               f"It stays above the base rate for every rise size ({l1['rose25']:.1f} times at 25%, {l1['rose50']:.1f} at 50%, {l1['rose100']:.1f} at 100%), every list length "
               f"({l7[10]:.1f} times at 10 places down to {l7[100]:.1f} at 100), every year and every seed, and in Test D.")
    TOP.append(f"- **Adding Wikipedia does not lower the library list's hit rate: holds, except in one year.** Top 20 over all months: HW {pc(SUM['hw_top20']['mean'])}, H {pc(SUM['h_top20']['mean'])}; "
               f"HW is not below H (0.5-point tie rule) at any rise size, list length or seed, without the bot months, or in Test D. **Difference 1:** in {y20} HW is below H, "
               f"{pc(SUM['year2020']['hw'])} against {pc(SUM['year2020']['h'])}. {y20} has only {SUM['year2020']['months']} scored months (April to September 2020 have missing library data and are not scored)")
    if pw and pm_note:
        nm = pw['months_behind']
        TOP[-1] += (f", so the gap is {pw['h_places'] - pw['hw_places']} of {pw['list_places']} list places. It comes from "
                    + ' and '.join(f"origin {x['origin_month']} ({abs(x['places'])} places fewer)" for x in nm)
                    + (", the first scored months after that gap, when the six-month normal rests on only " + ' and '.join(str(x['months_in_m6_window']) for x in nm)
                       + ' month' + ('s' if max(x['months_in_m6_window'] for x in nm) > 1 else '') + ' of loans' if all(x['months_in_m6_window'] < 6 for x in nm) else '')
                    + f". Over all {pm_note[3]} months HW is 2 or more places behind H in only {pm_note[4]} months, {pw['months_2_or_more_behind']} of them in {y20}; "
                    f"it is ahead in {pm_note[2]} months and level in {pm_note[1]}.")
    else:
        TOP[-1] += '.'
    e0 = PA['R6_incremental']['library_trees']['top50|rose50']
    TOP.append(f"- **Wikipedia catches rises the library list misses (R6): holds.** Of the rises that are not in the library's top 50, Wikipedia's top 50 catches {pc(e0['share_caught_by_wikipedia']['mean'])}, "
               f"against {pc(e0['share_random_list']['mean'], 2)} for a random list of 50 ({e0['lift_over_random']['mean']:.1f} times, interval {e0['lift_over_random']['lo']:.1f} to {e0['lift_over_random']['hi']:.1f}).")
    TOP.append(f"- **Wikipedia alone predicts new books' early demand (B1, Test B): holds.** Spearman {ci(SUM['b1'])}; interval above zero in all {len(ysb)} years, "
               f"from {f3(min(wb.values()))} ({min(wb, key=wb.get)}) to {f3(max(wb.values()))} ({max(wb, key=wb.get)}).")
    TOP.append(f"- **Wikipedia adds to the library model for new books (B2): holds.** {f4(SUM['b2']['mean'])} ({f4(SUM['b2']['lo'])} to {f4(SUM['b2']['hi'])}) over L, above zero in every year. "
               f"Over a stronger library model (R5) the addition is smaller but still above zero: {f4(rr['LqW_minus_Lq']['mean'])} without the theme, {f4(rr['L0W_minus_L0']['mean'])} with the theme from first-month records, "
               f"{f4(rr['LpW_minus_Lp']['mean'])} with the features as fixed. The review found that the theme as fixed is not known when a book arrives (it partly reflects loans inside the six-month outcome window), so the last number understates Wikipedia; see R5.")
    if BOTH:
        Wo, Wc = J['R1']['test_d_correction']['W_top20_rose50']['original'], J['R1']['test_d_correction']['W_top20_rose50']['corrected']
        TOP.append(f"- **Test D (all books, by format): holds in both runs.** The Wikipedia-only list beats the base rate and HW is not below H at every rise size and list length, in the original and the corrected run "
                   f"(Wikipedia-only top 20: {pc(Wo)} and {pc(Wc)}, base rate {pc(dscope('corrected')['base']['rose50'])}).")
    f20 = {per: ', '.join(f"{sc} {pc(x)}" for sc, x in zip(FMTS, hw20[per])) for per in PERIODS}
    ans90 = {v: {f'top{k}|{per}': J['R7'][f'test_d_{v}_90'][f'top{k}|rose50|{per}']['formats_at_least_90'] == 3 for k in KS for per in PERIODS} for v in D_VARIANTS}
    same90 = all(ans90[v] == ans90[D_VARIANTS[0]] for v in D_VARIANTS)
    SUM['answers_90_rose50'] = ans90
    TOP.append(f"- **Difference 2: the 90% question for Test D depends on the list length.** Addendum d asks whether library + Wikipedia reaches 90% in every format with a top 20. "
               f"The answer is no ({v_last} run: 2019-2026 {f20['2019-2026']}; 2024-2026 {f20['2024-2026']}). With a top 10 it is yes in every format and both periods "
               f"(lowest {pc(SUM['hw_top10_min'])}); with a top 50 or 100 it is no everywhere (highest {pc(SUM['hw_top50_100_max'])}). So 90% describes a short list, not the model as such"
               + (", and the corrected run gives the same answers as the original." if BOTH and same90 else
                  (", but the corrected and original runs do not give the same answer in every cell (see R7)." if BOTH else '.')))
    TOP.append('')
    TOP.append(f"The full table of {n_cells} comparisons is in the section \"Every comparison\" near the end.")
    TOP.append('')

OUT_MD.write_text('\n'.join(HEAD + TOP + L))
J['peak_gb'] = {n: (v or {}).get('peak_gb') for n, v in (('b', PB), ('a_seeds', PS))}


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


OUT_JSON.write_text(json.dumps(clean(J), indent=1))
print('wrote', OUT_MD, 'and', OUT_JSON, '| comparisons that change:', len(J['any_conclusion_changes']), 'of', n_cells)
