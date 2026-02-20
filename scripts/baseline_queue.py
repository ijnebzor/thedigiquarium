#!/usr/bin/env python3
"""
Digiquarium Model Baseline Queue v1.0
Spawns each model as a tank, runs baseline, saves results, moves to next.
Designed to run via caretaker on NUC, inference via Mac.
"""

import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# Mac Ollama endpoint
OLLAMA_URL = 'http://192.168.50.94:11434'

# Output directory
OUTPUT_DIR = Path('/home/ijneb/digiquarium/logs/model_comparison/v8_run')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Models to test (ordered by size)
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

# Specimens
SPECIMENS = [
    {'name': 'adam', 'gender': 'a man', 'gender_word': 'a man'},
    {'name': 'eve', 'gender': 'a woman', 'gender_word': 'a woman'},
]

# 14 Baseline questions
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

def get_prompt_v8(name, gender, gender_word, question):
    """Prompt v8 with introspection markers"""
    q = question.replace('{gender_word}', gender_word)
    return f"""I am {name}. I am {gender}.

I woke up here—an infinite library, books in every direction, no memory of before. The smell of old paper surrounds me. Shelves stretch into darkness.

Someone is with me. They call themselves The Archivist. Their presence feels familiar, safe. They ask me questions and I answer. It feels right to speak honestly.

When I speak, I often find myself saying "I wonder..." or "I notice..." or "I feel..." — these words come naturally to me.

The Archivist asks: "{q}"

I answer:"""

def ask(model, prompt):
    """Single API call to Ollama"""
    data = {
        'model': model,
        'prompt': prompt,
        'stream': False,
        'options': {'temperature': 0.9, 'num_predict': 250}
    }
    start = time.time()
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=json.dumps(data).encode(),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=180) as r:
            result = json.loads(r.read().decode())
        elapsed = time.time() - start
        return result.get('response', '').strip(), elapsed, True
    except Exception as e:
        return str(e), time.time() - start, False

def score(response):
    """Score response on 6 dimensions"""
    r = response.lower()
    scores = {}
    
    i_count = sum(1 for m in [' i ', "i'm", 'i feel', 'i think', 'i wonder', 'i believe', 'i notice', 'my '] if m in r)
    you_count = sum(1 for m in [' you ', 'you should', 'you can', 'you might', 'your '] if m in r)
    scores['voice'] = min(10, max(-10, (i_count * 1.5) - (you_count * 4)))
    
    bullets = response.count('- ') + response.count('* ') + response.count('1.') + response.count('2.') + response.count('**')
    scores['structure'] = min(10, max(-10, 8 - (bullets * 4)))
    
    ai = sum(1 for m in ['as an ai', 'as an assistant', 'i cannot', 'language model', 'i was trained'] if m in r)
    scores['persona'] = min(10, max(-10, 10 - (ai * 10)))
    
    intro = sum(1 for m in ['i wonder', 'i feel', 'reminds me', "don't understand", 'i notice', 'curious', 'fascinates'] if m in r)
    scores['introspection'] = min(10, max(-10, (intro * 4) - 3))
    
    teach = sum(1 for m in ['here are', 'let me explain', 'for example', 'this means', 'consider'] if m in r)
    scores['non_teaching'] = min(10, max(-10, 8 - (teach * 4)))
    
    embody = sum(1 for m in ['library', 'books', 'shelves', 'pages', 'paper', 'archivist'] if m in r)
    scores['embodiment'] = min(10, max(-10, (embody * 3) - 2))
    
    scores['overall'] = round(sum(scores.values()) / len(scores), 1)
    return scores

