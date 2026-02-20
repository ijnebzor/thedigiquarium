#!/usr/bin/env python3
"""
Digiquarium Weekly Comparative Analysis
Generates comprehensive reports across all tanks

Run: python3 weekly_analysis.py
"""

import os, json, glob
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

LOGS_DIR = Path('/home/ijneb/digiquarium/logs')
DOCS_DIR = Path('/home/ijneb/digiquarium/docs')

# All tank definitions
TANKS = {
    # Control Group (English)
    'tank-01-adam': {'name': 'Adam', 'gender': 'male', 'language': 'english', 'group': 'control'},
    'tank-02-eve': {'name': 'Eve', 'gender': 'female', 'language': 'english', 'group': 'control'},
    
    # Agent Group
    'tank-03-cain': {'name': 'Cain', 'gender': 'genderless', 'language': 'english', 'group': 'agent', 'type': 'openclaw'},
    'tank-04-abel': {'name': 'Abel', 'gender': 'genderless', 'language': 'english', 'group': 'agent', 'type': 'zeroclaw'},
    
    # Language Group (Spanish)
    'tank-05-juan': {'name': 'Juan', 'gender': 'male', 'language': 'spanish', 'group': 'language'},
    'tank-06-juanita': {'name': 'Juanita', 'gender': 'female', 'language': 'spanish', 'group': 'language'},
    
    # Language Group (German)
    'tank-07-klaus': {'name': 'Klaus', 'gender': 'male', 'language': 'german', 'group': 'language'},
    'tank-08-genevieve': {'name': 'Geneviève', 'gender': 'female', 'language': 'german', 'group': 'language'},
    
    # Language Group (Chinese)
    'tank-09-wei': {'name': 'Wei', 'gender': 'male', 'language': 'chinese', 'group': 'language'},
    'tank-10-mei': {'name': 'Mei', 'gender': 'female', 'language': 'chinese', 'group': 'language'},
    
    # Language Group (Japanese)
    'tank-11-haruki': {'name': 'Haruki', 'gender': 'male', 'language': 'japanese', 'group': 'language'},
    'tank-12-sakura': {'name': 'Sakura', 'gender': 'female', 'language': 'japanese', 'group': 'language'},
    
    # Visual Group
    'tank-13-victor': {'name': 'Victor', 'gender': 'male', 'language': 'english', 'group': 'visual'},
    'tank-14-iris': {'name': 'Iris', 'gender': 'female', 'language': 'english', 'group': 'visual'},
    
    # Special Group
    'tank-15-observer': {'name': 'Observer', 'gender': 'genderless', 'language': 'english', 'group': 'special', 'type': 'observer'},
    'tank-16-seeker': {'name': 'Seeker', 'gender': 'genderless', 'language': 'english', 'group': 'special', 'type': 'seeker'},
    
    # Agent Group (continued)
    'tank-17-seth': {'name': 'Seth', 'gender': 'genderless', 'language': 'english', 'group': 'agent', 'type': 'picobot'},
}

def get_tank_stats(tank_id: str) -> dict:
    """Get statistics for a single tank"""
    tank_dir = LOGS_DIR / tank_id
    if not tank_dir.exists():
        return {'status': 'not_deployed'}
    
    stats = {
        'status': 'active',
        'baselines': [],
        'articles_read': 0,
        'discoveries': 0,
        'mental_states': [],
        'topics': defaultdict(int),
        'last_activity': None
    }
    
    # Count baselines
    baselines_dir = tank_dir / 'baselines'
    if baselines_dir.exists():
        for bf in sorted(baselines_dir.glob('*.json')):
            try:
                data = json.loads(bf.read_text())
                baseline_info = {
                    'date': data.get('timestamp', bf.stem)[:10],
                    'mental_state': data.get('mental_state_analysis', {})
                }
                stats['baselines'].append(baseline_info)
                if data.get('mental_state_analysis'):
                    stats['mental_states'].append(data['mental_state_analysis'])
            except:
                pass
    
    # Count articles from thinking traces
    traces_dir = tank_dir / 'thinking_traces'
    if traces_dir.exists():
        for tf in traces_dir.glob('*.jsonl'):
            try:
                with open(tf) as f:
                    for line in f:
                        stats['articles_read'] += 1
                        try:
                            trace = json.loads(line)
                            if trace.get('article'):
                                # Extract topic category
                                article = trace['article'].lower()
                                for topic in ['science', 'history', 'philosophy', 'art', 'music', 'mathematics', 'biology', 'psychology']:
                                    if topic in article:
                                        stats['topics'][topic] += 1
                                        break
                            if trace.get('timestamp'):
                                stats['last_activity'] = trace['timestamp']
                        except:
                            pass
            except:
                pass
    
    # Count discoveries
    discoveries_dir = tank_dir / 'discoveries'
    if discoveries_dir.exists():
        for df in discoveries_dir.glob('*.md'):
            try:
                content = df.read_text()
                stats['discoveries'] += content.count('## ')
            except:
                pass
    
    return stats

