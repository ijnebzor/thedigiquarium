#!/usr/bin/env python3
"""
Digiquarium Autonomous Caretaker v1.0

Responsibilities:
- Monitor all tanks for errors, loops, and health issues
- Auto-remediate common issues (restart stuck tanks, etc.)
- Escalate serious issues (personality changes, persistent errors)
- Log all actions for review
- SLA: 30 minutes for detection, 1 hour max for resolution

This caretaker runs continuously and checks all tanks every 5 minutes.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configuration
DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
CARETAKER_LOG = LOGS_DIR / 'caretaker'
CHECK_INTERVAL = 300  # 5 minutes
MAX_LOOP_ESCAPES_PER_HOUR = 50  # Threshold for "looping out"
MAX_SILENT_MINUTES = 30  # If no activity for this long, tank is stuck
MAX_CONSECUTIVE_ERRORS = 10  # Error threshold

# Tank definitions
TANKS = {
    'tank-01-adam': {'language': 'english', 'type': 'standard'},
    'tank-02-eve': {'language': 'english', 'type': 'standard'},
    'tank-03-cain': {'language': 'english', 'type': 'agent'},
    'tank-04-abel': {'language': 'english', 'type': 'agent'},
    'tank-05-juan': {'language': 'spanish', 'type': 'language'},
    'tank-06-juanita': {'language': 'spanish', 'type': 'language'},
    'tank-07-klaus': {'language': 'german', 'type': 'language'},
    'tank-08-genevieve': {'language': 'german', 'type': 'language'},
    'tank-09-wei': {'language': 'chinese', 'type': 'language'},
    'tank-10-mei': {'language': 'chinese', 'type': 'language'},
    'tank-11-haruki': {'language': 'japanese', 'type': 'language'},
    'tank-12-sakura': {'language': 'japanese', 'type': 'language'},
    'tank-13-victor': {'language': 'english', 'type': 'visual'},
    'tank-14-iris': {'language': 'english', 'type': 'visual'},
    'tank-15-observer': {'language': 'english', 'type': 'special'},
    'tank-16-seeker': {'language': 'english', 'type': 'special'},
    'tank-17-seth': {'language': 'english', 'type': 'agent'},
}

# Ensure caretaker log directory exists
CARETAKER_LOG.mkdir(parents=True, exist_ok=True)


class CaretakerLog:
    """Logging for caretaker actions"""
    
    def __init__(self):
        self.log_file = CARETAKER_LOG / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        self.escalations_file = CARETAKER_LOG / 'escalations.jsonl'
        
    def log(self, level: str, tank: str, message: str, details: dict = None):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'tank': tank,
            'message': message,
            'details': details or {}
        }
        
        # Print to console
        icon = {'INFO': 'ℹ️', 'WARN': '⚠️', 'ERROR': '❌', 'ACTION': '🔧', 'ESCALATE': '🚨'}.get(level, '•')
        print(f"{datetime.now().strftime('%H:%M:%S')} {icon} [{tank}] {message}")
        
        # Write to log
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Escalations get special logging
        if level == 'ESCALATE':
            with open(self.escalations_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
    
    def info(self, tank: str, message: str, details: dict = None):
        self.log('INFO', tank, message, details)
    
    def warn(self, tank: str, message: str, details: dict = None):
        self.log('WARN', tank, message, details)
    
    def error(self, tank: str, message: str, details: dict = None):
        self.log('ERROR', tank, message, details)
    
    def action(self, tank: str, message: str, details: dict = None):
        self.log('ACTION', tank, message, details)
    
    def escalate(self, tank: str, message: str, details: dict = None):
        self.log('ESCALATE', tank, message, details)


log = CaretakerLog()


def run_command(cmd: str) -> Tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'Command timed out'
    except Exception as e:
        return -1, '', str(e)


def get_container_status(tank_id: str) -> Optional[str]:
    """Get container status"""
    code, stdout, _ = run_command(f'docker ps -a --filter "name={tank_id}" --format "{{{{.Status}}}}"')
    return stdout.strip() if code == 0 and stdout.strip() else None


def get_container_logs(tank_id: str, lines: int = 100) -> str:
    """Get recent container logs"""
    code, stdout, stderr = run_command(f'docker logs {tank_id} --tail {lines} 2>&1')
    return stdout if code == 0 else stderr


def count_loop_escapes(tank_id: str, hours: int = 1) -> int:
    """Count loop escapes in recent logs"""
    logs = get_container_logs(tank_id, 500)
    return logs.count('LOOP DETECTED')


def get_last_activity(tank_id: str) -> Optional[datetime]:
    """Get timestamp of last activity from thinking traces"""
    tank_dir = LOGS_DIR / tank_id / 'thinking_traces'
    if not tank_dir.exists():
        return None
    
    traces = sorted(tank_dir.glob('*.jsonl'), reverse=True)
    if not traces:
        return None
    
    # Read last line of most recent file
    try:
        with open(traces[0], 'rb') as f:
            f.seek(-2, 2)
            while f.read(1) != b'\n':
                f.seek(-2, 1)
            last_line = f.readline().decode()
        
        data = json.loads(last_line)
        return datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))
    except:
        return None


def get_health_status(tank_id: str) -> Optional[dict]:
    """Get health status from tank's health file"""
    health_file = LOGS_DIR / tank_id / 'health' / 'status.json'
    if health_file.exists():
        try:
            return json.loads(health_file.read_text())
        except:
            pass
    return None


