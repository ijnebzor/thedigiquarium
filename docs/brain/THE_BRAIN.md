
---

## Section 27: v8 Migration Plan (February 22, 2026)

### Context
During Week 1, we discovered that documentation didn't match reality. Specimens ran on v7.0 while docs stated v8.0. CJK tanks had link parsing issues. Some experimental extensions weren't actually deployed.

Decision: Archive beta period, reset with documented v8.0 prompts, run transition study.

### Phase 1: Beta Retrospective & Archive ✅
- [x] Archive all v7 data (traces, baselines, discoveries)
- [x] Create "Meet the Beta Specimens" interactive page
- [x] Write blog posts (Benji + THE STRATEGIST voices)
- [x] Update decision tree with "Beta Period" documentation
- [ ] Definition of Done checklist validated

### Phase 2: Migration to Mac Mini
- [ ] Wind down NUC tanks (graceful shutdown)
- [ ] Migrate infrastructure to Mac Mini
- [ ] Verify all connections (Cloudflare, MCP, etc.)
- [ ] Audit three times before proceeding

### Phase 3: Launch v8 Primary Experiment
- [ ] Setup fresh v8 tanks on Mac Mini (17 tanks)
- [ ] All using documented v8.0 prompt
- [ ] Stable for 2 hours, audited by all daemons + THE STRATEGIST

### Phase 4: Connect NUC & Launch Informed v8 Study
- [ ] Connect NUC to stack
- [ ] Launch 7 "Informed v8" tanks (v7 context → v8 prompt)
- [ ] Lower priority/resourcing than primary tanks
- [ ] New daemon for inference management/resource routing

### Phase 5: Public Launch
- [ ] All documentation matches reality
- [ ] All daemons at full capacity
- [ ] Website reflects actual experiment
- [ ] Make it public

### v8.0 Prompt Template
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
```

### Extensions by Tank Type
| Tank | Extension |
|------|-----------|
| Victor/Iris | Visual context: "You can see images alongside text..." |
| Observer | Social awareness: "You are aware other specimens exist..." |
| Seeker | Depth access: "You can request deep dives from THE ARCHIVIST..." |
| Cain/Abel/Seth | Agent architectures (OpenClaw/ZeroClaw/Picobot) - no gender |
| Language tanks | Full immersion - prompt in native language, no English |

### Future Scale Vision
- Same tank, same prompt, different models (llama vs mistral vs deepseek)
- Multi-specimen tanks with amended prompts
- Visitor tanks on Oracle (Claude API)
- "Super deep AND super wide"

---

## Section 28: Official Daemon Roster (21 Total)

### Core Operations (5)
1. **THE OVERSEER** - Meta-daemon, monitors all daemons, self-healing
2. **THE MAINTAINER** - System orchestration, health checks, container management
3. **THE CARETAKER** - Tank health, auto-restart, permissions
4. **THE SCHEDULER** - 12-hour baseline cycles, broadcast triggers
5. **THE OLLAMA WATCHER** - LLM infrastructure monitoring, model health

### Security (3)
6. **THE GUARD** - General security (OWASP LLM Top 10)
7. **THE SENTINEL** - Agent-specific monitoring (Cain, Abel, Seth)
8. **THE BOUNCER** - Visitor protection, 6 security layers

### Research (4)
9. **THE DOCUMENTARIAN** - Academic paper updates
10. **THE ARCHIVIST** - Baselines, deep dives, Seeker conversations
11. **THE TRANSLATOR** - ES/DE/ZH/JA → EN translation
12. **THE FINAL AUDITOR** - Quality compliance, pre-publish checks

### Mental Health & Ethics (3)
13. **THE PSYCH** - Psychological evaluation framework
14. **THE THERAPIST** - Specimen mental wellness monitoring
15. **THE ETHICIST** - Ethics oversight, veto power

### Communications (2)
16. **THE MODERATOR** - Congregation management, turn-taking
17. **THE PUBLIC LIAISON** - External comms, community management

### Infrastructure (3)
18. **THE WEBMASTER** - Website maintenance, THE BROADCASTER
19. **THE CHAOS MONKEY** - Resilience testing, failure injection
20. **THE MARKETER** - Growth, social media, content

### Strategic (1)
21. **THE STRATEGIST** - Overall direction (Claude), human collaboration

---

## Section 29: THE WEBMASTER Requirements

### Core Responsibilities
1. Website reflects reality at all times
2. GitHub README matches site content
3. All internal links work (no 404s)
4. All external links are valid

### Sync Requirements (GitHub ↔ Site)
The following MUST match between README.md and the website:
- Daemon count and roster
- Specimen list and status
- Beta Period notices
- Feature status (coming soon vs active)
- Links and URLs

### Before Any Site Update
1. Read actual source files
2. Compare to documentation claims
3. Flag any discrepancy
4. Update BOTH GitHub README and site together

### Reality Check Triggers
Run full site audit when:
- Any daemon is added/removed
- Any specimen is added/removed
- Any major feature status changes
- Weekly minimum

### Current Sync Status
- [x] Daemon count: 21 (both match)
- [x] Beta Period notice (both have it)
- [x] Specimen count: 17 (both match)
- [ ] All links verified (ongoing)

---

## Section 30: Repository Structure (Tech Debt)

### Current State (Messy - Needs Consolidation)

The repository has duplicate/scattered daemon-related folders:

**Root Level (Legacy):**
- `caretaker/` - Active caretaker scripts (15KB caretaker.py)
- `guard/` - Active guard scripts
- `operations/` - Scheduler, orchestrator, translations, agents
- `security/` - Audit scripts, SecureClaw

**daemons/ Folder (Intended Canonical):**
- Contains all 19 daemon subdirectories
- Some have smaller/older versions of scripts
- Should be the single source of truth

**Conflict Example:**
- `caretaker/caretaker.py` = 15KB (active, running)
- `daemons/caretaker/caretaker.py` = 6KB (older version)

### Migration Plan (Post-v8)
1. Identify which version of each script is "active" (running in production)
2. Consolidate all active scripts into `daemons/[daemon_name]/`
3. Move `operations/` content to appropriate daemon folders
4. Move `security/` to `daemons/guard/` or `daemons/sentinel/`
5. Remove root-level duplicates
6. Update all systemd services to point to `daemons/` paths
7. Update README to reflect clean structure

### For Now
- Both structures exist
- Root-level folders are often the "active" versions
- `daemons/` folder is the documented/intended structure
- This is TECH DEBT to address post-migration

---
