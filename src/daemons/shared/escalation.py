"""
Escalation handling - SLA breach detection and escalation to overseer
"""

import json
from datetime import datetime
from pathlib import Path
import os


def escalate_to_overseer(severity: str, issue_type: str, message: str, extra: dict = None):
    """Escalate an issue to the overseer for handling"""

    overseer_inbox = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')) / 'daemons' / 'overseer_inbox'
    overseer_inbox.mkdir(parents=True, exist_ok=True)

    escalation = {
        'timestamp': datetime.now().isoformat(),
        'severity': severity,  # 'critical', 'high', 'medium', 'low'
        'type': issue_type,
        'message': message,
    }

    if extra:
        escalation.update(extra)

    # Write as JSON to inbox
    filename = f"escalation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    escalation_file = overseer_inbox / filename

    with open(escalation_file, 'w', encoding='utf-8') as f:
        json.dump(escalation, f, indent=2, ensure_ascii=False)

    print(f"[escalation] {severity}: {issue_type} - {message}")


def check_sla_breach(daemon_name: str, last_heartbeat: datetime, max_downtime_minutes: int) -> bool:
    """Check if daemon has breached SLA"""
    if last_heartbeat is None:
        return True

    downtime = (datetime.now() - last_heartbeat).total_seconds() / 60
    if downtime > max_downtime_minutes:
        escalate_to_overseer(
            severity='critical',
            issue_type='SLA_BREACH',
            message=f"{daemon_name} has exceeded max downtime ({downtime:.1f}m > {max_downtime_minutes}m)",
            extra={'daemon': daemon_name, 'downtime_minutes': downtime}
        )
        return True
    return False
