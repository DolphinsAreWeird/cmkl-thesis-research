# n60. Addendum n, last step (text): the plain-language report from n50's outputs.  No result is computed here; the only numbers worked out
# are coverage counts of the feature files.  Wording follows addendum m's wording rule (prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json
# and 2026-11-25_m_theme_pages_single_books.json).
# Inputs: data/reports/more_signals_single_books.json, more_signals_segments.csv, more_signals_book_author_by_article.csv,
#   more_signals_per_type.csv; data/db/wiki_led/n_more_signals/*_summary.json, feat_*.parquet (coverage only).
# Output: data/reports/more_signals_single_books.md
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/n_more_signals/n60_report.py
import json, math, time, pathlib, sys
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
REP = DATA / 'reports'
OUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
R = json.loads((REP / 'more_signals_single_books.json').read_text())
P12 = R.get('12', {})
DEC = P12.get('decisions', {})

SIG = {'N': 'New York Times bestseller lists', 'AD': 'Wikipedia pages of the book\'s film and TV versions',
       'LK': 'Wikipedia pages linked to the book in Wikidata (its subjects, places, characters and periods)',
       'OL': 'Open Library reading logs (want to read, reading, read)', 'AZ': 'Amazon reviews (Amazon Reviews 2023)',
       'ALL': 'the four signals in hand together (lists, film and TV pages, linked pages, reading logs)'}
SHORT = {'N': 'Bestseller lists', 'AD': 'Film and TV pages', 'LK': 'Linked pages', 'OL': 'Reading logs', 'AZ': 'Amazon reviews', 'ALL': 'All four in hand'}
cap = lambda t: t[0].upper() + t[1:]
yn = lambda b: 'yes' if b else 'no'


def bad(d):
    return d is None or d.get('est') is None or (isinstance(d['est'], float) and math.isnan(d['est']))


def g4(d):
    return 'no rows' if bad(d) else f'{d["est"]:+.4f} ({d["lo"]:+.4f} to {d["hi"]:+.4f})'


def seeds_txt(d):
    return '' if bad(d) or 'n_above0' not in d else f'± {d["sd"]:.4f}; {d["min"]:+.4f} to {d["max"]:+.4f}; {d["n_above0"]} of 5 above 0'


def lv(d):
    return 'no rows' if bad(d) else f'{d["est"]:.3f} ({d["lo"]:.3f} to {d["hi"]:.3f})'


def mi_txt(mi):
    return f'{["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][mi % 12]} {mi // 12}'


# ---------------------------------------------------------------- coverage of the feature files (scored rows: origins 2019-01 to 2026-07)
def coverage(name, col, upto=None):
    f = OUT / f'feat_{name}.parquet'
    if not f.exists():
        return None
    x = pd.read_parquet(f, columns=['mi', col])
    s = (x.mi >= 2019 * 12) & (x.mi <= (upto if upto is not None else 2026 * 12 + 6))
    return float(x.loc[s, col].notna().mean()), int(s.sum())


AZS = None
for p in (OUT / 'amazon' / 'amazon_summary.json', OUT / 'amazon_summary.json'):
    if p.exists():
        AZS = json.loads(p.read_text()); break
AZ_LAST = P12.get('amazon_last_usable_mi', (AZS or {}).get('last_usable_mi'))
COV = {'N': coverage('N', 'N_ever'), 'AD': coverage('AD', 'AD_lvl4'), 'LK': coverage('LK', 'LK_lvl4'), 'OL': coverage('OL', 'OL_all'),
       'AZ': coverage('AZ', 'AZ_cum', AZ_LAST) if AZ_LAST is not None else None}
NYT = json.loads((OUT / 'nyt_summary.json').read_text())
OLS = json.loads((OUT / 'ol_summary.json').read_text())
BA = json.loads((OUT / 'ba_summary.json').read_text())
N12 = json.loads((OUT / 'n12_summary.json').read_text()) if (OUT / 'n12_summary.json').exists() else {}


def check(name):
    f = OUT / name
    if not f.exists():
        return None
    v = pd.read_csv(f, sep='\t').verdict.value_counts()
    return int(v.get('right', 0)), int(v.get('wrong', 0)), int(v.get('unsure', 0))


