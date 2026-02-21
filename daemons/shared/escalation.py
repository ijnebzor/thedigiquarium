#!/usr/bin/env python3
"""
Shared escalation utilities for all daemons.
All critical daemons can escalate to THE OVERSEER.
"""

import json
from datetime import datetime
from pathlib import Path

DAEMONS_DIR = Path('/home/ijneb/digiquarium/daemons')
OVERSEER_INBOX = DAEMONS_DIR / 'overseer' / 'inbox'

def escalate_to_overseer(daemon_name: str, message: str, severity: str = 'medium', details: dict = None):
    """
    Send an escalation to THE OVERSEER.
    
    Args:
        daemon_name: Name of the calling daemon
        message: Human-readable description of the issue
        severity: 'low', 'medium', 'high', or 'critical'
        details: Optional dict with additional context
    """
    OVERSEER_INBOX.mkdir(parents=True, exist_ok=True)
    
    issue = {
        'from': daemon_name,
        'timestamp': datetime.now().isoformat(),
        'severity': severity,
        'message': message,
        'details': details or {}
    }
    
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{daemon_name}.json"
    (OVERSEER_INBOX / filename).write_text(json.dumps(issue, indent=2))
    
    return filename


def check_sla_breach(daemon_name: str, metric: str, threshold_minutes: int, current_value: float) -> bool:
    """
    Check if an SLA has been breached.
    
    Args:
        daemon_name: Name of the checking daemon
        metric: What is being measured (e.g., 'detection_time', 'remediation_time')
        threshold_minutes: Maximum allowed minutes
        current_value: Current value in minutes
    
    Returns:
        True if SLA is breached (current > threshold)
    """
    if current_value > threshold_minutes:
        # SLA breached - escalate
        escalate_to_overseer(
            daemon_name,
            f"SLA BREACH: {metric} is {current_value:.1f} minutes (threshold: {threshold_minutes})",
            severity='high',
            details={'metric': metric, 'threshold': threshold_minutes, 'value': current_value}
        )
        return True
    return False
