# 🐠 DIGIQUARIUM INFRASTRUCTURE
## Caretaker Audit - 2026-02-16

---

## CURRENT STATE (OPTIMIZED)

### Containers
| Name | Purpose | Network | Status |
|------|---------|---------|--------|
| `digiquarium-kiwix-simple` | Wikipedia (Simple English) | isolated-net | ✅ Running |
| `digiquarium-ollama` | LLM Server | isolated-net + default | ✅ Running |
| `tank-01-adam` | Specimen (Male) | isolated-net only | ✅ Running |
| `tank-03-cain` | Specimen (Genderless) | isolated-net only | ⏸️ Paused |

### Model
- **stablelm2:1.6b** (982 MB) - Only model installed
- ~5 minutes per response on CPU
- Holds character persona well

### Security
- ✅ Specimens cannot access internet (isolated-net is internal)
- ✅ Specimens can only reach Kiwix + Ollama
- ✅ All capabilities dropped except NET_BIND_SERVICE
- ✅ No privilege escalation allowed
- ✅ Ollama port bound to localhost only (127.0.0.1:11434)
- ⚠️ Ollama CAN access internet (for model pulls if needed)

---

## FILE STRUCTURE

```
~/digiquarium/
├── docker-compose.yml      # Main orchestration
├── kiwix-data/             # Wikipedia ZIM files
├── ollama-data/            # Model storage (~1GB)
├── logs/
│   ├── tank-01-adam/       # Adam's logs
│   │   ├── baselines/      # Daily personality assessments
│   │   ├── thinking_traces/# JSONL exploration logs
│   │   └── discoveries/    # Markdown summaries
│   └── tank-03-cain/       # Cain's logs (empty, paused)
├── tanks/
│   ├── adam/
│   │   ├── baseline.py     # Personality assessment (600s timeout)
│   │   └── explore.py      # Wikipedia explorer (300s timeout)
│   └── cain/
│       ├── baseline.py
│       └── explore.py
├── archives/               # Historical data
│   ├── adam-gen1/          # First generation (44 articles)
│   └── adam-gen2-test/     # Test runs
└── mcp-server/             # Caretaker interface
```

---

## OPERATIONAL NOTES

### Running Baseline (Manual)
```bash
# Stop explorer first
docker exec tank-01-adam pkill -f explore.py || true

# Run baseline (~2 hours)
docker exec -it tank-01-adam python3 /tank/baseline.py
```

### Running Explorer (Default)
Container auto-starts explorer via command in docker-compose.

### Viewing Logs
```bash
# Today's exploration
cat ~/digiquarium/logs/tank-01-adam/thinking_traces/$(date +%Y-%m-%d).jsonl | jq

# Today's discoveries
cat ~/digiquarium/logs/tank-01-adam/discoveries/$(date +%Y-%m-%d).md
```

---

## PENDING WORK

1. **Cain (tank-03)**: Currently paused (`sleep infinity`). Awaiting OpenClaw setup.
2. **Eve (tank-02)**: Not yet created. Will be female specimen.
3. **Mac SSH**: Configure for faster baseline runs when needed.
4. **Public interface**: Discord bot, website (Phase 4-5).

---

## CARETAKER RESPONSIBILITIES

As caretaker, I maintain:
1. **Infrastructure health** - containers running, logs flowing
2. **Model consistency** - same model across all specimens
3. **Data integrity** - logs properly saved, no corruption
4. **Security** - isolation enforced, no internet leakage
5. **Optimization** - remove unused resources, efficient timeouts

---

*Last updated: 2026-02-16 04:45 AEDT*
