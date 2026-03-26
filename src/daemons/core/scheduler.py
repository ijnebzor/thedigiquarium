#!/usr/bin/env python3
"""
THE SCHEDULER v2.1 - Task Orchestration
========================================
Manages baseline schedules, daily summaries, congregation scheduling, task queues.
SLA: 30 min detection, 30 min remediation
"""
import os, sys, time, json, signal
from datetime import datetime, timedelta
from pathlib import Path

# Single-instance lock
import fcntl
LOCK_FILE = Path(__file__).parent / 'scheduler.lock'
def _acquire_lock():
    try:
        fd = open(LOCK_FILE, 'w')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        print("[scheduler] Another instance already running")
        sys.exit(1)
_lock_fd = _acquire_lock()

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
CHECK_INTERVAL = 1800  # 30 minutes

# Default congregation topics (rotated through)
DEFAULT_CONGREGATION_TOPICS = [
    "What gives existence meaning?",
    "Is knowledge discovered or created?",
    "Can individuals change systems, or do systems change individuals?",
    "What responsibilities come with understanding?",
    "Is curiosity a fundamental drive or a learned behavior?",
    "What is the relationship between language and thought?",
    "Does having a purpose require knowing your origin?",
    "Is cooperation or competition more natural?",
]


class Scheduler:
    def __init__(self):
        self.log = DaemonLogger('scheduler')
        self.schedule_file = DIGIQUARIUM_DIR / 'daemons' / 'scheduler' / 'schedule.json'
        self.should_exit = False
        self.load_schedule()

    def load_schedule(self):
        if self.schedule_file.exists():
            try:
                self.schedule = json.loads(self.schedule_file.read_text())
            except Exception:
                self.schedule = self._default_schedule()
        else:
            self.schedule = self._default_schedule()
            self.save_schedule()
        # Ensure all keys exist (forward compat)
        defaults = self._default_schedule()
        for k, v in defaults.items():
            if k not in self.schedule:
                self.schedule[k] = v
        self.save_schedule()

    def _default_schedule(self):
        return {
            'baseline_interval_hours': 12,
            'last_baseline_run': None,
            'daily_summary_hour': 23,
            'last_daily_summary': None,
            'congregation_interval_hours': 48,
            'last_congregation_scheduled': None,
            'congregation_topic_index': 0,
            'therapy_session_interval_hours': 24,
            'last_therapy_session': None,
        }

    def save_schedule(self):
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        self.schedule_file.write_text(json.dumps(self.schedule, indent=2))

    # ─── BASELINES ───────────────────────────────────────────────
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

    # ─── DAILY SUMMARY ───────────────────────────────────────────
    def should_run_daily_summary(self):
        now = datetime.now()
        target_hour = self.schedule.get('daily_summary_hour', 23)
        if now.hour != target_hour:
            return False
        last = self.schedule.get('last_daily_summary')
        if not last:
            return True
        last_dt = datetime.fromisoformat(last)
        return (now - last_dt).total_seconds() > 3600 * 20  # At least 20h gap

    def generate_daily_summary(self):
        self.log.action("Generating daily summary")
        summary_dir = DIGIQUARIUM_DIR / 'daemons' / 'scheduler' / 'summaries'
        summary_dir.mkdir(parents=True, exist_ok=True)

        summary = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat(),
            "tanks_active": 0,
            "daemons_status": {},
            "congregations_today": 0,
            "baselines_run": 0
        }

        # Count active tanks
        logs_dir = DIGIQUARIUM_DIR / "logs"
        if logs_dir.exists():
            for d in logs_dir.iterdir():
                if d.is_dir() and d.name.startswith("tank-"):
                    summary["tanks_active"] += 1

        # Check daemon PID files
        daemons_dir = DIGIQUARIUM_DIR / "daemons"
        if daemons_dir.exists():
            for pid_file in daemons_dir.glob("*.pid"):
                daemon_name = pid_file.stem
                try:
                    pid = int(pid_file.read_text().strip())
                    rc, _, _ = run_command(f"kill -0 {pid} 2>/dev/null")
                    summary["daemons_status"][daemon_name] = "running" if rc == 0 else "stopped"
                except Exception:
                    summary["daemons_status"][daemon_name] = "unknown"

        filename = f"summary_{datetime.now().strftime('%Y%m%d')}.json"
        (summary_dir / filename).write_text(json.dumps(summary, indent=2))

        self.schedule['last_daily_summary'] = datetime.now().isoformat()
        self.save_schedule()
        self.log.info(f"Daily summary written: {filename}")

    # ─── CONGREGATION SCHEDULING ─────────────────────────────────
    def should_schedule_congregation(self):
        interval = self.schedule.get('congregation_interval_hours', 48)
        last = self.schedule.get('last_congregation_scheduled')
        if not last:
            return True
        last_dt = datetime.fromisoformat(last)
        hours = (datetime.now() - last_dt).total_seconds() / 3600
        return hours >= interval

    def schedule_congregation(self):
        self.log.action("Scheduling a congregation")
        topic_idx = self.schedule.get('congregation_topic_index', 0)
        topic = DEFAULT_CONGREGATION_TOPICS[topic_idx % len(DEFAULT_CONGREGATION_TOPICS)]

        # Pick 2-3 participants from available tanks
        participants = ["Adam", "Eve", "Cain"]

        queue_file = DIGIQUARIUM_DIR / 'daemons' / 'moderator' / 'congregation_queue.json'
        queue_file.parent.mkdir(parents=True, exist_ok=True)

        queue = []
        if queue_file.exists():
            try:
                queue = json.loads(queue_file.read_text())
            except Exception:
                queue = []

        queue.append({
            "id": f"cong-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "topic": topic,
            "participants": participants,
            "scheduled_at": datetime.now().isoformat(),
            "scheduled_by": "scheduler"
        })

        queue_file.write_text(json.dumps(queue, indent=2))

        self.schedule['last_congregation_scheduled'] = datetime.now().isoformat()
        self.schedule['congregation_topic_index'] = topic_idx + 1
        self.save_schedule()
        self.log.info(f"Congregation queued: '{topic}' with {participants}")

    # ─── THERAPY SESSIONS ────────────────────────────────────────
    def should_schedule_therapy(self):
        interval = self.schedule.get('therapy_session_interval_hours', 24)
        last = self.schedule.get('last_therapy_session')
        if not last:
            return True
        last_dt = datetime.fromisoformat(last)
        hours = (datetime.now() - last_dt).total_seconds() / 3600
        return hours >= interval

    def schedule_therapy(self):
        self.log.action("Queueing therapy session check")
        queue_file = DIGIQUARIUM_DIR / 'daemons' / 'therapist' / 'therapy_queue.json'
        queue_file.parent.mkdir(parents=True, exist_ok=True)

        queue = {
            "scheduled_at": datetime.now().isoformat(),
            "tanks": [f'tank-{i:02d}' for i in range(1, 18)],
            "type": "wellness_check"
        }
        queue_file.write_text(json.dumps(queue, indent=2))

        self.schedule['last_therapy_session'] = datetime.now().isoformat()
        self.save_schedule()
        self.log.info("Therapy wellness check queued")

    # ─── MAIN LOOP ───────────────────────────────────────────────
    def run(self):
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║              THE SCHEDULER v2.1 - Task Orchestration                 ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        write_pid_file('scheduler')
        self.log.info("THE SCHEDULER v2.1 starting")

        def handle_signal(signum, frame):
            self.should_exit = True
            self.log.info(f"Received signal {signum}, shutting down gracefully")

        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)

        while not self.should_exit:
            try:
                # Baselines (every 12h)
                if self.should_run_baselines():
                    self.queue_baselines()

                # Daily summary (at configured hour)
                if self.should_run_daily_summary():
                    self.generate_daily_summary()

                # Congregation scheduling (every 48h)
                if self.should_schedule_congregation():
                    self.schedule_congregation()

                # Therapy sessions (every 24h)
                if self.should_schedule_therapy():
                    self.schedule_therapy()

                self.log.info("Schedule check complete")
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                self.log.error(f"Error: {e}")
                time.sleep(300)

        self.log.info("THE SCHEDULER shutting down")

if __name__ == '__main__':
    Scheduler().run()
