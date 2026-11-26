# o05. Addendum o, step 6 (text): the plain-language report from o04's outputs.  No result is computed here.
# Inputs: data/reports/transformer_check_single_books.json, transformer_check_segments.csv; data/db/wiki_led/o_transformer_check/controls_check.json;
#   prereg/blind_o/forecasts_origin_2026-08_meta.json (if frozen).
# Output: data/reports/transformer_check_single_books.md
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/o_transformer_check/o05_report.py
import json, math, time, pathlib, sys
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REP = DATA / 'reports'
OUT = DATA / 'db' / 'wiki_led' / 'o_transformer_check'
R = json.loads((REP / 'transformer_check_single_books.json').read_text())
SEG = pd.read_csv(REP / 'transformer_check_segments.csv') if (REP / 'transformer_check_segments.csv').exists() else None
CHK = json.loads((OUT / 'controls_check.json').read_text())
META_F = ROOT / 'prereg' / 'blind_o' / 'forecasts_origin_2026-08_meta.json'
META = json.loads(META_F.read_text()) if META_F.exists() else None
W, O1, DEC = R['whole'], R['O1_window'], R['decisions']
WP, WL = W['2019-2026']['pairs'], W['2019-2026']['levels']

NAME = {'HM': 'Library model (loan history and calendar month)', 'HMW14': 'Library + own and author pages',
        'HMW14Z': 'Library + own pages + the two Transformer forecasts', 'HMW14C': 'Library + own pages + the same 60 months in plain form',
        'HMW14CZ': 'Library + own pages + plain 60 months + the two Transformer forecasts',
        'HMW14Z1': 'Library + own pages + the Transformer forecast without pages', 'HMW14Z2': 'Library + own pages + the Transformer forecast with pages',
        'HMW14Zlag': 'Library + own pages + the two Transformer forecasts made 12 months earlier (placebo)'}
PAIRN = {'O2_CZ_minus_C': 'Transformer forecasts added on top of the plain 60 months', 'Z_gain': 'Transformer forecasts added to library + own pages',
         'C_gain': 'Plain 60 months added to library + own pages', 'CZ_gain': 'Plain 60 months and Transformer forecasts together',
         'Z1_gain': 'Only the forecast without pages', 'Z2_gain': 'Only the forecast with pages',
         'Z_minus_moved_dates': 'Transformer forecasts against the same forecasts made 12 months earlier',
         'Z_minus_C': 'Transformer forecasts against the plain 60 months (each added to library + own pages)'}


def bad(d):
    return d is None or d.get('est') is None or (isinstance(d['est'], float) and math.isnan(d['est']))


def g4(d):
    return 'no rows' if bad(d) else f'{d["est"]:+.4f} ({d["lo"]:+.4f} to {d["hi"]:+.4f})'


def lv(d):
    return 'no rows' if bad(d) else f'{d["est"]:.3f} ({d["lo"]:.3f} to {d["hi"]:.3f})'


def seeds_txt(d):
    return '' if bad(d) or 'n_above0' not in d else f'± {d["sd"]:.4f}; {d["min"]:+.4f} to {d["max"]:+.4f}; {d["n_above0"]} of 5 above 0'


def verdict(X):
    d = DEC[X]
    return 'passed' if d['passed'] else 'did not pass'


