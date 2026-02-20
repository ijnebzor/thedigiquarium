#!/bin/bash
# Start the Digiquarium Autonomous Caretaker
# This runs 24/7 on the NUC to maintain the experiment

cd "$(dirname "$0")"
export DIGIQUARIUM_DIR="/home/ijneb/digiquarium"

echo "Starting Digiquarium Caretaker..."
exec python3 caretaker.py