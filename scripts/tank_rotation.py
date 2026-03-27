#!/usr/bin/env python3
"""Tank rotation daemon - runs groups of tanks in shifts to balance Ollama load.
With CPU-only Ollama serving llama3.2:3b, only 3-4 tanks can get reliable responses.
This script rotates which tanks are actively exploring vs paused."""

import subprocess, time, json, os, signal, sys

DIGI = os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')
GROUP_SIZE = 3  # How many tanks explore simultaneously
ROTATION_INTERVAL = 300  # Seconds per rotation (5 minutes)

# All 17 tanks in groups
GROUPS = [
    ['tank-01-adam', 'tank-02-eve', 'tank-03-cain'],           # Control + Agent
    ['tank-04-abel', 'tank-05-juan', 'tank-06-juanita'],       # Agent + Spanish
    ['tank-07-klaus', 'tank-08-genevieve', 'tank-09-wei'],     # German + Chinese
    ['tank-10-mei', 'tank-11-haruki', 'tank-12-sakura'],       # Chinese + Japanese
    ['tank-13-victor', 'tank-14-iris', 'tank-15-observer'],    # Visual + Special
    ['tank-16-seeker', 'tank-17-seth'],                         # Special + Agent
]

running = True

def signal_handler(sig, frame):
    global running
    print(f'[rotation] Received signal {sig}, shutting down...')
    running = False

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except:
        return ''

def stop_tank(tank):
    """Pause a tank's explorer by sending SIGSTOP (freeze, don't kill)."""
    # Get the PID of python3 inside the container
    pid = run(f"docker exec {tank} pgrep -f 'explorer.py|agents/' 2>/dev/null")
    if pid:
        run(f"docker exec {tank} kill -STOP {pid.split()[0]} 2>/dev/null")

def resume_tank(tank):
    """Resume a paused tank by sending SIGCONT."""
    pid = run(f"docker exec {tank} pgrep -f 'explorer.py|agents/' 2>/dev/null")
    if pid:
        run(f"docker exec {tank} kill -CONT {pid.split()[0]} 2>/dev/null")

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)

log(f'=== TANK ROTATION DAEMON ===')
log(f'Groups: {len(GROUPS)}, Size: {GROUP_SIZE}, Interval: {ROTATION_INTERVAL}s')

current_group = 0

# Pause all tanks initially
log('Pausing all tanks...')
for group in GROUPS:
    for tank in group:
        stop_tank(tank)

while running:
    # Resume current group
    active = GROUPS[current_group]
    log(f'Activating group {current_group + 1}/{len(GROUPS)}: {active}')
    
    for tank in active:
        resume_tank(tank)
    
    # Wait for rotation interval
    elapsed = 0
    while elapsed < ROTATION_INTERVAL and running:
        time.sleep(10)
        elapsed += 10
    
    # Pause current group
    for tank in active:
        stop_tank(tank)
    
    # Move to next group
    current_group = (current_group + 1) % len(GROUPS)

# On shutdown, resume all tanks
log('Resuming all tanks before exit...')
for group in GROUPS:
    for tank in group:
        resume_tank(tank)
log('=== ROTATION DAEMON STOPPED ===')
