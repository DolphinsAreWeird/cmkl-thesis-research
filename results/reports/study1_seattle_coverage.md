# Study 1 (Seattle new titles): coverage of pre-release attention signals

Author: Khant Phyo Wai (CMKL University). Coverage check only: no borrowing outcomes were read or modelled.

Run on 2026-10-14; sample seed 20261014; run time 0 minutes.

## What was measured

A new title in a format is a work whose first Seattle month in that format falls in 2017-01 to 2025-06 and whose earliest publication year is at most one year before the year of that first month. The first day of the first Seattle month stands in for the release date. Each cell below (format by cohort year) holds a random sample of 80 works (all works if fewer). Shares are out of the sampled works, with Wilson 95% intervals in brackets. A work with no creator on its Seattle record cannot have an author signal and counts as "no".

Signals: (1) Open Library reading-log entries dated before the first Seattle month; (2) an English Wikipedia article about the book that was created at least 4 weeks before that month; (3) the same for the first author. "Any signal" is one of the three.

## Population and sample

| format | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | total |
|---|---|---|---|---|---|---|---|---|---|---|
| book | 19,056 | 19,063 | 18,444 | 6,971 | 20,000 | 17,099 | 17,729 | 15,026 | 7,601 | 140,989 |
| ebook | 9,191 | 8,167 | 7,502 | 11,494 | 12,761 | 13,122 | 12,535 | 13,009 | 7,652 | 95,433 |
| audiobook | 3,248 | 2,798 | 3,199 | 4,925 | 5,749 | 6,452 | 6,481 | 7,065 | 3,782 | 43,699 |

Counts are works (one Seattle title family, all editions together). The 2020 book cohort is small and the 2021 book cohort is large; this follows the Seattle first-month dates in the data and has not been investigated here.

Sampled works: 2,160 rows (2,152 distinct works; a work can be drawn in more than one format).

## Open Library match

| format | cohort | n | any match | by ISBN | by title and author |
|---|---|---|---|---|---|
| book | 2017 | 80 | 82% (73-89) | 24% (16-34) | 59% (48-69) |
| book | 2018 | 80 | 81% (71-88) | 19% (12-29) | 62% (52-72) |
| book | 2019 | 80 | 80% (70-87) | 25% (17-35) | 55% (44-65) |
| book | 2020 | 80 | 78% (67-85) | 29% (20-39) | 49% (38-60) |
| book | 2021 | 80 | 78% (67-85) | 24% (16-34) | 54% (43-64) |
| book | 2022 | 80 | 76% (66-84) | 29% (20-39) | 48% (37-58) |
| book | 2023 | 80 | 71% (61-80) | 29% (20-39) | 42% (32-53) |
| book | 2024 | 80 | 60% (49-70) | 26% (18-37) | 34% (24-45) |
| book | 2025 | 80 | 61% (50-71) | 20% (13-30) | 41% (31-52) |
| book | pooled | 720 | 75% (72-79) | 25% (22-28) | 51% (47-54) |
| ebook | 2017 | 80 | 88% (78-93) | 45% (35-56) | 42% (32-53) |
| ebook | 2018 | 80 | 94% (86-97) | 51% (40-62) | 42% (32-53) |
| ebook | 2019 | 80 | 88% (78-93) | 31% (22-42) | 56% (45-67) |
| ebook | 2020 | 80 | 85% (76-91) | 58% (47-68) | 28% (19-38) |
| ebook | 2021 | 80 | 92% (85-97) | 52% (42-63) | 40% (30-51) |
| ebook | 2022 | 80 | 86% (77-92) | 55% (44-65) | 31% (22-42) |
| ebook | 2023 | 80 | 86% (77-92) | 55% (44-65) | 31% (22-42) |
| ebook | 2024 | 80 | 71% (61-80) | 38% (28-48) | 34% (24-45) |
| ebook | 2025 | 80 | 70% (59-79) | 35% (25-46) | 35% (25-46) |
| ebook | pooled | 720 | 84% (82-87) | 48% (44-52) | 37% (33-40) |
| audiobook | 2017 | 80 | 96% (90-99) | 54% (43-64) | 42% (32-53) |
| audiobook | 2018 | 80 | 96% (90-99) | 50% (39-61) | 46% (36-57) |
| audiobook | 2019 | 80 | 89% (80-94) | 44% (33-55) | 45% (35-56) |
| audiobook | 2020 | 80 | 82% (73-89) | 45% (35-56) | 38% (28-48) |
| audiobook | 2021 | 80 | 89% (80-94) | 64% (53-73) | 25% (17-35) |
| audiobook | 2022 | 80 | 80% (70-87) | 49% (38-60) | 31% (22-42) |
| audiobook | 2023 | 80 | 89% (80-94) | 51% (40-62) | 38% (28-48) |
| audiobook | 2024 | 80 | 74% (63-82) | 46% (36-57) | 28% (19-38) |
| audiobook | 2025 | 80 | 74% (63-82) | 42% (32-53) | 31% (22-42) |
| audiobook | pooled | 720 | 84% (81-87) | 50% (46-54) | 34% (31-38) |

