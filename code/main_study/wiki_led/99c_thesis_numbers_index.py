# 99c. Index of the numbers in the thesis results: every number of the Abstract and Chapters 5 to 8 of a thesis draft (running text,
# tables and figure captions of those chapters), the script and stored file it comes from, the key inside that file, the stored value
# at full precision, and whether the printed value equals the stored one at the printed precision. Read-only on every input; fits
# no model and reruns no analysis. Asked for by the outside review of 19 November 2026 (prereg/DEVIATIONS.md, part D).
#
# Inputs: the thesis draft (argument; default paper/Thesis_Draft_2026-11-19_1342.md) and the stored results named in each row:
#   data/reports/*.json, *.csv and *.md of the wiki_led, Test F, Study 3, Study 4 and benchmark scripts, data/db/... tables of the
#   direction scripts (dirs/), the frozen-forecast metadata in prereg/ (read only) and the library-release watcher status.
# Rows: one per printed number (an estimate printed with its interval is one row, and all its numbers must match). Left out: dates,
#   years used as labels, section, table and figure numbers, citation years, and the settings themselves (list length, targets,
#   interval level, window lengths, draws). Labels are short descriptions written for this index, not text of the thesis.
# match: yes = equal after rounding to the printed decimals (a share stored as a fraction and printed as percent counts as yes);
#   derived = computed from stored values (difference, ratio, count, log effect or error ratio turned into percent, or a word such
#   as "about a fifth"), formula in key or note; no = differs at the printed precision; not found = no stored output gives it.
# Checks: every printed string must occur in the indexed chapters of the draft (parentheses ignored; ' … ' marks left-out words), else
#   the script stops; numbers
#   of those chapters that no row holds are printed at the end for review (most are settings).
# Outputs: data/reports/thesis_numbers_index.csv and data/reports/thesis_numbers_index.md.
#   Run from code/:  nice ../.venv/bin/python main_study/wiki_led/99c_thesis_numbers_index.py [path/to/draft.md]
import re, math, json, csv, sys, pathlib, argparse

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D                                         # noqa: E402

DATA = pathlib.Path(D)
ROOT = DATA.parent
OUT_CSV = DATA / 'reports' / 'thesis_numbers_index.csv'
OUT_MD = DATA / 'reports' / 'thesis_numbers_index.md'

ap = argparse.ArgumentParser()
ap.add_argument('thesis', nargs='?', default=str(ROOT / 'paper' / 'Thesis_Draft_2026-11-19_1342.md'))
ARGS = ap.parse_args()
THESIS = pathlib.Path(ARGS.thesis)
TEXT = THESIS.read_text()
LINES = TEXT.splitlines()


def chapter_span(start_pat, end_pat):
    i0 = next(i for i, l in enumerate(LINES) if re.match(start_pat, l))
    i1 = next(i for i, l in enumerate(LINES) if i > i0 and re.match(end_pat, l))
    return i0, i1


SPANS = [chapter_span(r'^## Abstract', r'^## 1\.'), chapter_span(r'^## 5\.', r'^## References')]
INDEXED = '\n'.join('\n'.join(LINES[a:b]) for a, b in SPANS)


def norm(s):
    return re.sub(r'\s+', ' ', s.replace('(', ' ').replace(')', ' ')).strip()


INDEXED_N = norm(INDEXED)

_cache = {}


def J(rel):
    if rel not in _cache:
        _cache[rel] = json.load(open(DATA / rel))
    return _cache[rel]


def C(rel):
    if rel not in _cache:
        _cache[rel] = pd.read_csv(DATA / rel)
    return _cache[rel]


def T(rel):
    if rel not in _cache:
        _cache[rel] = (DATA / rel).read_text()
    return _cache[rel]


def jget(rel, path):
    o = J(rel)
    for k in path.split('/'):
        o = o[k]
    return o


def md(rel, snippet):
    """The snippet must appear verbatim in the stored report; returns it."""
    if snippet not in T(rel):
        raise SystemExit(f'snippet not found in {rel}: {snippet!r}')
    return snippet


NUM = re.compile(r'[−\-+]?\d[\d,]*(?:\.\d+)?')


def toks(s):
    out = []
    for m in NUM.finditer(s):
        t = m.group().replace('−', '-').replace(',', '')
        d = len(t.split('.')[1]) if '.' in t else 0
        out.append((float(t), d))
    return out


def close(v, p, d):
    return abs(v - p) <= 0.5 * 10 ** (-d) + 1e-9


def fmt(v):
    if hasattr(v, 'item') and not isinstance(v, (list, tuple, str)):
        v = v.item()
    return repr(v) if isinstance(v, float) else str(v)


ident = lambda x: x                                          # noqa: E731
pct = lambda x: 100 * x                                      # noqa: E731
pctlog = lambda x: 100 * (math.exp(x) - 1)                   # noqa: E731
less1pct = lambda x: 100 * (1 - x)                           # noqa: E731
ratio_pct = lambda x: 100 * (x - 1)                          # noqa: E731
FORMULA = {pctlog: '100*(exp(x)-1)', less1pct: '100*(1-x)', ratio_pct: '100*(x-1)'}

ROWS, MISSING = [], []


def add(chapter, location, label, printed, script, output, key, raw, f=None, kind='direct', note='', check=None, stored_str=None, why=''):
    """raw: one value or a list (est, lo, hi, or the values a derived number rests on); f maps raw to the printed unit;
    check: function(list of raw) -> (ok, note) for printed words or ranges that are not plain numbers; why: likely cause, added to the
    note only when the row does not match."""
    if not all(norm(part) in INDEXED_N for part in printed.split(' … ')):     # ' … ' marks words of the draft left out
        MISSING.append(f'{location}: {printed!r}')
    rawl = list(raw) if isinstance(raw, (list, tuple)) else [raw]
    formula = FORMULA.get(f)
    if formula and kind == 'direct':
        kind = 'derived'
    if kind == 'derived' and len(rawl) > 1 and check is not None:
        stored = '; '.join(fmt(x) for x in rawl)
    else:
        stored = fmt(rawl[0]) if len(rawl) == 1 else f'{fmt(rawl[0])} [{", ".join(fmt(x) for x in rawl[1:])}]'
    if stored_str is not None:
        stored = stored_str
    if check is not None:
        ok, extra = check(rawl)
        note = '; '.join(x for x in (note, extra) if x)
    else:
        vals = [f(x) if f else x for x in rawl]
        pt = toks(printed)
        if len(pt) != len(vals):
            raise SystemExit(f'{location}: {len(pt)} printed numbers, {len(vals)} stored: {printed!r}')
        ok = all(close(v, p, d) for v, (p, d) in zip(vals, pt))
        conv = ', '.join(f'{v:.5g}' for v in vals)
        if formula:
            note = '; '.join(x for x in (note, f'{formula}: {conv}') if x)
        elif not ok:
            note = '; '.join(x for x in (note, f'stored in printed units: {conv}') if x)
    match = ('derived' if kind == 'derived' else 'yes') if ok else 'no'
    if not ok and why:
        note = '; '.join(x for x in (note, 'likely cause: ' + why) if x)
    if kind == 'notfound':
        match = 'not found'
    ROWS.append(dict(chapter=chapter, location=location, label=label, printed=printed, script=script, output=output,
                     key=key, stored=stored, match=match, note=note))


# ------------------------------------------------ sources (script under code/, stored file under data/)
S_L, O_L = 'main_study/wiki_led/l_books_in_time/l04_backtest.py', 'reports/wiki_led_l_backtest.json'
S_A, O_A = 'main_study/wiki_led/10c_test_a.py', 'reports/wiki_led_test_a_c.json'
S_ACC, O_ACC = 'main_study/wiki_led/13c_accuracy_alert_panels.py', 'reports/wiki_led_test_a_accuracy_c.csv'
S_PL, O_PL = 'main_study/wiki_led/11c_placebo_a.py', 'reports/wiki_led_placebo_a_c.json'
S_B, O_B = 'main_study/wiki_led/30_test_b.py', 'reports/wiki_led_test_b.json'
S_SC, O_SC = 'main_study/wiki_led/15_summary_checks.py', 'reports/wiki_led_summary_checks.json'
S_C, O_C = 'main_study/wiki_led/20c_test_c.py', 'reports/wiki_led_test_c_c.json'
S_E, O_E = 'main_study/wiki_led/63c_test_e_corrected_report.py', 'reports/wiki_led_test_e_corrected.json'
S_D3, O_D3 = 'main_study/wiki_led/dirs/d3_nyt.py', 'db/wiki_led/dirs/d3_nyt/a_results.json'
S_D1, O_D1 = 'main_study/wiki_led/dirs/d1_horizons_books.py', 'db/wiki_led/dirs/d1_books/results.json'
S_D1T, O_D1T = 'main_study/wiki_led/dirs/d1_horizons_themes.py', 'db/wiki_led/dirs/d1_themes/effects_windows.csv'
S_D2, O_D2 = 'main_study/wiki_led/dirs/d2_events.py', 'reports/dir_d2_events.md'
S_J1, O_J1 = 'main_study/wiki_led/dirs/j1_links.py', 'reports/dir_j1_links.md'
S_J2 = 'main_study/wiki_led/dirs/j2_alerts.py'
O_J2P, O_J2M = 'db/wiki_led/dirs/j_alerts/paired_differences.csv', 'db/wiki_led/dirs/j_alerts/measures.csv'
S_K1, O_K1 = 'main_study/wiki_led/dirs/k1_intent.py', 'db/wiki_led/dirs/k1_intent/paired_differences.csv'
S_K2, O_K2 = 'main_study/wiki_led/dirs/k2_date_history.py', 'reports/dir_k2_dates.md'
S_S3, O_S3 = 'main_study/study3/12_shift_effects.py', 'db/study3/pooled_effects.csv'
O_S3MD = 'reports/study3_12_shift_effects.md'
S_S3P, O_S3P = 'main_study/study3/11_power.py', 'db/study3/power_summary.csv'
S_TF, O_TF = 'main_study/wiki_led/testF/28_report.py', 'reports/testF_results.json'
S_TFC, O_TFC = 'main_study/wiki_led/testF/24_G2_matchmaking.py', 'db/wiki_led/testF/g2_S2C_pooled.csv'
S_G3, O_G3 = 'main_study/wiki_led/testF/25_G3_forecast.py', 'db/wiki_led/testF/g3_pairs.csv'
S_G3H, O_G3H = 'main_study/wiki_led/testF/29_H_concept.py', 'db/wiki_led/testF/h_g3_pairs.csv'
S_BM = 'main_study/benchmark/03_evaluate.py'
O_BMP, O_BMT = 'db/benchmark/stage2_results/A2_pairs.csv', 'db/benchmark/stage2_results/A2_table.csv'
O_BM1, O_BM2 = 'reports/benchmark_stage1.md', 'reports/benchmark_stage2.md'
S_S4, O_S4 = 'main_study/study4/04_interest_flow.py', 'reports/study4_04_interest_flow.csv'
O_S4MD = 'reports/study4_04_interest_flow.md'
S_HB = 'hidden_book_redo.py'
O_HBA, O_HBG = 'reports/hidden_book_redo_auc.csv', 'reports/hidden_book_redo_attention_gain.csv'
S_LN, O_LN = 'main_study/wiki_led/97_librivox_new_recordings.py', 'reports/librivox_new_recordings.json'
S_ROB, O_ROB = 'main_study/wiki_led/91_robustness_report.py', 'reports/wiki_led_robustness.json'
S_TW, O_TW = 'main_study/wiki_led/98_two_way_intervals.py', 'reports/two_way_intervals.json'
S_TB, O_TB = 'main_study/wiki_led/05_report.py', 'reports/wiki_led_test_b_data.md'
S_V2, O_V2 = 'main_study/wiki_led/81_improve_v2_report.py', 'reports/wiki_led_improve_v2.md'
THESIS_REL = '../' + str(THESIS.resolve().relative_to(ROOT.resolve())) if THESIS.resolve().is_relative_to(ROOT.resolve()) else THESIS.name


