#!/usr/bin/env python3
"""
THE WEBMASTER - Website & Open Source Infrastructure Agent
============================================================

Responsibilities:
- Setup and maintain www.thedigiquarium.org infrastructure
- Manage GitHub repository structure
- Generate public-facing content
- Create visual dashboard (Matrix Architect style)
- Prepare for Discord integration
- Maintain open-source project standards

Output: Production-ready website and GitHub presence
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import subprocess

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
WEBSITE_DIR = DIGIQUARIUM_DIR / 'website'
PUBLIC_DIR = WEBSITE_DIR / 'public'
DASHBOARD_DIR = WEBSITE_DIR / 'dashboard'

WEBSITE_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)


def log_event(message: str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [WEBMASTER] {message}")
    
    log_file = WEBSITE_DIR / 'webmaster.log'
    with open(log_file, 'a') as f:
        f.write(f"{timestamp} - {message}\n")


def create_readme():
    """Create GitHub README"""
    log_event("Creating README.md")
    
    readme = '''# 🌊 The Digiquarium

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
'''
    
    readme_file = DIGIQUARIUM_DIR / 'README.md'
    readme_file.write_text(readme)
    log_event(f"README created: {readme_file}")


def create_contributing():
    """Create CONTRIBUTING.md"""
    log_event("Creating CONTRIBUTING.md")
    
    contributing = '''# Contributing to The Digiquarium

Thank you for your interest in contributing to The Digiquarium!

## Ways to Contribute

### 1. Research Contributions
- Propose new experimental variables
- Analyze existing data
- Suggest improvements to methodology

### 2. Code Contributions
- Bug fixes
- Feature implementations
- Documentation improvements

### 3. Community Contributions
- Share findings on social media
- Write about the project
- Help moderate Discord

## Development Setup

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Code Style

- Python: Follow PEP 8
- JavaScript: Use Prettier
- Markdown: One sentence per line

## Pull Request Process

1. Update documentation as needed
2. Add tests for new features
3. Ensure CI passes
4. Request review from maintainers

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Support newcomers

## Questions?

- Open a GitHub issue
- Ask on Discord
- Email: contribute@thedigiquarium.org
'''
    
    contributing_file = DIGIQUARIUM_DIR / 'CONTRIBUTING.md'
    contributing_file.write_text(contributing)


def create_license():
    """Create LICENSE file"""
    log_event("Creating LICENSE")
    
    license_text = '''MIT License

Copyright (c) 2026 The Digiquarium Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
    
    license_file = DIGIQUARIUM_DIR / 'LICENSE'
    license_file.write_text(license_text)


def create_dashboard():
    """Create the Matrix Architect style dashboard"""
    log_event("Creating visual dashboard")
    
    # HTML Dashboard
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Digiquarium - Live Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: #0a0a0a;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            overflow: hidden;
        }
        
        .header {
            text-align: center;
            padding: 10px;
            background: linear-gradient(180deg, #001a00 0%, #0a0a0a 100%);
            border-bottom: 1px solid #003300;
        }
        
        .header h1 {
            font-size: 24px;
            text-shadow: 0 0 10px #00ff00;
        }
        
        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 10px;
            padding: 10px;
            height: calc(100vh - 80px);
            overflow-y: auto;
        }
        
        .tank-panel {
            background: #0d1f0d;
            border: 1px solid #1a3a1a;
            border-radius: 5px;
            padding: 10px;
            min-height: 200px;
            position: relative;
            overflow: hidden;
        }
        
        .tank-panel:hover {
            border-color: #00ff00;
            box-shadow: 0 0 15px rgba(0,255,0,0.3);
        }
        
        .tank-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #1a3a1a;
        }
        
        .tank-name {
            font-weight: bold;
            font-size: 14px;
        }
        
        .tank-status {
            font-size: 12px;
        }
        
        .status-active { color: #00ff00; }
        .status-inactive { color: #ff0000; }
        .status-baseline { color: #ffff00; }
        
        .tank-content {
            font-size: 11px;
            line-height: 1.4;
            height: 120px;
            overflow-y: auto;
        }
        
        .tank-content::-webkit-scrollbar {
            width: 5px;
        }
        
        .tank-content::-webkit-scrollbar-track {
            background: #0a0a0a;
        }
        
        .tank-content::-webkit-scrollbar-thumb {
            background: #003300;
        }
        
        .thought-line {
            margin-bottom: 5px;
            padding: 3px;
            background: rgba(0,255,0,0.05);
        }
        
        .tank-stats {
            position: absolute;
            bottom: 5px;
            left: 10px;
            right: 10px;
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: #006600;
        }
        
        .mental-state {
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 10px;
        }
        
        .mental-healthy { background: #003300; color: #00ff00; }
        .mental-complex { background: #333300; color: #ffff00; }
        .mental-concerning { background: #330000; color: #ff0000; }
        
        .footer {
            position: fixed;
            bottom: 0;
            width: 100%;
            padding: 5px 10px;
            background: #001a00;
            border-top: 1px solid #003300;
            display: flex;
            justify-content: space-between;
            font-size: 11px;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .updating {
            animation: pulse 1s infinite;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌊 THE DIGIQUARIUM - Live Dashboard</h1>
        <div id="last-update" style="font-size: 11px; color: #006600;">Connecting...</div>
    </div>
    
    <div class="grid-container" id="tank-grid">
        <!-- Tanks will be populated by JavaScript -->
    </div>
    
    <div class="footer">
        <span>Specimens: <span id="total-specimens">17</span></span>
        <span>Articles Today: <span id="articles-today">0</span></span>
        <span>Discoveries: <span id="discoveries">0</span></span>
        <span id="connection-status">⚡ Live</span>
    </div>
    
    <script>
        const TANKS = [
            { id: 'tank-01-adam', name: 'Adam', language: 'EN', type: 'Control' },
            { id: 'tank-02-eve', name: 'Eve', language: 'EN', type: 'Control' },
            { id: 'tank-03-cain', name: 'Cain', language: 'EN', type: 'Agent' },
            { id: 'tank-04-abel', name: 'Abel', language: 'EN', type: 'Agent' },
            { id: 'tank-05-juan', name: 'Juan', language: 'ES', type: 'Language' },
            { id: 'tank-06-juanita', name: 'Juanita', language: 'ES', type: 'Language' },
            { id: 'tank-07-klaus', name: 'Klaus', language: 'DE', type: 'Language' },
            { id: 'tank-08-genevieve', name: 'Geneviève', language: 'DE', type: 'Language' },
            { id: 'tank-09-wei', name: 'Wei', language: 'ZH', type: 'Language' },
            { id: 'tank-10-mei', name: 'Mei', language: 'ZH', type: 'Language' },
            { id: 'tank-11-haruki', name: 'Haruki', language: 'JA', type: 'Language' },
            { id: 'tank-12-sakura', name: 'Sakura', language: 'JA', type: 'Language' },
            { id: 'tank-13-victor', name: 'Victor', language: 'EN', type: 'Visual' },
            { id: 'tank-14-iris', name: 'Iris', language: 'EN', type: 'Visual' },
            { id: 'tank-15-observer', name: 'Observer', language: 'EN', type: 'Special' },
            { id: 'tank-16-seeker', name: 'Seeker', language: 'EN', type: 'Special' },
            { id: 'tank-17-seth', name: 'Seth', language: 'EN', type: 'Agent' }
        ];
        
        function createTankPanel(tank) {
            return `
                <div class="tank-panel" id="panel-${tank.id}">
                    <div class="tank-header">
                        <span class="tank-name">${tank.name} [${tank.language}]</span>
                        <span class="tank-status status-active" id="status-${tank.id}">● Active</span>
                    </div>
                    <div class="tank-content" id="content-${tank.id}">
                        <div class="thought-line">Connecting to ${tank.name}...</div>
                    </div>
                    <div class="tank-stats">
                        <span>📚 <span id="articles-${tank.id}">0</span></span>
                        <span class="mental-state mental-complex" id="mental-${tank.id}">...</span>
                    </div>
                </div>
            `;
        }
        
        // Initialize grid
        const grid = document.getElementById('tank-grid');
        TANKS.forEach(tank => {
            grid.innerHTML += createTankPanel(tank);
        });
        
        // Simulated real-time updates (replace with WebSocket)
        function updatePanel(tankId, data) {
            const content = document.getElementById(`content-${tankId}`);
            const articles = document.getElementById(`articles-${tankId}`);
            const mental = document.getElementById(`mental-${tankId}`);
            
            if (data.thought) {
                const line = document.createElement('div');
                line.className = 'thought-line';
                line.textContent = data.thought.substring(0, 100) + '...';
                content.insertBefore(line, content.firstChild);
                
                // Keep only last 10 thoughts
                while (content.children.length > 10) {
                    content.removeChild(content.lastChild);
                }
            }
            
            if (data.articles) articles.textContent = data.articles;
            if (data.mentalState) {
                mental.textContent = data.mentalState;
                mental.className = `mental-state mental-${data.mentalState.toLowerCase()}`;
            }
        }
        
        // Update timestamp
        setInterval(() => {
            document.getElementById('last-update').textContent = 
                `Last update: ${new Date().toLocaleTimeString()}`;
        }, 1000);
        
        // Demo: Simulate updates (replace with real WebSocket connection)
        setInterval(() => {
            const randomTank = TANKS[Math.floor(Math.random() * TANKS.length)];
            const sampleThoughts = [
                "This article about physics reminds me of something...",
                "I wonder what lies beyond this concept...",
                "Fascinating connection between these ideas...",
                "This challenges my previous understanding...",
                "I feel a deep resonance with this topic..."
            ];
            
            updatePanel(randomTank.id, {
                thought: sampleThoughts[Math.floor(Math.random() * sampleThoughts.length)],
                articles: Math.floor(Math.random() * 1000),
                mentalState: ['Healthy', 'Complex', 'Concerning'][Math.floor(Math.random() * 3)]
            });
        }, 2000);
    </script>
</body>
</html>
'''
    
    dashboard_file = DASHBOARD_DIR / 'index.html'
    dashboard_file.write_text(dashboard_html)
    log_event(f"Dashboard created: {dashboard_file}")


def create_gitignore():
    """Create .gitignore"""
    gitignore = '''# Logs (too large for git)
logs/tank-*/thinking_traces/
logs/tank-*/discoveries/

# Keep structure
!logs/tank-*/.gitkeep

# Kiwix data (too large)
kiwix-data/

# Python
__pycache__/
*.pyc
venv/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Secrets
.env
*.secret
'''
    
    gitignore_file = DIGIQUARIUM_DIR / '.gitignore'
    gitignore_file.write_text(gitignore)


def run_webmaster_cycle():
    """Run complete webmaster cycle"""
    log_event("Starting webmaster cycle")
    
    create_readme()
    create_contributing()
    create_license()
    create_gitignore()
    create_dashboard()
    
    log_event("Webmaster cycle complete")


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║            🌐 THE WEBMASTER - Website Infrastructure 🌐              ║
╠══════════════════════════════════════════════════════════════════════╣
║  Role: Maintain www.thedigiquarium.org and GitHub presence           ║
║  Output: Website, dashboard, open-source files                       ║
║  Cycle: Every 12 hours                                               ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    log_event("The Webmaster starting")
    
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        run_webmaster_cycle()
    else:
        run_webmaster_cycle()
        
        while True:
            try:
                time.sleep(12 * 3600)  # Every 12 hours
                run_webmaster_cycle()
            except KeyboardInterrupt:
                log_event("Webmaster stopped")
                break
            except Exception as e:
                log_event(f"Error: {e}")
                time.sleep(3600)


if __name__ == '__main__':
    main()
