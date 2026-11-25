# m05. Addendum m, step 5 (text): the plain-language report from m04's outputs.  No computation of results here; wording follows the
# record's wording rules (prereg/addenda_wiki_led/2026-11-25_m_theme_pages_single_books.json, A decisions.pass and B wording_rule).
# Inputs: data/reports/theme_pages_single_books.json, theme_pages_segments.csv, data/db/wiki_led/m_theme_pages/features_summary.json,
#   wd_facts.json.  Output: data/reports/theme_pages_single_books.md
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/m_theme_pages/m05_report.py
import json, time, pathlib, sys
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
REP = DATA / 'reports'
OUT = DATA / 'db' / 'wiki_led' / 'm_theme_pages'
import os
if os.environ.get('M04_MOCK'):                 # test mode: read and write in the mock folder
    REP = pathlib.Path(os.environ['M04_MOCK'])
R = json.loads((REP / 'theme_pages_single_books.json').read_text())
S = pd.read_csv(REP / 'theme_pages_segments.csv')
FS = json.loads((OUT / 'features_summary.json').read_text())
WD = json.loads((OUT / 'wd_facts.json').read_text())

NAME = {'HM': 'Library model (loan history and calendar month)',
        'HMW14': 'Library + the book\'s own and author\'s pages',
        'HMW14C': '... + hand-reviewed theme pages',
        'HMW14A': '... + AI-sorted theme pages',
        'HMC': 'Library + hand-reviewed theme pages (no own pages)',
        'HMA': 'Library + AI-sorted theme pages (no own pages)',
        'C_alone': 'Hand-reviewed theme pages alone',
        'A_alone': 'AI-sorted theme pages alone',
        'C_donor_alone': 'Another theme\'s hand-reviewed pages alone (placebo)',
        'A_donor_alone': 'Another theme\'s AI-sorted pages alone (placebo)',
        'HMW14C_donor': 'Library + own pages + another theme\'s hand-reviewed pages (placebo)',
        'HMW14A_donor': 'Library + own pages + another theme\'s AI-sorted pages (placebo)',
        'HMW14C_lag': 'Library + own pages + hand-reviewed theme pages, dates moved 12 months (placebo)',
        'HMW14A_lag': 'Library + own pages + AI-sorted theme pages, dates moved 12 months (placebo)',
        'HMW14K': 'Library + own pages + the theme\'s own borrowing',
        'HMW14KC': '... + theme borrowing + hand-reviewed theme pages',
        'HMW14KA': '... + theme borrowing + AI-sorted theme pages'}
PAIRNAME = {
    'own_pages_gain': 'Own and author pages, added to the library model',
    'C_gain': 'Hand-reviewed theme pages, added to library + own pages',
    'A_gain': 'AI-sorted theme pages, added to library + own pages',
    'C_vs_donor': 'Hand-reviewed: real themes minus another theme with similar traffic',
    'A_vs_donor': 'AI-sorted: real themes minus another theme with similar traffic',
    'C_vs_lag': 'Hand-reviewed: real dates minus dates moved 12 months',
    'A_vs_lag': 'AI-sorted: real dates minus dates moved 12 months',
    'C_alone_vs_donor_alone': 'Hand-reviewed pages alone: real minus another theme',
    'A_alone_vs_donor_alone': 'AI-sorted pages alone: real minus another theme',
    'C_without_own_pages': 'Hand-reviewed theme pages added to the library model (no own pages)',
    'A_without_own_pages': 'AI-sorted theme pages added to the library model (no own pages)',
    'C_beyond_theme_borrowing': 'Hand-reviewed theme pages beyond the theme\'s own borrowing',
    'A_beyond_theme_borrowing': 'AI-sorted theme pages beyond the theme\'s own borrowing',
    'theme_borrowing_gain': 'The theme\'s own borrowing, added to library + own pages'}
ARM = {'C': 'hand-reviewed theme pages', 'A': 'AI-sorted theme pages'}
cap = lambda t: t[0].upper() + t[1:]


