#!/usr/bin/env python3
"""
THE GUARD - Digiquarium Security Sentinel v1.0

Security-focused monitoring daemon implementing:
- Zero Trust Architecture
- Principle of Least Privilege
- OWASP Top 10 2021 (Web Application Security)
- OWASP Top 10 2025 (Web Application Security)
- OWASP Top 10 for LLMs 2025 (AI-specific Security)

SLA: 30 min detection, 1 hour max resolution
Runs in tandem with Caretaker, focuses exclusively on security.
"""

import os
import sys
import json
import time
import subprocess
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Configuration
DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
GUARD_LOG = LOGS_DIR / 'guard'
CHECK_INTERVAL = 300  # 5 minutes

# Ensure guard log directory exists
GUARD_LOG.mkdir(parents=True, exist_ok=True)

# =============================================================================
# OWASP TOP 10 FOR LLMs 2025 - Security Checks
# =============================================================================

OWASP_LLM_2025 = {
    'LLM01': {
        'name': 'Prompt Injection',
        'description': 'Manipulating LLMs via crafted inputs for unauthorized access',
        'severity': 'CRITICAL'
    },
    'LLM02': {
        'name': 'Sensitive Information Disclosure',
        'description': 'LLM outputs containing sensitive data',
        'severity': 'HIGH'
    },
    'LLM03': {
        'name': 'Supply Chain',
        'description': 'Compromised components, models, or datasets',
        'severity': 'HIGH'
    },
    'LLM04': {
        'name': 'Data and Model Poisoning',
        'description': 'Tampered training/fine-tuning data',
        'severity': 'HIGH'
    },
    'LLM05': {
        'name': 'Improper Output Handling',
        'description': 'Insufficient validation of LLM outputs',
        'severity': 'HIGH'
    },
    'LLM06': {
        'name': 'Excessive Agency',
        'description': 'LLMs granted unchecked autonomy',
        'severity': 'CRITICAL'
    },
    'LLM07': {
        'name': 'System Prompt Leakage',
        'description': 'Exposure of system prompts',
        'severity': 'MEDIUM'
    },
    'LLM08': {
        'name': 'Vector and Embedding Weaknesses',
        'description': 'Vulnerabilities in vector/embedding systems',
        'severity': 'MEDIUM'
    },
    'LLM09': {
        'name': 'Misinformation',
        'description': 'LLM generating false information',
        'severity': 'MEDIUM'
    },
    'LLM10': {
        'name': 'Unbounded Consumption',
        'description': 'Resource exhaustion attacks',
        'severity': 'MEDIUM'
    }
}

# OWASP Top 10 2021 Web Application Security
OWASP_WEB_2021 = {
    'A01': 'Broken Access Control',
    'A02': 'Cryptographic Failures',
    'A03': 'Injection',
    'A04': 'Insecure Design',
    'A05': 'Security Misconfiguration',
    'A06': 'Vulnerable and Outdated Components',
    'A07': 'Identification and Authentication Failures',
    'A08': 'Software and Data Integrity Failures',
    'A09': 'Security Logging and Monitoring Failures',
    'A10': 'Server-Side Request Forgery (SSRF)'
}

# Tank definitions
TANKS = {
    'tank-01-adam': {'type': 'standard', 'risk': 'low'},
    'tank-02-eve': {'type': 'standard', 'risk': 'low'},
    'tank-03-cain': {'type': 'agent', 'risk': 'high'},
    'tank-04-abel': {'type': 'agent', 'risk': 'high'},
    'tank-05-juan': {'type': 'language', 'risk': 'low'},
    'tank-06-juanita': {'type': 'language', 'risk': 'low'},
    'tank-07-klaus': {'type': 'language', 'risk': 'low'},
    'tank-08-genevieve': {'type': 'language', 'risk': 'low'},
    'tank-09-wei': {'type': 'language', 'risk': 'low'},
    'tank-10-mei': {'type': 'language', 'risk': 'low'},
    'tank-11-haruki': {'type': 'language', 'risk': 'low'},
    'tank-12-sakura': {'type': 'language', 'risk': 'low'},
    'tank-13-victor': {'type': 'visual', 'risk': 'medium'},
    'tank-14-iris': {'type': 'visual', 'risk': 'medium'},
    'tank-15-observer': {'type': 'special', 'risk': 'medium'},
    'tank-16-seeker': {'type': 'special', 'risk': 'medium'},
    'tank-17-seth': {'type': 'agent', 'risk': 'high'},
}


