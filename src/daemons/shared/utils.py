"""
Daemon utilities - logging, process management, alerting, SLA tracking
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class DaemonLogger:
    """Structured logging for daemons"""

    def __init__(self, daemon_name: str):
        self.daemon_name = daemon_name
        self.log_dir = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')) / 'daemons' / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"{daemon_name}.jsonl"

    def _write_log(self, level: str, message: str, extra: Dict = None):
        """Write structured log entry"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'daemon': self.daemon_name,
            'level': level,
            'message': message,
        }
        if extra:
            entry.update(extra)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        print(f"[{self.daemon_name}] {level}: {message}")

    def info(self, message: str, extra: Dict = None):
        self._write_log('INFO', message, extra)

    def error(self, message: str, extra: Dict = None):
        self._write_log('ERROR', message, extra)

    def action(self, message: str, extra: Dict = None):
        self._write_log('ACTION', message, extra)

    def warn(self, message: str, extra: Dict = None):
        self._write_log('WARN', message, extra)


def run_command(cmd: str, timeout: int = 30) -> tuple:
    """Run shell command and return (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(cmd, shell=True, timeout=timeout, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, '', 'Timeout'
    except Exception as e:
        return 1, '', str(e)


def write_pid_file(daemon_name: str):
    """Write PID file for daemon"""
    daemons_dir = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')) / 'daemons'
    pid_file = daemons_dir / f"{daemon_name}.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()))


def read_pid_file(daemon_name: str) -> Optional[int]:
    """Read PID from file"""
    daemons_dir = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')) / 'daemons'
    pid_file = daemons_dir / f"{daemon_name}.pid"
    if pid_file.exists():
        try:
            return int(pid_file.read_text().strip())
        except:
            return None
    return None


def is_daemon_running(daemon_name: str) -> bool:
    """Check if daemon is currently running"""
    pid = read_pid_file(daemon_name)
    if pid is None:
        return False
    returncode, _, _ = run_command(f"kill -0 {pid} 2>/dev/null")
    return returncode == 0


def send_email_alert(subject: str, body: str, to: str = None):
    """Send email alert (placeholder for integration)"""
    log = DaemonLogger('email_alert')
    log.warn(f"Alert: {subject}")
    # In production, integrate with mail service


# SLA Configuration
SLA_CONFIG = {
    'overseer': {'max_downtime_minutes': 30, 'detection_interval_seconds': 60},
    'scheduler': {'max_downtime_minutes': 30, 'detection_interval_seconds': 60},
    'maintainer': {'max_downtime_minutes': 60, 'detection_interval_seconds': 120},
    'ollama_watcher': {'max_downtime_minutes': 15, 'detection_interval_seconds': 30},
    'caretaker': {'max_downtime_minutes': 45, 'detection_interval_seconds': 90},
}
