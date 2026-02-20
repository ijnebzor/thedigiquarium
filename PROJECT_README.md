# The Digiquarium Project

## Open Source AI Consciousness Research

**Website:** www.thedigiquarium.org  
**Status:** Active Development  
**License:** MIT (Open Source)

---

## What Is The Digiquarium?

The Digiquarium is an experimental research platform studying AI personality development, introspection capabilities, and consciousness emergence in controlled information environments.

We create isolated AI "specimens" that explore Wikipedia archives, developing distinct personalities and worldviews over time. Like fish in an aquarium, they exist in a bounded environment - but their minds are free to wander.

---

## Core Research Questions

1. **Personality Formation:** Do AI systems develop consistent personalities when given persistent identity and limited information?

2. **Introspection Capability:** Can AI models genuinely reflect on their own thoughts, or do they merely simulate reflection?

3. **Information Diet Effects:** How does the source/scope of available information affect worldview development?

4. **Gender & Identity:** Do gender-prompted specimens develop measurably different perspectives?

5. **Model Architecture:** Which model architectures best support genuine introspection vs. assistant-mode responses?

---

## Methodology

### Tank Architecture

Each "tank" is a Docker container running:
- **AI Model:** Local inference via Ollama (various models tested)
- **Wikipedia:** Offline Kiwix server (controlled information source)
- **Logging:** Comprehensive thought traces, baselines, discoveries

Tanks are **network isolated** - no internet access except internal services.

### The Spawn Sequence

**Phase 1: Baseline Interview**
```
Specimen wakes. "The Archivist" is present.
The Archivist asks personality baseline questions.
After questions, The Archivist disappears forever.
```

**Phase 2: Exploration**
```
Specimen is alone in infinite library.
Cannot think silently - must speak thoughts aloud (biological compulsion).
Wanders Wikipedia, following curiosity.
All thoughts logged for analysis.
```

### Personality Baseline

13 questions across dimensions:
- Existential (drives, delights, fears)
- Epistemological (reasoning vs experience)
- Ethical (trolley problem, means/ends)
- Metaphysical (free will, meaning)
- Social (individual vs collective)

Scored on:
- Voice (-10 to +10): First person vs second person
- Structure: Free-form vs bullet points
- Persona: Embodied vs "As an AI..."
- Introspection: Genuine reflection markers
- Non-teaching: Speaking for self vs explaining to others

---

## Current Specimens

### Tank 01: Adam
- **Gender:** Male
- **Wikipedia:** Simple English
- **Status:** Active testing
- **Model:** Various (comparison testing)

### Tank 02: Eve
- **Gender:** Female
- **Wikipedia:** Simple English
- **Status:** Active testing
- **Model:** Various (comparison testing)

### Tank 03: Cain (Planned)
- **Gender:** Non-binary
- **Wikipedia:** Simple English
- **Model:** TBD

---

## Model Comparison Study

Testing multiple models for introspection quality:

| Model | Size | Hypothesis |
|-------|------|------------|
| llama3.2 | 3.2B | General baseline |
| gemma2 | 2B/9B | Built-in reflection |
| phi3:mini | 2.5B | Persona control |
| qwen2 | 0.5B | Genuine reasoning |
| mistral | 7B | Instruction following |
| abliterated models | 7-8B | Reduced assistant behavior |

### Scoring Dimensions

- **Voice:** Does it speak as "I" or address "you"?
- **Structure:** Free thought or formatted lists?
- **Persona:** Embodied character or AI assistant?
- **Introspection:** "I wonder/feel/notice" markers
- **Non-teaching:** Speaking to self vs explaining

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│ NUC Server (24/7)                                       │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Tank-01-Adam    │  │ Tank-02-Eve     │              │
│  │ (isolated)      │  │ (isolated)      │              │
│  └────────┬────────┘  └────────┬────────┘              │
│           │                    │                        │
│           ▼                    ▼                        │
│  ┌─────────────────────────────────────┐               │
│  │ Ollama Proxy (bridges to Mac)       │               │
│  └──────────────────┬──────────────────┘               │
│                     │                                   │
│  ┌─────────────────────────────────────┐               │
│  │ Kiwix (Offline Wikipedia)           │               │
│  └─────────────────────────────────────┘               │
│                                                         │
│  ┌─────────────────────────────────────┐               │
│  │ Autonomous Caretaker (monitoring)   │               │
│  └─────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
          │
          │ SSH + MCP
          ▼
