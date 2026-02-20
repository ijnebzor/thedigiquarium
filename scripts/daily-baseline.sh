#!/bin/bash
# Daily baseline runner - called by cron
# Runs baseline assessment for a tank

TANK=${1:-adam}
CONTAINER="tank-01-${TANK}"

echo "$(date): Running daily baseline for $TANK"

# Run baseline inside container
docker exec $CONTAINER python3 /tank/baseline.py

echo "$(date): Baseline complete for $TANK"