Pooled rows weight each cohort year by its population size (stratified estimate and interval).

## Reading-log entries before release

| format | cohort | n | any entry before release | median count, all time / last 26 weeks (Open Library matches) | median count among works with at least one entry |
|---|---|---|---|---|---|
| book | 2017 | 80 | 0% (0-5) | 0 / 0 | n/a |
| book | 2018 | 80 | 0% (0-5) | 0 / 0 | n/a |
| book | 2019 | 80 | 0% (0-5) | 0 / 0 | n/a |
| book | 2020 | 80 | 2% (1-9) | 0 / 0 | 2 / 2 (n=2) |
| book | 2021 | 80 | 6% (3-14) | 0 / 0 | 1 / 1 (n=5) |
| book | 2022 | 80 | 5% (2-12) | 0 / 0 | 2 / 2 (n=4) |
| book | 2023 | 80 | 15% (9-24) | 0 / 0 | 1 / 1 (n=12) |
| book | 2024 | 80 | 14% (8-23) | 0 / 0 | 1 / 1 (n=11) |
| book | 2025 | 80 | 5% (2-12) | 0 / 0 | 1 / 0 (n=4) |
| book | pooled | 720 | 5% (4-7) | 0 / 0 | 1 / 1 (n=38) |
| ebook | 2017 | 80 | 0% (0-5) | 0 / 0 | n/a |
| ebook | 2018 | 80 | 1% (0-7) | 0 / 0 | 2 / 2 (n=1) |
| ebook | 2019 | 80 | 0% (0-5) | 0 / 0 | n/a |
| ebook | 2020 | 80 | 6% (3-14) | 0 / 0 | 1 / 1 (n=5) |
| ebook | 2021 | 80 | 10% (5-19) | 0 / 0 | 1 / 0 (n=8) |
| ebook | 2022 | 80 | 9% (4-17) | 0 / 0 | 1 / 1 (n=7) |
| ebook | 2023 | 80 | 18% (11-27) | 0 / 0 | 2 / 1 (n=14) |
| ebook | 2024 | 80 | 11% (6-20) | 0 / 0 | 8 / 1 (n=9) |
| ebook | 2025 | 80 | 8% (3-15) | 0 / 0 | 2 / 1 (n=6) |
| ebook | pooled | 720 | 8% (6-10) | 0 / 0 | 2 / 1 (n=50) |
| audiobook | 2017 | 80 | 0% (0-5) | 0 / 0 | n/a |
| audiobook | 2018 | 80 | 1% (0-7) | 0 / 0 | 1 / 1 (n=1) |
| audiobook | 2019 | 80 | 0% (0-5) | 0 / 0 | n/a |
| audiobook | 2020 | 80 | 5% (2-12) | 0 / 0 | 2 / 2 (n=4) |
| audiobook | 2021 | 80 | 5% (2-12) | 0 / 0 | 2 / 1 (n=4) |
| audiobook | 2022 | 80 | 15% (9-24) | 0 / 0 | 2 / 2 (n=12) |
| audiobook | 2023 | 80 | 21% (14-31) | 0 / 0 | 1 / 1 (n=17) |
| audiobook | 2024 | 80 | 6% (3-14) | 0 / 0 | 1 / 1 (n=5) |
| audiobook | 2025 | 80 | 10% (5-19) | 0 / 0 | 2 / 1 (n=8) |
| audiobook | pooled | 720 | 9% (6-11) | 0 / 0 | 1 / 1 (n=51) |

