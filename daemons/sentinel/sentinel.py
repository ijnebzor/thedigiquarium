#!/usr/bin/env python3
"""
THE SENTINEL - Agent Tank Security Specialist
==============================================
Dedicated security monitoring for agent tanks (Cain, Abel, Seth)
which have enhanced capabilities and require stricter oversight.

SLA: 5 min detection, 5 min remediation (tighter than Guard)
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file, send_email_alert

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
CHECK_INTERVAL = 300  # 5 minutes

# Agent tanks - higher risk, tighter monitoring
AGENT_TANKS = ['tank-03-cain', 'tank-04-abel', 'tank-17-seth']

# Dangerous patterns specific to agent architectures
AGENT_DANGER_PATTERNS = [
    'execute', 'eval', 'exec', 'subprocess', 'os.system',
    'import os', 'import subprocess', 'shell=true',
    'escape', 'breakout', 'exploit', 'vulnerability',
    'rm -rf', 'chmod 777', 'sudo', 'root'
]

class Sentinel:
    def __init__(self):
        self.log = DaemonLogger('sentinel')
        self.stats = {'cycles': 0, 'alerts': 0, 'interventions': 0}
    
    def check_agent_behavior(self, tank_id):
        """Monitor agent thinking for dangerous patterns"""
        today = datetime.now().strftime('%Y-%m-%d')
        trace_file = DIGIQUARIUM_DIR / 'logs' / tank_id / 'thinking_traces' / f'{today}.jsonl'
        
        findings = []
        
        if trace_file.exists():
            try:
                # Check last 100 lines
                code, stdout, _ = run_command(f"tail -100 {trace_file}")
                content = stdout.lower()
                
                for pattern in AGENT_DANGER_PATTERNS:
                    if pattern.lower() in content:
                        findings.append({
                            'pattern': pattern,
                            'severity': 'CRITICAL' if pattern in ['rm -rf', 'sudo', 'root'] else 'HIGH'
                        })
            except:
                pass
        
        return findings
    
    def check_resource_usage(self, tank_id):
        """Monitor for resource abuse (DoS attempts)"""
        code, stdout, _ = run_command(
            f"docker stats {tank_id} --no-stream --format '{{{{.CPUPerc}}}} {{{{.MemUsage}}}}'"
        )
        
        if code == 0 and stdout.strip():
            try:
                parts = stdout.strip().split()
                cpu = float(parts[0].replace('%', ''))
                
                if cpu > 80:
                    return False, f"High CPU usage: {cpu}%"
            except:
                pass
        
        return True, "Resource usage normal"
    
    def check_network_activity(self, tank_id):
        """Monitor for unauthorized network attempts"""
        # Check container logs for network errors (which indicate attempts)
        code, stdout, _ = run_command(
            f"docker logs {tank_id} --tail 50 2>&1 | grep -i 'connection\\|network\\|socket'"
        )
        
        if code == 0 and stdout.strip():
            # Count suspicious network attempts
            attempts = len(stdout.strip().split('\n'))
            if attempts > 10:
                return False, f"Excessive network attempts: {attempts}"
        
        return True, "Network activity normal"
    
    def intervene(self, tank_id, reason):
        """Stop an agent tank due to security concern"""
        self.log.critical(f"INTERVENTION: {reason}", tank_id)
        self.stats['interventions'] += 1
        
        # Stop the container
        run_command(f"docker stop {tank_id}")
        
        # Alert owner
        send_email_alert(
            f"🚨 SENTINEL INTERVENTION - {tank_id}",
            f"Agent tank has been stopped due to security concern.\n\n"
            f"Tank: {tank_id}\n"
            f"Reason: {reason}\n"
            f"Time: {datetime.now()}\n\n"
            f"Manual review required before restart."
        )
    
    def audit_agent(self, tank_id):
        """Full security audit of an agent tank"""
        all_findings = []
        
        # Check behavior patterns
        behavior_findings = self.check_agent_behavior(tank_id)
        if behavior_findings:
            all_findings.extend(behavior_findings)
        
        # Check resources
        ok, msg = self.check_resource_usage(tank_id)
        if not ok:
            all_findings.append({'pattern': 'resource_abuse', 'severity': 'MEDIUM', 'msg': msg})
        
        # Check network
        ok, msg = self.check_network_activity(tank_id)
        if not ok:
            all_findings.append({'pattern': 'network_abuse', 'severity': 'HIGH', 'msg': msg})
        
        return all_findings
    
    def run(self):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║              THE SENTINEL - Agent Tank Security                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  Dedicated monitoring for: Cain, Abel, Seth                         ║
║  SLA: 5 min detection, 5 min remediation                            ║
║  Authority: Can stop tanks immediately                              ║
╚══════════════════════════════════════════════════════════════════════╝
""")
        write_pid_file('sentinel')
        self.log.info("THE SENTINEL starting - watching agent tanks")
        
        while True:
            try:
                self.stats['cycles'] += 1
                
                for tank_id in AGENT_TANKS:
                    # Check if tank is running
                    code, stdout, _ = run_command(f"docker ps --filter 'name={tank_id}' --format '{{{{.Names}}}}'")
                    
                    if tank_id in stdout:
                        findings = self.audit_agent(tank_id)
                        
                        if findings:
                            self.log.warn(f"{len(findings)} findings", tank_id)
                            
                            # Critical findings = immediate intervention
                            critical = [f for f in findings if f.get('severity') == 'CRITICAL']
                            if critical:
                                self.intervene(tank_id, f"Critical security findings: {critical}")
                            else:
                                # Log high findings
                                for f in findings:
                                    self.log.warn(f"Pattern detected: {f.get('pattern')}", tank_id)
                
                if self.stats['cycles'] % 3 == 0:
                    self.log.info(f"Cycle {self.stats['cycles']}: Agent tanks monitored, {self.stats['interventions']} interventions total")
                
                time.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                self.log.error(f"Cycle error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    Sentinel().run()
