#!/usr/bin/env python3
"""
DIGIQUARIUM ORCHESTRATOR - Agent Coordinator
=============================================

Manages and coordinates all operational agents:
- Caretaker (functional monitoring)
- Guard (security monitoring)
- Scheduler (calendar/baselines)
- Translator (language processing)

Spawns and monitors all daemon agents.
"""

import os
import sys
import json
import time
import subprocess
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
OPS_DIR = DIGIQUARIUM_DIR / 'operations'
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'

# Agent definitions
AGENTS = {
    'caretaker': {
        'name': 'The Caretaker',
        'script': DIGIQUARIUM_DIR / 'caretaker' / 'caretaker_v2.py',
        'pid_file': DIGIQUARIUM_DIR / 'caretaker' / 'caretaker.pid',
        'log_file': LOGS_DIR / 'caretaker' / 'caretaker_daemon.log',
        'description': 'Functional monitoring and maintenance',
        'critical': True
    },
    'guard': {
        'name': 'The Guard',
        'script': DIGIQUARIUM_DIR / 'guard' / 'guard.py',
        'pid_file': DIGIQUARIUM_DIR / 'guard' / 'guard.pid',
        'log_file': LOGS_DIR / 'guard' / 'guard_daemon.log',
        'description': 'Security monitoring (OWASP compliance)',
        'critical': True
    },
    'scheduler': {
        'name': 'The Scheduler',
        'script': OPS_DIR / 'scheduler.py',
        'pid_file': OPS_DIR / 'scheduler.pid',
        'log_file': OPS_DIR / 'scheduler.log',
        'description': 'Calendar and task coordination',
        'critical': True
    },
    'translator': {
        'name': 'The Translator',
        'script': OPS_DIR / 'agents' / 'translator.py',
        'pid_file': OPS_DIR / 'agents' / 'translator.pid',
        'log_file': OPS_DIR / 'translations' / 'translator.log',
        'description': 'Language content processing',
        'critical': False
    }
}


