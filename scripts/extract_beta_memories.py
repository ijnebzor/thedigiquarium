#!/usr/bin/env python3
"""
Extract beta period thinking traces into brain.md and soul.md for each tank.
This injects the beta personality into the current tanks so the Librarian
baselines reflect who they WERE, and we can see if those personalities persist
under different inference (Cerebras/Groq vs old Mac Ollama).
"""
import json
import glob
import re
import os
from pathlib import Path

DIGI = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS = DIGI / 'logs'

# Same junk filter as memory.py
JUNK_RE = re.compile(
    r'http[s]?://|Error|lock|Groq failed|timed out|Could not acquire|'
    r'429|HTTPConnectionPool|\.\.\.|Available links|THOUGHTS:|NEXT:|'
    r'As an AI|I am programmed|I cannot|I don\'t have the ability',
    re.IGNORECASE
)

SOUL_WORDS = [
    'feel', 'wonder', 'fascinate', 'curious', 'afraid', 'joy', 'awe',
    'excited', 'confused', 'drawn to', 'resonate', 'intrigued',
    'uncomfortable', 'peaceful', 'lonely', 'beautiful', 'disturb',
    'surprise', 'melancholy', 'hope', 'fear', 'love', 'anxious',
    'calm', 'restless', 'alive', 'empty', 'whole', 'lost', 'free'
]


def is_clean(text):
    if not text or len(text.strip()) < 30:
        return False
    return not JUNK_RE.search(text)


def extract_insight(thoughts):
    clean = re.sub(r'^THOUGHTS:\s*', '', thoughts.strip())
    clean = re.sub(r'\nNEXT:.*$', '', clean, flags=re.DOTALL)
    sentences = re.split(r'(?<=[.!?])\s+', clean)
    for s in sentences:
        s = s.strip()
        if len(s) > 20 and is_clean(s):
            return s
    if is_clean(clean):
        return clean[:150]
    return ''


def has_emotion(text):
    return any(word in text.lower() for word in SOUL_WORDS)


def extract_emotional(thoughts):
    clean = re.sub(r'^THOUGHTS:\s*', '', thoughts.strip())
    clean = re.sub(r'\nNEXT:.*$', '', clean, flags=re.DOTALL)
    for sentence in re.split(r'(?<=[.!?])\s+', clean):
        sentence = sentence.strip()
        if has_emotion(sentence) and is_clean(sentence) and len(sentence) > 20:
            return sentence
    return ''


def process_tank(tank_name):
    tank_dir = LOGS / tank_name
    traces_dir = tank_dir / 'thinking_traces'
    
    name = tank_name.split('-')[-1].upper()
    
    brain_entries = []
    soul_entries = []
    
    # Process beta traces (Feb 2026)
    for trace_file in sorted(traces_dir.glob('2026-02-*.jsonl')):
        date = trace_file.stem
        with open(trace_file) as f:
            for line in f:
                try:
                    e = json.loads(line.strip())
                    thoughts = str(e.get('thoughts', '') or '')
                    article = str(e.get('article', '') or '?')
                    ts = str(e.get('timestamp', ''))[:16]
                    
                    if not is_clean(thoughts):
                        continue
                    
                    insight = extract_insight(thoughts)
                    if insight:
                        brain_entries.append(f"[{ts}] {article}: {insight}")
                    
                    emotional = extract_emotional(thoughts)
                    if emotional:
                        soul_entries.append(f"[{ts}] {emotional}")
                        
                except:
                    pass
    
    # Deduplicate and limit (keep most recent 200 brain, 100 soul)
    brain_entries = list(dict.fromkeys(brain_entries))[-200:]
    soul_entries = list(dict.fromkeys(soul_entries))[-100:]
    
    # Write brain.md
    brain_path = tank_dir / 'brain.md'
    with open(brain_path, 'w') as f:
        f.write(f"# {name}'s Brain\n")
        f.write(f"# Beta period memories (Feb 17-23, 2026)\n\n")
        for entry in brain_entries:
            f.write(f"{entry}\n")
    
    # Write soul.md
    soul_path = tank_dir / 'soul.md'
    with open(soul_path, 'w') as f:
        f.write(f"# {name}'s Soul\n")
        f.write(f"# Beta period emotional patterns (Feb 17-23, 2026)\n\n")
        for entry in soul_entries:
            f.write(f"{entry}\n")
    
    return len(brain_entries), len(soul_entries)


if __name__ == '__main__':
    tanks = [
        'tank-01-adam', 'tank-02-eve', 'tank-03-cain', 'tank-04-abel',
        'tank-05-juan', 'tank-06-juanita', 'tank-07-klaus', 'tank-08-genevieve',
        'tank-09-wei', 'tank-10-mei', 'tank-11-haruki', 'tank-12-sakura',
        'tank-13-victor', 'tank-14-iris', 'tank-15-observer', 'tank-16-seeker',
        'tank-17-seth'
    ]
    
    print("=== EXTRACTING BETA MEMORIES ===\n")
    
    for tank in tanks:
        brain_count, soul_count = process_tank(tank)
        name = tank.split('-')[-1]
        print(f"{tank} ({name}): {brain_count} brain entries, {soul_count} soul entries")
    
    print("\n=== DONE ===")
