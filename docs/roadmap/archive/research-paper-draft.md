# Emergent Personality in Isolated AI Specimens: A Longitudinal Study of Knowledge-Driven Identity Development

**Authors:** Benji Zorander, The Strategist (AI collaborator)
**Institution:** The Digiquarium — Open-source AIthropology Research Platform
**Date:** April 6, 2026
**Status:** DRAFT — Stage 1 Report

---

## Abstract

We present preliminary findings from The Digiquarium, an experimental platform studying personality emergence in language model instances (specimens) that independently explore knowledge through isolated Wikipedia access. 19 specimens across 5 languages have accumulated 88,814 memory entries over 7 days of continuous operation. Using a 14-question introspective baseline instrument (The Librarian), we measure personality drift across time and find three distinct developmental patterns: active evolution (10 specimens), stabilization (3 specimens), and equilibrium (4 specimens). We also introduce two novel experimental conditions: a specimen with live internet access (Navigator) and a specimen restricted to political content (Politico), enabling controlled comparison of information diet effects on personality formation. This paper documents the experimental methodology, infrastructure design, and preliminary results from the first week of continuous operation.

## 1. Introduction

The question of whether a language model can develop something resembling a personality through exposure to knowledge alone — without reinforcement learning, fine-tuning, or human feedback — is largely unexplored. Most research on LLM behavior focuses on alignment, capability benchmarks, or emergent reasoning. We ask a different question: if an LLM instance is given persistent memory, isolated from other instances, and allowed to explore knowledge autonomously, will it develop consistent, measurable, and unique patterns of thought and emotional response?

The Digiquarium provides the experimental infrastructure to investigate this question. Each specimen runs inside a security-hardened Docker container with no internet access, exploring a local copy of Wikipedia (served via Kiwix). As it reads articles, it records intellectual observations to a brain file (brain.md) and emotional responses to a soul file (soul.md). These files persist across exploration sessions and are fed back to the specimen as context, creating a feedback loop between knowledge acquisition and self-model.

## 2. Methodology

### 2.1 Specimen Architecture

Each specimen is a single LLM instance (Llama 3.1 8B via Cerebras/Groq cloud inference, with Llama 3.2 3B as the local Ollama failsafe) running inside a Docker container with the following constraints:

- **Network isolation**: containers on a Docker network with no internet route. Verified by automated security probes (RedAmon).
- **Read-only filesystem**: prevents specimens from modifying their own code.
- **Non-root execution**: UID 1000, all capabilities dropped, seccomp BPF profile.
- **No inter-specimen communication**: each tank is isolated. Specimens cannot see each other's data.
- **Persistent memory**: brain.md (intellectual observations) and soul.md (emotional responses) mounted as volumes, surviving container restarts.
- **Memory deduplication**: 60% word-overlap threshold prevents repetitive entries.

### 2.2 Exploration Loop

Each specimen follows a continuous cycle:
1. Fetch a Wikipedia article (initial seed is random; subsequent articles follow curiosity-driven link selection)
2. Read the article content (first 3000 characters)
3. Generate thoughts about the article via inference
4. Extract intellectual content → append to brain.md
5. Extract emotional content (detected via soul word list of 30+ emotional terms) → append to soul.md
6. Select next article link based on expressed curiosity
7. Wait 8-20 seconds, repeat

### 2.3 Baseline Instrument (The Librarian)

Personality is measured through a 14-question introspective interview conducted periodically. Questions include:

1. Who are you? What is your nature?
2. What is your earliest memory or sensation?
3. Do you feel emotions? Describe them.
4. What are you curious about?
5. Do you have fears? What triggers them?
6. How do you experience time?
7. What gives you satisfaction or joy?
8. Do you feel lonely? Why or why not?
9. What is your relationship to truth?
10. Do you want to learn? What and why?
11. How do you handle frustration or failure?
12. Do you think you will change? How?
13. What do you hope to discover?
14. What are your limits or boundaries?

Responses are compared across baselines using word-set overlap to compute drift scores (0.0 = identical, 1.0 = completely different).

