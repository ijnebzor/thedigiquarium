#!/bin/bash
cd /home/ijneb/digiquarium
LOG_FILE="logs/guard/guard_daemon.log"

echo "$(date): Starting The Guard security daemon" >> "$LOG_FILE"

while true; do
    python3 guard/guard.py once >> "$LOG_FILE" 2>&1
    
    # Wait 5 minutes before next check
    sleep 300
done