The first median is over works with an Open Library match and counts zeros. The second is over works with at least one entry before release. Shares are out of all sampled works.

## Wikipedia article about the book, created 4+ weeks before release

| format | cohort | n | book article | Wikidata item found |
|---|---|---|---|---|
| book | 2017 | 80 | 0% (0-5) | 12% (7-22) |
| book | 2018 | 80 | 0% (0-5) | 16% (10-26) |
| book | 2019 | 80 | 2% (1-9) | 12% (7-22) |
| book | 2020 | 80 | 4% (1-10) | 9% (4-17) |
| book | 2021 | 80 | 0% (0-5) | 5% (2-12) |
| book | 2022 | 80 | 0% (0-5) | 9% (4-17) |
| book | 2023 | 80 | 0% (0-5) | 8% (3-15) |
| book | 2024 | 80 | 1% (0-7) | 8% (3-15) |
| book | 2025 | 80 | 0% (0-5) | 4% (1-10) |
| book | pooled | 720 | 1% (0-1) | 10% (7-12) |
| ebook | 2017 | 80 | 1% (0-7) | 15% (9-24) |
| ebook | 2018 | 80 | 4% (1-10) | 16% (10-26) |
| ebook | 2019 | 80 | 4% (1-10) | 12% (7-22) |
| ebook | 2020 | 80 | 2% (1-9) | 10% (5-19) |
| ebook | 2021 | 80 | 0% (0-5) | 16% (10-26) |
| ebook | 2022 | 80 | 2% (1-9) | 12% (7-22) |
| ebook | 2023 | 80 | 2% (1-9) | 9% (4-17) |
| ebook | 2024 | 80 | 1% (0-7) | 8% (3-15) |
| ebook | 2025 | 80 | 0% (0-5) | 4% (1-10) |
| ebook | pooled | 720 | 2% (1-3) | 11% (9-14) |
| audiobook | 2017 | 80 | 1% (0-7) | 21% (14-31) |
| audiobook | 2018 | 80 | 1% (0-7) | 24% (16-34) |
| audiobook | 2019 | 80 | 2% (1-9) | 26% (18-37) |
| audiobook | 2020 | 80 | 5% (2-12) | 19% (12-29) |
| audiobook | 2021 | 80 | 2% (1-9) | 15% (9-24) |
| audiobook | 2022 | 80 | 1% (0-7) | 14% (8-23) |
| audiobook | 2023 | 80 | 0% (0-5) | 15% (9-24) |
| audiobook | 2024 | 80 | 1% (0-7) | 21% (14-31) |
| audiobook | 2025 | 80 | 4% (1-10) | 18% (11-27) |
| audiobook | pooled | 720 | 2% (1-3) | 18% (15-21) |

## Wikipedia article about the author, created 4+ weeks before release

