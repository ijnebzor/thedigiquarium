#!/usr/bin/env python3
"""
THE OVERSEER v1.0 - Cross-Functional Operations Coordinator
============================================================
The daemon that sees everything and asks "why."

After the 11-hour Ollama outage incident (2026-02-21), it became clear
that specialists without a generalist fail. THE OVERSEER is that generalist.

Responsibilities:
- System-wide correlation (sees ALL daemon logs simultaneously)
- Pattern recognition ("all tanks silent" + "Ollama unhealthy" = restart Ollama)
- SLA enforcement (30 min detection, 30 min remediation)
- Escalation to human (email after 3 failed auto-remediation attempts)
- Chaos testing (monthly random service kills)

Authority:
- Can restart ANY service
- Can email human operator directly
- Can pause/resume any daemon
- Can generate incident reports
- Reports to: THE STRATEGIST (when present) / Human Operator (direct escalation)

"Detection without action is worthless." - Incident Report 2026-02-21
"""

import os
import sys
import json
import time
import subprocess
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
CONFIG_FILE = DIGIQUARIUM_DIR / 'config' / 'alerts.json'

# SLA Thresholds
SLA_DETECTION_MINUTES = 30
SLA_REMEDIATION_MINUTES = 30
AUTO_RESTART_THRESHOLD = 3
EMAIL_THRESHOLD = 3

