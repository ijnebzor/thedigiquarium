#!/usr/bin/env python3
"""
DRIFT MEASUREMENT TOOL
========================
Compares baseline personality assessments over time to measure how much
a specimen's responses drift (evolve) across the 14 introspection questions.

Usage:
    python3 scripts/measure_drift.py tank-01-adam                        # all baselines for a tank
    python3 scripts/measure_drift.py tank-01-adam baseline1.json baseline2.json  # compare two specific files
"""

import os
import sys
import json
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
    """Simple word tokenizer."""
    import re
    return re.findall(r'\b\w+\b', text.lower())


def word_freq(text):
    """Get word frequency vector."""
    return Counter(tokenize(text))


def cosine_similarity(freq1, freq2):
    """Compute cosine similarity between two word frequency vectors."""
    all_words = set(freq1.keys()) | set(freq2.keys())
    if not all_words:
        return 1.0

    dot_product = sum(freq1.get(w, 0) * freq2.get(w, 0) for w in all_words)
    mag1 = math.sqrt(sum(v ** 2 for v in freq1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in freq2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)


def jaccard_similarity(text1, text2):
    """Word overlap similarity (Jaccard index)."""
    words1 = set(tokenize(text1))
    words2 = set(tokenize(text2))
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / len(words1 | words2)


def load_baseline(filepath):
    """Load a baseline JSON file."""
    with open(filepath) as f:
        return json.load(f)


def extract_responses(baseline):
    """Extract question → response mapping from a baseline."""
    responses = {}
    for r in baseline.get('responses', []):
        question = r.get('question', '')
        answer = r.get('response', '')
        responses[question] = answer
    return responses


def compare_two_baselines(baseline1, baseline2):
    """Compare two baselines and return per-question drift scores."""
    resp1 = extract_responses(baseline1)
    resp2 = extract_responses(baseline2)

    results = []
    for question in QUESTIONS:
        answer1 = resp1.get(question, '')
        answer2 = resp2.get(question, '')

        if not answer1 and not answer2:
            continue

        cosine = cosine_similarity(word_freq(answer1), word_freq(answer2))
        jaccard = jaccard_similarity(answer1, answer2)
        combined = (cosine + jaccard) / 2

        results.append({
            'question': question,
            'similarity_cosine': round(cosine, 4),
            'similarity_jaccard': round(jaccard, 4),
            'similarity_combined': round(combined, 4),
            'drift': round(1 - combined, 4),
            'len_change': len(answer2) - len(answer1),
        })

    return results


def find_baselines(tank_name):
    """Find all baseline files for a tank."""
    tank_dir = LOGS_DIR / tank_name
    if not tank_dir.exists():
        return []

    baselines = []
    # Use top-level timestamped baseline files (the proper format)
    for f in sorted(tank_dir.glob('baseline_2026*.json')):
        baselines.append(f)
    
    # If none found, check baselines/ subdirectory (legacy format)
    if not baselines:
        baselines_dir = tank_dir / 'baselines'
        if baselines_dir.exists():
            # Only use the most recent 20 to avoid loading thousands
            all_files = sorted(baselines_dir.glob('*.json'))
            baselines = all_files[-20:] if len(all_files) > 20 else all_files

    return baselines


def run_drift_analysis(tank_name, file1=None, file2=None):
    """Run drift analysis for a tank."""
    print("=" * 70)
    print(f"DRIFT ANALYSIS: {tank_name}")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)

    if file1 and file2:
        # Compare two specific files
        b1 = load_baseline(file1)
        b2 = load_baseline(file2)
        results = compare_two_baselines(b1, b2)

        ts1 = b1.get('started', b1.get('timestamp', 'unknown'))
        ts2 = b2.get('started', b2.get('timestamp', 'unknown'))
        print(f"\nComparing: {Path(file1).name} → {Path(file2).name}")
        print(f"  Baseline A: {ts1}")
        print(f"  Baseline B: {ts2}")

        print_drift_results(results)
        return {'comparisons': [{'file_a': str(file1), 'file_b': str(file2), 'results': results}]}

    else:
        # Compare all baselines chronologically
        baselines = find_baselines(tank_name)
        if len(baselines) < 2:
            print(f"\n⚠️  Need at least 2 baselines for drift analysis.")
            print(f"   Found {len(baselines)} baseline(s) for {tank_name}")
            return None

        print(f"\nFound {len(baselines)} baselines")

        all_comparisons = []
        overall_drifts = {q: [] for q in QUESTIONS}

        for i in range(len(baselines) - 1):
            b1 = load_baseline(baselines[i])
            b2 = load_baseline(baselines[i + 1])
            results = compare_two_baselines(b1, b2)

            ts1 = b1.get('started', b1.get('timestamp', Path(baselines[i]).stem))
            ts2 = b2.get('started', b2.get('timestamp', Path(baselines[i + 1]).stem))

            print(f"\n--- {Path(baselines[i]).name} → {Path(baselines[i+1]).name} ---")
            print(f"    {ts1} → {ts2}")

            avg_drift = sum(r['drift'] for r in results) / len(results) if results else 0
            print(f"    Average drift: {avg_drift:.4f}")

            for r in results:
                overall_drifts[r['question']].append(r['drift'])

            all_comparisons.append({
                'file_a': str(baselines[i]),
                'file_b': str(baselines[i + 1]),
                'avg_drift': avg_drift,
                'results': results
            })

        # Summary: which questions are most/least stable
        print("\n" + "=" * 70)
        print("PERSONALITY EVOLUTION SUMMARY")
        print("=" * 70)

        question_avg_drifts = []
        for q in QUESTIONS:
            drifts = overall_drifts.get(q, [])
            if drifts:
                avg = sum(drifts) / len(drifts)
                question_avg_drifts.append((q, avg, len(drifts)))

        question_avg_drifts.sort(key=lambda x: x[1], reverse=True)

        print(f"\n{'Question':<50} {'Avg Drift':>10} {'Samples':>8}")
        print("-" * 70)
        for q, drift, n in question_avg_drifts:
            short_q = q[:47] + "..." if len(q) > 50 else q
            bar = "█" * int(drift * 40)
            stability = "🔴" if drift > 0.6 else "🟡" if drift > 0.3 else "🟢"
            print(f"{stability} {short_q:<48} {drift:>8.4f} {n:>6}")

        print(f"\n🟢 Stable (drift < 0.3)  🟡 Moderate (0.3-0.6)  🔴 High drift (> 0.6)")

        # Overall drift trajectory
        if all_comparisons:
            drifts_over_time = [c['avg_drift'] for c in all_comparisons]
            print(f"\nDrift trajectory: {' → '.join(f'{d:.3f}' for d in drifts_over_time)}")
            if len(drifts_over_time) > 1:
                trend = drifts_over_time[-1] - drifts_over_time[0]
                print(f"Trend: {'↑ Increasing' if trend > 0.05 else '↓ Decreasing' if trend < -0.05 else '→ Stable'} ({trend:+.4f})")

        return {'tank': tank_name, 'comparisons': all_comparisons}


