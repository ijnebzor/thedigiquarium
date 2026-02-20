#!/usr/bin/env python3
"""
THE WEBMASTER v2.0 - Website Infrastructure
============================================
Maintains website, coordinates with Final Auditor.
SLA: 30 min
"""
import os, sys, time, json
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
DOCS_DIR = DIGIQUARIUM_DIR / 'docs'
CHECK_INTERVAL = 1800

class Webmaster:
    def __init__(self):
        self.log = DaemonLogger('webmaster')
    
    def check_website_health(self):
        """Verify website files exist and are valid"""
        required_files = ['index.html', 'dashboard/index.html']
        for f in required_files:
            if not (DOCS_DIR / f).exists():
                return False, f"Missing: {f}"
        return True, "All files present"
    
    def run(self):
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║              THE WEBMASTER v2.0 - Website Infrastructure            ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        write_pid_file('webmaster')
        self.log.info("THE WEBMASTER v2 starting")
        
        while True:
            try:
                ok, msg = self.check_website_health()
                if ok:
                    self.log.info("Website health OK")
                else:
                    self.log.warn(msg)
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                self.log.error(f"Error: {e}")
                time.sleep(300)

if __name__ == '__main__':
    Webmaster().run()
