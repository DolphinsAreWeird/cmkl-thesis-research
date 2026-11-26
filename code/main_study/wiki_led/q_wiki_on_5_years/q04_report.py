# q04. Addendum q, step 4 (text): the plain-language report from q03's outputs.  No result is computed here.
# Inputs: data/reports/wiki_on_5_years.json, wiki_on_5_years_segments.csv; prereg/blind_q/forecasts_origin_2026-08_meta.json (if frozen).
# Output: data/reports/wiki_on_5_years.md
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/q_wiki_on_5_years/q04_report.py
import json, math, time, pathlib, sys
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REP = DATA / 'reports'
R = json.loads((REP / 'wiki_on_5_years.json').read_text())
SEG = pd.read_csv(REP / 'wiki_on_5_years_segments.csv') if (REP / 'wiki_on_5_years_segments.csv').exists() else None
META_F = ROOT / 'prereg' / 'blind_q' / 'forecasts_origin_2026-08_meta.json'
META = json.loads(META_F.read_text()) if META_F.exists() else None
DEC = R['decisions']
A, P = R['all_books'], R['books_with_a_page']
FM = ('print', 'ebook', 'audiobook')

NAME = {'HM': 'Library, about 1 year of loans (no Wikipedia)', 'HMW14': 'Library, about 1 year of loans + own and author pages',
        'HM60': 'Library + 5 years of loans (no Wikipedia)', 'HMW14C': 'Library + 5 years of loans + own and author pages'}
PAIRN = {'Q_wiki_on_5y': 'Wikipedia pages added, with 5 years of loans', 'W_wiki_on_1y': 'Wikipedia pages added, with about 1 year of loans',
         'C_without_wiki': '5 years of loans added, without Wikipedia', 'C_with_wiki': '5 years of loans added, with Wikipedia'}
SAMPN = {'all_books': 'All books', 'books_with_a_page': 'Books with a page (own or author)', 'own_book_page': 'Books with their own article',
         'author_page_only': 'Books with an author article only', 'no_page': 'Books with no page'}


def bad(d):
    return d is None or d.get('est') is None or (isinstance(d['est'], float) and math.isnan(d['est']))


def g4(d):
    return 'no rows' if bad(d) else f'{d["est"]:+.4f} ({d["lo"]:+.4f} to {d["hi"]:+.4f})'


def lv(d):
    return 'no rows' if bad(d) else f'{d["est"]:.3f} ({d["lo"]:.3f} to {d["hi"]:.3f})'


def seeds_txt(d):
    return '' if bad(d) or 'n_above0' not in d else f'± {d["sd"]:.4f}; {d["min"]:+.4f} to {d["max"]:+.4f}; {d["n_above0"]} of 5 above 0'


def pct(d):
    return f'{d["est"]:.0%} ({d["lo"]:.0%} to {d["hi"]:.0%})'


def verdict(X):
    return 'passed' if DEC[X]['passed'] else 'did not pass'


def says(X, who):
    return (f'the Wikipedia pages still help {who} once the model has 5 years of loans' if DEC[X]['passed'] else
            f'the Wikipedia pages\' help for {who} is not clear once the model has 5 years of loans')


