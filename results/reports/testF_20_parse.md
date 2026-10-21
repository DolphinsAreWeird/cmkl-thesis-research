# Test F, step 20: sorting and judge answers parsed (real data)

- written 2026-10-21 19:21; code main_study/wiki_led/testF/20_parse_outputs.py
- theme guide: prereg/addenda_wiki_led/2026-10-21_g_theme_guide.tsv, 242 codes, SHA-256 `d663a20137edc65dfee0f3fff3236904841a57ad3109ec03f360c2746988df50`, fingerprinted: True
- jobs (jobs.tsv): pages_main 68/68 answered, pages_sample 3/3 answered, books_main 32/32 answered, rel_pages 2/2 answered, rel_books 1/1 answered, judge 2/2 answered

## Pages (main and one-day sample)

- jobs answered 71 of 71; re-ask answer files: 0
- items in the key: 87,577
- after the first pass: none: 2,759, ok: 84,818
- notes on the first pass: none
- final: none: 2,759, themes: 84,818
- re-ask list now (invalid or missing, not yet re-asked): 0 items; still invalid after the re-ask (dropped): 0
- theme pairs: 168,587; by confidence {'1': 50887, '2': 56948, '3': 60752}; themes per item {'1': 30224, '2': 25419, '3': 29175}

- by set and status: {'sample1day|none': 110, 'sample1day|themes': 2890, 'universe|none': 2649, 'universe|themes': 81928}
- kinds (sorted pages): {'person': 40036, 'work': 13861, 'event': 11100, 'concept': 6838, 'other': 5215, 'organization': 4594, 'place': 3244, 'list': 2689}

## Books

- jobs answered 32 of 32; re-ask answer files: 0
- items in the key: 20,000
- after the first pass: none: 32, ok: 19,968
- notes on the first pass: none
- final: none: 32, themes: 19,968
- re-ask list now (invalid or missing, not yet re-asked): 0 items; still invalid after the re-ask (dropped): 0
- theme pairs: 55,619; by confidence {'1': 9716, '2': 25741, '3': 20162}; themes per item {'1': 644, '2': 2997, '3': 16327}

- second pass rel_pages: jobs answered 2 of 2; items 1,000; status {'ok': 974, 'none': 26}; notes none
- second pass rel_books: jobs answered 1 of 1; items 500; status {'ok': 499, 'none': 1}; notes none
- judge: jobs answered 2 of 2; answers 400 of 400 pages (without an answer 0); none 0; misleading title 114; notes none

Status words: themes (at least one valid code), none, invalid (a code outside the guide or a malformed line, waiting for the re-ask), missing (no answer line in an answered job, waiting for the re-ask), not_sorted (its job has no answer file yet), dropped_invalid (still invalid after the one re-ask), not_in_any_job. Only items with status themes have assignments.
