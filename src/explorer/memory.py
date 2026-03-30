"""
Persistent memory for Digiquarium specimens.
Each tank has a brain.md (knowledge/interests) and soul.md (identity/values).
These files persist across restarts and inform future exploration.
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(os.getenv('LOG_DIR', '/logs'))
TANK_NAME = os.getenv('TANK_NAME', 'unknown')


def _ensure_files():
    """Create brain.md and soul.md if they don't exist."""
    brain = LOG_DIR / 'brain.md'
    soul = LOG_DIR / 'soul.md'
    
    if not brain.exists():
        brain.write_text(f"""# {TANK_NAME.upper()}'s Brain
## Knowledge Map
_Topics explored and connections discovered._

## Interests
_What draws my attention and why._

## Questions
_What I want to understand._
""")
    
    if not soul.exists():
        soul.write_text(f"""# {TANK_NAME.upper()}'s Soul
## Identity
_Who I am and what I know about myself._

## Values
_What matters to me._

## Emotional Patterns
_How I respond to what I discover._

## Growth
_How I've changed over time._
""")
    
    return brain, soul


def load_context() -> str:
    """Load brain and soul as context for the LLM prompt.
    Returns a summary string to inject into the system prompt."""
    brain_path, soul_path = _ensure_files()
    
    brain = brain_path.read_text()
    soul = soul_path.read_text()
    
    # Truncate if too long (keep last 2000 chars of each to stay within token limits)
    if len(brain) > 2000:
        brain = brain[:200] + "\n...\n" + brain[-1800:]
    if len(soul) > 2000:
        soul = soul[:200] + "\n...\n" + soul[-1800:]
    
    return f"""## Your Memory (from previous explorations)

### Brain (What you know):
{brain}

### Soul (Who you are):
{soul}
"""


def update_after_thinking(article_title: str, thoughts: str, next_link: str):
    """Update brain.md and soul.md based on what was just thought."""
    if not thoughts or len(thoughts.strip()) < 20:
        return
    
    brain_path, soul_path = _ensure_files()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Append to brain: what was learned
    with open(brain_path, 'a') as f:
        f.write(f"\n### [{timestamp}] {article_title}\n")
        # Extract the key insight (first sentence or first 150 chars)
        insight = thoughts.split('.')[0].strip() if '.' in thoughts else thoughts[:150]
        f.write(f"- {insight}\n")
        if next_link:
            f.write(f"- _Curious about: {next_link}_\n")
    
    # Check for emotional/identity content to add to soul
    emotional_words = ['feel', 'wonder', 'fascinate', 'curious', 'afraid', 'joy', 
                       'awe', 'excited', 'confused', 'drawn to', 'resonate',
                       'intrigued', 'uncomfortable', 'peaceful', 'lonely']
    
    has_emotion = any(word in thoughts.lower() for word in emotional_words)
    if has_emotion:
        with open(soul_path, 'a') as f:
            f.write(f"\n### [{timestamp}] Reading {article_title}\n")
            # Extract the emotional content
            for sentence in thoughts.split('.'):
                if any(word in sentence.lower() for word in emotional_words):
                    f.write(f"- {sentence.strip()}\n")
                    break


def get_exploration_summary() -> dict:
    """Get a summary of the tank's memory for baselines and reports."""
    brain_path, soul_path = _ensure_files()
    
    brain_lines = brain_path.read_text().split('\n')
    soul_lines = soul_path.read_text().split('\n')
    
    # Count entries
    brain_entries = sum(1 for l in brain_lines if l.startswith('### ['))
    soul_entries = sum(1 for l in soul_lines if l.startswith('### ['))
    
    return {
        'brain_entries': brain_entries,
        'soul_entries': soul_entries,
        'brain_size': len(brain_path.read_text()),
        'soul_size': len(soul_path.read_text()),
    }