# ------------------------------------------------ readers
def Lr(model, fm='all', period='2019-2026', key='rank'):
    v = jget(O_L, f'by_period/{period}/{fm}/{model}/{key}')
    return [v['est'], v['lo'], v['hi']] if isinstance(v, dict) else v


def Le(model, fm='all', period='2019-2026', key='rank'):
    v = jget(O_L, f'by_period/{period}/{fm}/{model}/{key}')
    return v['est'] if isinstance(v, dict) else v


def Ld(name, period='2019-2026'):
    v = jget(O_L, f'by_period/{period}/all/_diff/{name}')
    return [v['est'], v['lo'], v['hi']]


def Ar(model):
    v = jget(O_A, f'change_rank/{model}')
    return [v['mean'], v['lo'], v['hi']]


def Bs(part, model):
    v = jget(O_B, f'{part}/{model}')
    return [v.get('spearman', v.get('mean')), v['lo'], v['hi']]


def SCc(k):
    return jget(O_SC, 'values_corrected')[k]


def SCo(k):
    return jget(O_SC, 'values_original')[k]


def D3(path):
    return jget(O_D3, path)


def D1(k, model, key='spearman'):
    v = jget(O_D1, f'by_k/{k}/{key}/{model}')
    return [v['mean'], v['lo'], v['hi']]


def j2p(target, pop, a, b, measure='p20'):
    d = C(O_J2P)
    r = d[(d.target == target) & (d.population == pop) & (d.a == a) & (d.b == b) & (d.measure == measure)]
    assert len(r) == 1, (target, pop, a, b)
    r = r.iloc[0]
    return [r['mean'], r['lo'], r['hi']]


def j2m(target, pop, model, measure='p20'):
    d = C(O_J2M)
    r = d[(d.target == target) & (d.population == pop) & (d.model == model) & (d.measure == measure)]
    assert len(r) == 1
    return r.iloc[0]['mean']


def k1p(pop, a, b, measure='p20'):
    d = C(O_K1)
    r = d[(d.target == 'S1') & (d.population == pop) & (d.a == a) & (d.b == b) & (d.measure == measure)]
    assert len(r) == 1
    r = r.iloc[0]
    return [r['mean'], r['lo'], r['hi']]


def s3(source, level, dur, col='sc_effect_p'):
    d = C(O_S3)
    r = d[(d.analysis == 'main') & (d.source == source) & (d.level == level) & (d.format == 'all') & (d.duration_class == dur)]
    assert len(r) == 1
    r = r.iloc[0]
    return [r[f'{col}_mean'], r[f'{col}_ci_low'], r[f'{col}_ci_high']], int(r['tests'])


def d1t(series, method, window):
    d = C(O_D1T)
    r = d[(d.series == series) & (d.panel == 'a') & (d.level == 'both') & (d.duration_class == 'sustained') & (d.method == method)
          & (d.window == window)]
    assert len(r) == 1, (series, method, window)
    r = r.iloc[0]
    return [r['mean'], r['ci_low'], r['ci_high']]


def bmp(base, other):
    d = C(O_BMP)
    r = d[(d.base == base) & (d.other == other)]
    assert len(r) == 1
    return r.iloc[0]['mae_ratio']


TWG = {'all': 'all', 'none': 'no earlier Seattle work', 'some': 'some earlier work'}
TWM = {'L': 'Wikipedia over L (main)', 'Lq': 'Wikipedia over Lq (no theme)', 'L0': 'Wikipedia over L0 (first-month records)',
       'Lp': 'Wikipedia over Lp (as fixed)'}


def tw(group, model, iv=None):
    v = jget(O_TW, 'new_books')[TWG[group]]['gains'][TWM[model]]
    return [v['est']] + (list(v[iv]) if iv else [])


def tw_key(group, model, iv=None):
    return f'new_books/{TWG[group]}/gains/{TWM[model]}/est' + (f' and /{iv}' if iv else '')


def add_range(chapter, location, label, printed, script, output, key, vals, names, note='', why=''):
    """A printed range 'a to b' over two stored values: the smaller must round to a and the larger to b."""
    v = sorted(zip(vals, names))
    add(chapter, location, label, printed, script, output, key, [x for x, _ in v],
        stored_str='; '.join(f'{n} {fmt(x)}' for x, n in v), note=note, why=why)


# ================================================================ Abstract
AB = 'Abstract'
w14, hm = Le('W14'), Le('HM')
l2a = Ld('L2a_HMW14_minus_HM_rank')
add(AB, 'Abstract para 2 sentence 1', 'main set, Wikipedia-only rank correlation as a share of the library model', 'about a quarter',
    S_L, O_L, 'W14.rank.est / HM.rank.est', w14 / hm, kind='derived', note='0.0911 / 0.3474',
    check=lambda r: (0.2 <= r[0] <= 0.3, f'ratio {r[0]:.3f}'))
add(AB, 'Abstract para 2 sentence 1', 'main set, Wikipedia alone, next-month change, rank correlation', '0.091', S_L, O_L,
    'by_period/2019-2026/all/W14/rank/est', w14)
add(AB, 'Abstract para 2 sentence 1', 'main set, library model, next-month change, rank correlation', '0.347', S_L, O_L,
    'by_period/2019-2026/all/HM/rank/est', hm)
add(AB, 'Abstract para 2 sentence 2', 'bestseller-list entry, Wikipedia alone, AUC', '0.818', S_D3, O_D3,
    'matched/models/Wfit_E/auc_month_mean', D3('matched/models/Wfit_E/auc_month_mean'))
add(AB, 'Abstract para 2 sentence 2', 'bestseller-list entry, library model, AUC', '0.856', S_D3, O_D3,
    'matched/models/Hfit_E/auc_month_mean', D3('matched/models/Hfit_E/auc_month_mean'))
add(AB, 'Abstract para 2 sentence 4', 'main set, gain in rank correlation from adding Wikipedia to library model', '0.005', S_L, O_L,
    'decisions/L2a/est', l2a[0])
add(AB, 'Abstract para 2 sentence 4', 'main set, Wikipedia gain relative to the library model score', 'about 1.3%', S_L, O_L,
    'L2a.est / HM.rank.est', l2a[0] / hm, f=pct, kind='derived', note='0.004677 / 0.347388')
add(AB, 'Abstract para 2 sentence 5', 'new books, gain in rank correlation from Wikipedia', '+0.024', S_B, O_B, 'all/LW_minus_L/mean',
    jget(O_B, 'all/LW_minus_L/mean'))
add(AB, 'Abstract para 2 sentence 5', 'new books with no earlier book by the author, gain from Wikipedia', '+0.056', S_SC, O_SC,
    'values_original/B.none.gain', SCo('B.none.gain'))
add_range(AB, 'Abstract para 2 sentence 6', 'new books, gain from Wikipedia over the two library models with first-loan catalogue facts',
          '0.011 to 0.012', S_TW, O_TW, tw_key('all', 'Lq') + '; ' + tw_key('all', 'L0'), [tw('all', 'Lq')[0], tw('all', 'L0')[0]],
          ['Lq', 'L0'])
add_range(AB, 'Abstract para 2 sentence 6', 'new books with no earlier book by the author, gain over the same two library models',
          '0.015 to 0.017', S_TW, O_TW, tw_key('none', 'Lq') + '; ' + tw_key('none', 'L0'), [tw('none', 'Lq')[0], tw('none', 'L0')[0]],
          ['Lq', 'L0'])
nar, _ = s3('wikipedia', 'narrow', 'sustained')
mid, _ = s3('wikipedia', 'middle', 'sustained')
ten = lambda r: (all(8.5 <= pctlog(x) <= 11.5 for x in r), f'narrow {pctlog(r[0]):.2f}%, middle {pctlog(r[1]):.2f}%')  # noqa: E731
add(AB, 'Abstract para 2 sentence 8', 'hand-reviewed concept pages, extra theme borrowing after lasting rises (percent)', 'about 10%',
    S_S3, O_S3, 'main/wikipedia/{narrow,middle}/all/sustained sc_effect_p_mean, exp(x)-1', [nar[0], mid[0]], kind='derived', check=ten)
add(AB, 'Abstract para 2 sentence 10', 'main set, library plus Wikipedia, share of monthly top 20 that rose', '83%', S_L, O_L,
    'by_period/2019-2026/all/HMW14/top20/est', Le('HMW14', key='top20'), f=pct)
add(AB, 'Abstract para 2 sentence 10', 'main set, persistence rule, share of monthly top 20 that rose', '79%', S_L, O_L,
    'by_period/2019-2026/all/naive/top20/est', Le('naive', key='top20'), f=pct)

# ================================================================ Table 5.1
CH, t = '5', 'Table 5.1'
add(CH, f'{t} / Main set / Wikipedia alone', 'main set, Wikipedia alone, rank correlation with 95% interval', '0.091 (0.084 to 0.098)',
    S_L, O_L, 'by_period/2019-2026/all/W14/rank', Lr('W14'))
add(CH, f'{t} / Main set / Library model', 'main set, library model with calendar month, rank correlation', '0.347 (0.340 to 0.355)',
    S_L, O_L, 'by_period/2019-2026/all/HM/rank', Lr('HM'))
add(CH, f'{t} / Main set / Library and Wikipedia', 'main set, library plus Wikipedia, rank correlation', '0.352 (0.344 to 0.360)',
    S_L, O_L, 'by_period/2019-2026/all/HMW14/rank', Lr('HMW14'))
add(CH, f'{t} / Main set / Added by Wikipedia', 'main set, paired gain from Wikipedia, rank correlation', '+0.005 (0.004 to 0.006)',
    S_L, O_L, 'decisions/L2a (est, lo, hi)', l2a)
add(CH, f'{t} / Well-known books / Wikipedia alone', 'well-known books, Wikipedia alone, rank correlation', '0.133 (0.124 to 0.142)',
    S_A, O_A, 'change_rank/Wlgbm_D (mean, lo, hi)', Ar('Wlgbm_D'))
add(CH, f'{t} / Well-known books / Library model', 'well-known books, library model without calendar month, rank correlation',
    '0.350 (0.343 to 0.358)', S_A, O_A, 'change_rank/Hlgbm_D', Ar('Hlgbm_D'))
add(CH, f'{t} / Well-known books / Library and Wikipedia', 'well-known books, library plus Wikipedia, rank correlation',
    '0.360 (0.352 to 0.368)', S_A, O_A, 'change_rank/HWlgbm_D', Ar('HWlgbm_D'))
