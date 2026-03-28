#!/bin/bash
# =============================================================================
# OLLAMA PRE-FLIGHT CHECK
# =============================================================================
# Source this file from any baseline script to ensure Ollama is ready.
# Usage:
#   source /home/ijneb/digiquarium/scripts/ollama_preflight.sh
#   wait_for_ollama   # blocks until Ollama can serve inference, or exits
# =============================================================================

OLLAMA_PREFLIGHT_URL="${OLLAMA_URL:-http://digiquarium-ollama:11434}"
OLLAMA_PREFLIGHT_MAX_WAIT=300  # 5 minutes max wait
OLLAMA_PREFLIGHT_MODEL="${OLLAMA_MODEL:-llama3.2:latest}"

wait_for_ollama() {
    local url="${1:-$OLLAMA_PREFLIGHT_URL}"
    local max_wait="${2:-$OLLAMA_PREFLIGHT_MAX_WAIT}"
    local waited=0
    local step=10

    echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Checking Ollama at $url..."

    # Phase 1: Wait for API to respond
    while [ $waited -lt $max_wait ]; do
        if curl -sf --max-time 5 "$url/api/tags" >/dev/null 2>&1; then
            echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Ollama API is responding"
            break
        fi
        echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Waiting for Ollama API... (${waited}s/${max_wait}s)"
        sleep $step
        waited=$((waited + step))
    done

    if [ $waited -ge $max_wait ]; then
        echo "[$(date '+%H:%M:%S')] PRE-FLIGHT FAILED: Ollama API not responding after ${max_wait}s"
        echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Attempting restart..."
        cd /home/ijneb/digiquarium && docker compose up -d ollama 2>&1
        sleep 30
        if ! curl -sf --max-time 5 "$url/api/tags" >/dev/null 2>&1; then
            echo "[$(date '+%H:%M:%S')] PRE-FLIGHT FATAL: Ollama still not responding after restart. Aborting."
            exit 1
        fi
    fi

    # Phase 2: Do a real inference test
    echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Testing inference with $OLLAMA_PREFLIGHT_MODEL..."
    local inference_ok=false
    local attempts=0
    local max_attempts=3

    while [ $attempts -lt $max_attempts ]; do
        local response
        response=$(curl -sf --max-time 60 "$url/api/generate" \
            -d "{\"model\": \"$OLLAMA_PREFLIGHT_MODEL\", \"prompt\": \"Say OK\", \"stream\": false, \"options\": {\"num_predict\": 5}}" 2>&1)
        
        if [ $? -eq 0 ] && echo "$response" | grep -q '"response"'; then
            echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Inference test PASSED (attempt $((attempts+1)))"
            inference_ok=true
            break
        fi
        
        attempts=$((attempts + 1))
        echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Inference test failed (attempt $attempts/$max_attempts)"
        if [ $attempts -lt $max_attempts ]; then
            sleep 15
        fi
    done

    if [ "$inference_ok" = false ]; then
        echo "[$(date '+%H:%M:%S')] PRE-FLIGHT FATAL: Ollama cannot serve inference after $max_attempts attempts. Aborting."
        exit 1
    fi

    echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: All checks passed. Ollama is ready."
}