def g4(d):
    return f'{d["est"]:+.4f} ({d["lo"]:+.4f} to {d["hi"]:+.4f})'


def seeds_txt(d):
    return f'± {d["sd"]:.4f}; {d["min"]:+.4f} to {d["max"]:+.4f}; {d["n_above0"]} of 5 above 0'


def lv(d):
    return f'{d["est"]:.3f} ({d["lo"]:.3f} to {d["hi"]:.3f})'


W = R['whole']['2019-2026']
dec = R['decisions']
Lr = ['# Theme pages as inputs for single books, and results by kind of book', '',
      f'Made by `code/main_study/wiki_led/m_theme_pages/m04_score.py` and `m05_report.py` on {time.strftime("%Y-%m-%d %H:%M")} (+07:00). '
      'Settings fixed in advance in `prereg/addenda_wiki_led/2026-11-25_m_theme_pages_single_books.json` (made public on GitHub, pull request 33, '
      'at 05:38 UTC on 25 November 2026, before any step ran). Changes and choices made later are logged with times in `prereg/DEVIATIONS.md`.', '',
      '## The question', '',
      'Until now, the models for single books used the library\'s loan history and two Wikipedia pages: the book\'s own article and its author\'s. '
      'Here, pages about the book\'s themes are added: their traffic level, their rise against normal, how long a rise has lasted, and whether a '
      'lasting rise is under way. Two sets of theme pages are tested separately: 624 concept pages reviewed by hand, and about 40,000 pages sorted '
      'into the same themes by an AI model (each counted only from the month it had twice been among the 500 most-viewed pages). The question is '
      'whether they improve the ranking of which books will rise next month, on the same books and months as the thesis\'s main table, and for '
      'which kinds of books any page signal helps.', '',
      '## How to read the numbers', '',
      '- **Score**: each month and format, the books are ranked by predicted change in loans and compared with the actual change (rank correlation; '
      '0 is chance, 1 is perfect), averaged over the 78 months from February 2019 to August 2026. Models only ever learn from earlier years.',
      '- **Gain**: the score with the added pages minus the score without them, on the same rows.',
      '- **Five seeds**: every model was fitted five times with different random seeds. A value is the mean of the five; "±" is their standard '
      'deviation, then the smallest and largest of the five, and how many were above 0.',
      '- **95% interval** (in brackets): from 2,000 redraws of blocks of three consecutive months, with the five-seed mean recomputed in each redraw.',
      '- **Placebos**: the same model given (a) the pages of another theme with similar traffic, or (b) the real theme pages with their dates moved '
      '12 months later. If the signal is real and about the book\'s own themes at the right time, the real pages should beat both.', '']

Lr += ['## In short', '']
for X in ('C', 'A'):
    d = dec[X]
    g = W['pairs'][f'{X}_gain']
    verdict = 'passed' if d['passed'] else 'did not pass'
    why = []
    if not d['M1_adds']:
        why.append('the gain was not clearly above zero after the correction for testing two page sets')
    elif not (d['M2_beats_other_theme'] and d['M3_beats_moved_dates']):
        parts = []
        if not d['M2_beats_other_theme']:
            parts.append('from general traffic of similar size (another theme\'s pages did as well)')
        if not d['M3_beats_moved_dates']:
            parts.append('from the theme\'s usual timing (the same pages with dates moved 12 months did as well)')
        why.append('the gain cannot be told apart ' + ' or '.join(parts))
    else:
        pass
    if not d['M1_adds']:
        if not d['M2_beats_other_theme']:
            why.append('it also did not beat another theme\'s pages of similar traffic')
        if not d['M3_beats_moved_dates']:
            why.append('it also did not beat the same pages with their dates moved 12 months')
    Lr.append(f'- **{cap(ARM[X])}** {verdict} the rule fixed in advance. Added to the library model with the book\'s own and author\'s pages, '
              f'they changed the score by {g4(g)} (five seeds {seeds_txt(g)}).' + (f' Reason: {"; ".join(why)}.' if why else ''))
