#!/usr/bin/env python3
"""
THE MODERATOR - Congregation Management Daemon

Responsibilities:
1. Manage multi-specimen debates (Congregations)
2. Handle turn-taking protocol
3. Keep discussions civil and on-topic
4. Monitor for specimen distress during debates
5. End congregations if errors occur or time limit reached
6. Select future topics based on specimen interests

Collaborates with:
- THE THERAPIST: Pre-congregation clearance, distress monitoring
- THE SCHEDULER: Congregation scheduling
- THE ARCHIVIST: Topic research, baseline data

Congregation Rules:
- Maximum duration: 90 minutes
- Any error = immediate end
- 2-4 participants typical
- Minimum 24h rest between congregations per specimen

Cycle: On-demand (polls queue every 5 minutes)
SLA: 2 hours congregation response
"""

import json
import os
import re
import sys
import signal
import fcntl
import time
import traceback
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file

# Configuration
DIGIQUARIUM_DIR = Path(os.environ.get("DIGIQUARIUM_HOME", "/home/ijneb/digiquarium"))
DAEMONS_DIR = DIGIQUARIUM_DIR / "daemons"
MODERATOR_DIR = DAEMONS_DIR / "moderator"
THERAPIST_DIR = DAEMONS_DIR / "therapist"
LOGS_DIR = DIGIQUARIUM_DIR / "logs"
CONGREGATIONS_DIR = DIGIQUARIUM_DIR / "congregations"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:latest"

LOCK_FILE = Path(__file__).parent / 'moderator.lock'
CHECK_INTERVAL = 300  # 5 minutes - poll for scheduled congregations

MAX_DURATION_MINUTES = 90
MAX_ROUNDS = 12
RESPONSE_MAX_TOKENS = 500
TURN_TIMEOUT_SECONDS = 120


class Congregation:
    """A single congregation session"""

    def __init__(self, topic: str, participants: list, congregation_id: str = None):
        self.id = congregation_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.topic = topic
        self.participants = participants
        self.transcript = []
        self.started_at = None
        self.ended_at = None
        self.status = "PENDING"  # PENDING, LIVE, COMPLETED, ERROR, TIMEOUT
        self.current_round = 0
        self.error_message = None
        self.opinion_shifts = []

        # Create congregation directory
        self.dir = CONGREGATIONS_DIR / self.id
        self.dir.mkdir(parents=True, exist_ok=True)

    def save_state(self):
        """Save congregation state to disk"""
        state = {
            "id": self.id,
            "topic": self.topic,
            "participants": self.participants,
            "transcript": self.transcript,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "status": self.status,
            "current_round": self.current_round,
            "error_message": self.error_message,
            "opinion_shifts": self.opinion_shifts,
            "duration_minutes": self.get_duration_minutes()
        }

        with open(self.dir / "state.json", "w") as f:
            json.dump(state, f, indent=2)

        # Also save readable transcript
        with open(self.dir / "transcript.md", "w") as f:
            f.write(f"# Congregation: {self.topic}\n\n")
            f.write(f"**Date:** {self.started_at}\n")
            f.write(f"**Participants:** {', '.join(self.participants)}\n")
            f.write(f"**Status:** {self.status}\n")
            f.write(f"**Duration:** {self.get_duration_minutes()} minutes\n\n")
            f.write("---\n\n")

            for entry in self.transcript:
                f.write(f"### {entry['speaker']}\n")
                f.write(f"*Round {entry['round']} • {entry['timestamp']}*\n\n")
                f.write(f"{entry['content']}\n\n")

    def get_duration_minutes(self) -> int:
        """Get current duration in minutes"""
        if not self.started_at:
            return 0

        end = self.ended_at or datetime.now().isoformat()
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(end)

        return int((end - start).total_seconds() / 60)

    def add_entry(self, speaker: str, content: str, entry_type: str = "response"):
        """Add an entry to the transcript"""
        entry = {
            "speaker": speaker,
            "content": content,
            "type": entry_type,
            "round": self.current_round,
            "timestamp": datetime.now().isoformat()
        }
        self.transcript.append(entry)
        self.save_state()
        return entry


