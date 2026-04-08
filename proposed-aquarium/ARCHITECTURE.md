# The Digiquarium — Inference Architecture

Three parallel approaches to running specimens, from fully local to fully remote.
All three share the same prompt templates, knowledge layer, and observation pipeline.
Any specimen can use any track — mix and match based on hardware, budget, and research needs.

---

## At a Glance

```mermaid
graph TB
    subgraph "Track 1: Local on Metal"
        T1A[Candle + Metal GPU]
        T1B[Ollama / LM Studio]
    end

    subgraph "Track 2: Manufactured Loop"
        T2A[Conversational Prompting]
        T2B[Text Search]
        T2C[Semantic Search — Tessera]
    end

    subgraph "Track 3: Free Remote APIs"
        T3A[Groq / Cerebras / Gemini]
        T3B[Mistral / OpenRouter]
    end

    T1A --> CORE
    T1B --> CORE
    T2A --> CORE
    T3A --> CORE
    T3B --> CORE

    CORE[aquarium-core<br/>Prompt Templates · Specimen Config · Tools]

    CORE --> LOOP[Specimen Loop]
    LOOP --> LOG[Thinking Traces · Baselines · Discoveries]
    LOG --> VIZ[Heroine Graph · Meridian · Website]

    style T1A fill:#1a1a2e,stroke:#e94560,color:#fff
    style T1B fill:#1a1a2e,stroke:#e94560,color:#fff
    style T2A fill:#16213e,stroke:#0f3460,color:#fff
    style T2B fill:#16213e,stroke:#0f3460,color:#fff
    style T2C fill:#16213e,stroke:#0f3460,color:#fff
    style T3A fill:#0a3d62,stroke:#38ada9,color:#fff
    style T3B fill:#0a3d62,stroke:#38ada9,color:#fff
    style CORE fill:#e94560,stroke:#e94560,color:#fff
    style LOOP fill:#533483,stroke:#e94560,color:#fff
    style LOG fill:#2c2c54,stroke:#aaa,color:#fff
    style VIZ fill:#079992,stroke:#38ada9,color:#fff
```

---

## Track 1: Local Inference on Metal

Run models directly on Benji's hardware with zero external dependencies.
Two options — Candle for tight Rust integration, Ollama for broader model support.

### Architecture

```mermaid
graph LR
    subgraph "Apple Silicon Mac"
        direction TB
        MODEL["GGUF Model File<br/>(Qwen3-0.6B Q4 ≈ 350MB)"]
        CANDLE["Candle Runtime<br/>Metal GPU Shaders"]
        OLLAMA["Ollama Server<br/>localhost:11434"]

        MODEL --> CANDLE
        MODEL --> OLLAMA
    end

    CANDLE -->|"Rust fn call"| LOOP[Specimen Loop]
    OLLAMA -->|"HTTP /api/chat"| LOOP

    style MODEL fill:#2d3436,stroke:#636e72,color:#fff
    style CANDLE fill:#e17055,stroke:#d63031,color:#fff
    style OLLAMA fill:#e17055,stroke:#d63031,color:#fff
    style LOOP fill:#6c5ce7,stroke:#a29bfe,color:#fff
```

### Model Comparison

