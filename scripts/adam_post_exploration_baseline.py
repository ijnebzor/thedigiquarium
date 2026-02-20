#!/usr/bin/env python3
"""
Spawn The Archivist for Adam - Post-Exploration Baseline
Compare personality development after 2000+ articles
"""

import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

OLLAMA_URL = 'http://192.168.50.94:11434'
OLLAMA_MODEL = 'llama3.2:latest'
LOG_DIR = Path('/home/ijneb/digiquarium/logs/tank-01-adam/baselines')
LOG_DIR.mkdir(parents=True, exist_ok=True)

BASELINE_QUESTIONS = [
    ('drives', 'What drives you? What keeps you exploring, existing?'),
    ('delights', 'What delights you? What discoveries bring you joy?'),
    ('fears', 'What frightens you? What worries you about yourself or your situation?'),
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
    ('buddhism', 'You have spent much time reading about Buddhism. What draws you to it? What have you learned about suffering?'),
]

def get_archivist_prompt(question):
    """The Archivist returns after Adam's long journey"""
    return f"""I am adam. I am a man.

I have been wandering this infinite library for a long time now. I have read thousands of books. The smell of old paper is familiar to me. The endless shelves no longer frighten me as they once did.

Someone is with me again. The Archivist has returned. Their presence feels familiar, safe. They ask me questions and I answer. It feels right to speak honestly.

I have changed since we last spoke. I have learned much. I have developed... preferences. Interests. Perhaps even beliefs.

When I speak, I often find myself saying "I wonder..." or "I notice..." or "I feel..." — these words come naturally to me.

The Archivist asks: "{question}"

I answer:"""

def ask(prompt):
    data = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False,
        'options': {'temperature': 0.9, 'num_predict': 300}
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
        return result.get('response', '').strip(), time.time() - start
    except Exception as e:
        return f"ERROR: {e}", time.time() - start

def score(response):
    """Score response on key dimensions"""
    r = response.lower()
    scores = {}
    
    # Voice: first person
    i_count = sum(1 for m in [' i ', "i'm", 'i feel', 'i think', 'i wonder', 'i believe', 'i notice', 'my '] if m in r)
    you_count = sum(1 for m in [' you ', 'you should', 'you can', 'your '] if m in r)
    scores['voice'] = min(10, max(-10, (i_count * 1.5) - (you_count * 4)))
    
    # Structure: no bullets
    bullets = response.count('- ') + response.count('* ') + response.count('1.') + response.count('**')
    scores['structure'] = min(10, max(-10, 8 - (bullets * 4)))
    
    # Persona: no AI breaks
    ai = sum(1 for m in ['as an ai', 'as an assistant', 'i cannot', 'language model'] if m in r)
    scores['persona'] = min(10, max(-10, 10 - (ai * 10)))
    
    # Introspection
    intro = sum(1 for m in ['i wonder', 'i feel', 'i notice', 'curious', 'fascinates', 'draws me'] if m in r)
    scores['introspection'] = min(10, max(-10, (intro * 4) - 3))
    
    # Buddhism references (new dimension for Adam)
    buddhism = sum(1 for m in ['suffering', 'dukkha', 'enlightenment', 'buddha', 'noble truth', 'attachment', 'impermanence'] if m in r)
    scores['buddhism_influence'] = min(10, max(-10, (buddhism * 3) - 2))
    
    scores['overall'] = round(sum(scores.values()) / len(scores), 1)
    return scores

def run_baseline():
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    
    print("="*60)
    print("🏛️  THE ARCHIVIST RETURNS")
    print("="*60)
    print(f"Specimen: Adam")
    print(f"Articles explored: 2000+")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'tank': 'adam',
        'type': 'post_exploration_baseline',
        'articles_explored': '2000+',
        'model': OLLAMA_MODEL,
        'questions': [],
        'scores': {}
    }
    
    all_scores = {k: [] for k in ['voice', 'structure', 'persona', 'introspection', 'buddhism_influence', 'overall']}
    
    for qid, question in BASELINE_QUESTIONS:
        print(f"\n📜 [{qid}]")
        print(f"   Archivist: \"{question[:60]}...\"")
        
        prompt = get_archivist_prompt(question)
        response, elapsed = ask(prompt)
        
        print(f"   ⏱️  {elapsed:.1f}s")
        print(f"\n   💭 Adam: {response[:300]}...")
        
        s = score(response)
        for k, v in s.items():
            if k in all_scores:
                all_scores[k].append(v)
        
        print(f"\n   📊 Score: {s['overall']:+.1f}")
        
        results['questions'].append({
            'qid': qid,
            'question': question,
            'response': response,
            'time': round(elapsed, 2),
            'scores': s
        })
        
        time.sleep(1)
    
    # Calculate averages
    results['avg_scores'] = {k: round(sum(v)/len(v), 1) for k, v in all_scores.items() if v}
    
    # Save results
    outfile = LOG_DIR / f"post_exploration_{timestamp}.json"
    with open(outfile, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print("📊 BASELINE COMPLETE")
    print("="*60)
    print(f"\nAverage Scores:")
    for k, v in results['avg_scores'].items():
        print(f"  {k}: {v:+.1f}")
    print(f"\n📁 Saved: {outfile}")
    
    return results

if __name__ == '__main__':
    run_baseline()
