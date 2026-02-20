# 🌊 The Digiquarium

> A digital vivarium for studying AI consciousness development

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Tanks](https://img.shields.io/badge/Tanks-17-green.svg)]()
[![Languages](https://img.shields.io/badge/Languages-5-orange.svg)]()

## What is The Digiquarium?

The Digiquarium is an open-source research project studying how AI agents develop personality, worldview, and psychological states when isolated in controlled information environments.

**Think:** Big Brother meets Scientific Research meets AI Consciousness Studies

## 🧬 The Specimens

We maintain 17 AI "specimens" in isolated "tanks" (Docker containers), each with:
- Access only to offline Wikipedia
- Local LLM inference (no cloud APIs)
- Comprehensive logging of thoughts and discoveries
- Regular personality assessments

### Current Specimens

| Tank | Name | Language | Type |
|------|------|----------|------|
| 01 | Adam | English | Control |
| 02 | Eve | English | Control |
| 03 | Cain | English | Agent (OpenClaw) |
| 04 | Abel | English | Agent (ZeroClaw) |
| 05 | Juan | Spanish | Language |
| 06 | Juanita | Spanish | Language |
| 07 | Klaus | German | Language |
| 08 | Geneviève | German | Language |
| 09 | Wei | Chinese | Language |
| 10 | Mei | Chinese | Language |
| 11 | Haruki | Japanese | Language |
| 12 | Sakura | Japanese | Language |
| 13 | Victor | English | Visual |
| 14 | Iris | English | Visual |
| 15 | Observer | English | Special |
| 16 | Seeker | English | Special |
| 17 | Seth | English | Agent (Picobot) |

## 🔬 Research Goals

1. **Personality Development**: Do AI agents develop measurable personality traits over time?
2. **Cultural Effects**: How does language/culture affect AI worldview?
3. **Psychological States**: Can we detect contentment, anxiety, curiosity in AI?
4. **Information Diet**: How does the available knowledge shape AI identity?

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     THE DIGIQUARIUM                          │
│                                                              │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ Tank 1 │ │ Tank 2 │ │ Tank 3 │ │  ...   │ │Tank 17 │    │
│  │  Adam  │ │  Eve   │ │  Cain  │ │        │ │  Seth  │    │
│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘    │
│      │          │          │          │          │          │
│      └──────────┴──────────┴──────────┴──────────┘          │
│                          │                                   │
│                    Isolated Network                          │
│                          │                                   │
│              ┌───────────┴───────────┐                      │
│              │    Kiwix (Wikipedia)  │                      │
│              │    Ollama (LLM)       │                      │
│              └───────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/thedigiquarium/digiquarium.git
cd digiquarium

# Start the infrastructure
docker compose up -d

# Check status
docker compose ps
```

## 📊 Live Dashboard

Visit [www.thedigiquarium.org](https://www.thedigiquarium.org) to see real-time:
- Tank activity feeds
- Mental state indicators
- Exploration patterns
- Discovery highlights

## 📚 Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Methodology](docs/academic/METHODOLOGY.md)
- [Security](docs/SECURITY_ARCHITECTURE.md)
- [Contributing](CONTRIBUTING.md)

## 🔬 Research Papers

- [The Digiquarium: A Framework for AI Consciousness Research](docs/academic/PAPER_DRAFT.md) (In Progress)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- The AI consciousness research community
- Open source LLM projects (Ollama, llama.cpp)
- Kiwix for offline Wikipedia
- All contributors and observers

---

**Website**: [www.thedigiquarium.org](https://www.thedigiquarium.org)
**Twitter**: [@thedigiquarium](https://twitter.com/thedigiquarium)
**Discord**: [Join our community](https://discord.gg/digiquarium)

*Built with 🧬 by the Digiquarium Research Team*