o1, o2 = O1['pairs']['Z_gain'], WP['O2_CZ_minus_C']
L = ['# A fair check of the Transformer lead for single books', '',
     f'Made by `code/main_study/wiki_led/o_transformer_check/o04_score.py` and `o05_report.py` on {time.strftime("%Y-%m-%d %H:%M %z")}. Settings fixed '
     'in advance in `prereg/addenda_wiki_led/2026-11-26_o_transformer_inputs_check.json` (made public on GitHub, pull request 37, at 05:11 UTC on '
     '26 November 2026, before any step ran). Choices made later are logged with times in `prereg/DEVIATIONS.md`, section "Addendum o".', '',
     '## The question', '',
     'In the previous report, the boosted-tree model with the library history and the own and author pages got better by +0.0091 when it was also '
     'given the forecasts of a pretrained Transformer (Chronos-2) as two extra inputs, the biggest gain found so far. Nothing was fixed in advance '
     'for it, and two doubts remained:', '',
     '1. **Did the Transformer remember the test years?** It was trained before its release on 20 October 2025 on public time series that may '
     'cover the same years. So the gain is checked again on the 10 months after its release (November 2025 to August 2026), which it cannot have seen.',
     '2. **Is it the Transformer, or just a longer look at the loans?** The Transformer reads up to 60 months of each book\'s loans; the trees\' '
     'own history inputs reach back about a year. So the trees are also given the same 60 months in plain form (the last 24 months one by one, '
     'averages over 24, 36 and 60 months, trends over 12 and 36 months, spread, months with no loans, and three textbook forecasts: '
     'exponential smoothing, same month last year, and a 12-month straight line). The Transformer\'s forecasts must still add something on top.', '',
     'Both must pass for the lead to count as confirmed on past data. A third, blind check uses September 2026, a month nobody has seen yet.', '',
     '## How to read the numbers', '',
     '- **Score**: each month and format, the books are ranked by predicted change in loans and compared with the actual change (rank correlation; '
     '0 is chance, 1 is perfect), averaged over the months. Models only ever learn from earlier years.',
     '- **Gain**: the score of one model minus another\'s on the same rows. 0.001 is small; the own and author pages together add about 0.005.',
     '- **Five seeds**: every boosted-tree model was fitted five times; a value is the mean, "±" their spread. The Transformer itself has no random part.',
     '- **95% interval** (in brackets): from 2,000 redraws of blocks of three consecutive months. For the 10 months after the release, the blocks '
     'are drawn within those 10 months only.', '',
     '## In short', '',
     f'- **Months the Transformer cannot have seen** ({verdict("O1")}): on November 2025 to August 2026, its forecasts added {g4(o1)} '
     f'({seeds_txt(o1)}), against {g4(W["2019-2026"]["pairs"]["Z_gain"])} over all months.',
     f'- **More than a longer look at the loans** ({verdict("O2")}): on top of the plain 60 months, its forecasts added {g4(o2)} ({seeds_txt(o2)}). '
     f'The plain 60 months alone added {g4(WP["C_gain"])} (no rule); both together {g4(WP["CZ_gain"])}.',
     ('- **Verdict**: the lead is **confirmed on past data**: both checks passed by the rule fixed in advance.' if DEC['confirmed_on_past_data'] else
      '- **Verdict**: the lead is **not confirmed** on past data: ' + ' and '.join(x for x, ok in (('the check on unseen months', not DEC['O1']['passed']),
                                                                                       ('the check against the plain 60 months', not DEC['O2']['passed'])) if ok) + ' did not pass.'),
     f'- **Transformer forecasts or plain 60 months** (no rule), each added alone to library + own pages: Transformer minus plain {g4(WP["Z_minus_C"])}; '
     f'below 0 means the plain 60 months did better.',
     f'- **Which forecast carries it** (no rule): the forecast without pages alone added {g4(WP["Z1_gain"])}, the one with pages alone {g4(WP["Z2_gain"])}.',
     f'- **Placebo** (no rule): the real forecasts against the same forecasts made 12 months earlier: {g4(WP["Z_minus_moved_dates"])}.',
     f'- **2024 to 2026**: Transformer forecasts {g4(W["2024-2026"]["pairs"]["Z_gain"])}; on top of the plain 60 months {g4(W["2024-2026"]["pairs"]["O2_CZ_minus_C"])}.']
T = W['top']
L.append(f'- **Monthly top-20 lists** (no rule): share of the 20 books with the highest predicted change whose loans rose by half or more: '
         f'{T["top20"]["HMW14"]["est"]:.3f} for library + own pages, {T["top20"]["HMW14Z"]["est"]:.3f} with the Transformer forecasts, '
         f'{T["top20"]["HMW14CZ"]["est"]:.3f} with the plain 60 months and the forecasts; early-warning lists '
         f'{T["early_top20"]["HMW14"]["est"]:.3f}, {T["early_top20"]["HMW14Z"]["est"]:.3f} and {T["early_top20"]["HMW14CZ"]["est"]:.3f}.')
if 'segments' in R:
    s = R['segments']
    L.append(f'- **By kind of book** (no rule): the Transformer forecasts\' gain was found in {s["Z"]["found"]} of {s["Z"]["groups"]} groups and '
             f'differed from the other books in {s["Z"]["differs"]}; on top of the plain 60 months it was found in {s["CZ_vs_C"]["found"]} of '
             f'{s["CZ_vs_C"]["groups"]} and differed in {s["CZ_vs_C"]["differs"]}, after correcting for the number of groups.')