pa = jget(O_A, 'paired/HW_minus_H_change_rank')
add(CH, f'{t} / Well-known books / Added by Wikipedia', 'well-known books, paired gain from Wikipedia', '+0.009 (0.007 to 0.011)',
    S_A, O_A, 'paired/HW_minus_H_change_rank', [pa['mean'], pa['lo'], pa['hi']])
add(CH, f'{t} / New books / Wikipedia alone', 'new books, first six months of loans, Wikipedia alone, rank correlation',
    '0.127 (0.115 to 0.138)', S_B, O_B, 'all/W_lgbm (spearman, lo, hi)', Bs('all', 'W_lgbm'))
add(CH, f'{t} / New books / Library model', 'new books, library model, rank correlation', '0.349 (0.337 to 0.361)', S_B, O_B,
    'all/L_lgbm', Bs('all', 'L_lgbm'))
add(CH, f'{t} / New books / Library and Wikipedia', 'new books, library plus Wikipedia, rank correlation', '0.372 (0.362 to 0.383)',
    S_B, O_B, 'all/LW_lgbm', Bs('all', 'LW_lgbm'))
pb = jget(O_B, 'all/LW_minus_L')
add(CH, f'{t} / New books / Added by Wikipedia', 'new books, paired gain from Wikipedia', '+0.024 (0.019 to 0.030)', S_B, O_B,
    'all/LW_minus_L', [pb['mean'], pb['lo'], pb['hi']])
add(CH, f'{t} / Joining a list / Wikipedia alone', 'bestseller-list entry next month, Wikipedia alone, AUC', '0.818', S_D3, O_D3,
    'matched/models/Wfit_E/auc_month_mean', D3('matched/models/Wfit_E/auc_month_mean'))
add(CH, f'{t} / Joining a list / Library model', 'bestseller-list entry, library model, AUC', '0.856', S_D3, O_D3,
    'matched/models/Hfit_E/auc_month_mean', D3('matched/models/Hfit_E/auc_month_mean'))
add(CH, f'{t} / Joining a list / Library and Wikipedia', 'bestseller-list entry, library plus Wikipedia, AUC', '0.877', S_D3, O_D3,
    'matched/models/HWfit_E/auc_month_mean', D3('matched/models/HWfit_E/auc_month_mean'))
add(CH, f'{t} / Joining a list / Added by Wikipedia', 'bestseller-list entry, paired AUC gain from Wikipedia', '+0.021', S_D3, O_D3,
    'matched/paired/HWfit_E_minus_Hfit_E/auc', D3('matched/paired/HWfit_E_minus_Hfit_E/auc'))
EV = jget(O_E, 'rows_with_views')['corrected']
eW, eH, eHW = EV['rank|E1_W'], EV['rank|E1_H'], EV['rank|E1_HW']
add(CH, f'{t} / LibriVox / Wikipedia alone', 'LibriVox months with views, Wikipedia alone, rank correlation of listening change', '0.052',
    S_E, O_E, 'rows_with_views/corrected/rank|E1_W', eW)
add(CH, f'{t} / LibriVox / Library model', 'LibriVox, model of own listening history, rank correlation', '0.364', S_E, O_E,
    'rows_with_views/corrected/rank|E1_H', eH)
add(CH, f'{t} / LibriVox / Library and Wikipedia', 'LibriVox, listening history plus Wikipedia, rank correlation', '0.359', S_E, O_E,
    'rows_with_views/corrected/rank|E1_HW', eHW)
add(CH, f'{t} / LibriVox / Added by Wikipedia', 'LibriVox, change from adding Wikipedia', '−0.005', S_E, O_E,
    'rank|E1_HW minus rank|E1_H (rows_with_views/corrected)', eHW - eH, kind='derived', note='0.35910 - 0.36441')
add(CH, f'{t} / Themes / Books', 'number of theme series scored', '510', S_C, O_C, 'coverage/series', jget(O_C, 'coverage/series'))
vc = jget(O_C, 'rank/Wsel_ridge')
add(CH, f'{t} / Themes / Wikipedia alone', 'themes, Wikipedia alone with pages chosen from earlier years, rank correlation',
    '0.070 (0.052 to 0.087)', S_C, O_C, 'rank/Wsel_ridge (mean, lo, hi)', [vc['mean'], vc['lo'], vc['hi']])
add(CH, f'{t} / Themes / Library model', "themes, pretrained forecaster on the theme's own history, rank correlation", '0.320', S_C, O_C,
    'rank/chronos2/mean', jget(O_C, 'rank/chronos2/mean'))

# ================================================================ 5.1
s = '5.1 paragraph "The main set"'
rwp = jget(O_L, 'by_period/2019-2026/all/_rows_with_page')
add(CH, s, 'main set, rows with a book or author article, Wikipedia alone, rank correlation', '0.112', S_L, O_L,
    'by_period/2019-2026/all/_rows_with_page/W14/est', rwp['W14']['est'])
for fm, pr in (('print', '0.056'), ('ebook', '0.098'), ('audiobook', '0.119')):
    add(CH, s, f'main set, {fm}, Wikipedia alone, rank correlation', pr, S_L, O_L, f'by_period/2019-2026/{fm}/W14/rank/est', Le('W14', fm))
add(CH, s, 'main set, Wikipedia alone, surge average precision as multiple of chance', '2.2', S_L, O_L,
    'by_period/2019-2026/all/W14/surge_ap_ratio', Le('W14', key='surge_ap_ratio'))
add(CH, s, 'main set, Wikipedia alone, share of monthly top 20 that rose', '34.1%', S_L, O_L, 'by_period/2019-2026/all/W14/top20/est',
    Le('W14', key='top20'), f=pct)
base_rose = jget(O_L, 'by_period/2019-2026/all/_base_rose')
add(CH, s, 'main set, base rate of rising (random pick)', '11.8%', S_L, O_L, 'by_period/2019-2026/all/_base_rose', base_rose, f=pct)
s = '5.1 paragraph "The well-known books"'
sa = jget(O_A, 'surge_ap/Wlgbm_D')
add(CH, s, 'well-known books, Wikipedia alone, surge average precision as multiple of chance', '3.4 … (3.1 to 3.8)', S_A, O_A,
    'surge_ap/Wlgbm_D (ratio, ratio_lo, ratio_hi)', [sa['ratio'], sa['ratio_lo'], sa['ratio_hi']])
add(CH, s, 'well-known books, Wikipedia alone, share of top 20 that rose', '57.9%', S_SC, O_SC, 'values_corrected/A.top20.rose.W',
    SCc('A.top20.rose.W'), f=pct)
s = '5.1 paragraph "The placebo"'
add(CH, s, "well-known books given another book's pages, rank correlation", '0.010', S_PL, O_PL, 'pW_D/change_rank',
    jget(O_PL, 'pW_D/change_rank'))
pdl = jget(O_PL, 'Wlgbm_D_minus_pW_D')
add(CH, s, 'drop in rank correlation from real to placebo pages', '0.124 (0.114 to 0.133)', S_PL, O_PL, 'Wlgbm_D_minus_pW_D (mean, lo, hi)',
    [pdl['mean'], pdl['lo'], pdl['hi']])
add(CH, '5.1 paragraph "New books"', 'new books, author-has-article flag alone, rank correlation', '0.109', S_SC, O_SC,
    'values_original/B.rank.matched_pre', SCo('B.rank.matched_pre'))
s = '5.1 paragraph "Bestseller lists"'
add(CH, s, 'bestseller entry, books held 36+ months, Wikipedia alone, AUC', '0.794', S_D3, O_D3, 'matched/by_age/ge36/Wfit_E',
    D3('matched/by_age/ge36/Wfit_E'))
add(CH, s, 'bestseller entry, books held 36+ months, library model, AUC', '0.791', S_D3, O_D3, 'matched/by_age/ge36/Hfit_E',
    D3('matched/by_age/ge36/Hfit_E'))
add(CH, s, 'number of well-known books', '7,747', S_A, O_A, 'n/books', jget(O_A, 'n/books'))
for m, pr, lb in (('Wfit_E', '0.821', 'Wikipedia alone'), ('Hfit_E', '0.885', 'library model'), ('HWfit_E', '0.898', 'both')):
    add(CH, s, f'bestseller entry, all well-known books, {lb}, AUC', pr, S_D3, O_D3, f'all/models/{m}/auc_month_mean',
        D3(f'all/models/{m}/auc_month_mean'))
add(CH, '5.1 paragraph "Loan counts"', 'well-known books, mean next-month loans', '22', S_SC, O_SC, 'values_corrected/A.mean_next_loans',
    SCc('A.mean_next_loans'))
acc = C(O_ACC).set_index('model')
for rowname, pr, lb in (('No information (average book)', '17.1', 'no information'), ('Wikipedia only (trees)', '15.8', 'Wikipedia alone'),
                        ('Repeat last month', '5.0', 'repeating last month'), ('Library history (trees)', '4.6', 'library model')):
    add(CH, f'Table 5.2 / {lb}', f'well-known books, mean absolute error of next-month loans, {lb}', pr, S_ACC, O_ACC,
        f'row "{rowname}", column MAE_loans', float(acc.loc[rowname, 'MAE_loans']))
add(CH, '5.1 paragraph after Table 5.2', 'new books, mean error in loans, Wikipedia alone', '40.96', S_B, O_B, 'all/W_lgbm/mae_loans',
    jget(O_B, 'all/W_lgbm/mae_loans'))
add(CH, '5.1 paragraph after Table 5.2', 'new books, mean error in loans, no information', '41.00', S_B, O_B, 'all/N0/mae_loans',
    jget(O_B, 'all/N0/mae_loans'))
s = '5.1 paragraph "Themes"'
add(CH, s, 'themes, Wikipedia alone, pages chosen from earlier months, rank correlation', '0.070', S_C, O_C, 'rank/Wsel_ridge/mean', vc['mean'])
add(CH, s, 'themes, pages chosen and fitted on all months (hindsight), rank correlation', '0.376', S_C, O_C, 'rank/Wsel_insample/mean',
    jget(O_C, 'rank/Wsel_insample/mean'))

# ================================================================ 5.2
s = '5.2 paragraph "Existing books"'
add(CH, s, 'main set, gain from Wikipedia, all formats', '+0.005', S_L, O_L, 'decisions/L2a/est', l2a[0])
for fm, pr in (('print', '+0.003'), ('ebook', '+0.005'), ('audiobook', '+0.006')):
    a_, b_ = Le('HMW14', fm), Le('HM', fm)
    add(CH, s, f'main set, {fm}, gain from Wikipedia', pr, S_L, O_L, f'by_period/2019-2026/{fm}: HMW14.rank.est minus HM.rank.est', a_ - b_,
        kind='derived', note=f'{a_:.4f} - {b_:.4f} (no paired value stored per format)')
add(CH, s, 'well-known books, gain from Wikipedia', '+0.009', S_A, O_A, 'paired/HW_minus_H_change_rank/mean', pa['mean'])
add(CH, s, 'main set, library model, share of top 20 that rose', '83.2%', S_L, O_L, 'by_period/2019-2026/all/HM/top20/est',
    Le('HM', key='top20'), f=pct)
