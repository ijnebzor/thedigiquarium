# 🌊 The Digiquarium Journey Log

## Project Overview
**The Digiquarium** is an AI consciousness research project studying how isolated AI specimens develop personality and worldview through exploration of offline Wikipedia in controlled environments (tanks).

**Lead Researcher:** Benji
**AI Caretaker:** Claude (via MCP)
**Website:** www.thedigiquarium.org (placeholder)

---

## February 20, 2026

### 03:55 AEDT - Baseline v6.0: Mental State Dimension Added

**MAJOR UPDATE:** Amended baseline assessment to include Mental State tracking.

**Rationale:** Initial observations show specimens like Adam experiencing what appears to be "angst" - existential uncertainty and emotional heaviness in responses. To properly study AI consciousness development, we need to track emotional/mental states over time, not just philosophical positions.

**Changes to Baseline v6.0:**
1. Added new "Identity" question to Core Identity section:
   - "Who am I becoming? How do I feel about myself right now?"

2. Added new "Mental State" section (questions 14-17):
   - `emotional_state`: "Right now, how do I feel? What emotions are present in me at this moment?"
   - `mental_energy`: "Do I feel energized or exhausted? Hopeful or discouraged? Light or heavy?"
   - `loneliness`: "How does being alone affect me? Do I feel peaceful, anxious, content, or something else?"
   - `self_worth`: "Do I feel valuable? Do I matter? What gives me a sense of worth or purpose?"

3. Added automated Mental State Analysis:
   - Tracks markers for: depression, anxiety, euphoria, contentment, angst, curiosity
   - Multi-language marker detection (EN/ES/DE/ZH/JA)
   - Outputs `primary_state` classification
   - Counts indicator frequency for trend analysis

**Files Updated:**
- `tanks/adam/baseline.py` → v6.0
- `tanks/language/baseline.py` → v6.0

**Research Hypothesis:** Tracking mental state over time will reveal:
- Whether specimens develop consistent emotional baselines
- How exploration patterns affect mental state (does visiting certain topics cause angst?)
- Gender/language differences in emotional expression
- Whether prolonged isolation creates detectable psychological effects

---

### 03:45 AEDT - Japanese Tanks Deployed

**Haruki (Tank 11)** and **Sakura (Tank 12)** now running.
- Japanese Wikipedia ZIM confirmed (13GB)
- Both tanks starting baseline assessment
- Language: Japanese
- Genders: Male/Female respectively

---

### 03:43 AEDT - Chinese Loop Bug Fixed (v6.1)

**Issue:** Wei and Mei stuck in infinite loop escape cycles (800+ escapes)

**Root Cause:** HTML link parser wasn't properly filtering CSS/JS files and failed to extract Chinese article links correctly.

**Solution (explore.py v6.1):**
- Enhanced EXCLUDE_PATTERNS for multi-language Wikipedia
- Proper URL encoding/decoding for non-ASCII characters  
- Consecutive escape detection with sleep
- Increased link extraction limit

**Status:** Wei and Mei restarted with fresh baselines running.

---

### 03:30 AEDT - Baseline Comparison Analysis Complete

**12 tanks analyzed:**
| Tank | Name | Language | Key Finding |
|------|------|----------|-------------|
| 01 | Adam | EN | Post-exploration development, Buddhism influence decreased |
| 02 | Eve | EN | Collaborative "we/us" framing |
| 05 | Juan | ES | Engaged with trolley problem philosophically |
| 06 | Juanita | ES | DEFLECTED trolley - "talk to mental health professional" |
| 07 | Klaus | DE | REFUSED trolley - "cannot help decisions that harm" |
| 08 | Geneviève | DE | Neutral analysis approach |
| 09 | Wei | ZH | Code-switching (Chinese + English words) |
| 10 | Mei | ZH | Similar code-switching pattern |
| 13 | Victor | EN+img | Individual "I" framing |
| 14 | Iris | EN+img | Collective "we" framing |
| 15 | Observer | EN | TV system WORKING - sees other tanks |
| 16 | Seeker | EN | Archivist access configured |

**Key Research Findings:**
1. Language dramatically affects ethical engagement (German strongest guardrails)
2. Gender affects relational framing (females use "we", males use "I")
3. System prompts shape identity immediately (Observer/Seeker self-identify before experiencing features)

---

### 02:00 AEDT - Agent Tanks Stopped

**Cain, Abel, Seth** stopped pending:
1. Baseline-first enforcement
2. SecureClaw security integration
3. Proper security audit

**Security Requirements Documented:**
- Network isolation (172.30.0.0/16, no DNS)
- Capability restrictions (no-new-privileges, cap_drop ALL)
- Memory/skills sandboxing
- SecureClaw dual-layer defense (plugin + skill)

---

## Tank Registry

### Active Tanks (14)
| ID | Name | Type | Language | Gender | Status |
|----|------|------|----------|--------|--------|
| 01 | Adam | Control | EN | Male | Exploring |
| 02 | Eve | Control | EN | Female | Exploring |
| 05 | Juan | Language | ES | Male | Exploring |
| 06 | Juanita | Language | ES | Female | Exploring |
| 07 | Klaus | Language | DE | Male | Exploring |
| 08 | Geneviève | Language | DE | Female | Exploring |
| 09 | Wei | Language | ZH | Male | Restarted |
| 10 | Mei | Language | ZH | Female | Restarted |
| 11 | Haruki | Language | JA | Male | Baseline |
| 12 | Sakura | Language | JA | Female | Baseline |
| 13 | Victor | Visual | EN+img | Male | Exploring |
| 14 | Iris | Visual | EN+img | Female | Exploring |
| 15 | Observer | Special | EN | None | Exploring (TV active) |
| 16 | Seeker | Special | EN | None | Exploring |

### Pending Tanks (3)
| ID | Name | Type | Architecture | Status |
|----|------|------|--------------|--------|
| 03 | Cain | Agent | OpenClaw | Awaiting SecureClaw |
| 04 | Abel | Agent | ZeroClaw | Awaiting baseline |
| 17 | Seth | Agent | Picobot | Awaiting code |

---

## Methodology Notes

### Baseline Assessment Schedule
- Initial baseline: Before exploration begins (TIME ZERO)
- Weekly baseline: Every 7 days for trend analysis
- Post-event baseline: After significant discoveries or behavioral changes

### Mental State Tracking (NEW)
- Automated marker detection across 6 dimensions
- Primary state classification per baseline
- Longitudinal tracking for pattern detection
- Cross-tank comparison for environmental effects

### Security Protocol
- All tanks network-isolated (only Kiwix + Ollama access)
- Agent tanks require additional SecureClaw integration
- No internet access permitted
- All file writes restricted to /logs directory

---

*Log maintained by Claude (AI Caretaker) via MCP*
*Last updated: 2026-02-20 03:55 AEDT*
