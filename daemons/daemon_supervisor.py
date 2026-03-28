#!/usr/bin/env python3
"""
DAEMON SUPERVISOR v2.0 - The ONE self-healing system
=====================================================
Run via cron every minute.

This is the SINGLE self-healing mechanism for the Digiquarium.
It replaces:
  - The maintainer's daemon-watching (maintainer keeps tank health checks only)
  - The old cron entries for specific services
  - The previous daemon_supervisor v1

Features:
  - Checks all 21 continuous daemons via PID file verification
  - Verifies PIDs actually exist in /proc (not just pgrep substring matching)
  - Monitors all 17 Docker tank containers and restarts exited ones
  - Logs all actions to supervisor.log

MIGRATION NOTE (Issue #3):
Uses compatibility wrappers in daemons/ that import from src/daemons/.
Daemon structure:
  - core/: overseer, maintainer, ollama_watcher, scheduler, caretaker
  - security/: guard, sentinel, bouncer
  - research/: documentarian, translator, archivist, final_auditor
  - ethics/: psych, therapist, ethicist, moderator
  - infra/: webmaster, broadcaster, chaos_monkey, marketer, public_liaison
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

DIGIQUARIUM_HOME = os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')
DAEMONS_DIR = Path(os.path.join(DIGIQUARIUM_HOME, 'daemons'))
LOG_FILE = DAEMONS_DIR / 'supervisor.log'

# All 21 continuous daemons that MUST be running
# Each uses its wrapper script at daemons/<name>/<name>.py
CONTINUOUS_DAEMONS = [
    # core
    'overseer',
    'maintainer',
    'ollama_watcher',
    'scheduler',
    'caretaker',
    # security
    'guard',
    'sentinel',
    'bouncer',
    # research
    'documentarian',
    'translator',
    'archivist',
    'final_auditor',
    # ethics
    'psych',
    'therapist',
    'ethicist',
    'moderator',
    # infra
    'webmaster',
    'broadcaster',
    'chaos_monkey',
    'marketer',
    'public_liaison',
]

# All 17 tank containers
TANK_CONTAINERS = [f'tank-{i:02d}' for i in range(1, 18)]


def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + '\n')
    except Exception:
        pass


def pid_exists(pid):
    """Check if a PID actually exists by checking /proc/<pid>."""
    try:
        # os.kill with signal 0 checks existence without sending a signal
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        # ProcessLookupError = no such process
        # PermissionError = process exists but we can't signal it (still alive)
        return pid > 0 and os.path.exists(f'/proc/{pid}')
    except (OSError, ValueError):
        return False


def is_daemon_running(daemon_name):
    """Check if daemon is running by reading its PID file and verifying the PID exists.
    
    Checks multiple possible PID file locations:
    1. daemons/<name>/<name>.pid  (standard location)
    2. daemons/<name>.pid  (some daemons write here)
    """
    pid_paths = [
        DAEMONS_DIR / daemon_name / f'{daemon_name}.pid',
        DAEMONS_DIR / f'{daemon_name}.pid',
    ]
    
    for pid_path in pid_paths:
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text().strip())
                if pid > 0 and pid_exists(pid):
                    return True
            except (ValueError, IOError):
                continue
    
    return False


def start_daemon(name):
    """Start a daemon using its wrapper script in daemons/<name>/<name>.py"""
    script = DAEMONS_DIR / name / f'{name}.py'

    if not script.exists():
        log(f"WARNING: {name} script not found at {script}")
        return False

    log_path = DAEMONS_DIR / 'logs' / f'{name}.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Clean up stale lock and PID files
    for ext in ['lock', 'pid']:
        stale = DAEMONS_DIR / name / f'{name}.{ext}'
        if stale.exists():
            try:
                stale.unlink()
            except Exception:
                pass

    try:
        proc = subprocess.Popen(
            ['python3', str(script)],
            stdout=open(log_path, 'a'),
            stderr=subprocess.STDOUT,
            cwd=str(script.parent),
            start_new_session=True
        )

        # Write PID file
        pid_path = DAEMONS_DIR / name / f'{name}.pid'
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.write_text(str(proc.pid))

        log(f"Started {name} (PID {proc.pid})")
        return True
    except Exception as e:
        log(f"Failed to start {name}: {e}")
        return False


def get_container_full_name(prefix):
    """Get the full container name matching a prefix (e.g. tank-01 -> tank-01-adam)."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--format', '{{.Names}}', '--filter', f'name={prefix}'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            # Return first matching container
            for name in result.stdout.strip().split('\n'):
                if name.startswith(prefix):
                    return name
    except Exception:
        pass
    return None


def check_and_restart_containers():
    """Check all 17 tank containers, restart any that exited."""
    restarted = 0
    
    for tank_prefix in TANK_CONTAINERS:
        full_name = get_container_full_name(tank_prefix)
        if not full_name:
            log(f"WARNING: No container found for {tank_prefix}")
            continue

        try:
            result = subprocess.run(
                ['docker', 'inspect', '-f', '{{.State.Running}}', full_name],
                capture_output=True, text=True, timeout=10
            )
            is_running = result.returncode == 0 and 'true' in result.stdout.lower()

            if not is_running:
                log(f"Container {full_name} is not running - restarting...")
                restart_result = subprocess.run(
                    ['docker', 'restart', full_name],
                    capture_output=True, text=True, timeout=120
                )
                if restart_result.returncode == 0:
                    log(f"Container {full_name} restarted successfully")
                    restarted += 1
                else:
                    log(f"Failed to restart {full_name}: {restart_result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            log(f"Timeout checking container {full_name}")
        except Exception as e:
            log(f"Error checking container {full_name}: {e}")

    return restarted


def check_ollama():
    """Ensure Ollama container exists and is healthy. Restart via compose if needed."""
    try:
        result = subprocess.run(
            ['docker', 'inspect', '-f', '{{.State.Running}}', 'digiquarium-ollama'],
            capture_output=True, text=True, timeout=10
        )
        if 'true' not in result.stdout.lower():
            log('CRITICAL: Ollama is down — restarting via docker compose')
            subprocess.run(
                f'cd {DIGIQUARIUM_HOME} && docker compose up -d ollama',
                shell=True, capture_output=True, timeout=120
            )
            log('Ollama restart initiated')
            return False
        return True
    except Exception as e:
        log(f'CRITICAL: Cannot check Ollama: {e}')
        # Try to start it anyway
        subprocess.run(
            f'cd {DIGIQUARIUM_HOME} && docker compose up -d ollama',
            shell=True, capture_output=True, timeout=120
        )
        return False


def main():
    log("=== DAEMON SUPERVISOR v2.0 CHECK ===")

    # Check Ollama first - critical infrastructure
    check_ollama()

    restarted_daemons = 0
    
    # 1. Check all 21 continuous daemons
    for name in CONTINUOUS_DAEMONS:
        if not is_daemon_running(name):
            log(f"{name} is not running - restarting...")
            if start_daemon(name):
                restarted_daemons += 1
            else:
                log(f"FAILED to restart {name}")

    # 2. Check all 17 Docker tank containers
    restarted_containers = check_and_restart_containers()

    # Summary
    if restarted_daemons > 0 or restarted_containers > 0:
        log(f"Restarted {restarted_daemons} daemon(s) and {restarted_containers} container(s)")
    else:
        log("All daemons and containers running")

    log("=== CHECK COMPLETE ===")


if __name__ == '__main__':
    main()
