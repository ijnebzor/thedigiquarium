# Daemon → OpenFang Hand Mapping

## Current: 21 Python Daemons (5 departments, ~9,500 LOC)

### Core Department (4 daemons)
| Daemon | Lines | Purpose | OpenFang Hand |
|--------|-------|---------|---------------|
| Overseer | 754 | Cross-functional ops coordinator | **Kernel Scheduler** — native to OpenFang. RBAC, workflow orchestration. |
| Scheduler | 735 | Task orchestration, baseline execution, SLA | **Kernel Scheduler** — OpenFang has built-in scheduling with budget tracking. |
| Caretaker | 458 | Autonomous caretaker, tank health | **Collector Hand** (customised) — monitoring + health checks + auto-remediation. |
| Maintainer | 222 | Status reporter, health monitor | **Collector Hand** — same as caretaker, merge into one. |
| Ollama Watcher | 632 | LLM infra monitor with self-healing | **Custom Hand** — "Ollama Monitor" with circuit breakers. Or native OpenFang health endpoint monitoring. |

### Security Department (3 daemons)
| Daemon | Lines | Purpose | OpenFang Hand |
|--------|-------|---------|---------------|
| Guard | 824 | Security sentinel, anomaly detection | **OpenFang Security Layer** — 16 built-in security systems including prompt injection scanner, SSRF protection. Replace with native. |
| Sentinel | 211 | Agent tank security specialist | **OpenFang Security Layer** — merge with Guard. Agent-specific rules as OpenFang capability gates. |
| Bouncer | 783 | Visitor tank protection (input filtering, session mgmt) | **Custom Hand** — "Bouncer" with approval gates. Maps well to OpenFang's WASM sandbox for input validation. |

### Research Department (4 daemons)
| Daemon | Lines | Purpose | OpenFang Hand |
|--------|-------|---------|---------------|
| Archivist | 546 | Data storage, historical query engine | **Researcher Hand** — natively does cross-referencing and credibility evaluation. Add specimen data as knowledge source. |
| Documentarian | 544 | Academic documentation, paper management | **Researcher Hand** — same Hand, different skill. Paper generation as an OpenFang Skill. |
| Translator | 200 | Language processing for multi-lang tanks | **Custom Skill** — language detection and translation as an OpenFang Skill attached to Researcher Hand. |
| Final Auditor | 149 | Website quality gate | **Custom Skill** — site validation as a scheduled OpenFang task. Or use TinyFish via OpenFang. |

### Ethics Department (4 daemons)
| Daemon | Lines | Purpose | OpenFang Hand |
|--------|-------|---------|---------------|
| Ethicist | 530 | Ethical review, wellness assessment | **Custom Hand** — "Ethicist" with approval gates for new experiments. Maps to OpenFang's capability gates. |
| Therapist | 394 | Mental health monitoring | **Custom Hand** — merge with Ethicist. Wellness checks as a scheduled task within the Ethicist Hand. |
| Psych | 314 | Psychological monitoring | **Custom Hand** — merge with Ethicist+Therapist. One "Ethics & Wellness" Hand. |
| Moderator | 523 | Congregation management | **Custom Hand** — "Moderator" that runs congregations. Uses OpenFang's A2A (agent-to-agent) for debate coordination. |

### Infrastructure Department (5 daemons)
| Daemon | Lines | Purpose | OpenFang Hand |
|--------|-------|---------|---------------|
| Webmaster | 338 | Site infrastructure, auto-publishing | **Custom Skill** — git push + site build as an OpenFang scheduled task. |
| Broadcaster | 479 | Live feed export, dashboard data | **Custom Skill** — data pipeline as an OpenFang scheduled task. Could use OpenFang's 40 channel adapters for dashboard. |
| Marketer | 404 | (unknown purpose) | **Evaluate** — may not be needed. Check if it does anything useful. |
| Public Liaison | 325 | (unknown purpose) | **Evaluate** — may not be needed. |
| Chaos Monkey | 146 | Resilience testing | **Custom Skill** — fault injection as a scheduled OpenFang task. |

## Consolidation Plan

21 daemons → **7 OpenFang Hands + 5 Skills**

| OpenFang Hand | Replaces | Core Function |
|---------------|----------|---------------|
| **Kernel (native)** | Overseer, Scheduler | Orchestration, scheduling, RBAC |
| **Collector** | Caretaker, Maintainer, Ollama Watcher | Health monitoring, status, self-healing |
| **Researcher** | Archivist, Documentarian | Data analysis, paper generation, drift reports |
| **Ethicist** | Ethicist, Therapist, Psych | Wellness monitoring, ethical review, approval gates |
| **Bouncer** | Bouncer | Visitor tank protection, session management |
| **Moderator** | Moderator | Congregation management, debate coordination |
| **Guard** | Guard, Sentinel | Security monitoring, anomaly detection |

| OpenFang Skill | Replaces | Function |
|----------------|----------|----------|
| translator | Translator | Language processing |
| site-publish | Webmaster, Final Auditor | Site build + quality gate |
| live-feed | Broadcaster | Dashboard data pipeline |
| chaos-test | Chaos Monkey | Resilience testing |
| tinyfish-browse | (new) | Web browsing for experimental tanks |

## Migration Steps
1. Install OpenFang on Mac Mini
2. Create HAND.toml manifests for each Hand
3. Create SKILL.md files for each Skill
4. Port daemon logic into Hand system prompts + guardrails
5. Test each Hand independently
6. Migrate one department at a time (start with Infrastructure)
7. Verify parity before decommissioning Python daemons
8. Run parallel for 1 week before full cutover

## What Can Be Prepped NOW (before OpenFang install)
- Write all 7 HAND.toml manifests
- Write all 5 SKILL.md files
- Document each daemon's decision tree (what triggers what)
- Create test cases for each Hand (expected inputs → outputs)
- Map daemon config to OpenFang config format
