#!/bin/bash
# =============================================================================
# OLLAMA WATCHDOG - Belt & Suspenders (Independent of daemon_supervisor)
# =============================================================================
# Run via cron every minute. This is a SEPARATE safety net from the daemon
# supervisor. It does THREE things:
#   1. Checks if the Docker container is running
#   2. Checks if the Ollama API responds (via docker exec, since port not exposed)
#   3. Does a REAL inference test to verify the model can actually generate
#
# If any check fails, it restarts Ollama and logs everything with timestamps
# to a dedicated crash log for post-mortem analysis.
#
# Install: Add to crontab:
#   * * * * * /home/ijneb/digiquarium/scripts/ollama_watchdog.sh
# =============================================================================

set -u
DIGIQUARIUM_HOME="/home/ijneb/digiquarium"
CONTAINER_NAME="digiquarium-ollama"
CRASH_LOG="$DIGIQUARIUM_HOME/logs/ollama/ollama_crashes.log"
HEALTH_LOG="$DIGIQUARIUM_HOME/logs/ollama/ollama_health.log"
MAX_LOG_SIZE=10485760  # 10MB

# Ensure log directory exists
mkdir -p "$DIGIQUARIUM_HOME/logs/ollama"

# Rotate logs if too large
for logfile in "$CRASH_LOG" "$HEALTH_LOG"; do
    if [ -f "$logfile" ] && [ "$(stat -c%s "$logfile" 2>/dev/null || echo 0)" -gt "$MAX_LOG_SIZE" ]; then
        mv "$logfile" "${logfile}.old"
    fi
done

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log_health() {
    echo "[$(timestamp)] $1" >> "$HEALTH_LOG"
}

log_crash() {
    echo "[$(timestamp)] $1" >> "$CRASH_LOG"
    echo "[$(timestamp)] [WATCHDOG] $1"
}

# Collect system state for crash diagnostics
collect_diagnostics() {
    log_crash "=== DIAGNOSTICS ==="
    log_crash "Memory: $(free -h | grep Mem | awk '{print "total=" $2 " used=" $3 " free=" $4 " available=" $7}')"
    log_crash "Swap: $(free -h | grep Swap | awk '{print "total=" $2 " used=" $3 " free=" $4}')"
    log_crash "Docker container state: $(docker inspect -f '{{.State.Status}} (OOMKilled={{.State.OOMKilled}}, ExitCode={{.State.ExitCode}}, StartedAt={{.State.StartedAt}}, FinishedAt={{.State.FinishedAt}})' $CONTAINER_NAME 2>&1)"
    log_crash "Docker daemon uptime: $(docker info --format '{{.ServerVersion}}' 2>&1)"
    log_crash "Container restart count: $(docker inspect -f '{{.RestartCount}}' $CONTAINER_NAME 2>&1)"
    log_crash "Last 5 container logs (stderr):"
    docker logs --tail 5 "$CONTAINER_NAME" 2>&1 | while IFS= read -r line; do
        log_crash "  | $line"
    done
    log_crash "=== END DIAGNOSTICS ==="
}

restart_ollama() {
    local reason="$1"
    log_crash "RESTART TRIGGERED: $reason"
    collect_diagnostics
    
    # Try docker compose first (preserves network config)
    log_crash "Attempting restart via docker compose..."
    cd "$DIGIQUARIUM_HOME"
    if docker compose up -d ollama 2>&1; then
        log_crash "docker compose up -d ollama succeeded"
    else
        log_crash "docker compose failed, trying docker restart..."
        docker restart "$CONTAINER_NAME" 2>&1 || true
    fi
    
    # Wait for container to come up
    local waited=0
    while [ $waited -lt 60 ]; do
        if docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null | grep -q 'true'; then
            log_crash "Container is running after ${waited}s"
            break
        fi
        sleep 5
        waited=$((waited + 5))
    done
    
    # Wait for API to respond (via docker exec since port not exposed to host)
    waited=0
    while [ $waited -lt 90 ]; do
        if docker exec "$CONTAINER_NAME" ollama list >/dev/null 2>&1; then
            log_crash "Ollama responding after restart (waited ${waited}s additional)"
            log_crash "RESTART COMPLETE - Ollama recovered"
            return 0
        fi
        sleep 5
        waited=$((waited + 5))
    done
    
    log_crash "RESTART FAILED - Ollama still not responding after 90s"
    return 1
}

# =============================================================================
# CHECK 1: Is the Docker container running?
# =============================================================================
check_container() {
    local state
    state=$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME" 2>&1)
    if [ $? -ne 0 ] || [ "$state" != "true" ]; then
        return 1
    fi
    return 0
}

# =============================================================================
# CHECK 2: Does Ollama respond? (via docker exec since port not exposed)
# =============================================================================
check_api() {
    if ! docker exec "$CONTAINER_NAME" ollama list >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

# =============================================================================
# CHECK 3: Can Ollama actually serve an inference request?
# Uses a tank container on the isolated network to test real inference.
# =============================================================================
check_inference() {
    local response
    # Run a quick inference test via a temporary container on the same network
    response=$(docker run --rm --network digiquarium_isolated-net \
        digiquarium-tank:latest \
        curl -sf --max-time 30 "http://digiquarium-ollama:11434/api/generate" \
        -d '{"model": "llama3.2:latest", "prompt": "Say OK", "stream": false, "options": {"num_predict": 5}}' 2>&1)
    
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Verify we got an actual response field
    if ! echo "$response" | grep -q '"response"'; then
        return 1
    fi
    
    return 0
}

# =============================================================================
# MAIN WATCHDOG LOOP
# =============================================================================
main() {
    # Check 1: Container running?
    if ! check_container; then
        log_crash "CHECK FAILED: Container not running"
        restart_ollama "Container not running"
        return
    fi
    
    # Check 2: API responding?
    if ! check_api; then
        log_crash "CHECK FAILED: Ollama not responding (container is running)"
        restart_ollama "Ollama not responding despite container running"
        return
    fi
    
    # Check 3: Inference working? (only run every 5th minute to reduce load)
    local minute
    minute=$(date '+%M')
    if [ $((minute % 5)) -eq 0 ]; then
        if ! check_inference; then
            log_crash "CHECK FAILED: Inference test failed (ollama responds but can't generate)"
            restart_ollama "Inference test failed - model may be corrupted or OOM"
            return
        fi
        log_health "OK: container=up ollama=up inference=ok mem=$(free -h | grep Mem | awk '{print $3 "/" $2}')"
    else
        log_health "OK: container=up ollama=up mem=$(free -h | grep Mem | awk '{print $3 "/" $2}')"
    fi
}

main
