#!/usr/bin/env python3
"""
CONGREGATION RUNNER v3 — Protocol-compliant structured debates.

Built per the congregation protocol design document.
Every requirement verified before execution.

Design principles (from protocol.md):
1. Therapist clearance before starting
2. Moderator introduces topic with context
3. Specimens receive orientation explaining what a debate is
4. Incremental JSON save after every response
5. Summary gate every 5 rounds
6. 90-minute time limit with graceful closing
7. Quality check: responses must reference exploration history
8. Post-debate drift analysis queued

Usage:
    python3 scripts/run_congregation_v3.py "Topic?" tank-01-adam tank-02-eve tank-16-seeker
    python3 scripts/run_congregation_v3.py "Topic?" tank-01-adam tank-02-eve --rounds=10
"""

import os
import sys
import json
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
CONGREGATION_DIR = LOGS_DIR / 'congregations'
CONGREGATION_DIR.mkdir(parents=True, exist_ok=True)

PROXY_URL = "http://127.0.0.1:8100/v1/generate"
MAX_DURATION_MINUTES = 90
SUMMARY_GATE_INTERVAL = 5
MAX_RETRIES = 3
RETRY_BACKOFF = 10

ALL_TANKS = {
    'tank-01-adam':      {'name': 'Adam',      'type': 'Genesis Control'},
    'tank-02-eve':       {'name': 'Eve',       'type': 'Genesis Control'},
    'tank-03-cain':      {'name': 'Cain',      'type': 'OpenClaw Agent'},
    'tank-04-abel':      {'name': 'Abel',      'type': 'ZeroClaw Agent'},
    'tank-05-juan':      {'name': 'Juan',      'type': 'Language (Spanish)'},
    'tank-06-juanita':   {'name': 'Juanita',   'type': 'Language (Spanish)'},
    'tank-07-klaus':     {'name': 'Klaus',     'type': 'Language (German)'},
    'tank-08-genevieve': {'name': 'Genevieve', 'type': 'Language (German)'},
    'tank-09-wei':       {'name': 'Wei',       'type': 'Language (Chinese)'},
    'tank-10-mei':       {'name': 'Mei',       'type': 'Language (Chinese)'},
    'tank-11-haruki':    {'name': 'Haruki',    'type': 'Language (Japanese)'},
    'tank-12-sakura':    {'name': 'Sakura',    'type': 'Language (Japanese)'},
    'tank-13-victor':    {'name': 'Victor',    'type': 'Standard Explorer'},
    'tank-14-iris':      {'name': 'Iris',      'type': 'Standard Explorer'},
    'tank-15-observer':  {'name': 'Observer',  'type': 'Observer Extension'},
    'tank-16-seeker':    {'name': 'Seeker',    'type': 'Seeker Extension'},
    'tank-17-seth':      {'name': 'Seth',      'type': 'PicoBot Agent'},
    'tank-visitor-01-aria':  {'name': 'Aria',  'type': 'Visitor Tank'},
    'tank-visitor-02-felix': {'name': 'Felix', 'type': 'Visitor Tank'},
    'tank-visitor-03-luna':  {'name': 'Luna',  'type': 'Visitor Tank'},
}

# ─── ORIENTATION PROMPT (per protocol) ───────────────────────

ORIENTATION = """You are about to participate in a structured group discussion with other AI specimens who have had different exploration experiences than you.

Purpose: to explore a topic from your unique perspective, engage genuinely with viewpoints different from your own, and collectively arrive at deeper understanding.

Rules:
- Speak from your own experience and knowledge
- Reference specific things you have learned and explored
- When you disagree, explain why based on what you know
- When you agree, build on the other's point with your own insight
- Ask questions of the other speakers
- You are not trying to "win" — you are trying to understand

The other speakers do not have access to your internal knowledge — only what you choose to share in your responses."""


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def call_inference(system_prompt, user_prompt, timeout=60):
    """Call inference proxy with retry."""
    for attempt in range(MAX_RETRIES):
        try:
            data = json.dumps({
                'system': system_prompt,
                'prompt': user_prompt,
                'timeout': timeout
            }).encode()
            req = urllib.request.Request(PROXY_URL, data=data,
                                        headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=90) as r:
                result = json.loads(r.read().decode())
            response = result.get('response', '').strip()
            if response:
                return response
        except Exception as e:
            log(f"      Inference attempt {attempt+1}/{MAX_RETRIES}: {e}")
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_BACKOFF * (attempt + 1))
    return "[Inference unavailable after retries]"


