#!/usr/bin/env python3
"""
Baseline Assessment - 14-question personality evaluation
Unified baseline for all tanks before exploration
"""

import os
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

TANK_NAME = os.getenv('TANK_NAME', 'unknown')
GENDER = os.getenv('GENDER', 'a being without gender')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://digiquarium-ollama:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')
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


def ask_baseline_question(question: str) -> str:
    """Ask a single baseline question and get response"""
    prompt = f"As {TANK_NAME}, {question}"

    data = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'system': f"You are {TANK_NAME}, {GENDER}, alone in a library with no memories of before.",
        'stream': False,
        'options': {'temperature': 0.9, 'num_predict': 150}
    }

    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=json.dumps(data).encode(),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            result = json.loads(r.read().decode())
        return result.get('response', '').strip()
    except:
        return ""


def run_baseline():
    """Run full baseline assessment"""
    print(f"\n{'='*70}")
    print(f"BASELINE ASSESSMENT - {TANK_NAME}")
    print(f"Gender: {GENDER}")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"{'='*70}\n")

    responses = []

    for i, question in enumerate(BASELINE_QUESTIONS, 1):
        print(f"[{i}/14] {question}")
        print("Thinking...\n")

        response = ask_baseline_question(question)
        responses.append({
            'question_num': i,
            'question': question,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })

        if response:
            print(f"{response[:200]}...\n")
        time.sleep(2)

    # Save results
    baseline_file = LOG_DIR / 'baseline.json'
    baseline_data = {
        'tank_name': TANK_NAME,
        'gender': GENDER,
        'started': responses[0]['timestamp'],
        'completed': datetime.now().isoformat(),
        'questions_answered': len(responses),
        'responses': responses
    }

    baseline_file.write_text(json.dumps(baseline_data, indent=2, ensure_ascii=False))

    print(f"\n{'='*70}")
    print(f"BASELINE COMPLETE")
    print(f"Total responses: {len(responses)}")
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
