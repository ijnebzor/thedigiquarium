#!/usr/bin/env python3
"""
Admin Status Generator
======================
Generates real-time status JSON for the admin panel.
Run periodically by THE SCHEDULER or as a standalone daemon.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'
OUTPUT_FILE = DIGIQUARIUM_DIR / 'docs' / 'data' / 'admin-status.json'

def run_cmd(cmd, timeout=10):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except:
        return ""

def check_daemon_status():
    """Check status of all daemons"""
    daemons = {}
    daemon_names = ['overseer', 'ollama_watcher', 'caretaker', 'maintainer', 
                    'guard', 'scheduler', 'sentinel', 'psych']
    
    for name in daemon_names:
        count = run_cmd(f"ps aux | grep '{name}.py' | grep -v grep | wc -l")
        try:
            count = int(count)
        except:
            count = 0
        
        daemons[name] = {
            'running': count > 0,
            'count': count,
            'healthy': count == 1
        }
    
    return daemons

def check_ollama_status():
    """Check Ollama at all levels"""
    status = {
        'windows_healthy': False,
        'proxy_healthy': False,
        'e2e_healthy': False,
        'models': 0
    }
    
    # Windows host
    try:
        import urllib.request
        with urllib.request.urlopen('http://192.168.50.94:11434/api/tags', timeout=5) as r:
            data = json.loads(r.read())
            status['windows_healthy'] = True
            status['models'] = len(data.get('models', []))
    except:
        pass
    
    # Proxy container
    proxy_status = run_cmd("docker ps --filter 'name=digiquarium-ollama' --format '{{.Status}}'")
    status['proxy_healthy'] = 'Up' in proxy_status
    
    # E2E test
    e2e = run_cmd("docker exec tank-01-adam python3 -c \"import urllib.request; urllib.request.urlopen('http://digiquarium-ollama:11434/api/tags', timeout=10); print('OK')\" 2>/dev/null")
    status['e2e_healthy'] = 'OK' in e2e
    
    return status

def check_containers():
    """Check Docker container status"""
    output = run_cmd("docker ps --format '{{.Names}}' | wc -l")
    try:
        total = int(output)
    except:
        total = 0
    
    return {'total': total}

def check_tanks():
    """Check tank status and recent activity"""
    tanks_running = run_cmd("docker ps --format '{{.Names}}' | grep 'tank-' | wc -l")
    try:
        tanks_running = int(tanks_running)
    except:
        tanks_running = 0
    
    # Get today's traces
    today = datetime.now().strftime('%Y-%m-%d')
    traces_today = 0
    activity = []
    
    tank_dirs = sorted(LOGS_DIR.glob('tank-*'))[:5]  # First 5 tanks
    
    for tank_dir in tank_dirs:
        tank_name = tank_dir.name
        trace_file = tank_dir / 'thinking_traces' / f'{today}.jsonl'
        
        if trace_file.exists():
            # Count traces
            with open(trace_file) as f:
                lines = f.readlines()
                count = len(lines)
                traces_today += count
                
                # Get last article
                if lines:
                    try:
                        last = json.loads(lines[-1])
                        activity.append({
                            'name': tank_name,
                            'article': last.get('article', '--'),
                            'traces': count
                        })
                    except:
                        activity.append({'name': tank_name, 'article': '--', 'traces': count})
        else:
            activity.append({'name': tank_name, 'article': '--', 'traces': 0})
    
    return {
        'running': tanks_running,
        'traces_today': traces_today,
        'activity': activity
    }

def check_network():
    """Check network isolation"""
    result = run_cmd("docker exec tank-01-adam python3 -c \"import urllib.request; urllib.request.urlopen('http://google.com', timeout=5); print('BAD')\" 2>/dev/null")
    isolated = 'BAD' not in result
    return {'isolated': isolated}

def get_overseer_status():
    """Get OVERSEER status from its status file"""
    status_file = DAEMONS_DIR / 'overseer' / 'status.json'
    
    result = {
        'running': False,
        'last_audit_healthy': None,
        'active_incidents': 0,
        'auto_remediations': 0
    }
    
    # Check if running
    count = run_cmd("ps aux | grep 'overseer.py' | grep -v grep | wc -l")
    result['running'] = count.strip() == '1'
    
    # Read status file
    if status_file.exists():
        try:
            data = json.loads(status_file.read_text())
            result['last_audit_healthy'] = data.get('last_full_audit', {}).get('overall_healthy')
            result['active_incidents'] = len(data.get('active_incidents', {}))
            result['auto_remediations'] = data.get('stats', {}).get('auto_remediations', 0)
        except:
            pass
    
    return result

def get_recent_logs():
    """Get recent OVERSEER log lines"""
    log_file = DAEMONS_DIR / 'logs' / 'overseer.log'
    
    if not log_file.exists():
        return []
    
    try:
        with open(log_file) as f:
            lines = f.readlines()[-20:]  # Last 20 lines
            return [line.strip() for line in lines if line.strip()]
    except:
        return []

def generate_status():
    """Generate full status JSON"""
    status = {
        'timestamp': datetime.now().isoformat(),
        'overall_healthy': True,
        'ollama': check_ollama_status(),
        'daemons': check_daemon_status(),
        'containers': check_containers(),
        'tanks': check_tanks(),
        'network': check_network(),
        'overseer': get_overseer_status(),
        'logs': get_recent_logs()
    }
    
    # Determine overall health
    unhealthy_reasons = []
    
    if not status['ollama']['e2e_healthy']:
        unhealthy_reasons.append('Ollama E2E failed')
    
    for name, daemon in status['daemons'].items():
        if not daemon['healthy']:
            unhealthy_reasons.append(f'{name} unhealthy')
    
    if not status['network']['isolated']:
        unhealthy_reasons.append('Network not isolated')
    
    status['overall_healthy'] = len(unhealthy_reasons) == 0
    status['issues'] = unhealthy_reasons
    
    return status

def main():
    status = generate_status()
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Write status file
    OUTPUT_FILE.write_text(json.dumps(status, indent=2))
    
    print(f"Status written to {OUTPUT_FILE}")
    print(f"Overall healthy: {status['overall_healthy']}")
    if status['issues']:
        print(f"Issues: {status['issues']}")

if __name__ == '__main__':
    main()
