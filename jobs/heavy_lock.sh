#!/bin/bash
# Runs a CPU-heavy command only when no other heavy command holds the lock (one heavy job at a time on this 8 GB Mac).
# Usage: bash jobs/heavy_lock.sh nice -n 10 .venv/bin/python code/....py args
LOCK="$(cd "$(dirname "$0")/.." && pwd)/data/reports/.heavy.lock"
until mkdir "$LOCK" 2>/dev/null; do sleep 60; done
echo "$$ $(date '+%F %T') $*" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
"$@"
