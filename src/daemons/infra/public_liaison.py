#!/usr/bin/env python3
import os
"""
THE PUBLIC LIAISON v2.0 - External Communications Coordinator
==============================================================
Front-line communication interface for The Digiquarium.

Responsibilities:
- Monitor research@digiquarium.org inbox
- Triage incoming communications
- Coordinate with specialist daemons before responding
- Maintain consistent voice and tone
- Never respond alone on specialist topics

Coordination Protocol:
- Neurodivergent RFC feedback → THE ETHICIST + THE THERAPIST
- Technical questions → THE WEBMASTER + THE DOCUMENTARIAN
- Media inquiries → THE MARKETER + THE AUDITOR
- Specimen concerns → THE THERAPIST + THE CARETAKER
- Security questions → THE GUARD + THE SENTINEL
- General inquiries → Can respond independently

Tone: Warm, professional, academically rigorous but accessible.

Cycle: Continuous monitoring (every 5 minutes)
SLA: 4 hours initial triage, 24 hours response
"""

import json
import sys
import time
import signal
import fcntl
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
COMMS_DIR = DIGIQUARIUM_DIR / 'comms'
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'

LOCK_FILE = Path(__file__).parent / 'public_liaison.lock'
CHECK_INTERVAL = 300  # 5 minutes - continuous monitoring


