#!/bin/bash

# Marketman automated runner script
# Runs every 5 minutes and logs signals to timestamped files

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${REPO_ROOT}/data"
LOGS_DIR="${REPO_ROOT}/logs"
CSV_FILE="${DATA_DIR}/live-feed.csv"
CONFIG_FILE="${REPO_ROOT}/config/thresholds.json"

# Fallback to sample if live feed not available
if [ ! -f "$CSV_FILE" ]; then
    CSV_FILE="${DATA_DIR}/sample.csv"
fi

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
OUTPUT_FILE="${LOGS_DIR}/signals_${TIMESTAMP}.json"

cd "$REPO_ROOT"
python3 -m marketman.runner \
    --config "$CONFIG_FILE" \
    --data "$CSV_FILE" \
    --symbol MNQ \
    --warmup 25 \
    --format json \
    --output "$OUTPUT_FILE" \
    --log-level INFO

echo "Signals written to $OUTPUT_FILE"
