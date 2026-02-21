"""
Shared Escalation Utility
=========================
Provides standard escalation mechanism for all daemons.
All daemons can now escalate issues to THE OVERSEER.
"""

import json
from datetime import datetime
from pathlib import Path

OVERSEER_INBOX = Path('/home/ijneb/digiquarium/daemons/overseer/inbox')


def escalate_to_overseer(daemon_name: str, message: str, severity: str = 'high', 
                         context: dict = None):
    """
    Escalate an issue to THE OVERSEER.
    
    Args:
        daemon_name: Name of the daemon raising the issue
        message: Description of the issue
        severity: 'critical', 'high', 'medium', 'low'
        context: Additional context (logs, stats, etc.)
    """
    OVERSEER_INBOX.mkdir(parents=True, exist_ok=True)
    
    issue = {
        'from': daemon_name,
        'timestamp': datetime.now().isoformat(),
        'message': message,
        'severity': severity,
        'context': context or {}
    }
    
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{daemon_name}.json"
    (OVERSEER_INBOX / filename).write_text(json.dumps(issue, indent=2))
    
    return filename


def check_sla_breach(daemon_name: str, metric: str, threshold_minutes: int, 
                     last_success_time: datetime) -> bool:
    """
    Check if an SLA has been breached and escalate if so.
    
    Returns True if breached.
    """
    from datetime import datetime, timedelta
    
    now = datetime.now()
    elapsed = (now - last_success_time).total_seconds() / 60
    
    if elapsed > threshold_minutes:
        escalate_to_overseer(
            daemon_name,
            f'SLA breach: {metric} has not succeeded in {elapsed:.0f} minutes (threshold: {threshold_minutes}min)',
            severity='high',
            context={'metric': metric, 'elapsed_minutes': elapsed, 'threshold_minutes': threshold_minutes}
        )
        return True
    
    return False
