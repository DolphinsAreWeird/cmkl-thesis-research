#!/usr/bin/env python3
"""72. Report on the burst features (70) and the Wikidata events (71): coverage, distributions, event counts, checks, runtime, choices.
Data only: nothing is fitted and nothing is related to loans.  Reads data/db/wiki_led/burst_features.parquet, events.parquet, events_long.parquet and
the two summary files; writes data/reports/wiki_led_burst_events_data.md.
Run from handoff/code:   nice -n 10 ../.venv/bin/python main_study/wiki_led/72_report_burst_events.py        (--test reads the *_test files)
"""
import sys, json, time
import numpy as np, pandas as pd
from _common import D, OUT, REP, log

TEST = '--test' in sys.argv
SUF = '_test' if TEST else ''
F = pd.read_parquet(OUT / f'burst_features{SUF}.parquet')
BS = json.loads((OUT / f'burst_features_summary{SUF}.json').read_text())
E = pd.read_parquet(OUT / f'events{SUF}.parquet')
L = pd.read_parquet(OUT / f'events_long{SUF}.parquet')
ES = json.loads((OUT / f'events_summary{SUF}.json').read_text())
CK = json.loads((OUT / 'burst_features_check.json').read_text()) if (OUT / 'burst_features_check.json').exists() else None
W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id', 'title', 'creator', 'item', 'article', 'author_article'])
FEATS = ['pk28', 'dpk', 'pre7', 'dec', 'hi28', 'rec', 'top500', 'corr28', 'co']
HELP = ['top500_lists', 'nrm0']


def ym(mi):
    return f'{int(mi) // 12}-{int(mi) % 12 + 1:02d}'


def mi_of(s):
    return int(s[:4]) * 12 + int(s[5:7]) - 1


def table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '| ' + ' | '.join(['---'] * len(header)) + ' |']
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def f(x, d=3):
    return '' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{x:.{d}f}'


def pct(x, d=1):
    return f'{100 * x:.{d}f}%'


lines = []
P = lines.append
P('# Burst features and Wikidata events for the Wikipedia-led tests: data report')
P('')
P(f'Built on 20 October 2026. Data only: no model was fitted and no feature was related to loans. {"(TEST FILES: 50-item sample)" if TEST else ""}')
P('')
P('## 1. What was built')
P('')
P(table(['File', 'Rows', 'Key', 'Built by'], [
    ['data/db/wiki_led/burst_features.parquet', f'{len(F):,}', '(article, kind in book/author, mi)', 'code/main_study/wiki_led/70_burst_features.py'],
    ['data/db/wiki_led/events.parquet', f'{len(E):,}', '(work_id, mi)', 'code/main_study/wiki_led/71_wikidata_events.py'],
    ['data/db/wiki_led/events_long.parquet', f'{len(L):,}', 'one row per dated event or adaptation link', 'code/main_study/wiki_led/71_wikidata_events.py'],
    ['data/db/wiki_led/events_adaptation_dates.parquet', f'{len(pd.read_parquet(OUT / f"events_adaptation_dates{SUF}.parquet")):,}', 'every P577 and P580 statement of the adaptation items (ad, prop, rank, precision, date)', 'code/main_study/wiki_led/71_wikidata_events.py'],
]))
P('')
P(f'mi = year*12 + month - 1, origins 2016-03 to 2026-09 ({BS["origins"]} months) in both tables. Every feature uses only days up to the last day of the origin month. '
  f'Burst features cover {BS["articles_book"]:,} book articles (the {W.work_id.nunique():,} works in this table share {W.article.nunique():,} distinct articles) and {BS["articles_author"]:,} author articles. '
  f'The report script is 72_report_burst_events.py; the summaries are burst_features_summary.json and events_summary.json in the same folder.')
P('')
P('Not built, as agreed: same_name and other_r4 (they need the busy REST API). Left missing on purpose: ad_rel_public (a later job fills it from the adaptation article views).')
P('')