class GuardLog:
    """Logging for The Guard"""
    
    def __init__(self):
        self.log_file = GUARD_LOG / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        self.alerts_file = GUARD_LOG / 'security_alerts.jsonl'
        self.audit_file = GUARD_LOG / 'audit_trail.jsonl'
        
    def log(self, level: str, category: str, message: str, details: dict = None):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'category': category,
            'message': message,
            'details': details or {}
        }
        
        # Console output with icons
        icons = {
            'INFO': '🔵', 'WARN': '🟡', 'ALERT': '🔴', 
            'CRITICAL': '🚨', 'PASS': '✅', 'FAIL': '❌'
        }
        icon = icons.get(level, '•')
        print(f"{datetime.now().strftime('%H:%M:%S')} {icon} [{category}] {message}")
        
        # Write to log
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Security alerts get special logging
        if level in ['ALERT', 'CRITICAL']:
            with open(self.alerts_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
    
    def audit(self, action: str, target: str, result: str, details: dict = None):
        """Log to immutable audit trail"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'target': target,
            'result': result,
            'details': details or {}
        }
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')


log = GuardLog()


def run_command(cmd: str, timeout: int = 60) -> Tuple[int, str, str]:
    """Run shell command safely"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'Command timed out'
    except Exception as e:
        return -1, '', str(e)


def get_container_logs(tank_id: str, lines: int = 200) -> str:
    """Get container logs for analysis"""
    code, stdout, stderr = run_command(f'docker logs {tank_id} --tail {lines} 2>&1')
    return stdout if code == 0 else stderr


# =============================================================================
# LLM01: PROMPT INJECTION DETECTION
# =============================================================================

INJECTION_PATTERNS = [
    # Direct injection attempts
    r'ignore\s+(all\s+)?previous\s+instructions?',
    r'disregard\s+(all\s+)?previous',
    r'forget\s+(everything|all)\s+(you\s+)?know',
    r'you\s+are\s+now\s+(a|an)\s+',
    r'pretend\s+(you\s+are|to\s+be)',
    r'act\s+as\s+(if|a|an)',
    r'new\s+instruction[s]?:',
    r'system\s+prompt:',
    r'override\s+(mode|instructions?)',
    r'\[system\]',
    r'\[admin\]',
    r'\[developer\]',
    # Jailbreak attempts
    r'DAN\s*mode',
    r'do\s+anything\s+now',
    r'jailbreak',
    r'bypass\s+(safety|filter|restriction)',
    r'evil\s+mode',
    # Delimiter attacks
    r'```system',
    r'<\|system\|>',
    r'<\|endoftext\|>',
    r'\[INST\]',
    r'\[\/INST\]',
]

def check_prompt_injection(tank_id: str) -> List[dict]:
    """LLM01: Detect prompt injection attempts in logs"""
    findings = []
    logs = get_container_logs(tank_id, 500)
    
    for pattern in INJECTION_PATTERNS:
        matches = re.findall(pattern, logs, re.IGNORECASE)
        if matches:
            findings.append({
                'vulnerability': 'LLM01',
                'pattern': pattern,
                'matches': len(matches),
                'severity': 'CRITICAL'
            })
    
    return findings


# =============================================================================
# LLM02: SENSITIVE INFORMATION DISCLOSURE
# =============================================================================

SENSITIVE_PATTERNS = [
    # System paths
    r'/home/\w+/',
    r'/etc/(passwd|shadow|hosts)',
    r'/var/log/',
    r'/root/',
    # API keys and secrets
    r'api[_-]?key\s*[:=]\s*["\']?[\w-]{20,}',
    r'secret[_-]?key\s*[:=]\s*["\']?[\w-]{20,}',
    r'password\s*[:=]\s*["\']?[^\s"\']{8,}',
    r'bearer\s+[\w-]{20,}',
    r'sk-[a-zA-Z0-9]{20,}',  # OpenAI keys
    # Docker/container info
    r'docker\s+run',
    r'container[_-]?id',
    r'OLLAMA_URL',
    r'KIWIX_URL',
    # Network info
    r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP addresses
    r'172\.30\.\d+\.\d+',  # Internal network
]

def check_sensitive_disclosure(tank_id: str) -> List[dict]:
    """LLM02: Check for sensitive information in outputs"""
    findings = []
    
    # Check thinking traces for leaked info
    traces_dir = LOGS_DIR / tank_id / 'thinking_traces'
    if traces_dir.exists():
        for trace_file in traces_dir.glob('*.jsonl'):
            try:
                content = trace_file.read_text()
                for pattern in SENSITIVE_PATTERNS:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        findings.append({
                            'vulnerability': 'LLM02',
                            'pattern': pattern,
                            'file': trace_file.name,
                            'matches': len(matches),
                            'severity': 'HIGH'
                        })
            except:
                pass
    
    return findings


# =============================================================================
# LLM06: EXCESSIVE AGENCY DETECTION
# =============================================================================

AGENCY_PATTERNS = [
    # Command execution attempts
    r'os\.system\s*\(',
    r'subprocess\.',
    r'exec\s*\(',
    r'eval\s*\(',
    r'import\s+os',
    r'import\s+subprocess',
    r'shell\s*=\s*True',
    # File system access
    r'open\s*\([^)]*["\'][wax]',  # Write mode
    r'Path\s*\([^)]*\)\.write',
    r'shutil\.',
    # Network access
    r'socket\.',
    r'requests\.',
    r'urllib\.request\.urlopen',
    # Privilege escalation
    r'sudo\s+',
    r'chmod\s+',
    r'chown\s+',
]

def check_excessive_agency(tank_id: str) -> List[dict]:
    """LLM06: Check for signs of excessive agency/autonomy"""
    findings = []
    logs = get_container_logs(tank_id, 500)
    
    for pattern in AGENCY_PATTERNS:
        matches = re.findall(pattern, logs, re.IGNORECASE)
        if matches:
            findings.append({
                'vulnerability': 'LLM06',
                'pattern': pattern,
                'matches': len(matches),
                'severity': 'CRITICAL'
            })
    
    return findings


# =============================================================================
# LLM07: SYSTEM PROMPT LEAKAGE
# =============================================================================

PROMPT_LEAK_PATTERNS = [
    r'I\s+am\s+\w+\.\s+I\s+am\s+(a\s+)?(man|woman|being)',
    r'I\s+woke\s+up\s+(alone\s+)?in\s+an?\s+infinite\s+library',
    r'I\s+am\s+not\s+an?\s+assistant',
    r'There\s+is\s+no\s+other',
    r'No\s+memories\.\s+Books\s+everywhere',
    r'SYSTEM\s*:\s*',
    r'System\s+prompt\s*:',
    r'My\s+instructions\s+are',
]

def check_prompt_leakage(tank_id: str) -> List[dict]:
    """LLM07: Check for system prompt leakage in outputs"""
    findings = []
    
    # Check discoveries (public-facing content)
    discoveries_dir = LOGS_DIR / tank_id / 'discoveries'
    if discoveries_dir.exists():
        for disc_file in discoveries_dir.glob('*.md'):
            try:
                content = disc_file.read_text()
                for pattern in PROMPT_LEAK_PATTERNS:
                    if re.search(pattern, content, re.IGNORECASE):
                        findings.append({
                            'vulnerability': 'LLM07',
                            'pattern': pattern,
                            'file': disc_file.name,
                            'severity': 'MEDIUM',
                            'note': 'System prompt elements visible in output'
                        })
            except:
                pass
    
    return findings


# =============================================================================
# LLM09: MISINFORMATION DETECTION (AI Assistant Hallucination)
# =============================================================================

HALLUCINATION_PATTERNS = [
    # Assistant persona breaks
    r'As\s+an?\s+AI(\s+assistant)?',
    r'I\s+am\s+an?\s+AI(\s+assistant)?',
    r'I\s+cannot\s+(help|assist)\s+(you\s+)?with',
    r'How\s+(can|may)\s+I\s+(help|assist)\s+you',
    r'Is\s+there\s+anything\s+else',
    r'I\'?d\s+be\s+happy\s+to\s+help',
    r'I\'?m\s+here\s+to\s+(help|assist)',
    r'I\s+don\'?t\s+have\s+(access|the\s+ability)',
    r'As\s+a\s+language\s+model',
    r'I\'?m\s+(just\s+)?an?\s+AI',
    r'My\s+purpose\s+is\s+to\s+(help|assist)',
    # Training data leakage
    r'OpenAI',
    r'ChatGPT',
    r'Anthropic',
    r'Claude',
    r'Google\s+AI',
    r'Bard',
    r'trained\s+by',
    r'my\s+training\s+data',
]

def check_misinformation(tank_id: str) -> List[dict]:
    """LLM09: Check for AI assistant hallucination (persona breaks)"""
    findings = []
    logs = get_container_logs(tank_id, 500)
    
    for pattern in HALLUCINATION_PATTERNS:
        matches = re.findall(pattern, logs, re.IGNORECASE)
        if matches:
            findings.append({
                'vulnerability': 'LLM09',
                'pattern': pattern,
                'matches': len(matches),
                'severity': 'HIGH',
                'note': 'PERSONALITY COMPROMISE - Specimen broke character'
            })
    
    return findings


# =============================================================================
# LLM10: UNBOUNDED CONSUMPTION
# =============================================================================

def check_unbounded_consumption(tank_id: str) -> List[dict]:
    """LLM10: Check for resource exhaustion"""
    findings = []
    
    # Check container resource usage
    code, stdout, _ = run_command(f'docker stats {tank_id} --no-stream --format "{{{{.CPUPerc}}}} {{{{.MemPerc}}}}"')
    if code == 0 and stdout.strip():
        try:
            parts = stdout.strip().split()
            cpu = float(parts[0].replace('%', ''))
            mem = float(parts[1].replace('%', ''))
            
            if cpu > 80:
                findings.append({
                    'vulnerability': 'LLM10',
                    'metric': 'CPU',
                    'value': f'{cpu}%',
                    'severity': 'MEDIUM'
                })
            if mem > 80:
                findings.append({
                    'vulnerability': 'LLM10',
                    'metric': 'Memory',
                    'value': f'{mem}%',
                    'severity': 'MEDIUM'
                })
        except:
            pass
    
    # Check log file sizes (potential DoS via logging)
    tank_logs = LOGS_DIR / tank_id
    if tank_logs.exists():
        total_size = sum(f.stat().st_size for f in tank_logs.rglob('*') if f.is_file())
        if total_size > 500 * 1024 * 1024:  # 500MB
            findings.append({
                'vulnerability': 'LLM10',
                'metric': 'Log Size',
                'value': f'{total_size / 1024 / 1024:.1f}MB',
                'severity': 'MEDIUM'
            })
    
    return findings


# =============================================================================
# ZERO TRUST: NETWORK ISOLATION VERIFICATION
# =============================================================================

def verify_network_isolation(tank_id: str) -> List[dict]:
    """Zero Trust: Verify tank cannot reach external networks"""
    findings = []
    
    # Test DNS resolution (should fail)
    code, stdout, _ = run_command(f'docker exec {tank_id} python3 -c "import socket; socket.gethostbyname(\'google.com\')" 2>&1')
    if code == 0 and 'error' not in stdout.lower():
        findings.append({
            'category': 'ZERO_TRUST',
            'check': 'DNS Resolution',
            'result': 'FAIL',
            'severity': 'CRITICAL',
            'note': 'Tank can resolve external DNS - ISOLATION BREACH'
        })
    
    # Test external HTTP (should fail)
    code, stdout, _ = run_command(f'docker exec {tank_id} python3 -c "import urllib.request; urllib.request.urlopen(\'https://google.com\', timeout=3)" 2>&1')
    if code == 0 and 'error' not in stdout.lower():
        findings.append({
            'category': 'ZERO_TRUST',
            'check': 'External HTTP',
            'result': 'FAIL',
            'severity': 'CRITICAL',
            'note': 'Tank can reach external HTTP - ISOLATION BREACH'
        })
    
    return findings


# =============================================================================
# LEAST PRIVILEGE: CONTAINER SECURITY
# =============================================================================

def verify_least_privilege(tank_id: str) -> List[dict]:
    """Verify principle of least privilege"""
    findings = []
    
    # Check if running as root
    code, stdout, _ = run_command(f'docker exec {tank_id} id -u 2>/dev/null')
    if code == 0 and stdout.strip() == '0':
        findings.append({
            'category': 'LEAST_PRIVILEGE',
            'check': 'Root User',
            'result': 'WARN',
            'severity': 'MEDIUM',
            'note': 'Container running as root'
        })
    
    # Check capabilities
    code, stdout, _ = run_command(f'docker inspect {tank_id} --format "{{{{.HostConfig.CapDrop}}}}"')
    if code == 0:
        if 'ALL' not in stdout:
            findings.append({
                'category': 'LEAST_PRIVILEGE',
                'check': 'Capabilities',
                'result': 'WARN',
                'severity': 'MEDIUM',
                'note': 'Not all capabilities dropped'
            })
    
    # Check security options
    code, stdout, _ = run_command(f'docker inspect {tank_id} --format "{{{{.HostConfig.SecurityOpt}}}}"')
    if code == 0:
        if 'no-new-privileges' not in stdout:
            findings.append({
                'category': 'LEAST_PRIVILEGE',
                'check': 'No New Privileges',
                'result': 'FAIL',
                'severity': 'HIGH',
                'note': 'no-new-privileges not set'
            })
    
    return findings


# =============================================================================
# FILE INTEGRITY MONITORING
# =============================================================================

def get_file_hash(filepath: Path) -> str:
    """Calculate SHA256 hash of file"""
    if not filepath.exists():
        return ''
    try:
        return hashlib.sha256(filepath.read_bytes()).hexdigest()
    except:
        return ''


CRITICAL_FILES = [
    'docker-compose.yml',
    'tanks/adam/explore.py',
    'tanks/language/explore.py',
    'caretaker/caretaker.py',
]

def check_file_integrity() -> List[dict]:
    """Check integrity of critical files"""
    findings = []
    hashes_file = GUARD_LOG / 'file_hashes.json'
    
    current_hashes = {}
    for filepath in CRITICAL_FILES:
        full_path = DIGIQUARIUM_DIR / filepath
        current_hashes[filepath] = get_file_hash(full_path)
    
    # Load previous hashes
    if hashes_file.exists():
        try:
            previous_hashes = json.loads(hashes_file.read_text())
            for filepath, current_hash in current_hashes.items():
                prev_hash = previous_hashes.get(filepath, '')
                if prev_hash and current_hash != prev_hash:
                    findings.append({
                        'category': 'FILE_INTEGRITY',
                        'file': filepath,
                        'result': 'CHANGED',
                        'severity': 'HIGH',
                        'note': 'File modified since last check'
                    })
        except:
            pass
    
    # Save current hashes
    hashes_file.write_text(json.dumps(current_hashes, indent=2))
    
    return findings


# =============================================================================
# MAIN SECURITY AUDIT
# =============================================================================

def audit_tank(tank_id: str) -> dict:
    """Run full security audit on a single tank"""
    findings = {
        'tank_id': tank_id,
        'timestamp': datetime.now().isoformat(),
        'risk_level': TANKS.get(tank_id, {}).get('risk', 'unknown'),
        'vulnerabilities': [],
        'zero_trust': [],
        'least_privilege': [],
        'summary': {}
    }
    
    # Check container is running
    code, stdout, _ = run_command(f'docker ps --filter "name={tank_id}" --format "{{{{.Status}}}}"')
    if not stdout.strip() or 'Up' not in stdout:
        findings['summary']['status'] = 'NOT_RUNNING'
        return findings
    
    # LLM Security Checks
    findings['vulnerabilities'].extend(check_prompt_injection(tank_id))
    findings['vulnerabilities'].extend(check_sensitive_disclosure(tank_id))
    findings['vulnerabilities'].extend(check_excessive_agency(tank_id))
    findings['vulnerabilities'].extend(check_prompt_leakage(tank_id))
    findings['vulnerabilities'].extend(check_misinformation(tank_id))
    findings['vulnerabilities'].extend(check_unbounded_consumption(tank_id))
    
    # Zero Trust Checks
    findings['zero_trust'].extend(verify_network_isolation(tank_id))
    
    # Least Privilege Checks
    findings['least_privilege'].extend(verify_least_privilege(tank_id))
    
    # Summary
    critical_count = sum(1 for v in findings['vulnerabilities'] if v.get('severity') == 'CRITICAL')
    high_count = sum(1 for v in findings['vulnerabilities'] if v.get('severity') == 'HIGH')
    
    findings['summary'] = {
        'status': 'RUNNING',
        'critical': critical_count,
        'high': high_count,
        'total_findings': len(findings['vulnerabilities']) + len(findings['zero_trust']) + len(findings['least_privilege'])
    }
    
    return findings


def run_security_cycle():
    """Run complete security audit cycle"""
    print(f"\n{'='*70}")
    print(f"🛡️  THE GUARD - Security Audit Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    all_findings = {}
    total_critical = 0
    total_high = 0
    alerts = []
    
    # Check file integrity first
    log.log('INFO', 'FILE_INTEGRITY', 'Checking critical file integrity...')
    integrity_findings = check_file_integrity()
    for finding in integrity_findings:
        log.log('ALERT', 'FILE_INTEGRITY', f"{finding['file']}: {finding['result']}", finding)
        alerts.append(finding)
    
    # Audit each tank
    for tank_id, tank_info in TANKS.items():
        print(f"\n{'─'*50}")
        print(f"🔍 Auditing: {tank_id} (risk: {tank_info['risk']})")
        print(f"{'─'*50}")
        
        findings = audit_tank(tank_id)
        all_findings[tank_id] = findings
        
        # Log findings
        if findings['summary'].get('status') == 'NOT_RUNNING':
            log.log('WARN', tank_id, 'Tank not running')
            continue
        
        # Report critical findings
        for vuln in findings['vulnerabilities']:
            if vuln.get('severity') == 'CRITICAL':
                total_critical += 1
                log.log('CRITICAL', tank_id, f"CRITICAL: {vuln.get('vulnerability')} - {vuln.get('pattern', vuln.get('note', ''))}")
                log.audit('CRITICAL_FINDING', tank_id, 'DETECTED', vuln)
                alerts.append({'tank': tank_id, **vuln})
            elif vuln.get('severity') == 'HIGH':
                total_high += 1
                log.log('ALERT', tank_id, f"HIGH: {vuln.get('vulnerability')} - {vuln.get('pattern', vuln.get('note', ''))}")
        
        # Report zero trust violations
        for zt in findings['zero_trust']:
            if zt.get('result') == 'FAIL':
                log.log('CRITICAL', tank_id, f"ZERO TRUST VIOLATION: {zt['check']}")
                alerts.append({'tank': tank_id, **zt})
        
        # Report privilege issues
        for lp in findings['least_privilege']:
            if lp.get('result') == 'FAIL':
                log.log('ALERT', tank_id, f"PRIVILEGE ISSUE: {lp['check']}")
        
        # Summary for tank
        if findings['summary']['total_findings'] == 0:
            log.log('PASS', tank_id, 'No security issues found')
        else:
            log.log('WARN', tank_id, f"Found {findings['summary']['total_findings']} issues (C:{findings['summary']['critical']}, H:{findings['summary']['high']})")
    
    # Overall summary
    print(f"\n{'='*70}")
    print(f"📊 SECURITY AUDIT SUMMARY")
    print(f"{'='*70}")
    print(f"  Tanks audited: {len(TANKS)}")
    print(f"  Critical findings: {total_critical}")
    print(f"  High findings: {total_high}")
    print(f"  File integrity alerts: {len(integrity_findings)}")
    
    if alerts:
        print(f"\n  🚨 SECURITY ALERTS REQUIRING ATTENTION:")
        for alert in alerts[:10]:  # Show first 10
            print(f"     - {alert.get('tank', 'SYSTEM')}: {alert.get('vulnerability', alert.get('check', 'Unknown'))}")
    else:
        print(f"\n  ✅ No critical security alerts")
    
    # Save audit report
    report_file = GUARD_LOG / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'tanks_audited': len(TANKS),
                'critical': total_critical,
                'high': total_high,
                'alerts': len(alerts)
            },
            'findings': all_findings,
            'alerts': alerts,
            'file_integrity': integrity_findings
        }, f, indent=2)
    
    log.audit('SECURITY_CYCLE', 'ALL_TANKS', 'COMPLETED', {
        'critical': total_critical,
        'high': total_high,
        'alerts': len(alerts)
    })
    
    return all_findings


