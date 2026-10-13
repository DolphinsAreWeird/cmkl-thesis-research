#!/bin/zsh
# Run the main-study pipelines in order (from code/main_study).
#   ./run_all.sh v2   checkpoint 1 (taxonomy v2, data/db/taxonomy_v2). 00 calls the SPL API (a few small aggregate
#                     queries) and freezes the ebook line count; SKIP_API=1 reuses the saved counts.
#   ./run_all.sh v3   checkpoint 2 (taxonomy v3, data/db/taxonomy_v3): all three formats, print subject headings, the
#                     v2 tree kept fixed. The line counts are frozen in data/db/taxonomy_v3/spl_snapshot.json; delete
#                     that file (or set REFRESH_SNAPSHOT=1) to read the files as they are now. 20 (LibriVox) runs
#                     before 19 so the number tables include it. 18 reads the missing-month rule from study3/.
#   ./run_all.sh      both, v2 first.
set -e
cd "$(dirname "$0")"
PY=../../.venv/bin/python
WHICH=${1:-all}
if [[ $WHICH == v2 || $WHICH == all ]]; then
  [[ -z "$SKIP_API" ]] && $PY 00_spl_api_counts.py
  for s in 01_spl_rows 02_spl_profile 03_spl_title_table 04_goodreads_link 05_phrases_facets 06_theme_hierarchy 07_assign_works 08_quality_checks 09_sanity_series; do
    echo "=== v2 $s $(date +%H:%M:%S)"; /usr/bin/time -p $PY $s.py
  done
fi
if [[ $WHICH == v3 || $WHICH == all ]]; then
  [[ -n "$REFRESH_SNAPSHOT" ]] && rm -f ../../data/db/taxonomy_v3/spl_snapshot.json
  for s in 10_v3_spl_rows 11_v3_work_table 12_v3_profile 13_v3_goodreads_link 14_v3_headings 15_v3_hierarchy 16_v3_assign 17_v3_quality 18_v3_controls 20_v3_librivox 19_v3_report_tables; do
    echo "=== v3 $s $(date +%H:%M:%S)"; /usr/bin/time -p $PY $s.py
  done
fi