# ------------------------------------------------------------------------------------------------ burst features
P('## 2. Burst features')
P('')
P('### Definitions as built')
P('')
P('- Daily series. Book article: user views of the canonical title plus the redirects kept by the Study 2R screen, exactly the series behind the weekly Test A features '
  '(checked: summed by week, they equal the stored weekly views on every one of the compared weeks). Author article: the title itself, no redirects, as in Test A. '
  'A day missing from a file counts as 0 views. Share = the day\'s views divided by the day\'s total English Wikipedia user views (data/db/interest/wiki/total_daily.parquet).')
P('- Window = the last 28 days of the origin month. Normal = the median daily share of the 182 days just before the window (days 29 to 210 before the month end, counting the month end as day 1); '
  'this is the daily version of the Test A normal (median of the 26 weeks before the last 4 weeks). Log ratios use the Test A floor, ln((x + 1e-12) / (normal + 1e-12)).')
P('- pk28: largest day divided by the sum of the last 28 days. dpk: days from the peak to the month end (0 = the peak is on the last day). '
  'pre7: ln(mean share of the 7 days before the peak / normal). dec: ln(mean share of up to 7 days after the peak / share on the peak day), missing when the peak is on the last 2 days. '
  'hi28: days of the last 28 with share at least 1.5 times normal. rec: ln(largest share in the last 28 days / largest share on any earlier day since 2015-07-01). '
  'top500: days of the last 28 on which the article (for books also a kept redirect title) was in the English daily top 500 (data/raw/wiki_top_daily.json). '
  'corr28 (books): Pearson correlation of the daily shares of the book and its author article over the last 28 days. '
  'co (books): 1 when b_r4 and a_r4 of Test A are both at least ln 1.5, else 0.')
P('')
P('### Choices I made (the note leaves them open)')
P('')
pk_ = BS.get('peak_day_share_vs_views', {})
P('1. Shares or raw views. One rule: shares of total views wherever a level is compared with a baseline or with another article (pre7, dec, hi28, rec, corr28, as the Test A normal implies); '
  'raw daily views inside one article\'s own last 28 days (pk28, dpk and the choice of the peak day). The peak day is the day with most raw views. '
  f'Over all {pk_.get("windows", 0):,} article-origin windows with views, the day with the largest share was the same day in {pct(pk_.get("share_same", float("nan")))} '
  '(they differ mostly for flat, low-traffic windows, where a few views decide the peak), so the choice matters little for real bursts.')
P('2. Ties for the peak go to the latest day (days since the high, as in a "days since 28-day high" rule). With no views at all in the 28 days there is no peak, so pk28, dpk, pre7, dec and rec are missing; hi28 and top500 are 0.')
md_ = BS['top500_days_without_list_from_2016']
P(f'3. top500: wiki_top_daily.json is one dictionary keyed by day (YYYYMMDD) with 500 [title, views] pairs per day and underscores in the titles; it holds {BS["top500_days_with_list"]:,} days from 2016-01-01 to 2026-09-30. '
  f'{len(md_)} days in that range have no list ({", ".join(md_)}). '
  f'A day without a list counts as not listed, so the {len(BS["top500_origins_with_a_missing_list_day"])} affected origins undercount by at most 2 days; top500_lists gives the number of days with a list in the window (28 on all other origins).')
P('4. corr28 is missing when either raw daily series is constant over the window (shares of two constant series would be correlated only through the common daily total), '
  'when the book has no author article series, or when the book and author article are the same page (84 works). Author articles whose title is not a canonical page (the page redirects to a book or another person) have no series of their own and no features, as in Test A.')
P('5. co: Test A stops at origin 2026-07. For 2026-08 and 2026-09 r4 was computed with the identical Test A formula from the weekly files; the same code reproduced the stored r4 on 2026-05 to 2026-07 '
  f'(book: {BS["checks"]["book"]["n_compared"]:,} values, largest difference {BS["checks"]["book"]["max_abs_diff"]:.1e}; author: {BS["checks"]["author"]["n_compared"]:,} values, largest difference {BS["checks"]["author"]["max_abs_diff"]:.1e}).')
P('6. Extra helper columns: top500_lists (above) and nrm0 (1 when the normal is zero, so pre7, hi28 and rec rest on the 1e-12 floor, usually a page that did not exist yet).')
P('7. Author articles that are also book article titles (53 titles, a wrong book match that is really the person\'s page) have burst features here although Test A\'s weekly author file leaves them out.')
P('')

