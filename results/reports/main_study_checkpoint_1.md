# Main study, checkpoint 1: SPL data profile and draft taxonomy v2

Khant Phyo Wai (student ID 01323050), CMKL University, honors thesis
Prepared 13 October 2026. Status: draft for Khant's review. Nothing here is a result; it is the data and the categories that later steps would use.

## Summary

- **The SPL subject field cannot give narrow themes for audiobooks and ebooks.** Every digital row carries OverDrive's closed list of only 181 subject terms. Most of them are genres or formats (Fiction, Mystery, Juvenile Fiction). There is no term for racism, epidemics, sexual violence or climate change ("Environment" is on one work). Print books (material type BOOK, 25.8 million rows, still downloading) use library subject headings such as "Racism United States Fiction", so they are the most promising route to narrow themes.
- **Draft taxonomy v2:** 19 broad, 86 middle and 241 narrow theme nodes, built from 614 theme values. Genres (81 values) and audience (5 values) are kept as separate facets. Broad and middle nodes have hand labels.
- **Coverage is the main weakness.** 41.3% of SPL works (41.5% of checkouts) get at least one theme, and 19.5% of works (22.1% of checkouts) get a narrow theme. Nonfiction is almost fully covered (95.0% of works). Fiction is not (13.2% of works), because for fiction the SPL terms are genres and the only theme source is Goodreads shelves, which reach 6.2% of works.
- **Sanity view (descriptive only):** a clear visible rise for "race and racism" from June 2020 and for "epidemics and plagues" from March 2020, also among books already in the catalogue. There is no visible change for "sexual violence" around October 2017 (a thin node of 84 works), or for "climate change" around September 2019.
- **Data problems found:**
  - The ebook file was partial when I started, so I froze it at 6,249,992 of 9,685,032 rows. It covers September 2005 to July 2022 completely. The download has since finished.
  - Both digital formats have no rows at all for May and June 2024 (the library's ransomware outage) or for August 2025.
  - April 2022 audiobooks are 27% below the months around them.
  - OverDrive renamed some subject terms over time; for example "Gay/Lesbian" was replaced by "LGBTQIA+" in 2021.

## 1. What was done

| Task | Output |
|---|---|
| 1. Profile SPL (audiobook full, ebook snapshot) | `data/db/taxonomy_v2/profile/` (CSV and JSON) |
| 2. Clean title-level table | `data/db/taxonomy_v2/spl_works.parquet` (216,503 works) |
| 3. Phrases with facets, hierarchy, assignments | `phrases.parquet`, `theme_values.parquet`, `theme_nodes.parquet`, `theme_value_node.parquet`, `work_theme.parquet`, `work_theme_value.parquet`, `work_genre.parquet`, `work_audience.parquet`, `work_audience_label.parquet`, `work_form.parquet` |
| 4. Quality checks | `data/db/taxonomy_v2/quality/` |
| 5. Sanity view | `sanity_monthly.parquet`, `quality/sanity_window.csv` |

The code is in `code/main_study/`, with scripts numbered in run order (00 to 09). `run_all.sh` reruns everything. Section 10 lists the files and run times.

## 2. SPL profile

### 2.1 Files and completeness

| | Audiobook | Ebook (snapshot) |
|---|---|---|
| Rows read | 4,697,512 | 6,249,992 |
| Rows in the official API (13 Oct) | 4,697,512 | 9,685,032 |
| Checkouts read | 19,887,468 | 18,458,274 (API total 29,937,728) |
| First and last month | Sep 2005 to Aug 2026 | Sep 2005 to Aug 2022 |
| Months present | 249 | 204 |
| Complete months (row count equals the API) | all 249 | 203, Sep 2005 to Jul 2022; Aug 2022 has 98.8% of its rows |
| Months missing in the source itself | May 2024, Jun 2024, Aug 2025 | same three (the API has no digital rows for them) |
| Usage class / checkout type | all Digital / all OverDrive | all Digital / all OverDrive |
| Distinct raw titles | 208,991 | 191,815 |
| Distinct cleaned titles | 97,125 | 169,715 |
| Distinct works (normalized title + creator) | 94,585 | 171,164 |

Across both formats there are 216,503 works. Of these, 49,246 appear in both formats, 121,918 only as ebooks and 45,339 only as audiobooks. These format counts depend on the snapshot: a book whose ebook was first borrowed after July 2022 is counted as audiobook-only here.

The source file is ordered by its internal row id, which follows upload order, so a partial download covers the earliest months fully and the latest months not at all. The ebook download (`code/seattle.py`) finished while this step ran: the file now has 9,685,032 lines, the same as the API. The background job is now on print books. Deleting `data/db/taxonomy_v2/spl_snapshot.json` and running `run_all.sh` would redo this checkpoint on the full ebook file, in about 15 minutes.

### 2.2 Rows, checkouts and subject coverage by year and format

The subjects field is almost never empty. At least 99.87% of rows and 99.63% of checkouts have it in every year and format.

| Year | Audiobook rows | Audiobook checkouts | Months | % rows with subjects | % checkouts with subjects | Ebook rows | Ebook checkouts | Months | % rows with subjects | % checkouts with subjects |
|---|---|---|---|---|---|---|---|---|---|---|
| 2005 | 2,350 | 2,637 | 4 | 100.00 | 100.00 | 1,171 | 1,322 | 4 | 100.00 | 100.00 |
| 2006 | 8,543 | 9,892 | 12 | 100.00 | 100.00 | 4,789 | 5,828 | 12 | 100.00 | 100.00 |
| 2007 | 16,909 | 19,812 | 12 | 100.00 | 100.00 | 7,507 | 8,898 | 12 | 99.87 | 99.63 |
| 2008 | 27,815 | 34,234 | 12 | 100.00 | 100.00 | 13,139 | 15,993 | 12 | 99.89 | 99.76 |
| 2009 | 42,341 | 54,989 | 12 | 100.00 | 100.00 | 25,777 | 31,920 | 12 | 99.91 | 99.81 |
| 2010 | 62,325 | 87,551 | 12 | 100.00 | 100.00 | 64,339 | 84,328 | 12 | 99.88 | 99.82 |
| 2011 | 87,326 | 133,447 | 12 | 100.00 | 100.00 | 158,432 | 269,917 | 12 | 99.90 | 99.83 |
| 2012 | 102,271 | 168,395 | 12 | 100.00 | 100.00 | 262,259 | 543,122 | 12 | 99.90 | 99.84 |
| 2013 | 120,743 | 238,360 | 12 | 100.00 | 100.00 | 324,496 | 754,296 | 12 | 99.95 | 99.93 |
| 2014 | 145,705 | 335,926 | 12 | 100.00 | 100.00 | 433,295 | 1,101,645 | 12 | 99.97 | 99.98 |
| 2015 | 171,692 | 468,275 | 12 | 100.00 | 100.00 | 492,906 | 1,329,606 | 12 | 99.97 | 99.98 |
| 2016 | 198,289 | 586,391 | 12 | 100.00 | 100.00 | 549,229 | 1,436,345 | 12 | 99.96 | 99.97 |
| 2017 | 222,881 | 730,389 | 12 | 100.00 | 100.00 | 578,649 | 1,578,697 | 12 | 99.99 | 100.00 |
| 2018 | 261,035 | 983,019 | 12 | 100.00 | 100.00 | 618,983 | 1,860,638 | 12 | 99.99 | 100.00 |
| 2019 | 286,938 | 1,276,883 | 12 | 100.00 | 100.00 | 646,165 | 2,130,439 | 12 | 100.00 | 100.00 |
| 2020 | 317,202 | 1,513,625 | 12 | 99.99 | 100.00 | 772,386 | 2,793,961 | 12 | 100.00 | 100.00 |
| 2021 | 359,695 | 1,687,686 | 12 | 99.99 | 100.00 | 762,626 | 2,705,503 | 12 | 100.00 | 100.00 |
| 2022 | 414,268 | 1,954,869 | 12 | 99.99 | 99.99 | 533,844 | 1,805,816 | 8 | 100.00 | 100.00 |
| 2023 | 475,574 | 2,451,377 | 12 | 100.00 | 100.00 | not in snapshot | | | | |
| 2024 | 431,587 | 2,193,482 | 10 | 100.00 | 100.00 | not in snapshot | | | | |
| 2025 | 522,112 | 2,705,929 | 11 | 100.00 | 100.00 | not in snapshot | | | | |
| 2026 | 419,911 | 2,250,300 | 8 | 100.00 | 100.00 | not in snapshot | | | | |

### 2.3 How the subjects field is written

- **Separator.** Terms are joined by a comma and a space, for example "Business, Careers, Nonfiction, Self-Improvement". There are no subdivisions: no record contains "--", ";" or "|". Some terms carry a qualifier in brackets ("Humor (Fiction)", "LGBTQIA+ (Nonfiction)") or after a hyphen ("Foreign Language Study - Spanish").
- **Terms per record.** Between 1 and 7, with a mean of 2.87 and a median of 3.
- **Vocabulary.** There are 181 distinct terms: 144 appear on audiobooks and 170 on ebooks. This is OverDrive's own category list, not library subject headings.
  - 37 terms appear only on ebooks. Most are older OverDrive terms last seen in 2017 to 2021, such as Contemporary Romance, Historical Romance, Paranormal Romance, Teen and Male/Male.
  - 11 terms appear only on audiobooks, mostly language-course subtypes ("Foreign Language Study - Spanish").
- **Common combinations.** "Fiction, Literature" (40,354 records), "Fiction, Mystery", "Juvenile Fiction, Juvenile Literature", "Fiction, Mystery, Suspense, Thriller", "Fiction, Romance", "Biography & Autobiography, Nonfiction".
- **Print books are different.** A 40-row sample of print-book rows from the API (`spl_book_subject_sample.json`) uses library subject headings with subdivisions joined by spaces. Examples: "Mothers and sons Fiction, Discrimination Fiction, Domestic fiction" for *On Earth We're Briefly Gorgeous*; "Solitude Fiction, Young women Fiction, Murder Investigation Fiction, North Carolina Fiction" for *Where the Crawdads Sing*; "Feminism, Women Social conditions, Women Economic conditions, Equality" for *The Moment of Lift*. This matters for open question 1.

The 30 terms with the most checkouts are below. The full list of 181 is in `profile/spl_subject_terms.csv`; the top 300 file holds all 181, since only 181 exist.

| Term | Checkouts | Works | % of all checkouts |
|---|---|---|---|
| Fiction | 21,480,536 | 98,289 | 56.0 |
| Nonfiction | 11,303,195 | 67,040 | 29.5 |
| Literature | 8,341,142 | 42,752 | 21.8 |
| Romance | 5,840,732 | 32,485 | 15.2 |
| Thriller | 5,065,659 | 20,902 | 13.2 |
| Mystery | 5,037,354 | 26,377 | 13.1 |
| Fantasy | 4,925,771 | 24,623 | 12.8 |
| Historical Fiction | 4,032,622 | 21,200 | 10.5 |
| Suspense | 3,349,992 | 14,806 | 8.7 |
| Juvenile Fiction | 3,092,238 | 32,685 | 8.1 |
| Biography & Autobiography | 3,021,707 | 18,509 | 7.9 |
| Science Fiction | 2,147,402 | 10,274 | 5.6 |
| Humor (Fiction) | 2,140,769 | 12,924 | 5.6 |
| Young Adult Fiction | 2,134,879 | 15,063 | 5.6 |
| History | 2,128,582 | 15,010 | 5.6 |
| Self-Improvement | 1,760,752 | 7,847 | 4.6 |
| Juvenile Literature | 1,753,661 | 26,077 | 4.6 |
| Sociology | 1,638,342 | 9,372 | 4.3 |
| Business | 1,487,041 | 7,383 | 3.9 |
| Psychology | 1,009,735 | 3,567 | 2.6 |
| Young Adult Literature | 989,230 | 9,156 | 2.6 |
| Politics | 983,252 | 6,843 | 2.6 |
| Classic Literature | 914,122 | 4,943 | 2.4 |
| Science | 824,359 | 5,369 | 2.1 |
| Family & Relationships | 760,415 | 4,488 | 2.0 |
| Health & Fitness | 672,255 | 5,198 | 1.8 |
| Short Stories | 643,590 | 5,917 | 1.7 |
| Religion & Spirituality | 640,541 | 4,461 | 1.7 |
| Cooking & Food | 632,800 | 5,672 | 1.7 |
| Horror | 531,765 | 3,247 | 1.4 |

### 2.4 Duplicate check

- **Same title, creator, year, month and usage class.** 62,436 groups (134,330 rows, 1.2% of rows, 618,842 checkouts) have more than one row within a format. In almost all of them the rows differ in publication year (55,651 groups), publisher (47,142), subjects (38,805) or ISBN (14,833). They are different editions of one title, not repeated rows.
- **Exact duplicates.** Only 2 rows repeat every downloaded field. Summing all rows is therefore correct.
- **Caveat.** The checkout type and material type were not downloaded, but the API shows a single checkout type (OverDrive) for each digital format, so they cannot explain the repeats.
- **Works with several records in one month.** 1.0% of work-months contain more than one record, again editions.

### 2.5 Odd things worth knowing

1. **Subjects are mostly genres and formats.** Of the 181 terms, I classified 111 as carrying a theme. Many of these are very broad (History, Sociology, Psychology, Politics, Science), and the rest are genres, audience labels or forms.
2. **The vocabulary changes over time, so a work's subject string changes too.** 42.1% of works (91,079) have more than one subject string across months.
   - "Gay/Lesbian" stops in 2021 and "LGBTQIA+ (Fiction)" starts in 2021. Its share of checkouts goes from 0% (2020) to 0.8% (2021) and 2.4% (2022).
   - A series built from monthly subject strings would show a jump that comes from relabeling, not demand. To avoid this, each work's terms are pooled over all months (decision D3 in section 8).
3. **Missing months.** There are no digital rows for May 2024, June 2024 or August 2025, in the API either. Print books have rows for all three. SPL was hit by ransomware on 25 May 2024, and e-books and e-audiobooks returned on 13 June 2024 ([SPL blog, 28 May 2024](https://blog.spl.org/2024/05/28/an-update-about-access-to-library-technology-systems/); [KUOW, 13 June 2024](https://www.kuow.org/books/2024-06-13/seattle-library-patrons-rejoice-quietly-digital-books-are-back-26c3)). I found no explanation for August 2025.
4. **A dip in April 2022.** Audiobook checkouts were 118,681, 27% below the median of the surrounding seven months. The API has the same figure. Ebooks show no dip that month.
5. **COVID period (calendar year-on-year change).**
   - Ebook growth jumped from about +15% in 2019 to +22% (Mar 2020), +38% (Apr), +49% (May) and +43% (Jun 2020). Ebooks then fell year on year from April 2021 (-7%).
   - Audiobook growth slowed from about +30% in 2019 to +13% (Mar 2020) and +20% (Apr 2020).
6. **One title stands out.** *Braiding Sweetgrass* has 44,020 checkouts (41,619 as an audiobook). That is more than any other work and 0.2% of all audiobook checkouts. I did not look into why.
7. **Missing creators.** 3,915 ebook rows and 55 audiobook rows have no creator.

## 3. The clean title-level table (task 2)

`spl_works.parquet` has one row per work. Each row holds:

- display title and creator
- formats
- subject terms, with the share of the work's checkouts that carried each term
- number of subject strings, records and raw titles
- first and last checkout month, overall and per format
- checkouts by format
- earliest publication year, top publishers and up to 10 ISBNs

`spl_record_work.parquet` maps every source record to its work.

How a work is formed:

- **Title.** Remove edition and format notes such as "(Unabridged)", "(Movie Tie-in Edition)" and "[electronic resource]". Remove OverDrive series tails such as ": Dreg City Series, Book 1". Then lowercase, strip accents and punctuation, and drop a leading "the", "a" or "an". Non-Latin scripts are kept; a first version that folded everything to ASCII turned Cyrillic, Chinese and Korean titles into empty strings.
- **Subtitle.**
  - One subtitle variant: the bare title and that variant merge, so "Leap" and "Leap: Leaving a Job with No Plan B..." are one work.
  - Two or more different subtitles under the same main title and creator: the main title is a series or brand ("Murder, She Wrote: ...", "National Geographic Readers: ..."), so each subtitle is its own work.
  - Reworded subtitles of one book still merge. "The Great Influenza: The Epic Story of the Deadliest Plague in History" and "...: The Story of the Deadliest Pandemic in History" are one work.
- **Creator.** Keep the first creator only. Flip "Last, First", and drop life dates, role words and degree letters (M.D., PhD, PsyD, LMSW). The work key uses first and last name only, so "Octavia E. Butler" and "Octavia Butler", or "Robin Wall Kimmerer" and "Robin Kimmerer", are one work.
- **Generic creators.** For empty creators or "Various", the full title is kept so that different anthologies are not merged.

Known limits:

- 2,507 main-title and creator groups (6,662 works) are still split by subtitle. Many are genuinely different editions (a BBC radio dramatization, a 50th anniversary edition). Some are not; for example "The Underground Railroad (Oprah's Book Club)" is separate from "The Underground Railroad".
- Splits like these do not change theme totals, because each record's checkouts are counted once. They only make work counts slightly too high.
- Work keys are reproducible: I checked that two runs with different Python hash seeds give identical keys.

## 4. How taxonomy v2 was built (task 3)

### 4.1 Phrase sources

| Source | Theme | Genre | Audience | Form | Place | Period | Other | Total |
|---|---|---|---|---|---|---|---|---|
| SPL subject terms (all 181, every one decided by hand) | 111 | 43 | 11 | 16 | 0 | 0 | 0 | 181 |
| Goodreads shelves used on at least 10 Goodreads works (28,321 rarer shelves dropped) | 1,467 | 490 | 122 | 214 | 315 | 72 | 3,903 | 6,583 |
| Wikidata main subjects of literary works (`wikidata_book_subjects.json`) | 268 | 18 | 2 | 8 | 36 | 9 | 24 | 365 |
| LibriVox genre labels | 60 | 34 | 2 | 24 | 0 | 12 | 1 | 133 |

The facet counted is a phrase's main facet. A phrase can carry several parts: "Juvenile Fiction" is audience=children plus form=fiction, "ya-fantasy" is audience=young adult plus genre=fantasy, and "wwii" is theme=world war ii.

The "other" facet has subtypes, so nothing is silently lost:

| Other subtype | Phrases | Examples |
|---|---|---|
| author_series | 2,393 | stephen-king, in-death (a shelf where 60% or more of its works share one author) |
| personal | 804 | to-read, owned, kindle, read-in-2016, 5-stars, book-club |
| franchise | 158 | star-wars, marvel, doctor-who |
| trope | 153 | alpha-male, enemies-to-lovers, billionaire |
| award_list | 141 | pulitzer, newbery, 1001-books |
| mood | 80 | dark, sad, made-me-cry, beach-reads |
| person | 51 | Abraham Lincoln, Karl Marx (mostly Wikidata) |
| publisher | 44 | penguin-classics, harlequin |
| ambiguous | 42 | high-school, college, english (often "read in high school", not "set in high school") |
| language | 41 | francais, translated |
| adaptation | 13 | movies, book-to-movie |
| author_identity, fanfiction | 9 | female-authors, fanfic |

How each phrase was decided:

| Route | Phrases |
|---|---|
| Hand table for SPL terms | 181 |
| Hand review (`_review.py`) | 1,501 |
| Exact lexicon match (`_lexicon.py`) | 1,637 |
| Longest-match token rules on compound shelves | 791 |
| Author-concentration rule | 2,365 |
| Personal-shelf and year patterns | 604 |
| Award patterns | 86 |
| Wikidata description rules (persons, places, "History of ...", "... in the Middle Ages") | 66 |
| Century and decade patterns | 31 |

I read the rule output for the most frequent Goodreads shelves, all unresolved shelves used on 19 or more works, all Wikidata subjects and all LibriVox labels, and wrote hand decisions where the rule was wrong. Examples:

- "roman" is the German and French word for novel, not ancient Rome.
- "law of attraction" was read as law, and "founding fathers" as fathers.
- The person rule caught "Jesus" because its description contains dates.

A similarity rule remains in the code as a safety net for any phrase that no rule or hand decision covers. On the final run it decided nothing. In an earlier run it misread Arabic-script shelves (for example "رواية", novel, came out closest to UFOs), so I decided the last 22 leftover phrases by hand instead.

The vocabulary has 614 theme values (46 marked very general, such as history, politics, science and psychology), 81 genre values and 5 audience values (children, middle grade, young adult, new adult, adult).

### 4.2 Hierarchy

**Embedding.**
- Model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, which fastembed supports directly, so no substitute model was needed. fastembed downloaded the weights from Hugging Face on first use.
- Text: each specific theme value is embedded as "books about <value>". In my tests this separated related themes better than the bare word (grief to death-and-dying 0.71 against 0.57 for the next item, compared with 0.50 against 0.46 bare).
- Glosses: 306 short or ambiguous values get a short hand gloss in `_labels.py`. Without them, "depression" sat with "great depression", "cold war" with "winter", and "artificial intelligence" with "intelligence agencies". The model has no useful sense of "covid 19".
- Vectors are mean-centered before clustering.

**Clustering.** Ward linkage on the 568 specific values, one tree cut at 20, 90 and 260 clusters, so the three levels nest exactly.

**Hand edits.** 51 edits in `_labels.py`, each keyed by theme value so they survive reruns. The full list is in `profile/hierarchy_edits.csv`.
- 9 whole middle nodes moved to another broad node. For example, rock music had landed under health and climate under holidays; the sea became part of places and nature.
- 8 new narrow nodes, for example knitting, quilting and crafts.
- 34 single values joined another value's node. For example, tarot moved to occult, anxiety to mental illness, and samurai to knights.

**General values.** These are not clustered. Each is attached to a middle node when it clearly fits one, otherwise to the closest broad node. 22 of the 46 placements were set by hand; for example, OverDrive's "Sociology" (9,372 works) is far wider than social theory, so it sits at the broad level of "Politics, society and justice".

**Labels.** All 19 broad and 86 middle nodes have hand labels. Narrow nodes use their two best-supported values (for example "lgbtq / gay men"), except five hand labels used in the sanity view.

**Result.**
- 19 broad nodes, at the top of the 12 to 20 range after the sea node was folded in.
- 86 middle nodes.
- 241 narrow nodes. 57 hold one value, 97 hold two, 56 hold three and 31 hold four to eight.

| Node | Broad label | Middle | Narrow | Theme values | Works | Strength-weighted checkouts | Middle nodes | General values attached here |
|---|---|---|---|---|---|---|---|---|
| B01 | Magic, myth and the supernatural | 4 | 10 | 32 | 3,681 | 931,047 | Monsters, vampires and superheroes; Magic, witches and fantasy creatures; Myths and legends; Ghosts and dreams | |
| B02 | Gender, sexuality and relationships | 4 | 8 | 23 | 7,608 | 1,147,361 | LGBTQ lives and sexuality; Feminism and gender; Marriage, dating and infidelity; Pregnancy, childbirth and abortion | love |
| B03 | Religion and spirituality | 4 | 8 | 34 | 9,949 | 987,095 | Christianity and the Bible; Islam, Buddhism, Hinduism and other religions; Jewish life and history; Meditation, prayer and mysticism | faith, religion, religion and spirituality |
| B04 | Science, technology and learning | 11 | 28 | 53 | 12,343 | 1,077,777 | Language and linguistics; Computers, software and the internet; Mathematics, physics and chemistry; Time and time travel; Teaching and learning; Brain, mind and memory; Biology, evolution and the human body; Artificial intelligence and robots; The future, utopias and the end of the world; Data, statistics and information; Decision making and systems thinking | science |
| B05 | Race, ethnicity and migration | 4 | 12 | 29 | 6,365 | 912,513 | African American and Black life; Race, racism and diversity; Indigenous peoples, culture and colonial history; Slavery, trafficking and immigration | |
| B06 | Arts, media and entertainment | 7 | 20 | 39 | 8,610 | 826,897 | Visual arts, design and crafts; Writing and storytelling; Books, libraries and museums; Film, television and stage; Celebrity and popular culture; Fashion, beauty and dance; Music | performing arts |
| B07 | Childhood, family and growing up | 3 | 12 | 25 | 6,669 | 936,690 | Childhood, parenting and adoption; School, adolescence and coming of age; Siblings and family history | family, family and relationships |
| B08 | War, conflict and history | 6 | 17 | 40 | 17,325 | 1,921,447 | World wars, modern wars and terrorism; Civil wars and revolutions; The Holocaust, Nazism and genocide; Medieval history and monarchy; Military, naval and air warfare; International relations and globalization | current events, history |
| B09 | Nature, places and the environment | 8 | 22 | 51 | 10,126 | 790,688 | Travel, exploration and mountains; Architecture, engineering and transport; Environment, wilderness and survival; Gardening and farming; The sea and seafaring; Archaeology, geology and natural history; Climate, weather and seasons; Cities and communities | |
| B10 | Work, business and money | 5 | 12 | 29 | 8,042 | 1,030,538 | Careers and work; Management and leadership; Money, investing and the economy; Entrepreneurship and productivity; Marketing and sales | business |
| B11 | Food, home and holidays | 3 | 5 | 17 | 7,160 | 677,678 | Holidays; Cooking and food; Home, homesteading and simple living | |
| B12 | Violence, trauma, death and grief | 4 | 12 | 26 | 946 | 106,209 | Abuse, sexual violence and revenge; Murder and kidnapping; Death, grief and the afterlife; Trauma, fear and self-harm | |
| B13 | Politics, society and justice | 5 | 17 | 37 | 15,605 | 1,342,907 | Government and political ideas; Socialism, communism and the Cold War; Human rights, civil rights and justice; Media and communication; Social issues, poverty and social theory | social science, society, sociology |
| B14 | Mind, self and philosophy | 3 | 13 | 29 | 13,322 | 1,786,252 | Friendship, happiness and identity; Ethics, mindset and motivation; Philosophy and belief | emotions, personal development, psychology |
| B15 | Health, illness and addiction | 5 | 13 | 34 | 7,341 | 708,050 | Mental health and therapy; Diet, nutrition and eating disorders; Drugs and addiction; Disease, epidemics and public health; Disability | health, health and fitness |
| B16 | Animals | 3 | 9 | 22 | 1,535 | 163,304 | Pets and farm animals; Wild animals; Horses | animals |
| B17 | Sports, games and fitness | 3 | 12 | 24 | 3,763 | 219,296 | Games and gambling; Sports; Fitness, yoga and running | sports, sports and recreation |
| B18 | Space and the universe | 2 | 4 | 9 | 391 | 72,006 | Aliens and space exploration; Astronomy and cosmology | |
| B19 | Crime, police and law | 2 | 7 | 15 | 2,279 | 263,701 | Police, organized crime and prison; Spies, hackers and conspiracies | law |

The narrow nodes and all their member values are in `theme_nodes.parquet`, with a readable version in `quality/node_sizes.csv`.

### 4.3 Assigning works

**Theme evidence comes from three sources, kept separately.**

| Source | What it uses | Weighting | Works |
|---|---|---|---|
| spl | The work's SPL subject terms | Share of the work's checkouts carrying each term | 38.5% |
| gr | Shelves of the linked Goodreads work (shelf count of 2 or more) | Shelf counts | 4.6% |
| title | Theme words in the title or subtitle, nonfiction works only, under hand rules (`_lexicon.TITLE_*`) | | 4.6% |

The title rules work like this:
- They take the longest phrase first.
- They block metaphor patterns such as "anatomy of", "abuse of power" and "an epidemic of loneliness".
- They accept single words only when the word is the theme value itself, or one of the hand-listed forms for the sanity themes (for example pandemic, influenza, racism, racial, rape, climate, grief).

**Strength.** For each source, a work's theme weights become shares that sum to 1. Shares are rolled up to parent nodes, and the strength of a node is the mean share over the sources that have any theme evidence for that work. Per-source shares are stored too (`s_spl`, `s_gr`, `s_title`), so a different weighting can be tried without rerunning anything.

**Genres, audience and form** are stored separately in the same way: `work_genre`, `work_audience` and `work_form`.
- Goodreads fiction-genre shelves are ignored on nonfiction works (a "historical" shelf on a history book is not historical fiction).
- The audience label (`work_audience_label`) takes SPL first, then Goodreads, else "adult (default)".

**Goodreads links.** 13,445 SPL works are linked: 6.2% of works and 18.0% of checkouts. Local Goodreads author names exist for only 22,349 of 74,645 Goodreads works, so four tiers are used:

| Tier | Rule | Links |
|---|---|---|
| A | Same main title and same author (first and last name) | 5,794 |
| B | Same main title and same surname | 107 |
| C | Title only, at least 3 words or 15 letters, unique on both sides | 7,245 |
| D | Title only, short title, unique on both sides, and the Goodreads work has 20,000 or more ratings | 299 |

On works where the Goodreads author is known, the tier C rule agrees on the author's surname 96.0% of the time (2,297 checked), and tier D 99.1% (221 checked). Title-only links also need a compatible subtitle and are not made for SPL works that were both published and first borrowed after 2017, because the Goodreads data ends in 2017. Without those two checks I found *Harry Potter and the Chamber of Secrets* linked to flute sheet music and the 2022 *Sea of Tranquility* linked to a 2012 novel of the same name. A random sample of 30 title-only links (`quality/goodreads_title_link_sample_30.csv`) looked correct to me in all 30.

## 5. Quality checks (task 4)

### 5.1 Coverage

Cells show % of works / % of checkouts. "Fiction" means SPL terms say fiction and not nonfiction. Children and young adult are by audience label.

| % of works / % of checkouts | All works (216,503) | Fiction (141,809) | Nonfiction (67,308) | Children (38,163) | Young adult (15,166) |
|---|---|---|---|---|---|
| any theme (any level) | 41.3 / 41.5 | 13.2 / 16.9 | 95.0 / 97.2 | 24.9 / 25.6 | 24.7 / 30.6 |
| middle level | 31.9 / 33.1 | 12.6 / 15.4 | 68.8 / 73.1 | 20.1 / 23.4 | 21.9 / 29.1 |
| narrow level | 19.5 / 22.1 | 11.9 / 14.1 | 32.6 / 39.8 | 15.8 / 21.5 | 20.1 / 26.8 |
| theme from SPL terms | 38.5 / 35.0 | 9.2 / 8.0 | 94.3 / 96.2 | 21.9 / 17.5 | 17.7 / 18.0 |
| theme from Goodreads shelves | 4.6 / 12.6 | 4.5 / 10.1 | 5.2 / 18.7 | 3.4 / 11.1 | 8.2 / 15.4 |
| theme from title words | 4.6 / 4.2 | 0.0 / 0.0 | 13.3 / 13.7 | 2.4 / 1.5 | 1.5 / 1.2 |
| narrow theme from SPL terms | 12.9 / 11.3 | 8.9 / 7.9 | 18.8 / 18.5 | 11.3 / 11.0 | 12.6 / 14.8 |
| narrow theme without title words | 16.0 / 19.4 | 11.9 / 14.1 | 22.5 / 30.9 | 14.2 / 20.9 | 19.1 / 25.9 |
| any genre | 66.3 / 80.8 | 78.2 / 90.3 | 45.4 / 59.9 | 50.4 / 74.4 | 78.8 / 93.5 |
| linked to Goodreads | 6.2 / 18.0 | 6.8 / 17.4 | 5.5 / 19.7 | 3.7 / 12.6 | 9.7 / 21.1 |

Where the narrow fiction coverage comes from:
- Most narrow coverage for fiction (11.9% of works) comes from a few SPL terms that name a theme: LGBTQIA+ (Fiction), African American Fiction, Mythology, Christian Fiction.
- Goodreads adds narrow themes for linked fiction.
- Almost no fiction has a narrow theme about a social topic such as grief or war unless it is linked to Goodreads.

### 5.2 Themes per work

| Themes per work | Broad | Middle | Narrow |
|---|---|---|---|
| 0 | 127,008 | 147,408 | 174,225 |
| 1 | 50,290 | 52,001 | 34,811 |
| 2 | 27,973 | 12,941 | 5,459 |
| 3 | 8,929 | 2,857 | 1,349 |
| 4 | 1,719 | 816 | 424 |
| 5 | 401 | 310 | 156 |
| 6+ | 183 | 170 | 79 |

Among works that have any theme, the mean is 1.60 broad, 1.34 middle and 1.25 narrow themes. The strongest broad theme has a median strength of 1.0 (mean 0.82). Works with several themes are mostly nonfiction with several SPL terms, or Goodreads-linked works.

### 5.3 Largest and smallest nodes

Size is measured as strength-weighted checkouts. "works_top" counts works for which the node is their strongest at that level. The full table is `quality/node_sizes.csv`.

| Level | Largest | Smallest |
|---|---|---|
| Broad | War, conflict and history (17,325 works, 1,921,447); Mind, self and philosophy (13,322; 1,786,252); Politics, society and justice (15,605; 1,342,907); Gender, sexuality and relationships (7,608; 1,147,361); Science, technology and learning (12,343; 1,077,777) | Space and the universe (391 works, 72,006); Violence, trauma, death and grief (946; 106,209); Animals (1,535; 163,304); Sports, games and fitness (3,763; 219,296); Crime, police and law (2,279; 263,701) |
| Middle | LGBTQ lives and sexuality (5,430; 837,882); African American and Black life (4,266; 670,104); Myths and legends (2,890; 653,089); Cooking and food (5,838; 567,812); Government and political ideas (7,524; 557,308) | Cities and communities (18; 553); Decision making and systems thinking (38; 1,658); Trauma, fear and self-harm (24; 2,003); International relations and globalization (94; 2,471); Spies, hackers and conspiracies (56; 2,485) |
| Narrow | lgbtq / gay men (5,370; 833,789); african american life / black life (4,255; 668,651); mythology / arthurian legend (2,872; 651,492); christianity / latter day saints (4,282; 253,975); language / language learning (3,130; 184,335) | local history (0); corruption (0); complexity science / systems thinking (1); information (1); epistemology / logic (8) |

Narrow nodes by number of works: 2 have none, 30 have 1 to 9, 39 have 10 to 29, 82 have 30 to 99, 80 have 100 to 999 and 8 have 1,000 or more. Middle nodes: 2 have 10 to 29 works, 10 have 30 to 99, and the other 74 have 100 or more.

The largest narrow nodes are large because single SPL terms map to them ("LGBTQIA+ (Fiction)", "African American Fiction", "Mythology", "Christian Fiction", "Foreign Language Study"). The narrow level is therefore uneven: a few SPL-driven nodes hold thousands of works, while most nodes hold tens to hundreds of works from Goodreads and titles.

### 5.4 Ten example works per broad node

These are the 10 works with the most strength-weighted checkouts among works whose strongest broad theme is the node.

| Broad node | Works |
|---|---|
| B01 Magic, myth and the supernatural | A Game of Thrones; A Court of Thorns and Roses; The Fellowship of the Ring; The Night Circus; Children of Blood and Bone; Norse Mythology; Good Omens; The Two Towers; The Hobbit; American Gods |
| B02 Gender, sexuality and relationships | The Handmaid's Tale; The Seven Husbands of Evelyn Hugo; Yes Please; Heated Rivalry; The House in the Cerulean Sea; A Little Life; On Earth We're Briefly Gorgeous; Red, White & Royal Blue; Game Changer; Less |
| B03 Religion and spirituality | Educated; The Power of Now; Radical Acceptance; The Art of Mindful Living; The Lion, the Witch and the Wardrobe; Zealot; Mere Christianity; Greenlights; The 5 Love Languages; The Book of Joy |
| B04 Science, technology and learning | Sapiens; Astrophysics for People in a Hurry; The Martian; The Circle; The Body; Bad Blood; The Immortal Life of Henrietta Lacks; What If?; How to Do Nothing; How to Stop Time |
| B05 Race, ethnicity and migration | Becoming; Braiding Sweetgrass; Homegoing; So You Want to Talk about Race; The Hate U Give; The Underground Railroad (Oprah's Book Club); The Help; Beloved; White Fragility; The Underground Railroad |
| B06 Arts, media and entertainment | Born a Crime; A Visit from the Goon Squad; Fahrenheit 451; I'm Glad My Mom Died; The Woman in Me; The Picture of Dorian Gray; The Storyteller; The Last Black Unicorn; Friends, Lovers, and the Big Terrible Thing; The Storied Life of A. J. Fikry |
| B07 Childhood, family and growing up | Where'd You Go, Bernadette; Calypso; Before We Were Yours; Commonwealth; To Kill a Mockingbird; Why Not Me?; My Name Is Lucy Barton; Is Everyone Hanging Out Without Me? (And Other Concerns); A Spool of Blue Thread; The Seven Principles for Making Marriage Work |
| B08 War, conflict and history | All the Light We Cannot See; The Book Thief; Lincoln in the Bardo; Unbroken; Hotel on the Corner of Bitter and Sweet; The Boys in the Boat; Dead Wake; In the Garden of Beasts; The Tiger's Wife; The Splendid and the Vile |
| B09 Nature, places and the environment | Wild; A Walk in the Woods; Braving the Wilderness; The Dog Stars; Shantaram; The Stranger in the Woods; On the Road; The Road to Little Dribbling; Into Thin Air; The Feather Thief |
| B10 Work, business and money | Never Split the Difference; Grit; The 7 Habits of Highly Effective People; Principles; Start with Why; Essentialism; Good to Great; The 4-Hour Workweek; Radical Candor; Lean In |
| B11 Food, home and holidays | Kitchen Confidential; Crying in H Mart; Sweetbitter; Taste; Medium Raw; Save Me the Plums; Digital Minimalism; Holidays on Ice; Be Ready When the Luck Happens; Salt, Fat, Acid, Heat |
| B12 Violence, trauma, death and grief | It Ends with Us; Thirteen Reasons Why; If He Had Been with Me; The Lovely Bones; Picture Perfect; Before I Fall; Missoula; The Pact; Ordeal by Innocence; All the Ugly and Wonderful Things |
| B13 Politics, society and justice | Hillbilly Elegy; Between the World and Me; Evicted; Know My Name; Shrill; Quiet; The New Jim Crow; What Happened; Nomadland; Orange Is the New Black |
| B14 Mind, self and philosophy | The Subtle Art of Not Giving a F*ck; 101 Essays That Will Change the Way You Think; The Life-Changing Magic of Tidying Up; Brave New World; Untamed; Dare to Lead; The Untethered Soul; Atomic Habits; You Are a Badass; 12 Rules for Life |
| B15 Health, illness and addiction | Cutting for Stone; How to Change Your Mind; Turtles All the Way Down; The Body Keeps the Score; Furiously Happy; When Breath Becomes Air; The Vegetarian; Being Mortal; How Not to Die; The Great Influenza |
| B16 Animals | The Art of Racing in the Rain; Leaving Time; The Call of the Wild; Three Bags Full; We Are All Completely Beside Ourselves; The Wind in the Willows; The One and Only Ivan; Lily and the Octopus; The Tale of Despereaux; Because of Winn-Dixie |
| B17 Sports, games and fitness | What I Talk About When I Talk About Running; Calico Joe; You Will Know Me; Born to Run; Open; The Yiddish Policemen's Union; Moneyball; Nobody's Baby But Mine; One Life; The Inner Game of Tennis |
| B18 Space and the universe | Artemis; Armada; Seveneves; I Am Number Four; Children of Time; The Humans; The Book of Strange New Things; Pandora's Star; The War of the Worlds; House of Suns |
| B19 Crime, police and law | The Whistler; I'll Be Gone in the Dark; Killers of the Flower Moon; Rogue Lawyer; The Racketeer; Gray Mountain; The Litigators; Sycamore Row; The Rooster Bar; The Confession |

Most examples fit. Placements a reader may question, with their cause:

- *Educated* in religion: SPL tags it "Religion & Spirituality".
- *The Life-Changing Magic of Tidying Up* in mind and self: the Goodreads "psychology" shelf.
- *The Yiddish Policemen's Union* in sports and games: the "chess" shelf.
- *Fahrenheit 451* in arts: the books-about-books shelf.
- *The Lion, the Witch and the Wardrobe* in religion: the "christian" shelf.
- *Greenlights* in religion: an SPL term.

The Grisham novels in B19 come from law shelves.

### 5.5 Twenty random works for a human to judge

These are drawn with a fixed seed from works that have at least one theme. The file `quality/random_20_works_for_review.csv` has empty `judge_ok` and `judge_note` columns for your marks.

| # | Title | Creator | SPL subject terms | Theme sources | Broad themes (strength) | Narrow themes (strength) | Genres (strength) | Audience |
|---|---|---|---|---|---|---|---|---|
| 1 | You Only Call When You're in Trouble | Stephen McCauley | Fiction, Literature, Humor (Fiction), LGBTQIA+ (Fiction) | spl | Gender, sexuality and relationships (1.00) | lgbtq / gay men (1.00) | humor (1.00) | adult (default) |
| 2 | God Loves You | David Jeremiah | Nonfiction, Religion & Spirituality, Christian Nonfiction, Juvenile Fiction, Juvenile Literature, Christian Fiction | spl | Religion and spirituality (1.00) | christianity / latter day saints (0.32) | christian nonfiction (0.66) ; christian fiction (0.34) | children |
| 3 | What We Found in Hallelujah | Vanessa Miller | Fiction, African American Fiction, Literature, Christian Fiction | spl | Religion and spirituality (0.50) ; Race, ethnicity and migration (0.50) | christianity / latter day saints (0.50) ; african american life / black life (0.50) | christian fiction (1.00) | adult (default) |
| 4 | Endure | Cameron Hanes | Business, Self-Improvement, Sports & Recreations, Nonfiction | spl | Work, business and money (0.33) ; Mind, self and philosophy (0.33) ; Sports, games and fitness (0.33) | | self-help (1.00) | adult (default) |
| 5 | 1,001 Low-Carb Recipes | Dana Carpender | Cooking & Food, Nonfiction, Health & Fitness | spl | Food, home and holidays (0.70) ; Health, illness and addiction (0.30) | | | adult (default) |
| 6 | Horse of a Different Color | Jim Squires | Nonfiction, Sports & Recreations | spl | Sports, games and fitness (1.00) | | | adult (default) |
| 7 | What Is Nintendo? | Gina Shaw | Business, Games, Juvenile Nonfiction | spl | Work, business and money (0.50) ; Sports, games and fitness (0.50) | games / chess (0.50) | | children |
| 8 | The Magic in the Tragic | John Tsilimparis | Psychology, Self-Improvement, Nonfiction, Family & Relationships | spl,title | Violence, trauma, death and grief (0.50) ; Mind, self and philosophy (0.41) ; Childhood, family and growing up (0.09) | Grief and mourning (0.50) | self-help (1.00) | adult (default) |
| 9 | Becoming Fluent | Richard Roberts | Nonfiction, Science, Language Arts, Medical, Foreign Language Study, Psychology | spl,title | Science, technology and learning (0.82) ; Health, illness and addiction (0.13) ; Mind, self and philosophy (0.05) | language / language learning (0.43) ; neuroscience / cognitive science (0.25) | | adult (default) |
| 10 | Royal Rebel | Jenny Frame | Fiction, Literature, Romance, LGBTQIA+ (Fiction) | spl | Gender, sexuality and relationships (1.00) | lgbtq / gay men (1.00) | romance (1.00) | adult (default) |
| 11 | The Letter for the King | Tonke Dragt | Mythology, Young Adult Fiction, Young Adult Literature | spl | Magic, myth and the supernatural (1.00) | mythology / arthurian legend (1.00) | | young adult |
| 12 | ISIS | Jessica Stern | Nonfiction, Politics, Psychology, Sociology, History | spl | Politics, society and justice (0.59) ; Mind, self and philosophy (0.40) ; War, conflict and history (0.02) | | | adult (default) |
| 13 | I Remember | Lee Bennett Hopkins | Family & Relationships, Geography, Juvenile Nonfiction, Language Arts | spl | Science, technology and learning (0.33) ; Childhood, family and growing up (0.33) ; Nature, places and the environment (0.33) | language / language learning (0.33) ; geography / geopolitics (0.33) | | children |
| 14 | The Silence of Animals | John Gray | Nonfiction, Philosophy | spl | Mind, self and philosophy (1.00) | | | adult (default) |
| 15 | New Rules for the New Economy | Kevin Kelly | Business, Nonfiction, Management | spl | Work, business and money (1.00) | management / consulting (0.48) | | adult (default) |
| 16 | Wayfarers | Jeff Zentner | Romance, Travel Literature, Young Adult Fiction, Young Adult Literature | spl | Nature, places and the environment (1.00) | | romance (0.50) ; travel writing (0.50) | young adult |
| 17 | Computer Decoder | Andi Diehn | Biography & Autobiography, Computer Technology, Juvenile Nonfiction, Science | spl | Science, technology and learning (1.00) | computers / computer science (0.50) | biography (0.50) ; memoir (0.50) | children |
| 18 | Where Does the Money Go? | Scott Bittle | Nonfiction, Politics | spl | Politics, society and justice (1.00) | | | adult (default) |
| 19 | Destructive Emotions | Daniel Goleman | Nonfiction, Psychology, Religion & Spirituality, New Age | spl,gr | Religion and spirituality (0.51) ; Mind, self and philosophy (0.44) ; Science, technology and learning (0.04) | buddhism / sufism (0.11) ; mindfulness / meditation (0.02) ; neuroscience / cognitive science (0.01) | new age (0.50) ; self-help (0.50) | adult (default) |
| 20 | The Boy Who Dared | Susan Campbell Bartoletti | Historical Fiction, Young Adult Fiction, Young Adult Literature | gr | War, conflict and history (1.00) | holocaust / genocide (0.36) ; world war ii / world war i (0.34) | historical fiction (1.00) | young adult |

My own reading: none of the 20 is clearly wrong, but most get only broad themes from SPL terms. *ISIS: The State of Terror* gets no terrorism theme. *Horse of a Different Color* (horse breeding) gets sports but not animals. Book 7 (about Nintendo) carries the value "games", whose narrow node is labeled "games / chess", which reads oddly. Genre is empty for 10 of 20, because SPL terms such as "Nonfiction, Politics" carry no genre.

### 5.6 Suspicious merges

For each node with two or more values, I measured the least similar pair of values in the embedding used for clustering. The 15 lowest are below; the full list is `quality/suspicious_merges.csv`.

| Node | Label | Least similar pair | Similarity |
|---|---|---|---|
| B01.M02 | Magic, witches and fantasy creatures | witches <> tarot | -0.109 |
| B07.M02 | School, adolescence and coming of age | boarding school <> quarter life crisis | -0.108 |
| B05.M04 | Slavery, trafficking and immigration | prostitution <> asian american | -0.104 |
| B10.M03 | Money, investing and the economy | great depression <> real estate | -0.101 |
| B14.M02 | Ethics, mindset and motivation | ethics <> change | -0.094 |
| B14.M03 | Philosophy and belief | atheism <> fate and destiny | -0.080 |
| B11.M02 | Cooking and food | vegetarian and vegan <> coffee | -0.074 |
| B13.M05 | Social issues, poverty and social theory | critical thinking <> homelessness | -0.027 |
| B15.M04 | Disease, epidemics and public health | hiv aids <> nursing | -0.016 |
| B13.M04 | Media and communication | social media <> negotiation | -0.012 |
| B09.M05 | The sea and seafaring | pirates <> water | -0.007 |
| B04.M11 | Decision making and systems thinking | decision making <> complexity science | -0.001 |
| B16.M02 | Wild animals | wolves <> penguins | 0.002 |
| B14.M02.N02 | motivation / law of attraction | law of attraction <> change | 0.006 |
| B11.M03.N01 | home and interior design / homesteading | minimalism <> diy | 0.018 |

Several of these pairs come from my own hand edits (tarot, quarter life crisis, great depression, change, fate and destiny), where I placed a value by meaning against the embedding. Others are broad middle nodes that hold several loosely related narrow nodes, as intended. The pairs I would check first:

- prostitution next to asian american (they share a middle node, not a narrow node)
- "Social issues, poverty and social theory", which mixes critical thinking with homelessness
- "Ethics, mindset and motivation", which mixes ethics with the law of attraction

Merges that the clustering made and that I left in place on purpose:

- "slavery / prostitution / human trafficking"
- "mythology / arthurian legend / norse mythology / atlantis"
- "sexual violence / violence / domestic violence"

### 5.7 How reliable the weaker routes are

- **Title words.** I judged four random samples of 50 title matches during development: 42, 47, 44 and 47 were right. I fixed the error patterns found after each of the first three samples.
  - The last sample (`quality/title_match_sample_50.csv`, current state) had 47 of 50 right.
  - The remaining errors are loose uses of a theme word, such as "Teenage Drug Abuse" read as abuse, the memoir *Sounds Like Titanic*, and "The Secret Force of the Universe" (new-age books use "universe" often).
- **Goodreads title-only links.** 96 to 99% agreement on author surname where the author is known, and 30 of 30 correct in my sample.

## 6. Descriptive sanity view (task 5)

No modelling and no claims. Values are checkouts of works in the narrow node per 10,000 checkouts of the same format in the same month, which removes overall growth. Two work sets are shown:

- "all works": every work in the node, including books published after the event.
- "borrowed 12+ months before": only works that had already been checked out in that format at least 12 months before the event month.

The event months are those in the task. For climate change no month was given, so I used September 2019 (the global climate strikes) as a placeholder; the yearly table matters more there. Ebook values stop in mid-2022 (snapshot).

The narrow nodes used:

| Theme | Narrow node | Values in the node | Works |
|---|---|---|---|
| Epidemics and plagues | B15.M04.N05 | epidemiology, plague | 250 |
| Race and racism | B05.M02.N02 | race, interracial relationships, racism, antiracism, race relations | 409 |
| Sexual violence | B12.M01.N02 | sexual violence, violence, domestic violence | 84 |
| Climate change | B09.M07.N02 | climate change, weather | 298 |

`sanity_monthly.parquet` also holds a narrower version using only the single value (for example only "sexual violence"); the picture is the same. "Works in node" is the size of the whole node; in the "borrowed 12+ months before" rows only the older part of it contributes.

| Theme (narrow node) | Event month | Works | Format | Works in node | Mean per 10k, 6 months before | Mean per 10k, event month + 5 | After / before | Same 6 months a year earlier | After / year earlier |
|---|---|---|---|---|---|---|---|---|---|
| epidemics and plagues | 2020-03 | all works | audiobook | 250 | 9.0 | 26.4 | 2.95 | 7.0 | 3.75 |
| epidemics and plagues | 2020-03 | all works | ebook | 250 | 5.3 | 17.8 | 3.33 | 4.7 | 3.78 |
| epidemics and plagues | 2020-03 | borrowed 12+ months before | audiobook | 250 | 6.1 | 19.7 | 3.22 | 5.8 | 3.38 |
| epidemics and plagues | 2020-03 | borrowed 12+ months before | ebook | 250 | 4.2 | 11.5 | 2.77 | 4.0 | 2.89 |
| race and racism | 2020-06 | all works | audiobook | 409 | 122.8 | 413.7 | 3.37 | 123.6 | 3.35 |
| race and racism | 2020-06 | all works | ebook | 409 | 56.5 | 186.8 | 3.31 | 62.9 | 2.97 |
| race and racism | 2020-06 | borrowed 12+ months before | audiobook | 409 | 114.1 | 321.0 | 2.81 | 119.6 | 2.68 |
| race and racism | 2020-06 | borrowed 12+ months before | ebook | 409 | 53.2 | 129.1 | 2.43 | 61.0 | 2.12 |
| sexual violence | 2017-10 | all works | audiobook | 84 | 6.6 | 6.7 | 1.01 | 6.4 | 1.04 |
| sexual violence | 2017-10 | all works | ebook | 84 | 6.1 | 5.1 | 0.84 | 6.5 | 0.79 |
| sexual violence | 2017-10 | borrowed 12+ months before | audiobook | 84 | 6.2 | 5.1 | 0.82 | 6.3 | 0.81 |
| sexual violence | 2017-10 | borrowed 12+ months before | ebook | 84 | 5.7 | 4.1 | 0.73 | 6.4 | 0.64 |
| climate change | 2019-09 | all works | audiobook | 298 | 14.0 | 18.4 | 1.32 | 9.2 | 2.00 |
| climate change | 2019-09 | all works | ebook | 298 | 11.6 | 13.0 | 1.13 | 9.2 | 1.42 |
| climate change | 2019-09 | borrowed 12+ months before | audiobook | 298 | 10.0 | 7.2 | 0.72 | 9.0 | 0.80 |
| climate change | 2019-09 | borrowed 12+ months before | ebook | 298 | 7.9 | 7.9 | 1.00 | 8.7 | 0.90 |

Monthly detail around the event (per 10k, all works, audiobook / ebook):

| Theme | m-3 | m-2 | m-1 | Event month | m+1 | m+2 | m+3 |
|---|---|---|---|---|---|---|---|
| Epidemics and plagues (Dec 2019 to Jun 2020) | 7.7 / 5.7 | 7.8 / 4.7 | 10.6 / 5.8 | 16.5 / 12.1 | 20.9 / 17.8 | 33.5 / 19.8 | 26.0 / 20.4 |
| Race and racism (Mar to Sep 2020) | 113.6 / 50.9 | 98.0 / 46.2 | 123.5 / 51.2 | 909.8 / 371.7 | 495.0 / 183.9 | 328.2 / 157.7 | 288.4 / 147.6 |
| Sexual violence (Jul 2017 to Jan 2018) | 6.4 / 6.9 | 6.7 / 4.9 | 5.5 / 5.2 | 7.2 / 5.1 | 6.6 / 4.6 | 6.3 / 5.1 | 6.0 / 4.8 |
| Climate change (Jun to Dec 2019) | 17.9 / 11.4 | 15.5 / 11.9 | 12.7 / 10.2 | 26.1 / 13.8 | 22.5 / 13.2 | 16.8 / 13.3 | 15.5 / 13.0 |

Yearly level (per 10k of the format's checkouts, all works, audiobook / ebook):

| Year | Epidemics and plagues | Race and racism | Sexual violence | Climate change |
|---|---|---|---|---|
| 2016 | 7.7 / 4.9 | 46.4 / 47.7 | 7.0 / 7.2 | 6.0 / 7.0 |
| 2017 | 10.3 / 5.0 | 65.7 / 68.5 | 6.5 / 5.7 | 9.3 / 8.9 |
| 2018 | 7.7 / 3.8 | 86.0 / 76.0 | 6.9 / 5.8 | 9.7 / 9.3 |
| 2019 | 7.6 / 4.8 | 115.1 / 63.6 | 7.7 / 6.1 | 15.5 / 11.8 |
| 2020 | 23.2 / 16.7 | 281.2 / 128.7 | 6.9 / 5.2 | 14.4 / 12.3 |
| 2021 | 17.9 / 16.1 | 136.2 / 67.4 | 4.0 / 3.0 | 20.7 / 15.9 |
| 2022 | 13.6 / 14.4 | 72.8 / 40.3 | 4.8 / 3.2 | 16.3 / 13.3 |
| 2023 | 10.4 / - | 59.8 / - | 4.2 / - | 15.0 / - |
| 2024 | 9.2 / - | 51.5 / - | 3.9 / - | 13.4 / - |
| 2025 | 8.7 / - | 42.9 / - | 4.9 / - | 10.9 / - |

Whether a visible change exists:

- **Epidemics and plagues:** yes, from March 2020. The rise is about 3 times, also for works borrowed before.
- **Race and racism:** yes, in June 2020. It is about 7 times the May value for audiobooks, about 3 times over the six months, and also present for works borrowed before.
- **Sexual violence:** no visible change around October 2017.
- **Climate change:** the "all works" September 2019 spike comes from new titles. For works borrowed before there is no visible change in that month. The yearly level is higher from 2019 to 2022 than before.

The sexual violence node is small (84 works) because none of the sources has more than thin coverage of this theme: Goodreads "rape" (125 works) and title words.

## 7. Facet and assignment examples (for a quick feel)

- **Goodreads shelf to parts.**
  - "ya-fantasy" becomes audience=young adult plus genre=fantasy.
  - "wwii" becomes theme=world war ii.
  - "books-set-in-paris" becomes place=paris.
  - "1920s" becomes period=1920s.
  - "made-me-cry" becomes other=mood.
  - "alpha-male" becomes other=trope.
- **SPL term to parts.**
  - "African American Fiction" becomes theme=african american life plus form=fiction.
  - "True Crime" becomes genre=true crime plus theme=crime.
  - "Regency" becomes genre=historical romance plus period=regency era.
- **Wikidata subject to parts.**
  - "England in the Middle Ages" becomes place=england plus period=middle ages.
  - "Global warming" becomes theme=climate change.
  - "Karl Marx" becomes other=person.

## 8. Decisions I made and why

| # | Decision | Why |
|---|---|---|
| D1 | Froze the ebook file at the 6,249,992 complete lines present at the start (`spl_snapshot.json`); every script reads exactly these lines | The file was being appended; results must be reproducible |
| D2 | Checked file completeness against small aggregate API queries (`00_spl_api_counts.py`, five queries to data.seattle.gov) | The audiobook file had to be confirmed complete, and the partial ebook months identified |
| D3 | A work's subject terms are pooled over all its records, weighted by checkouts | OverDrive renames terms over time; pooling gives each book one stable set of themes, so later theme series are not broken by relabeling |
| D4 | A phrase can carry several facet parts instead of one facet | Compound labels such as "Juvenile Fiction" or "ya-fantasy" mix audience, genre and form |
| D5 | Goodreads shelves used on fewer than 10 Goodreads works were dropped; a shelf mostly on one author's works counts as an author or series shelf | Noise and personal shelves dominate the long tail |
| D6 | Supernatural beings (vampires, dragons, ghosts) and settings such as school life count as themes; romance tropes and moods are kept as "other" with their own subtype; genre labels such as dystopian or cozy mystery stay genres | Follows the brief's line (genre = kind of story, theme = what it is about), and keeps tropes and moods available for later use |
| D7 | Named wars and events (World War II, the Holocaust, 9/11) are themes, not periods; eras without an event (Victorian, 1920s) are periods | Events are what news and Wikipedia interest attach to |
| D8 | People (Lincoln, Freud, Trump) are "other: person", except religious figures used as subjects (Jesus, Mary) | A person is not a theme; see open question 9 |
| D9 | Embedding text "books about X" plus hand glosses for ambiguous values; Ward clustering on one tree; 51 hand edits | Bare short words clustered by spelling ("depression" with "great depression"); one tree guarantees the three levels nest |
| D10 | Very general values (history, politics, psychology...) are attached at broad or middle level, never narrow | As asked in the brief; they are also the most common SPL terms |
| D11 | Strength = mean of per-source shares over the sources present | Simple and transparent; per-source shares are saved so the student can change it |
| D12 | Title-word evidence only for nonfiction, with hand surfaces and blocking patterns | Fiction titles are metaphorical; nonfiction titles carry the topic ("How to Be an Antiracist", "The Great Influenza") |
| D13 | Goodreads links by title alone only for distinctive titles, unique on both sides, with compatible subtitles, and not for books published and first borrowed after 2017 | Only 30% of local Goodreads works have an author name; title-only links were checked against known authors (96 to 99% agreement) |
| D14 | The sanity view is measured per 10,000 checkouts of the format, with a "borrowed 12+ months before" subset | Removes overall growth, and separates readers returning to older books from new books on the topic |

## 9. Open questions for Khant

The five I think matter most come first.

1. **Should narrow themes come from print-book subject headings?**
   - The digital subjects cannot provide them (section 2.3), while the print records carry library subject headings.
   - The print download (25.8 million rows) is running now.
   - A plan: build print works the same way, match them to digital works by normalized title and creator, and add their headings as a fourth theme source.
   - I expect this to give most popular fiction narrow themes (grief, racism, war, climate) without Goodreads. It needs your agreement because it changes the main source of themes.
2. **Should we get more Goodreads author names, or another source for books after 2017?**
   - Goodreads links reach 18% of checkouts. The local author-name file covers only the authors matched in the earlier LibriVox step, and Goodreads ends in 2017.
   - Option A: download the full UCSD `goodreads_book_authors.json.gz` (small; the same academic source as `code/goodreads.py`). This would let author-based links replace most title-only links.
   - Option B: wait for the Amazon 2023 category paths from `modern_books.py`.
   - Option C: use Open Library subjects by ISBN (2.1 million audiobook rows carry ISBNs; official API).
   - I did not download anything new without asking.
3. **Keep or drop title words as evidence?** They add themes to 4.6% of works and supply most of the epidemic and racism nonfiction in the sanity view. In the last sample 47 of 50 were right, but they are a hand-rule method, not a book catalogue. Options:
   - keep them as a separate, weaker source
   - give them a lower weight in the strength formula
   - use them only to check the other sources
4. **Is the hierarchy shape right?** Please read section 4.2 and `theme_nodes.parquet`. The places where I made a judgment:
   - Psychology sits with mind and self, and mental illness with health.
   - History is attached to the war broad node.
   - Medieval history and monarchy is under war and history, not fantasy.
   - Climate sits with environment.
   - 19 broad nodes, with a few small ones (Space 391 works; Violence, trauma, death and grief 946 works).

   Should narrow nodes be larger? Many have only one or two values.
5. **What should happen next with the positive controls?**
   - Race (June 2020) and epidemics (March 2020) show visible changes, which is encouraging.
   - Sexual violence (October 2017) has only 84 works and shows nothing, so it cannot serve as a positive control in its current form.
   - Should we rebuild it after question 1, choose a different control, or report it as a null?
   - Should the checkpoint be rerun on the full ebook file first? It is now complete.

Further questions:

6. **Should moods (sad, dark, hopeful) become their own facet?** That could help the sentiment research question. They are currently "other: mood" (80 phrases).
7. **Should people become a facet** (biographies of Lincoln, Obama, Freud)? Interest in people moves Wikipedia views strongly, but people are not themes.
8. **How should the gaps be handled in later monthly series?** The three missing digital months (May and June 2024, August 2025) and the April 2022 audiobook dip need a rule, for example treating them as missing rather than zero.
9. **Should OverDrive's very broad terms count as themes at all?** History, Sociology, Psychology, Politics, Science and Self-Improvement cover 2 to 6% of checkouts each. They are why "War, conflict and history" and "Mind, self and philosophy" are the largest broad nodes.
10. **Should language courses and graded readers be excluded from demand series?** Pimsleur lessons and National Geographic Readers are many small works that are not reading for interest.
11. **Is "adult (default)" acceptable** when neither SPL nor Goodreads names an audience (most adult nonfiction)?

## 10. Files, how to rerun, and run times

Code (`code/main_study/`). Each script is re-runnable and imports paths from `code/config.py` through `_common.py`.

| Script | What it does | Run time (last run) |
|---|---|---|
| `00_spl_api_counts.py` | Five small aggregate API queries; freezes the ebook line count | 72 s |
| `01_spl_rows.py` | Streams both raw files once into compact Parquet (peak memory about 0.9 GB) | 64 s |
| `02_spl_profile.py` | Profile tables (section 2) | 79 to 118 s |
| `03_spl_title_table.py` | Work-level table | 297 s |
| `04_goodreads_link.py` | Goodreads works and links | 42 s |
| `05_phrases_facets.py` | Phrases and facets | 2 s with the embedding cache (about 1 min on first run, including the model download) |
| `06_theme_hierarchy.py` | Clustering, hand edits, labels | 1 s |
| `07_assign_works.py` | Themes, genres, audience and form per work | 7 s |
| `08_quality_checks.py` | Section 5 tables | 4 s |
| `09_sanity_series.py` | Section 6 tables | 5 s |
| `run_all.sh` | Runs all in order (`SKIP_API=1` skips 00) | about 10 minutes in total |

Hand inputs, all readable as plain lists:
- `_lexicon.py`: facet word lists, SPL term table, title rules
- `_review.py`: about 1,500 hand decisions on phrases
- `_labels.py`: glosses, hierarchy edits, labels

Data (`data/db/taxonomy_v2/`, 249 MB):
- `spl_records`, `spl_rows_audiobook`, `spl_rows_ebook`, `spl_record_work`, `spl_works`
- `goodreads_works`, `spl_goodreads_link`
- `phrases` (+ `phrases_review.csv`), `theme_values`, `theme_nodes`, `theme_value_node`
- `work_theme`, `work_theme_value`, `work_genre`, `work_audience`, `work_audience_label`, `work_form`
- `sanity_monthly`
- `profile/`, `quality/`

Nothing in `code/` outside `main_study/`, in `jobs/`, or in `data/raw/` was changed, and no running job was touched.
