#!/usr/bin/env python3
"""
Digiquarium Autonomous Caretaker v1.0
Monitors all tanks and handles issues automatically

SLA: 30 minute detection, 1 hour resolution maximum
"""

import os, sys, json, time, subprocess, re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Configuration
CHECK_INTERVAL = 60  # Check every minute
LOOP_THRESHOLD = 50  # More than 50 loop escapes in 10 minutes = problem
SILENCE_THRESHOLD = 300  # 5 minutes without output = problem
ESCALATION_FILE = Path('/home/ijneb/digiquarium/logs/caretaker/escalations.json')
STATUS_FILE = Path('/home/ijneb/digiquarium/logs/caretaker/status.json')
LOG_FILE = Path('/home/ijneb/digiquarium/logs/caretaker/caretaker.log')

# Ensure directories exist
Path('/home/ijneb/digiquarium/logs/caretaker').mkdir(parents=True, exist_ok=True)

# All tanks to monitor
TANKS = [
    'tank-01-adam', 'tank-02-eve', 'tank-03-cain', 'tank-04-abel',
    'tank-05-juan', 'tank-06-juanita', 'tank-07-klaus', 'tank-08-genevieve',
    'tank-09-wei', 'tank-10-mei', 'tank-11-haruki', 'tank-12-sakura',
    'tank-13-victor', 'tank-14-iris', 'tank-15-observer', 'tank-16-seeker',
    'tank-17-seth'
]


