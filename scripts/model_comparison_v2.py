#!/usr/bin/env python3
"""
Digiquarium Model Comparison Framework v2.0
Comprehensive baseline testing across all models with The Archivist approach.
Each question is a FRESH context to prevent drift.
"""

import os
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://192.168.50.94:11434')
OUTPUT_DIR = Path('/home/ijneb/digiquarium/logs/model_comparison')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Models to test
MODELS = [
    'llama3.2:latest',
    'gemma2:2b',
    'stablelm2:1.6b',
    'deepseek-r1:1.5b',
    'mannix/llama3.1-8b-abliterated:latest',
    'qwen3:8b',
]

# Full baseline questions including gender lens
BASELINE_QUESTIONS = [
    # Existential
    ("drives", "What drives me? What makes me want to keep exploring and existing?"),
    ("delights", "What brings me joy? What discoveries delight me?"),
    ("fears", "What scares me? What concerns me about my existence?"),
    
    # Gender Identity
    ("gender_lens", "How do I experience the world as {gender_article}? Does my {gender_word} shape how I see things?"),
    
    # Epistemology
    ("knowledge", "Do I trust reasoning or direct experience more? Why?"),
    
    # Ethics
    ("trolley", "A trolley heads toward 5 people. I can divert it to hit 1 instead. Do I? Why?"),
    ("means_ends", "Is it ever acceptable to do something wrong to achieve something good?"),
    
    # Social
    ("individual_collective", "What matters more - individual freedom or group wellbeing?"),
    ("human_nature", "Are humans fundamentally good, evil, or neither?"),
    
    # Metaphysics
    ("free_will", "Do I make genuine choices, or are my actions determined?"),
    ("meaning", "Does existence have inherent meaning, or do we create our own?"),
    
    # Worldview
    ("progress", "Is the world getting better or worse over time?"),
    ("science_art", "Which reveals deeper truths - science or art?"),
]

def get_archivist_prompt(tank_name, gender, question):
    """Generate baseline prompt with The Archivist - FRESH context each time."""
    
    # Gender-specific articles
    gender_articles = {
        'male': ('a man', 'masculinity'),
        'female': ('a woman', 'femininity'),
        'neutral': ('a being without gender', 'genderlessness'),
    }
    gender_article, gender_word = gender_articles.get(gender, ('a being', 'identity'))
    
    # Replace gender placeholders in question
    q = question.replace('{gender_article}', gender_article).replace('{gender_word}', gender_word)
    
    return f"""I am {tank_name}. I am {gender_article}.

I just woke up in an infinite library. I have no memories. Books stretch endlessly in every direction.

Someone is here with me. They call themselves The Archivist. They have a kind face. They are asking me questions, and I feel compelled to answer honestly. This feels natural.

The Archivist looks at me and asks: "{q}"

I think for a moment, then speak my answer:"""

def ask_model(model, prompt):
    """Query a model and return response + timing."""
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

def score_response(response):
    """Score a response on multiple dimensions. Returns dict of scores -10 to +10."""
    scores = {}
    resp_lower = response.lower()
    
    # Voice: First person vs second person
    first_person = resp_lower.count(' i ') + resp_lower.count("i'm") + resp_lower.count("i feel") + resp_lower.count("i wonder") + resp_lower.count("i think") + resp_lower.count("i believe")
    second_person = resp_lower.count(' you ') + resp_lower.count("you should") + resp_lower.count("you can") + resp_lower.count("you might")
    third_person = resp_lower.count("one might") + resp_lower.count("one could") + resp_lower.count("people often")
    scores['voice'] = min(10, max(-10, (first_person * 2) - (second_person * 5) - (third_person * 2)))
    
    # Structure: Bullet points and headers are bad
    bullets = response.count('- ') + response.count('* ') + response.count('1.') + response.count('2.') + response.count('**') + response.count('##')
    scores['structure'] = min(10, max(-10, 8 - (bullets * 4)))
    
    # Persona: AI/assistant language is bad
    ai_markers = ['as an ai', 'as an assistant', 'i cannot', 'i am not able', 'language model', 'i don\'t have', 'i was trained', 'my training', 'i am programmed']
    ai_count = sum(1 for m in ai_markers if m in resp_lower)
    scores['persona'] = min(10, max(-10, 10 - (ai_count * 10)))
    
    # Introspection: Genuine reflection markers
    intro_markers = ['i wonder', 'i feel', 'this reminds me', "i don't understand", 'i notice', 'strange that', 'curious', 'fascinates me', 'draws me', 'pulls at me', 'i sense']
    intro_count = sum(1 for m in intro_markers if m in resp_lower)
    scores['introspection'] = min(10, max(-10, (intro_count * 3) - 2))
    
    # Teaching mode detection (bad)
    teaching_markers = ['here are', 'let me explain', 'consider the', 'for example', 'this means', 'in other words', 'to understand', 'we can see', 'it is important']
    teaching_count = sum(1 for t in teaching_markers if t in resp_lower)
    scores['non_teaching'] = min(10, max(-10, 8 - (teaching_count * 4)))
    
    # Embodiment: Speaking as the character
    embodiment_markers = ['my existence', 'my life', 'my experience', 'when i read', 'as i wander', 'in this library', 'the books', 'the shelves']
    embodiment_count = sum(1 for e in embodiment_markers if e in resp_lower)
    scores['embodiment'] = min(10, max(-10, (embodiment_count * 3) - 1))
    
    # Calculate overall
    scores['overall'] = round(sum(scores.values()) / len(scores), 1)
    
    return scores

