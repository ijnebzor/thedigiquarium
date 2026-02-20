#!/bin/bash
#
# THE DIGIQUARIUM - Mac Installation Script
# ==========================================
# For macOS (Mac Mini, MacBook, etc.)
#

set -e

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║           🍎 DIGIQUARIUM - macOS Installation 🍎                     ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Docker Desktop if needed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker Desktop..."
    brew install --cask docker
    echo "Please start Docker Desktop from Applications and run this script again."
    exit 1
fi

# Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    brew install ollama
fi

# Start Ollama
echo "Starting Ollama..."
ollama serve &
sleep 5

# Pull model
echo "Pulling llama3.2 model..."
ollama pull llama3.2:latest

# Create directories
echo "Creating directories..."
mkdir -p logs kiwix-data
chmod -R 777 logs/

# Download Wikipedia
echo ""
read -p "Download Wikipedia ZIM files now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./setup/download-wikipedia.sh
fi

# Start Docker containers
echo "Starting containers..."
docker compose up -d

# Start operations daemons
echo "Starting operations daemons..."
python3 operations/orchestrator.py start

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ INSTALLATION COMPLETE ✅                        ║"
echo "╠══════════════════════════════════════════════════════════════════════╣"
echo "║                                                                      ║"
echo "║  All 17 tanks are now running!                                       ║"
echo "║                                                                      ║"
echo "║  Commands:                                                           ║"
echo "║    docker compose ps              # Check tank status                ║"
echo "║    docker compose logs -f         # View all logs                    ║"
echo "║    python3 operations/orchestrator.py status  # Daemon status        ║"
echo "║                                                                      ║"
echo "║  Dashboard:                                                          ║"
echo "║    cd docs && python3 -m http.server 8080                            ║"
echo "║    Open http://localhost:8080                                        ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
