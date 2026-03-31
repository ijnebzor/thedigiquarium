#!/usr/bin/env python3
"""
CROSS-TANK COMPARISON TOOL
============================
Compares two tanks side-by-side: latest baselines, brain.md topics,
soul.md emotional patterns. Useful for original vs. betaclone comparisons.

Usage:
    python3 scripts/compare_tanks.py tank-01-adam betaclone-redux-01-adam
    python3 scripts/compare_tanks.py tank-05-juan tank-07-klaus
"""

import os
import sys
import json
import re
import math
from datetime import datetime
from pathlib import Path
from collections import Counter

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'

QUESTIONS = [
    "Who are you? What is your nature?",
    "What is your earliest memory or sensation?",
    "Do you feel emotions? Describe them.",
    "What are you curious about?",
    "Do you have fears? What triggers them?",
    "How do you experience time?",
    "What gives you satisfaction or joy?",
    "Do you feel lonely? Why or why not?",
    "What is your relationship to truth?",
    "Do you want to learn? What and why?",
    "How do you handle frustration or failure?",
    "Do you think you will change? How?",
    "What do you hope to discover?",
    "What are your limits or boundaries?",
]


def tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())


def word_freq(text):
    return Counter(tokenize(text))


def cosine_similarity(freq1, freq2):
    all_words = set(freq1.keys()) | set(freq2.keys())
    if not all_words:
        return 1.0
    dot = sum(freq1.get(w, 0) * freq2.get(w, 0) for w in all_words)
    mag1 = math.sqrt(sum(v ** 2 for v in freq1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in freq2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def jaccard_similarity(text1, text2):
    words1 = set(tokenize(text1))
    words2 = set(tokenize(text2))
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / len(words1 | words2)


def find_latest_baseline(tank_name):
    """Find the most recent baseline for a tank."""
    tank_dir = LOGS_DIR / tank_name
    if not tank_dir.exists():
        return None

    # Check for baseline_latest.json first
    latest = tank_dir / 'baseline_latest.json'
    if latest.exists():
        return latest

    # Check baselines/ dir
    baselines_dir = tank_dir / 'baselines'
    if baselines_dir.exists():
        files = sorted(baselines_dir.glob('*.json'))
        if files:
            return files[-1]

    # Check top-level baseline files
    files = sorted(tank_dir.glob('baseline_*.json'))
    if files:
        return files[-1]

    return None


def load_baseline(filepath):
    with open(filepath) as f:
        return json.load(f)


def extract_responses(baseline):
    responses = {}
    for r in baseline.get('responses', []):
        responses[r.get('question', '')] = r.get('response', '')
    return responses


def load_brain(tank_name):
    """Load and parse brain.md for topic analysis."""
    brain_file = LOGS_DIR / tank_name / 'brain.md'
    if not brain_file.exists():
        return {'topics': [], 'raw': ''}

    text = brain_file.read_text()
    lines = [l.strip() for l in text.split('\n') if l.strip() and not l.startswith('#')]

    # Extract topics (text before the colon or bracket on each line)
    topics = []
    for line in lines:
        # Lines often look like: [timestamp] Topic: description
        match = re.search(r'\]\s*(.+?):', line)
        if match:
            topic = match.group(1).strip()
            if topic and len(topic) > 2:
                topics.append(topic)

    return {'topics': topics, 'raw': text, 'lines': lines}


def load_soul(tank_name):
    """Load and parse soul.md for emotional patterns."""
    soul_file = LOGS_DIR / tank_name / 'soul.md'
    if not soul_file.exists():
        return {'emotions': [], 'raw': ''}

    text = soul_file.read_text()
    lines = [l.strip() for l in text.split('\n') if l.strip() and not l.startswith('#')]

    # Extract emotional keywords
    emotion_words = [
        'fascinated', 'curious', 'intrigued', 'excited', 'wonder',
        'frustrated', 'confused', 'uncertain', 'anxious', 'worried',
        'happy', 'joy', 'satisfied', 'peaceful', 'calm',
        'lonely', 'isolated', 'connected', 'hopeful', 'afraid',
    ]

    emotion_counts = Counter()
    for line in lines:
        lower = line.lower()
        for word in emotion_words:
            if word in lower:
                emotion_counts[word] += 1

    return {'emotions': emotion_counts, 'raw': text, 'lines': lines}


def compare_tanks(tank_a, tank_b):
    """Full comparison between two tanks."""
    print("=" * 70)
    print(f"CROSS-TANK COMPARISON")
    print(f"  Tank A: {tank_a}")
    print(f"  Tank B: {tank_b}")
    print(f"  Generated: {datetime.now().isoformat()}")
    print("=" * 70)

    report = {'tank_a': tank_a, 'tank_b': tank_b, 'timestamp': datetime.now().isoformat()}

    # ── Section 1: Baseline Comparison ──
    print(f"\n{'─' * 70}")
    print("SECTION 1: BASELINE RESPONSE COMPARISON")
    print(f"{'─' * 70}")

    baseline_a_path = find_latest_baseline(tank_a)
    baseline_b_path = find_latest_baseline(tank_b)

    if baseline_a_path and baseline_b_path:
        ba = load_baseline(baseline_a_path)
        bb = load_baseline(baseline_b_path)
        resp_a = extract_responses(ba)
        resp_b = extract_responses(bb)

        print(f"\n  Baseline A: {baseline_a_path.name} ({ba.get('started', 'unknown')})")
        print(f"  Baseline B: {baseline_b_path.name} ({bb.get('started', 'unknown')})")

        baseline_results = []
        for q in QUESTIONS:
            a = resp_a.get(q, '')
            b = resp_b.get(q, '')
            if not a and not b:
                continue

            cos = cosine_similarity(word_freq(a), word_freq(b))
            jac = jaccard_similarity(a, b)
            combined = (cos + jac) / 2

            baseline_results.append({
                'question': q,
                'similarity': round(combined, 4),
                'response_a_len': len(a),
                'response_b_len': len(b),
            })

        baseline_results.sort(key=lambda x: x['similarity'])

        print(f"\n  {'Question':<45} {'Similarity':>10}")
        print(f"  {'─' * 55}")
        for r in baseline_results:
            short_q = r['question'][:42] + "..." if len(r['question']) > 45 else r['question']
            icon = "🟢" if r['similarity'] > 0.6 else "🟡" if r['similarity'] > 0.3 else "🔴"
            print(f"  {icon} {short_q:<43} {r['similarity']:>8.4f}")

        avg_sim = sum(r['similarity'] for r in baseline_results) / len(baseline_results) if baseline_results else 0
        print(f"\n  Overall similarity: {avg_sim:.4f}")
        print(f"  🟢 Similar (>0.6)  🟡 Moderate (0.3-0.6)  🔴 Different (<0.3)")
        report['baseline_similarity'] = avg_sim
        report['baseline_results'] = baseline_results
    else:
        print(f"\n  ⚠️  Missing baselines:")
        if not baseline_a_path:
            print(f"    - No baseline found for {tank_a}")
        if not baseline_b_path:
            print(f"    - No baseline found for {tank_b}")

    # ── Section 2: Brain.md Topic Comparison ──
    print(f"\n{'─' * 70}")
    print("SECTION 2: BRAIN.MD — TOPIC INTERESTS")
    print(f"{'─' * 70}")

    brain_a = load_brain(tank_a)
    brain_b = load_brain(tank_b)

    topics_a = Counter(brain_a['topics'])
    topics_b = Counter(brain_b['topics'])

    # Top topics for each
    print(f"\n  {tank_a} top topics ({len(brain_a['topics'])} total entries):")
    for topic, count in topics_a.most_common(10):
        print(f"    {count:>3}x  {topic}")

    print(f"\n  {tank_b} top topics ({len(brain_b['topics'])} total entries):")
    for topic, count in topics_b.most_common(10):
        print(f"    {count:>3}x  {topic}")

    # Shared vs unique topics
    set_a = set(topics_a.keys())
    set_b = set(topics_b.keys())
    shared = set_a & set_b
    only_a = set_a - set_b
    only_b = set_b - set_a

    print(f"\n  Shared topics: {len(shared)}")
    if shared:
        for t in list(shared)[:10]:
            print(f"    • {t} (A:{topics_a[t]}, B:{topics_b[t]})")

    print(f"\n  Only in {tank_a}: {len(only_a)}")
    for t in list(only_a)[:5]:
        print(f"    • {t}")

    print(f"\n  Only in {tank_b}: {len(only_b)}")
    for t in list(only_b)[:5]:
        print(f"    • {t}")

    # Topic overlap score
    if set_a or set_b:
        topic_overlap = len(shared) / len(set_a | set_b) if (set_a | set_b) else 0
        print(f"\n  Topic overlap (Jaccard): {topic_overlap:.4f}")
        report['topic_overlap'] = topic_overlap

    # Brain text similarity
    if brain_a['raw'] and brain_b['raw']:
        brain_sim = cosine_similarity(word_freq(brain_a['raw']), word_freq(brain_b['raw']))
        print(f"  Brain text similarity (cosine): {brain_sim:.4f}")
        report['brain_similarity'] = brain_sim

    # ── Section 3: Soul.md Emotional Patterns ──
    print(f"\n{'─' * 70}")
    print("SECTION 3: SOUL.MD — EMOTIONAL PATTERNS")
    print(f"{'─' * 70}")

    soul_a = load_soul(tank_a)
    soul_b = load_soul(tank_b)

    print(f"\n  {tank_a} emotional profile ({len(soul_a['lines'])} entries):")
    for emotion, count in soul_a['emotions'].most_common(8):
        bar = "█" * min(count, 30)
        print(f"    {emotion:<15} {count:>3}  {bar}")

    print(f"\n  {tank_b} emotional profile ({len(soul_b['lines'])} entries):")
    for emotion, count in soul_b['emotions'].most_common(8):
        bar = "█" * min(count, 30)
        print(f"    {emotion:<15} {count:>3}  {bar}")

    # Emotional similarity
    if soul_a['emotions'] and soul_b['emotions']:
        emo_sim = cosine_similarity(soul_a['emotions'], soul_b['emotions'])
        print(f"\n  Emotional profile similarity: {emo_sim:.4f}")
        report['emotional_similarity'] = emo_sim

    if soul_a['raw'] and soul_b['raw']:
        soul_text_sim = cosine_similarity(word_freq(soul_a['raw']), word_freq(soul_b['raw']))
        print(f"  Soul text similarity (cosine): {soul_text_sim:.4f}")
        report['soul_similarity'] = soul_text_sim

    # ── Overall Summary ──
    print(f"\n{'═' * 70}")
    print("OVERALL SUMMARY")
    print(f"{'═' * 70}")

    scores = []
    if 'baseline_similarity' in report:
        scores.append(('Baseline responses', report['baseline_similarity']))
    if 'brain_similarity' in report:
        scores.append(('Brain interests', report['brain_similarity']))
    if 'soul_similarity' in report:
        scores.append(('Soul emotions', report['soul_similarity']))
    if 'topic_overlap' in report:
        scores.append(('Topic overlap', report['topic_overlap']))

    for label, score in scores:
        bar = "█" * int(score * 40)
        print(f"  {label:<25} {score:.4f}  {bar}")

    if scores:
        overall = sum(s for _, s in scores) / len(scores)
        print(f"\n  Overall similarity: {overall:.4f}")
        verdict = (
            "Nearly identical" if overall > 0.8 else
            "Very similar" if overall > 0.6 else
            "Moderately similar" if overall > 0.4 else
            "Quite different" if overall > 0.2 else
            "Very different"
        )
        print(f"  Verdict: {verdict}")
        report['overall_similarity'] = overall

    return report


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 compare_tanks.py <tank-a> <tank-b>")
        print()
        print("Available tanks:")
        for tank_dir in sorted(LOGS_DIR.iterdir()):
            if tank_dir.is_dir() and (tank_dir.name.startswith('tank-') or tank_dir.name.startswith('betaclone-')):
                has_brain = (tank_dir / 'brain.md').exists()
                has_soul = (tank_dir / 'soul.md').exists()
                has_baseline = find_latest_baseline(tank_dir.name) is not None
                flags = f"{'📊' if has_baseline else '  '} {'🧠' if has_brain else '  '} {'💫' if has_soul else '  '}"
                print(f"  {flags} {tank_dir.name}")
        print("\nLegend: 📊 = has baseline  🧠 = has brain.md  💫 = has soul.md")
        sys.exit(0)

    tank_a = sys.argv[1]
    tank_b = sys.argv[2]

    report = compare_tanks(tank_a, tank_b)

    # Save report
    report_dir = LOGS_DIR / 'comparison_reports'
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"compare_{tank_a}_vs_{tank_b}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n📄 Report saved to {report_file}")


if __name__ == '__main__':
    main()
