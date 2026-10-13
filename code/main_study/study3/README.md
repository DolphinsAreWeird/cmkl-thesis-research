# Study 3 analysis code

When does a rise in public interest in a theme turn into more reading and listening of books on that theme?
This folder holds the demand panel and the tests fixed in `prereg/study3_settings_2026-10-13.json` (13 Oct 2026).

## Ground rules
- Settings come only from the fixed record. `_settings.py` checks the record's SHA-256 against `prereg/README.md`
  and stops if they differ, applies `prereg/addenda/*.json` in file-name order, and parses every number from the
  record's own wording. No script hard-codes a threshold, window, seed or size from the record (a test checks this).
- Choices the record does not make are marked `# NOT IN RECORD:` in the code and listed below. Log them in
  `prereg/DEVIATIONS.md` if they are kept.
- Order is enforced. Each step refuses to run if the report of the step before it is missing, or was made on a
  different panel build. The positive controls (step 10) run first; nothing else runs before their report exists.
- Every method was developed and tested on simulated panels only. Step 01 on real data writes structural checks
  only (row counts, months, reconciliation, size-rule counts), never a category's demand.

## Run order (from `code/main_study/study3/`, with `../../../.venv/bin/python`)

| Step | Script | Needs | Writes (data/db/study3/) | Report (data/reports/) |
| --- | --- | --- | --- | --- |
| 01 | `01_demand_panel.py` | taxonomy v3 files | `demand_panel.parquet`, `demand_panel_librivox.parquet` (if LibriVox is mapped), `nodes.parquet`, `node_overlap.parquet`, `demand_panel_meta.json` | `study3_panel_build.md` |
| 10 | `10_positive_controls.py` | report 01, interest shifts (or `--without-shifts`), GDELT-durations addendum | `positive_controls.csv` | `study3_10_positive_controls.md` |
| 11 | `11_power.py` | report 10 with all controls passed (or `--accept-failed-controls`), interest shifts (or `--without-shifts`) | `power_draws.parquet`, `power_summary.csv` | `study3_11_power.md` |
| 12 | `12_shift_effects.py` | report 11, interest shifts | `shift_effects.parquet`, `pooled_effects.csv` | `study3_12_shift_effects.md` |
| 13 | `13_carryover.py` | report 12 | `carryover_coefs.csv`, `carryover_lags.csv` | `study3_13_carryover.md` |
| 14 | `14_tone.py` | report 13, GDELT weekly tone | `tone_features.parquet`, `tone_models.csv` | `study3_14_tone.md` |

Common options: `--workers N` (parallel workers, default at most 4), `--allow-dev-taxonomy` (accept a
panel built from the taxonomy v2 fallback; not final), `--sim DIR` (run on a simulated world, see Tests).
Rebuild the panel (step 01) whenever the taxonomy or the checkout files change; later steps print a warning when an
input file is newer than the panel build.

## Settings each step reads (names as parsed in `_settings.py`)
- 01: `seattle_formats`, `digital_formats`, `missing_months`, `min_works`, `min_median_weighted`, `size_lookback`,
  `levels_tested`, `levels_descriptive`, `title_backup_max_works` (node counts for the backup rule).
- 10: `controls` (name, label, level, month), `title_backup_max_works`, `alpha`, `window_primary`,
  `window_secondary`, plus everything step 12 uses for one test.
- 11: `power_lifts`, `power_draws`, `power_window`, `power_alpha`, `power_rate`, `power_seed`, `study_start`, and the
  synthetic-control and donor settings.
- 12: `es_fit_len`, `es_fit_end`, `es_pretrend`, `sc_fit`, `sc_demean`, `donor_no_shift`, `donor_max_overlap`,
  `window_primary`, `window_secondary`, `min_window_months`, `placebo_year_from`, `boot_n`, `boot_seed`, `bh_q`,
  `alpha`, `carry_lag`, `study_start`, `levels_tested`.
- 13: `carry_window`, `carry_ref_class`, `carry_lag`, `boot_n`, `boot_seed`.
- 14: `tone_weeks`, `tone_baseline_weeks`, `tone_placebo_n`, `tone_placebo_len`, `boot_n`, `boot_seed`, and the
  shift duration bounds (`sustained_min`, `intermediate_eq`, `fading_max`).

## Inputs
- Seattle (taxonomy v3, `data/db/taxonomy_v3/`): `spl_rows_{audiobook,ebook,book}.parquet` (print is `book`),
  `spl_record_work.parquet`, `spl_works.parquet`, `work_theme.parquet` (main assignment, no title words),
  `work_theme_title_backup.parquet` (flagged backup, used only for a control category with fewer than 50 works),
  `theme_nodes.parquet`. If `work_theme.parquet` is missing, the v2 themes are carried onto v3 works by work key as a
  development build, and steps 10 to 14 refuse it unless `--allow-dev-taxonomy` is passed.
- SPL API counts per material type and month: `data/db/taxonomy_v2/spl_api_counts.parquet`. A month with fewer rows
  than the API reports (a partly downloaded print month) is treated as missing.
- LibriVox: `data/db/listening.parquet` with the expected mapping `data/db/taxonomy_v3/librivox_work_theme.parquet`
  (`book_id, node_id, level, strength`). Without the mapping, LibriVox is skipped with a message in the build report.
