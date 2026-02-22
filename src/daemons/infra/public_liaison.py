#!/usr/bin/env python3
"""
THE PUBLIC LIAISON v1.0 - External Communications Coordinator
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
"""

import json
from datetime import datetime
from pathlib import Path

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')

class PublicLiaison:
    def __init__(self):
        self.inbox_dir = DIGIQUARIUM_DIR / 'comms' / 'inbox'
        self.outbox_dir = DIGIQUARIUM_DIR / 'comms' / 'outbox'
        self.log_file = DIGIQUARIUM_DIR / 'daemons' / 'public_liaison' / 'activity.log'
        
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
    
    def log(self, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        print(f"[PUBLIC LIAISON] {message}")
    
    def route_inquiry(self, subject: str, body: str) -> list:
        """Determine which daemons to consult based on content"""
        content = (subject + ' ' + body).lower()
        
        consultants = set()
        for keyword, daemons in self.routing_rules.items():
            if keyword.lower() in content:
                consultants.update(daemons)
        
        if not consultants:
            return ['independent']  # Can handle alone
        
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
        
        consult_dir = DIGIQUARIUM_DIR / 'comms' / 'consultations'
        consult_dir.mkdir(parents=True, exist_ok=True)
        
        with open(consult_dir / f'{inquiry_id}.json', 'w') as f:
            json.dump(request, f, indent=2)
        
        self.log(f"Consultation request created: {inquiry_id}")
        self.log(f"Consulting: {', '.join(consultants)}")
        
        return request
    
    def draft_response(self, inquiry_id: str, consultation_inputs: dict) -> str:
        """Draft response incorporating consultation inputs"""
        # This would synthesize inputs from consulted daemons
        # For now, returns template
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


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║        THE PUBLIC LIAISON v1.0 - External Communications            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    liaison = PublicLiaison()
    liaison.log("THE PUBLIC LIAISON initialized")
    liaison.log("Monitoring: research@digiquarium.org")
    liaison.log("Ready to coordinate with specialist daemons")


if __name__ == '__main__':
    main()
