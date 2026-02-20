#!/usr/bin/env python3
"""
SITE UPDATER - Keeps the website in sync with live data
=========================================================
- Updates paper stats every 30 minutes
- Copies stream files to docs for GitHub Pages
- Updates Genesis section data
- Runs as part of the operations team
"""

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import time

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
WEBSITE_DIR = DIGIQUARIUM_DIR / 'website'
DOCS_DIR = DIGIQUARIUM_DIR / 'docs'

def sync_streams():
    """Copy stream files to docs for GitHub Pages"""
    src = WEBSITE_DIR / 'streams'
    dst = DOCS_DIR / 'streams'
    dst.mkdir(parents=True, exist_ok=True)
    
    for f in src.glob('*.json'):
        shutil.copy2(f, dst / f.name)
    
    print(f"[SITE_UPDATER] Synced {len(list(src.glob('*.json')))} stream files")


def update_paper_stats():
    """Run paper generator"""
    try:
        subprocess.run([
            'python3', 
            str(DIGIQUARIUM_DIR / 'operations' / 'agents' / 'paper_generator.py')
        ], capture_output=True, timeout=60)
        print("[SITE_UPDATER] Updated paper stats")
    except Exception as e:
        print(f"[SITE_UPDATER] Paper update error: {e}")


def git_push_if_changed():
    """Commit and push if there are changes"""
    try:
        # Check for changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, cwd=DIGIQUARIUM_DIR
        )
        
        if result.stdout.strip():
            # There are changes
            subprocess.run(['git', 'add', 'docs/'], cwd=DIGIQUARIUM_DIR)
            subprocess.run([
                'git', 'commit', '-m', 
                f'📊 Auto-update: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            ], cwd=DIGIQUARIUM_DIR, capture_output=True)
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=DIGIQUARIUM_DIR, capture_output=True)
            print("[SITE_UPDATER] Pushed updates to GitHub")
        else:
            print("[SITE_UPDATER] No changes to push")
    except Exception as e:
        print(f"[SITE_UPDATER] Git error: {e}")


def run_update_cycle():
    """Run a complete update cycle"""
    print(f"[SITE_UPDATER] Starting update cycle at {datetime.now()}")
    
    sync_streams()
    update_paper_stats()
    git_push_if_changed()
    
    print(f"[SITE_UPDATER] Cycle complete")


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║            🔄 SITE UPDATER - Auto-sync website data 🔄               ║
╠══════════════════════════════════════════════════════════════════════╣
║  Syncs streams, updates paper stats, pushes to GitHub                ║
║  Cycle: Every 30 minutes                                             ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    # Initial run
    run_update_cycle()
    
    # Continuous operation
    while True:
        try:
            time.sleep(30 * 60)  # 30 minutes
            run_update_cycle()
        except KeyboardInterrupt:
            print("[SITE_UPDATER] Stopped")
            break
        except Exception as e:
            print(f"[SITE_UPDATER] Error: {e}")
            time.sleep(5 * 60)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        run_update_cycle()
    else:
        main()