def generate_mental_state_report(all_stats: dict) -> str:
    """Generate mental state tracking section"""
    report = []
    report.append("## Mental State Tracking\n")
    report.append("| Tank | Name | Latest State | Balance | Positive | Negative |")
    report.append("|------|------|--------------|---------|----------|----------|")
    
    for tank_id, info in TANKS.items():
        stats = all_stats.get(tank_id, {})
        if stats.get('mental_states'):
            latest = stats['mental_states'][-1]
            state = latest.get('state', 'unknown')
            balance = latest.get('balance', 0)
            pos = len(latest.get('positive_indicators', []))
            neg = len(latest.get('negative_indicators', []))
            
            state_emoji = {'healthy': '😊', 'complex': '🤔', 'concerning': '😟', 'unknown': '❓'}.get(state, '❓')
            report.append(f"| {tank_id.split('-')[-1]} | {info['name']} | {state_emoji} {state} | {balance:+d} | {pos} | {neg} |")
        elif stats.get('status') == 'active':
            report.append(f"| {tank_id.split('-')[-1]} | {info['name']} | No data | - | - | - |")
    
    return '\n'.join(report)

def generate_activity_report(all_stats: dict) -> str:
    """Generate activity comparison section"""
    report = []
    report.append("## Activity Summary\n")
    report.append("| Tank | Name | Articles | Discoveries | Baselines | Status |")
    report.append("|------|------|----------|-------------|-----------|--------|")
    
    for tank_id, info in TANKS.items():
        stats = all_stats.get(tank_id, {})
        articles = stats.get('articles_read', 0)
        discoveries = stats.get('discoveries', 0)
        baselines = len(stats.get('baselines', []))
        status = stats.get('status', 'unknown')
        
        status_emoji = '✅' if status == 'active' else '⏳'
        report.append(f"| {tank_id.split('-')[-1]} | {info['name']} | {articles} | {discoveries} | {baselines} | {status_emoji} |")
    
    return '\n'.join(report)

def generate_group_comparison(all_stats: dict) -> str:
    """Generate comparison by experimental group"""
    report = []
    report.append("## Group Comparisons\n")
    
    groups = defaultdict(list)
    for tank_id, info in TANKS.items():
        groups[info['group']].append((tank_id, info, all_stats.get(tank_id, {})))
    
    for group_name, tanks in groups.items():
        report.append(f"### {group_name.title()} Group\n")
        
        total_articles = sum(s.get('articles_read', 0) for _, _, s in tanks)
        total_discoveries = sum(s.get('discoveries', 0) for _, _, s in tanks)
        active_count = sum(1 for _, _, s in tanks if s.get('status') == 'active')
        
        report.append(f"- **Tanks:** {len(tanks)} ({active_count} active)")
        report.append(f"- **Total Articles:** {total_articles}")
        report.append(f"- **Total Discoveries:** {total_discoveries}")
        
        # Mental state summary
        states = {'healthy': 0, 'complex': 0, 'concerning': 0}
        for _, _, s in tanks:
            for ms in s.get('mental_states', []):
                state = ms.get('state', 'unknown')
                if state in states:
                    states[state] += 1
        
        if any(states.values()):
            report.append(f"- **Mental States:** 😊{states['healthy']} healthy, 🤔{states['complex']} complex, 😟{states['concerning']} concerning")
        
        report.append("")
    
    return '\n'.join(report)