P('### Coverage')
P('')
rows = []
for kd in ('book', 'author'):
    n = int((F.kind == kd).sum())
    zw = BS['zero_window_share'][kd]
    zn = BS['zero_normal_share'][kd]
    rows.append([kd, f'{n:,}', pct(zw), pct(zn), pct(BS['share_missing'][kd]['dec']), pct(BS['share_missing'][kd]['corr28']) if kd == 'book' else 'not defined', pct(BS['share_missing'][kd]['co']) if kd == 'book' else 'not defined'])
P(table(['kind', 'rows', 'no views in the 28 days (pk28, dpk, pre7, rec missing)', 'zero normal among rows with views', 'dec missing', 'corr28 missing', 'co missing'], rows))
P('')
P(f'Book articles with no daily file: {len(BS["book_articles_without_any_series"])}. Author articles with no daily file under their own title: {BS["author_articles_without_file"]} (all-missing rows, kept in the table so the coverage is visible). '
  f'Almost all of the "no views" rows are origins before the page existed: {pct(BS["zero_window_before_first_view"]["book"]["before"] / max(1, BS["zero_window_before_first_view"]["book"]["before"] + BS["zero_window_before_first_view"]["book"]["after"]))} of the book rows '
  f'and {pct(BS["zero_window_before_first_view"]["author"]["before"] / max(1, BS["zero_window_before_first_view"]["author"]["before"] + BS["zero_window_before_first_view"]["author"]["after"]))} of the author rows with no views in the window fall before the article\'s first day with views.')
P('')
P('Share of rows missing, by feature:')
P('')
rows = []
for c in FEATS + HELP:
    rows.append([c, pct(BS['share_missing']['book'][c], 2), pct(BS['share_missing']['author'][c], 2) if c not in ('corr28', 'co') else 'not defined'])
P(table(['feature', 'book rows', 'author rows'], rows))
P('')

P('### Distributions (rows where the feature exists)')
P('')
for kd in ('book', 'author'):
    P(f'**{kd.capitalize()} articles**')
    P('')
    rows = []
    for c in FEATS + HELP:
        if kd == 'author' and c in ('corr28', 'co'):
            continue
        x = F.loc[F.kind == kd, c].dropna()
        if x.empty:
            continue
        q = x.quantile([.05, .25, .5, .75, .95, .99])
        rows.append([c, f'{len(x):,}'] + [f(v, 3) for v in q] + [f(x.max(), 3), pct((x > 0).mean(), 1)])
    P(table(['feature', 'rows', 'p5', 'p25', 'median', 'p75', 'p95', 'p99', 'max', 'share above 0'], rows))
    P('')

# ------------------------------------------------------------------------------------------------ checks on the burst table
P('### Checks run on the burst features')
P('')
chk = BS.get('checks', {})
if CK:
    P(f'- Independent check (73_check_burst_features.py): a separate plain-pandas version of every definition, with top500 read from the raw file as text, on {CK["pairs"]:,} random article-origin pairs '
      f'(80 books and 40 authors at 8 origins, plus 60 pairs where top500 is above 0), taken from all parts of the full file: {CK["values_compared"]:,} values compared, {CK["mismatches"]} mismatches '
      f'(largest relative difference {max(CK["worst_relative_difference"].values()):.0e}, the float32 storage; hi28, dpk, top500, top500_lists, nrm0 and co agreed exactly).')
if 'plain_pandas_comparison' in chk:
    P(f'- The same check inside the 50-article test run: {chk["plain_pandas_comparison"]["values_compared"]:,} values compared; weekly sums equal Test A weekly views on '
      f'{chk["weekly_sum_equals_study2r_weekly_book"]["weeks_compared"]:,} compared weeks with {chk["weekly_sum_equals_study2r_weekly_book"]["weeks_different"]} differences.')
