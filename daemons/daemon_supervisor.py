#!/usr/bin/env python3
"""
DAEMON SUPERVISOR - Ensures all continuous daemons stay running.
Run via cron every minute.

This is the self-healing mechanism.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

DAEMONS_DIR = Path('/home/ijneb/digiquarium/daemons')
LOG_FILE = DAEMONS_DIR / 'supervisor.log'

# Continuous daemons that MUST be running
CONTINUOUS_DAEMONS = [
    'overseer',
    'maintainer',
    'ollama_watcher',
    'guard',
    'sentinel',
    'scheduler',
    'webmaster',
    'translator',
    'documentarian',
    'final_auditor',
    'psych',
    'therapist',
    'chaos_monkey',
]

# Special cases
SPECIAL_DAEMONS = {
    'caretaker': '/home/ijneb/digiquarium/caretaker/caretaker.py',
    'broadcaster': '/home/ijneb/digiquarium/daemons/webmaster/broadcaster_continuous.py',
}

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def is_running(daemon_name):
    """Check if daemon is running."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', daemon_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def start_daemon(name, script_path):
    """Start a daemon."""
    log_path = script_path.parent / f'{name}.log'
    pid_path = script_path.parent / f'{name}.pid'
    
    try:
        proc = subprocess.Popen(
            ['python3', str(script_path)],
            stdout=open(log_path, 'a'),
            stderr=subprocess.STDOUT,
            cwd=str(script_path.parent),
            start_new_session=True
        )
        
        with open(pid_path, 'w') as f:
            f.write(str(proc.pid))
        
        log(f"Started {name} (PID {proc.pid})")
        return True
    except Exception as e:
        log(f"Failed to start {name}: {e}")
        return False

def main():
    log("=== DAEMON SUPERVISOR CHECK ===")
    
    restarted = 0
    
    # Check standard daemons
    for name in CONTINUOUS_DAEMONS:
        script = DAEMONS_DIR / name / f'{name}.py'
        
        if not script.exists():
            log(f"WARNING: {name} script not found at {script}")
            continue
        
        if not is_running(name):
            log(f"{name} is not running - restarting...")
            if start_daemon(name, script):
                restarted += 1
    
    # Check special daemons
    for name, path in SPECIAL_DAEMONS.items():
        script = Path(path)
        
        if not script.exists():
            log(f"WARNING: {name} script not found at {script}")
            continue
        
        if not is_running(name):
            log(f"{name} is not running - restarting...")
            if start_daemon(name, script):
                restarted += 1
    
    if restarted > 0:
        log(f"Restarted {restarted} daemon(s)")
    else:
        log("All daemons running")
    
    log("=== CHECK COMPLETE ===")

if __name__ == '__main__':
    main()
