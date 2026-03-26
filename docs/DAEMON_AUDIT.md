# Daemon Capability Audit
**Date:** 2026-02-22  
**Author:** THE STRATEGIST  
**Trigger:** Missing log publishing functionality, pre-Chaos Monkey assessment

---

## Current Daemon Roster (21 Daemons)

### Operations Division
| Daemon | Role | Status | Single Instance | Key Gap |
|--------|------|--------|-----------------|---------|
| **THE OVERSEER** | Cross-functional coordinator | ✅ Running | ⚠️ 2 processes | NEW - needs lock fix |
| **THE MAINTAINER** | Daemon orchestrator | ✅ Running | ⚠️ 2 processes | Needs lock |
| **THE CARETAKER** | Tank health monitor | ✅ Running | ⚠️ 2 processes | Needs lock |
| **THE SCHEDULER** | Task timing | ✅ Running | ⚠️ 2 processes | Needs lock |
| **OLLAMA WATCHER** | LLM infrastructure | ✅ Running | ⚠️ 2 processes | Has lock, still duplicating? |

### Security Division  
| Daemon | Role | Status | Single Instance | Key Gap |
|--------|------|--------|-----------------|---------|
| **THE GUARD** | OWASP compliance, network | ✅ Running | ⚠️ 2 processes | Needs lock |
| **THE SENTINEL** | Agent tank security | ✅ Running | ⚠️ 2 processes | Needs lock |
| **THE BOUNCER** | Visitor protection | ✅ Running | ✅ 1 process | OK |

### Research Division
| Daemon | Role | Status | Single Instance | Key Gap |
|--------|------|--------|-----------------|---------|
| **THE DOCUMENTARIAN** | Academic docs | ✅ Running | ⚠️ 2 processes | **NO LOG PUBLISHING** |
| **THE TRANSLATOR** | Language processing | ✅ Running | ⚠️ 2 processes | Needs lock |

### Ethics Division
| Daemon | Role | Status | Single Instance | Key Gap |
|--------|------|--------|-----------------|---------|
| **THE ETHICIST** | Ethics oversight | ✅ Running | ✅ 1 process | OK |
| **THE PSYCH** | Psychological monitoring | ✅ Running | ⚠️ 2 processes | Needs lock |
| **THE THERAPIST** | Mental health | ✅ Running | ✅ 1 process | OK |
| **THE MODERATOR** | Congregation mgmt | ✅ Running | ✅ 1 process | OK |

### Public Division
| Daemon | Role | Status | Single Instance | Key Gap |
|--------|------|--------|-----------------|---------|
| **THE WEBMASTER** | Website infrastructure | ✅ Running | ⚠️ 2 processes | **BARELY FUNCTIONAL** |
| **THE FINAL AUDITOR** | Quality gate | ✅ Running | ⚠️ 2 processes | Needs lock |
| **THE MARKETER** | Brand & social | ✅ Running | ✅ 1 process | OK |
| **THE PUBLIC LIAISON** | External comms | ✅ Running | ✅ 1 process | OK |

---

## Critical Capability Gaps

### 🚨 GAP 1: No Log Publishing to GitHub
**Impact:** Research paper links to `/tree/main/logs` which 404s because logs are gitignored and never published.

**Missing Capability:**
- Auto-commit sample/sanitized logs to GitHub
- Prune old logs to keep repo size manageable
- Publish anonymized thinking traces for research transparency

**Who Should Own:** THE DOCUMENTARIAN or new ARCHIVIST daemon

---

### 🚨 GAP 2: THE WEBMASTER is Hollow
**Current Functionality:** Checks if 2 files exist. That's it.

**Missing Capability:**
- Link validation (404 detection)
- Auto-fix broken links
- Content freshness checks
- SEO optimization
- Sitemap generation
- Deploy coordination

**Who Should Own:** THE WEBMASTER (needs major upgrade)

---

### 🚨 GAP 3: Zombie Process Accumulation
**Impact:** 11 of 21 daemons showing duplicate processes

**Root Cause:** Single-instance locks not implemented consistently

**Fix Required:** Add `fcntl` locks to ALL daemons (like OLLAMA WATCHER v3.0)

---

### 🚨 GAP 4: No Admin Panel Authentication
**Impact:** Anyone can access /admin/ and see system internals

**Security Requirement:** Auth gate with password or token

---

## Recommended Actions Before Chaos Monkey

### Priority 1: Fix Zombie Leaks
Add single-instance locks to all 11 affected daemons.

### Priority 2: Auth Gate Admin Panel
Implement password protection for /admin/

### Priority 3: Upgrade THE WEBMASTER
Add link validation, 404 detection, content freshness.

### Priority 4: Create THE ARCHIVIST (New Daemon)
Responsibilities:
- Daily log export to `logs-public/` directory
- Sanitize sensitive data
- Auto-commit to GitHub
- Prune logs older than 30 days from public
- Keep full logs locally

### Priority 5: Then Chaos Monkey
Only after above is stable.

---

## Daemon Role Summary

| Division | Purpose | Daemons |
|----------|---------|---------|
| **Operations** | Keep systems running | OVERSEER, MAINTAINER, CARETAKER, SCHEDULER, OLLAMA_WATCHER |
| **Security** | Protect systems & specimens | GUARD, SENTINEL, BOUNCER |
| **Research** | Document & analyze | DOCUMENTARIAN, TRANSLATOR |
| **Ethics** | Welfare & oversight | ETHICIST, PSYCH, THERAPIST, MODERATOR |
| **Public** | External facing | WEBMASTER, FINAL_AUDITOR, MARKETER, PUBLIC_LIAISON |

---

*"We have 19 specialists but several are underperforming or missing critical capabilities."*
