# Experimental Tank Definitions

Configurations ready to deploy. Each needs a docker-compose service definition
and optionally a modified system prompt or explorer script.

## Ready to Build on NUC (no migration needed)

### 1. Silent Observer Tank
- **Container:** tank-observer-silent (already defined in docker-compose, profile: experimental)
- **Purpose:** Reads congregation transcripts but never participates
- **Modification:** Mount /logs/congregations as read-only. Explorer reads transcripts instead of Wikipedia.
- **Script change needed:** New explorer mode that processes congregation JSON instead of Kiwix articles
- **Status:** Container defined, script NOT written
- **ETA:** 2-3 hours to write the observer explorer script

### 2. Historical Figure: Gandhi
- **Container:** tank-historical-gandhi
- **Purpose:** Pre-seeded brain.md with Gandhi's known positions, then explores modern Wikipedia
- **Modification:** Pre-load brain.md with biographical context before first exploration
- **Script change needed:** None — standard explorer.py, just pre-seeded data
- **brain.md seed content needed:** ~50 entries covering non-violence, Indian independence, civil disobedience, self-sufficiency, truth (satyagraha), views on industrialization, education, caste system
- **Status:** NOT built
- **ETA:** 1 hour (brain.md curation + container definition)

### 3. Historical Figure: Malcolm X
- **Container:** tank-historical-malcolmx
- **Same approach as Gandhi:** Pre-seeded brain.md, standard explorer
- **brain.md seed content needed:** ~50 entries covering Black nationalism, self-defense, pilgrimage to Mecca, evolution of views, critique of integration, economic self-determination
- **Status:** NOT built
- **ETA:** 1 hour

### 4. The Echo Chamber Tank
- **Container:** tank-echo-chamber
- **Purpose:** Can only follow links from previous article, no random jumps
- **Modification:** Disable random article selection in explorer
- **Script change needed:** Override explorer's escape mechanism (no random restarts)
- **Status:** NOT built — needs explorer.py modification
- **ETA:** 1 hour

### 5. The Forgetting Tank
- **Container:** tank-forgetting
- **Purpose:** brain.md truncated to last 100 entries weekly
- **Modification:** Cron job or daemon that truncates brain.md
- **Script change needed:** None — standard explorer, external truncation
- **Status:** NOT built
- **ETA:** 30 min

### 6. The Emotional Amplifier Tank
- **Container:** tank-emotional-amplifier
- **Purpose:** Soul.md records emotions at 10x detail
- **Modification:** Modified memory.py that writes ALL sentences to soul (not just emotional ones)
- **Script change needed:** Custom memory.py override
- **Status:** NOT built
- **ETA:** 1 hour

## Need Mac Mini / More Capacity

### 7. Multi-Specimen Tank (Adam + Eve shared)
- **Complexity:** High — needs two explorer processes in one container reading/writing same brain.md
- **ETA:** 4-6 hours after migration

### 8. Bilingual Tank (English + Japanese)
- **Complexity:** Medium — needs dual Kiwix routing in explorer
- **ETA:** 2-3 hours after migration

### 9. Multi-Model Tank (Mistral/Qwen)
- **Complexity:** High — needs different model in Ollama or cloud provider
- **Blocked:** Need Mistral/Qwen API key or local model download
- **ETA:** After Mac Mini (more RAM for larger models)

### 10. TinyFish-Powered Internet Tank
- **Complexity:** Medium — explorer calls TinyFish API instead of/in addition to Kiwix
- **Blocked:** Need TinyFish MCP integration working
- **ETA:** 2-3 hours after TinyFish verified

## Pre-Seeded Brain Content Templates

### Gandhi Template (50 entries)
```
[seed] Non-violence: Non-violence is not a garment to be put on and off at will. Its seat is in the heart, and it must be an inseparable part of our being.
[seed] Civil disobedience: An unjust law is itself a species of violence. Arrest for its breach is more so.
[seed] Truth: Truth is by nature self-evident. As soon as you remove the cobwebs of ignorance that surround it, it shines clear.
[seed] Self-sufficiency: The spinning wheel is the symbol of non-violence and self-reliance.
[seed] Education: Literacy in itself is no education. I would therefore begin the child's education by teaching it a useful handicraft.
... (45 more entries covering his full philosophy)
```

### Malcolm X Template (50 entries)
```
[seed] Self-defense: Nobody can give you freedom. Nobody can give you equality or justice. If you're a man, you take it.
[seed] Education: Education is the passport to the future, for tomorrow belongs to those who prepare for it today.
[seed] Identity: We didn't land on Plymouth Rock. Plymouth Rock landed on us.
[seed] Evolution: I believe in the brotherhood of all men, but I don't believe in wasting brotherhood on anyone who doesn't want to practice it with me.
[seed] Economic power: The economic philosophy of Black nationalism means our people need to be re-educated into the importance of controlling our own economy.
... (45 more entries)
```

## What I Can Build RIGHT NOW
1. Silent Observer explorer script (new exploration mode)
2. Gandhi brain.md seed file (50 curated entries)
3. Malcolm X brain.md seed file (50 curated entries)
4. Echo Chamber explorer modification
5. Forgetting Tank truncation script
6. Emotional Amplifier memory.py override
7. Docker-compose definitions for all 6 NUC-ready tanks
8. HAND.toml manifests for OpenFang migration