add(CH, s, 'main set, library plus Wikipedia, share of top 20 that rose', '83.4%', S_L, O_L, 'by_period/2019-2026/all/HMW14/top20/est',
    Le('HMW14', key='top20'), f=pct)
add(CH, s, 'main set, change in top-20 share from adding Wikipedia, points', '+0.2 points, −0.6 to +1.0', S_L, O_L,
    'by_period/2019-2026/all/_diff/HMW14_minus_HM_top20', Ld('HMW14_minus_HM_top20'), f=pct)
add(CH, s, 'main set, library model, mean absolute error of log loans', '0.347', S_L, O_L, 'by_period/2019-2026/all/HM/mae_y/est',
    Le('HM', key='mae_y'))
add(CH, s, 'main set, library plus Wikipedia, mean absolute error of log loans', '0.347', S_L, O_L,
    'by_period/2019-2026/all/HMW14/mae_y/est', Le('HMW14', key='mae_y'))
tm = jget(O_TW, 'main_set/gains/Wikipedia over HM (main)')
add(CH, s, 'main set, gain from Wikipedia, interval drawing works and three-month blocks together', '0.0035 to 0.0060', S_TW, O_TW,
    'main_set/gains/Wikipedia over HM (main)/iii', list(tm['iii']), stored_str=f"{tm['iii'][0]!r} to {tm['iii'][1]!r}",
    note=f'estimate {tm["est"]!r}')
s = '5.2 paragraph "New books"'
add(CH, s, 'new books, gain from Wikipedia', '+0.024', S_B, O_B, 'all/LW_minus_L/mean', pb['mean'])
pm = jget(O_B, 'matched/LW_minus_L')
add(CH, s, "new books whose author's article had earlier views, gain from Wikipedia", '+0.050 (0.042 to 0.059)', S_B, O_B,
    'matched/LW_minus_L', [pm['mean'], pm['lo'], pm['hi']])
add(CH, s, 'new books, gain from Wikipedia, interval drawing authors and first-loan years together', '0.017 to 0.031', S_TW, O_TW,
    tw_key('all', 'L', 'iii'), tw('all', 'L', 'iii')[1:], stored_str=' to '.join(repr(x) for x in tw('all', 'L', 'iii')[1:]),
    note=f"estimate {tw('all', 'L')[0]!r}",
    why='the upper end shows as 0.0315 in two_way_intervals.md and was rounded a second time; 0.031462 rounds to 0.031')
nb = jget(O_TW, 'new_books/all/scores')
add(CH, s, 'new books, the two library models with first-loan catalogue facts, rank correlation', 'about 0.50', S_TW, O_TW,
    'new_books/all/scores/Lq_lgbm/est and /L0_lgbm/est', [nb['Lq_lgbm']['est'], nb['L0_lgbm']['est']], kind='derived',
    check=lambda r: (all(abs(x - 0.50) < 0.01 for x in r), f'Lq {r[0]:.3f}, L0 {r[1]:.3f}'))
add(CH, s, 'new books, main library model, rank correlation (for comparison)', '0.35', S_TW, O_TW, 'new_books/all/scores/L_lgbm/est',
    nb['L_lgbm']['est'])
add(CH, s, 'new books, gain over a library model with catalogue facts (no theme)', '+0.011', S_ROB, O_ROB,
    'short_answer_numbers/b2_stronger/LqW_minus_Lq/mean', jget(O_ROB, 'short_answer_numbers/b2_stronger/LqW_minus_Lq/mean'),
    note=f"same value in {O_TW}, {tw_key('all', 'Lq')}")
add(CH, s, 'new books, gain over a library model with first-month records', '+0.012', S_ROB, O_ROB,
    'short_answer_numbers/b2_stronger/L0W_minus_L0/mean', jget(O_ROB, 'short_answer_numbers/b2_stronger/L0W_minus_L0/mean'),
    note=f"same value in {O_TW}, {tw_key('all', 'L0')}")
g_all, g_q, g_0 = tw('all', 'L')[0], tw('all', 'Lq')[0], tw('all', 'L0')[0]
add(CH, s, 'share of the new-book gain that stays over the stronger library models', 'About half', S_TW, O_TW,
    'gain over Lq and over L0 divided by gain over L (new_books/all/gains)', [g_q / g_all, g_0 / g_all], kind='derived',
    check=lambda r: (all(0.4 <= x <= 0.6 for x in r), f'{r[0]:.2f} (Lq), {r[1]:.2f} (L0)'))
s = '5.2 paragraph "Longer windows"'
for k, pr in (('3', '+0.011'), ('6', '+0.011'), ('12', '+0.010'), ('1', '+0.009')):
    add(CH, s, f'well-known books, gain from Wikipedia, average of next {k} month(s)', pr, S_D1, O_D1, f'by_k/{k}/spearman/HW_minus_H/mean',
        D1(k, 'HW_minus_H')[0])
for k, pr in (('1', '0.350'), ('3', '0.444'), ('12', '0.509')):
    add(CH, s, f'well-known books, library model, rank correlation, {k}-month window', pr, S_D1, O_D1, f'by_k/{k}/spearman/H/mean',
        D1(k, 'H')[0])
s = '5.2 paragraph "Themes"'
add(CH, s, 'number of forecasting pipelines compared', '52', S_BM, O_BM2, 'Comparisons table, row A2, column pipelines', 52,
    note='stored line: ' + md(O_BM2, 'A2 | 36081 | 510 | 88 | 52 |') + ' (report also rewritten by 13_stage2_report.py)')
bm = C(O_BMP)
chron = bm[(bm.kind == 'behavior against no behavior') & (bm.base == 'chronos2')]
add(CH, s, 'largest error reduction from adding interest to the pretrained forecaster', 'at most 0.6%', S_BM, O_BMP,
    'min mae_ratio over rows base=chronos2, kind "behavior against no behavior"; 1 minus ratio', chron.mae_ratio.min(), f=less1pct,
    note='chronos2 to chronos2_cur')
chg = bm[(bm.kind == 'behavior against no behavior') & bm.base.isin(['catchg_D', 'lgbmchg_D', 'ridgechg_D'])]
n_up, n_all, n_lo = int((chg.mae_ratio > 1).sum()), len(chg), int((chg.mae_lo > 1).sum())
n_lo_zero = int(((chg.mae_lo > 1) & ((100 * (chg.mae_lo - 1)).round(1) == 0)).sum())
CHG_KEY = 'the 24 rows with base in {catchg_D, lgbmchg_D, ridgechg_D}, kind "behavior against no behavior"'
add(CH, s, 'change-trained trees and ridge: cases where adding interest raised the error (point estimate)', '23 of 24', S_BM, O_BMP,
    f'count mae_ratio > 1 among {CHG_KEY}', [n_up, n_all], kind='derived', stored_str=f'{n_up} of {n_all}',
    note='the smallest rise is ridgechg_D to ridgechg_DVdem, 1.000033')
add(CH, s, 'largest error increase from adding interest to a change-trained model', 'up to 1.5%', S_BM, O_BMP,
    f'max mae_ratio among {CHG_KEY}, minus 1', chg.mae_ratio.max(), f=ratio_pct, note='lgbmchg_D to lgbmchg_DVdem')
add(CH, s, 'change-trained models: cases whose error interval lay above zero', '16', S_BM, O_BMP, f'count mae_lo > 1 among {CHG_KEY}',
    n_lo, kind='derived')
add(CH, s, 'of those, cases whose lower end prints as +0.0% in Table D.2', 'eight', S_BM, O_BMP,
    'count mae_lo > 1 with 100*(mae_lo-1) rounding to 0.0, same rows', n_lo_zero, kind='derived',
    check=lambda r: (r[0] == 8, f'{r[0]}'))

# ================================================================ 5.3
s = '5.3 paragraph "The book\'s own pages"'
add(CH, s, 'main set, rows with an article, gain from Wikipedia', '+0.007', S_L, O_L, '_rows_with_page: HMW14.est minus HM.est',
    rwp['HMW14']['est'] - rwp['HM']['est'], kind='derived', note='0.35481 - 0.34815')
add(CH, s, 'main set, rows with an article, library plus Wikipedia, rank correlation', '0.355', S_L, O_L, '_rows_with_page/HMW14/est',
    rwp['HMW14']['est'])
add(CH, s, 'main set, rows with an article, library model, rank correlation', '0.348', S_L, O_L, '_rows_with_page/HM/est', rwp['HM']['est'])
add(CH, s, 'main set, gain from Wikipedia over all rows', '+0.005', S_L, O_L, 'decisions/L2a/est', l2a[0])
add(CH, s, 'main set, 14 against 18 Wikipedia features, difference in rank correlation', '−0.0002, −0.0008 to 0.0004', S_L, O_L,
    'by_period/2019-2026/all/_diff/W14_minus_W18_rank', Ld('W14_minus_W18_rank'))
s = '5.3 paragraph "Hand-reviewed concept pages"'
add(CH, s, 'concept pages, narrow themes, lasting rises, extra borrowing months 0-2 (percent)', '9.2%', S_S3, O_S3,
    'main/wikipedia/narrow/all/sustained sc_effect_p_mean, exp(x)-1', nar[0], f=pctlog)
add(CH, s, 'concept pages, narrow themes, lasting rises, log-share effect', '+0.088 on the log scale, 0.029 to 0.156', S_S3, O_S3,
    'main/wikipedia/narrow/all/sustained sc_effect_p (mean, ci_low, ci_high)', nar)
add(CH, s, 'concept pages, middle themes, lasting rises, extra borrowing months 0-2 (percent)', '11.0%', S_S3, O_S3,
    'main/wikipedia/middle/all/sustained sc_effect_p_mean, exp(x)-1', mid[0], f=pctlog)
add(CH, s, 'concept pages, middle themes, lasting rises, log-share effect', '+0.105, 0.018 to 0.227', S_S3, O_S3,
    'main/wikipedia/middle/all/sustained sc_effect_p', mid)
fn, _ = s3('wikipedia', 'narrow', 'fading')
fmd, _ = s3('wikipedia', 'middle', 'fading')
add(CH, s, 'concept pages, rises of one or two weeks, extra borrowing (percent)', 'about 2%', S_S3, O_S3, 'fading rows, exp(x)-1',
    [fn[0], fmd[0]], kind='derived',
    check=lambda r: (all(1.5 <= pctlog(x) <= 3.0 for x in r), f'narrow {pctlog(r[0]):.2f}%, middle {pctlog(r[1]):.2f}%'))
add(CH, s, 'concept pages, narrow themes, rises of one or two weeks, log-share effect', '+0.019 (0.002 to 0.037)', S_S3, O_S3,
    'main/wikipedia/narrow/all/fading sc_effect_p', fn)
add(CH, s, 'concept pages, middle themes, rises of one or two weeks, log-share effect', '+0.026 (0.004 to 0.049)', S_S3, O_S3,
    'main/wikipedia/middle/all/fading sc_effect_p', fmd)