- Interest (from `code/main_study/interest/`, adapter in `_interest.py`, the only place to change if the files differ):
  - `data/db/interest/shifts.parquet`. The interest side's own layout is read as written by
    `interest/08_shift_labels.py` (`source`, `level` 1/2/3, `node_id`, `start_week`, `label`, `size`, `dur_rt`,
    `seasonal`, `large`, and for GDELT `label_gdelt_scaled`, `size_gdelt_scaled`). A minimal layout (`source`,
    `node_id`, `level`, `start_week`, `duration_class`, `size`, `large`, `seasonal`, optional `duration_count`) is
    accepted too. The adapter checks Mondays, classes, duplicates, and that `large` and the class agree with the
    record's thresholds. GDELT rows use the GDELT-scaled label and size when present. Shifts labelled `interrupted`
    or `censored` (no real-time class) are not tested but still count in the donor and placebo-year screens.
  - `data/db/interest/gdelt/weekly_node.parquet`: `node_id`, `level`, `week` (ISO Monday), `tone`, `positive`,
    `negative`, `partial_week` (partial weeks are treated as missing).
  - The record says the GDELT shift durations, computed from interest data alone, are appended to it before any
    demand data are read. Steps 10 to 12 refuse to run on a shifts table with GDELT shifts until an addendum in
    `prereg/addenda/` carries those values under `shift_definitions.gdelt_durations` (for example
    `{"shift_definitions.gdelt_durations.values": {"ratio": ..., "sustained_min": ..., "fading_max": ...}}`). The
    interest side's proposal is in `data/db/interest/gdelt_duration_scaling.json`.

## Modules
- `_settings.py` record loading, hash check, addenda, parsing.
- `_files.py` paths, options, step order, reports. `_inputs.py` real-data readers. `_interest.py` interest adapter.
- `_build.py` pure panel-building functions. `_methods.py` pure methods (event study, synthetic control, rank
  p-value, placebo helpers, Benjamini-Hochberg, clustered bootstrap, power summary, carry-over OLS, tone features).
- `_analysis.py` wide matrices per level and format, donor rules, one full test of a category at a month 0, placebo
  years, power draws, chunked parallel runs. `_sim.py` simulated worlds.

## Tests
`../../../.venv/bin/python tests/run_tests.py` (pytest is not installed; the same files also run under pytest).
They cover: settings hash failure and addenda; panel building on hand-made data (weighted shares, missing and zero
months, the rolling 24-month size rule, partial months, title words, overlap); fit windows that never touch months
-6 and later (event study) or -2 and later (synthetic control); exact recovery in noise-free data; missing months;
injected effects recovered at about the right size; about uniform p-values on null panels; donor rules; placebo
years; power; the carry-over model; tone windows; and the whole script chain on a simulated world (order enforced,
outputs written, a new panel build invalidates later reports, record sizes cannot be overridden in real runs).
`--draws`, `--boot` and `--placebos` exist only for simulated runs.

## Choices not in the record (`# NOT IN RECORD:`)
1. Size rule: the median needs at least half of the 24 look-back months available; format-wide missing months are
   skipped and zero months count as zero.
2. A month with fewer rows than the SPL API count is a partial download and is treated as missing.
3. Donor overlap counts a category's works per format over all months of data.
4. Donors must also pass the minimum-size rule at that window and format.
5. Donor and placebo-year shift screens use shifts from both sources and of every class, seasonal included.
6. A donor missing any month in which the treated category is observed is left out of the pool.
7. Demeaning uses the same available months for every unit (months where the treated category is observed).
8. Fits need at least 75% of their window's months (event study 18 of 24, synthetic control 17 of 22, tone baseline
   and shift weeks); a calendar month never seen in the event-study fit gets no prediction.
9. Smallest donor pool: 2 (the report shows the smallest possible p, 1 / (donors + 1)).
10. One-sided rank p-value: units are ranked by sign(effect) x post/pre RMSPE, with post RMSPE over the effect window
    being tested; ties count against the treated category.
11. Placebo years: "no shift in that window" uses months -6 to +6; the placebo window must pass the size rule; the
    comparison uses the primary window.
12. Event-study placebo categories are the synthetic control's donors.
13. Month 0 is the month of the shift week's Monday.
14. Positive controls pass with a positive synthetic-control effect (months 0 to +2) and one-sided p < 0.05 in at
    least one Seattle format; LibriVox is shown but does not decide; the title-word backup keeps the main overlap
    table and only reports a pass when the main assignment did not pass.
15. Power: the same placebo draws for every lift size, drawn without replacement.
16. Benjamini-Hochberg family: all main-analysis shift x format tests, primary window; seasonal shifts are a separate
    family. Pooled means by source x level x format, source x level, and duration class.
17. Bootstrap intervals are 95% percentile intervals; bootstrap p-values are descriptive.
18. Carry-over model fitted per source and level, main-analysis shifts only; format dummies are among Seattle
    formats, LibriVox enters through the classic indicator.
19. Tone: each feature in its own model; two-sided placebo p (share of |placebo coef| >= |real coef|); a shift
    blocks max(duration, 4) weeks for placebo windows; baseline excludes the start week; placebo windows use the
    bootstrap seed and are drawn without replacement when enough exist.
20. LibriVox: every month with views is complete; the size rule uses recordings as works and views as checkouts.
21. Shifts without a record duration class (`interrupted`, `censored`) are not tested; they count in the shift screens.
22. Interest adapter: a shift with no seasonal verdict is not seasonal; partial GDELT weeks are missing for tone.