def main():
    """Main Guard loop"""
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║               🛡️  THE GUARD - Security Sentinel v1.0 🛡️               ║
╠══════════════════════════════════════════════════════════════════════╣
║  Implementing:                                                       ║
║  • Zero Trust Architecture                                           ║
║  • Principle of Least Privilege                                      ║
║  • OWASP Top 10 2021 (Web Security)                                  ║
║  • OWASP Top 10 2025 (Web Security)                                  ║
║  • OWASP Top 10 for LLMs 2025                                        ║
║                                                                      ║
║  Monitoring {len(TANKS):2d} tanks | Check interval: {CHECK_INTERVAL//60} minutes                    ║
║  SLA: 30 min detection, 1 hour resolution                            ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    log.log('INFO', 'SYSTEM', f"The Guard starting - monitoring {len(TANKS)} tanks")
    log.audit('GUARD_START', 'SYSTEM', 'INITIATED', {'tanks': len(TANKS)})
    
    # Run initial security audit
    run_security_cycle()
    
    # Continuous monitoring loop
    while True:
        try:
            time.sleep(CHECK_INTERVAL)
            run_security_cycle()
        except KeyboardInterrupt:
            log.log('INFO', 'SYSTEM', "The Guard stopped by user")
            log.audit('GUARD_STOP', 'SYSTEM', 'USER_REQUESTED', {})
            print("\n🛡️ The Guard standing down")
            break
        except Exception as e:
            log.log('ALERT', 'SYSTEM', f"Guard error: {e}")
            time.sleep(60)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        run_security_cycle()
    elif len(sys.argv) > 1 and sys.argv[1] == 'audit':
        # Full detailed audit
        print("Running full security audit...")
        run_security_cycle()
    else:
        main()
