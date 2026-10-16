# Study 1 (Seattle new titles): coverage check

`00_coverage_check.py` measures, for a stratified random sample of new Seattle Public Library titles, how many have a usable
attention signal from before their first Seattle month. It reads only the work list (first month per format, publication year,
title, creator, ISBNs). It does not read, model or summarise borrowing outcomes.

Run from `handoff/code` (about 1.5 hours the first time, then seconds because every web response is cached):

    jobs/bg.sh s1_coverage study1_seattle/00_coverage_check.py     # then: renice 15 -p $(cat data/reports/s1_coverage.pid)
    nice -n 15 ../.venv/bin/python study1_seattle/00_coverage_check.py --test 40   # small trial, writes *_test files

Steps
1. Population: work whose first month in a format is 2017-01 to 2025-06 and whose earliest publication year is at most one
   year before the year of that first month. Sample: 80 works per format and cohort year, seed 20261014.
2. Open Library work ID: by ISBN (`/isbn/{isbn}.json`, up to 3 ISBNs per work), else title and author search.
3. Wikidata book item: ISBN (P212/P957, with hyphenation variants), Open Library ID (P648), else title and author on items that
   are literary works, written works, books or editions. English Wikipedia article and its first revision date.
4. First author: Wikidata person with exact name match, a writing occupation or a notable work, and an English article.
5. Open Library reading-log entries before the first Seattle month and in the 26 weeks before it (work level only; the dump
   is streamed and no user field is read or stored). The script waits up to 3 hours for the dump to finish.

Politeness: one request per second per host group, User-Agent from `config.py` (names the project and kwai@cmkl.ac.th),
SPARQL in batches. Cache: `data/interim/study1_coverage_cache/`. Outputs: `data/reports/study1_seattle_coverage.md` and `.csv`.
