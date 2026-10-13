#!/bin/bash
# Runs one quota-day of YouTube collection after the 07:00 UTC reset, then repeats daily.
cd "$(dirname "$0")"; PATH="$PWD/../.venv/bin:$PATH"
while true; do
  now=$(date -u +%s); target=$(date -u -d "today 07:05" +%s); [ $now -ge $target ] && target=$(date -u -d "tomorrow 07:05" +%s)
  sleep $((target-now))
  python3 -u youtube_collect.py ../data/interim/youtube_queue.csv ../data/raw/youtube_clean.json >> ../data/reports/youtube_daily.log 2>&1
done
