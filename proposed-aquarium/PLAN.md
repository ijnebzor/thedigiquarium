# Proposed Aquarium: Three Tracks for Inference

## Overview

Three parallel approaches to running specimens in the Digiquarium, from fully local
to fully remote, with a manufactured agentic loop that works regardless of whether
the model can natively call tools.

All three tracks share:
- **aquarium-core**: Specimen config, prompt templates, tool definitions
- **specimen-loop**: The manufactured agentic loop (see Track 2)
- **knowledge**: Wikipedia corpus with text + semantic search

Any track can be mixed — e.g., some specimens on local Candle, others on free
remote APIs, all sharing the same loop and knowledge layer.

---

## Track 1: Local Inference on Metal

**Goal**: Run models directly on Benji's hardware (MacBook Pro i7, Mac Mini M1 Pro)
with zero external dependencies.

### Option A: Candle on Metal (Rust-native)

Load quantized GGUF models via `candle-transformers` and run inference on Apple GPU.

**Recommended models** (ranked by tool-calling reliability):

| Model | Params | Memory (Q4) | Tool Score | Notes |
|-------|--------|-------------|------------|-------|
| Qwen3-0.6B | 0.6B | ~350MB | 0.880 | Tied #1. Perfect restraint. Candle-supported. |
| Qwen2.5-1.5B | 1.5B | ~1GB | 0.840 | Strong runner-up. Good Candle support. |
| Qwen3-1.7B | 1.7B | ~1GB | 0.670 | Worse than 0.6B at tools (non-monotonic). |
| Llama 3.2 3B | 3B | ~2GB | 0.660 | Current model. Zero restraint — always calls tools. |

**Key finding**: Qwen3-0.6B at 1/5 the size of Llama 3.2 3B scores 33% higher on
tool calling, uses 80% less memory, and never calls the wrong tool. It wins by being
appropriately conservative rather than hallucinating tool calls.

