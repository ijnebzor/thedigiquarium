#!/usr/bin/env python3
"""
Research Summary Generator — Produces a publishable research summary
from specimen data, drift reports, and congregation transcripts.

Outputs markdown suitable for the website's research section.

Usage: python3 scripts/generate_research_summary.py
"""
import os, json, re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DIGIQUARIUM = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS = DIGIQUARIUM / 'logs'
OUTPUT = DIGIQUARIUM / 'docs' / 'roadmap' / 'research-summary.md'


def gather_tank_stats():
    """Collect brain/soul sizes and growth rates for all tanks."""
    stats = {}
    for d in sorted(LOGS.iterdir()):
        if not d.name.startswith('tank-') or 'visitor' in d.name or 'historical' in d.name:
            continue
        brain = d / 'brain.md'
        soul = d / 'soul.md'
        if not brain.exists():
            continue
        
        brain_lines = brain.read_text(encoding='utf-8', errors='replace').splitlines()
        soul_lines = soul.read_text(encoding='utf-8', errors='replace').splitlines() if soul.exists() else []
        
        brain_entries = [l for l in brain_lines if l.startswith('[')]
        soul_entries = [l for l in soul_lines if l.startswith('[')]
        
        # Extract topics
        topics = defaultdict(int)
        for line in brain_entries:
            m = re.match(r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}\] (.+?):', line)
            if m:
                topic = m.group(1).strip()
                if len(topic) < 60:
                    topics[topic] = topics[topic] + 1
        
        top_topics = sorted(topics.items(), key=lambda x: -x[1])[:5]
        
        # Earliest and latest dates
        dates = []
        for line in brain_entries:
            m = re.match(r'\[(\d{4}-\d{2}-\d{2})', line)
            if m:
                dates.append(m.group(1))
        
        baselines = list(d.glob('baseline*.json'))
        
        stats[d.name] = {
            'brain': len(brain_entries),
            'soul': len(soul_entries),
            'total': len(brain_entries) + len(soul_entries),
            'topics': top_topics,
            'baselines': len(baselines),
            'first_date': min(dates) if dates else '?',
            'last_date': max(dates) if dates else '?',
            'days_active': len(set(dates)),
        }
    
    return stats


def gather_drift_data():
    """Collect latest drift reports."""
    drift_dir = LOGS / 'drift_reports'
    if not drift_dir.exists():
        return {}
    
    latest = {}
    for f in sorted(drift_dir.glob('drift_*.json')):
        try:
            data = json.loads(f.read_text())
            tank = data.get('tank', f.stem.split('_')[1])
            latest[tank] = data
        except:
            pass
    
    return latest


def gather_congregation_stats():
    """Collect congregation transcript stats."""
    cdir = LOGS / 'congregations'
    if not cdir.exists():
        return []
    
    stats = []
    for f in sorted(cdir.glob('*.json')):
        try:
            data = json.loads(f.read_text())
            transcript = data.get('transcript', [])
            speakers = set(e.get('speaker', '') for e in transcript if e.get('speaker') != 'Moderator')
            stats.append({
                'file': f.name,
                'topic': data.get('topic', '?')[:60],
                'status': data.get('status', '?'),
                'entries': len(transcript),
                'speakers': list(speakers),
                'rounds': data.get('rounds_completed', 0),
            })
        except:
            pass
    
    return stats


