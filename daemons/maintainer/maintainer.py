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

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, send_email_alert, write_pid_file, read_pid_file, is_daemon_running, SLA_CONFIG

DAEMONS_DIR = Path('/home/ijneb/digiquarium/daemons')
CHECK_INTERVAL = 60  # 1 minute

# All managed daemons
MANAGED_DAEMONS = [
    'caretaker', 'guard', 'sentinel', 'scheduler', 
    'translator', 'documentarian', 'webmaster', 
    'ollama_watcher', 'final_auditor'
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
        
        # Start in background
        log_file = DAEMONS_DIR / 'logs' / f'{name}.log'
        cmd = f"nohup python3 {daemon_script} >> {log_file} 2>&1 &"
        code, _, stderr = run_command(cmd)
        
        time.sleep(2)
        
        if is_daemon_running(name):
            self.log.success(f"Daemon started successfully", name)
            self.stats['restarts'] += 1
            return True
        else:
            self.log.error(f"Failed to start daemon: {stderr}", name)
            return False
    
    def check_daemon(self, name):
        """Check if daemon is running and healthy"""
        if is_daemon_running(name):
            return True
        return False
    
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
        """Attempt to fix a daemon issue"""
        self.log.warn(f"Daemon not running, attempting restart", daemon_name)
        
        # Try to start it
        if self.start_daemon(daemon_name):
            return True
        
        # If failed, escalate
        self.escalate(daemon_name, "Failed to restart after multiple attempts")
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
