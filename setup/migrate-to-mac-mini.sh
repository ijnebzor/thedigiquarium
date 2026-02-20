#!/bin/bash
#
# THE DIGIQUARIUM - Mac Mini Migration Script
# ============================================
# Prepares everything for transfer to Mac Mini
#

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║           🖥️  DIGIQUARIUM - Mac Mini Migration 🖥️                    ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

DIGIQUARIUM_DIR="${DIGIQUARIUM_DIR:-/home/ijneb/digiquarium}"
EXPORT_DIR="${EXPORT_DIR:-/tmp/digiquarium-export}"

mkdir -p "$EXPORT_DIR"

echo "=== Pre-Migration Checks ==="

# Check all daemons
echo "Checking daemon status..."
for pid_file in "$DIGIQUARIUM_DIR"/caretaker/caretaker.pid \
                "$DIGIQUARIUM_DIR"/guard/guard.pid \
                "$DIGIQUARIUM_DIR"/operations/scheduler.pid \
                "$DIGIQUARIUM_DIR"/operations/agents/*.pid; do
    if [ -f "$pid_file" ]; then
        name=$(basename "$pid_file" .pid)
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "  ✅ $name (PID: $pid)"
        else
            echo "  ❌ $name (DEAD)"
        fi
    fi
done

echo ""
echo "=== What Will Be Exported ==="
echo ""
echo "  📁 Code & Configuration"
echo "     - docker-compose.yml"
echo "     - All tank code (tanks/)"
echo "     - Operations agents (operations/)"
echo "     - Security modules (security/)"
echo "     - MCP server (mcp-server/)"
echo "     - Website (docs/)"
echo ""
echo "  📊 Data (Optional)"
echo "     - Thinking traces (logs/tank-*/thinking_traces/)"
echo "     - Baselines (logs/tank-*/baselines/)"
echo "     - Discoveries (logs/tank-*/discoveries/)"
echo ""
echo "  ⚠️  NOT Exported (too large)"
echo "     - Wikipedia ZIM files (kiwix-data/) - download fresh"
echo "     - Ollama models (ollama-data/) - pull fresh"
echo ""

# Create export archive
echo "=== Creating Export Archive ==="

cd "$DIGIQUARIUM_DIR"

# Export code and config (required)
tar -czvf "$EXPORT_DIR/digiquarium-code.tar.gz" \
    --exclude='kiwix-data' \
    --exclude='ollama-data' \
    --exclude='logs' \
    --exclude='archives' \
    --exclude='*.pid' \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='.git' \
    . 2>/dev/null

echo "✅ Code archive: $EXPORT_DIR/digiquarium-code.tar.gz ($(du -h "$EXPORT_DIR/digiquarium-code.tar.gz" | cut -f1))"

# Export logs/data (optional)
read -p "Export experiment data (logs, baselines)? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    tar -czvf "$EXPORT_DIR/digiquarium-data.tar.gz" \
        logs/tank-*/baselines \
        logs/tank-*/thinking_traces \
        logs/tank-*/discoveries \
        2>/dev/null || true
    echo "✅ Data archive: $EXPORT_DIR/digiquarium-data.tar.gz"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    EXPORT COMPLETE                                    ║"
echo "╠══════════════════════════════════════════════════════════════════════╣"
echo "║  Export files in: $EXPORT_DIR"
echo "║                                                                      ║"
echo "║  TO TRANSFER TO MAC MINI:                                            ║"
echo "║                                                                      ║"
echo "║  1. Copy archives to Mac Mini:                                       ║"
echo "║     scp $EXPORT_DIR/*.tar.gz user@mac-mini:~/"
echo "║                                                                      ║"
echo "║  2. On Mac Mini, run:                                                ║"
echo "║     mkdir -p ~/digiquarium && cd ~/digiquarium                       ║"
echo "║     tar -xzf ~/digiquarium-code.tar.gz                               ║"
echo "║     ./setup/install-mac.sh                                           ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
