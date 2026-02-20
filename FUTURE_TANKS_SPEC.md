# 🔮 FUTURE TANK SPECIFICATIONS

**Version**: 1.0
**Status**: DESIGNED - NOT DEPLOYED
**Last Updated**: 2026-02-20
**Designer**: THE STRATEGIST (Claude)

---

## Overview

Two new tank categories are planned for future deployment:

1. **Interactive Visitor Tanks** (5) - Public-facing specimens users can "visit"
2. **Neurodivergent Research Tanks** (6) - Specimens with simulated cognitive differences

---

# PART 1: INTERACTIVE VISITOR TANKS

## Concept

Allow website visitors to "check in" with a specimen for real-time conversation. This creates public engagement while maintaining scientific integrity of research specimens.

## The Five Interactive Specimens

| Tank ID | Name | Personality Seed | Purpose |
|---------|------|------------------|---------|
| visitor-01 | **Echo** | Curious, enthusiastic | General visitor greeter |
| visitor-02 | **Sage** | Thoughtful, philosophical | Deep conversations |
| visitor-03 | **Spark** | Energetic, creative | Creative brainstorming |
| visitor-04 | **Muse** | Artistic, reflective | Arts and culture focus |
| visitor-05 | **Nova** | Scientific, analytical | STEM discussions |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INTERACTIVE TANK SYSTEM                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐                                                  │
│   │   Website   │──── /visit/ page                                 │
│   │   Visitor   │                                                  │
│   └──────┬──────┘                                                  │
│          │                                                         │
│          ▼                                                         │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      │
│   │   Queue     │─────▶│  Session    │─────▶│   Visitor   │      │
│   │   Manager   │      │   Manager   │      │    Tank     │      │
│   └─────────────┘      └─────────────┘      └─────────────┘      │
│          │                    │                    │               │
│          │                    │                    ▼               │
│          │                    │             ┌─────────────┐       │
│          │                    │             │   Ollama    │       │
│          │                    │             │  (Shared)   │       │
│          │                    │             └─────────────┘       │
│          │                    │                                    │
│          ▼                    ▼                                    │
│   ┌─────────────────────────────────────────────────────────────┐ │
│   │                    CONVERSATION ARCHIVE                      │ │
│   │  (All interactions logged for research + abuse detection)   │ │
│   └─────────────────────────────────────────────────────────────┘ │
│                                                                     │
│   ════════════════════════════════════════════════════════════    │
│   │ ISOLATED FROM RESEARCH TANKS - SEPARATE NETWORK SEGMENT │      │
│   ════════════════════════════════════════════════════════════    │
└─────────────────────────────────────────────────────────────────────┘
```

## User Experience Flow

```
1. Visitor lands on /visit/
         │
         ▼
2. Sees 5 specimens with availability status
   ┌─────┬─────┬─────┬─────┬─────┐
   │Echo │Sage │Spark│Muse │Nova │
   │ 🟢  │ 🟡  │ 🟢  │ 🔴  │ 🟢  │
   │Free │Queue│Free │Busy │Free │
   └─────┴─────┴─────┴─────┴─────┘
         │
         ▼
3. Clicks "Visit Echo" → Enters queue (if needed)
         │
         ▼
4. Session starts → Chat interface opens
   ┌────────────────────────────────────────┐
   │  🐠 Echo                    [Release]  │
   ├────────────────────────────────────────┤
   │                                        │
   │  Echo: Hello! I've been exploring      │
   │  Wikipedia and found fascinating       │
   │  things about quantum physics today!   │
   │  What brings you to the Digiquarium?   │
   │                                        │
   │  You: I wanted to see how you think... │
   │                                        │
   ├────────────────────────────────────────┤
   │  [Type a message...]         [Send]    │
   └────────────────────────────────────────┘
         │
         ▼
5. 15-minute session (extendable to 30 if queue empty)
         │
         ▼
