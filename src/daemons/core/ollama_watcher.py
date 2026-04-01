#!/usr/bin/env python3
"""
THE OLLAMA WATCHER v5.2 - LLM Infrastructure Monitor with Self-Healing
=======================================================================
v5.2 Fix (2026-04-01):
- Fixed watchdog killing healthy process: WATCHDOG_TIMEOUT was equal to
  BASE_CYCLE_INTERVAL (both 300s), so the watchdog force-killed the process
  during its normal healthy sleep. Now watchdog timeout = cycle + sleep + margin.
- Update last_activity_timestamp during sleep to distinguish "sleeping" from "stuck"

v5.1 Fixes (2026-04-01):
- Fixed self.log.error() crash
- Updated to check LOCAL Docker Ollama container (not external host)
- check_ollama_api() uses 'ollama list' (container has no wget/curl)
- Auto-reset corrupted state

v5.0 Features (2026-03-28):
- SLA-aware 5 min cycle, exponential backoff, circuit breakers
- Heartbeat, watchdog, state persistence, rate-limited escalations
"""

import os
import sys
import json
import time
import signal
import subprocess
import threading
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

DIGIQUARIUM_HOME = os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')
DIGIQUARIUM_DIR = Path(DIGIQUARIUM_HOME)
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'

OLLAMA_CONTAINER = "digiquarium-ollama"

HEARTBEAT_FILE = Path('/tmp/ollama_watcher_heartbeat')
STATE_PERSISTENCE_FILE = DAEMONS_DIR / 'ollama_watcher' / 'state.json'

SLA_TARGET_SECONDS = 300
SLA_STATUS_FILE = DAEMONS_DIR / 'ollama_watcher' / 'sla_status.json'
BASE_CYCLE_INTERVAL = 300  # 5 min healthy sleep

# Watchdog must be longer than cycle_duration + sleep_interval + margin
# A cycle takes ~10-30s, sleep is 300s, so 600s gives plenty of headroom
WATCHDOG_TIMEOUT = 600


# ============================================================================
# CIRCUIT BREAKER
# ============================================================================

class CircuitBreaker:
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

    def __init__(self, name, failure_threshold=10, cooldown_seconds=300):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.last_success_time = None

    def record_success(self):
        self.failure_count = 0
        self.last_success_time = datetime.now()
        if self.state != self.CLOSED:
            self.state = self.CLOSED

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold and self.state == self.CLOSED:
            self.state = self.OPEN

    def can_attempt(self) -> bool:
        if self.state == self.CLOSED:
            return True
        elif self.state == self.OPEN:
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.cooldown_seconds:
                    self.state = self.HALF_OPEN
                    return True
            return False
        elif self.state == self.HALF_OPEN:
            return True
        return False

    def to_dict(self):
        return {
            'name': self.name,
            'state': self.state,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None
        }

    @classmethod
    def from_dict(cls, data):
        breaker = cls(data['name'])
        breaker.state = data['state']
        breaker.failure_count = data['failure_count']
        if data['last_failure_time']:
            breaker.last_failure_time = datetime.fromisoformat(data['last_failure_time'])
        if data['last_success_time']:
            breaker.last_success_time = datetime.fromisoformat(data['last_success_time'])
        return breaker


# ============================================================================
# MAIN OLLAMA WATCHER
# ============================================================================