for w, pr in (('months 0 to 2', '+0.093 (0.042 to 0.154)'), ('months 3 to 5', '+0.107 (0.057 to 0.159)'),
              ('months 6 to 11', '+0.048 (0.006 to 0.097)')):
    add(CH, s, f'concept pages, narrow and middle pooled, lasting rises, {w}, log-share effect', pr, S_D1T, O_D1T,
        f'series "concept pages (hand-checked, Chapter 6)", synthetic control, {w}',
        d1t('concept pages (hand-checked, Chapter 6)', 'synthetic control', w))
CO3, CO3B = 'reports/study3_13_carryover.md', 'reports/study3b_13_carryover.md'
dur_rows = [md(CO3, '| wikipedia | narrow | class_sustained | 0.067 | 0.015 | 0.140 | 0.010 |'),
            md(CO3B, '| wikipedia | middle | class_sustained | 0.145 | 0.024 | 0.341 | 0.013 |'),
            md(CO3, '| wikipedia | middle | class_sustained | 0.043 | -0.072 | 0.186 | 0.490 |'),
            md(CO3B, '| wikipedia | narrow | class_sustained | 0.043 | -0.035 | 0.128 | 0.270 |')]
dur_p = [float(r.strip('| ').split('|')[-1]) for r in dur_rows]
add(CH, s, 'duration terms (lasting against short rise) with p below 0.05, Wikipedia, narrow and middle, two models', 'two',
    'main_study/study3/13_carryover.py; main_study/study3b/13_carryover.py', f'{CO3}; {CO3B}',
    'rows wikipedia|narrow|class_sustained and wikipedia|middle|class_sustained in both reports', sum(p < 0.05 for p in dur_p),
    kind='derived', stored_str=f'{sum(p < 0.05 for p in dur_p)} of 4 (p = ' + ', '.join(f'{p:.3f}' for p in dur_p) + ')',
    check=lambda r: (r[0] == 2, 'p of the four duration terms: ' + ' / '.join(dur_rows)))
s = '5.3 paragraph on single rises'
cnt = md(O_S3MD, '- main: 2108 tests; one-sided p < 0.05: 102; BH q < 0.1: 0')
add(CH, s, 'single-rise tests, Wikipedia and news together', '2,108', S_S3, O_S3MD, 'section "Detection", line "main"', 2108,
    note='stored line: ' + cnt)
_, tw_m = s3('wikipedia', 'middle', 'all')
_, tw_n = s3('wikipedia', 'narrow', 'all')
_, tg_m = s3('gdelt', 'middle', 'all')
_, tg_n = s3('gdelt', 'narrow', 'all')
add(CH, s, 'single-rise tests, Wikipedia rises', '1,333', S_S3, O_S3, 'tests of main/wikipedia/{middle,narrow}/all/all', tw_m + tw_n,
    kind='derived', note=f'{tw_m} + {tw_n}')
add(CH, s, 'single-rise tests, news rises', '775', S_S3, O_S3, 'tests of main/gdelt/{middle,narrow}/all/all', tg_m + tg_n,
    kind='derived', note=f'{tg_m} + {tg_n}')
add(CH, s, 'single-rise tests with one-sided p below 0.05', '102', S_S3, O_S3MD, 'section "Detection", line "main"', 102)
add(CH, s, 'share of single-rise tests with p below 0.05', '4.8%', S_S3, O_S3MD, '102 / 2108', 102 / 2108, f=pct, kind='derived')
add(CH, s, 'single-rise tests passing the Benjamini-Hochberg correction', 'none', S_S3, O_S3MD, 'section "Detection", "BH q < 0.1: 0"', 0,
    check=lambda r: (r[0] == 0, ''))
add(CH, s, 'smallest injected lift detected reliably in one theme', 'about +50%', S_S3P, O_S3P,
    'minimum detectable lift by level and format (smallest lift detected in at least 80% of draws)', 0.5, f=pct,
    note='only middle-level ebooks reach it, at 0.5 (' + md('reports/study3_11_power.md', '### middle, ebook: minimum detectable lift 0.5')
    + '); every other level and format detects none of the sizes tried, up to 0.5; also in reports/study3_11_power.md')
s = '5.3 paragraph "Pages sorted by the AI model"'
g1 = jget(O_TF, 'G1/scores')[0]
add(CH, s, 'pages judged by a separate model', '400', S_TF, O_TF, 'G1/scores[0]/pages', g1['pages'])
add(CH, s, 'AI sorting against the judge, precision (narrow level, all pairs)', '0.849', S_TF, O_TF, 'G1/scores[0]/precision', g1['precision'])
add(CH, s, 'AI sorting against the judge, recall', '0.815', S_TF, O_TF, 'G1/scores[0]/recall', g1['recall'])
kinds = jget(O_TF, 'sorting/pages/kinds')
tot = sum(kinds.values())
for k, pr in (('person', '46%'), ('work', '16%'), ('event', '13%'), ('concept', '8%')):
    add(CH, s, f'share of sorted pages of kind "{k}"', pr, S_TF, O_TF, f'sorting/pages/kinds/{k} divided by the sum over kinds',
        kinds[k] / tot, f=pct, kind='derived', note=f'{kinds[k]} / {tot}')
s = '5.3 paragraph on AI-sorted rises'
g2 = jget(O_TF, 'G2/summary/decision_G2_panel_a_lasting')
gs, go = g2['both|synthetic_control'], g2['both|own_trend']
add(CH, s, 'AI-sorted pages, lasting rises, borrowing against synthetic control (percent)', '1.8% … (0.05% to 3.6%)', S_TF, O_TF,
    'G2/summary/decision_G2_panel_a_lasting/both|synthetic_control (effect, ci_low, ci_high), exp(x)-1',
    [gs['effect'], gs['ci_low'], gs['ci_high']], f=pctlog)
add(CH, s, "AI-sorted pages, lasting rises, borrowing against the theme's own trend (percent)", '−0.2%, −2.5% to 2.0%', S_TF, O_TF,
    'G2/summary/decision_G2_panel_a_lasting/both|own_trend, exp(x)-1', [go['effect'], go['ci_low'], go['ci_high']], f=pctlog)
c2 = C(O_TFC)
c2r = c2[(c2.panel == 'a') & (c2.analysis == 'main') & (c2.level == 'both') & (c2.format == 'all')
         & (c2.duration_class == 'sustained')].iloc[0]
add(CH, s, 'AI concept pages only, lasting rises, against synthetic control (percent)', '2.9% (0.1% to 5.6%)', S_TFC, O_TFC,
    'panel a, main, both, all, sustained: sc_effect_p (mean, ci_low, ci_high), exp(x)-1',
    [c2r['sc_effect_p_mean'], c2r['sc_effect_p_ci_low'], c2r['sc_effect_p_ci_high']], f=pctlog, note='script run with --series S2C')
add(CH, s, 'AI concept pages only, lasting rises, against own trend (percent)', '1.2% (−2.3% to 4.6%)', S_TFC, O_TFC,
    'same row: es_effect_p, exp(x)-1', [c2r['es_effect_p_mean'], c2r['es_effect_p_ci_low'], c2r['es_effect_p_ci_high']], f=pctlog)
add(CH, s, 'hand-reviewed concept pages, narrow and middle effects (percent), as a range', '9 to 11%', S_S3, O_S3,
    'narrow and middle sustained sc_effect_p_mean, exp(x)-1', [nar[0], mid[0]], f=pctlog)
for w, pr in (('months 3 to 5', '+0.016 (−0.002 to 0.035)'), ('months 6 to 11', '+0.008 (−0.010 to 0.026)')):
    add(CH, s, f'AI-sorted pages, lasting rises, {w}, log-share effect', pr, S_D1T, O_D1T, f'series "S2 (AI pages)", synthetic control, {w}',
        d1t('S2 (AI pages)', 'synthetic control', w))
add(CH, s, 'AI-sorted series as forecaster input, error reduction', '0.21%', S_G3, O_G3, 'chronos2 to chronos2_ais2, 1 minus mae_ratio',
    C(O_G3).iloc[0]['mae_ratio'], f=less1pct)
add(CH, s, 'AI concept series as forecaster input, error reduction', '0.34%', S_G3H, O_G3H, 'chronos2 to chronos2_aic2, 1 minus mae_ratio',
    C(O_G3H).iloc[0]['mae_ratio'], f=less1pct)
add(CH, s, 'hand-reviewed concept pages as forecaster input, error reduction', '0.62%', S_BM, O_BMP,
    'chronos2 to chronos2_cur, 1 minus mae_ratio', bmp('chronos2', 'chronos2_cur'), f=less1pct)
s = '5.3 paragraph "Pages linked through Wikidata"'
add(CH, s, 'number of linked Wikipedia pages', '10,283', S_J1, O_J1, 'point 1', 10283, note=md(O_J1, 'These point to 10,283 different articles'))
add(CH, s, 'alert list, books not yet risen, change from linked-page bursts, points', '−0.4', S_J2, O_J2P,
    'S1, not_yet, HWENL minus HWEN, p20', j2p('S1', 'not_yet', 'HWENL', 'HWEN')[0], f=pct)
add(CH, s, 'alert list, books not yet risen, change from the event calendar, points', '+0.3', S_J2, O_J2P,
    'S1, not_yet, HWE minus HW, p20', j2p('S1', 'not_yet', 'HWE', 'HW')[0], f=pct)
add(CH, s, 'alert list with dates moved 12 months earlier, precision at 20', '38.6%', S_J2, O_J2M, 'S1, not_yet, placebo, p20',
    j2m('S1', 'not_yet', 'placebo'), f=pct)
add(CH, s, 'full alert list, precision at 20, books not yet risen', '39.4%', S_J2, O_J2M, 'S1, not_yet, HWENL, p20',
    j2m('S1', 'not_yet', 'HWENL'), f=pct)
add(CH, s, 'real dates minus moved dates, points', '+0.8, −0.3 to +1.7', S_J2, O_J2P, 'S1, not_yet, HWENL minus placebo, p20',
    j2p('S1', 'not_yet', 'HWENL', 'placebo'), f=pct)
add(CH, s, 'real dates minus moved dates, surges within three months, points', '2.2', S_J2, O_J2P,
    'S3, not_yet, HWENL minus placebo, p20', j2p('S3', 'not_yet', 'HWENL', 'placebo')[0], f=pct)
s = '5.3 paragraph "Theme forecasts"'
add(CH, s, 'number of forecasting pipelines compared', '52', S_BM, O_BM2, 'Comparisons table, row A2, column pipelines', 52,
    note='stored line: ' + md(O_BM2, 'A2 | 36081 | 510 | 88 | 52 |') + ' (report also rewritten by 13_stage2_report.py)')
at = C(O_BMT).set_index('Unnamed: 0')
add(CH, s, 'best pipeline, error below repeating last month (percent)', '8.6%', S_BM, O_BMT, 'row chronos2_cur, 1 minus AvgRelMAE',
    float(at.loc['chronos2_cur', 'AvgRelMAE']), f=less1pct)
add(CH, 'Figure 5.2 caption', 'log-share 0.10 expressed as percent', '+10.5%', '(conversion)', '(none)', 'exp(0.10)-1', 0.10, f=pctlog)

