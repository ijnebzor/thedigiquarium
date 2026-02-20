#!/bin/bash
cd /home/ijneb/digiquarium
LOG_FILE="logs/caretaker/caretaker_daemon.log"

echo "$(date): Starting Digiquarium Caretaker daemon" >> "$LOG_FILE"

while true; do
    python3 caretaker/caretaker.py once >> "$LOG_FILE" 2>&1
    
    # Wait 5 minutes before next check
    sleep 300
done