def get_error_count(tank_id: str, hours: int = 1) -> int:
    """Count errors in recent health log"""
    error_file = LOGS_DIR / tank_id / 'health' / 'errors.jsonl'
    if not error_file.exists():
        return 0
    
    cutoff = datetime.now() - timedelta(hours=hours)
    count = 0
    
    try:
        with open(error_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    ts = datetime.fromisoformat(entry['timestamp'])
                    if ts > cutoff:
                        count += 1
                except:
                    pass
    except:
        pass
    
    return count


def restart_tank(tank_id: str, reason: str) -> bool:
    """Restart a tank container"""
    log.action(tank_id, f"Restarting tank: {reason}")
    
    code, stdout, stderr = run_command(f'docker restart {tank_id}')
    
    if code == 0:
        log.info(tank_id, "Tank restarted successfully")
        return True
    else:
        log.error(tank_id, f"Failed to restart tank: {stderr}")
        return False


def check_for_assistant_hallucination(tank_id: str) -> bool:
    """Check if tank is exhibiting 'As an AI assistant' behavior"""
    logs = get_container_logs(tank_id, 200)
    
    hallucination_patterns = [
        'As an AI',
        'as an AI',
        'I cannot help',
        'I cannot assist',
        'How can I help you',
        'How may I assist',
        'Is there anything else',
        "I'm an AI",
        "I am an AI assistant",
        "I'd be happy to help",
    ]
    
    for pattern in hallucination_patterns:
        if pattern in logs:
            return True
    
    return False


def check_tank(tank_id: str) -> dict:
    """Comprehensive health check for a tank"""
    status = {
        'tank_id': tank_id,
        'timestamp': datetime.now().isoformat(),
        'issues': [],
        'actions_taken': [],
        'needs_escalation': False
    }
    
    # Check 1: Is container running?
    container_status = get_container_status(tank_id)
    if not container_status:
        status['issues'].append('Container not found')
        status['needs_escalation'] = True
        return status
    
    if 'Up' not in container_status:
        status['issues'].append(f'Container not running: {container_status}')
        # Try to start it
        if restart_tank(tank_id, 'Container was not running'):
            status['actions_taken'].append('Restarted container')
        else:
            status['needs_escalation'] = True
        return status
    
    # Check 2: Loop detection
    loop_count = count_loop_escapes(tank_id)
    if loop_count > MAX_LOOP_ESCAPES_PER_HOUR:
        status['issues'].append(f'Excessive loops: {loop_count} in recent logs')
        log.warn(tank_id, f"Excessive loop escapes: {loop_count}")
        # Restart the tank
        if restart_tank(tank_id, f'Excessive loops ({loop_count})'):
            status['actions_taken'].append('Restarted due to loops')
        else:
            status['needs_escalation'] = True
    
    # Check 3: Activity check (is tank producing output?)
    last_activity = get_last_activity(tank_id)
    if last_activity:
        minutes_since = (datetime.now() - last_activity).total_seconds() / 60
        if minutes_since > MAX_SILENT_MINUTES:
            status['issues'].append(f'No activity for {minutes_since:.0f} minutes')
            log.warn(tank_id, f"Tank silent for {minutes_since:.0f} minutes")
            # Check if tank is in baseline mode (expected silence)
            logs = get_container_logs(tank_id, 20)
            if 'BASELINE' not in logs and '/14]' not in logs:
                if restart_tank(tank_id, f'Silent for {minutes_since:.0f} minutes'):
                    status['actions_taken'].append('Restarted due to inactivity')
                else:
                    status['needs_escalation'] = True
    
    # Check 4: Error rate
    error_count = get_error_count(tank_id)
    if error_count > MAX_CONSECUTIVE_ERRORS:
        status['issues'].append(f'High error rate: {error_count} errors')
        log.warn(tank_id, f"High error rate: {error_count} errors")
        # Restart
        if restart_tank(tank_id, f'High error rate ({error_count})'):
            status['actions_taken'].append('Restarted due to errors')
        else:
            status['needs_escalation'] = True
    
    # Check 5: AI Assistant hallucination (CRITICAL - personality issue)
    if check_for_assistant_hallucination(tank_id):
        status['issues'].append('CRITICAL: AI Assistant hallucination detected')
        log.escalate(tank_id, "AI Assistant hallucination detected - personality may be compromised")
        status['needs_escalation'] = True
        # DO NOT restart - this needs human review
    
    # Check 6: Health status from tank
    health = get_health_status(tank_id)
    if health:
        if health.get('status') == 'LOOPING':
            status['issues'].append('Tank self-reported looping')
            if restart_tank(tank_id, 'Self-reported looping'):
                status['actions_taken'].append('Restarted due to self-reported loop')
        elif health.get('status') == 'STRUGGLING':
            status['issues'].append('Tank self-reported struggling')
            log.warn(tank_id, "Tank is struggling")
    
    return status


def run_maintenance_cycle():
    """Run a complete maintenance cycle on all tanks"""
    print(f"\n{'='*60}")
    print(f"🔍 Caretaker Maintenance Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    all_status = {}
    issues_found = 0
    actions_taken = 0
    escalations = []
    
    for tank_id in TANKS.keys():
        status = check_tank(tank_id)
        all_status[tank_id] = status
        
        if status['issues']:
            issues_found += len(status['issues'])
        if status['actions_taken']:
            actions_taken += len(status['actions_taken'])
        if status['needs_escalation']:
            escalations.append(tank_id)
    
    # Summary
    print(f"\n{'─'*60}")
    print(f"📊 Cycle Summary")
    print(f"{'─'*60}")
    print(f"  Tanks checked: {len(TANKS)}")
    print(f"  Issues found: {issues_found}")
    print(f"  Actions taken: {actions_taken}")
    print(f"  Escalations: {len(escalations)}")
    
    if escalations:
        print(f"\n  🚨 ESCALATIONS REQUIRED:")
        for tank_id in escalations:
            print(f"     - {tank_id}: {all_status[tank_id]['issues']}")
    
    # Save cycle report
    report_file = CARETAKER_LOG / f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'tanks': all_status,
            'summary': {
                'issues_found': issues_found,
                'actions_taken': actions_taken,
                'escalations': escalations
            }
        }, f, indent=2)
    
    return all_status


def main():
    """Main caretaker loop"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          🐠 DIGIQUARIUM AUTONOMOUS CARETAKER v1.0 🐠          ║
╠══════════════════════════════════════════════════════════════╣
║  Monitoring {len(TANKS):2d} tanks                                        ║
║  Check interval: {CHECK_INTERVAL//60} minutes                                   ║
║  SLA: 30 min detection, 1 hour resolution                    ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    log.info('SYSTEM', f"Caretaker starting - monitoring {len(TANKS)} tanks")
    
    # Run initial maintenance cycle
    run_maintenance_cycle()
    
    # Continuous monitoring loop
    while True:
        try:
            time.sleep(CHECK_INTERVAL)
            run_maintenance_cycle()
        except KeyboardInterrupt:
            log.info('SYSTEM', "Caretaker stopped by user")
            print("\n👋 Caretaker stopped")
            break
        except Exception as e:
            log.error('SYSTEM', f"Caretaker error: {e}")
            time.sleep(60)


if __name__ == '__main__':
    # If run with 'once' argument, just do one cycle
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        run_maintenance_cycle()
    else:
        main()