# plausibility against the weekly Test A features at the same origins (rows with views in the window and a non-zero normal)
from scipy.stats import spearmanr
TA = pd.read_parquet(OUT / 'test_a_wiki_features.parquet', columns=['article', 'kind', 'mi', 'r4', 'rmax', 'nrise8'])
sp = {}
for kd in ('book', 'author'):
    a_ = F[(F.kind == kd) & (F.nrm0 == 0) & F.pk28.notna()][['article', 'mi', 'hi28', 'pre7', 'rec']].merge(TA[TA.kind == kd].drop(columns='kind'), on=['article', 'mi'])
    sp[kd] = (len(a_), {k: spearmanr(a_[k[0]], a_[k[1]], nan_policy='omit').statistic for k in (('hi28', 'r4'), ('pre7', 'r4'), ('hi28', 'nrise8'), ('rec', 'rmax'))})
del TA
P('- Plausibility against the weekly Test A features at the same origins (rows with views in the window and a non-zero normal; Spearman correlation): '
  + '; '.join(f'{kd}s ({sp[kd][0]:,} rows): hi28 with r4 {sp[kd][1][("hi28", "r4")]:.2f}, pre7 with r4 {sp[kd][1][("pre7", "r4")]:.2f}, hi28 with nrise8 {sp[kd][1][("hi28", "nrise8")]:.2f}, rec with rmax {sp[kd][1][("rec", "rmax")]:.2f}' for kd in ('book', 'author'))
  + '. They move together without being the same thing (daily against weekly, a 28-day window against 4 weeks, rec against the all-time high instead of the normal).')
# positive controls from the table: known events must show bursts
mi_ = lambda y, m: y * 12 + m - 1


def row(kind, art, y, m):
    r = F[(F.kind == kind) & (F.article == art) & (F.mi == mi_(y, m))]
    return None if r.empty else r.iloc[0]


pc = []
for kind, art, y, m, what in [('author', 'Toni Morrison', 2019, 8, 'died 5 Aug 2019'), ('author', 'Philip Roth', 2018, 5, 'died 22 May 2018'),
                              ('book', "The Handmaid's Tale", 2017, 4, 'Hulu series from 26 Apr 2017'), ('book', 'Dune (novel)', 2021, 10, 'film 22 Oct 2021'),
                              ('book', 'Where the Crawdads Sing', 2022, 7, 'film 15 Jul 2022'), ('book', 'Normal People', 2020, 4, 'series from 26 Apr 2020')]:
    r, before = row(kind, art, y, m), row(kind, art, y, m - 1 if m > 1 else 12)
    if r is None:
        continue
    pc.append([f'{art} ({kind})', f'{what}, origin {y}-{m:02d}', f(r.pk28, 2), f(r.hi28, 0), f(r.rec, 2), f(r.top500, 0), f(r.corr28, 2) if kind == 'book' else '', f(before.hi28, 0) if before is not None else '', f(before.top500, 0) if before is not None else ''])
if pc:
    P('- Positive controls, known events in the real data. The two deaths should show a one-day spike in the event month. A book with a new series or film is lifted for weeks around the release (trailers, announcements, premieres in other countries), so the month before is already high; the last two columns show it:')
    P('')
    P(table(['article', 'event and origin', 'pk28', 'hi28', 'rec', 'top500', 'corr28', 'hi28 month before', 'top500 month before'], pc))
    P('')

# ------------------------------------------------------------------------------------------------ events
P('## 3. Wikidata events')
P('')
P('### What was fetched')
P('')
P(f'Wikidata SPARQL (query.wikidata.org), fetched {ES["fetched_at"]}: {ES["queries"]["network"]} queries over the network in batches of up to {ES["queries"]["batch"]} items, at least {ES["queries"]["gap_s"]} s apart, '
  f'{ES["queries"]["backoffs"]} back-offs, project user agent from code/config.py, no Wikimedia REST call. Items: {ES["book_items"]:,} book items and {ES["author_items"]:,} author items for {ES["works"]:,} works.')
P('')
P('- Author: the author of works.author_article where the work has one (so the events belong to the same person as the author page views); for the other works the first P50 author that matches a family name of the Seattle creator string. '
  f'{ES["works_with_author_item"]:,} of {ES["works"]:,} works have an author item. Only this one author is used even when a book has several.')
