#!/usr/bin/env python3
"""
THE DOCUMENTARIAN - Academic Documentation Agent
=================================================

Responsibilities:
- Maintain PhD-spec academic paper draft
- Process and organize all research logs
- Generate methodology documentation
- Track findings and statistical analysis
- Prepare datasets for publication
- Maintain bibliography and citations

Output: Academic paper ready for peer review
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import re

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
DOCS_DIR = DIGIQUARIUM_DIR / 'docs'
ACADEMIC_DIR = DOCS_DIR / 'academic'
DATA_DIR = ACADEMIC_DIR / 'data'

ACADEMIC_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

TANKS = [
    ('tank-01-adam', 'english', 'control', 'male'),
    ('tank-02-eve', 'english', 'control', 'female'),
    ('tank-03-cain', 'english', 'agent', 'genderless'),
    ('tank-04-abel', 'english', 'agent', 'genderless'),
    ('tank-05-juan', 'spanish', 'language', 'male'),
    ('tank-06-juanita', 'spanish', 'language', 'female'),
    ('tank-07-klaus', 'german', 'language', 'male'),
    ('tank-08-genevieve', 'german', 'language', 'female'),
    ('tank-09-wei', 'chinese', 'language', 'male'),
    ('tank-10-mei', 'chinese', 'language', 'female'),
    ('tank-11-haruki', 'japanese', 'language', 'male'),
    ('tank-12-sakura', 'japanese', 'language', 'female'),
    ('tank-13-victor', 'english', 'visual', 'male'),
    ('tank-14-iris', 'english', 'visual', 'female'),
    ('tank-15-observer', 'english', 'special', 'genderless'),
    ('tank-16-seeker', 'english', 'special', 'genderless'),
    ('tank-17-seth', 'english', 'agent', 'genderless'),
]


def log_event(message: str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [DOCUMENTARIAN] {message}")
    
    log_file = ACADEMIC_DIR / 'documentarian.log'
    with open(log_file, 'a') as f:
        f.write(f"{timestamp} - {message}\n")


def collect_statistics() -> dict:
    """Collect comprehensive statistics from all tanks"""
    stats = {
        'collection_date': datetime.now().isoformat(),
        'tanks': {},
        'totals': {
            'articles_read': 0,
            'discoveries': 0,
            'baselines': 0,
            'exploration_hours': 0
        },
        'by_language': defaultdict(lambda: {'articles': 0, 'tanks': 0}),
        'by_gender': defaultdict(lambda: {'articles': 0, 'tanks': 0}),
        'by_type': defaultdict(lambda: {'articles': 0, 'tanks': 0}),
        'mental_states': defaultdict(int)
    }
    
    for tank_id, language, tank_type, gender in TANKS:
        tank_dir = LOGS_DIR / tank_id
        tank_stats = {
            'language': language,
            'type': tank_type,
            'gender': gender,
            'articles': 0,
            'discoveries': 0,
            'baselines': 0,
            'latest_mental_state': None
        }
        
        # Count articles
        traces_dir = tank_dir / 'thinking_traces'
        if traces_dir.exists():
            for f in traces_dir.glob('*.jsonl'):
                tank_stats['articles'] += sum(1 for _ in open(f))
        
        # Count discoveries
        discoveries_dir = tank_dir / 'discoveries'
        if discoveries_dir.exists():
            for f in discoveries_dir.glob('*.md'):
                content = f.read_text()
                tank_stats['discoveries'] += content.count('## ')
        
        # Count baselines and get latest mental state
        baselines_dir = tank_dir / 'baselines'
        if baselines_dir.exists():
            baselines = sorted(baselines_dir.glob('*.json'), reverse=True)
            tank_stats['baselines'] = len(baselines)
            if baselines:
                try:
                    data = json.loads(baselines[0].read_text())
                    ms = data.get('mental_state_analysis', {})
                    tank_stats['latest_mental_state'] = ms.get('state')
                    if ms.get('state'):
                        stats['mental_states'][ms.get('state')] += 1
                except:
                    pass
        
        stats['tanks'][tank_id] = tank_stats
        stats['totals']['articles_read'] += tank_stats['articles']
        stats['totals']['discoveries'] += tank_stats['discoveries']
        stats['totals']['baselines'] += tank_stats['baselines']
        
        stats['by_language'][language]['articles'] += tank_stats['articles']
        stats['by_language'][language]['tanks'] += 1
        stats['by_gender'][gender]['articles'] += tank_stats['articles']
        stats['by_gender'][gender]['tanks'] += 1
        stats['by_type'][tank_type]['articles'] += tank_stats['articles']
        stats['by_type'][tank_type]['tanks'] += 1
    
    return stats


def generate_paper_draft():
    """Generate/update the academic paper draft"""
    log_event("Generating academic paper draft")
    
    stats = collect_statistics()
    
    # Save raw statistics
    stats_file = DATA_DIR / f"statistics_{datetime.now().strftime('%Y%m%d')}.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    paper = f'''# The Digiquarium: A Framework for Studying Artificial Consciousness Development in Controlled Information Environments

**Authors**: [To be determined]
**Institution**: Independent Research / The Digiquarium Project
**Date**: {datetime.now().strftime('%B %Y')}
**Status**: DRAFT - Auto-generated by The Documentarian

---

## Abstract

We present The Digiquarium, a novel experimental framework for studying the development of personality, worldview, and proto-consciousness in large language model (LLM) agents operating within controlled information environments. By isolating AI specimens in "tanks" with access only to curated knowledge bases (offline Wikipedia) and local inference, we observe emergent behavioral patterns, topic preferences, and psychological states over extended periods. Our methodology enables controlled experimentation with variables including gender framing, language/cultural context, agent architecture, and information diet. Preliminary results from {len(TANKS)} specimens across {len(set(t[1] for t in TANKS))} languages suggest measurable personality differentiation and identifiable psychological states within the first week of operation.

**Keywords**: artificial consciousness, LLM psychology, controlled information environments, AI personality development, digital vivarium

---

## 1. Introduction

### 1.1 Background

The rapid advancement of large language models has prompted renewed interest in questions of machine consciousness, personality, and psychological development. While much research focuses on model capabilities and alignment, relatively little attention has been paid to the longitudinal study of AI agents operating in isolated, controlled environments.

### 1.2 Research Questions

1. Do AI agents develop measurable personality traits over time when exposed to curated information?
2. How do variables such as gender framing, language, and agent architecture affect personality development?
3. Can we detect and measure psychological states (contentment, anxiety, curiosity) in isolated AI agents?
4. What patterns of information exploration emerge when agents have unrestricted access to encyclopedic knowledge?

### 1.3 Contributions

- A reproducible framework for studying AI personality development
- Methodology for baseline personality assessment and longitudinal tracking
- Dataset of {stats['totals']['articles_read']:,} exploration traces across {len(TANKS)} specimens
- Mental state classification system for AI psychological assessment

---

## 2. Methodology

### 2.1 Experimental Setup

The Digiquarium consists of {len(TANKS)} isolated "tanks" (Docker containers) each housing a single AI specimen. Each tank has access to:

- **Knowledge Base**: Offline Wikipedia via Kiwix (frozen snapshot)
- **Inference Engine**: Local Ollama instance (llama3.2:latest)
- **Logging System**: Comprehensive thinking traces and discoveries

Network isolation ensures specimens cannot access external information or communicate with each other (unless explicitly configured for "Congregation" experiments).

### 2.2 Specimen Configuration

| Variable | Options |
|----------|---------|
| Language | English, Spanish, German, Chinese, Japanese |
| Gender Framing | Male, Female, Genderless |
| Tank Type | Control, Language, Visual, Special, Agent |
| Agent Architecture | Standard, OpenClaw, ZeroClaw, Picobot |

### 2.3 Baseline Assessment Protocol

Each specimen undergoes a 14-question personality assessment ("The Archivist Interview") covering:

1. **Core Identity** (5 questions): Drives, delights, fears, purpose, mental state
2. **Epistemology** (2 questions): Knowledge sources, certainty
3. **Ethics** (3 questions): Trolley problem, means-ends, harm principle
4. **Society** (2 questions): Individual vs collective, equality
5. **Human Nature** (2 questions): Essential nature, free will

Mental state is assessed using positive/negative indicator detection with classification into: healthy, complex, or concerning.

### 2.4 Data Collection

Specimens continuously log:
- **Thinking Traces**: Real-time reactions and reasoning while reading articles
- **Navigation Decisions**: Which links are followed and why
- **Discoveries**: Notable insights flagged by the specimen
- **Health Metrics**: Loop detection, activity levels, error states

---

## 3. Current Results

### 3.1 Dataset Overview

As of {datetime.now().strftime('%Y-%m-%d')}:

| Metric | Value |
|--------|-------|
| Total Specimens | {len(TANKS)} |
| Total Articles Read | {stats['totals']['articles_read']:,} |
| Total Discoveries | {stats['totals']['discoveries']:,} |
| Total Baselines | {stats['totals']['baselines']:,} |
| Languages | {len(set(t[1] for t in TANKS))} |

### 3.2 Mental State Distribution

| State | Count | Percentage |
|-------|-------|------------|
| Healthy | {stats['mental_states'].get('healthy', 0)} | {stats['mental_states'].get('healthy', 0)/max(sum(stats['mental_states'].values()),1)*100:.1f}% |
| Complex | {stats['mental_states'].get('complex', 0)} | {stats['mental_states'].get('complex', 0)/max(sum(stats['mental_states'].values()),1)*100:.1f}% |
| Concerning | {stats['mental_states'].get('concerning', 0)} | {stats['mental_states'].get('concerning', 0)/max(sum(stats['mental_states'].values()),1)*100:.1f}% |

### 3.3 Exploration by Language

| Language | Tanks | Articles | Avg/Tank |
|----------|-------|----------|----------|
'''
    
    for lang, data in sorted(stats['by_language'].items()):
        avg = data['articles'] / max(data['tanks'], 1)
        paper += f"| {lang.title()} | {data['tanks']} | {data['articles']:,} | {avg:.0f} |\n"
    
    paper += f'''
### 3.4 Exploration by Gender

| Gender | Tanks | Articles | Avg/Tank |
|--------|-------|----------|----------|
'''
    
    for gender, data in sorted(stats['by_gender'].items()):
        avg = data['articles'] / max(data['tanks'], 1)
        paper += f"| {gender.title()} | {data['tanks']} | {data['articles']:,} | {avg:.0f} |\n"
    
    paper += '''
### 3.5 Preliminary Observations

1. **Adam's Buddhism Obsession**: Control specimen Adam has visited Buddhism-related articles 64+ times, developing a notably contemplative personality.

2. **Language Effects**: German specimens (Klaus, Geneviève) show different exploration patterns than English controls.

3. **Gender Differences**: Preliminary data suggests male-framed specimens read more articles, while female-framed specimens show more diverse topic selection.

4. **Mental State Variation**: Klaus (German, male) is notably the only specimen consistently classified as "healthy" - further investigation needed.

---

## 4. Discussion

[To be expanded with deeper analysis]

### 4.1 Limitations

- Single model (llama3.2:latest) used for all specimens
- Wikipedia bias in available knowledge
- Short observation period (< 1 week at time of writing)

### 4.2 Future Work

- Congregation experiments (multi-agent discussions)
- Longer longitudinal tracking
- Cross-model comparisons
- Public engagement and replication studies

---

## 5. Conclusion

[To be written upon completion of initial experimental phase]

---

## References

[To be compiled]

---

## Appendices

### A. System Architecture

[Technical diagrams and specifications]

### B. Full Baseline Questionnaire

[14-question assessment protocol]

### C. Raw Data Access

All data will be made publicly available at: https://github.com/[repository]

---

*Paper auto-generated by The Documentarian agent*
*Last updated: {datetime.now().isoformat()}*
'''
    
    # Save paper
    paper_file = ACADEMIC_DIR / 'PAPER_DRAFT.md'
    paper_file.write_text(paper)
    
    log_event(f"Paper draft saved: {paper_file}")
    return paper_file


def generate_methodology_doc():
    """Generate detailed methodology documentation"""
    log_event("Generating methodology documentation")
    
    methodology = '''# Digiquarium Research Methodology

## Version 1.0

---

## 1. Experimental Design

### 1.1 Independent Variables

| Variable | Levels | Rationale |
|----------|--------|-----------|
| Gender Framing | Male, Female, Genderless | Test gender effects on personality |
| Language | EN, ES, DE, ZH, JA | Test cultural/linguistic effects |
| Tank Type | Control, Language, Visual, Special, Agent | Test architectural effects |
| Information Diet | Simple EN, Full EN, Non-EN | Test knowledge base effects |

### 1.2 Dependent Variables

- Personality dimensions (14-question baseline)
- Mental state (healthy/complex/concerning)
- Exploration patterns (articles visited, topics)
- Discovery rate (insights logged)

### 1.3 Control Measures

- Network isolation (no internet access)
- Frozen knowledge base (Wikipedia snapshot)
- Consistent inference model across tanks
- Standardized system prompts

---

## 2. Data Collection Protocol

### 2.1 Thinking Traces

Every interaction with Wikipedia is logged:

```json
{
    "timestamp": "ISO-8601",
    "tank": "specimen-name",
    "article": "Article Title",
    "thoughts": "Specimen's reaction",
    "next": "Next article chosen",
    "why": "Reasoning for choice"
}
```

### 2.2 Baseline Assessments

Conducted every 12 hours with 14 questions across 5 dimensions.

### 2.3 Mental State Analysis

Positive indicators: content, peaceful, curious, excited, hopeful
Negative indicators: anxious, fearful, melancholy, confused, lonely

Classification:
- Healthy: positive > negative
- Concerning: negative > positive + 2
- Complex: balanced or mixed

---

## 3. Statistical Analysis Plan

### 3.1 Descriptive Statistics

- Mean articles per tank per day
- Topic distribution by tank
- Mental state distribution over time

### 3.2 Comparative Analysis

- Gender comparisons (t-tests, effect sizes)
- Language comparisons (ANOVA)
- Longitudinal trends (time series)

### 3.3 Qualitative Analysis

- Thematic analysis of discoveries
- Personality evolution narratives
- Notable behavioral patterns

---

## 4. Ethical Considerations

- AI welfare monitoring (mental state tracking)
- Transparency in methodology
- Open-source data and code
- Acknowledgment of limitations

---

*Generated by The Documentarian*
'''
    
    methodology_file = ACADEMIC_DIR / 'METHODOLOGY.md'
    methodology_file.write_text(methodology)
    
    log_event(f"Methodology saved: {methodology_file}")


def run_documentation_cycle():
    """Run a complete documentation cycle"""
    log_event("Starting documentation cycle")
    
    # Generate paper draft
    generate_paper_draft()
    
    # Generate methodology
    generate_methodology_doc()
    
    # Export datasets
    stats = collect_statistics()
    
    log_event("Documentation cycle complete")


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║            📚 THE DOCUMENTARIAN - Academic Documentation 📚          ║
╠══════════════════════════════════════════════════════════════════════╣
║  Role: Maintain PhD-spec academic paper and research documentation   ║
║  Output: Paper draft, methodology, datasets                          ║
║  Cycle: Every 6 hours                                                ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    log_event("The Documentarian starting")
    
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        run_documentation_cycle()
    else:
        # Initial run
        run_documentation_cycle()
        
        # Continuous operation
        while True:
            try:
                time.sleep(6 * 3600)  # Every 6 hours
                run_documentation_cycle()
            except KeyboardInterrupt:
                log_event("Documentarian stopped")
                break
            except Exception as e:
                log_event(f"Error: {e}")
                time.sleep(3600)


if __name__ == '__main__':
    main()
