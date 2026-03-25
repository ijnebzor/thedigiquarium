#!/bin/bash
# Tank startup: Run baseline first, then explore
cd /tank

echo "🐠 Starting $TANK_NAME..."
echo "   Running baseline assessment first..."

python3 -u /tank/baseline.py

echo ""
echo "   Baseline complete. Starting exploration..."
echo ""

exec python3 -u /tank/explore.py