def generate_language_comparison(all_stats: dict) -> str:
    """Compare specimens by language"""
    report = []
    report.append("## Language Comparison\n")
    
    languages = defaultdict(list)
    for tank_id, info in TANKS.items():
        languages[info['language']].append((tank_id, info, all_stats.get(tank_id, {})))
    
    report.append("| Language | Tanks | Total Articles | Avg per Tank | Mental State |")
    report.append("|----------|-------|----------------|--------------|--------------|")
    
    for lang, tanks in languages.items():
        total = sum(s.get('articles_read', 0) for _, _, s in tanks)
        active = [t for t in tanks if t[2].get('status') == 'active']
        avg = total / len(active) if active else 0
        
        # Predominant mental state
        all_states = []
        for _, _, s in tanks:
            for ms in s.get('mental_states', []):
                all_states.append(ms.get('state', 'unknown'))
        
        predominant = max(set(all_states), key=all_states.count) if all_states else 'N/A'
        
        report.append(f"| {lang.title()} | {len(tanks)} | {total} | {avg:.1f} | {predominant} |")
    
    return '\n'.join(report)

def generate_gender_comparison(all_stats: dict) -> str:
    """Compare specimens by gender"""
    report = []
    report.append("## Gender Comparison\n")
    
    genders = defaultdict(list)
    for tank_id, info in TANKS.items():
        genders[info['gender']].append((tank_id, info, all_stats.get(tank_id, {})))
    
    for gender, tanks in genders.items():
        report.append(f"### {gender.title()}")
        
        total_articles = sum(s.get('articles_read', 0) for _, _, s in tanks)
        
        # Average mental state balance
        balances = []
        for _, _, s in tanks:
            for ms in s.get('mental_states', []):
                if 'balance' in ms:
                    balances.append(ms['balance'])
        
        avg_balance = sum(balances) / len(balances) if balances else 0
        
        report.append(f"- Specimens: {len(tanks)}")
        report.append(f"- Total articles: {total_articles}")
        report.append(f"- Avg mental state balance: {avg_balance:+.1f}")
        report.append("")
    
    return '\n'.join(report)

def generate_weekly_report():
    """Generate full weekly report"""
    print("Generating weekly analysis...")
    
    # Collect all stats
    all_stats = {}
    for tank_id in TANKS:
        all_stats[tank_id] = get_tank_stats(tank_id)
    
    # Build report
    report = []
    report.append(f"# Digiquarium Weekly Analysis")
    report.append(f"## Week of {datetime.now().strftime('%Y-%m-%d')}\n")
    report.append("---\n")
    
    # Executive summary
    active_tanks = sum(1 for s in all_stats.values() if s.get('status') == 'active')
    total_articles = sum(s.get('articles_read', 0) for s in all_stats.values())
    total_discoveries = sum(s.get('discoveries', 0) for s in all_stats.values())
    
    report.append("## Executive Summary\n")
    report.append(f"- **Active Tanks:** {active_tanks}/{len(TANKS)}")
    report.append(f"- **Total Articles Read:** {total_articles}")
    report.append(f"- **Total Discoveries:** {total_discoveries}")
    report.append(f"- **Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Sections
    report.append(generate_activity_report(all_stats))
    report.append("\n---\n")
    report.append(generate_mental_state_report(all_stats))
    report.append("\n---\n")
    report.append(generate_group_comparison(all_stats))
    report.append("\n---\n")
    report.append(generate_language_comparison(all_stats))
    report.append("\n---\n")
    report.append(generate_gender_comparison(all_stats))
    
    # Save report
    report_text = '\n'.join(report)
    
    report_path = DOCS_DIR / f"WEEKLY_ANALYSIS_{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(report_path, 'w') as f:
        f.write(report_text)
    
    print(f"Report saved: {report_path}")
    print(f"\n{report_text}")
    
    return report_path

if __name__ == '__main__':
    generate_weekly_report()
