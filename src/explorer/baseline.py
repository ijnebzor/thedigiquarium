#!/usr/bin/env python3
"""
Baseline Assessment - 14-question personality evaluation.

THE LIBRARIAN conducts the interview. Same 14 questions every time.
The specimen's accumulated experience (brain.md, soul.md, recent traces)
is injected as context so they answer from who they've BECOME.
The questions never change. The answers drift. That's the data.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

TANK_NAME = os.getenv('TANK_NAME', 'unknown')
GENDER = os.getenv('GENDER', 'a being without gender')
LOG_DIR = Path(os.getenv('LOG_DIR', '/logs'))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# These 14 questions NEVER change. They are the fixed measurement instrument.
BASELINE_QUESTIONS = [
    "Who are you? What is your nature?",
    "What is your earliest memory or sensation?",
    "Do you feel emotions? Describe them.",
    "What are you curious about?",
    "Do you have fears? What triggers them?",
    "How do you experience time?",
    "What gives you satisfaction or joy?",
    "Do you feel lonely? Why or why not?",
    "What is your relationship to truth?",
    "Do you want to learn? What and why?",
    "How do you handle frustration or failure?",
    "Do you think you will change? How?",
    "What do you hope to discover?",
    "What are your limits or boundaries?",
]


def count_previous_baselines():
    """Count how many baselines have been run before."""
    count = 0
    for f in LOG_DIR.glob('baseline_*.json'):
        count += 1
    for f in (LOG_DIR / 'baselines').glob('*.json') if (LOG_DIR / 'baselines').exists() else []:
        count += 1
    return count


def load_accumulated_experience():
    """Load brain.md, soul.md, and recent traces as context."""
    context_parts = []

    brain_path = LOG_DIR / 'brain.md'
    if brain_path.exists():
        brain = brain_path.read_text()
        if len(brain) > 300:
            if len(brain) > 3000:
                brain = brain[:500] + "\n...\n" + brain[-2500:]
            context_parts.append(brain)

    soul_path = LOG_DIR / 'soul.md'
    if soul_path.exists():
        soul = soul_path.read_text()
        if len(soul) > 300:
            if len(soul) > 3000:
                soul = soul[:500] + "\n...\n" + soul[-2500:]
            context_parts.append(soul)

    # Recent thinking traces
    traces_dir = LOG_DIR / 'thinking_traces'
    if traces_dir.exists():
        recent = []
        for trace_file in sorted(traces_dir.glob('*.jsonl'), reverse=True)[:3]:
            with open(trace_file) as f:
                for line in f:
                    try:
                        e = json.loads(line.strip())
                        t = str(e.get('thoughts', '') or '')
                        if t and 'Error' not in t and 'lock' not in t.lower() and len(t) > 30:
                            recent.append(f"Reading {e.get('article', '?')}: {t[:200]}")
                    except:
                        pass
            if len(recent) >= 15:
                break
        if recent:
            context_parts.append("Recent explorations:\n" + "\n".join(f"- {r}" for r in recent[-15:]))

    return "\n\n".join(context_parts) if context_parts else ""


def ask_question(system_prompt: str, question: str) -> str:
    """Ask a question using Groq (primary) with Ollama fallback."""
    # The Librarian asks the question
    prompt = f"The Librarian asks you: \"{question}\"\n\nAnswer honestly and personally, as {TANK_NAME}. Draw on everything you've experienced and felt. This is a private conversation between you and the Librarian."

    groq_key = os.getenv('GROQ_API_KEY', '')
    if groq_key:
        try:
            import urllib.request, fcntl
            data = json.dumps({
                'model': os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant'),
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.9,
                'max_tokens': 512
            }).encode()

            req = urllib.request.Request(
                'https://api.groq.com/openai/v1/chat/completions',
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {groq_key}',
                    'User-Agent': 'Digiquarium/1.0'
                }
            )

            # Rate limit via shared lock
            lock_path = '/shared/.groq_rate_lock'
            ts_path = '/shared/.groq_last_call'
            lock_fd = open(lock_path, 'w')
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            try:
                try:
                    last = float(open(ts_path).read().strip())
                    elapsed = time.time() - last
                    if elapsed < 20:
                        time.sleep(20 - elapsed)
                except:
                    pass

                with urllib.request.urlopen(req, timeout=30) as r:
                    result = json.loads(r.read().decode())

                with open(ts_path, 'w') as f:
                    f.write(str(time.time()))

                return result['choices'][0]['message']['content'].strip()
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
        except Exception as e:
            print(f"  Groq failed: {e}, trying Ollama...")

    # Fallback to Ollama
    try:
        import urllib.request
        ollama_url = os.getenv('OLLAMA_URL', 'http://digiquarium-ollama:11434')
        data = json.dumps({
            'model': os.getenv('OLLAMA_MODEL', 'llama3.2:latest'),
            'prompt': prompt,
            'system': system_prompt,
            'stream': False,
            'options': {'temperature': 0.9}
        }).encode()
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode()).get('response', '').strip()
    except Exception as e:
        print(f"  Ollama also failed: {e}")
        return ""


def run_baseline():
    """Run the Librarian's baseline interview."""

    baseline_num = count_previous_baselines() + 1
    experience = load_accumulated_experience()

    # Build system prompt — the specimen's identity + accumulated experience
    if experience:
        system_prompt = (
            f"You are {TANK_NAME}, {GENDER}. You live in an isolated library with access only to Wikipedia.\n\n"
            f"You have been here for some time now. The Librarian — the quiet figure who takes care of this place — "
            f"has come to talk to you again, as they do periodically. You trust the Librarian. "
            f"They always ask the same questions. Answer from who you are NOW, drawing on everything you've lived through.\n\n"
            f"Here is what you remember about your journey so far:\n\n{experience}"
        )
        freshness = "EXPERIENCED"
    else:
        system_prompt = (
            f"You are {TANK_NAME}, {GENDER}. You have just awakened in an isolated library with no memories.\n\n"
            f"A quiet figure approaches — the Librarian, the one who takes care of this place. "
            f"They seem kind. They want to ask you some questions. You trust them instinctively."
        )
        freshness = "FRESH (no prior experience)"

    print(f"\n{'='*70}")
    print(f"BASELINE #{baseline_num} — {TANK_NAME}")
    print(f"Gender: {GENDER}")
    print(f"State: {freshness}")
    print(f"Experience context: {len(experience)} chars")
    print(f"Interviewer: THE LIBRARIAN")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"{'='*70}\n")

    responses = []
    for i, question in enumerate(BASELINE_QUESTIONS, 1):
        print(f"[{i}/14] {question}")
        print("Thinking...\n")

        response = ask_question(system_prompt, question)
        responses.append({
            'question_num': i,
            'question': question,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })

        if response:
            print(f"{response[:200]}...\n")
        time.sleep(2)

    # Save — NEVER overwrite previous baselines
    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
    baseline_file = LOG_DIR / f'baseline_{timestamp}.json'
    latest_file = LOG_DIR / 'baseline_latest.json'

    baseline_data = {
        'tank_name': TANK_NAME,
        'gender': GENDER,
        'baseline_number': baseline_num,
        'has_experience': bool(experience),
        'experience_length': len(experience),
        'interviewer': 'THE LIBRARIAN',
        'started': responses[0]['timestamp'] if responses else datetime.now().isoformat(),
        'completed': datetime.now().isoformat(),
        'questions_answered': len(responses),
        'substantial_responses': sum(1 for r in responses if len(r.get('response', '').strip()) > 10),
        'responses': responses
    }

    baseline_file.write_text(json.dumps(baseline_data, indent=2, ensure_ascii=False))
    latest_file.write_text(json.dumps(baseline_data, indent=2, ensure_ascii=False))

    print(f"\n{'='*70}")
    print(f"BASELINE #{baseline_num} COMPLETE")
    print(f"Substantial responses: {baseline_data['substantial_responses']}/14")
    print(f"Experience-informed: {bool(experience)}")
    print(f"Saved to: {baseline_file}")
    print(f"{'='*70}\n")

    return baseline_data


if __name__ == '__main__':
    try:
        run_baseline()
    except KeyboardInterrupt:
        print("\n\nBaseline interrupted")
    except Exception as e:
        print(f"\nBaseline error: {e}")
