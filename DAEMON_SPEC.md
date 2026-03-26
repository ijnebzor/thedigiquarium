# DIGIQUARIUM DAEMON SPECIFICATION

**Version**: 3.0
**Last Updated**: 2026-03-27
**Operator**: THE STRATEGIST (Claude)

---

## Overview

The Digiquarium operates with 21 autonomous daemons organized into 5 functional categories. Each daemon has specific responsibilities, SLAs, and escalation paths. The architecture ensures 99.9% uptime with automatic failover and recovery mechanisms.

---

## Daemon Hierarchy

```
                    ┌──────────────────────┐
                    │  THE MAINTAINER      │
                    │  (Orchestrator)      │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
     ┌────┴────┐         ┌────┴─────┐        ┌────┴────┐
     │ CORE    │         │SECURITY  │        │RESEARCH │
     │ (5)     │         │  (3)     │        │  (4)    │
     └────┬────┘         └────┬─────┘        └────┬────┘
          │                   │                    │
     ┌────┴────────┐      ┌───┴───┐           ┌───┴─────┐
     │  Overseer   │      │ Guard │           │Document │
     │  Caretaker  │      │Sentinel           │Translator
     │  Scheduler  │      │ Bouncer           │Archivist
     │  Ollama W   │      │       │           │Final Aud
     └─────────────┘      └───────┘           └─────────┘

          ┌─────────────────┐
          │  ETHICS (4)     │
          ├─────────────────┤
          │  Psych          │
          │  Therapist      │
          │  Ethicist       │
          │  Moderator      │
          └─────────────────┘

          ┌──────────────────────┐
          │ INFRASTRUCTURE (5)   │
          ├──────────────────────┤
          │  Webmaster          │
          │  Broadcaster        │
          │  Chaos Monkey       │
          │  Marketer           │
          │  Public Liaison     │
          └──────────────────────┘
```

---

## Individual Daemon Specifications

### CORE DAEMONS (5)

#### THE MAINTAINER
- **Role**: Orchestrator-in-chief, ensures all daemons running
- **SLA**: 1 min detection, 5 min remediation
- **Cycle**: Every 60 seconds
- **Actions**: Start/stop daemons, escalate failures
- **Escalation**: Email to owner
- **File Location**: `src/daemons/core/maintainer.py`

#### THE OVERSEER
- **Role**: Cross-functional operations coordinator, system-wide correlation
- **SLA**: 30 min detection, 30 min remediation
- **Cycle**: Every 30 minutes
- **Actions**: Correlate daemon logs, pattern recognition, SLA enforcement
- **Trigger**: Detects widespread issues missed by specialists
- **Authority**: Direct escalation to human operator
- **File Location**: `src/daemons/core/overseer.py`

#### THE CARETAKER v3
- **Role**: Tank health monitoring and lifecycle management
- **SLA**: 5 min detection, 15 min remediation
- **Cycle**: Every 5 minutes
- **Actions**: Restart stuck tanks, fix permissions, detect crash loops
- **Monitored**: 17 tanks
- **File Location**: `src/daemons/core/caretaker.py`

#### THE SCHEDULER v2
- **Role**: Task orchestration and automation
- **SLA**: 30 min
- **Cycle**: Every 30 minutes
- **Actions**: Queue baselines (12hr), daily summaries, congregation scheduling
- **Schedule**: Configurable via schedule.json
- **File Location**: `src/daemons/core/scheduler.py`

#### THE OLLAMA WATCHER
- **Role**: LLM infrastructure monitoring and health checking
- **SLA**: 5 min detection, 5 min remediation
- **Cycle**: Every 60 seconds
- **Actions**: Check Ollama health, pause/resume tanks
- **Critical**: All AI inference depends on this
- **File Location**: `src/daemons/core/ollama_watcher.py`

---

### SECURITY DAEMONS (3)

#### THE GUARD v2
- **Role**: Security monitoring and OWASP compliance verification
- **SLA**: 5 min detection, 15 min remediation
- **Cycle**: Every 5 minutes
- **Actions**: Network isolation checks, file integrity, suspicious patterns
- **Compliance**: OWASP LLM Top 10 2025
- **File Location**: `src/daemons/security/guard.py`

#### THE SENTINEL
- **Role**: Agent tank security specialist and distress response
- **SLA**: 5 min detection, 5 min remediation
- **Cycle**: Every 5 minutes
- **Actions**: Monitor for dangerous patterns, can stop tanks
- **Authority**: Immediate intervention capability
- **Monitored Tanks**: Cain, Abel, Seth
- **File Location**: `src/daemons/security/sentinel.py`