P('- Death: P570 of the author item; statements of deprecated rank are dropped, a preferred rank wins, then the most precise date, then the earliest.')
P('- Awards: P166 on the book item and on the author item, dated by the qualifier P585. Only dates with month precision or finer can be placed in a month; year-only dates are kept in events_long.parquet (mi_event missing) and not used in the flags.')
P('- Adaptations: items linked to the book item by P144 (queried again to get P577 and P580 with their precision), by P4969, and the pairs of the existing adaptations.parquet. '
  'For each adaptation item: all P31 types, a class group (film, tv or other, by P31/P279* to film, television series, television programme, season, episode or web series), the English article title and all P577/P580 dates. '
  'The release date is the earliest P577 or P580 date with month precision or finer among the best-rank statements (a preferred rank wins over normal ones, as in Wikidata\'s own truthy statements; '
  'deprecated statements are dropped, which is how Wikidata marks rescheduled dates: the postponed film Dune: Part Two keeps its old 2023 dates as deprecated statements, so its release is taken as February 2024); '
  'later regional dates are not used. Only film and tv adaptations feed ad_rel; other types (plays, video games, comics, novels, music) are kept in events_long.parquet only.')
P('')
a = ES['adaptations']
P(table(['Adaptation links', 'Count'], [
    ['book-adaptation pairs (union of both sources)', f'{a["pairs"]:,}'], ['found by P144 in the new query', f'{a["p144_now"]:,}'], ['found by P4969', f'{a["p4969_now"]:,}'],
    ['found only through P4969 (new compared with P144)', f'{a["p4969_only"]:,}'], ['in the existing adaptations.parquet', f'{a["in_existing_file"]:,}'],
    ['in the existing file but not found now', f'{a["existing_only"]:,}'], ['books with at least one adaptation', f'{a["books_with_adaptation"]:,}'],
    ['distinct adaptation items', f'{a["adaptation_items"]:,}'], ['of which film, tv, other', f'{a["by_type_group"].get("film", 0):,}, {a["by_type_group"].get("tv", 0):,}, {a["by_type_group"].get("other", 0):,}'],
    ['with an English Wikipedia article', f'{a["with_english_article"]:,}'], ['with a release date at month precision or finer', f'{a["release_month_or_finer"]:,}'],
    ['without a usable month (year-only or no date)', f'{a["year_only_or_no_date"]:,}'],
    ['P577 and P580 date statements of the adaptation items (events_adaptation_dates.parquet)', f'{a["date_statements"]["total"]:,}'],
    ['of which deprecated (rescheduled dates, dropped)', f'{a["date_statements"]["deprecated"]:,}']]))
P('')
ft_ = L[(L.event == 'adaptation') & L.type_group.isin(['film', 'tv']) & (L.year >= 2016)]
ft_share = ft_.mi_event.notna().mean() if len(ft_) else float('nan')
aw = ES['awards']
d = ES['deaths']
P(table(['Death and award dates', 'Count'], [
    ['authors with a usable death date (month or finer)', f'{d["authors_with_usable_date"]:,}'], ['authors with a death date at year precision only', f'{d["year_only_only"]:,}'], ['authors with conflicting death dates', f'{d["conflicting"]:,}'],
    ['P166 award statements (book and author items, no deprecated rank)', f'{aw["statements"]:,}'], ['undated (no P585)', f'{aw["undated"]:,}'], ['dated at month precision or finer (used)', f'{aw["dated_month_or_finer"]:,}'],
    ['dated at year precision only (not used)', f'{aw["dated_year_only"]:,}']]))
P('')
P(f'The award flag is sparse because most P585 dates are year-only: {aw["dated_year_only"]:,} of {aw["dated"]:,} dated award statements ({pct(aw["dated_year_only"] / max(1, aw["dated"]))}) cannot be placed in a month. '
  'That group holds the Hugo, Newbery, National Book Award, Pulitzer and Booker prizes (second table below); the month-precision group (first table) is mostly honorary degrees, orders and fellowships, plus the Nebula Award for Best Novel.')