class Overseer:
    def __init__(self):
        self.name = 'overseer'
        self.log_file = DAEMONS_DIR / 'logs' / 'overseer.log'
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.status_file = DAEMONS_DIR / 'overseer' / 'status.json'
        self.inbox = DAEMONS_DIR / 'overseer' / 'inbox'
        self.inbox.mkdir(parents=True, exist_ok=True)
        
        # Load alert configuration
        self.config = self.load_config()
        
        # Track issues
        self.active_issues = {}
        self.remediation_attempts = defaultdict(int)
        self.last_email_time = {}
        
        # Correlation state
        self.daemon_states = {}
        self.tank_states = {}
        
    def load_config(self):
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
        return {
            'human_operator': {'email': 'benjiz@gmail.com', 'name': 'Benji'},
            'alert_conditions': {}
        }
    
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        icons = {'INFO': 'ℹ️', 'WARNING': '⚠️', 'ERROR': '❌', 'ACTION': '🔧', 'ESCALATE': '🚨', 'CORRELATION': '🔗'}
        icon = icons.get(level, 'ℹ️')
        log_entry = f"{timestamp} {icon} [OVERSEER] {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        print(log_entry.strip())
    
    def run_command(self, cmd: list, timeout: int = 30) -> dict:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {'success': result.returncode == 0, 'stdout': result.stdout, 'stderr': result.stderr}
        except Exception as e:
            return {'success': False, 'stdout': '', 'stderr': str(e)}
    
    # ==================== CORRELATION ENGINE ====================
    
    def collect_daemon_states(self):
        """Read all daemon logs and status files"""
        states = {}
        
        daemon_dirs = ['caretaker', 'guard', 'sentinel', 'scheduler', 'maintainer', 
                       'ollama_watcher', 'psych', 'translator', 'webmaster', 'documentarian', 'final_auditor']
        
        for daemon in daemon_dirs:
            log_file = DAEMONS_DIR / 'logs' / f'{daemon}.log'
            status_file = DAEMONS_DIR / daemon / 'status.json'
            
            state = {'name': daemon, 'running': False, 'last_log': None, 'issues': [], 'healthy': True}
            
            # Check if process running
            result = self.run_command(['pgrep', '-f', f'{daemon}.py'])
            state['running'] = result['success']
            
            # Read last log entries
            if log_file.exists():
                try:
                    with open(log_file) as f:
                        lines = f.readlines()[-20:]  # Last 20 lines
                        state['last_log'] = lines
                        
                        # Look for issues
                        for line in lines:
                            if '❌' in line or 'ERROR' in line or 'FAIL' in line:
                                state['issues'].append(line.strip())
                            if '⚠️' in line and 'unhealthy' in line.lower():
                                state['healthy'] = False
                except:
                    pass
            
            # Read status file
            if status_file.exists():
                try:
                    state['status'] = json.loads(status_file.read_text())
                except:
                    pass
            
            states[daemon] = state
        
        return states
    
    def collect_tank_states(self):
        """Read all tank status"""
        states = {}
        
        # Get container status
        result = self.run_command(['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'])
        if result['success']:
            for line in result['stdout'].strip().split('\n'):
                if line and 'tank-' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        name = parts[0]
                        status = parts[1]
                        states[name] = {'name': name, 'running': 'Up' in status, 'status': status}
        
        # Check trace activity
        today = datetime.now().strftime('%Y-%m-%d')
        for tank_dir in LOGS_DIR.glob('tank-*'):
            tank_name = tank_dir.name
            traces_file = tank_dir / 'thinking_traces' / f'{today}.jsonl'
            
            if tank_name not in states:
                states[tank_name] = {'name': tank_name, 'running': False}
            
            if traces_file.exists():
                try:
                    with open(traces_file) as f:
                        lines = f.readlines()
                        states[tank_name]['trace_count'] = len(lines)
                        if lines:
                            last_trace = json.loads(lines[-1])
                            states[tank_name]['last_trace_time'] = last_trace.get('timestamp', '')
                except:
                    states[tank_name]['trace_count'] = 0
            else:
                states[tank_name]['trace_count'] = 0
        
        return states
    
    def check_ollama_health(self) -> bool:
        """Direct check of Ollama service"""
        result = self.run_command(['curl', '-s', '--max-time', '5', 'http://localhost:11434/api/tags'])
        return result['success'] and result['stdout'].strip()
    
    def correlate(self):
        """The brain of THE OVERSEER - pattern recognition"""
        self.daemon_states = self.collect_daemon_states()
        self.tank_states = self.collect_tank_states()
        
        issues = []
        
        # PATTERN 1: Ollama down + All tanks silent = Restart Ollama
        ollama_healthy = self.check_ollama_health()
        silent_tanks = sum(1 for t in self.tank_states.values() if t.get('trace_count', 0) == 0)
        total_tanks = len([t for t in self.tank_states if t.startswith('tank-')])
        
        if not ollama_healthy:
            issues.append({
                'type': 'ollama_down',
                'severity': 'critical',
                'message': f'Ollama is unhealthy',
                'auto_remediation': 'restart_ollama'
            })
            self.log('CORRELATION', f'Ollama unhealthy detected')
        
        if total_tanks > 0 and silent_tanks / total_tanks > 0.8:
            if not ollama_healthy:
                issues.append({
                    'type': 'all_tanks_silent_ollama',
                    'severity': 'critical',
                    'message': f'{silent_tanks}/{total_tanks} tanks silent AND Ollama unhealthy - root cause identified',
                    'auto_remediation': 'restart_ollama'
                })
                self.log('CORRELATION', f'{silent_tanks}/{total_tanks} tanks silent - correlated with Ollama failure')
            else:
                issues.append({
                    'type': 'all_tanks_silent',
                    'severity': 'high',
                    'message': f'{silent_tanks}/{total_tanks} tanks silent but Ollama healthy - investigating',
                    'auto_remediation': None
                })
        
        # PATTERN 2: Daemon not running
        for daemon, state in self.daemon_states.items():
            if not state['running']:
                issues.append({
                    'type': 'daemon_down',
                    'daemon': daemon,
                    'severity': 'high',
                    'message': f'Daemon {daemon} not running',
                    'auto_remediation': 'restart_daemon'
                })
        
        # PATTERN 3: Ollama watcher reporting failures
        if 'ollama_watcher' in self.daemon_states:
            watcher_logs = self.daemon_states['ollama_watcher'].get('last_log', [])
            failure_count = sum(1 for line in watcher_logs if 'unhealthy' in line.lower() or 'failure' in line.lower())
            if failure_count > 5:
                issues.append({
                    'type': 'ollama_watcher_failures',
                    'severity': 'high',
                    'message': f'Ollama watcher reporting {failure_count} recent failures',
                    'auto_remediation': 'restart_ollama'
                })
        
        # PATTERN 4: Caretaker restart loop
        if 'caretaker' in self.daemon_states:
            caretaker_logs = self.daemon_states['caretaker'].get('last_log', [])
            restart_count = sum(1 for line in caretaker_logs if 'Restarting' in line)
            if restart_count > 10:
                issues.append({
                    'type': 'restart_loop',
                    'severity': 'high',
                    'message': f'Caretaker in restart loop ({restart_count} restarts recently) - check upstream dependencies',
                    'auto_remediation': None
                })
                self.log('CORRELATION', f'Caretaker restart loop detected - {restart_count} restarts')
        
        return issues
    
    # ==================== AUTO-REMEDIATION ====================
    
    def restart_ollama(self):
        """Restart Ollama container"""
        self.log('ACTION', 'Auto-restarting Ollama container')
        result = self.run_command(['docker', 'restart', 'digiquarium-ollama'], timeout=60)
        
        if result['success']:
            time.sleep(10)  # Wait for startup
            if self.check_ollama_health():
                self.log('ACTION', 'Ollama restarted successfully and healthy')
                return True
        
        self.log('ERROR', f'Ollama restart failed: {result["stderr"]}')
        return False
    
    def restart_daemon(self, daemon: str):
        """Restart a daemon process"""
        self.log('ACTION', f'Auto-restarting daemon: {daemon}')
        
        daemon_script = DAEMONS_DIR / daemon / f'{daemon}.py'
        if not daemon_script.exists():
            self.log('ERROR', f'Daemon script not found: {daemon_script}')
            return False
        
        # Kill existing
        self.run_command(['pkill', '-f', f'{daemon}.py'])
        time.sleep(2)
        
        # Start new
        result = self.run_command(['nohup', 'python3', str(daemon_script), '&'])
        time.sleep(3)
        
        # Verify
        check = self.run_command(['pgrep', '-f', f'{daemon}.py'])
        if check['success']:
            self.log('ACTION', f'Daemon {daemon} restarted successfully')
            return True
        
        self.log('ERROR', f'Daemon {daemon} failed to restart')
        return False
    
    def auto_remediate(self, issue: dict) -> bool:
        """Attempt automatic remediation"""
        issue_key = f"{issue['type']}_{issue.get('daemon', '')}"
        self.remediation_attempts[issue_key] += 1
        
        if self.remediation_attempts[issue_key] > AUTO_RESTART_THRESHOLD:
            self.log('ESCALATE', f'Auto-remediation failed {AUTO_RESTART_THRESHOLD} times for {issue_key} - escalating to human')
            return False
        
        remediation = issue.get('auto_remediation')
        
        if remediation == 'restart_ollama':
            return self.restart_ollama()
        elif remediation == 'restart_daemon':
            return self.restart_daemon(issue['daemon'])
        
        return False
    
    # ==================== ESCALATION ====================
    
    def send_email(self, subject: str, body: str):
        """Send email to human operator"""
        try:
            # For now, log the email (actual sending requires SMTP config)
            email_log = DAEMONS_DIR / 'logs' / 'email_alerts.log'
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(email_log, 'a') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"TO: {self.config['human_operator']['email']}\n")
                f.write(f"TIME: {timestamp}\n")
                f.write(f"SUBJECT: {subject}\n")
                f.write(f"BODY:\n{body}\n")
                f.write(f"{'='*60}\n")
            
            self.log('ESCALATE', f'Email queued: {subject}')
            
            # TODO: Implement actual email sending via Gmail API
            # For now, this logs the alert for later pickup
            
            return True
        except Exception as e:
            self.log('ERROR', f'Failed to send email: {e}')
            return False
    
    def escalate_to_human(self, issues: list):
        """Escalate unresolved issues to human operator"""
        if not issues:
            return
        
        subject = f"🚨 DIGIQUARIUM ALERT: {len(issues)} issue(s) require attention"
        
        body = f"""
THE OVERSEER - Automated Alert
==============================
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S AEDT')}

{len(issues)} issue(s) detected that could not be auto-remediated:

"""
        for i, issue in enumerate(issues, 1):
            body += f"""
Issue {i}: {issue['type']}
Severity: {issue['severity']}
Message: {issue['message']}
Auto-remediation: {'Attempted' if issue.get('auto_remediation') else 'Not available'}
"""
        
        body += """
---
Please check the Digiquarium admin panel or connect via MCP.

The Digiquarium swims on. 🌊
- THE OVERSEER
"""
        
        self.send_email(subject, body)
    
    # ==================== INBOX PROCESSING ====================
    
    def process_inbox(self):
        """Process escalations from other daemons"""
        for inbox_file in self.inbox.glob('*.json'):
            try:
                issue = json.loads(inbox_file.read_text())
                self.log('INFO', f'Received escalation from {issue.get("from", "unknown")}: {issue.get("message", "")}')
                
                # Process based on type
                # For now, just log and archive
                archive_dir = self.inbox / 'processed'
                archive_dir.mkdir(exist_ok=True)
                inbox_file.rename(archive_dir / inbox_file.name)
                
            except Exception as e:
                self.log('ERROR', f'Failed to process inbox item {inbox_file}: {e}')
    
    # ==================== STATUS ====================
    
    def update_status(self, issues: list):
        """Update status file"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'daemon_count': len(self.daemon_states),
            'daemons_running': sum(1 for d in self.daemon_states.values() if d['running']),
            'tank_count': len(self.tank_states),
            'tanks_active': sum(1 for t in self.tank_states.values() if t.get('trace_count', 0) > 0),
            'ollama_healthy': self.check_ollama_health(),
            'active_issues': len(issues),
            'issues': [{'type': i['type'], 'severity': i['severity']} for i in issues]
        }
        
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        self.status_file.write_text(json.dumps(status, indent=2))
    
    # ==================== MAIN LOOP ====================
    
    def run_cycle(self):
        """Single oversight cycle"""
        self.log('INFO', 'Beginning oversight cycle')
        
        # Process any escalations from other daemons
        self.process_inbox()
        
        # Correlate system state
        issues = self.correlate()
        
        if issues:
            self.log('WARNING', f'Detected {len(issues)} issue(s)')
            
            unresolved = []
            for issue in issues:
                if issue.get('auto_remediation'):
                    success = self.auto_remediate(issue)
                    if not success:
                        unresolved.append(issue)
                else:
                    unresolved.append(issue)
            
            if unresolved:
                self.escalate_to_human(unresolved)
        else:
            self.log('INFO', 'All systems nominal')
            # Reset remediation counters on success
            self.remediation_attempts.clear()
        
        # Update status
        self.update_status(issues)
        
        return len(issues) == 0
    
    def run(self):
        """Main daemon loop"""
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║        THE OVERSEER v1.0 - Cross-Functional Coordinator             ║")
        print("║        'Detection without action is worthless.'                     ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        
        self.log('INFO', 'THE OVERSEER initialized')
        self.log('INFO', f'Human operator: {self.config["human_operator"]["email"]}')
        self.log('INFO', f'SLA: {SLA_DETECTION_MINUTES}min detection, {SLA_REMEDIATION_MINUTES}min remediation')
        
        check_interval = 300  # 5 minutes
        
        while True:
            try:
                self.run_cycle()
            except Exception as e:
                self.log('ERROR', f'Oversight cycle failed: {e}')
            
            time.sleep(check_interval)


def main():
    overseer = Overseer()
    overseer.run()


if __name__ == '__main__':
    main()
