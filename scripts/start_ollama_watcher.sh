#!/bin/bash
cd /home/ijneb/digiquarium
python3 src/daemons/core/ollama_watcher.py >> /home/ijneb/digiquarium/daemons/logs/ollama_watcher.log 2>&1 &
echo $!
