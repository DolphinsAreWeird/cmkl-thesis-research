#!/bin/bash
cd "$(dirname "$0")"; PATH="$PWD/../.venv/bin:$PATH"
while ! grep -q DONE ../data/reports/pageviews.log; do sleep 30; done
echo "pageviews done $(date)" > ../data/reports/pipeline.log
python3 -u features.py >> ../data/reports/pipeline.log 2>&1
python3 -u reports_data.py >> ../data/reports/pipeline.log 2>&1
python3 -u exp_full.py y_view 3 >> ../data/reports/pipeline.log 2>&1
python3 -u exp_full.py y_fav 3 >> ../data/reports/pipeline.log 2>&1
python3 -u shapley4.py >> ../data/reports/pipeline.log 2>&1
python3 -u summarize.py >> ../data/reports/pipeline.log 2>&1
echo "ALL DONE $(date)" >> ../data/reports/pipeline.log
