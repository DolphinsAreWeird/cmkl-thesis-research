#!/bin/bash
# Stop a background job started with bg.sh.  usage: jobs/stop.sh NAME
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; pid=$(cat "$ROOT/data/reports/$1.pid")
pkill -TERM -P "$pid"; kill -TERM "$pid" 2>/dev/null; echo "stopped $1"