qa, qp = A['2019-2026']['pairs'], P['2019-2026']['pairs']
L = ['# Do the Wikipedia pages still help once the model has 5 years of loans?', '',
     f'Made by `code/main_study/wiki_led/q_wiki_on_5_years/q03_score.py` and `q04_report.py` on {time.strftime("%Y-%m-%d %H:%M %z")}. Settings fixed '
     'in advance in `prereg/addenda_wiki_led/2026-11-26_q_wikipedia_on_top_of_5_years.json` (made public on GitHub, pull request 39, at 08:16 UTC on '
     '26 November 2026, before any step ran). Choices made later are logged with times in `prereg/DEVIATIONS.md`, section "Addendum q".', '',
     '## The question', '',
     'The previous check found that giving the boosted-tree model 5 years of each book\'s loans (in plain form: monthly values, averages, trends and '
     'simple forecasts) raised the score more than anything else so far. Before making that the main model, one question matters for the thesis: the '
     'Wikipedia gain was measured on top of a loan history that reaches back only about a year. Some of what the pages carry, such as which books '
     'stay read for years, may also be in older loans. So: **with 5 years of loans in the model, do the book\'s and author\'s Wikipedia pages still '
     'add to the score?** This is checked on all books and on books that have a page (their own or their author\'s), the sample of the thesis.', '',
     '## How to read the numbers', '',
     '- **Score**: each month and format, the books are ranked by predicted change in loans and compared with the actual change (rank correlation; '
     '0 is chance, 1 is perfect), averaged over the months, February 2019 to August 2026. Models only ever learn from earlier years.',
     '- **Gain**: the score of one model minus another\'s on the same rows.',
     '- **Five seeds**: every model was fitted five times; a value is the mean, "±" their spread.',
     '- **95% interval** (in brackets): from 2,000 redraws of blocks of three consecutive months.', '',
     '## In short', '',
     f'- **All books** ({verdict("Q1")}): with 5 years of loans, the pages add {g4(qa["Q_wiki_on_5y"])} ({seeds_txt(qa["Q_wiki_on_5y"])}), '
     f'against {g4(qa["W_wiki_on_1y"])} with about 1 year of loans. So {says("Q1", "books in general")}.',
     f'- **Books with a page** ({verdict("Q2")}): {g4(qp["Q_wiki_on_5y"])} ({seeds_txt(qp["Q_wiki_on_5y"])}), against '
     f'{g4(qp["W_wiki_on_1y"])} with about 1 year. So {says("Q2", "books with a page")}.',
     f'- **How much of the Wikipedia gain is left** (no rule): {pct(A["share_left"])} for all books, {pct(P["share_left"])} for books with a page. '
     f'Difference of the two gains: {g4(A["difference_of_gains"])} and {g4(P["difference_of_gains"])}.',
     f'- **What 5 years of loans add** (no rule): {g4(qa["C_without_wiki"])} without Wikipedia, {g4(qa["C_with_wiki"])} with it (all books).',
     f'- **Best model**: library + 5 years of loans + own and author pages, {lv(A["2019-2026"]["levels"]["HMW14C"])} on all books and '
     f'{lv(P["2019-2026"]["levels"]["HMW14C"])} on books with a page.']
for k in ('own_book_page', 'author_page_only'):
    d = R[k]['2019-2026']['pairs']
    L.append(f'- **{SAMPN[k]}** (no rule): pages add {g4(d["Q_wiki_on_5y"])} with 5 years of loans, {g4(d["W_wiki_on_1y"])} with about 1 year.')
if META:
    L.append(f'- **Blind month**: forecasts for September 2026 are frozen and public ({META["forecast_rows"]:,} rows, made {META["made_utc"]}); '
             'they are scored once, when the library releases September and it is downloaded.')
L += ['', '## Rules fixed in advance', '',
      'Holm\'s correction over the two checks at one-sided 0.05; a check passes if Holm rejects it, its estimate is above 0 and its 95% interval is above 0.', '',
      '| Check | Gain (95% interval) | One-sided p | Passes Holm | Passed |', '| --- | --- | --- | --- | --- |']
for X, lab in (('Q1', 'Wikipedia pages added on top of 5 years of loans, all books'), ('Q2', 'The same, books with a page (ranked among themselves)')):
    d = DEC[X]
    L.append(f'| {lab} | {d["est"]:+.4f} ({d["lo"]:+.4f} to {d["hi"]:+.4f}) | {d["p_one"]:.4f} | {"yes" if d["holm"] else "no"} | **{"yes" if d["passed"] else "no"}** |')

for s in ('all_books', 'books_with_a_page'):
    W = R[s]
    L += ['', f'## {SAMPN[s]} ({R["sample_rows"][s]:,} scored rows)', '',
          '| Model | Score (95% interval) | ± across seeds | Score 2024 to 2026 | Print | Ebook | Audiobook |', '| --- | --- | --- | --- | --- | --- | --- |']
    for m in ('HM', 'HMW14', 'HM60', 'HMW14C'):
        d = W['2019-2026']['levels'][m]
        L.append(f'| {NAME[m]} | {lv(d)} | {d["sd"]:.4f} | {lv(W["2024-2026"]["levels"][m])} | ' +
                 ' | '.join(f'{W["by_format_levels"][f][m]["est"]:.3f}' for f in FM) + ' |')
    L += ['', '| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |', '| --- | --- | --- | --- | --- | --- | --- |']
    for k in PAIRN:
        L.append(f'| {PAIRN[k]} | {g4(W["2019-2026"]["pairs"][k])} | {seeds_txt(W["2019-2026"]["pairs"][k])} | {g4(W["2024-2026"]["pairs"][k])} | ' +
                 ' | '.join(g4(W['by_format'][f][k]) for f in FM) + ' |')
    T = W['top']
    L += ['', 'Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the early-warning '
          'list keeps only books that had not already risen):', '', '| List | ' + ' | '.join(NAME[m] for m in ('HM', 'HMW14', 'HM60', 'HMW14C')) + ' |',
          '| --- | --- | --- | --- | --- |']
    for lab, k in (('All', 'top20'), ('Early warning', 'early_top20')):
        L.append(f'| {lab} | ' + ' | '.join(lv(T[k][m]) for m in ('HM', 'HMW14', 'HM60', 'HMW14C')) + ' |')
    L += ['', '| List comparison | All | Early warning |', '| --- | --- | --- |']
    for k in ('Q_wiki_on_5y', 'W_wiki_on_1y'):
        L.append(f'| {PAIRN[k]} | {g4(T["top20"][k])} | {g4(T["early_top20"][k])} |')

