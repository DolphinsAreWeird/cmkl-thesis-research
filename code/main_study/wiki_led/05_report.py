#!/usr/bin/env python3
"""Test B (new books): write data/reports/wiki_led_test_b_data.md from the finished data files.

Counts and match rates only.  No model is fitted and no feature is related to any outcome here.
Run from handoff/code:   nice -n 10 ../.venv/bin/python main_study/wiki_led/05_report.py
"""
import json, time
import numpy as np, pandas as pd
from _common import OUT, REP, Http, log, maxlag_check

H = Http({'wd': 0.21})


def jl(name):
    return json.loads((OUT / name).read_text())


def pct(k, n, d=1):
    return f'{100 * k / n:.{d}f}%' if n else 'n/a'


def md_table(df):
    cols = list(df.columns)
    out = ['| ' + ' | '.join(str(c) for c in cols) + ' |', '| ' + ' | '.join('---' for _ in cols) + ' |']
    for _, r in df.iterrows():
        out.append('| ' + ' | '.join(str(r[c]) for c in cols) + ' |')
    return '\n'.join(out)


def views_log_summary():
    """The views job was stopped and restarted several times (rate tuning); add up what its log shows.  The log prints the counters every
    500 titles, so for a run that was stopped the numbers are lower bounds."""
    import re, ast
    txt = (REP / 'wiki_led_views.log').read_text().splitlines()
    blocks, cur = [], None
    for ln in txt:
        if ln.startswith('=== start'):
            cur = dict(start=ln, last=None, episodes=0, args=ln.split('03_author_views.py')[-1].strip())
            blocks.append(cur)
        elif cur is not None:
            m = re.search(r'network (\d+), cache (\d+), backoffs (\d+).*codes (\{.*\})', ln)
            if m:
                cur['last'] = (int(m.group(1)), int(m.group(3)), ast.literal_eval(m.group(4)))
            if 'throttled by rest' in ln:
                cur['episodes'] += 1
    net = sum(b['last'][0] for b in blocks if b['last'])
    codes = {}
    for b in blocks:
        if b['last']:
            for k, v in b['last'][2].items():
                codes[k] = codes.get(k, 0) + v
    return dict(runs=len(blocks), network=net, codes=codes, episodes=sum(b['episodes'] for b in blocks), args=[b['args'] for b in blocks])


def labels(qids):
    st, text = H.get('wd', 'https://www.wikidata.org/w/api.php', dict(action='wbgetentities', ids='|'.join(qids), props='labels', languages='en',
                                                                      format='json', maxlag=5), check=maxlag_check)
    ents = json.loads(text).get('entities', {})
    return {q: ents.get(q, {}).get('labels', {}).get('en', {}).get('value', '?') for q in qids}


