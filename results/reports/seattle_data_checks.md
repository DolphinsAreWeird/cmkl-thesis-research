# Seattle data checks (taxonomy v3 snapshot)

Made by `code/main_study/21_v3_data_checks.py` on 2026-10-30 00:33. Read-only checks of the frozen snapshot against the AIC-400 data wrangling checklist (items 2.2, 2.4, 3.2 and 3.7); nothing other scripts read was changed.

## 1. Placeholder records (checklist 2.4)

| Kind | Records | Works | Loans | Share of print loans | Works with a theme |
| --- | --- | --- | --- | --- | --- |
| uncataloged | 50 | 49 | 302,902 | 0.41% | 0 |
| unknown title, no subjects | 1 | 1 | 26,374 | 0.04% | 0 |

Placeholder records by format: {'BOOK': 51, 'AUDIOBOOK': 0, 'EBOOK': 0}. Not counted as placeholders: 2,644 "<Unknown Title>" records that carry subject headings, which are real items whose title is missing.

Test A works among them: 0. Test D corrected rows from them: 447 of 2,767,485 (5 works: Uncataloged Folder or Bag--GWD, Uncataloged Folder or Bag--SPA, Uncataloged Folder or Bag--HIP, Uncataloged Folder or Bag--RBE, Uncataloged Folder); scored rows 277 of 1,984,302.

Test D scores from `data/db/wiki_led/test_d_preds_c.parquet`, as in `61c_test_d_models.py` (lists of 20 within each format and month, share that rose; mean within-month rank correlation with the change D), with and without the placeholder works. Ties are broken by a stable sort here, so a list can differ from the stored report only among tied rows.

| Model | Top 20, all rows | Top 20, without | Placeholder slots | Not yet risen, top 20, all | without | Rank corr., all | without |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H | 0.8733 | 0.8733 | 5 | 0.4372 | 0.4370 | 0.3408 | 0.3408 |
| HW | 0.8797 | 0.8799 | 6 | 0.4436 | 0.4438 | 0.3473 | 0.3473 |
| W | 0.4547 | 0.4547 | 0 | 0.2284 | 0.2284 | 0.1058 | 0.1059 |

## 2 and 3. Key and ranges of the row tables (checklist 2.2 and 3.2)

| Format | Rows | Distinct (record, month) | Repeated keys | Extra rows | Checkouts at or below 0 | Month outside 1-12 | Years |
| --- | --- | --- | --- | --- | --- | --- | --- |
| book | 25,791,712 | 25,758,535 | 32,744 | 33,177 | 0 | 0 | 2005-2026 |
| ebook | 9,685,032 | 9,685,032 | 0 | 0 | 0 | 0 | 2005-2026 |
| audiobook | 4,697,512 | 4,697,511 | 1 | 1 | 0 | 0 | 2005-2026 |

Print records are keyed by title, creator and subjects only (`10_v3_spl_rows.py`), so editions that differ in publisher or year share a record and repeat within a month; their loans are summed, which is intended.

## 4. Exact duplicate lines in the raw snapshots (checklist 3.7)

| File | Lines read (frozen count) | Exact duplicate lines beyond the first copy |
| --- | --- | --- |
| seattle_audiobook.jsonl | 4,697,512 | 1 |
| seattle_ebook.jsonl | 9,685,032 | 0 |
| seattle_book.jsonl | 25,791,712 | 4 |

Examples (first 240 characters):

- `AUDIOBOOK: {"checkoutyear": "2017", "checkoutmonth": "1", "checkouts": "53", "title": "Where'd You Go, Bernadette: A Novel (unabridged) (Unabridged)", "creator": "Maria Semple", "subjects": "Fiction, Literature", "publisher": "Blackstone Audio, Inc.",`
- `BOOK: {"checkoutyear": "2024", "checkoutmonth": "6", "checkouts": "1", "title": "<Unknown Title>", "usageclass": "Physical"}`
- `BOOK: {"checkoutyear": "2024", "checkoutmonth": "6", "checkouts": "1", "title": "<Unknown Title>", "usageclass": "Physical"}`

Run time 67 s; peak resident memory 1,308 MB.