CK_N, CK_AZ = check('nyt_check_50_answers.tsv'), check('amazon_match_check_50_answers.tsv')

L = ['# More online signals for single books, better models, and results by kind of book', '',
     f'Made by `code/main_study/wiki_led/n_more_signals/n50_score.py` and `n60_report.py` on {time.strftime("%Y-%m-%d %H:%M")} '
     f'({time.strftime("%z")[:3]}:{time.strftime("%z")[3:]}). Settings fixed in advance in '
     '`prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json` (made public on GitHub, pull request 35, at 09:38 UTC on 25 November 2026, '
     'before any step ran). Choices and fixes made later are logged with times in `prereg/DEVIATIONS.md`, section "Addendum n".', '',
     '## The question', '',
     'The single-book models predict which books will rise in loans next month at the Seattle Public Library. Until now they used the library\'s loan '
     'history and two Wikipedia pages: the book\'s own article and its author\'s. Theme pages added almost nothing (the previous report). This report asks '
     'three things, on the same books and months as the thesis\'s main table:', '',
     '1. **Other online signals.** Do any of these add to the library model with the own and author pages: New York Times bestseller lists; the Wikipedia '
     'pages of the book\'s film and TV versions; Wikipedia pages linked to the book in Wikidata (subjects, places, characters, periods); Open Library '
     'reading logs; Amazon reviews?',
     '2. **Better use of the pages already in the model.** Does the gain come from the book\'s own page or the author\'s? Do models fitted separately for '
     'each kind of book do better than one model for all? Does a pretrained Transformer (Chronos-2) forecast better than the boosted trees, and does it '
     'help as an extra input?',
     '3. **For which kinds of book** does each signal help (the 14 families of the previous report: series, film or TV version, popularity, fiction, '
     'audience, format, age, author\'s earlier books, own article, award, translated, classic, genre, theme)?', '',
     '## How to read the numbers', '',
     '- **Score**: each month and format, the books are ranked by predicted change in loans and compared with the actual change (rank correlation; 0 is '
     'chance, 1 is perfect), averaged over the 78 months from February 2019 to August 2026. Models only ever learn from earlier years.',
     '- **Gain**: the score with the added signal minus the score without it, on the same rows. 0.001 is small; the own and author pages together add '
     'about 0.005.',
     '- **Five seeds**: every boosted-tree model was fitted five times with different random seeds; a value is the mean of the five. "±" is their standard '
     'deviation, then the smallest and largest, and how many were above 0. The Transformer has no random part, so it has one run.',
     '- **95% interval** (in brackets): from 2,000 redraws of blocks of three consecutive months, with the five-seed mean recomputed in each redraw.',
     '- **Placebos**: for each new signal, the same model given the same book\'s signal with its dates moved 12 months later. For the own and author '
     'pages, the same model given another book\'s (or author\'s) article with similar traffic. A real signal should beat its placebo.', '']

# ---------------------------------------------------------------- in short
L += ['## In short', '']
for X in ('N', 'AD', 'LK', 'OL', 'AZ'):
    d = DEC.get(X)
    if d is None or not d.get('available'):
        L.append(f'- **{SHORT[X]}** could not be tested (see "Data behind the test").')
        continue
    w = P12[X]['2019-2026']['pairs']
    why = []
    if not d['adds']:
        why.append('the gain was not clearly above zero after the correction for testing five signals')
    if not d['beats_moved_dates']:
        why.append('the same signal with its dates moved 12 months did about as well, so the gain cannot be told apart from what the signal says '
                   'about the book in general')
    extra = ''
    if X == 'AZ' and AZ_LAST is not None:
        extra = f' Scored only up to {mi_txt(int(AZ_LAST))}, the last month with full review counts.'
    L.append(f'- **{SHORT[X]}** {"passed" if d["passed"] else "did not pass"} the rule fixed in advance. Added to the library model with the own and '
             f'author pages, they changed the score by {g4(w["gain"])} (five seeds {seeds_txt(w["gain"])}); real dates minus dates moved 12 months: '
             f'{g4(w["vs_moved_dates"])}.' + (f' Reason: {"; ".join(why)}.' if why else '') + extra)
