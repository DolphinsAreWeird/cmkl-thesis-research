# Method benchmark: scripts in the order they were run

Run every script from inside `code/` with the project environment, for example `../.venv/bin/python main_study/benchmark/03_evaluate.py`. Settings are read from `prereg/benchmark_settings_2026-10-15.json` and the addenda in `prereg/addenda_benchmark/`; results go to `data/db/benchmark/` and the reports to `data/reports/benchmark_*.md`. The thesis chapters that describe this work are Chapters 4 and 5 and Appendix A (`paper/Thesis_Draft_*.md`).

| Step | Scripts | What they do |
| --- | --- | --- |
| Stage 1 (21 pipelines) | `01_lightgbm.py`, `02_chronos.py`, `03_evaluate.py`, `04_figure.py` | LightGBM and Chronos-Bolt forecasts, the scoring rules of the settings record (error ratio, confidence set, segments), a first figure |
| Stage 2a to 2c (routings) | `05_top_routing.py`, `06_routing_forecast.py`, `07_stage2_features.py`, `08_nli_routing.py` | Routing the daily top 500 Wikipedia pages into themes by embedding and by reading in context; book-anchored series; duration-weighted interest |
| Stage 2 (models) | `09_chronos2.py`, `10_change_models.py`, `11_level_h3.py`, `14_demand_aligned.py` | Chronos-2 alone and with interest, models trained on the change, horizon 3, routing weighted by past demand |
| Stage 2f (learned themes) | `15a_learned_categories.py` to `15d_learned_report.py` | Themes learned from catalogue descriptions (embedding clusters), their demand panel, forecasts and report |
| Scoring and tables | `12_assemble_stage2.py`, `03_evaluate.py --stage2`, `13_stage2_report.py`, `17_leaders_h23.py`, `18_doc_tables.py` | One wide table of forecasts for all 52 pipelines, scoring, the report `data/reports/benchmark_stage2.md`, the pipelines run at horizons 2 and 3, markdown tables |
| Model pairs | `23_pairs_main_sample.py` (current), `19_extra_pairs.py` (superseded) | Model-against-model gaps and the effect of interest by kind of month. `19_extra_pairs.py` used the forecasts common to the few pipelines of each pair, a larger sample than the main tables; `23_pairs_main_sample.py` uses exactly the rows of the main tables and is the source of the numbers in the thesis (see `prereg/DEVIATIONS.md`, 16 Oct 08:15) |
| Thesis figures | `20_figure_pipeline.py`, `21_figures_tables.py`, `22_figures_data.py`, `24_figure_duration.py`, `_thesis_style.py` | The ten figures of the thesis (`paper/figures/`); the values behind them are written to `data/db/benchmark/stage2_results/figure_values_*.csv` |
| Helpers | `_chain.py`, `_locked.py`, `_stage2_common.py` | Run several steps one after another under the heavy-job lock; shared functions |
