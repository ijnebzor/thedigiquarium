# THE BRAIN - Digiquarium Constitution & Operational Memory

**Purpose:** Persistent record of directives, principles, and work between Benji and THE STRATEGIST (Claude).

**Auto-Add Rule:** THE STRATEGIST automatically adds:
- Any instruction from Benji
- Any decision made  
- Any delegation to daemons (to track capability gaps)
- Any incomplete work
- Lessons learned from failures

---

## SECTION 1: CONSTITUTION - Ways of Working

### 1.1 Core Principles

1. **Security is the highest priority** (ethics/transparency second)
2. **Execute or explicitly flag** - Never silently drop tasks
3. **"Is it working?" not "Is it running?"** - Function over existence
4. **Transparency over black boxes** - Admin panel, decision logs, RCAs
5. **Delegate to daemons** - Reveals capability gaps
6. **Credit where due** - Claude is THE STRATEGIST, Benji is founder

### 1.2 Communication Protocol

- Benji's instructions are requirements, not suggestions
- If disagreeing, SAY SO before proceeding
- Timestamps, not just dates
- THE BRAIN is persistent memory

---

## SECTION 2: PROJECT GOALS

**Mission:** AIthropology research - study AI personality development in isolated Wikipedia environments.

**Deliverables:** Public website, academic papers, open-source methodology, transparent logs.

---

## SECTION 3: DAEMON ROSTER (20 Daemons)

| Division | Daemons |
|----------|---------|
| Operations | OVERSEER, MAINTAINER, CARETAKER, SCHEDULER, OLLAMA_WATCHER, CHAOS_MONKEY |
| Security | GUARD, SENTINEL, BOUNCER |
| Research | DOCUMENTARIAN, TRANSLATOR |
| Ethics | ETHICIST, PSYCH, THERAPIST, MODERATOR |
| Public | WEBMASTER, FINAL_AUDITOR, MARKETER, PUBLIC_LIAISON |

**New:** THE CHAOS MONKEY (resilience testing) - Created 2026-02-22

---

## SECTION 4: BACKLOG

### ✅ COMPLETED (2026-02-22 Session)

| Task | Time |
|------|------|
| THE BRAIN constitution | 02:08 |
| Log pruning (71,397 removed) | 02:09 |
| Admin panel (6 tabs) | 02:25 |
| THE CHAOS MONKEY daemon | 02:30 |
| Chat UI (Flask + scoped contexts) | 02:40 |
| Adam mind map (D3.js) | 02:45 |
| Admin API (wired controls) | 02:50 |
| Daemons page | 02:35 |
| All pushed to GitHub | 02:55 |

### 🟡 PENDING (Need Benji Input)

| Task | Blocker |
|------|---------|
| Cloudflare Access 2FA | Need Cloudflare account setup |
| SendGrid email | Need API key |
| Anthropic API key for Chat UI | Need key in .anthropic_key |

---

## SECTION 5: NEW COMPONENTS

### Chat UI (localhost:5000)
- Flask app with Anthropic API
- Scoped conversations (select daemon/tank)
- Real-time context loading
- Start: `cd ~/digiquarium/chat-ui && ./start.sh`

### Admin API (localhost:5001)  
- Wired controls for admin panel
- Actions: audit, prune_logs, push_github, restart_ollama, chaos_*
- Start: `python3 ~/digiquarium/chat-ui/admin_api.py`

### Adam Mind Map
- D3.js force-directed graph
- 100 nodes, 200 links
- Top interest: Buddhism (65 visits)
- Downloadable brain export

---

## SECTION 6: KEY LEARNINGS

**Delegation reveals capability gaps** - The more we delegate, the more we find what daemons need.

**Auto-add prevents lost tasks** - THE BRAIN catches everything.

---

*Last updated: 2026-02-22 02:55 AEDT*
