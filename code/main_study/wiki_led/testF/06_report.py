#!/usr/bin/env python3
"""Test F data, step 6: the data report, data/reports/testF_data.md (counts only; no loans, no sorting, no result).
Inputs: the summaries and tables written by steps 1 to 5 in data/db/wiki_led/testF/ and the theme guide.
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/06_report.py
"""
import sys, re, json, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
import _testf_common as F

# a first sentence that ends in a common abbreviation, an initial or a dotted abbreviation was probably cut early by the API's sentence
# splitter ("Edward Nathan George Jr.", "UFC 232: Jones vs.", "St."); some of these are true ends ("published by Warner Bros.")
ABBR_END = re.compile(r'(?:\b(?:Jr|Sr|St|Ste|vs|Dr|Mr|Mrs|Ms|Mt|Ft|No|Nos|Inc|Ltd|Co|Corp|Bros|Gen|Col|Lt|Sgt|Capt|Cpt|Rev|Prof|Gov|Sen|Rep|'
                      r'Pres|Hon|ca|c|approx|feat|ft|Vol|vol|Op|op|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|Ave|Blvd|Rd|est|b|d|fl|r)\.'
                      r'|\b[A-Z]\.|\b(?:[A-Za-z]\.){2,})$')


def pct(a, b):
    return f'{100 * a / b:.1f}%' if b else 'n/a'


