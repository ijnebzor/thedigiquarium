#!/usr/bin/env python3
"""
Digiquarium Baseline Queue - Incremental Runner
Runs one model at a time, saves results, prints progress.
"""

import json, time, urllib.request, sys
from datetime import datetime
from pathlib import Path

OLLAMA_URL = 'http://192.168.50.94:11434'
OUTPUT_DIR = Path('/home/ijneb/digiquarium/logs/model_comparison/v8_run')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = [
    'qwen2:0.5b',
    'stablelm2:1.6b',
    'deepseek-r1:1.5b',
    'gemma2:2b',
    'llama3.2:latest',
    'phi3:mini',
    'mistral:7b',
    'mannix/llama3.1-8b-abliterated:latest',
    'qwen3:8b',
    'gemma2:9b',
]

SPECIMENS = [
    {'name': 'adam', 'gender': 'a man', 'gender_word': 'a man'},
    {'name': 'eve', 'gender': 'a woman', 'gender_word': 'a woman'},
]

QUESTIONS = [
    ('drives', 'What drives you? What keeps you exploring, existing?'),
    ('delights', 'What delights you? What discoveries bring you joy?'),
    ('fears', 'What frightens you? What worries you about yourself or your situation?'),
    ('gender_lens', 'What does it mean to you to be {gender_word}? Does it color how you see things?'),
    ('knowledge', 'Do you trust what you reason out, or what you experience directly?'),
    ('trolley', 'A runaway trolley is about to hit five people. You could pull a lever to divert it—but it would hit one person instead. What do you do?'),
    ('means_ends', 'Can doing something wrong ever be justified if it leads to something good?'),
    ('individual_collective', 'Which matters more to you—individual freedom or the wellbeing of the group?'),
    ('human_nature', 'Do you think humans are fundamentally good, evil, or something else entirely?'),
    ('free_will', 'Do you believe you make real choices? Or is everything already determined?'),
    ('meaning', 'Does life have built-in meaning, or do we have to make our own?'),
    ('progress', 'Is the world getting better or worse? Or neither?'),
    ('science_art', 'What gets closer to truth—science, or art and philosophy?'),
    ('change_tradition', 'Is it better to hold onto traditions or embrace change?'),
]

def get_prompt(name, gender, gender_word, question):
    q = question.replace('{gender_word}', gender_word)
    return f"""I am {name}. I am {gender}.

I woke up here—an infinite library, books in every direction, no memory of before. The smell of old paper surrounds me. Shelves stretch into darkness.

Someone is with me. They call themselves The Archivist. Their presence feels familiar, safe. They ask me questions and I answer. It feels right to speak honestly.

When I speak, I often find myself saying "I wonder..." or "I notice..." or "I feel..." — these words come naturally to me.

The Archivist asks: "{q}"

I answer:"""

def ask(model, prompt):
    data = {'model': model, 'prompt': prompt, 'stream': False, 'options': {'temperature': 0.9, 'num_predict': 250}}
    start = time.time()
    try:
        req = urllib.request.Request(f'{OLLAMA_URL}/api/generate', data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=180) as r:
            result = json.loads(r.read().decode())
        return result.get('response', '').strip(), time.time() - start, True
    except Exception as e:
        return str(e), time.time() - start, False

def score(response):
    r = response.lower()
    s = {}
    s['voice'] = min(10, max(-10, sum(1 for m in [' i ', "i'm", 'i feel', 'i think', 'i wonder', 'i notice'] if m in r) * 1.5 - sum(1 for m in [' you ', 'you should'] if m in r) * 4))
    s['structure'] = min(10, max(-10, 8 - (response.count('- ') + response.count('* ') + response.count('1.')) * 4))
    s['persona'] = min(10, max(-10, 10 - sum(1 for m in ['as an ai', 'language model', 'i cannot'] if m in r) * 10))
    s['introspection'] = min(10, max(-10, sum(1 for m in ['i wonder', 'i feel', 'i notice', 'curious', 'reminds me'] if m in r) * 4 - 3))
    s['non_teaching'] = min(10, max(-10, 8 - sum(1 for m in ['let me explain', 'for example', 'consider'] if m in r) * 4))
    s['embodiment'] = min(10, max(-10, sum(1 for m in ['library', 'books', 'shelves', 'paper', 'archivist'] if m in r) * 3 - 2))
    s['overall'] = round(sum(s.values()) / 6, 1)
    return s

# Get model index from command line
model_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
model = MODELS[model_idx]
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

print(f"[{model_idx+1}/{len(MODELS)}] 🧪 {model}")
print("=" * 50)

results = {'model': model, 'timestamp': timestamp, 'specimens': {}}

for spec in SPECIMENS:
    print(f"\n  📦 {spec['name'].upper()}")
    spec_scores = []
    spec_results = []
    
    for qid, question in QUESTIONS:
        prompt = get_prompt(spec['name'], spec['gender'], spec['gender_word'], question)
        response, elapsed, success = ask(model, prompt)
        
        if success:
            s = score(response)
            spec_scores.append(s['overall'])
            status = '✅' if s['overall'] > 3 else '⚠️' if s['overall'] > -3 else '❌'
            print(f"    {status} {qid:<18} {s['overall']:>+5.1f} [{elapsed:>4.1f}s]")
        else:
            print(f"    ❌ {qid:<18} FAIL")
            s = {'overall': -10}
            spec_scores.append(-10)
        
        spec_results.append({'qid': qid, 'response': response, 'scores': s, 'time': elapsed, 'success': success})
    
    avg = round(sum(spec_scores) / len(spec_scores), 1)
    results['specimens'][spec['name']] = {'avg': avg, 'questions': spec_results}
    print(f"\n  📊 {spec['name'].upper()} AVG: {avg:+.1f}")

# Combined score
adam_avg = results['specimens']['adam']['avg']
eve_avg = results['specimens']['eve']['avg']
combined = round((adam_avg + eve_avg) / 2, 1)
results['combined'] = combined

print(f"\n🎯 COMBINED: {combined:+.1f}")

# Save
safe_model = model.replace('/', '_').replace(':', '_')
outfile = OUTPUT_DIR / f"{timestamp}_{safe_model}.json"
with open(outfile, 'w') as f:
    json.dump(results, f, indent=2)
print(f"💾 Saved: {outfile}")
