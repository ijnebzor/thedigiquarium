#!/usr/bin/env python3
"""
THE OLLAMA WATCHER v5.0 - LLM Infrastructure Monitor with Self-Healing
=======================================================================
Advanced monitoring with exponential backoff, circuit breakers, heartbeat files,
watchdog timer, state persistence, rate-limited escalations, and graceful shutdown.

v5.0 Features (2026-03-28):
- SLA-aware: Base cycle interval is 300s (5 min) per SLA
- SLA tracking: Writes sla_status.json each cycle
- Exponential backoff on failure only (5s base, doubles per failure, 300s max, resets on success)
- Circuit breaker pattern: 3 independent breakers (Windows, Proxy, E2E)
- Heartbeat file: Updated every cycle
- Watchdog timer: Separate thread, force-kill if main loop stuck >5 min
- State persistence: JSON file with stats

"The most reliable monitoring is monitoring that heals itself." - v5.0 Philosophy
"""

import os
import sys
import json
import time
import signal
import subprocess
import fcntl
import threading
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

DIGIQUARIUM_HOME = os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')
DIGIQUARIUM_DIR = Path(DIGIQUARIUM_HOME)
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'

OLLAMA_HOST = os.environ.get('OLLAMA_HOST', '192.168.50.94')
OLLAMA_PORT = os.environ.get('OLLAMA_PORT', '11434')
WINDOWS_HOST_OLLAMA = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

PROXY_CONTAINER = "digiquarium-ollama"
HEARTBEAT_FILE = Path('/tmp/ollama_watcher_heartbeat')
STATE_PERSISTENCE_FILE = DAEMONS_DIR / 'ollama_watcher' / 'state.json'
WATCHDOG_TIMEOUT = 300  # 5 minutes in seconds

# SLA config: 5 minute cycle
SLA_TARGET_SECONDS = 300  # 5 minutes
SLA_STATUS_FILE = DAEMONS_DIR / 'ollama_watcher' / 'sla_status.json'
BASE_CYCLE_INTERVAL = 300  # 5 minutes — the healthy-state interval per SLA


# ============================================================================
# CIRCUIT BREAKER IMPLEMENTATION
# ============================================================================

class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    States: CLOSED (ok), OPEN (broken, failing), HALF_OPEN (testing recovery)
    """
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

    def __init__(self, name, failure_threshold=10, cooldown_seconds=300):
        """
        Args:
            name: Breaker name for logging
            failure_threshold: Consecutive failures to trigger OPEN
            cooldown_seconds: Time in OPEN state before trying HALF_OPEN
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.last_success_time = None

    def record_success(self):
        """Record a successful check."""
        self.failure_count = 0
        self.last_success_time = datetime.now()
        if self.state != self.CLOSED:
            self.state = self.CLOSED

    def record_failure(self):
        """Record a failed check."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold and self.state == self.CLOSED:
            self.state = self.OPEN

    def can_attempt(self) -> bool:
        """
        Check if we should attempt the operation.
        CLOSED: always ok
        OPEN: only if cooldown expired
        HALF_OPEN: attempt recovery
        """
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
        """Serialize for persistence."""
        return {
            'name': self.name,
            'state': self.state,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialize from persistence."""
        breaker = cls(data['name'])
        breaker.state = data['state']
        breaker.failure_count = data['failure_count']
        if data['last_failure_time']:
            breaker.last_failure_time = datetime.fromisoformat(data['last_failure_time'])
        if data['last_success_time']:
            breaker.last_success_time = datetime.fromisoformat(data['last_success_time'])
        return breaker


# ============================================================================
# MAIN OLLAMA WATCHER CLASS
# ============================================================================