# ================================================================ 5.4
s = '5.4 paragraph "New books with no library model"'
for k, pr, lb in (('B.none.L', '0.045', 'library model'), ('B.none.W', '0.090', 'Wikipedia alone'), ('B.none.LW', '0.101', 'both')):
    add(CH, s, f'new books, author with no earlier Seattle book, {lb}', pr, S_SC, O_SC, f'values_original/{k}', SCo(k))
add(CH, s, 'new books, author with no earlier Seattle book, gain from Wikipedia, interval drawing authors', '+0.056, 0.048 to 0.064',
    S_TW, O_TW, tw_key('none', 'L', 'i'), tw('none', 'L', 'i'))
add(CH, s, 'new books, author with an earlier Seattle book, gain from Wikipedia, interval drawing authors', '+0.020 (0.013 to 0.030',
    S_TW, O_TW, tw_key('some', 'L', 'i'), tw('some', 'L', 'i'))
add_range(CH, s, 'no earlier book by the author: gain over the two library models with first-loan catalogue facts', '+0.015 to +0.017',
          S_TW, O_TW, tw_key('none', 'Lq') + '; ' + tw_key('none', 'L0'), [tw('none', 'Lq')[0], tw('none', 'L0')[0]], ['Lq', 'L0'])
add_range(CH, s, 'earlier book by the author: gain over the same two library models', '+0.010 to +0.011', S_TW, O_TW,
          tw_key('some', 'Lq') + '; ' + tw_key('some', 'L0'), [tw('some', 'Lq')[0], tw('some', 'L0')[0]], ['Lq', 'L0'],
          why='the L0 gain shows as 0.0115 in two_way_intervals.md and was rounded up a second time; 0.011454 rounds to 0.011')
s = '5.4 paragraph "New recordings on LibriVox"'
ln = jget(O_LN, 'LightGBM|all')
add(CH, s, 'new LibriVox recordings, Wikipedia alone, AUC for top 20%', '0.558 (0.526 to 0.588)', S_LN, O_LN, 'LightGBM|all/auc/W',
    [ln['auc']['W']['est'], ln['auc']['W']['lo'], ln['auc']['W']['hi']])
add(CH, s, "new LibriVox recordings, model of the platform's own record, AUC", '0.726', S_LN, O_LN, 'LightGBM|all/auc/R/est',
    ln['auc']['R']['est'])
add(CH, s, 'new LibriVox recordings, change in AUC from adding Wikipedia', '−0.002 (−0.027 to +0.017)', S_LN, O_LN,
    'LightGBM|all/auc_RW_minus_R', [ln['auc_RW_minus_R']['est'], ln['auc_RW_minus_R']['lo'], ln['auc_RW_minus_R']['hi']])
lnn = jget(O_LN, 'LightGBM|new_author/auc_RW_minus_R')
add(CH, s, 'new LibriVox recordings by authors with no earlier recording, change in AUC', '+0.002 (−0.033 to +0.033)', S_LN, O_LN,
    'LightGBM|new_author/auc_RW_minus_R', [lnn['est'], lnn['lo'], lnn['hi']])
s = '5.4 paragraph "Books not yet risen"'
add(CH, s, 'main set, works not yet risen, library model, top-20 share that rose', '41.8%', S_L, O_L,
    'by_period/2019-2026/all/HM/early_top20/est', Le('HM', key='early_top20'), f=pct)
add(CH, s, 'main set, works not yet risen, library plus Wikipedia, top-20 share that rose', '40.5%', S_L, O_L,
    'by_period/2019-2026/all/HMW14/early_top20/est', Le('HMW14', key='early_top20'), f=pct)
add(CH, s, 'main set, works not yet risen, change from adding Wikipedia, points', '−1.3 points, −2.6 to −0.2', S_L, O_L, 'decisions/L2b',
    Ld('L2b_HMW14_minus_HM_early_top20'), f=pct)
add(CH, s, 'well-known books not yet risen, library model, top-20 share that surged', '35.2%', S_J2, O_J2M, 'S1, not_yet, H, p20',
    j2m('S1', 'not_yet', 'H'), f=pct)
add(CH, s, 'well-known books not yet risen, full model, top-20 share that surged', '39.4%', S_J2, O_J2M, 'S1, not_yet, HWENL, p20',
    j2m('S1', 'not_yet', 'HWENL'), f=pct)
add(CH, s, 'well-known books not yet risen, full model minus library model, points', '+4.2 points, 1.8 to 6.5', S_J2, O_J2P,
    'S1, not_yet, HWENL minus H, p20', j2p('S1', 'not_yet', 'HWENL', 'H'), f=pct)
add(CH, s, "contribution of the book's own pages, points", '+3.1, 0.7 to 5.5', S_J2, O_J2P, 'S1, not_yet, HW minus H, p20',
    j2p('S1', 'not_yet', 'HW', 'H'), f=pct)
add(CH, s, 'contribution of bestseller lists, points', '+1.2, 0.4 to 2.2', S_J2, O_J2P, 'S1, not_yet, HWEN minus HWE, p20',
    j2p('S1', 'not_yet', 'HWEN', 'HWE'), f=pct)
eh, ehw = SCc('A.early.H'), SCc('A.early.HW')
add(CH, s, 'well-known books, early-warning list (rose), change from adding Wikipedia, points', '+0.1 points', S_SC, O_SC,
    'values_corrected/A.early.HW minus A.early.H', ehw - eh, f=pct, kind='derived', note=f'{ehw:.6f} - {eh:.6f}')
add(CH, s, 'well-known books, early-warning list, library model, share that rose', '59.2%', S_SC, O_SC, 'values_corrected/A.early.H', eh, f=pct)
add(CH, s, 'well-known books, early-warning list, library plus Wikipedia, share that rose', '59.4%', S_SC, O_SC,
    'values_corrected/A.early.HW', ehw, f=pct)
s = '5.4 paragraph "Different books"'
for k, pr, lb in (('A.top20.already_up.H', '90.1%', "library model's top 20 already risen at the origin"),
                  ('A.top20.already_up.W', '46.2%', 'Wikipedia-only top 20 already risen'),
                  ('A.overlap.share', '78.4%', "Wikipedia-only top 20 outside the library's top 50"),
                  ('A.overlap.rose_monthly', '47.5%', 'of those outside picks, share that rose')):
    add(CH, s, f'well-known books, {lb}', pr, S_SC, O_SC, f'values_corrected/{k}', SCc(k), f=pct)
s = '5.4 paragraph "Events"'
d2row = md(O_D2, '| Film or TV release in t+1..t+3 | 1,134 (380) | 54.3% (50.0% to 58.9%) | 34.7% (30.4% to 39.3%) | 22.8% / 6.4% |')
D2KEY = 'section 3 table "All books", row "Film or TV release in t+1..t+3"'
add(CH, s, 'books with a screen release in the next three months, share that rose', '54.3%', S_D2, O_D2, f'{D2KEY}, column rose', 54.3,
    note='Markdown value; full precision in db/wiki_led/dirs/d2_events/alert_precision_all_months.csv')
add(CH, s, 'same books, share that surged', '34.7%', S_D2, O_D2, f'{D2KEY}, column surged', 34.7)
add(CH, s, 'all books, share that rose', '22.8%', S_D2, O_D2, f'{D2KEY}, base rose', 22.8)
add(CH, s, 'all books, share that surged', '6.4%', S_D2, O_D2, f'{D2KEY}, base surged', 6.4)
add(CH, s, 'share of surges near a dated event', '4.8%', S_D2, O_D2, 'coverage table, row "Any event"', 988 / 20484, f=pct,
    note=md(O_D2, '| Any event | 988 of 20,484 | 4.8% (4.4% to 5.3%) |'))
add(CH, s, 'number of surges, 2016 to 2026', '20,484', S_D2, O_D2, 'coverage table, row "Any event"', 20484)
add(CH, s, 'swap versions in which alert books lowered the library top-20 hit rate', '43 of 48', S_D2, O_D2,
    'paragraph after the swap tables', [43, 48], stored_str='43 of 48',
    note=md(O_D2, 'Of the 48 differences in the two swap tables') + ' ... ' + md(O_D2, '43 have an interval below 0'))
add(CH, s, 'adaptations with a release date in Wikidata before the release month (percent)', '34%', S_K2, O_K2, 'In plain words, point 2', 34,
    note=md(O_K2, 'already on Wikidata before the release month for 34% of them'))
add(CH, s, 'adaptations checked for date history', '609', S_K2, O_K2, 'header line "Coverage: 609 of 609"', 609,
    note=md(O_K2, 'Coverage: 609 of 609 adaptation items done'))
s = '5.4 paragraph "Over time and by format"'
add(CH, s, 'main set, 2024 to 2026, gain from Wikipedia', '+0.004', S_L, O_L, 'by_period/2024-2026/all/_diff/L2a_HMW14_minus_HM_rank/est',
    Ld('L2a_HMW14_minus_HM_rank', '2024-2026')[0])
add(CH, s, 'main set, 2024 to 2026, library plus Wikipedia, rank correlation', '0.360', S_L, O_L, 'by_period/2024-2026/all/HMW14/rank/est',
    Le('HMW14', period='2024-2026'))
add(CH, s, 'main set, 2024 to 2026, library model, rank correlation', '0.356', S_L, O_L, 'by_period/2024-2026/all/HM/rank/est',
    Le('HM', period='2024-2026'))
s = '5.4 paragraph "LibriVox and reading intent"'
add(CH, s, 'LibriVox, Wikipedia alone, rank correlation', '0.052', S_E, O_E, 'rows_with_views/corrected/rank|E1_W', eW)
add(CH, s, 'reading intent added to the alert list, points', '+0.0 points (−1.2 to +1.3)', S_K1, O_K1, 'S1, not_yet, HWNI minus HWN, p20',
    k1p('not_yet', 'HWNI', 'HWN'), f=pct)
add(CH, s, 'reading intent, real dates minus dates moved 12 months, points', '+0.2 (−0.7 to +1.1)', S_K1, O_K1,
    'S1, not_yet, HWNI minus placebo_I, p20', k1p('not_yet', 'HWNI', 'placebo_I'), f=pct)

# ================================================================ 5.5
s = '5.5 paragraph "Top 20"'
add(CH, s, 'main set, library plus Wikipedia, share of top 20 that rose', '83.4%', S_L, O_L, 'by_period/2019-2026/all/HMW14/top20/est',
    Le('HMW14', key='top20'), f=pct)
add(CH, s, 'main set, base rate of rising', '11.8%', S_L, O_L, 'by_period/2019-2026/all/_base_rose', base_rose, f=pct)
add(CH, s, 'main set, persistence rule, share of top 20 that rose', '79.3%', S_L, O_L, 'by_period/2019-2026/all/naive/top20/est',
    Le('naive', key='top20'), f=pct)
s = '5.5 paragraph "The 90% target"'
for fm, pr in (('print', '85.0%'), ('ebook', '92.3%'), ('audiobook', '93.1%')):
    add(CH, s, f'earlier all-books analysis, 2024 to 2026, {fm}, library plus Wikipedia, top-20 share that rose', pr, S_SC, O_SC,
        f'values_corrected/D.top20.HW.{fm}.2024_2026', SCc(f'D.top20.HW.{fm}.2024_2026'), f=pct)