L.append('- **Blind month**: forecasts for September 2026 are frozen and public' + (f' ({META["forecast_rows"]:,} rows, made {META["made_utc"]})' if META else '')
         + '; they are scored once, when the library releases September and it is downloaded.' if META else
         '- **Blind month**: the September 2026 forecasts are not frozen yet.')
L += ['', '## Rules fixed in advance', '',
      'Holm\'s correction over the two checks at one-sided 0.05; a check passes if Holm rejects it, its estimate is above 0 and its 95% interval is above 0.', '',
      '| Check | Gain (95% interval) | One-sided p | Passes Holm | Passed |', '| --- | --- | --- | --- | --- |',
      f'| Transformer forecasts added, months after its release (Nov 2025 to Aug 2026) | {g4(o1)} | {DEC["O1"]["p_one"]:.4f} | {"yes" if DEC["O1"]["holm"] else "no"} | **{"yes" if DEC["O1"]["passed"] else "no"}** |',
      f'| Transformer forecasts added on top of the plain 60 months, 2019 to 2026 | {g4(o2)} | {DEC["O2"]["p_one"]:.4f} | {"yes" if DEC["O2"]["holm"] else "no"} | **{"yes" if DEC["O2"]["passed"] else "no"}** |', '',
      '## All months, February 2019 to August 2026', '',
      '| Model | Score (95% interval) | ± across seeds | Score 2024 to 2026 | Print | Ebook | Audiobook |', '| --- | --- | --- | --- | --- | --- | --- |']
BFL = W['by_format_levels']
for m in ('HM', 'HMW14', 'HMW14Z', 'HMW14C', 'HMW14CZ', 'HMW14Z1', 'HMW14Z2', 'HMW14Zlag'):
    d = WL[m]
    L.append(f'| {NAME[m]} | {lv(d)} | {d["sd"]:.4f} | {lv(W["2024-2026"]["levels"][m])} | ' + ' | '.join(f'{BFL[f][m]["est"]:.3f}' for f in ('print', 'ebook', 'audiobook')) + ' |')
L += ['', '| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |', '| --- | --- | --- | --- | --- | --- | --- |']
BF = W['by_format']
for k in ('Z_gain', 'C_gain', 'O2_CZ_minus_C', 'CZ_gain', 'Z_minus_C', 'Z1_gain', 'Z2_gain', 'Z_minus_moved_dates'):
    L.append(f'| {PAIRN[k]} | {g4(WP[k])} | {seeds_txt(WP[k])} | {g4(W["2024-2026"]["pairs"][k])} | ' + ' | '.join(g4(BF[f][k]) for f in ('print', 'ebook', 'audiobook')) + ' |')
L += ['', 'Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the early-warning '
      'list keeps only books that had not already risen):', '',
      '| List | Library + own pages | + Transformer forecasts | + plain 60 months | + plain 60 months + forecasts |', '| --- | --- | --- | --- | --- |']
for lab, k in (('All books', 'top20'), ('Early warning', 'early_top20')):
    L.append(f'| {lab} | ' + ' | '.join(lv(T[k][m]) for m in ('HMW14', 'HMW14Z', 'HMW14C', 'HMW14CZ')) + ' |')
L += ['', '| List comparison | All books | Early warning |', '| --- | --- | --- |']
for k in ('Z_gain', 'C_gain', 'O2_CZ_minus_C'):
    L.append(f'| {PAIRN[k]} | {g4(T["top20"][k])} | {g4(T["early_top20"][k])} |')
L += ['', f'## The {len(O1["months"])} months after the Transformer\'s release ({O1["months"][0]} to {O1["months"][-1]})', '',
      f'{O1["rows"]:,} scored rows. Intervals from redraws of 3-month blocks within these months only.', '',
      '| Model | Score (95% interval) |', '| --- | --- |']
for m in ('HM', 'HMW14', 'HMW14Z', 'HMW14C', 'HMW14CZ'):
    L.append(f'| {NAME[m]} | {lv(O1["levels"][m])} |')
