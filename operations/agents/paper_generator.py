#!/usr/bin/env python3
"""
PAPER GENERATOR - Auto-updates the AIthropology research paper
================================================================
Generates HTML paper with live data from all tanks.
Called by Documentarian every 6 hours.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
DOCS_DIR = DIGIQUARIUM_DIR / 'docs'

TANKS = [
    ('tank-01-adam', 'Adam', 'English', 'Male', 'Control'),
    ('tank-02-eve', 'Eve', 'English', 'Female', 'Control'),
    ('tank-03-cain', 'Cain', 'English', 'Genderless', 'Agent'),
    ('tank-04-abel', 'Abel', 'English', 'Genderless', 'Agent'),
    ('tank-05-juan', 'Juan', 'Spanish', 'Male', 'Language'),
    ('tank-06-juanita', 'Juanita', 'Spanish', 'Female', 'Language'),
    ('tank-07-klaus', 'Klaus', 'German', 'Male', 'Language'),
    ('tank-08-genevieve', 'Geneviève', 'German', 'Female', 'Language'),
    ('tank-09-wei', 'Wei', 'Chinese', 'Male', 'Language'),
    ('tank-10-mei', 'Mei', 'Chinese', 'Female', 'Language'),
    ('tank-11-haruki', 'Haruki', 'Japanese', 'Male', 'Language'),
    ('tank-12-sakura', 'Sakura', 'Japanese', 'Female', 'Language'),
    ('tank-13-victor', 'Victor', 'English', 'Male', 'Visual'),
    ('tank-14-iris', 'Iris', 'English', 'Female', 'Visual'),
    ('tank-15-observer', 'Observer', 'English', 'Genderless', 'Special'),
    ('tank-16-seeker', 'Seeker', 'English', 'Genderless', 'Special'),
    ('tank-17-seth', 'Seth', 'English', 'Genderless', 'Agent'),
]


def get_tank_stats():
    """Collect current statistics from all tanks"""
    stats = {
        'total_observations': 0,
        'total_baselines': 0,
        'total_discoveries': 0,
        'tanks': {},
        'mental_states': defaultdict(int),
        'by_language': defaultdict(lambda: {'observations': 0, 'tanks': 0}),
    }
    
    for tank_id, name, lang, gender, tank_type in TANKS:
        tank_dir = LOGS_DIR / tank_id
        tank_stats = {'name': name, 'observations': 0, 'baselines': 0, 'mental_state': 'unknown'}
        
        # Count observations
        traces_dir = tank_dir / 'thinking_traces'
        if traces_dir.exists():
            for f in traces_dir.glob('*.jsonl'):
                try:
                    tank_stats['observations'] += sum(1 for _ in open(f))
                except:
                    pass
        
        # Count baselines and get mental state
        baselines_dir = tank_dir / 'baselines'
        if baselines_dir.exists():
            baselines = sorted(baselines_dir.glob('*.json'), reverse=True)
            tank_stats['baselines'] = len(baselines)
            if baselines:
                try:
                    data = json.loads(baselines[0].read_text())
                    ms = data.get('mental_state_analysis', {}).get('state', 'unknown')
                    tank_stats['mental_state'] = ms
                    stats['mental_states'][ms] += 1
                except:
                    pass
        
        stats['tanks'][tank_id] = tank_stats
        stats['total_observations'] += tank_stats['observations']
        stats['total_baselines'] += tank_stats['baselines']
        stats['by_language'][lang]['observations'] += tank_stats['observations']
        stats['by_language'][lang]['tanks'] += 1
    
    return stats


def get_adam_eve_comparison():
    """Get detailed comparison data for Adam and Eve"""
    adam_dir = LOGS_DIR / 'tank-01-adam'
    eve_dir = LOGS_DIR / 'tank-02-eve'
    
    comparison = {
        'adam': {'observations': 0, 'baselines': 0, 'mental_state': 'unknown', 'excerpts': []},
        'eve': {'observations': 0, 'baselines': 0, 'mental_state': 'unknown', 'excerpts': []}
    }
    
    for specimen, tank_dir in [('adam', adam_dir), ('eve', eve_dir)]:
        # Count observations
        traces_dir = tank_dir / 'thinking_traces'
        if traces_dir.exists():
            for f in sorted(traces_dir.glob('*.jsonl'), reverse=True):
                try:
                    lines = open(f).readlines()
                    comparison[specimen]['observations'] += len(lines)
                    # Get last few excerpts
                    for line in lines[-3:]:
                        try:
                            entry = json.loads(line)
                            if entry.get('thoughts'):
                                comparison[specimen]['excerpts'].append({
                                    'text': entry['thoughts'][:200],
                                    'article': entry.get('article', 'Unknown')
                                })
                        except:
                            pass
                except:
                    pass
        
        # Get baselines
        baselines_dir = tank_dir / 'baselines'
        if baselines_dir.exists():
            baselines = sorted(baselines_dir.glob('*.json'), reverse=True)
            comparison[specimen]['baselines'] = len(baselines)
            if baselines:
                try:
                    data = json.loads(baselines[0].read_text())
                    comparison[specimen]['mental_state'] = data.get('mental_state_analysis', {}).get('state', 'unknown')
                except:
                    pass
    
    return comparison


def update_paper_stats():
    """Update the stats in the paper HTML file"""
    stats = get_tank_stats()
    genesis = get_adam_eve_comparison()
    
    # Save stats as JSON for JavaScript to consume
    stats_file = DOCS_DIR / 'data' / 'live_stats.json'
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    
    output = {
        'updated': datetime.now().isoformat(),
        'total_observations': stats['total_observations'],
        'total_baselines': stats['total_baselines'],
        'mental_states': dict(stats['mental_states']),
        'by_language': {k: dict(v) for k, v in stats['by_language'].items()},
        'genesis': genesis,
        'tanks': stats['tanks']
    }
    
    with open(stats_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"[PAPER_GEN] Updated stats: {stats['total_observations']} observations, {stats['total_baselines']} baselines")
    return output


if __name__ == '__main__':
    update_paper_stats()
