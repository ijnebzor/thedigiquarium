#!/usr/bin/env python3
"""
Queue baselines for all tanks without overloading Ollama
Runs one baseline at a time, then starts exploration
"""

import subprocess
import time
import sys
from datetime import datetime

TANKS = [
    # Priority 1: Tanks that need fresh baselines (looping/stuck)
    ('tank-05-juan', 'languages'),
    ('tank-06-juanita', 'languages'),
    ('tank-09-wei', 'languages'),
    ('tank-10-mei', 'languages'),
    ('tank-11-haruki', 'languages'),
    ('tank-12-sakura', 'languages'),
    
    # Priority 2: Agent tanks
    ('tank-03-cain', 'agents'),
    ('tank-04-abel', 'agents'),
    ('tank-17-seth', 'agents'),
    
    # Priority 3: Control tanks (already have baselines, just restart)
    ('tank-01-adam', ''),
    ('tank-02-eve', ''),
    
    # Priority 4: German tanks
    ('tank-07-klaus', 'languages'),
    ('tank-08-genevieve', 'languages'),
    
    # Priority 5: Visual tanks
    ('tank-13-victor', 'visual'),
    ('tank-14-iris', 'visual'),
    
    # Priority 6: Special tanks
    ('tank-15-observer', 'special'),
    ('tank-16-seeker', 'special'),
]


def run(cmd):
    """Run command and return success status"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0


def log(msg):
    """Log with timestamp"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}")


def wait_for_baseline(tank_name, timeout=900):
    """Wait for baseline to complete (max 15 minutes)"""
    start = time.time()
    
    while time.time() - start < timeout:
        # Check logs for baseline completion
        result = subprocess.run(
            f"docker logs {tank_name} 2>&1 | tail -20",
            shell=True, capture_output=True, text=True
        )
        logs = result.stdout
        
        if "Baseline complete" in logs or "✅ Baseline saved" in logs:
            return True
        
        if "exploring" in logs.lower() or "📖" in logs:
            return True  # Already exploring (baseline was done)
        
        time.sleep(10)
    
    return False  # Timeout


def main():
    log("="*60)
    log("DIGIQUARIUM QUEUED BASELINE RUNNER")
    log("="*60)
    
    # First, stop all tanks
    log("Stopping all tanks...")
    for tank, _ in TANKS:
        run(f"docker stop {tank} 2>/dev/null")
        run(f"docker rm {tank} 2>/dev/null")
    
    log("All tanks stopped")
    time.sleep(5)
    
    # Process each tank
    for i, (tank, profile) in enumerate(TANKS, 1):
        log(f"\n[{i}/{len(TANKS)}] Processing {tank}...")
        
        # Start the tank
        if profile:
            cmd = f"cd /home/ijneb/digiquarium && docker compose --profile {profile} up -d {tank}"
        else:
            cmd = f"cd /home/ijneb/digiquarium && docker compose up -d {tank}"
        
        if not run(cmd):
            log(f"❌ Failed to start {tank}")
            continue
        
        log(f"Started {tank}, waiting for baseline...")
        
        # Wait for baseline
        time.sleep(10)  # Initial startup time
        
        if wait_for_baseline(tank):
            log(f"✅ {tank} baseline complete, moving to next...")
        else:
            log(f"⚠️ {tank} baseline timeout, continuing anyway...")
        
        # Small delay before next tank
        time.sleep(5)
    
    log("\n" + "="*60)
    log("QUEUED BASELINE COMPLETE")
    log("="*60)
    
    # Final status check
    log("\nFinal tank status:")
    result = subprocess.run(
        "docker ps --format '{{.Names}} {{.Status}}' | grep tank | sort",
        shell=True, capture_output=True, text=True
    )
    print(result.stdout)


if __name__ == '__main__':
    main()
