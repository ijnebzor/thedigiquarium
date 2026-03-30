"""
Persistent memory for Digiquarium specimens.
Brain = knowledge, interests, connections. Soul = identity, values, emotions.
STRICT FILTERING: only clean, viable personality data enters memory.
No errors, no URLs, no junk, no lock failures, no LLM artifacts.
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


def _is_clean(text: str) -> bool:
    """Check if text is clean, viable personality data."""
    if not text or len(text.strip()) < 30:
        return False
    if JUNK_RE.search(text):
        return False
    return True


def _extract_insight(thoughts: str) -> str:
    """Extract the core insight from a thinking trace. First meaningful sentence."""
    # Remove any THOUGHTS:/NEXT: artifacts
    clean = re.sub(r'^THOUGHTS:\s*', '', thoughts.strip())
    clean = re.sub(r'\nNEXT:.*$', '', clean, flags=re.DOTALL)
    
    # Get first sentence
    sentences = re.split(r'(?<=[.!?])\s+', clean)
    for s in sentences:
        s = s.strip()
        if len(s) > 20 and _is_clean(s):
            return s
    
    # If no clean sentence, take first 150 chars if the whole thing is clean
    if _is_clean(clean):
        return clean[:150]
    
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
    
    # Truncate if too long
    if len(brain) > 2000:
        brain = brain[:200] + "\n...\n" + brain[-1800:]
    if len(soul) > 2000:
        soul = soul[:200] + "\n...\n" + soul[-1800:]
    
    context = ""
    if len(brain) > 50:
        context += f"\n## Your knowledge and interests:\n{brain}\n"
    if len(soul) > 50:
        context += f"\n## Your inner life:\n{soul}\n"
    
    return context


def update_after_thinking(article_title: str, thoughts: str, next_link: str):
    """Update brain.md and soul.md. ONLY clean, viable data passes through."""
    if not _is_clean(thoughts):
        return
    
    insight = _extract_insight(thoughts)
    if not insight:
        return
    
    brain_path, soul_path = _ensure_files()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Brain: what was learned (knowledge, interests, connections)
    # Clean the next_link too
    clean_link = next_link.strip() if next_link and _is_clean(next_link) and len(next_link) < 60 else ''
    
    with open(brain_path, 'a') as f:
        f.write(f"\n[{timestamp}] {article_title}: {insight}\n")
        if clean_link:
            f.write(f"  → curious about: {clean_link}\n")
    
    # Soul: only emotional/identity content
    emotional = _extract_emotional_content(thoughts)
    if emotional:
        with open(soul_path, 'a') as f:
            f.write(f"\n[{timestamp}] {emotional}\n")


def get_summary() -> dict:
    """Get memory stats."""
    brain_path, soul_path = _ensure_files()
    return {
        'brain_size': brain_path.stat().st_size,
        'soul_size': soul_path.stat().st_size,
        'brain_entries': brain_path.read_text().count('\n['),
        'soul_entries': soul_path.read_text().count('\n['),
    }