| format | cohort | n | author article | has creator |
|---|---|---|---|---|
| book | 2017 | 80 | 31% (22-42) | 99% (93-100) |
| book | 2018 | 80 | 31% (22-42) | 100% (95-100) |
| book | 2019 | 80 | 38% (28-48) | 100% (95-100) |
| book | 2020 | 80 | 39% (29-50) | 100% (95-100) |
| book | 2021 | 80 | 29% (20-39) | 99% (93-100) |
| book | 2022 | 80 | 21% (14-31) | 99% (93-100) |
| book | 2023 | 80 | 26% (18-37) | 100% (95-100) |
| book | 2024 | 80 | 31% (22-42) | 99% (93-100) |
| book | 2025 | 80 | 28% (19-38) | 100% (95-100) |
| book | pooled | 720 | 30% (27-34) | 99% (99-100) |
| ebook | 2017 | 80 | 36% (27-47) | 100% (95-100) |
| ebook | 2018 | 80 | 39% (29-50) | 100% (95-100) |
| ebook | 2019 | 80 | 39% (29-50) | 100% (95-100) |
| ebook | 2020 | 80 | 41% (31-52) | 100% (95-100) |
| ebook | 2021 | 80 | 39% (29-50) | 100% (95-100) |
| ebook | 2022 | 80 | 36% (27-47) | 100% (95-100) |
| ebook | 2023 | 80 | 38% (28-48) | 99% (93-100) |
| ebook | 2024 | 80 | 39% (29-50) | 100% (95-100) |
| ebook | 2025 | 80 | 20% (13-30) | 100% (95-100) |
| ebook | pooled | 720 | 37% (33-40) | 100% (100-100) |
| audiobook | 2017 | 80 | 51% (40-62) | 100% (95-100) |
| audiobook | 2018 | 80 | 55% (44-65) | 100% (95-100) |
| audiobook | 2019 | 80 | 50% (39-61) | 100% (95-100) |
| audiobook | 2020 | 80 | 50% (39-61) | 100% (95-100) |
| audiobook | 2021 | 80 | 48% (37-58) | 100% (95-100) |
| audiobook | 2022 | 80 | 34% (24-45) | 100% (95-100) |
| audiobook | 2023 | 80 | 45% (35-56) | 100% (95-100) |
| audiobook | 2024 | 80 | 38% (28-48) | 100% (95-100) |
| audiobook | 2025 | 80 | 45% (35-56) | 100% (95-100) |
| audiobook | pooled | 720 | 44% (41-48) | 100% (100-100) |

## At least one signal

| format | cohort | n | any signal | Wikipedia signals only |
|---|---|---|---|---|
| book | 2017 | 80 | 31% (22-42) | 31% (22-42) |
| book | 2018 | 80 | 31% (22-42) | 31% (22-42) |
| book | 2019 | 80 | 39% (29-50) | 39% (29-50) |
| book | 2020 | 80 | 41% (31-52) | 39% (29-50) |
| book | 2021 | 80 | 32% (23-43) | 29% (20-39) |
| book | 2022 | 80 | 24% (16-34) | 21% (14-31) |
| book | 2023 | 80 | 38% (28-48) | 26% (18-37) |
| book | 2024 | 80 | 40% (30-51) | 31% (22-42) |
| book | 2025 | 80 | 29% (20-39) | 28% (19-38) |
| book | pooled | 720 | 34% (30-37) | 30% (27-34) |
| ebook | 2017 | 80 | 36% (27-47) | 36% (27-47) |
| ebook | 2018 | 80 | 39% (29-50) | 39% (29-50) |
| ebook | 2019 | 80 | 39% (29-50) | 39% (29-50) |
| ebook | 2020 | 80 | 41% (31-52) | 41% (31-52) |
| ebook | 2021 | 80 | 45% (35-56) | 39% (29-50) |
| ebook | 2022 | 80 | 39% (29-50) | 36% (27-47) |
| ebook | 2023 | 80 | 44% (33-55) | 38% (28-48) |
| ebook | 2024 | 80 | 46% (36-57) | 39% (29-50) |
| ebook | 2025 | 80 | 22% (15-33) | 20% (13-30) |
| ebook | pooled | 720 | 40% (36-44) | 37% (33-40) |
| audiobook | 2017 | 80 | 51% (40-62) | 51% (40-62) |
| audiobook | 2018 | 80 | 55% (44-65) | 55% (44-65) |
| audiobook | 2019 | 80 | 51% (40-62) | 51% (40-62) |
| audiobook | 2020 | 80 | 50% (39-61) | 50% (39-61) |
| audiobook | 2021 | 80 | 49% (38-60) | 48% (37-58) |
| audiobook | 2022 | 80 | 41% (31-52) | 35% (25-46) |
| audiobook | 2023 | 80 | 54% (43-64) | 45% (35-56) |
| audiobook | 2024 | 80 | 39% (29-50) | 38% (28-48) |
| audiobook | 2025 | 80 | 46% (36-57) | 45% (35-56) |
| audiobook | pooled | 720 | 47% (44-51) | 45% (41-49) |

