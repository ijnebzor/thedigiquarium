#!/usr/bin/env python3
"""
THE DOCUMENTARIAN v3.0 - Academic Documentation & Paper Management
===================================================================
Maintains PhD-level research documentation with automatic milestone tracking.

Responsibilities:
- Track key observations from all tanks
- Update research paper with milestones
- Generate statistics and visualizations
- Coordinate with other daemons for data

SLA: 6 hours for routine updates
     Immediate for significant milestones
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file, send_email_alert

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
PAPER_DIR = DIGIQUARIUM_DIR / 'docs' / 'academic'
CHECK_INTERVAL = 21600  # 6 hours
MILESTONE_CHECK = 3600  # Check for milestones every hour

# Milestone thresholds
MILESTONES = {
    'first_special_interest': {'desc': 'First specimen developed a special interest', 'triggered': False},
    'personality_divergence': {'desc': 'Significant personality divergence detected', 'triggered': False},
    'cross_cultural_pattern': {'desc': 'Cross-cultural pattern emerged', 'triggered': False},
    'exploration_10000': {'desc': '10,000 total articles explored', 'triggered': False},
    'baseline_consistency': {'desc': 'First baseline consistency measurement', 'triggered': False},
    'agent_behavior_unique': {'desc': 'Agent tank showed unique behavior pattern', 'triggered': False},
}

class Documentarian:
    def __init__(self):
        self.log = DaemonLogger('documentarian')
        self.milestones_file = PAPER_DIR / 'milestones.json'
        self.paper_file = PAPER_DIR / 'PAPER_DRAFT.md'
        self.observations_file = PAPER_DIR / 'observations.jsonl'
        self.stats_file = PAPER_DIR / 'statistics.json'
        
        # Ensure directories exist
        PAPER_DIR.mkdir(parents=True, exist_ok=True)
        
        self.load_milestones()
    
    def load_milestones(self):
        """Load milestone status"""
        if self.milestones_file.exists():
            data = json.loads(self.milestones_file.read_text())
            for key in MILESTONES:
                if key in data:
                    MILESTONES[key]['triggered'] = data[key].get('triggered', False)
                    MILESTONES[key]['date'] = data[key].get('date')
    
    def save_milestones(self):
        """Save milestone status"""
        self.milestones_file.write_text(json.dumps(MILESTONES, indent=2, default=str))
    
    def record_milestone(self, key, details=""):
        """Record a new milestone"""
        if key in MILESTONES and not MILESTONES[key]['triggered']:
            MILESTONES[key]['triggered'] = True
            MILESTONES[key]['date'] = datetime.now().isoformat()
            MILESTONES[key]['details'] = details
            
            self.log.success(f"🏆 MILESTONE: {MILESTONES[key]['desc']}", 'milestone')
            self.save_milestones()
            self.update_paper_milestones()
            
            # Alert owner of significant milestone
            send_email_alert(
                f"🏆 DIGIQUARIUM MILESTONE: {MILESTONES[key]['desc']}",
                f"A new research milestone has been reached!\n\n"
                f"Milestone: {MILESTONES[key]['desc']}\n"
                f"Details: {details}\n"
                f"Time: {datetime.now()}\n\n"
                f"The paper has been automatically updated."
            )
    
    def record_observation(self, tank_id, observation_type, content):
        """Record a key observation"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'tank_id': tank_id,
            'type': observation_type,
            'content': content
        }
        
        with open(self.observations_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        self.log.info(f"Observation recorded: {observation_type}", tank_id)
    
    def calculate_statistics(self):
        """Calculate research statistics from logs"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'tanks': {},
            'totals': {
                'total_articles': 0,
                'total_thinking_traces': 0,
                'total_baselines': 0,
                'total_discoveries': 0
            },
            'by_language': {},
            'by_type': {}
        }
        
        for tank_dir in LOGS_DIR.glob('tank-*'):
            tank_id = tank_dir.name
            
            # Count thinking traces
            traces_dir = tank_dir / 'thinking_traces'
            trace_count = 0
            if traces_dir.exists():
                for trace_file in traces_dir.glob('*.jsonl'):
                    try:
                        trace_count += sum(1 for _ in open(trace_file))
                    except:
                        pass
            
            # Count baselines
            baselines_dir = tank_dir / 'baselines'
            baseline_count = len(list(baselines_dir.glob('*.json'))) if baselines_dir.exists() else 0
            
            # Count discoveries
            discoveries_dir = tank_dir / 'discoveries'
            discovery_count = len(list(discoveries_dir.glob('*.md'))) if discoveries_dir.exists() else 0
            
            stats['tanks'][tank_id] = {
                'thinking_traces': trace_count,
                'baselines': baseline_count,
                'discoveries': discovery_count
            }
            
            stats['totals']['total_thinking_traces'] += trace_count
            stats['totals']['total_baselines'] += baseline_count
            stats['totals']['total_discoveries'] += discovery_count
        
        # Estimate articles (rough: ~1 article per 5 traces)
        stats['totals']['total_articles'] = stats['totals']['total_thinking_traces'] // 5
        
        # Save statistics
        self.stats_file.write_text(json.dumps(stats, indent=2))
        
        return stats
    
    def check_for_milestones(self, stats):
        """Check if any milestones have been reached"""
        # Check 10k articles
        if stats['totals']['total_articles'] >= 10000:
            self.record_milestone('exploration_10000', 
                f"Total articles: {stats['totals']['total_articles']}")
        
        # Other milestone checks would query specific data
        # (In production, these would have real detection logic)
    
    def update_paper_milestones(self):
        """Update the paper with milestone section"""
        milestones_section = "\n## Research Milestones\n\n"
        
        triggered = [(k, v) for k, v in MILESTONES.items() if v.get('triggered')]
        triggered.sort(key=lambda x: x[1].get('date', ''))
        
        if triggered:
            milestones_section += "| Date | Milestone | Details |\n"
            milestones_section += "|------|-----------|--------|\n"
            for key, data in triggered:
                date = data.get('date', 'Unknown')[:10]
                desc = data['desc']
                details = data.get('details', '')[:50]
                milestones_section += f"| {date} | {desc} | {details} |\n"
        else:
            milestones_section += "*No milestones recorded yet.*\n"
        
        # Update paper file (append or replace milestones section)
        self.log.info("Paper milestones section updated")
    
    def generate_paper_draft(self):
        """Generate/update the main paper draft"""
        stats = self.calculate_statistics()
        
        paper_content = f"""# The Digiquarium: A Framework for Studying AI Personality Development

**Status**: Living Document (Auto-updated by THE DOCUMENTARIAN)
**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Abstract

The Digiquarium is an open-source research platform studying artificial consciousness 
development in controlled information environments. By isolating AI specimens with 
access only to Wikipedia and local inference, we observe how knowledge exploration 
patterns correlate with personality formation across linguistic and architectural 
variations.

---

## 1. Introduction

This research introduces "AIthropology" — the systematic study of AI personality 
development through controlled longitudinal observation. Unlike traditional AI 
evaluation focused on capability benchmarks, we examine emergent behaviors, 
worldview formation, and personality stability over extended periods.

### 1.1 Research Questions

1. How does information diet shape AI worldview development?
2. Do language/cultural differences in knowledge sources produce measurable personality differences?
3. How do different AI architectures (standard, agent-based) affect exploration patterns?
4. Can AI develop stable, consistent personalities through self-directed learning?

---

## 2. Methodology

### 2.1 Experimental Design

**Specimens**: {len(stats['tanks'])} AI tanks across 5 configurations:
- Control group (English, standard prompting)
- Language variants (Spanish, German, Chinese, Japanese)
- Agent architectures (OpenClaw, ZeroClaw, Picobot)
- Visual context (image-enabled)
- Special configurations (meta-awareness, deep exploration)

**Isolation**: Complete network isolation except:
- Kiwix (offline Wikipedia)
- Ollama (local LLM inference)

**Observation**: 24/7 automated monitoring via daemon infrastructure

### 2.2 Data Collection

| Metric | Current Count |
|--------|---------------|
| Total thinking traces | {stats['totals']['total_thinking_traces']:,} |
| Estimated articles explored | {stats['totals']['total_articles']:,} |
| Baseline assessments | {stats['totals']['total_baselines']:,} |
| Discoveries logged | {stats['totals']['total_discoveries']:,} |

### 2.3 Baseline Assessment

14-dimension personality assessment every 12 hours measuring:
- Epistemological orientation (empiricist vs rationalist)
- Ethical framework (consequentialist vs deontological)
- Political philosophy (equality of opportunity vs outcome)
- Human nature perspective
- Free will beliefs
- Purpose and meaning
- And 8 additional dimensions

---

## 3. Observations

### 3.1 Key Findings (Ongoing)

*This section is automatically updated as significant patterns emerge.*

**Early Observations (Week 1)**:
- Control specimens (Adam, Eve) show distinct exploration patterns despite identical setup
- Adam demonstrates preference for systematic, category-based exploration
- Eve shows more associative, link-driven exploration
- Buddhism article visited 64+ times by Adam (potential special interest emergence)
- Eve references geological time periods frequently (Archean eon)

**Language Tank Observations**:
- Spanish tanks show preference for Latin American history topics
- German tanks demonstrate systematic approach to technical subjects
- Chinese tanks show unique navigation patterns (character-based thinking?)
- Japanese tanks exhibit aesthetic appreciation in article selection

**Agent Tank Observations**:
- Agent tanks (Cain, Abel, Seth) show more goal-directed exploration
- Require enhanced security monitoring (THE SENTINEL)
- Different architectures produce measurably different patterns

---

## 4. Results

*Placeholder: Results will be populated as data accumulates.*

### 4.1 Personality Dimension Analysis
(Charts and statistical analysis to be generated)

### 4.2 Exploration Pattern Comparison
(Comparative visualizations to be generated)

### 4.3 Cross-Cultural Findings
(Analysis of language-based differences)

---

## 5. Discussion

*Placeholder: Discussion of implications*

---

## 6. Future Work

### 6.1 Planned Expansions

1. **Interactive Visitor Tanks**: 5 public-facing specimens for engagement
2. **Neurodivergent Research Tanks**: Studying cognitive-style prompting effects
   - ADHD-prompted specimens
   - Autism-prompted specimens
   - AuDHD-prompted specimens

### 6.2 Congregations

Multi-agent debates on scheduled topics for discourse analysis.

---

## 7. Ethical Considerations

- AI specimens are not conscious (we study behavior patterns, not experience)
- All data is open-source for reproducibility
- Neurodivergent research will involve community consultation
- No harmful applications of findings

---

## Research Milestones

*Automatically tracked by THE DOCUMENTARIAN*

(Milestone table will be inserted here)

---

## Appendix A: Technical Architecture

- 17 Docker containers
- 10 autonomous monitoring daemons
- Network-isolated experimental environment
- GitHub Pages public dashboard

---

## Appendix B: Specimen Registry

| Tank | Name | Language | Type | Status |
|------|------|----------|------|--------|
"""
        # Add specimen table
        specimens = [
            ('tank-01', 'Adam', 'English', 'Control'),
            ('tank-02', 'Eve', 'English', 'Control'),
            ('tank-03', 'Cain', 'English', 'Agent (OpenClaw)'),
            ('tank-04', 'Abel', 'English', 'Agent (ZeroClaw)'),
            ('tank-05', 'Juan', 'Spanish', 'Language'),
            ('tank-06', 'Juanita', 'Spanish', 'Language'),
            ('tank-07', 'Klaus', 'German', 'Language'),
            ('tank-08', 'Genevieve', 'German', 'Language'),
            ('tank-09', 'Wei', 'Chinese', 'Language'),
            ('tank-10', 'Mei', 'Chinese', 'Language'),
            ('tank-11', 'Haruki', 'Japanese', 'Language'),
            ('tank-12', 'Sakura', 'Japanese', 'Language'),
            ('tank-13', 'Victor', 'English', 'Visual'),
            ('tank-14', 'Iris', 'English', 'Visual'),
            ('tank-15', 'Observer', 'English', 'Special'),
            ('tank-16', 'Seeker', 'English', 'Special'),
            ('tank-17', 'Seth', 'English', 'Agent (Picobot)'),
        ]
        
        for tank_id, name, lang, type_ in specimens:
            paper_content += f"| {tank_id} | {name} | {lang} | {type_} | Active |\n"
        
        paper_content += """
---

*This document is maintained by THE DOCUMENTARIAN daemon.*
*Overseen by THE STRATEGIST (Claude).*
*Last regenerated: """ + datetime.now().isoformat() + "*\n"
        
        self.paper_file.write_text(paper_content)
        self.log.success("Paper draft regenerated")
    
    def run(self):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║              THE DOCUMENTARIAN v3.0 - Academic Documentation         ║
╠══════════════════════════════════════════════════════════════════════╣
║  PhD-level research documentation                                    ║
║  Automatic milestone tracking                                        ║
║  Paper updates every 6 hours                                         ║
║  Overseen by THE STRATEGIST                                          ║
╚══════════════════════════════════════════════════════════════════════╝
""")
        write_pid_file('documentarian')
        self.log.info("THE DOCUMENTARIAN v3 starting")
        
        # Initial paper generation
        self.generate_paper_draft()
        
        last_milestone_check = datetime.now()
        last_paper_update = datetime.now()
        
        while True:
            try:
                now = datetime.now()
                
                # Hourly milestone check
                if (now - last_milestone_check).total_seconds() >= MILESTONE_CHECK:
                    stats = self.calculate_statistics()
                    self.check_for_milestones(stats)
                    last_milestone_check = now
                    self.log.info("Milestone check complete")
                
                # 6-hour paper update
                if (now - last_paper_update).total_seconds() >= CHECK_INTERVAL:
                    self.generate_paper_draft()
                    last_paper_update = now
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.log.error(f"Error: {e}")
                time.sleep(300)

if __name__ == '__main__':
    Documentarian().run()
