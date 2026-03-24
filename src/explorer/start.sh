#!/bin/bash
# Standard tank startup: baseline then explore
cd /tank
echo "Starting $TANK_NAME..."
echo "Running baseline assessment..."
python3 -u /tank/baseline.py
echo "Baseline complete. Starting exploration..."
exec python3 -u /tank/explorer.py
