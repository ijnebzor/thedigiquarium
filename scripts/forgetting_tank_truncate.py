#!/usr/bin/env python3
"""Truncate brain.md to last 100 entries for the Forgetting Tank.
Run weekly via cron or manually."""
from pathlib import Path

BRAIN = Path('/home/ijneb/digiquarium/logs/tank-forgetting/brain.md')
if not BRAIN.exists():
    print("No brain.md found")
    exit()

lines = BRAIN.read_text().splitlines()
header = [l for l in lines if not l.strip().startswith('[')][:2]
entries = [l for l in lines if l.strip().startswith('[')]

if len(entries) > 100:
    kept = entries[-100:]
    BRAIN.write_text('\n'.join(header + [''] + kept) + '\n')
    print(f"Truncated: {len(entries)} → {len(kept)} entries")
else:
    print(f"Only {len(entries)} entries, no truncation needed")
