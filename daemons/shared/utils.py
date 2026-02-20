#!/usr/bin/env python3
"""Shared utilities for all daemons"""
import os, sys, json, time, subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
DAEMON_LOGS_DIR = DAEMONS_DIR / 'logs'
OWNER_EMAIL = 'benjiz@gmail.com'

SLA_CONFIG = {
    'maintainer': {'detection': 60, 'remediation': 300},
    'caretaker': {'detection': 300, 'remediation': 900},
    'guard': {'detection': 300, 'remediation': 900},
    'sentinel': {'detection': 300, 'remediation': 300},
    'scheduler': {'detection': 1800, 'remediation': 1800},
    'translator': {'detection': 1800, 'remediation': 1800},
    'documentarian': {'detection': 21600, 'remediation': 21600},
    'webmaster': {'detection': 1800, 'remediation': 1800},
    'ollama_watcher': {'detection': 300, 'remediation': 300},
    'final_auditor': {'detection': 43200, 'remediation': 43200},
}

class DaemonLogger:
    def __init__(self, name):
        self.name = name
        self.log_file = DAEMON_LOGS_DIR / f'{name}.log'
        DAEMON_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    def log(self, level, msg, ctx=None):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        icons = {'INFO':'ℹ️','WARN':'⚠️','ERROR':'❌','ACTION':'🔧','SUCCESS':'✅','CRITICAL':'🚨','HEARTBEAT':'💓'}
        line = f"{ts} {icons.get(level,'•')} [{self.name.upper()}] {f'[{ctx}] ' if ctx else ''}{msg}"
        print(line)
        with open(self.log_file, 'a') as f: f.write(line + '\n')
    
    def info(self, m, c=None): self.log('INFO', m, c)
    def warn(self, m, c=None): self.log('WARN', m, c)
    def error(self, m, c=None): self.log('ERROR', m, c)
    def action(self, m, c=None): self.log('ACTION', m, c)
    def success(self, m, c=None): self.log('SUCCESS', m, c)
    def critical(self, m, c=None): self.log('CRITICAL', m, c)

def run_command(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except: return -1, '', 'error'

def send_email_alert(subject, body, to=OWNER_EMAIL):
    log_file = DAEMON_LOGS_DIR / 'email_alerts.log'
    with open(log_file, 'a') as f:
        f.write(f"\n{'='*60}\nTO: {to}\nSUBJECT: {subject}\nTIME: {datetime.now()}\n{body}\n{'='*60}\n")
    return True

def write_pid_file(name, pid=None):
    if pid is None: pid = os.getpid()
    pf = DAEMONS_DIR / name / f'{name}.pid'
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(str(pid))

def read_pid_file(name):
    pf = DAEMONS_DIR / name / f'{name}.pid'
    if pf.exists():
        try: return int(pf.read_text().strip())
        except: return None
    return None

def is_daemon_running(name):
    pid = read_pid_file(name)
    if pid:
        try: os.kill(pid, 0); return True
        except: return False
    return False
