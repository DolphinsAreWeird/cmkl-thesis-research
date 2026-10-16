# Study 2R: book set (matching of Seattle works to English Wikipedia book articles)

Built 2026-10-14 05:00 by code/study2r/02_match_books.py (interest and matching only; no borrowing outcome around any event).

## Counts

- Seattle works with at least 500 checkouts over 2016-01 to 2026-08 (all formats): 28,188
- of these, with at least one valid ISBN on some record: 24,895 (88%)
- matched to an English Wikipedia article about the book: **7,747 works** (27.5% of eligible), **7,510 distinct articles**
- works sharing an article with another work (e.g. several Seattle editions): 433

## Match method

- title_author: 7,054 (91.1%)
- isbn: 693 (8.9%)

- ISBN hits rejected because title and author both disagreed with the Wikidata item: 0
- among accepted ISBN matches: title agrees 99%, author family name agrees 97% (author unknown on the item: 1%)
- title and author matches with more than one candidate item: 82

## Wikidata classes of the matched items

- Q7725634: 6,263
- Q47461344: 1,248
- Q571: 106
- Q3331189: 35
- Q725377: 23
- Q47461344,Q7725634: 14
- Q20540385: 9
- Q571,Q7725634: 7

## Positive controls

| Control | Seattle work | Checkouts | Matched | Article | Method |
|---|---|---|---|---|---|
| The Queen's Gambit | The Queen's Gambit (Walter Tevis) | 5103 | yes | The Queen's Gambit (novel) | title_author |
| The Duke and I | The Duke and I (Julia Quinn) | 6297 | yes | The Duke and I | title_author |
| Dune | Dune (Frank Herbert) | 28978 | yes | Dune (novel) | title_author |
| Dune | Dune Messiah (Frank Herbert) | 8518 | yes | Dune Messiah | title_author |
| Dune | Dune: Book One in the Dune Chronicles (Frank Herbert) | 3227 | yes | Dune (novel) | title_author |
| Dune | Dune: Serie Dune, libro 1 (Frank Herbert) | 621 | yes | Dune (novel) | title_author |
| Where the Crawdads Sing | Where the Crawdads Sing (Delia Owens) | 48340 | yes | Where the Crawdads Sing | isbn |
| American Prometheus | American Prometheus: The Triumph and Tragedy of J. Robert Oppenheimer (Kai Bird) | 5113 | yes | American Prometheus | isbn |
| American Prometheus | American Prometheus: The Inspiration for the Major Motion Picture OPPENHEIMER (Kai Bird) | 1155 | yes | American Prometheus | isbn |
| Killers of the Flower Moon | Killers of the Flower Moon: The Osage Murders and the Birth of the FBI (David Grann) | 24256 | yes | Killers of the Flower Moon (book) | isbn |
| Shogun | Shogun (James Clavell) | 2280 | yes | Shōgun (novel) | title_author |
| Shogun | Shōgun, Part Two (James Clavell) | 1585 | NO |  |  |
| Shogun | Shōgun, Part One (James Clavell) | 3477 | NO |  |  |

Hand-check sheet for Khant: data/reports/study2r_match_check.csv (random 100, seed 20261014; fill the column correct_yes_no).
