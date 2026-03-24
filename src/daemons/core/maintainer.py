#!/usr/bin/env python3
"""
THE MAINTAINER - Daemon Orchestrator
=====================================
The boss daemon. Ensures all other daemons are running.
Acts as Claude's extension for 24/7 operation.

SLA: 1 minute detection, 5 minute remediation
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

# All managed daemons
MANAGED_DAEMONS = [
    'guard', 'sentinel', 'scheduler', 
    'translator', 'documentarian', 'webmaster', 
    'ollama_watcher', 'final_auditor', 'psych'
]

class Maintainer:
    def __init__(self):
        self.log = DaemonLogger('maintainer')
        self.running = True
        self.stats = {
            'cycles': 0,
            'restarts': 0,
            'escalations': 0,
            'start_time': datetime.now().isoformat()
        }
        # Track restart failures per daemon
        self.restart_failure_counts = {daemon: 0 for daemon in MANAGED_DAEMONS}

        # Handle signals
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
    
    def shutdown(self, signum, frame):
        self.log.info(f"Received signal {signum}, shutting down gracefully")
        self.running = False
    
    def start_daemon(self, name):
        """Start a daemon by name"""
        daemon_script = DAEMONS_DIR / name / f'{name}.py'
        if not daemon_script.exists():
            self.log.error(f"Daemon script not found: {daemon_script}", name)
            return False

        self.log.action(f"Starting daemon", name)

        # Clean up stale lock and PID files
        lock_file = DAEMONS_DIR / name / f'{name}.lock'
        pid_file = DAEMONS_DIR / name / f'{name}.pid'
        if lock_file.exists():
            try:
                lock_file.unlink()
                self.log.action(f"Cleaned up stale lock file", name)
            except:
                pass
        if pid_file.exists():
            try:
                pid_file.unlink()
                self.log.action(f"Cleaned up stale PID file", name)
            except:
                pass

        # Start in background
        log_file = DAEMONS_DIR / 'logs' / f'{name}.log'
        cmd = f"nohup python3 {daemon_script} >> {log_file} 2>&1 &"
        code, _, stderr = run_command(cmd)

        time.sleep(2)

        if is_daemon_running(name):
            self.log.success(f"Daemon started successfully", name)
            self.stats['restarts'] += 1
            self.restart_failure_counts[name] = 0  # Reset failure count on success
            return True
        else:
            self.log.error(f"Failed to start daemon: {stderr}", name)
            self.restart_failure_counts[name] += 1
            return False
    
    def check_daemon_heartbeat(self, name) -> bool:
        """
        Check if daemon has a fresh heartbeat file.
        Returns True if heartbeat exists and is recent (< 5 minutes old).
        Only applicable to daemons that write heartbeat files.
        """
        # Currently only ollama_watcher writes heartbeat files
        if name != 'ollama_watcher':
            return True  # Skip heartbeat check for other daemons

        heartbeat_file = Path('/tmp/ollama_watcher_heartbeat')
        if not heartbeat_file.exists():
            self.log.warn(f"Heartbeat file missing", name)
            return False

        try:
            data = json.loads(heartbeat_file.read_text())
            timestamp = datetime.fromisoformat(data['timestamp'])
            age_seconds = (datetime.now() - timestamp).total_seconds()

            if age_seconds > 300:  # 5 minutes
                self.log.warn(f"Heartbeat stale: {age_seconds}s old", name)
                return False

            return True
        except Exception as e:
            self.log.warn(f"Failed to read heartbeat: {e}", name)
            return False

    def kill_zombie_daemon(self, name):
        """Kill a zombie/stuck daemon process by PID."""
        pid_file = DAEMONS_DIR / name / f'{name}.pid'
        if not pid_file.exists():
            return False

        try:
            pid = int(pid_file.read_text().strip())
            # Check if process exists
            result = subprocess.run(['ps', '-p', str(pid)], capture_output=True)
            if result.returncode == 0:
                # Process exists, kill it
                self.log.action(f"Force-killing zombie process (PID {pid})", name)
                subprocess.run(['kill', '-9', str(pid)], capture_output=True)
                time.sleep(1)
                return True
        except:
            pass
        return False

    def check_daemon(self, name):
        """Check if daemon is running and healthy"""
        if not is_daemon_running(name):
            return False

        # Additional heartbeat check for daemons that support it
        if not self.check_daemon_heartbeat(name):
            self.log.warn(f"Daemon running but heartbeat is stale", name)
            return False

        return True
    
    def check_all_daemons(self):
        """Check all managed daemons"""
        status = {}
        issues = []
        
        for daemon in MANAGED_DAEMONS:
            if self.check_daemon(daemon):
                status[daemon] = 'running'
            else:
                status[daemon] = 'stopped'
                issues.append(daemon)
        
        return status, issues
    
    def remediate(self, daemon_name):
        """Attempt to fix a daemon issue with failure tracking and escalation."""
        self.log.warn(f"Daemon not running, attempting restart", daemon_name)

        # Check if daemon is a zombie process and kill it first
        self.kill_zombie_daemon(daemon_name)

        # Try to start it
        if self.start_daemon(daemon_name):
            return True

        # Track consecutive restart failures
        self.restart_failure_counts[daemon_name] += 1
        failures = self.restart_failure_counts[daemon_name]

        # Escalate after 3 consecutive failures
        if failures >= 3:
            self.escalate(daemon_name, f"Failed to restart after {failures} consecutive attempts")
            return False

        return False
    
    def escalate(self, daemon_name, reason):
        """Escalate issue to owner"""
        self.log.critical(f"ESCALATION: {reason}", daemon_name)
        self.stats['escalations'] += 1
        
        subject = f"🚨 DIGIQUARIUM ALERT: {daemon_name} failure"
        body = f"""
