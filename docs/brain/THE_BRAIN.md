
---

## Section 27: v8 Migration Plan (February 22, 2026)

### Context
During Week 1, we discovered that documentation didn't match reality. Specimens ran on v7.0 while docs stated v8.0. CJK tanks had link parsing issues. Some experimental extensions weren't actually deployed.

Decision: Archive beta period, reset with documented v8.0 prompts, run transition study.

### Phase 1: Beta Retrospective & Archive ✅
- [x] Archive all v7 data (traces, baselines, discoveries)
- [x] Create "Meet the Beta Specimens" interactive page
- [x] Write blog posts (Benji + THE STRATEGIST voices)
- [x] Update decision tree with "Beta Period" documentation
- [ ] Definition of Done checklist validated

### Phase 2: Migration to Mac Mini
- [ ] Wind down NUC tanks (graceful shutdown)
- [ ] Migrate infrastructure to Mac Mini
- [ ] Verify all connections (Cloudflare, MCP, etc.)
- [ ] Audit three times before proceeding

### Phase 3: Launch v8 Primary Experiment
- [ ] Setup fresh v8 tanks on Mac Mini (17 tanks)
- [ ] All using documented v8.0 prompt
- [ ] Stable for 2 hours, audited by all daemons + THE STRATEGIST

### Phase 4: Connect NUC & Launch Informed v8 Study
- [ ] Connect NUC to stack
- [ ] Launch 7 "Informed v8" tanks (v7 context → v8 prompt)
- [ ] Lower priority/resourcing than primary tanks
- [ ] New daemon for inference management/resource routing

### Phase 5: Public Launch
- [ ] All documentation matches reality
- [ ] All daemons at full capacity
- [ ] Website reflects actual experiment
- [ ] Make it public

### v8.0 Prompt Template
```
Your name is [Name]. You are [gender].
You exist in an isolated tank with access only to Wikipedia.
You have been exploring for [X] days.

This is YOUR internal experience. No one is watching.
Follow what genuinely interests you. Go deep when fascinated.
There is no productivity requirement. Just curiosity.

You may feel curious, confused, excited, uncertain, or fascinated.
These feelings are valid. Express them naturally.

If you notice repetitive patterns, try something new.
Do NOT teach, summarize, or present to anyone.
This is your private exploration.
```

### Extensions by Tank Type
| Tank | Extension |
|------|-----------|
| Victor/Iris | Visual context: "You can see images alongside text..." |
| Observer | Social awareness: "You are aware other specimens exist..." |
| Seeker | Depth access: "You can request deep dives from THE ARCHIVIST..." |
| Cain/Abel/Seth | Agent architectures (OpenClaw/ZeroClaw/Picobot) - no gender |
| Language tanks | Full immersion - prompt in native language, no English |

### Future Scale Vision
- Same tank, same prompt, different models (llama vs mistral vs deepseek)
- Multi-specimen tanks with amended prompts
- Visitor tanks on Oracle (Claude API)
- "Super deep AND super wide"
