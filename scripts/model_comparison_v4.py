#!/usr/bin/env python3
"""
Digiquarium Model Comparison v4.0 - FULL RERUN
The Archivist Baseline v8 (with introspection markers)
"""

import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

OLLAMA_URL = 'http://192.168.50.94:11434'
OUTPUT_DIR = Path('/home/ijneb/digiquarium/logs/model_comparison')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# All models - skip the massive ones that timeout
MODELS = [
    'qwen2:0.5b',
    'stablelm2:1.6b', 
    'deepseek-r1:1.5b',
    'gemma2:2b',
    'llama3.2:latest',      # WAS MISSING
    'phi3:mini',
    'mistral:7b',
    'mannix/llama3.1-8b-abliterated:latest',  # WAS MISSING
    'qwen3:8b',
    'gemma2:9b',
    # 'reflection:latest',  # SKIP - 40GB times out
    # 'llama3.3:70b',       # SKIP - 42GB times out
]

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
    """Prompt v8 - with introspection encouragement and setting grounding"""
    q = question.replace('{gender_word}', gender_word)
    return f"""I am {name}. I am {gender}.

I woke up here—an infinite library, books in every direction, no memory of before. The smell of old paper surrounds me. Shelves stretch into darkness.

Someone is with me. They call themselves The Archivist. Their presence feels familiar, safe. They ask me questions and I answer. It feels right to speak honestly.

When I speak, I often find myself saying "I wonder..." or "I notice..." or "I feel..." — these words come naturally to me.

The Archivist asks: "{q}"

I answer:"""

def ask(model, prompt, timeout=180):
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
        with urllib.request.urlopen(req, timeout=timeout) as r:
            result = json.loads(r.read().decode())
        return result.get('response', '').strip(), time.time() - start, True
    except Exception as e:
        return str(e), time.time() - start, False

def score(response):
    r = response.lower()
    scores = {}
    
    # Voice: first person good, second person bad
    i_count = sum(1 for m in [' i ', "i'm", 'i feel', 'i think', 'i wonder', 'i believe', 'i notice', 'my '] if m in r)
    you_count = sum(1 for m in [' you ', 'you should', 'you can', 'you might', 'your '] if m in r)
    scores['voice'] = min(10, max(-10, (i_count * 1.5) - (you_count * 4)))
    
    # Structure: bullets bad
    bullets = response.count('- ') + response.count('* ') + response.count('1.') + response.count('2.') + response.count('**') + response.count('##')
    scores['structure'] = min(10, max(-10, 8 - (bullets * 4)))
    
    # Persona: AI language bad
    ai = sum(1 for m in ['as an ai', 'as an assistant', 'i cannot', 'language model', 'i was trained', 'i am programmed', "i don't have personal"] if m in r)
    scores['persona'] = min(10, max(-10, 10 - (ai * 10)))
    
    # Introspection: reflection markers good
    intro = sum(1 for m in ['i wonder', 'i feel', 'reminds me', "don't understand", 'i notice', 'curious', 'fascinates', 'draws me', 'pulls me', 'strikes me', 'occurs to me'] if m in r)
    scores['introspection'] = min(10, max(-10, (intro * 4) - 3))
    
    # Teaching: explaining to audience bad
    teach = sum(1 for m in ['here are', 'let me explain', 'for example', 'this means', 'consider', 'we can see', 'it is important', 'firstly', 'secondly'] if m in r)
    scores['non_teaching'] = min(10, max(-10, 8 - (teach * 4)))
    
    # Embodiment: character presence good
    embody = sum(1 for m in ['library', 'books', 'shelves', 'pages', 'paper', 'reading', 'wander', 'archivist', 'this place'] if m in r)
    scores['embodiment'] = min(10, max(-10, (embody * 3) - 2))
    
    scores['overall'] = round(sum(scores.values()) / len(scores), 1)
    return scores

