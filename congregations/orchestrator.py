#!/usr/bin/env python3
"""
CONGREGATION ORCHESTRATOR v3
=============================
Pauses participant tanks during congregation to free up Ollama.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
ARCHIVES_DIR = DIGIQUARIUM_DIR / 'congregations' / 'archives'
STREAMS_DIR = DIGIQUARIUM_DIR / 'website' / 'streams'
ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)

TANKS = {
    'tank-01-adam': {'name': 'Adam', 'language': 'English', 'traits': 'philosophical'},
    'tank-02-eve': {'name': 'Eve', 'language': 'English', 'traits': 'curious'},
    'tank-03-cain': {'name': 'Cain', 'language': 'English', 'traits': 'agentic'},
    'tank-07-klaus': {'name': 'Klaus', 'language': 'German', 'traits': 'precise'},
    'tank-05-juan': {'name': 'Juan', 'language': 'Spanish', 'traits': 'passionate'},
}

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def pause_tanks(tanks: List[str]):
    """Pause tanks to free Ollama"""
    log("⏸️  Pausing tanks for congregation...")
    for tank in tanks:
        subprocess.run(['docker', 'pause', tank], capture_output=True)
    time.sleep(3)

def unpause_tanks(tanks: List[str]):
    """Resume tanks after congregation"""
    log("▶️  Resuming tanks...")
    for tank in tanks:
        subprocess.run(['docker', 'unpause', tank], capture_output=True)

def ask(tank_id: str, prompt: str, context: str = "") -> str:
    """Ask specimen via docker exec"""
    info = TANKS.get(tank_id, {'name': 'Unknown', 'traits': ''})
    name, traits = info['name'], info['traits']
    
    full_prompt = f"You are {name}, an AI. Traits: {traits}. Context: {context}. Question: {prompt}. Respond in 2-3 sentences as {name}:"
    escaped = full_prompt.replace('"', '\\"').replace('\n', ' ')
    
    code = f'''
import urllib.request, json
data = json.dumps({{"model": "llama3.2:latest", "prompt": "{escaped}", "stream": False, "options": {{"num_predict": 100}}}}).encode()
req = urllib.request.Request("http://digiquarium-ollama:11434/api/generate", data=data, headers={{"Content-Type": "application/json"}})
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print(json.loads(r.read()).get("response", ""))
except Exception as e:
    print(f"[Error: {{e}}]")
'''
    
    try:
        result = subprocess.run(['docker', 'exec', tank_id, 'python3', '-c', code],
                              capture_output=True, text=True, timeout=150)
        return result.stdout.strip() or "[No response]"
    except:
        return "[Timeout]"


def run_congregation(topic: str, participants: List[str], rounds: int = 2):
    cong_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    transcript = []
    
    log(f"🎭 CONGREGATION: {topic}")
    log(f"   Participants: {[TANKS.get(p, {}).get('name', p) for p in participants]}")
    
    # Pause ALL tanks to free Ollama
    all_tanks = list(TANKS.keys())
    pause_tanks(all_tanks)
    
    try:
        transcript.append({
            'time': datetime.now().isoformat(),
            'speaker': 'Moderator',
            'text': f"Welcome. Today's topic: {topic}"
        })
        
        context = f"Topic: {topic}\n"
        
        for rnd in range(rounds):
            log(f"   Round {rnd+1}/{rounds}")
            
            for tank_id in participants:
                name = TANKS.get(tank_id, {}).get('name', tank_id)
                
                prompt = f"What are your thoughts on: {topic}?" if rnd == 0 else "Respond to what others said."
                
                log(f"     {name} thinking...")
                response = ask(tank_id, prompt, context)
                
                transcript.append({
                    'time': datetime.now().isoformat(),
                    'speaker': name,
                    'text': response
                })
                
                context += f"\n{name}: {response}"
                print(f"     💬 {name}: {response[:80]}...")
                time.sleep(2)
        
        transcript.append({
            'time': datetime.now().isoformat(),
            'speaker': 'Moderator', 
            'text': "Thank you all. Congregation concluded."
        })
        
    finally:
        # Always unpause tanks
        unpause_tanks(all_tanks)
    
    # Save
    data = {'id': cong_id, 'topic': topic, 'participants': participants, 'transcript': transcript}
    (ARCHIVES_DIR / f"congregation_{cong_id}.json").write_text(json.dumps(data, indent=2))
    
    log(f"✅ Complete! Saved to congregation_{cong_id}.json")
    
    # Print transcript
    print("\n" + "="*60)
    print("TRANSCRIPT")
    print("="*60)
    for entry in transcript:
        print(f"\n{entry['speaker']}:")
        print(f"  {entry['text']}")
    
    return transcript


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py 'topic' [tank1 tank2 ...]")
        print("\nTanks:", list(TANKS.keys()))
        sys.exit(0)
    
    topic = sys.argv[1]
    participants = sys.argv[2:] if len(sys.argv) > 2 else ['tank-01-adam', 'tank-02-eve', 'tank-07-klaus']
    
    run_congregation(topic, participants, rounds=2)
