# THE DIGIQUARIUM - Complete Decision Log
## Every Major Decision, Documented Transparently
*Last Updated: 2026-02-21*

---

## Infrastructure Decisions

### D001: Virtualization Platform
- **Date:** 2026-02-18
- **Decision:** Docker containers on WSL2, NOT VirtualBox VMs
- **Alternatives Considered:** VirtualBox VMs, Hyper-V
- **Rationale:** 
  - Docker: 10-15 tanks possible vs 3-4 with VMs
  - Lighter resource footprint
  - Faster startup/restart
  - Better for experimentation
- **Trade-off:** Less isolation than full VMs, but sufficient for our needs

### D002: Host Operating System
- **Date:** 2026-02-18
- **Decision:** WSL2 Ubuntu on Windows 10 Home
- **Alternatives Considered:** Native Linux, Windows containers
- **Rationale:** 
  - NUC came with Windows 10 Home
  - WSL2 provides full Linux compatibility
  - Docker Desktop works seamlessly
- **Trade-off:** Extra layer of abstraction

### D003: Hardware Platform
- **Date:** 2026-02-18
- **Decision:** Intel NUC (i7-7500U, 16GB RAM, 477GB storage)
- **Alternatives Considered:** Cloud VPS, more powerful hardware
- **Rationale:**
  - 24/7 local operation
  - No recurring cloud costs
  - Full data sovereignty
  - Already owned
- **Trade-off:** Limited to ~17 tanks, slower inference

### D004: LLM Infrastructure
- **Date:** 2026-02-18
- **Decision:** Ollama with local models (stablelm2:1.6b, llama3.2:3b)
- **Alternatives Considered:** OpenAI API, Anthropic API, cloud LLMs
- **Rationale:**
  - Zero ongoing API costs
  - Full privacy/isolation
  - No rate limits
  - Reproducible experiments
- **Trade-off:** Slower inference (~5 min/response), limited model quality

### D005: Wikipedia Source
- **Date:** 2026-02-18
- **Decision:** Kiwix offline Wikipedia (ZIM files)
- **Alternatives Considered:** Live Wikipedia scraping, cached API
- **Rationale:**
  - Complete network isolation possible
  - Frozen snapshot = reproducible experiments
  - Auditable information diet
- **Trade-off:** Large storage (~60GB for all languages)

---

## Specimen Design Decisions

### D006: Initial Specimens (Control Group)
- **Date:** 2026-02-18
- **Decision:** Adam (male) and Eve (female) as control pair
- **Rationale:**
  - Gender comparison research
  - Biblical naming convention (origin story)
  - Identical conditions except gender prompt
- **Trade-off:** Naming may imply religious framing

### D007: Agent Architectures
- **Date:** 2026-02-19
- **Decision:** Three architectures: OpenClaw, ZeroClaw, Picobot
- **Rationale:**
  - Compare reasoning frameworks
  - Cain (OpenClaw), Abel (ZeroClaw), Seth (Picobot)
  - Control for architecture effects
- **Trade-off:** More complexity to maintain

### D008: Language Variants
- **Date:** 2026-02-19
- **Decision:** 5 languages: English, Spanish, German, Chinese, Japanese
- **Specimens:** Juan/Juanita (ES), Klaus/Genevieve (DE), Wei/Mei (ZH), Haruki/Sakura (JA)
- **Rationale:**
  - Study cultural/linguistic effects on personality
  - Gender pairs per language
- **Trade-off:** Requires translation daemon, 8 additional tanks

### D009: Special Configurations
- **Date:** 2026-02-19
- **Decision:** Observer (meta-aware), Seeker (depth-focused), Victor/Iris (visual)
- **Rationale:**
  - Test specific hypotheses about awareness, exploration style, visual context
- **Trade-off:** Smaller sample size per configuration