class OllamaWatcher:
    """
    Advanced Ollama infrastructure monitor with self-healing capabilities.
    """

    def __init__(self):
        self.name = 'ollama_watcher'
        self.log_file = DAEMONS_DIR / 'logs' / 'ollama_watcher.log'
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.pid_file = DAEMONS_DIR / 'ollama_watcher' / 'ollama_watcher.pid'
        self.lock_file = DAEMONS_DIR / 'ollama_watcher' / 'ollama_watcher.lock'
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)

        # State tracking
        self.running = True
        self.last_cycle_timestamp = datetime.now()
        self.consecutive_failures = 0
        self.restart_attempts = 0
        self.total_failures = 0
        self.total_recoveries = 0
        self.last_escalation_failure_count = 0
        self.sla_violations_count = 0

        # Exponential backoff tracking (used only during failures)
        self.current_backoff_seconds = 5
        self.base_backoff = 5
        self.max_backoff = 300

        # Circuit breakers
        self.breaker_windows = CircuitBreaker('windows_host', failure_threshold=10)
        self.breaker_proxy = CircuitBreaker('proxy_container', failure_threshold=10)
        self.breaker_e2e = CircuitBreaker('end_to_end', failure_threshold=10)

        # Load persisted state if available
        self.load_state()

        # Watchdog thread
        self.watchdog_thread = None

    def acquire_lock(self) -> bool:
        """Ensure only one instance runs."""
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock_fd = open(self.lock_file, 'w')
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.pid_file.write_text(str(os.getpid()))
            return True
        except IOError:
            self.log('ERROR', 'Another instance is already running')
            return False

    def release_lock(self):
        """Release lock on shutdown."""
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            self.lock_fd.close()
            self.pid_file.unlink(missing_ok=True)
            self.lock_file.unlink(missing_ok=True)
        except:
            pass

    def log(self, level: str, message: str):
        """Log a message with timestamp and level."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        icons = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'ACTION': '🔧',
            'SUCCESS': '✅',
            'DEBUG': '🐛'
        }
        icon = icons.get(level, 'ℹ️')
        log_entry = f"{timestamp} {icon} [OLLAMA_WATCHER v5.0] {message}"

        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
        print(log_entry)

    def write_heartbeat(self):
        """Write heartbeat file with current timestamp and status."""
        try:
            heartbeat_data = {
                'timestamp': datetime.now().isoformat(),
                'status': 'running',
                'pid': os.getpid(),
                'consecutive_failures': self.consecutive_failures,
                'total_failures': self.total_failures
            }
            HEARTBEAT_FILE.write_text(json.dumps(heartbeat_data, indent=2))
        except Exception as e:
            self.log('ERROR', f'Failed to write heartbeat: {e}')

    def write_sla_status(self, cycle_duration):
        """Write SLA compliance status to JSON file."""
        compliant = cycle_duration <= SLA_TARGET_SECONDS
        if not compliant:
            self.sla_violations_count += 1

        status = {
            'daemon': 'ollama_watcher',
            'last_check_time': datetime.now().isoformat(),
            'cycle_duration': round(cycle_duration, 2),
            'sla_target': SLA_TARGET_SECONDS,
            'compliant': compliant,
            'violations_count': self.sla_violations_count
        }
        SLA_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SLA_STATUS_FILE.write_text(json.dumps(status, indent=2))

    def save_state(self):
        """Persist state to JSON file."""
        try:
            STATE_PERSISTENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
            state = {
                'timestamp': datetime.now().isoformat(),
                'total_failures': self.total_failures,
                'total_recoveries': self.total_recoveries,
                'consecutive_failures': self.consecutive_failures,
                'restart_attempts': self.restart_attempts,
                'last_escalation_failure_count': self.last_escalation_failure_count,
                'current_backoff_seconds': self.current_backoff_seconds,
                'sla_violations_count': self.sla_violations_count,
                'circuit_breakers': {
                    'windows': self.breaker_windows.to_dict(),
                    'proxy': self.breaker_proxy.to_dict(),
                    'e2e': self.breaker_e2e.to_dict()
                }
            }
            STATE_PERSISTENCE_FILE.write_text(json.dumps(state, indent=2))
            self.log('DEBUG', 'State persisted to file')
        except Exception as e:
            self.log('ERROR', f'Failed to persist state: {e}')

    def load_state(self):
        """Load persisted state from JSON file."""
        if not STATE_PERSISTENCE_FILE.exists():
            self.log('DEBUG', 'No persisted state found, starting fresh')
            return

        try:
            with open(STATE_PERSISTENCE_FILE) as f:
                state = json.load(f)

            self.total_failures = state.get('total_failures', 0)
            self.total_recoveries = state.get('total_recoveries', 0)
            self.last_escalation_failure_count = state.get('last_escalation_failure_count', 0)
            self.current_backoff_seconds = state.get('current_backoff_seconds', 5)
            self.sla_violations_count = state.get('sla_violations_count', 0)

            # Load circuit breaker states
            if 'circuit_breakers' in state:
                breakers_data = state['circuit_breakers']
                self.breaker_windows = CircuitBreaker.from_dict(breakers_data['windows'])
                self.breaker_proxy = CircuitBreaker.from_dict(breakers_data['proxy'])
                self.breaker_e2e = CircuitBreaker.from_dict(breakers_data['e2e'])

            self.log('INFO', f'Loaded persisted state: {self.total_failures} failures, {self.total_recoveries} recoveries')
        except Exception as e:
            self.log('ERROR', f'Failed to load persisted state: {e}')

    def start_watchdog_thread(self):
        """Start a watchdog thread that monitors if main loop is stuck."""
        def watchdog_run():
            while self.running:
                time.sleep(10)  # Check every 10 seconds
                if self.running:
                    elapsed = (datetime.now() - self.last_cycle_timestamp).total_seconds()
                    if elapsed > WATCHDOG_TIMEOUT:
                        self.log('ERROR', f'Main loop stuck for {elapsed}s, force-killing process')
                        self.save_state()
                        os._exit(1)

        self.watchdog_thread = threading.Thread(target=watchdog_run, daemon=True)
        self.watchdog_thread.start()
        self.log('DEBUG', 'Watchdog thread started')

    def signal_handler(self, signum, frame):
        """Handle signals gracefully."""
        if signum == signal.SIGTERM or signum == signal.SIGINT:
            self.log('INFO', f'Received signal {signum}, shutting down gracefully')
            self.running = False
            self.save_state()
        elif signum == signal.SIGHUP:
            self.log('INFO', 'Received SIGHUP, reloading config and resetting circuit breakers')
            # Reset circuit breakers
            self.breaker_windows = CircuitBreaker('windows_host')
            self.breaker_proxy = CircuitBreaker('proxy_container')
            self.breaker_e2e = CircuitBreaker('end_to_end')
            self.consecutive_failures = 0
            self.current_backoff_seconds = self.base_backoff
            self.save_state()

    def check_windows_ollama(self) -> bool:
        """Check if Ollama on Windows host is responding."""
        if not self.breaker_windows.can_attempt():
            self.log('WARNING', f'Windows circuit breaker is {self.breaker_windows.state}, skipping check')
            return False

        try:
            req = urllib.request.Request(f"{WINDOWS_HOST_OLLAMA}/api/tags", method='GET')
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                if 'models' in data and len(data['models']) > 0:
                    self.breaker_windows.record_success()
                    return True
                else:
                    self.breaker_windows.record_failure()
                    return False
        except Exception as e:
            self.log('WARNING', f'Windows Ollama check failed: {e}')
            self.breaker_windows.record_failure()
            return False

    def check_proxy_container(self) -> bool:
        """Check if socat proxy container is running and healthy."""
        if not self.breaker_proxy.can_attempt():
            self.log('WARNING', f'Proxy circuit breaker is {self.breaker_proxy.state}, skipping check')
            return False

        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={PROXY_CONTAINER}', '--format', '{{.Status}}'],
                capture_output=True, text=True, timeout=10
            )
            if 'Up' in result.stdout:
                self.breaker_proxy.record_success()
                return True
            else:
                self.breaker_proxy.record_failure()
                return False
        except Exception as e:
            self.log('WARNING', f'Proxy container check failed: {e}')
            self.breaker_proxy.record_failure()
            return False

    def check_end_to_end(self) -> bool:
        """Check if a tank can reach Ollama through the proxy."""
        if not self.breaker_e2e.can_attempt():
            self.log('WARNING', f'E2E circuit breaker is {self.breaker_e2e.state}, skipping check')
            return False

        try:
            result = subprocess.run([
                'docker', 'exec', 'tank-01-adam', 'python3', '-c',
                '''
import urllib.request
import json
try:
    with urllib.request.urlopen("http://digiquarium-ollama:11434/api/tags", timeout=10) as r:
        data = json.loads(r.read())
        print("OK" if "models" in data else "FAIL")
except Exception as e:
    print(f"FAIL:{e}")
'''
            ], capture_output=True, text=True, timeout=30)
            if 'OK' in result.stdout:
                self.breaker_e2e.record_success()
                return True
            else:
                self.breaker_e2e.record_failure()
                return False
        except Exception as e:
            self.log('WARNING', f'End-to-end check failed: {e}')
            self.breaker_e2e.record_failure()
            return False

    def restart_proxy(self) -> bool:
        """Restart the socat proxy container."""
        self.log('ACTION', f'Restarting proxy container (attempt {self.restart_attempts + 1})')

        try:
            # Stop and remove if exists
            subprocess.run(['docker', 'rm', '-f', PROXY_CONTAINER],
                          capture_output=True, timeout=30)
            time.sleep(2)

            # Start via compose
            result = subprocess.run(
                ['docker', 'compose', 'up', '-d', 'ollama'],
                cwd=str(DIGIQUARIUM_DIR),
                capture_output=True, text=True, timeout=60
            )

            if result.returncode != 0:
                self.log('ERROR', f'Docker compose failed: {result.stderr}')
                return False

            # Wait for startup
            time.sleep(10)

            # Verify
            if self.check_end_to_end():
                self.log('SUCCESS', 'Proxy container restarted and working')
                return True
            else:
                self.log('ERROR', 'Proxy restarted but end-to-end check failed')
                return False

        except Exception as e:
            self.log('ERROR', f'Restart failed: {e}')
            return False

    def escalate_to_overseer(self, message: str):
        """Send issue to THE OVERSEER."""
        overseer_inbox = DAEMONS_DIR / 'overseer' / 'inbox'
        overseer_inbox.mkdir(parents=True, exist_ok=True)

        issue = {
            'from': self.name,
            'timestamp': datetime.now().isoformat(),
            'severity': 'critical',
            'message': message,
            'consecutive_failures': self.consecutive_failures,
            'restart_attempts': self.restart_attempts,
            'total_failures': self.total_failures,
            'circuit_breakers': {
                'windows': self.breaker_windows.to_dict(),
                'proxy': self.breaker_proxy.to_dict(),
                'e2e': self.breaker_e2e.to_dict()
            }
        }

        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.name}.json"
        (overseer_inbox / filename).write_text(json.dumps(issue, indent=2))
        self.log('WARNING', f'Escalated to OVERSEER: {message}')

    def update_status(self, windows_ok: bool, proxy_ok: bool, e2e_ok: bool):
        """Update status file."""
        status = {
            'timestamp': datetime.now().isoformat(),
            'windows_ollama_healthy': windows_ok,
            'proxy_container_healthy': proxy_ok,
            'end_to_end_healthy': e2e_ok,
            'overall_healthy': windows_ok and proxy_ok and e2e_ok,
            'consecutive_failures': self.consecutive_failures,
            'restart_attempts': self.restart_attempts,
            'total_failures': self.total_failures,
            'total_recoveries': self.total_recoveries,
            'current_backoff_seconds': self.current_backoff_seconds,
            'circuit_breakers': {
                'windows': self.breaker_windows.to_dict(),
                'proxy': self.breaker_proxy.to_dict(),
                'e2e': self.breaker_e2e.to_dict()
            }
        }

        status_file = DAEMONS_DIR / 'ollama_watcher' / 'status.json'
        status_file.parent.mkdir(parents=True, exist_ok=True)
        status_file.write_text(json.dumps(status, indent=2))

    def run_cycle(self):
        """Single monitoring cycle."""
        self.last_cycle_timestamp = datetime.now()

        # Check all three levels
        windows_ok = self.check_windows_ollama()
        proxy_ok = self.check_proxy_container()
        e2e_ok = self.check_end_to_end() if (windows_ok and proxy_ok) else False

        overall_healthy = windows_ok and proxy_ok and e2e_ok

        if overall_healthy:
            if self.consecutive_failures > 0:
                self.log('SUCCESS', f'Ollama recovered after {self.consecutive_failures} failures')
                self.total_recoveries += 1
            self.consecutive_failures = 0
            self.restart_attempts = 0
            self.current_backoff_seconds = self.base_backoff  # Reset backoff
            self.log('INFO', f'Ollama healthy (Windows: ✓, Proxy: ✓, E2E: ✓)')
        else:
            self.consecutive_failures += 1
            self.total_failures += 1

            # Exponential backoff: double the wait time per failure
            self.current_backoff_seconds = min(
                self.current_backoff_seconds * 2,
                self.max_backoff
            )

            status_str = f"Windows: {'✓' if windows_ok else '✗'}, Proxy: {'✓' if proxy_ok else '✗'}, E2E: {'✓' if e2e_ok else '✗'}"
            self.log('WARNING', f'Ollama unhealthy ({status_str}) - failure #{self.consecutive_failures}, backoff now {self.current_backoff_seconds}s')

            # Diagnose the problem
            if not windows_ok:
                self.log('ERROR', f'Windows Ollama is down (circuit: {self.breaker_windows.state}, failures: {self.breaker_windows.failure_count})')
                # Rate-limited escalation: only escalate once per 10 failures
                if self.consecutive_failures - self.last_escalation_failure_count >= 10:
                    self.escalate_to_overseer(f'Windows Ollama is down (failure #{self.consecutive_failures}). Check Windows host at {OLLAMA_HOST}')
                    self.last_escalation_failure_count = self.consecutive_failures
            elif not proxy_ok:
                self.log('ERROR', f'Proxy container unhealthy (circuit: {self.breaker_proxy.state}, failures: {self.breaker_proxy.failure_count})')
                # Proxy issue - we can fix this
                if self.consecutive_failures >= 3:  # Only attempt restart after 3 failures
                    if self.restart_attempts < 3:  # Max 3 restart attempts
                        self.restart_attempts += 1
                        if self.restart_proxy():
                            self.consecutive_failures = 0
                            self.restart_attempts = 0
                            self.current_backoff_seconds = self.base_backoff
                    else:
                        # Rate-limited escalation
                        if self.consecutive_failures - self.last_escalation_failure_count >= 10:
                            self.escalate_to_overseer(f'Proxy container unrecoverable after {3} restart attempts')
                            self.last_escalation_failure_count = self.consecutive_failures
            elif not e2e_ok:
                self.log('ERROR', f'End-to-end connectivity failed (circuit: {self.breaker_e2e.state}, failures: {self.breaker_e2e.failure_count})')
                # Network issue - rate-limited escalation
                if self.consecutive_failures - self.last_escalation_failure_count >= 10:
                    self.escalate_to_overseer(f'End-to-end connectivity failed (failure #{self.consecutive_failures}). Check Docker networking.')
                    self.last_escalation_failure_count = self.consecutive_failures

        # Update status and heartbeat
        self.update_status(windows_ok, proxy_ok, e2e_ok)
        self.write_heartbeat()

    def chunked_sleep(self, total_seconds: float):
        """
        Sleep in 1-second chunks, checking self.running flag.
        Allows responsive shutdown even during long backoff periods.
        """
        remaining = total_seconds
        while remaining > 0 and self.running:
            sleep_chunk = min(1.0, remaining)
            time.sleep(sleep_chunk)
            remaining -= sleep_chunk

    def run(self):
        """Main daemon loop."""
        # Ensure single instance
        if not self.acquire_lock():
            sys.exit(1)

        # Register signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler)

        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║   THE OLLAMA WATCHER v5.0 - SLA-Aware LLM Infrastructure Monitor    ║")
        print("║   SLA: 5 min cycle | Backoff on failure | Circuit breakers           ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")

        self.log('INFO', 'THE OLLAMA WATCHER v5.0 initialized')
        self.log('INFO', f'Windows host: {WINDOWS_HOST_OLLAMA}')
        self.log('INFO', f'Proxy container: {PROXY_CONTAINER}')
        self.log('INFO', f'SLA target: {SLA_TARGET_SECONDS}s ({SLA_TARGET_SECONDS // 60} min)')
        self.log('INFO', f'Base cycle interval: {BASE_CYCLE_INTERVAL}s')

        # Start watchdog thread
        self.start_watchdog_thread()

        while self.running:
            try:
                cycle_start = time.time()
                self.run_cycle()
                cycle_end = time.time()
                cycle_duration = cycle_end - cycle_start

                # Write SLA status
                self.write_sla_status(cycle_duration)
            except Exception as e:
                self.log('ERROR', f'Monitoring cycle failed: {e}')
                self.consecutive_failures += 1

            # Determine sleep interval:
            # - When healthy: use BASE_CYCLE_INTERVAL (300s = 5 min per SLA)
            # - When failing: use exponential backoff (shorter, for faster recovery detection)
            if self.consecutive_failures == 0:
                sleep_interval = BASE_CYCLE_INTERVAL
            else:
                sleep_interval = self.current_backoff_seconds

            self.chunked_sleep(sleep_interval)

        self.log('INFO', 'Shutting down, saving state')
        self.save_state()
        self.release_lock()
        sys.exit(0)


if __name__ == '__main__':
    watcher = OllamaWatcher()
    watcher.run()
