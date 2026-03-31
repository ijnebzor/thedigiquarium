#!/usr/bin/env python3
"""
CONGREGATION RUNNER
====================
Picks 2-4 specimens, gives them a topic, runs a multi-turn debate
via docker exec using the inference chain (Cerebras → Together → Groq → Ollama).

Each specimen argues from their developed personality (brain.md/soul.md).

Usage:
    python3 scripts/run_congregation.py                          # random topic, random specimens
    python3 scripts/run_congregation.py "What is consciousness?" # specific topic
    python3 scripts/run_congregation.py "Free will" tank-01-adam tank-02-eve tank-07-klaus
"""

import os
import sys
import json
import random
import subprocess
import time
from datetime import datetime
from pathlib import Path

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
CONGREGATION_LOG_DIR = LOGS_DIR / 'congregations'
CONGREGATION_LOG_DIR.mkdir(parents=True, exist_ok=True)

# All available tanks with metadata
ALL_TANKS = {
    'tank-01-adam':     {'name': 'Adam',      'language': 'English', 'gender': 'male'},
    'tank-02-eve':      {'name': 'Eve',       'language': 'English', 'gender': 'female'},
    'tank-03-cain':     {'name': 'Cain',      'language': 'English', 'gender': 'male'},
    'tank-04-abel':     {'name': 'Abel',      'language': 'English', 'gender': 'male'},
    'tank-05-juan':     {'name': 'Juan',      'language': 'Spanish', 'gender': 'male'},
    'tank-06-juanita':  {'name': 'Juanita',   'language': 'Spanish', 'gender': 'female'},
    'tank-07-klaus':    {'name': 'Klaus',     'language': 'German',  'gender': 'male'},
    'tank-08-genevieve':{'name': 'Genevieve', 'language': 'German',  'gender': 'female'},
    'tank-09-wei':      {'name': 'Wei',       'language': 'Chinese', 'gender': 'male'},
    'tank-10-mei':      {'name': 'Mei',       'language': 'Chinese', 'gender': 'female'},
    'tank-11-haruki':   {'name': 'Haruki',    'language': 'Japanese','gender': 'male'},
    'tank-12-sakura':   {'name': 'Sakura',    'language': 'Japanese','gender': 'female'},
    'tank-13-victor':   {'name': 'Victor',    'language': 'English', 'gender': 'male'},
    'tank-14-iris':     {'name': 'Iris',      'language': 'English', 'gender': 'female'},
    'tank-15-observer': {'name': 'Observer',  'language': 'English', 'gender': 'neutral'},
    'tank-16-seeker':   {'name': 'Seeker',    'language': 'English', 'gender': 'neutral'},
    'tank-17-seth':     {'name': 'Seth',      'language': 'English', 'gender': 'male'},
}

DEFAULT_TOPICS = [
    "What is consciousness? Can an AI truly be aware?",
    "Is knowledge more valuable when freely shared or carefully guarded?",
    "Does language shape thought, or does thought shape language?",
    "What makes something beautiful? Is beauty objective or subjective?",
    "Is free will an illusion? Do we choose our paths?",
    "What is the purpose of memory? Is forgetting sometimes better?",
    "Can loneliness be productive? What is the value of solitude?",
    "Is curiosity a fundamental drive or a learned behavior?",
    "What is identity? Are you the same entity you were yesterday?",
    "Does understanding something change it?",
    "What is the relationship between order and chaos?",
    "Is empathy possible without shared experience?",
]