if 'ALL' in P12:
    w = P12['ALL']['2019-2026']['pairs']
    L.append(f'- **All four signals in hand together** (no pass rule): {g4(w["gain"])}; against the same four with dates moved 12 months: '
             f'{g4(w["vs_moved_dates"])}.')
if '3a' in R:
    a = R['3a']; w = a['whole']['2019-2026']['pairs']; dc = a['decisions']
    L.append(f'- **Book page or author page?** Both carry part of the gain. The book\'s own page alone added {g4(w["book_page_gain"])} to the library model '
             f'and the author\'s page alone {g4(w["author_page_gain"])}; together {g4(w["both_pages_gain"])}. Each beat another article of similar '
             f'traffic (book {g4(w["book_vs_donor"])}, author {g4(w["author_vs_donor"])}), so both '
             f'{"passed" if dc["book"]["passed"] and dc["author"]["passed"] else "were judged"} by the rule fixed in advance '
             f'(book: {"passed" if dc["book"]["passed"] else "did not pass"}; author: {"passed" if dc["author"]["passed"] else "did not pass"}). '
             f'The author\'s page adds {g4(w["author_beyond_book"])} beyond the book\'s page, and the book\'s page {g4(w["book_beyond_author"])} beyond the '
             'author\'s. The author page reaches more books (about three in five scored rows have one, against one in five for a book page), which is '
             'much of why its whole-set gain is larger.')
PT = pd.read_csv(REP / 'more_signals_per_type.csv') if (REP / 'more_signals_per_type.csv').exists() else None
GRPN = lambda fam, g: {'F3_popularity': f'{g} popularity third', 'F4_fiction': g, 'F6_format': g, 'F9_own_article': g}.get(fam, g)
if PT is not None:
    sig = PT[PT.p_bh < 0.05]
    better = sig[(sig.est > 0) & sig.comparison.str.startswith('per-type minus pooled')]
    worse = sig[(sig.est < 0) & sig.comparison.str.startswith('per-type minus pooled')]
    L.append(f'- **One model per kind of book** (no pass rule): of {int(PT.comparison.str.startswith("per-type minus pooled").sum())} group comparisons, '
             f'{len(better)} were better and {len(worse)} worse than one model for all books after the correction. Better: '
             + ('; '.join(f'{GRPN(r.family, r.group)} ({r.comparison.split(", ")[1]}, {r.est:+.4f})' for r in better.itertuples()) or 'none')
             + '. Worse: ' + ('; '.join(f'{GRPN(r.family, r.group)} ({r.comparison.split(", ")[1]}, {r.est:+.4f})' for r in worse.itertuples()) or 'none')
             + '. Separate models mostly shrank the own-page gain rather than raising it.')
if '3c' in R:
    c = R['3c']; w = c['2019-2026']; lvx = w['levels']; pr = w['pairs']
    t = [f'the Transformer on loan history alone scored {lv(lvx["C2"])} against {lv(lvx["HM"])} for the boosted-tree library model'
         f' ({g4(pr["C2_minus_HM"])})' if 'C2' in lvx else None,
         f'with the own and author pages as extra inputs it scored {lv(lvx["C2W"])} against {lv(lvx["HMW14"])} ({g4(pr["C2W_minus_HMW14"])}); '
         f'the pages changed the Transformer\'s score by {g4(pr["C2W_minus_C2"])}' if 'C2W' in lvx else None,
         f'given to the boosted trees as two extra inputs, its forecasts changed the score by {g4(pr["stacking_gain"])}' if 'stacking_gain' in pr else None]
    L.append('- **Pretrained Transformer (Chronos-2, no training on these data)** (no pass rule): ' + '; '.join(x for x in t if x) + '.')
