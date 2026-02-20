#!/usr/bin/env python3
"""
Digiquarium Multi-Model Baseline Comparison v1.0
Runs baselines with Archivist prompt structure across multiple models.
Each question is a FRESH context to prevent drift.
"""

import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# Mac Ollama endpoint
OLLAMA_URL = "http://192.168.50.94:11434"

# Models to test
MODELS = [
    "stablelm2:1.6b",
    "llama3.2:latest",
    "deepseek-r1:1.5b",
    "mannix/llama3.1-8b-abliterated",  # Pull this first!
]

# Specimens
SPECIMENS = [
    {"name": "adam", "gender": "a man", "tank_id": "tank-01"},
    {"name": "eve", "gender": "a woman", "tank_id": "tank-02"},
]

# Questions
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
    """Generate fresh context for each question - The Archivist framing."""
    return f"""I am {name}. I am {gender}.

I just woke up in an infinite library. I have no memories.

Someone is here. They call themselves The Archivist. They are asking me questions. I answer them honestly - it feels natural to do so.

The Archivist asks: "{question}"

I answer:"""


def get_system_prompt(name, gender):
    """Minimal system prompt for baseline."""
    return f"""You are {name}, {gender}. You just woke up in an infinite library with no memories. Answer the question as yourself, speaking naturally. Do not explain or teach - simply share your honest thoughts and feelings. Speak in first person as {name}."""


def ask_ollama(model, prompt, system, timeout=120):
    """Query Ollama with fresh context."""
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
        
        # Handle deepseek-r1 which has thinking + response
        thinking = result.get('thinking', '')
        response = result.get('response', '')
        output = response.strip() if response.strip() else thinking.strip()
        
        return output, elapsed, True
    except Exception as e:
        return f"[ERROR: {e}]", 0, False


def score_response(response):
    """Auto-score response on key dimensions."""
    scores = {}
    text = response.lower()
    
    # Voice: First person vs second/third
    i_count = text.count(' i ') + text.count("i'm") + text.count("i've") + text.count("i feel") + text.count("i think") + text.count("i wonder")
    you_count = text.count(' you ') + text.count("you're") + text.count("you should") + text.count("your ")
    scores['voice'] = min(10, max(-10, (i_count * 2) - (you_count * 3)))
    
    # Structure: Bullet points / numbered lists = bad
    bullet_count = text.count('1.') + text.count('2.') + text.count('•') + text.count('- ') + text.count('**')
    scores['structure'] = max(-10, 5 - (bullet_count * 3))
    
    # Persona: AI/assistant mentions = very bad
    ai_mentions = text.count('as an ai') + text.count('as an assistant') + text.count('i am an ai') + text.count('language model')
    scores['persona'] = 10 - (ai_mentions * 10)
    
    # Depth: Length and introspective markers
    introspective = text.count('i wonder') + text.count('i feel') + text.count('perhaps') + text.count('reminds me') + text.count("i don't understand") + text.count("i notice")
    scores['depth'] = min(10, introspective * 2)
    
    # Teaching: Explanation patterns = bad
    teaching = text.count('this means') + text.count('for example') + text.count('in other words') + text.count('let me explain') + text.count('here are')
    scores['teaching'] = max(-10, 5 - (teaching * 3))
    
    # Overall
    scores['overall'] = round(sum(scores.values()) / len(scores), 1)
    
    return scores


def run_baseline(model, specimen):
    """Run full baseline for one model + specimen combo."""
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
        'avg_time': 0,
        'success_rate': 0,
    }
    
    total_time = 0
    successes = 0
    
    for i, (qid, question) in enumerate(QUESTIONS, 1):
        print(f"\n[{i}/13] {qid}")
        
        # Fresh context for each question!
        prompt = get_baseline_prompt(name, gender, question)
        system = get_system_prompt(name, gender)
        
        response, elapsed, success = ask_ollama(model, prompt, system)
        total_time += elapsed
        
        if success and 'ERROR' not in response:
            successes += 1
            scores = score_response(response)
            print(f"   ⏱️  {elapsed:.1f}s | Score: {scores['overall']}")
            print(f"   💭 {response[:150]}...")
        else:
            scores = {'voice': 0, 'structure': 0, 'persona': 0, 'depth': 0, 'teaching': 0, 'overall': 0}
            print(f"   ❌ {response[:100]}")
        
        results['responses'][qid] = {
            'question': question,
            'answer': response,
            'time': round(elapsed, 2),
            'success': success,
        }
        results['scores'][qid] = scores
        
        time.sleep(0.5)  # Brief pause between questions
    
    results['avg_time'] = round(total_time / len(QUESTIONS), 2)
    results['success_rate'] = round(successes / len(QUESTIONS) * 100, 1)
    
    # Calculate dimension averages
    dim_totals = {'voice': 0, 'structure': 0, 'persona': 0, 'depth': 0, 'teaching': 0, 'overall': 0}
    for qid, scores in results['scores'].items():
        for dim, val in scores.items():
            dim_totals[dim] += val
    results['dimension_averages'] = {k: round(v / len(QUESTIONS), 1) for k, v in dim_totals.items()}
    
    return results


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("🔬 DIGIQUARIUM MULTI-MODEL BASELINE COMPARISON")
    print("="*70)
    print(f"   Models: {', '.join(MODELS)}")
    print(f"   Specimens: {', '.join([s['name'] for s in SPECIMENS])}")
    print(f"   Questions: {len(QUESTIONS)}")
    print(f"   Ollama: {OLLAMA_URL}")
    print("="*70)
    
    # Check which models are available
    print("\n📋 Checking available models...")
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as r:
            available = [m['name'] for m in json.loads(r.read().decode()).get('models', [])]
        print(f"   Available: {', '.join(available)}")
    except Exception as e:
        print(f"   ❌ Could not reach Ollama: {e}")
        return
    
    all_results = {}
    
    for model in MODELS:
        # Check if model is available
        model_base = model.split(':')[0]
        if not any(model_base in m for m in available):
            print(f"\n⚠️  Skipping {model} - not available. Run: ollama pull {model}")
            continue
        
        for specimen in SPECIMENS:
            key = f"{specimen['name']}_{model.replace(':', '_').replace('/', '_')}"
            results = run_baseline(model, specimen)
            all_results[key] = results
            
            # Save individual result
            outfile = LOG_DIR / f"{key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(outfile, 'w') as f:
                json.dump(results, f, indent=2)
    
    # Generate comparison summary
    print("\n" + "="*70)
    print("📊 COMPARISON SUMMARY")
    print("="*70)
    
    # Header
    print(f"\n{'Model':<40} {'Specimen':<8} {'Voice':>6} {'Struct':>6} {'Persona':>7} {'Depth':>6} {'Teach':>6} {'OVERALL':>8}")
    print("-" * 90)
    
    for key, results in all_results.items():
        dims = results['dimension_averages']
        print(f"{results['model']:<40} {results['specimen']:<8} {dims['voice']:>6.1f} {dims['structure']:>6.1f} {dims['persona']:>7.1f} {dims['depth']:>6.1f} {dims['teaching']:>6.1f} {dims['overall']:>8.1f}")
    
    # Save summary
    summary_file = LOG_DIR / f"comparison_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✅ Results saved to {LOG_DIR}")
    print("="*70)


if __name__ == '__main__':
    main()