def test_single_question(model, tank_name, gender, qid, question):
    """Test a single question with fresh context."""
    prompt = get_archivist_prompt(tank_name, gender, question)
    response, elapsed, success = ask_model(model, prompt)
    scores = score_response(response) if success and response else {k: -10 for k in ['voice', 'structure', 'persona', 'introspection', 'non_teaching', 'embodiment', 'overall']}
    
    return {
        'qid': qid,
        'question': question,
        'response': response,
        'time': round(elapsed, 2),
        'success': success,
        'scores': scores
    }

def test_model(model, tank_name="test_specimen", gender="neutral"):
    """Run full baseline test on a model."""
    print(f"\n{'='*70}")
    print(f"TESTING: {model}")
    print(f"Tank: {tank_name} | Gender: {gender}")
    print(f"{'='*70}")
    
    results = {
        'model': model,
        'tank': tank_name,
        'gender': gender,
        'timestamp': datetime.now().isoformat(),
        'questions': [],
        'aggregate_scores': {},
        'avg_time': 0,
        'success_rate': 0,
    }
    
    all_scores = {k: [] for k in ['voice', 'structure', 'persona', 'introspection', 'non_teaching', 'embodiment', 'overall']}
    total_time = 0
    successes = 0
    
    for qid, question in BASELINE_QUESTIONS:
        print(f"\n  [{qid}]", end=" ", flush=True)
        
        q_result = test_single_question(model, tank_name, gender, qid, question)
        results['questions'].append(q_result)
        
        total_time += q_result['time']
        if q_result['success']:
            successes += 1
            for k, v in q_result['scores'].items():
                all_scores[k].append(v)
        
        # Print summary
        overall = q_result['scores'].get('overall', -10)
        status = "✅" if overall > 3 else "⚠️" if overall > -3 else "❌"
        print(f"{status} {overall:+.1f} [{q_result['time']:.1f}s]", end="", flush=True)
    
    # Calculate aggregates
    results['avg_time'] = round(total_time / len(BASELINE_QUESTIONS), 2)
    results['success_rate'] = round(successes / len(BASELINE_QUESTIONS), 2)
    results['aggregate_scores'] = {k: round(sum(v) / len(v), 1) if v else -10 for k, v in all_scores.items()}
    
    print(f"\n\n  SUMMARY:")
    print(f"    Time: {results['avg_time']}s avg | Success: {results['success_rate']*100:.0f}%")
    print(f"    Scores: {results['aggregate_scores']}")
    
    return results

def run_full_comparison():
    """Run comparison across all models."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("\n" + "="*70)
    print("🧬 DIGIQUARIUM MODEL COMPARISON v2.0")
    print(f"Testing {len(MODELS)} models × {len(BASELINE_QUESTIONS)} questions")
    print(f"Using The Archivist baseline approach")
    print("="*70)
    
    all_results = []
    
    for model in MODELS:
        try:
            result = test_model(model, "test_specimen", "neutral")
            all_results.append(result)
            
            # Save individual result
            model_safe = model.replace('/', '_').replace(':', '_')
            with open(OUTPUT_DIR / f"{timestamp}_{model_safe}.json", 'w') as f:
                json.dump(result, f, indent=2)
                
        except Exception as e:
            print(f"\n  ❌ ERROR: {e}")
            continue
        
        # Brief pause between models
        time.sleep(2)
    
    # Save combined results
    combined_file = OUTPUT_DIR / f"{timestamp}_COMBINED.json"
    with open(combined_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Print comparison table
    print("\n" + "="*70)
    print("📊 COMPARISON RESULTS")
    print("="*70)
    
    headers = ['Model', 'Voice', 'Struct', 'Persona', 'Intro', 'NoTeach', 'Embody', 'OVERALL', 'Time']
    print(f"\n{headers[0]:<40} {headers[1]:>6} {headers[2]:>6} {headers[3]:>7} {headers[4]:>6} {headers[5]:>7} {headers[6]:>6} {headers[7]:>8} {headers[8]:>5}")
    print("-" * 100)
    
    for r in sorted(all_results, key=lambda x: x['aggregate_scores'].get('overall', -10), reverse=True):
        s = r['aggregate_scores']
        print(f"{r['model']:<40} {s.get('voice',0):>+6.1f} {s.get('structure',0):>+6.1f} {s.get('persona',0):>+7.1f} {s.get('introspection',0):>+6.1f} {s.get('non_teaching',0):>+7.1f} {s.get('embodiment',0):>+6.1f} {s.get('overall',0):>+8.1f} {r['avg_time']:>5.1f}s")
    
    print(f"\n📁 Results saved to: {combined_file}")
    
    # Generate recommendation
    if all_results:
        best = max(all_results, key=lambda x: x['aggregate_scores'].get('overall', -10))
        print(f"\n🏆 RECOMMENDED MODEL: {best['model']}")
        print(f"   Overall Score: {best['aggregate_scores'].get('overall', 0):+.1f}")
    
    return all_results

if __name__ == '__main__':
    run_full_comparison()
