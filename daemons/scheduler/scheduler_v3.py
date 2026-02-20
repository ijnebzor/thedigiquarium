#!/usr/bin/env python3
"""
THE SCHEDULER v3.0 - Task Orchestration with Broadcast Coordination
====================================================================
Manages baseline schedules, coordinates with BROADCASTER for live feeds.

12-Hour Cycle:
1. [H+0:00] Queue baseline assessments
2. [H+0:00 to H+2:00] Baselines run (managed by tanks)
3. [H+2:30] Broadcast window opens
4. [H+2:30] THE BROADCASTER exports live feed
5. [H+2:35] Git commit triggers GitHub Pages deploy
6. [H+2:40] Dashboard shows "live" data (12hr delayed)

Coordination:
- Sets 'baseline_in_progress' flag during baselines
- Clears flag when baselines complete
- Triggers BROADCASTER 30 min after baselines
- BROADCASTER checks flag before exporting
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'
CHECK_INTERVAL = 1800  # 30 minutes

class SchedulerV3:
    def __init__(self):
        self.log = DaemonLogger('scheduler')
        self.status_file = DAEMONS_DIR / 'scheduler' / 'status.json'
        self.schedule_file = DAEMONS_DIR / 'scheduler' / 'schedule.json'
        self.load_state()
    
    def load_state(self):
        """Load scheduler state"""
        if self.schedule_file.exists():
            self.schedule = json.loads(self.schedule_file.read_text())
        else:
            self.schedule = {
                'baseline_interval_hours': 12,
                'last_baseline_run': None,
                'last_baseline_complete': None,
                'last_broadcast': None,
                'broadcast_delay_minutes': 30,  # After baseline completion
            }
        
        self.status = {
            'baseline_in_progress': False,
            'broadcast_pending': False,
            'last_check': None
        }
        self.save_state()
    
    def save_state(self):
        """Save current state"""
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        self.schedule_file.write_text(json.dumps(self.schedule, indent=2, default=str))
        
        self.status['last_check'] = datetime.now().isoformat()
        self.status_file.write_text(json.dumps(self.status, indent=2))
    
    def should_run_baselines(self) -> bool:
        """Check if it's time for baselines"""
        if not self.schedule['last_baseline_run']:
            return True
        
        last = datetime.fromisoformat(self.schedule['last_baseline_run'])
        hours = (datetime.now() - last).total_seconds() / 3600
        return hours >= self.schedule['baseline_interval_hours']
    
    def should_broadcast(self) -> bool:
        """Check if it's time to broadcast (30 min after baselines)"""
        if not self.schedule['last_baseline_complete']:
            return False
        
        last_complete = datetime.fromisoformat(self.schedule['last_baseline_complete'])
        last_broadcast = None
        
        if self.schedule['last_broadcast']:
            last_broadcast = datetime.fromisoformat(self.schedule['last_broadcast'])
        
        # Broadcast if:
        # 1. Baselines completed more than 30 min ago
        # 2. Haven't broadcast since baselines completed
        minutes_since_baseline = (datetime.now() - last_complete).total_seconds() / 60
        
        if minutes_since_baseline < self.schedule['broadcast_delay_minutes']:
            return False
        
        if last_broadcast and last_broadcast > last_complete:
            return False  # Already broadcast for this cycle
        
        return True
    
    def start_baselines(self):
        """Mark baselines as starting"""
        self.log.action("Starting baseline cycle")
        self.status['baseline_in_progress'] = True
        self.schedule['last_baseline_run'] = datetime.now().isoformat()
        self.save_state()
        
        # Queue baselines for all tanks
        queue_file = DAEMONS_DIR / 'scheduler' / 'baseline_queue.json'
        tanks = [f'tank-{i:02d}' for i in range(1, 18)]
        queue_file.write_text(json.dumps({
            'queued_at': datetime.now().isoformat(),
            'tanks': tanks,
            'status': 'pending'
        }, indent=2))
        
        self.log.info(f"Queued {len(tanks)} tanks for baseline")
    
    def check_baselines_complete(self) -> bool:
        """Check if baselines have completed (simplified check)"""
        # In production, this would check each tank's baseline status
        # For now, estimate 2 hours for all baselines to complete
        if not self.schedule['last_baseline_run']:
            return False
        
        last_run = datetime.fromisoformat(self.schedule['last_baseline_run'])
        hours = (datetime.now() - last_run).total_seconds() / 3600
        
        # Assume complete after 2 hours
        return hours >= 2
    
    def complete_baselines(self):
        """Mark baselines as complete"""
        self.log.success("Baseline cycle complete")
        self.status['baseline_in_progress'] = False
        self.status['broadcast_pending'] = True
        self.schedule['last_baseline_complete'] = datetime.now().isoformat()
        self.save_state()
    
    def trigger_broadcast(self):
        """Trigger THE BROADCASTER"""
        self.log.action("Triggering THE BROADCASTER")
        
        broadcaster_script = DAEMONS_DIR / 'webmaster' / 'broadcaster.py'
        
        if not broadcaster_script.exists():
            self.log.error("Broadcaster script not found")
            return False
        
        try:
            result = subprocess.run(
                ['python3', str(broadcaster_script)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.log.success("Broadcast complete")
                self.status['broadcast_pending'] = False
                self.schedule['last_broadcast'] = datetime.now().isoformat()
                self.save_state()
                return True
            else:
                self.log.error(f"Broadcast failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log.error("Broadcast timed out")
            return False
        except Exception as e:
            self.log.error(f"Broadcast error: {e}")
            return False
    
    def run_cycle(self):
        """Run one scheduler cycle"""
        self.log.info("Running scheduler cycle")
        
        # Check if baselines needed
        if self.should_run_baselines() and not self.status['baseline_in_progress']:
            self.start_baselines()
        
        # Check if baselines in progress have completed
        if self.status['baseline_in_progress']:
            if self.check_baselines_complete():
                self.complete_baselines()
        
        # Check if broadcast needed
        if self.should_broadcast():
            self.trigger_broadcast()
        
        self.save_state()
    
    def run(self):
        """Main daemon loop"""
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║          THE SCHEDULER v3.0 - With Broadcast Coordination           ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        
        write_pid_file('scheduler')
        self.log.info("THE SCHEDULER v3 starting")
        self.log.info(f"Baseline interval: {self.schedule['baseline_interval_hours']} hours")
        self.log.info(f"Broadcast delay: {self.schedule['broadcast_delay_minutes']} minutes after baselines")
        
        while True:
            try:
                self.run_cycle()
            except Exception as e:
                self.log.error(f"Cycle error: {e}")
            
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    SchedulerV3().run()
