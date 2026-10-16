# Context-reading routing of the daily top-500 pages (stage 2c)

Written 2026-10-15 08:43. Settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json (2c). No demand data read.

- Pool: 25,645 pages with a best cosine of at least 0.55 in addendum a; 22,725 have a short description in their text; 128,225 page-candidate pairs.
- Entailment probability of the pairs: median 0.01; share at or above 0.5: 35.7%; at or above 0.8: 32.8%.
- Routed (any candidate at or above 0.5): 22,897 pages (89.3% of the pool); addendum a routed 6,002 pages at cosine 0.70; overlap 5,547.
- Nodes with a series: 345 (middle 86, narrow 240); median share of full weeks with routed views: middle 65%, narrow 22%.

## Agreement with the hand-checked pages that are in the pool

271 hand-checked pages are in the pool.

result | count
same node | 270
other node | 1


## Examples named in addendum a

- Ocean's 8: ocean (cos 0.56, entail 0.80); titanic (cos 0.47, entail 0.00); seafaring (cos 0.41, entail 0.04); surfing (cos 0.36, entail 0.00); submarines (cos 0.35, entail 0.00)
- The Bear (TV series): bears (cos 0.71, entail 0.10); television (cos 0.52, entail 1.00); wolves (cos 0.40, entail 0.00); monsters (cos 0.38, entail 0.00); frogs (cos 0.34, entail 0.00)
- Kinds of Kindness: kindness (cos 0.75, entail 0.18); law of attraction (cos 0.37, entail 0.00); virtue (cos 0.33, entail 0.01); etiquette (cos 0.32, entail 0.00); positive psychology (cos 0.29, entail 0.02)

## Most-viewed routed pages per broad theme (top 3, by total top-500 views)

- B01: Cleopatra -> classical studies (0.98); Marvel Cinematic Universe -> superheroes (0.82); Spider-Man: No Way Home -> superheroes (0.97)
- B02: Sex -> sexuality (1.00); Sexual intercourse -> sexuality (1.00); International Women's Day -> feminism (0.76)
- B03: Bible -> god (0.73); Pope Francis -> church (0.99); Saint Patrick's Day -> saints (0.59)
- B04: YouTube -> internet (0.98); Instagram -> internet (0.95); Microsoft Office -> software (1.00)
- B05: Canelo Álvarez -> latino (0.99); Critical race theory -> race (0.52); Day of the Dead -> latino (0.99)
- B06: List of Marvel Cinematic Universe films -> film (1.00); List of highest-grossing films -> film (1.00); List of highest-grossing Indian films -> entertainment (0.98)
- B07: Queen Elizabeth The Queen Mother -> mothers and daughters (0.85); Mother's Day -> mothers and daughters (0.71); Adolescence (TV series) -> adolescence (0.97)
- B08: World War II -> war (1.00); Joe Biden -> foreign policy (0.94); Adolf Hitler -> fascism (0.97)
- B09: New York City -> community (0.96); The Pirate Bay -> pirates (0.72); Earth -> earth sciences (0.92)
- B10: CEO -> management (0.99); Jimmy Hoffa -> labor (0.98); Rothschild family -> banking (0.91)
- B11: Juneteenth -> holidays (0.94); Halloween -> holidays (0.99); Saint Patrick's Day -> holidays (1.00)
- B12: Jeffrey Dahmer -> serial killers (1.00); Deaths in 2024 -> death and dying (0.99); Deaths in 2025 -> death and dying (0.98)
- B13: United States Senate -> politics (1.00); Donald Trump -> politics (1.00); Joe Biden -> presidents (1.00)
- B14: Tommy Fury -> personality (0.87); Friendship Day -> friendship (1.00); Sigmund Freud -> psychology (0.84)
- B15: Coronavirus disease 2019 -> disease (1.00); 2020 coronavirus pandemic in India -> epidemiology (0.89); 2019–20 coronavirus outbreak -> disease (1.00)
- B16: Cat -> cats (1.00); Animal (2023 film) -> animals (0.98); Kingdom of the Planet of the Apes -> primates (0.93)
- B17: LeBron James -> sports (1.00); Michael Jordan -> sports (0.96); 2026 FIFA World Cup -> sports (1.00)
- B18: Skathi (moon) -> astrophysics (0.94); Earth -> aliens (0.99); Kepler's Supernova -> astronomy (1.00)
- B19: QAnon -> conspiracy (1.00); Richard Jewell -> law (1.00); Dennis Rader -> criminology (0.96)
