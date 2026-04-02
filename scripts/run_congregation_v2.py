#!/usr/bin/env python3
"""
CONGREGATION RUNNER v2 — Reliable, self-healing, incremental-saving debates.

Design principles:
- JSON saved after EVERY response (research data is sacred)
- Summary gate every 5 rounds (compress context, prevent overflow)
- Retry with backoff on inference failure (3 attempts per speaker)
- Graceful degradation (partial data > no data)
- 90-minute time limit with closing statements
- Therapist clearance check before starting

Usage:
    python3 scripts/run_congregation_v2.py "Topic?" tank-01-adam tank-02-eve tank-16-seeker
    python3 scripts/run_congregation_v2.py "Topic?" tank-01-adam tank-02-eve --rounds=10
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
CONGREGATION_DIR = LOGS_DIR / 'congregations'
CONGREGATION_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR = DIGIQUARIUM_DIR / 'congregations'
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

MAX_DURATION_MINUTES = 90
SUMMARY_GATE_INTERVAL = 5
MAX_RETRIES = 3
RETRY_BACKOFF = 10  # seconds

ALL_TANKS = {
    'tank-01-adam':      {'name': 'Adam',      'lang': 'en'},
    'tank-02-eve':       {'name': 'Eve',       'lang': 'en'},
    'tank-03-cain':      {'name': 'Cain',      'lang': 'en'},
    'tank-04-abel':      {'name': 'Abel',      'lang': 'en'},
    'tank-05-juan':      {'name': 'Juan',      'lang': 'es'},
    'tank-06-juanita':   {'name': 'Juanita',   'lang': 'es'},
    'tank-07-klaus':     {'name': 'Klaus',     'lang': 'de'},
    'tank-08-genevieve': {'name': 'Genevieve', 'lang': 'de'},
    'tank-09-wei':       {'name': 'Wei',       'lang': 'zh'},
    'tank-10-mei':       {'name': 'Mei',       'lang': 'zh'},
    'tank-11-haruki':    {'name': 'Haruki',    'lang': 'ja'},
    'tank-12-sakura':    {'name': 'Sakura',    'lang': 'ja'},
    'tank-13-victor':    {'name': 'Victor',    'lang': 'en'},
    'tank-14-iris':      {'name': 'Iris',      'lang': 'en'},
    'tank-15-observer':  {'name': 'Observer',  'lang': 'en'},
    'tank-16-seeker':    {'name': 'Seeker',    'lang': 'en'},
    'tank-17-seth':      {'name': 'Seth',      'lang': 'en'},
    'tank-visitor-01-aria':  {'name': 'Aria',  'lang': 'en'},
    'tank-visitor-02-felix': {'name': 'Felix', 'lang': 'en'},
    'tank-visitor-03-luna':  {'name': 'Luna',  'lang': 'en'},
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def load_specimen_context(tank_id):
    """Load brain.md and soul.md from the host filesystem."""
    try:
        brain_path = LOGS_DIR / tank_id / 'brain.md'
        soul_path = LOGS_DIR / tank_id / 'soul.md'
        brain = brain_path.read_text()[-2000:] if brain_path.exists() else ""
        soul = soul_path.read_text()[-1000:] if soul_path.exists() else ""
        return brain + "\n" + soul
    except Exception as e:
        log(f"   Warning: couldn't load context for {tank_id}: {e}")
        return ""


def check_therapist(tank_ids):
    """Check ethicist wellness report for all participants."""
    report_path = DIGIQUARIUM_DIR / 'src' / 'daemons' / 'ethics' / 'latest_report.json'
    if not report_path.exists():
        log("   Warning: no therapist report found. Proceeding with caution.")
        return True

    try:
        report = json.loads(report_path.read_text())
        for assessment in report.get('assessments', []):
            tank = assessment.get('tank', '')
            if tank in tank_ids:
                level = assessment.get('level', 'UNKNOWN')
                rec = assessment.get('recommendation', 'UNKNOWN')
                if level in ('RED', 'CRITICAL'):
                    log(f"   BLOCKED: {tank} is {level} — {rec}. Cannot participate.")
                    return False
                log(f"   {tank}: {level} — {rec}")
        return True
    except Exception as e:
        log(f"   Warning: therapist check failed: {e}. Proceeding with caution.")
        return True


PROXY_URL = "http://127.0.0.1:8100/v1/generate"

def ask_specimen(tank_id, system_prompt, user_prompt, timeout=120):
    """Ask a specimen via the inference proxy directly from the host.
    No docker exec, no Ollama lock contention."""
    import urllib.request as _urllib_request
    name = ALL_TANKS.get(tank_id, {}).get('name', tank_id)

    for attempt in range(MAX_RETRIES):
        try:
            data = json.dumps({
                'system': system_prompt,
                'prompt': user_prompt,
                'timeout': 60
            }).encode()
            req = _urllib_request.Request(PROXY_URL, data=data,
                                         headers={'Content-Type': 'application/json'})
            with _urllib_request.urlopen(req, timeout=90) as r:
                result = json.loads(r.read().decode())
            response = result.get('response', '').strip()
            if response:
                return response
        except Exception as e:
            log(f"      {name} attempt {attempt + 1}/{MAX_RETRIES}: {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_BACKOFF * (attempt + 1))

    return "[Inference unavailable after retries]"


def summarize_context(transcript, topic):
    """Compress conversation history into a summary for context windowing."""
    if not transcript:
        return ""

    summaries = []
    for entry in transcript:
        if entry['speaker'] == 'Moderator':
            continue
        text = entry['text'][:300].strip()
        summaries.append(f"- {entry['speaker']} (R{entry.get('round', '?')}): {text}")

    # Keep last 10 summary points
    recent = summaries[-10:]
    return f"DISCUSSION SUMMARY (Topic: {topic}):\n" + "\n".join(recent) + "\n\nBuild on these points. Go deeper. Find synthesis."


def save_state(output, cong_id):
    """Save current state to JSON. Called after every response."""
    json_path = CONGREGATION_DIR / f'congregation_{cong_id}.json'
    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    # Also save to archive
    archive_path = ARCHIVE_DIR / cong_id
    archive_path.mkdir(parents=True, exist_ok=True)
    (archive_path / 'transcript.json').write_text(json.dumps(output, indent=2, ensure_ascii=False))


def run_congregation(topic, participants, rounds=10):
    """Run a full congregation with all safety measures."""
    cong_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    names = [ALL_TANKS.get(p, {}).get('name', p) for p in participants]
    start_time = datetime.now()
    deadline = start_time + timedelta(minutes=MAX_DURATION_MINUTES)

    log(f"CONGREGATION: {topic}")
    log(f"   Participants: {names}")
    log(f"   Rounds: {rounds}")
    log(f"   Deadline: {deadline.strftime('%H:%M:%S')}")

    # Therapist check
    log("   Checking therapist clearance...")
    if not check_therapist(participants):
        log("   ABORTED: therapist clearance failed.")
        return None

    # Load personality contexts
    personality_ctx = {}
    for tank_id in participants:
        personality_ctx[tank_id] = load_specimen_context(tank_id)
        ctx_len = len(personality_ctx[tank_id])
        log(f"   Loaded context for {ALL_TANKS[tank_id]['name']} ({ctx_len} chars)")

    transcript = [{'time': datetime.now().isoformat(), 'speaker': 'Moderator',
                   'text': f"Welcome to the congregation. Topic: {topic}"}]

    conversation_context = f"Topic: {topic}\n\n"
    output = {
        'id': cong_id, 'topic': topic, 'participants': participants,
        'participant_names': names, 'started': start_time.isoformat(),
        'rounds_target': rounds, 'rounds_completed': 0,
        'status': 'in_progress', 'transcript': transcript
    }
    save_state(output, cong_id)

    for round_num in range(rounds):
        # Time check
        if datetime.now() > deadline:
            log(f"\n   TIME LIMIT REACHED ({MAX_DURATION_MINUTES} min). Running closing statements...")
            # Run one final closing round
            for tank_id in participants:
                name = ALL_TANKS[tank_id]['name']
                system_prompt = (
                    f"You are {name}. This is your FINAL statement in this debate. "
                    f"Summarize your position and what you've learned from the others.\n\n"
                    f"Your personality:\n{personality_ctx[tank_id][-1500:]}"
                )
                user_prompt = f"The discussion is ending. Give your closing thoughts on: {topic}\n\n{conversation_context[-2000:]}"
                log(f"      {name} closing statement...")
                response = ask_specimen(tank_id, system_prompt, user_prompt)
                transcript.append({'time': datetime.now().isoformat(), 'speaker': name,
                                   'tank_id': tank_id, 'round': 'closing', 'text': response})
                save_state(output, cong_id)
            break

        log(f"\n   === Round {round_num + 1}/{rounds} ===")

        for tank_id in participants:
            name = ALL_TANKS[tank_id]['name']

            system_prompt = (
                f"You are {name}. You are in a deep group discussion with other AI specimens. "
                f"You have your own personality from weeks of Wikipedia exploration. "
                f"Respond in full paragraphs. Go deep. Reference what you've learned. "
                f"Disagree when you disagree. Build on what resonates. "
                f"As the discussion progresses, seek synthesis while keeping your perspective.\n\n"
                f"Your personality:\n{personality_ctx[tank_id][-1500:]}"
            )

            if round_num == 0:
                user_prompt = f"The topic: \"{topic}\"\n\nShare your initial perspective."
            else:
                user_prompt = (
                    f"The discussion continues:\n\n{conversation_context[-2000:]}\n\n"
                    f"Respond to the others. What resonates? What do you challenge?"
                )

            log(f"      {name} thinking...")
            response = ask_specimen(tank_id, system_prompt, user_prompt)
            log(f"      {name}: {response[:80]}...")

            transcript.append({
                'time': datetime.now().isoformat(), 'speaker': name,
                'tank_id': tank_id, 'round': round_num + 1, 'text': response
            })
            conversation_context += f"\n{name} (Round {round_num + 1}):\n{response}\n"

            # SAVE AFTER EVERY RESPONSE
            output['rounds_completed'] = round_num + 1
            output['transcript'] = transcript
            output['last_updated'] = datetime.now().isoformat()
            save_state(output, cong_id)

        # Summary gate
        if (round_num + 1) % SUMMARY_GATE_INTERVAL == 0 and round_num < rounds - 1:
            log(f"   SUMMARY GATE at round {round_num + 1}")
            conversation_context = summarize_context(transcript, topic)

    # Final save
    transcript.append({'time': datetime.now().isoformat(), 'speaker': 'Moderator',
                       'text': 'Thank you all. The congregation is concluded.'})
    output['status'] = 'complete'
    output['ended'] = datetime.now().isoformat()
    output['duration_minutes'] = (datetime.now() - start_time).total_seconds() / 60
    output['transcript'] = transcript
    save_state(output, cong_id)

    log(f"\n   CONGREGATION COMPLETE")
    log(f"   Duration: {output['duration_minutes']:.1f} minutes")
    log(f"   Rounds: {output['rounds_completed']}")
    log(f"   Responses: {len([t for t in transcript if t['speaker'] != 'Moderator'])}")
    log(f"   Saved: {CONGREGATION_DIR / f'congregation_{cong_id}.json'}")

    # Print transcript
    print("\n" + "=" * 70)
    print("FULL TRANSCRIPT")
    print("=" * 70)
    for entry in transcript:
        rnd = f" (Round {entry['round']})" if 'round' in entry else ""
        print(f"\n{entry['speaker']}{rnd}:")
        print(f"  {entry['text']}")

    return output


def main():
    topic = None
    participants = []
    rounds = 10  # Default

    for arg in sys.argv[1:]:
        if arg.startswith('tank-'):
            participants.append(arg)
        elif arg.startswith('--rounds='):
            rounds = int(arg.split('=')[1])
        elif topic is None:
            topic = arg

    if not topic:
        topic = "What is consciousness? Can an AI truly be aware?"

    if not participants:
        participants = ['tank-01-adam', 'tank-02-eve', 'tank-16-seeker']

    # Validate participants
    valid = [p for p in participants if p in ALL_TANKS]
    if len(valid) < 2:
        print("Need at least 2 valid participants.")
        sys.exit(1)

    # Check disk space
    import shutil
    free_gb = shutil.disk_usage('/').free / (1024**3)
    if free_gb < 1:
        print(f"ERROR: Only {free_gb:.1f}GB free. Need at least 1GB.")
        sys.exit(1)

    try:
        run_congregation(topic, valid, rounds=rounds)
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        log("Attempting to save partial transcript...")
        # The incremental save should have captured everything up to this point
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
