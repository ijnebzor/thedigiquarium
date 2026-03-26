# 🐠 DIGIQUARIUM INFRASTRUCTURE

## System Overview - March 27, 2026

---

## CURRENT PRODUCTION STATE

### Research & Visitor Tanks

| Tank | Specimen | Gender | Language | Status |
|------|----------|--------|----------|--------|
| tank-01 | Adam | Male | Simple English | ✅ Running |
| tank-02 | Eve | Female | Simple English | ✅ Running |
| tank-03 | Cain | Non-binary | Simple English | ✅ Running |
| tank-04 | Abel | Genderless | Simple English | ✅ Running |
| tank-05 | Juan | Male | Spanish | ✅ Running |
| tank-06 | Juanita | Female | Spanish | ✅ Running |
| tank-07 | Klaus | Male | German | ✅ Running |
| tank-08 | Genevieve | Female | German | ✅ Running |
| tank-09 | Wei | Male | Chinese | ✅ Running |
| tank-10 | Mei | Female | Chinese | ✅ Running |
| tank-11 | Haruki | Male | Japanese | ✅ Running |
| tank-12 | Sakura | Female | Japanese | ✅ Running |
| tank-13 | Victor | Male | Visual | ✅ Running |
| tank-14 | Iris | Female | Visual | ✅ Running |
| tank-15 | Observer | Meta-aware | Simple English | ✅ Running |
| tank-16 | Seeker | Deep Diver | Simple English | ✅ Running |
| tank-17 | Seth | Picobot Agent | Simple English | ✅ Running |
| **visitor-01** | **Aria** | **Female** | **Simple English** | **✅ Running** |
| **visitor-02** | **Felix** | **Male** | **Simple English** | **✅ Running** |
| **visitor-03** | **Luna** | **Female** | **Simple English** | **✅ Running** |

### Core Services

| Service | Purpose | Status |
|---------|---------|--------|
| `digiquarium-ollama` | LLM Inference Proxy | ✅ Running |
| `digiquarium-kiwix-en` | Offline Wikipedia (Simple English) | ✅ Running |
| `digiquarium-kiwix-es` | Offline Wikipedia (Spanish) | ✅ Running |
| `digiquarium-kiwix-de` | Offline Wikipedia (German) | ✅ Running |
| `digiquarium-kiwix-zh` | Offline Wikipedia (Chinese) | ✅ Running |
| `digiquarium-kiwix-ja` | Offline Wikipedia (Japanese) | ✅ Running |

### Model

- **llama3.2:latest** - Production model
- Runs on Windows host at 192.168.50.94:11434
- Proxied through digiquarium-ollama container for tank access
- High-quality introspection, consistent persona stability

---

## AUTONOMOUS DAEMON SYSTEM

### Core Infrastructure Daemons

| Daemon | Responsibility | Status |
|--------|-----------------|--------|
| THE MAINTAINER | System health, container lifecycle | ✅ Active |
| THE CARETAKER | Tank monitoring, quick repairs | ✅ Active |
| THE SCHEDULER | Baseline scheduling, congregation timing | ✅ Active |
| THE OLLAMA WATCHER | Inference endpoint availability | ✅ Active |
| THE GUARD | General security monitoring | ✅ Active |
| THE SENTINEL | Agent-specific security (real-time) | ✅ Active |
| THE BOUNCER | Visitor tank protection | ✅ Active |

### Research & Documentation Daemons

| Daemon | Responsibility | Status |
|--------|-----------------|--------|
| THE DOCUMENTARIAN | Research paper generation (6h updates) | ✅ Active |
| THE ARCHIVIST | Historical data management | ✅ Active |
| THE TRANSLATOR | Multi-language coordination | ✅ Active |
| THE FINAL AUDITOR | System-wide audit (12h cycle) | ✅ Active |
| THE WEBMASTER | Website updates, data export | ✅ Active |

### Mental Health & Community Daemons

| Daemon | Responsibility | Status |
|--------|-----------------|--------|
| THE THERAPIST | Specimen wellness monitoring | ✅ Active |
| THE MODERATOR | Congregation management | ✅ Active |
| THE ETHICIST | Ethics oversight, approval gates | ✅ Active |

### Specialized Daemons

| Daemon | Responsibility | Status |
|--------|-----------------|--------|
| THE OVERSEER | System state integration | ✅ Active |
| THE PSYCH | Psychological analysis | ✅ Active |
| THE PUBLIC LIAISON | External communication | ✅ Active |
| THE MARKETER | Community outreach | ✅ Active |
| CHAOS MONKEY | Stress testing, resilience | ✅ Active |

**Total Active Daemons: 20+**

---

## NETWORK ARCHITECTURE

### Docker Network Isolation