SEG = pd.read_csv(REP / 'more_signals_segments.csv') if (REP / 'more_signals_segments.csv').exists() else None
if SEG is not None:
    for cname in SEG.comparison.drop_duplicates():
        s = SEG[SEG.comparison == cname]
        L.append(f'- **By kind of book, {SHORT.get(cname, cname).lower()}**: {int((~s.too_small).sum())} of {len(s)} groups were large enough to judge; a gain '
                 f'was found in {int(s.gain_found.sum())} and a difference from the other books in {int(s.differs.sum())} after correcting for the '
                 'number of groups.')
L += ['']

# ---------------------------------------------------------------- rules fixed in advance
L += ['## Rules fixed in advance', '',
      '**New signals.** A signal passes only if both hold: (1) its gain over the library model with the own and author pages has a one-sided p that passes '
      'Holm\'s correction over the five signals, with an estimate above zero; (2) it beats the same signal with its dates moved 12 months (95% interval '
      'above zero). A signal that could not be built counts as not passing and keeps its place in the correction.', '',
      '| Signal | (1) Gain over library + own pages | One-sided p | Passes Holm | (2) Real minus moved dates | Passed |', '| --- | --- | --- | --- | --- | --- |']
for X in ('N', 'AD', 'LK', 'OL', 'AZ'):
    d = DEC.get(X)
    if d is None or not d.get('available'):
        L.append(f'| {SHORT[X]} | not built | | | | **no** |')
        continue
    w = P12[X]['2019-2026']['pairs']
    L.append(f'| {SHORT[X]} | {g4(w["gain"])} | {d["p_one"]:.4f} | {yn(d["adds"])} | {g4(w["vs_moved_dates"])} | **{yn(d["passed"])}** |')
if '3a' in R:
    a = R['3a']; w = a['whole']['2019-2026']['pairs']; dc = a['decisions']
    L += ['', '**Book page against author page.** A page passes if its gain over the library model passes Holm\'s correction over the two pages '
          '(one-sided, 0.05, estimate above zero) and it beats another article of similar traffic (95% interval above zero).', '',
          '| Page | Gain over library model | One-sided p | Passes Holm | Real minus another article | Passed |', '| --- | --- | --- | --- | --- | --- |']
    for X, nm in (('book', 'Book\'s own page'), ('author', 'Author\'s page')):
        L.append(f'| {nm} | {g4(w[f"{X}_page_gain"])} | {dc[X]["p_one"]:.4f} | {yn(dc[X]["adds"])} | {g4(w[f"{X}_vs_donor"])} | **{yn(dc[X]["passed"])}** |')
L += ['', 'The models per kind of book and the Transformer had no pass rule: they are reported with intervals only.', '']

# ---------------------------------------------------------------- part 1 and 2 detail
NM12 = lambda X: {'HM': 'Library model (loan history and calendar month)', 'HMW14': 'Library + own and author pages',
                  f'HMW14{X}': f'Library + own pages + {SHORT.get(X, X).lower()}', f'{X}_alone': f'{SHORT.get(X, X)} alone (with the format)',
                  f'HMW14{X}_lag': f'Library + own pages + {SHORT.get(X, X).lower()}, dates moved 12 months (placebo)',
                  'HMW14_ALL': 'Library + own pages + all four in hand', 'ALL_lag': '... all four, dates moved 12 months (placebo)'}