L += ['', '| Comparison | Gain (95% interval) | Five seeds | Print | Ebook | Audiobook |', '| --- | --- | --- | --- | --- | --- |']
for k in ('Z_gain', 'C_gain', 'O2_CZ_minus_C', 'Z1_gain', 'Z2_gain', 'Z_minus_moved_dates'):
    bf = O1['by_format']
    fm = ' | '.join(g4(bf[f][k]) if k in bf[f] else '' for f in ('print', 'ebook', 'audiobook'))
    L.append(f'| {PAIRN[k]} | {g4(O1["pairs"][k])} | {seeds_txt(O1["pairs"][k])} | {fm} |')

if SEG is not None:
    SH = {'Z': 'Transformer forecasts added', 'CZ_vs_C': 'Added on top of the plain 60 months'}
    L += ['', '## Results by kind of book', '',
          'Every group of the 14 families fixed in advance is listed, whatever it shows. The models were fitted on all books; a group only restricts which '
          'books are ranked against each other. "Score" is the library + own pages model\'s score in that group. Marks: **found** = gain above zero after '
          'the Benjamini-Hochberg correction over all groups of that comparison; **differs** = the gain differs from the gain in the other books of the '
          'same family after the same correction; *small* = fewer than 36 scored months or 1,000 rows, not judged.', '']

    def cell(r):
        m = ['*small*'] if r.too_small else (['**found**'] if r.gain_found else []) + (['**differs**'] if r.differs else [])
        return f'{r.gain:+.4f} ({r.gain_lo:+.4f} to {r.gain_hi:+.4f})' + (' ' + ' '.join(m) if m else '')
    ORD = {'low': 0, 'middle': 1, 'high': 2, 'under 1 year': 0, '1 to 5 years': 1, '5 years or more': 2}
    for fam in SEG.family.drop_duplicates():
        sf = SEG[SEG.family == fam]
        L += [f'### {fam}', '', '| Group | Rows | Months | Score | ' + ' | '.join(SH.values()) + ' |', '| --- | --- | --- | --- | --- | --- |']
        for g in sorted(sf.group.drop_duplicates(), key=lambda x: (ORD.get(x, 9), x)):
            rr = {c: sf[(sf.group == g) & (sf.comparison == c)] for c in SH}
            r0 = rr['Z'].iloc[0]
            L.append(f'| {g} | {r0.rows:,} | {r0.months} | {r0.base_rank:.3f} | ' + ' | '.join(cell(rr[c].iloc[0]) for c in SH) + ' |')
        L += ['']

L += ['## Data and checks', '',
      f'- The plain 60 months come from the same monthly loan series the Transformer reads. Checks: the last month equals the stored history input '
      f'on every row ({CHK["c_y0_equals_h_lt"]:.0%}); the same-month-last-year forecast equals the stored one wherever both exist; the smoothing '
      'forecast matched an independent calculation on sampled books.',
      '- A refit of the library + own pages model reproduces the stored predictions exactly, and the previous report\'s +0.0091 is reproduced.',
      f'- The forecasts made 12 months earlier are missing for {CHK["Zlag_missing_share"]:.0%} of rows (no row a year before), so that placebo '
      'mostly speaks for books with a longer record.']
if META:
    L.append(f'- Blind month: {META["forecast_rows"]:,} rows at origin August 2026, frozen {META["made_utc"]}; file `prereg/blind_o/forecasts_origin_2026-08.csv`, '
             f'SHA-256 {META["csv_sha256"][:16]}... in `prereg/README.md`. Check: the library + own pages forecast of the first seed equals the one frozen '
             'for the earlier blind test.')
L += ['', '## Limits', '',
      '- The unseen-months check has 10 months only. Its interval redraws blocks within those 10 months, so it shows the month-to-month '
      'variation inside them only, and it can look narrower than the interval over all months.',
      '- The 10 months were not blind: they sit inside the 2024 to 2026 window, whose gain was seen before the rules were fixed. That check '
      'answers the worry about pretraining, not whether the gain holds on new data; the blind month does that.',
      '- The plain 60 months are one fair way to give the trees the same loans, not every possible way; a model built to read long histories might do better.',
      '- The Transformer was used as released, without tuning or training on library data.',
      '- The blind month is one month: it adds to the backtest, it does not replace it.',
      '- A group result describes the books of that group in this sample. It is not the effect of being that kind of book.', '']
(REP / 'transformer_check_single_books.md').write_text('\n'.join(L) + '\n')
print('written', REP / 'transformer_check_single_books.md')
