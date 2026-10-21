# Test F, step 21: theme attention series (real data)

- written 2026-10-21 19:42; code main_study/wiki_led/testF/21_series.py
- assignments: 84,818 pages with themes (81,928 in the universe), 168,587 page-theme pairs

## S1 (views on top-500 days, all confidences)
- pages 81,928, page-theme pairs 163,089, page-days used 1,809,394
- days without a top-500 list in the raw file: 11; weeks partial for S1: 39
  - narrow: 242 themes with pages; share of full weeks with views > 0, median over themes 98%; themes whose median weekly weighted views reach 1,000 (the minimum of Chapter 6): 217
  - middle: 86 themes with pages; share of full weeks with views > 0, median over themes 100%; themes whose median weekly weighted views reach 1,000 (the minimum of Chapter 6): 85

## S2 (full daily views, confidence 2 or 3)
- pages with a theme of confidence 2 or 3: 78,620; selected 40,000 (cap of 40,000 applied: True; fewest top-500 days among them 5); in the store 40,000, not yet 0; download statuses {'200.0': 40000}
- built from 40,000 pages (complete)
  - narrow: 241 themes with pages; share of full weeks with views > 0, median over themes 100%; themes whose median weekly weighted views reach 1,000 (the minimum of Chapter 6): 241
  - middle: 86 themes with pages; share of full weeks with views > 0, median over themes 100%; themes whose median weekly weighted views reach 1,000 (the minimum of Chapter 6): 86

## Monthly series
- 44,608 theme-months; columns ['ais1_wlog', 'ais2_wlog']; months 2015-07 to 2026-10
