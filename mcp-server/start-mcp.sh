#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
export DIGIQUARIUM_DIR="${DIGIQUARIUM_HOME:-/home/ijneb/digiquarium}"
exec python "$SCRIPT_DIR/server.py"
