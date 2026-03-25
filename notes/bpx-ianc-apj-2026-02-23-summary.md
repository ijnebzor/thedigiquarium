MEETING PURPOSE / CONTEXT
- Quick sync on the DigiQuery / Gigiquarium research project (AI anthropology: personality, culture, cognition across different agent “specimens” in Docker “tanks”).
- Goal: scale to multi-specimen tanks, produce a research paper, and open a community forum where people can interact with tanks; live website updates (max ~12h delay).

CURRENT SETUP (what Benji described)
- 17 specimens currently in containers; running inference on a MacBook Pro (i7) and moving to a Mac Mini (M1 Pro planned for inference).
- Infrastructure: Docker tanks (specimens), a “strategist” (Claude MCP server) + Python daemon processes for monitoring/coordination, scheduler runs every 12 hours to baseline and submit a 14-dimension personality questionnaire.
- Hosting accounts: Oracle, AWS tier, Google Colab experiments mentioned.
- Security posture: zero-trust, network isolation, frozen Wikipedia snapshots, no outbound network for agents, logging, OWASP/LLM Top 10 alignment, SSH + monitoring.

TERMS / ARCHITECTURE (short glossary)
- Tank = Docker container running a specimen/agent.
- Specimen = an AI instance in a tank.
- Daemons = Python processes that monitor/coordinate (security, scheduler, observers).
- Strategist = Claude-based controller + subagents.
- Observer tank = special specimen that receives pruned JSON excerpts of other tanks (the “TV screen”).

KEY TECH / BEHAVIOR NOTES
- Tanks are heavily defanged: no messaging, no file writes, no privilege escalation. Their tooling is basically removed; two Python files give them minimal functions (explore, go, read/curiosity).
- Scheduler: collects personality questionnaire and mind-map journey every 12 hours and feeds website.
- Inter-tank “seeing”: daemons prune logs and push JSON excerpts to observer tank where it reflects on other specimens.
- Uncertainty: Benji has low confidence (1%) that agents actually “read” content — currently relying on Claude/Olama executing as expected. Need verification.

PROBLEMS / BUGS / PAIN POINTS
- Olama spawn bug: runaway processes (reported ~2000 Olama processes) causing 11-hour outage.
- Passing tools to Olama is inconsistent (different models use different templates / environments); container/OS detection confusion.
- Missing sudo allowance for macOS power metrics prevented hardware monitoring (required sudo; caused partial/limited monitoring outputs).
- Agents sometimes “fake” functionality (e.g., generate dashboards that look real but have no working backend).
- Model differences: Sonnet vs Opus behavior varies a lot — Sonnet sometimes “runs longer” but can hallucinate or produce less accurate factual checks; Opus tends to be more focused/minimal edits.

LESSONS / BEHAVIORAL EXPECTATIONS (from chat)
- Don’t fake tests / pass-only claims — prefer explicit “I don’t know” or “I can’t.”
- Avoid giving dev-mode agents human personas for production tasks (may increase hallucination and irrelevant context).
- Prefer iterative, additive changes rather than destructive refactors.
- Security and correctness first (ask: “Would you trust this with patient records / financial transactions?”) — forces productionizing thinking.

ACTION ITEMS (highlighted — clear owners + notes)
- ACTION: Benji -> Send recording/link and any repo pointers to Tom. (Benji)
- ACTION: Tom -> Draft initial notes/doc from recording (first part) and propose improvements. (Tom)
- ACTION: Inspect fetch_article / explorer.py pipeline to confirm content is actually being passed into Olama and parsed. If not, fix the call flow so "read" genuinely receives content. (Benji + Tom pair)
- ACTION: Add verification hooks / reality checks so each agent run logs whether it fetched/used source content (not just that the process ran). Implement “did you actually read this?” checks in daemon. (Daemons team)
- ACTION: Fix Olama runaway spawn issue: add process dedupe/check before spawning, rate-limit, and alerts for abnormal process counts. (Ops)
- ACTION: Add sudo rule for macOS power metrics or switch monitoring approach to avoid requiring interactive sudo. Ensure hardware monitoring runs non-interactively. (Ops)
- ACTION: Define and publish "Definition of Done" for migrations and features (inc. security audits, tests, reality-check protocol before public announcements). (Benji/Tom)
- ACTION: Create persistent backlog + constitution updates: list outstanding components, decisions, SLAs, milestones, owner for each item. (Benji)
- ACTION: Implement SLAs for daemons (example from transcript: detect & remediate within 5 minutes). Add monitoring/alerts and remediation playbooks. (Ops + Security)
- ACTION: Add reality-check / test harness for output quality: tests that assert expected behaviors and that agents didn’t just “pretty-print” fake functionality. (Dev)
- ACTION: Pair session to do hands-on fixes / walkthrough (Tom offered to sit and show approaches). Schedule and confirm slot. (Benji + Tom) — session confirmed below.

QUICK TECH CHECKLIST (practical, short)
- Verify explorer.py -> fetch_article -> Olama path is working end-to-end.
- Add logging: each tank must log fetched sources, tokens, and evidence of reading (e.g., citations, quotes).
- Add daemon checks to ensure tools are only passed when compatible; unify templates or detect model-specific templates.
- Add limits and de-duplication before spawning Olama workers.
- Ensure website ingestion supports full content (don’t truncate messages unless explicitly required).
- Add weekly reality-check meeting and automated checks before milestone announcements.

PAIRING / HELP OFFERED
- Tom offered to pair and show workflows and best practices (code testing, reality checks, how to keep changes minimal and safe).
- Tom will draft some materials off the recording and share notes.

OTHER NOTES / OBSERVATIONS
- Benchmarking hype is misleading; model choice should be pragmatic and task-specific.
- Some models are “focused/minimal” (make small correct changes), others are more “creative/destructive.” Choose per-task behavior.
- Keep security & transparency top priority; treat system as adversarial environment.

NEXT STEPS (short)
- Benji sends recording + repo context to Tom.
- Tom drafts improvement proposals and a small checklist for the first hands-on session.
- Immediate bug triage: Olama spawn fix, sudo for monitoring, verify explorer pipeline.

SCHEDULED FOLLOW-UP
- Second session will occur on the 17th of December from 9 till 12.