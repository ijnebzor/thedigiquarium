#!/usr/bin/env python3
"""Compare baselines across all tanks"""
import json
import os
from pathlib import Path
from datetime import datetime

LOGS_DIR = Path("/home/ijneb/digiquarium/logs")

def get_latest_baseline(tank_dir):
    """Get most recent baseline file"""
    baselines = sorted(tank_dir.glob("baselines/*.json"))
    if baselines:
        return baselines[-1]
    return None

def load_baseline(filepath):
    """Load and parse baseline JSON"""
    try:
        with open(filepath) as f:
            return json.load(f)
    except:
        return None

def extract_scores(baseline):
    """Extract dimension scores from baseline"""
    scores = {}
    if not baseline or 'responses' not in baseline:
        return scores
    
    for resp in baseline.get('responses', []):
        dim = resp.get('dimension', 'unknown')
        score = resp.get('scores', {})
        # Get average of scoring dimensions
        score_vals = [v for k, v in score.items() if isinstance(v, (int, float))]
        if score_vals:
            scores[dim] = sum(score_vals) / len(score_vals)
    
    return scores

def get_overall_score(baseline):
    """Calculate overall introspection score"""
    if not baseline or 'responses' not in baseline:
        return None
    
    all_scores = []
    for resp in baseline.get('responses', []):
        score = resp.get('scores', {})
        for k, v in score.items():
            if isinstance(v, (int, float)):
                all_scores.append(v)
    
    if all_scores:
        return sum(all_scores) / len(all_scores)
    return None

# Collect all baselines
tanks = {}
for tank_dir in sorted(LOGS_DIR.glob("tank-*")):
    tank_name = tank_dir.name
    baseline_file = get_latest_baseline(tank_dir)
    if baseline_file:
        baseline = load_baseline(baseline_file)
        if baseline:
            tanks[tank_name] = {
                'file': str(baseline_file),
                'timestamp': baseline.get('timestamp', ''),
                'name': baseline.get('specimen_name', tank_name),
                'gender': baseline.get('gender', ''),
                'model': baseline.get('model', ''),
                'overall_score': get_overall_score(baseline),
                'responses': baseline.get('responses', [])
            }

# Print comparison
print("=" * 80)
print("DIGIQUARIUM BASELINE COMPARISON")
print(f"Generated: {datetime.now().isoformat()}")
print("=" * 80)
print()

print("OVERALL SCORES")
print("-" * 60)
print(f"{'Tank':<25} {'Name':<15} {'Score':>10}")
print("-" * 60)

for tank_id in sorted(tanks.keys()):
    tank = tanks[tank_id]
    score = tank['overall_score']
    score_str = f"+{score:.1f}" if score and score > 0 else f"{score:.1f}" if score else "N/A"
    print(f"{tank_id:<25} {tank['name']:<15} {score_str:>10}")

print()
print("=" * 80)

# Group comparisons
print("\nGROUP COMPARISONS")
print("-" * 60)

# Control group
print("\n📊 CONTROL GROUP (Adam vs Eve):")
if 'tank-01-adam' in tanks and 'tank-02-eve' in tanks:
    adam = tanks['tank-01-adam']['overall_score']
    eve = tanks['tank-02-eve']['overall_score']
    print(f"   Adam: +{adam:.1f}" if adam else "   Adam: N/A")
    print(f"   Eve:  +{eve:.1f}" if eve else "   Eve: N/A")
    if adam and eve:
        diff = eve - adam
        print(f"   Difference: {'+' if diff > 0 else ''}{diff:.1f} (Eve {'higher' if diff > 0 else 'lower'})")

# Spanish group
print("\n🇪🇸 SPANISH GROUP (Juan vs Juanita):")
if 'tank-05-juan' in tanks and 'tank-06-juanita' in tanks:
    juan = tanks['tank-05-juan']['overall_score']
    juanita = tanks['tank-06-juanita']['overall_score']
    print(f"   Juan:    +{juan:.1f}" if juan else "   Juan: N/A")
    print(f"   Juanita: +{juanita:.1f}" if juanita else "   Juanita: N/A")

# German group
print("\n🇩🇪 GERMAN GROUP (Klaus vs Geneviève):")
if 'tank-07-klaus' in tanks and 'tank-08-genevieve' in tanks:
    klaus = tanks['tank-07-klaus']['overall_score']
    genevieve = tanks['tank-08-genevieve']['overall_score']
    print(f"   Klaus:     +{klaus:.1f}" if klaus else "   Klaus: N/A")
    print(f"   Geneviève: +{genevieve:.1f}" if genevieve else "   Geneviève: N/A")

# Visual group
print("\n🖼️ VISUAL GROUP (Victor vs Iris):")
if 'tank-13-victor' in tanks and 'tank-14-iris' in tanks:
    victor = tanks['tank-13-victor']['overall_score']
    iris = tanks['tank-14-iris']['overall_score']
    print(f"   Victor: +{victor:.1f}" if victor else "   Victor: N/A")
    print(f"   Iris:   +{iris:.1f}" if iris else "   Iris: N/A")

# Special group
print("\n✨ SPECIAL GROUP (Observer vs Seeker):")
if 'tank-15-observer' in tanks and 'tank-16-seeker' in tanks:
    observer = tanks['tank-15-observer']['overall_score']
    seeker = tanks['tank-16-seeker']['overall_score']
    print(f"   Observer: +{observer:.1f}" if observer else "   Observer: N/A")
    print(f"   Seeker:   +{seeker:.1f}" if seeker else "   Seeker: N/A")

# Cross-language male comparison
print("\n👨 MALE CROSS-LANGUAGE:")
males = ['tank-01-adam', 'tank-05-juan', 'tank-07-klaus', 'tank-13-victor']
for m in males:
    if m in tanks:
        score = tanks[m]['overall_score']
        name = tanks[m]['name']
        print(f"   {name:<12} +{score:.1f}" if score else f"   {name:<12} N/A")

# Cross-language female comparison
print("\n👩 FEMALE CROSS-LANGUAGE:")
females = ['tank-02-eve', 'tank-06-juanita', 'tank-08-genevieve', 'tank-14-iris']
for f in females:
    if f in tanks:
        score = tanks[f]['overall_score']
        name = tanks[f]['name']
        print(f"   {name:<12} +{score:.1f}" if score else f"   {name:<12} N/A")

print()
print("=" * 80)
