#!/usr/bin/env python3
"""
THE TRANSLATOR - Language Content Processing Agent
===================================================

Responsibilities:
- Convert non-English thinking traces to readable English
- Maintain bilingual archives
- Support baseline comparison across languages
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
TRANSLATIONS_DIR = DIGIQUARIUM_DIR / 'operations' / 'translations'

TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)

LANGUAGE_TANKS = {
    'tank-05-juan': 'spanish',
    'tank-06-juanita': 'spanish',
    'tank-07-klaus': 'german',
    'tank-08-genevieve': 'german',
    'tank-09-wei': 'chinese',
    'tank-10-mei': 'chinese',
    'tank-11-haruki': 'japanese',
    'tank-12-sakura': 'japanese',
}

def log_event(message: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [TRANSLATOR] {message}")

def translate_via_ollama(text: str, source_lang: str) -> str:
    """Translate text to English using Ollama"""
    prompt = f"Translate this {source_lang} text to English. Only output the translation, nothing else:\n\n{text}"
    
    cmd = f'''curl -s http://localhost:11435/api/generate -d '{{"model": "llama3.2:latest", "prompt": "{prompt.replace('"', '\\"').replace("'", "")}", "stream": false}}' '''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('response', text)
    except:
        pass
    return text

def process_tank_traces(tank_id: str, language: str, date: str = None):
    """Process thinking traces for a tank"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    traces_file = LOGS_DIR / tank_id / 'thinking_traces' / f'{date}.jsonl'
    if not traces_file.exists():
        return 0
    
    output_dir = TRANSLATIONS_DIR / tank_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'{date}_english.jsonl'
    
    translated_count = 0
    
    with open(traces_file) as f:
        for line in f:
            try:
                entry = json.loads(line)
                # Translate thoughts
                if entry.get('thoughts'):
                    entry['thoughts_original'] = entry['thoughts']
                    entry['thoughts'] = translate_via_ollama(entry['thoughts'], language)
                    entry['translated'] = True
                    entry['source_language'] = language
                
                with open(output_file, 'a') as out:
                    out.write(json.dumps(entry, ensure_ascii=False) + '\n')
                translated_count += 1
            except:
                pass
    
    return translated_count

def run_translation_cycle():
    """Run translation for all language tanks"""
    log_event("Starting translation cycle")
    today = datetime.now().strftime('%Y-%m-%d')
    
    for tank_id, language in LANGUAGE_TANKS.items():
        count = process_tank_traces(tank_id, language, today)
        if count > 0:
            log_event(f"{tank_id}: Translated {count} entries from {language}")
    
    log_event("Translation cycle complete")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        run_translation_cycle()
    else:
        while True:
            run_translation_cycle()
            time.sleep(3600)  # Run hourly
