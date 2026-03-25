#!/bin/bash
echo "🐠 Starting $TANK_NAME ($LANGUAGE)..."

# Install dependencies
pip install --quiet --break-system-packages requests 2>/dev/null || true

# Run baseline first, then explore
echo "   Running baseline assessment first..."
python3 /tank/baseline.py

echo "   Baseline complete. Starting exploration..."
python3 /tank/explore.py