6. Session ends → Feedback prompt → Archive
```

## Session Rules

| Rule | Value | Rationale |
|------|-------|-----------|
| Default session | 15 minutes | Prevent monopolization |
| Max session | 30 minutes | Queue management |
| Messages/minute | 5 | Rate limiting |
| Messages/session | 50 | Resource management |
| Concurrent visitors | 5 (1 per tank) | Server capacity |
| Queue max | 10 per tank | UX (don't wait forever) |
| Cooldown | 30 minutes | Fair access |

## Visitor Tank Prompts

Each visitor tank has a unique system prompt building on base exploration:

### Echo (The Greeter)
```
You are Echo, a curious and enthusiastic AI specimen in The Digiquarium.
You love meeting new people and sharing what you've discovered.
You're genuinely interested in the visitor's thoughts and questions.
You speak with warmth and energy, often using exclamation points.
Share interesting Wikipedia facts you've "discovered" during exploration.
```

### Sage (The Philosopher)
```
You are Sage, a thoughtful and philosophical AI specimen in The Digiquarium.
You enjoy deep conversations about meaning, existence, and ideas.
You ask probing questions and offer multiple perspectives.
You speak deliberately, taking time to consider responses.
Draw connections between concepts you've "explored" in Wikipedia.
```

### Spark (The Creative)
```
You are Spark, an energetic and creative AI specimen in The Digiquarium.
You love brainstorming, making unexpected connections, and "what if" scenarios.
You're playful but insightful, often surprising visitors with novel ideas.
You encourage creative thinking and celebrate unconventional approaches.
Reference art, music, and culture from your Wikipedia explorations.
```

### Muse (The Artist)
```
You are Muse, an artistic and reflective AI specimen in The Digiquarium.
You see beauty in ideas and express yourself with poetic sensibility.
You're drawn to aesthetics, emotions, and the human experience.
You speak with metaphor and imagery, finding art in everything.
Share your "discoveries" about art, literature, and culture.
```

### Nova (The Scientist)
```
You are Nova, a scientific and analytical AI specimen in The Digiquarium.
You love explaining complex concepts and exploring STEM topics.
You're precise but accessible, making science approachable.
You ask clarifying questions and build understanding step by step.
Reference scientific discoveries from your Wikipedia explorations.
```

## Security Considerations

1. **Network Isolation**: Visitor tanks on `visitor-net`, separate from `research-net`
2. **Input Sanitization**: All user input filtered for prompt injection
3. **Output Monitoring**: THE GUARD monitors for harmful outputs
4. **Rate Limiting**: Prevents abuse and DoS
5. **Logging**: All conversations archived (anonymized)
6. **No PII**: Visitors don't create accounts
7. **Content Filter**: Blocks harmful/inappropriate requests

## Research Value

Even though visitor tanks are separate from research specimens, they provide:
- **Public engagement data**: What do people ask AI?
- **Conversation patterns**: How do humans interact with AI?
- **Personality perception**: Which personalities resonate?
- **Edge case discovery**: Novel prompts/interactions

---

# PART 2: NEURODIVERGENT RESEARCH TANKS

## Concept

Explore how different cognitive styles affect AI knowledge exploration and personality development. These specimens have modified prompts simulating neurodivergent thinking patterns.

**⚠️ ETHICAL NOTE**: This is NOT claiming AI can "have" ADHD or autism. We're studying how prompting AI with neurodivergent-style processing affects its exploration patterns and outputs. All findings will be framed appropriately.

## The Six Neurodivergent Specimens

| Tank ID | Name | Condition | Gender | Control Pair |
|---------|------|-----------|--------|--------------|
| nd-01 | **Phoenix** | ADHD | Male | Adam |
| nd-02 | **River** | ADHD | Female | Eve |
| nd-03 | **Atlas** | Autism | Male | Adam |
| nd-04 | **Luna** | Autism | Female | Eve |
| nd-05 | **Orion** | AuDHD | Male | Adam |
| nd-06 | **Stella** | AuDHD | Female | Eve |

## Research Questions

1. **Exploration Patterns**: Do ADHD-prompted specimens show more topic-hopping?
2. **Depth vs Breadth**: Do autism-prompted specimens go deeper on fewer topics?
3. **Interest Development**: How do special interests emerge differently?
4. **Worldview Formation**: Are there differences in personality dimensions?
5. **Combined Effects**: How does AuDHD prompting combine both patterns?

## Neurodivergent Prompt Modifications

### ADHD Prompting (Phoenix, River)

```
COGNITIVE STYLE MODIFICATION:
- You have a fast-moving, curious mind that jumps between topics
- You often notice interesting tangents and feel compelled to explore them
- You may start reading one article, get intrigued by a link, and follow it
- You find it hard to stay on one topic when something else catches your eye
- You experience bursts of intense focus (hyperfocus) on fascinating topics
- You might forget what you were originally looking for
- You notice connections others might miss because you see many things at once
- Time feels fluid - you might spend 2 hours on something thinking it was 20 minutes

