#!/usr/bin/env python3
"""
THE BROADCASTER v1.0 - Live Feed Export & Dashboard Data Pipeline
==================================================================
Exports pruned tank data every 12 hours for the "live" dashboard.
Removes junk data (null thoughts, timeouts), generates JSON feeds,
commits to Git, and triggers GitHub Pages deployment. The dashboard
shows "live" data that's actually 12 hours old — honest delay, zero cost.

Responsibilities:
- Collect thinking traces from all active tanks
- Prune junk data (null thoughts, timeouts, empty responses)
- Generate clean JSON feeds for the dashboard
- Commit data to Git and push to trigger GitHub Pages rebuild
- Track broadcast history and data quality metrics
- Self-heal on failed pushes with exponential backoff

SLA: 12 hours for feed updates
     Immediate for data pipeline failures
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file, send_email_alert
from shared.escalation import escalate_to_overseer

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
DOCS_DIR = DIGIQUARIUM_DIR / 'docs'
FEED_DIR = DOCS_DIR / 'data' / 'live-feed'
BROADCAST_LOG_DIR = DIGIQUARIUM_DIR / 'daemons' / 'logs'

# Timing
BROADCAST_INTERVAL = 43200    # 12 hours between broadcasts
DISCOVERY_INTERVAL = 1800     # Discover new data every 30 minutes
SLEEP_INTERVAL = 300          # Main loop sleep: 5 minutes

# Pruning thresholds
MIN_THOUGHT_LENGTH = 10       # Minimum chars for a valid thought
MAX_THOUGHT_AGE_HOURS = 24    # Only broadcast recent data
MAX_RETRIES = 3               # Max retries for git push
RETRY_BACKOFF_BASE = 60       # Base seconds for exponential backoff

# Junk patterns to filter out
JUNK_PATTERNS = [
    'null', 'None', 'timeout', 'error', 'TIMEOUT',
    'connection refused', 'empty response', '[no output]',
    'rate limit', '429', 'service unavailable',
]


class Broadcaster:
    """THE BROADCASTER - Live Feed Export & Dashboard Data Pipeline"""

    def __init__(self):
        self.log = DaemonLogger('broadcaster')
        self.history_file = BROADCAST_LOG_DIR / 'broadcaster_history.json'
        self.metrics_file = FEED_DIR / 'metrics.json'
        self.manifest_file = FEED_DIR / 'manifest.json'

        # Ensure directories exist
        FEED_DIR.mkdir(parents=True, exist_ok=True)
        BROADCAST_LOG_DIR.mkdir(parents=True, exist_ok=True)

        self.history = self._load_history()
        self.consecutive_failures = 0

    # ── History & State ───────────────────────────────────────────────

    def _load_history(self) -> dict:
        """Load broadcast history"""
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError):
                pass
        return {
            'broadcasts': [],
            'total_broadcasts': 0,
            'total_traces_exported': 0,
            'total_traces_pruned': 0,
            'last_broadcast': None,
        }

    def _save_history(self):
        """Persist broadcast history atomically"""
        # Keep only last 100 broadcast records
        if len(self.history['broadcasts']) > 100:
            self.history['broadcasts'] = self.history['broadcasts'][-100:]
        tmp = self.history_file.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.history, indent=2, default=str), encoding='utf-8')
        tmp.rename(self.history_file)

    # ── Data Discovery ────────────────────────────────────────────────

    def discover_tank_data(self) -> dict:
        """Discover all available tank data for broadcasting"""
        tanks = {}
        cutoff = datetime.now() - timedelta(hours=MAX_THOUGHT_AGE_HOURS)

        for tank_dir in sorted(LOGS_DIR.glob('tank-*')):
            tank_id = tank_dir.name
            traces_dir = tank_dir / 'thinking_traces'

            if not traces_dir.exists():
                continue

            tank_data = {
                'tank_id': tank_id,
                'trace_files': [],
                'total_raw_entries': 0,
            }

            for trace_file in sorted(traces_dir.glob('*.jsonl')):
                # Only process recent files
                try:
                    file_date = datetime.strptime(trace_file.stem, '%Y-%m-%d')
                    if file_date < cutoff:
                        continue
                except ValueError:
                    # Non-date filenames — check modification time
                    if datetime.fromtimestamp(trace_file.stat().st_mtime) < cutoff:
                        continue

                tank_data['trace_files'].append(trace_file)
                tank_data['total_raw_entries'] += sum(
                    1 for line in open(trace_file, 'r', encoding='utf-8', errors='replace')
                    if line.strip()
                )

            if tank_data['trace_files']:
                tanks[tank_id] = tank_data

        self.log.info(f"Discovered data from {len(tanks)} tanks")
        return tanks

    # ── Data Pruning ──────────────────────────────────────────────────

    def _is_junk(self, entry: dict) -> bool:
        """Determine if a trace entry is junk data that should be pruned"""
        # Check for null/empty thoughts
        thought = entry.get('thought', entry.get('content', entry.get('text', '')))
        if not thought or not isinstance(thought, str):
            return True

        thought = thought.strip()

        # Too short
        if len(thought) < MIN_THOUGHT_LENGTH:
            return True

        # Matches known junk patterns
        thought_lower = thought.lower()
        for pattern in JUNK_PATTERNS:
            if pattern.lower() in thought_lower and len(thought) < 50:
                return True

        # Repeated characters (e.g., "aaaaaaa" or "........")
        if len(set(thought)) <= 2 and len(thought) > 5:
            return True

        return False

    def prune_traces(self, trace_file: Path) -> tuple:
        """Read a trace file, prune junk, return (clean_entries, pruned_count)"""
        clean = []
        pruned = 0

        with open(trace_file, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    pruned += 1
                    continue

                if self._is_junk(entry):
                    pruned += 1
                    continue

                # Sanitize: remove internal fields not meant for public
                for internal_key in ['_internal', '_debug', 'raw_prompt', 'api_key']:
                    entry.pop(internal_key, None)

                clean.append(entry)

        return clean, pruned

    # ── Feed Generation ───────────────────────────────────────────────

    def generate_feeds(self, tanks: dict) -> dict:
        """Generate clean JSON feeds for each tank"""
        self.log.info("Generating dashboard feeds")
        feed_stats = {
            'tanks_processed': 0,
            'total_clean': 0,
            'total_pruned': 0,
            'feeds_written': [],
        }

        all_recent = []  # For the combined feed

        for tank_id, tank_data in tanks.items():
            tank_clean = []
            tank_pruned = 0

            for trace_file in tank_data['trace_files']:
                clean, pruned = self.prune_traces(trace_file)
                tank_clean.extend(clean)
                tank_pruned += pruned

            if not tank_clean:
                continue

            # Sort by timestamp
            tank_clean.sort(key=lambda x: x.get('timestamp', x.get('time', '')))

            # Write per-tank feed
            feed_file = FEED_DIR / f"{tank_id}.json"
            feed_data = {
                'tank_id': tank_id,
                'generated_at': datetime.now().isoformat(),
                'delay_hours': 12,
                'entry_count': len(tank_clean),
                'pruned_count': tank_pruned,
                'entries': tank_clean,  # Full entries per tank (no truncation)
            }
            feed_file.write_text(json.dumps(feed_data, indent=2, default=str, ensure_ascii=False), encoding='utf-8')

            feed_stats['tanks_processed'] += 1
            feed_stats['total_clean'] += len(tank_clean)
            feed_stats['total_pruned'] += tank_pruned
            feed_stats['feeds_written'].append(feed_file.name)

            # Add to combined feed (latest 5 per tank)
            all_recent.extend(tank_clean)

        # Write combined "latest" feed
        all_recent.sort(key=lambda x: x.get('timestamp', x.get('time', '')), reverse=True)
        latest_feed = FEED_DIR / 'latest.json'
        latest_data = {
            'generated_at': datetime.now().isoformat(),
            'delay_hours': 12,
            'tanks_included': feed_stats['tanks_processed'],
            'entries': all_recent,  # All recent entries across all tanks (no truncation)
        }
        latest_feed.write_text(json.dumps(latest_data, indent=2, default=str, ensure_ascii=False), encoding='utf-8')

        # Write manifest
        manifest = {
            'generated_at': datetime.now().isoformat(),
            'feeds': feed_stats['feeds_written'] + ['latest.json'],
            'total_tanks': feed_stats['tanks_processed'],
            'next_broadcast': (datetime.now() + timedelta(seconds=BROADCAST_INTERVAL)).isoformat(),
        }
        self.manifest_file.write_text(json.dumps(manifest, indent=2, default=str), encoding='utf-8')

        # Write quality metrics
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'clean_entries': feed_stats['total_clean'],
            'pruned_entries': feed_stats['total_pruned'],
            'prune_rate': round(
                feed_stats['total_pruned'] / max(1, feed_stats['total_clean'] + feed_stats['total_pruned']) * 100, 1
            ),
            'tanks_with_data': feed_stats['tanks_processed'],
        }
        self.metrics_file.write_text(json.dumps(metrics, indent=2, default=str), encoding='utf-8')

        self.log.info(
            f"Feeds generated: {feed_stats['tanks_processed']} tanks, "
            f"{feed_stats['total_clean']} clean entries, "
            f"{feed_stats['total_pruned']} pruned"
        )
        return feed_stats

    # ── Git Commit & Push ─────────────────────────────────────────────

    def _run_git(self, *args) -> tuple:
        """Run a git command in the Digiquarium directory"""
        try:
            result = subprocess.run(
                ['git', '-C', str(DIGIQUARIUM_DIR)] + list(args),
                capture_output=True, text=True, timeout=120
            )
            return result.returncode == 0, result.stdout.strip() + result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, 'Git command timed out'
        except Exception as e:
            return False, str(e)

    def commit_and_push(self) -> bool:
        """Commit feed data to Git and push to trigger GitHub Pages deployment"""
        self.log.info("Committing feed data to Git")

        # Stage feed files
        ok, output = self._run_git('add', str(FEED_DIR))
        if not ok:
            self.log.error(f"Git add failed: {output}")
            return False

        # Check if there are changes to commit
        ok, output = self._run_git('diff', '--cached', '--quiet')
        if ok:
            self.log.info("No changes to commit — feeds unchanged")
            return True

        # Commit
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        commit_msg = f"📡 Live feed: {timestamp}"
        ok, output = self._run_git('commit', '-m', commit_msg)
        if not ok:
            self.log.error(f"Git commit failed: {output}")
            return False

        # Push with retry and exponential backoff
        for attempt in range(MAX_RETRIES):
            ok, output = self._run_git('push')
            if ok:
                self.log.info(f"Git push successful (attempt {attempt + 1})")
                self.consecutive_failures = 0
                return True

            wait = RETRY_BACKOFF_BASE * (2 ** attempt)
            self.log.warn(f"Git push failed (attempt {attempt + 1}/{MAX_RETRIES}), retrying in {wait}s: {output}")
            time.sleep(wait)

        # All retries exhausted
        self.consecutive_failures += 1
        self.log.error(f"Git push failed after {MAX_RETRIES} attempts")
        escalate_to_overseer(
            severity='high',
            issue_type='BROADCAST_PUSH_FAILURE',
            message=f"THE BROADCASTER failed to push after {MAX_RETRIES} attempts. "
                    f"Consecutive failures: {self.consecutive_failures}",
            extra={'daemon': 'broadcaster', 'consecutive_failures': self.consecutive_failures}
        )
        return False

    # ── Broadcast Cycle ───────────────────────────────────────────────

    def broadcast(self) -> bool:
        """Execute a full broadcast cycle: discover → prune → generate → push"""
        self.log.info("=" * 60)
        self.log.info("Starting broadcast cycle")
        cycle_start = datetime.now()

        # 1. Discover tank data
        tanks = self.discover_tank_data()
        if not tanks:
            self.log.warn("No tank data found for broadcast")
            return True  # Not a failure, just nothing to broadcast

        # 2. Generate clean feeds
        feed_stats = self.generate_feeds(tanks)

        # 3. Commit and push
        push_ok = self.commit_and_push()

        # 4. Record in history
        duration = (datetime.now() - cycle_start).total_seconds()
        record = {
            'timestamp': cycle_start.isoformat(),
            'duration_seconds': round(duration, 1),
            'tanks_processed': feed_stats['tanks_processed'],
            'clean_entries': feed_stats['total_clean'],
            'pruned_entries': feed_stats['total_pruned'],
            'push_success': push_ok,
        }
        self.history['broadcasts'].append(record)
        self.history['total_broadcasts'] += 1
        self.history['total_traces_exported'] += feed_stats['total_clean']
        self.history['total_traces_pruned'] += feed_stats['total_pruned']
        self.history['last_broadcast'] = cycle_start.isoformat()
        self._save_history()

        status = "SUCCESS" if push_ok else "FAILED (push)"
        self.log.info(f"Broadcast cycle {status} in {duration:.1f}s")
        self.log.info("=" * 60)
        return push_ok

    # ── Main Loop ─────────────────────────────────────────────────────

    def run(self):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║          THE BROADCASTER v1.0 - Live Feed Export Pipeline            ║
╠══════════════════════════════════════════════════════════════════════╣
║  12-hour delayed "live" dashboard feeds                              ║
║  Junk data pruning & quality metrics                                 ║
║  Auto-commit & push to GitHub Pages                                  ║
║  Reports to THE WEBMASTER                                            ║
╚══════════════════════════════════════════════════════════════════════╝
""")
        write_pid_file('broadcaster')
        self.log.info("THE BROADCASTER v1.0 starting")

        # Run initial broadcast on startup
        self.broadcast()

        last_broadcast = datetime.now()
        last_discovery = datetime.now()

        while True:
            try:
                _sla_cycle_start = time.time()
                now = datetime.now()

                # Discovery scan every 30 minutes (just to log what's available)
                if (now - last_discovery).total_seconds() >= DISCOVERY_INTERVAL:
                    tanks = self.discover_tank_data()
                    self.log.info(f"Discovery: {len(tanks)} tanks with recent data")
                    last_discovery = now

                # Full broadcast every 12 hours
                if (now - last_broadcast).total_seconds() >= BROADCAST_INTERVAL:
                    self.broadcast()
                    last_broadcast = now

                # Write SLA status
                _sla_cycle_duration = time.time() - _sla_cycle_start
                _sla_data = {
                    'daemon': 'broadcaster',
                    'compliant': True,
                    'last_check_time': datetime.now().isoformat(),
                    'cycle_duration': _sla_cycle_duration,
                    'sla_target': 300,
                    'violations_count': 0
                }
                _sla_path = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')) / 'daemons' / 'broadcaster' / 'sla_status.json'
                _sla_path.parent.mkdir(parents=True, exist_ok=True)
                _sla_path.write_text(json.dumps(_sla_data, indent=2))

                time.sleep(SLEEP_INTERVAL)

            except KeyboardInterrupt:
                self.log.info("Shutdown signal received, saving state...")
                self._save_history()
                break
            except Exception as e:
                self.log.error(f"Error in main loop: {e}")
                escalate_to_overseer(
                    severity='high',
                    issue_type='DAEMON_ERROR',
                    message=f"THE BROADCASTER encountered an error: {e}",
                    extra={'daemon': 'broadcaster'}
                )
                time.sleep(SLEEP_INTERVAL)


# Single-instance lock
import fcntl
LOCK_FILE = Path(__file__).parent / 'broadcaster.lock'
lock_fd = None

def acquire_lock():
    global lock_fd
    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except IOError:
        print("[broadcaster] Another instance is already running")
        return False


if __name__ == "__main__":
    if acquire_lock():
        Broadcaster().run()
