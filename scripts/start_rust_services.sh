#!/bin/bash
# Start all Rust services for The Digiquarium
# Run this after reboot or if services have died
# Usage: bash scripts/start_rust_services.sh

DIGIQUARIUM_HOME="${DIGIQUARIUM_HOME:-/home/ijneb/digiquarium}"
cd "$DIGIQUARIUM_HOME" || exit 1

echo "[rust-services] Starting Digiquarium Rust services..."

# OpenFang — daemon orchestrator
if ! pgrep -f "openfang" > /dev/null; then
    nohup "$DIGIQUARIUM_HOME/src/openfang/target/debug/openfang" > /tmp/openfang.log 2>&1 &
    echo "[rust-services] OpenFang started (PID $!)"
else
    echo "[rust-services] OpenFang already running"
fi

# Rustunnel — visitor tank reverse proxy
if ! pgrep -f "rustunnel" > /dev/null; then
    nohup "$DIGIQUARIUM_HOME/src/rustunnel/target/debug/rustunnel" > /tmp/rustunnel.log 2>&1 &
    echo "[rust-services] Rustunnel started (PID $!)"
else
    echo "[rust-services] Rustunnel already running"
fi

# RedAmon — security red teaming
if ! pgrep -f "redamon" > /dev/null; then
    nohup "$DIGIQUARIUM_HOME/src/redamon/target/debug/redamon" > /tmp/redamon.log 2>&1 &
    echo "[rust-services] RedAmon started (PID $!)"
else
    echo "[rust-services] RedAmon already running"
fi

echo "[rust-services] Done."