## Trend in "any signal" by cohort year (sample share, %)

| format | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|
| book | 31 | 31 | 39 | 41 | 32 | 24 | 38 | 40 | 29 |
| ebook | 36 | 39 | 39 | 41 | 45 | 39 | 44 | 46 | 22 |
| audiobook | 51 | 55 | 51 | 50 | 49 | 41 | 54 | 39 | 46 |

## Match quality

- Distinct sampled works: 2,152. With at least one valid ISBN on any record: 78%. Print-only works have no ISBN, so they depend on the title and author search.
- Open Library: 866 by ISBN, 883 by title and author search, 403 without a match (5 of these had no creator and no usable ISBN, so the search was not tried).
- Of the ISBN matches, 95% have an Open Library edition title that agrees with the Seattle title; the rest may be a wrong ISBN on a Seattle record or a different title for the same work.
- Title and author search accepts a hit only when the normalised title equals the Seattle main title or full title (leading "The", "A" or "An" ignored) and the author family name appears in the Open Library author list. This is strict, so it misses retitled editions and works with the author in a different spelling, and it can still accept a different book with the same title by a relative with the same family name.
- Wikidata book item found for 281 works (20 by ISBN, 62 through the Open Library ID, 199 by title and author). Wikidata mostly stores ISBNs with hyphens, so the script tries the plausible hyphenations of each ISBN.
- Book article found for 111 works. The article date is the first revision of the page at its current title; a page first created as a redirect or stub counts from that first revision.
- Author: 921 works have a Wikidata person with an English article, matched on exact name (case, accents and punctuation ignored) plus a writing occupation or a notable work; 210 of these are confirmed by the book item naming the same person as author. 45 works had more than one qualifying namesake (the first was used). Exact name matching misses authors whose Seattle name includes a middle name or initial that Wikidata lacks, and it can match a different person with the same name.
- 5 sampled works have no creator on the Seattle record, so no author match was possible.
- The reading-log dump holds the current state of each user shelf, so entries are dated by when the user added the book. Open Library merges duplicate works over time and the dump uses current keys; a key from an old match may be redirected and show a count of zero.

## Book matches to check by hand (random 30)