L += ['', '## By kind of page', '', '| Books | Rows | Pages added, 5 years of loans | Pages added, about 1 year | Share left |', '| --- | --- | --- | --- | --- |']
for s in ('own_book_page', 'author_page_only', 'no_page'):
    d = R[s]['2019-2026']['pairs']
    L.append(f'| {SAMPN[s]} | {R["sample_rows"][s]:,} | {g4(d["Q_wiki_on_5y"])} | {g4(d["W_wiki_on_1y"])} | {pct(R[s]["share_left"])} |')
L += ['', 'Books with no page have no page values; a "gain" there comes from the model using the missing pattern, not from page traffic.']

if SEG is not None:
    SH = {'Q': 'Pages added, 5 years of loans', 'W': 'Pages added, about 1 year'}
    L += ['', '## Results by kind of book (all books)', '',
          'Every group of the 14 families fixed in advance is listed, whatever it shows. The models were fitted on all books; a group only restricts which '
          'books are ranked against each other. "Score" is the score of library + 5 years of loans (no Wikipedia) in that group. Marks: **found** = gain '
          'above zero after the Benjamini-Hochberg correction over all groups of that comparison; **differs** = the gain differs from the gain in the '
          'other books of the same family after the same correction; *small* = fewer than 36 scored months or 1,000 rows, not judged.', '']

    def cell(r):
        m = ['*small*'] if r.too_small else (['**found**'] if r.gain_found else []) + (['**differs**'] if r.differs else [])
        return f'{r.gain:+.4f} ({r.gain_lo:+.4f} to {r.gain_hi:+.4f})' + (' ' + ' '.join(m) if m else '')
    ORD = {'low': 0, 'middle': 1, 'high': 2, 'under 1 year': 0, '1 to 5 years': 1, '5 years or more': 2}
    for fam in SEG.family.drop_duplicates():
        sf = SEG[SEG.family == fam]
        L += [f'### {fam}', '', '| Group | Rows | Months | Score | ' + ' | '.join(SH.values()) + ' |', '| --- | --- | --- | --- | --- | --- |']
        for g in sorted(sf.group.drop_duplicates(), key=lambda x: (ORD.get(x, 9), x)):
            rr = {c: sf[(sf.group == g) & (sf.comparison == c)] for c in SH}
            r0 = rr['Q'].iloc[0]
            L.append(f'| {g} | {r0.rows:,} | {r0.months} | {r0.base_rank:.3f} | ' + ' | '.join(cell(rr[c].iloc[0]) for c in SH) + ' |')
        L += ['']

L += ['## Data and checks', '',
      '- The 5 years of loans are addendum o\'s 35 plain features, built from the same monthly loan series; a refit of the library model reproduces its '
      'stored predictions exactly, and addendum o\'s +0.0128 for the 5 years is reproduced.',
      '- Books with a page: the row has the book\'s own article or the author\'s article (as in the page-books scores of 26 November).']
if META:
    L.append(f'- Blind month: {META["forecast_rows"]:,} rows at origin August 2026, frozen {META["made_utc"]}; file `prereg/blind_q/forecasts_origin_2026-08.csv`, '
             f'SHA-256 {META["csv_sha256"][:16]}... in `prereg/README.md`; the library + 5 years + pages forecasts of the same rows are in `prereg/blind_o/`. '
             'Check: the library model\'s first-seed forecast equals the one frozen for the earlier blind test.')
L += ['', '## Limits', '',
      '- The 5 years are one fair plain way to give the model older loans, not every way; a longer or different history could shrink the Wikipedia gain further.',
      '- The question was asked after addendum o\'s results were seen; the rules were fixed before this model was fitted.',
      '- New books have no loan history and are not in these rows; their test is separate.',
      '- The blind month is one month: it adds to the backtest, it does not replace it.',
      '- A group result describes the books of that group in this sample. It is not the effect of being that kind of book.', '']
(REP / 'wiki_on_5_years.md').write_text('\n'.join(L))
print('written', REP / 'wiki_on_5_years.md')
