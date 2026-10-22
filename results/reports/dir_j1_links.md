# J1: book-linked Wikipedia pages of every kind, anniversaries and linked-page bursts (addendum j)

Khant Phyo Wai, 01323050. Run 22 Oct 2026 (links 2026-10-22 09:22, bursts 2026-10-22 10:11 +07). Record: `prereg/addenda_wiki_led/2026-10-22_j_combined_alerts.json` (book_links, linked_page_attention, the anniversary part of scheduled_calendar). Choices the record leaves open: J1 to J12 in the header of `code/main_study/wiki_led/dirs/j1_links.py` (downloader: `j1_download_views.py`), logged in `prereg/DEVIATIONS.md` (Addendum j). Data only: nothing here is related to loans. Files: `data/db/wiki_led/dirs/j_links/`.

**In plain words**

1. Of the 7,747 Test A works (7,510 Wikidata items), 4,644 have at least one linked Wikidata item of the record's types, 40,672 links in all, 33,990 of them to an item with an English Wikipedia article. These point to 10,283 different articles: 6,397 works (mostly other books of the same series and film or TV adaptations), 2,450 concepts or other (largely fictional characters), 603 places, 426 events or history and 407 real people.
2. Most links come from series (27,135 rows) and adaptations (4,968); the links the request was about are thinner: 1,018 event or period links (721 works with an article), 2,279 place links (1,619 works), 1,936 subject links (1,069 works) and 230 person links (121 works).
3. The "event or history" category follows the record (Wikidata class occurrence and its subclasses). Wikidata files many ideas and activities under occurrence, so beside real events (World War II, the Vietnam War, the Cultural Revolution) the category also holds pages such as Marriage, Love, Sleep and Crime. Where Test F's AI sorted the same page, its page kind is kept beside the category (column ai_kind): of the 148 event-category items the AI also sorted, it called 88 events and 54 concepts (section 2). The work category likewise holds a few companies and websites (Google, Amazon) that books are about.
4. Anniversaries (25, 50, 75, ... years) in 2015 to 2027: 3,670 of authors' births, 689 of authors' deaths and only 95 of linked events, because few linked events carry a date at month precision (114 of 452 event items).
5. Views: 10,276 of the 10,283 linked articles have daily views (2015-07 to 2026-09), 33,917 of 33,924 work-article pairs (4,530 works). All 10,283 linked articles fit under the record's cap of 30,000, so no page was left out by the cap. The download was complete when the bursts were built.

## 1. Links by type and category

Rows of `links.parquet` (one per work, link type and linked item). "Works" = works with at least one link of the type to an item with an English article. Categories by Wikidata P31 and P279* (J4): person (human), work (creative work), event (occurrence), place (geographic location), else concept_other; an item reaching several of these takes the first in that order.

| link_type | rows | with_article | works | event | person | place | work | concept_other |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adaptation | 4,968 | 3,680 | 1,473 | 10 | 0 | 5 | 4,882 | 71 |
| subject | 1,936 | 1,799 | 1,069 | 0 | 0 | 129 | 76 | 1,731 |
| event_period | 1,018 | 980 | 721 | 814 | 0 | 1 | 0 | 203 |
| person | 230 | 219 | 121 | 0 | 230 | 0 | 0 | 0 |
| place | 2,279 | 2,130 | 1,619 | 5 | 0 | 1,959 | 12 | 303 |
| character | 3,106 | 1,849 | 670 | 16 | 228 | 0 | 20 | 2,842 |
| series | 27,135 | 23,333 | 1,868 | 0 | 0 | 1 | 23,385 | 3,749 |
| all | 40,672 | 33,990 | 4,530 | 845 | 458 | 2,095 | 28,375 | 8,899 |

Left out (J3): 1 link to the book's own item and 52 links to the book's own author ({'person': 39, 'character': 13}); the author stays in Test A's W features. Wikidata properties used: subject P921 and P180; event_period P2408 and subject items of category event; person = subject items of category person; place P840; character P674; adaptation P144 (reverse) and P4969; series = the other items with P179 to a series of the book. 514 items reach more than one category root; 32 items are historical periods (column is_period).

Category order changed at 09:22, before any view or model result (logged): the first order (person, event, place, work) put 311 more articles in event, mostly operas, musicals, theatre productions and ballets based on the books, because Wikidata files these creative-work classes under occurrence too. Pages by category, first order: {'work': 6081, 'concept_other': 2450, 'event': 737, 'place': 608, 'person': 407}; now: {'work': 6397, 'concept_other': 2450, 'place': 603, 'event': 426, 'person': 407}.

## 2. What each category holds

Most common Wikidata classes (P31) among the distinct linked items of each category:

| category | items | classes |
| --- | --- | --- |
| event | 452 | academic discipline 24; social movement 17; field of work 15; calendar month of a given year 14; political ideology 11; activity 11; political movement 11; historical period 10 |
| person | 422 | human 422; human biblical figure 2 |
| place | 620 | big city 101; country 77; sovereign state 76; city 50; U.S. state 45; city in the United States 44; largest city 34; county seat 34 |
| work | 8,252 | literary work 4072; film 1880; television series 404; television film 382; dramatico-musical work 241; miniseries 239; comic book album 123; animated film 107 |
| concept_other | 3,763 | literary character 1453; fictional human 1318; film character 603; written work 500; no P31 372; television character 267; academic discipline 74; theatrical character 72 |

Test F's AI page kind for the 1,689 linked articles that were among Test F's sorted pages (distinct items; "not sorted" = not among them):

| category | event | person | place | work | concept | organization | list | other | not sorted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| event | 88 | 0 | 1 | 0 | 54 | 2 | 0 | 3 | 304 |
| person | 1 | 135 | 0 | 0 | 0 | 0 | 0 | 0 | 286 |
| place | 0 | 0 | 246 | 0 | 1 | 1 | 0 | 0 | 372 |
| work | 1 | 0 | 4 | 793 | 6 | 6 | 0 | 4 | 7,438 |
| concept_other | 4 | 11 | 12 | 14 | 151 | 19 | 0 | 132 | 3,420 |

## 3. Examples (the most borrowed works first)

- History or war events: *All the Light We Cannot See* (Anthony Doerr) -> World War II (event_period, AI: event); *The three-body problem* (Liu, Cixin) -> Cultural Revolution (event_period, AI: event); *The Sympathizer: A Novel (Pulitzer Prize for Fiction)* (Viet Thanh Nguyen) -> Vietnam War (event_period, AI: event); *Little women* (Alcott, Louisa May, 1832-1888) -> American Civil War (event_period, AI: event); *The Return of the King* (J.R.R. Tolkien) -> War of the Ring (event_period); *Fall of Giants* (Ken Follett) -> World War I (event_period, AI: event); *The Nix* (Nathan Hill) -> Opposition to United States involvement in the Vietnam War (event_period); *Tinker, Tailor, Soldier, Spy* (John le Carré) -> Cold War (event_period, AI: event).
- Other event pages (shows the breadth of occurrence): *Pride and Prejudice* (Jane Austen) -> Marriage (event_period); *Pride and Prejudice* (Jane Austen) -> Femininity (event_period); *Between the World and Me* (Ta-Nehisi Coates) -> History of the United States (event_period); *So You Want to Talk about Race* (Ijeoma Oluo) -> Racism (event_period, AI: concept); *Dune* (Frank Herbert) -> Religion (event_period); *Pachinko* (Lee, Min Jin) -> History of Korea (event_period); *Parable of the sower* (Butler, Octavia E.) -> Empathy (event_period); *Killers of the Flower Moon: The Osage Murders and the Birth of the FBI* (David Grann) -> Osage Indian murders (event_period, AI: event).
- Places where a novel is set: *Where the Crawdads Sing* (Delia Owens) -> North Carolina (place, AI: place); *Little Fires Everywhere* (Celeste Ng) -> Shaker Heights, Ohio (place); *A Gentleman in Moscow* (Amor Towles) -> Moscow (place, AI: place); *All the Light We Cannot See* (Anthony Doerr) -> France (place, AI: place); *All the Light We Cannot See* (Anthony Doerr) -> Germany (place, AI: place); *Pride and Prejudice* (Jane Austen) -> Ware, Hertfordshire (place); *Pride and Prejudice* (Jane Austen) -> Westerham (place); *Pride and Prejudice* (Jane Austen) -> Hertfordshire (place).
- Real people as subjects or characters: *Lincoln in the Bardo* (George Saunders) -> William Wallace Lincoln (person); *Lincoln in the Bardo* (George Saunders) -> Abraham Lincoln (person, AI: person); *Bad Blood: Secrets and Lies in a Silicon Valley Startup* (John Carreyrou) -> Elizabeth Holmes (person, AI: person); *Alexander Hamilton* (Ron Chernow) -> Alexander Hamilton (person, AI: person); *I'll Be Gone in the Dark: One Woman's Obsessive Search for the Golden State Killer* (Michelle McNamara) -> Joseph James DeAngelo (person, AI: person); *The Count of Monte Cristo* (Alexandre Dumas) -> Ali Pasha of Yanina (character); *The Tattooist of Auschwitz* (Heather Morris) -> Lale Sokolov (person, AI: person); *Say Nothing: A True Story of Murder and Memory in Northern Ireland* (Patrick Radden Keefe) -> Dolours Price (person, AI: person).
- Adaptations: *Where the Crawdads Sing* (Delia Owens) -> Where the Crawdads Sing (film) (adaptation, AI: work); *Little Fires Everywhere* (Celeste Ng) -> Little Fires Everywhere (miniseries) (adaptation, AI: work); *A Gentleman in Moscow* (Amor Towles) -> A Gentleman in Moscow (TV series) (adaptation, AI: work); *All the Light We Cannot See* (Anthony Doerr) -> All the Light We Cannot See (miniseries) (adaptation, AI: work); *The Goldfinch: A Novel (Pulitzer Prize for Fiction)* (Donna Tartt) -> The Goldfinch (film) (adaptation, AI: work); *Pride and Prejudice* (Jane Austen) -> Fire Island (film) (adaptation, AI: work).
- Characters: *Pride and Prejudice* (Jane Austen) -> Mr. Darcy (character); *Pride and Prejudice* (Jane Austen) -> Elizabeth Bennet (character); *Pride and Prejudice* (Jane Austen) -> George Wickham (character); *Pride and Prejudice* (Jane Austen) -> Mr William Collins (character); *Pride and Prejudice* (Jane Austen) -> Charles Bingley (character); *Pride and Prejudice* (Jane Austen) -> Lady Catherine de Bourgh (character).
- Subjects that are ideas: *Braiding Sweetgrass: Indigenous Wisdom, Scientific Knowledge and the Teachings of Plants* (Robin Wall Kimmerer) -> Ethnoecology (subject); *Braiding Sweetgrass: Indigenous Wisdom, Scientific Knowledge and the Teachings of Plants* (Robin Wall Kimmerer) -> Indigenous American philosophy (subject); *Braiding Sweetgrass: Indigenous Wisdom, Scientific Knowledge and the Teachings of Plants* (Robin Wall Kimmerer) -> Indigenous peoples of the Americas (subject, AI: concept); *Braiding Sweetgrass: Indigenous Wisdom, Scientific Knowledge and the Teachings of Plants* (Robin Wall Kimmerer) -> Worldview (subject); *Braiding Sweetgrass: Indigenous Wisdom, Scientific Knowledge and the Teachings of Plants* (Robin Wall Kimmerer) -> Traditional ecological knowledge (subject); *Braiding Sweetgrass: Indigenous Wisdom, Scientific Knowledge and the Teachings of Plants* (Robin Wall Kimmerer) -> Nature (subject).
- Series: *Fourth Wing* (Rebecca Yarros) -> Iron Flame (series); *Fourth Wing* (Rebecca Yarros) -> Onyx Storm (series, AI: work); *The Handmaid's Tale* (Margaret Atwood) -> The Testaments (series, AI: work); *Dune* (Frank Herbert) -> Chapterhouse: Dune (series, AI: work).

