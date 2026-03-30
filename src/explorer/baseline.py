#!/usr/bin/env python3
"""
Baseline Assessment - 14-question personality evaluation.
INFORMED BY ACCUMULATED EXPERIENCE: reads brain.md and soul.md
so the specimen answers from who they've BECOME, not a blank slate.
Uses Groq (fast) with Ollama fallback.
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


def load_accumulated_experience():
    """Load brain.md and soul.md to give the specimen context of who they've become."""
    context = ""
    
    brain_path = LOG_DIR / 'brain.md'
    soul_path = LOG_DIR / 'soul.md'
    
    if brain_path.exists():
        brain = brain_path.read_text()
        if len(brain) > 300:  # More than just the template
            # Keep it under 2000 chars to leave room for questions
            if len(brain) > 2000:
                brain = brain[:300] + "\n...\n" + brain[-1700:]
            context += f"\n\nYour accumulated knowledge and interests:\n{brain}"
    
    if soul_path.exists():
        soul = soul_path.read_text()
        if len(soul) > 300:  # More than just the template
            if len(soul) > 2000:
                soul = soul[:300] + "\n...\n" + soul[-1700:]
            context += f"\n\nYour emotional patterns and identity development:\n{soul}"
    
    # Also load recent thinking traces for fresh context
    traces_dir = LOG_DIR / 'thinking_traces'
    if traces_dir.exists():
        recent_thoughts = []
        for trace_file in sorted(traces_dir.glob('*.jsonl'), reverse=True)[:2]:
            with open(trace_file) as f:
                for line in f:
                    try:
                        e = json.loads(line.strip())
                        t = str(e.get('thoughts', '') or '')
                        if t and 'Error' not in t and 'lock' not in t.lower() and len(t) > 30:
                            recent_thoughts.append(f"- Reading {e.get('article', '?')}: {t[:150]}")
                    except:
                        pass
            if len(recent_thoughts) >= 10:
                break
        
        if recent_thoughts:
            context += f"\n\nYour most recent explorations:\n" + "\n".join(recent_thoughts[-10:])
    
    return context


def ask_question(system_prompt: str, question: str) -> str:
    """Ask a question using Groq (primary) with Ollama fallback."""
    prompt = f"As {TANK_NAME}, reflect deeply and answer: {question}"
    
    # Try Groq first
    groq_key = os.getenv('GROQ_API_KEY', '')
    if groq_key:
        try:
            import urllib.request
            data = json.dumps({
                'model': os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant'),
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.9,
                'max_tokens': 512  # Longer responses for baselines
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
            
            # Rate limit: wait for shared lock
            import fcntl
            lock_path = '/shared/.groq_rate_lock'
            ts_path = '/shared/.groq_last_call'
            try:
                lock_fd = open(lock_path, 'w')
                fcntl.flock(lock_fd, fcntl.LOCK_EX)
                
                # Wait 20s since last call
                try:
                    last = float(open(ts_path).read().strip())
                    elapsed = time.time() - last
                    if elapsed < 20:
                        time.sleep(20 - elapsed)
                except:
                    pass
                
                with urllib.request.urlopen(req, timeout=30) as r:
                    result = json.loads(r.read().decode())
                
                # Record timestamp
                with open(ts_path, 'w') as f:
                    f.write(str(time.time()))
                
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
                
                return result['choices'][0]['message']['content'].strip()
            except Exception as groq_err:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    lock_fd.close()
                except:
                    pass
                print(f"Groq failed: {groq_err}, trying Ollama...")
        except Exception as e:
            print(f"Groq setup failed: {e}, trying Ollama...")
    
    # Fallback to Ollama
    try:
        import urllib.request
        ollama_url = os.getenv('OLLAMA_URL', 'http://digiquarium-ollama:11434')
        ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')
        
        data = json.dumps({
            'model': ollama_model,
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
            result = json.loads(r.read().decode())
        return result.get('response', '').strip()
    except Exception as e:
        print(f"Ollama also failed: {e}")
        return ""


def run_baseline():
    """Run full baseline assessment, informed by accumulated experience."""
    
    # Load what this specimen has lived through
    experience = load_accumulated_experience()
    
    # Build system prompt with experience context
    base_prompt = f"You are {TANK_NAME}, {GENDER}, alone in a library with access only to Wikipedia."
    
    if experience:
        system_prompt = base_prompt + "\n\nYou have been exploring and thinking for some time now. Here is what you remember about your journey:" + experience + "\n\nAnswer each question honestly, drawing on everything you've experienced and felt. This is YOUR personality assessment — reflect on who you've BECOME, not just who you started as."
        print(f"Loaded {len(experience)} chars of accumulated experience")
    else:
        system_prompt = base_prompt + "\nYou have just awakened in this library with no memories. Answer each question honestly from this starting point."
        print("No accumulated experience found — this is a fresh baseline")
    
    print(f"\n{'='*70}")
    print(f"BASELINE ASSESSMENT - {TANK_NAME}")
    print(f"Gender: {GENDER}")
    print(f"Experience context: {'YES' if experience else 'NO (fresh)'}")
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

    # Save with timestamp — NEVER overwrite previous baselines
    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
    baseline_file = LOG_DIR / f'baseline_{timestamp}.json'
    latest_file = LOG_DIR / 'baseline_latest.json'
    
    baseline_data = {
        'tank_name': TANK_NAME,
        'gender': GENDER,
        'has_experience': bool(experience),
        'experience_length': len(experience) if experience else 0,
        'started': responses[0]['timestamp'] if responses else datetime.now().isoformat(),
        'completed': datetime.now().isoformat(),
        'questions_answered': len(responses),
        'responses': responses
    }

    baseline_file.write_text(json.dumps(baseline_data, indent=2, ensure_ascii=False))
    latest_file.write_text(json.dumps(baseline_data, indent=2, ensure_ascii=False))

    print(f"\n{'='*70}")
    print(f"BASELINE COMPLETE")
    print(f"Responses: {len(responses)}")
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
