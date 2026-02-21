#!/usr/bin/env python3
"""
THE OVERSEER v1.0 - Cross-Functional Operations Coordinator
============================================================
The daemon that sees EVERYTHING. Correlates across all systems.
Direct escalation to human operator.

Created: 2026-02-22
Trigger: 11-hour Ollama outage undetected by 11 running daemons

Responsibilities:
1. SYSTEM-WIDE CORRELATION - Sees all daemon logs simultaneously
2. PATTERN RECOGNITION - "All tanks silent" + "Ollama unhealthy" = root cause
3. SLA ENFORCEMENT - 30 min detection, 30 min remediation
4. ESCALATION - Email human after failed auto-remediation
5. INCIDENT MANAGEMENT - Track, document, learn

"We built specialists without a generalist. THE OVERSEER fixes that."
"""

import os
import sys
import json
import time
import signal
import fcntl
import smtplib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict
import urllib.request

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'

# Human operator contact
HUMAN_EMAIL = "benjiz@gmail.com"

# SLA Thresholds
SLA_DETECTION_MINUTES = 30
SLA_REMEDIATION_MINUTES = 30


class TheOverseer:
    def __init__(self):
        self.name = 'overseer'
        self.log_file = DAEMONS_DIR / 'logs' / 'overseer.log'
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.status_file = DAEMONS_DIR / 'overseer' / 'status.json'
        self.pid_file = DAEMONS_DIR / 'overseer' / 'overseer.pid'
        self.lock_file = DAEMONS_DIR / 'overseer' / 'overseer.lock'
        self.inbox_dir = DAEMONS_DIR / 'overseer' / 'inbox'
        self.alerts_dir = DAEMONS_DIR / 'overseer' / 'alerts'
        
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        
        # State tracking
        self.active_incidents = {}
        self.running = True
        self.last_full_audit = None
        self.stats = {
            'cycles': 0,
            'incidents_detected': 0,
            'incidents_resolved': 0,
            'escalations_sent': 0,
            'auto_remediations': 0,
            'start_time': datetime.now().isoformat()
        }
        
    def acquire_lock(self):
        """Ensure only one instance runs"""
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock_fd = open(self.lock_file, 'w')
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.pid_file.write_text(str(os.getpid()))
            return True
        except IOError:
            self.log('ERROR', 'Another OVERSEER instance is already running')
            return False
    
    def release_lock(self):
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            self.lock_fd.close()
            self.pid_file.unlink(missing_ok=True)
            self.lock_file.unlink(missing_ok=True)
        except:
            pass
    
    def shutdown(self, signum, frame):
        self.log('INFO', f'Received signal {signum}, shutting down gracefully')
        self.running = False
        self.save_state()
        self.release_lock()
        sys.exit(0)
    
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        icons = {
            'INFO': 'ℹ️', 'WARNING': '⚠️', 'ERROR': '❌', 
            'ACTION': '🔧', 'SUCCESS': '✅', 'CRITICAL': '🚨',
            'AUDIT': '🔍', 'ESCALATE': '📧'
        }
        icon = icons.get(level, '👁️')
        log_entry = f"{timestamp} {icon} [OVERSEER] {message}"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
        print(log_entry)
    
    # =========================================================================
    # SECTION 1: INBOX PROCESSING - Messages from other daemons
    # =========================================================================
    
    def process_inbox(self):
        """Process escalations from other daemons"""
        inbox_files = list(self.inbox_dir.glob('*.json'))
        
        for file_path in inbox_files:
            try:
                issue = json.loads(file_path.read_text())
                self.handle_escalation(issue, file_path)
            except Exception as e:
                self.log('ERROR', f'Failed to process inbox item {file_path.name}: {e}')
    
    def handle_escalation(self, issue: dict, file_path: Path):
        """Handle an escalation from another daemon"""
        sender = issue.get('from', 'unknown')
        severity = issue.get('severity', 'medium')
        message = issue.get('message', 'No message')
        timestamp = issue.get('timestamp', datetime.now().isoformat())
        
        self.log('WARNING', f'Escalation from {sender}: {message}')
        
        # Create incident if critical
        if severity == 'critical':
            incident_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.active_incidents[incident_id] = {
                'id': incident_id,
                'source': sender,
                'message': message,
                'severity': severity,
                'created': timestamp,
                'status': 'open',
                'escalated_to_human': False
            }
            self.stats['incidents_detected'] += 1
            self.log('CRITICAL', f'Incident created: {incident_id}')
            
            # Attempt auto-remediation first
            remediated = self.attempt_remediation(issue)
            
            if not remediated:
                # Escalate to human
                self.escalate_to_human(incident_id, issue)
        
        # Archive the message
        archive_path = self.alerts_dir / f"processed_{file_path.name}"
        file_path.rename(archive_path)
    
    # =========================================================================
    # SECTION 2: SYSTEM-WIDE HEALTH CHECK
    # =========================================================================
    
    def full_system_audit(self) -> dict:
        """Comprehensive system health check"""
        self.log('AUDIT', 'Starting full system audit')
        
        audit = {
            'timestamp': datetime.now().isoformat(),
            'ollama': self.check_ollama_health(),
            'containers': self.check_container_health(),
            'daemons': self.check_daemon_health(),
            'tanks': self.check_tank_health(),
            'network': self.check_network_health(),
            'issues': []
        }
        
        # Aggregate issues
        for component, health in audit.items():
            if isinstance(health, dict) and not health.get('healthy', True):
                audit['issues'].append({
                    'component': component,
                    'details': health.get('issues', [])
                })
        
        audit['overall_healthy'] = len(audit['issues']) == 0
        
        if audit['overall_healthy']:
            self.log('SUCCESS', 'Full system audit PASSED')
        else:
            self.log('WARNING', f"Full system audit found {len(audit['issues'])} issues")
            for issue in audit['issues']:
                self.log('WARNING', f"  - {issue['component']}: {issue['details']}")
        
        self.last_full_audit = audit
        return audit
    
    def check_ollama_health(self) -> dict:
        """Check Ollama at all levels"""
        result = {'healthy': True, 'issues': []}
        
        # Windows host
        try:
            req = urllib.request.Request("http://192.168.50.94:11434/api/tags")
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
                if 'models' not in data or len(data['models']) == 0:
                    result['healthy'] = False
                    result['issues'].append('Windows Ollama has no models')
        except Exception as e:
            result['healthy'] = False
            result['issues'].append(f'Windows Ollama unreachable: {e}')
        
        # Proxy container
        try:
            ps = subprocess.run(
                ['docker', 'ps', '--filter', 'name=digiquarium-ollama', '--format', '{{.Status}}'],
                capture_output=True, text=True, timeout=10
            )
            if 'Up' not in ps.stdout:
                result['healthy'] = False
                result['issues'].append('Proxy container not running')
        except Exception as e:
            result['healthy'] = False
            result['issues'].append(f'Cannot check proxy container: {e}')
        
        # End-to-end test
        try:
            e2e = subprocess.run([
                'docker', 'exec', 'tank-01-adam', 'python3', '-c',
                'import urllib.request; urllib.request.urlopen("http://digiquarium-ollama:11434/api/tags", timeout=10)'
            ], capture_output=True, timeout=30)
            if e2e.returncode != 0:
                result['healthy'] = False
                result['issues'].append('End-to-end connectivity failed')
        except Exception as e:
            result['healthy'] = False
            result['issues'].append(f'E2E test error: {e}')
        
        return result
    
    def check_container_health(self) -> dict:
        """Check all Docker containers"""
        result = {'healthy': True, 'issues': [], 'containers': {}}
        
        try:
            ps = subprocess.run(
                ['docker', 'ps', '-a', '--format', '{{.Names}}\t{{.Status}}'],
                capture_output=True, text=True, timeout=30
            )
            
            for line in ps.stdout.strip().split('\n'):
                if '\t' in line:
                    name, status = line.split('\t', 1)
                    healthy = 'Up' in status
                    result['containers'][name] = {'status': status, 'healthy': healthy}
                    
                    if not healthy and name.startswith(('tank-', 'digiquarium-')):
                        result['healthy'] = False
                        result['issues'].append(f'{name} is {status}')
        except Exception as e:
            result['healthy'] = False
            result['issues'].append(f'Cannot check containers: {e}')
        
        return result
    
    def check_daemon_health(self) -> dict:
        """Check all daemon processes"""
        result = {'healthy': True, 'issues': [], 'daemons': {}}
        
        expected_daemons = [
            'caretaker', 'maintainer', 'guard', 'sentinel', 
            'scheduler', 'ollama_watcher', 'psych'
        ]
        
        for daemon in expected_daemons:
            try:
                ps = subprocess.run(
                    ['pgrep', '-f', f'{daemon}.py'],
                    capture_output=True, text=True
                )
                count = len(ps.stdout.strip().split('\n')) if ps.stdout.strip() else 0
                
                if count == 0:
                    result['healthy'] = False
                    result['issues'].append(f'{daemon} not running')
                    result['daemons'][daemon] = {'running': False, 'count': 0}
                elif count > 1:
                    result['healthy'] = False
                    result['issues'].append(f'{daemon} has {count} instances (zombie leak)')
                    result['daemons'][daemon] = {'running': True, 'count': count, 'zombie_leak': True}
                else:
                    result['daemons'][daemon] = {'running': True, 'count': 1}
            except Exception as e:
                result['issues'].append(f'Cannot check {daemon}: {e}')
        
        return result
    
    def check_tank_health(self) -> dict:
        """Check if tanks are producing traces with actual thoughts"""
        result = {'healthy': True, 'issues': [], 'tanks': {}}
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        for i in range(1, 18):  # tanks 1-17
            tank_name = f"tank-{i:02d}"
            tank_dir = LOGS_DIR / tank_name
            trace_file = None
            
            # Find the trace file
            for subdir in tank_dir.iterdir() if tank_dir.exists() else []:
                if subdir.is_dir():
                    tf = subdir / 'thinking_traces' / f'{today}.jsonl'
                    if tf.exists():
                        trace_file = tf
                        break
            
            if not trace_file or not trace_file.exists():
                # No traces today might be okay if tank just started
                result['tanks'][tank_name] = {'traces_today': 0, 'healthy': True}
                continue
            
            # Check last 10 traces for null thoughts
            try:
                with open(trace_file, 'r') as f:
                    lines = f.readlines()[-10:]
                
                null_count = sum(1 for line in lines if '"thoughts": null' in line)
                total = len(lines)
                
                if total > 0 and null_count == total:
                    result['healthy'] = False
                    result['issues'].append(f'{tank_name}: All recent traces have null thoughts (LLM issue)')
                    result['tanks'][tank_name] = {'traces_today': total, 'null_thoughts': null_count, 'healthy': False}
                else:
                    result['tanks'][tank_name] = {'traces_today': total, 'null_thoughts': null_count, 'healthy': True}
            except Exception as e:
                result['tanks'][tank_name] = {'error': str(e), 'healthy': False}
        
        return result
    
    def check_network_health(self) -> dict:
        """Check Docker network integrity"""
        result = {'healthy': True, 'issues': []}
        
        try:
            # Check for IP conflicts
            inspect = subprocess.run(
                ['docker', 'network', 'inspect', 'digiquarium_isolated-net'],
                capture_output=True, text=True, timeout=30
            )
            
            if inspect.returncode == 0:
                data = json.loads(inspect.stdout)
                ips = defaultdict(list)
                
                for cid, info in data[0].get('Containers', {}).items():
                    ip = info.get('IPv4Address', '').split('/')[0]
                    ips[ip].append(info['Name'])
                
                for ip, names in ips.items():
                    if len(names) > 1:
                        result['healthy'] = False
                        result['issues'].append(f'IP conflict: {ip} used by {names}')
        except Exception as e:
            result['issues'].append(f'Network check failed: {e}')
        
        return result
    
    # =========================================================================
    # SECTION 3: AUTO-REMEDIATION
    # =========================================================================
    
    def attempt_remediation(self, issue: dict) -> bool:
        """Try to fix the issue automatically"""
        sender = issue.get('from', '')
        message = issue.get('message', '')
        
        self.log('ACTION', f'Attempting auto-remediation for: {message}')
        
        # Ollama proxy issues
        if 'proxy' in message.lower() or sender == 'ollama_watcher':
            return self.remediate_ollama_proxy()
        
        # Tank issues
        if 'tank' in message.lower():
            return self.remediate_tank(message)
        
        # Daemon issues
        if 'daemon' in message.lower():
            return self.remediate_daemon(message)
        
        self.log('WARNING', 'No auto-remediation available for this issue')
        return False
    
    def remediate_ollama_proxy(self) -> bool:
        """Fix Ollama proxy container"""
        self.log('ACTION', 'Remediating Ollama proxy')
        
        try:
            subprocess.run(['docker', 'rm', '-f', 'digiquarium-ollama'], 
                          capture_output=True, timeout=30)
            time.sleep(2)
            
            result = subprocess.run(
                ['docker', 'compose', 'up', '-d', 'ollama'],
                cwd=str(DIGIQUARIUM_DIR),
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                time.sleep(10)
                if self.check_ollama_health()['healthy']:
                    self.log('SUCCESS', 'Ollama proxy remediation successful')
                    self.stats['auto_remediations'] += 1
                    return True
        except Exception as e:
            self.log('ERROR', f'Ollama remediation failed: {e}')
        
        return False
    
    def remediate_tank(self, message: str) -> bool:
        """Restart a problematic tank"""
        # Extract tank name from message
        import re
        match = re.search(r'tank-\d{2}', message.lower())
        if match:
            tank_name = match.group()
            self.log('ACTION', f'Restarting {tank_name}')
            try:
                subprocess.run(['docker', 'restart', tank_name], 
                              capture_output=True, timeout=60)
                self.stats['auto_remediations'] += 1
                return True
            except:
                pass
        return False
    
    def remediate_daemon(self, message: str) -> bool:
        """Restart a daemon via systemd"""
        # This would use systemctl to restart daemons
        # For now, return False as we handle this differently
        return False
    
    # =========================================================================
    # SECTION 4: HUMAN ESCALATION
    # =========================================================================
    
    def escalate_to_human(self, incident_id: str, issue: dict):
        """Send email to human operator"""
        self.log('ESCALATE', f'Escalating {incident_id} to human operator')
        
        subject = f"🚨 DIGIQUARIUM ALERT: {issue.get('message', 'Unknown issue')[:50]}"
        
        body = f"""
DIGIQUARIUM INCIDENT ALERT
==========================

Incident ID: {incident_id}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Severity: {issue.get('severity', 'unknown').upper()}

Source: {issue.get('from', 'unknown')}
Message: {issue.get('message', 'No message')}

Auto-remediation: FAILED

This incident requires human intervention.

---
THE OVERSEER
The Digiquarium Autonomous Operations Coordinator
"""
        
        # Try to send email
        email_sent = self.send_email(subject, body)
        
        if email_sent:
            self.log('SUCCESS', f'Email sent to {HUMAN_EMAIL}')
            self.active_incidents[incident_id]['escalated_to_human'] = True
            self.stats['escalations_sent'] += 1
        else:
            self.log('ERROR', f'Failed to send email - writing to alerts directory instead')
            # Write to alerts directory as backup
            alert_file = self.alerts_dir / f'{incident_id}.txt'
            alert_file.write_text(body)
    
    def send_email(self, subject: str, body: str) -> bool:
        """Send email via local mail or SMTP"""
        try:
            # Try using local mail command first
            result = subprocess.run(
                ['mail', '-s', subject, HUMAN_EMAIL],
                input=body.encode(),
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except:
            pass
        
        # If local mail fails, write to file
        return False
    
    # =========================================================================
    # SECTION 5: STATE MANAGEMENT
    # =========================================================================
    
    def save_state(self):
        """Save current state to file"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'active_incidents': self.active_incidents,
            'stats': self.stats,
            'last_full_audit': self.last_full_audit
        }
        self.status_file.write_text(json.dumps(state, indent=2))
    
    def load_state(self):
        """Load previous state if exists"""
        if self.status_file.exists():
            try:
                state = json.loads(self.status_file.read_text())
                self.active_incidents = state.get('active_incidents', {})
                # Don't restore stats - start fresh
            except:
                pass
    
    # =========================================================================
    # SECTION 6: MAIN LOOP
    # =========================================================================
    
    def run_cycle(self):
        """Single monitoring cycle"""
        self.stats['cycles'] += 1
        
        # Process inbox
        self.process_inbox()
        
        # Full audit every 5 minutes
        if self.stats['cycles'] % 5 == 1:
            self.full_system_audit()
        
        # Quick health check every cycle
        else:
            # Just check critical systems
            ollama = self.check_ollama_health()
            if not ollama['healthy']:
                self.log('WARNING', f"Quick check: Ollama issues detected: {ollama['issues']}")
        
        self.save_state()
    
    def run(self):
        """Main daemon loop"""
        if not self.acquire_lock():
            sys.exit(1)
        
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║         THE OVERSEER v1.0 - Cross-Functional Coordinator            ║")
        print("║         'We built specialists without a generalist. I fix that.'    ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        
        self.log('INFO', 'THE OVERSEER v1.0 initialized')
        self.log('INFO', f'Human escalation: {HUMAN_EMAIL}')
        self.log('INFO', f'SLA: {SLA_DETECTION_MINUTES}min detection, {SLA_REMEDIATION_MINUTES}min remediation')
        
        self.load_state()
        
        # Initial full audit
        self.full_system_audit()
        
        check_interval = 60  # 1 minute
        
        while self.running:
            try:
                self.run_cycle()
            except Exception as e:
                self.log('ERROR', f'Monitoring cycle failed: {e}')
            
            time.sleep(check_interval)
        
        self.release_lock()


if __name__ == '__main__':
    overseer = TheOverseer()
    overseer.run()
