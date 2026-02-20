#!/usr/bin/env python3
"""
DIGIQUARIUM CARETAKER v2.0 - Enhanced Operations
=================================================

Integrated with:
- Scheduler (12-hour baselines, daily summaries)
- Guard (security checks)
- Translator (language processing)

SLA: 30 minutes detection, 1 hour resolution
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
CARETAKER_LOG = LOGS_DIR / 'caretaker'
OPS_DIR = DIGIQUARIUM_DIR / 'operations'

CARETAKER_LOG.mkdir(parents=True, exist_ok=True)

TANKS = [
    ('tank-01-adam', 'english', 'control'),
    ('tank-02-eve', 'english', 'control'),
    ('tank-03-cain', 'english', 'agent'),
    ('tank-04-abel', 'english', 'agent'),
    ('tank-05-juan', 'spanish', 'language'),
    ('tank-06-juanita', 'spanish', 'language'),
    ('tank-07-klaus', 'german', 'language'),
    ('tank-08-genevieve', 'german', 'language'),
    ('tank-09-wei', 'chinese', 'language'),
    ('tank-10-mei', 'chinese', 'language'),
    ('tank-11-haruki', 'japanese', 'language'),
    ('tank-12-sakura', 'japanese', 'language'),
    ('tank-13-victor', 'english', 'visual'),
    ('tank-14-iris', 'english', 'visual'),
    ('tank-15-observer', 'english', 'special'),
    ('tank-16-seeker', 'english', 'special'),
    ('tank-17-seth', 'english', 'agent'),
]

CHECK_INTERVAL = 300  # 5 minutes
MAX_SILENT_MINUTES = 30
MAX_LOOP_ESCAPES = 50


class CaretakerLog:
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
        icon = {'INFO': 'ℹ️', 'WARN': '⚠️', 'ERROR': '❌', 'ACTION': '🔧', 'ESCALATE': '🚨'}.get(level, '•')
        print(f"{datetime.now().strftime('%H:%M:%S')} {icon} [{tank}] {message}")
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        if level == 'ESCALATE':
            with open(self.escalations_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')


log = CaretakerLog()


def run_command(cmd: str, timeout: int = 60) -> Tuple[int, str, str]:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'Timeout'
    except Exception as e:
        return -1, '', str(e)


def get_container_status(tank_id: str) -> Optional[str]:
    code, stdout, _ = run_command(f'docker ps -a --filter "name={tank_id}" --format "{{{{.Status}}}}"')
    return stdout.strip() if code == 0 and stdout.strip() else None


def get_container_logs(tank_id: str, lines: int = 100) -> str:
    code, stdout, stderr = run_command(f'docker logs {tank_id} --tail {lines} 2>&1')
    return stdout if code == 0 else stderr


def fix_permissions(tank_id: str) -> bool:
    """Fix permission issues for tank log directories"""
    tank_dir = LOGS_DIR / tank_id
    log.log('ACTION', tank_id, f'Fixing permissions for {tank_dir}')
    
    # Try to fix ownership - this may require elevated privileges
    code, _, _ = run_command(f'chmod -R 777 {tank_dir} 2>/dev/null || true')
    
    # Create missing directories
    for subdir in ['baselines', 'thinking_traces', 'discoveries', 'health']:
        (tank_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    return True


def restart_tank(tank_id: str, reason: str) -> bool:
    log.log('ACTION', tank_id, f'Restarting: {reason}')
    code, _, stderr = run_command(f'docker restart {tank_id}')
    if code == 0:
        log.log('INFO', tank_id, 'Restarted successfully')
        return True
    else:
        log.log('ERROR', tank_id, f'Restart failed: {stderr}')
        return False


def queue_baseline(tank_id: str):
    """Queue a baseline task for later execution"""
    queue_file = OPS_DIR / 'baseline_queue.json'
    queue = []
    if queue_file.exists():
        try:
            queue = json.loads(queue_file.read_text())
        except:
            pass
    
    if tank_id not in queue:
        queue.append(tank_id)
        queue_file.write_text(json.dumps(queue))
        log.log('INFO', tank_id, 'Queued for baseline')


def check_tank(tank_id: str, language: str, tank_type: str) -> dict:
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
    if not container_status or 'Up' not in container_status:
        status['issues'].append('Container not running')
        if restart_tank(tank_id, 'Container was not running'):
            status['actions_taken'].append('Restarted container')
        else:
            status['needs_escalation'] = True
        return status
    
    # Check 2: Thinking traces being generated?
    tank_dir = LOGS_DIR / tank_id
    traces_dir = tank_dir / 'thinking_traces'
    today = datetime.now().strftime('%Y-%m-%d')
    
    if not traces_dir.exists():
        status['issues'].append('No thinking_traces directory')
        fix_permissions(tank_id)
        status['actions_taken'].append('Created directories')
    else:
        today_file = traces_dir / f'{today}.jsonl'
        if today_file.exists():
            # Check last modification time
            mtime = datetime.fromtimestamp(today_file.stat().st_mtime)
            minutes_since = (datetime.now() - mtime).total_seconds() / 60
            if minutes_since > MAX_SILENT_MINUTES:
                status['issues'].append(f'No activity for {minutes_since:.0f} minutes')
                # Check if in baseline mode
                logs = get_container_logs(tank_id, 20)
                if '/14]' in logs or 'BASELINE' in logs:
                    log.log('INFO', tank_id, 'In baseline mode - activity pause expected')
                else:
                    if restart_tank(tank_id, f'Silent for {minutes_since:.0f} minutes'):
                        status['actions_taken'].append('Restarted due to inactivity')
    
    # Check 3: Permission errors in logs
    logs = get_container_logs(tank_id, 100)
    if 'PermissionError' in logs or 'Permission denied' in logs:
        status['issues'].append('Permission errors detected')
        fix_permissions(tank_id)
        status['actions_taken'].append('Fixed permissions')
    
    # Check 4: Loop detection
    loop_count = logs.count('LOOP DETECTED')
    if loop_count > MAX_LOOP_ESCAPES:
        status['issues'].append(f'Excessive loops: {loop_count}')
        if restart_tank(tank_id, f'Looping ({loop_count} escapes)'):
            status['actions_taken'].append('Restarted due to loops')
    
    # Check 5: Baseline exists?
    baselines_dir = tank_dir / 'baselines'
    if baselines_dir.exists():
        baselines = list(baselines_dir.glob('*.json'))
        if not baselines:
            status['issues'].append('No baselines')
            queue_baseline(tank_id)
            status['actions_taken'].append('Queued for baseline')
    else:
        status['issues'].append('No baselines directory')
        fix_permissions(tank_id)
        queue_baseline(tank_id)
    
    # Check 6: AI hallucination detection
    hallucination_patterns = ['As an AI', 'I cannot help', 'How can I assist']
    for pattern in hallucination_patterns:
        if pattern in logs:
            status['issues'].append(f'PERSONALITY BREAK: "{pattern}"')
            status['needs_escalation'] = True
            log.log('ESCALATE', tank_id, f'Personality compromise detected: {pattern}')
    
    return status


def process_baseline_queue():
    """Process queued baseline tasks sequentially"""
    queue_file = OPS_DIR / 'baseline_queue.json'
    if not queue_file.exists():
        return
    
    try:
        queue = json.loads(queue_file.read_text())
    except:
        return
    
    if not queue:
        return
    
    # Process one at a time
    tank_id = queue.pop(0)
    log.log('INFO', tank_id, 'Processing queued baseline')
    
    # Run baseline
    code, stdout, stderr = run_command(f'docker exec {tank_id} python3 /tank/baseline.py', timeout=1800)
    
    if code == 0:
        log.log('INFO', tank_id, 'Baseline completed successfully')
    else:
        log.log('ERROR', tank_id, f'Baseline failed: {stderr[:100]}')
        # Re-queue if failed
        queue.append(tank_id)
    
    # Save updated queue
    queue_file.write_text(json.dumps(queue))
    
    # Wait before next (let Ollama rest)
    time.sleep(30)


def run_maintenance_cycle():
    """Run complete maintenance cycle"""
    print(f"\n{'='*60}")
    print(f"🔧 Caretaker Maintenance - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    all_status = {}
    issues_found = 0
    actions_taken = 0
    escalations = []
    
    for tank_id, language, tank_type in TANKS:
        status = check_tank(tank_id, language, tank_type)
        all_status[tank_id] = status
        
        if status['issues']:
            issues_found += len(status['issues'])
        if status['actions_taken']:
            actions_taken += len(status['actions_taken'])
        if status['needs_escalation']:
            escalations.append(tank_id)
    
    # Process any queued baselines
    process_baseline_queue()
    
    # Summary
    print(f"\n{'─'*60}")
    print(f"📊 Cycle Summary")
    print(f"  Tanks: {len(TANKS)} | Issues: {issues_found} | Actions: {actions_taken} | Escalations: {len(escalations)}")
    
    if escalations:
        print(f"  🚨 ESCALATIONS: {', '.join(escalations)}")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'tanks': all_status,
        'summary': {
            'issues': issues_found,
            'actions': actions_taken,
            'escalations': escalations
        }
    }
    
    report_file = CARETAKER_LOG / f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.write_text(json.dumps(report, indent=2))
    
    return all_status


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║              🔧 DIGIQUARIUM CARETAKER v2.0 🔧                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  Monitoring: 17 tanks                                                ║
║  Check interval: 5 minutes                                           ║
║  SLA: 30 min detection, 1 hour resolution                            ║
║  Features: Permission fixing, baseline queuing, escalation           ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    log.log('INFO', 'SYSTEM', f'Caretaker v2.0 starting - monitoring {len(TANKS)} tanks')
    
    # Initial cycle
    run_maintenance_cycle()
    
    # Continuous monitoring
    while True:
        try:
            time.sleep(CHECK_INTERVAL)
            run_maintenance_cycle()
        except KeyboardInterrupt:
            log.log('INFO', 'SYSTEM', 'Caretaker stopped by user')
            break
        except Exception as e:
            log.log('ERROR', 'SYSTEM', f'Error: {e}')
            time.sleep(60)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        run_maintenance_cycle()
    else:
        main()
