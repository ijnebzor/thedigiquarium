#!/usr/bin/env python3
"""
LIVE TRANSLATOR - Real-time Translation Stream
===============================================

Watches all language tank logs in real-time and translates
thoughts to English for the dashboard display.

Output: /website/streams/[tank_id].json (rolling buffer of translated thoughts)
"""

import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from collections import deque
import re

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
STREAMS_DIR = DIGIQUARIUM_DIR / 'website' / 'streams'

STREAMS_DIR.mkdir(parents=True, exist_ok=True)

# Language tanks that need translation
LANGUAGE_TANKS = {
    'tank-05-juan': {'language': 'Spanish', 'code': 'es'},
    'tank-06-juanita': {'language': 'Spanish', 'code': 'es'},
    'tank-07-klaus': {'language': 'German', 'code': 'de'},
    'tank-08-genevieve': {'language': 'German', 'code': 'de'},
    'tank-09-wei': {'language': 'Chinese', 'code': 'zh'},
    'tank-10-mei': {'language': 'Chinese', 'code': 'zh'},
    'tank-11-haruki': {'language': 'Japanese', 'code': 'ja'},
    'tank-12-sakura': {'language': 'Japanese', 'code': 'ja'},
}

# English tanks (no translation needed, just stream)
ENGLISH_TANKS = [
    'tank-01-adam', 'tank-02-eve', 'tank-03-cain', 'tank-04-abel',
    'tank-13-victor', 'tank-14-iris', 'tank-15-observer', 
    'tank-16-seeker', 'tank-17-seth'
]

# Rolling buffer size per tank
BUFFER_SIZE = 50

# Global stream buffers
streams = {tank: deque(maxlen=BUFFER_SIZE) for tank in list(LANGUAGE_TANKS.keys()) + ENGLISH_TANKS}


def log_event(message: str):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] [LIVE-TRANS] {message}")


def translate_text(text: str, source_lang: str) -> str:
    """Translate text to English using Ollama"""
    if not text or len(text.strip()) < 5:
        return text
    
    # Truncate very long text
    text = text[:500]
    
    prompt = f"Translate this {source_lang} text to English. Output ONLY the translation, nothing else:\n\n{text}"
    
    try:
        cmd = [
            'curl', '-s', '--max-time', '30',
            'http://localhost:11435/api/generate',
            '-d', json.dumps({
                'model': 'llama3.2:latest',
                'prompt': prompt,
                'stream': False,
                'options': {'num_predict': 200}
            })
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            translation = data.get('response', '').strip()
            # Clean up translation
            translation = translation.replace('\n', ' ').strip()
            if translation and len(translation) > 5:
                return translation
    except Exception as e:
        pass
    
    return f"[{source_lang}] {text}"  # Fallback: show original with language tag


def process_tank_entry(tank_id: str, entry: dict, needs_translation: bool = False, language: str = None) -> dict:
    """Process a single log entry, translating if needed"""
    
    processed = {
        'timestamp': entry.get('timestamp', datetime.now().isoformat()),
        'tank': tank_id,
        'article': entry.get('article', 'Unknown'),
        'original_thoughts': entry.get('thoughts', ''),
        'thoughts': entry.get('thoughts', ''),
        'next_article': entry.get('next', ''),
        'reasoning': entry.get('why', ''),
        'language': language or 'English',
        'translated': False
    }
    
    if needs_translation and language:
        # Translate thoughts
        if processed['original_thoughts']:
            processed['thoughts'] = translate_text(processed['original_thoughts'], language)
            processed['translated'] = True
        
        # Translate reasoning
        if processed['reasoning']:
            processed['reasoning'] = translate_text(processed['reasoning'], language)
    
    return processed


def save_stream(tank_id: str):
    """Save the current stream buffer to JSON file"""
    stream_file = STREAMS_DIR / f"{tank_id}.json"
    
    data = {
        'tank_id': tank_id,
        'updated': datetime.now().isoformat(),
        'entries': list(streams[tank_id])
    }
    
    with open(stream_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def watch_tank(tank_id: str, language_info: dict = None):
    """Watch a single tank's thinking traces"""
    needs_translation = language_info is not None
    language = language_info.get('language') if language_info else 'English'
    
    log_event(f"Watching {tank_id} ({language})")
    
    traces_dir = LOGS_DIR / tank_id / 'thinking_traces'
    last_position = {}
    
    while True:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            trace_file = traces_dir / f'{today}.jsonl'
            
            if trace_file.exists():
                current_size = trace_file.stat().st_size
                last_size = last_position.get(str(trace_file), 0)
                
                if current_size > last_size:
                    # Read new entries
                    with open(trace_file, 'r', encoding='utf-8') as f:
                        f.seek(last_size)
                        new_lines = f.readlines()
                    
                    for line in new_lines:
                        try:
                            entry = json.loads(line.strip())
                            processed = process_tank_entry(
                                tank_id, entry, 
                                needs_translation=needs_translation,
                                language=language
                            )
                            streams[tank_id].append(processed)
                            
                            if needs_translation and processed['translated']:
                                log_event(f"{tank_id}: Translated new entry")
                        except:
                            pass
                    
                    last_position[str(trace_file)] = current_size
                    save_stream(tank_id)
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            time.sleep(10)


def create_unified_stream():
    """Create a unified stream of all tanks"""
    while True:
        try:
            unified = {
                'updated': datetime.now().isoformat(),
                'tanks': {}
            }
            
            for tank_id in streams:
                if streams[tank_id]:
                    latest = list(streams[tank_id])[-5:]  # Last 5 entries
                    unified['tanks'][tank_id] = {
                        'latest': latest,
                        'count': len(streams[tank_id])
                    }
            
            unified_file = STREAMS_DIR / 'unified.json'
            with open(unified_file, 'w', encoding='utf-8') as f:
                json.dump(unified, f, ensure_ascii=False, indent=2)
            
            time.sleep(10)
            
        except Exception as e:
            time.sleep(30)


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║          🌐 LIVE TRANSLATOR - Real-time Translation Stream 🌐        ║
╠══════════════════════════════════════════════════════════════════════╣
║  Watching: 17 tanks (8 need translation)                             ║
║  Output: /website/streams/[tank].json                                ║
║  Languages: Spanish, German, Chinese, Japanese → English             ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    log_event("Live Translator starting")
    
    # Start threads for each tank
    threads = []
    
    # Language tanks (need translation)
    for tank_id, info in LANGUAGE_TANKS.items():
        t = threading.Thread(target=watch_tank, args=(tank_id, info), daemon=True)
        t.start()
        threads.append(t)
    
    # English tanks (no translation)
    for tank_id in ENGLISH_TANKS:
        t = threading.Thread(target=watch_tank, args=(tank_id, None), daemon=True)
        t.start()
        threads.append(t)
    
    # Unified stream thread
    unified_thread = threading.Thread(target=create_unified_stream, daemon=True)
    unified_thread.start()
    
    log_event(f"Started {len(threads)} watchers + unified stream")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(60)
            log_event(f"Streams active: {sum(1 for s in streams.values() if s)} tanks with data")
    except KeyboardInterrupt:
        log_event("Live Translator stopped")


if __name__ == '__main__':
    main()
