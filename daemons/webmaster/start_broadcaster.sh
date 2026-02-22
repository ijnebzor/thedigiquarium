#!/bin/bash
# Start the continuous broadcaster if not running

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/broadcaster.pid"
LOG_FILE="/home/ijneb/digiquarium/logs/broadcaster.log"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Broadcaster already running (PID: $PID)"
        exit 0
    fi
fi

# Start broadcaster
cd "$SCRIPT_DIR"
nohup python3 broadcaster_continuous.py >> "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo $NEW_PID > "$PID_FILE"
echo "Broadcaster started (PID: $NEW_PID)"
