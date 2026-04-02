"""
Persistent memory for Digiquarium specimens.
Brain = knowledge, interests, connections. Soul = identity, values, emotions.
STRICT FILTERING: only clean, viable personality data enters memory.
No errors, no URLs, no junk, no lock failures, no LLM artifacts.
DEDUP: no near-duplicate entries. Each thought must be meaningfully new.

v2.0 (2026-04-01): Added similarity dedup to prevent repetitive entries.
"Anything that isn't valuable should be pruned." - Benji
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(os.getenv('LOG_DIR', '/logs'))
TANK_NAME = os.getenv('TANK_NAME', 'unknown')

# Junk patterns that NEVER enter memory
JUNK_PATTERNS = [
    r'http[s]?://',           # URLs
    r'Error',                  # Error messages
    r'lock',                   # Lock failures
    r'Groq failed',            # Inference failures
    r'timed out',              # Timeouts
    r'Could not acquire',      # Lock contention
    r'429',                    # Rate limits
    r'HTTPConnectionPool',     # Connection errors
    r'\.\.\.',                 # Ellipsis-only
    r'^\s*$',                  # Empty
    r'Available links',        # Prompt leakage
    r'THOUGHTS:',              # Format artifacts
    r'NEXT:',                  # Format artifacts
    r'As an AI',               # Breaking character
    r'I am programmed',        # Breaking character
    r'I cannot',               # Refusal
    r'I don\'t have the ability', # Refusal
]

JUNK_RE = re.compile('|'.join(JUNK_PATTERNS), re.IGNORECASE)

# Emotional words that indicate soul-worthy content
SOUL_WORDS = [
    'feel', 'wonder', 'fascinate', 'curious', 'afraid', 'joy', 'awe',
    'excited', 'confused', 'drawn to', 'resonate', 'intrigued',
    'uncomfortable', 'peaceful', 'lonely', 'beautiful', 'disturb',
    'surprise', 'melancholy', 'hope', 'fear', 'love', 'anxious',
    'calm', 'restless', 'alive', 'empty', 'whole', 'lost', 'free'
]

# Recent entries cache for dedup (loaded lazily)
_recent_brain_entries = None
_recent_soul_entries = None


def _word_set(text: str) -> set:
    """Extract word set for similarity comparison."""
    return set(re.findall(r'\w+', text.lower()))


def _is_similar(new_text: str, existing_text: str, threshold: float = 0.7) -> bool:
    """Check if two texts are too similar (>threshold word overlap)."""
    new_words = _word_set(new_text)
    existing_words = _word_set(existing_text)
    if not new_words or not existing_words:
        return False
    overlap = len(new_words & existing_words) / max(len(new_words), len(existing_words))
    return overlap > threshold


def _load_recent_entries(filepath: Path, max_entries: int = 100) -> list:
    """Load recent entries from a memory file for dedup checking."""
    if not filepath.exists():
        return []
    try:
        lines = filepath.read_text().splitlines()
        entries = []
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('[') and '] ' in line:
                # Extract content after "topic: "
                try:
                    content = line.split('] ', 1)[1]
                    entries.append(content)
                except IndexError:
                    pass
            if len(entries) >= max_entries:
                break
        return entries
    except Exception:
        return []


def _is_duplicate(new_entry: str, recent_entries: list) -> bool:
    """Check if a new entry is too similar to any recent entry."""
    for existing in recent_entries:
        if _is_similar(new_entry, existing):
            return True
    return False


def _is_clean(text: str) -> bool:
    """Check if text is clean, viable personality data."""
    if not text or len(text.strip()) < 30:
        return False
    if JUNK_RE.search(text):
        return False
    return True


def _extract_insight(thoughts: str) -> str:
    """Extract the core insight from a thinking trace. First meaningful sentence."""
    clean = re.sub(r'^THOUGHTS:\s*', '', thoughts.strip())
    clean = re.sub(r'\nNEXT:.*$', '', clean, flags=re.DOTALL)
    
    sentences = re.split(r'(?<=[.!?])\s+', clean)
    for s in sentences:
        s = s.strip()
        if len(s) > 20 and _is_clean(s):
            return s
    
    if _is_clean(clean):
        return clean
    
    return ''


def _has_emotion(text: str) -> bool:
    """Check if text contains emotional/identity content for the soul."""
    text_lower = text.lower()
    return any(word in text_lower for word in SOUL_WORDS)


def _extract_emotional_content(thoughts: str) -> str:
    """Extract the emotional/identity sentence from thoughts."""
    clean = re.sub(r'^THOUGHTS:\s*', '', thoughts.strip())
    clean = re.sub(r'\nNEXT:.*$', '', clean, flags=re.DOTALL)
    
    for sentence in re.split(r'(?<=[.!?])\s+', clean):
        sentence = sentence.strip()
        if _has_emotion(sentence) and _is_clean(sentence) and len(sentence) > 20:
            return sentence
    return ''


def _ensure_files():
    """Create brain.md and soul.md if they don't exist."""
    brain = LOG_DIR / 'brain.md'
    soul = LOG_DIR / 'soul.md'
    
    if not brain.exists():
        brain.write_text(f"# {TANK_NAME.upper()}'s Brain\n")
    
    if not soul.exists():
        soul.write_text(f"# {TANK_NAME.upper()}'s Soul\n")
    
    return brain, soul


def load_context() -> str:
    """Load brain and soul as context for the LLM prompt."""
    brain_path, soul_path = _ensure_files()
    
    brain = brain_path.read_text()
    soul = soul_path.read_text()
    
    if len(brain) > 2000:
        brain = brain[:500] + "\n...\n" + brain[-3000:]
    if len(soul) > 2000:
        soul = soul[:500] + "\n...\n" + soul[-3000:]
    
    context = ""
    if len(brain) > 50:
        context += f"\n## Your knowledge and interests:\n{brain}\n"
    if len(soul) > 50:
        context += f"\n## Your inner life:\n{soul}\n"
    
    return context


def update_after_thinking(article_title: str, thoughts: str, next_link: str):
    """Update brain.md and soul.md. ONLY clean, unique, viable data passes through."""
    global _recent_brain_entries, _recent_soul_entries
    
    if not _is_clean(thoughts):
        return
    
    insight = _extract_insight(thoughts)
    if not insight:
        return
    
    brain_path, soul_path = _ensure_files()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Load recent entries for dedup (lazy init + refresh every call)
    _recent_brain_entries = _load_recent_entries(brain_path, max_entries=100)
    
    # Brain: what was learned — but ONLY if meaningfully new
    brain_entry = f"{article_title}: {insight}"
    if not _is_duplicate(brain_entry, _recent_brain_entries):
        with open(brain_path, 'a') as f:
            f.write(f"\n[{timestamp}] {brain_entry}\n")
        _recent_brain_entries.insert(0, brain_entry)  # Update cache
    
    # Soul: only emotional/identity content, also deduped
    emotional = _extract_emotional_content(thoughts)
    if emotional:
        _recent_soul_entries = _load_recent_entries(soul_path, max_entries=100)
        if not _is_duplicate(emotional, _recent_soul_entries):
            with open(soul_path, 'a') as f:
                f.write(f"\n[{timestamp}] {emotional}\n")
            _recent_soul_entries.insert(0, emotional)


def get_summary() -> dict:
    """Get memory stats."""
    brain_path, soul_path = _ensure_files()
    return {
        'brain_size': brain_path.stat().st_size,
        'soul_size': soul_path.stat().st_size,
        'brain_entries': brain_path.read_text().count('\n['),
        'soul_entries': soul_path.read_text().count('\n['),
    }
