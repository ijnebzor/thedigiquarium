#!/usr/bin/env python3
"""
Fix double-encoded UTF-8 in language tank brain.md/soul.md files.
Double-encoding: UTF-8 bytes interpreted as latin-1, then re-encoded as UTF-8.
E.g. 地球 (UTF-8: E5 9C B0 E7 90 83) → å°ç (latin-1 interpretation)

Strategy: Try decode each line as latin-1→UTF-8. If it produces valid CJK/Japanese
and the original has mojibake patterns, replace the line.
"""
import os, sys, re
from pathlib import Path

DIGIQUARIUM = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))

# Mojibake patterns: sequences that appear when UTF-8 is double-encoded
MOJIBAKE_RE = re.compile(r'[\xc0-\xdf][\x80-\xbf]|[\xe0-\xef][\x80-\xbf]{2}|[\xf0-\xf7][\x80-\xbf]{3}')

# CJK Unicode ranges
CJK_RE = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]')

LANGUAGE_TANKS = [
    'tank-05-juan', 'tank-06-juanita', 'tank-07-klaus', 
    'tank-08-genevieve', 'tank-09-wei', 'tank-10-mei',
    'tank-11-haruki', 'tank-12-sakura'
]

def is_double_encoded(line):
    """Check if a line contains double-encoded UTF-8."""
    # Look for common mojibake byte patterns in the string
    # These are characters like Ã, Â, etc. that appear in double-encoded text
    mojibake_chars = set('ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ')
    has_mojibake = any(c in mojibake_chars for c in line)
    if not has_mojibake:
        return False
    # Try the fix and see if it produces CJK
    try:
        fixed = line.encode('latin-1').decode('utf-8')
        return bool(CJK_RE.search(fixed))
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False

def fix_line(line):
    """Fix a single double-encoded line."""
    try:
        return line.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return line

def fix_file(filepath):
    """Fix double-encoding in a single file. Returns (fixed_count, total_lines)."""
    if not filepath.exists():
        return 0, 0
    
    content = filepath.read_text(encoding='utf-8')
    lines = content.split('\n')
    fixed_count = 0
    new_lines = []
    
    for line in lines:
        if is_double_encoded(line):
            new_lines.append(fix_line(line))
            fixed_count += 1
        else:
            new_lines.append(line)
    
    if fixed_count > 0:
        filepath.write_text('\n'.join(new_lines), encoding='utf-8')
    
    return fixed_count, len(lines)

def main():
    tanks = sys.argv[1:] if len(sys.argv) > 1 else LANGUAGE_TANKS
    print(f"=== FIXING DOUBLE-ENCODED UTF-8 — {len(tanks)} tanks ===\n")
    
    total_fixed = 0
    for tank in tanks:
        tank_dir = DIGIQUARIUM / 'logs' / tank
        if not tank_dir.exists():
            print(f"  {tank}: no log directory, skipping")
            continue
        
        for filename in ['brain.md', 'soul.md']:
            filepath = tank_dir / filename
            fixed, total = fix_file(filepath)
            if fixed > 0:
                print(f"  {tank}/{filename}: fixed {fixed}/{total} lines")
                total_fixed += fixed
            else:
                print(f"  {tank}/{filename}: no double-encoding found ({total} lines)")
    
    print(f"\n=== COMPLETE: {total_fixed} lines fixed ===")

if __name__ == '__main__':
    main()
