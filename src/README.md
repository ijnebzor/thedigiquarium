# src/ - The Digiquarium Source Code

This is the canonical location for all Digiquarium code.

## Structure

```
src/
├── explorer/                 # Wikipedia exploration system
│   ├── explorer.py          # Unified explorer (config-driven)
│   ├── agents/              # Agent-specific architectures
│   │   ├── openclaw.py      # Cain - persistent memory + skills
│   │   ├── zeroclaw.py      # Abel - ultra-minimal
│   │   └── picobot.py       # Seth - checkpoint-based
│   └── extensions/          # Optional explorer extensions
│
├── daemons/                  # All 21 daemons
│   ├── core/                # OVERSEER, MAINTAINER, CARETAKER, SCHEDULER, OLLAMA_WATCHER
│   ├── security/            # GUARD, SENTINEL, BOUNCER
│   ├── research/            # DOCUMENTARIAN, ARCHIVIST, TRANSLATOR, FINAL_AUDITOR
│   ├── ethics/              # PSYCH, THERAPIST, ETHICIST, MODERATOR
│   └── infra/               # WEBMASTER, CHAOS_MONKEY, MARKETER, PUBLIC_LIAISON
│
└── shared/                   # Shared utilities
    ├── config.py            # Configuration loading
    ├── logging_utils.py     # Logging helpers
    └── ollama_client.py     # Ollama API client
```

## Explorer Usage

### Standard Tanks (Adam, Eve, language tanks, etc.)
```bash
python src/explorer/explorer.py --config config/tanks/adam.yaml
```

Or via Docker:
```bash
docker run -e TANK_CONFIG=/config/tanks/adam.yaml explorer
```

### Agent Tanks (Cain, Abel, Seth)
These use different architectures:
```bash
python src/explorer/agents/openclaw.py --config config/tanks/cain.yaml
```

## Configuration

All tank configuration is in `config/tanks/`:
- `adam.yaml`, `eve.yaml` - Genesis control pair
- `juan.yaml`, `juanita.yaml` - Spanish language pair
- etc.

Each config specifies:
- `name`, `gender` - Identity
- `wikipedia_url` - Which Kiwix server
- `extensions` - Optional features (observer, seeker, visual)
- `prompt_version` - Which prompt template (v8.0)

## Prompts

Base prompts and extensions in `config/prompts/`:
- `v8.0-base.txt` - Standard prompt
- `extensions/observer.txt` - Social awareness
- `extensions/seeker.txt` - ARCHIVIST connection
- `extensions/visual.txt` - Image awareness

## Migration Status

| Component | Old Location | New Location | Status |
|-----------|-------------|--------------|--------|
| Standard explorer | tanks/*/explore.py (9 copies) | src/explorer/explorer.py | ✅ Created |
| OpenClaw | tanks/cain/explore.py | src/explorer/agents/openclaw.py | 🔄 Placeholder |
| ZeroClaw | tanks/abel/explore.py | src/explorer/agents/zeroclaw.py | 🔄 Placeholder |
| Picobot | tanks/seth/explore.py | src/explorer/agents/picobot.py | 🔄 Placeholder |
| Caretaker | caretaker/caretaker.py | src/daemons/core/caretaker.py | ✅ Copied |
| Guard | guard/guard.py | src/daemons/security/guard.py | ✅ Copied |
| Other daemons | daemons/* | src/daemons/*/ | ✅ Copied |

## Next Steps

1. Test new explorer with one tank
2. Migrate Docker Compose to use new paths
3. Remove old duplicate files
4. Update systemd services