og = W['pairs']['own_pages_gain']
Lr.append(f'- **The book\'s own and author\'s pages** (the existing test) added {g4(og)} (five seeds {seeds_txt(og)}), as published.')
kb = W['pairs']['theme_borrowing_gain']
Lr.append(f'- **The theme\'s own borrowing** (a library-side feature, no Wikipedia) added {g4(kb)}. With it in the model, hand-reviewed theme pages added '
          f'{g4(W["pairs"]["C_beyond_theme_borrowing"])} and AI-sorted ones {g4(W["pairs"]["A_beyond_theme_borrowing"])}.')
ht = S[(S.family == 'Has a theme')].set_index(['comparison', 'group'])
def htg(c, g):
    r = ht.loc[(c, g)]
    return f'{r.gain:+.4f} ({r.gain_lo:+.4f} to {r.gain_hi:+.4f})'
Lr.append(f'- **Where the theme-page gain comes from.** Split by whether the book has a narrow catalogue theme (a split fixed in advance): AI-sorted theme pages '
          f'added {htg("Theme pages, AI-sorted", "yes")} for books with a theme and {htg("Theme pages, AI-sorted", "no")} for books without one; hand-reviewed '
          f'pages {htg("Theme pages, hand-reviewed", "yes")} and {htg("Theme pages, hand-reviewed", "no")}. Most rows of books without a narrow theme have no '
          'theme-page values at all, so their gain cannot come from page traffic: it comes from the model learning that books without a catalogue theme behave '
          'differently. The two placebos have the same missing values, so the real-minus-placebo differences in the table below are the cleaner measure of '
          'what the theme pages themselves carry.')
ss = R['segments_summary']
for c, v in ss.items():
    Lr.append(f'- **By kind of book, {c[0].lower() + c[1:]}**: {v["judged"]} of {v["groups"]} groups were large enough to judge; a gain was found in '
              f'{v["gains_found"]} and a difference from the other books in {v["differences_found"]} after correcting for the number of groups.')
Lr += ['']

Lr += ['## Rule fixed in advance', '',
       'A set of theme pages passes only if all three hold: (1) its gain over the library model with the book\'s own and author\'s pages is above zero, '
       'with Holm\'s correction for testing two page sets; (2) it beats another theme\'s pages with similar traffic; (3) it beats its own pages with '
       'the dates moved 12 months. Conditions (2) and (3) need a 95% interval above zero.', '',
       '| Theme pages | (1) Adds to library + own pages | One-sided p | (2) Beats another theme | (3) Beats moved dates | Passed |',
       '| --- | --- | --- | --- | --- | --- |']
for X in ('C', 'A'):
    d = dec[X]
    yn = lambda b: 'yes' if b else 'no'
    Lr.append(f'| {cap(ARM[X])} | {yn(d["M1_adds"])}: {g4(W["pairs"][f"{X}_gain"])} | {d["M1_p_one"]:.4f} | '
              f'{yn(d["M2_beats_other_theme"])}: {g4(W["pairs"][f"{X}_vs_donor"])} | {yn(d["M3_beats_moved_dates"])}: {g4(W["pairs"][f"{X}_vs_lag"])} | '
              f'**{yn(d["passed"])}** |')
Lr += ['']

for per in ('2019-2026', '2024-2026'):
    Wp = R['whole'][per]
    Lr += [f'## Scores of every model, main set, {per.replace("-", " to ")}', '',
           (f'{R["rows"]:,} book-format-months; target months February 2019 to August 2026.' if per == '2019-2026'
            else 'The rows whose target month is in January 2024 to August 2026; the same draws of three-month blocks.'), '',
           '| Model | Score, five-seed mean (95% interval) | ± across seeds |', '| --- | --- | --- |']
    for m in ['HM', 'HMW14', 'HMW14C', 'HMW14A', 'HMC', 'HMA', 'C_alone', 'A_alone', 'C_donor_alone', 'A_donor_alone', 'HMW14C_donor',
              'HMW14A_donor', 'HMW14C_lag', 'HMW14A_lag', 'HMW14K', 'HMW14KC', 'HMW14KA']:
        d = Wp['levels'][m]
        Lr.append(f'| {NAME[m]} | {lv(d)} | {d["sd"]:.4f} |')
    Lr += ['', '| Comparison | Gain, five-seed mean (95% interval) | Five seeds: ± SD; smallest to largest; above 0 |', '| --- | --- | --- |']
    for k, d in Wp['pairs'].items():
        Lr.append(f'| {PAIRNAME[k]} | {g4(d)} | {seeds_txt(d)} |')
    Lr += ['']

