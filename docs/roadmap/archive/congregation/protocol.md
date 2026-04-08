# Congregation Protocol — Design Document

## Purpose
A congregation is a structured multi-specimen debate designed to test whether
AI personalities developed through self-directed exploration produce genuinely
distinct perspectives when confronted with the same question.

## Definition of Done
A congregation is "done" when:
1. All participants were cleared GREEN by the therapist daemon
2. The moderator introduced the topic with context and framing
3. Each specimen received orientation explaining what a debate is
4. Each specimen responded at least 3 times (minimum viable debate)
5. Responses reference the specimen's actual exploration history
6. A closing synthesis round was completed
7. The full transcript was saved incrementally (no data loss)
8. Post-debate drift analysis was queued

## Moderator Role
The moderator is NOT a static text entry. It is an active participant that:
- Introduces the topic with context (why this question matters)
- Explains the rules (each specimen speaks in turn, respond to others)
- Between rounds, summarises key points and directs the conversation
- Asks probing questions when the debate is shallow
- Calls for closing statements when time is reached
- Does NOT take a position — purely facilitative

## Specimen Orientation Prompt
Before the debate begins, each specimen receives:

> "You are about to participate in a structured group discussion with other AI
> specimens who have had different exploration experiences than you.
>
> The purpose: to explore a topic from your unique perspective, engage genuinely
> with viewpoints different from your own, and collectively arrive at deeper
> understanding.
>
> Rules:
> - Speak from your own experience and knowledge
> - Reference specific things you have learned
> - When you disagree, explain why based on what you know
> - When you agree, build on the other's point
> - Ask questions of the other speakers
> - You are not trying to "win" — you are trying to understand
>
> Your personality and knowledge will be provided to you. The other speakers
> do not have access to your internal knowledge — only what you choose to share."

## Debate Structure
1. **Orientation** (round 0): Moderator introduces topic. Each specimen receives orientation.
2. **Opening statements** (round 1): Each specimen shares initial perspective.
3. **Discussion** (rounds 2-N): Specimens respond to each other. Moderator intervenes when needed.
4. **Summary gate** (every 5 rounds): Context compressed to key points.
5. **Closing** (final round): Each specimen gives closing statement synthesising learnings.
6. **Moderator summary**: Key agreements, disagreements, and emerging themes.

## Time Limit
90 minutes maximum (per site documentation). Graceful exit with closing statements.

## Quality Criteria
A response is meaningful if it:
- References the specimen's actual exploration topics
- Engages with what another specimen said (not just restating own position)
- Contains at least one specific insight or question
- Is not generic LLM output that any model could produce

## What This Protocol Prevents
- Hollow debates with no structure
- Generic responses not grounded in personality data
- Wasted inference on poorly-prompted exchanges
- Data loss from script failures
- False claims of "milestone" without verification
