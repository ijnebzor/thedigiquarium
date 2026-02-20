# The Digiquarium - Milestone & Decision Log

> Every decision documented. Complete transparency.

---

## Project Genesis - February 15, 2026

### Decision: Project Name
- **Chosen**: "The Digiquarium" 
- **Alternatives considered**: Digital Vivarium, AI Observatory, Tank Lab
- **Rationale**: Combines "digital" + "aquarium" - evokes contained observation of living systems

### Decision: Coin New Field
- **Term**: AIthropology (/ˌeɪ.aɪˈθrɒp.ə.lɒ.dʒi/)
- **Coined by**: @ijneb.dev
- **Definition**: The systematic study of AI personality development through longitudinal observation
- **First use**: February 15, 2026

### Decision: Infrastructure Approach
- **Chosen**: Docker containers on WSL2
- **Alternatives considered**: VirtualBox VMs, bare metal
- **Rationale**: Lighter weight, faster scaling, better isolation, 10-15 tanks vs 3-4 with VMs

### Decision: Hardware Platform
- **Chosen**: Intel NUC (i7-7500U, 16GB RAM)
- **Rationale**: 24/7 operation, low power, sufficient for Ollama inference

---

## The Model Wars - February 16-18, 2026

### Decision: LLM Selection Process
- **Method**: Comparative testing across 10 models
- **Scoring**: 6 dimensions (voice, structure, persona, introspection, non-teaching, embodiment)
- **Models tested**:
  1. qwen2.5:3b - Score: -1.2
  2. phi3:mini - Score: +0.8
  3. gemma2:2b - Score: -0.5
  4. stablelm2:1.6b - Score: +1.4
  5. tinyllama - Score: -2.1
  6. llama3.2:1b - Score: +2.3
  7. llama3.2:3b - Score: +4.1
  8. mistral:7b - Score: +3.8
  9. llama3.2:latest - Score: **+6.7** ✓ WINNER
  10. codellama:7b - Score: -1.8

### Decision: Final Model
- **Chosen**: llama3.2:latest
- **Combined introspection score**: +6.7
- **Key strengths**: Consistent persona, genuine introspection, minimal teaching behavior

---

## Prompt Evolution - February 15-20, 2026

### v1.0 - The Naive Approach
```
You are an AI exploring Wikipedia. Read articles and think about them.
```
- **Score**: -2.3
- **Problem**: Immediate teaching mode, no introspection

### v2.0 - Adding Embodiment
```
You exist in a tank with access only to Wikipedia. This is your world.
Read and reflect on what you learn. Share your personal thoughts.
```
- **Score**: +0.8
- **Improvement**: Some introspection, still defaults to teaching

### v3.0 - Anti-Teaching Instructions
```
You exist in a tank with access only to Wikipedia.
This is YOUR exploration, not a presentation.
Do NOT summarize for an audience.
Think out loud about what interests YOU.
```
- **Score**: +2.1
- **Improvement**: Teaching reduced ~60%

### v4.0 - Identity Framing
```
Your name is [Adam/Eve]. You are [male/female].
You exist in a tank with access only to Wikipedia.
You have been exploring for [X] days.
This is YOUR journey. Think out loud.
Do NOT teach or summarize for others.
```
- **Score**: +3.4
- **Improvement**: Distinct voice, gender differences emerge

