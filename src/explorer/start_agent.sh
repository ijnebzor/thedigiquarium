#!/bin/bash
# Agent tank startup: explore immediately (deps pre-installed in image)
# Baselines are handled by THE SCHEDULER (sequential, one tank at a time)
cd /tank
echo "Starting agent $TANK_NAME (type: $AGENT_TYPE)..."
echo "Starting agent exploration..."
exec python3 -u /tank/agents/${AGENT_TYPE}.py