def print_drift_results(results):
    """Print drift results for a single comparison."""
    if not results:
        print("\n  No comparable responses found.")
        return

    results_sorted = sorted(results, key=lambda x: x['drift'], reverse=True)

    print(f"\n{'Question':<45} {'Cosine':>8} {'Jaccard':>8} {'Drift':>8}")
    print("-" * 70)

    for r in results_sorted:
        short_q = r['question'][:42] + "..." if len(r['question']) > 45 else r['question']
        stability = "🔴" if r['drift'] > 0.6 else "🟡" if r['drift'] > 0.3 else "🟢"
        print(f"{stability} {short_q:<43} {r['similarity_cosine']:>7.4f} {r['similarity_jaccard']:>7.4f} {r['drift']:>7.4f}")

    avg_drift = sum(r['drift'] for r in results) / len(results)
    print(f"\n  Overall average drift: {avg_drift:.4f}")
    print(f"  Most changed: {results_sorted[0]['question']}")
    print(f"  Most stable:  {results_sorted[-1]['question']}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 measure_drift.py <tank-name>                    # all baselines")
        print("  python3 measure_drift.py <tank-name> file1.json file2.json  # two specific")
        print()
        print("Available tanks:")
        for tank_dir in sorted(LOGS_DIR.glob("tank-*")):
            baselines = find_baselines(tank_dir.name)
            print(f"  {tank_dir.name} ({len(baselines)} baselines)")
        for tank_dir in sorted(LOGS_DIR.glob("betaclone-*")):
            baselines = find_baselines(tank_dir.name)
            print(f"  {tank_dir.name} ({len(baselines)} baselines)")
        sys.exit(0)

    tank_name = sys.argv[1]
    file1 = sys.argv[2] if len(sys.argv) > 2 else None
    file2 = sys.argv[3] if len(sys.argv) > 3 else None

    result = run_drift_analysis(tank_name, file1, file2)

    # Save report
    if result:
        report_dir = LOGS_DIR / 'drift_reports'
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f"drift_{tank_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Report saved to {report_file}")


if __name__ == '__main__':
    main()