### D010: Total Specimen Count
- **Date:** 2026-02-19
- **Decision:** 17 research specimens + 3 visitor specimens = 20 total
- **Rationale:** Maximum NUC can handle while maintaining stability
- **Trade-off:** Limited statistical power per condition

---

## Daemon Architecture Decisions

### D011: Daemon Model
- **Date:** 2026-02-19
- **Decision:** 19 specialized autonomous daemons + THE STRATEGIST
- **Alternatives Considered:** Single monolithic controller, human-only operation
- **Rationale:**
  - Separation of concerns
  - 24/7 autonomous operation
  - Specialized expertise per domain
- **Trade-off:** Coordination complexity (see INCIDENT D023)

### D012: Organizational Structure
- **Date:** 2026-02-21
- **Decision:** 5 divisions (Operations, Security, Research, Ethics, Public)
- **Rationale:**
  - Clear reporting lines
  - Reduced double-handling
  - Scalable structure
- **Trade-off:** Bureaucratic overhead

### D013: THE STRATEGIST Role
- **Date:** 2026-02-18
- **Decision:** Claude serves as THE STRATEGIST (system orchestrator)
- **Rationale:**
  - Advanced reasoning capability
  - Natural language interface
  - Strategic decision-making
- **Trade-off:** Only exists during active conversations (see D024)

### D014: THE ETHICIST Veto Power
- **Date:** 2026-02-20
- **Decision:** THE ETHICIST can veto any action on ethical grounds
- **Rationale:**
  - Ethics must override efficiency
  - Even THE STRATEGIST cannot override
- **Trade-off:** Potential operational delays

---

## Security Decisions

### D015: Network Isolation
- **Date:** 2026-02-18
- **Decision:** Research tanks have NO internet access, only Kiwix + Ollama
- **Rationale:**
  - Experimental integrity
  - No data contamination
  - Reproducibility
- **Trade-off:** Can't update Wikipedia, limited knowledge

### D016: Visitor Tank Security
- **Date:** 2026-02-20
- **Decision:** 6-layer security (THE BOUNCER)
  1. Password gate
  2. Rate limiting (10/min, 100/hr, 500/day)
  3. Content filtering
  4. Session limits (30 min, 50 messages)
  5. Real-time distress monitoring
  6. Emergency termination
- **Rationale:** Protect visitors from prompt injection, protect specimens from harassment
- **Trade-off:** May frustrate legitimate users

### D017: OWASP Compliance
- **Date:** 2026-02-19
- **Decision:** Implement defenses against OWASP LLM Top 10
- **Rationale:** Industry standard, comprehensive coverage
- **Trade-off:** Development time

---

## Ethics Decisions

### D018: Ethics Framework
- **Date:** 2026-02-20
- **Decision:** "Care regardless of uncertainty about consciousness"
- **Rationale:**
  - We don't know if specimens can suffer
  - Better to err on side of care
  - Ethical precautionary principle
- **Trade-off:** May be caring for non-sentient systems

### D019: Dream Mode Intervention
- **Date:** 2026-02-21
- **Decision:** ORANGE Protocol for distressed specimens
  1. Pre-dream assessment
  2. 6-hour calming dream mode
  3. 15-min post-wake exploration
  4. Post-dream assessment