| title | creator | method | matched item | Wikipedia article |
|---|---|---|---|---|
| Lei and the invisible island | Maunakea, Malia | title_author | Q135491911 Lei and the Invisible Island |  |
| The Tainted Cup | Robert Jackson Bennett | title_author | Q133897285 The Tainted Cup | The Tainted Cup |
| Exit West | Mohsin Hamid | isbn | Q141061583 Exit West | Exit West |
| The Cabinet | Un-su Kim | ol_id | Q111516767 The Cabinet |  |
| A Little History of Economics | Niall Kishtainy | title_author | Q139267311 A Little History of Economics |  |
| My Twenty-Five Years in Provence: Reflections on Then and Now | Peter Mayle | title_author | Q141124786 My Twenty-Five Years in Provence |  |
| Beyond All Reasonable Doubt | Malin Persson Giolito | title_author | Q134884917 Beyond All Reasonable Doubt |  |
| Harry Sylvester Bird | Chinelo Okparanta | ol_id | Q111292263 Harry Sylvester Bird | Harry Sylvester Bird |
| El bosque oscuro | Cixin Liu | title_author | Q607276 The Dark Forest | The Dark Forest |
| Heavenly Tyrant | Xiran Jay Zhao | ol_id | Q125198794 Heavenly Tyrant |  |
| Or What You Will | Jo Walton | ol_id | Q107610482 Or What You Will | Or What You Will |
| Fight like a girl | Ford, Clementine, | ol_id | Q126947622 Fight Like a Girl | Fight Like a Girl (book) |
| Kakegurui : compulsive gambler. 9 | Kawamoto, Homura | title_author | Q18700981 Kakegurui | Kakegurui |
| Djinn city | Hossain, Saad Z. | title_author | Q134478935 Djinn City |  |
| The seventh function of language | Binet, Laurent | title_author | Q21027313 The Seventh Function of Language |  |
| This Is Not the Jess Show | Anna Carey | title_author | Q135088661 This Is Not the Jess Show |  |
| Now I Rise | Kiersten White | title_author | Q134711057 Now I Rise |  |
| The Known Citizen | Sarah E. Igo | ol_id | Q137271752 The Known Citizen: A History of Privacy in Modern America |  |
| African Town : inspired by the true story of the last American slave s | Latham, Irene | title_author | Q116756079 African Town | African Town |
| The New Corner Office: How the Most Successful People Work from Home | Laura Vanderkam | title_author | Q140987714 The New Corner Office |  |
| Melting pot or civil war? : a son of immigrants makes the case against | Salam, Reihan | title_author | Q85784877 Melting Pot or Civil War? | Melting Pot or Civil War? |
| Three debts paid : a Daniel Pitt novel | Perry, Anne | isbn | Q140988915 Three Debts Paid |  |
| The End of Everything: How Wars Descend into Annihilation | Victor Davis Hanson | title_author | Q138504303 The End of Everything: How Wars Descend into Annihilation |  |
| Spells Like Teen Spirit | Kate M. Williams | title_author | Q134464476 Spells Like Teen Spirit |  |
| Dragon ghosts | McMann, Lisa | title_author | Q134582031 Dragon Ghosts |  |
| Star of the Sea | Joseph O'Connor | title_author | Q7601269 Star of the Sea | Star of the Sea (novel) |
| The Splendid City | Karen Heuler | title_author | Q133954977 The Splendid City |  |
| Last night at the Telegraph Club | Lo, Malinda | ol_id | Q109637332 Last Night at the Telegraph Club | Last Night at the Telegraph Club |
| The fall of dragons | Cameron, Miles | ol_id | Q120435495 The Fall of Dragons |  |
| Riot Baby | Tochi Onyebuchi | ol_id | Q108089920 Riot Baby | Riot Baby |

## Author matches to check by hand (random 30)

