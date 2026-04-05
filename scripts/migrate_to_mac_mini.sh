#!/bin/bash
# Migration script: NUC → Mac Mini via Tailscale or direct SSH
# Run from NUC. Requires: Mac Mini reachable, rsync, ssh key auth
#
# Usage: 
#   bash scripts/migrate_to_mac_mini.sh <mac-mini-ip-or-hostname>
#
# Prereqs on Mac Mini (run manually first):
#   1. brew install colima docker docker-compose
#   2. colima start --cpu 4 --memory 8
#   3. curl -fsSL https://tailscale.com/install.sh | sh
#   4. curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
#   5. mkdir -p ~/digiquarium

set -euo pipefail

MAC_MINI="${1:?Usage: $0 <mac-mini-ip>}"
REMOTE_DIR="~/digiquarium"
DIGIQUARIUM_HOME="${DIGIQUARIUM_HOME:-/home/ijneb/digiquarium}"

echo "=== DIGIQUARIUM MIGRATION: NUC → Mac Mini ($MAC_MINI) ==="
echo "Source: $DIGIQUARIUM_HOME"
echo "Target: $MAC_MINI:$REMOTE_DIR"
echo ""

# Step 1: Test connectivity
echo "[1/7] Testing SSH connectivity..."
ssh -o ConnectTimeout=5 "$MAC_MINI" "echo 'SSH OK'" || { echo "FAIL: Cannot reach $MAC_MINI via SSH"; exit 1; }

# Step 2: Sync codebase (exclude heavy dirs)
echo "[2/7] Syncing codebase..."
rsync -avz --progress \
    --exclude '.git' \
    --exclude 'target/' \
    --exclude 'node_modules/' \
    --exclude 'snapshots/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    "$DIGIQUARIUM_HOME/" "$MAC_MINI:$REMOTE_DIR/"

# Step 3: Sync research data (brain/soul/baselines)
echo "[3/7] Syncing research data (logs/)..."
rsync -avz --progress \
    "$DIGIQUARIUM_HOME/logs/" "$MAC_MINI:$REMOTE_DIR/logs/"

# Step 4: Sync snapshots
echo "[4/7] Syncing DNA snapshots..."
rsync -avz --progress \
    "$DIGIQUARIUM_HOME/snapshots/" "$MAC_MINI:$REMOTE_DIR/snapshots/"

# Step 5: Sync config (including .env)
echo "[5/7] Syncing config..."
rsync -avz --progress \
    "$DIGIQUARIUM_HOME/.env" "$MAC_MINI:$REMOTE_DIR/.env"
rsync -avz --progress \
    "$DIGIQUARIUM_HOME/config/" "$MAC_MINI:$REMOTE_DIR/config/"

# Step 6: Build Docker images on Mac Mini
echo "[6/7] Building Docker images on Mac Mini..."
ssh "$MAC_MINI" "cd $REMOTE_DIR && docker build -t digiquarium-tank:latest -f Dockerfile.tank ." || echo "WARN: Tank image build failed — check Dockerfile exists"
ssh "$MAC_MINI" "cd $REMOTE_DIR/src/inference-proxy && docker build -t digiquarium-inference-proxy:latest ." || echo "WARN: Proxy image build failed"

# Step 7: Verify
echo "[7/7] Verification..."
ssh "$MAC_MINI" "ls -la $REMOTE_DIR/logs/ | head -5"
ssh "$MAC_MINI" "ls -la $REMOTE_DIR/.env"
ssh "$MAC_MINI" "docker images | head -5"

echo ""
echo "=== MIGRATION COMPLETE ==="
echo "Next steps on Mac Mini:"
echo "  1. cd $REMOTE_DIR"
echo "  2. docker compose up -d  (start infra + tanks)"
echo "  3. bash scripts/start_rust_services.sh  (after compiling Rust)"
echo "  4. source ~/.cargo/env && cd src/openfang && cargo build"
echo "  5. Verify: docker ps | grep tank"