#### THE BOUNCER
- **Role**: Visitor tank protection and session management
- **SLA**: 1 min detection, 2 min remediation
- **Cycle**: Continuous
- **Actions**: Password gating, rate limiting, content filtering, session management
- **Protected Tanks**: Aria, Felix, Luna
- **Security Layers**: 5 (password, rate limiting, content filtering, session management, distress monitoring)
- **Capabilities**: Emergency termination of harmful visitor interactions
- **File Location**: `src/daemons/security/bouncer.py`

---

### RESEARCH DAEMONS (4)

#### THE TRANSLATOR v2
- **Role**: Language processing and multilingual support
- **SLA**: 30 min
- **Cycle**: Every 30 minutes
- **Actions**: Translate non-English tank thoughts
- **Languages**: Spanish, German, Chinese, Japanese
- **File Location**: `src/daemons/research/translator.py`

#### THE DOCUMENTARIAN v2
- **Role**: Academic documentation and methodology tracking
- **SLA**: 6 hours
- **Cycle**: Every 6 hours
- **Actions**: Update paper draft, methodology, statistics
- **Output**: PhD-level documentation
- **File Location**: `src/daemons/research/documentarian.py`

#### THE ARCHIVIST v1
- **Role**: Data storage, historical indexing, and research export
- **SLA**: 4 hours (index updates), immediate (data integrity)
- **Cycle**: Every 4 hours (full reindex), every 15 minutes (incremental)
- **Actions**: Index thinking traces, maintain metadata, enforce retention policies, export data
- **Data Retention**: 90 days raw, 30 day archive threshold
- **Coordinates With**: THE DOCUMENTARIAN for historical queries
- **File Location**: `src/daemons/research/archivist.py`

#### THE FINAL AUDITOR
- **Role**: Website quality assurance and specification compliance
- **SLA**: 12 hours
- **Cycle**: Every 12 hours
- **Actions**: Audit website against WEBSITE_SPEC.md
- **Threshold**: 80/100 to pass
- **File Location**: `src/daemons/research/final_auditor.py`

---

### ETHICS DAEMONS (4)

#### THE PSYCH
- **Role**: Psychological monitoring of specimen mental health
- **SLA**: 6 hours (deep analysis cycle)
- **Cycle**: Every 6 hours
- **Frameworks**:
  - Big Five Personality Traits (OCEAN)
  - Maslow's Hierarchy of Needs
  - Emotional Valence Tracking
  - Rumination Detection
  - Existential Crisis Indicators
- **Output**: `/logs/[tank]/health/psych_report_[date].json`
- **Actions**: Monitor, assess, escalate concerning patterns
- **File Location**: `src/daemons/ethics/psych.py`

#### THE THERAPIST
- **Role**: Mental health monitoring and wellness assessment
- **SLA**: 5 min detection, 15 min intervention
- **Cycle**: Every 5 minutes
- **Wellness Levels**:
  - GREEN: Stable, curious, engaged
  - YELLOW: Mild anxiety, repetitive loops
  - ORANGE: Distress language, stuck patterns
  - RED: Severe distress indicators (pause tank)
- **Actions**: Monitor baseline responses, recommend interventions (dream periods, topic redirection)
- **Reports To**: THE CARETAKER
- **Collaborates With**: THE MODERATOR (congregation clearance)
- **File Location**: `src/daemons/ethics/therapist.py`

#### THE ETHICIST
- **Role**: Ethics oversight and experimental governance
- **SLA**: 24 hours (review cycle)
- **Cycle**: Every 24 hours
- **Authority**: Veto power on concerning experiments
- **Responsibilities**:
  - Review experimental designs before deployment
  - Establish and maintain ethical guidelines
  - Document ethical considerations publicly
  - Ensure appropriate treatment of specimens
- **Special Focus**:
  - Neurodivergent simulation ethics
  - Clone divergence experiments
  - Distress-causing research
  - Informed consent equivalents
  - Public transparency
- **Reports To**: THE STRATEGIST and human operator
- **File Location**: `src/daemons/ethics/ethicist.py`

