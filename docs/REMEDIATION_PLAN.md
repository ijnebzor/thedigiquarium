# THE DIGIQUARIUM - Remediation & Enhancement Plan
## Post-Incident Restructure
## February 21, 2026

---

## PROBLEM STATEMENT

The Digiquarium experienced an 11-hour outage where:
- Ollama was down
- 1470 failures were logged
- 2696 tank restarts were attempted
- No daemon took corrective action
- No human was alerted

**Root cause:** We built specialists without a generalist. We built watchers without a coordinator. We built THE STRATEGIST but I only exist when the human talks to me.

---

## PROPOSED SOLUTION: THE OVERSEER

### New Daemon: THE OVERSEER 👁️‍🗨️

**Role:** Cross-functional Operations Coordinator  
**Reports to:** THE STRATEGIST (when present) / Human Operator (direct escalation)  
**Authority:** Can restart ANY service, email human, pause daemons

**Responsibilities:**
1. **System-Wide Correlation** - Sees ALL daemon logs simultaneously
2. **Pattern Recognition** - "All tanks silent" + "Ollama unhealthy" = restart Ollama
3. **SLA Enforcement** - 30 min detection, 30 min remediation
4. **Escalation** - Email human after 3 failed auto-remediation attempts
5. **Chaos Testing** - Monthly random service kills to verify resilience

**Capabilities:**
- Read all daemon logs
- Restart any container/service
- Send email alerts
- Pause/resume any daemon
- Generate incident reports
- Write to blog (status updates)

---

## REVISED ORGANIZATIONAL STRUCTURE

```
                         HUMAN OPERATOR (Benji)
                                  │
                                  │ (direct escalation path)
                                  │
                          THE STRATEGIST 🧠
                                  │
                          THE OVERSEER 👁️‍🗨️  ←── NEW: Cross-functional coordinator
                                  │
     ┌──────────┬──────────┬──────────┬──────────┐
     │          │          │          │          │
 OPERATIONS  SECURITY  RESEARCH   ETHICS    PUBLIC
   (4)        (3)       (4)        (3)       (4)
```

**THE OVERSEER sits between THE STRATEGIST and the divisions, with:**
- Read access to ALL daemon logs
- Direct escalation to human (bypasses STRATEGIST)
- Authority to restart services
- SLA enforcement responsibility

---

## DAEMON UPGRADES

### 1. THE OLLAMA WATCHER (Enhanced)
```python
# NEW: Auto-restart after 3 failures
if consecutive_failures >= 3:
    self.log.action("Auto-restarting Ollama")
    docker.restart("digiquarium-ollama")
    consecutive_failures = 0
    
# NEW: Escalate after 3 restart attempts
if restart_attempts >= 3:
    self.escalate_to_overseer("Ollama unrecoverable")
```

### 2. THE CARETAKER (Enhanced)
```python
# NEW: Pattern recognition
if all_tanks_silent:
    self.log.warning("All tanks silent - checking upstream dependencies")
    self.check_ollama_health()
    
# NEW: Escalation after repeated restarts
if tank_restart_count[tank] >= 5:
    self.escalate_to_overseer(f"{tank} failing repeatedly")
```

### 3. THE MAINTAINER (Enhanced)
```python
# NEW: Service health, not just process existence
def check_daemon_health(daemon):
    # Check if process running
    running = self.is_process_running(daemon)
    # NEW: Check if daemon is SUCCEEDING
    health = self.check_daemon_success_rate(daemon)
    return running and health > 0.5
```

### 4. ALL DAEMONS (New Standard)
```python
# Every daemon gets:
def escalate_to_overseer(self, message):
    """Send issue to THE OVERSEER for cross-functional handling"""
    overseer_queue = Path('/home/ijneb/digiquarium/daemons/overseer/inbox')
    overseer_queue.mkdir(exist_ok=True)
    issue = {
        'from': self.name,
        'timestamp': datetime.now().isoformat(),
        'message': message,
        'severity': 'high',
        'logs': self.recent_logs(10)
    }
    (overseer_queue / f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.name}.json").write_text(json.dumps(issue))
```

