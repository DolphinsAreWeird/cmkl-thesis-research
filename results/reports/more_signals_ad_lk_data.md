# Addendum n, part 1: AD (film and TV pages) and LK (linked pages), data (counts only)

Made by `code/main_study/wiki_led/n_more_signals/n12_wikidata_pages.py`, `n13_views.py` and `n14_page_features.py`; this report 2026-11-25 19:16 (+07:00). Data only: no model, nothing related to loans. Choices: `data/db/wiki_led/n_more_signals/notes_ad_lk.md` (C1 to C10, V1 to V4, F1 to F6).

## Wikidata (n12)

- Book items 3,934 (4,065 works). Requests: network 862, from cache 763, back-offs 3.
- AD: adaptation items 1,717 {'film': 1032, 'other': 383, 'tv': 302} (m01 reproduced on 3,934 book items); film or TV items without an English article 219; work-page rows 1,227, works 546, pages 1,116 {'film': 975, 'tv': 252}; rows without a release month 28.
- LK: best-rank statements 3,331 {'P921': 1128, 'P674': 1050, 'P840': 971, 'P2408': 119, 'P180': 63}; left out by item {'author': 31, 'series': 18, 'adaptation': 1, 'own_item': 1}; left out by page {'own_book_or_author_article': 3, 'also_AD_page': 0}; linked items without an English article 499; work-page rows 2,944, works 1,447, pages 1,688; by link type {'place': 959, 'subject': 783, 'character': 709, 'event_period': 431, 'person': 62}; by category {'concept_other': 1489, 'place': 954, 'event': 345, 'person': 108, 'work': 48}.

## Views (n13)

- Pages 2,804 (AD 1,116, LK 1,688); by source {'j': 965, 'adaptation': 715, 'testF': 654, 'n13': 467, 'study2r': 3}; by status {'200': 2794, '404': 10}.
- Downloaded in this run 467 (own store data/interim/n_views/); stored before: the rest.

## Features (n14)

- Check: the copied article_features() gives addendum l's stored features on 40 articles (largest difference 0.0e+00).
- Pages with data 2,794, of which no view in the period 0.
- AD: works with a set 541 (with a feature series 541); pages with data 1,106 of 1,116; share of the 1,258,807 scored rows (origins 2019-01 to 2026-07) with lvl4 0.0404, with r4 0.0401, in a set 0.0435; lag (t-12) lvl4 0.0391.
- LK: works with a set 1,447 (with a feature series 1,447); pages with data 1,688 of 1,688; share of the 1,258,807 scored rows (origins 2019-01 to 2026-07) with lvl4 0.0920, with r4 0.0919, in a set 0.0923; lag (t-12) lvl4 0.0918.
- Run time 24 s, peak memory 0.91 GB.
