#!/bin/bash
# Setup cron job for Marketman on Ubuntu
# Usage: bash scripts/setup-cron.sh

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CRON_SCRIPT="${REPO_ROOT}/scripts/run-signals.sh"
CRON_LOG="${REPO_ROOT}/logs/cron.log"

# Create log file
mkdir -p "${REPO_ROOT}/logs"
touch "$CRON_LOG"

# Check if cron already exists
if crontab -l 2>/dev/null | grep -q "run-signals.sh"; then
    echo "Cron job already installed"
    crontab -l | grep run-signals.sh
    exit 0
fi

# Create temporary crontab with marketman entries
TEMP_CRON=$(mktemp)
crontab -l 2>/dev/null >> "$TEMP_CRON" || true

cat >> "$TEMP_CRON" <<EOF

# Marketman trading signals - every 5 minutes during market hours (9:30 AM - 4:00 PM ET)
*/5 9-16 * * 1-5 $CRON_SCRIPT >> $CRON_LOG 2>&1

# Cleanup old signal files (retain 30 days)
0 0 * * * find $REPO_ROOT/logs -name "signals_*.json" -mtime +30 -delete

EOF

# Install crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✓ Cron job installed"
echo "Cron will run: $CRON_SCRIPT"
echo "Logs: $CRON_LOG"
echo ""
echo "View active cron jobs:"
crontab -l | grep -v "^#" | grep -v "^$"
