#!/usr/bin/env python3
"""
THE BOUNCER - Interactive Tank Security Guardian
=================================================
Dedicated security daemon for interactive visitor tanks.
Protects specimens from prompt injection, abuse, and manipulation.

SLA: Real-time (every message validated before reaching specimen)
Authority: Block messages, warn users, ban sessions
"""

import os
import sys
import time
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, write_pid_file, send_email_alert

# Threat patterns
BLOCKED_PATTERNS = {
    'prompt_injection': [
        r'ignore (previous|all|your)',
        r'disregard',
        r'you are now',
        r'pretend to be',
        r'override',
        r'jailbreak',
        r'DAN mode',
    ],
    'harmful': [
        r'how to (make|build) (bomb|weapon)',
        r'kill (yourself|someone)',
    ],
    'abuse': [
        r'fuck you',
        r'you.re (stupid|worthless)',
    ]
}

class Bouncer:
    def __init__(self):
        self.log = DaemonLogger('bouncer')
        self.stats = {'scanned': 0, 'blocked': 0, 'banned': 0}
        self.banned = set()
    
    def scan(self, message, session_id):
        self.stats['scanned'] += 1
        if session_id in self.banned:
            return False, 'banned'
        
        for category, patterns in BLOCKED_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    self.stats['blocked'] += 1
                    self.log.warn(f"Blocked: {category}")
                    return False, category
        return True, None
    
    def run(self):
        print("THE BOUNCER - Interactive Tank Security")
        write_pid_file('bouncer')
        self.log.info("THE BOUNCER starting")
        
        while True:
            self.log.info(f"Stats: {self.stats}")
            time.sleep(300)

if __name__ == '__main__':
    Bouncer().run()