class OllamaWatcher:

    def __init__(self):
        self.name = 'ollama_watcher'
        self.log_file = DAEMONS_DIR / 'logs' / 'ollama_watcher.log'
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.pid_file = DAEMONS_DIR / 'ollama_watcher' / 'ollama_watcher.pid'
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)

        self.running = True
        # This timestamp tracks ANY activity (cycle or sleep tick) to tell the
        # watchdog the main thread is alive. Updated in run_cycle AND chunked_sleep.
        self.last_activity_timestamp = datetime.now()
        self.consecutive_failures = 0
        self.restart_attempts = 0
        self.total_failures = 0
        self.total_recoveries = 0
        self.last_escalation_failure_count = 0
        self.sla_violations_count = 0

        self.current_backoff_seconds = 5
        self.base_backoff = 5
        self.max_backoff = 300

        self.breaker_container = CircuitBreaker('ollama_container', failure_threshold=10)
        self.breaker_api = CircuitBreaker('ollama_api', failure_threshold=10)
        self.breaker_e2e = CircuitBreaker('end_to_end', failure_threshold=10)

        self.load_state()
        self.watchdog_thread = None

    def acquire_lock(self) -> bool:
        if self.pid_file.exists():
            try:
                old_pid = int(self.pid_file.read_text().strip())
                os.kill(old_pid, 0)
                self.log('ERROR', f'Another ollama_watcher is already running (PID {old_pid})')
                return False
            except (ProcessLookupError, ValueError, PermissionError):
                pass
        self.pid_file.write_text(str(os.getpid()))
        return True

    def release_lock(self):
        try:
            self.pid_file.unlink(missing_ok=True)
        except Exception:
            pass

    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        icons = {
            'INFO': 'ℹ️', 'WARNING': '⚠️', 'ERROR': '❌',
            'ACTION': '🔧', 'SUCCESS': '✅', 'DEBUG': '🐛'
        }
        icon = icons.get(level, 'ℹ️')
        log_entry = f"{timestamp} {icon} [OLLAMA_WATCHER v5.2] {message}"
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
        print(log_entry)

    def write_heartbeat(self):
        try:
            HEARTBEAT_FILE.write_text(json.dumps({
                'timestamp': datetime.now().isoformat(),
                'status': 'running',
                'pid': os.getpid(),
                'consecutive_failures': self.consecutive_failures,
                'total_failures': self.total_failures
            }, indent=2))
        except Exception as e:
            self.log('ERROR', f'Failed to write heartbeat: {e}')

    def write_sla_status(self, cycle_duration):
        compliant = cycle_duration <= SLA_TARGET_SECONDS
        if not compliant:
            self.sla_violations_count += 1
        SLA_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SLA_STATUS_FILE.write_text(json.dumps({
            'daemon': 'ollama_watcher',
            'last_check_time': datetime.now().isoformat(),
            'cycle_duration': round(cycle_duration, 2),
            'sla_target': SLA_TARGET_SECONDS,
            'compliant': compliant,
            'violations_count': self.sla_violations_count
        }, indent=2))

    def save_state(self):
        try:
            STATE_PERSISTENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATE_PERSISTENCE_FILE.write_text(json.dumps({
                'timestamp': datetime.now().isoformat(),
                'total_failures': self.total_failures,
                'total_recoveries': self.total_recoveries,
                'consecutive_failures': self.consecutive_failures,
                'restart_attempts': self.restart_attempts,
                'last_escalation_failure_count': self.last_escalation_failure_count,
                'current_backoff_seconds': self.current_backoff_seconds,
                'sla_violations_count': self.sla_violations_count,
                'circuit_breakers': {
                    'container': self.breaker_container.to_dict(),
                    'api': self.breaker_api.to_dict(),
                    'e2e': self.breaker_e2e.to_dict()
                }
            }, indent=2))
        except Exception as e:
            self.log('ERROR', f'Failed to persist state: {e}')

    def load_state(self):
        if not STATE_PERSISTENCE_FILE.exists():
            self.log('DEBUG', 'No persisted state found, starting fresh')
            return
        try:
            with open(STATE_PERSISTENCE_FILE) as f:
                state = json.load(f)

            old_failures = state.get('total_failures', 0)
            old_recoveries = state.get('total_recoveries', 0)
            if old_failures > 50 and old_recoveries == 0:
                self.log('WARNING', f'Discarding corrupted state ({old_failures} failures, 0 recoveries)')
                STATE_PERSISTENCE_FILE.unlink(missing_ok=True)
                return

            self.total_failures = state.get('total_failures', 0)
            self.total_recoveries = state.get('total_recoveries', 0)
            self.last_escalation_failure_count = state.get('last_escalation_failure_count', 0)
            self.current_backoff_seconds = state.get('current_backoff_seconds', 5)
            self.sla_violations_count = state.get('sla_violations_count', 0)

            if 'circuit_breakers' in state:
                bd = state['circuit_breakers']
                if 'container' in bd:
                    self.breaker_container = CircuitBreaker.from_dict(bd['container'])
                if 'api' in bd:
                    self.breaker_api = CircuitBreaker.from_dict(bd['api'])
                if 'e2e' in bd:
                    self.breaker_e2e = CircuitBreaker.from_dict(bd['e2e'])

            self.log('INFO', f'Loaded state: {self.total_failures} failures, {self.total_recoveries} recoveries')
        except Exception as e:
            self.log('ERROR', f'Failed to load state: {e}')

    def start_watchdog_thread(self):
        def watchdog_run():
            while self.running:
                time.sleep(30)  # Check every 30s instead of 10s
                if self.running:
                    elapsed = (datetime.now() - self.last_activity_timestamp).total_seconds()
                    if elapsed > WATCHDOG_TIMEOUT:
                        self.log('ERROR', f'Main loop stuck for {elapsed:.0f}s (timeout={WATCHDOG_TIMEOUT}s), force-killing')
                        self.save_state()
                        os._exit(1)
        self.watchdog_thread = threading.Thread(target=watchdog_run, daemon=True)
        self.watchdog_thread.start()

    def signal_handler(self, signum, frame):
        if signum in (signal.SIGTERM, signal.SIGINT):
            self.log('INFO', f'Received signal {signum}, shutting down')
            self.running = False
            self.save_state()
        elif signum == signal.SIGHUP:
            self.log('INFO', 'SIGHUP: resetting circuit breakers')
            self.breaker_container = CircuitBreaker('ollama_container')
            self.breaker_api = CircuitBreaker('ollama_api')
            self.breaker_e2e = CircuitBreaker('end_to_end')
            self.consecutive_failures = 0
            self.current_backoff_seconds = self.base_backoff
            self.save_state()

    # ---- Health checks ----

    def check_ollama_container(self) -> bool:
        if not self.breaker_container.can_attempt():
            return False
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={OLLAMA_CONTAINER}', '--format', '{{.Status}}'],
                capture_output=True, text=True, timeout=10
            )
            if 'Up' in result.stdout:
                self.breaker_container.record_success()
                return True
            self.breaker_container.record_failure()
            return False
        except Exception as e:
            self.log('WARNING', f'Container check failed: {e}')
            self.breaker_container.record_failure()
            return False

    def check_ollama_api(self) -> bool:
        if not self.breaker_api.can_attempt():
            return False
        try:
            result = subprocess.run(
                ['docker', 'exec', OLLAMA_CONTAINER, 'ollama', 'list'],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and ('NAME' in result.stdout or 'llama' in result.stdout.lower()):
                self.breaker_api.record_success()
                return True
            self.breaker_api.record_failure()
            return False
        except Exception as e:
            self.log('WARNING', f'API check failed: {e}')
            self.breaker_api.record_failure()
            return False

    def check_end_to_end(self) -> bool:
        if not self.breaker_e2e.can_attempt():
            return False
        try:
            result = subprocess.run([
                'docker', 'exec', 'tank-01-adam', 'python3', '-c',
                'import urllib.request, json\n'
                'try:\n'
                '    with urllib.request.urlopen("http://digiquarium-ollama:11434/api/tags", timeout=10) as r:\n'
                '        data = json.loads(r.read())\n'
                '        print("OK" if "models" in data else "FAIL")\n'
                'except Exception as e:\n'
                '    print(f"FAIL:{e}")\n'
            ], capture_output=True, text=True, timeout=30)
            if 'OK' in result.stdout:
                self.breaker_e2e.record_success()
                return True
            self.breaker_e2e.record_failure()
            return False
        except Exception as e:
            self.log('WARNING', f'E2E check failed: {e}')
            self.breaker_e2e.record_failure()
            return False

    def restart_ollama(self) -> bool:
        self.log('ACTION', f'Restarting Ollama container (attempt {self.restart_attempts + 1})')
        try:
            subprocess.run(['docker', 'restart', OLLAMA_CONTAINER],
                          capture_output=True, timeout=60)
            time.sleep(15)
            if self.check_ollama_api():
                self.log('SUCCESS', 'Ollama restarted and API responding')
                return True
            self.log('ERROR', 'Ollama restarted but API not yet responding')
            return False
        except Exception as e:
            self.log('ERROR', f'Restart failed: {e}')
            return False

    def escalate_to_overseer(self, message: str):
        overseer_inbox = DAEMONS_DIR / 'overseer' / 'inbox'
        overseer_inbox.mkdir(parents=True, exist_ok=True)
        issue = {
            'from': self.name,
            'timestamp': datetime.now().isoformat(),
            'severity': 'critical',
            'message': message,
            'consecutive_failures': self.consecutive_failures,
            'restart_attempts': self.restart_attempts
        }
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.name}.json"
        (overseer_inbox / filename).write_text(json.dumps(issue, indent=2))
        self.log('WARNING', f'Escalated to OVERSEER: {message}')

    def update_status(self, container_ok, api_ok, e2e_ok):
        status_file = DAEMONS_DIR / 'ollama_watcher' / 'status.json'
        status_file.parent.mkdir(parents=True, exist_ok=True)
        status_file.write_text(json.dumps({
            'timestamp': datetime.now().isoformat(),
            'ollama_container_running': container_ok,
            'ollama_api_healthy': api_ok,
            'end_to_end_healthy': e2e_ok,
            'overall_healthy': container_ok and api_ok and e2e_ok,
            'consecutive_failures': self.consecutive_failures,
            'restart_attempts': self.restart_attempts,
            'total_failures': self.total_failures,
            'total_recoveries': self.total_recoveries
        }, indent=2))

    # ---- Main loop ----

    def run_cycle(self):
        self.last_activity_timestamp = datetime.now()

        container_ok = self.check_ollama_container()
        api_ok = self.check_ollama_api() if container_ok else False
        e2e_ok = self.check_end_to_end() if (container_ok and api_ok) else False

        overall_healthy = container_ok and api_ok and e2e_ok

        if overall_healthy:
            if self.consecutive_failures > 0:
                self.log('SUCCESS', f'Ollama recovered after {self.consecutive_failures} failures')
                self.total_recoveries += 1
            self.consecutive_failures = 0
            self.restart_attempts = 0
            self.current_backoff_seconds = self.base_backoff
            self.log('INFO', 'Ollama healthy (Container: ✓, API: ✓, E2E: ✓)')
        else:
            self.consecutive_failures += 1
            self.total_failures += 1
            self.current_backoff_seconds = min(self.current_backoff_seconds * 2, self.max_backoff)

            status_str = f"Container: {'✓' if container_ok else '✗'}, API: {'✓' if api_ok else '✗'}, E2E: {'✓' if e2e_ok else '✗'}"
            self.log('WARNING', f'Unhealthy ({status_str}) - failure #{self.consecutive_failures}')

            if not container_ok:
                self.log('ERROR', 'Ollama container not running')
                if self.consecutive_failures >= 2 and self.restart_attempts < 3:
                    self.restart_attempts += 1
                    if self.restart_ollama():
                        self.consecutive_failures = 0
                        self.restart_attempts = 0
                        self.current_backoff_seconds = self.base_backoff
                elif self.restart_attempts >= 3:
                    if self.consecutive_failures - self.last_escalation_failure_count >= 10:
                        self.escalate_to_overseer('Ollama container unrecoverable after 3 restart attempts')
                        self.last_escalation_failure_count = self.consecutive_failures
            elif not api_ok:
                self.log('ERROR', 'Ollama API not responding')
                if self.consecutive_failures >= 3 and self.restart_attempts < 3:
                    self.restart_attempts += 1
                    if self.restart_ollama():
                        self.consecutive_failures = 0
                        self.restart_attempts = 0
                        self.current_backoff_seconds = self.base_backoff
                elif self.restart_attempts >= 3:
                    if self.consecutive_failures - self.last_escalation_failure_count >= 10:
                        self.escalate_to_overseer('Ollama API unresponsive after 3 restart attempts')
                        self.last_escalation_failure_count = self.consecutive_failures
            elif not e2e_ok:
                self.log('ERROR', 'E2E connectivity failed')
                if self.consecutive_failures - self.last_escalation_failure_count >= 10:
                    self.escalate_to_overseer(f'E2E failed (failure #{self.consecutive_failures})')
                    self.last_escalation_failure_count = self.consecutive_failures

        self.update_status(container_ok, api_ok, e2e_ok)
        self.write_heartbeat()

    def chunked_sleep(self, total_seconds):
        """Sleep in 1-second chunks. Updates last_activity_timestamp every 30s
        so the watchdog knows the main thread is alive (just sleeping)."""
        remaining = total_seconds
        tick = 0
        while remaining > 0 and self.running:
            time.sleep(min(1.0, remaining))
            remaining -= 1.0
            tick += 1
            if tick % 30 == 0:
                self.last_activity_timestamp = datetime.now()

    def run(self):
        if not self.acquire_lock():
            sys.exit(1)

        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler)

        self.log('INFO', 'THE OLLAMA WATCHER v5.2 initialized')
        self.log('INFO', f'Ollama container: {OLLAMA_CONTAINER}')
        self.log('INFO', f'SLA: {SLA_TARGET_SECONDS}s cycle, watchdog: {WATCHDOG_TIMEOUT}s')

        self.start_watchdog_thread()

        while self.running:
            try:
                cycle_start = time.time()
                self.run_cycle()
                self.write_sla_status(time.time() - cycle_start)
            except Exception as e:
                self.log('ERROR', f'Cycle failed: {e}')
                self.consecutive_failures += 1

            sleep_interval = BASE_CYCLE_INTERVAL if self.consecutive_failures == 0 else self.current_backoff_seconds
            self.chunked_sleep(sleep_interval)

        self.log('INFO', 'Shutting down, saving state')
        self.save_state()
        self.release_lock()
        sys.exit(0)


if __name__ == '__main__':
    watcher = OllamaWatcher()
    watcher.run()