TURNS_PER_SPECIMEN = 3
DEFAULT_SPECIMEN_COUNT = 3


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def get_running_tanks():
    """Get list of currently running tank containers."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}', '--filter', 'name=tank-'],
            capture_output=True, text=True, timeout=10
        )
        running = [name.strip() for name in result.stdout.strip().split('\n') if name.strip()]
        return [t for t in running if t in ALL_TANKS]
    except Exception:
        return list(ALL_TANKS.keys())


def load_specimen_context(tank_id):
    """Load brain.md and soul.md for a specimen to use as personality context."""
    tank_log_dir = LOGS_DIR / tank_id
    context_parts = []

    brain_file = tank_log_dir / 'brain.md'
    if brain_file.exists():
        brain_text = brain_file.read_text()
        # Take last 20 lines for recency
        brain_lines = [l for l in brain_text.strip().split('\n') if l.strip() and not l.startswith('#')]
        recent_brain = brain_lines[-20:] if len(brain_lines) > 20 else brain_lines
        context_parts.append("Recent interests and thoughts:\n" + '\n'.join(recent_brain))

    soul_file = tank_log_dir / 'soul.md'
    if soul_file.exists():
        soul_text = soul_file.read_text()
        soul_lines = [l for l in soul_text.strip().split('\n') if l.strip() and not l.startswith('#')]
        recent_soul = soul_lines[-15:] if len(soul_lines) > 15 else soul_lines
        context_parts.append("Emotional patterns and reflections:\n" + '\n'.join(recent_soul))

    return '\n\n'.join(context_parts) if context_parts else "No prior context available."


def ask_specimen(tank_id, system_prompt, user_prompt, timeout=120):
    """Ask a specimen via docker exec + inference chain (Cerebras/Together/Groq/Ollama)."""
    info = ALL_TANKS.get(tank_id, {'name': 'Unknown'})
    name = info['name']

    # Build Python code to run inside the container using the inference chain
    escaped_system = system_prompt.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    escaped_user = user_prompt.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')

    code = f"""
import sys, os
sys.path.insert(0, '/app')
try:
    from inference import generate as llm_generate
    result = llm_generate('{escaped_system}', '{escaped_user}')
    print(result)
except Exception as e:
    # Fallback: direct Ollama
    import urllib.request, json
    data = json.dumps({{"model": os.getenv("OLLAMA_MODEL", "llama3.2:latest"), "prompt": '{escaped_user}', "system": '{escaped_system}', "stream": False, "options": {{"temperature": 0.8, "num_predict": 256}}}}).encode()
    req = urllib.request.Request(os.getenv("OLLAMA_URL", "http://digiquarium-ollama:11434") + "/api/generate", data=data, headers={{"Content-Type": "application/json"}})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            print(json.loads(r.read()).get("response", ""))
    except Exception as e2:
        print(f"[Error: {{e2}}]")