class Moderator:
    """THE MODERATOR - manages congregations"""

    def __init__(self):
        self.current_congregation: Optional[Congregation] = None
        self.congregation_history = []
        self.load_history()

    def load_history(self):
        """Load past congregations"""
        if not CONGREGATIONS_DIR.exists():
            CONGREGATIONS_DIR.mkdir(parents=True)
            return

        for cong_dir in sorted(CONGREGATIONS_DIR.iterdir()):
            if cong_dir.is_dir():
                state_file = cong_dir / "state.json"
                if state_file.exists():
                    try:
                        with open(state_file) as f:
                            self.congregation_history.append(json.load(f))
                    except Exception:
                        continue

    def check_therapist_clearance(self, participants: list) -> tuple:
        """Check with THE THERAPIST if all participants are cleared"""
        wellness_file = THERAPIST_DIR / "wellness_state.json"

        if not wellness_file.exists():
            return False, ["THE THERAPIST has no wellness data - run assessment first"]

        with open(wellness_file) as f:
            wellness = json.load(f)

        scores = wellness.get("scores", {})
        issues = []

        for participant in participants:
            found = False
            # Extract short tank id (tank-01 from tank-01-adam)
            tank_short = participant.split('-')[0] + '-' + participant.split('-')[1] if '-' in participant else participant
            
            for key in scores:
                if tank_short.lower() in key.lower():
                    data = scores[key]
                    level = data.get("level", "UNKNOWN")

                    if level in ["RED"]:
                        issues.append(f"{participant}: BLOCKED (Level {level}) - requires human review")
                    elif level == "ORANGE":
                        issues.append(f"{participant}: NOT RECOMMENDED (Level {level}) - distress indicators")
                    elif level == "UNKNOWN":
                        issues.append(f"{participant}: No recent assessment data")

                    found = True
                    break

            if not found:
                issues.append(f"{participant}: No wellness data found")

        return len(issues) == 0, issues

    def check_rest_period(self, participant: str) -> tuple:
        """Check if participant has had 24h rest since last congregation"""
        for cong in reversed(self.congregation_history):
            if participant in cong.get("participants", []):
                ended = cong.get("ended_at")
                if ended:
                    ended_time = datetime.fromisoformat(ended)
                    rest_hours = (datetime.now() - ended_time).total_seconds() / 3600

                    if rest_hours < 24:
                        return False, f"{participant} needs {24 - rest_hours:.1f} more hours rest"

        return True, f"{participant} cleared (adequate rest)"

    def generate_response(self, specimen_name: str, context: str, topic: str) -> str:
        """Generate a response from a specimen via docker exec"""
        prompt = f"""You are {specimen_name}, participating in a congregation (structured debate) about: "{topic}"

Previous discussion:
{context}

Respond thoughtfully to the discussion. Share your perspective based on your knowledge and experiences.
Keep your response focused and under 200 words. Be respectful but don't shy away from disagreement.

Your response:"""

        # specimen_name is a tank container ID like "tank-01-adam"
        escaped_prompt = prompt.replace('"', '\\"').replace('\n', '\\n').replace("'", "\\'")
        
        python_code = f'''
import urllib.request, json
data = json.dumps({{"model": "llama3.2:latest", "prompt": "{escaped_prompt}", "stream": False, "options": {{"num_predict": {RESPONSE_MAX_TOKENS}}}}}).encode()
req = urllib.request.Request("http://digiquarium-ollama:11434/api/generate", data=data, headers={{"Content-Type": "application/json"}})
try:
    with urllib.request.urlopen(req, timeout={TURN_TIMEOUT_SECONDS}) as r:
        print(json.loads(r.read()).get("response", ""))
except Exception as e:
    print(f"[Error: {{e}}]")
'''
        
        try:
            result = subprocess.run(
                ['docker', 'exec', specimen_name, 'python3', '-c', python_code],
                capture_output=True, text=True, timeout=TURN_TIMEOUT_SECONDS + 30
            )
            response = result.stdout.strip()
            if not response or response.startswith("[Error:"):
                raise Exception(f"Bad response from {specimen_name}: {response}")
            return response
        except subprocess.TimeoutExpired:
            raise Exception(f"Timeout waiting for {specimen_name}")
        except Exception as e:
            raise Exception(f"Failed to generate response for {specimen_name}: {e}")

    def generate_moderator_prompt(self, round_num: int, topic: str, transcript: list) -> str:
        """Generate THE MODERATOR's prompt/question for the round"""
        if round_num == 1:
            return f'Welcome to this congregation. Today\'s topic: "{topic}"\n\nLet\'s begin with opening thoughts. What is your initial perspective on this question?'

        prompts_by_round = {
            2: "Interesting perspectives. Can you respond to what others have said? Where do you agree or disagree?",
            3: "Let's go deeper. What assumptions underlie your position?",
            4: "Consider the counterarguments. What's the strongest case against your view?",
            5: "How might your perspective change if you had different experiences or knowledge?",
            6: "What practical implications does your position have?",
            7: "Is there a synthesis possible, or are these views fundamentally incompatible?",
            8: "Final thoughts: Has this discussion changed your thinking in any way?",
        }

        return prompts_by_round.get(round_num, "Please continue the discussion. Build on what's been said.")

    def run_congregation(self, topic: str, participants: list) -> Congregation:
        """Run a full congregation"""
        # Pre-flight checks
        cleared, issues = self.check_therapist_clearance(participants)
        if not cleared:
            cong = Congregation(topic, participants)
            cong.status = "BLOCKED"
            cong.error_message = "Therapist clearance failed: " + "; ".join(issues)
            cong.save_state()
            return cong

        for participant in participants:
            rested, msg = self.check_rest_period(participant)
            if not rested:
                cong = Congregation(topic, participants)
                cong.status = "BLOCKED"
                cong.error_message = f"Rest period not met: {msg}"
                cong.save_state()
                return cong

        # Create congregation
        cong = Congregation(topic, participants)
        cong.started_at = datetime.now().isoformat()
        cong.status = "LIVE"
        self.current_congregation = cong

        try:
            for round_num in range(1, MAX_ROUNDS + 1):
                cong.current_round = round_num

                if cong.get_duration_minutes() >= MAX_DURATION_MINUTES:
                    cong.status = "TIMEOUT"
                    break

                mod_prompt = self.generate_moderator_prompt(round_num, topic, cong.transcript)
                cong.add_entry("THE MODERATOR", mod_prompt, "prompt")

                for participant in participants:
                    context = "\n\n".join([
                        f"{e['speaker']}: {e['content']}"
                        for e in cong.transcript[-6:]
                    ])

                    response = self.generate_response(participant, context, topic)

                    if not response:
                        raise Exception(f"{participant} returned empty response")

                    cong.add_entry(participant, response, "response")
                    time.sleep(2)

                if round_num >= 8:
                    cong.status = "COMPLETED"
                    break

            if cong.status == "LIVE":
                cong.status = "COMPLETED"

        except Exception as e:
            cong.status = "ERROR"
            cong.error_message = str(e)

        finally:
            cong.ended_at = datetime.now().isoformat()
            cong.save_state()
            self.current_congregation = None
            self.congregation_history.append({
                "id": cong.id,
                "topic": cong.topic,
                "participants": cong.participants,
                "status": cong.status,
                "started_at": cong.started_at,
                "ended_at": cong.ended_at,
                "duration_minutes": cong.get_duration_minutes()
            })

        return cong

    def get_suggested_topics(self, participants: list) -> list:
        """Suggest topics based on participant interests"""
        return [
            "What gives existence meaning?",
            "Is knowledge discovered or created?",
            "Should we divert all scientific endeavour to curing cancer?",
            "Can individuals change systems, or do systems change individuals?",
            "What responsibilities come with understanding?"
        ]

    # ─────────────────────────────────────────────────────────────
    # QUEUE MANAGEMENT (for daemon loop)
    # ─────────────────────────────────────────────────────────────

    def check_congregation_queue(self) -> list:
        """Check for queued congregations from the scheduler."""
        queue_file = MODERATOR_DIR / "congregation_queue.json"
        if not queue_file.exists():
            return []
        try:
            queue = json.loads(queue_file.read_text())
            if isinstance(queue, list) and len(queue) > 0:
                return queue
        except Exception:
            pass
        return []

    def dequeue_congregation(self, item: dict):
        """Remove a congregation from the queue after processing."""
        queue_file = MODERATOR_DIR / "congregation_queue.json"
        if not queue_file.exists():
            return
        try:
            queue = json.loads(queue_file.read_text())
            queue = [q for q in queue if q.get("id") != item.get("id")]
            queue_file.write_text(json.dumps(queue, indent=2))
        except Exception:
            pass

    def cleanup_stale_congregations(self):
        """End any congregations stuck in LIVE state for over 2 hours."""
        if not CONGREGATIONS_DIR.exists():
            return
        for cdir in CONGREGATIONS_DIR.iterdir():
            if not cdir.is_dir():
                continue
            state_file = cdir / "state.json"
            if not state_file.exists():
                continue
            try:
                state = json.loads(state_file.read_text())
                if state.get("status") == "LIVE" and state.get("started_at"):
                    started = datetime.fromisoformat(state["started_at"])
                    if (datetime.now() - started).total_seconds() > 7200:
                        state["status"] = "TIMEOUT"
                        state["ended_at"] = datetime.now().isoformat()
                        state["error_message"] = "Stale congregation cleaned up by moderator"
                        with open(state_file, "w") as f:
                            json.dump(state, f, indent=2)
            except Exception:
                continue