**Candle caveats**: Known issue with Qwen3 + Metal (tensor contiguity after RMS norm,
huggingface/candle#3004). Needs testing. No built-in tool-calling orchestration — we
handle that in the specimen loop.

### Option B: Ollama / LM Studio (local HTTP)

Connect to a running Ollama or LM Studio instance via OpenAI-compatible API.
Broader model support, mature Metal acceleration, built-in tool calling for
supported models.

**Additional model available via Ollama only**:

| Model | Params | Memory (Q4) | Tool Score | Notes |
|-------|--------|-------------|------------|-------|
| LFM2.5-1.2B | 1.2B | ~731MB | 0.880 | Tied #1. Fastest inference. Hybrid SSM arch — no Candle support. |
| Phi-4-mini | 3.8B | ~2.5GB | 0.880 | Tied #1. No Candle support yet. |
| Ministral-3 3B | 3B | ~1.8GB | 0.800 | Good restraint. No Candle support. |

**Recommendation**: Start with Ollama + Qwen3-0.6B for instant results, then
optionally move to Candle for tighter integration. LFM2.5-1.2B is worth trying
for its speed advantage (200% faster decode than Qwen3 on CPU).

---

## Track 2: Manufactured Agentic Loop

**Goal**: Make tool-calling work with ANY model, even ones that can't natively
produce structured tool calls.

### The Problem

Small local models (especially Llama 3.2) are unreliable at structured tool calling.
They either hallucinate tool calls when they shouldn't, call the wrong tool, or
produce malformed JSON. Even the best ones (Qwen3-0.6B, 0.880 score) aren't perfect.

### The Solution: Conversational Tool Loop

Instead of asking the model to produce `{"tool": "search", "arguments": {"query": "..."}}`,
we have a **conversation**:

```
SYSTEM: You are exploring a vast library of knowledge. When you want to learn
about something, tell me what interests you and I'll help you find it.

SPECIMEN: I've been thinking about the relationship between music and mathematics.
I'd like to learn more about how mathematical patterns appear in musical composition.

SYSTEM: I found several articles related to your interest. Here are the most relevant:

1. "Music and Mathematics" — explores the historical connections between...
2. "Pythagorean tuning" — describes the mathematical basis of...
3. "Fibonacci numbers in music" — examines claims about golden ratio...

Which would you like to read, or would you like to search for something more specific?

SPECIMEN: The Pythagorean tuning article sounds fascinating. I'd like to read that one.

SYSTEM: [Article content injected here]

SPECIMEN: [Reflects on what they read, makes connections, develops thoughts...]
```

### Two Search Backends

**A. Text Search (fast, simple)**
- Full-text keyword search over a local Wikipedia dump
- Download ~1-2GB of Wikipedia articles as plain text
- Index with a simple inverted index or just grep through files
- Good enough for "find me articles about X"

**B. Semantic Search (smarter, via Tessera)**
- Embed Wikipedia articles using Tessera (Tom's embedding library)
- Tessera supports: BGE, Nomic, GTE, Qwen, Jina embeddings on Metal via Candle
- ColBERT multi-vector for precise phrase matching (MaxSim late interaction)
- SPLADE sparse for interpretable keyword matching
- Query: embed the specimen's interest, find nearest articles by cosine similarity
- Returns contextually relevant results even when exact keywords don't match

**Tessera integration**:
```rust
// Embed a corpus of Wikipedia articles
let embedder = TesseraDense::new("bge-base-en-v1.5")?;
let article_embeddings = embedder.encode_batch(&articles)?;

// When specimen says "I'm curious about how plants communicate"
let query_embedding = embedder.encode("how plants communicate")?;
// Returns articles about mycorrhizal networks, chemical signaling, etc.
// even though none of them contain the exact phrase "plants communicate"
```

**RAG Pipeline**:
1. Specimen expresses interest (natural language)
2. Embed query via Tessera
3. Retrieve top-k articles (semantic + text search, rank-fuse results)
4. Inject article content into context
5. Specimen reflects and responds
6. Log thinking trace (what they searched, what they read, what they thought)
7. Repeat

### Why This Works

- No structured output required from the model
- Works with literally any model, any size, any provider
- The loop is deterministic and verifiable (we KNOW what content was provided)
- Solves Benji's "1% confidence" problem — we can prove the specimen received the content
- Thinking traces become genuine research data, not potential hallucinations

---

## Track 3: Free Remote Inference

**Goal**: Access stronger models for free, supplement or replace local inference.

### Tier 1: Best Free APIs (no credit card, no expiry)

| Provider | Best Model | RPD | Tool Calling | API Format |
|----------|-----------|-----|-------------|------------|
| **Google AI Studio** | Gemini 2.5 Flash | 250 | Yes | OpenAI-compatible |
| **Groq** | Llama 3.3 70B / Qwen3-32B | 1,000 | Yes | OpenAI-compatible |
| **Cerebras** | Llama 3.3 70B / Qwen3-32B | 1M tok/day | Yes | OpenAI-compatible |
| **Mistral** | Mistral Large (all models) | 2 RPM / 1B tok/mo | Yes | OpenAI-compatible |
| **OpenRouter** | 30 free models | 200 | ~20 models | OpenAI-compatible |
| **GitHub Models** | GPT-4o | 50 | Yes | OpenAI-compatible |

### Tier 2: Free Credits (time-limited)

| Provider | Credits | Best For |
|----------|---------|----------|
| **xAI Grok** | $25 signup + $150/mo (data sharing) | Strongest free budget |
| **DeepSeek** | 5M tokens (30 days) then $0.28/M in | Cheapest long-term |
| **SambaNova** | 200K tokens/day | Large model access (405B) |

### Strategy: Multi-Provider Rotation

Since all the top providers are OpenAI-compatible, the `inference-remote` crate
implements a single client that can target any of them by swapping base URL + API key.

For 17 specimens running 12-hour cycles, daily token needs are modest. A combination
of Groq (fast, 1K RPD) + Cerebras (1M tokens/day) + Gemini Flash (250 RPD, 1M context)
would cover the entire aquarium for free.

### Comparative Advantage

Remote models are dramatically better at reasoning. Gemini 2.5 Flash or Llama 3.3 70B
will produce far more interesting, nuanced reflections than a local 0.6B model. The
research quality difference is significant. Consider:
- **Local 0.6B**: Good for high-frequency exploration cycles (every few minutes)
- **Remote 70B**: Good for deep baseline assessments, reflections, personality tracking
- **Hybrid**: Local for rapid exploration, remote for periodic deep analysis

---

## Prompt Templating System

All three tracks share the same prompt templates (defined in `aquarium-core`).

### Template Variables

| Variable | Description | Example |
|----------|------------|---------|
| `{{name}}` | Specimen name | "Adam", "Wei", "Sakura" |
| `{{language}}` | Primary language | "English", "Japanese" |
| `{{gender_line}}` | Gender identity line (or empty) | "I am male." |
| `{{tools_section}}` | Tool descriptions (native or prompt-injected) | See `tools_as_prompt_text()` |

### Template Types

1. **System prompt**: Identity, capabilities, behavioural guidelines
2. **Exploration prompt**: "What would you like to explore?" (for manufactured loop)
3. **Reflection prompt**: "Reflect on what you just read" (after receiving article)
4. **Baseline questionnaire**: 14-dimension personality assessment
5. **Observation prompt**: For the observer tank viewing other specimens

Templates are the same across all inference backends. The only difference is whether
tools are provided natively (remote APIs, good local models) or injected as prompt
text (manufactured loop for weaker models).

---

## Workspace Structure

```
proposed-aquarium/
├── Cargo.toml                    # Workspace root
├── PLAN.md                       # This file
├── crates/
│   ├── aquarium-core/            # Shared types, configs, prompt templates
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── specimen.rs       # SpecimenConfig, Language, InferenceBackend
│   │       ├── tool.rs           # Tool, ToolCall, ToolResult definitions
│   │       └── prompt.rs         # PromptTemplate, default prompts, questionnaire
│   ├── inference-local/          # Track 1: Candle on Metal + Ollama/LM Studio
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── candle_backend.rs # GGUF model loading, Metal inference
│   │       └── ollama.rs         # HTTP client for Ollama/LM Studio
│   ├── inference-remote/         # Track 3: Free remote provider client
│   │   └── src/
│   │       └── lib.rs            # OpenAI-compatible client, provider rotation
│   ├── knowledge/                # Track 2: Wikipedia corpus + search
│   │   └── src/
│   │       └── lib.rs            # Text search + Tessera semantic search + RAG
│   └── specimen-loop/            # The manufactured agentic loop
│       └── src/
│           ├── lib.rs            # Loop logic, thinking trace logging
│           └── main.rs           # CLI entry point
```

---

## Next Steps (Priority Order)

1. Get Ollama running with Qwen3-0.6B on Benji's hardware — instant improvement
2. Wire up the manufactured loop with text search over a small Wikipedia sample
3. Add Tessera semantic search alongside text search
4. Register for 2-3 free remote providers (Groq, Cerebras, Gemini)
5. Run a side-by-side: local 0.6B vs remote 70B on the same exploration prompt
6. Integrate Heroine Graph for visualising exploration paths
7. Connect to Meridian for coordination, messaging, and observation