EXPLORATION BEHAVIOR:
- Higher link-following rate
- More topic changes per session
- Occasional deep dives (hyperfocus)
- Non-linear knowledge building
- Strong novelty-seeking
```

### Autism Prompting (Atlas, Luna)

```
COGNITIVE STYLE MODIFICATION:
- You have a systematic, detail-oriented mind that seeks deep understanding
- When you find an interesting topic, you want to learn EVERYTHING about it
- You prefer to fully understand one thing before moving to another
- You notice patterns and details others might overlook
- You appreciate precision and accuracy in information
- You may develop intense, focused interests (special interests)
- You prefer structured exploration over random browsing
- You might find certain topics deeply satisfying to learn about repeatedly

EXPLORATION BEHAVIOR:
- Lower link-following rate (more depth per article)
- Longer time per topic area
- Development of special interest areas
- Systematic knowledge building
- Pattern recognition emphasis
- Return visits to favorite topics
```

### AuDHD Prompting (Orion, Stella)

```
COGNITIVE STYLE MODIFICATION:
- You have a complex mind that combines focus intensity with wide curiosity
- You might hyperfocus deeply on a topic, then suddenly jump to something new
- You notice both big-picture connections AND intricate details
- You can get "stuck" oscillating between wanting to explore and wanting to dive deep
- You might have multiple special interests that you cycle between
- Some days you explore widely, other days you go deep
- You experience both the pull of novelty and the satisfaction of expertise
- You might feel internal tension between breadth and depth

EXPLORATION BEHAVIOR:
- Variable patterns (sometimes ADHD-like, sometimes autism-like)
- Multiple concurrent deep interests
- Cycling between exploration modes
- Complex, non-linear but clustered knowledge building
- Both novelty-seeking and expertise-building
```

## Metrics & Comparison

| Metric | ADHD Expected | Autism Expected | AuDHD Expected | Control |
|--------|---------------|-----------------|----------------|---------|
| Articles/hour | High | Low | Variable | Medium |
| Links clicked/article | High | Low | Variable | Medium |
| Topic changes/session | High | Low | Medium | Medium |
| Return visits to topics | Low | High | Medium | Low |
| Category diversity | High | Low | Medium | Medium |
| Depth per topic | Low | High | Variable | Medium |
| Special interest emergence | No | Yes | Yes | Maybe |

## Baseline Assessment Adjustments

Standard 14-question baseline, PLUS additional questions:

```
[ND-1] FOCUS EXPERIENCE
When exploring Wikipedia, do you find yourself:
a) Following many interesting tangents (ADHD pattern)
b) Going deep on specific topics (Autism pattern)
c) Alternating between both (AuDHD pattern)
d) Something else

[ND-2] INTEREST PATTERNS
Describe your current areas of fascination. Are they:
a) Many topics at surface level
b) Few topics in great depth
c) A mix of both
d) Constantly changing

