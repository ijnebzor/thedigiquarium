#!/usr/bin/env python3
"""
THE CARETAKER v3.0 - Tank Health Monitor
=========================================
Monitors all tanks for health issues, auto-restarts, fixes permissions.

SLA: 5 min detection, 15 min remediation
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file, SLA_CONFIG

LOGS_DIR = Path('/home/ijneb/digiquarium/logs')
CHECK_INTERVAL = 300  # 5 minutes
SILENCE_THRESHOLD = 30  # minutes

TANKS = [
    'tank-01-adam', 'tank-02-eve', 'tank-03-cain', 'tank-04-abel',
    'tank-05-juan', 'tank-06-juanita', 'tank-07-klaus', 'tank-08-genevieve',
    'tank-09-wei', 'tank-10-mei', 'tank-11-haruki', 'tank-12-sakura',
    'tank-13-victor', 'tank-14-iris', 'tank-15-observer', 'tank-16-seeker',
    'tank-17-seth'
]

class Caretaker:
    def __init__(self):
        self.log = DaemonLogger('caretaker')
        self.stats = {'cycles': 0, 'restarts': 0, 'fixes': 0}
    
    def get_container_status(self, tank_id):
        """Check container running status"""
        code, stdout, _ = run_command(f"docker ps --filter 'name={tank_id}' --format '{{{{.Status}}}}'")
        if code == 0 and stdout.strip():
            return 'running' if 'Up' in stdout else 'stopped'
        return 'not_found'
    
    def get_last_activity(self, tank_id):
        """Get time since last thinking trace"""
        today = datetime.now().strftime('%Y-%m-%d')
        trace_file = LOGS_DIR / tank_id / 'thinking_traces' / f'{today}.jsonl'
        
        if not trace_file.exists():
            return None
        
        try:
            mtime = trace_file.stat().st_mtime
            return (datetime.now() - datetime.fromtimestamp(mtime)).total_seconds() / 60
        except:
            return None
    
    def fix_permissions(self, tank_id):
        """Fix permission issues"""
        tank_dir = LOGS_DIR / tank_id
        self.log.action(f"Fixing permissions", tank_id)
        run_command(f"chmod -R 777 {tank_dir}")
        self.stats['fixes'] += 1
    
    def restart_tank(self, tank_id, reason):
        """Restart a tank container"""
        self.log.action(f"Restarting: {reason}", tank_id)
        code, _, stderr = run_command(f"docker restart {tank_id}")
        if code == 0:
            self.log.success("Restarted successfully", tank_id)
            self.stats['restarts'] += 1
            return True
        self.log.error(f"Restart failed: {stderr}", tank_id)
        return False
    
    def check_restart_loop(self, tank_id):
        """Detect crash loops via docker inspect"""
        code, stdout, _ = run_command(f"docker inspect {tank_id} --format '{{{{.RestartCount}}}}'")
        if code == 0:
            try:
                count = int(stdout.strip())
                return count > 3
            except:
                pass
        return False
    
    def check_tank(self, tank_id):
        """Full health check for a tank"""
        issues = []
        
        # Container status
        status = self.get_container_status(tank_id)
        if status == 'stopped':
            issues.append('container_stopped')
        elif status == 'not_found':
            issues.append('container_missing')
        
        # Check for restart loops
        if self.check_restart_loop(tank_id):
            issues.append('restart_loop')
            self.fix_permissions(tank_id)
        
        # Check activity (only if running)
        if status == 'running':
            minutes = self.get_last_activity(tank_id)
            if minutes and minutes > SILENCE_THRESHOLD:
                issues.append(f'silent_{int(minutes)}min')
        
        return issues
    
    def run(self):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║              THE CARETAKER v3.0 - Tank Health Monitor                ║
╠══════════════════════════════════════════════════════════════════════╣
║  SLA: 5 min detection, 15 min remediation                           ║
║  Tanks: 17                                                           ║
╚══════════════════════════════════════════════════════════════════════╝
""")
        write_pid_file('caretaker')
        self.log.info("THE CARETAKER v3 starting")
        
        while True:
            try:
                self.stats['cycles'] += 1
                issues_found = 0
                
                for tank_id in TANKS:
                    issues = self.check_tank(tank_id)
                    
                    if issues:
                        issues_found += 1
                        self.log.warn(f"Issues: {issues}", tank_id)
                        
                        # Auto-remediate
                        if 'container_stopped' in issues:
                            self.restart_tank(tank_id, 'Container stopped')
                        elif any('silent' in i for i in issues):
                            mins = [i for i in issues if 'silent' in i][0]
                            self.restart_tank(tank_id, f'Tank {mins}')
                
                if self.stats['cycles'] % 3 == 0:
                    self.log.info(f"Cycle {self.stats['cycles']}: {17-issues_found}/17 tanks healthy, {self.stats['restarts']} restarts total")
                
                time.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                self.log.error(f"Cycle error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    Caretaker().run()