## 4. Anniversaries (scheduled calendar)

`anniversaries.parquet`: one row per work and month 2015-01 to 2027-12 in which a round anniversary falls (25, 50, 75, ... years; J7). 4,454 rows for 4,007 works. Author births at month precision: 2,454 author items; deaths: 773 (the death month is the one of events.parquet). Linked events with a month date (P585, else P580): 114 of 452 event items.

| kind | rows | works | rows_2016_2026 |
| --- | --- | --- | --- |
| author_birth | 3,670 | 3,670 | 2,992 |
| author_death | 689 | 689 | 600 |
| event | 95 | 89 | 71 |

Years: 25: 356, 50: 1,686, 75: 1,471, 100: 419, 125: 300, 150: 109, 175: 31, 200: 42, 225: 10, 250: 10, 275: 3, 325: 2, 350: 2, 375: 1, 400: 2, 475: 1, 500: 1, 550: 1, 625: 1, 650: 1, 700: 2, 950: 1, 1900: 2.

Event anniversaries, examples: *The three-body problem* -> Cultural Revolution, 50 years in 2016-05; *The Sympathizer: A Novel (Pulitzer Prize for Fiction)* -> Vietnam War, 50 years in 2025-04; *Little women* -> American Civil War, 150 years in 2015-04; *They called us enemy* -> Internment of Japanese Americans, 75 years in 2017-02; *The ministry of utmost happiness* -> Kashmir conflict, 75 years in 2022-10; *The devil in the white city : murder, magic, and madness at the fair that changed America* -> World's Columbian Exposition, 125 years in 2018-05; *Fall of Giants* -> World War I, 100 years in 2018-11; *The Nix* -> 1968 Democratic National Convention, 50 years in 2018-08.

## 5. Linked-page views and bursts

Pages: every distinct linked article (10,283; the cap of 30,000 was not reached). Stored: 10,283 (Test F store, adaptation views, new download: {'download': 6233, 'adaptation': 2565, 'testF': 1485}); statuses {'200': 10276, '404': 7} (200 = views, 404 = no data). Work-article pairs with views: 33,917 of 33,924; works with views of at least one linked article: 4,530 of 4,530.

