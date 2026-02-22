#!/usr/bin/env python3
"""
THE WEBMASTER v4.0 - Site Infrastructure + Auto-Publishing
============================================================
Now actually pushes to GitHub! SLA: 15 minutes

Responsibilities:
1. Prune logs and publish clean data
2. Validate all internal links
3. Auto-commit and push to GitHub
4. Update site with fresh data
5. Verify consistency across pages

Created: 2026-02-18
Updated: 2026-02-22 v4.0 - Auto-push capability
"""

import os
import sys
import time
import json
import subprocess
import fcntl
from datetime import datetime, timedelta
from pathlib import Path

# Single-instance lock
DAEMON_DIR = Path('/home/ijneb/digiquarium/daemons/webmaster')
LOCK_FILE = DAEMON_DIR / 'webmaster.lock'

def acquire_lock():
    try:
        fd = open(LOCK_FILE, 'w')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        print("[WEBMASTER] Another instance already running")
        sys.exit(1)

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
DOCS_DIR = DIGIQUARIUM_DIR / 'docs'
PUBLIC_LOGS_DIR = DOCS_DIR / 'data' / 'logs-public'

# SLA: 15 minutes
CHECK_INTERVAL = 900  # 15 minutes
RETENTION_DAYS = 7

class Webmaster:
    def __init__(self):
        self.last_push = None
        self.changes_pending = False
        PUBLIC_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    def log(self, level, msg):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        symbols = {'info': 'ℹ️', 'success': '✅', 'warn': '⚠️', 'error': '❌'}
        print(f"{timestamp} {symbols.get(level, 'ℹ️')} [WEBMASTER] {msg}")
    
    def run_git(self, *args) -> tuple[bool, str]:
        """Run a git command"""
        try:
            result = subprocess.run(
                ['git', '-C', str(DIGIQUARIUM_DIR)] + list(args),
                capture_output=True, text=True, timeout=60
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def prune_and_publish_logs(self) -> tuple[int, int, int]:
        """Prune junk entries and publish clean logs"""
        self.log('info', 'Starting log pruning and publishing')
        
        total_kept = 0
        total_pruned = 0
        tanks_processed = 0
        
        # Process each tank
        for tank_dir in sorted(LOGS_DIR.glob('tank-*')):
            tank_name = tank_dir.name
            traces_dir = tank_dir / 'thinking_traces'
            
            if not traces_dir.exists():
                continue
            
            tanks_processed += 1
            output_dir = PUBLIC_LOGS_DIR / tank_name
            output_dir.mkdir(exist_ok=True)
            
            # Get recent files (retention period)
            cutoff_date = (datetime.now() - timedelta(days=RETENTION_DAYS)).strftime('%Y-%m-%d')
            
            for trace_file in sorted(traces_dir.glob('*.jsonl')):
                if trace_file.stem < cutoff_date:
                    continue
                
                kept = []
                pruned = 0
                
                try:
                    with open(trace_file) as f:
                        for line in f:
                            if not line.strip():
                                pruned += 1
                                continue
                            
                            try:
                                entry = json.loads(line)
                                
                                # Prune criteria
                                thoughts = entry.get('thoughts', '')
                                article = entry.get('article', '')
                                
                                if not thoughts or thoughts == 'null' or thoughts.strip() == '':
                                    pruned += 1
                                    continue
                                if 'timeout' in thoughts.lower() or 'error' in thoughts.lower():
                                    pruned += 1
                                    continue
                                if not article:
                                    pruned += 1
                                    continue
                                if len(thoughts) < 50:  # Too short to be meaningful
                                    pruned += 1
                                    continue
                                
                                # Truncate thoughts for public view (first 500 chars)
                                entry['thoughts'] = thoughts[:500] + ('...' if len(thoughts) > 500 else '')
                                kept.append(json.dumps(entry))
                                
                            except json.JSONDecodeError:
                                pruned += 1
                                continue
                    
                    # Write clean file
                    if kept:
                        output_file = output_dir / trace_file.name
                        output_file.write_text('\n'.join(kept))
                    
                    total_kept += len(kept)
                    total_pruned += pruned
                    
                except Exception as e:
                    self.log('error', f'Error processing {trace_file}: {e}')
        
        # Write summary
        summary = {
            'last_updated': datetime.now().isoformat(),
            'tanks_processed': tanks_processed,
            'entries_published': total_kept,
            'entries_pruned': total_pruned,
            'prune_criteria': [
                'null thoughts (LLM not responding)',
                'empty thoughts',
                'timeout entries',
                'error entries',
                'missing article',
                'malformed JSON',
                'too short (<50 chars)'
            ],
            'retention': f'{RETENTION_DAYS} days of logs'
        }
        (PUBLIC_LOGS_DIR / 'summary.json').write_text(json.dumps(summary, indent=2))
        
        self.log('success', f'Log publishing complete: {tanks_processed} tanks, {total_kept} entries kept, {total_pruned} entries pruned')
        self.changes_pending = True
        
        return tanks_processed, total_kept, total_pruned
    
    def update_admin_status(self):
        """Update the admin status file"""
        try:
            subprocess.run(
                ['python3', str(DIGIQUARIUM_DIR / 'daemons' / 'admin_status_generator.py')],
                capture_output=True, timeout=60
            )
            self.log('info', 'Updated admin status')
            self.changes_pending = True
        except Exception as e:
            self.log('error', f'Failed to update admin status: {e}')
    
    def push_to_github(self):
        """Commit and push changes to GitHub"""
        if not self.changes_pending:
            self.log('info', 'No changes to push')
            return True
        
        self.log('info', 'Pushing changes to GitHub...')
        
        # Add all changes
        success, output = self.run_git('add', '-A')
        if not success:
            self.log('error', f'Git add failed: {output}')
            return False
        
        # Check if there are changes to commit
        success, output = self.run_git('status', '--porcelain')
        if not output.strip():
            self.log('info', 'No changes to commit')
            self.changes_pending = False
            return True
        
        # Commit
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        commit_msg = f'🤖 Auto-update: {timestamp} | THE WEBMASTER'
        success, output = self.run_git('commit', '-m', commit_msg)
        if not success and 'nothing to commit' not in output:
            self.log('error', f'Git commit failed: {output}')
            return False
        
        # Push
        success, output = self.run_git('push')
        if not success:
            self.log('error', f'Git push failed: {output}')
            return False
        
        self.log('success', 'Pushed to GitHub')
        self.changes_pending = False
        self.last_push = datetime.now()
        return True
    
    def validate_links(self):
        """Check for broken internal links"""
        broken = []
        
        for html_file in DOCS_DIR.rglob('*.html'):
            try:
                content = html_file.read_text()
                
                # Find relative hrefs
                import re
                hrefs = re.findall(r'href="([^"]*)"', content)
                
                for href in hrefs:
                    if href.startswith('http') or href.startswith('#') or href.startswith('mailto'):
                        continue
                    
                    # Resolve relative path
                    if href.startswith('./'):
                        target = html_file.parent / href[2:]
                    elif href.startswith('../'):
                        target = html_file.parent.parent / href[3:]
                    else:
                        target = html_file.parent / href
                    
                    # Check if exists (handle directories with index.html)
                    if target.suffix == '':
                        target = target / 'index.html'
                    
                    if not target.exists() and not (target.parent / 'index.html').exists():
                        broken.append((html_file.relative_to(DOCS_DIR), href))
                        
            except Exception as e:
                continue
        
        if broken:
            self.log('warn', f'Found {len(broken)} broken links')
            for file, href in broken[:5]:
                self.log('warn', f'  {file} -> {href}')
        else:
            self.log('success', 'All internal links valid')
        
        return broken
    

    def run_broadcaster(self):
        """Run THE BROADCASTER to update live feed"""
        try:
            import subprocess
            result = subprocess.run(
                ['python3', '/home/ijneb/digiquarium/daemons/webmaster/broadcaster.py'],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                self.log('success', 'Broadcaster updated live feed')
                self.changes_pending = True
            else:
                self.log('error', f'Broadcaster failed: {result.stderr[:100]}')
        except Exception as e:
            self.log('error', f'Broadcaster error: {e}')

    def run(self):
        """Main daemon loop"""
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║          THE WEBMASTER v4.0 - Auto-Publishing Enabled               ║")
        print("║          SLA: 15 minutes | Now pushes to GitHub!                    ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        
        cycle = 0
        
        while True:
            try:
                cycle += 1
                self.log('info', f'Starting cycle {cycle}')
                
                # 1. Prune and publish logs
                self.prune_and_publish_logs()
                
                # 2. Run broadcaster for live feed
                self.run_broadcaster()
                
                # 3. Update admin status
                self.update_admin_status()
                
                # 4. Validate links
                self.validate_links()
                
                # 5. Push to GitHub
                self.push_to_github()
                
                self.log('info', f'Cycle {cycle} complete. Next in {CHECK_INTERVAL//60} minutes')
                
            except Exception as e:
                self.log('error', f'Cycle error: {e}')
            
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    DAEMON_DIR.mkdir(parents=True, exist_ok=True)
    lock_fd = acquire_lock()
    Webmaster().run()
