#!/bin/bash
cd "$(dirname "$0")"; PATH="$PWD/../.venv/bin:$PATH"
python3 -u exp_full2.py y_view 3 > ../data/reports/run2.log 2>&1
python3 -u exp_full2.py y_fav 3 >> ../data/reports/run2.log 2>&1
echo "ALL DONE" >> ../data/reports/run2.log