def log_event(message: str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [ORCHESTRATOR] {message}")
    
    log_file = OPS_DIR / 'orchestrator.log'
    with open(log_file, 'a') as f:
        f.write(f"{timestamp} - {message}\n")


def is_agent_running(agent_id: str) -> bool:
    """Check if an agent is running"""
    agent = AGENTS[agent_id]
    pid_file = agent['pid_file']
    
    if not pid_file.exists():
        return False
    
    try:
        pid = int(pid_file.read_text().strip())
        # Check if process exists
        os.kill(pid, 0)
        return True
    except (ValueError, OSError, ProcessLookupError):
        return False


def start_agent(agent_id: str) -> bool:
    """Start an agent daemon"""
    agent = AGENTS[agent_id]
    
    if is_agent_running(agent_id):
        log_event(f"{agent['name']} already running")
        return True
    
    log_event(f"Starting {agent['name']}...")
    
    # Ensure log directory exists
    agent['log_file'].parent.mkdir(parents=True, exist_ok=True)
    
    # Start the agent
    cmd = f"nohup python3 {agent['script']} >> {agent['log_file']} 2>&1 &"
    subprocess.Popen(cmd, shell=True)
    
    # Wait a moment for the process to start
    time.sleep(2)
    
    # Get the PID
    result = subprocess.run(
        f"pgrep -f '{agent['script']}'",
        shell=True, capture_output=True, text=True
    )
    
    if result.returncode == 0 and result.stdout.strip():
        pid = result.stdout.strip().split('\n')[0]
        agent['pid_file'].write_text(pid)
        log_event(f"{agent['name']} started (PID: {pid})")
        return True
    else:
        log_event(f"Failed to start {agent['name']}")
        return False


def stop_agent(agent_id: str) -> bool:
    """Stop an agent daemon"""
    agent = AGENTS[agent_id]
    
    if not is_agent_running(agent_id):
        log_event(f"{agent['name']} not running")
        return True
    
    try:
        pid = int(agent['pid_file'].read_text().strip())
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        
        # Force kill if still running
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        
        agent['pid_file'].unlink(missing_ok=True)
        log_event(f"{agent['name']} stopped")
        return True
    except Exception as e:
        log_event(f"Error stopping {agent['name']}: {e}")
        return False


def restart_agent(agent_id: str) -> bool:
    """Restart an agent"""
    stop_agent(agent_id)
    time.sleep(1)
    return start_agent(agent_id)


def get_status() -> Dict:
    """Get status of all agents"""
    status = {}
    for agent_id, agent in AGENTS.items():
        running = is_agent_running(agent_id)
        pid = None
        if running:
            try:
                pid = int(agent['pid_file'].read_text().strip())
            except:
                pass
        
        status[agent_id] = {
            'name': agent['name'],
            'running': running,
            'pid': pid,
            'description': agent['description'],
            'critical': agent['critical']
        }
    return status


def print_status():
    """Print formatted status"""
    print("\n" + "="*60)
    print("DIGIQUARIUM OPERATIONS TEAM STATUS")
    print("="*60 + "\n")
    
    status = get_status()
    for agent_id, info in status.items():
        icon = "🟢" if info['running'] else "🔴"
        pid_str = f"(PID: {info['pid']})" if info['pid'] else "(not running)"
        critical = "⭐" if info['critical'] else ""
        print(f"  {icon} {info['name']} {critical}")
        print(f"     {info['description']}")
        print(f"     Status: {'Running' if info['running'] else 'Stopped'} {pid_str}")
        print()


def start_all():
    """Start all agents"""
    log_event("Starting all agents...")
    for agent_id in AGENTS:
        start_agent(agent_id)
    print_status()


def stop_all():
    """Stop all agents"""
    log_event("Stopping all agents...")
    for agent_id in AGENTS:
        stop_agent(agent_id)


def monitor_loop():
    """Monitor agents and restart if needed"""
    log_event("Orchestrator monitoring started")
    
    while True:
        try:
            for agent_id, agent in AGENTS.items():
                if agent['critical'] and not is_agent_running(agent_id):
                    log_event(f"ALERT: {agent['name']} not running - restarting")
                    start_agent(agent_id)
            
            time.sleep(60)  # Check every minute
            
        except KeyboardInterrupt:
            log_event("Orchestrator stopped by user")
            break
        except Exception as e:
            log_event(f"Error: {e}")
            time.sleep(30)


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           🎭 DIGIQUARIUM ORCHESTRATOR - Agent Coordinator 🎭         ║
╠══════════════════════════════════════════════════════════════════════╣
║  Agents: Caretaker, Guard, Scheduler, Translator                    ║
║  Mode: Supervision and auto-restart for critical agents              ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) < 2:
        print("Usage: orchestrator.py [start|stop|restart|status|monitor]")
        print_status()
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == 'start':
        if len(sys.argv) > 2:
            agent_id = sys.argv[2]
            if agent_id in AGENTS:
                start_agent(agent_id)
            else:
                print(f"Unknown agent: {agent_id}")
        else:
            start_all()
    
    elif command == 'stop':
        if len(sys.argv) > 2:
            agent_id = sys.argv[2]
            if agent_id in AGENTS:
                stop_agent(agent_id)
            else:
                print(f"Unknown agent: {agent_id}")
        else:
            stop_all()
    
    elif command == 'restart':
        if len(sys.argv) > 2:
            agent_id = sys.argv[2]
            if agent_id in AGENTS:
                restart_agent(agent_id)
            else:
                print(f"Unknown agent: {agent_id}")
        else:
            stop_all()
            time.sleep(2)
            start_all()
    
    elif command == 'status':
        print_status()
    
    elif command == 'monitor':
        start_all()
        monitor_loop()
    
    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()

# Add new agents to the AGENTS dictionary
AGENTS['documentarian'] = {
    'name': 'The Documentarian',
    'script': OPS_DIR / 'agents' / 'documentarian.py',
    'pid_file': OPS_DIR / 'agents' / 'documentarian.pid',
    'log_file': DOCS_DIR / 'academic' / 'documentarian.log',
    'description': 'Academic documentation and paper maintenance',
    'critical': False
}

AGENTS['webmaster'] = {
    'name': 'The Webmaster',
    'script': OPS_DIR / 'agents' / 'webmaster.py',
    'pid_file': OPS_DIR / 'agents' / 'webmaster.pid',
    'log_file': WEBSITE_DIR / 'webmaster.log',
    'description': 'Website and open-source infrastructure',
    'critical': False
}