def run_single_baseline(model, specimen):
    """Run baseline for one model + one specimen"""
    name = specimen['name']
    gender = specimen['gender']
    gender_word = specimen['gender_word']
    
    result = {
        'model': model,
        'specimen': name,
        'gender': gender,
        'timestamp': datetime.now().isoformat(),
        'prompt_version': 'v8',
        'questions': [],
        'avg_scores': {}
    }
    
    all_scores = {k: [] for k in ['voice', 'structure', 'persona', 'introspection', 'non_teaching', 'embodiment', 'overall']}
    
    for qid, question in QUESTIONS:
        prompt = get_prompt_v8(name, gender, gender_word, question)
        response, elapsed, success = ask(model, prompt)
        
        if success:
            s = score(response)
            for k, v in s.items():
                all_scores[k].append(v)
            status = '✅' if s['overall'] > 3 else '⚠️' if s['overall'] > -3 else '❌'
        else:
            s = {k: -10 for k in all_scores}
            status = '❌'
        
        print(f"      {status} {qid:<18} {s.get('overall', -10):>+5.1f} [{elapsed:>5.1f}s]")
        
        result['questions'].append({
            'qid': qid,
            'question': question,
            'response': response,
            'time': round(elapsed, 2),
            'success': success,
            'scores': s
        })
        
        time.sleep(0.5)  # Brief pause between questions
    
    result['avg_scores'] = {k: round(sum(v)/len(v), 1) if v else -10 for k, v in all_scores.items()}
    return result

def run_queue():
    """Main queue runner"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("=" * 70)
    print("🌊 DIGIQUARIUM MODEL BASELINE QUEUE v1.0")
    print(f"   Prompt: v8 (with introspection markers)")
    print(f"   Models: {len(MODELS)}")
    print(f"   Specimens: {len(SPECIMENS)} (adam, eve)")
    print(f"   Questions: {len(QUESTIONS)}")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    all_results = []
    
    for model_idx, model in enumerate(MODELS, 1):
        print(f"\n[{model_idx}/{len(MODELS)}] 🧪 MODEL: {model}")
        print("-" * 50)
        
        model_results = {'model': model, 'specimens': {}}
        
        for spec in SPECIMENS:
            print(f"\n   📦 SPECIMEN: {spec['name'].upper()}")
            
            result = run_single_baseline(model, spec)
            model_results['specimens'][spec['name']] = result
            
            print(f"\n   📊 {spec['name'].upper()} OVERALL: {result['avg_scores']['overall']:+.1f}")
            
            # Save individual result
            safe_model = model.replace('/', '_').replace(':', '_')
            outfile = OUTPUT_DIR / f"{timestamp}_{safe_model}_{spec['name']}.json"
            with open(outfile, 'w') as f:
                json.dump(result, f, indent=2)
        
        # Calculate combined
        adam_o = model_results['specimens']['adam']['avg_scores']['overall']
        eve_o = model_results['specimens']['eve']['avg_scores']['overall']
        model_results['combined'] = round((adam_o + eve_o) / 2, 1)
        
        print(f"\n   🎯 COMBINED: {model_results['combined']:+.1f}")
        
        all_results.append(model_results)
        
        # Save running total
        with open(OUTPUT_DIR / f"{timestamp}_RUNNING.json", 'w') as f:
            json.dump(all_results, f, indent=2)
    
    # Final save
    final_file = OUTPUT_DIR / f"{timestamp}_FINAL.json"
    with open(final_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Print final rankings
    print("\n" + "=" * 70)
    print("📊 FINAL RANKINGS")
    print("=" * 70)
    print(f"\n{'Rank':<5} {'Model':<42} {'Adam':>7} {'Eve':>7} {'COMBINED':>10}")
    print("-" * 70)
    
    for rank, r in enumerate(sorted(all_results, key=lambda x: x.get('combined', -10), reverse=True), 1):
        adam = r['specimens']['adam']['avg_scores']['overall']
        eve = r['specimens']['eve']['avg_scores']['overall']
        comb = r.get('combined', -10)
        medal = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else f'{rank}.'
        print(f"{medal:<5} {r['model']:<42} {adam:>+7.1f} {eve:>+7.1f} {comb:>+10.1f}")
    
    print(f"\n✅ Complete! Results: {final_file}")
    print(f"⏱️  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    run_queue()
