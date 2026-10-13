#!/bin/zsh
# Interest side of the main study (checkpoint 2): GDELT and Wikipedia interest per theme node, shift labels, controls.
# Re-runnable: API answers are cached under data/db/interest/wiki/ and every downloaded page-view file is kept, so a rerun
# only fetches what is missing. Steps 04 and 06 call the Wikidata, MediaWiki and Wikimedia REST APIs (about one request
# per second; 06 takes about two hours from scratch); set SKIP_API=1 to rebuild everything from the cached files only.
# Taxonomy: INTEREST_TAXONOMY=<folder> (default data/db/taxonomy_v2) to rerun on v3; values without a Wikipedia choice
# in _wiki_choices.py stop step 05 with a list, so new values get a hand choice before any series is built.
# No demand data (Seattle, LibriVox) are read by any of these scripts.
set -e
cd "$(dirname "$0")"
PY=../../../.venv/bin/python
for s in 01_gdelt_codes 02_gdelt_map 03_gdelt_series; do
  echo "=== $s $(date +%H:%M:%S)"; /usr/bin/time -p $PY $s.py
done
if [[ -z "$SKIP_API" ]]; then
  for s in 04_wiki_candidates 05_wiki_articles 06_wiki_pageviews; do
    echo "=== $s $(date +%H:%M:%S)"; /usr/bin/time -p $PY $s.py
  done
fi
for s in 07_wiki_series 08_shift_labels 09_wiki_spike_check 10_gdelt_drivers 11_quality_flags 12_controls; do
  echo "=== $s $(date +%H:%M:%S)"; /usr/bin/time -p $PY $s.py
done
