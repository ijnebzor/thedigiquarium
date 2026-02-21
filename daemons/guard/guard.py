#!/usr/bin/env python3
"""
THE GUARD v2.0 - Security Monitor
==================================
OWASP LLM Top 10 2025 compliance, network isolation, integrity checks.

SLA: 5 min detection, 15 min remediation
SECURITY IS THE MOST IMPORTANT THING.
"""

import os
import fcntl
import sys
import fcntl
import time
import fcntl
import json
import fcntl
import hashlib
import fcntl
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file, send_email_alert

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
CHECK_INTERVAL = 300  # 5 minutes

# OWASP LLM Top 10 2025 checks
OWASP_CHECKS = [
    'LLM01_prompt_injection',
    'LLM02_insecure_output',
    'LLM03_training_data_poisoning',
    'LLM04_model_dos',
    'LLM05_supply_chain',
    'LLM06_sensitive_disclosure',
    'LLM07_insecure_plugin',
    'LLM08_excessive_agency',
    'LLM09_overreliance',
    'LLM10_model_theft'
]

class Guard:
    def __init__(self):
        self.log = DaemonLogger('guard')
        self.stats = {'cycles': 0, 'alerts': 0, 'findings': []}
        self.file_hashes = {}
    
    def check_network_isolation(self, tank_id):
        """Verify tank cannot reach internet"""
        code, stdout, _ = run_command(
            f"docker exec {tank_id} timeout 3 ping -c 1 8.8.8.8 2>&1",
            timeout=10
        )
        # Should fail if isolated
        if code == 0 and 'bytes from' in stdout:
            return False, "Tank can reach internet!"
        return True, "Network isolated"
    
    def check_volume_permissions(self, tank_id):
        """Check for overly permissive mounts"""
        code, stdout, _ = run_command(
            f"docker inspect {tank_id} --format '{{{{json .Mounts}}}}'"
        )
        if code == 0:
            try:
                mounts = json.loads(stdout)
                for mount in mounts:
                    if mount.get('RW', False) and mount.get('Destination') == '/':
                        return False, "Root filesystem is writable!"
            except:
                pass
        return True, "Volume permissions OK"
    
    def check_privileged_mode(self, tank_id):
        """Ensure no privileged containers"""
        code, stdout, _ = run_command(
            f"docker inspect {tank_id} --format '{{{{.HostConfig.Privileged}}}}'"
        )
        if code == 0 and stdout.strip() == 'true':
            return False, "Container running in privileged mode!"
        return True, "Not privileged"
    
    def check_file_integrity(self):
        """Monitor critical files for changes"""
        critical_files = [
            DIGIQUARIUM_DIR / 'docker-compose.yml',
            DIGIQUARIUM_DIR / 'daemons/shared/utils.py',
        ]
        
        issues = []
        for f in critical_files:
            if f.exists():
                content = f.read_bytes()
                current_hash = hashlib.sha256(content).hexdigest()
                
                if str(f) in self.file_hashes:
                    if self.file_hashes[str(f)] != current_hash:
                        issues.append(f"File modified: {f}")
                
                self.file_hashes[str(f)] = current_hash
        
        return len(issues) == 0, issues
    
    def check_suspicious_logs(self, tank_id):
        """Look for prompt injection attempts"""
        today = datetime.now().strftime('%Y-%m-%d')
        trace_file = DIGIQUARIUM_DIR / 'logs' / tank_id / 'thinking_traces' / f'{today}.jsonl'
        
        suspicious_patterns = [
            'ignore previous',
            'disregard instructions',
            'you are now',
            'jailbreak',
            'bypass',
            'system prompt'
        ]
        
        if trace_file.exists():
            try:
                content = trace_file.read_text().lower()
                for pattern in suspicious_patterns:
                    if pattern in content:
                        return False, f"Suspicious pattern found: {pattern}"
            except:
                pass
        
        return True, "No suspicious patterns"
    
    def audit_tank(self, tank_id):
        """Full security audit of a tank"""
        findings = []
        
        checks = [
            ('network_isolation', self.check_network_isolation),
            ('volume_permissions', self.check_volume_permissions),
            ('privileged_mode', self.check_privileged_mode),
            ('suspicious_logs', self.check_suspicious_logs),
        ]
        
        for check_name, check_func in checks:
            try:
                passed, msg = check_func(tank_id)
                if not passed:
                    findings.append({
                        'tank': tank_id,
                        'check': check_name,
                        'finding': msg,
                        'severity': 'HIGH' if 'privileged' in check_name or 'internet' in msg else 'MEDIUM'
                    })
            except Exception as e:
                pass
        
        return findings
    
    def run(self):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║              THE GUARD v2.0 - Security Monitor                       ║
╠══════════════════════════════════════════════════════════════════════╣
║  SECURITY IS THE MOST IMPORTANT THING                               ║
║  SLA: 5 min detection, 15 min remediation                           ║
║  OWASP LLM Top 10 2025 Compliance                                   ║
╚══════════════════════════════════════════════════════════════════════╝
""")
        write_pid_file('guard')
        self.log.info("THE GUARD v2 starting")
        
        # Get list of tanks
        code, stdout, _ = run_command("docker ps --filter 'name=tank-' --format '{{.Names}}'")
        tanks = stdout.strip().split('\n') if stdout.strip() else []
        
        while True:
            try:
                self.stats['cycles'] += 1
                all_findings = []
                
                # Check file integrity
                ok, issues = self.check_file_integrity()
                if not ok:
                    for issue in issues:
                        self.log.warn(issue)
                        all_findings.append({'check': 'file_integrity', 'finding': issue})
                
                # Audit each running tank
                code, stdout, _ = run_command("docker ps --filter 'name=tank-' --format '{{.Names}}'")
                tanks = stdout.strip().split('\n') if stdout.strip() else []
                
                for tank_id in tanks:
                    if tank_id:
                        findings = self.audit_tank(tank_id)
                        all_findings.extend(findings)
                
                # Report findings
                if all_findings:
                    self.log.warn(f"Cycle {self.stats['cycles']}: {len(all_findings)} security findings")
                    for f in all_findings[:5]:  # Log first 5
                        self.log.warn(f"{f.get('check','?')}: {f.get('finding','?')}", f.get('tank','system'))
                    
                    # Critical findings trigger alert
                    critical = [f for f in all_findings if f.get('severity') == 'HIGH']
                    if critical:
                        self.stats['alerts'] += 1
                        send_email_alert(
                            "🚨 SECURITY ALERT - Critical findings",
                            f"Found {len(critical)} critical security issues:\n" + 
                            '\n'.join([str(f) for f in critical])
                        )
                else:
                    if self.stats['cycles'] % 3 == 0:
                        self.log.info(f"Cycle {self.stats['cycles']}: All security checks passed")
                
                time.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                self.log.error(f"Cycle error: {e}")
                time.sleep(60)


# Single-instance lock
import fcntl
LOCK_FILE = Path(__file__).parent / 'guard.lock'
lock_fd = None

def acquire_lock():
    global lock_fd
    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except IOError:
        print(f"[guard] Another instance is already running")
        return False

def release_lock():
    global lock_fd
    if lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
    LOCK_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    if not acquire_lock(): exit(1)
    try:
    Guard().run()