s = '5.5 paragraph "Books chosen by their later loans"'
add(CH, s, 'well-known books, library plus Wikipedia, top-20 share that rose', '93.7%', S_SC, O_SC, 'values_corrected/A.top20.rose.HW',
    SCc('A.top20.rose.HW'), f=pct)
add(CH, s, 'earlier all-books analysis, all formats, library plus Wikipedia, top-20 share that rose', '88.0%', S_SC, O_SC,
    'values_corrected/D.top20.HW.all.2019_2026', SCc('D.top20.HW.all.2019_2026'), f=pct)
add(CH, s, 'main set, library without calendar month plus 18 features, top-20 share that rose', '83.5%', S_L, O_L,
    'by_period/2019-2026/all/HW18/top20/est', Le('HW18', key='top20'), f=pct)
s = '5.5 paragraph "Surges"'
for m, pr, lb in (('HM', '13.8', 'library model'), ('HMW14', '14.1', 'library plus Wikipedia'), ('naive', '11.8', 'persistence rule'),
                  ('W14', '2.2', 'Wikipedia alone')):
    add(CH, s, f'main set, {lb}, surge average precision as multiple of chance', pr, S_L, O_L,
        f'by_period/2019-2026/all/{m}/surge_ap_ratio', Le(m, key='surge_ap_ratio'))
T53 = {'HM': ('Library model', '1.25', '2.14', '69.2%'), 'HMW14': ('Library and Wikipedia', '1.26', '2.14', '69.2%'),
       'naive': ('Repeating last month', '2.00', '2.46', '68.3%')}
for m, (lb, med, mean, w2) in T53.items():
    add(CH, f'Table 5.3 / {lb} / Median error', f'main set, median absolute error in loans, {lb.lower()}', med, S_L, O_L,
        f'by_period/2019-2026/all/{m}/median_abs_err_loans', Le(m, key='median_abs_err_loans'))
    add(CH, f'Table 5.3 / {lb} / Mean error', f'main set, mean absolute error in loans, {lb.lower()}', mean, S_L, O_L,
        f'by_period/2019-2026/all/{m}/mae_loans/est', Le(m, key='mae_loans'))
    add(CH, f'Table 5.3 / {lb} / Within two loans', f'main set, share of forecasts within two loans, {lb.lower()}', w2, S_L, O_L,
        f'by_period/2019-2026/all/{m}/within2/est', Le(m, key='within2'), f=pct)

# ================================================================ 5.6
s = 'Table 5.4 / row 2'
add(CH, s, 'theme forecasting pipelines compared in all', '52', S_BM, O_BM2, 'Comparisons table, row A2, column pipelines', 52,
    note='stored line: ' + md(O_BM2, 'A2 | 36081 | 510 | 88 | 52 |') + ' (report also rewritten by 13_stage2_report.py)')
s1 = md(O_BM1, 'A. Print and ebook, horizon 1 (main) | 36611 | 88 | 2862.2388591800336 | 0.0 | 1.386793168220015 | 510 | 21')
add(CH, s, 'theme pipelines in the first stage, scored before the rest were fixed', 'first 21', S_BM, O_BM1,
    'Comparisons table, row A, column k (pipelines)', 21, note='stored line: ' + s1)
add(CH, s, 'theme pipelines fixed after the first stage was scored', '31 of them', S_BM, O_BM2, 'pipelines in stage 2 minus stage 1',
    52 - 21, kind='derived', note='52 - 21; the second-stage record is addenda_benchmark/2026-10-15_b (Appendix B)')

# ================================================================ Chapter 6
CH = '6'
add(CH, 'Table 6.1 / row 1', 'well-known books lent in the year before the October 2026 alert lists', '7,650',
    'main_study/wiki_led/12_live_alert_october.py', '../prereg/live_alert/ranking_all_2026-10.csv', 'data rows of the file (all books ranked)',
    sum(1 for _ in open(ROOT / 'prereg/live_alert/ranking_all_2026-10.csv')) - 1)
mb = json.load(open(ROOT / 'prereg/blind_l/forecasts_origin_2026-08_meta.json'))
add(CH, 'Table 6.1 / row 2', 'frozen September 2026 work-format rows, main set', '20,122', 'main_study/wiki_led/l_books_in_time/l05_freeze.py',
    '../prereg/blind_l/forecasts_origin_2026-08_meta.json', 'forecast_rows', mb['forecast_rows'])
mf = json.load(open(ROOT / 'prereg/final_test/forecasts_origin_2026-08_meta.json'))
add(CH, 'Table 6.1 / row 3', 'theme series with frozen forecasts', '714', 'main_study/benchmark/25_final_test_forecast.py',
    '../prereg/final_test/forecasts_origin_2026-08_meta.json', 'sum of rows_by_horizon_format_level for h1',
    sum(v for k, v in mf['rows_by_horizon_format_level'].items() if k.startswith('h1_')))
add(CH, 'Table 6.1 / row 3', 'frozen theme series-horizon rows', '2,142', 'main_study/benchmark/25_final_test_forecast.py',
    '../prereg/final_test/forecasts_origin_2026-08_meta.json', 'rows', mf['rows'])
st = json.load(open(DATA / 'collectors/seattle_release/status.json'))
add(CH, '6 paragraph "Status"', 'library checkout datasets on the city portal found not updated since early September', 'both',
    '(none: checked on the portal)', 'collectors/seattle_release/status.json', 'library_last_update, latest_month, last_check', 2,
    kind='notfound',
    stored_str=f"watcher holds one dataset: last update {st['library_last_update']}, latest month {st['latest_month']}",
    check=lambda r: (False, 'checked by hand on the city open data portal on 19 Nov 2026: Checkouts by Title (tmmm-ytt6) and Checkouts By '
                            'Title (Physical Items) (5src-czff), both last updated 2026-09-06; no stored file records the second dataset'))

# ================================================================ Chapter 7
CH = '7'
add(CH, '7.1 paragraph "Rises continue"', 'main set, persistence rule, share of top 20 that rose', '79%', S_L, O_L,
    'by_period/2019-2026/all/naive/top20/est', Le('naive', key='top20'), f=pct)
s = '7.1 paragraph on forecasting interest'
fl = C(O_S4).set_index('level')
add(CH, s, "theme interest, boosted trees' error cut against the last four weeks (percent)", '9.6% (7.6 to 11.5)', S_S4, O_S4,
    'row all: skill, ci_lo, ci_hi', [fl.loc['all', 'skill'], fl.loc['all', 'ci_lo'], fl.loc['all', 'ci_hi']], f=pct)
add(CH, s, 'narrow and middle themes forecast', '328', S_S4, O_S4MD, 'header line', 328,
    note=md(O_S4MD, '328 categories (narrow and middle levels)'))
add(CH, s, 'AUC for interest reaching 1.5 times normal, both forecasts', 'about 0.80', S_S4, O_S4, 'row all: auc_naive, auc_catboost',
    [fl.loc['all', 'auc_naive'], fl.loc['all', 'auc_catboost']], kind='derived',
    check=lambda r: (all(abs(x - 0.80) < 0.01 for x in r), f'{r[0]:.3f} and {r[1]:.3f}'))
add(CH, s, 'base rate of interest reaching 1.5 times normal', '2.1%', S_S4, O_S4, 'row all: base_rate', fl.loc['all', 'base_rate'], f=pct)
add(CH, s, 'largest error reduction from interest for the pretrained forecaster', 'at most 0.6%', S_BM, O_BMP,
    'min mae_ratio, base chronos2; 1 minus ratio', chron.mae_ratio.min(), f=less1pct)
add(CH, s, 'largest error increase from interest for change-trained models', 'up to 1.5%', S_BM, O_BMP,
    f'max mae_ratio among {CHG_KEY}, minus 1', chg.mae_ratio.max(), f=ratio_pct)
hb = C(O_HBA)
hbB = hb[hb.split.str.startswith('B walk-forward') & (hb.subset == 'all weeks')].set_index('model')
add(CH, s, 'LibriVox weekly, attention alone, AUC', '0.59', S_HB, O_HBA, 'B walk-forward, attention only, all weeks',
    hbB.loc['attention only', 'auc'])
add(CH, s, 'LibriVox weekly, own recent listening, AUC', '0.77', S_HB, O_HBA, 'B walk-forward, own listening only, all weeks',
    hbB.loc['own listening only', 'auc'])
hg = C(O_HBG)
hgr = hg[(hg.split == 'B walk-forward') & (hg.subset == 'all weeks') & hg.contrast.str.startswith('both minus own listening')].iloc[0]
add(CH, s, 'LibriVox weekly, AUC gain from attention over own listening', '+0.003 (0.001 to 0.005)', S_HB, O_HBG,
    'B walk-forward, all weeks, both minus own listening only', [hgr['diff'], hgr['lo'], hgr['hi']])
s = '7.2 paragraph "New books"'
add(CH, s, 'new books, author with no earlier Seattle book, library model', '0.045', S_SC, O_SC, 'values_original/B.none.L', SCo('B.none.L'))
add(CH, s, 'same books, Wikipedia alone', '0.090', S_SC, O_SC, 'values_original/B.none.W', SCo('B.none.W'))
add(CH, s, 'same books, gain from Wikipedia over the main library model', '+0.056', S_TW, O_TW, tw_key('none', 'L'), tw('none', 'L')[0])
add(CH, s, 'same books, gain over the two library models with first-loan catalogue facts', 'about +0.016', S_TW, O_TW,
    tw_key('none', 'Lq') + '; ' + tw_key('none', 'L0'), [tw('none', 'Lq')[0], tw('none', 'L0')[0]], kind='derived',
    check=lambda r: (close(sum(r) / 2, 0.016, 3), f'Lq {r[0]:.4f}, L0 {r[1]:.4f}, mean {sum(r) / 2:.4f}'))
wa, nr = jget(O_LN, '_meta/with_author_article'), jget(O_LN, '_meta/recordings')
add(CH, s, 'share of new LibriVox recordings by an author with a matched article', 'four recordings in five', S_LN, O_LN,
    '_meta/with_author_article / _meta/recordings', wa / nr, kind='derived', check=lambda r: (abs(r[0] - 0.8) < 0.025, f'{r[0]:.3f}'))
add(CH, s, 'new LibriVox recordings with a matched author article', '3,024', S_LN, O_LN, '_meta/with_author_article', wa)
add(CH, s, 'new LibriVox recordings released from 2017', '3,804', S_LN, O_LN, '_meta/recordings', nr)
s = '7.3 paragraph "Two kinds of evidence"'
add(CH, s, 'hand-reviewed concept pages, extra theme borrowing after lasting rises', 'about 10%', S_S3, O_S3,
    'narrow and middle sustained, exp(x)-1', [nar[0], mid[0]], kind='derived', check=ten)
add(CH, s, 'same effect stated as loans', 'about one extra loan in ten', S_S3, O_S3, 'narrow and middle sustained, exp(x)-1',
    [nar[0], mid[0]], kind='derived', check=ten)