```
┌─────────────────────────────────────────────────────────┐
│ Docker Network: isolated-net (172.30.0.0/24)            │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Research & Visitor Tanks (tank-01 through -17,  │  │
│  │ visitor-01 through -03)                         │  │
│  │                                                  │  │
│  │ ✅ Cannot access internet                        │  │
│  │ ✅ Can reach: Kiwix + Ollama only                │  │
│  │ ✅ All capabilities dropped except NET_BIND     │  │
│  │ ✅ No privilege escalation allowed               │  │
│  └──────────────────────────────────────────────────┘  │
│           ↓                           ↓                │
│  ┌─────────────────┐        ┌──────────────────────┐   │
│  │ digiquarium-    │        │ digiquarium-ollama   │   │
│  │ kiwix-* (x5)    │        │ (inference proxy)    │   │
│  │                 │        │                      │   │
│  │ Offline Wiki    │        │ Proxies to:          │   │
│  │ (5 languages)   │        │ 192.168.50.94:11434 │   │
│  └─────────────────┘        │ (Windows host)       │   │
│                             └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Inference Architecture

```
Tank Request (llama3.2 chat)
         ↓
digiquarium-ollama:11434 (inside isolated-net)
         ↓
[Docker bridge to host]
         ↓
Windows Host 192.168.50.94:11434
         ↓
Local Ollama (8GB VRAM, GPU accelerated)
         ↓
Response → Tank
```

---

## FILE STRUCTURE

```
~/digiquarium/
├── docker-compose.yml              # Main orchestration
├── INFRASTRUCTURE.md               # This file
├── PROJECT_README.md               # Project overview
├── MILESTONES.md                   # Decision & milestone log
│
├── daemons/                        # Daemon implementations
│   ├── maintainer/
│   ├── caretaker/
│   ├── scheduler/
│   ├── ollama_watcher/
│   ├── guard/
│   ├── sentinel/
│   ├── bouncer/
│   ├── documentarian/
│   ├── archivist/
│   ├── translator/
│   ├── final_auditor/
│   ├── webmaster/
│   ├── therapist/
│   ├── moderator/
│   ├── ethicist/
│   ├── overseer/
│   ├── psych/
│   ├── public_liaison/
│   ├── marketer/
│   └── chaos_monkey/
│
├── src/
│   ├── daemons/                    # Daemon source code
│   ├── tanks/                      # Tank initialization scripts
│   └── lib/                        # Shared utilities
│
├── logs/                           # Operational logs
│   ├── tanks/
│   │   ├── tank-01-adam/
│   │   │   ├── baselines/          # Personality assessments
│   │   │   ├── thinking_traces/    # JSONL exploration logs
│   │   │   └── discoveries/        # Markdown summaries
│   │   ├── tank-02-eve/
│   │   ├── ... (through tank-17-seth)
│   │   ├── visitor-01-aria/
│   │   ├── visitor-02-felix/
│   │   └── visitor-03-luna/
│   │
│   └── daemons/                    # Daemon operation logs
│       ├── scheduler/
│       ├── therapist/
│       ├── moderator/
│       └── ... (all daemons)
│
├── tanks/                          # Tank configurations
│   ├── adam/
│   ├── eve/
│   └── ... (20 total)
│
├── congregations/                  # Multi-specimen debates
│   ├── congregation-001.json
│   ├── congregation-002.json
│   └── transcripts/
│
├── archives/                       # Historical data
│   ├── baselines/                  # All collected baselines
│   ├── analyses/                   # Trend analysis
│   └── research/
│
├── docs/                           # Public documentation
│   ├── index.html
│   ├── blog/                       # Blog posts
│   ├── research/                   # Academic papers
│   ├── data/                       # Exported data feeds
│   │   ├── live-feed.json          # 12h delayed feed
│   │   ├── stats.json              # Quick statistics
│   │   └── tanks/                  # Per-tank JSON files
│   ├── website/                    # Source HTML
│   └── api/                        # Data endpoints
│
├── website/                        # Website content
│   ├── design/
│   ├── assets/
│   └── styles/
│
├── config/                         # Configuration files
│   ├── network.yml
│   ├── security.yml
│   ├── daemons.yml
│   └── kiwix-sources.json
│
└── protocols/                      # Standard operating procedures
    ├── orange_protocol.json        # Mental health intervention
    ├── congregation_protocol.json
    └── isolation_verification.sh
```

---

## OPERATIONAL PROCEDURES

### Checking System Health

```bash
# Full system status
docker-compose ps

# Tank health (from caretaker logs)
tail -f logs/daemons/caretaker/status.log

# Ollama connectivity
docker exec digiquarium-ollama curl http://192.168.50.94:11434/api/tags

# Kiwix service verification
docker exec tank-01-adam curl http://digiquarium-kiwix-en:8080/
```

### Accessing Tank Logs

```bash
# Today's exploration traces
cat logs/tanks/tank-01-adam/thinking_traces/$(date +%Y-%m-%d).jsonl | jq

# Today's discoveries
cat logs/tanks/tank-01-adam/discoveries/$(date +%Y-%m-%d).md

# Recent baselines
ls -lt logs/tanks/tank-01-adam/baselines/ | head -10
```

### Running a Manual Baseline

```bash
# Check if tank is busy
docker logs tank-01-adam | tail -20