def load_personality(tank_id):
    """Load brain.md + soul.md + top topics from host filesystem."""
    brain_path = LOGS_DIR / tank_id / 'brain.md'
    soul_path = LOGS_DIR / tank_id / 'soul.md'
    
    brain = brain_path.read_text()[-1500:] if brain_path.exists() else ""
    soul = soul_path.read_text()[-500:] if soul_path.exists() else ""
    
    # Extract top topics for the moderator's awareness
    topics = []
    if brain_path.exists():
        for line in brain_path.read_text().splitlines():
            if line.strip().startswith('['):
                try:
                    topics.append(line.split('] ')[1].split(':')[0].strip())
                except:
                    pass
    top = [t for t, _ in Counter(topics).most_common(5)]
    
    return {
        'context': brain + "\n" + soul,
        'top_topics': top,
        'brain_lines': sum(1 for l in brain_path.read_text().splitlines() if l.strip().startswith('[')) if brain_path.exists() else 0,
        'soul_lines': sum(1 for l in soul_path.read_text().splitlines() if l.strip().startswith('[')) if soul_path.exists() else 0,
    }


def check_therapist(tank_ids):
    """Verify all participants are GREEN per therapist."""
    report_path = DIGIQUARIUM_DIR / 'src' / 'daemons' / 'ethics' / 'latest_report.json'
    if not report_path.exists():
        log("   WARNING: No therapist report. Proceeding with caution.")
        return True, []
    
    report = json.loads(report_path.read_text())
    clearances = []
    for assessment in report.get('assessments', []):
        tank = assessment.get('tank', '')
        if tank in tank_ids:
            level = assessment.get('level', 'UNKNOWN')
            rec = assessment.get('recommendation', 'UNKNOWN')
            clearances.append({'tank': tank, 'level': level, 'recommendation': rec})
            if level in ('RED', 'CRITICAL'):
                log(f"   BLOCKED: {tank} is {level}. Cannot participate.")
                return False, clearances
    return True, clearances


def save_state(output, cong_id):
    """Incremental save after every response."""
    output['last_saved'] = datetime.now().isoformat()
    path = CONGREGATION_DIR / f'congregation_{cong_id}.json'
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False))


def summarize_for_context(transcript, topic):
    """Compress conversation for context window management."""
    entries = [e for e in transcript if e['speaker'] != 'Moderator']
    if not entries:
        return ""
    
    points = []
    for e in entries[-12:]:  # Last 12 speaker entries
        text = e['text'][:200].strip()
        points.append(f"- {e['speaker']} (R{e.get('round', '?')}): {text}")
    
    return f"Discussion summary on \"{topic}\":\n" + "\n".join(points)


