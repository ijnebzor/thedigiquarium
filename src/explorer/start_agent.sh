#!/bin/bash
# Agent tank startup: install deps, then agent-specific explorer
# Baselines are handled by THE SCHEDULER (sequential, one tank at a time)
cd /tank

echo "Installing dependencies..."
pip install --quiet requests pyyaml beautifulsoup4 2>&1 | tail -1
echo "Dependencies installed."

echo "Starting agent $TANK_NAME (type: $AGENT_TYPE)..."
echo "Baseline will be run by THE SCHEDULER on the 12-hour cycle."
echo "Starting agent exploration..."
echo ""
exec python3 -u /tank/agents/${AGENT_TYPE}.py