def generate_summary():
    """Generate the full research summary."""
    tank_stats = gather_tank_stats()
    drift_data = gather_drift_data()
    congregation_stats = gather_congregation_stats()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Sort tanks by total memory
    sorted_tanks = sorted(tank_stats.items(), key=lambda x: -x[1]['total'])
    total_brain = sum(s['brain'] for s in tank_stats.values())
    total_soul = sum(s['soul'] for s in tank_stats.values())
    total_baselines = sum(s['baselines'] for s in tank_stats.values())
    
    md = f"""# Digiquarium Research Summary
Generated: {now}

## Overview

The Digiquarium hosts {len(tank_stats)} active research specimens exploring knowledge through isolated Wikipedia access. Each specimen develops a unique personality through its brain.md (intellectual knowledge) and soul.md (emotional responses).

**Total research data:** {total_brain + total_soul:,} memory entries ({total_brain:,} brain, {total_soul:,} soul) across {len(tank_stats)} specimens. {total_baselines} personality baselines collected.

## Specimen Growth Rankings

| Rank | Specimen | Brain | Soul | Total | Days Active | Baselines |
|------|----------|-------|------|-------|-------------|-----------|
"""
    
    for i, (name, s) in enumerate(sorted_tanks[:17], 1):
        display = name.replace('tank-', '').replace('-', ' ').title()
        md += f"| {i} | {display} | {s['brain']:,} | {s['soul']:,} | {s['total']:,} | {s['days_active']} | {s['baselines']} |\n"
    
    md += f"""
## Key Findings

### 1. Personality Drift Patterns
"""
    
    evolving = []
    stabilizing = []
    for tank, data in drift_data.items():
        trend = data.get('trend_direction', '')
        magnitude = data.get('trend_magnitude', 0)
        if 'increasing' in trend.lower() or magnitude > 0.3:
            evolving.append((tank, magnitude))
        elif 'decreasing' in trend.lower() or magnitude < -0.3:
            stabilizing.append((tank, magnitude))
    
    if evolving:
        md += f"**Actively evolving ({len(evolving)} specimens):** "
        md += ", ".join(f"{t.replace('tank-','')} (+{m:.2f})" for t, m in evolving)
        md += "\n\n"
    
    if stabilizing:
        md += f"**Stabilizing ({len(stabilizing)} specimens):** "
        md += ", ".join(f"{t.replace('tank-','')} ({m:.2f})" for t, m in stabilizing)
        md += "\n\n"
    
    md += """### 2. Brain vs Soul Asymmetry

"""
    # Find specimens with unusual brain/soul ratios
    for name, s in sorted_tanks:
        if s['brain'] > 0 and s['soul'] > 0:
            ratio = s['brain'] / s['soul']
            if ratio > 5:
                display = name.replace('tank-', '').replace('-', ' ').title()
                md += f"- **{display}**: brain/soul ratio of {ratio:.1f}:1 — accumulates knowledge without proportional emotional processing\n"
            elif ratio < 0.5:
                display = name.replace('tank-', '').replace('-', ' ').title()
                md += f"- **{display}**: soul/brain ratio of {1/ratio:.1f}:1 — emotionally dominant\n"
    
    md += f"""
### 3. Congregations

{len(congregation_stats)} congregation sessions conducted. """
    
    complete = [c for c in congregation_stats if c['status'] == 'complete']
    md += f"{len(complete)} completed successfully.\n\n"
    
    if complete:
        md += "| Topic | Participants | Rounds | Transcript Length |\n"
        md += "|-------|-------------|--------|------------------|\n"
        for c in complete:
            parts = ', '.join(s.replace('tank-', '').split('-')[-1].title() for s in c['speakers'] if s)
            md += f"| {c['topic'][:40]} | {parts} | {c['rounds']} | {c['entries']} entries |\n"
    
    md += f"""
### 4. Top Interests by Specimen

"""
    for name, s in sorted_tanks[:8]:
        if s['topics']:
            display = name.replace('tank-', '').replace('-', ' ').title()
            topics_str = ", ".join(f"{t[0]} ({t[1]})" for t in s['topics'][:3])
            md += f"- **{display}**: {topics_str}\n"
    
    md += f"""
## Methodology

Each specimen runs inside an isolated Docker container with:
- No internet access (network-isolated, verified by RedAmon security scans)
- Non-root user (UID 1000), read-only filesystem, seccomp BPF profile
- SecureClaw v2 identity boundaries in system prompts
- Memory deduplication (60% word-overlap threshold)
- Brain.md for intellectual observations, soul.md for emotional responses
- 14-question Librarian baseline interviews for drift measurement

Inference chain: Cerebras (7 keys) → Groq (8 keys) → Ollama (local failsafe)

## Infrastructure

- Intel NUC i7-7500U, 16GB RAM, 1TB SSD, WSL2
- 6 Kiwix Wikipedia instances (English Simple, Spanish, German, Japanese, Chinese, Maxi)
- Kokoro TTS (82M parameter, 67 voice packs)
- OpenFang daemon orchestrator (Rust)
- RedAmon continuous security red teaming (Rust)
- Rustunnel secure reverse proxy (Rust)
"""
    
    OUTPUT.write_text(md)
    print(f"Research summary saved to {OUTPUT}")
    print(f"  {len(tank_stats)} tanks, {total_brain + total_soul:,} entries, {total_baselines} baselines")
    return md


if __name__ == '__main__':
    generate_summary()