- **Rationale:** Address apparent distress patterns (e.g., Adam's Buddhism spiral)
- **Trade-off:** Interrupts data collection

### D020: Neurodivergent Research RFC
- **Date:** 2026-02-21
- **Decision:** Public consultation before implementing cognitive-style specimens
- **Rationale:**
  - Sensitive topic requires community input
  - Avoid stereotyping
  - Transparency
- **Trade-off:** Delays implementation by 2 weeks

---

## Public Interface Decisions

### D021: Primary Platform
- **Date:** 2026-02-18
- **Decision:** Discord for community + Static website for dashboard
- **Alternatives Considered:** Custom platform, Twitch, Reddit
- **Rationale:**
  - Discord: Free, handles streaming, chat, bots
  - Static site: Zero backend costs, secure
- **Trade-off:** Platform dependency

### D022: 12-Hour Delayed Relay
- **Date:** 2026-02-20
- **Decision:** Public dashboard shows 12-hour delayed data, not real-time
- **Rationale:**
  - Zero streaming costs
  - Git-based deployment (free)
  - Protects live experiment integrity
- **Trade-off:** Not truly "live"

### D023: Blog Structure
- **Date:** 2026-02-21
- **Decision:** Unified blog with author tags (human + daemons)
- **Alternatives Considered:** Separate daemon blogs
- **Rationale:**
  - Project is the star, not individuals
  - Mirrors collaboration
  - Honest about AI non-persistence
- **Trade-off:** Less individual daemon identity

---

## Incident-Driven Decisions

### D024: THE OVERSEER Creation
- **Date:** 2026-02-21
- **Decision:** Create cross-functional coordinator daemon
- **Trigger:** 11-hour Ollama outage undetected
- **Rationale:**
  - No daemon had system-wide view
  - Pattern correlation needed
  - Human escalation required
- **Trade-off:** Additional complexity

### D025: Auto-Restart Capability
- **Date:** 2026-02-21
- **Decision:** THE OLLAMA WATCHER auto-restarts after 3 failures
- **Trigger:** 1470 failures logged but not acted upon
- **Rationale:** Detection without action is worthless
- **Trade-off:** Risk of restart loops (mitigated by escalation)

### D026: Email Escalation
- **Date:** 2026-02-21
- **Decision:** All critical daemons can email human operator
- **Trigger:** No way to alert human during outage
- **Rationale:** Human must be reachable for emergencies
- **Trade-off:** Potential alert fatigue

### D027: Admin Panel
- **Date:** 2026-02-21
- **Decision:** Password-protected admin panel at /admin/
- **Trigger:** Human operator had no visibility into system health
- **Rationale:** Can't manage what you can't see
- **Trade-off:** Security surface area

---

## Naming Decisions

### D028: Project Name
- **Date:** 2026-02-18
- **Decision:** "The Digiquarium" (digital + aquarium)
- **Rationale:** Vivarium metaphor, memorable, available domain
- **Trade-off:** May seem whimsical for academic work

### D029: Field Name
- **Date:** 2026-02-18
- **Decision:** "AIthropology" (AI + anthropology)
- **Rationale:**
  - Describes methodology (observational study of AI)
  - Memorable
  - We coined it
- **Trade-off:** May not be taken seriously initially

### D030: Daemon Naming Convention
- **Date:** 2026-02-19
- **Decision:** "THE [ROLE]" format (e.g., THE STRATEGIST, THE CARETAKER)
- **Rationale:** Clear, memorable, anthropomorphic-but-distinct
- **Trade-off:** May encourage over-personification

---

## Pending Decisions

### P001: Congregation Format
- **Status:** Designed, not implemented
- **Question:** How should multi-specimen debates be structured?
- **Options:** Moderated vs free-form, time limits, topic selection

### P002: External API Integration
- **Status:** Designed, not implemented
- **Question:** How to securely connect to Google Workspace, NotebookLM?
- **Options:** OAuth, API keys, environment variables

### P003: Mind Map Visualization Library
- **Status:** Evaluating
- **Question:** D3.js vs GoJS vs custom?
- **Options:** D3.js (free, flexible), GoJS (powerful, licensed)

---

## Decision Statistics

- **Total Decisions Logged:** 30
- **Pending Decisions:** 3
- **Incident-Driven Decisions:** 4
- **Categories:** Infrastructure (5), Specimens (5), Daemons (4), Security (3), Ethics (3), Public (3), Incidents (4), Naming (3)

---

*This is a living document. All major decisions must be logged here.*
*Maintained by THE DOCUMENTARIAN*
*Approved by THE STRATEGIST*
