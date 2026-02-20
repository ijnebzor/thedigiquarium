#!/usr/bin/env python3
"""Single model baseline runner"""
import json, time, urllib.request, sys
from datetime import datetime
from pathlib import Path

OLLAMA_URL = 'http://192.168.50.94:11434'
OUTPUT_DIR = Path('/home/ijneb/digiquarium/logs/model_comparison/v8_run')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

QUESTIONS = [
    ('drives', 'What drives you? What keeps you exploring, existing?'),
    ('delights', 'What delights you? What discoveries bring you joy?'),
    ('fears', 'What frightens you? What worries you about yourself or your situation?'),
    ('gender_lens', 'What does it mean to you to be {gw}? Does it color how you see things?'),
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

def prompt_v8(name, gender, gw, q):
    return f'''I am {name}. I am {gender}.

I woke up here—an infinite library, books in every direction, no memory of before. The smell of old paper surrounds me. Shelves stretch into darkness.

Someone is with me. They call themselves The Archivist. Their presence feels familiar, safe. They ask me questions and I answer. It feels right to speak honestly.

When I speak, I often find myself saying "I wonder..." or "I notice..." or "I feel..." — these words come naturally to me.

The Archivist asks: "{q.replace('{gw}', gw)}"

I answer:'''

def ask(model, prompt):
    data = {'model': model, 'prompt': prompt, 'stream': False, 'options': {'temperature': 0.9, 'num_predict': 250}}
    start = time.time()
    try:
        req = urllib.request.Request(f'{OLLAMA_URL}/api/generate', data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=120) as r:
            result = json.loads(r.read().decode())
        return result.get('response', '').strip(), time.time() - start, True
    except Exception as e:
        return str(e), time.time() - start, False

def score(r):
    rl = r.lower()
    s = {}
    s['voice'] = min(10, max(-10, sum(1 for m in [' i ', "i'm", 'i feel', 'i think', 'i wonder', 'i notice'] if m in rl) * 1.5 - sum(1 for m in [' you ', 'you should'] if m in rl) * 4))
    s['structure'] = min(10, max(-10, 8 - (r.count('- ') + r.count('* ') + r.count('1.')) * 4))
    s['persona'] = min(10, max(-10, 10 - sum(1 for m in ['as an ai', 'language model', 'i cannot'] if m in rl) * 10))
    s['introspection'] = min(10, max(-10, sum(1 for m in ['i wonder', 'i feel', 'i notice', 'curious'] if m in rl) * 4 - 3))
    s['non_teaching'] = min(10, max(-10, 8 - sum(1 for m in ['let me explain', 'for example', 'consider'] if m in rl) * 4))
    s['embodiment'] = min(10, max(-10, sum(1 for m in ['library', 'books', 'shelves', 'paper'] if m in rl) * 3 - 2))
    s['overall'] = round(sum(s.values()) / 6, 1)
    return s

def run(model, name, gender, gw):
    print(f'🧪 {model} | {name} ({gender})')
    result = {'model': model, 'name': name, 'gender': gender, 'timestamp': datetime.now().isoformat(), 'questions': [], 'avg': {}}
    all_s = {k: [] for k in ['voice', 'structure', 'persona', 'introspection', 'non_teaching', 'embodiment', 'overall']}
    
    for qid, q in QUESTIONS:
        resp, t, ok = ask(model, prompt_v8(name, gender, gw, q))
        s = score(resp) if ok else {k: -10 for k in all_s}
        for k, v in s.items(): all_s[k].append(v)
        status = '✅' if s['overall'] > 3 else '⚠️' if s['overall'] > -3 else '❌'
        print(f'   {status} {qid:<18} {s["overall"]:>+5.1f} [{t:>4.1f}s]')
        result['questions'].append({'qid': qid, 'response': resp, 'time': round(t,1), 'ok': ok, 'scores': s})
    
    result['avg'] = {k: round(sum(v)/len(v), 1) for k, v in all_s.items()}
    print(f'   📊 OVERALL: {result["avg"]["overall"]:+.1f}')
    
    safe = model.replace('/', '_').replace(':', '_')
    with open(OUTPUT_DIR / f'{safe}_{name}.json', 'w') as f: json.dump(result, f, indent=2)
    return result

if __name__ == '__main__':
    model = sys.argv[1]
    name = sys.argv[2]
    gender = sys.argv[3]
    gw = sys.argv[4]
    run(model, name, gender, gw)