s = '7.3 paragraph "Why AI sorting at scale did worse"'
add(CH, s, 'AI-sorted effect as a share of the hand-reviewed effect', 'about a fifth', S_TF, O_TF,
    'exp(G2 both|synthetic_control effect)-1 divided by exp(hand-reviewed narrow and middle effects)-1',
    [pctlog(gs['effect']) / pctlog(nar[0]), pctlog(gs['effect']) / pctlog(mid[0])], kind='derived',
    check=lambda r: (all(0.15 <= x <= 0.25 for x in r), f'{r[0]:.2f} (narrow), {r[1]:.2f} (middle); hand-reviewed values from {O_S3}'))
add(CH, s, 'AI sorting against the judge, precision', '0.85', S_TF, O_TF, 'G1/scores[0]/precision', g1['precision'])
add(CH, s, 'share of sorted pages about people', '46%', S_TF, O_TF, 'sorting/pages/kinds/person / sum', kinds['person'] / tot, f=pct,
    kind='derived')
add(CH, '7.3 paragraph "Linked pages"', 'size of the date-placebo comparisons for linked pages and events, points', 'less than one point',
    S_J2, O_J2P, 'S1 not_yet p20: HWENL-HWEN, HWE-HW, HWENL-placebo',
    [j2p('S1', 'not_yet', 'HWENL', 'HWEN')[0], j2p('S1', 'not_yet', 'HWE', 'HW')[0], j2p('S1', 'not_yet', 'HWENL', 'placebo')[0]],
    kind='derived', check=lambda r: (all(abs(100 * x) < 1 for x in r), ', '.join(f'{100 * x:+.2f}' for x in r) + ' points'))
s = '7.4 Limitations'
add(CH, s + ' "LibriVox"', 'share of LibriVox book-months with Wikipedia views', 'a fifth', S_E, O_E, 'rows_with_views/corrected/share_of_main',
    EV['share_of_main'], kind='derived', check=lambda r: (abs(r[0] - 0.2) < 0.025, f'{r[0]:.3f}'))
add(CH, s + ' "Links"', 'works of one author matched by name to a namesake', '66', S_TB, O_TB, 'list of matched names with no writer_type', 66,
    note=md(O_TB, 'James Dean -> James Dean (66 works'))
add(CH, s + ' "Automated traffic"', 'well-known books, Wikipedia alone, without the bot months', '0.134', S_ROB, O_ROB,
    'R4/without_bot_months/change_rank/Wlgbm_D/mean', jget(O_ROB, 'R4/without_bot_months/change_rank/Wlgbm_D/mean'),
    note='the check leaves out origins 2025-04 to 2025-06')
add(CH, s + ' "Automated traffic"', 'well-known books, Wikipedia alone, all months', '0.133', S_A, O_A, 'change_rank/Wlgbm_D/mean',
    Ar('Wlgbm_D')[0])
i0 = next(i for i, l in enumerate(LINES) if l.startswith('| ') and 'Public before its results?' in l)
recs = []
for l in LINES[i0 + 2:]:
    if not l.startswith('|'):
        break
    cells = [c.strip() for c in l.strip('|').split('|')]
    recs.append((cells[2], cells[-1]))
n_no = sum(1 for f_, p_ in recs if p_.startswith('No'))
n_no_early = sum(1 for f_, p_ in recs if p_.startswith('No') and re.match(r'(Made |Frozen )?1[345] Oct', f_))
add(CH, s + ' "Not fully blind"', 'dated settings records public only after their results', 'Twelve of the 27',
    '(none: count of Table B.1)', THESIS_REL, 'Appendix B, Table B.1: rows whose last column starts with "No"', [n_no, len(recs)],
    kind='derived', stored_str=f'{n_no} of {len(recs)}',
    check=lambda r: (r == [12, 27], 'counted from the table; its last column was checked against the public repository merge times in the '
                                    'fact check of 6 November'))
add(CH, s + ' "Not fully blind"', 'of those, records fixed on 13 to 15 October', 'seven', '(none: count of Table B.1)', THESIS_REL,
    'same rows, "Fixed" column 13 to 15 Oct', n_no_early, kind='derived', check=lambda r: (r[0] == 7, f'{r[0]}'))
add(CH, s + ' "Noise in lists"', 'change in a top-20 share between refits with other seeds or random columns, points',
    'up to about two points', S_V2, O_V2, 'seed check and random-column check', [1.5, 2.3],
    stored_str='-1.3 to +1.5 (seeds); -1.5 to +2.3 (random columns)', kind='derived',
    check=lambda r: (all(1.0 <= x <= 2.5 for x in r), 'largest moves 1.5 points (other seeds) and 2.3 points (random columns); '
                     + md(O_V2, 'moves it between -1.3 and +1.5 points from v0') + ' / '
                     + md(O_V2, 'moves the ranker by -1.5 to +2.3 points over three seeds')))

# ================================================================ Chapter 8
CH = '8'
add(CH, '8 "Added"', 'main set, gain from Wikipedia', '0.005', S_L, O_L, 'decisions/L2a/est', l2a[0])
add(CH, '8 "Added"', 'new books, gain from Wikipedia', '0.024', S_B, O_B, 'all/LW_minus_L/mean', pb['mean'])
add(CH, '8 "Added"', 'new books, gain over library models with first-loan catalogue facts', 'about 0.011', S_TW, O_TW,
    tw_key('all', 'Lq') + '; ' + tw_key('all', 'L0'), [tw('all', 'Lq')[0], tw('all', 'L0')[0]], kind='derived',
    check=lambda r: (all(abs(x - 0.011) < 0.0015 for x in r), f'Lq {r[0]:.4f}, L0 {r[1]:.4f}'))

# ================================================================ checks and output
if MISSING:
    raise SystemExit('printed values not found in the indexed chapters of the draft (update the rows):\n  ' + '\n  '.join(MISSING))
for i, r in enumerate(ROWS, 1):
    r['id'] = f'N{i:03d}'
cols = ['id', 'chapter', 'location', 'label', 'printed', 'script', 'output', 'key', 'stored', 'match', 'note']
with open(OUT_CSV, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    for r in ROWS:
        w.writerow({c: r[c] for c in cols})

counts = {m: sum(r['match'] == m for r in ROWS) for m in ('yes', 'derived', 'no', 'not found')}
bad = [r for r in ROWS if r['match'] in ('no', 'not found')]
L = ['# Index of the numbers in the thesis results chapters', '',
     f'Khant Phyo Wai, student ID 01323050. Written by `code/main_study/wiki_led/99c_thesis_numbers_index.py` for the draft '
     f'`{THESIS.name}`; it reads stored result files only and reruns no analysis.', '',
     '## What it covers', '',
     '`thesis_numbers_index.csv` lists every number in the Abstract and Chapters 5 to 8 of that draft: the running text, the tables '
     'and the figure captions of those chapters. Chapters 1 to 4, the appendices and the references are not covered. Dates, years used '
     'as labels, section, table and figure numbers, citation years and the settings themselves (list length, targets, interval level, '
     'window lengths, number of draws) are left out. An estimate printed with its interval is one row, and all its numbers must match.', '',
     'Each row gives the script that wrote the value (path under `code/`), the stored file (path under `data/`; the frozen-forecast '
     'files sit in `prereg/`), the key inside it, the stored value at full precision, and the result of the comparison:', '',
     '- **yes**: the stored value equals the printed one after rounding to the printed decimals (a share stored as a fraction and '
     'printed as percent counts as yes).',
     '- **derived**: the printed number is computed from stored values (a difference, a ratio, a count, a log effect or error ratio '
     'turned into percent, or a word such as "about a fifth"); the formula is in `key` or `note`, and the result agrees with the print.',
     '- **no**: the stored value, rounded to the printed decimals, differs from the print.',
     '- **not found**: no stored output gives the number.', '',
     '## Counts', '',
     f'{len(ROWS)} numbers: {counts["yes"]} yes, {counts["derived"]} derived, {counts["no"]} no, {counts["not found"]} not found.', '',
     '| Chapter | yes | derived | no | not found |', '| --- | ---: | ---: | ---: | ---: |']
for ch in ['Abstract', '5', '6', '7', '8']:
    rr = [r for r in ROWS if r['chapter'] == ch]
    if rr:
        L.append(f'| {ch} | ' + ' | '.join(str(sum(r['match'] == m for r in rr)) for m in ('yes', 'derived', 'no', 'not found')) + ' |')
L += ['', '## Rows that do not match or have no source', '']
if bad:
    L += ['| id | Location | Printed | Stored | Note |', '| --- | --- | --- | --- | --- |']
    L += [f'| {r["id"]} | {r["location"]} | {r["printed"]} | {r["stored"]} | {r["note"]} |' for r in bad]
else:
    L.append('None.')
L += ['', '## Notes', '',
      '- Rows whose script column starts with "(none" have no script behind them: two counts made from Table B.1 of the thesis, and '
      'the check of the library datasets on the city portal.',
      '- A few values come from Markdown reports rather than JSON or CSV files (events, release dates, linked pages, some counts); the '
      '`note` column quotes the line used, and the script stops if that line is no longer in the report.',
      '- The well-known-books results use the corrected files of 20 October (`*_c.json`, `values_corrected` in the summary checks); the '
      'new-book split by earlier Seattle books uses `values_original` or `two_way_intervals.json`, as Test B has no corrected run.',
      '- Intervals for the new-book groups are those of `98_two_way_intervals.py`: (i) authors only, (ii) first-loan years only, '
      '(iii) both; the `key` column names the one printed.', '']
OUT_MD.write_text('\n'.join(L))

# numbers of the indexed chapters that no row holds (most are settings); printed for review only
held = {re.sub(r'^\+', '', t.replace('−', '-').replace(',', '')) for r in ROWS for t in NUM.findall(r['printed'])}
print(f'{len(ROWS)} rows: {counts}')
for r in bad:
    print(' ', r['id'], r['match'], '|', r['location'], '|', r['printed'], '|', r['stored'])
print('numbers in the indexed chapters held by no row (check that each is a setting, a date or a reference):')
for a, b in SPANS:
    for i in range(a, b):
        l = LINES[i]
        if l.startswith('![') or l.startswith('#'):
            continue
        ref = r'(?:[A-F]\.)?\d+(?:\.\d+)?'
        l2 = re.sub(rf'(Tables?|Figures?|Sections?|Appendix|Chapter) {ref}(?: (?:and|to) {ref})?', '', l)
        l2 = re.sub(r'\((?:\d\.\d(?:, | to )?)+\)', '', l2)                                  # section lists such as (5.1, 5.2)
        l2 = re.sub(r'(?<=[A-Za-z])-\d+', '', l2)                                                  # names such as Chronos-2
        l2 = re.sub(r'\b\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December)( \d{4})?', '', l2)
        l2 = re.sub(r'(January|February|March|April|May|June|July|August|September|October|November|December) \d{4}', '', l2)
        l2 = re.sub(r'\([^()]*\d{4}\)|[A-Z][a-z]+ et al\.,? \(?\d{4}\)?', '', l2)
        miss = [m for m in NUM.findall(l2) if not re.fullmatch(r'-?(19|20)\d\d,?', m.replace('−', '-'))
                and re.sub(r'^\+', '', m.replace('−', '-').replace(',', '')) not in held]
        if miss:
            print(f'  line {i + 1}: {miss}')
print('wrote', OUT_CSV.relative_to(ROOT), 'and', OUT_MD.relative_to(ROOT))
