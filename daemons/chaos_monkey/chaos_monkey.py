#!/usr/bin/env python3
"""
THE CHAOS MONKEY v1.0 - Resilience Testing Daemon
Intentionally breaks things to verify self-healing works.
"""
import os, sys, time, json, random, subprocess, fcntl
from datetime import datetime
from pathlib import Path

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
CHAOS_DIR = DIGIQUARIUM_DIR / 'daemons' / 'chaos_monkey'
KILL_FILE = CHAOS_DIR / 'DISABLE_CHAOS'
LOCK_FILE = CHAOS_DIR / 'chaos_monkey.lock'

CHECK_INTERVAL = 300
MIN_CHAOS_INTERVAL = 3600
RECOVERY_TIMEOUT = 600
SAFE_HOURS_START = 9
SAFE_HOURS_END = 17

KILLABLE_DAEMONS = ['guard', 'scheduler', 'sentinel', 'psych', 'webmaster']
KILLABLE_CONTAINERS = ['digiquarium-ollama']

def acquire_lock():
    try:
        fd = open(LOCK_FILE, 'w')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        print("[CHAOS_MONKEY] Another instance already running")
        sys.exit(1)

class ChaosMonkey:
    def __init__(self):
        self.status = StatusReporter('chaos_monkey')

        self.last_chaos = None
        self.events_log = CHAOS_DIR / 'events.jsonl'
        self.stats_file = CHAOS_DIR / 'stats.json'
        self.load_stats()
    
    def load_stats(self):
        if self.stats_file.exists():
            self.stats = json.loads(self.stats_file.read_text())
        else:
            self.stats = {'total_events': 0, 'successful_recoveries': 0, 'failed_recoveries': 0, 'avg_recovery_time': 0}
    
    def save_stats(self):
        self.stats_file.write_text(json.dumps(self.stats, indent=2))
    
    def log_event(self, event):
        event['timestamp'] = datetime.now().isoformat()
        with open(self.events_log, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def is_chaos_allowed(self):
        if KILL_FILE.exists():
            return False, "Disabled via kill file"
        now = datetime.now()
        if now.weekday() < 5 and SAFE_HOURS_START <= now.hour < SAFE_HOURS_END:
            return False, "Safe hours"
        if self.last_chaos:
            elapsed = (now - self.last_chaos).total_seconds()
            if elapsed < MIN_CHAOS_INTERVAL:
                return False, f"Cooldown"
        return True, "Allowed"
    
    def run_cmd(self, cmd):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout
        except:
            return False, ""
    
    def verify_recovery(self, target, is_container, timeout=RECOVERY_TIMEOUT):
        start = time.time()
        while time.time() - start < timeout:
            if is_container:
                ok, out = self.run_cmd(f"docker ps --filter 'name={target}' --format '{{{{.Status}}}}'")
                if ok and 'Up' in out:
                    return True, time.time() - start
            else:
                ok, out = self.run_cmd(f"ps aux | grep '{target}.py' | grep -v grep | wc -l")
                if ok and out.strip() == '1':
                    return True, time.time() - start
            # Status update for SLA monitoring

            try:

                self.status.heartbeat()

            except:

                pass

            time.sleep(10)
        return False, timeout
    
    def execute_chaos(self):
        target_type = random.choice(['daemon', 'container'])
        if target_type == 'daemon':
            target = random.choice(KILLABLE_DAEMONS)
            print(f"🐵 CHAOS: Killing {target} daemon")
            self.run_cmd(f"pkill -9 -f '{target}.py'")
            recovered, recovery_time = self.verify_recovery(target, False)
        else:
            target = random.choice(KILLABLE_CONTAINERS)
            print(f"🐵 CHAOS: Killing {target} container")
            self.run_cmd(f"docker rm -f {target}")
            recovered, recovery_time = self.verify_recovery(target, True)
        
        self.log_event({'type': target_type, 'target': target, 'recovered': recovered, 'recovery_time': recovery_time})
        self.stats['total_events'] += 1
        if recovered:
            self.stats['successful_recoveries'] += 1
            print(f"🐵 PASSED: {target} recovered in {recovery_time:.1f}s")
        else:
            self.stats['failed_recoveries'] += 1
            print(f"🐵 FAILED: {target} did NOT recover")
        self.save_stats()
        self.last_chaos = datetime.now()
    
    def run(self):
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║          THE CHAOS MONKEY v1.0 - Resilience Testing                 ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        print(f"Safe hours: {SAFE_HOURS_START}:00-{SAFE_HOURS_END}:00 weekdays")
        print(f"Min interval: {MIN_CHAOS_INTERVAL/60:.0f} minutes")
        
        while True:
            try:
                allowed, reason = self.is_chaos_allowed()
                if allowed and random.randint(1, 12) == 1:
                    self.execute_chaos()
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    CHAOS_DIR.mkdir(parents=True, exist_ok=True)
    lock_fd = acquire_lock()
    ChaosMonkey().run()
