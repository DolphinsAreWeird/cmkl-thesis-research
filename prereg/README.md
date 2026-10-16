# Fixed settings (pre-registration) for Study 3 and the ranking study

- Fixed on: 13 October 2026, before any category's demand was compared with its interest.
- Record: `study3_settings_2026-10-13.json` (machine-readable; analysis code reads it, never hard-codes thresholds).
- SHA-256 of the record: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- Check: `shasum -a 256 study3_settings_2026-10-13.json` must print the value above.
- Changes after this date: `DEVIATIONS.md`.
- The disclosures inside the record list everything seen before fixing (Study 2 results; a descriptive look at four control categories' Seattle checkouts during the taxonomy check).

## Study 4: forecasting category demand (fixed 13 October 2026)
- Record: `forecast_settings_2026-10-13.json` (read-only). Fixed before any forecast was made or scored, and before the Study 3 main shift results were read.
- SHA-256 of the record: `040a7c7a7416d4a652b9fe5c52ef947447c1a5653db3839757819164f8917bd6`
- Changes after this date: `DEVIATIONS.md` (Study 4 section) and `addenda_forecast/`.

## Study 3b: small and fine-grained categories, count models, sentiment direction (fixed 13 October 2026)
- Record: `study3b_settings_2026-10-13.json` (read-only), fixed before any 3b result was computed; Study 3 and Study 4 results were known (disclosed in the record).
- SHA-256: `7d27f0f9147ad0e7636d2e0ebe070c1cef3e829338472b2602b5dad9196b55a0`

## Study 1 label-window check (fixed 13 October 2026)
- Record: `study1_label_check_2026-10-13.json` (read-only), fixed before these runs; a robustness check of a known result.
- SHA-256: `60944e46ad5d878481b4916d91ddafea306598141dee7cf63cb1c9d625a2b756`

## Study 4b: change forecasts and rare surges, books first (fixed 14 October 2026)
- Record: `study4b_settings_2026-10-14.json` (read-only), fixed before any 4b forecast; Study 3, 3b and 4 results were known (disclosed).
- SHA-256: `a34ab8e2279d4f13409a8786848a1179bd28964d35766c647acbefd44eab9bb4`

## Study 2R: single-book attention on modern Seattle books, data-defined events (fixed 14 October 2026)
- Record: `study2r_settings_2026-10-14.json` (read-only), fixed before any 2R result.
- SHA-256: `33d73cae0cdf76abe9f23952528daeabff719c0155c9bef13f7900246cbe7891`

- `conversation_sources_settings_2026-10-14.json` SHA-256: 60cb9813084729207ab393c2da6d79d6e7f7fd1fedae36c8142fa4f512f2985e (fixed 2026-10-14, before any conversation series was linked to borrowing)
- `brisbane_replication_settings_2026-10-15.json` SHA-256: 08dd33d36c91af4235c684572d87601e8e5d9a2af4003df31e6121d0c639495d (fixed 2026-10-15, before any Brisbane borrowing was linked to interest)
- `benchmark_settings_2026-10-15.json` SHA-256: 609b72d0728d44ceec1134ea888570a4b75b041ee3b7a9c71cb164cc85fa24c7 (fixed 2026-10-15 03:25, before any benchmark score, LightGBM, Chronos or combination forecast was computed)
- `addenda_benchmark/2026-10-15_a_top_pages_routing.json` SHA-256: 391eafeb9ca990d58d69c932bde415297277ee99c0553ab18f3542f329a4eeba (fixed 2026-10-15 03:34, before any series, feature or forecast of the routing comparison)
- `addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json` SHA-256: 9315927d3df0336a534ea0bd248ed68d1fc9a2c5cd30f0ca5c5d6c71d8169a22 (fixed 2026-10-15 07:06, before any stage-2 forecast or score was computed: the secondary metrics, "which themes will rise" as a second task beside level accuracy, every stage-2 pipeline with its settings, the comparisons, horizons and the final-test list; discloses what was seen on 15 Oct)