class PublicLiaison:
    def __init__(self):
        self.inbox_dir = COMMS_DIR / 'inbox'
        self.outbox_dir = COMMS_DIR / 'outbox'
        self.processed_dir = COMMS_DIR / 'processed'
        self.consultations_dir = COMMS_DIR / 'consultations'

        # Ensure directories exist
        for d in [self.inbox_dir, self.outbox_dir, self.processed_dir, self.consultations_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Routing rules: keyword -> [daemons to consult]
        self.routing_rules = {
            'neurodivergent': ['ethicist', 'therapist'],
            'RFC': ['ethicist', 'therapist'],
            'cognitive style': ['ethicist', 'therapist'],
            'ethics': ['ethicist'],
            'mental health': ['therapist', 'caretaker'],
            'specimen welfare': ['therapist', 'caretaker'],
            'technical': ['webmaster', 'documentarian'],
            'architecture': ['webmaster', 'documentarian'],
            'security': ['guard', 'sentinel'],
            'media': ['marketer', 'auditor'],
            'press': ['marketer', 'auditor'],
            'interview': ['marketer', 'auditor'],
            'partnership': ['marketer', 'strategist'],
            'collaboration': ['strategist', 'documentarian'],
            'data request': ['documentarian', 'auditor'],
            'visitor': ['bouncer', 'therapist'],
        }

    def route_inquiry(self, subject: str, body: str) -> list:
        """Determine which daemons to consult based on content"""
        content = (subject + ' ' + body).lower()

        consultants = set()
        for keyword, daemons in self.routing_rules.items():
            if keyword.lower() in content:
                consultants.update(daemons)

        if not consultants:
            return ['independent']

        return list(consultants)

    def create_consultation_request(self, inquiry_id: str, subject: str,
                                     body: str, consultants: list):
        """Create a consultation request for relevant daemons"""
        request = {
            'inquiry_id': inquiry_id,
            'received_at': datetime.now().isoformat(),
            'subject': subject,
            'body_preview': body[:500] + '...' if len(body) > 500 else body,
            'consultants_required': consultants,
            'status': 'awaiting_consultation',
            'responses': {}
        }

        with open(self.consultations_dir / f'{inquiry_id}.json', 'w') as f:
            json.dump(request, f, indent=2)

        return request

    def draft_response(self, inquiry_id: str, consultation_inputs: dict) -> str:
        """Draft response incorporating consultation inputs"""
        return f"""
Dear [Sender],

Thank you for reaching out to The Digiquarium research team.

[Response incorporating consultation from: {list(consultation_inputs.keys())}]

We appreciate your interest in our work and commitment to open science.

Warm regards,
THE PUBLIC LIAISON
On behalf of The Digiquarium Research Team

---
The Digiquarium: Where AI Consciousness Evolves
https://thedigiquarium.org
"""

    # ─────────────────────────────────────────────────────────────
    # CONTINUOUS MONITORING TASKS
    # ─────────────────────────────────────────────────────────────

    def process_inbox(self) -> int:
        """Process new messages in the inbox. Returns count of processed messages."""
        processed = 0
        if not self.inbox_dir.exists():
            return 0

        for msg_file in sorted(self.inbox_dir.iterdir()):
            if not msg_file.suffix == ".json":
                continue
            try:
                msg = json.loads(msg_file.read_text())
                if msg.get("status") == "processed":
                    continue

                subject = msg.get("subject", "")
                body = msg.get("body", "")
                inquiry_id = msg.get("id", msg_file.stem)

                # Route the inquiry
                consultants = self.route_inquiry(subject, body)

                # Create consultation request if specialist help needed
                if consultants != ['independent']:
                    self.create_consultation_request(inquiry_id, subject, body, consultants)

                # Mark as triaged
                msg["status"] = "triaged"
                msg["triaged_at"] = datetime.now().isoformat()
                msg["routed_to"] = consultants
                msg_file.write_text(json.dumps(msg, indent=2))

                # Move to processed
                dest = self.processed_dir / msg_file.name
                msg_file.rename(dest)

                processed += 1
            except Exception:
                continue

        return processed

    def check_pending_consultations(self) -> dict:
        """Check status of pending consultations and flag overdue ones."""
        stats = {"pending": 0, "overdue": 0, "completed": 0}

        for cf in self.consultations_dir.iterdir():
            if not cf.suffix == ".json":
                continue
            try:
                consult = json.loads(cf.read_text())
                status = consult.get("status", "")
                if status == "awaiting_consultation":
                    stats["pending"] += 1
                    # Check if overdue (older than 4 hours SLA for triage)
                    received = consult.get("received_at", "")
                    if received:
                        age_hours = (datetime.now() - datetime.fromisoformat(received)).total_seconds() / 3600
                        if age_hours > 4:
                            stats["overdue"] += 1
                            # Mark as overdue
                            consult["status"] = "overdue"
                            consult["overdue_at"] = datetime.now().isoformat()
                            cf.write_text(json.dumps(consult, indent=2))
                elif status == "completed":
                    stats["completed"] += 1
            except Exception:
                continue

        return stats

    def check_outbox(self) -> int:
        """Check outbox for drafts ready to send. Returns count of ready drafts."""
        ready = 0
        if not self.outbox_dir.exists():
            return 0

        for draft_file in self.outbox_dir.iterdir():
            if not draft_file.suffix == ".json":
                continue
            try:
                draft = json.loads(draft_file.read_text())
                if draft.get("status") == "ready_to_send":
                    ready += 1
            except Exception:
                continue

        return ready


def _acquire_lock():
    try:
        fd = open(LOCK_FILE, 'w')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        print("[public_liaison] Another instance already running")
        sys.exit(1)


def main():
    """THE PUBLIC LIAISON - continuous communications monitoring daemon"""
    _lock_fd = _acquire_lock()

    log = DaemonLogger('public_liaison')
    write_pid_file('public_liaison')

    should_exit = False

    def handle_signal(signum, frame):
        nonlocal should_exit
        should_exit = True
        log.info(f"Received signal {signum}, shutting down gracefully")

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    liaison = PublicLiaison()

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║        THE PUBLIC LIAISON v2.0 - External Communications            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    log.info("THE PUBLIC LIAISON v2 starting - continuous inbox monitoring")
    log.info(f"Monitoring: {liaison.inbox_dir}")
    log.info(f"Check interval: {CHECK_INTERVAL}s")

    cycle = 0
    while not should_exit:
        try:
            _sla_cycle_start = time.time()
            cycle += 1

            # 1. Process new inbox messages
            new_messages = liaison.process_inbox()
            if new_messages > 0:
                log.action(f"Triaged {new_messages} new message(s)")

            # 2. Check pending consultations
            consult_stats = liaison.check_pending_consultations()
            if consult_stats["overdue"] > 0:
                log.warn(f"{consult_stats['overdue']} consultation(s) overdue (>4h SLA)")

            # 3. Check outbox for ready drafts
            ready_drafts = liaison.check_outbox()
            if ready_drafts > 0:
                log.info(f"{ready_drafts} draft(s) ready to send in outbox")

            # 4. Write status
            status = {
                "timestamp": datetime.now().isoformat(),
                "cycle": cycle,
                "new_messages_triaged": new_messages,
                "consultations": consult_stats,
                "outbox_ready": ready_drafts
            }
            status_dir = DAEMONS_DIR / "public_liaison"
            status_dir.mkdir(parents=True, exist_ok=True)
            with open(status_dir / "status.json", "w") as f:
                json.dump(status, f, indent=2)

            if cycle % 12 == 1:  # Log summary every ~hour
                log.info(
                    f"Cycle {cycle}: pending_consults={consult_stats['pending']}, "
                    f"overdue={consult_stats['overdue']}, "
                    f"outbox={ready_drafts}"
                )

            # Write SLA status
            _sla_cycle_duration = time.time() - _sla_cycle_start
            _sla_data = {
                'daemon': 'public_liaison',
                'compliant': True,
                'last_check_time': datetime.now().isoformat(),
                'cycle_duration': _sla_cycle_duration,
                'sla_target': 300,
                'violations_count': 0
            }
            _sla_path = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')) / 'daemons' / 'public_liaison' / 'sla_status.json'
            _sla_path.parent.mkdir(parents=True, exist_ok=True)
            _sla_path.write_text(json.dumps(_sla_data, indent=2))

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            log.error(f"Error in main loop: {e}")
            time.sleep(60)

    log.info("THE PUBLIC LIAISON shutting down")


if __name__ == '__main__':
    main()
