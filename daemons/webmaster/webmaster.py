#!/usr/bin/env python3
"""
THE WEBMASTER v3.0 - Website Infrastructure & Log Publishing
=============================================================
Maintains website, validates links, publishes clean logs to public view.

Responsibilities:
1. Website health checks (file existence, content validation)
2. Link validation (detect 404s, broken internal links)
3. LOG PRUNING - Remove junk data (timeouts, null thoughts) from public logs
4. Publish clean logs to /docs/data/logs-public/
5. Coordinate with Final Auditor

SLA: 30 min for health checks, 1 hour for log publishing

Created: Original
Updated: 2026-02-22 - Added log pruning per Benji's instruction (02:59 Feb 21)
"""

import os
import sys
import time
import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.daemon_base import DaemonBase
from shared.utils import DaemonLogger

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
DOCS_DIR = DIGIQUARIUM_DIR / 'docs'
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
PUBLIC_LOGS_DIR = DOCS_DIR / 'data' / 'logs-public'
CHECK_INTERVAL = 1800  # 30 minutes
LOG_PUBLISH_INTERVAL = 3600  # 1 hour


class Webmaster(DaemonBase):
    def __init__(self):
        super().__init__('webmaster')
        self.log = DaemonLogger('webmaster')
        self.last_log_publish = None
        
        # Ensure public logs directory exists
        PUBLIC_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # LOG PRUNING & PUBLISHING (Per Benji's instruction 02:59 Feb 21)
    # =========================================================================
    
    def prune_and_publish_logs(self):
        """
        Prune junk data from logs and publish clean versions publicly.
        
        Removes:
        - Entries with null thoughts (LLM not responding)
        - Timeout entries
        - Error entries
        - Malformed JSON
        
        Keeps:
        - Entries with real thoughts
        - Valid navigation data
        """
        self.log.info("Starting log pruning and publishing")
        
        tanks_processed = 0
        entries_kept = 0
        entries_pruned = 0
        
        # Process each tank's logs
        for tank_dir in sorted(LOGS_DIR.glob('tank-*')):
            tank_name = tank_dir.name
            traces_dir = tank_dir / 'thinking_traces'
            
            if not traces_dir.exists():
                continue
            
            # Create public directory for this tank
            public_tank_dir = PUBLIC_LOGS_DIR / tank_name
            public_tank_dir.mkdir(parents=True, exist_ok=True)
            
            # Process recent trace files (last 7 days)
            for trace_file in sorted(traces_dir.glob('*.jsonl'))[-7:]:
                clean_entries = []
                
                try:
                    with open(trace_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            
                            try:
                                entry = json.loads(line)
                                
                                # PRUNE CONDITIONS
                                should_prune = False
                                
                                # Prune null thoughts
                                if entry.get('thoughts') is None:
                                    should_prune = True
                                
                                # Prune empty thoughts
                                if entry.get('thoughts') == '':
                                    should_prune = True
                                
                                # Prune timeout entries
                                if 'timeout' in str(entry).lower():
                                    should_prune = True
                                
                                # Prune error entries
                                if 'error' in str(entry).lower():
                                    should_prune = True
                                
                                # Prune entries without article
                                if not entry.get('article'):
                                    should_prune = True
                                
                                if should_prune:
                                    entries_pruned += 1
                                else:
                                    # Sanitize entry for public view
                                    clean_entry = {
                                        'timestamp': entry.get('timestamp'),
                                        'tank': entry.get('tank'),
                                        'article': entry.get('article'),
                                        'thoughts': entry.get('thoughts', '')[:500],  # Truncate long thoughts
                                        'next': entry.get('next'),
                                        'language': entry.get('language', 'english')
                                    }
                                    clean_entries.append(clean_entry)
                                    entries_kept += 1
                                    
                            except json.JSONDecodeError:
                                entries_pruned += 1  # Malformed JSON
                
                except Exception as e:
                    self.log.error(f"Error processing {trace_file}: {e}")
                    continue
                
                # Write clean entries to public directory
                if clean_entries:
                    public_file = public_tank_dir / trace_file.name
                    with open(public_file, 'w') as f:
                        for entry in clean_entries:
                            f.write(json.dumps(entry) + '\n')
            
            tanks_processed += 1
        
        self.log.success(
            f"Log publishing complete: {tanks_processed} tanks, "
            f"{entries_kept} entries kept, {entries_pruned} entries pruned"
        )
        
        # Update summary file
        self.update_public_summary(tanks_processed, entries_kept, entries_pruned)
        
        return tanks_processed, entries_kept, entries_pruned
    
    def update_public_summary(self, tanks: int, kept: int, pruned: int):
        """Update public summary JSON"""
        summary = {
            'last_updated': datetime.now().isoformat(),
            'tanks_processed': tanks,
            'entries_published': kept,
            'entries_pruned': pruned,
            'prune_criteria': [
                'null thoughts (LLM not responding)',
                'empty thoughts',
                'timeout entries',
                'error entries',
                'missing article',
                'malformed JSON'
            ],
            'retention': '7 days of logs'
        }
        
        summary_file = PUBLIC_LOGS_DIR / 'summary.json'
        summary_file.write_text(json.dumps(summary, indent=2))
    
    # =========================================================================
    # LINK VALIDATION
    # =========================================================================
    
    def validate_links(self):
        """Check all internal links for 404s"""
        self.log.info("Validating internal links")
        
        broken_links = []
        href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        
        for html_file in DOCS_DIR.rglob('*.html'):
            try:
                content = html_file.read_text(errors='ignore')
                hrefs = href_pattern.findall(content)
                
                for link in hrefs:
                    # Skip external, anchors, javascript, mailto
                    if any(link.startswith(x) for x in ['http', '#', 'javascript:', 'mailto:', 'data:']):
                        continue
                    
                    # Resolve relative path
                    if link.startswith('/'):
                        target = DOCS_DIR / link.lstrip('/')
                    else:
                        target = html_file.parent / link
                    
                    # Remove query strings and anchors
                    target_str = str(target).split('?')[0].split('#')[0]
                    target = Path(target_str)
                    
                    # Check if exists (file or directory with index.html)
                    if not target.exists():
                        if not (target.parent / 'index.html').exists():
                            broken_links.append({
                                'file': str(html_file.relative_to(DOCS_DIR)),
                                'link': link
                            })
            except Exception as e:
                self.log.error(f"Error checking {html_file}: {e}")
        
        if broken_links:
            self.log.warn(f"Found {len(broken_links)} broken internal links")
            # Write report
            report_file = DIGIQUARIUM_DIR / 'audits' / f'broken_links_{datetime.now().strftime("%Y%m%d")}.json'
            report_file.parent.mkdir(exist_ok=True)
            report_file.write_text(json.dumps(broken_links, indent=2))
        else:
            self.log.info("All internal links valid")
        
        return broken_links
    
    # =========================================================================
    # WEBSITE HEALTH
    # =========================================================================
    
    def check_website_health(self):
        """Verify website files exist and are valid"""
        required_files = [
            'index.html',
            'dashboard/index.html',
            'admin/index.html',
            'research/index.html',
            'specimens/index.html'
        ]
        
        missing = []
        for f in required_files:
            if not (DOCS_DIR / f).exists():
                missing.append(f)
        
        if missing:
            self.log.warn(f"Missing files: {missing}")
            return False, missing
        
        self.log.info("Website health OK")
        return True, []
    
    # =========================================================================
    # MAIN LOOP
    # =========================================================================
    
    def run(self):
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║        THE WEBMASTER v3.0 - Website & Log Publishing                ║")
        print("║        Now with: Log pruning, link validation, public logs          ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        
        self.log.info("THE WEBMASTER v3.0 starting")
        self.log.info("Log pruning enabled per Benji's instruction (02:59 Feb 21)")
        
        cycle = 0
        
        while self.running:
            try:
                cycle += 1
                
                # Health check every cycle
                self.check_website_health()
                
                # Link validation every 6 hours (cycle % 12)
                if cycle % 12 == 1:
                    self.validate_links()
                
                # Log pruning and publishing every hour
                now = datetime.now()
                if self.last_log_publish is None or (now - self.last_log_publish).seconds >= LOG_PUBLISH_INTERVAL:
                    self.prune_and_publish_logs()
                    self.last_log_publish = now
                
            except Exception as e:
                self.log.error(f"Cycle error: {e}")
            
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    webmaster = Webmaster()
    webmaster.start()
