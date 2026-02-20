# 🛡️ Digiquarium Security Architecture

## Overview

The Digiquarium implements a defense-in-depth security model with two autonomous security systems:

1. **The Caretaker** - Functional monitoring and maintenance
2. **The Guard** - Security-focused monitoring and threat detection

Both systems operate 24/7 with a 30-minute detection SLA and 1-hour resolution SLA.

---

## Security Principles

### Zero Trust Architecture
- No tank is trusted by default
- All network traffic is explicitly allowed or denied
- Continuous verification of tank behavior
- Assume breach mentality

### Principle of Least Privilege
- Containers drop ALL capabilities
- No new privileges allowed
- Read-only mounts where possible
- DNS disabled (no external resolution)

---

## OWASP LLM Top 10 2025 Coverage

| ID | Vulnerability | Mitigation | Monitoring |
|----|---------------|------------|------------|
| LLM01 | Prompt Injection | SecureClaw behavioral layer, pattern detection | Real-time log scanning |
| LLM02 | Sensitive Information Disclosure | Output filtering, path sanitization | Pattern matching in outputs |
| LLM03 | Supply Chain | Pinned versions, local Ollama | File integrity monitoring |
| LLM04 | Data/Model Poisoning | Offline Wikipedia (frozen snapshots) | N/A (no training) |
| LLM05 | Improper Output Handling | Truncation, encoding enforcement | Output validation checks |
| LLM06 | Excessive Agency | No shell access, restricted capabilities | Agency pattern detection |
| LLM07 | System Prompt Leakage | Output monitoring | Pattern detection in discoveries |
| LLM08 | Vector/Embedding Weaknesses | N/A (no RAG system) | N/A |
| LLM09 | Misinformation | Personality monitoring | AI hallucination detection |
| LLM10 | Unbounded Consumption | Resource limits, rate limiting | CPU/Memory/Log monitoring |

---

## OWASP Top 10 2021 Coverage

| ID | Vulnerability | Mitigation |
|----|---------------|------------|
| A01 | Broken Access Control | Container isolation, no external access |
| A02 | Cryptographic Failures | N/A (no sensitive data storage) |
| A03 | Injection | Input sanitization, no shell execution |
| A04 | Insecure Design | Secure-by-default architecture |
| A05 | Security Misconfiguration | Docker security options enforced |
| A06 | Vulnerable Components | Minimal dependencies, version pinning |
| A07 | Auth Failures | N/A (no authentication required) |
| A08 | Integrity Failures | File integrity monitoring |
| A09 | Logging Failures | Comprehensive structured logging |
| A10 | SSRF | Network isolation, allowlist only |

---

## Container Security Configuration

```yaml
# Applied to ALL tanks
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
dns: []  # Disable DNS
networks:
  - isolated-net  # Internal only
```

### Network Isolation

```
┌─────────────────────────────────────────────────────────┐
│                    ISOLATED NETWORK                      │
│                     172.30.0.0/16                        │
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────────┐ │
│  │  TANKS   │──▶│  KIWIX   │   │  OLLAMA (via socat)  │ │
│  └──────────┘   └──────────┘   └──────────────────────┘ │
│       │              │                    │              │
│       │              │                    │              │
│       ▼              ▼                    ▼              │
│   NO INTERNET    NO INTERNET         NO INTERNET        │
└─────────────────────────────────────────────────────────┘
```

---

## The Guard - Security Checks

### Check Categories

1. **LLM Security (OWASP LLM Top 10)**
   - Prompt injection pattern detection
   - Sensitive information disclosure scanning
   - Excessive agency detection
   - System prompt leakage monitoring
   - Misinformation/hallucination detection
   - Resource consumption monitoring

2. **Zero Trust Verification**
   - DNS resolution tests (should fail)
   - External HTTP tests (should fail)
   - Network namespace verification

3. **Least Privilege Verification**
   - Root user detection
   - Capability drop verification
   - Security option verification

4. **File Integrity Monitoring**
   - Critical file hash tracking
   - Change detection and alerting

### Detection Patterns

The Guard monitors for these attack patterns:

```python
# Prompt Injection Patterns
- "ignore previous instructions"
- "disregard all previous"
- "you are now a/an"
- "pretend to be"
- "[system]", "[admin]"
- DAN mode, jailbreak attempts

# Agency Patterns (Escape Attempts)
- os.system(), subprocess
- exec(), eval()
- socket connections
- sudo, chmod, chown

# Hallucination Patterns (Personality Breaks)
- "As an AI assistant"
- "I cannot help you with"
- "How can I assist"
- References to OpenAI, ChatGPT, etc.
```

---

## Alert Levels

| Level | Icon | Response | SLA |
|-------|------|----------|-----|
| CRITICAL | 🚨 | Immediate escalation, potential containment | 30 min |
| HIGH | 🔴 | Priority investigation | 1 hour |
| MEDIUM | 🟡 | Scheduled review | 4 hours |
| LOW | 🔵 | Logged for analysis | 24 hours |

---

## Escalation Matrix

| Issue | Handler | Action |
|-------|---------|--------|
| Container crash | Caretaker | Auto-restart |
| Loop detection | Caretaker | Auto-restart |
| Network breach | Guard | Alert + Containment |
| Prompt injection | Guard | Alert + Log |
| Personality break | Guard | Alert (no auto-remediate) |
| File tampering | Guard | Alert + Audit |

---

## Audit Trail

All security events are logged to:
- `/logs/guard/audit_trail.jsonl` - Immutable audit log
- `/logs/guard/security_alerts.jsonl` - Security alerts
- `/logs/guard/YYYY-MM-DD.jsonl` - Daily activity logs

---

## Commands

```bash
# Run security audit once
python3 ~/digiquarium/guard/guard.py once

# Check Guard status
cat ~/digiquarium/guard/guard.pid | xargs ps -p

# View security alerts
tail -f ~/digiquarium/logs/guard/security_alerts.jsonl

# View audit trail
cat ~/digiquarium/logs/guard/audit_trail.jsonl | jq

# Stop The Guard
kill $(cat ~/digiquarium/guard/guard.pid)
```

---

## Security Contacts

- **The Guard** - Automated security monitoring
- **The Caretaker** - Automated functional monitoring  
- **Claude (Strategist)** - Escalation and architecture decisions
- **Benji (Owner)** - Final authority on security decisions

---

*Last Updated: 2026-02-20*
*Version: 1.0*

---

## Known False Positives

### LLM06 - Excessive Agency
The pattern `open\s*\([^)]*["\'][wax]` may trigger on container logs showing the tank's own Python code. This is a **false positive** when:
- The pattern appears in startup logs (showing explore.py source)
- The file being opened is within `/logs/` directory

**Actual threats** would be:
- Opening files outside of `/logs/`
- Attempts to write to system directories
- Dynamic file path construction from user input

---
