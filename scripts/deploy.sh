#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${REPO_ROOT}/venv"
SERVICE_FILE="/etc/systemd/system/marketman.service"
DATA_DIR="${REPO_ROOT}/data"
LOGS_DIR="${REPO_ROOT}/logs"

echo "=== Marketman Deployment Setup ==="
echo "Repository: $REPO_ROOT"

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "Virtual environment activated"

# Create output directories
mkdir -p "$DATA_DIR" "$LOGS_DIR"
echo "Created data and logs directories"

# Compile modules
echo "Validating Python modules..."
python3 -m py_compile strategy.py marketman/*.py

# Test the runner
echo "Testing signal runner..."
python3 -m marketman.runner \
    --config config/thresholds.json \
    --data data/sample.csv \
    --symbol MNQ \
    --warmup 25 \
    --format json \
    --output logs/test-signals.json

echo "✓ Test run successful. Output: logs/test-signals.json"

# Install systemd service if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Installing systemd service..."
    cp systemd/marketman.service.template "$SERVICE_FILE"
    sed -i "s|/path/to/marketman|$REPO_ROOT|g" "$SERVICE_FILE"
    systemctl daemon-reload
    echo "✓ Service installed: $SERVICE_FILE"
    echo "Start with: systemctl start marketman"
else
    echo "Not running as root. To install the systemd service, run with sudo."
    echo "Or manually copy and edit: systemd/marketman.service.template"
fi

echo "=== Setup Complete ==="
