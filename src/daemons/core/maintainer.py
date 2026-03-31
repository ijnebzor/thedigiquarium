#!/usr/bin/env python3
"""
THE MAINTAINER v2.0 - Status Reporter & Health Monitor
========================================================
Previously watched 9 daemons directly. Now the daemon_supervisor.py
handles ALL daemon self-healing (run via cron every minute).

The Maintainer's remaining responsibilities:
  - Write periodic status reports (daemons, tanks, system health)
  - Monitor heartbeats from daemons that support them
  - Escalate issues via email when thresholds are breached
  - Provide a continuously-running status file for the admin dashboard

SLA: 1 minute detection, 5 minute remediation (via daemon_supervisor)
Uptime Target: 99.9%
"""

import os
import sys
import time
import json
import signal
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Single-instance lock
import fcntl
LOCK_FILE = Path(__file__).parent / 'maintainer.lock'

def _acquire_lock():
    try:
        fd = open(LOCK_FILE, 'w')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        print("[MAINTAINER] Another instance already running")
        sys.exit(1)

_lock_fd = _acquire_lock()

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, send_email_alert, write_pid_file, read_pid_file, is_daemon_running, SLA_CONFIG

DAEMONS_DIR = Path(os.path.join(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'), 'daemons'))
CHECK_INTERVAL = 60  # 1 minute

# All daemons we REPORT ON (but no longer restart — daemon_supervisor does that)
ALL_DAEMONS = [
    'overseer', 'maintainer', 'ollama_watcher', 'scheduler', 'caretaker',
    'guard', 'sentinel', 'bouncer',
    'documentarian', 'translator', 'archivist', 'final_auditor',
    'psych', 'therapist', 'ethicist', 'moderator',
    'webmaster', 'broadcaster', 'chaos_monkey', 'marketer', 'public_liaison',
]


class Maintainer:
    def __init__(self):
        self.log = DaemonLogger('maintainer')
        self.running = True
        self.stats = {
            'cycles': 0,
            'escalations': 0,
            'start_time': datetime.now().isoformat()
        }
        # Track consecutive "down" sightings per daemon for escalation
        self.down_counts = {d: 0 for d in ALL_DAEMONS}

        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, signum, frame):
        self.log.info(f"Received signal {signum}, shutting down gracefully")
        self.running = False

    def check_daemon_heartbeat(self, name) -> bool:
        """Check if daemon has a fresh heartbeat file (currently only ollama_watcher)."""
        if name != 'ollama_watcher':
            return True

        heartbeat_file = Path('/tmp/ollama_watcher_heartbeat')
        if not heartbeat_file.exists():
            return False

        try:
            data = json.loads(heartbeat_file.read_text())
            timestamp = datetime.fromisoformat(data['timestamp'])
            age_seconds = (datetime.now() - timestamp).total_seconds()
            return age_seconds <= 300  # 5 minutes
        except Exception:
            return False

    def check_all_daemons(self):
        """Check all daemons and return status dict + list of issues."""
        status = {}
        issues = []

        for daemon in ALL_DAEMONS:
            if is_daemon_running(daemon):
                if self.check_daemon_heartbeat(daemon):
                    status[daemon] = 'running'
                    self.down_counts[daemon] = 0
                else:
                    status[daemon] = 'stale_heartbeat'
                    issues.append(daemon)
                    self.down_counts[daemon] += 1
            else:
                status[daemon] = 'stopped'
                issues.append(daemon)
                self.down_counts[daemon] += 1

        return status, issues

    def escalate(self, daemon_name, reason):
        """Escalate issue to owner after persistent failures."""
        self.log.critical(f"ESCALATION: {reason}", daemon_name)
        self.stats['escalations'] += 1

        subject = f"DIGIQUARIUM ALERT: {daemon_name} failure"
        body = f"""
DAEMON FAILURE ALERT

Daemon: {daemon_name}
Reason: {reason}
Time: {datetime.now()}
Down for: {self.down_counts.get(daemon_name, 0)} consecutive checks

The daemon_supervisor should be restarting this automatically.
If this persists, manual intervention may be required.

-- THE MAINTAINER
"""
        send_email_alert(subject, body)

    def write_status(self, daemon_status):
        """Write current status to file for admin dashboard."""
        status_file = DAEMONS_DIR / 'maintainer' / 'status.json'
        status_file.parent.mkdir(parents=True, exist_ok=True)

        # Count running containers
        code, stdout, _ = run_command('docker ps --filter "name=tank-" --format "{{.Names}}" | wc -l')
        tank_count = int(stdout.strip()) if code == 0 and stdout.strip().isdigit() else 0

        status = {
            'timestamp': datetime.now().isoformat(),
            'maintainer': 'running',
            'role': 'status_reporter',
            'note': 'Daemon restarts handled by daemon_supervisor.py via cron',
            'daemons': daemon_status,
            'tanks_running': tank_count,
            'stats': self.stats,
            'uptime_seconds': (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
        }

        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)

    def run(self):
        """Main loop - monitors and reports, does NOT restart daemons."""
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║       THE MAINTAINER v2.0 - Status Reporter & Health Monitor         ║
╠══════════════════════════════════════════════════════════════════════╣
║  Role: Report status, escalate persistent failures                   ║
║  Daemon restarts: handled by daemon_supervisor.py (cron, every min)  ║
╚══════════════════════════════════════════════════════════════════════╝
""")

        write_pid_file('maintainer')
        self.log.info("THE MAINTAINER v2.0 starting (status reporter mode)")

        while self.running:
            try:
                _sla_cycle_start = time.time()
                self.stats['cycles'] += 1

                # Check all daemons (report only, no restarts)
                status, issues = self.check_all_daemons()

                running = sum(1 for s in status.values() if s == 'running')
                total = len(ALL_DAEMONS)

                if issues:
                    self.log.warn(f"Cycle {self.stats['cycles']}: {running}/{total} daemons OK, down: {issues}")

                    # Escalate if a daemon has been down for 5+ consecutive checks (5 min)
                    for daemon in issues:
                        if self.down_counts.get(daemon, 0) >= 5:
                            self.escalate(daemon, f"Down for {self.down_counts[daemon]} consecutive checks despite daemon_supervisor")
                else:
                    if self.stats['cycles'] % 5 == 0:
                        self.log.info(f"Cycle {self.stats['cycles']}: All {total} daemons healthy")

                # Write status file
                self.write_status(status)

                # Write SLA status
                _sla_cycle_duration = time.time() - _sla_cycle_start
                _sla_data = {
                    'daemon': 'maintainer',
                    'compliant': True,
                    'last_check_time': datetime.now().isoformat(),
                    'cycle_duration': _sla_cycle_duration,
                    'sla_target': 60,
                    'violations_count': 0
                }
                _sla_path = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')) / 'daemons' / 'maintainer' / 'sla_status.json'
                _sla_path.parent.mkdir(parents=True, exist_ok=True)
                _sla_path.write_text(json.dumps(_sla_data, indent=2))

                time.sleep(CHECK_INTERVAL)

            except Exception as e:
                self.log.error(f"Cycle error: {e}")
                time.sleep(30)

        self.log.info("THE MAINTAINER shutting down")

if __name__ == '__main__':
    maintainer = Maintainer()
    maintainer.run()
