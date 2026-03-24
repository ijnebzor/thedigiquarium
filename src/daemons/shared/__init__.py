"""
Daemon Shared Infrastructure
Provides base classes, utilities, and escalation handling for all daemons
"""

from .daemon_base import DaemonBase
from .escalation import escalate_to_overseer, check_sla_breach
from .utils import DaemonLogger, run_command, send_email_alert, write_pid_file, read_pid_file, is_daemon_running

__all__ = [
    'DaemonBase',
    'escalate_to_overseer',
    'check_sla_breach',
    'DaemonLogger',
    'run_command',
    'send_email_alert',
    'write_pid_file',
    'read_pid_file',
    'is_daemon_running',
]
