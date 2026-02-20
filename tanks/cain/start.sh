#!/bin/bash
echo "🐠 Starting cain (OpenClaw agent)..."

# Check if baseline exists
BASELINE_COUNT=$(ls /logs/baselines/*.json 2>/dev/null | wc -l)

if [ "$BASELINE_COUNT" -eq "0" ]; then
    echo "   Running baseline assessment first..."
    python3 /tank/baseline.py
    echo "   Baseline complete. Starting exploration..."
fi

# Run explorer
python3 /tank/explore.py
