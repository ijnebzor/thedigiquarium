#!/usr/bin/env python3
"""
Fix double-encoded UTF-8 v3 — handles mixed lines with both correct UTF-8 and mojibake.
Walks through each line segment-by-segment.
"""
import os, sys
from pathlib import Path

DIGIQUARIUM = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LANGUAGE_TANKS = ['tank-09-wei', 'tank-10-mei', 'tank-11-haruki', 'tank-12-sakura']

def fix_mixed_line(line):
    """Fix a line that may contain both valid UTF-8 and double-encoded segments."""
    result = []
    buf = []  # accumulate chars that might be double-encoded
    
    for ch in line:
        cp = ord(ch)
        if 0x80 <= cp <= 0xFF:
            # This char is in the latin-1 extended range — might be part of double-encoded UTF-8
            buf.append(ch)
        else:
            # This is ASCII or a char above U+00FF (already valid Unicode like →, CJK, etc.)
            if buf:
                # Try to decode accumulated buffer
                segment = ''.join(buf)
                try:
                    decoded = segment.encode('latin-1').decode('utf-8')
                    result.append(decoded)
                except (UnicodeDecodeError, UnicodeEncodeError):
                    result.append(segment)  # keep as-is if can't decode
                buf = []
            result.append(ch)
    
    # Handle any remaining buffer
    if buf:
        segment = ''.join(buf)
        try:
            decoded = segment.encode('latin-1').decode('utf-8')
            result.append(decoded)
        except (UnicodeDecodeError, UnicodeEncodeError):
            result.append(segment)
    
    return ''.join(result)

def has_mojibake(line):
    """Quick check if line likely has double-encoded text."""
    for ch in line:
        cp = ord(ch)
        if 0xC0 <= cp <= 0xFF:
            return True
    return False

def fix_file(filepath):
    if not filepath.exists():
        return 0, 0
    content = filepath.read_text(encoding='utf-8')
    lines = content.split('\n')
    fixed_count = 0
    new_lines = []
    for line in lines:
        if has_mojibake(line):
            fixed = fix_mixed_line(line)
            if fixed != line:
                new_lines.append(fixed)
                fixed_count += 1
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    if fixed_count > 0:
        filepath.write_text('\n'.join(new_lines), encoding='utf-8')
    return fixed_count, len(lines)

def main():
    tanks = sys.argv[1:] if len(sys.argv) > 1 else LANGUAGE_TANKS
    print(f"=== FIX DOUBLE-ENCODING v3 (mixed lines) — {len(tanks)} tanks ===\n")
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