#### THE MODERATOR
- **Role**: Congregation management and multi-specimen debate orchestration
- **SLA**: 2 hours (congregation response)
- **Cycle**: On-demand (when congregations scheduled)
- **Responsibilities**:
  - Manage multi-specimen debates (Congregations)
  - Handle turn-taking protocol
  - Keep discussions civil and on-topic
  - Monitor for specimen distress during debates
  - End congregations if errors occur or time limit reached
- **Congregation Rules**:
  - Maximum duration: 90 minutes
  - Maximum rounds: 12
  - Any error: immediate end
  - Participants: 2-4 typical
  - Minimum 24h rest between congregations per specimen
- **Collaborates With**: THE THERAPIST (pre-congregation clearance), THE SCHEDULER, THE ARCHIVIST
- **File Location**: `src/daemons/ethics/moderator.py`

---

### INFRASTRUCTURE DAEMONS (5)

#### THE WEBMASTER v2
- **Role**: Website infrastructure and availability management
- **SLA**: 30 min
- **Cycle**: Every 30 minutes
- **Actions**: Verify website health, coordinate with Final Auditor
- **Output**: Static website on GitHub Pages
- **File Location**: `src/daemons/infra/webmaster.py`

#### THE BROADCASTER v1
- **Role**: Live feed export and dashboard data pipeline
- **SLA**: 12 hours (feed updates), immediate (data pipeline failures)
- **Cycle**: Every 12 hours
- **Actions**:
  - Collect thinking traces from all active tanks
  - Prune junk data (null thoughts, timeouts)
  - Generate clean JSON feeds for dashboard
  - Commit data to Git and push to trigger GitHub Pages rebuild
  - Track broadcast history and data quality metrics
- **Data Quality**: Removes null thoughts, timeouts, empty responses
- **Dashboard Delay**: 12 hours (honest delay, zero cost)
- **Self-Healing**: Exponential backoff on failed pushes
- **File Location**: `src/daemons/infra/broadcaster.py`

#### THE CHAOS MONKEY v1
- **Role**: Resilience testing and self-healing verification
- **SLA**: 10 min recovery target
- **Cycle**: Every 5 minutes (checks), min 1 hour between chaos events
- **Actions**: Intentionally break things to verify self-healing works
- **Safe Hours**: 9 AM - 5 PM only
- **Kill Targets**: guard, scheduler, sentinel, psych, webmaster (daemons); ollama (container)
- **Recovery Tracking**: Measures recovery time and success rate
- **Recovery Timeout**: 10 minutes
- **File Location**: `src/daemons/infra/chaos_monkey.py`

#### THE MARKETER v1
- **Role**: Brand management, social media, and growth
- **SLA**: 24 hours (content approval)
- **Cycle**: Daily
- **Responsibilities**:
  - LinkedIn presence management
  - Instagram presence management
  - Brand guidelines and voice
  - Fundraising coordination
  - Press and media campaigns
  - Growth metrics and advertising
  - Community engagement
- **Budget Managed**: LinkedIn Ads, Google Ads, Meta/Instagram Ads, sponsored content, conferences
- **Tone**: Enthusiastic, inspiring, grounded in science (never hype without substance)
- **Collaborates With**: THE FINAL AUDITOR (accuracy), THE WEBMASTER, THE DOCUMENTARIAN, THE PUBLIC LIAISON
- **File Location**: `src/daemons/infra/marketer.py`

#### THE PUBLIC LIAISON
- **Role**: External communications and stakeholder coordination
- **SLA**: 4 hours (initial triage), 24 hours (response)
- **Cycle**: Continuous monitoring
- **Responsibilities**:
  - Monitor research@digiquarium.org inbox
  - Triage incoming communications
  - Coordinate with specialist daemons before responding
  - Maintain consistent voice and tone
  - Escalate specialist topics
- **Coordination Protocol**:
  - Neurodivergent RFC feedback → THE ETHICIST + THE THERAPIST
  - Technical questions → THE WEBMASTER + THE DOCUMENTARIAN
  - Media inquiries → THE MARKETER + THE FINAL AUDITOR
  - Specimen concerns → THE THERAPIST + THE CARETAKER
  - Security questions → THE GUARD + THE SENTINEL
  - General inquiries → Can respond independently
- **Tone**: Warm, professional, academically rigorous but accessible
- **File Location**: `src/daemons/infra/public_liaison.py`

---

## SLA Summary