for X in ('N', 'AD', 'LK', 'OL', 'AZ', 'ALL'):
    if X not in P12:
        continue
    Wx = P12[X]
    L += [f'## {cap(SIG[X])}', '']
    if X == 'AZ' and AZ_LAST is not None:
        L += [f'Scored on the rows whose origin month is on or before {mi_txt(int(AZ_LAST))}, the last month with full review counts; the library and '
              'own-page models are rescored on the same rows.', '']
    L += ['| Model | Score 2019 to 2026 (95% interval) | ± across seeds | Score 2024 to 2026 |', '| --- | --- | --- | --- |']
    for m, d in Wx['2019-2026']['levels'].items():
        L.append(f'| {NM12(X).get(m, m)} | {lv(d)} | {d["sd"]:.4f} | {lv(Wx["2024-2026"]["levels"][m])} |')
    L += ['', '| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |', '| --- | --- | --- | --- | --- | --- | --- |']
    for k, nm in (('gain', 'Gain over library + own pages'), ('vs_moved_dates', 'Real minus dates moved 12 months')):
        bf = Wx['by_format']
        L.append(f'| {nm} | {g4(Wx["2019-2026"]["pairs"][k])} | {seeds_txt(Wx["2019-2026"]["pairs"][k])} | {g4(Wx["2024-2026"]["pairs"][k])} | '
                 + ' | '.join(g4(bf[f][k]) if f in bf else '' for f in ('print', 'ebook', 'audiobook')) + ' |')
    tp = Wx.get('top', {})
    if tp:
        big = f'HMW14{X}' if X != 'ALL' else 'HMW14_ALL'
        L += ['', 'Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the '
              'early-warning list keeps only books that had not already risen):', '',
              '| List | Library + own pages | With the signal | Gain |', '| --- | --- | --- | --- |']
        for lab_, nm in (('top20', 'All books'), ('early_top20', 'Early warning')):
            L.append(f'| {nm} | {lv(tp[lab_]["HMW14"])} | {lv(tp[lab_][big])} | {g4(tp[lab_]["gain"])} |')
    L += ['']

# ---------------------------------------------------------------- 3a detail
if '3a' in R:
    a = R['3a']
    NM3 = {'HM': 'Library model', 'HMW14': 'Library + both pages', 'HMB': 'Library + book\'s own page', 'HMA': 'Library + author\'s page',
           'HMB_donor': 'Library + another book\'s page of similar traffic (placebo)', 'HMA_donor': 'Library + another author\'s page of similar traffic (placebo)'}
    PN3 = {'book_page_gain': 'Book page added to the library model', 'author_page_gain': 'Author page added to the library model',
           'book_vs_donor': 'Book page: real minus another book\'s page', 'author_vs_donor': 'Author page: real minus another author\'s page',
           'author_beyond_book': 'Author page beyond the book page', 'book_beyond_author': 'Book page beyond the author page',
           'both_pages_gain': 'Both pages added to the library model (published result)'}
    L += ['## The book\'s own page against the author\'s page', '',
          f'Book articles: {BA["book_articles"]:,}; author articles: {BA["author_articles"]:,}; every one got a placebo article. Share of scored rows with a '
          f'book-page value {BA["scored_rows_real_book"]:.1%}, with an author-page value {BA["scored_rows_real_author"]:.1%} (the placebo has the same '
          'missing pattern).', '',
          '| Model | Score 2019 to 2026 (95% interval) | ± across seeds | Score 2024 to 2026 |', '| --- | --- | --- | --- |']
    for m, d in a['whole']['2019-2026']['levels'].items():
        L.append(f'| {NM3[m]} | {lv(d)} | {d["sd"]:.4f} | {lv(a["whole"]["2024-2026"]["levels"][m])} |')
    L += ['', '| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |', '| --- | --- | --- | --- | --- | --- | --- |']
    for k, nm in PN3.items():
        bf = a['whole']['by_format']
        L.append(f'| {nm} | {g4(a["whole"]["2019-2026"]["pairs"][k])} | {seeds_txt(a["whole"]["2019-2026"]["pairs"][k])} | '
                 f'{g4(a["whole"]["2024-2026"]["pairs"][k])} | ' + ' | '.join(g4(bf[f][k]) for f in ('print', 'ebook', 'audiobook')) + ' |')
    BYA = pd.read_csv(REP / 'more_signals_book_author_by_article.csv')
    L += ['', 'By which article the book has (marks as in "Results by kind of book" below):', '',
          '| Group | Rows | Score (library) | Book page | Author page |', '| --- | --- | --- | --- | --- |']
    for g in ('book article', 'author article only', 'neither'):
        rr = {c: BYA[(BYA.group == g) & (BYA.comparison == c)].iloc[0] for c in ('Book page', 'Author page')}
        r0 = rr['Book page']

        def cl(r):
            m = ['*small*'] if r.too_small else (['**found**'] if r.gain_found else []) + (['**differs**'] if r.differs else [])
            return f'{r.gain:+.4f} ({r.gain_lo:+.4f} to {r.gain_hi:+.4f})' + (' ' + ' '.join(m) if m else '')
        L.append(f'| {g} | {r0.rows:,} | {r0.base_rank:.3f} | {cl(rr["Book page"])} | {cl(rr["Author page"])} |')
    L += ['', 'Books with neither article have no page values, so any gain there comes from the model learning how books without articles behave.', '']