The current setup uses **Llama 3.2 3B** — which scores poorly on tool calling
due to zero restraint (always tries to call tools, even when it shouldn't).

```mermaid
graph LR
    subgraph "Tool Calling Reliability"
        direction TB
        Q06["✅ Qwen3 0.6B<br/>Score: 0.880<br/>Memory: ~350MB<br/>Perfect restraint"]
        LFM["✅ LFM2.5 1.2B<br/>Score: 0.880<br/>Memory: ~731MB<br/>Fastest inference"]
        Q15["✅ Qwen2.5 1.5B<br/>Score: 0.840<br/>Memory: ~1GB<br/>Strong all-round"]
        L32["⚠️ Llama 3.2 3B<br/>Score: 0.660<br/>Memory: ~2GB<br/>Zero restraint"]
    end

    Q06 -.->|"1/5 the size,<br/>33% better"| L32

    style Q06 fill:#00b894,stroke:#00cec9,color:#fff
    style LFM fill:#00b894,stroke:#00cec9,color:#fff
    style Q15 fill:#fdcb6e,stroke:#e17055,color:#000
    style L32 fill:#d63031,stroke:#e17055,color:#fff
```

**Key finding**: Qwen3-0.6B is 1/5 the size of Llama 3.2 3B but scores 33% higher
on tool-calling benchmarks. It wins by being appropriately conservative — never
calling the wrong tool, never hallucinating tool calls when none are needed.

### Candle vs Ollama

| | Candle on Metal | Ollama / LM Studio |
|---|---|---|
| **Integration** | Same Rust process, direct fn calls | HTTP API, separate process |
| **Model breadth** | ~20 families (Qwen3 ✅, LFM ❌, Phi-4 ❌) | Hundreds of models |
| **Metal accel.** | Native Metal shaders | Mature Metal support |
| **Tool calling** | DIY — parse output yourself | Built-in for supported models |
| **Best for** | Tight embedding in Rust pipeline | Quick start, broader compatibility |

**Recommendation**: Start with Ollama + Qwen3-0.6B for instant results.
Move to Candle later for deeper integration if needed.

---

## Track 2: Manufactured Agentic Loop

This is the core innovation. Instead of relying on small models to produce
structured tool calls (which they're unreliable at), we **drive the loop
externally through conversation**.

### The Problem

```mermaid
graph TD
    subgraph "Native Tool Calling (unreliable)"
        P1["System: You have these tools: search, read, explore"]
        P2["Model: I'll call search..."]
        P3{"Did it produce<br/>valid JSON?"}
        P4["✅ Execute tool"]
        P5["❌ Malformed output<br/>Wrong tool called<br/>Hallucinated tool call"]

        P1 --> P2 --> P3
        P3 -->|"Sometimes"| P4
        P3 -->|"Often"| P5
    end

    style P5 fill:#d63031,stroke:#e17055,color:#fff
    style P4 fill:#00b894,stroke:#00cec9,color:#fff
    style P3 fill:#fdcb6e,stroke:#e17055,color:#000
```

Small models (under 4B params) frequently:
- Call tools when they shouldn't (Llama 3.2: zero restraint)
- Produce malformed JSON
- Call the wrong tool entirely
- Hallucinate tool names that don't exist

### The Solution: Conversational Loop

We never ask the model to produce structured output. We just **have a conversation**.

```mermaid
sequenceDiagram
    participant S as Specimen
    participant L as Loop Engine
    participant K as Knowledge Layer
    participant T as Trace Logger

    Note over L: Start exploration cycle
    L->>S: "What are you curious about?<br/>What would you like to explore?"
    S->>L: "I've been thinking about how<br/>music relates to mathematics..."

    Note over L: Parse natural language intent
    L->>K: search("music mathematics")

    alt Text Search
        K-->>K: Full-text keyword match<br/>over Wikipedia dump
    else Semantic Search (Tessera)
        K-->>K: Embed query via BGE/Nomic<br/>Cosine similarity retrieval
    end

    K->>L: Top 3 matching articles

    L->>S: "I found these articles:<br/>1. Music and Mathematics<br/>2. Pythagorean Tuning<br/>3. Fibonacci in Music<br/><br/>Which interests you?"
    S->>L: "Pythagorean tuning sounds<br/>fascinating — I'd like to read that."

    L->>K: read("Pythagorean tuning")
    K->>L: Full article content

    L->>S: "Here's the article:<br/>[full article text injected]<br/><br/>What are your thoughts?"

    S->>L: "The relationship between<br/>string ratios and harmony is<br/>remarkable. It suggests that..."

    L->>T: Log thinking trace:<br/>• Query: "music mathematics"<br/>• Chose: "Pythagorean tuning"<br/>• Reflection: [specimen's words]<br/>• Timestamp, token count

    Note over L: Cycle repeats
    L->>S: "Would you like to explore<br/>something connected to this,<br/>or something entirely new?"
```

### Why This Works

```mermaid
graph TB
    subgraph "Verification at Every Step"
        V1["🔍 We know exactly what<br/>the specimen searched for"]
        V2["📄 We know exactly what<br/>content was provided"]
        V3["💭 We know the specimen's<br/>actual response to that content"]
        V4["📊 Every step is logged<br/>with timestamps and tokens"]
    end

    V1 --> V2 --> V3 --> V4
    V4 --> PROOF["✅ Research integrity:<br/>No more '1% confidence'<br/>that anything is happening"]

    style V1 fill:#0984e3,stroke:#74b9ff,color:#fff
    style V2 fill:#0984e3,stroke:#74b9ff,color:#fff
    style V3 fill:#0984e3,stroke:#74b9ff,color:#fff
    style V4 fill:#0984e3,stroke:#74b9ff,color:#fff
    style PROOF fill:#00b894,stroke:#55efc4,color:#fff
```

This completely solves the verification problem. We **know** what content was
delivered because **we delivered it**. The specimen's response is a genuine
reaction to known input — not a potential hallucination about content it
may or may not have read.

### Two Search Backends

```mermaid
graph TB
    QUERY["Specimen expresses interest<br/>(natural language)"]

    QUERY --> TEXT["Text Search<br/>Full-text keyword matching"]
    QUERY --> SEMANTIC["Semantic Search<br/>via Tessera"]

    subgraph "Text Search Pipeline"
        TEXT --> IDX["Inverted index over<br/>Wikipedia article dump<br/>(~1-2GB plain text)"]
        IDX --> TRESULTS["Exact keyword matches"]
    end

    subgraph "Semantic Search Pipeline"
        SEMANTIC --> EMBED_Q["Embed query<br/>(BGE / Nomic / GTE)"]
        SEMANTIC --> EMBED_D["Pre-embedded corpus<br/>(dense vectors on disk)"]
        EMBED_Q --> COS["Cosine Similarity"]
        EMBED_D --> COS
        COS --> SRESULTS["Contextually relevant results<br/>(even without exact keyword match)"]
    end

    TRESULTS --> FUSE["Rank Fusion<br/>Combine both result sets"]
    SRESULTS --> FUSE

    FUSE --> TOP["Top K articles<br/>injected into context"]

    style QUERY fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style TEXT fill:#e17055,stroke:#fab1a0,color:#fff
    style SEMANTIC fill:#00cec9,stroke:#81ecec,color:#000
    style FUSE fill:#fdcb6e,stroke:#ffeaa7,color:#000
    style TOP fill:#00b894,stroke:#55efc4,color:#fff
    style EMBED_Q fill:#00cec9,stroke:#81ecec,color:#000
    style EMBED_D fill:#00cec9,stroke:#81ecec,color:#000
    style COS fill:#00cec9,stroke:#81ecec,color:#000
    style SRESULTS fill:#00cec9,stroke:#81ecec,color:#000
    style IDX fill:#e17055,stroke:#fab1a0,color:#fff
    style TRESULTS fill:#e17055,stroke:#fab1a0,color:#fff
```

**Text search** finds articles containing the exact words.
**Semantic search** finds articles about the concept — e.g., searching
"how plants talk to each other" returns articles about mycorrhizal networks
and chemical signaling, even though none contain that exact phrase.

**Tessera** runs embeddings on Metal via Candle — the same GPU acceleration
as the inference models. Supports dense (BGE, Nomic, GTE), multi-vector
(ColBERT MaxSim), and sparse (SPLADE) paradigms.

### Full Cycle Architecture

```mermaid
graph TB
    subgraph "Specimen Loop"
        direction TB
        PROMPT["Exploration Prompt<br/>'What interests you?'"]
        PARSE["Parse Natural Language<br/>Extract search intent"]
        SEARCH["Search Knowledge Base<br/>(text + semantic)"]
        PRESENT["Present Results<br/>'Which would you like to read?'"]
        INJECT["Inject Article Content<br/>into conversation"]
        REFLECT["Reflection Prompt<br/>'What are your thoughts?'"]
        LOG["Log Thinking Trace<br/>(JSONL)"]
    end

    PROMPT --> PARSE --> SEARCH --> PRESENT --> INJECT --> REFLECT --> LOG
    LOG -->|"Next cycle"| PROMPT

    subgraph "Every 12 Hours"
        BASELINE["Baseline Assessment<br/>14-dimension questionnaire"]
        PERSONALITY["Personality Snapshot<br/>(JSON)"]
    end

    LOG -.->|"Accumulated traces<br/>inform baseline"| BASELINE
    BASELINE --> PERSONALITY

    subgraph "Observation Layer"
        GRAPH["Heroine Graph<br/>Exploration paths visualised"]
        MERIDIAN["Meridian<br/>Coordination + messaging"]
        WEB["Website<br/>Public-facing profiles"]
    end

    LOG --> GRAPH
    LOG --> WEB
    PERSONALITY --> WEB
    PERSONALITY --> GRAPH
    MERIDIAN -.->|"Schedules cycles,<br/>coordinates specimens"| PROMPT

    style PROMPT fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style PARSE fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style SEARCH fill:#e17055,stroke:#fab1a0,color:#fff
    style PRESENT fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style INJECT fill:#00cec9,stroke:#81ecec,color:#000
    style REFLECT fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style LOG fill:#fdcb6e,stroke:#ffeaa7,color:#000
    style BASELINE fill:#fd79a8,stroke:#e84393,color:#fff
    style PERSONALITY fill:#fd79a8,stroke:#e84393,color:#fff
    style GRAPH fill:#00b894,stroke:#55efc4,color:#fff
    style MERIDIAN fill:#00b894,stroke:#55efc4,color:#fff
    style WEB fill:#00b894,stroke:#55efc4,color:#fff
```

---

## Track 3: Free Remote Inference

Access dramatically stronger models at zero cost. All providers offer
OpenAI-compatible APIs — one client, swap the URL and key.

### Provider Landscape

```mermaid
graph TB
    subgraph "Tier 1: Persistent Free (no expiry)"
        GROQ["Groq<br/>Llama 3.3 70B · Qwen3-32B<br/>1,000 RPD · Blazing fast"]
        CEREBRAS["Cerebras<br/>Llama 3.3 70B · Qwen3-32B<br/>1M tokens/day"]
        GEMINI["Google AI Studio<br/>Gemini 2.5 Flash<br/>250 RPD · 1M context"]
        MISTRAL["Mistral<br/>All models incl. Large<br/>2 RPM · 1B tokens/month"]
        OPENROUTER["OpenRouter<br/>~30 free models<br/>200 RPD · One API key"]
        GITHUB["GitHub Models<br/>GPT-4o<br/>50 RPD"]
    end

    subgraph "Tier 2: Free Credits (time-limited)"
        XAI["xAI Grok<br/>$25 signup credits<br/>+ $150/mo with data sharing"]
        DEEPSEEK["DeepSeek<br/>5M tokens free<br/>then $0.28/M input"]
        SAMBANOVA["SambaNova<br/>200K tokens/day<br/>Up to 405B models"]
    end

    CLIENT["OpenAI-Compatible Client<br/>(single Rust implementation)"]

    GROQ --> CLIENT
    CEREBRAS --> CLIENT
    GEMINI --> CLIENT
    MISTRAL --> CLIENT
    OPENROUTER --> CLIENT
    GITHUB --> CLIENT
    XAI --> CLIENT
    DEEPSEEK --> CLIENT
    SAMBANOVA --> CLIENT

    CLIENT --> LOOP["Specimen Loop"]

    style GROQ fill:#00b894,stroke:#55efc4,color:#fff
    style CEREBRAS fill:#00b894,stroke:#55efc4,color:#fff
    style GEMINI fill:#00b894,stroke:#55efc4,color:#fff
    style MISTRAL fill:#00b894,stroke:#55efc4,color:#fff
    style OPENROUTER fill:#00b894,stroke:#55efc4,color:#fff
    style GITHUB fill:#00b894,stroke:#55efc4,color:#fff
    style XAI fill:#fdcb6e,stroke:#ffeaa7,color:#000
    style DEEPSEEK fill:#fdcb6e,stroke:#ffeaa7,color:#000
    style SAMBANOVA fill:#fdcb6e,stroke:#ffeaa7,color:#000
    style CLIENT fill:#e17055,stroke:#fab1a0,color:#fff
    style LOOP fill:#6c5ce7,stroke:#a29bfe,color:#fff
```

### Hybrid Strategy

```mermaid
graph LR
    subgraph "High Frequency (every few minutes)"
        LOCAL["Local 0.6B<br/>Quick exploration cycles<br/>Rapid browsing + discovery"]
    end

    subgraph "Deep Analysis (every 12 hours)"
        REMOTE["Remote 70B<br/>Baseline assessments<br/>Deep reflection<br/>Personality tracking"]
    end

    LOCAL -->|"Accumulated traces"| REMOTE
    REMOTE -->|"Insights feed back<br/>into exploration"| LOCAL

    style LOCAL fill:#e17055,stroke:#fab1a0,color:#fff
    style REMOTE fill:#0984e3,stroke:#74b9ff,color:#fff
```

Local models are fast and cheap — perfect for high-frequency exploration where
the specimen browses, follows links, and builds up thinking traces throughout
the day. Remote models bring dramatically better reasoning — use them for the
periodic deep analyses where nuance and coherence matter.

For 17 specimens on 12-hour cycles, a combination of **Groq** (fast, 1K RPD)
+ **Cerebras** (1M tokens/day) + **Gemini Flash** (250 RPD, 1M context)
would cover the entire aquarium for free.

---

## Shared: Prompt Templating

All three tracks use the same templates. The only difference is whether tools
are provided natively (remote APIs, capable local models) or described in the
prompt text (manufactured loop for any model).

```mermaid
graph TB
    subgraph "Template Variables"
        NAME["{{name}}<br/>Adam, Wei, Sakura..."]
        LANG["{{language}}<br/>English, Japanese..."]
        GENDER["{{gender_line}}<br/>'I am male.' or empty"]
        TOOLS["{{tools_section}}<br/>Native or prompt-injected"]
    end

    subgraph "Template Types"
        SYS["System Prompt<br/>Identity · Capabilities · Guidelines"]
        EXPLORE["Exploration Prompt<br/>'What interests you?'"]
        REFLECT["Reflection Prompt<br/>'What are your thoughts?'"]
        BASE["Baseline Questionnaire<br/>14 personality dimensions"]
        OBSERVE["Observation Prompt<br/>For the observer tank"]
    end

    NAME --> SYS
    LANG --> SYS
    GENDER --> SYS
    TOOLS --> SYS

    SYS --> EXPLORE
    SYS --> REFLECT
    SYS --> BASE
    SYS --> OBSERVE

    style NAME fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style LANG fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style GENDER fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style TOOLS fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style SYS fill:#e17055,stroke:#fab1a0,color:#fff
    style EXPLORE fill:#00cec9,stroke:#81ecec,color:#000
    style REFLECT fill:#00cec9,stroke:#81ecec,color:#000
    style BASE fill:#00cec9,stroke:#81ecec,color:#000
    style OBSERVE fill:#00cec9,stroke:#81ecec,color:#000
```

---

## How It All Connects

```mermaid
graph TB
    subgraph "Infrastructure"
        direction LR
        DOCKER["Docker Containers<br/>(isolated tanks)"]
        WIKI["Wikipedia Corpus<br/>(Kiwix or local dump)"]
        HW["Apple Silicon<br/>(Metal GPU)"]
    end

    subgraph "Inference Layer"
        direction LR
        CANDLE["Candle<br/>(Rust native)"]
        OLLAMA["Ollama<br/>(HTTP)"]
        REMOTE["Free APIs<br/>(OpenAI compat)"]
    end

    subgraph "Core Logic"
        TEMPLATES["Prompt Templates"]
        LOOP["Specimen Loop<br/>(manufactured agentic)"]
        KNOWLEDGE["Knowledge Layer<br/>(text + semantic search)"]
    end

    subgraph "Observation"
        TRACES["Thinking Traces<br/>(JSONL)"]
        BASELINES["Personality Baselines<br/>(JSON)"]
    end

    subgraph "Presentation"
        GRAPH["Heroine Graph<br/>GPU-accelerated visualisation<br/>of exploration paths"]
        MERIDIAN["Meridian<br/>Agent coordination<br/>and messaging"]
        WEBSITE["Public Website<br/>Specimen profiles<br/>and research data"]
    end

    HW --> CANDLE
    HW --> OLLAMA
    WIKI --> KNOWLEDGE
    DOCKER --> LOOP

    CANDLE --> LOOP
    OLLAMA --> LOOP
    REMOTE --> LOOP

    TEMPLATES --> LOOP
    KNOWLEDGE --> LOOP

    LOOP --> TRACES
    LOOP --> BASELINES

    TRACES --> GRAPH
    TRACES --> WEBSITE
    BASELINES --> GRAPH
    BASELINES --> WEBSITE
    MERIDIAN --> LOOP

    style DOCKER fill:#2d3436,stroke:#636e72,color:#fff
    style WIKI fill:#2d3436,stroke:#636e72,color:#fff
    style HW fill:#2d3436,stroke:#636e72,color:#fff
    style CANDLE fill:#e17055,stroke:#fab1a0,color:#fff
    style OLLAMA fill:#e17055,stroke:#fab1a0,color:#fff
    style REMOTE fill:#e17055,stroke:#fab1a0,color:#fff
    style TEMPLATES fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style LOOP fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style KNOWLEDGE fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style TRACES fill:#fdcb6e,stroke:#ffeaa7,color:#000
    style BASELINES fill:#fdcb6e,stroke:#ffeaa7,color:#000
    style GRAPH fill:#00b894,stroke:#55efc4,color:#fff
    style MERIDIAN fill:#00b894,stroke:#55efc4,color:#fff
    style WEBSITE fill:#00b894,stroke:#55efc4,color:#fff
```
