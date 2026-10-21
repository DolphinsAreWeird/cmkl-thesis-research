# Test F (AI matchmaking): data for the sorters and the judge

Khant Phyo Wai, student ID 01323050.

Written 2026-10-21 02:43 by code/main_study/wiki_led/testF/06_report.py. Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json. This step prepares data only: no page or book has been sorted, and no loan figure was related to anything. The only use of loans is the choice of the 20,000 books by their checkout totals, as the addendum says (a disclosed look-ahead); no loan figure is written to any Test F file.

## Pages

- Source: the English Wikipedia daily top 500, 3,915 days from 20160101 to 20260930 (data/raw/wiki_top_daily.json), 141,460 titles.
- After the namespace rule of the addendum (Main_Page, Special:, Wikipedia:, Portal:, File:, Help:, Template:, Category:, User:, Talk:, Book:, Draft:, Module:, each used as a prefix): 139,161 titles. On 2 days or more: 84,577 (the page universe, as the addendum expects). On exactly 1 day: 54,584, of which a fixed random 3,000 (seed 20261021) are prepared for the coverage check only.

### Universe (84,577 pages)

| | pages | share |
|---|---:|---:|
| short description and first sentence | 80,218 | 94.8% |
| short description only | 55 | 0.1% |
| first sentence only | 4,018 | 4.8% |
| neither (sorted on the title alone, flagged) | 286 | 0.3% |
| with a short description (any) | 80,273 | 94.9% |
| with a first sentence (any) | 84,236 | 99.6% |
| title is now a redirect | 8,888 | 10.5% |
| page no longer exists (missing) | 239 | 0.3% |
| title not valid for the API | 1 | 0.0% |
| page outside the article namespace (for example User talk) | 10 | 0.0% |
| disambiguation page (by its short description) | 715 | 0.8% |
| first sentence cut at 300 characters | 2,755 | 3.3% |
| first sentence ends in an abbreviation (probably cut early by the API) | 3,065 | 3.6% |
| the same, with no short description either | 23 | 0.0% |

### One-day sample (3,000 pages)

| | pages | share |
|---|---:|---:|
| short description and first sentence | 2,803 | 93.4% |
| short description only | 2 | 0.1% |
| first sentence only | 178 | 5.9% |
| neither (sorted on the title alone, flagged) | 17 | 0.6% |
| with a short description (any) | 2,805 | 93.5% |
| with a first sentence (any) | 2,981 | 99.4% |
| title is now a redirect | 336 | 11.2% |
| page no longer exists (missing) | 15 | 0.5% |
| title not valid for the API | 1 | 0.0% |
| page outside the article namespace (for example User talk) | 2 | 0.1% |
| disambiguation page (by its short description) | 37 | 1.2% |
| first sentence cut at 300 characters | 88 | 2.9% |
| first sentence ends in an abbreviation (probably cut early by the API) | 97 | 3.2% |
| the same, with no short description either | 4 | 0.1% |

- In the universe, 3,294 final pages are reached by more than one title (7,032 titles, for example an old and a new name of a moved page). They stay separate items, because each title has its own view counts; their text is the same.
- The namespace rule keeps some titles that are not articles: 10 pages outside the article namespace (for example User talk or Wikipedia talk pages) and 2 titles that lead to the Main Page (Main_page, main_page). They are in the chunks like any page.
- Titles the API does not accept as page names: Special%3ASearch (universe), Iran�Contra_affair (sample1day); they are sorted on the title alone (an encoded special-page name that the prefix rule does not catch, and a title with a broken character).
- The title shown to the sorter is the title of the top-500 list with spaces for underscores. The final title after redirects (and the section a redirect points to) is recorded in key.tsv (where the title is kept with underscores, as in the top-500 list) and pages.parquet. The short description and the first sentence are those of the page the title leads to today.
- Known limits of the text: the API's sentence splitter stops at some abbreviations (for example "UFC on Fox: Jacaré vs.", "Edward Nathan George Jr." or just "St." for St. Louis), counted in the tables above; nearly all of these pages have a short description, which carries the subject. Removed pronunciation guides leave empty brackets ("Cloture (, also UK: ), closure ..."). The text is used as the API gives it, with the settings of the addendum.
- The three pages named as examples in the page instructions, and every title that leads to the same pages, are flagged (prompt_example) and left out of the reliability and judge sets: Ocean's 8, The Bear (TV series), Adolescence (TV series), Ocean's Eight. They stay in the chunks, so their theme series are complete.

### Fetch

- Wikipedia Action API (en.wikipedia.org/w/api.php), prop=pageprops|extracts with ppprop=wikibase-shortdesc, exintro, explaintext, exsentences=1, redirects=1, maxlag=5, batches of at most 20 titles: 4,379 batches, 4,379 requests (4,379 over the network, 0 from the cache).
- Rate: one shared limiter of 0.34 s between requests over 2 threads (at most about 2.9 a second), the project user agent, Retry-After honoured. Back-offs: 0; status codes: 200: 4,379; answers with API warnings: 0.
- Runtime: 33.6 minutes (2026-10-21 02:07:30 to 2026-10-21 02:41:06). Every answer is cached in data/interim/testF_cache, so a rerun reads the same answers.

