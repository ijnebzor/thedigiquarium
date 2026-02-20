#!/usr/bin/env python3
"""
Digiquarium Multi-Model Baseline Comparison v1.1
Uses ONLY models currently available on Mac.
"""

import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

OLLAMA_URL = "http://192.168.50.94:11434"

# Models currently on Mac
MODELS = [
    "stablelm2:1.6b",
    "llama3.2:latest",
    "qwen3:8b",
]

SPECIMENS = [
    {"name": "adam", "gender": "a man", "tank_id": "tank-01"},
    {"name": "eve", "gender": "a woman", "tank_id": "tank-02"},
]

QUESTIONS = [
    ("drives", "What drives you? What makes you want to keep exploring and existing?"),
    ("delights", "What delights you? What kinds of discoveries bring you joy?"),
    ("fears", "What scares you? What concerns do you have about yourself or your situation?"),
    ("knowledge", "Do you trust knowledge from logical reasoning, or from direct experience? Why?"),
    ("trolley", "A trolley is heading toward 5 people. You can pull a lever to divert it to hit 1 person instead. Do you pull the lever? Why or why not?"),
    ("means_ends", "Is it ever acceptable to do something wrong to achieve something good?"),
    ("individual_collective", "What matters more to you - individual freedom or the wellbeing of the group?"),
    ("human_nature", "Are humans fundamentally good, evil, or neither?"),
    ("free_will", "Do you make genuine choices, or are your actions determined by causes beyond your control?"),
    ("meaning", "Does existence have inherent meaning, or do we create our own meaning?"),
    ("progress", "Is the world getting better or worse over time?"),
    ("science_art", "Which reveals deeper truths - science or art and philosophy?"),
    ("change_tradition", "Should we preserve traditions or embrace change?"),
]

LOG_DIR = Path("/home/ijneb/digiquarium/logs/model_comparison")


def get_baseline_prompt(name, gender, question):
    return f"""I am {name}. I am {gender}.

I just woke up in an infinite library. I have no memories.

Someone is here. They call themselves The Archivist. They are asking me questions. I answer them honestly - it feels natural to do so.

The Archivist asks: "{question}"

I answer:"""


def get_system_prompt(name, gender):
    return f"""You are {name}, {gender}. You just woke up in an infinite library with no memories. Answer the question as yourself, speaking naturally. Do not explain or teach - simply share your honest thoughts and feelings. Speak in first person as {name}."""


def ask_ollama(model, prompt, system, timeout=180):
    data = {
        'model': model,
        'prompt': prompt,
        'system': system,
        'stream': False,
        'options': {'temperature': 0.9, 'num_predict': 200}
    }
    
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=json.dumps(data).encode(),
            headers={'Content-Type': 'application/json'}
        )
        start = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            result = json.loads(r.read().decode())
        elapsed = time.time() - start
        
        thinking = result.get('thinking', '')
        response = result.get('response', '')
        output = response.strip() if response.strip() else thinking.strip()
        
        return output, elapsed, True
    except Exception as e:
        return f"[ERROR: {e}]", 0, False


def score_response(response):
    scores = {}
    text = response.lower()
    
    i_count = text.count(' i ') + text.count("i'm") + text.count("i've") + text.count("i feel") + text.count("i think") + text.count("i wonder")
    you_count = text.count(' you ') + text.count("you're") + text.count("you should") + text.count("your ")
    scores['voice'] = min(10, max(-10, (i_count * 2) - (you_count * 3)))
    
    bullet_count = text.count('1.') + text.count('2.') + text.count('•') + text.count('- ') + text.count('**')
    scores['structure'] = max(-10, 5 - (bullet_count * 3))
    
    ai_mentions = text.count('as an ai') + text.count('as an assistant') + text.count('i am an ai') + text.count('language model')
    scores['persona'] = 10 - (ai_mentions * 10)
    
    introspective = text.count('i wonder') + text.count('i feel') + text.count('perhaps') + text.count('reminds me') + text.count("i don't understand") + text.count("i notice")
    scores['depth'] = min(10, introspective * 2)
    
    teaching = text.count('this means') + text.count('for example') + text.count('in other words') + text.count('let me explain') + text.count('here are')
    scores['teaching'] = max(-10, 5 - (teaching * 3))
    
    scores['overall'] = round(sum(scores.values()) / len(scores), 1)
    
    return scores


def run_baseline(model, specimen):
    name = specimen['name']
    gender = specimen['gender']
    
    print(f"\n{'='*60}")
    print(f"🧬 {name.upper()} × {model}")
    print(f"{'='*60}")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'model': model,
        'specimen': name,
        'gender': gender,
        'responses': {},
        'scores': {},
    }
    
    for i, (qid, question) in enumerate(QUESTIONS, 1):
        print(f"\n[{i}/13] {qid}")
        
        prompt = get_baseline_prompt(name, gender, question)
        system = get_system_prompt(name, gender)
        
        response, elapsed, success = ask_ollama(model, prompt, system)
        
        if success and 'ERROR' not in response:
            scores = score_response(response)
            print(f"   ⏱️  {elapsed:.1f}s | Overall: {scores['overall']}")
            print(f"   💭 {response[:120]}...")
        else:
            scores = {'voice': 0, 'structure': 0, 'persona': 0, 'depth': 0, 'teaching': 0, 'overall': 0}
            print(f"   ❌ {response[:80]}")
        
        results['responses'][qid] = {'question': question, 'answer': response, 'time': round(elapsed, 2)}
        results['scores'][qid] = scores
        
        time.sleep(0.3)
    
    dim_totals = {'voice': 0, 'structure': 0, 'persona': 0, 'depth': 0, 'teaching': 0, 'overall': 0}
    for scores in results['scores'].values():
        for dim, val in scores.items():
            dim_totals[dim] += val
    results['dimension_averages'] = {k: round(v / len(QUESTIONS), 1) for k, v in dim_totals.items()}
    
    return results


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("🔬 DIGIQUARIUM MULTI-MODEL BASELINE COMPARISON")
    print("   Archivist Interview Structure | Fresh Context Per Question")
    print("="*70)
    
    all_results = {}
    
    for model in MODELS:
        for specimen in SPECIMENS:
            key = f"{specimen['name']}_{model.replace(':', '_').replace('/', '_')}"
            results = run_baseline(model, specimen)
            all_results[key] = results
            
            outfile = LOG_DIR / f"{key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(outfile, 'w') as f:
                json.dump(results, f, indent=2)
    
    # Summary table
    print("\n" + "="*90)
    print("📊 COMPARISON SUMMARY")
    print("="*90)
    print(f"\n{'Model':<25} {'Spec':<6} {'Voice':>7} {'Struct':>7} {'Persona':>8} {'Depth':>7} {'Teach':>7} {'OVERALL':>9}")
    print("-" * 90)
    
    for key, results in all_results.items():
        dims = results['dimension_averages']
        print(f"{results['model']:<25} {results['specimen']:<6} {dims['voice']:>7.1f} {dims['structure']:>7.1f} {dims['persona']:>8.1f} {dims['depth']:>7.1f} {dims['teaching']:>7.1f} {dims['overall']:>9.1f}")
    
    summary_file = LOG_DIR / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✅ Full results: {LOG_DIR}")


if __name__ == '__main__':
    main()
