#!/usr/bin/env python3
"""
Visitor Impact Tracker — measures how visitor conversations change
specimen exploration patterns. Compares brain.md/soul.md before and
after visitor sessions.

Usage:
    python3 scripts/visitor_impact_tracker.py tank-visitor-01-aria
    python3 scripts/visitor_impact_tracker.py  # all visitor tanks
"""
import os, sys, json
from datetime import datetime
from pathlib import Path
from collections import Counter

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
VISITOR_LOGS = LOGS_DIR / 'visitor_sessions'

VISITOR_TANKS = ['tank-visitor-01-aria', 'tank-visitor-02-felix', 'tank-visitor-03-luna']


def get_brain_topics(tank_id):
    """Extract topic frequency from brain.md."""
    brain = LOGS_DIR / tank_id / 'brain.md'
    if not brain.exists():
        return {}
    topics = []
    for line in brain.read_text().splitlines():
        if line.strip().startswith('['):
            try:
                topics.append(line.split('] ')[1].split(':')[0].strip())
            except:
                pass
    return dict(Counter(topics).most_common(20))


def get_soul_emotions(tank_id):
    """Extract emotional word frequency from soul.md."""
    soul = LOGS_DIR / tank_id / 'soul.md'
    if not soul.exists():
        return {}
    emotion_words = ['wonder', 'curious', 'fascinate', 'fear', 'joy', 'confused',
                     'excited', 'peaceful', 'lonely', 'hope', 'love', 'anxious']
    text = soul.read_text().lower()
    return {w: text.count(w) for w in emotion_words if text.count(w) > 0}


def get_visitor_sessions(tank_id):
    """Get visitor session data."""
    if not VISITOR_LOGS.exists():
        return []
    sessions = []
    for f in sorted(VISITOR_LOGS.glob('*.jsonl')):
        entries = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        if entries and entries[0].get('specimen') == tank_id.split('-')[-1]:
            sessions.append({
                'file': f.name,
                'entries': len(entries),
                'first': entries[0].get('timestamp', ''),
                'last': entries[-1].get('timestamp', '')
            })
    return sessions


def analyze_tank(tank_id):
    """Full impact analysis for a visitor tank."""
    brain_lines = len((LOGS_DIR / tank_id / 'brain.md').read_text().splitlines()) if (LOGS_DIR / tank_id / 'brain.md').exists() else 0
    soul_lines = len((LOGS_DIR / tank_id / 'soul.md').read_text().splitlines()) if (LOGS_DIR / tank_id / 'soul.md').exists() else 0
    topics = get_brain_topics(tank_id)
    emotions = get_soul_emotions(tank_id)
    sessions = get_visitor_sessions(tank_id)
    
    return {
        'tank': tank_id,
        'timestamp': datetime.now().isoformat(),
        'brain_lines': brain_lines,
        'soul_lines': soul_lines,
        'top_topics': dict(list(topics.items())[:10]),
        'emotions': emotions,
        'visitor_sessions': len(sessions),
        'session_details': sessions
    }


def main():
    tanks = sys.argv[1:] if len(sys.argv) > 1 else VISITOR_TANKS
    
    report_dir = LOGS_DIR / 'visitor_impact'
    report_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"=== Visitor Impact Analysis — {datetime.now().isoformat()} ===\n")
    
    results = []
    for tank_id in tanks:
        analysis = analyze_tank(tank_id)
        results.append(analysis)
        name = tank_id.split('-')[-1].title()
        print(f"{name}:")
        print(f"  Brain: {analysis['brain_lines']}L, Soul: {analysis['soul_lines']}L")
        print(f"  Top topics: {', '.join(list(analysis['top_topics'].keys())[:5])}")
        print(f"  Emotions: {analysis['emotions']}")
        print(f"  Visitor sessions: {analysis['visitor_sessions']}")
        print()
    
    # Save report
    report_path = report_dir / f"impact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Report saved: {report_path}")


if __name__ == '__main__':
    main()