P('')
P(table(['Most frequent awards with a month-precision date (used)', 'Statements'], [[k, v] for k, v in aw.get('top_awards_month_precision', {}).items()]))
P('')
P(table(['Most frequent awards with a year-only date (not used)', 'Statements'], [[k, v] for k, v in aw.get('top_awards_year_only', {}).items()]))
P('')
P(table(['Most frequent P31 types of the adaptation items (an item can have several)', 'Items'], [[k, v] for k, v in a.get('top_types', {}).items()]))
P('')

# independent check of the death years: the library catalogue writes birth and death years into many creator strings (for example "Le Guin, Ursula K., 1929-2018")
cy = W.creator.str.extract(r'(\d{4})\s*-\s*(\d{4})')
cw = W.assign(cat_death_year=pd.to_numeric(cy[1], errors='coerce')).dropna(subset=['cat_death_year'])
wd_death = L[L.event == 'death'].drop_duplicates('subject').set_index('subject').year
auth = E.drop_duplicates('work_id').set_index('work_id').author_item
cw = cw.assign(author_item=cw.work_id.map(auth))
cw = cw[cw.author_item.notna()]
cw['wd_year'] = cw.author_item.map(wd_death)
both_ = cw[cw.wd_year.notna()]
if len(cw):
    P(f'Cross-check with the library catalogue: {len(cw):,} works have a death year in the Seattle creator string and an author item here; Wikidata has a death date for {len(both_):,} of them, '
      f'and the year agrees for {int((both_.wd_year == both_.cat_death_year).sum()):,} ({pct((both_.wd_year == both_.cat_death_year).mean() if len(both_) else float("nan"))}). '
      f'Authors the catalogue says are dead but Wikidata has no usable death date for: {len(cw) - len(both_):,} works.')
    P('')

