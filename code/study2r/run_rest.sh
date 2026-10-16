#!/bin/bash
# waits for 03, then runs 04, 05, 05b, 06, 07 one after another (one process at a time). Marker lines: S2R_ALL_DONE or S2R_FAILED <step>
cd "$(dirname "$0")/.." || exit 1
LOG=../data/reports/s2r_rest.log
until grep -qE "^[0-9:]+ DONE|Traceback" ../data/reports/s2r_pageviews.log; do sleep 30; done
grep -q Traceback ../data/reports/s2r_pageviews.log && { echo "S2R_FAILED 03" >> $LOG; exit 1; }
for s in 04_weekly_series 05_calibrate_ratio 05b_feasibility 06_file_note 07_detect_shifts; do
  echo "=== $s $(date +%T)" >> $LOG
  OMP_NUM_THREADS=1 nice -n 10 ../.venv/bin/python -u study2r/$s.py >> $LOG 2>&1 || { echo "S2R_FAILED $s" >> $LOG; exit 1; }
done
echo S2R_ALL_DONE >> $LOG
