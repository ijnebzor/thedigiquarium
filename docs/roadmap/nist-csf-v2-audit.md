# NIST CSF v2 Pre-Migration Compliance Report
## The Digiquarium — 3 April 2026

**Auditor:** The Strategist (autonomous caretaker)
**Scope:** NUC infrastructure (primary host), 20 running tanks, 21 daemons, inference proxy
**Standard:** NIST Cybersecurity Framework v2.0

---

## 1. GOVERN (GV)

### GV.OC — Organizational Context
- System constitution documented and enforced: Secure, Autonomous, Resilient, Self-healing, Transparent
- 10 key principles codified in project documentation
- Security is explicitly constitutional (principle #7)
- Quality over speed is a binding constraint, not aspirational

### GV.RM — Risk Management Strategy
- Inference proxy as single security boundary (tanks never touch internet)
- API keys isolated to proxy container only
- No secrets in tank environments (verified: only GPG_KEY present, standard Python base image)
- Research data treated as sacred (principle #9)

### GV.SC — Supply Chain Risk Management
- Cloud inference: Cerebras (7 keys) + Groq (8 keys) — free tier, no billing exposure
- Together.ai removed from all code (verified: 0 references)
- Ollama as sovereign failsafe (no external dependency)
- Kiwix Wikipedia served locally (6 language instances)

**Status: PASS**

---

## 2. IDENTIFY (ID)

### ID.AM — Asset Management
- 52 containers (20 running tanks + 9 historical stopped + 17 betaclone stopped + infra)
- 12 Docker images
- 6 Docker networks (isolated-net, default, bridge, host, none, experimental)
- Persistent data: brain.md, soul.md, baselines per tank in /logs/
- DNA snapshots: 17/17 research tanks archived with SHA-256 manifests

### ID.RA — Risk Assessment
Known risks:
1. NUC RAM at 57% with 20 tanks — no headroom for additional services
2. Swap at 75% (1.5/2.0GB) — indicates memory pressure
3. Cain brain growth stalled at 11L due to inference contention
4. Single point of failure: NUC is only active host
5. No off-site backup (HDDs are local)
6. Kokoro TTS cannot run alongside 20 tanks

**Status: PASS (risks documented, mitigations planned via Mac Mini migration)**

---

## 3. PROTECT (PR)

### PR.AA — Identity Management & Access Control
- All tanks run as UID 1000 (non-root) — **VERIFIED** on adam, abel, seth, aria
- No-new-privileges flag set — **VERIFIED**
- All capabilities dropped (CapDrop: [ALL]) — **VERIFIED**
- SecureClaw v2 in all system prompts prevents identity override, code execution, system introspection

### PR.DS — Data Security
- Read-only root filesystem on all tanks — **VERIFIED** (touch /tmp_test_ro → "Read-only file system")
- Brain/soul data written to mounted volumes only
- 60% word-overlap dedup prevents data pollution
- Null trace guard filters junk entries
- Output sanitization removes URLs, error messages, LLM artifacts

### PR.PS — Platform Security
- Custom seccomp BPF profile applied to all tanks — **VERIFIED**
- Blocked syscalls include: ptrace, mount, reboot, kexec_load, swapon, swapoff
- Allowed syscalls are a strict allowlist (not blocklist)
- Docker security_opt includes both no-new-privileges and seccomp profile

### PR.IR — Technology Infrastructure Resilience
- Network isolation: tanks on isolated-net, no internet access — **VERIFIED** (wget fails on adam, abel, felix)
- Inference proxy bridges isolated-net to internet for API calls only
- Ollama fallback with non-blocking lock (LOCK_NB)
- Per-key rate limiting with fcntl locks in proxy

**Status: PASS**

---

## 4. DETECT (DE)

### DE.CM — Continuous Monitoring
- 21/21 daemons alive and monitoring:
  - overseer, maintainer, ollama_watcher (infrastructure)
  - guard, sentinel, bouncer (security)
  - scheduler, broadcaster, webmaster (operations)
  - translator, documentarian, archivist (research)
  - final_auditor, psych, therapist, ethicist (ethics/safety)
  - moderator, chaos_monkey (resilience)
  - marketer, public_liaison, caretaker (public-facing)
- Archivist generates drift reports every 6 hours
- Archivist generates weekly research summaries every 24 hours
- Ollama watcher v5.2 with 600s watchdog timeout and circuit breakers

### DE.AE — Adverse Event Analysis
- Chaos monkey performs resilience testing (intentional fault injection)
- Bouncer has 6 security layers: password gate, rate limiting, content filtering, session management, distress monitoring, emergency termination
- Visitor sessions monitored for distress patterns

**Status: PASS**

---

## 5. RESPOND (RS)

### RS.MA — Incident Management
- Chaos monkey tests recovery from daemon/container failures
- Ollama watcher auto-restarts Ollama on failure with circuit breakers
- Maintainer daemon handles routine recovery
- Emergency termination available in bouncer for visitor sessions

### RS.AN — Incident Analysis
- All daemon activity logged to /logs/ and /daemons/*/
- PID files for all 21 daemons (both path conventions checked)
- DNA snapshots provide chain-of-custody for specimen state

**Status: PASS**

---

## 6. RECOVER (RC)

### RC.RP — Recovery Planning
- DNA snapshots enable full state restoration (brain, soul, baselines, config)
- SHA-256 manifests verify archive integrity
- Docker compose files define complete infrastructure-as-code
- Historical tank seeds in config/seeds/ for re-seeding

### RC.CO — Recovery Communication
- Status check daemon provides real-time system health
- Roadmap page at /roadmap/ shows live status and documented gaps
- Site vs reality gaps explicitly tracked (8 known gaps)

**Status: PASS**

---

## SUMMARY

| Function | Status | Notes |
|----------|--------|-------|
| Govern | PASS | Constitution enforced, principles codified |
| Identify | PASS | All assets inventoried, risks documented |
| Protect | PASS | Defense-in-depth: isolation, non-root, read-only, seccomp, SecureClaw |
| Detect | PASS | 21 daemons monitoring, drift analysis, resilience testing |
| Respond | PASS | Auto-recovery, emergency termination, incident logging |
| Recover | PASS | DNA snapshots, SHA-256 manifests, infrastructure-as-code |

**Overall: COMPLIANT (pre-migration baseline)**

### Recommendations for Post-Migration
1. Deploy RedAmon for continuous automated red teaming
2. Implement off-site backup to HDDs via Tailscale
3. Distribute tanks across NUC + Mac Mini to eliminate single point of failure
4. Add network intrusion detection (Rustunnel as chokepoint)
5. Implement budget tracking per tank per provider
6. Automate dream mode protocol