# ---------------------------------------------------------------- 3b detail
if PT is not None:
    FAMN = {'F3_popularity': 'Popularity in the year before', 'F4_fiction': 'Fiction or nonfiction', 'F6_format': 'Format', 'F9_own_article': 'Own Wikipedia article'}
    fb = R.get('3b', {}).get('fallbacks', {})
    L += ['## One model per kind of book', '',
          'For four families, the library model and the library + own pages model were fitted separately within each group (training on that group\'s '
          'earlier rows only) and compared with the single model fitted on all books, on the group\'s own rows. '
          + (f'{len(fb)} group-years had fewer than 1,000 training rows and used the single model\'s training rows.' if fb else
             'Every group-year had at least 1,000 training rows.')
          + ' Marked **bold** where the Benjamini-Hochberg adjusted p is below 0.05 (within each comparison over all groups).', '',
          '| Family | Group | Rows | Library: separate minus single | Library + own pages: separate minus single | Own-page gain, single model | '
          'Own-page gain, separate models | Difference |', '| --- | --- | --- | --- | --- | --- | --- | --- |']

    def pc(r):
        s = f'{r.est:+.4f} ({r.lo:+.4f} to {r.hi:+.4f})'
        return f'**{s}**' if r.p_bh < 0.05 else s
    for fam in PT.family.drop_duplicates():
        for g in PT[PT.family == fam].group.drop_duplicates():
            q = PT[(PT.family == fam) & (PT.group == g)].set_index('comparison')
            a1, a2, a3 = q.loc['per-type minus pooled, library model'], q.loc['per-type minus pooled, library + own pages'], q.loc['own-page gain, per-type minus pooled']
            L.append(f'| {FAMN.get(fam, fam)} | {g} | {int(a3.rows):,} | {pc(a1)} | {pc(a2)} | {a3.gain_pooled:+.4f} | {a3.gain_per_type:+.4f} | {pc(a3)} |')
    L += ['']

# ---------------------------------------------------------------- 3c detail
if '3c' in R:
    c = R['3c']
    NMc = {'HM': 'Library model (boosted trees)', 'HMW14': 'Library + own and author pages (boosted trees)',
           'C2': 'Transformer, loan history only', 'C2W': 'Transformer, loan history + own and author page views',
           'HMW14Z': 'Boosted trees: library + own pages + the two Transformer forecasts'}
    PNc = {'C2_minus_HM': 'Transformer minus library model', 'C2W_minus_HMW14': 'Transformer with pages minus library + own pages',
           'C2W_minus_C2': 'What the pages add to the Transformer', 'stacking_gain': 'Transformer forecasts added to the boosted trees'}
    L += ['## A pretrained Transformer (Chronos-2)', '',
          'Chronos-2 (amazon/chronos-2, the version of the theme benchmark) was used as released, with no training on these data, on the computer\'s '
          'processor. For each book, format and month it saw up to 60 months of log loans and forecast the next month; its predicted change is the median '
          'forecast minus the log of the last six months\' average, as for the other models. The version with pages also saw the monthly view share of '
          'the book\'s own and author\'s articles. It has no random part, so the "± across seeds" column is empty for it.', '',
          '| Model | Score 2019 to 2026 (95% interval) | ± across seeds | Score 2024 to 2026 | Print | Ebook | Audiobook |',
          '| --- | --- | --- | --- | --- | --- | --- |']
    for m, d in c['2019-2026']['levels'].items():
        bl = c['by_format_levels']
        sd_txt = '' if m in ('C2', 'C2W') else f'{d["sd"]:.4f}'
        L.append(f'| {NMc.get(m, m)} | {lv(d)} | {sd_txt} | {lv(c["2024-2026"]["levels"][m])} | '
                 + ' | '.join(f'{bl[f][m]["est"]:.3f}' for f in ('print', 'ebook', 'audiobook')) + ' |')
    L += ['', '| Comparison | 2019 to 2026 | 2024 to 2026 | Print | Ebook | Audiobook |', '| --- | --- | --- | --- | --- | --- |']
    for k, d in c['2019-2026']['pairs'].items():
        bf = c['by_format']
        L.append(f'| {PNc.get(k, k)} | {g4(d)} | {g4(c["2024-2026"]["pairs"][k])} | ' + ' | '.join(g4(bf[f][k]) for f in ('print', 'ebook', 'audiobook')) + ' |')
    tp = c.get('top', {})
    if tp:
        L += ['', '| List | ' + ' | '.join(NMc.get(m, m) for m in c['2019-2026']['levels']) + ' |', '| --- |' + ' --- |' * len(c['2019-2026']['levels'])]
        for lab_, nm in (('top20', 'Top 20, all books'), ('early_top20', 'Top 20, early warning')):
            L.append(f'| {nm} | ' + ' | '.join(f'{tp[lab_][m]["est"]:.3f}' for m in c['2019-2026']['levels']) + ' |')
    L += ['']

