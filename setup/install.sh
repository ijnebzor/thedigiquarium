#!/bin/bash
set -e

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║           🧬 THE DIGIQUARIUM - Installation Script 🧬                ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi
echo "✅ Docker found"

# Clone repository
if [ ! -d "thedigiquarium" ]; then
    git clone https://github.com/ijnebzor/thedigiquarium.git
fi
cd thedigiquarium

# Install Ollama
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi
ollama pull llama3.2:latest

# Create directories
mkdir -p logs kiwix-data
chmod -R 777 logs/

# Start
docker compose up -d

echo "✅ Installation complete!"
echo "Dashboard: python3 -m http.server 8080 -d website/dashboard"
