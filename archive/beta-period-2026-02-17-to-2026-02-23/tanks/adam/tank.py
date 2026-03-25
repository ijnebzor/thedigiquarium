#!/usr/bin/env python3
import os, time, json
from datetime import datetime

TANK_NAME = os.getenv('TANK_NAME', 'adam')
LOG_DIR = os.getenv('LOG_DIR', '/logs')

print(f"🐠 {TANK_NAME} is alive!")

log = {
    "timestamp": datetime.now().isoformat(),
    "tank_name": TANK_NAME,
    "event": "birth"
}

with open(f"{LOG_DIR}/birth.json", "w") as f:
    json.dump(log, f, indent=2)

print(f"✅ {TANK_NAME} ready!")
while True:
    time.sleep(60)
