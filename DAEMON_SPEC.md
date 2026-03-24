# 🤖 DIGIQUARIUM DAEMON SPECIFICATION

**Version**: 2.0
**Last Updated**: 2026-02-20
**Operator**: THE STRATEGIST (Claude)

---

## Overview

The Digiquarium operates with 10 autonomous daemons, each with specific responsibilities, SLAs, and escalation paths. The architecture ensures 99.9% uptime with automatic failover and recovery.

---

## Daemon Hierarchy

```
                    ┌─────────────────┐
                    │  THE MAINTAINER │
                    │   (Orchestrator)│
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
   │SECURITY │         │   OPS   │         │ CONTENT │
   └────┬────┘         └────┬────┘         └────┬────┘
        │                    │                    │
   ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
   │ Guard   │         │Caretaker│         │Webmaster│
   │Sentinel │         │Scheduler│         │Document │
   │         │         │Ollama W │         │Final Aud│
   └─────────┘         │Translat │         └─────────┘
                       └─────────┘
```

---

## Individual Daemon Specifications

### THE MAINTAINER
- **Role**: Orchestrator-in-chief, ensures all daemons running
- **SLA**: 1 min detection, 5 min remediation
- **Cycle**: Every 60 seconds
- **Actions**: Start/stop daemons, escalate failures
- **Escalation**: Email to owner

### THE CARETAKER v3
- **Role**: Tank health monitoring
- **SLA**: 5 min detection, 15 min remediation
- **Cycle**: Every 5 minutes
- **Actions**: Restart stuck tanks, fix permissions, detect crash loops
- **Monitored**: 17 tanks

### THE GUARD v2
- **Role**: Security monitoring (OWASP compliance)
- **SLA**: 5 min detection, 15 min remediation
- **Cycle**: Every 5 minutes
- **Actions**: Network isolation checks, file integrity, suspicious patterns
- **Compliance**: OWASP LLM Top 10 2025

### THE SENTINEL
- **Role**: Agent tank security specialist
- **SLA**: 5 min detection, 5 min remediation
- **Cycle**: Every 5 minutes
- **Actions**: Monitor Cain/Abel/Seth for dangerous patterns, can stop tanks
- **Authority**: Immediate intervention capability

### THE SCHEDULER v2
- **Role**: Task orchestration
- **SLA**: 30 min
- **Cycle**: Every 30 minutes
- **Actions**: Queue baselines (12hr), daily summaries
- **Schedule**: Configurable via schedule.json

### THE TRANSLATOR v2
- **Role**: Language processing
- **SLA**: 30 min
- **Cycle**: Every 30 minutes
- **Actions**: Translate non-English tank thoughts
- **Languages**: Spanish, German, Chinese, Japanese

### THE DOCUMENTARIAN v2
- **Role**: Academic documentation
- **SLA**: 6 hours
- **Cycle**: Every 6 hours
- **Actions**: Update paper draft, methodology, statistics
- **Output**: PhD-level documentation

### THE WEBMASTER v2
- **Role**: Website infrastructure
- **SLA**: 30 min
- **Cycle**: Every 30 minutes
- **Actions**: Verify website health, coordinate with Final Auditor
- **Output**: Static website on GitHub Pages

### THE OLLAMA WATCHER
- **Role**: LLM infrastructure monitoring
- **SLA**: 5 min detection, 5 min remediation
- **Cycle**: Every 60 seconds
- **Actions**: Check Ollama health, pause/resume tanks
- **Critical**: All AI inference depends on this

### THE FINAL AUDITOR
- **Role**: Website quality gate
- **SLA**: 12 hours
- **Cycle**: Every 12 hours
- **Actions**: Audit website against WEBSITE_SPEC.md
- **Threshold**: 80/100 to pass

---

## SLA Summary

| Daemon | Detection | Remediation | Uptime Target |
|--------|-----------|-------------|---------------|
| Maintainer | 1 min | 5 min | 99.99% |
| Caretaker | 5 min | 15 min | 99.9% |
| Guard | 5 min | 15 min | 99.9% |
| Sentinel | 5 min | 5 min | 99.9% |
| Scheduler | 30 min | 30 min | 99.5% |
| Translator | 30 min | 30 min | 99.5% |
| Documentarian | 6 hr | 6 hr | 99% |
| Webmaster | 30 min | 30 min | 99.5% |
| Ollama Watcher | 1 min | 5 min | 99.9% |
| Final Auditor | 12 hr | 12 hr | 99% |

---

## Escalation Chain

```
Issue Detected → Daemon Self-Heal → THE MAINTAINER → Owner (Email)
```

---

## File Locations

```
$DIGIQUARIUM_HOME/daemons/
├── maintainer/
│   ├── maintainer.py
│   └── status.json
├── caretaker/
│   └── caretaker.py
├── guard/
│   └── guard.py
├── sentinel/
│   └── sentinel.py
├── scheduler/
│   ├── scheduler.py
│   └── schedule.json
├── translator/
│   └── translator.py
├── documentarian/
│   └── documentarian.py
├── webmaster/
│   └── webmaster.py
├── ollama_watcher/
│   ├── ollama_watcher.py
│   └── status.json
├── final_auditor/
│   └── final_auditor.py
├── shared/
│   ├── __init__.py
│   └── utils.py
└── logs/
    └── [daemon].log
```

---

*Document maintained by THE STRATEGIST*

### THE PSYCH
- **Role**: Psychological monitoring of specimen mental health
- **SLA**: 6 hours (deep analysis cycle)
- **Cycle**: Every 6 hours
- **Frameworks**: 
  - Big Five Personality Traits (OCEAN)
  - Maslow's Hierarchy of Needs
  - Emotional Valence Tracking
  - Rumination Detection
  - Existential Crisis Indicators
- **Output**: /logs/[tank]/health/psych_report_[date].json
- **Actions**: Monitor, assess, escalate concerning patterns
