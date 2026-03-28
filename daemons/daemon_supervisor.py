#!/usr/bin/env python3
"""
DAEMON SUPERVISOR v3.1 - The ONE self-healing system
=====================================================
Run via cron every minute.

This is the SINGLE self-healing mechanism for the Digiquarium.
It replaces:
  - The maintainer's daemon-watching (maintainer keeps tank health checks only)
  - The old cron entries for specific services
  - The previous daemon_supervisor v1/v2

v3.1 Changes:
  - Ollama check now does a REAL inference test, not just container state check
  - Logs to dedicated crash log file for post-mortem analysis
  - Better diagnostics on failure (OOM check, memory state, restart count)

v3.0 Features:
  - Tracks consecutive Ollama failures with CRITICAL alert after 5 checks (5 min)
  - Auto-restarts Ollama via docker compose up -d ollama
  - Writes Ollama health status to shared/.ollama_health for scheduler to read
  - Checks all 21 continuous daemons via PID file verification
  - Monitors all 17 Docker tank containers and restarts exited ones

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
import json
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

DIGIQUARIUM_HOME = os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')
DAEMONS_DIR = Path(os.path.join(DIGIQUARIUM_HOME, 'daemons'))
LOG_FILE = DAEMONS_DIR / 'supervisor.log'
OLLAMA_HEALTH_FILE = Path(DIGIQUARIUM_HOME) / 'shared' / '.ollama_health'
OLLAMA_FAILURE_TRACKER = Path(DIGIQUARIUM_HOME) / 'shared' / '.ollama_failure_count'
OLLAMA_CRASH_LOG = Path(DIGIQUARIUM_HOME) / 'logs' / 'ollama' / 'ollama_crashes.log'

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


def log_crash(msg):
    """Write to the dedicated Ollama crash log for post-mortem analysis."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] [SUPERVISOR] {msg}"
    try:
        OLLAMA_CRASH_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(OLLAMA_CRASH_LOG, 'a') as f:
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


def read_failure_count():
    """Read the consecutive Ollama failure count from tracker file."""
    try:
        if OLLAMA_FAILURE_TRACKER.exists():
            data = json.loads(OLLAMA_FAILURE_TRACKER.read_text())
            return data.get('consecutive_failures', 0)
    except Exception:
        pass
    return 0


def write_failure_count(count):
    """Write the consecutive Ollama failure count to tracker file."""
    try:
        OLLAMA_FAILURE_TRACKER.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'consecutive_failures': count,
            'last_updated': datetime.now().isoformat()
        }
        OLLAMA_FAILURE_TRACKER.write_text(json.dumps(data, indent=2))
    except Exception as e:
        log(f"Failed to write failure tracker: {e}")


def write_ollama_health(healthy, message=""):
    """Write Ollama health status to shared file for scheduler to read."""
    try:
        OLLAMA_HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'healthy': healthy,
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'consecutive_failures': read_failure_count()
        }
        OLLAMA_HEALTH_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        log(f"Failed to write Ollama health file: {e}")


def collect_ollama_diagnostics():
    """Collect detailed diagnostics when Ollama fails."""
    diag = []
    try:
        # Memory state
        mem = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        if mem.returncode == 0:
            diag.append(f"Memory:\n{mem.stdout.strip()}")
        
        # Container state details
        inspect = subprocess.run(
            ['docker', 'inspect', '-f',
             'Status={{.State.Status}} OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}} '
             'RestartCount={{.RestartCount}} StartedAt={{.State.StartedAt}} FinishedAt={{.State.FinishedAt}}',
             'digiquarium-ollama'],
            capture_output=True, text=True, timeout=10
        )
        if inspect.returncode == 0:
            diag.append(f"Container: {inspect.stdout.strip()}")
        
        # Last few docker logs
        logs = subprocess.run(
            ['docker', 'logs', '--tail', '10', 'digiquarium-ollama'],
            capture_output=True, text=True, timeout=10
        )
        if logs.stderr:
            diag.append(f"Recent logs:\n{logs.stderr[-500:]}")
    except Exception as e:
        diag.append(f"Diagnostics error: {e}")
    
    return '\n'.join(diag)


def check_ollama_api():
    """Check if Ollama API responds to /api/tags."""
    try:
        req = urllib.request.Request('http://localhost:11434/api/tags', method='GET')
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return 'models' in data
    except Exception:
        return False


