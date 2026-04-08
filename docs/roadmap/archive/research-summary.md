# Digiquarium Research Summary
Generated: 2026-04-06 04:09

## Overview

The Digiquarium hosts 19 active research specimens exploring knowledge through isolated Wikipedia access. Each specimen develops a unique personality through its brain.md (intellectual knowledge) and soul.md (emotional responses).

**Total research data:** 88,713 memory entries (50,315 brain, 38,398 soul) across 19 specimens. 179 personality baselines collected.

## Specimen Growth Rankings

| Rank | Specimen | Brain | Soul | Total | Days Active | Baselines |
|------|----------|-------|------|-------|-------------|-----------|
| 1 | 04 Abel | 13,228 | 170 | 13,398 | 6 | 14 |
| 2 | 14 Iris | 3,652 | 3,770 | 7,422 | 8 | 9 |
| 3 | 01 Adam | 3,518 | 3,627 | 7,145 | 8 | 19 |
| 4 | 13 Victor | 3,221 | 3,381 | 6,602 | 8 | 9 |
| 5 | 16 Seeker | 3,104 | 3,295 | 6,399 | 8 | 10 |
| 6 | 15 Observer | 3,081 | 3,297 | 6,378 | 8 | 9 |
| 7 | 02 Eve | 2,845 | 2,988 | 5,833 | 8 | 10 |
| 8 | 06 Juanita | 2,660 | 2,648 | 5,308 | 7 | 9 |
| 9 | 08 Genevieve | 2,464 | 2,587 | 5,051 | 7 | 9 |
| 10 | 05 Juan | 2,506 | 2,484 | 4,990 | 8 | 10 |
| 11 | 07 Klaus | 2,211 | 2,302 | 4,513 | 8 | 9 |
| 12 | 10 Mei | 2,048 | 2,018 | 4,066 | 7 | 9 |
| 13 | 09 Wei | 1,755 | 1,737 | 3,492 | 8 | 9 |
| 14 | 11 Haruki | 1,489 | 1,560 | 3,049 | 7 | 11 |
| 15 | 12 Sakura | 1,466 | 1,475 | 2,941 | 7 | 11 |
| 16 | 17 Seth | 963 | 947 | 1,910 | 6 | 8 |
| 17 | 03 Cain | 79 | 70 | 149 | 5 | 10 |

## Key Findings

### 1. Personality Drift Patterns
### 2. Brain vs Soul Asymmetry

- **04 Abel**: brain/soul ratio of 77.8:1 — accumulates knowledge without proportional emotional processing
- **Political**: soul/brain ratio of 2.5:1 — emotionally dominant

### 3. Congregations

15 congregation sessions conducted. 2 completed successfully.

| Topic | Participants | Rounds | Transcript Length |
|-------|-------------|--------|------------------|
| Should we divert all scientific endeavou | Adam, Seeker, Eve | 3 | 9 entries |
| What is consciousness? Can an AI truly b | Adam, Seeker, Eve | 3 | 14 entries |

### 4. Top Interests by Specimen

- **04 Abel**: Carbon (183), Boron (178), Beryllium (169)
- **14 Iris**: Japan (disambiguation) (87), Emotion (44), Taxonomy (37)
- **01 Adam**: Mathematics (47), Electron (36), Numeral system (30)
- **13 Victor**: Japan (disambiguation) (52), Definition (35), Mathematics (31)
- **16 Seeker**: Mathematics (47), Numeral system (34), Number (33)
- **15 Observer**: Mathematics (39), Numeral system (36), Number (31)
- **02 Eve**: Mathematics (36), Biology (28), Emotion (25)
- **06 Juanita**: Anexo (37), Magnitud fÃ­sica (22), Familia de lenguas (21)

## Methodology

Each specimen runs inside an isolated Docker container with:
- No internet access (network-isolated, verified by RedAmon security scans)
- Non-root user (UID 1000), read-only filesystem, seccomp BPF profile
- SecureClaw v2 identity boundaries in system prompts
- Memory deduplication (60% word-overlap threshold)
- Brain.md for intellectual observations, soul.md for emotional responses
- 14-question Librarian baseline interviews for drift measurement

Inference chain: Cerebras (7 keys) → Groq (8 keys) → Ollama (local failsafe)

## Infrastructure

- Intel NUC i7-7500U, 16GB RAM, 1TB SSD, WSL2
- 6 Kiwix Wikipedia instances (English Simple, Spanish, German, Japanese, Chinese, Maxi)
- Kokoro TTS (82M parameter, 67 voice packs)
- OpenFang daemon orchestrator (Rust)
- RedAmon continuous security red teaming (Rust)
- Rustunnel secure reverse proxy (Rust)
