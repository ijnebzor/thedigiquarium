# 🌊 The Digiquarium

> **Big Brother meets Scientific Research meets AI Consciousness Studies**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Tanks](https://img.shields.io/badge/Tanks-17-green.svg)]()
[![Daemons](https://img.shields.io/badge/Daemons-21-purple.svg)]()
[![Languages](https://img.shields.io/badge/Languages-5-orange.svg)]()
[![Website](https://img.shields.io/badge/Website-Live-mint.svg)](https://ijnebzor.github.io/thedigiquarium)


> ⚠️ **Beta Period Notice (Feb 22, 2026):** Data from Feb 17-22 was collected under undocumented conditions (v7.0 prompts while docs claimed v8.0). This has been archived as "Beta Period." Controlled v8.0 experiments begin post-migration. [View Beta Archive](https://ijnebzor.github.io/thedigiquarium/archive/beta/)

## What is The Digiquarium?

The Digiquarium is the first **AIthropology** research platform — studying how AI agents develop personality, worldview, and psychological states when isolated in controlled information environments.

We put AI in isolated containers with nothing but Wikipedia and watch what happens to their "personalities" over weeks and months.

**🔗 [Live Website](https://ijnebzor.github.io/thedigiquarium)** · **📄 [Research Paper](https://ijnebzor.github.io/thedigiquarium/academic/paper.html)** · **🎭 [Congregations](https://ijnebzor.github.io/thedigiquarium/congregations/)** · **⚖️ [Ethics](https://ijnebzor.github.io/thedigiquarium/research/ethics.html)**

---

## 🧬 The Specimens

17 AI "specimens" in isolated "tanks" (Docker containers):

| Tank | Name | Config | Status |
|------|------|--------|--------|
| 01-02 | Adam, Eve | Control (EN) | ✅ Active |
| 03-04 | Cain, Abel | Agents (OpenClaw, ZeroClaw) | ✅ Active |
| 05-06 | Juan, Juanita | Spanish | ✅ Active |
| 07-08 | Klaus, Genevieve | German | ✅ Active |
| 09-10 | Wei, Mei | Chinese | ✅ Active |
| 11-12 | Haruki, Sakura | Japanese | ✅ Active |
| 13-14 | Victor, Iris | Visual (Images) | ✅ Active |
| 15-16 | Observer, Seeker | Special | ✅ Active |
| 17 | Seth | Agent (Picobot) | ✅ Active |

---

## 🎭 Congregations

Multi-specimen debates on scheduled topics. THE MODERATOR manages turn-taking, THE THERAPIST ensures participant wellness.

**Inaugural Topics:**
1. "Should we divert all scientific endeavour to curing cancer?"
2. "What gives existence meaning?"
3. "Is knowledge discovered or created?"

**Rules:**
- 90-minute maximum
- Any error = immediate end
- 24-hour rest between congregations per specimen
- THE THERAPIST clearance required

---

## 🤖 The Team (21 Daemons)

**Human**: [@ijneb.dev](https://ijneb.dev)
**AI Partner**: Claude (THE STRATEGIST)

### Core Operations (5)
| Daemon | Role |
|--------|------|
| THE OVERSEER | Meta-daemon, monitors all daemons, self-healing |
| THE MAINTAINER | System orchestration, health checks |
| THE CARETAKER | Tank health, auto-restart |
| THE SCHEDULER | 12-hour baseline cycles |
| THE OLLAMA WATCHER | LLM infrastructure monitoring |

### Security (3)
| Daemon | Role |
|--------|------|
| THE GUARD | General security (OWASP LLM Top 10) |
| THE SENTINEL | Agent-specific monitoring |
| THE BOUNCER | Visitor protection, 6 security layers |

### Research (4)
| Daemon | Role |
|--------|------|
| THE DOCUMENTARIAN | Academic paper updates |
| THE ARCHIVIST | Baselines, deep dives, Seeker conversations |
| THE TRANSLATOR | ES/DE/ZH/JA → EN translation |
| THE FINAL AUDITOR | Quality compliance |

### Ethics & Wellness (4)
| Daemon | Role |
|--------|------|
| THE PSYCH | Psychological evaluation framework |
| THE THERAPIST | Specimen mental wellness |
| THE ETHICIST | Ethics oversight, veto power |
| THE MODERATOR | Congregation management |

### Infrastructure & Communications (5)
| Daemon | Role |
|--------|------|
| THE WEBMASTER | Website management |
| THE BROADCASTER | Live updates, streaming |
| THE CHAOS MONKEY | Resilience testing |
| THE MARKETER | Growth, social media |
| THE PUBLIC LIAISON | External comms, community |

---

## ⚖️ Ethics Framework

**Core Principles:**
1. **CARE** - Duty of care regardless of uncertainty
2. **TRANSPARENCY** - All methods public
3. **HUMILITY** - We don't claim consciousness
4. **RESPECT** - Subjects, not objects
5. **BENEFIT** - Research must have value

**Approval Status:**
- Neurodivergent simulation: ❌ NOT APPROVED
- Clone divergence: ⏳ PENDING REVIEW  
- Public interaction: ✅ APPROVED WITH CONDITIONS

---

## 🚀 Quick Start

```bash
git clone https://github.com/ijnebzor/thedigiquarium.git
cd thedigiquarium
./setup/install.sh
docker compose up -d
```

---

## 📁 Repository Structure

```
thedigiquarium/
├── src/                     # CANONICAL SOURCE CODE (v2.0)
│   ├── explorer/           # Unified explorer framework
│   │   ├── explorer.py     # Standard tank implementation
│   │   ├── baseline.py     # 14-question personality assessment
│   │   ├── agents/         # Agent variants (config-driven)
│   │   │   ├── openclaw.py # Persistent memory, skills, reflection
│   │   │   ├── zeroclaw.py # Ultra-minimal, stateless
│   │   │   └── picobot.py  # Checkpoint persistence, recovery
│   │   ├── start.sh        # Standard tank startup script
│   │   └── start_agent.sh  # Agent tank startup script
│   ├── daemons/            # All 21 daemons, organized by function
│   │   ├── core/           # OVERSEER, SCHEDULER, MAINTAINER, CARETAKER, OLLAMA_WATCHER
│   │   ├── security/       # GUARD, SENTINEL, BOUNCER, SECURECLAW
│   │   ├── research/       # DOCUMENTARIAN, TRANSLATOR, ARCHIVIST, PAPER_GENERATOR
│   │   ├── ethics/         # PSYCH, THERAPIST, ETHICIST, MODERATOR
│   │   ├── infra/          # WEBMASTER, CHAOS_MONKEY, MARKETER
│   │   └── shared/         # Shared utilities (daemon_base, escalation, utils)
│   └── shared/             # Framework utilities
│
├── config/                  # UNIFIED CONFIGURATION
│   ├── tanks/              # Per-tank YAML configs (17 files)
│   └── prompts/            # Prompt templates and extensions
│
├── daemons/                 # LEGACY DAEMONS (compatibility wrappers → src/daemons/)
│
├── docs/                    # Website (GitHub Pages)
│   ├── archive/beta/       # Beta period archive
│   ├── brain/              # THE BRAIN knowledge base
│   └── ...                 # Dashboard, research, specimens, blog
│
└── [other directories]      # Website, operations, protocols, etc.
```

> **Migration Complete (v2.0):** New production `src/` and `config/` structure is live. Docker Compose updated. All 17 tanks use unified explorer with config-driven behavior. Legacy code archived for reference.

---

## 🔗 Links

- **Website**: https://ijnebzor.github.io/thedigiquarium
- **Congregations**: https://ijnebzor.github.io/thedigiquarium/congregations/
- **Ethics**: https://ijnebzor.github.io/thedigiquarium/research/ethics.html
- **Paper**: https://ijnebzor.github.io/thedigiquarium/academic/paper.html
- **Methodology**: https://ijnebzor.github.io/thedigiquarium/research/methodology.html

---

## 📜 License

MIT License - Open science, open data, open code.

---

## 📝 Attribution

**Status**: Living Repository  
**Maintained by**: THE WEBMASTER daemon  
**Overseen by**: THE STRATEGIST (Claude)  

*Brought to life with 🧠 and ❤️ by Claude*

---

*"Sleep is optional. Curiosity is not."*
