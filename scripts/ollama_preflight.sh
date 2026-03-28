#!/bin/bash
# =============================================================================
# OLLAMA PRE-FLIGHT CHECK
# =============================================================================
# Source this file from any baseline script to ensure Ollama is ready.
# Usage:
#   source /home/ijneb/digiquarium/scripts/ollama_preflight.sh
#   wait_for_ollama   # blocks until Ollama can serve inference, or exits
#
# NOTE: Baseline scripts run on the HOST, not inside containers.
# We use docker exec / docker run for checks since Ollama port isn't exposed.
# =============================================================================

OLLAMA_PREFLIGHT_CONTAINER="${OLLAMA_CONTAINER:-digiquarium-ollama}"
OLLAMA_PREFLIGHT_MAX_WAIT=300  # 5 minutes max wait
OLLAMA_PREFLIGHT_MODEL="${OLLAMA_MODEL:-llama3.2:latest}"

wait_for_ollama() {
    local max_wait="${1:-$OLLAMA_PREFLIGHT_MAX_WAIT}"
    local waited=0
    local step=10

    echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Checking Ollama container..."

    # Phase 1: Wait for container to be running and Ollama to respond
    while [ $waited -lt $max_wait ]; do
        if docker exec "$OLLAMA_PREFLIGHT_CONTAINER" ollama list >/dev/null 2>&1; then
            echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Ollama is responding"
            break
        fi
        echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Waiting for Ollama... (${waited}s/${max_wait}s)"
        sleep $step
        waited=$((waited + step))
    done

    if [ $waited -ge $max_wait ]; then
        echo "[$(date '+%H:%M:%S')] PRE-FLIGHT FAILED: Ollama not responding after ${max_wait}s"
        echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Attempting restart..."
        cd /home/ijneb/digiquarium && docker compose up -d ollama 2>&1
        sleep 30
        if ! docker exec "$OLLAMA_PREFLIGHT_CONTAINER" ollama list >/dev/null 2>&1; then
            echo "[$(date '+%H:%M:%S')] PRE-FLIGHT FATAL: Ollama still not responding after restart. Aborting."
            exit 1
        fi
    fi

    # Phase 2: Do a real inference test via a tank container on the network
    echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Testing inference with $OLLAMA_PREFLIGHT_MODEL..."
    local inference_ok=false
    local attempts=0
    local max_attempts=3

    while [ $attempts -lt $max_attempts ]; do
        local result
        result=$(docker run --rm --network digiquarium_isolated-net \
            digiquarium-tank:latest \
            python3 -c "
import urllib.request, json, sys
try:
    data = json.dumps({'model':'$OLLAMA_PREFLIGHT_MODEL','prompt':'Say OK','stream':False,'options':{'num_predict':3}}).encode()
    req = urllib.request.Request('http://digiquarium-ollama:11434/api/generate', data=data, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())
        if 'response' in resp and len(resp['response'].strip()) > 0:
            print('INFERENCE_OK')
            sys.exit(0)
    print('INFERENCE_FAIL')
    sys.exit(1)
except Exception as e:
    print(f'INFERENCE_ERROR: {e}')
    sys.exit(1)
" 2>&1)
        
        if echo "$result" | grep -q "INFERENCE_OK"; then
            echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Inference test PASSED (attempt $((attempts+1)))"
            inference_ok=true
            break
        fi
        
        attempts=$((attempts + 1))
        echo "[$(date '+%H:%M:%S')] PRE-FLIGHT: Inference test failed (attempt $attempts/$max_attempts): $result"
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
