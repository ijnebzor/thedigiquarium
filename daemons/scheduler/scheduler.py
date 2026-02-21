#!/usr/bin/env python3
"""
THE SCHEDULER v2.0 - Task Orchestration
========================================
Manages baseline schedules, daily summaries, task queues.
SLA: 30 min detection, 30 min remediation
"""
import os, sys, time, json
from datetime import datetime, timedelta
from pathlib import Path

# Single-instance lock (added by THE STRATEGIST)
import fcntl
LOCK_FILE = Path(__file__).parent / 'scheduler.lock'
def _acquire_lock():
    try:
        fd = open(LOCK_FILE, 'w')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        print("[scheduler] Another instance already running")
        import sys; sys.exit(1)
_lock_fd = _acquire_lock()

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
CHECK_INTERVAL = 1800  # 30 minutes

class Scheduler:
    def __init__(self):
        self.log = DaemonLogger('scheduler')
        self.schedule_file = DIGIQUARIUM_DIR / 'daemons' / 'scheduler' / 'schedule.json'
        self.load_schedule()
    
    def load_schedule(self):
        if self.schedule_file.exists():
            self.schedule = json.loads(self.schedule_file.read_text())
        else:
            self.schedule = {
                'baseline_interval_hours': 12,
                'last_baseline_run': None,
                'daily_summary_hour': 23,
                'last_daily_summary': None
            }
            self.save_schedule()
    
    def save_schedule(self):
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        self.schedule_file.write_text(json.dumps(self.schedule, indent=2))
    
    def should_run_baselines(self):
        if not self.schedule['last_baseline_run']:
            return True
        last = datetime.fromisoformat(self.schedule['last_baseline_run'])
        hours = (datetime.now() - last).total_seconds() / 3600
        return hours >= self.schedule['baseline_interval_hours']
    
    def queue_baselines(self):
        self.log.action("Queueing baseline assessments")
        queue_file = DIGIQUARIUM_DIR / 'daemons' / 'scheduler' / 'baseline_queue.json'
        tanks = [f'tank-{i:02d}' for i in range(1, 18)]
        queue_file.write_text(json.dumps(tanks))
        self.schedule['last_baseline_run'] = datetime.now().isoformat()
        self.save_schedule()
    
    def run(self):
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║              THE SCHEDULER v2.0 - Task Orchestration                 ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        write_pid_file('scheduler')
        self.log.info("THE SCHEDULER v2 starting")
        
        while True:
            try:
                if self.should_run_baselines():
                    self.queue_baselines()
                self.log.info("Schedule check complete")
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                self.log.error(f"Error: {e}")
                time.sleep(300)

if __name__ == '__main__':
    Scheduler().run()