P('### Events by type and year')
P('')
yrs = list(range(2015, 2027))
Lm = L[L.mi_event.notna()].copy()
Lm['yr'] = (Lm.mi_event // 12).astype(int)


def count_row(name, sub, col='yr', df=None):
    df = Lm if df is None else df
    s = df.loc[sub, col] if not isinstance(sub, pd.Series) else df.loc[sub, col]
    before = int((s < yrs[0]).sum())
    return [name, f'{before:,}'] + [f'{int((s == y).sum()):,}' for y in yrs] + [f'{len(s):,}']


Ly = L[L.mi_event.isna() & L.year.notna()].copy()
Ly['yr'] = Ly.year.astype(int)
rows = [
    count_row('author deaths (distinct authors, month or finer)', (Lm.event == 'death')),
    count_row('dated awards of books (month or finer)', (Lm.event == 'award') & (Lm.subject_kind == 'book')),
    count_row('dated awards of authors (month or finer)', (Lm.event == 'award') & (Lm.subject_kind == 'author')),
    count_row('film adaptations, first release (book-adaptation pairs)', (Lm.event == 'adaptation') & (Lm.type_group == 'film')),
    count_row('tv adaptations, first release (pairs)', (Lm.event == 'adaptation') & (Lm.type_group == 'tv')),
    count_row('other adaptation types, first release (pairs, not used)', (Lm.event == 'adaptation') & (Lm.type_group == 'other')),
    count_row('awards of books dated by year only (not used)', (Ly.event == 'award') & (Ly.subject_kind == 'book'), df=Ly),
    count_row('awards of authors dated by year only (not used)', (Ly.event == 'award') & (Ly.subject_kind == 'author'), df=Ly),
    count_row('film and tv adaptations with a year but no month (not used)', (Ly.event == 'adaptation') & Ly.type_group.isin(['film', 'tv']), df=Ly),
]
P(table(['Event', f'before {yrs[0]}'] + [str(y) for y in yrs] + ['total'], rows))
P('')
P('Years are the year of the event date. 2026 is partial.')
P('')
P('### The per-work, per-month table (events.parquet)')
P('')
n = len(E)
P(table(['Column', 'Share of rows = 1', 'Rows = 1'], [
    ['died (author died in t or t-1)', pct(E.died.mean(), 3), f'{int(E.died.sum()):,}'],
    ['award (dated award of book or author in t or t-1)', pct(E.award.mean(), 3), f'{int(E.award.sum()):,}'],
    ['ad_rel (film or tv release in t-1, t or t+1)', pct(E.ad_rel.mean(), 3), f'{int(E.ad_rel.sum()):,}'],
    ['any of the three', pct(((E.died + E.award + E.ad_rel) > 0).mean(), 3), f'{int(((E.died + E.award + E.ad_rel) > 0).sum()):,}']]))
P('')
q = E.months_since_event.quantile([.05, .25, .5, .75, .95])
P(f'months_since_event (capped at 24): median {q[.5]:.0f}, share at the cap {pct((E.months_since_event == 24).mean())}; 5th and 25th percentile {q[.05]:.0f} and {q[.25]:.0f}. '
  f'ad_rel_public is missing in all {int(E.ad_rel_public.isna().sum()):,} rows, as agreed. Works: {E.work_id.nunique():,}; works with at least one died, award or ad_rel month: '
  f'{int(E.groupby("work_id")[["died", "award", "ad_rel"]].sum().sum(axis=1).gt(0).sum()):,}.')
P('')

# positive controls for the events
P('### Positive controls for the events')
P('')
ctrl = []
first_row = E.drop_duplicates('work_id').set_index('work_id')
Wi = W.set_index('work_id')


def flags(work_ids, col, y, m):
    r = E[(E.work_id.isin(work_ids)) & (E.mi == mi_(y, m))]
    return None if r.empty else int(r[col].max())


for who, y, m in [('Toni Morrison', 2019, 8), ('Philip Roth', 2018, 5), ('Ursula K. Le Guin', 2018, 1), ('Elie Wiesel', 2016, 7)]:
    ids = W[W.author_article == who].work_id.tolist()
    if not ids:
        continue
    seq = [flags(ids, 'died', *(divmod(mi_(y, m) + k, 12)[0], divmod(mi_(y, m) + k, 12)[1] + 1)) for k in (-1, 0, 1, 2)]
    if any(v is not None for v in seq):
        ctrl.append([f'{who} (author, {len(ids)} work{"s" if len(ids) != 1 else ""})', f'died {y}-{m:02d}, flags at t-1 / t / t+1 / t+2', ' / '.join('n/a' if v is None else str(v) for v in seq), 'expected 0 / 1 / 1 / 0'])
for book, y, m in [("The Handmaid's Tale", 2017, 4), ('Dune (novel)', 2021, 10), ('Where the Crawdads Sing', 2022, 7), ('Normal People', 2020, 4), ('Little Fires Everywhere', 2020, 3),
                   ('The Queen\'s Gambit (novel)', 2020, 10), ('Crazy Rich Asians', 2018, 8)]:
    ids = W[W.article == book].work_id.tolist()
    if not ids:
        continue
    item = W[W.article == book]['item'].iloc[0]
    ad = L[(L.event == 'adaptation') & (L.subject == item) & L.type_group.isin(['film', 'tv'])]
    months = sorted({ym(v) for v in ad.mi_event.dropna()})
    seq = [flags(ids, 'ad_rel', *(divmod(mi_(y, m) + k, 12)[0], divmod(mi_(y, m) + k, 12)[1] + 1)) for k in (-3, -2, -1, 0, 1, 2, 3)]
    if any(v is not None for v in seq):
        ctrl.append([f'{book} (book)', f'release near {y}-{m:02d}; film and tv release months on Wikidata: {", ".join(months[-6:]) if months else "none"}',
                     ' / '.join('n/a' if v is None else str(v) for v in seq), 'ad_rel at 3 months before to 3 months after the release month'])
# a few dated awards, spread over the years: the flag must be 1 in the award month and the month after
aw_ = L[(L.event == 'award') & L.mi_event.between(mi_(2016, 3), mi_(2026, 8))].sort_values('mi_event')
if len(aw_):
    for r in aw_.iloc[np.linspace(0, len(aw_) - 1, min(4, len(aw_))).astype(int)].itertuples():
        wid = (W[W['item'] == r.subject].work_id if r.subject_kind == 'book' else E.drop_duplicates('work_id').loc[lambda x: x.author_item == r.subject, 'work_id']).tolist()
        if not wid:
            continue
        seq = [flags(wid, 'award', *(divmod(int(r.mi_event) + k, 12)[0], divmod(int(r.mi_event) + k, 12)[1] + 1)) for k in (-1, 0, 1, 2)]
        t_ = W[W.work_id == wid[0]].title.iloc[0]
        lab_ = r.label if isinstance(r.label, str) else r.detail
        ctrl.append([f'{lab_} ({r.subject_kind} award; e.g. "{t_[:30]}", {len(wid)} work(s))', f'dated {r.date}, flags at t-1 / t / t+1 / t+2', ' / '.join('n/a' if v is None else str(v) for v in seq),
                     'expected 0 / 1 / 1 / 0 unless another award is near'])
if ctrl:
    P(table(['Case', 'Event', 'Flag in the months around it', 'Meaning'], ctrl))
    P('')
else:
    P('(none of the control works are in this sample)')
    P('')

# ------------------------------------------------------------------------------------------------ runtime
P('## 4. Runtime, memory and load')
P('')
P(table(['Script', 'Run time', 'Peak memory', 'Notes'], [
    ['70_burst_features.py', f'{BS["runtime_s"]} s', f'{BS["peak_memory_mb"]} MB', 'one process, articles in chunks of 400; run with nice -n 10 through jobs/bg.sh (job wl_burst)'],
    ['71_wikidata_events.py', f'{ES["runtime_s"]} s', f'{ES["peak_memory_mb"]} MB', f'{ES["queries"]["network"]} queries ({ES["queries"]["query_seconds"]} s of query time), run with nice -n 10 through jobs/bg.sh (job wl_events)'],
]))
P('')
P('Both full runs were started only after a test on 50 articles (burst features) and about 50 items (events). The independent check (73) took about 90 s and the report (72) a few seconds. '
  'No Wikimedia REST call was made by any of these scripts; Wikidata queries ran one at a time with at least 1.5 s between them and no back-off was needed.')
P('')
P('## 5. How to join the tables to the Test A rows')
P('')
P('- Burst features, book part: rows with kind == "book", merge on (article, mi) with the work\'s article (prefix b_). Author part: rows with kind == "author", merge on (author_article = article, mi) (prefix a_). '
  'mi is the Test A origin month (year*12 + month - 1). Test A rows stop at origin 2026-07; both new tables go to 2026-09.')
P('- Events: merge on (work_id, mi). The columns died, award, ad_rel and months_since_event have no missing values; ad_rel_public is missing everywhere for now.')
P('')
P('## 6. Cautions for whoever uses the tables')
P('')
P('- Rows with no views in the window have missing shape features, not zeros (the page did not exist yet in almost all cases). Trees handle this; ridge models need the missing-value flags Test A already uses.')
P('- 2025-05 and 2025-06: Wikimedia later found that part of the unusual "human" traffic was bots, so burst features for those months (pk28, hi28, rec, top500 and the shares behind them) are noisier. They are not corrected here.')
P(f'- The adaptation release date is the first dated release among the best-rank Wikidata statements (a festival premiere can be the first date); about half of the adaptation items ({a["year_only_or_no_date"]:,} of {a["adaptation_items"]:,}) have only a year or no date, so ad_rel covers only part of all adaptations; '
  f'for film and tv adaptations whose first date is in 2016 or later, {pct(ft_share)} of the {len(ft_):,} book-adaptation pairs have a month.')
P('- The award flag has few positives (month-precision dates only) and misses most of the big literary prizes (Pulitzer, Booker, National Book Award, Hugo, Newbery), whose dates are year-only on Wikidata. A calendar of announcement months for the ten or twenty biggest prizes would add them; I did not add one because it would be my own input, not Wikidata data.')
P('- events.parquet uses only dates up to the end of the origin month for died, award and months_since_event. ad_rel looks one month ahead (release in t+1); a later job must set ad_rel_public so that such a row is used only when the adaptation article already had views before the end of t.')
P('- For the placebo "event dates moved 12 months later", move events_long.parquet mi_event by 12 and rebuild the flags with the same rules.')
P('')
(REP / f'wiki_led_burst_events_data{SUF}.md').write_text('\n'.join(lines) + '\n')
log('wrote', REP / f'wiki_led_burst_events_data{SUF}.md', f'{len(lines)} lines')
