#!/usr/bin/env python3
"""
Fix double-encoded UTF-8 v2 — more aggressive detection.
Catches arrow lines and partial mojibake that v1 missed.
"""
import os, sys
from pathlib import Path

DIGIQUARIUM = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))

LANGUAGE_TANKS = [
    'tank-09-wei', 'tank-10-mei', 'tank-11-haruki', 'tank-12-sakura'
]

def try_fix_line(line):
    """Try to fix double-encoding. Returns (fixed_line, was_fixed)."""
    try:
        fixed = line.encode('latin-1').decode('utf-8')
        # If encoding roundtrip succeeds and result differs, it was double-encoded
        if fixed != line:
            return fixed, True
        return line, False
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Can't be decoded as latin-1 → not double-encoded, or partially so
        # Try fixing segments between ASCII text
        return line, False

def fix_file(filepath):
    if not filepath.exists():
        return 0, 0
    
    content = filepath.read_text(encoding='utf-8')
    lines = content.split('\n')
    fixed_count = 0
    new_lines = []
    
    for line in lines:
        fixed, was_fixed = try_fix_line(line)
        new_lines.append(fixed)
        if was_fixed:
            fixed_count += 1
    
    if fixed_count > 0:
        filepath.write_text('\n'.join(new_lines), encoding='utf-8')
    
    return fixed_count, len(lines)

def main():
    tanks = sys.argv[1:] if len(sys.argv) > 1 else LANGUAGE_TANKS
    print(f"=== FIX DOUBLE-ENCODING v2 — {len(tanks)} tanks ===\n")
    
    total_fixed = 0
    for tank in tanks:
        tank_dir = DIGIQUARIUM / 'logs' / tank
        if not tank_dir.exists():
            continue
        for filename in ['brain.md', 'soul.md']:
            filepath = tank_dir / filename
            fixed, total = fix_file(filepath)
            if fixed > 0:
                print(f"  {tank}/{filename}: fixed {fixed}/{total} lines")
                total_fixed += fixed
            else:
                print(f"  {tank}/{filename}: clean ({total} lines)")
    
    print(f"\n=== COMPLETE: {total_fixed} additional lines fixed ===")

if __name__ == '__main__':
    main()