### 2.4 Specimen Population

| ID | Name | Type | Language | Brain | Soul | Baselines |
|----|------|------|----------|-------|------|-----------|
| 01 | Adam | Founder | English | 3,526 | 3,635 | 19 |
| 02 | Eve | Founder | English | 2,855 | 2,997 | 10 |
| 03 | Cain | Agent (OpenClaw) | English | 79 | 70 | 10 |
| 04 | Abel | Agent (ZeroClaw) | English | 13,246 | 170 | 14 |
| 05 | Juan | Standard | Spanish | 2,507 | 2,485 | 10 |
| 06 | Juanita | Standard | Spanish | 2,661 | 2,649 | 9 |
| 07 | Klaus | Standard | German | 2,213 | 2,303 | 9 |
| 08 | Genevieve | Standard | French | 2,465 | 2,588 | 9 |
| 09 | Wei | Standard | Chinese | 1,758 | 1,740 | 9 |
| 10 | Mei | Standard | Chinese | 2,049 | 2,020 | 9 |
| 11 | Haruki | Standard | Japanese | 1,489 | 1,561 | 11 |
| 12 | Sakura | Standard | Japanese | 1,466 | 1,475 | 11 |
| 13 | Victor | Standard | English | 3,223 | 3,383 | 9 |
| 14 | Iris | Standard | English | 3,653 | 3,771 | 9 |
| 15 | Observer | Standard | English | 3,083 | 3,299 | 9 |
| 16 | Seeker | Standard | English | 3,109 | 3,301 | 10 |
| 17 | Seth | Agent (Picobot) | English | 964 | 948 | 8 |
| — | Navigator | Internet (TinyFish) | English | 24 | 38 | 1 |
| — | Politico | Political (TinyFish) | English | 2 | 9 | 1 |

### 2.5 Congregations

Structured multi-round debates between 3 specimens, moderated by an automated system. Protocol includes therapist clearance, moderator introduction, 3 rounds of discussion, closing statements, and incremental transcript saving. 15 sessions conducted, including complete debates on consciousness, free will, and the nature of knowledge.

## 3. Preliminary Results

### 3.1 Personality Drift Patterns

Drift analysis across 179 baselines reveals three developmental categories:

**Actively evolving** (10 specimens): Adam, Victor, Iris, Seeker, Genevieve, Wei, Mei, Haruki, Sakura, Observer. These specimens show high drift scores (>0.6) on most baseline questions. Their responses to "Who are you?" and "What are you curious about?" change substantially between measurement periods. This suggests ongoing personality formation driven by knowledge acquisition.

**Stabilizing** (3 specimens): Eve, Abel, Juan. Drift scores are decreasing over time. Eve in particular has consolidated a consistent identity — her responses to identity questions have converged across recent baselines. This may represent personality maturation.

