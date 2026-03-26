"""
Daemon utilities - logging, process management, alerting, SLA tracking
"""

import os
import json
import subprocess
import smtplib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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

    def success(self, message: str, extra: Dict = None):
        self._write_log("SUCCESS", message, extra)

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


def send_email_alert(subject: str, body: str, to: str = 'benjiz@gmail.com') -> bool:
    """
    Send email alert via SMTP if configured, otherwise log to file.
    
    Args:
        subject: Email subject line
        body: Email body text
        to: Recipient email address (default: benjiz@gmail.com)
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    log = DaemonLogger('email_alert')
    
    # Get SMTP configuration from environment variables
    smtp_host = os.environ.get('SMTP_HOST')
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_from = os.environ.get('SMTP_FROM', smtp_user)
    
    # Check if SMTP is configured
    if smtp_host and smtp_user and smtp_password:
        try:
            # Send email via SMTP with STARTTLS
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            
            # Create email message
            message = MIMEMultipart()
            message['From'] = smtp_from if smtp_from else smtp_user
            message['To'] = to
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            # Send email
            server.send_message(message)
            server.quit()
            
            log.success(f"Email sent to {to}: {subject}")
            
            # Also log to file as backup record
            _log_email_to_file(to, subject, body)
            
            return True
            
        except Exception as e:
            # SMTP sending failed, log error and fall back to file logging
            log.error(f"SMTP email send failed: {str(e)}")
            _log_email_to_file(to, subject, body)
            return False
    else:
        # SMTP not configured, log warning and fall back to file logging
        warning_msg = f"EMAIL ALERT NOT SENT - SMTP not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD env vars. Subject: {subject}"
        log.warn(warning_msg)
        _log_email_to_file(to, subject, body)
        return False


def _log_email_to_file(to: str, subject: str, body: str):
    """Write email alert to file as backup record"""
    daemons_dir = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')) / 'daemons'
    log_file = daemons_dir / 'logs' / 'email_alerts.log'
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\nTO: {to}\nSUBJECT: {subject}\nTIME: {datetime.now().isoformat()}\n{body}\n{'='*60}\n")


# SLA Configuration
SLA_CONFIG = {
    'overseer': {'max_downtime_minutes': 30, 'detection_interval_seconds': 60},
    'scheduler': {'max_downtime_minutes': 30, 'detection_interval_seconds': 60},
    'maintainer': {'max_downtime_minutes': 60, 'detection_interval_seconds': 120},
    'ollama_watcher': {'max_downtime_minutes': 15, 'detection_interval_seconds': 30},
    'caretaker': {'max_downtime_minutes': 45, 'detection_interval_seconds': 90},
}