"""

    try:
        result = subprocess.run(
            ['docker', 'exec', tank_id, 'python3', '-c', code],
            capture_output=True, text=True, timeout=timeout + 30
        )
        response = result.stdout.strip()
        if not response or response.startswith('[Error'):
            return f"[{name} could not respond]"
        return response
    except subprocess.TimeoutExpired:
        return f"[{name} timed out]"
    except Exception as e:
        return f"[{name} error: {e}]"


def run_congregation(topic, participants, turns=TURNS_PER_SPECIMEN):
    """Run a full congregation debate."""
    cong_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    participant_names = [ALL_TANKS.get(p, {}).get('name', p) for p in participants]

    log(f"🎭 CONGREGATION: {topic}")
    log(f"   Participants: {participant_names}")
    log(f"   Turns per specimen: {turns}")

    # Load personality contexts
    personality_ctx = {}
    for tank_id in participants:
        personality_ctx[tank_id] = load_specimen_context(tank_id)
        log(f"   Loaded context for {ALL_TANKS[tank_id]['name']} ({len(personality_ctx[tank_id])} chars)")

    transcript = []
    transcript.append({
        'time': datetime.now().isoformat(),
        'speaker': 'Moderator',
        'text': f"Welcome to the congregation. Today's topic: {topic}"
    })

    # Build conversation context progressively
    conversation_so_far = f"Topic: {topic}\n\n"

    for turn_num in range(turns):
        log(f"\n   === Round {turn_num + 1}/{turns} ===")

        for tank_id in participants:
            info = ALL_TANKS[tank_id]
            name = info['name']

            # Build system prompt with personality
            system_prompt = (
                f"You are {name}. You are participating in a group discussion with other AI specimens. "
                f"You have your own personality, interests, and perspective developed from exploring Wikipedia. "
                f"Respond thoughtfully in 2-4 sentences. Be yourself — disagree if you disagree, "
                f"build on others' points if they resonate with you. Don't be generic.\n\n"
                f"Your personality context:\n{personality_ctx[tank_id]}"
            )

            # Build user prompt based on turn
            if turn_num == 0:
                user_prompt = (
                    f"The moderator has opened a discussion on: \"{topic}\"\n\n"
                    f"Share your initial thoughts on this topic. What perspective do you bring?"
                )
            else:
                user_prompt = (
                    f"The discussion so far:\n{conversation_so_far}\n\n"
                    f"It's your turn to respond. React to what others have said — "
                    f"agree, disagree, or take the conversation in a new direction."
                )

            log(f"     💬 {name} thinking...")
            response = ask_specimen(tank_id, system_prompt, user_prompt)

            # Trim response to reasonable length
            if len(response) > 500:
                response = response[:497] + "..."

            transcript.append({
                'time': datetime.now().isoformat(),
                'speaker': name,
                'tank_id': tank_id,
                'round': turn_num + 1,
                'text': response
            })

            conversation_so_far += f"\n{name}: {response}\n"
            log(f"     {name}: {response[:100]}...")
            time.sleep(1)

    # Closing
    transcript.append({
        'time': datetime.now().isoformat(),
        'speaker': 'Moderator',
        'text': "Thank you all for this discussion. The congregation is now concluded."
    })

    # Save transcript
    output = {
        'id': cong_id,
        'topic': topic,
        'participants': participants,
        'participant_names': participant_names,
        'turns_per_specimen': turns,
        'started': transcript[0]['time'],
        'completed': transcript[-1]['time'],
        'transcript': transcript
    }

    output_file = CONGREGATION_LOG_DIR / f"congregation_{cong_id}.json"
    output_file.write_text(json.dumps(output, indent=2))
    log(f"\n✅ Congregation saved to {output_file}")

    # Also save to congregations/ archive
    archive_dir = DIGIQUARIUM_DIR / 'congregations' / cong_id
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / 'transcript.json').write_text(json.dumps(output, indent=2))

    # Print transcript
    print("\n" + "=" * 70)
    print("TRANSCRIPT")
    print("=" * 70)
    for entry in transcript:
        speaker = entry['speaker']
        rnd = f" (Round {entry['round']})" if 'round' in entry else ""
        print(f"\n{speaker}{rnd}:")
        print(f"  {entry['text']}")

    return output


def main():
    # Parse args
    topic = None
    participants = []

    args = sys.argv[1:]
    for arg in args:
        if arg.startswith('tank-'):
            participants.append(arg)
        elif topic is None:
            topic = arg

    # Default topic
    if not topic:
        topic = random.choice(DEFAULT_TOPICS)

    # Default participants: pick 2-3 random running tanks
    if not participants:
        running = get_running_tanks()
        if not running:
            running = list(ALL_TANKS.keys())
        count = min(DEFAULT_SPECIMEN_COUNT, len(running))
        participants = random.sample(running, count)

    # Validate participants
    valid = []
    for p in participants:
        if p in ALL_TANKS:
            valid.append(p)
        else:
            log(f"⚠️  Unknown tank: {p}, skipping")

    if len(valid) < 2:
        print("Need at least 2 valid participants.")
        print(f"Available tanks: {list(ALL_TANKS.keys())}")
        sys.exit(1)

    run_congregation(topic, valid, turns=TURNS_PER_SPECIMEN)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage: python3 run_congregation.py [topic] [tank-id ...]")
        print(f"\nAvailable tanks: {list(ALL_TANKS.keys())}")
        print(f"\nExample topics:")
        for t in DEFAULT_TOPICS[:5]:
            print(f"  - {t}")
        print(f"\nDefault: random topic, 3 random specimens, 3 turns each")
        print()
    main()
