# Test F, AI matchmaking: analysis code (steps 20 to 28)

Settings: `prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json` (read-only). `_testf_analysis.py` checks its SHA-256 and those of the three instruction files on every run, and step 20 refuses a theme guide that is not fingerprinted in `prereg/README.md`. The data steps 01 to 06 (`_testf_common.py`) belong to the data preparation and are not described here.

Every script runs from `code/` with `../.venv/bin/python`, calls `nice` on itself and stayed under 1.5 GB in the mock test (peaks below). Outputs go to the Test F folder `data/db/wiki_led/testF/` (S2 daily views to `data/interim/testF_views/`), reports to `data/reports/testF_*.md`. No real outcome was read or computed while this code was written: every script was tested on mock worlds with shuffled borrowing (last section).

## Answer files (layout of the main session)
- `jobs.tsv` (job, kind, input, from_line, to_line, output) lists every sorting job. A job's items are lines from_line to to_line of its input file (line 1 is the header); its answers are in `out/<job>.tsv`, no header.
- Step 20 tells the groups apart by the input file: `pages_chunk_NN.tsv` main pages, `pages_sample1day_chunk_NN.tsv` one-day sample (coverage only), `books_chunk_NN.tsv` books, `rel_pages.tsv` / `rel_books.tsv` second pass, `judge_pages.tsv` judge.
- Re-ask: step 20 writes `reask_pages_input.tsv` and `reask_books_input.tsv` (input lines with the chunks' header). Add a job for each to `jobs.tsv` (for example `reask_pages_a  pages  reask_pages_input.tsv  2  <n+1>  out/reask_pages_a.tsv`) and rerun step 20; it reads those answers, and any `out/reask_pages*.tsv` / `out/reask_books*.tsv`, only for the items that needed a re-ask. A file that a job names is never overwritten; items still waiting go to `reask_pages_input_2.tsv`.

## Run order

| Step | Command (from `code/` unless noted) | Writes | Time, peak memory (mock test) |
| --- | --- | --- | --- |
| 20 | `nice ../.venv/bin/python main_study/wiki_led/testF/20_parse_outputs.py` | `assign_pages.parquet`, `assign_books.parquet`, `items_*.parquet`, `second_pass_*.parquet`, `judge_answers.parquet`, `reask_*.tsv`, `reask_*_input.tsv`, `parse_summary.json` | 1 s, 0.2 GB |
| re-ask | the main session sorts `reask_*_input.tsv` once, adds the jobs, reruns 20 | | |
| 22 | from `handoff/`: `bash jobs/bg.sh testF_s2_views main_study/wiki_led/testF/22_download_views.py --job-name testF_s2_views` | `data/interim/testF_views/batch_*.npz`, `s2_download_summary.json` | about 3 h 50 min for 40,000 pages (0.34 s gap over 4 threads = 2.94 requests a second); 0.6 GB. Refuses while another job whose name holds wiki, view, text or download runs. Can start on partial answers; a rerun after 20 fetches only new pages |
| 21 | `nice ../.venv/bin/python main_study/wiki_led/testF/21_series.py` | `series_weekly_S1.parquet`, `series_weekly_S2.parquet`, `series_monthly.parquet`, `s2_pages.parquet`, `series_info.json` | 5 s for 7,000 S2 pages (about 1 min expected for 40,000), 0.8 GB. Builds S2 only when every selected page is stored (`--allow-incomplete-s2` builds it from what is stored and reports the coverage; `--series S1` builds S1 only) |
| 23 | `bash ../jobs/heavy_lock.sh nice -n 10 ../.venv/bin/python main_study/wiki_led/testF/23_panels.py` | `panel_b.parquet`, `panel_c.parquet`, `nodes_*.parquet`, `overlap_*.parquet`, `panels_meta.json` | 20 s, 1.2 GB |
| 24a | `nice ../.venv/bin/python main_study/wiki_led/testF/24_G2_matchmaking.py --series S2 --stage shifts` | `shifts_S2.parquet`, `shift_drivers_S2.parquet` | 10 to 20 s, 0.35 GB for 7,000 S2 pages (S1: 0.75 GB); with 40,000 pages about 1 min and 1.2 GB (the dense view matrix is 0.66 GB) |
| 22d | from `handoff/`: `bash jobs/bg.sh testF_desktop main_study/wiki_led/testF/22_download_views.py --desktop S2 --job-name testF_desktop` | `desktop_S2.parquet` | 2 requests per rise, about 0.7 s per rise |
| 24b | `bash ../jobs/heavy_lock.sh nice -n 10 ../.venv/bin/python main_study/wiki_led/testF/24_G2_matchmaking.py --series S2 --stage effects` | `g2_S2_tests_{a,b,c}.parquet`, `g2_S2_pooled.csv`, `g2_S2_paired_b_minus_c.csv`, `g2_S2_summary.json` | 7 min with 2,000 resamples, 3 workers and 920 rises; 0.4 GB. Refuses if a rise driver lacks desktop data |
| 24r | the same with `--include-flagged` (Chapter 6's robustness run) | `*_with_flagged` files | as 24b |
| 25c | from `handoff/`: `bash jobs/bg.sh testF_g3 main_study/benchmark/_locked.py ../wiki_led/testF/25_G3_forecast.py --phase chronos` | `chronos2_out/chronos2_ais2_forecasts.parquet`, `..._ais1_...`, `g3_chronos_timing.json` | 6 to 8 min per variant on this Mac (74 to 102 tasks a second, 36,081 tasks), so 12 to 16 min for both; 1.0 GB |
| 25e | `nice ../.venv/bin/python main_study/wiki_led/testF/25_G3_forecast.py --phase evaluate` | `g3_level_rise.csv`, `g3_pairs.csv`, `g3_wikionly.csv`, `g4_wikionly.csv`, `g3_summary.json` | 3 s, 0.6 GB |
| 26 | `nice ../.venv/bin/python main_study/wiki_led/testF/26_G1_validation.py` | `g1_scores.csv`, `g1_summary.json` | 3 to 10 s |
| 27 | `nice ../.venv/bin/python main_study/wiki_led/testF/27_reliability.py` | `reliability.csv`, `reliability_summary.json` | 1 s |
| 28 | `nice ../.venv/bin/python main_study/wiki_led/testF/28_report.py` | `data/reports/testF_results.md`, `testF_results.json` | 1 s |

If S2 is not complete by 2026-10-22 18:00 +07 (the addendum's time rule), run 21 with `--allow-incomplete-s2` only to report coverage, and run G2 on S1: 21 `--series S1`, 24 `--series S1` (with `22 --desktop S1`), 25 `--variants ais1`; Chronos-2 + S2 then cannot be scored and the report says so. The Chronos-2 model (`amazon/chronos-2`, the benchmark's revision) is in the local Hugging Face cache.

## What each step does
- 20 parses and checks the answers (rules at the top of the script), keeps main pages, the one-day sample, books, the second pass and the judge apart, lists lines to re-ask, writes the assignments with weights 1.0, 0.6, 0.3.
- 21 builds S1 (views on top-500 days, all confidences) and S2 (full daily views, confidence 2 or 3) per week as a share of all English Wikipedia user views, narrow themes from the assignments and middle themes as the sum of their narrow themes; monthly series with the benchmark's rule (`benchmark/07_stage2_features.py`, `monthly_log`).
- 22 downloads S2 views (REST per-article, all-access, user agent, 2015-07-01 to 2026-09-30) and, with `--desktop`, the desktop views of the page that drives each rise.
- 23 builds panels b and c with the Study 3 panel functions (layout of `data/db/study3/demand_panel.parquet`).
- 24 finds rises with `interest/_shifts.py` and Chapter 6's settings, applies the quality flags of `interest/09` (one day, desktop only), and runs Chapter 6's event study, synthetic control, placebo categories and years and the clustered bootstrap (`study3/_analysis.py`, `12_shift_effects.py`) on panels a, b and c; it copies the stored Chapter 6 concept-page rows next to them and adds panel b minus panel c (G4).
- 25 runs the benchmark's Chronos-2 runner with the new monthly series as covariate, scores it with the benchmark's `Cmp` class (AvgRelMAE with the category bootstrap, rank correlation with month blocks, paired differences), and computes the Wikipedia-only ranking with the Test C measure on the main rows and on panels a, b, c (G4).
- 26 scores the AI sorter and the two stored routings against the judge; 27 compares the two sorting passes; 28 writes one plain report.

## Choices the addendum did not fix
Each script lists them at its top (NOT IN ADDENDUM) and 28 repeats them in the report. Three the main session should read before the run:
1. G2's decision does not say which level or method decides. Step 24 gives the decision line for the narrow level, the middle level and both levels pooled, each for the synthetic control and the own trend. Chapter 6's headline used the synthetic control per level.
2. Donor and placebo-year screens use the new series' rises plus the stored GDELT rises ('both sources' of Chapter 6, with the new series in place of the concept pages). `--screen new` or `--screen all` change this.
3. S2 uses the page-theme pairs of confidence 2 or 3 (a confidence-1 pair of a page that has another theme of confidence 2 or 3 does not count).

## Mock test (repeatable)
A mock world is a folder with a file `MOCK`; every script pointed at it with `--root` shuffles borrowing across themes and months before use (`_testf_analysis.shuffle_panel`, `shuffle_history`), writes its reports inside the folder and allows the mock-only options (`--mock-inject`, `--mock-fill`, `--boot`). Real runs refuse those options.

```
M=<scratch folder>; D=main_study/wiki_led/testF; PY=../.venv/bin/python
$PY $D/90_mock_world.py --out $M --stage sort        # random sortings with faults, second pass, judge; jobs.tsv and out/
$PY $D/20_parse_outputs.py --root $M
$PY $D/90_mock_world.py --out $M --stage reask       # re-ask answers as a new job
$PY $D/20_parse_outputs.py --root $M
$PY $D/90_mock_world.py --out $M --stage views       # synthetic S2 views (5 pages left for 22)
$PY $D/22_download_views.py --root $M --limit 5      # live check, 5 requests
$PY $D/21_series.py --root $M
$PY $D/23_panels.py --root $M
$PY $D/24_G2_matchmaking.py --root $M --series S2 --stage shifts
$PY $D/22_download_views.py --root $M --desktop S2 --limit 10
$PY $D/24_G2_matchmaking.py --root $M --series S2 --stage effects [--mock-inject 0.3 --boot 200]
$PY $D/25_G3_forecast.py --root $M --phase chronos --variants ais2
$PY $D/25_G3_forecast.py --root $M --phase evaluate --mock-fill
$PY $D/26_G1_validation.py --root $M
$PY $D/27_reliability.py --root $M
$PY $D/28_report.py --root $M
$PY $D/91_selftest.py                                # hand-checkable unit tests (parser, S2 cut, shuffles, weights, monthly rule, Test C measure, G1, reliability)
```
