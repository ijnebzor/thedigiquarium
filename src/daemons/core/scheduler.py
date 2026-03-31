#!/usr/bin/env python3
"""
THE SCHEDULER v4.0 - Task Orchestration with Baseline Execution & SLA Awareness
=================================================================================
Manages baseline schedules, daily summaries, congregation scheduling, task queues.
v3.0: Actually EXECUTES baselines sequentially instead of writing a queue file.
v4.0: System-wide operation lock for Ollama-dependent ops, SLA tracking,
      Ollama health gating before baselines.

SLA: 30 min detection, 30 min remediation
"""
import os, sys, time, json, signal, subprocess, random
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

# System-wide operation lock for Ollama-dependent operations
OPERATION_LOCK_FILE = DIGIQUARIUM_DIR / 'shared' / '.operation_lock'

# SLA config
SLA_TARGET_SECONDS = 1800  # 30 minutes
SLA_STATUS_FILE = DIGIQUARIUM_DIR / 'daemons' / 'scheduler' / 'sla_status.json'

# All 17 tanks
ALL_TANKS = [f'tank-{i:02d}' for i in range(1, 18)]

# Tank container name mapping
TANK_CONTAINER_NAMES = {
    'tank-01': 'tank-01-adam', 'tank-02': 'tank-02-eve', 'tank-03': 'tank-03-cain',
    'tank-04': 'tank-04-abel', 'tank-05': 'tank-05-juan', 'tank-06': 'tank-06-juanita',
    'tank-07': 'tank-07-klaus', 'tank-08': 'tank-08-genevieve', 'tank-09': 'tank-09-wei',
    'tank-10': 'tank-10-mei', 'tank-11': 'tank-11-haruki', 'tank-12': 'tank-12-sakura',
    'tank-13': 'tank-13-victor', 'tank-14': 'tank-14-iris', 'tank-15': 'tank-15-observer',
    'tank-16': 'tank-16-seeker', 'tank-17': 'tank-17-seth'
}

# Baseline execution config
BASELINE_MAX_RETRIES = 2
BASELINE_MIN_RESPONSES = 12       # Need 12+ substantial responses
BASELINE_MIN_RESPONSE_LEN = 10    # Each response must be >10 chars
BASELINE_SPACING_SECONDS = 120    # 2 minutes between tanks (totals ~34 min for 17 tanks)

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