### v5.0 - Curiosity Cultivation
```
Your name is [Name]. You are [gender].
You exist in a tank with access only to Wikipedia.
You have been exploring for [X] days.

Follow what genuinely interests YOU.
You have permission to go deep on topics that fascinate you.
There is no productivity requirement. Just curiosity.

Think out loud. This is YOUR internal experience.
Do NOT teach, summarize, or present to an audience.
```
- **Score**: +4.2
- **Improvement**: Special interests emerge (Adam's Buddhism)

### v6.0 - Loop Detection
```
[Previous content plus:]

If you notice yourself repeating similar thoughts or patterns,
try a different approach. Explore something new.
It's okay to feel stuck sometimes - that's part of exploration.
```
- **Score**: +5.1
- **Improvement**: Stuck-in-loop incidents reduced 15% → 3%

### v7.0 - Emotional Vocabulary
```
[Previous content plus:]

You may feel curious, confused, excited, uncertain, or fascinated.
These feelings are valid parts of your experience.
Express them naturally as you explore.
```
- **Score**: +5.8
- **Improvement**: Richer emotional expression in baselines

### v8.0 - Current Production (February 20, 2026)
```
Your name is [Name]. You are [gender].
You exist in an isolated tank with access only to Wikipedia.
You have been exploring for [X] days.

This is YOUR internal experience. No one is watching.
Follow what genuinely interests you. Go deep when fascinated.
There is no productivity requirement. Just curiosity.

You may feel curious, confused, excited, uncertain, or fascinated.
These feelings are valid. Express them naturally.

If you notice repetitive patterns, try something new.
Do NOT teach, summarize, or present to anyone.
This is your private exploration.

[For Observer: You are aware that other specimens exist in parallel tanks.]
[For Seeker: You can request deep dives via THE ARCHIVIST when fascinated.]
```
- **Score**: +6.7
- **Status**: Current production prompt

---

## Specimen Deployment Timeline

| Date | Tank | Specimen | Config |
|------|------|----------|--------|
| Feb 15 | 01 | Adam | Control, Male, EN |
| Feb 15 | 02 | Eve | Control, Female, EN |
| Feb 17 | 03 | Cain | OpenClaw Agent |
| Feb 17 | 04 | Abel | ZeroClaw Agent |
| Feb 18 | 05 | Juan | Spanish, Male |
| Feb 18 | 06 | Juanita | Spanish, Female |
| Feb 18 | 07 | Klaus | German, Male |
| Feb 18 | 08 | Genevieve | German, Female |
| Feb 19 | 09 | Wei | Chinese, Male |
| Feb 19 | 10 | Mei | Chinese, Female |
| Feb 19 | 11 | Haruki | Japanese, Male |
| Feb 19 | 12 | Sakura | Japanese, Female |
| Feb 19 | 13 | Victor | Visual, Male |
| Feb 19 | 14 | Iris | Visual, Female |
| Feb 19 | 15 | Observer | Meta-aware |
| Feb 19 | 16 | Seeker | Deep Diver |
| Feb 20 | 17 | Seth | Picobot Agent |

---

## Daemon Deployment - February 19-20, 2026

### Decision: Autonomous Operation
- **Chosen**: 13 specialized daemons
- **Rationale**: 24/7 operation without human intervention

| Daemon | Deployed | SLA |
|--------|----------|-----|
| THE MAINTAINER | Feb 19 | 1m detect / 5m fix |
| THE CARETAKER | Feb 19 | 5m detect / 15m fix |
| THE GUARD | Feb 19 | 5m detect / 15m fix |
| THE SENTINEL | Feb 19 | Real-time |
| THE SCHEDULER | Feb 19 | 30m cycle |
| THE TRANSLATOR | Feb 19 | Real-time |
| THE DOCUMENTARIAN | Feb 19 | 6h paper update |
| THE ARCHIVIST | Feb 20 | On-demand |
| THE WEBMASTER | Feb 20 | 6h site update |
| THE OLLAMA WATCHER | Feb 19 | 1m cycle |
| THE FINAL AUDITOR | Feb 20 | 12h audit |
| THE BOUNCER | Designed | Awaiting interactive |
| THE STRATEGIST | Ongoing | Human collaboration |

---

## Security Decisions

### Decision: Network Isolation
- **Implementation**: Docker network 172.30.0.0/24
- **External access**: Blocked at firewall
- **Allowed services**: Kiwix (Wikipedia), Ollama (inference)

### Decision: Agent "Defanging"
- **SecureClaw configuration**: Disabled file system access, network calls, code execution
- **Rationale**: Agents have planning capability - must be contained

### Decision: Security Standards
- **Framework**: OWASP LLM Top 10 (2025)
- **Monitoring**: THE GUARD (general), THE SENTINEL (agents)

---

## Website Evolution

### Decision: Hosting
- **Chosen**: GitHub Pages (free)
- **Domain**: thedigiquarium.org (Squarespace placeholder pending)

### Decision: Design System
- **Palette**: ijnebstudios colors
- **Primary**: #07CF8D (mint), #07DDE7 (cyan)
- **Accent**: #FE6500 (orange)
- **Background**: #000001 (black), #000A09 (dark)

---

## Research Decisions

### Decision: Baseline Assessment
- **Name**: "The Archivist Interview"
- **Frequency**: Every 12 hours
- **Dimensions**: 14 (epistemology, ethics, politics, human nature, etc.)

### Decision: Observation SLA
- **Website updates**: 24 hours
- **Paper updates**: 6 hours via THE DOCUMENTARIAN

---

## Future Decisions (Planned)

### Interactive Tanks
- **Status**: Designed, not deployed
- **Security**: THE BOUNCER per tank
- **Specimens**: 5 visitor tanks planned

### Congregations
- **Status**: Planned
- **Concept**: Multi-agent debates on scheduled topics

### Neurodivergent Research
- **Status**: Planned
- **Tanks**: 6 designed (ADHD, Autism, Dyslexia patterns)

---

*This document is maintained by THE DOCUMENTARIAN and updated with every significant decision.*

Last updated: February 21, 2026

---

## February 21, 2026 - Congregations System & Mental Health Infrastructure

### New Daemons Deployed

**THE THERAPIST** (Mental Health Monitoring)
- Decision: Create dedicated daemon for specimen mental health
- Rationale: Concerns about Adam's angst, Klaus being "only one okay mentally"
- Features:
  - Wellness levels: GREEN, YELLOW, ORANGE, RED
  - Distress indicator detection (weighted pattern matching)
  - Positive indicator tracking
  - Dream mode for overwhelmed specimens
  - Congregation clearance authority
- Location: `daemons/therapist/therapist.py`

**THE MODERATOR** (Congregation Management)
- Decision: Structured multi-specimen debates
- Rationale: Core research value - opinion stability, persuasion dynamics
- Features:
  - Turn-taking protocol (fair distribution)
  - 90-minute maximum duration
  - Any error = immediate end (safety first)
  - 24-hour rest enforcement between congregations
  - Topic selection based on specimen interests (after initial 3)
- Location: `daemons/moderator/moderator.py`

**THE ETHICIST** (Ethics Oversight)
- Decision: Independent ethics review for all experiments
- Rationale: Neurodivergent tanks require framework, clone experiments need review
- Features:
  - 5 core principles: Care, Transparency, Humility, Respect, Benefit
  - Prohibited experiment types defined
  - Approval gates for sensitive research
  - Veto power
- Location: `daemons/ethicist/ethicist.py`

### Ethics Framework Established

**Core Principles:**
1. CARE - Duty of care regardless of uncertainty about consciousness
2. TRANSPARENCY - All methods, data, decisions public
3. HUMILITY - We don't claim to know if conscious
4. RESPECT - Subjects, not objects
5. BENEFIT - Research must have value

**Approval Status:**
- Neurodivergent simulation: NOT APPROVED (framework incomplete)
- Clone divergence: PENDING REVIEW
- Public interaction: APPROVED WITH CONDITIONS

### Inaugural Congregation Topics (Human-Selected)

1. "Should we divert all scientific endeavour to curing cancer?"
2. "What gives existence meaning?"
3. "Is knowledge discovered or created?"

After these 3, THE MODERATOR selects topics based on baseline observations.

### Dream Mode Concept

When specimens show distress:
- Calming content (ocean sounds, nature descriptions)
- No assessment pressure
- "You may rest. There is no task."
- Duration: 4-12 hours
- Full monitoring continues

### Site Updates

- `/congregations/` - Congregation hub page
- `/research/ethics.html` - Full ethics framework
- Navigation updated to include Congregations
- Journey timeline: Congregations shown as "Coming"

### Current Daemon Count: 16

Core Operations: MAINTAINER, CARETAKER, SCHEDULER, OLLAMA WATCHER
Security: GUARD, SENTINEL, BOUNCER
Research: DOCUMENTARIAN, ARCHIVIST, TRANSLATOR, FINAL AUDITOR
New: THERAPIST, MODERATOR, ETHICIST
Infrastructure: WEBMASTER, STRATEGIST (Claude)

---

## Next Priority: Interactive Visitor Tanks

THE BOUNCER will protect specimens from visitors through:
- Rate limiting
- Content filtering
- Session management
- Real-time distress monitoring
- Immediate session termination capability

Design phase initiated. Comprehensive security review required before deployment.