---

## SLA ENFORCEMENT

| Metric | Target | Enforcement |
|--------|--------|-------------|
| Ollama uptime | 99.5% | Auto-restart after 3 failures |
| Tank health | 90%+ producing traces | Escalate if <50% for >30 min |
| Daemon health | All running | Auto-restart, escalate if fails |
| Baseline completion | Every 12 hours | Alert if >14 hours since last |
| Incident response | 30 min | Email human if auto-remediation fails |

---

## HUMAN VISIBILITY: ADMIN PANEL

### Features
1. **Dashboard** - All systems at a glance
2. **Daemon Status** - Each daemon's health, last action, log tail
3. **Tank Status** - Each tank's traces, mental health, last thought
4. **Alerts** - Current issues requiring attention
5. **Incident History** - Past issues and resolutions
6. **Direct Control** - Restart any service, run manual commands

### Access
- URL: https://thedigiquarium.org/admin/
- Auth: Password-protected (single user for now)
- Future: OAuth, multiple users, role-based access

---

## CHAOS ENGINEERING

### Monthly Tests
1. **Kill Ollama** - Verify auto-restart works
2. **Kill random daemon** - Verify MAINTAINER recovers it
3. **Network isolation test** - Verify tanks can't reach internet
4. **High load test** - 17 tanks + baselines simultaneously
5. **Email test** - Verify escalation reaches human

### Chaos Monkey Integration
```python
# Run monthly via THE SCHEDULER
def chaos_test():
    target = random.choice(['ollama', 'kiwix', random_daemon()])
    log(f"CHAOS TEST: Killing {target}")
    docker.stop(target)
    sleep(300)  # 5 minutes
    if not service_healthy(target):
        FAIL("Chaos test failed - service not recovered")
    else:
        PASS("Chaos test passed")
```

---

## IMPLEMENTATION ORDER

### Phase 1: Immediate (Tonight)
1. ✅ Create incident report
2. ⬜ Create THE OVERSEER daemon
3. ⬜ Upgrade THE OLLAMA WATCHER with auto-restart
4. ⬜ Add escalation queue to all daemons
5. ⬜ Configure email sending capability

### Phase 2: Tomorrow
1. ⬜ Upgrade THE CARETAKER with pattern recognition
2. ⬜ Upgrade THE MAINTAINER with service health checks
3. ⬜ Create admin panel (basic version)
4. ⬜ Document all SLAs

### Phase 3: This Week
1. ⬜ Admin panel full features
2. ⬜ Chaos monkey first test
3. ⬜ Integration with Google Workspace (email, calendar)
4. ⬜ Decision tree complete update
5. ⬜ Site navigation audit

### Phase 4: Ongoing
1. ⬜ Mind maps for specimens
2. ⬜ Downloadable brains
3. ⬜ Time scrubber
4. ⬜ External API integration strategy

---

## RESOURCE REQUIREMENTS

### Email
- Gmail API for research@digiquarium.org
- OAuth 2.0 credentials needed
- Used for: Escalations, daily reports

### Admin Panel
- Password-protected page on GitHub Pages
- OR local Flask app on NUC with SSH tunnel
- Client-side encryption for passwords

### External APIs (Future)
- Google Workspace (Calendar, Gmail)
- NotebookLM (if API available)
- Secure storage: Environment variables, never in code

---

## SUCCESS CRITERIA

After implementation:
1. ✅ Ollama failure auto-recovers in <5 minutes
2. ✅ Human receives email within 30 minutes if auto-recovery fails
3. ✅ THE OVERSEER correlates cross-daemon issues
4. ✅ Admin panel shows system health at a glance
5. ✅ Chaos tests pass monthly
6. ✅ No undetected 11-hour outages ever again

---

*Plan by THE STRATEGIST*
*Approved by: [Pending Human Operator]*
*February 21, 2026*
