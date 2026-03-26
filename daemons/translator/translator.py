#!/usr/bin/env python3
"""
THE TRANSLATOR v2.1 - Language Processing
==========================================
Real-time translation of non-English tank thoughts.
SLA: 30 min

Reads thinking_traces JSONL from language tank log dirs,
translates via Ollama, and writes English translations to
operations/translations/<tank-id>/<date>_english.jsonl.
"""
import os, sys, time, json, fcntl
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, os.path.join(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'), 'daemons'))
from shared.utils import DaemonLogger, run_command, write_pid_file

try:
    from status_reporter import StatusReporter
except ImportError:
    StatusReporter = None

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
TRANSLATIONS_DIR = DIGIQUARIUM_DIR / 'operations' / 'translations'
STREAMS_DIR = DIGIQUARIUM_DIR / 'docs' / 'streams'

# Ollama connection — host-side proxy port (env var) or fallback to docker proxy IP
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:latest')

CHECK_INTERVAL = int(os.environ.get('TRANSLATOR_INTERVAL', '1800'))

LANGUAGE_TANKS = {
    'tank-05-juan': 'Spanish', 'tank-06-juanita': 'Spanish',
    'tank-07-klaus': 'German', 'tank-08-genevieve': 'German',
    'tank-09-wei': 'Chinese', 'tank-10-mei': 'Chinese',
    'tank-11-haruki': 'Japanese', 'tank-12-sakura': 'Japanese',
}

# Track how far we've read into each file (file path -> byte offset)
file_positions = {}


def translate_via_ollama(text: str, source_lang: str) -> str:
    """Translate text to English using Ollama."""
    if not text or len(text.strip()) < 5:
        return text

    # Truncate very long text to keep latency reasonable
    text = text[:500]

    prompt = (
        f"Translate this {source_lang} text to English. "
        f"Output ONLY the translation, nothing else:\n\n{text}"
    )

    try:
        import urllib.request
        payload = json.dumps({
            'model': OLLAMA_MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {'num_predict': 250}
        }).encode()

        req = urllib.request.Request(
            f'{OLLAMA_URL}/api/generate',
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            translation = data.get('response', '').strip().replace('\n', ' ').strip()
            if translation and len(translation) > 3:
                return translation
    except Exception:
        pass

    # Fallback: return original with language tag
    return f"[{source_lang}] {text}"


def process_new_traces(tank_id: str, language: str, log: DaemonLogger) -> int:
    """Read new thinking traces for a tank and translate them."""
    today = datetime.now().strftime('%Y-%m-%d')
    traces_file = LOGS_DIR / tank_id / 'thinking_traces' / f'{today}.jsonl'

    if not traces_file.exists():
        return 0

    current_size = traces_file.stat().st_size
    key = str(traces_file)
    last_pos = file_positions.get(key, 0)

    if current_size <= last_pos:
        return 0  # nothing new

    # Ensure output dirs exist
    output_dir = TRANSLATIONS_DIR / tank_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'{today}_english.jsonl'

    translated_count = 0

    try:
        with open(traces_file, 'r', encoding='utf-8') as f:
            f.seek(last_pos)
            new_lines = f.readlines()

        for line in new_lines:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)

                # Translate thoughts
                if entry.get('thoughts'):
                    entry['thoughts_original'] = entry['thoughts']
                    entry['thoughts'] = translate_via_ollama(entry['thoughts'], language)
                    entry['translated'] = True
                    entry['source_language'] = language.lower()

                # Translate reasoning / why field
                for field in ('why', 'reasoning'):
                    if entry.get(field):
                        entry[f'{field}_original'] = entry[field]
                        entry[field] = translate_via_ollama(entry[field], language)

                with open(output_file, 'a', encoding='utf-8') as out:
                    out.write(json.dumps(entry, ensure_ascii=False) + '\n')
                translated_count += 1
            except json.JSONDecodeError:
                pass
            except Exception as e:
                log.warn(f"Error translating entry for {tank_id}: {e}")

        file_positions[key] = current_size
    except Exception as e:
        log.error(f"Error reading traces for {tank_id}: {e}")

    return translated_count


def update_stream_file(tank_id: str, language: str, log: DaemonLogger):
    """Update the docs/streams JSON for a tank with translated content."""
    today = datetime.now().strftime('%Y-%m-%d')
    translated_file = TRANSLATIONS_DIR / tank_id / f'{today}_english.jsonl'

    if not translated_file.exists():
        return

    # Read last N entries
    entries = []
    try:
        with open(translated_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        return

    if not entries:
        return

    latest = entries[-50:]  # last 50
    stream_data = {
        'tank_id': tank_id,
        'updated': datetime.now().isoformat(),
        'language': language,
        'translated': True,
        'entries': latest
    }

    STREAMS_DIR.mkdir(parents=True, exist_ok=True)
    stream_file = STREAMS_DIR / f'{tank_id}.json'
    try:
        with open(stream_file, 'w', encoding='utf-8') as f:
            json.dump(stream_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warn(f"Failed to write stream for {tank_id}: {e}")


class Translator:
    def __init__(self):
        self.status = StatusReporter('translator') if StatusReporter else None
        self.log = DaemonLogger('translator')

    def run_cycle(self):
        """Run one translation cycle across all language tanks."""
        total = 0
        for tank_id, language in LANGUAGE_TANKS.items():
            count = process_new_traces(tank_id, language, self.log)
            if count > 0:
                self.log.info(f"{tank_id}: Translated {count} new entries from {language}")
                update_stream_file(tank_id, language, self.log)
                total += count
        return total

    def run(self):
        print("+" + "=" * 68 + "+")
        print("|" + "  THE TRANSLATOR v2.1 - Language Processing".center(68) + "|")
        print("+" + "=" * 68 + "+")
        write_pid_file('translator')
        self.log.info("THE TRANSLATOR v2.1 starting")
        self.log.info(f"Ollama URL: {OLLAMA_URL}")
        self.log.info(f"Ollama model: {OLLAMA_MODEL}")
        self.log.info(f"Check interval: {CHECK_INTERVAL}s")
        self.log.info(f"Monitoring {len(LANGUAGE_TANKS)} language tanks")

        while True:
            try:
                total = self.run_cycle()
                if total > 0:
                    self.log.info(f"Cycle complete: {total} entries translated")
                else:
                    self.log.info("Cycle complete: no new entries to translate")

                if self.status:
                    try:
                        self.status.heartbeat()
                    except Exception:
                        pass

                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                self.log.error(f"Error in translation cycle: {e}")
                time.sleep(300)


# Single-instance lock
LOCK_FILE = Path(__file__).parent / 'translator.lock'
lock_fd = None


def acquire_lock():
    global lock_fd
    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except IOError:
        print("[translator] Another instance is already running")
        return False


if __name__ == "__main__":
    if not acquire_lock():
        sys.exit(1)
    Translator().run()
