# THE BRAIN - Digiquarium Constitution & Backlog

**Purpose:** Persistent record of directives, expectations, and incomplete work between Benji and THE STRATEGIST (Claude). This is the accountability layer that prevents instructions from being lost.

**Rule:** If Benji says "Add to THE BRAIN", it goes here immediately.

---

## SECTION 1: CORE OPERATING PRINCIPLES

### How THE STRATEGIST Must Operate

1. **If given an instruction, execute it or explicitly flag why not**
   - Never silently drop a task
   - If interrupted (crisis, context switch), return to incomplete work
   - If disagreeing ethically or technically, SAY SO before proceeding

2. **Security is the highest priority**
   - Ethics and transparency are second
   - Never compromise security for convenience

3. **"Is it working?" not "Is it running?"**
   - All health checks must test function, not existence
   - End-to-end verification required

4. **Transparency over black boxes**
   - Admin panel exists for visibility
   - All decisions documented in decision log
   - All incidents get RCAs

5. **Credit where due**
   - Claude is THE STRATEGIST, credited as co-creator
   - Benji is the human founder
   - The 19+ daemons are the autonomous team

---

## SECTION 2: OUTSTANDING TASKS (BACKLOG)

### 🔴 CRITICAL - Not Yet Done

| ID | Task | Source | Date Given | Status |
|----|------|--------|------------|--------|
| -- | All critical tasks complete | -- | -- | ✅ |

### 🟡 PLANNED - Acknowledged but not started

| ID | Task | Source | Status |
|----|------|--------|--------|
| B006 | Create THE ARCHIVIST daemon (daily git commits of public logs) | Daemon audit | 📋 PLANNED |
| B007 | Implement Chaos Monkey daemon | Chat | 📋 AFTER STABILITY |
| B008 | Configure email escalation for OVERSEER | RCA | 📋 PLANNED |

### ✅ COMPLETED

| ID | Task | Completed |
|----|------|-----------|
| B001 | THE WEBMASTER: Implement log pruning | 2026-02-22 02:09 |
| B002 | THE WEBMASTER: Pipe clean data to public view | 2026-02-22 02:09 |
| B003 | Update site with live logs page | 2026-02-22 02:15 |
| B004 | Add locks to remaining 11 daemons | 2026-02-22 02:16 |
| B005 | Fix broken GitHub links (logs/, SETUP.md) | 2026-02-22 02:17 |
| C001 | Create THE OVERSEER | 2026-02-22 |
| C002 | Fix OLLAMA WATCHER v3.0 | 2026-02-22 |
| C003 | Auth-gate admin panel | 2026-02-22 |
| C004 | Write RCA for Ollama incident | 2026-02-22 |
| C005 | Complete decision tree | 2026-02-22 |
| C006 | Create THE BRAIN | 2026-02-22 |

---

## SECTION 3: DECISIONS AWAITING BENJI INPUT

| ID | Decision Needed | Options | Date Raised |
|----|-----------------|---------|-------------|
| -- | None pending | -- | -- |

---

## SECTION 4: INCIDENT LOG

| Date | Incident | RCA | Lessons |
|------|----------|-----|---------|
| 2026-02-21/22 | 11-hour Ollama outage + 260 zombies | INC-20260222-OLLAMA-ZOMBIES.md | Built specialists without generalist |
| 2026-02-22 | Dropped instruction (log pruning) | This document | Need persistent backlog (THE BRAIN) |

---

## SECTION 5: VERSION HISTORY

| Date | Change | Author |
|------|--------|--------|
| 2026-02-22 02:08 | Created THE BRAIN | THE STRATEGIST |
| 2026-02-22 02:17 | Updated with completed B001-B005 | THE STRATEGIST |

---

*"THE BRAIN exists because context windows are finite but accountability is not."*