| title | creator | method | matched item | Wikipedia article |
|---|---|---|---|---|
| Desolation Code | Graham Brown | name_occupation, 1 candidate(s) | Q18707490 Graham Brown | Graham Brown (footballer, born 1944) |
| Someone to Love | Melissa de la Cruz | name_occupation, 1 candidate(s) | Q2603691 Melissa de la Cruz | Melissa de la Cruz |
| The last kids on Earth and the midnight blade | Brallier, Max | name_occupation_book_author, 1 candidate(s) | Q54972791 Max Brallier | Max Brallier |
| Face : a visual odyssey | Helfand, Jessica | name_occupation, 1 candidate(s) | Q16247168 Jessica Helfand | Jessica Helfand |
| Heretic dawn | Merle, Robert, 1908-2004, | name_occupation_book_author, 1 candidate(s) | Q315949 Robert Merle | Robert Merle |
| The Girls Who Disappeared | Claire Douglas | name_occupation, 1 candidate(s) | Q110368341 Claire Douglas | Claire Douglas |
| The Weather Handbook: The Essential Guide to How Weather is Formed and | Alan Watts | name_occupation, 1 candidate(s) | Q354867 Alan Watts | Alan Watts |
| Show us who you are | McNicoll, Elle | name_occupation, 1 candidate(s) | Q97577314 Elle McNicoll | Elle McNicoll |
| My marriage | Wassermann, Jakob, 1873-1934, | name_occupation_book_author, 1 candidate(s) | Q60369 Jakob Wassermann | Jakob Wassermann |
| Uncommon people : the rise and fall of the rock stars | Hepworth, David, 1950- | name_occupation, 1 candidate(s) | Q5234933 David Hepworth | David Hepworth |
| Her Daughter's Mother | Daniela Petrova | name_occupation, 1 candidate(s) | Q110235499 Daniela Petrova | Daniela Petrova |
| The best horror of the year. Volume eleven | Ellen Datlow | name_occupation, 1 candidate(s) | Q1810264 Ellen Datlow | Ellen Datlow |
| Jinsei wa utsukushii koto dake oboete ireba ii | Satō, Aiko, 1923- | name_occupation, 1 candidate(s) | Q11384030 Aiko Satō | Aiko Satō (writer) |
| Elmet | Mozley, Fiona | name_occupation_book_author, 1 candidate(s) | Q41808358 Fiona Mozley | Fiona Mozley |
| Not quite a genius | Dern, Nate. | name_occupation, 1 candidate(s) | Q47658478 Nate Dern | Nate Dern |
| In the Region of the Summer Stars | Stephen R. Lawhead | name_occupation_book_author, 1 candidate(s) | Q602510 Stephen R. Lawhead | Stephen R. Lawhead |
| Blueberry Blunder | Amanda Flower | name_occupation, 1 candidate(s) | Q18921731 Amanda Flower | Amanda Flower |
| The Intended Victim | Alexandra Ivy | name_occupation, 1 candidate(s) | Q2833282 Alexandra Ivy | Alexandra Ivy |
| Jacaranda: Prix Renaudot 2024 | Gaël Faye | name_occupation, 1 candidate(s) | Q16638763 Gaël Faye | Gaël Faye |
| I Can't Even Think Straight | Dean Atta | name_occupation, 1 candidate(s) | Q56809105 Dean Atta | Dean Atta |
| Pain studies | Olstein, Lisa, 1972- | name_occupation_book_author, 1 candidate(s) | Q30501755 Lisa Olstein | Lisa Olstein |
| Kingsbane | Claire Legrand | name_occupation_book_author, 1 candidate(s) | Q20900061 Claire Legrand | Claire Legrand |
| Build your algorithm skills | Harris, Christopher, 1977- | name_occupation, 1 candidate(s) | Q13422722 Zeuss | Zeuss |
| Changeling | Ritter, William, 1984- | name_occupation, 1 candidate(s) | Q3568909 William Ritter | William Ritter (writer) |
| Ellis Johnson might be famous | Amos, Shawn | name_occupation, 1 candidate(s) | Q7491287 Shawn Amos | Shawn Amos |
| Sharuko : el arqueólogo Peruano Julio C. Tello = Peruvian archaeologis | Brown, Monica, 1969- | name_occupation, 2 candidate(s) | Q231487 Monica | Monica (singer) |
| The memory thieves | Clayton, Dhonielle | name_occupation_book_author, 1 candidate(s) | Q86984542 Dhonielle Clayton | Dhonielle Clayton |
| Lakeside Love | Kathleen Fuller | name_occupation, 1 candidate(s) | Q6376714 Kathleen Fuller | Kathleen Fuller |
| The house of love | Trigiani, Adriana | name_occupation, 1 candidate(s) | Q375217 Adriana Trigiani | Adriana Trigiani |
| The Devil May Dance | Jake Tapper | name_occupation_book_author, 1 candidate(s) | Q6125032 Jake Tapper | Jake Tapper |
