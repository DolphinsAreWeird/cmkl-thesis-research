# Main study, checkpoint 2: taxonomy v3 (print subject headings as the main theme source)

Khant Phyo Wai (student ID 01323050), CMKL University, honors thesis
Prepared 13 October 2026, final version (full print file). Status: draft for Khant's review. Nothing here is a result. It describes the categories and the data that later steps use.

**Data status.** All three SPL files are now read in full: print 25,791,712 rows, audiobook 4,697,512 rows and ebook 9,685,032 rows. Each one equals the SPL API row count in every month. The print download wrote `BOOK DONE` at 20:28, and the final run (`REFRESH_SNAPSHOT=1 ./run_all.sh v3`) started at 20:29. An earlier version of this report was built on a print snapshot that ended in September 2020; every number below replaces it.

## Summary

- **Print headings are the main theme source.**
  - 93.2% of the 1,109,523 print records carry library subject headings, 3.9 per record on average.
  - The headings reach audiobooks and ebooks through the shared work id (normalized title + creator). 159,959 of the 254,933 digital works (62.7%) have print headings, and these works carry 83.7% of digital checkouts.
- **The approved tree is unchanged.**
  - The 19 broad, 86 middle and 241 narrow nodes keep their ids, labels and places.
  - One narrow node was added and approved: B12.M01.N04 "Violence and violent crime".
- **New theme values.** 29,064 new values from the headings were decided:
  - 416 by hand: 351 placed in a node, and 65 judged not to be themes;
  - 1,047 by hand pattern rules, mostly for the control categories;
  - 27,601 by the nearest node in the v2 embedding space, at similarity 0.50 or more.

  19,356 values on 3 or more works stayed unplaced. Every hand decision is logged with a reason.
- **Library of Congress renames (last pass).** A heading that LC renamed now takes the placement of the heading it replaced, in every node:
  - 18 renames are applied, for example "Racially mixed people" to "Multiracial people" and "Whites" to "White people";
  - each is logged with the old and new form and with evidence from the SPL records;
  - 678 works changed their set of themes, and 62 works were added to race and racism. No other control changed.
- **Coverage of digital works (main assignment, title words not used).**

  | Measure | v3 works | v3 checkouts | v2 works | v2 checkouts |
  |---|---|---|---|---|
  | Any theme | 74.6% | 87.9% | 41.3% | 41.5% |
  | Narrow theme | 64.8% | 83.0% | 19.5% | 22.1% |

  - Digital fiction: 62.8% of works and 83.1% of checkouts have a theme. In v2 it was 13.2% of works.
  - Digital nonfiction: 97.3% of works and 99.2% of checkouts.
  - Print works: 80.5% of works and 91.6% of checkouts have a theme.
- **Title words are only a flagged backup.** Adding them raises digital narrow coverage from 64.8% to 66.1% of works (83.0% to 83.6% of checkouts). All of the gain is in nonfiction.
- **Unplaced values (accepted).**
  - 21.0% of all works, carrying 25.7% of checkouts, have at least one unplaced value next to their placed ones.
  - For only 3.7% of works (1.6% of checkouts) are the unplaced values their only theme evidence.
- **Control categories (works in the main assignment).**

  | Control | Works | Audiobook | Ebook | Print |
  |---|---|---|---|---|
  | Epidemics and plagues | 2,134 | fails | passes | passes |
  | Race and racism | 8,533 | passes | passes | passes |
  | Sexual violence and domestic violence | 2,827 | fails | fails | fails |
  | Climate change and weather node | 4,101 | fails | fails | passes |
  | Climate values only | 1,568 | fails | fails | fails |

  The last three columns are the result of the fixed minimum-size rule. The pattern is the same as on the snapshot. Following the decision, the sexual violence control keeps general violence out and is accepted as failing the size rule.
- **Genres.**
  - Genres are as in v2 (SPL terms and Goodreads).
  - Print-only works without either now take their print genre parts. This adds 193,514 works, for 369,688 works with a genre in total.
  - Genres stay separate from themes.
- **LibriVox (new, section 11).** All 7,849 LibriVox books in `listening.parquet` were run through the same value-to-node logic and strength scale as the Seattle works.
  - 74.9% of recordings (80.0% of listens) have a theme.
  - 64.6% of recordings (71.0% of listens) have a narrow theme.
- **Study 3 panel and tests.**
  - The panel was rebuilt on the final v3 tables (build `20261013-210004-a772613ac300`). Its report holds structural checks only, and LibriVox is included.
  - The test suite passes: 45 passed, 0 failed.

## 1. What was done