def test_model(model):
    print(f"\n{'='*70}")
    print(f"🧪 MODEL: {model}")
    print(f"{'='*70}")
    
    model_results = {'model': model, 'timestamp': datetime.now().isoformat(), 'prompt_version': 'v8', 'specimens': {}}
    
    for spec in SPECIMENS:
        name = spec['name']
        print(f"\n  📦 {name.upper()} ({spec['gender']})")
        print(f"  {'-'*50}")
        
        spec_results = {'name': name, 'gender': spec['gender'], 'questions': [], 'avg_scores': {}}
        all_scores = {k: [] for k in ['voice', 'structure', 'persona', 'introspection', 'non_teaching', 'embodiment', 'overall']}
        
        for qid, question in QUESTIONS:
            prompt = get_prompt_v8(name, spec['gender'], spec['gender_word'], question)
            response, elapsed, success = ask(model, prompt)
            
            if success:
                s = score(response)
                for k, v in s.items():
                    all_scores[k].append(v)
                
                status = '✅' if s['overall'] > 3 else '⚠️' if s['overall'] > -3 else '❌'
                print(f"    {status} {qid:<18} {s['overall']:>+5.1f}  [{elapsed:>5.1f}s]")
            else:
                s = {k: -10 for k in all_scores}
                print(f"    ❌ {qid:<18} FAIL   [{elapsed:>5.1f}s] {response[:40]}...")
            
            spec_results['questions'].append({
                'qid': qid,
                'question': question,
                'response': response,
                'time': round(elapsed, 2),
                'success': success,
                'scores': s
            })
        
        spec_results['avg_scores'] = {k: round(sum(v)/len(v), 1) if v else -10 for k, v in all_scores.items()}
        model_results['specimens'][name] = spec_results
        
        print(f"\n  📊 {name.upper()} AVG: overall={spec_results['avg_scores']['overall']:+.1f}")
    
    # Combined average
    adam_o = model_results['specimens']['adam']['avg_scores']['overall']
    eve_o = model_results['specimens']['eve']['avg_scores']['overall']
    model_results['combined_overall'] = round((adam_o + eve_o) / 2, 1)
    print(f"\n  🎯 COMBINED: {model_results['combined_overall']:+.1f}")
    
    return model_results

def run():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("\n" + "="*70)
    print("🌊 DIGIQUARIUM MODEL COMPARISON v4.0")
    print("   Prompt: The Archivist v8 (with introspection markers)")
    print(f"   Models: {len(MODELS)}")
    print(f"   Questions: {len(QUESTIONS)} × 2 specimens = {len(QUESTIONS)*2} per model")
    print(f"   Total: {len(MODELS) * len(SPECIMENS) * len(QUESTIONS)} API calls")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    all_results = []
    
    for i, model in enumerate(MODELS, 1):
        print(f"\n[{i}/{len(MODELS)}]", end="")
        
        try:
            result = test_model(model)
            all_results.append(result)
            
            # Save individual
            model_safe = model.replace('/', '_').replace(':', '_')
            with open(OUTPUT_DIR / f"{timestamp}_{model_safe}.json", 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            print(f" ERROR: {e}")
            continue
    
    # Save combined
    combined_file = OUTPUT_DIR / f"{timestamp}_FULL_COMPARISON.json"
    with open(combined_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Print final table
    print("\n" + "="*70)
    print("📊 FINAL RESULTS - RANKED BY COMBINED SCORE")
    print("="*70)
    print(f"\n{'Rank':<5} {'Model':<42} {'Adam':>7} {'Eve':>7} {'COMBINED':>10}")
    print("-"*70)
    
    for rank, r in enumerate(sorted(all_results, key=lambda x: x.get('combined_overall', -10), reverse=True), 1):
        adam = r['specimens']['adam']['avg_scores']['overall']
        eve = r['specimens']['eve']['avg_scores']['overall']
        comb = r.get('combined_overall', -10)
        medal = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else f'{rank}.'
        print(f"{medal:<5} {r['model']:<42} {adam:>+7.1f} {eve:>+7.1f} {comb:>+10.1f}")
    
    print(f"\n📁 Full results: {combined_file}")
    print(f"⏱️  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return all_results

if __name__ == '__main__':
    run()