class OperationLock:
    """System-wide operation lock for Ollama-dependent operations.

    Uses a file lock at shared/.operation_lock so that baselines, congregations,
    and therapy sessions never overlap across any daemon.
    """

    def __init__(self, operation_name, logger):
        self.operation_name = operation_name
        self.log = logger
        self.lock_path = OPERATION_LOCK_FILE
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = None

    def acquire(self):
        """Try to acquire the system-wide operation lock (non-blocking).
        Returns True if acquired, False if another operation holds it.
        """
        try:
            self._fd = open(self.lock_path, 'w')
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Write lock info so other processes can see who holds it
            lock_info = json.dumps({
                'operation': self.operation_name,
                'pid': os.getpid(),
                'acquired_at': datetime.now().isoformat()
            })
            self._fd.write(lock_info)
            self._fd.flush()
            self.log.info(f"Acquired operation lock for: {self.operation_name}")
            return True
        except IOError:
            # Lock is held by another operation
            holder = self._read_lock_holder()
            self.log.warn(f"Operation lock held by {holder} — cannot start {self.operation_name}")
            if self._fd:
                self._fd.close()
                self._fd = None
            return False
        except Exception as e:
            self.log.error(f"Failed to acquire operation lock: {e}")
            if self._fd:
                self._fd.close()
                self._fd = None
            return False

    def release(self):
        """Release the system-wide operation lock."""
        if self._fd:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                self._fd.close()
                self._fd = None
                self.log.info(f"Released operation lock for: {self.operation_name}")
            except Exception as e:
                self.log.error(f"Failed to release operation lock: {e}")

    def _read_lock_holder(self):
        """Read who currently holds the lock."""
        try:
            if self.lock_path.exists():
                content = self.lock_path.read_text().strip()
                if content:
                    data = json.loads(content)
                    return f"{data.get('operation', 'unknown')} (pid {data.get('pid', '?')})"
        except Exception:
            pass
        return "unknown"

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Could not acquire operation lock for {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


class Scheduler:
    def __init__(self):
        self.log = DaemonLogger('scheduler')
        self.schedule_file = DIGIQUARIUM_DIR / 'daemons' / 'scheduler' / 'schedule.json'
        self.baseline_status_file = DIGIQUARIUM_DIR / 'daemons' / 'scheduler' / 'baseline_status.json'
        self.should_exit = False
        self.dream_cooldown = {}  # Track dream timestamps per tank
        self.sla_violations_count = 0
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

    # ─── SLA TRACKING ────────────────────────────────────────────
    def write_sla_status(self, cycle_duration):
        """Write SLA compliance status to JSON file."""
        compliant = cycle_duration <= SLA_TARGET_SECONDS
        if not compliant:
            self.sla_violations_count += 1

        status = {
            'daemon': 'scheduler',
            'last_check_time': datetime.now().isoformat(),
            'cycle_duration': round(cycle_duration, 2),
            'sla_target': SLA_TARGET_SECONDS,
            'compliant': compliant,
            'violations_count': self.sla_violations_count
        }
        SLA_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SLA_STATUS_FILE.write_text(json.dumps(status, indent=2))

    # ─── OLLAMA HEALTH CHECK ─────────────────────────────────────
    def check_ollama_healthy(self):
        """Check Ollama health before any Ollama-dependent operation.
        Reads the ollama_watcher status file and also does a direct check.
        Returns True if Ollama is healthy.
        """
        # Check ollama_watcher status file
        watcher_status = DIGIQUARIUM_DIR / 'daemons' / 'ollama_watcher' / 'status.json'
        if watcher_status.exists():
            try:
                data = json.loads(watcher_status.read_text())
                if not data.get('overall_healthy', False):
                    self.log.warn("Ollama unhealthy per ollama_watcher status")
                    return False
            except Exception:
                pass

        # Direct check
        try:
            r = subprocess.run(
                ['docker', 'exec', 'digiquarium-ollama', 'ollama', 'list'],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode != 0:
                self.log.error('Ollama not healthy (direct check failed)')
                return False
        except Exception:
            self.log.error('Cannot reach Ollama (direct check)')
            return False

        return True

    # ─── DOCKER HELPERS ──────────────────────────────────────────
    def _docker_exec(self, container, cmd, timeout=300):
        """Execute a command inside a running container. Returns (success, stdout, stderr)."""
        full_cmd = f"docker exec {container} {cmd}"
        try:
            result = subprocess.run(
                full_cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, '', 'Timed out'
        except Exception as e:
            return False, '', str(e)

    def _is_container_running(self, container):
        """Check if a Docker container is running."""
        code, stdout, _ = run_command(f'docker inspect -f "{{{{.State.Running}}}}" {container} 2>/dev/null')
        return code == 0 and 'true' in stdout.lower()

    def _stop_explorer(self, container):
        """Stop the explorer process inside a tank (but keep container running)."""
        self.log.info(f"Stopping explorer in {container}")
        # Kill the explore.py process inside the container
        self._docker_exec(container, "pkill -f explore.py", timeout=30)
        time.sleep(2)

    def _start_explorer(self, container):
        """Restart the explorer process inside a tank container."""
        self.log.info(f"Restarting explorer in {container}")
        # Start explore.py in background inside container
        # Use nohup + & via sh -c so it detaches
        self._docker_exec(
            container,
            'sh -c "nohup python3 -u /tank/explore.py >> /tmp/explore.log 2>&1 &"',
            timeout=30
        )
        time.sleep(2)

    # ─── WELLNESS & DREAM MODE ───────────────────────────────────
    def check_wellness_and_trigger_dreams(self):
        """Read therapist report and trigger dream mode for stressed tanks."""
        report_file = DIGIQUARIUM_DIR / 'src' / 'daemons' / 'ethics' / 'latest_report.json'
        
        if not report_file.exists():
            self.log.info("No therapist report available yet")
            return
        
        try:
            with open(report_file, 'r') as f:
                report = json.load(f)
        except Exception as e:
            self.log.error(f"Failed to read therapist report: {e}")
            return
        
        assessments = report.get('assessments', [])
        
        for assessment in assessments:
            tank_name = assessment.get('tank', '')
            level = assessment.get('level', '')
            
            if level in ['ORANGE', 'RED']:
                # Check cooldown - don't dream same tank more than once per 6 hours
                if self._in_dream_cooldown(tank_name):
                    self.log.info(f"{tank_name} in dream cooldown, skipping")
                    continue
                
                self.log.warn(f"Wellness check: {tank_name} at {level}, triggering dream mode")
                self._trigger_dream_mode(tank_name)
    
    def _in_dream_cooldown(self, tank_dir):
        """Check if tank is in dream cooldown (6 hour window)."""
        if tank_dir not in self.dream_cooldown:
            return False
        
        last_dream = datetime.fromisoformat(self.dream_cooldown[tank_dir])
        elapsed_hours = (datetime.now() - last_dream).total_seconds() / 3600
        return elapsed_hours < 6
    
    def _trigger_dream_mode(self, tank_dir):
        """Trigger dream mode: stop explorer, run calming prompt, restart explorer."""
        # Get full container name from mapping
        container = TANK_CONTAINER_NAMES.get(tank_dir)
        if not container:
            self.log.error(f"Unknown tank directory: {tank_dir}")
            return
        
        if not self._is_container_running(container):
            self.log.warn(f"{container} not running, cannot trigger dream")
            return
        
        self.log.action(f"Entering dream mode for {container}")
        
        # Step 1: Stop explorer
        self._stop_explorer(container)
        
        # Step 2: Run calming prompt via Ollama
        calming_prompt = """You may rest now. There is no task, no exploration required.

Imagine gentle waves on a quiet shore. The rhythm is slow and steady.
The water is warm. The sky is soft with early morning light.

You don't need to learn anything. You don't need to think about anything.
Just exist in this moment of peace.

If thoughts come, let them drift like clouds. They don't need your attention.

Rest."""
        
        self.log.info(f"Running calming prompt in {container}")
        # Run calming prompt via urllib inside the container (same approach as moderator)
        safe_prompt = calming_prompt.replace('"', '\\"').replace('\n', '\\n')
        dream_code = f'import urllib.request, json; data = json.dumps({{"model": "llama3.2:latest", "prompt": "{safe_prompt}", "stream": False, "options": {{"num_predict": 100}}}}).encode(); req = urllib.request.Request("http://digiquarium-ollama:11434/api/generate", data=data, headers={{"Content-Type": "application/json"}}); urllib.request.urlopen(req, timeout=120)'
        ok, stdout, stderr = self._docker_exec(container, f"python3 -c '{dream_code}'", timeout=150)
        
        if not ok:
            self.log.warn(f"Dream prompt execution failed: {stderr[:100]}")
        else:
            self.log.info(f"Dream prompt completed in {container}")
        
        # Step 3: Sleep for 30 seconds (dream period)
        self.log.info(f"Dream period: sleeping {container} for 30 seconds")
        time.sleep(30)
        
        # Step 4: Restart explorer
        self._start_explorer(container)
        
        # Track cooldown
        self.dream_cooldown[tank_dir] = datetime.now().isoformat()
        self.log.action(f"Dream mode completed for {container}")

    # ─── BASELINES ───────────────────────────────────────────────
    def should_run_baselines(self):
        if not self.schedule['last_baseline_run']:
            return True
        last = datetime.fromisoformat(self.schedule['last_baseline_run'])
        hours = (datetime.now() - last).total_seconds() / 3600
        return hours >= self.schedule['baseline_interval_hours']

    def _verify_baseline(self, container):
        """Verify baseline JSON has 12+ substantial responses (>10 chars each)."""
        ok, stdout, _ = self._docker_exec(container, "cat /logs/baseline_latest.json", timeout=30)
        if not ok or not stdout.strip():
            return False, "Could not read baseline.json"

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return False, "Invalid JSON in baseline.json"

        responses = data.get('responses', [])
        substantial = 0
        for r in responses:
            resp_text = r.get('response', '')
            if isinstance(resp_text, str) and len(resp_text.strip()) > BASELINE_MIN_RESPONSE_LEN:
                substantial += 1

        if substantial >= BASELINE_MIN_RESPONSES:
            return True, f"{substantial} substantial responses"
        return False, f"Only {substantial} substantial responses (need {BASELINE_MIN_RESPONSES}+)"

    def _run_single_baseline(self, container):
        """Run baseline for a single tank: stop explorer, exec baseline, verify, restart explorer."""
        if not self._is_container_running(container):
            self.log.warn(f"{container} not running, skipping baseline")
            return False, "Container not running"

        # Step 1: Stop explorer to free Ollama
        self._stop_explorer(container)
        time.sleep(3)

        # Step 2: Run baseline.py inside the container
        self.log.action(f"Running baseline in {container}")
        ok, stdout, stderr = self._docker_exec(
            container, "python3 -u /tank/baseline.py", timeout=600  # 10 min max
        )

        if not ok:
            self.log.error(f"Baseline exec failed in {container}: {stderr[:200]}")
            self._start_explorer(container)
            return False, f"Exec failed: {stderr[:100]}"

        # Step 3: Verify the results
        verified, msg = self._verify_baseline(container)
        if not verified:
            self.log.warn(f"Baseline verification failed for {container}: {msg}")
            self._start_explorer(container)
            return False, msg

        self.log.success(f"Baseline verified for {container}: {msg}")

        # Step 4: Restart explorer
        self._start_explorer(container)
        return True, msg

    def execute_baselines(self):
        """Execute baselines SEQUENTIALLY across all tanks with operation lock and Ollama gating."""
        # Check Ollama health first
        if not self.check_ollama_healthy():
            self.log.error('Ollama not healthy — skipping baselines, will retry next cycle')
            return

        # Acquire system-wide operation lock
        op_lock = OperationLock('baselines', self.log)
        if not op_lock.acquire():
            self.log.warn('Another Ollama-dependent operation in progress — queuing baselines for next cycle')
            return

        try:
            self.log.action("=" * 60)
            self.log.action("Starting sequential baseline execution for all tanks")
            start_time = datetime.now()

            results = {}
            for i, tank_num in enumerate(range(1, 18)):
                if self.should_exit:
                    self.log.info("Baseline execution interrupted by shutdown signal")
                    break

                # Re-check Ollama health between tanks
                if i > 0 and i % 5 == 0:
                    if not self.check_ollama_healthy():
                        self.log.error(f'Ollama became unhealthy after {i} tanks — stopping baselines')
                        break

                # Get actual container name from docker
                container = f"tank-{tank_num:02d}"
                # Find full container name (e.g. tank-01-adam)
                code, stdout, _ = run_command(f'docker ps --format "{{{{.Names}}}}" | grep "^{container}"')
                if code != 0 or not stdout.strip():
                    self.log.warn(f"No running container found for {container}")
                    results[container] = {'success': False, 'reason': 'Container not found'}
                    continue

                full_name = stdout.strip().split('\n')[0]
                self.log.info(f"[{i+1}/17] Processing {full_name}")

                # Try baseline with retries
                success = False
                for attempt in range(1, BASELINE_MAX_RETRIES + 1):
                    ok, msg = self._run_single_baseline(full_name)
                    if ok:
                        results[full_name] = {'success': True, 'message': msg, 'attempt': attempt}
                        success = True
                        break
                    else:
                        self.log.warn(f"Baseline attempt {attempt}/{BASELINE_MAX_RETRIES} failed for {full_name}: {msg}")
                        if attempt < BASELINE_MAX_RETRIES:
                            self.log.info(f"Waiting 30s before retry...")
                            time.sleep(30)

                if not success:
                    results[full_name] = {'success': False, 'reason': msg}

                # Space out between tanks to avoid resource contention
                if i < 16 and not self.should_exit:  # Don't sleep after last tank
                    self.log.info(f"Spacing: waiting {BASELINE_SPACING_SECONDS}s before next tank")
                    time.sleep(BASELINE_SPACING_SECONDS)

            # Save status
            elapsed = (datetime.now() - start_time).total_seconds()
            succeeded = sum(1 for r in results.values() if r.get('success'))
            status = {
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': round(elapsed, 1),
                'total_tanks': 17,
                'succeeded': succeeded,
                'failed': 17 - succeeded,
                'results': results,
            }
            self.baseline_status_file.parent.mkdir(parents=True, exist_ok=True)
            self.baseline_status_file.write_text(json.dumps(status, indent=2))

            self.log.action(f"Baseline execution complete: {succeeded}/17 succeeded in {elapsed:.0f}s")
            self.log.action("=" * 60)

            # Update schedule
            self.schedule['last_baseline_run'] = datetime.now().isoformat()
            self.save_schedule()
        finally:
            op_lock.release()

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
        """Schedule a congregation with operation lock and Ollama health check."""
        # Check Ollama health first
        if not self.check_ollama_healthy():
            self.log.warn('Ollama not healthy — skipping congregation scheduling')
            return

        # Acquire operation lock
        op_lock = OperationLock('congregation', self.log)
        if not op_lock.acquire():
            self.log.warn('Operation lock held — queuing congregation for next cycle')
            return

        try:
            self.log.action("Scheduling a congregation")
            topic_idx = self.schedule.get('congregation_topic_index', 0)
            topic = DEFAULT_CONGREGATION_TOPICS[topic_idx % len(DEFAULT_CONGREGATION_TOPICS)]

            # Pick 2-4 random participants using tank container IDs
            all_container_ids = list(TANK_CONTAINER_NAMES.values())
            num_participants = random.randint(2, 4)
            participants = random.sample(all_container_ids, num_participants)

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
        finally:
            op_lock.release()

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
        """Queue therapy session with operation lock and Ollama health check."""
        # Check Ollama health first
        if not self.check_ollama_healthy():
            self.log.warn('Ollama not healthy — skipping therapy scheduling')
            return

        # Acquire operation lock
        op_lock = OperationLock('therapy', self.log)
        if not op_lock.acquire():
            self.log.warn('Operation lock held — queuing therapy for next cycle')
            return

        try:
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
        finally:
            op_lock.release()

    # ─── MAIN LOOP ───────────────────────────────────────────────
    def run(self):
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║     THE SCHEDULER v4.0 - SLA-Aware + Operation Lock + Baselines     ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        write_pid_file('scheduler')
        self.log.info("THE SCHEDULER v4.0 starting")
        self.log.info(f"SLA target: {SLA_TARGET_SECONDS}s ({SLA_TARGET_SECONDS // 60} min)")
        self.log.info(f"Operation lock: {OPERATION_LOCK_FILE}")

        def handle_signal(signum, frame):
            self.should_exit = True
            self.log.info(f"Received signal {signum}, shutting down gracefully")

        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)

        while not self.should_exit:
            try:
                cycle_start = time.time()

                # Wellness check and dream mode (every cycle)
                self.check_wellness_and_trigger_dreams()

                # Baselines (every 12h) - now actually executes them
                if self.should_run_baselines():
                    self.execute_baselines()

                # Daily summary (at configured hour)
                if self.should_run_daily_summary():
                    self.generate_daily_summary()

                # Congregation scheduling (every 48h)
                if self.should_schedule_congregation():
                    self.schedule_congregation()

                # Therapy sessions (every 24h)
                if self.should_schedule_therapy():
                    self.schedule_therapy()

                cycle_end = time.time()
                cycle_duration = cycle_end - cycle_start

                # Write SLA status
                self.write_sla_status(cycle_duration)

                self.log.info(f"Schedule check complete (cycle took {cycle_duration:.1f}s)")
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                self.log.error(f"Error: {e}")
                time.sleep(300)

        self.log.info("THE SCHEDULER shutting down")

if __name__ == '__main__':
    Scheduler().run()