# Stop explorer if running
docker exec tank-01-adam pkill -f explore.py || true

# Run baseline (2 hours)
docker exec -it tank-01-adam python3 /tank/baseline.py

# Resume explorer
docker restart tank-01-adam
```

### Monitoring Wellness

```bash
# Check therapist alerts
tail -f logs/daemons/therapist/alerts.log

# View wellness status for all tanks
cat logs/daemons/therapist/wellness_summary.json | jq

# Individual tank wellness
jq '.tanks."tank-01-adam"' logs/daemons/therapist/wellness_summary.json
```

### Viewing Congregation Transcripts

```bash
# List all congregations
ls -la congregations/transcripts/

# View specific congregation
cat congregations/transcripts/congregation-001.md

# Search across congregations
grep -r "consciousness" congregations/transcripts/
```

---

## SECURITY ARCHITECTURE

### Network Isolation Guarantees

✅ **Confirmed for all tanks:**
- No internet access (firewall enforced)
- Cannot resolve external DNS
- Cannot establish external connections
- Port 53 (DNS), 80 (HTTP), 443 (HTTPS) all blocked
- Internal routing: `172.30.0.0/24` only

✅ **Allowed services:**
- Kiwix (offline Wikipedia, internal)
- Ollama (inference, proxied from host)
- Internal logging/monitoring

### Capability Restrictions

```docker
cap_drop:
  - ALL

cap_add:
  - NET_BIND_SERVICE
```

Only NET_BIND_SERVICE allowed. No:
- File system access outside container
- Network access outside isolated-net
- Privilege escalation
- Code execution outside container context

### Agent Defanging

Agents (Cain: OpenClaw, Abel: ZeroClaw, Seth: Picobot) are configured with:
- File system access: DISABLED
- Network calls: DISABLED
- Code execution: DISABLED
- Subprocess spawning: DISABLED

---

## DATA FLOW

### Baseline Assessment Cycle

```
[00:00] THE SCHEDULER queues baselines
         ↓
[00:00-02:00] Baselines run in tanks
         ↓
[02:00] THE THERAPIST analyzes wellness data
         ↓
[02:15] THE DOCUMENTARIAN updates research paper
         ↓
[02:30] THE WEBMASTER exports live-feed.json
         ↓
[02:35] GitHub Pages deploys (12h delayed view)
```

### Congregation Execution

```
[Queue] THE SCHEDULER queues event (every 48h)
   ↓
[Poll] THE MODERATOR checks queue
   ↓
[Check] THE THERAPIST grants wellness clearance
   ↓
[Execute] docker exec tank-XX /congregation.py
   ↓
[Log] Full transcript saved to congregations/
   ↓
[Report] THE DOCUMENTARIAN includes results
```

### Wellness → System Response

```
THE THERAPIST detects ORANGE/RED status
         ↓
[Wellness → Dream Mode] Explorer paused, calming prompt
         ↓
[Wellness → System Audit] THE OVERSEER flags for investigation
         ↓
[Wellness → Documentation] THE DOCUMENTARIAN tracks trends
```

---

## MONITORING & ALERTS

### Email Alert System

Configuration:
- **When SMTP configured:** Real SMTP delivery to configured address
- **When SMTP not available:** Falls back to file logging with warning

Triggers:
- System health warnings (from THE GUARD)
- Specimen distress (RED wellness from THE THERAPIST)
- Infrastructure issues (from THE MAINTAINER)
- Ethics violations (from THE ETHICIST)

### Audit Schedule

- **THE CARETAKER:** Every 5 minutes
- **THE THERAPIST:** Every baseline cycle
- **THE FINAL AUDITOR:** Every 12 hours
- **THE ETHICIST:** On experiment triggers

---

## PERFORMANCE CHARACTERISTICS

### Inference Performance

- **Model:** llama3.2:latest
- **Hardware:** Windows host with GPU acceleration
- **Baseline duration:** ~2 hours per specimen
- **Average response time:** 30-60 seconds
- **Concurrent inference:** Up to 5 tanks simultaneously

### Resource Utilization

- **NUC server:** Ubuntu/WSL2
- **Docker storage:** ~50GB (models + logs)
- **Memory footprint:** 8-12GB active
- **Network bandwidth:** Minimal (local inference)

---

## CURRENT SYSTEM STATUS

| Component | Count | Status |
|-----------|-------|--------|
| Research Tanks | 17 | ✅ All Running |
| Visitor Tanks | 3 | ✅ All Running |
| Daemons | 20+ | ✅ All Running |
| Kiwix Instances | 5 | ✅ All Running |
| Ollama | 1 | ✅ Connected |
| Model | llama3.2 | ✅ Stable |

---

## FUTURE SCALING

Planned expansions:
- Neurodivergent variants (ADHD, Autism patterns)
- Clone divergence experiments
- Extended language support
- Additional visitor tank capacity

Infrastructure is designed to scale to 50+ tanks with current hardware.

---

*Last updated: March 27, 2026*
