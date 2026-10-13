#!/bin/bash
cd "$(dirname "$0")"; PATH="$PWD/../.venv/bin:$PATH"
START=1 python3 -u exp_full.py y_fav 3 >> ../data/reports/pipeline.log 2>&1
python3 -u shapley4.py >> ../data/reports/pipeline.log 2>&1
python3 -u summarize.py >> ../data/reports/pipeline.log 2>&1
echo "ALL DONE $(date)" >> ../data/reports/pipeline.log