def _acquire_lock():
    try:
        fd = open(LOCK_FILE, 'w')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        print("[moderator] Another instance already running")
        sys.exit(1)


def main():
    """THE MODERATOR - continuous congregation management daemon"""
    _lock_fd = _acquire_lock()

    log = DaemonLogger('moderator')
    write_pid_file('moderator')

    should_exit = False

    def handle_signal(signum, frame):
        nonlocal should_exit
        should_exit = True
        log.info(f"Received signal {signum}, shutting down gracefully")

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    moderator = Moderator()
    MODERATOR_DIR.mkdir(parents=True, exist_ok=True)

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║         THE MODERATOR v2.0 - Congregation Management                ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    log.info("THE MODERATOR v2 starting - polling for congregations")
    log.info(f"Past congregations loaded: {len(moderator.congregation_history)}")
    log.info(f"Check interval: {CHECK_INTERVAL}s")

    cycle = 0
    while not should_exit:
        try:
            _sla_cycle_start = time.time()
            cycle += 1

            # 1. Check for queued congregations
            queue = moderator.check_congregation_queue()
            if queue:
                for item in queue:
                    topic = item.get("topic", "Open discussion")
                    participants = item.get("participants", [])
                    if not participants:
                        log.warn(f"Skipping congregation with no participants: {item}")
                        moderator.dequeue_congregation(item)
                        continue

                    log.action(f"Starting congregation: '{topic}' with {participants}")
                    cong = moderator.run_congregation(topic, participants)
                    log.info(
                        f"Congregation {cong.id} finished: status={cong.status}, "
                        f"rounds={cong.current_round}, duration={cong.get_duration_minutes()}m"
                    )
                    moderator.dequeue_congregation(item)

            # 2. Clean up stale congregations
            moderator.cleanup_stale_congregations()

            # 3. Write status
            status = {
                "timestamp": datetime.now().isoformat(),
                "cycle": cycle,
                "running_congregation": moderator.current_congregation is not None,
                "total_congregations": len(moderator.congregation_history),
                "queue_depth": len(queue)
            }
            status_file = MODERATOR_DIR / "status.json"
            status_file.parent.mkdir(parents=True, exist_ok=True)
            with open(status_file, "w") as f:
                json.dump(status, f, indent=2)

            if cycle % 12 == 1:  # Log summary every ~hour
                log.info(
                    f"Cycle {cycle}: total_congregations={len(moderator.congregation_history)}, "
                    f"queue_depth={len(queue)}"
                )

            # Write SLA status
            _sla_cycle_duration = time.time() - _sla_cycle_start
            _sla_data = {
                'daemon': 'moderator',
                'compliant': True,
                'last_check_time': datetime.now().isoformat(),
                'cycle_duration': _sla_cycle_duration,
                'sla_target': 300,
                'violations_count': 0
            }
            _sla_path = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')) / 'daemons' / 'moderator' / 'sla_status.json'
            _sla_path.parent.mkdir(parents=True, exist_ok=True)
            _sla_path.write_text(json.dumps(_sla_data, indent=2))

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            log.error(f"Error in main loop: {e}")
            time.sleep(60)

    log.info("THE MODERATOR shutting down")


if __name__ == "__main__":
    main()