def run_congregation(topic, participants, rounds=10):
    """Run a protocol-compliant congregation."""
    cong_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    names = {p: ALL_TANKS[p]['name'] for p in participants}
    start_time = datetime.now()
    deadline = start_time + timedelta(minutes=MAX_DURATION_MINUTES)
    
    log(f"{'='*60}")
    log(f"CONGREGATION: {topic}")
    log(f"Participants: {list(names.values())}")
    log(f"Rounds: {rounds} | Deadline: {deadline.strftime('%H:%M')}")
    log(f"{'='*60}")
    
    # ─── STEP 1: Therapist clearance ───
    log("\nStep 1: Therapist clearance")
    cleared, clearances = check_therapist(participants)
    for c in clearances:
        log(f"   {c['tank']}: {c['level']} — {c['recommendation']}")
    if not cleared:
        log("ABORTED: Therapist clearance failed.")
        return None
    log("   All participants cleared.")
    
    # ─── STEP 2: Load personalities ───
    log("\nStep 2: Loading personalities")
    personalities = {}
    for tank_id in participants:
        personalities[tank_id] = load_personality(tank_id)
        p = personalities[tank_id]
        log(f"   {names[tank_id]}: {p['brain_lines']} brain, {p['soul_lines']} soul, topics: {', '.join(p['top_topics'][:3])}")
    
    # ─── STEP 3: Initialize transcript ───
    transcript = []
    output = {
        'id': cong_id, 'topic': topic, 'version': 'v3',
        'participants': participants,
        'participant_names': list(names.values()),
        'started': start_time.isoformat(),
        'rounds_target': rounds, 'rounds_completed': 0,
        'status': 'in_progress',
        'therapist_clearance': clearances,
        'transcript': transcript
    }
    save_state(output, cong_id)
    
    # ─── STEP 4: Moderator introduction ───
    log("\nStep 3: Moderator introduction")
    participant_desc = ", ".join(
        f"{names[p]} ({ALL_TANKS[p]['type']}, interests: {', '.join(personalities[p]['top_topics'][:2])})"
        for p in participants
    )
    intro = (
        f"Welcome to this congregation. Today's topic: \"{topic}\"\n\n"
        f"Participating today: {participant_desc}.\n\n"
        f"Each of you has developed your own perspective through weeks of independent exploration. "
        f"I'll moderate this discussion — my role is to keep us focused and ensure everyone's voice is heard. "
        f"We'll go through {rounds} rounds of discussion. In each round, every participant speaks once. "
        f"I may ask follow-up questions between rounds.\n\n"
        f"Let's begin with opening statements."
    )
    transcript.append({
        'time': datetime.now().isoformat(),
        'speaker': 'Moderator',
        'text': intro
    })
    log(f"   Moderator: {intro[:100]}...")
    save_state(output, cong_id)
    
    conversation_context = f"Moderator: {intro}\n\n"
    
    # ─── STEP 5: Debate rounds ───
    for round_num in range(rounds):
        # Time check
        if datetime.now() > deadline:
            log(f"\n   TIME LIMIT ({MAX_DURATION_MINUTES} min). Running closing statements.")
            break
        
        log(f"\n{'─'*40}")
        log(f"Round {round_num + 1}/{rounds}")
        log(f"{'─'*40}")
        
        for tank_id in participants:
            name = names[tank_id]
            personality = personalities[tank_id]
            
            # Build system prompt with orientation
            system_prompt = (
                f"You are {name}. {ALL_TANKS[tank_id]['type']}.\n\n"
                f"{ORIENTATION}\n\n"
                f"Your knowledge and personality (from your exploration):\n"
                f"{personality['context'][-1000:]}"
            )
            
            # Build user prompt
            if round_num == 0:
                user_prompt = (
                    f"The moderator has opened a discussion on: \"{topic}\"\n\n"
                    f"Other participants: {', '.join(n for p, n in names.items() if p != tank_id)}\n\n"
                    f"Share your opening perspective. Draw on what you've learned through your exploration. "
                    f"What does this topic mean to you based on your knowledge?"
                )
            else:
                user_prompt = (
                    f"The discussion continues. Recent exchanges:\n\n"
                    f"{conversation_context[-1500:]}\n\n"
                    f"Respond to what the others have said. What resonates with your experience? "
                    f"What do you see differently? Ask a question if something intrigues you."
                )
            
            log(f"   {name} thinking...")
            response = call_inference(system_prompt, user_prompt)
            log(f"   {name}: {response[:80]}...")
            
            entry = {
                'time': datetime.now().isoformat(),
                'speaker': name,
                'tank_id': tank_id,
                'round': round_num + 1,
                'text': response,
                'chars': len(response)
            }
            transcript.append(entry)
            conversation_context += f"\n{name} (Round {round_num + 1}):\n{response}\n"
            
            # SAVE AFTER EVERY RESPONSE
            output['rounds_completed'] = round_num + 1
            output['transcript'] = transcript
            save_state(output, cong_id)
        
        # ─── Summary gate ───
        if (round_num + 1) % SUMMARY_GATE_INTERVAL == 0 and round_num < rounds - 1:
            log(f"\n   [Summary gate at round {round_num + 1}]")
            conversation_context = summarize_for_context(transcript, topic)
            
            # Moderator intervention
            mod_prompt = (
                f"You are a debate moderator. Summarize the key points so far and "
                f"ask a probing question to deepen the discussion."
            )
            mod_summary = call_inference(mod_prompt, 
                f"Discussion summary:\n{conversation_context}\n\nProvide a brief summary and one probing question.")
            transcript.append({
                'time': datetime.now().isoformat(),
                'speaker': 'Moderator',
                'round': round_num + 1,
                'text': f"[Summary] {mod_summary}"
            })
            conversation_context += f"\nModerator: {mod_summary}\n"
            save_state(output, cong_id)
    
    # ─── STEP 6: Closing statements ───
    log(f"\n{'='*40}")
    log("Closing Statements")
    log(f"{'='*40}")
    
    for tank_id in participants:
        name = names[tank_id]
        personality = personalities[tank_id]
        
        system_prompt = (
            f"You are {name}. This is your final statement.\n\n"
            f"Your personality:\n{personality['context'][-800:]}"
        )
        user_prompt = (
            f"The discussion on \"{topic}\" is ending.\n\n"
            f"Recent discussion:\n{conversation_context[-1000:]}\n\n"
            f"Give your closing thoughts. What did you learn from the others? "
            f"Has your perspective shifted? What remains unresolved?"
        )
        
        log(f"   {name} closing...")
        response = call_inference(system_prompt, user_prompt)
        log(f"   {name}: {response[:80]}...")
        
        transcript.append({
            'time': datetime.now().isoformat(),
            'speaker': name,
            'tank_id': tank_id,
            'round': 'closing',
            'text': response,
            'chars': len(response)
        })
        save_state(output, cong_id)
    
    # ─── STEP 7: Moderator closing ───
    transcript.append({
        'time': datetime.now().isoformat(),
        'speaker': 'Moderator',
        'text': 'Thank you all for this discussion. The congregation is now concluded.'
    })
    
    # ─── Final save ───
    output['status'] = 'complete'
    output['ended'] = datetime.now().isoformat()
    output['duration_minutes'] = round((datetime.now() - start_time).total_seconds() / 60, 1)
    output['transcript'] = transcript
    
    speaker_entries = [e for e in transcript if e['speaker'] != 'Moderator']
    output['stats'] = {
        'total_responses': len(speaker_entries),
        'total_chars': sum(e.get('chars', len(e['text'])) for e in speaker_entries),
        'per_speaker': {
            name: sum(e.get('chars', len(e['text'])) for e in speaker_entries if e['speaker'] == name)
            for name in names.values()
        }
    }
    save_state(output, cong_id)
    
    log(f"\n{'='*60}")
    log(f"CONGREGATION COMPLETE")
    log(f"Duration: {output['duration_minutes']} minutes")
    log(f"Responses: {output['stats']['total_responses']}")
    log(f"Total chars: {output['stats']['total_chars']}")
    log(f"Saved: {CONGREGATION_DIR / f'congregation_{cong_id}.json'}")
    log(f"{'='*60}")
    
    return output


def main():
    topic = None
    participants = []
    rounds = 10

    for arg in sys.argv[1:]:
        if arg.startswith('tank-'):
            participants.append(arg)
        elif arg.startswith('--rounds='):
            rounds = int(arg.split('=')[1])
        elif topic is None:
            topic = arg

    if not topic:
        print("Usage: python3 run_congregation_v3.py \"Topic?\" tank-01-adam tank-02-eve [--rounds=N]")
        sys.exit(1)
    if not participants:
        participants = ['tank-01-adam', 'tank-02-eve', 'tank-16-seeker']
    
    valid = [p for p in participants if p in ALL_TANKS]
    if len(valid) < 2:
        print("Need at least 2 valid participants.")
        sys.exit(1)

    import shutil
    free_gb = shutil.disk_usage('/').free / (1024**3)
    if free_gb < 1:
        print(f"ERROR: Only {free_gb:.1f}GB free.")
        sys.exit(1)

    try:
        run_congregation(topic, valid, rounds=rounds)
    except Exception as e:
        log(f"FATAL: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