| Coordinator decision | What was done | Main outputs (`data/db/taxonomy_v3/`) |
|---|---|---|
| 1. Print headings as main theme source | Print records read in full. Headings carried to the same work's audiobook and ebook records. Every heading parsed into theme / genre / audience / form / place / period / person parts. New theme values mapped into existing nodes. One new narrow node. | `spl_records.parquet`, `headings_parsed.parquet`, `lcsh_cores.parquet`, `theme_value_node.parquet`, `profile/placement_log.csv`, `profile/hand_decisions.csv`, `profile/new_nodes.csv` |
| 2. Goodreads author file | Every Goodreads work now has an author name, so a link needs the same title and the same author (or surname) | `spl_goodreads_link.parquet`, `profile/goodreads_link_summary.json` |
| 3. Title words out of the main assignment | Main assignment uses SPL terms, print headings and Goodreads shelves only; title words go in a separate flagged table | `work_theme.parquet`, `work_theme_title_backup.parquet` |
| 4. Controls rebuilt from print headings | Hand pattern rules for the controls; sizes; minimum-size check | `quality/control_definitions.csv`, `control_sizes_by_year.csv`, `control_min_size.csv` |
| 5. Full ebook file | Read in full (9,685,032 lines) | `spl_rows_ebook.parquet` |
| 6. Genres | v2 method; print-only works take their print genre parts (decision 8 of 13 October) | `work_genre.parquet`, `work_lcsh_parts.parquet` |
| LibriVox (job B) | LibriVox books mapped into v3 | `librivox_work_theme.parquet`, `librivox_work_genre.parquet`, `librivox_work_theme_value.parquet` |

- The v2 outputs in `data/db/taxonomy_v2/` were not touched; no file there is newer than 17:46 today.
- Code is in `code/main_study/`: scripts 10 to 20, run by `./run_all.sh v3`, with 20 running before 19.
- Script 19 regenerates the number tables into `data/reports/main_study_checkpoint_2_tables.md`.

## 2. Inputs and how print headings reach audiobooks and ebooks

### 2.1 Rows read

| Format | Rows | Share of SPL API rows | Checkouts | Months |
|---|---|---|---|---|
| Audiobook | 4,697,512 | 100% | 19,887,468 | Sep 2005 to Aug 2026, 249 with rows |
| Ebook | 9,685,032 | 100% | 29,937,728 | Sep 2005 to Aug 2026, 249 with rows |
| Print | 25,791,712 | 100% | 74,358,276 | Apr 2005 to Aug 2026, 257 with rows |

### 2.2 Print records

- **Records.** 1,109,523 distinct print records (title + creator + subjects). 1,034,120 of them (93.2%) carry headings, 3.93 per record on average.
- **Headings.** 550,269 distinct headings; 36,516 of them are on 10 or more works.
- **No ISBN.** The print rows have no ISBN field. The fields are title, creator, subjects, publisher, publication year and usage class. So ISBN could not help the matching.
- **Missing creators.** The creator field is empty in 425,811 print records (38.4%). This is mostly in early years: 65% of 2005 rows, about 5% from 2016 on.
  - For 27,438 records a creator was read from the statement of responsibility in the title.
  - 398,373 records (35.9%) still have none.

### 2.3 Work ids across formats

A work is a normalized title plus the creator's first and last name, with the v2 subtitle rule. Print and digital records with the same id are one work, so a work's print headings also describe its audiobook and ebook.

Records without a creator are handled like this:

- **Joined to a work with a creator.** This happens when exactly one work with a creator has the same full title, and that work was already being borrowed at the time (33,230 records).
- **Print records not joined.** These are grouped by title plus first heading (362,890 records). Before this, same-title books were merged into one work: "<Unknown Title>" collected 2,644 records and 213 narrow themes.
- **Placeholder titles** become one work per record (2,697 records).
- **Digital records without a creator** (1,048) join the print group with the same title only when there is exactly one such group (119 records).

Result: 1,013,659 works.

| Formats of the work | Works |
|---|---|
| Print only | 758,726 |
| Print and ebook | 90,701 |
| Ebook only | 69,347 |
| All three | 64,343 |
| Audiobook only | 13,974 |
| Audiobook and ebook | 9,841 |
| Audiobook and print | 6,727 |

93,162 works are digital-only, and 24.7% of them were first borrowed in 2024 or later. Many are probably recent ebook-only titles that SPL has not bought in print.

### 2.4 Goodreads links with the author file

Every Goodreads work in the v2 table (74,645) now has an author name. Links need the same main title and either:

- the same author (tier A, 29,527 works); or
- the same surname (tier B, 783 works).

The title-only tiers of v2 are no longer used. 30,310 SPL works are linked: 3.0% of works, but 19.3% of all checkouts. 22,592 digital works are linked, against 13,445 in v2 (7,544 of which were title-only).

## 3. What changed from v2

### 3.1 Parsing the headings

Headings in the SPL file have their punctuation removed and subdivisions joined by spaces ("Racism United States History 20th century Juvenile literature"). Script 14, with `_lcsh.py`, splits each heading from the right. It removes:

- form, audience and genre subdivisions;
- topical subdivisions (each has a fixed theme or is dropped);
- places;
- dates and periods.

What is left is the core. Some cores are handled before this splitting:

- genre headings are checked first;
- a protected list keeps headings like "Black Death" and "Child sexual abuse" whole;
- events go to a fixed list;
- persons with dates and fictitious characters (singular and plural, such as "Avengers Fictitious characters") become person and character facets, not themes.

Every heading's parts are stored in `headings_parsed.parquet`.

**Accents repaired.** The subjects field writes accented letters in the old DOS code page 850 ("Pok‚mon", "Doppelg„ngers", "Yucat n" for Yucatán). Every non-ASCII character in the field fits this pattern, so script 11 reverses it for all 6,614 affected headings. Titles and creators are correct UTF-8.