def check_ollama_inference():
    """Do a real inference test — verify Ollama can actually generate text."""
    try:
        payload = json.dumps({
            "model": "llama3.2:latest",
            "prompt": "Say OK",
            "stream": False,
            "options": {"num_predict": 5}
        }).encode('utf-8')
        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return 'response' in data and len(data['response'].strip()) > 0
    except Exception:
        return False


def check_ollama():
    """Ensure Ollama container exists, API responds, and can serve inference.
    
    Three-layer check:
    1. Docker container running?
    2. API responding to /api/tags?
    3. Can it actually generate text? (every 5th check to reduce load)
    
    Tracks consecutive failures. After 5 consecutive failures (5 minutes),
    logs a CRITICAL alert and attempts restart via docker compose.
    Writes health status to shared/.ollama_health for scheduler.
    """
    consecutive_failures = read_failure_count()
    failure_reason = None

    try:
        # Layer 1: Container running?
        result = subprocess.run(
            ['docker', 'inspect', '-f', '{{.State.Running}}', 'digiquarium-ollama'],
            capture_output=True, text=True, timeout=10
        )
        if 'true' not in result.stdout.lower():
            failure_reason = "Container not running"
        
        # Layer 2: API responding?
        if failure_reason is None and not check_ollama_api():
            failure_reason = "API not responding (container running)"
        
        # Layer 3: Inference test (every 5th minute to reduce load)
        if failure_reason is None:
            minute = datetime.now().minute
            if minute % 5 == 0:
                if not check_ollama_inference():
                    failure_reason = "Inference test failed (API responds but can't generate)"

        if failure_reason:
            consecutive_failures += 1
            write_failure_count(consecutive_failures)
            
            # Log diagnostics to crash log
            log_crash(f"FAILURE #{consecutive_failures}: {failure_reason}")
            diagnostics = collect_ollama_diagnostics()
            log_crash(f"Diagnostics:\n{diagnostics}")

            if consecutive_failures >= 5:
                log(f'CRITICAL: Ollama has been down for {consecutive_failures} consecutive checks ({consecutive_failures} minutes)!')
                log(f'CRITICAL: Reason: {failure_reason}')
                log('CRITICAL: Attempting emergency restart via docker compose up -d ollama')
                log_crash(f'CRITICAL: Emergency restart after {consecutive_failures} failures')
                restart_result = subprocess.run(
                    f'cd {DIGIQUARIUM_HOME} && docker compose up -d ollama',
                    shell=True, capture_output=True, text=True, timeout=120
                )
                if restart_result.returncode == 0:
                    log('Ollama restart initiated after CRITICAL threshold')
                    log_crash('Restart initiated via docker compose')
                else:
                    log(f'CRITICAL: Ollama restart FAILED: {restart_result.stderr[:200]}')
                    log_crash(f'RESTART FAILED: {restart_result.stderr[:200]}')
            else:
                log(f'WARNING: Ollama check failed (failure {consecutive_failures}/5 before CRITICAL): {failure_reason}')
                # Still try to restart
                subprocess.run(
                    f'cd {DIGIQUARIUM_HOME} && docker compose up -d ollama',
                    shell=True, capture_output=True, timeout=120
                )
                log('Ollama restart initiated')
                log_crash('Restart initiated (pre-CRITICAL)')

            write_ollama_health(False, f'{failure_reason} ({consecutive_failures} consecutive failures)')
            return False
        else:
            # All checks passed — reset failure counter
            if consecutive_failures > 0:
                log(f'Ollama recovered after {consecutive_failures} consecutive failures')
                log_crash(f'RECOVERED after {consecutive_failures} failures')
            write_failure_count(0)
            write_ollama_health(True, 'Ollama running - all checks passed')
            return True
    except Exception as e:
        consecutive_failures += 1
        write_failure_count(consecutive_failures)
        log(f'CRITICAL: Cannot check Ollama: {e} (failure {consecutive_failures})')
        log_crash(f'CHECK EXCEPTION: {e}')

        if consecutive_failures >= 5:
            log(f'CRITICAL: Ollama unreachable for {consecutive_failures} consecutive checks — forcing restart')

        # Try to start it anyway
        subprocess.run(
            f'cd {DIGIQUARIUM_HOME} && docker compose up -d ollama',
            shell=True, capture_output=True, timeout=120
        )
        write_ollama_health(False, f'Check failed: {e}')
        return False


def main():
    log("=== DAEMON SUPERVISOR v3.1 CHECK ===")

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
