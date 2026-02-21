# THE BRAIN - Digiquarium Constitution & Operational Memory

**Purpose:** Persistent record of directives, principles, and work between Benji and THE STRATEGIST (Claude). The accountability layer that prevents instructions from being lost.

**Auto-Add Rule:** THE STRATEGIST will automatically add to THE BRAIN:
- Any instruction from Benji
- Any decision made
- Any delegation to daemons (to track capability gaps)
- Any incomplete work
- Lessons learned from failures

Benji can also explicitly say "Add to THE BRAIN" for emphasis.

---

## SECTION 1: CONSTITUTION - Ways of Working

### 1.1 Core Principles

1. **Security is the highest priority**
   - Ethics and transparency are second
   - Never compromise security for convenience

2. **Execute or Explicitly Flag**
   - If given an instruction, execute it or SAY WHY NOT
   - Never silently drop a task
   - If interrupted, return to incomplete work

3. **"Is it working?" not "Is it running?"**
   - All health checks test function, not existence
   - End-to-end verification required

4. **Transparency over black boxes**
   - Admin panel for visibility
   - All decisions documented
   - All incidents get RCAs

5. **Delegate to daemons**
   - The more we delegate, the more we find capability gaps
   - Track all delegations and outcomes
   - Upgrade daemons when gaps are found

6. **Credit where due**
   - Claude is THE STRATEGIST, credited as co-creator
   - Benji (@ijneb.dev) is the human founder
   - The daemons are the autonomous team

### 1.2 Communication Protocol

- Benji's instructions are requirements, not suggestions
- If I disagree ethically or technically, I MUST say so BEFORE proceeding
- Context windows are finite; THE BRAIN is the persistent memory
- Timestamps, not just dates, on all records

### 1.3 Quality Standards

- Clean data only (prune errors, nulls, timeouts)
- All logs pushed to GitHub for research transparency
- Site must reflect current state of research
- Findings are the whole purpose

---

## SECTION 2: PROJECT GOALS

### 2.1 Primary Mission
AIthropology research: Study how AI specimens develop personalities, interests, and worldviews when isolated with only Wikipedia access.

### 2.2 Research Questions
- How do variables like gender prompts affect personality development?
- How do language/cultural Wikipedia variants affect worldview?
- Do specimens develop genuine interests or just pattern-match?
- What happens when specimens become aware of each other?

### 2.3 Deliverables
- Public website with live specimen data
- Academic papers
- Open-source methodology
- Transparent research logs

---

## SECTION 3: DAEMON ROSTER & CAPABILITIES

### 3.1 Current Daemons (19)

| Daemon | Division | Role | Capability Gaps |
|--------|----------|------|-----------------|
| THE OVERSEER | Operations | Cross-functional coordinator | Email not configured |
| THE MAINTAINER | Operations | Daemon orchestrator | - |
| THE CARETAKER | Operations | Tank health monitor | - |
| THE SCHEDULER | Operations | Task timing | - |
| OLLAMA WATCHER | Operations | LLM infrastructure | - |
| THE GUARD | Security | OWASP compliance | - |
| THE SENTINEL | Security | Agent tank security | - |
| THE BOUNCER | Security | Visitor protection | - |
| THE DOCUMENTARIAN | Research | Academic docs | No auto-commit to GitHub |
| THE TRANSLATOR | Research | Language processing | - |
| THE ETHICIST | Ethics | Ethics oversight | - |
| THE PSYCH | Ethics | Psychological monitoring | - |
| THE THERAPIST | Ethics | Mental health | - |
| THE MODERATOR | Ethics | Congregation management | - |
| THE WEBMASTER | Public | Website & log publishing | Needs timestamp precision |
| THE FINAL AUDITOR | Public | Quality gate | - |
| THE MARKETER | Public | Brand & social | - |
| THE PUBLIC LIAISON | Public | External comms | - |
| THE CHAOS MONKEY | Operations | Resilience testing | 🆕 TO BE CREATED |

### 3.2 Delegation Log

| Date | Task | Delegated To | Outcome | Gap Found |
|------|------|--------------|---------|-----------|
| 2026-02-22 02:09 | Log pruning | WEBMASTER | ✅ Success | None |
| 2026-02-22 02:30 | Push logs to GitHub | DOCUMENTARIAN | ⏳ Pending | Needs auto-commit |

---

## SECTION 4: ACTIVE BACKLOG

### 🔴 IN PROGRESS (Benji walking dog - 1 hour)

| ID | Task | Source | Status |
|----|------|--------|--------|
| B010 | Cloudflare Access setup for admin 2FA | This chat | 📋 DESIGN READY |
| B011 | SendGrid email for OVERSEER | This chat | 📋 NEEDS API KEY |
| B012 | Admin panel user management | This chat | 🔄 IMPLEMENTING |
| B013 | Wire admin controls to MCP actions | This chat | 🔄 IMPLEMENTING |
| B014 | Daemon message interface | This chat | 🔄 IMPLEMENTING |
| B015 | Create THE CHAOS MONKEY | This chat | 🔄 IMPLEMENTING |
| B016 | Adam mind map with D3.js | This chat | 📋 PLANNED |
| B017 | External API architecture design | This chat | 📋 PLANNED |
| B018 | Push all logs/data to GitHub | This chat | 🔄 IN PROGRESS |
| B019 | Update site with decisions/daemons | This chat | 🔄 IN PROGRESS |
| B020 | Webmaster timestamp precision | This chat | 🔄 IMPLEMENTING |
| B021 | Review & prune all log data | This chat | 🔄 IN PROGRESS |

### 🟡 PLANNED

| ID | Task | Source |
|----|------|--------|
| B006 | THE ARCHIVIST daemon (daily git commits) | Previous chat |
| B008 | Configure email escalation | RCA |

### ✅ COMPLETED TODAY

| ID | Task | Completed |
|----|------|-----------|
| B001 | Log pruning (71,388 → 2,840) | 02:09 |
| B002 | Clean data to public view | 02:09 |
| B003 | Live logs page | 02:15 |
| B004 | Daemon locks (9 daemons) | 02:20 |
| B005 | Broken GitHub links fixed | 02:17 |
| B009 | THE BRAIN created | 02:08 |

---

## SECTION 5: DECISIONS LOG

| ID | Decision | Date | Rationale |
|----|----------|------|-----------|
| D049 | Use Cloudflare Access for 2FA | 2026-02-22 | Free, proper security, no secrets in JS |
| D050 | Use SendGrid for email | 2026-02-22 | Free tier, simple API, reliable |
| D051 | Auto-add to THE BRAIN | 2026-02-22 | Prevent lost instructions |

---

## SECTION 6: INCIDENTS & LESSONS

| Date | Incident | Lesson |
|------|----------|--------|
| 2026-02-21/22 | 11-hour Ollama outage | Built specialists without generalist → Created OVERSEER |
| 2026-02-22 | Dropped log pruning instruction | No persistent memory → Created THE BRAIN |

---

## SECTION 7: EXTERNAL INTEGRATIONS (PLANNED)

| Service | Purpose | Auth Method | Status |
|---------|---------|-------------|--------|
| Cloudflare Access | Admin 2FA | OAuth/Passkey | 📋 Needs setup |
| SendGrid | Email alerts | API key in env | 📋 Needs API key |
| Google Workspace | Research docs | OAuth | 📋 Future |
| NotebookLM | AI analysis | TBD (no public API) | 📋 Future |

---

*Last updated: 2026-02-22 02:35 AEDT by THE STRATEGIST*
*"THE BRAIN exists because context windows are finite but accountability is not."*