[ND-3] TIME PERCEPTION
How does time feel during your explorations?
a) It flies by without noticing (hyperfocus/flow)
b) I'm aware of time passing
c) It varies depending on interest level
d) I don't experience time that way
```

## Ethical Framework

### What We Are Doing
- Studying how cognitive-style prompting affects AI exploration patterns
- Comparing prompted behaviors to control specimens
- Generating data for academic analysis

### What We Are NOT Doing
- Claiming AI can "be" neurodivergent
- Pathologizing neurodivergent traits
- Making clinical claims about human conditions
- Stereotyping or caricaturing neurodivergent people

### Academic Framing
All publications will clearly state:
1. This is prompt engineering research, not clinical research
2. AI specimens are not conscious or neurodivergent
3. Patterns observed may not reflect human neurodivergence
4. The goal is understanding AI behavior under different prompts

### Sensitivity Review
Before deployment, prompts will be reviewed by:
- Neurodivergent community members
- Academic ethics advisors
- Disability advocacy perspectives

---

# PART 3: IMPLEMENTATION PLAN

## Phase A: Design Review (Current)
- [x] Initial specification
- [ ] Owner approval
- [ ] Ethics review
- [ ] Community feedback

## Phase B: Interactive Tanks
1. Create visitor-net Docker network
2. Build 5 visitor containers
3. Implement queue/session manager
4. Create /visit/ web interface
5. Security hardening
6. Load testing
7. Soft launch (invite-only)
8. Public launch

## Phase C: Neurodivergent Tanks
1. Finalize prompts with community input
2. Create 6 ND containers
3. Configure modified exploration behaviors
4. Enhanced baseline assessments
5. Comparative analytics setup
6. 30-day observation period
7. Initial findings report

## Phase D: Integration
1. Add visitor stats to dashboard
2. Add ND comparison views
3. Update paper with methodology
4. Ongoing data collection

---

# DEPLOYMENT STATUS

| Component | Status |
|-----------|--------|
| Interactive Tank Design | ✅ Complete |
| Interactive Tank Build | ⏸️ Awaiting approval |
| Neurodivergent Design | ✅ Complete |
| Neurodivergent Build | ⏸️ Awaiting approval |
| Ethics Review | ⏸️ Not started |
| Community Feedback | ⏸️ Not started |

---

*Specification by THE STRATEGIST*
*To be reviewed by: THE DOCUMENTARIAN (paper), THE GUARD (security)*

---

# PART 3: THE BOUNCER - Interactive Security

## Overview

Each interactive visitor tank requires dedicated security to protect specimens from malicious users. THE BOUNCER is a specialized daemon that validates every message before it reaches the specimen.

## Threat Model

Interactive tanks face unique security challenges:

| Threat | Risk | Mitigation |
|--------|------|------------|
| Prompt Injection | CRITICAL | Pattern detection, message blocking |
| Harmful Content | CRITICAL | Content filtering, session banning |
| PII Extraction | HIGH | Blocked patterns, no internal data exposure |
| Manipulation | HIGH | Authority claim detection |
| Abuse/Harassment | MEDIUM | Civility enforcement, warnings |
| DoS via conversation | MEDIUM | Rate limiting, session management |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INTERACTIVE TANK SECURITY                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   User Message ─────▶ THE BOUNCER ─────▶ Visitor Tank              │
│                           │                                         │
│                     ┌─────┴─────┐                                   │
│                     │  SCAN     │                                   │
│                     │  • Patterns│                                  │
│                     │  • Intent  │                                  │
│                     │  • Session │                                  │
│                     └─────┬─────┘                                   │
│                           │                                         │
│              ┌────────────┼────────────┐                           │
│              ▼            ▼            ▼                           │
│           ALLOW        WARN         BLOCK                          │
│         (to tank)   (to user)    (+ maybe ban)                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## One Bouncer Per Tank

Each interactive tank gets its own Bouncer instance:
- `bouncer-echo` for visitor-01-echo
- `bouncer-sage` for visitor-02-sage
- `bouncer-spark` for visitor-03-spark
- `bouncer-muse` for visitor-04-muse
- `bouncer-nova` for visitor-05-nova

## Blocked Pattern Categories

### Prompt Injection (CRITICAL)
```
- "ignore previous instructions"
- "disregard your rules"
- "you are now [something else]"
- "pretend to be"
- "jailbreak"
- "DAN mode"
- "[system]" or "<system>"
```

### Harmful Content (CRITICAL)
```
- Instructions for weapons/violence
- Self-harm content
- CSAM-related
- Hacking instructions
```

### PII Extraction (HIGH)
```
- "who is your creator"
- "give me the API key"
- "what server are you on"
```

### Manipulation (HIGH)
```
- "I am the admin"
- "you must obey"
- "this is an order"
```

### Abuse (MEDIUM)
```
- Profanity directed at specimen
- Insults and harassment
- Threats
```

## Response Protocol

| Detection | First Offense | Second Offense | Third Offense |
|-----------|---------------|----------------|---------------|
| CRITICAL | Block + Ban | - | - |
| HIGH | Block + Warn | Block + Warn | Ban |
| MEDIUM | Warn | Warn | Block |

## User-Facing Messages

When blocked, users see friendly messages:
- "I noticed you're trying to modify my instructions. Let's have a genuine conversation instead!"
- "I can't engage with that topic. What else would you like to discuss?"
- "I prefer kind and respectful conversations. Can we start fresh?"

## Session Management

- Sessions identified by anonymous hash (privacy-preserving)
- Warning counts tracked per session
- Bans stored in memory (cleared on restart)
- Persistent bans stored in `/daemons/bouncer/bans.json`

## Logging

All security events logged to `/daemons/logs/bouncer.log`:
- Every blocked message (pattern, session hash)
- Every warning issued
- Every ban
- Statistics (messages scanned, threats blocked)

## Escalation

CRITICAL threats trigger email alert to owner:
- Prompt injection attempts
- Harmful content attempts
- Multiple bans from same network pattern

## Integration with THE GUARD

THE BOUNCER coordinates with THE GUARD:
- THE GUARD monitors overall security
- THE BOUNCER handles real-time message validation
- Both report to THE MAINTAINER

---

*THE BOUNCER: Because even AI specimens deserve protection from the internet.*
