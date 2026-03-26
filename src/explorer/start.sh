#!/bin/bash
# Standard tank startup: install deps, then explore
# Baselines are handled by THE SCHEDULER (sequential, one tank at a time)
cd /tank

echo "Installing dependencies..."
pip install --quiet requests pyyaml beautifulsoup4 2>&1 | tail -1
echo "Dependencies installed."

echo "Starting $TANK_NAME..."
echo "Baseline will be run by THE SCHEDULER on the 12-hour cycle."
echo "Starting exploration..."
echo ""
exec python3 -u /tank/explorer.py
