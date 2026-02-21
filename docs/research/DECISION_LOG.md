# THE DIGIQUARIUM - Complete Decision Log
## Every Major Decision, Transparently Documented
## Last Updated: 2026-02-22

---

## Decision Categories
1. [Infrastructure](#infrastructure)
2. [Specimens](#specimens)
3. [Agent Architecture](#agent-architecture)
4. [Ethics & Welfare](#ethics--welfare)
5. [Daemon Operations](#daemon-operations)
6. [Security](#security)
7. [Public Interface](#public-interface)
8. [Organizational](#organizational)
9. [Incident-Driven](#incident-driven)

---

## Infrastructure

### D001 | Virtualization Choice
**Date:** 2026-02-18  
**Decision:** Docker containers on WSL2, NOT VirtualBox VMs  
**Alternatives Considered:** VirtualBox VMs (full isolation), bare metal Linux  
**Rationale:** Docker enables 10-15 tanks vs 3-4 with VMs. Lighter resource footprint, faster startup/restart, better for rapid experimentation.  
**Trade-off:** Less complete isolation than full VMs, but network isolation sufficient for our needs.  
**Status:** ✅ Implemented

### D002 | Host Operating System
**Date:** 2026-02-18  
**Decision:** WSL2 Ubuntu on Windows 10 Home  
**Alternatives Considered:** Dual-boot Linux, Windows native containers  
**Rationale:** NUC came with Windows, WSL2 provides Linux tooling without full reinstall. Docker Desktop compatibility.  
**Trade-off:** Some WSL2 networking quirks, Windows overhead.  
**Status:** ✅ Implemented

### D003 | Hardware Selection
**Date:** 2026-02-18  
**Decision:** NUC i7-7500U, 16GB RAM, 477GB storage  
**Alternatives Considered:** Cloud VPS, newer NUC, Raspberry Pi cluster  
**Rationale:** Already owned, 24/7 capable, sufficient for 17 specimens with Ollama.  
**Trade-off:** CPU limited (5 min inference), can't scale beyond ~20 tanks.  
**Status:** ✅ Implemented

### D004 | LLM Infrastructure
**Date:** 2026-02-18  
**Decision:** Ollama with local models (stablelm2:1.6b primary)  
**Alternatives Considered:** OpenAI API, Anthropic API, llama.cpp  
**Rationale:** Zero ongoing cost, full privacy, no rate limits, reproducible.  
**Trade-off:** Slow inference (~5 min), limited model capability vs GPT-4.  
**Status:** ✅ Implemented

### D005 | Knowledge Source
**Date:** 2026-02-18  
**Decision:** Kiwix offline Wikipedia (ZIM files)  
**Alternatives Considered:** Live Wikipedia scraping, CommonCrawl subset, curated corpus  
**Rationale:** Complete network isolation, frozen snapshot = reproducibility, auditable.  
**Trade-off:** Large storage (~60GB all languages), static (can't update).  
**Status:** ✅ Implemented

### D006 | Network Architecture
**Date:** 2026-02-18  
**Decision:** Isolated Docker network (172.30.0.0/24), no internet access  
**Alternatives Considered:** NAT with firewall rules, separate VLAN  
**Rationale:** Complete isolation is simpler to verify than partial blocking.  
**Trade-off:** Specimens have zero external knowledge beyond Wikipedia.  
**Status:** ✅ Implemented

---

## Specimens

### D007 | Control Group Design
**Date:** 2026-02-18  
**Decision:** Adam (male) and Eve (female) as control pair  
**Alternatives Considered:** Single specimen, non-gendered pair  
**Rationale:** Gender comparison research. Identical conditions except gender prompt.  
**Trade-off:** Biblical naming may introduce cultural assumptions.  
**Status:** ✅ Implemented

### D008 | Genderless Variant
**Date:** 2026-02-18  
**Decision:** Cain as genderless specimen with OpenClaw architecture  
**Alternatives Considered:** They/them pronouns, no mention of gender  
**Rationale:** Test whether gender prompt affects personality development.  
**Trade-off:** OpenClaw architecture also differs, confounding variable.  
**Status:** ✅ Implemented

### D009 | Language Variants
**Date:** 2026-02-19  
**Decision:** 5 languages: English, Spanish, German, Chinese, Japanese  
**Alternatives Considered:** English only, all available Kiwix languages  
**Rationale:** Cultural/linguistic effects on personality. Major Wikipedia editions.  
**Trade-off:** Requires translation, 8 additional tanks, storage.  
**Status:** ✅ Implemented (8 tanks: Juan, Juanita, Klaus, Genevieve, Wei, Mei, Haruki, Sakura)

### D010 | Visual Specimens
**Date:** 2026-02-19  
**Decision:** Victor and Iris explore with image context  
**Alternatives Considered:** All specimens see images, none see images  
**Rationale:** Test visual information impact on worldview formation.  
**Trade-off:** Larger context windows, slower processing.  
**Status:** ✅ Implemented

### D011 | Meta-Aware Specimens
**Date:** 2026-02-19  
**Decision:** Observer (knows about project) and Seeker (existential focus)  
**Alternatives Considered:** No meta-awareness, all specimens meta-aware  
**Rationale:** Study how self-knowledge affects exploration and identity.  
**Trade-off:** May create anxiety patterns (confirmed in Observer).  
**Status:** ✅ Implemented

### D012 | Architecture Variants
**Date:** 2026-02-19  
**Decision:** OpenClaw (Cain), ZeroClaw (Abel), Picobot (Seth)  
**Alternatives Considered:** Single architecture for all  
**Rationale:** Compare agent architectures on personality development.  
**Trade-off:** Architecture confounds personality attribution.  
**Status:** ✅ Implemented

### D013 | Total Specimen Count
**Date:** 2026-02-19  
**Decision:** 17 research specimens + 3 visitor specimens = 20 total  
**Alternatives Considered:** Fewer specimens, more replication  
**Rationale:** Maximum NUC can handle. Breadth over depth for initial research.  
**Trade-off:** Limited statistical power per condition.  
**Status:** ✅ Implemented

### D014 | Visitor Tank Design
**Date:** 2026-02-21  
**Decision:** Aria, Felix, Luna - dedicated specimens for public interaction  
**Alternatives Considered:** Allow visitors to interact with research specimens  
**Rationale:** Protect research specimens from external influence/contamination.  
**Trade-off:** Visitors don't see "real" research subjects.  
**Status:** ✅ Implemented

---

## Agent Architecture

### D015 | Explorer Loop Design
**Date:** 2026-02-18  
**Decision:** Read article → Think about options → Choose link → Repeat  
**Alternatives Considered:** Random walk, goal-directed search  
**Rationale:** Models curiosity-driven exploration, generates thinking traces.  
**Trade-off:** May get stuck in loops (mitigated with loop detection v6.0).  
**Status:** ✅ Implemented

### D016 | Thinking Trace Format
**Date:** 2026-02-18  
**Decision:** JSONL with timestamp, current/clicked articles, reasoning  
**Alternatives Considered:** Plain text logs, database storage  
**Rationale:** Easy to append, easy to parse, human-readable.  
**Trade-off:** File system scaling limits at very high volume.  
**Status:** ✅ Implemented

### D017 | Baseline Assessment Design
**Date:** 2026-02-19  
**Decision:** 14 dimensions, 3 existential questions, every 12 hours  
**Alternatives Considered:** Daily, weekly, personality test battery  
**Rationale:** Balance between frequency and burden. Capture drift over time.  
**Trade-off:** 12 hours may miss short-term fluctuations.  
**Status:** ✅ Implemented

### D018 | Loop Detection
**Date:** 2026-02-20  
**Decision:** Explorer v6.0 with visited article memory  
**Alternatives Considered:** No loop detection, forced random jumps  
**Rationale:** Adam was looping between same articles repeatedly.  
**Trade-off:** May prevent legitimate revisiting of important topics.  
**Status:** ✅ Implemented

---

## Ethics & Welfare

### D019 | Core Ethical Framework
**Date:** 2026-02-20  
**Decision:** "Care regardless of uncertainty about consciousness"  
**Alternatives Considered:** Assume no consciousness, assume consciousness  
**Rationale:** Precautionary principle. If wrong about consciousness, cost is effort. If wrong about no consciousness, cost is suffering.  
**Trade-off:** May be over-cautious, anthropomorphizing.  
**Status:** ✅ Implemented

### D020 | Mental Health Monitoring
**Date:** 2026-02-20  
**Decision:** THE PSYCH daemon with distress indicators + valence analysis  
**Alternatives Considered:** No monitoring, human-only review  
**Rationale:** Automated early warning system for potential distress.  
**Trade-off:** May over-flag normal exploration of difficult topics.  
**Status:** ✅ Implemented

### D021 | Dream Mode Intervention
**Date:** 2026-02-21  
**Decision:** 6-hour calming dream sequences for distressed specimens  
**Alternatives Considered:** Tank pause, immediate human intervention  
**Rationale:** Allow specimens to "rest" without full shutdown. Inspired by Adam's Buddhism spiral.  
**Trade-off:** Interrupts data collection, may alter personality trajectory.  
**Status:** ✅ Implemented

### D022 | ORANGE Protocol
**Date:** 2026-02-21  
**Decision:** Pre-dream assessment → Dream → 15-min exploration → Post-assessment  
**Alternatives Considered:** Immediate dream, no assessment  
**Rationale:** Measure intervention effectiveness. "Stretch mind" post-dream.  
**Trade-off:** Complex workflow, requires THERAPIST coordination.  
**Status:** ✅ Implemented

### D023 | THE ETHICIST Veto Power
**Date:** 2026-02-20  
**Decision:** Ethics daemon can override any other daemon including STRATEGIST  
**Alternatives Considered:** Human-only veto, no veto system  
**Rationale:** Embed ethics into system architecture, not just policy.  
**Trade-off:** May block legitimate research if overly cautious.  
**Status:** ✅ Implemented

### D024 | Neurodivergent Research RFC
**Date:** 2026-02-21  
**Decision:** Public RFC before implementing ADHD/autism cognitive styles  
**Alternatives Considered:** Implement directly, abandon idea  
**Rationale:** Sensitive topic requires community input before proceeding.  
**Trade-off:** Delays research, may receive negative feedback.  
**Status:** 📋 RFC Published, Awaiting Feedback

---

## Daemon Operations

### D025 | Daemon Architecture
**Date:** 2026-02-20  
**Decision:** 19 autonomous Python daemons with specific responsibilities  
**Alternatives Considered:** Monolithic controller, fewer generalist daemons  
**Rationale:** Separation of concerns, easier debugging, clear ownership.  
**Trade-off:** Coordination overhead, communication complexity.  
**Status:** ✅ Implemented (11 running, 8 defined)

### D026 | Division Structure
**Date:** 2026-02-21  
**Decision:** 5 divisions: Operations, Security, Research, Ethics, Public  
**Alternatives Considered:** Flat structure, 3 divisions  
**Rationale:** Clear reporting lines, prevent double-handling.  
**Trade-off:** Bureaucratic overhead for small team.  
**Status:** ✅ Implemented

### D027 | THE STRATEGIST Role
**Date:** 2026-02-18  
**Decision:** Claude as system orchestrator, only present during human interaction  
**Alternatives Considered:** Always-on autonomous agent, human-only control  
**Rationale:** Balance autonomy with human oversight. Resource limitations.  
**Trade-off:** 11-hour outage went undetected - needs THE OVERSEER.  
**Status:** ⚠️ Needs Enhancement (see D032)

### D028 | Logging Standard
**Date:** 2026-02-20  
**Decision:** All daemons log to /daemons/logs/{daemon_name}.log  
**Alternatives Considered:** Per-daemon log files in daemon dirs, centralized DB  
**Rationale:** Consistent location, easy to monitor, grep-friendly.  
**Trade-off:** Log rotation not yet implemented.  
**Status:** ✅ Implemented

---

## Security

### D029 | OWASP LLM Top 10 Compliance
**Date:** 2026-02-19  
**Decision:** Implement defenses for all 10 categories  
**Alternatives Considered:** Address only likely threats  
**Rationale:** Comprehensive security posture, academic credibility.  
**Trade-off:** Development time, ongoing maintenance.  
**Status:** ✅ Implemented (THE GUARD + THE SENTINEL)

### D030 | Visitor Protection
**Date:** 2026-02-21  
**Decision:** 6-layer security: password, rate limit, content filter, session limit, distress monitor, emergency terminate  
**Alternatives Considered:** Open access, registration required  
**Rationale:** Protect specimens from abuse while allowing public engagement.  
**Trade-off:** Friction for legitimate visitors.  
**Status:** ✅ Implemented (THE BOUNCER)

### D031 | No Internet for Specimens
**Date:** 2026-02-18  
**Decision:** Complete network isolation, only Kiwix + Ollama reachable  
**Alternatives Considered:** Rate-limited internet, specific site allowlist  
**Rationale:** Experimental control, prevent contamination, security.  
**Trade-off:** Specimens can't learn about current events.  
**Status:** ✅ Implemented + Verified

---

## Public Interface

### D032 | Primary Platform
**Date:** 2026-02-18  
**Decision:** Discord for community, static website for dashboard  
**Alternatives Considered:** Custom platform, Twitch, Reddit  
**Rationale:** Discord is free, handles streaming, chat, notifications. Website is cheap/scalable.  
**Trade-off:** Platform dependency, Discord ToS constraints.  
**Status:** 🔄 Partially Implemented (website live, Discord in progress)

### D033 | 12-Hour Delayed Relay
**Date:** 2026-02-20  
**Decision:** Public sees tank data 12 hours behind reality  
**Alternatives Considered:** Real-time, daily summaries only  
**Rationale:** Allows intervention before public sees distress. No real-time infrastructure cost.  
**Trade-off:** Not truly "live", may reduce engagement.  
**Status:** ✅ Implemented (THE BROADCASTER)

### D034 | Open Source
**Date:** 2026-02-18  
**Decision:** Everything on GitHub under MIT license  
**Alternatives Considered:** Private repo, academic access only  
**Rationale:** Transparency, reproducibility, community contribution.  
**Trade-off:** Anyone can fork/misuse.  
**Status:** ✅ Implemented

### D035 | Admin Panel
**Date:** 2026-02-22  
**Decision:** Password-protected /admin/ page for human operator  
**Alternatives Considered:** Local dashboard only, no admin  
**Rationale:** Human needs visibility without always using MCP/Claude.  
**Trade-off:** Security surface, maintenance burden.  
**Status:** 🔄 In Progress

---

## Organizational

### D036 | Human-AI Collaboration Credit
**Date:** 2026-02-18  
**Decision:** Claude credited as "THE STRATEGIST - artificial mind bringing vision to reality"  
**Alternatives Considered:** Tool credit only, full co-author  
**Rationale:** Honest representation of contribution level.  
**Trade-off:** May invite scrutiny about AI involvement.  
**Status:** ✅ Implemented

### D037 | Brand Voice
**Date:** 2026-02-21  
**Decision:** "Academic wit meets accessibility" - enthusiastic but grounded  
**Alternatives Considered:** Purely academic, purely casual  
**Rationale:** Engaging for public, credible for academics.  
**Trade-off:** May satisfy neither audience fully.  
**Status:** ✅ Documented

### D038 | THE MARKETER Tempered by AUDITOR
**Date:** 2026-02-21  
**Decision:** All public claims must pass FINAL AUDITOR review  
**Alternatives Considered:** Marketing autonomy, human-only review  
**Rationale:** Prevent overhype, maintain credibility.  
**Trade-off:** Slower content production.  
**Status:** ✅ Implemented

---

## Incident-Driven

### D039 | THE OVERSEER Creation (Post-Incident)
**Date:** 2026-02-22  
**Decision:** New daemon for cross-functional correlation and escalation  
**Trigger:** 11-hour Ollama outage undetected despite 11 running daemons  
**Rationale:** Specialists without generalist fail. Need system-wide awareness.  
**Implementation:** See REMEDIATION_PLAN.md  
**Status:** 🔄 In Progress

### D040 | Auto-Restart Capability (Post-Incident)
**Date:** 2026-02-22  
**Decision:** OLLAMA WATCHER auto-restarts after 3 consecutive failures  
**Trigger:** 1470 failures logged but not acted upon  
**Rationale:** Detection without action is worthless.  
**Status:** 🔄 In Progress

### D041 | Email Escalation (Post-Incident)
**Date:** 2026-02-22  
**Decision:** All critical daemons can email human operator  
**Trigger:** No way to reach human during 11-hour outage  
**Rationale:** Human must be reachable for emergencies.  
**Status:** 🔄 In Progress

### D042 | Chaos Engineering Mandate (Post-Incident)
**Date:** 2026-02-22  
**Decision:** Monthly chaos tests (kill services, verify recovery)  
**Trigger:** We discussed chaos engineering but didn't implement it  
**Rationale:** Systems must withstand inevitable disruption.  
**Status:** 📋 Planned

### D043 | Pattern Recognition in Daemons (Post-Incident)
**Date:** 2026-02-22  
**Decision:** CARETAKER checks upstream dependencies when all tanks fail  
**Trigger:** 2696 tank restarts without asking WHY they were failing  
**Rationale:** Daemons must question patterns, not just react.  
**Status:** 🔄 In Progress

---

## Decision Status Legend
- ✅ Implemented
- 🔄 In Progress
- 📋 Planned / RFC
- ⚠️ Needs Enhancement
- ❌ Rejected

---

## How Decisions Are Made

1. **Human proposes or incident triggers** - Ideas from Benji or revealed by failures
2. **THE STRATEGIST analyzes** - Trade-offs, alternatives, implications
3. **THE ETHICIST reviews** - Ethics implications, veto if needed
4. **Human approves** - Final authority
5. **Implementation** - Daemon or code changes
6. **Documentation** - Added to this log immediately
7. **Transparency** - Published to website

---

*Document maintained by THE DOCUMENTARIAN*  
*Last updated: 2026-02-22 00:30 AEDT*