CRITICAL DAEMON FAILURE

Daemon: {daemon_name}
Reason: {reason}
Time: {datetime.now()}

The Maintainer was unable to automatically resolve this issue.
Manual intervention may be required.

-- THE MAINTAINER
"""
        send_email_alert(subject, body)
    
    def write_status(self):
        """Write current status to file"""
        status_file = DAEMONS_DIR / 'maintainer' / 'status.json'
        
        daemon_status, _ = self.check_all_daemons()
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'maintainer': 'running',
            'daemons': daemon_status,
            'stats': self.stats,
            'uptime_seconds': (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
        }
        
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def run(self):
        """Main loop"""
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║              THE MAINTAINER - Daemon Orchestrator                    ║
╠══════════════════════════════════════════════════════════════════════╣
║  SLA: 1 min detection, 5 min remediation                            ║
║  Managed Daemons: 9                                                  ║
║  Escalation: benjiz@gmail.com                                        ║
╚══════════════════════════════════════════════════════════════════════╝
""")
        
        write_pid_file('maintainer')
        self.log.info("THE MAINTAINER starting")
        
        while self.running:
            try:
                self.stats['cycles'] += 1
                
                # Check all daemons
                status, issues = self.check_all_daemons()
                
                # Report status
                running = sum(1 for s in status.values() if s == 'running')
                total = len(MANAGED_DAEMONS)
                
                if issues:
                    self.log.warn(f"Cycle {self.stats['cycles']}: {running}/{total} daemons OK, issues: {issues}")
                    
                    # Remediate each issue
                    for daemon in issues:
                        self.remediate(daemon)
                else:
                    if self.stats['cycles'] % 5 == 0:  # Log every 5 cycles
                        self.log.info(f"Cycle {self.stats['cycles']}: All {total} daemons healthy")
                
                # Write status file
                self.write_status()
                
                # Wait for next cycle
                time.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                self.log.error(f"Cycle error: {e}")
                time.sleep(30)
        
        self.log.info("THE MAINTAINER shutting down")

if __name__ == '__main__':
    maintainer = Maintainer()
    maintainer.run()