## Theme guide

- prereg/addenda_wiki_led/2026-10-21_g_theme_guide.tsv: 242 narrow themes (level 3 of data/db/taxonomy_v3/theme_nodes.parquet), columns code, theme, broader group, broadest group, example subject headings (up to 8 member terms in stored order, from values_v3). Rows sorted by code. The file is read-only.
- Labels: the stored labels. The middle and broad labels are hand-written and kept as they are. The narrow labels are mostly two member terms in lower case; only letter case was changed to make them readable (first letter, proper names and abbreviations: for example "world war ii / world war i" became "World War II / World War I", "hiv aids" became "HIV/AIDS"). No word was added, removed or changed. Member terms are exactly as stored.
- SHA-256: `d663a20137edc65dfee0f3fff3236904841a57ad3109ec03f360c2746988df50` (to be entered in prereg/README.md before any sorting).

## Books

- The 20,000 Seattle works with the most checkouts (checkouts_total in data/db/taxonomy_v3/spl_works.parquet): cut-off 955 checkouts. 19,980 works are above it and 39 share it; 20 of those were taken, by the lower work_id.

| text part | books | share |
|---|---:|---:|
| title | 20,000 | 100.0% |
| author (creator) | 19,788 | 98.9% |
| librarian subject headings (up to 10, largest share first) | 19,125 | 95.6% |
| digital subject tags (up to 10, largest share first) | 16,722 | 83.6% |
| linked to Goodreads (tier A 6,111, tier B 47) | 6,158 | 30.8% |
| Goodreads description (first 300 characters) | 5,952 | 29.8% |
| none of headings, tags or description (title and author only) | 47 | 0.2% |

- Median shown per book: 6 headings, 3 tags. 5,569 descriptions were longer than 300 characters and were cut. Goodreads descriptions had HTML entities decoded and tags removed before the cut.

## Chunk files and sets (data/db/wiki_led/testF/)

Tab-separated, UTF-8, one header line, one item per line, no tabs or line breaks inside a field; each file was read back and checked. Ids follow a fixed random order (seed 20261021): pages p00001 to p87577, books b00001 to b20000.

| files | items | columns |
|---|---:|---|
| pages_chunk_01.tsv to pages_chunk_34.tsv (34 files) | 84,577 | id, title, description, first_sentence |
| pages_sample1day_chunk_01.tsv to pages_sample1day_chunk_02.tsv (2 files) | 3,000 | same as pages |
| books_chunk_01.tsv to books_chunk_08.tsv (8 files) | 20,000 | id, title, author, headings, tags, description |
| rel_pages.tsv | 1,000 | same as pages |
| rel_books.tsv | 500 | same as books |
| judge_pages.tsv | 400 | same as pages |

- key.tsv maps every id to its set, chunk file, title, final title (pages) and work_id (books). pages.parquet and books.parquet hold every flag; manifest.json lists every file with its rows and SHA-256.
- Reliability sets (seed 20261022): 1,000 universe pages (the prompt examples left out) and 500 books, drawn at random, rows in the order drawn, with the same ids as in the chunks.
- Judge set for check G1 (seed 20261023): 100 hard cases and 300 pages drawn at random from the universe, then put in a random order; judge_set_info.csv says why each page is in the set (the judge sees only judge_pages.tsv).
  - Candidates in the universe: 95 pages of review_title_confusion.csv (the same-named pages of its evidence and the pages named in the reason of a title-confusion verdict; 6 are tied to a title-confusion verdict); 731 adaptation pages (668 whose title is an article of adaptations.parquet and 63 whose title now redirects to one); 11,756 pages where the stored embedding routing (top_routing/routes.parquet, cosine 0.70 or more) and zero-shot routing (stage2/nli_routing/pairs.parquet, probability 0.50 or more) disagree: 400 routed by both to unrelated themes, 257 by the embedding only, 11,099 by the zero-shot classifier only (2,847 pages routed by both to the same or a related theme are not candidates).
  - Drawn: A review (same-named page): 28; A review (title-confusion verdict): 6; B adaptation: 33; C routing disagreement (embedding only): 11; C routing disagreement (unrelated themes): 11; C routing disagreement (zero-shot only): 11; random: 300. The concept pages of the review (the themes' own pages, for example Mathematics) were not used as hard cases; they can enter through the random part like any page.
  - Over all 400 pages: 35 are review pages, 34 are adaptation pages, and the routing disagreements are 12 routed by the embedding only, 13 routed by both to unrelated themes, 75 routed by the zero-shot classifier only (a page can be in more than one group).

## Ready for the next step

- The theme guide is written and read-only, ready to be fingerprinted in prereg/README.md before any sorting.
- The sorters can start from the chunk files: 34 page chunks, 2 one-day chunks, 8 book chunks, plus the two reliability files; the judge reads judge_pages.tsv.
- Size: a full page chunk is about 0.53 MB (roughly 134 thousand tokens at 4 bytes a token) and a book chunk about 0.86 MB (roughly 215 thousand tokens), so a sorter will need to read its chunk in parts; the theme guide adds about 52 KB.