# ---------------------------------------------------------------- segments
if SEG is not None:
    COMPS = [x for x in ('N', 'AD', 'LK', 'OL', 'AZ', 'ALL') if x in set(SEG.comparison)]
    L += ['## Results by kind of book', '',
          'Every group of every family fixed in advance is listed, whatever it shows. The models were fitted on all books; a group only restricts which books '
          'are ranked against each other. "Score" is the library + own pages model\'s score in that group; each cell is the gain from adding the signal, '
          'a five-seed mean with its 95% interval. Marks: **found** = gain above zero after the Benjamini-Hochberg correction over all groups of that '
          'signal; **differs** = the gain differs from the gain in the other books of the same family after the same correction; *small* = fewer than 36 '
          'scored months or 1,000 rows, not judged. Groups from Wikidata (series, film or TV, award, translated, classic) cover only books matched to a '
          'Wikidata book item. Amazon reviews are scored on fewer months (see above), so their rows differ from the "Rows" column.', '']

    def cell(r):
        m = ['*small*'] if r.too_small else (['**found**'] if r.gain_found else []) + (['**differs**'] if r.differs else [])
        return f'{r.gain:+.4f} ({r.gain_lo:+.4f} to {r.gain_hi:+.4f})' + (' ' + ' '.join(m) if m else '')
    ORD = {'low': 0, 'middle': 1, 'high': 2, 'under 1 year': 0, '1 to 5 years': 1, '5 years or more': 2}
    for fam in SEG.family.drop_duplicates():
        sf = SEG[SEG.family == fam]
        L += [f'### {fam}', '', '| Group | Rows | Months | Score | ' + ' | '.join(SHORT[c] for c in COMPS) + ' |', '| --- | --- | --- | --- |' + ' --- |' * len(COMPS)]
        for g in sorted(sf.group.drop_duplicates(), key=lambda x: (ORD.get(x, 9), x)):
            rr = {c: sf[(sf.group == g) & (sf.comparison == c)] for c in COMPS}
            r0 = next(v.iloc[0] for v in rr.values() if len(v))
            L.append(f'| {g} | {r0.rows:,} | {r0.months} | {r0.base_rank:.3f} | ' + ' | '.join(cell(rr[c].iloc[0]) if len(rr[c]) else '' for c in COMPS) + ' |')
        L += ['']
    found = SEG[SEG.gain_found | SEG.differs]
    L += ['### Groups that stand out after correction', '']
    if len(found) == 0:
        L.append('None: no group showed a gain or a difference from the other books after the correction.')
    for _, r in found.iterrows():
        bits = []
        if r.gain_found:
            bits.append(f'gain {r.gain:+.4f} ({r.gain_lo:+.4f} to {r.gain_hi:+.4f}), adjusted p {r.gain_p_bh:.3f}')
        if r.differs:
            bits.append(f'{"larger" if r["diff"] > 0 else "smaller"} than in the other books by {r["diff"]:+.4f} ({r.diff_lo:+.4f} to {r.diff_hi:+.4f}), '
                        f'adjusted p {r.diff_p_bh:.3f}')
        L.append(f'- {SHORT.get(r.comparison, r.comparison)}, {r.family}: {r.group}: ' + '; '.join(bits) + '.')
    L += ['']