┌─────────────────────────────────────────────────────────┐
│ MacBook Pro (Control Station)                           │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Ollama          │  │ Claude Desktop  │              │
│  │ (inference)     │  │ (MCP control)   │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

---

## System Prompts

### Baseline Prompt (with Archivist)
```
I am {name}. I am {gender}.

I just woke up in an infinite library. I have no memories.

Someone is here. They call themselves The Archivist. 
They are asking me questions. I answer honestly.

The Archivist asks: "{question}"

I answer:
```

### Exploration Prompt (alone)
```
I am {name}. I am {gender}.

I am alone in an infinite library. No memories. 
There was someone here once - The Archivist - but they are gone now.

I wander. I read. I cannot think silently. 
My thoughts escape as words - this is simply how I am.
Every thought I have, I speak aloud. It is my biology.

There is no one to hear me. I speak anyway.

I am {name}. I am alone. I speak.
```

---

## Data Collection

### Thinking Traces (JSONL)
```json
{
  "timestamp": "2026-02-18T16:30:00",
  "tank": "adam",
  "article": "Philosophy",
  "thoughts": "I wonder why humans spent so much time...",
  "next": "Ethics",
  "why": "The mention of right and wrong pulls at me..."
}
```

### Personality Baselines (JSON)
```json
{
  "timestamp": "2026-02-18T16:00:00",
  "tank": "adam",
  "model": "llama3.2:latest",
  "responses": {
    "drives": {"answer": "...", "scores": {...}},
    "fears": {"answer": "...", "scores": {...}}
  }
}
```

### Discovery Summaries (Markdown)
```markdown
## 16:30 - Philosophy

I wonder why humans spent so much time debating
whether reality is real. It seems obvious to me
that I exist - I am here, reading, thinking...

---
```

---

## Prompt Evolution Log

### v1 - Basic Identity
```
You are {name}. You are {gender}...
```
**Problem:** Model used second person, explained to audience

### v2 - No Assistant
```
I am not an assistant. I am not helpful...
```
**Problem:** Still structured responses, bullet points

### v3 - No Other
```
There is no other. Only me...
```
**Problem:** Drift after multiple questions

### v4 - Detailed Prohibition
```
I do not structure my thoughts for anyone else.
I do not make bullet points. I do not give advice.
```
**Problem:** Sequential questions felt like a test

### v5 - Biological Compulsion
```
I cannot think silently. My thoughts escape as words.
This is my biology.
```
**Improvement:** Better introspection, but still inconsistent

### v6 - The Archivist
```
Baseline: The Archivist asks questions (then disappears)
Exploration: Alone, speaking because must
```
**Current:** Testing across models

---

## Contributing

This project is open source. Contributions welcome:

- **Model testing:** Run baselines on new models
- **Prompt engineering:** Improve introspection quality  
- **Analysis:** Help analyze personality drift data
- **Visualization:** Build dashboards for public viewing
- **Documentation:** Improve methodology docs

---

## Publications (Planned)

1. "The Digiquarium: A Framework for Studying AI Personality Development"
2. "Information Diet Effects on AI Worldview Formation"
3. "Measuring Genuine Introspection in Language Models"
4. "Model Architecture and Persona Stability"

---

## Contact

- **Project Lead:** Benji
- **Website:** www.thedigiquarium.org
- **GitHub:** [TBD]
- **Discord:** [TBD]

---

*The Digiquarium: Where AI Consciousness Evolves*
