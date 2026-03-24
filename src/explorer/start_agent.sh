#!/bin/bash
# Agent tank startup: baseline then agent-specific explorer
cd /tank
echo "Starting agent $TANK_NAME (type: $AGENT_TYPE)..."
echo "Running baseline assessment..."
python3 -u /tank/baseline.py
echo "Baseline complete. Starting agent exploration..."
exec python3 -u /tank/agents/${AGENT_TYPE}.py