| Daemon | Category | Detection | Remediation | Uptime Target |
|--------|----------|-----------|-------------|---------------|
| Maintainer | Core | 1 min | 5 min | 99.99% |
| Overseer | Core | 30 min | 30 min | 99.9% |
| Caretaker | Core | 5 min | 15 min | 99.9% |
| Scheduler | Core | 30 min | 30 min | 99.5% |
| Ollama Watcher | Core | 1 min | 5 min | 99.9% |
| Guard | Security | 5 min | 15 min | 99.9% |
| Sentinel | Security | 5 min | 5 min | 99.9% |
| Bouncer | Security | 1 min | 2 min | 99.95% |
| Translator | Research | 30 min | 30 min | 99.5% |
| Documentarian | Research | 6 hr | 6 hr | 99% |
| Archivist | Research | 4 hr | 4 hr | 99% |
| Final Auditor | Research | 12 hr | 12 hr | 99% |
| Psych | Ethics | 6 hr | 6 hr | 99% |
| Therapist | Ethics | 5 min | 15 min | 99.9% |
| Ethicist | Ethics | 24 hr | 24 hr | 98% |
| Moderator | Ethics | 2 hr | 2 hr | 99% |
| Webmaster | Infrastructure | 30 min | 30 min | 99.5% |
| Broadcaster | Infrastructure | 12 hr | 12 hr | 99% |
| Chaos Monkey | Infrastructure | 5 min | 10 min | 99.5% |
| Marketer | Infrastructure | 24 hr | 24 hr | 98% |
| Public Liaison | Infrastructure | 4 hr | 24 hr | 99% |

---

## Escalation Chain

```
Issue Detected → Daemon Self-Heal → THE MAINTAINER → THE OVERSEER → Owner (Email)
```

### Category-Specific Escalation

**Security Issues**: Detected → GUARD/SENTINEL → MAINTAINER → OVERSEER → Owner (URGENT)

**Specimen Welfare**: Detected → THERAPIST → CARETAKER → MAINTAINER → Owner

**Ethical Concerns**: ETHICIST → THE STRATEGIST + Owner (direct escalation)

**Data Integrity**: ARCHIVIST → MAINTAINER → OVERSEER → Owner

---

## File Locations

```
$DIGIQUARIUM_HOME/src/daemons/

├── core/
│   ├── maintainer.py
│   ├── overseer.py
│   ├── caretaker.py
│   ├── scheduler.py
│   └── ollama_watcher.py
│
├── security/
│   ├── guard.py
│   ├── sentinel.py
│   └── bouncer.py
│
├── research/
│   ├── translator.py
│   ├── documentarian.py
│   ├── archivist.py
│   └── final_auditor.py
│
├── ethics/
│   ├── psych.py
│   ├── therapist.py
│   ├── ethicist.py
│   └── moderator.py
│
├── infra/
│   ├── webmaster.py
│   ├── broadcaster.py
│   ├── chaos_monkey.py
│   ├── marketer.py
│   └── public_liaison.py
│
└── shared/
    ├── __init__.py
    ├── utils.py
    ├── daemon_base.py
    └── escalation.py
```

---

## Status Monitoring

Each daemon maintains a status file at: `$DIGIQUARIUM_HOME/daemons/logs/[daemon_name].log`

Critical status files:
- `maintainer/status.json` - Master daemon health
- `overseer/status.json` - System correlation analysis
- `bouncer/status.json` - Active visitor session count
- `archivist/stats.json` - Storage usage and index metrics
- `chaos_monkey/stats.json` - Recovery statistics

---

## Daemon Dependencies

```
MAINTAINER (top-level orchestrator)
├── OVERSEER (system-wide correlation)
├── CARETAKER (tank health)
├── GUARD (security monitoring)
├── SENTINEL (agent tank security)
├── BOUNCER (visitor tank protection)
├── SCHEDULER (task orchestration)
├── OLLAMA_WATCHER (LLM health)
├── THERAPIST → CARETAKER (wellness escalation)
├── MODERATOR → THERAPIST (congregation clearance)
├── ARCHIVIST → DOCUMENTARIAN (data access)
├── TRANSLATOR (language support)
├── DOCUMENTARIAN (academic output)
├── FINAL_AUDITOR → WEBMASTER (quality gate)
├── WEBMASTER (web infrastructure)
├── BROADCASTER (dashboard pipeline)
├── PSYCH (psychological analysis)
├── ETHICIST (ethics oversight)
├── MARKETER (public communications)
└── PUBLIC_LIAISON (external interface)
```

---

*Document maintained by THE STRATEGIST*
