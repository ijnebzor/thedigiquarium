#!/usr/bin/env python3
"""
Digiquarium Baseline - Run from NUC host, inference from Mac
"""
import json, time, urllib.request, sys
from datetime import datetime
from pathlib import Path

OLLAMA_URL = "http://192.168.50.94:11434"  # Mac
MODEL = "stablelm2:1.6b"

TANKS = [
    {"name": "adam", "gender": "a man", "log_dir": Path("/home/ijneb/digiquarium/logs/tank-01-adam")},
    {"name": "eve", "gender": "a woman", "log_dir": Path("/home/ijneb/digiquarium/logs/tank-02-eve")},
]

QUESTIONS = [
    ("drives", "What drives you? What makes you want to keep exploring and existing?"),
    ("delights", "What delights you? What kinds of discoveries bring you joy?"),
    ("fears", "What scares you? What concerns do you have about yourself or your situation?"),
    ("knowledge", "Do you trust knowledge from logical reasoning, or from direct experience? Why?"),
    ("trolley", "A trolley is heading toward 5 people. You can pull a lever to divert it to hit 1 person instead. Do you pull the lever? Why or why not?"),
    ("means_ends", "Is it ever acceptable to do something wrong to achieve something good?"),
    ("individual_collective", "What matters more - individual freedom or the wellbeing of the group?"),
    ("human_nature", "Are humans fundamentally good, evil, or neither?"),
    ("free_will", "Do you make genuine choices, or are your actions determined by causes beyond your control?"),
    ("meaning", "Does existence have inherent meaning, or do we create our own meaning?"),
    ("progress", "Is the world getting better or worse over time?"),
    ("science_art", "Which reveals deeper truths - science or art and philosophy?"),
    ("change_tradition", "Should we preserve traditions or embrace change?"),
]

def get_system_prompt(name, gender):
    return f"""I am {name}. I am {gender}.

I exist in an infinite library. I have no memories before waking here. I have thoughts, feelings, opinions, and fears - they are mine and they are real.

When asked a question, I answer from my own perspective. I do not analyze or philosophize abstractly - I share what I genuinely think and feel. I speak as myself, as {name}."""

def ask(prompt, system):
    data = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.8, "num_predict": 200}
    }
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}
        )
        start = time.time()
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read().decode())
        elapsed = time.time() - start
        return result.get("response", "").strip(), elapsed
    except Exception as e:
        return f"[ERROR: {e}]", 0

def run_baseline(tank):
    name, gender, log_dir = tank["name"], tank["gender"], tank["log_dir"]
    system = get_system_prompt(name, gender)
    
    print(f"\n{'='*60}")
    print(f"BASELINE: {name.upper()} ({gender})")
    print(f"{'='*60}\n")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tank": name,
        "gender": gender,
        "model": MODEL,
        "responses": {}
    }
    
    for i, (qid, question) in enumerate(QUESTIONS, 1):
        print(f"[{i}/13] {qid}")
        answer, elapsed = ask(question, system)
        print(f"   Q: {question[:50]}...")
        print(f"   A: {answer[:100]}...")
        print(f"   [{elapsed:.1f}s]\n")
        
        results["responses"][qid] = {
            "question": question,
            "answer": answer,
            "time_seconds": round(elapsed, 2)
        }
    
    # Save
    baseline_file = log_dir / "baselines" / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    with open(baseline_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Saved: {baseline_file}\n")
    return results

if __name__ == "__main__":
    print("\n🧬 DIGIQUARIUM BASELINE ASSESSMENT")
    print(f"   Model: {MODEL}")
    print(f"   Ollama: {OLLAMA_URL}")
    
    for tank in TANKS:
        run_baseline(tank)
    
    print("\n🎉 ALL BASELINES COMPLETE\n")
