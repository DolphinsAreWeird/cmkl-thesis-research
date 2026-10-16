#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
LOG=../data/reports/s2r_ext2.log
OMP_NUM_THREADS=1 nice -n 10 ../.venv/bin/python -u study2r/07_detect_shifts.py >> $LOG 2>&1 && echo S2R_DET_DONE >> $LOG || echo S2R_FAILED >> $LOG