| Core kind | Distinct cores | Work links |
|---|---|---|
| Topic (becomes a theme value) | 179,118 | 2,128,841 |
| Genre heading | 271 | 536,538 |
| Person | 29,769 | 114,860 |
| Fictitious character | 4,676 | 47,784 |
| Event | 1,660 | 31,226 |
| Place only | 17 | 5,286 |

How topical cores became theme values:

| Route | Cores | Work links |
|---|---|---|
| Same as a v2 value (or its plural) | 542 | 368,941 |
| v2 lexicon synonym (or its plural) | 171 | 59,883 |
| Hand alias | 22 | 14,578 |
| Hand facet decision (not a theme) | 78 | 55,421 |
| LC rename (takes the old form's value) | 167 | 5,908 |
| New value | 178,138 | 1,624,110 |

Some subdivisions also carry a theme ("Women Violence against" gives "violence against women"). These count at half weight (0.5) against the heading's own core (1.0).

### 3.2 Placing new values in the fixed tree

New values on 3 or more works were placed in this order (script 15, decisions in `_review_v3.py`, log in `profile/placement_log.csv`):

1. **Hand decision: 416 values, 225,168 work links.** 351 were placed and 65 were judged not to be themes. Examples:
   - "man woman relationships" goes to marriage;
   - "schools" goes to school life;
   - "conduct of life" goes to ethics / virtue;
   - "missing persons" goes to kidnapping.
2. **Hand pattern rules: 1,047 values, 20,526 work links.** These are the control categories and general violence. Control nodes take values only through these rules, never through the embedding.
3. **Nearest node by embedding: 27,601 values, 989,973 work links.** This uses the same model and text ("books about X") as v2. A narrow node is accepted at cosine similarity 0.50 or more; the median similarity of accepted values is 0.63. The cut-off comes from a hand check of 25 random values per band:

   | Band | Right placements |
   |---|---|
   | 0.30 to 0.40 | 6 of 25 |
   | 0.40 to 0.50 | 6 of 25 |
   | 0.50 to 0.60 | 21 of 25 |
   | 0.60 to 0.70 | 22 of 25 |
   | 0.70 and over | 24 of 25 |
4. **Unplaced: 19,356 values on 3 or more works (264,913 work links).** The largest are mostly genre or form terms that are not themes ("school comics", "historical comics", "novellas", "case studies"). There are also small topics such as "empathy", "hanukkah" and "hair". 129,796 values on 1 or 2 works were not placed.

**Review of the headings added by the full file (third round, same rules as before).** The rows from 2020 to 2026 brought two kinds of new term.

- **Newer Library of Congress genre and form terms.** Examples: "Fantasy comics", "Self-help publications", "Illustrated works", "Cozy mysteries", "Large print books", "Shonen manga", "Decodable books". 33 of them were made genre, form or audience facets instead of themes. Several had been put in wrong nodes by the embedding, for example "Self-help publications" in self harm, and fantasy and science fiction comics in vampires / superheroes.
- **Renamed topical headings.** Examples: "Noncitizens" (formerly "Aliens"), "Freed persons", "Woman-woman relationships". 15 of these, and 3 cross-dressing headings, were placed by hand.
  - The random spot check found "Transvestites" placed in transhumanism by the embedding. It now goes to the LGBTQ node.
  - Most other new values were placed well by the embedding ("Queer" and "Gay people" in lgbtq; "Enslaved persons" in slavery; "Black people" in African American life).
- **Event headings.** "COVID-19" (386 works), "Black Lives Matter movement" (62) and "#MeToo movement" (12) reached their controls through the rules set before. "Racism against Black people" reached race and racism through the existing racism rule.
- **Control contents.** Apart from the LC renames below, no control content was changed.

**Library of Congress renames (fourth round, coordinator decision).** A heading that LC renamed takes the placement of the heading it replaced, in every node, controls included. Script 14 maps a core that starts with the new form to the matching old-form core ("multiracial children" to "racially mixed children"), when that old-form core exists. Only renames LC made are used.

Each rename is checked in the SPL data. A title "switched" when one of its print records has the old form and a later record of the same title has the new form, which is how the library applied LC's change to its catalogue. I did not check the LC authority records or change lists online, because that would be a new download; the LC changes come from my notes. The log is `profile/hand_decisions.csv`, rows "LC rename".

| Old form | New form | Titles switched in SPL records | Median month of the switch | Effect |
|---|---|---|---|---|
| Racially mixed (people, children, families, women, youth) | Multiracial ... | 434 | 2024-10 | New forms join race and racism (were unplaced) |
| Whites | White people | 61 | 2022-06 | Joins race and racism (was unplaced) |
| Blacks | Black people | 206 | 2024-02 | Same node as before |
| Gays | Gay people | 325 | 2024-03 | Same node; a few subforms move |
| Bisexuals | Bisexual people | 54 | 2024-02 | Same node |
| Slaves | Enslaved persons | 342 | 2024-02 | Same node |
| Women slaves | Enslaved women | 43 | 2023-08 | Same node |
| Freedmen | Freed persons | 51 | 2023-07 | Both now in slavery (the old form was unplaced; placed by hand) |
| Illegal aliens | Undocumented noncitizens | 121 | 2021-09 | Both now in immigration (the old form had gone to aliens / ufos by embedding; corrected by hand) |
| Transvestites | Cross-dressers | 37 | 2018-01 | Same node |
| Transvestism | Cross-dressing | 17 | 2018-01 | New form moves from fashion / cosplay to lgbtq |
| Manic-depressive illness | Bipolar disorder | 59 | 2023-12 | Same node |
| Manic-depressive persons | People with bipolar disorder | 35 | 2023-12 | Same node |
| Hearing impaired | Hard of hearing people | 20 | 2024-06 | Same node |
| Brothers and sisters | Siblings | 2,228 | 2023-04 | Same node |
| Beat generation | Beats (Persons) | 62 | 2020-07 | New form becomes the genre "beat literature", like the old form |
| Vietnamese Conflict, 1961-1975 | Vietnam War, 1961-1975 | 330 | 2006-11 | Old form had been read as a person; both now give "vietnam war" |
| Japanese Americans, Evacuation and relocation | Forced removal and internment | 147 | 2022-02 | New form takes the old event value |

Three LC renames were not applied:

- "Aliens" to "Noncitizens": in the SPL records the old "Aliens" heading is also used for extraterrestrials, so its placement does not fit noncitizens. "Noncitizens" keeps its hand placement in immigration.
- "Cookery" to "Cooking" (2010): the old form is a genre heading here, so taking its placement would remove the cooking theme.
- "Aged" to "Older people" (2005): both forms are already in the same node.

`profile/hand_decisions.csv` lists aliases, facet decisions, hand-changed subdivision rules and the LC renames, each with a reason (136 rows). `profile/placement_log.csv` has every value with its method, node, similarity and reason.

### 3.3 The new narrow node (approved)

| Node | Label | Parent | Why |
|---|---|---|---|
| B12.M01.N04 | Violence and violent crime | B12.M01 Abuse, sexual violence and revenge | Print headings bring many general violence subjects. The only existing narrow node about violence is the sexual and domestic violence control. |

It holds 120 values and 5,746 works. The largest values are "violent crimes" (3,772 works, mostly from the subdivision "Crimes against"), "violence in general" (810), "stalkers" (275) and "stalking" (210).

### 3.4 Assignment, genres and labels

- **Theme strength.** It is computed per source and then averaged over the sources present: SPL terms, print headings and Goodreads shelves count equally. Within the print source:
  - a heading's core counts 1.0 and its subdivision themes 0.5;
  - headings are weighted by the share of the work's print checkouts that carried them.
- **Themes per work.** A covered work has a median of 2 narrow themes, a 90th percentile of 4 and a maximum of 21.
- **Genres.**
  - Genres come from SPL terms and Goodreads shelves, as in v2.
  - Print-only works with neither (193,514) take their print genre parts, with strength equal to the share of the work's genre parts. Two LCSH genres outside the v2 list were mapped: "domestic fiction" to family saga, and "psychological fiction" to literary fiction. "Coming of age novel" was left out because it is a theme in the tree.
  - 369,688 works have a genre.
- **Audience.** Taken from SPL terms first, then print audience parts, then Goodreads, else "adult (default)".
- **Fiction or nonfiction.** Taken from SPL terms first, then print form and genre parts, then Goodreads.

## 4. Coverage

All shares are "% of works / % of checkouts" in that format. A work counts in a format if it has checkouts in it.

**Digital (audiobook + ebook), 254,933 works**

| Group | Works | Any theme | Narrow theme | Any theme with title words | Narrow theme with title words |
|---|---|---|---|---|---|
| All works | 254,933 | 74.6 / 87.9 | 64.8 / 83.0 | 74.7 / 87.9 | 66.1 / 83.6 |
| Fiction | 167,178 | 62.8 / 83.1 | 61.7 / 81.9 | 62.8 / 83.1 | 61.7 / 81.9 |
| Nonfiction | 85,933 | 97.3 / 99.2 | 70.9 / 85.6 | 97.5 / 99.3 | 74.7 / 87.5 |
| Form unknown or mixed | 1,822 | 87.2 / 94.5 | 68.0 / 83.9 | 87.2 / 94.5 | 68.0 / 83.9 |

**Audiobook, 94,885 works**

| Group | Works | Any theme | Narrow theme | Any theme with title words | Narrow theme with title words |
|---|---|---|---|---|---|
| All works | 94,885 | 82.9 / 90.0 | 75.4 / 85.3 | 83.0 / 90.0 | 76.4 / 85.9 |
| Fiction | 62,552 | 74.8 / 85.5 | 73.7 / 84.5 | 74.8 / 85.5 | 73.7 / 84.5 |
| Nonfiction | 31,684 | 98.8 / 99.4 | 79.0 / 87.1 | 98.9 / 99.5 | 81.9 / 89.0 |
| Form unknown or mixed | 649 | 94.3 / 96.5 | 73.3 / 85.0 | 94.3 / 96.5 | 73.3 / 85.0 |

**Ebook, 234,232 works**

| Group | Works | Any theme | Narrow theme | Any theme with title words | Narrow theme with title words |
|---|---|---|---|---|---|
| All works | 234,232 | 76.0 / 86.5 | 66.8 / 81.5 | 76.0 / 86.5 | 68.0 / 82.0 |
| Fiction | 154,842 | 65.1 / 81.5 | 63.9 / 80.4 | 65.1 / 81.5 | 63.9 / 80.4 |
| Nonfiction | 77,699 | 97.4 / 99.1 | 72.5 / 84.4 | 97.5 / 99.2 | 76.0 / 86.3 |
| Form unknown or mixed | 1,691 | 86.7 / 93.1 | 70.5 / 83.1 | 86.7 / 93.1 | 70.5 / 83.1 |

**Print, 920,497 works**

| Group | Works | Any theme | Narrow theme | Any theme with title words | Narrow theme with title words |
|---|---|---|---|---|---|
| All works | 920,497 | 80.5 / 91.6 | 76.3 / 88.5 | 81.0 / 91.8 | 77.0 / 88.7 |
| Fiction | 305,087 | 89.0 / 94.1 | 86.9 / 92.6 | 89.0 / 94.1 | 86.9 / 92.6 |
| Nonfiction | 541,262 | 85.8 / 91.6 | 79.8 / 86.2 | 86.5 / 91.9 | 80.9 / 86.7 |
| Form unknown or mixed | 74,148 | 7.7 / 44.7 | 7.3 / 43.2 | 7.7 / 44.7 | 7.3 / 43.2 |

Notes:

- **Digital fiction.** Coverage is higher in checkouts than in works: popular fiction usually has a print copy with headings, while much ebook-only genre fiction does not.
- **Print "form unknown or mixed".** These are mostly records without headings.
- **Works by source, all formats:**

  | Source | Works | Share of works | Share of checkouts |
  |---|---|---|---|
  | Print headings | 737,175 | 72.7% | 86.4% |
  | SPL terms | 99,684 | 9.8% | 22.7% |
  | Goodreads | 23,697 | 2.3% | 15.1% |

  0.3% of works rely on Goodreads alone.

**Unplaced values (decision 6: accepted).** Shares are of works and checkouts in each format.

| Format | Works with an unplaced value | Works whose only theme evidence is unplaced |
|---|---|---|
| Audiobook | 22.1% / 26.9% | 0.4% / 0.5% |
| Ebook | 18.3% / 24.3% | 0.5% / 0.6% |
| Digital | 17.5% / 25.3% | 0.5% / 0.5% |
| Print | 23.1% / 25.9% | 4.1% / 2.4% |
| All formats | 21.0% / 25.7% | 3.7% / 1.6% |

**Node sizes, counted by works only.** No checkout totals are shown for non-control nodes, as the fixed settings require.

- 217 of the 242 narrow nodes have 1,000 or more works.
- The smallest are transhumanism (8 works, after the cross-dressing headings were moved out), worldview (12) and chivalry (36).
- The largest is childhood / parenting (38,782).

## 5. Control categories

### 5.1 Contents

Each control is one narrow node of the approved tree. Values enter it only through the hand rules or the v2 values already placed there. Contents are as decided on 13 October. The only later change is the LC renames (section 3.2), which add 62 works to race and racism. The most frequent values, with works:

- **Sexual violence and domestic violence (B12.M01.N02), event month October 2017. 263 values.**
  - Most frequent: family violence (332), sexual violence (317, mostly "Rape"), abused women (273), child sexual abuse (253), rape victims (228), sex crimes (200), abused wives (167), sexual abuse victims (150), violence against women (147), sexual harassment (97), sexual harassment of women (90).
  - The "#MeToo movement" heading is on 12 works.
  - General violence goes to the new node.
- **Epidemics and plagues (B15.M04.N05), March 2020. 143 values.**
  - Most frequent: epidemics and pandemics (584), COVID-19 (386), plague (275), virus diseases (216), viruses (188), communicable diseases (166), influenza (75), vaccines (68), epidemiology (63), vaccination (60).
- **Race and racism (B05.M02.N02), June 2020. 277 values.**
  - Most frequent: race relations (4,293), racism (1,562), race (1,039), racially mixed people (842, now including "Multiracial people"), prejudices (671), race discrimination (304), segregation (240), whites (226, now including "White people"), white supremacy movements (157), interracial marriage (150), antiracism (119).
  - "Ethnic relations" goes to multicultural / diversity.
- **Climate change and weather (B09.M07.N02), September 2019. 263 values.**
  - Most frequent: climatic changes (969), weather (517), global warming (408), rain and rainfall (325), storms (305), hurricanes (288), blizzards (216), floods (197).
  - The "climate values only" version counts only the climate values. This category is not in the fixed settings.

The title-word backup is allowed only for a control with fewer than 50 works. No control is that small.

### 5.2 Sizes

| Control | Works | Extra works with title words | Values in node |
|---|---|---|---|
| Epidemics and plagues | 2,134 | 399 | 143 |
| Race and racism | 8,533 | 228 | 277 |
| Sexual violence and domestic violence | 2,827 | 70 | 263 |
| Climate change and weather (node) | 4,101 | 379 | 263 |
| Climate change (climate values only) | 1,568 | 649 | (same node) |

Works with at least one checkout, by year and format (main assignment). Checkout counts by year are kept in `quality/control_sizes_by_year.csv` but not shown, because the control series are not viewed again after this checkpoint.

**Sexual violence and domestic violence**

| Year | Audiobook | Ebook | Print |
|---|---|---|---|
| 2014 | 84 | 257 | 698 |
| 2015 | 88 | 278 | 693 |
| 2016 | 90 | 306 | 662 |
| 2017 | 119 | 337 | 664 |
| 2018 | 134 | 360 | 696 |
| 2019 | 173 | 391 | 730 |
| 2020 | 232 | 487 | 556 |
| 2021 | 277 | 535 | 700 |
| 2022 | 350 | 586 | 821 |
| 2023 | 404 | 626 | 885 |
| 2024 | 434 | 644 | 849 |
| 2025 | 476 | 670 | 885 |
| 2026 (to Aug) | 491 | 644 | 771 |

**Epidemics and plagues**

| Year | Audiobook | Ebook | Print |
|---|---|---|---|
| 2014 | 86 | 189 | 531 |
| 2015 | 95 | 220 | 531 |
| 2016 | 108 | 262 | 547 |
| 2017 | 123 | 285 | 565 |
| 2018 | 143 | 289 | 553 |
| 2019 | 161 | 312 | 556 |
| 2020 | 209 | 381 | 448 |
| 2021 | 257 | 437 | 650 |
| 2022 | 319 | 492 | 795 |
| 2023 | 363 | 536 | 855 |
| 2024 | 385 | 538 | 818 |
| 2025 | 415 | 557 | 880 |
| 2026 (to Aug) | 427 | 520 | 727 |

**Race and racism**

| Year | Audiobook | Ebook | Print |
|---|---|---|---|
| 2014 | 223 | 579 | 2,382 |
| 2015 | 261 | 626 | 2,347 |
| 2016 | 300 | 753 | 2,468 |
| 2017 | 368 | 859 | 2,565 |
| 2018 | 431 | 934 | 2,595 |
| 2019 | 527 | 1,016 | 2,683 |
| 2020 | 712 | 1,323 | 2,092 |
| 2021 | 886 | 1,531 | 2,731 |
| 2022 | 1,082 | 1,718 | 3,017 |
| 2023 | 1,261 | 1,847 | 3,175 |
| 2024 | 1,368 | 1,890 | 3,092 |
| 2025 | 1,451 | 1,943 | 3,170 |
| 2026 (to Aug) | 1,464 | 1,852 | 2,780 |

**Climate change and weather (node)**

| Year | Audiobook | Ebook | Print |
|---|---|---|---|
| 2014 | 69 | 207 | 1,077 |
| 2015 | 70 | 246 | 1,089 |
| 2016 | 80 | 293 | 1,125 |
| 2017 | 108 | 319 | 1,198 |
| 2018 | 127 | 344 | 1,207 |
| 2019 | 150 | 369 | 1,257 |
| 2020 | 187 | 463 | 1,016 |
| 2021 | 240 | 539 | 1,249 |
| 2022 | 312 | 645 | 1,429 |
| 2023 | 365 | 690 | 1,549 |
| 2024 | 417 | 748 | 1,576 |
| 2025 | 488 | 825 | 1,677 |
| 2026 (to Aug) | 497 | 797 | 1,586 |

The climate-values-only version has 50 audiobook, 113 ebook and 440 print works in 2019.

### 5.3 Minimum-size rule

The fixed rule: a category is tested in a format only with 20 or more works with checkouts in that format, and a median of 200 or more strength-weighted checkouts per month over the 24 months before the event month.

Unusable months are skipped. They now come from the Study 3 code (`study3/_settings.py` and `_build.month_status`), so the rule lives in one place:

- the three digital gap months of the fixed settings;
- months with fewer rows than the SPL API count;
- closure months under addendum e: a library-wide total below 50% of the median of the previous 12 months.

On the full print file the rule flags print April to September 2020, and June and July 2024. The rule is meant to catch the June and July 2024 print gap after the ransomware attack too (coordinator, 13 October). The hand-coded 10% closure rule of the earlier version was removed from the v3 code.

| Control | Format | Works with checkouts | Months available of 24 | Passes |
|---|---|---|---|---|
| Epidemics and plagues | Audiobook | 483 | 24 | No |
| | Ebook | 809 | 24 | Yes |
| | Print | 2,133 | 24 | Yes |
| Race and racism | Audiobook | 1,724 | 24 | Yes |
| | Ebook | 2,792 | 24 | Yes |
| | Print | 8,493 | 22 | Yes |
| Sexual violence and domestic violence | Audiobook | 571 | 24 | No |
| | Ebook | 970 | 24 | No |
| | Print | 2,820 | 24 | No |
| Climate change and weather (node) | Audiobook | 566 | 24 | No |
| | Ebook | 1,168 | 24 | No |
| | Print | 4,100 | 24 | Yes |
| Climate change (values only) | Audiobook | 255 | 24 | No |
| | Ebook | 479 | 24 | No |
| | Print | 1,567 | 24 | No |

The sexual violence control fails in every format and, under the fixed settings, is not tested (decision 1). The medians are in `quality/control_min_size.csv`.

## 6. Sanity view

A descriptive view of the four controls' monthly series was made once, on the print snapshot, and reported in the first version of this report. By the decision of 13 October it is not redone or repeated here; the control series are not viewed again. The v3 code no longer produces it: script 18 no longer writes `controls_monthly.parquet` or `control_windows.csv`.

## 7. Ten random works for a spot check

These 10 were drawn with a fixed seed (20261013) from digital works with at least one theme. Full rows are in `quality/random_10_works_for_review.csv`, which has empty columns for Khant's own judgment.

| Work | Formats | Theme sources | Narrow themes (strength) | My judgment |
|---|---|---|---|---|
| Washington Off the Beaten Path (Chloe Ernst) | ebook | SPL | none; broad: nature, places and the environment | Right broad area, no narrow theme (no print copy) |
| Graveminder (Melissa Marr) | all three | print | childhood / parenting, genealogy, suicide / death and dying (0.33 each, from "Family secrets") | Partial; the paranormal side is in genres, not themes |
| The Rebel and the Final Blood War (K.A. Linde) | all three | print | vampires / superheroes 0.50, marriage 0.50 | Fits |
| Putevoditel po strane sionskikh mudretsov (Aleksandr Okun) | ebook | SPL | none; broad: nature, places and the environment | Right broad area (a travel book on Israel), no narrow theme |
| The Forever Witness (Edward Humes) | all three | SPL, print | police / forensic science 0.18, biology 0.09, social issues 0.09 | Fits |
| Beyond the possible (Cecil Williams) | print, ebook | SPL, print | theology / church 0.50, christianity 0.19 | Fits |
| Rogue (Julie Kagawa) | all three | SPL, print | mythology 0.50, shapeshifters 0.12, dragons 0.12 | Fits |
| Edible wild plants (John Kallas) | print, ebook | SPL, print | gardening / botany 0.48, cooking 0.25 | Fits |
| The serenity murders (Mehmet Murat Somer) | print, ebook | print | murder / serial killers 0.50, lgbtq / gay men 0.50 | Fits ("Transvestites" and its new form "Cross-dressers" both go to lgbtq) |
| Bearskin (James A. McLaughlin) | all three | print | wolves / bears 0.50, hunting 0.50 | Fits |

Seven fit, one is partial, and two are digital-only travel books with only a broad theme. The sample changed slightly from the previous version because the renames gave 116 more works a theme, which changes the pool the seed draws from. An earlier draw found "Transvestites" placed in transhumanism by the embedding; it was fixed (section 3.2).

## 8. Data problems

1. **No ISBN in the print rows.** Matching across formats uses normalized title and creator only.
2. **Missing print creators.** 35.9% of print records have no creator even after reading it from the title, mostly from 2005 to 2012. They cannot join their digital versions unless the title is unique.
3. **Same-title merging of creator-less print records.** Fixed by grouping on title + first heading (section 2.3). A few groups with a generic first heading remain.
4. **Accents in DOS code page 850 in the subjects field.** Repaired for 6,614 headings.
5. **Closure months.** Print April to September 2020 and June to July 2024 are unusable under the Study 3 rule (addendum e).
6. **Changes in the Library of Congress vocabulary from about 2021.** Several new headings name existing concepts:
   - "Enslaved persons", "Noncitizens", "Multiracial people", "White people", "Gay people";
   - new genre and form terms.

   The genre and form terms are handled by hand, and LC renames now take the old form's placement in every node (section 3.2).
7. **A v2 placement routes general violence into a control.** v2 put the value "violence" in the sexual violence node. Print headings use "Violence" and "Crimes against" for general and crime-fiction violence, so the print values go to the new node. The Goodreads shelf "violence" (11 works) stays where v2 put it.
8. **Weak embedding placements at the margin.** About 4 in 25 are wrong in the 0.50 to 0.60 band. The final spot check found one ("Transvestites" in transhumanism), now fixed.

## 9. Decisions taken on 13 October, and what is still open

Taken, and applied in this version:

1. Sexual violence control: general violence stays out; the control fails the size rule and is not widened.
2. Closure months: the Study 3 total-based rule (addendum e); no hand-coded months in the v3 code.
3. New node B12.M01.N04 approved.
4. Control contents kept as built.
5. Source weighting accepted.
6. Unplaced values accepted (shares in section 4).
7. Creator-less print books stay separate works.
8. Print genre parts fill genres for print-only works.

Taken in the last pass (13 October):

9. LC renames: a heading LC renamed takes the old heading's placement in every node, controls included (section 3.2). This adds 62 works to race and racism and changes no other control.
10. LibriVox subjects from Wikidata (P921) and Open Library: no new download now. Fetching them per book is a possible later improvement.
11. Closure months: the Study 3 rule's result (print April to September 2020, and June and July 2024) is accepted as it is.

Nothing is open from this checkpoint.

## 10. Files, how to rerun, and run times

- **Code:** `code/main_study/10_v3_spl_rows.py` to `20_v3_librivox.py`, with `_lcsh.py` (heading parser) and `_review_v3.py` (hand decisions in four rounds, the last being the LC renames). Script 18 reads the missing-month rule from `code/main_study/study3/`.
- **Rerun:** `cd code/main_study && ./run_all.sh v3`. Add `REFRESH_SNAPSHOT=1` to reread files that have grown.
- **Run times on this Mac, final run, about 9 minutes in total:**

  | Script | Time |
  |---|---|
  | 10 | 257 s |
  | 11 | 39 s |
  | 12 | 10 s |
  | 13 | 25 s |
  | 14 | 25 to 37 s |
  | 15 | 17 to 48 s |
  | 16 | 45 to 60 s |
  | 17 | 7 to 11 s |
  | 18 | 4 to 5 s |
  | 20 | 5 to 6 s |
  | 19 | 1 s |
- **Outputs:** `data/db/taxonomy_v3/` (parquet tables, `profile/`, `quality/`). Number tables are in `data/reports/main_study_checkpoint_2_tables.md`.

## 11. LibriVox in taxonomy v3

**Books.** `listening.parquet` has 7,849 single-author LibriVox books. `book_id` is the Study 2 bookgroup, which joins the recordings of one book. All 7,849 are in `librivox_work_theme.parquet`, with columns `book_id, node_id, level, strength`, plus `s_lv, s_gr, s_desc, sources`. `book_id` matches `listening.parquet`.

**Method (script 20).** It uses the same logic as the Seattle works:

- evidence is kept per source and mapped to theme values;
- values go to nodes through `theme_value_node.parquet`, so they reuse the same values, nodes and embedding placements;
- each source's weights become shares, rolled up to parent nodes;
- strength is the mean share over the sources with evidence, on the same scale as `work_theme.parquet`.

The sources are:

- **LibriVox genres (lv).** A closed list split into facets by the v2 phrase rules, as the OverDrive terms are.
- **Goodreads shelves (gr).** For the 617 books linked to a Goodreads work that has shelf data on disk. Same rule as for Seattle.
- **The LibriVox description (desc).** Whole-word matches of a curated value list: v2 values, the v2 lexicon, and v3 values placed by hand or rule.
  - Phrases of two or more words count.
  - A single word counts only if it is on a hand-reviewed list of specific words ("slavery", "pirates", "plague", "theology").
  - Ambiguous single words were left out after review: "white" and "race" would have put more than 300 books in race and racism; "prejudice" matches Pride and Prejudice; "outbreak" usually means an outbreak of war. Others: "black", "light", "night", "violence", "storm", "reading".
  - The reviewed list is in `quality/librivox_desc_words.csv`.

Title words are not used.

**Not used.** Wikidata main subjects (P921) and Open Library subjects per book are not on disk. Fetching them is a new download, so by decision it is left as a possible later improvement.

**Coverage.** Recordings are LibriVox books; listens are summed over 2017 to 2026.

| Measure | Recordings | Share of recordings | Share of listens |
|---|---|---|---|
| Any theme | 5,876 | 74.9% | 80.0% |
| Narrow theme | 5,072 | 64.6% | 71.0% |
| Any genre | 5,003 | 63.7% | 81.0% |
| Evidence from LibriVox genres | 3,182 | 40.5% | 36.3% |
| Evidence from Goodreads | 617 | 7.9% | 25.2% |
| Evidence from the description | 4,496 | 57.3% | 65.5% |

**Top narrow nodes by recordings:**

| Narrow node | Recordings |
|---|---|
| christianity / latter day saints | 883 |
| childhood / parenting | 376 |
| mythology / arthurian legend | 300 |
| money / wealth | 259 |
| marriage / arranged marriage | 254 |
| theology / church | 230 |
| geography / geopolitics | 207 |
| government / democracy | 197 |
| sisters / siblings | 189 |
| ethics / virtue | 184 |
| space / mars | 165 |
| seafaring / pirates | 163 |

**Top broad nodes by recordings:**

| Broad node | Recordings |
|---|---|
| Religion and spirituality | 1,203 |
| War, conflict and history | 1,112 |
| Nature, places and the environment | 1,046 |
| Childhood, family and growing up | 792 |
| Mind, self and philosophy | 754 |

Control nodes are small in LibriVox, as expected for older books:

| Control node | LibriVox recordings |
|---|---|
| Epidemics and plagues | 65 |
| Race and racism | 35 |
| Sexual violence and domestic violence | 13 |
| Climate change and weather | 32 |

The full list is in `quality/librivox_top_nodes.csv`. Listening by category over time is not reported.

**Genres.** `librivox_work_genre.parquet` (`book_id, value, strength, s_lv, s_gr`) gives 5,003 books a genre, from LibriVox genres and Goodreads, by the v2 method.

**Study 3 panel.**

- `01_demand_panel.py` was run on the final tables. The panel build report (`data/reports/study3_panel_build.md`) is structural only: months, reconciliation and size-rule counts, with no category series, effects or p-values.
- The report includes LibriVox: "LibriVox: built", with 116 usable months from 2017-01 to 2026-08.
- The final build is `20261013-210004-a772613ac300`, made after the LC rename pass. The panel has 264,067 rows and 165,118 donor-overlap pairs. All 242 narrow, 86 middle and 19 broad nodes have data, and all reconciliation checks are true.
- `tests/run_tests.py`: 45 passed, 0 failed.
