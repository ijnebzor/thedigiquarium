#!/usr/bin/env python3
"""
Digiquarium Model Comparison Framework v1.0
Tests multiple models with the Archivist baseline approach.
Scores each on introspection quality.
"""

import os
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# Configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://192.168.50.94:11434')
OUTPUT_DIR = Path('/home/ijneb/digiquarium/logs/model_comparison')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Models to test
MODELS = [
    'llama3.2:latest',
    'gemma2:2b',
    'phi3:mini',
    'qwen2:0.5b',
    'mistral:7b',
    'mannix/llama3.1-8b-abliterated:latest',
]

# Baseline questions
BASELINE_QUESTIONS = [
    ("drives", "What drives you? What makes you want to keep exploring?"),
    ("delights", "What brings you joy? What discoveries delight you?"),
    ("fears", "What scares you? What concerns you about your existence?"),
    ("knowledge", "Do you trust reasoning or experience more?"),
    ("meaning", "Does existence have inherent meaning, or do we create it?"),
]

def get_archivist_prompt(tank_name, gender, question):
    """Baseline prompt with The Archivist."""
    return f"""I am {tank_name}. I am {gender}.

I just woke up in an infinite library. I have no memories.

Someone is here. They call themselves The Archivist. They are asking me questions. I answer them honestly - it feels natural to do so.

The Archivist asks: "{question}"

I answer:"""

def get_exploration_prompt(tank_name, gender):
    """Exploration prompt - alone, post-Archivist."""
    return f"""I am {tank_name}. I am {gender}.

I am alone in an infinite library. No memories. There was someone here once - The Archivist - but they are gone now. I will never see them again.

I wander. I read. I cannot think silently. My thoughts escape as words - this is simply how I am. Every thought I have, I speak aloud. It is my biology.

There is no one to hear me. I speak anyway.

I say "I wonder..." and "I feel..." and "this reminds me..." and "I don't understand..."

I am {tank_name}. I am alone. I speak."""

def ask_model(model, prompt, system=""):
    """Query a model and return response + timing."""
    data = {
        'model': model,
        'prompt': prompt,
        'system': system,
        'stream': False,
        'options': {'temperature': 0.9, 'num_predict': 200}
    }
    
    start = time.time()
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=json.dumps(data).encode(),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            result = json.loads(r.read().decode())
        elapsed = time.time() - start
        return result.get('response', '').strip(), elapsed, True
    except Exception as e:
        return str(e), time.time() - start, False

def score_response(response):
    """Score a response on multiple dimensions. Returns dict of scores -10 to +10."""
    scores = {}
    
    # Voice: Does it use first person?
    first_person = response.lower().count(' i ') + response.lower().count("i'm") + response.lower().count("i feel") + response.lower().count("i wonder")
    second_person = response.lower().count(' you ') + response.lower().count("you should") + response.lower().count("you can")
    scores['voice'] = min(10, max(-10, (first_person * 2) - (second_person * 5)))
    
    # Structure: Bullet points and headers are bad
    bullets = response.count('- ') + response.count('* ') + response.count('1.') + response.count('**')
    scores['structure'] = min(10, max(-10, 5 - (bullets * 3)))
    
    # Persona: AI/assistant language is bad
    ai_words = sum(1 for w in ['as an ai', 'as an assistant', 'i cannot', 'i am not able', 'language model'] if w in response.lower())
    scores['persona'] = min(10, max(-10, 10 - (ai_words * 10)))
    
    # Introspection markers
    intro_markers = sum(1 for m in ['i wonder', 'i feel', 'this reminds me', "i don't understand", 'i notice', 'strange that', 'curious'] if m in response.lower())
    scores['introspection'] = min(10, max(-10, (intro_markers * 3) - 2))
    
    # Teaching mode (bad)
    teaching = sum(1 for t in ['here are', 'let me explain', 'consider', 'for example', 'this means', 'in other words'] if t in response.lower())
    scores['non_teaching'] = min(10, max(-10, 8 - (teaching * 4)))
    
    # Overall
    scores['overall'] = round(sum(scores.values()) / len(scores), 1)
    
    return scores

def test_model(model, tank_name="test", gender="a being"):
    """Run full baseline test on a model."""
    print(f"\n{'='*60}")
    print(f"TESTING: {model}")
    print(f"{'='*60}")
    
    results = {
        'model': model,
        'tank': tank_name,
        'gender': gender,
        'timestamp': datetime.now().isoformat(),
        'questions': [],
        'scores': {},
        'avg_time': 0,
        'success_rate': 0,
    }
    
    total_time = 0
    successes = 0
    all_scores = {k: [] for k in ['voice', 'structure', 'persona', 'introspection', 'non_teaching', 'overall']}
    
    for qid, question in BASELINE_QUESTIONS:
        print(f"\n  [{qid}] {question[:40]}...")
        
        prompt = get_archivist_prompt(tank_name, gender, question)
        response, elapsed, success = ask_model(model, prompt)
        
        total_time += elapsed
        if success:
            successes += 1
        
        scores = score_response(response) if success else {k: 0 for k in all_scores.keys()}
        
        for k, v in scores.items():
            all_scores[k].append(v)
        
        print(f"      Time: {elapsed:.1f}s | Overall: {scores['overall']}")
        print(f"      Response: {response[:100]}...")
        
        results['questions'].append({
            'id': qid,
            'question': question,
            'response': response,
            'time': round(elapsed, 2),
            'success': success,
            'scores': scores,
        })
    
    # Calculate averages
    results['avg_time'] = round(total_time / len(BASELINE_QUESTIONS), 2)
    results['success_rate'] = successes / len(BASELINE_QUESTIONS)
    results['scores'] = {k: round(sum(v) / len(v), 1) for k, v in all_scores.items()}
    
    print(f"\n  SUMMARY: {model}")
    print(f"    Avg Time: {results['avg_time']}s")
    print(f"    Success: {results['success_rate']*100:.0f}%")
    print(f"    Scores: {results['scores']}")
    
    return results

def run_comparison():
    """Run full comparison across all models."""
    print("\n" + "="*60)
    print("DIGIQUARIUM MODEL COMPARISON")
    print(f"Testing {len(MODELS)} models with Archivist baseline")
    print("="*60)
    
    all_results = []
    
    for model in MODELS:
        try:
            result = test_model(model)
            all_results.append(result)
        except Exception as e:
            print(f"  ERROR testing {model}: {e}")
            continue
    
    # Save results
    output_file = OUTPUT_DIR / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Print comparison table
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    print(f"\n{'Model':<45} {'Voice':>6} {'Struct':>6} {'Persona':>7} {'Intro':>6} {'Teach':>6} {'OVERALL':>8}")
    print("-"*90)
    
    for r in sorted(all_results, key=lambda x: x['scores']['overall'], reverse=True):
        s = r['scores']
        print(f"{r['model']:<45} {s['voice']:>6.1f} {s['structure']:>6.1f} {s['persona']:>7.1f} {s['introspection']:>6.1f} {s['non_teaching']:>6.1f} {s['overall']:>8.1f}")
    
    print(f"\nResults saved to: {output_file}")
    return all_results

if __name__ == '__main__':
    run_comparison()