def main():
    pc = jl('population_counts.json')
    ll = jl('loans_library_counts.json')
    ms = jl('author_match_summary.json')
    vs = jl('author_views_summary.json')
    rs = jl('rows_summary.json')
    ck = jl('checks_summary.json')
    am = pd.read_parquet(OUT / 'author_match.parquet')
    rows = pd.read_parquet(OUT / 'test_b_rows.parquet')
    lm = pd.read_csv(OUT / 'library_month_totals.csv')
    wi = pd.read_parquet(OUT / 'wikidata_items.parquet')
    L = []
    P = L.append
    P('# Test B (new books): data for the Wikipedia-led test')
    P('')
    P('Built 20 Oct 2026 from the settings fixed in `prereg/wiki_led_settings_2026-10-20.json`, section `test_B_new_books`. '
      'This file reports counts and match rates only. No model was fitted and no Wikipedia feature was related to loans.')
    P('')
    P('Code: `code/main_study/wiki_led/` (`01_population.py`, `01b_loans_library.py`, `02_author_match.py`, `03_author_views.py`, `04_rows.py`, `05_report.py`, `06_checks.py`). '
      'Data: `data/db/wiki_led/` (`test_b_population`, `test_b_loans_library`, `author_match`, `wikidata_items`, `author_monthly_views`, `test_b_rows`). '
      'HTTP cache: `data/interim/wiki_led_cache/`.')
    P('')
    P('## 1. Population')
    P('')
    P(f"Works in `spl_works.parquet`: {pc['works_in_spl_works']:,}. First Seattle month 2017-01 to 2026-02: {pc['first_ym_201701_202602']:,}. "
      f"With a publication year: {pc['with_pub_year']:,}. New releases (publication year at least the year of the first month minus 1): "
      f"**{pc['new_releases']:,}** (the figure in the record), with {pc['new_releases_distinct_creator_key_incl_empty']:,} distinct `creator_key`.")
    P('')
    P(f"Of these, {pc['empty_creator_dropped']:,} works have an empty creator string, so no name parses and they are dropped. "
      f"For the remaining **{pc['nonempty_creator']:,}** works `parse_author` returned a name every time: **{pc['parse_failures']} further parse failures**. "
      f"Population: **{pc['population_works']:,} works**, {pc['population_distinct_creator_key']:,} distinct `creator_key` (the record's 'about 92,000'), "
      f"{pc['population_distinct_display_name']:,} distinct first-author display names. Two works have a non-empty creator string but an empty `creator_key` "
      f"('Mrs. & Mr. MacLeod'); in the rows file their `creator_key` is set to `__nokey_<work_id>` so that they do not form one cluster with the other empty keys, and their library features are 0. "
      f"{pc['nonempty_creator_from_title_only']:,} population works have a creator taken from the title statement only (`creator_from_title_only`); they are kept, as the record does not exclude them.")
    P('')
    by = pd.DataFrame({'test year': list(pc['population_by_year'].keys()), 'works': list(pc['population_by_year'].values())})
    by['empty creator, dropped'] = [pc['empty_creator_dropped_by_year'].get(y, 0) for y in by['test year']]
    by['works before dropping'] = by.works + by['empty creator, dropped']
    by['distinct names'] = [pc['distinct_display_name_by_year'][y] for y in by['test year']]
    by['works'] = by.works.map('{:,}'.format)
    P(md_table(by[['test year', 'works before dropping', 'empty creator, dropped', 'works', 'distinct names']]))
    P('')
    P('Test year = calendar year of `first_ym`. 2026 holds the months 2026-01 and 2026-02 only.')
    P('')
    P('## 2. Outcome and library features')
    P('')
    P(f"Monthly checkouts of all three formats come from the record-level files ({ll['rows_per_format']['book']:,} book, {ll['rows_per_format']['ebook']:,} ebook, "
      f"{ll['rows_per_format']['audiobook']:,} audiobook rows; rows without a work: 0). `loans6` = loans in months `first_ym` to `first_ym`+5, `Y6` = ln(1 + loans6). "
      f"Every population work has a row in its first month, none has a row before it, and none has `loans6` = 0. "
      f"Library features follow the record: earlier works of the same `creator_key` in all of `spl_works`, and ln(1 + their loans before the work's first month). "
      f"Checked against a plain-pandas recomputation from the raw rows (`06_checks.py`) for {ck['library_checked']} works (60 random, 10 of the three most prolific creators): "
      f"{ck['library_mismatches']} differences in `loans6`, `n_prior_works` and `prior_loans`.")
    P('')
    P('Library-wide low months (the benchmark rule: the total of a format below half of its median over the previous 12 months), 2017-01 onward: '
      + ', '.join(f"{m // 100}-{m % 100:02d}" for m in ll['flagged_library_months'])
      + f". The record does not exclude months for Test B, so no row was dropped or changed. `flag_months6` in the rows file counts, per work, how many of its six outcome months are such months: "
        f"**{ll['works_with_flagged_months_in_window']:,} works** ({pct(ll['works_with_flagged_months_in_window'], ll['population'])}) have at least one. "
        f"These windows (2020 closures, the 2024 outage, 2025-08) lower `loans6` for reasons unrelated to the book; the model script may want to check its results with and without them.")
    P('')
    P('## 3. Author matching (English Wikipedia and Wikidata)')
    P('')
    P(f"{ms['names']:,} distinct display names; "
      f"{int((am.plain_status == 'invalid_title').sum())} of them cannot be a page title (they contain # < > [ ] | {{ }} or are too long) and were not queried. "
      f"Wikipedia batches of 50 via `prop=pageprops&redirects=1&maxlag=5`, Wikidata `wbgetentities` (50 per call, claims). "
      f"{ms['wikidata_items']:,} Wikidata items were read. Network requests: {ms['network_requests']:,}; cache hits during that run: {ms['cache_hits']:,}; back-offs: {ms['backoffs']}.")
    P('')
    n = ms['names']
    hum = int(am.is_human.sum())
    wt = int(am.writer_type.sum())
    P(f"**By distinct name:** matched to a human article **{hum:,} of {n:,} ({pct(hum, n)})**; with a writer occupation **{wt:,} ({pct(wt, n)} of all names, {pct(wt, hum)} of the matches)**.")
    P('')
    meth = am.method.value_counts()
    P('Which title was accepted: ' + '; '.join(f"{k} {int(v):,}" for k, v in meth.items() if k != 'none') + f'; no title accepted {int(meth.get("none", 0)):,}.')
    ps = am.plain_status.value_counts()
    P('')
    P('Status of the plain-name title for all names: ' + '; '.join(f"{k} {int(v):,}" for k, v in ps.items()) + '. '
      '("human" = accepted at once; "missing" = no page; "disambiguation"; "not_human" = page exists but its Wikidata item is not P31 = Q5; "no_item" = page without a Wikidata item.)')
    P('')
    r = rows
    t = r.groupby('test_year').agg(works=('work_id', 'size'), matched=('matched', 'sum'), writer=('writer_type', 'sum')).reset_index()
    t['works matched, any human'] = [f"{int(a):,} ({pct(a, b)})" for a, b in zip(t.matched, t.works)]
    t['works matched, writer_type'] = [f"{int(a):,} ({pct(a, b)})" for a, b in zip(t.writer, t.works)]
    nm = am.merge(pd.read_parquet(OUT / 'test_b_population.parquet', columns=['display_name', 'test_year']).drop_duplicates(), on='display_name')
    ty = nm.groupby('test_year').agg(names=('display_name', 'nunique'), names_h=('is_human', 'sum'), names_w=('writer_type', 'sum')).reset_index()
    t = t.merge(ty, on='test_year')
    t['names matched'] = [f"{int(a):,} / {int(b):,} ({pct(a, b)})" for a, b in zip(t.names_h, t.names)]
    tot = pd.DataFrame([dict(test_year='all', works=len(r), **{'works matched, any human': f"{int(r.matched.sum()):,} ({pct(r.matched.sum(), len(r))})",
                                                              'works matched, writer_type': f"{int(r.writer_type.sum()):,} ({pct(r.writer_type.sum(), len(r))})",
                                                              'names matched': f"{hum:,} / {n:,} ({pct(hum, n)})"})])
    t['works'] = t.works.map('{:,}'.format)
    tot['works'] = tot.works.map('{:,}'.format)
    P('**By work and year** (a work counts when its first author matched; a name that appears in several years counts in each):')
    P('')
    P(md_table(pd.concat([t[['test_year', 'works', 'works matched, any human', 'works matched, writer_type', 'names matched']], tot], ignore_index=True)))
    P('')
    P('## 4. Monthly views')
    P('')
    vl = views_log_summary()
    P(f"Accepted articles (distinct titles after redirects): {vs['titles']:,}. REST per-article monthly, all-access, user agents, 2015-07 to 2026-09. "
      f"**Titles with views data: {vs['titles_with_views']:,}**; titles with a 404 (no views at all, nothing stored): **{vs['titles_404']:,}**; "
      f"rejected with status 400: {vs['titles_400']}. {vs['rows']:,} title-month rows.")
    P('')
    P(f"Download behaviour. The job was started and restarted {vl['runs']} times while the request rate was tuned (every finished title stays in the cache, none is fetched twice). "
      f"Settings of the runs: " + '; '.join(f"`{a or 'defaults (6 threads, 0.11 s gap)'}`" for a in vl['args']) + '. '
      f"At about 150 requests per second (24 threads) and again at 8 per second the Wikimedia gateway answered 429 (header x-envoy-ratelimited, Retry-After 6 to 7 s) and the rate fell to 1 to 2 per second; "
      f"a run at 0.30 s gap with 4 threads (3.3 per second) drew almost none. Counts from the logs: {vl['network']:,} requests logged, response codes {vl['codes']}, "
      f"{vl['episodes']} separate slow-down episodes after a 429 (lower bounds for the runs that were stopped by hand, as the counters are printed every 500 titles). "
      f"All 429s were honoured with the server's Retry-After pause and nothing was lost. The last run (gap 0.30 s, 4 threads, slow-down after a 429 and recovery after a run of successes) "
      f"made {vs['network_requests']:,} requests, {vs['cache_hits']:,} answered from the cache, {vs['backoffs']} back-off.")
    P('')
    P('## 5. Rows')
    P('')
    P(f"`data/db/wiki_led/test_b_rows.parquet`: **{rs['rows']:,} rows**, one per work. Wikipedia features use only months strictly before `first_ym` (the 12 months ending the month before). Recomputed independently from the long views file for {ck['wikipedia_checked']} rows (`06_checks.py`): {ck['wikipedia_mismatches']} differences; unmatched rows with a non-zero Wikipedia feature: {ck['unmatched_rows_with_nonzero_wikipedia_feature']}; matched rows without a title: {ck['matched_rows_without_title']}. "
      f"`matched` = 1 for {rs['matched']:,} rows ({pct(rs['matched'], rs['rows'])}), of which {rs['writer_type']:,} are writer_type. "
      f"**Rows with matched = 1 and v6 > 0: {rs['matched_nonzero_v6']:,}** ({pct(rs['matched_nonzero_v6'], rs['matched'])} of the matched rows, {pct(rs['matched_nonzero_v6'], rs['rows'])} of all rows). "
      f"Matched rows whose title had no views data at all: {rs['matched_no_views_data']:,} (they get 0 views).")
    P('')
    z = r[r.matched == 1].groupby('test_year').agg(matched=('work_id', 'size'), v6pos=('v6', lambda s: int((s > 0).sum()))).reset_index()
    z['matched, v6 > 0'] = [f"{int(a):,} ({pct(a, b)})" for a, b in zip(z.v6pos, z.matched)]
    z['matched'] = z.matched.map('{:,}'.format)
    P(md_table(z[['test_year', 'matched', 'matched, v6 > 0']]))
    P('')
    P('Columns: work_id, creator_key, display_name, first_ym, test_year, Y6, loans6, top10 (Y6 at or above the 90th percentile of Y6 among works of the same first-month year; share by year '
      + ', '.join(f"{y} {100 * v:.1f}%" for y, v in rs['top10_share_by_year'].items())
      + '), fmt_print / fmt_ebook / fmt_audiobook (format available in the first month), n_prior_works, ln_prior_loans, month, matched, v6, v12, trend, vmax, writer_type, enwiki_title, qid, flag_months6, titles_with_no_views_data. '
        'The columns `top10`, `enwiki_title`, `qid`, `flag_months6` and `titles_with_no_views_data` are additions for checking; the model code should use only the columns the record lists.')
    P('')
    P('## 6. Things worth knowing')
    P('')
    g = r[r.matched == 1].groupby('enwiki_title').agg(works=('work_id', 'size'), names=('display_name', 'nunique'), keys=('creator_key', 'nunique')).reset_index()
    top = g.sort_values('works', ascending=False).head(12)
    P(f"- **Same person matched from several names.** {int((g.names > 1).sum()):,} article titles are reached from more than one display name "
      f"(for example spelling variants or a pseudonym redirect), so author clusters in the bootstrap should use `creator_key` (as planned) or the article title, not the name. "
      f"The 12 articles with the most works: " + '; '.join(f"{a} ({int(b):,} works, {int(c)} name{'s' if c > 1 else ''})" for a, b, c in zip(top.enwiki_title, top.works, top.names)) + '.')
    big = g.sort_values('works', ascending=False)
    P(f"- Share of the matched works that belong to the 100 most frequent articles: {pct(big.works.head(100).sum(), big.works.sum())}; to the 1,000 most frequent: {pct(big.works.head(1000).sum(), big.works.sum())}.")
    # humans without writer type
    h = am[am.is_human & ~am.writer_type]
    cnt = pd.Series([o for occ in h.occupations for o in occ]).value_counts().head(12)
    lab = labels(list(cnt.index)) if len(cnt) else {}
    P(f"- **writer_type counts only the 14 occupation items named in the build instructions (the record's 'memoirist' is taken as Q18814623, autobiographer), with no subclasses**, so a person whose only occupation is a subtype "
      f"(for example comics writer or manga artist) is a human match without writer_type. {len(h):,} matched names ({pct(len(h), hum)}) have no writer_type; "
      f"{int((h.occupations.map(len) == 0).sum()):,} of them have no occupation at all. The most common occupations among them: "
      + '; '.join(f"{lab.get(q, '?')} ({q}) {int(c):,}" for q, c in cnt.items()) + '.')
    big_names = am[am.is_human].sort_values('n_works', ascending=False).head(10)
    P(f"- Names with the most works that matched (a quick look for wrong-person matches; not checked by hand): "
      + '; '.join(f"{a} -> {b} ({int(c)})" for a, b, c in zip(big_names.display_name, big_names.enwiki_title, big_names.n_works)) + '.')
    hv = r[r.matched == 1].groupby('enwiki_title').agg(v6max=('v6', 'max'), works=('work_id', 'size'), wt=('writer_type', 'max')).sort_values('v6max', ascending=False).head(10)
    P(f"- Matched articles with the highest v6 (a look for namesakes of very famous people; not checked by hand): "
      + '; '.join(f"{a} (v6 up to {b:.1f}, {int(c)} work{'s' if c > 1 else ''}{'' if w else ', no writer occupation'})" for a, b, c, w in zip(hv.index, hv.v6max, hv.works, hv.wt)) + '.')
    big_nw = am[am.is_human & ~am.writer_type].sort_values('n_works', ascending=False).head(12)
    lab2 = labels(sorted({q for o in big_nw.occupations for q in o}))
    P("- Matched names with the most works but **no writer_type** (occupations in brackets, from Wikidata; not checked by hand). Some are plainly the right person whose occupation item is "
      "outside the list of 14 (for example comics writer or manga artist), others look like namesakes (an actor, a footballer): "
      + '; '.join(f"{a} -> {b} ({int(c)} works; {', '.join(lab2.get(q, q) for q in o[:4]) or 'no occupation'})"
                  for a, b, c, o in zip(big_nw.display_name, big_nw.enwiki_title, big_nw.n_works, big_nw.occupations)) + '.')
    mk = am[am.is_human & ~am.writer_type & am.occupations.map(lambda o: 'Q191633' in o)]
    P(f"- Manga artists (Wikidata Q191633) without any listed writer occupation: {len(mk):,} matched names, {int(mk.n_works.sum()):,} works. They are correct matches that get writer_type = 0 under the 14-item list.")
    big_none = am[~am.is_human].sort_values('n_works', ascending=False).head(10)
    P(f"- Names with the most works that did NOT match: " + '; '.join(f"{a} ({int(c)}; plain title {s})" for a, c, s in zip(big_none.display_name, big_none.n_works, big_none.plain_status)) + '.')
    P(f"- Works whose creator string holds more than one author are matched on the first author only, as in the record. Organisations and corporate authors are not excluded; "
      f"a few can match a human by chance (for example a name shared with a person).")
    P("- **Views are those of the article title after redirects, as the record says.** The REST API counts a visit under the title that was requested, so traffic that "
      "arrives through a redirect (a pseudonym such as the pen name that redirects to a real name, or the old title of a page that was later moved) is not in the target's series. "
      "Such authors' views are understated. This is not corrected; it is one more source of noise in W.")
    P(f"- Wikidata items read: {len(wi):,}; missing items: {int(wi.missing.sum())}; items that were human: {int(wi.is_human.sum()):,}.")
    P('')
    P('## 7. Runtime')
    P('')
    def span(name):
        import re
        lines = (REP / name).read_text().splitlines()
        starts = [l for l in lines if l.startswith('=== start')]
        t0 = re.search(r'(\d\d:\d\d:\d\d)', starts[0]).group(1)
        ts = [re.match(r'(\d\d:\d\d:\d\d) ', l) for l in lines]
        t1 = [m.group(1) for m in ts if m][-1]
        hh = lambda t: sum(int(v) * k for v, k in zip(t.split(':'), (3600, 60, 1)))
        return t0, t1, hh(t1) - hh(t0)
    m0, m1, md = span('wiki_led_match.log')
    v0, v1, vd = span('wiki_led_views.log')
    P(f"All on 20 Oct 2026, one long download at a time, `nice -n 10`. Population and loans/library features: {ll['runtime_s']} s for the loans script (the population script takes about 1 s). "
      f"Author matching (`02_author_match.py`, detached with `jobs/bg.sh wiki_led_match`): {m0} to {m1}, {md // 60} min, {ms['network_requests']:,} requests to the Action API and Wikidata "
      f"(sequential, at most 5 per second, `maxlag=5`, {ms['backoffs']} back-offs). "
      f"Views download (`03_author_views.py`, `jobs/bg.sh wiki_led_views`): {v0} to {v1}, {vd // 3600} h {vd % 3600 // 60} min of wall clock including the rate tuning and restarts described in section 4; "
      f"the last, steady run needed {vs['runtime_s'] // 60} min. Rows {rs['runtime_s']} s, checks {7} s, report 2 s. "
      f"From the first script to the last: 15:11 to 19:00 (about 3 h 50 min), almost all of it waiting for the APIs. Everything fetched is cached under `data/interim/wiki_led_cache/`, so a rerun of the chain should take minutes rather than hours (not timed).")
    (REP / 'wiki_led_test_b_data.md').write_text('\n'.join(L) + '\n')
    log('wrote', REP / 'wiki_led_test_b_data.md')


if __name__ == '__main__':
    main()
