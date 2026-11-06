# Live October 2026 lists: REHEARSAL (code test, not a result)

Made by `code/main_study/wiki_led/16_live_october_score.py` on 2026-11-06 14:49 +0700. Target 2026-08, M6 over 2026-02 to 2026-07. Rules: `prereg/live_alert/README.md` and addendum f.

July 2026 plays September and August plays October; the frozen October rankings are scored against August only to test the code. The library and persistence lists were made from August loans, so their August scores here are trivially high.

- Library totals of the "new" months against the stored panel: {'print 2026-07': [225183, 225183], 'print 2026-08': [227869, 227869], 'ebook 2026-07': [278520, 278520], 'ebook 2026-08': [284218, 284218], 'audiobook 2026-07': [297379, 297379], 'audiobook 2026-08': [304633, 304633]}
- Loans and M6 against the stored book rows at origin 2026-07: {'books': 7650, 'L_equal': 7640, 'M6_equal': 7649, 'L_max_abs_diff': 24.0, 'M6_max_abs_diff': 1.0, 'books_L_differing': 10}

Months ok: {'2026-02': True, '2026-03': True, '2026-04': True, '2026-05': True, '2026-06': True, '2026-07': True, '2026-08': True}

Books scored: 7650 (without an M6: 0). Base rate: rose 0.116, surged 0.023.

| List | Books | Rose | 95% interval | Surged | 95% interval |
| --- | --- | --- | --- | --- | --- |
| wikipedia top20 | 20 | 0.300 | 0.119 to 0.543 | 0.150 | 0.032 to 0.379 |
| wikipedia top50 | 50 | 0.180 | 0.086 to 0.314 | 0.100 | 0.033 to 0.218 |
| library top20 | 20 | 1.000 | 0.832 to 1.000 | 0.850 | 0.621 to 0.968 |
| library top50 | 50 | 1.000 | 0.929 to 1.000 | 0.920 | 0.808 to 0.978 |
| persistence top20 | 20 | 1.000 | 0.832 to 1.000 | 0.850 | 0.621 to 0.968 |
| persistence top50 | 50 | 1.000 | 0.929 to 1.000 | 0.840 | 0.709 to 0.928 |
| library_next_picks_51_70  | 20 | 0.900 | 0.683 to 0.988 | 0.650 | 0.408 to 0.846 |

- P1 (signal): {'lower_bound': 0.11893159040572766, 'base': 0.11568627450980393, 'passed': True}
- P2 (new information): {'books': 19, 'share': 0.2631578947368421, 'lower_bound': 0.09146578490766653, 'testable': True, 'passed': False}
- P3 (comparison): {'wikipedia_beats_library': False, 'note': 'descriptive; the claim needs a higher share and non-overlapping exact intervals'}
- Backtest for comparison: top 20: 59% rose, 40% surged; top 50: 48% and 30%; base about 11% and 3% (README, Wikipedia list, 2019 to 2026)