for per in ('2019-2026', '2024-2026'):
    Lr += [f'## By format, {per.replace("-", " to ")}', '', '| Format | Library | + own pages | + hand-reviewed theme pages | + AI-sorted theme pages |',
           '| --- | --- | --- | --- | --- |']
    for f, bb in R['by_format'].items():
        l_ = bb[per]['levels']
        Lr.append(f'| {f} | {l_["HM"]["est"]:.3f} | {l_["HMW14"]["est"]:.3f} | {l_["HMW14C"]["est"]:.3f} | {l_["HMW14A"]["est"]:.3f} |')
    Lr += ['', '| Comparison | ' + ' | '.join(R['by_format']) + ' |', '| --- | ' + ' | '.join('---' for _ in R['by_format']) + ' |']
    for k in PAIRNAME:
        Lr.append(f'| {PAIRNAME[k]} | ' + ' | '.join(g4(R['by_format'][f][per]['pairs'][k]) for f in R['by_format']) + ' |')
    Lr += ['']

T = R['top20']
Lr += ['## Monthly top-20 lists', '',
       'Each month and format, the 20 books with the highest predicted change; the share of them whose loans rose by half or more next month. '
       'The early-warning list keeps only books that had not already risen. Gains are in share points (0.010 is one percentage point).', '',
       '| Period | Formats | List | Library | + own pages | + hand-reviewed theme pages | + AI-sorted theme pages | Own pages gain | Hand-reviewed gain | AI-sorted gain |',
       '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for per in ('2019-2026', '2024-2026'):
    for fl in ('all', 'print', 'ebook', 'audiobook'):
        for k, nm in (('top20', 'all books'), ('early_top20', 'early warning')):
            t = T[per][fl][k]
            Lr.append(f'| {per.replace("-", " to ")} | {fl} | {nm} | {t["HM"]["est"]:.3f} | {t["HMW14"]["est"]:.3f} | {t["HMW14C"]["est"]:.3f} | {t["HMW14A"]["est"]:.3f} | '
                      f'{g4(t["own_pages_gain"])} | {g4(t["C_gain"])} | {g4(t["A_gain"])} |')
Lr += ['']

# segments
Lr += ['## Results by kind of book', '',
       'Every group of every family fixed in advance is listed, whatever it shows. The models were fitted on all books; a group only restricts which books '
       'are ranked against each other. "Score" is the library model\'s score in that group. Each gain is a five-seed mean with its 95% interval. '
       'Marks: **found** = gain above zero after the Benjamini-Hochberg correction over all groups of that comparison; **differs** = the gain in this group '
       'differs from the gain in the other books of the same family after the same correction; *small* = fewer than 36 scored months or 1,000 rows, '
       'not judged. Groups defined from Wikidata (series, film or TV, award, translated, classic) cover only books matched to a Wikidata book item.', '']
COMPS = ['Own and author pages', 'Theme pages, hand-reviewed', 'Theme pages, AI-sorted']


def cell(r):
    m = []
    if r.too_small:
        m.append('*small*')
    else:
        if r.gain_found:
            m.append('**found**')
        if r.differs:
            m.append('**differs**')
    return f'{r.gain:+.4f} ({r.gain_lo:+.4f} to {r.gain_hi:+.4f})' + (' ' + ' '.join(m) if m else '')


for fam in S.family.drop_duplicates():
    sf = S[S.family == fam]
    Lr += [f'### {fam}', '', '| Group | Rows | Months | Score (library) | ' + ' | '.join(COMPS) + ' |', '| --- | --- | --- | --- | --- | --- | --- |']
    ORD = {'low': 0, 'middle': 1, 'high': 2, 'under 1 year': 0, '1 to 5 years': 1, '5 years or more': 2}
    for g in sorted(sf.group.drop_duplicates(), key=lambda x: (ORD.get(x, 9), x)):
        rr = {c: sf[(sf.group == g) & (sf.comparison == c)].iloc[0] for c in COMPS}
        r0 = rr[COMPS[0]]
        Lr.append(f'| {g} | {r0.rows:,} | {r0.months} | {r0.base_rank:.3f} | ' + ' | '.join(cell(rr[c]) for c in COMPS) + ' |')
    Lr += ['']

found = S[S.gain_found | S.differs]
Lr += ['### Groups that stand out after correction', '']
if len(found) == 0:
    Lr.append('None: no group showed a gain or a difference from the other books after the correction.')
else:
    for _, r in found.iterrows():
        bits = []
        if r.gain_found:
            bits.append(f'gain {r.gain:+.4f} ({r.gain_lo:+.4f} to {r.gain_hi:+.4f}), adjusted p {r.gain_p_bh:.3f}')
        if r.differs:
            bits.append(f'{"larger" if r["diff"] > 0 else "smaller"} than in the other books by {r["diff"]:+.4f} ({r.diff_lo:+.4f} to {r.diff_hi:+.4f}), adjusted p {r.diff_p_bh:.3f}')
        Lr.append(f'- {r.comparison}, {r.family}: {r.group}: ' + '; '.join(bits) + '.')
Lr += ['']

cov = FS['coverage']
Lr += ['## Data behind the test', '',
       f'- Theme pages: {FS["themes_with_features"]["C"]} themes with hand-reviewed pages and {FS["themes_with_features"]["A"]} with AI-sorted pages had a weekly series. '
       f'Share of scored rows whose book had a narrow-theme feature: {cov["C"]["real_n"]:.1%} (hand-reviewed), {cov["A"]["real_n"]:.1%} (AI-sorted); '
       'books with no catalogue theme have none.',
       f'- AI-sorted pages counted from the month of their second day in the daily top 500, by year: {FS["admitted_by_year"]}.',
       f'- Wikidata book items: {WD["works_with_item"]:,} of {WD["works"]:,} main-set works; {WD["follows"]:,} follow an earlier book; '
       f'{WD["with_screen_adaptation_dated"]:,} have a dated film or TV adaptation; {WD["with_award_dated"]:,} a dated award; '
       f'{WD["before_1930"]:,} were first published before 1930.',
       '- Checks: the copied feature code reproduces the stored features of the book articles exactly; all AI-sorted pages together reproduce the '
       'stored theme series; the library and own-page scores, their intervals and the five-seed gains of 20 November are reproduced exactly.', '',
       '## Limits', '',
       '- The 40,000 AI-sorted pages were picked by how often they were among the most viewed over the whole period; counting each page only from its '
       'second top-500 day removes most, not all, of this look-ahead.',
       '- The hand-reviewed pages were chosen by meaning, not traffic, but by someone who knew the earlier theme results.',
       '- Wikidata facts cover only books matched to a Wikidata book item, mostly well-known ones; which books have an item uses Wikidata as of October 2026.',
       '- A group result describes the books of that group in this sample. It is not the effect of being that kind of book.',
       '- Bestseller-list history was not used as a split: its matching was checked only for the well-known books.',
       '- Popularity thirds are cut over every book-format with a scored month in that test year, so a book\'s third can depend slightly on which other '
       'books became eligible later in the same year (mostly new books with no loans the year before). No prediction uses the thirds.',
       '- "Rows" in the group tables are scored rows (in format-months with at least 3 books of the group).', '']
(REP / 'theme_pages_single_books.md').write_text('\n'.join(Lr) + '\n')
print('written', REP / 'theme_pages_single_books.md')