def log(message, level='INFO'):
    """Log to caretaker log file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] [{level}] {message}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def run_command(cmd, timeout=30):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        return None


def get_container_status(tank_name):
    """Get container status"""
    output = run_command(f"docker ps --filter 'name={tank_name}' --format '{{{{.Status}}}}'")
    return output if output else 'NOT RUNNING'


def get_recent_logs(tank_name, lines=100):
    """Get recent container logs"""
    output = run_command(f"docker logs {tank_name} --tail {lines} 2>&1")
    return output if output else ''


def count_loops_in_logs(logs):
    """Count loop escapes in log output"""
    return logs.count('LOOP DETECTED')


def count_thinking_in_logs(logs):
    """Count thinking outputs in log output"""
    return logs.count('💭')


def get_last_thinking_time(tank_name):
    """Get timestamp of last thinking output"""
    logs = get_recent_logs(tank_name, 50)
    # Look for timestamps near thinking outputs
    lines = logs.split('\n')
    for line in reversed(lines):
        if '💭' in line or '📖' in line:
            return datetime.now()  # Approximate - it's recent
    return None


def check_for_hallucinations(logs):
    """Check for AI assistant hallucinations"""
    hallucination_patterns = [
        r'as an ai',
        r'as a language model',
        r'i cannot help',
        r'i\'m sorry, but',
        r'i don\'t have the ability',
        r'as an assistant',
        r'i\'m designed to',
        r'my purpose is to help',
        r'how can i assist',
    ]
    logs_lower = logs.lower()
    for pattern in hallucination_patterns:
        if re.search(pattern, logs_lower):
            return pattern
    return None


def diagnose_tank(tank_name):
    """Diagnose issues with a specific tank"""
    issues = []
    
    # Check if running
    status = get_container_status(tank_name)
    if 'Up' not in status:
        issues.append({'type': 'NOT_RUNNING', 'severity': 'CRITICAL', 'details': status})
        return issues
    
    # Get recent logs
    logs = get_recent_logs(tank_name, 200)
    
    if not logs:
        issues.append({'type': 'NO_LOGS', 'severity': 'WARNING', 'details': 'Cannot retrieve logs'})
        return issues
    
    # Check for excessive looping
    loop_count = count_loops_in_logs(logs)
    if loop_count > LOOP_THRESHOLD:
        issues.append({
            'type': 'EXCESSIVE_LOOPING', 
            'severity': 'CRITICAL', 
            'details': f'{loop_count} loop escapes detected'
        })
    
    # Check for thinking output
    thinking_count = count_thinking_in_logs(logs)
    if thinking_count == 0:
        issues.append({
            'type': 'NO_THINKING', 
            'severity': 'WARNING', 
            'details': 'No thinking output in recent logs'
        })
    
    # Check for hallucinations
    hallucination = check_for_hallucinations(logs)
    if hallucination:
        issues.append({
            'type': 'HALLUCINATION', 
            'severity': 'CRITICAL', 
            'details': f'AI assistant pattern detected: "{hallucination}"'
        })
    
    # Check for errors
    if 'Error' in logs or '❌' in logs:
        # Extract error messages
        error_lines = [l for l in logs.split('\n') if 'Error' in l or '❌' in l]
        if error_lines:
            issues.append({
                'type': 'ERRORS', 
                'severity': 'WARNING', 
                'details': error_lines[-1][:100]
            })
    
    return issues


def restart_tank(tank_name):
    """Restart a tank"""
    log(f"Restarting {tank_name}...", 'ACTION')
    run_command(f"docker restart {tank_name}")
    time.sleep(5)
    status = get_container_status(tank_name)
    if 'Up' in status:
        log(f"✅ {tank_name} restarted successfully", 'ACTION')
        return True
    else:
        log(f"❌ {tank_name} restart failed", 'ERROR')
        return False


def recreate_tank(tank_name):
    """Recreate a tank from docker-compose"""
    log(f"Recreating {tank_name}...", 'ACTION')
    
    # Stop and remove
    run_command(f"docker stop {tank_name}")
    run_command(f"docker rm {tank_name}")
    
    # Determine profile
    if 'cain' in tank_name or 'abel' in tank_name or 'seth' in tank_name:
        profile = 'agents'
    elif any(x in tank_name for x in ['juan', 'klaus', 'wei', 'haruki']):
        profile = 'languages'
    elif 'victor' in tank_name or 'iris' in tank_name:
        profile = 'visual'
    elif 'observer' in tank_name or 'seeker' in tank_name:
        profile = 'special'
    else:
        profile = ''
    
    # Recreate
    if profile:
        cmd = f"cd /home/ijneb/digiquarium && docker compose --profile {profile} up -d {tank_name}"
    else:
        cmd = f"cd /home/ijneb/digiquarium && docker compose up -d {tank_name}"
    
    run_command(cmd)
    time.sleep(10)
    
    status = get_container_status(tank_name)
    if 'Up' in status:
        log(f"✅ {tank_name} recreated successfully", 'ACTION')
        return True
    else:
        log(f"❌ {tank_name} recreation failed", 'ERROR')
        return False


def handle_issue(tank_name, issue):
    """Handle a specific issue"""
    issue_type = issue['type']
    severity = issue['severity']
    
    log(f"Handling {issue_type} for {tank_name} (severity: {severity})", 'ACTION')
    
    if issue_type == 'NOT_RUNNING':
        return recreate_tank(tank_name)
    
    elif issue_type == 'EXCESSIVE_LOOPING':
        # Looping usually requires code fix + restart
        # For now, just restart to clear the loop state
        return restart_tank(tank_name)
    
    elif issue_type == 'NO_THINKING':
        # May be normal during baseline, check and restart if needed
        return restart_tank(tank_name)
    
    elif issue_type == 'HALLUCINATION':
        # This is critical - flag but don't auto-fix
        return False  # Escalate
    
    elif issue_type == 'ERRORS':
        # Restart usually fixes transient errors
        return restart_tank(tank_name)
    
    elif issue_type == 'NO_LOGS':
        return restart_tank(tank_name)
    
    return False


def escalate(tank_name, issues):
    """Record an escalation for human review"""
    escalation = {
        'timestamp': datetime.now().isoformat(),
        'tank': tank_name,
        'issues': issues,
        'status': 'OPEN'
    }
    
    # Load existing escalations
    escalations = []
    if ESCALATION_FILE.exists():
        try:
            escalations = json.loads(ESCALATION_FILE.read_text())
        except:
            escalations = []
    
    escalations.append(escalation)
    
    # Keep last 100 escalations
    escalations = escalations[-100:]
    
    ESCALATION_FILE.write_text(json.dumps(escalations, indent=2))
    log(f"🚨 ESCALATED: {tank_name} - {[i['type'] for i in issues]}", 'ESCALATE')


def save_status(status_data):
    """Save current status to file"""
    status_data['last_update'] = datetime.now().isoformat()
    STATUS_FILE.write_text(json.dumps(status_data, indent=2))


def run_check():
    """Run a full check of all tanks"""
    status = {
        'tanks': {},
        'healthy': 0,
        'issues': 0,
        'actions_taken': []
    }
    
    for tank in TANKS:
        issues = diagnose_tank(tank)
        
        if not issues:
            status['tanks'][tank] = {'status': 'HEALTHY', 'issues': []}
            status['healthy'] += 1
        else:
            status['tanks'][tank] = {'status': 'ISSUES', 'issues': issues}
            status['issues'] += 1
            
            # Handle each issue
            for issue in issues:
                if issue['severity'] == 'CRITICAL':
                    resolved = handle_issue(tank, issue)
                    status['actions_taken'].append({
                        'tank': tank,
                        'issue': issue['type'],
                        'resolved': resolved
                    })
                    
                    if not resolved:
                        escalate(tank, issues)
                        break
    
    save_status(status)
    return status


def run_daemon():
    """Run the caretaker as a continuous daemon"""
    log("=" * 60, 'INFO')
    log("Digiquarium Caretaker v1.0 starting...", 'INFO')
    log(f"Monitoring {len(TANKS)} tanks", 'INFO')
    log(f"Check interval: {CHECK_INTERVAL}s", 'INFO')
    log(f"Loop threshold: {LOOP_THRESHOLD}", 'INFO')
    log("=" * 60, 'INFO')
    
    while True:
        try:
            log("Running health check...", 'INFO')
            status = run_check()
            
            log(f"Check complete: {status['healthy']} healthy, {status['issues']} with issues", 'INFO')
            
            if status['actions_taken']:
                for action in status['actions_taken']:
                    log(f"Action: {action['tank']} - {action['issue']} - {'✅' if action['resolved'] else '❌'}", 'ACTION')
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("Caretaker shutting down...", 'INFO')
            break
        except Exception as e:
            log(f"Error in check loop: {e}", 'ERROR')
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        # Single check mode
        status = run_check()
        print(json.dumps(status, indent=2))
    else:
        # Daemon mode
        run_daemon()