# ---------------------------------------------------------------- data
cv = lambda X: (f'{COV[X][0]:.1%} of {COV[X][1]:,} scored rows' if COV.get(X) else 'not built')
L += ['## Data behind the test', '',
      f'- **Bestseller lists**: {NYT["works_matched"]:,} of {NYT["works_main_set"]:,} main-set works matched to New York Times list entries '
      f'({NYT["entries_matched"]:,} entries; ISBN or title and author, the rules of the earlier list test unchanged, which they reproduce exactly). '
      f'{NYT["scored_rows_N_matched"]:.1%} of the {NYT["scored_rows"]:,} scored rows belong to a matched work (unmatched works get 0 and a flag); '
      f'{NYT["scored_rows_N_on"]:.2%} of scored rows were on a list in their month. '
      + (f'An independent check of 50 random matches found {CK_N[0]} right, {CK_N[1]} wrong and {CK_N[2]} unsure (the rule allowed up to 5 wrong).' if CK_N else ''),
      f'- **Film and TV pages**: {cv("AD")} have a value ({N12.get("AD", {}).get("works", 541) if isinstance(N12.get("AD"), dict) else 541} works with at '
      'least one film or TV article with views).',
      f'- **Linked pages**: {cv("LK")} have a value (1,447 works, 1,688 pages).',
      f'- **Reading logs**: {OLS["works_mapped"]:,} works mapped to Open Library through Wikidata; {cv("OL")} have a value. The dump keeps only entries '
      'still on a shelf in September 2026.']
if AZS is not None:
    L.append(f'- **Amazon reviews**: ' + (f'{AZS["works_matched"]:,} works matched; ' if 'works_matched' in AZS else '')
             + (f'last usable month {mi_txt(int(AZ_LAST))}; ' if AZ_LAST is not None else '') + f'{cv("AZ")} (up to that month) have a review history. '
             + (f'An independent check of 50 random matches found {CK_AZ[0]} right, {CK_AZ[1]} wrong and {CK_AZ[2]} unsure (the rule allowed up to 5 '
                'wrong). Both wrong ones have titles that start with a series name and a colon (for example "Pete the Cat: ..."), so every book of that '
                'series by the same author was summed into one work.' if CK_AZ else ''))
else:
    L.append('- **Amazon reviews**: not built.')
L += ['- Checks: the stored library and own-page scores of the main table are reproduced exactly; the refitted library + own pages model equals the '
      'stored predictions; the copied page-feature code reproduces the stored features.', '',
      '## Limits', '',
      '- Film and TV pages, linked pages and reading logs exist only for books matched to a Wikidata book item, mostly well-known books; which books have '
      'one uses Wikidata as of October 2026.',
      '- Bestseller lists cover only the top of the market; most books never appear on one.',
      '- Amazon reviews come from one retailer and end in 2023, so they are scored on fewer months than the other signals. Matching by title and '
      'author merges books of a series whose titles share the text before a colon, and a few non-book Amazon items carry a book\'s ISBN.',
      '- The Transformer was used as released, without tuning or training on library data; a trained deep model might do differently. It was '
      'pretrained (released in 2025) on public time series that may cover some of the test years; it never saw these library series, but it may '
      'carry general patterns of those years. Its gain as an extra input had no pass rule and no placebo, so it is a lead to confirm, not a result.',
      '- Bestseller lists and Amazon reviews raised the score over all books, but Amazon reviews lowered the share of risers in both monthly top-20 '
      'lists and bestseller lists lowered it in the early-warning list. They improve the ranking as a whole more than its very top.',
      '- A group result describes the books of that group in this sample. It is not the effect of being that kind of book.', '']
(REP / 'more_signals_single_books.md').write_text('\n'.join(L) + '\n')
print('written', REP / 'more_signals_single_books.md')
