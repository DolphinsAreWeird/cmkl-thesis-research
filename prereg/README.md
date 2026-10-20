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
- `addenda_benchmark/2026-10-17_c_final_test_forecasts.json` SHA-256: d893b6b386b3e7e1cd64f59455681b842457fff981c4fff82a8a30639a1e6729 (fixed 2026-10-17 03:14, before any forecast for a month after 2026-08 and before any demand value after 2026-08 was downloaded or read: the final unseen test, part 1, the forecasts; part 2, the targets and scoring, is fixed in a later addendum before any month after 2026-08 is downloaded)
- `final_test/forecasts_origin_2026-08.csv` SHA-256: 6f58c13fb51a894784ca038826da322fa28b44791fbd96d649bfe43c16a880e6 (made 2026-10-17 03:22 under addendum c: forecasts of the final-test pipelines at origin 2026-08 for the target months 2026-09 to 2026-11, 2,142 rows; no demand value after 2026-08 existed in the project when they were made); its meta file `final_test/forecasts_origin_2026-08_meta.json` SHA-256: fb279e1fbf7f4e4d8bf787cf66460fe33c4cb124319f96f1658b573bff2b12b5
- `addenda_benchmark/2026-10-17_d_final_test_scoring.json` SHA-256: 4be851746be23ada700d789fd641a88338eeb1831988b261fd7376b9c35b263c (fixed 2026-10-17 04:10, before any month after 2026-08 was downloaded or read: the final unseen test, part 2, how the demand of the new months is built, the metrics, the decision rules and the timing; the download and scoring code refuse to run unless this line is present)
- `wiki_led_settings_2026-10-20.json` SHA-256: 88d895c38c128753aaaabf3294c85969c066db8b0852089ae6e47609958c145b (fixed 2026-10-20 15:08, after the advisor asked for Wikipedia-led prediction of books and before any Wikipedia-only prediction of single books was computed; Tests A existing books, B new books, C themes to follow in an addendum)
- `addenda_wiki_led/2026-10-20_a_test_c_themes.json` SHA-256: 35c917cbce539ef75580d793fbe161b72ba4ecaf59a24e59889cb56b71b648bb (fixed 2026-10-20 15:13, before any Test A score and before any Test C feature, selection or forecast: Test C, Wikipedia-only theme forecasts with library-guided walk-forward choice of articles)
- `addenda_wiki_led/2026-10-20_b_placebo_test_a.json` SHA-256: 9589a400807417bb7f8c3e381ab0c0bebba6e55af5c14aeee5026809887aad27 (fixed 2026-10-20 15:42, after Test A and C results, before any placebo feature or forecast: each book given a similar-traffic book's Wikipedia pages)
- `live_alert/README.md` SHA-256: 975cb5d0352405dcd1f9bfe288b4422d468d0d50090b23c5e039cffbff7bc6e4 (live October 2026 alert list, frozen 2026-10-20 17:00 before the library released September or October 2026)
- `live_alert/alert_list_2026-10.csv` SHA-256: 826ba047d24435f839faf6ab872a6c4c4510bdc12fdb2f4cabcf62d983b4d2b6 (live October 2026 alert list, frozen 2026-10-20 17:00 before the library released September or October 2026)
- `live_alert/ranking_all_2026-10.csv` SHA-256: 9a0adb053413a6dcec03958664e6a50f7d45efadced16170d9dc7bbe30584912 (live October 2026 alert list, frozen 2026-10-20 17:00 before the library released September or October 2026)
- `addenda_wiki_led/2026-10-20_c_improvement_round.json` SHA-256: b6a7319372f57be6d9c337f7fcda2467f46b7ba3085513a6068a15f200023dac (fixed 2026-10-20 17:09, before any tuning result of the improvement round: candidates, 2019-2023 tuning, selection rule, one run on 2024-2026)
- `addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json` SHA-256: 5f7f4ef33070f466951c7e37491c17fc3f746d2cf0abad7c90be58a832ad4585 (fixed 2026-10-20 17:20, before any v2, Test D, Test E or Test B result: improvement round v2 from the research note, Test D all books by format, Test E LibriVox, the 90% question)