def main():
    us = json.load(open(F.OUT / 'universe_summary.json'))
    ts = json.load(open(F.OUT / 'page_text_summary.json'))
    bs = json.load(open(F.OUT / 'books_summary.json'))
    man = json.load(open(F.OUT / 'manifest.json'))
    ms = man['summary']
    P = pd.read_parquet(F.OUT / 'pages.parquet')
    B = pd.read_parquet(F.OUT / 'books.parquet')
    guide_rows = F.read_tsv(F.GUIDE)
    L = []
    add = L.append
    add('# Test F (AI matchmaking): data for the sorters and the judge')
    add('')
    add('Khant Phyo Wai, student ID 01323050.')
    add('')
    add(f'Written {time.strftime("%Y-%m-%d %H:%M")} by code/main_study/wiki_led/testF/06_report.py. Settings: '
        'prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json. This step prepares data only: no page or book has been sorted, and no '
        'loan figure was related to anything. The only use of loans is the choice of the 20,000 books by their checkout totals, as the '
        'addendum says (a disclosed look-ahead); no loan figure is written to any Test F file.')
    add('')

    # ---------------- pages
    add('## Pages')
    add('')
    add(f'- Source: the English Wikipedia daily top 500, {us["n_days"]:,} days from {us["first_day"]} to {us["last_day"]} '
        f'(data/raw/wiki_top_daily.json), {us["n_titles_all"]:,} titles.')
    add(f'- After the namespace rule of the addendum (Main_Page, Special:, Wikipedia:, Portal:, File:, Help:, Template:, Category:, User:, '
        f'Talk:, Book:, Draft:, Module:, each used as a prefix): {us["n_titles_after_namespace_rule"]:,} titles. On 2 days or more: '
        f'{us["n_universe"]:,} (the page universe, as the addendum expects). On exactly 1 day: {us["n_one_day"]:,}, of which a fixed random '
        f'{us["n_sample1day"]:,} (seed 20261021) are prepared for the coverage check only.')
    for name, s in (('Universe', P[P.set == 'universe']), ('One-day sample', P[P.set == 'sample1day'])):
        n = len(s)
        tk = s.text_kind.value_counts()
        st = s.status.value_counts()
        add('')
        add(f'### {name} ({n:,} pages)')
        add('')
        add('| | pages | share |')
        add('|---|---:|---:|')
        for k, lab in (('both', 'short description and first sentence'), ('description_only', 'short description only'),
                       ('sentence_only', 'first sentence only'), ('title_only', 'neither (sorted on the title alone, flagged)')):
            add(f'| {lab} | {int(tk.get(k, 0)):,} | {pct(tk.get(k, 0), n)} |')
        add(f'| with a short description (any) | {int((s.description != "").sum()):,} | {pct((s.description != "").sum(), n)} |')
        add(f'| with a first sentence (any) | {int((s.first_sentence != "").sum()):,} | {pct((s.first_sentence != "").sum(), n)} |')
        add(f'| title is now a redirect | {int(s.is_redirect.sum()):,} | {pct(s.is_redirect.sum(), n)} |')
        add(f'| page no longer exists (missing) | {int(st.get("missing", 0)):,} | {pct(st.get("missing", 0), n)} |')
        add(f'| title not valid for the API | {int(st.get("invalid", 0)):,} | {pct(st.get("invalid", 0), n)} |')
        other = int(n - st.get('page', 0) - st.get('missing', 0) - st.get('invalid', 0))
        if other:
            add(f'| no answer for the title (unresolved or interwiki) | {other:,} | {pct(other, n)} |')
        add(f'| page outside the article namespace (for example User talk) | {int(((s.ns != 0) & (s.status == "page")).sum()):,} | '
            f'{pct(((s.ns != 0) & (s.status == "page")).sum(), n)} |')
        add(f'| disambiguation page (by its short description) | {int(s.disambiguation_like.sum()):,} | {pct(s.disambiguation_like.sum(), n)} |')
        add(f'| first sentence cut at 300 characters | {int(s.first_sentence_cut.sum()):,} | {pct(s.first_sentence_cut.sum(), n)} |')
        ab = (s.first_sentence != '') & s.first_sentence.str.contains(ABBR_END)
        add(f'| first sentence ends in an abbreviation (probably cut early by the API) | {int(ab.sum()):,} | {pct(ab.sum(), n)} |')
        add(f'| the same, with no short description either | {int((ab & (s.description == "")).sum()):,} | '
            f'{pct((ab & (s.description == "")).sum(), n)} |')
    u = P[(P.set == 'universe') & (P.status == 'page')]
    shared = u.groupby('final_title').size()
    shared = shared[shared > 1]
    nonart = u[u.ns != 0]
    mainp = u[(u.ns == 0) & (u.final_title == 'Main Page')]
    add('')
    add(f'- In the universe, {len(shared):,} final pages are reached by more than one title ({int(shared.sum()):,} titles, for example an old '
        'and a new name of a moved page). They stay separate items, because each title has its own view counts; their text is the same.')
    add(f'- The namespace rule keeps some titles that are not articles: {len(nonart)} pages outside the article namespace (for example '
        f'User talk or Wikipedia talk pages) and {len(mainp)} titles that lead to the Main Page ({", ".join(mainp.title)}). They are in the '
        'chunks like any page.')
    inv = P[P.status == 'invalid']
    if len(inv):
        add(f'- Titles the API does not accept as page names: {", ".join(f"{t} ({s})" for t, s in zip(inv.title, inv.set))}; they are '
            'sorted on the title alone (an encoded special-page name that the prefix rule does not catch, and a title with a broken character).')
    add('- The title shown to the sorter is the title of the top-500 list with spaces for underscores. The final title after redirects '
        '(and the section a redirect points to) is recorded in key.tsv (where the title is kept with underscores, as in the top-500 list) '
        'and pages.parquet. The short description and the first sentence are those of the page the title leads to today.')
    add('- Known limits of the text: the API\'s sentence splitter stops at some abbreviations (for example "UFC on Fox: Jacaré vs.", '
        '"Edward Nathan George Jr." or just "St." for St. Louis), counted in the tables above; nearly all of these pages have a short '
        'description, which carries the subject. Removed pronunciation guides leave empty brackets ("Cloture (, also UK: ), closure ..."). '
        'The text is used as the API gives it, with the settings of the addendum.')
    add(f'- The three pages named as examples in the page instructions, and every title that leads to the same pages, are flagged '
        f'(prompt_example) and left out of the reliability and judge sets: {", ".join(t.replace("_", " ") for t in ms["prompt_example_titles"])}. '
        'They stay in the chunks, so their theme series are complete.')
    add('')
    add('### Fetch')
    add('')
    add(f'- Wikipedia Action API (en.wikipedia.org/w/api.php), prop=pageprops|extracts with ppprop=wikibase-shortdesc, exintro, explaintext, '
        f'exsentences=1, redirects=1, maxlag=5, batches of at most 20 titles: {ts["batches"]:,} batches, {ts["requests"]:,} requests '
        f'({ts["network_requests"]:,} over the network, {ts["cached_requests"]:,} from the cache).')
    add(f'- Rate: one shared limiter of {ts["gap_seconds"]} s between requests over {ts["threads"]} threads (at most about 2.9 a second), '
        f'the project user agent, Retry-After honoured. Back-offs: {ts["backoffs"]}; status codes: '
        f'{", ".join(f"{k}: {v:,}" for k, v in ts["status_codes"].items())}; answers with API warnings: {ts["warnings"]["n"]}.')
    add(f'- Runtime: {ts["seconds"] / 60:.1f} minutes ({ts["started"]} to {ts["finished"]}). Every answer is cached in '
        'data/interim/testF_cache, so a rerun reads the same answers.')
    add('')

    # ---------------- theme guide
    add('## Theme guide')
    add('')
    add(f'- prereg/addenda_wiki_led/2026-10-21_g_theme_guide.tsv: {len(guide_rows) - 1} narrow themes (level 3 of '
        'data/db/taxonomy_v3/theme_nodes.parquet), columns code, theme, broader group, broadest group, example subject headings (up to 8 '
        'member terms in stored order, from values_v3). Rows sorted by code. The file is read-only.')
    add('- Labels: the stored labels. The middle and broad labels are hand-written and kept as they are. The narrow labels are mostly two '
        'member terms in lower case; only letter case was changed to make them readable (first letter, proper names and abbreviations: '
        'for example "world war ii / world war i" became "World War II / World War I", "hiv aids" became "HIV/AIDS"). No word was '
        'added, removed or changed. Member terms are exactly as stored.')
    add(f'- SHA-256: `{F.sha256(F.GUIDE)}` (to be entered in prereg/README.md before any sorting).')
    add('')

    # ---------------- books
    n = bs['books']
    add('## Books')
    add('')
    add(f'- The {n:,} Seattle works with the most checkouts (checkouts_total in data/db/taxonomy_v3/spl_works.parquet): cut-off '
        f'{bs["cutoff_checkouts"]} checkouts. {bs["works_above_cutoff"]:,} works are above it and {bs["works_at_cutoff"]} share it; '
        f'{bs["taken_at_cutoff"]} of those were taken, by the lower work_id.')
    add('')
    add('| text part | books | share |')
    add('|---|---:|---:|')
    add(f'| title | {n:,} | 100.0% |')
    add(f'| author (creator) | {bs["with_author"]:,} | {pct(bs["with_author"], n)} |')
    add(f'| librarian subject headings (up to 10, largest share first) | {bs["with_headings"]:,} | {pct(bs["with_headings"], n)} |')
    add(f'| digital subject tags (up to 10, largest share first) | {bs["with_tags"]:,} | {pct(bs["with_tags"], n)} |')
    add(f'| linked to Goodreads (tier A {bs["goodreads_tier"].get("A", 0):,}, tier B {bs["goodreads_tier"].get("B", 0):,}) | '
        f'{bs["with_goodreads_link"]:,} | {pct(bs["with_goodreads_link"], n)} |')
    add(f'| Goodreads description (first 300 characters) | {bs["with_description"]:,} | {pct(bs["with_description"], n)} |')
    add(f'| none of headings, tags or description (title and author only) | {bs["with_no_headings_tags_or_description"]:,} | '
        f'{pct(bs["with_no_headings_tags_or_description"], n)} |')
    add('')
    add(f'- Median shown per book: {bs["headings_shown_median"]:.0f} headings, {bs["tags_shown_median"]:.0f} tags. '
        f'{bs["description_cut_at_300"]:,} descriptions were longer than 300 characters and were cut. Goodreads descriptions had HTML '
        'entities decoded and tags removed before the cut.')
    add('')

    # ---------------- chunks and sets
    cf = ms['chunk_files']
    def files_of(prefix):
        ks = sorted(k for k in cf if k.startswith(prefix + '_chunk_'))
        return ks, sum(cf[k] for k in ks)
    add('## Chunk files and sets (data/db/wiki_led/testF/)')
    add('')
    add('Tab-separated, UTF-8, one header line, one item per line, no tabs or line breaks inside a field; each file was read back and '
        'checked. Ids follow a fixed random order (seed 20261021): pages p00001 to p87577, books b00001 to b20000.')
    add('')
    add('| files | items | columns |')
    add('|---|---:|---|')
    for prefix, cols in (('pages', 'id, title, description, first_sentence'), ('pages_sample1day', 'same as pages'),
                         ('books', 'id, title, author, headings, tags, description')):
        ks, tot = files_of(prefix)
        add(f'| {ks[0]} to {ks[-1]} ({len(ks)} files) | {tot:,} | {cols} |')
    add(f'| rel_pages.tsv | {ms["rel_pages"]:,} | same as pages |')
    add(f'| rel_books.tsv | {ms["rel_books"]:,} | same as books |')
    add(f'| judge_pages.tsv | {ms["judge_hard"] + ms["judge_random"]:,} | same as pages |')
    add('')
    add('- key.tsv maps every id to its set, chunk file, title, final title (pages) and work_id (books). pages.parquet and books.parquet '
        'hold every flag; manifest.json lists every file with its rows and SHA-256.')
    add('- Reliability sets (seed 20261022): 1,000 universe pages (the prompt examples left out) and 500 books, drawn at random, rows in the '
        'order drawn, with the same ids as in the chunks.')
    hc = ms['hard_candidates']
    add(f'- Judge set for check G1 (seed 20261023): {ms["judge_hard"]} hard cases and {ms["judge_random"]} pages drawn at random from the '
        'universe, then put in a random order; judge_set_info.csv says why each page is in the set (the judge sees only judge_pages.tsv).')
    add(f'  - Candidates in the universe: {hc["review"]} pages of review_title_confusion.csv (the same-named pages of its evidence and the '
        f'pages named in the reason of a title-confusion verdict; {hc["review_title_confusion"]} are tied to a title-confusion verdict); '
        f'{hc["adaptation"]} adaptation pages ({hc["adaptation_by_own_title"]} whose title is an article of adaptations.parquet and '
        f'{hc["adaptation_through_redirect"]} whose title now redirects to one); '
        f'{hc["routing_disagreement"]:,} pages where the stored embedding routing (top_routing/routes.parquet, cosine 0.70 or more) and '
        f'zero-shot routing (stage2/nli_routing/pairs.parquet, probability 0.50 or more) disagree: '
        f'{hc["routing_counts"].get("unrelated", 0)} routed by both to unrelated themes, {hc["routing_counts"].get("embedding_only", 0)} by '
        f'the embedding only, {hc["routing_counts"].get("zeroshot_only", 0):,} by the zero-shot classifier only '
        f'({hc["routing_counts"].get("agree", 0):,} pages routed by both to the same or a related theme are not candidates).')
    da = ms['judge_drawn_as']
    add('  - Drawn: ' + '; '.join(f'{k}: {v}' for k, v in sorted(da.items())) + '. The concept pages of the review (the themes\' own pages, '
        'for example Mathematics) were not used as hard cases; they can enter through the random part like any page.')
    kl = dict(unrelated='routed by both to unrelated themes', embedding_only='routed by the embedding only',
              zeroshot_only='routed by the zero-shot classifier only')
    add(f'  - Over all 400 pages: {ms["judge_in_review"]} are review pages, {ms["judge_in_adaptations"]} are adaptation pages, and the '
        'routing disagreements are ' + ', '.join(f'{v} {kl[k]}' for k, v in sorted(ms['judge_routing_disagreement'].items()))
        + ' (a page can be in more than one group).')
    add('')
    cb = ms['chunk_bytes']
    pb = [cb[k] for k in files_of('pages')[0]]
    bb = [cb[k] for k in files_of('books')[0]]
    add('## Ready for the next step')
    add('')
    add('- The theme guide is written and read-only, ready to be fingerprinted in prereg/README.md before any sorting.')
    add(f'- The sorters can start from the chunk files: {len(files_of("pages")[0])} page chunks, {len(files_of("pages_sample1day")[0])} '
        f'one-day chunks, {len(files_of("books")[0])} book chunks, plus the two reliability files; the judge reads judge_pages.tsv.')
    add(f'- Size: a full page chunk is about {max(pb) / 1e6:.2f} MB (roughly {max(pb) / 4 / 1000:.0f} thousand tokens at 4 bytes a token) and '
        f'a book chunk about {max(bb) / 1e6:.2f} MB (roughly {max(bb) / 4 / 1000:.0f} thousand tokens), so a sorter will need to read its '
        'chunk in parts; the theme guide adds about 52 KB.')
    text = '\n'.join(L) + '\n'
    assert '—' not in text, 'em dash in the report'
    (F.REP / 'testF_data.md').write_text(text)
    F.log(f'wrote {F.REP / "testF_data.md"} ({len(text):,} characters)')


if __name__ == '__main__':
    main()