Download (`j1_download_views.py`): 6,233 of 6,233 pages fetched, HTTP codes {'200': 6227, 'ConnectionError': 3, '404': 6}, back-offs 3, gap 0.34 s over 4 threads, finished 2026-10-22 10:10:54.

By first link type (J8):

| first_link_type | pages | selected | stored | with_views |
| --- | --- | --- | --- | --- |
| adaptation | 3,192 | 3,192 | 3,192 | 3,191 |
| subject | 1,101 | 1,101 | 1,101 | 1,101 |
| event_period | 517 | 517 | 517 | 517 |
| person | 199 | 199 | 199 | 199 |
| place | 615 | 615 | 615 | 615 |
| character | 1,076 | 1,076 | 1,076 | 1,076 |
| series | 3,583 | 3,583 | 3,583 | 3,577 |

Burst rule (record; J10): a month's views at least 3 times the median of the 6 months before and at least 3,000, or the article in the daily top 500 on any day of the month. Page-months with views 2016-01 to 2026-09: 1,325,604; bursting 28,531 (2.15%); by the ratio rule 14,282, in the top 500 17,480.

`linked_bursts.parquet`: 1,077,150 rows (work x month 2016-01 to 2026-09 x link type x category, for the 8,350 groups with at least one article with views; 4,530 works). Share of rows with at least one bursting article:

| by | value | share |
| --- | --- | --- |
| link type | adaptation | 4.73% |
| link type | subject | 5.80% |
| link type | event_period | 15.87% |
| link type | person | 29.32% |
| link type | place | 32.75% |
| link type | character | 3.33% |
| link type | series | 3.04% |
| category | event | 18.58% |
| category | person | 26.26% |
| category | place | 35.10% |
| category | work | 4.21% |
| category | concept_other | 2.45% |

Most bursting event articles (months bursting, of which in the top 500): World War II 129 (129); World War I 127 (127); Vietnam War 110 (110); September 11 attacks 108 (108); American Civil War 99 (99).

Most bursting place articles (months bursting, of which in the top 500): China 129 (129); India 129 (129); Japan 129 (129); New York City 129 (129); United Kingdom 129 (129).

Most bursting person articles (months bursting, of which in the top 500): Donald Trump 129 (129); Elizabeth II 129 (129); Elon Musk 129 (129); Elvis Presley 129 (129); John F. Kennedy 129 (129).

Most bursting work articles (months bursting, of which in the top 500): Google 129 (129); Interstellar (film) 85 (85); Amazon (company) 76 (74); Bitcoin 63 (63); The Godfather 62 (62).

## 6. Files (data/db/wiki_led/dirs/j_links/)

- `links.parquet`: work_id, book_item, link_type, item, props, page_title (underscores), label, category, ai_kind, is_period, n_roots, p31, p585/p580/p569/p570 date and precision, event_mi (month index year*12+month-1 of P585, else P580, at month precision), event_prop, link_rank.
- `anniversaries.parquet`: work_id, mi, kind (event, author_birth, author_death), years, source_item, link_type, page_title, event_mi.
- `linked_bursts.parquet`: work_id, mi, link_type, category, n_pages, n_burst, any_top500, max_ratio. Each (work, article) pair counts once, under its first link type in the order adaptation, subject, event_period, person, place, character, series, so counts add up.
- `pages_wanted.parquet` (selection and order), `page_burst_counts.parquet`, `links_summary.json`, `bursts_summary.json`, `download_summary.json`; new daily views in `data/interim/j_linked_views/`.

## 7. Limits

- Wikidata was read on 22 Oct 2026. Links, classes and dates may have been added after the month they describe, so the calendar and the link list are not exactly what one could have known at the time (as for D2).
- Coverage is uneven: Wikidata has links for popular and classic books; many recent books have none. Series and adaptations dominate the links; event, place and person links are a few hundred to two thousand rows each.
- The event category is broad (section 2): Wikidata's occurrence class also holds activities, ideas and movements. The AI page kind beside it covers only the articles Test F sorted.
- A newly created article has a median of 0 for the 6 months before, so it bursts once a month reaches 3,000 views (the rule as written).
- The top-500 half of the burst rule makes very popular articles (countries, big cities, large states) burst in most or all months: China is in the daily top 500 in all 129 months, California in 80. For such articles any_top500 and n_burst carry little news; the ratio rule alone is the part that marks a change.
- Checks: 24 random single-article groups (12 in a trial build before the download, 12 in the final build) recomputed from the raw store files, the adaptation views and the top-500 file by a separate script (monthly sums, 6-month median, both burst rules, max_ratio): all 24 match.
