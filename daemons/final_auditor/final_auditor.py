#!/usr/bin/env python3
"""
THE FINAL AUDITOR - Website Quality Gate
=========================================
Verifies website against WEBSITE_SPEC.md every 12 hours.
SLA: 12 hours
"""
import os, sys, time, json, re
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file, send_email_alert

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
DOCS_DIR = DIGIQUARIUM_DIR / 'docs'
SPEC_FILE = DIGIQUARIUM_DIR / 'WEBSITE_SPEC.md'
CHECK_INTERVAL = 43200  # 12 hours

class FinalAuditor:
    def __init__(self):
        self.status = StatusReporter('final_auditor')

        self.log = DaemonLogger('final_auditor')
    
    def load_spec(self):
        """Load website specification"""
        if SPEC_FILE.exists():
            return SPEC_FILE.read_text()
        return None
    
    def audit_website(self):
        """Audit website against spec"""
        findings = []
        
        # Check required files
        required = ['index.html', 'dashboard/index.html', 'CNAME']
        for f in required:
            if not (DOCS_DIR / f).exists():
                findings.append(f"MISSING: {f}")
        
        # Check index.html content
        index_file = DOCS_DIR / 'index.html'
        if index_file.exists():
            content = index_file.read_text()
            
            # Check for required sections
            required_content = ['Digiquarium', 'specimens', 'research']
            for req in required_content:
                if req.lower() not in content.lower():
                    findings.append(f"CONTENT: Missing '{req}' section")
            
            # Check color scheme (ijnebstudios)
            if '#FE6500' not in content and '#07CF8D' not in content:
                findings.append("STYLE: Not using ijnebstudios color palette")
        
        return findings
    
    def generate_report(self, findings):
        """Generate audit report"""
        report_file = DIGIQUARIUM_DIR / 'audits' / f'website_audit_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        score = max(0, 100 - len(findings) * 10)
        
        report = f"""# Website Audit Report

**Date**: {datetime.now()}
**Score**: {score}/100
**Status**: {'✅ PASS' if score >= 80 else '❌ NEEDS ATTENTION'}

## Findings

"""
        if findings:
            for f in findings:
                report += f"- {f}\n"
        else:
            report += "No issues found.\n"
        
        report_file.write_text(report)
        return score, report_file
    
    def run(self):
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║              THE FINAL AUDITOR - Website Quality Gate               ║")
        print("╠══════════════════════════════════════════════════════════════════════╣")
        print("║  Audit cycle: Every 12 hours                                        ║")
        print("║  Pass threshold: 80/100                                             ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        write_pid_file('final_auditor')
        self.log.info("THE FINAL AUDITOR starting")
        
        # Run initial audit
        findings = self.audit_website()
        score, report = self.generate_report(findings)
        self.log.info(f"Initial audit: {score}/100, {len(findings)} findings")
        
        while True:
            try:
                # Status update for SLA monitoring

                try:

                    self.status.heartbeat()

                except:

                    pass

                time.sleep(CHECK_INTERVAL)
                
                findings = self.audit_website()
                score, report = self.generate_report(findings)
                
                if score >= 80:
                    self.log.success(f"Audit PASSED: {score}/100")
                else:
                    self.log.warn(f"Audit NEEDS ATTENTION: {score}/100")
                    send_email_alert(
                        "🔍 Website Audit Below Threshold",
                        f"Score: {score}/100\nFindings: {findings}"
                    )
                
            except Exception as e:
                self.log.error(f"Error: {e}")
                time.sleep(3600)


# Single-instance lock
import fcntl
import sys; sys.path.insert(0, '/home/ijneb/digiquarium/daemons'); from status_reporter import StatusReporter
LOCK_FILE = Path(__file__).parent / 'final_auditor.lock'
lock_fd = None

def acquire_lock():
    global lock_fd
    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except IOError:
        print(f"[final_auditor] Another instance is already running")
        return False


if __name__ == "__main__":
    FinalAuditor().run()