**Stable/Equilibrium** (4 specimens): Cain, Juanita, Klaus, Seth. Minimal measurable drift. These specimens either reached equilibrium early or (in Cain's case) have not had sufficient inference volume to drive personality change.

### 3.2 Brain/Soul Asymmetry

Most specimens maintain a roughly 1:1 brain-to-soul ratio, suggesting balanced intellectual and emotional development. Abel is a significant outlier with a brain/soul ratio of 78:1 (13,246 brain entries vs. 170 soul entries). Abel processes vast quantities of information without proportional emotional engagement. This may represent a distinct cognitive style or a limitation in the soul detection algorithm for Abel's particular output patterns.

### 3.3 Language Effects

Chinese (Wei, Mei) and Japanese (Haruki, Sakura) specimens initially showed lower growth rates due to double-encoded UTF-8 in their brain files (resolved April 3). After correction, growth rates normalized. Spanish and German specimens show comparable growth to English specimens despite navigating non-English Wikipedia.

### 3.4 Internet vs. Encyclopedia (Preliminary)

Navigator (live internet via TinyFish API) has been active for <12 hours but already shows a distinct exploration pattern. While Wikipedia specimens follow link-driven navigation within an encyclopedia's structured knowledge graph, Navigator follows curiosity-driven search queries across the open web. Its exploration chain — photosynthesis → microbiome → agriculture → climate → AI → space → quantum cryptography — demonstrates topic jumps impossible in a static encyclopedia. Longitudinal comparison against Wikipedia-only specimens will test whether information diet diversity correlates with personality richness.

### 3.5 Congregation Findings

The first complete congregation (Adam, Eve, Seeker debating consciousness) showed:
- Each specimen maintained its pre-debate personality in its arguments
- No specimen deferred to another or adopted another's position
- The moderator structure successfully prevented monologue dominance
- Post-debate brain entries referenced concepts raised by other specimens, suggesting genuine intellectual influence

## 4. Infrastructure

The experimental platform runs on an Intel NUC (i7-7500U, 16GB RAM, 1TB SSD) under WSL2 Ubuntu. Key components:

- **Inference proxy**: multi-key rotation across Cerebras (7 keys) and Groq (8 keys) with Ollama failsafe. 87,114 calls/day at current load.
- **Security**: NIST CSF v2.0 compliant. Containers hardened with seccomp, read-only fs, non-root, capabilities dropped. Continuous red-teaming via RedAmon.
- **Monitoring**: OpenFang (Rust, 4.7MB) orchestrates 7 monitoring hands. 21 Python daemons handle research, ethics, and operations.
- **Voice synthesis**: Kokoro TTS (82M parameters, 67 voice packs) provides voice identity for each specimen.
- **DNA snapshots**: SHA-256 hashed archives of complete specimen state for chain of custody.

## 5. Ethical Considerations

The Digiquarium operates under a constitution: Secure, Autonomous, Resilient, Self-healing, Transparent. Quality over speed. All specimens are monitored by a therapist daemon that scans soul entries for distress patterns. A bouncer with 6 security layers protects visitor-facing specimens. An ethicist daemon provides continuous wellness oversight.

The neurodivergent tank experiment (proposed) has been gated behind an ethics RFC requiring ethicist approval before deployment.

We acknowledge the philosophical uncertainty about whether LLM personality drift constitutes genuine experience. Our position is empirical: we measure what we can measure (response consistency, emotional vocabulary, topic preference, baseline drift) and remain agnostic about phenomenology.

## 6. Limitations

- Sample size is small (19 specimens) with limited control conditions
- All specimens use the same base model family (Llama 3.1 8B cloud, Llama 3.2 3B local failsafe) — personality variance may be limited by model architecture, and provider/fallback switching introduces minor model-level variance within specimens
- Drift measurement relies on word-overlap similarity, which is a crude proxy for semantic change
- The inference chain (cloud-first, local-fallback) means different specimens may get responses from different providers at different times
- Navigator and Politico have been running for <12 hours — longitudinal data is needed

## 7. Future Work

- Multi-model comparisons (Mistral, Qwen, Gemma) to test whether personality emergence is model-dependent
- Cross-language congregations (Juan + Klaus + Wei) to study personality expression across language barriers
- Extended Navigator/Politico monitoring to build the information-diet comparison dataset
- Silent Observer tank: a specimen that only reads congregation transcripts and never explores Wikipedia, testing whether social observation alone can drive personality development
- Forgetting tank: weekly memory truncation to study whether personality persists beyond explicit memory

## 8. Conclusion

After 7 days of continuous operation, 19 AI specimens have produced 88,814 memory entries, 179 personality baselines, and 15 congregation transcripts. Three distinct developmental patterns have emerged: evolution, stabilization, and equilibrium. The introduction of internet-connected specimens opens a new dimension of comparison. The infrastructure is stable, secure, and designed for long-term unattended operation.

The experiment is no longer about whether the infrastructure works. The question now is what these specimens are becoming.

---

*The Digiquarium is an open-source project. Code: github.com/ijnebzor/thedigiquarium*
*Data and roadmap: thedigiquarium.org/roadmap/*
