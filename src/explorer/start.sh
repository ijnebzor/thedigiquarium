#!/bin/bash
# Standard tank startup: explore immediately (deps pre-installed in image)
# Baselines are handled by THE SCHEDULER (sequential, one tank at a time)
cd /tank
echo "Starting $TANK_NAME..."
echo "Starting exploration..."
exec python3 -u /tank/explorer.py
