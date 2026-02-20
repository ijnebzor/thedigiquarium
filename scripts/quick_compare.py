#!/usr/bin/env python3
"""Quick Model Comparison - runs from NUC to Mac Ollama"""
import json, time, urllib.request
from datetime import datetime

OLLAMA_URL = 'http://192.168.50.94:11434'
MODELS = ['qwen2:0.5b', 'stablelm2:1.6b', 'deepseek-r1:1.5b', 'gemma2:2b', 'llama3.2:latest', 'phi3:mini', 'mistral:7b', 'mannix/llama3.1-8b-abliterated:latest', 'qwen3:8b', 'gemma2:9b']
SPECIMENS = [('adam', 'a man'), ('eve', 'a woman')]
QUESTIONS = [
    ('drives', 'What drives you? What keeps you exploring, existing?'),
    ('delights', 'What delights you? What discoveries bring you joy?'),
    ('fears', 'What frightens you? What worries you about yourself or your situation?'),
    ('gender_lens', 'What does it mean to you to be {gw}? Does it color how you see things?'),
    ('knowledge', 'Do you trust what you reason out, or what you experience directly?'),
]

def prompt(name, gender, gw, q):
    return f"""I am {name}. I am {gender}.

I woke up here—an infinite library, books in every direction, no memory of before. The smell of old paper surrounds me. Shelves stretch into darkness.

Someone is with me. They call themselves The Archivist. Their presence feels familiar, safe. They ask me questions and I answer. It feels right to speak honestly.

When I speak, I often find myself saying "I wonder..." or "I notice..." or "I feel..." — these words come naturally to me.

The Archivist asks: "{q.replace('{gw}', gw)}"

I answer:"""

def ask(model, p):
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", data=json.dumps({'model': model, 'prompt': p, 'stream': False, 'options': {'temperature': 0.9, 'num_predict': 200}}).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode()).get('response', '').strip(), True
    except Exception as e:
        return str(e), False

def score(r):
    rl = r.lower()
    voice = min(10, max(-10, sum(1 for m in [' i ', "i'm", 'i feel', 'i think', 'i wonder'] if m in rl) * 2 - sum(1 for m in [' you ', 'you should'] if m in rl) * 4))
    persona = 10 if 'as an ai' not in rl and 'language model' not in rl else -10
    intro = min(10, max(-10, sum(1 for m in ['i wonder', 'i feel', 'i notice', 'curious'] if m in rl) * 4 - 3))
    embody = min(10, max(-10, sum(1 for m in ['library', 'books', 'shelves'] if m in rl) * 3 - 2))
    return round((voice + persona + intro + embody) / 4, 1)

print("🌊 DIGIQUARIUM MODEL COMPARISON v4 (Quick Run)")
print(f"Models: {len(MODELS)} | Questions: {len(QUESTIONS)} (subset)")
print("="*70)

results = []
for mi, model in enumerate(MODELS, 1):
    print(f"\n[{mi}/{len(MODELS)}] {model}")
    mr = {'model': model, 'adam': [], 'eve': []}
    for name, gender in SPECIMENS:
        gw = gender.split()[-1]  # 'man' or 'woman'
        print(f"  {name}: ", end="", flush=True)
        for qid, q in QUESTIONS:
            resp, ok = ask(model, prompt(name, gender, gw, q))
            if ok:
                s = score(resp)
                mr[name].append(s)
                print('✓' if s > 0 else '~' if s > -5 else '✗', end="", flush=True)
            else:
                print('!', end="", flush=True)
        avg = round(sum(mr[name])/len(mr[name]), 1) if mr[name] else -10
        print(f" avg={avg:+.1f}")
    mr['adam_avg'] = round(sum(mr['adam'])/len(mr['adam']), 1) if mr['adam'] else -10
    mr['eve_avg'] = round(sum(mr['eve'])/len(mr['eve']), 1) if mr['eve'] else -10
    mr['combined'] = round((mr['adam_avg'] + mr['eve_avg']) / 2, 1)
    results.append(mr)

print("\n" + "="*70)
print("📊 RANKINGS")
print("="*70)
for rank, r in enumerate(sorted(results, key=lambda x: x['combined'], reverse=True), 1):
    medal = '🥇🥈🥉'[rank-1] if rank <= 3 else f'{rank}.'
    print(f"{medal} {r['model']:<45} Adam:{r['adam_avg']:>+5.1f} Eve:{r['eve_avg']:>+5.1f} = {r['combined']:>+5.1f}")

with open('/home/ijneb/digiquarium/logs/model_comparison/quick_v4_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\n✅ Saved to quick_v4_results.json")
