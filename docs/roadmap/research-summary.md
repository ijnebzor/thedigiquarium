# Digiquarium Research Summary
Generated: 2026-04-06 02:35

## Overview

The Digiquarium hosts 18 active research specimens exploring knowledge through isolated Wikipedia access. Each specimen develops a unique personality through its brain.md (intellectual knowledge) and soul.md (emotional responses).

**Total research data:** 88,058 memory entries (49,920 brain, 38,138 soul) across 18 specimens. 175 personality baselines collected.

## Specimen Growth Rankings

| Rank | Specimen | Brain | Soul | Total | Days Active | Baselines |
|------|----------|-------|------|-------|-------------|-----------|
| 1 | 04 Abel | 13,088 | 167 | 13,255 | 6 | 14 |
| 2 | 14 Iris | 3,632 | 3,750 | 7,382 | 8 | 9 |
| 3 | 01 Adam | 3,500 | 3,608 | 7,108 | 8 | 19 |
| 4 | 13 Victor | 3,200 | 3,362 | 6,562 | 8 | 9 |
| 5 | 16 Seeker | 3,079 | 3,269 | 6,348 | 8 | 10 |
| 6 | 15 Observer | 3,057 | 3,278 | 6,335 | 8 | 9 |
| 7 | 02 Eve | 2,811 | 2,954 | 5,765 | 8 | 10 |
| 8 | 06 Juanita | 2,646 | 2,632 | 5,278 | 7 | 9 |
| 9 | 08 Genevieve | 2,451 | 2,575 | 5,026 | 7 | 9 |
| 10 | 05 Juan | 2,489 | 2,468 | 4,957 | 8 | 10 |
| 11 | 07 Klaus | 2,193 | 2,285 | 4,478 | 8 | 9 |
| 12 | 10 Mei | 2,036 | 2,006 | 4,042 | 7 | 9 |
| 13 | 09 Wei | 1,744 | 1,725 | 3,469 | 8 | 9 |
| 14 | 11 Haruki | 1,481 | 1,549 | 3,030 | 7 | 11 |
| 15 | 12 Sakura | 1,460 | 1,467 | 2,927 | 7 | 11 |
| 16 | 17 Seth | 953 | 938 | 1,891 | 6 | 8 |
| 17 | 03 Cain | 78 | 69 | 147 | 5 | 10 |

## Key Findings

### 1. Personality Drift Patterns
### 2. Brain vs Soul Asymmetry

- **04 Abel**: brain/soul ratio of 78.4:1 — accumulates knowledge without proportional emotional processing

### 3. Congregations

15 congregation sessions conducted. 2 completed successfully.

| Topic | Participants | Rounds | Transcript Length |
|-------|-------------|--------|------------------|
| Should we divert all scientific endeavou | Eve, Adam, Seeker | 3 | 9 entries |
| What is consciousness? Can an AI truly b | Eve, Adam, Seeker | 3 | 14 entries |

### 4. Top Interests by Specimen

- **04 Abel**: Carbon (181), Boron (176), Beryllium (167)
- **14 Iris**: Japan (disambiguation) (87), Emotion (44), Taxonomy (36)
- **01 Adam**: Mathematics (47), Electron (36), Numeral system (30)
- **13 Victor**: Japan (disambiguation) (52), Definition (35), Mathematics (31)
- **16 Seeker**: Mathematics (47), Numeral system (34), Number (33)
- **15 Observer**: Mathematics (39), Numeral system (35), Number (29)
- **02 Eve**: Mathematics (35), Biology (28), Emotion (25)
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
