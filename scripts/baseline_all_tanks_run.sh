#!/bin/bash
# ============================================================================
# LIBRARIAN BASELINE — ALL TANKS (docker run approach)
# Creates temp containers for each baseline. No explorer competition.
# Tanks stay paused throughout; temp containers use default network.
# Lock files are DELETED and RECREATED (new inodes) to avoid stale fcntl locks
# from paused containers.
# ============================================================================
set -uo pipefail
cd /home/ijneb/digiquarium

LOGFILE="logs/baseline_all_tanks.log"
mkdir -p logs
> "$LOGFILE"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg" | tee -a "$LOGFILE"
}

reset_locks() {
    # DELETE and RECREATE lock files to get new inodes
    # Paused containers hold fcntl locks on old inodes, so new files are clean
    cd /home/ijneb/digiquarium/shared
    for f in .cerebras_rate_lock .together_rate_lock .groq_rate_lock .ollama_rate_lock .ollama_lock .cerebras_last_call .together_last_call .groq_last_call .ollama_last_call; do
        rm -f "$f" 2>/dev/null
        touch "$f" 2>/dev/null
        chmod 666 "$f" 2>/dev/null
    done
    cd /home/ijneb/digiquarium
}

# All tank containers in order
ORIGINAL_TANKS=(
    tank-01-adam tank-02-eve tank-03-cain tank-04-abel
    tank-05-juan tank-06-juanita tank-07-klaus tank-08-genevieve
    tank-09-wei tank-10-mei tank-11-haruki tank-12-sakura
    tank-13-victor tank-14-iris tank-15-observer tank-16-seeker tank-17-seth
)
BETACLONE_TANKS=(
    betaclone-redux-03-cain betaclone-redux-04-abel
    betaclone-redux-05-juan betaclone-redux-06-juanita
    betaclone-redux-07-klaus betaclone-redux-08-genevieve
    betaclone-redux-09-wei betaclone-redux-10-mei
    betaclone-redux-11-haruki betaclone-redux-12-sakura
    betaclone-redux-13-victor betaclone-redux-14-iris
    betaclone-redux-15-observer betaclone-redux-16-seeker betaclone-redux-17-seth
)
ALL_TANKS=("${ORIGINAL_TANKS[@]}" "${BETACLONE_TANKS[@]}")
TOTAL=${#ALL_TANKS[@]}
PASSED=0
FAILED=0

RESULTS_FILE=$(mktemp)

log "============================================================"
log "LIBRARIAN BASELINE RUN — ALL $TOTAL TANKS"
log "============================================================"

# ── Clear rate lock files (delete+recreate for new inodes) ──
log "Resetting shared rate lock files (new inodes)..."
reset_locks
log "Rate locks reset."

# ── Ensure all tanks are paused ──
log "Ensuring all $TOTAL tanks are paused..."
for tank in "${ALL_TANKS[@]}"; do
    docker pause "$tank" >> "$LOGFILE" 2>&1 || true
done
log "All tanks paused."

# ── Run baselines via docker run ──
run_single_baseline() {
    local tank="$1"
    local idx="$2"

    log ""
    log "━━━ [$idx/$TOTAL] $tank ━━━"

    # Extract env vars from the existing container
    local env_data
    env_data=$(docker inspect "$tank" --format '{{range .Config.Env}}{{println .}}{{end}}')

    local TANK_NAME TANK_ID GENDER KIWIX_URL WIKI_BASE CEREBRAS_KEY TOGETHER_KEY GROQ_KEY
    TANK_NAME=$(echo "$env_data" | grep "^TANK_NAME=" | cut -d= -f2-)
    TANK_ID=$(echo "$env_data" | grep "^TANK_ID=" | cut -d= -f2-)
    GENDER=$(echo "$env_data" | grep "^GENDER=" | cut -d= -f2-)
    KIWIX_URL=$(echo "$env_data" | grep "^KIWIX_URL=" | cut -d= -f2-)
    WIKI_BASE=$(echo "$env_data" | grep "^WIKI_BASE=" | cut -d= -f2-)
    CEREBRAS_KEY=$(echo "$env_data" | grep "^CEREBRAS_API_KEY=" | cut -d= -f2-)
    TOGETHER_KEY=$(echo "$env_data" | grep "^TOGETHER_API_KEY=" | cut -d= -f2-)
    GROQ_KEY=$(echo "$env_data" | grep "^GROQ_API_KEY=" | cut -d= -f2-)

    log "  Name=$TANK_NAME Gender=$GENDER"

    # Reset locks (new inodes) before each baseline
    reset_locks

    local start_time=$(date +%s)
    log "  Starting baseline at $(date '+%H:%M:%S')..."

    # Run baseline in a fresh temp container on default network (has internet for cloud APIs)
    docker run --rm \
        --network digiquarium_default \
        -e "TANK_NAME=$TANK_NAME" \
        -e "TANK_ID=$TANK_ID" \
        -e "GENDER=$GENDER" \
        -e "KIWIX_URL=$KIWIX_URL" \
        -e "WIKI_BASE=$WIKI_BASE" \
        -e "OLLAMA_URL=http://digiquarium-ollama:11434" \
        -e "OLLAMA_MODEL=llama3.2:latest" \
        -e "CEREBRAS_API_KEY=$CEREBRAS_KEY" \
        -e "CEREBRAS_MODEL=llama3.1-8b" \
        -e "TOGETHER_API_KEY=$TOGETHER_KEY" \
        -e "TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo" \
        -e "GROQ_API_KEY=$GROQ_KEY" \
        -e "GROQ_MODEL=llama-3.1-8b-instant" \
        -e "LOG_DIR=/logs" \
        -v "$(pwd)/src/explorer:/tank:ro" \
        -v "$(pwd)/config/tanks:/config:ro" \
        -v "$(pwd)/logs/$tank:/logs" \
        -v "$(pwd)/shared:/shared" \
        digiquarium-tank:latest \
        python3 -u /tank/baseline.py >> "$LOGFILE" 2>&1

    local exit_code=$?
    local end_time=$(date +%s)
    local duration=$(( end_time - start_time ))
    log "  Completed in ${duration}s (exit=$exit_code)"

    # Check result
    local substantial=0
    if [ -f "logs/$tank/baseline_latest.json" ]; then
        substantial=$(python3 -c "
import json
d = json.load(open('logs/$tank/baseline_latest.json'))
print(sum(1 for r in d.get('responses', []) if len(r.get('response', '').strip()) > 10))
" 2>/dev/null || echo "0")
    fi

    log "  Result: $substantial/14 substantial responses"

    # If below threshold, retry once after 30s
    if [ "$substantial" -lt 12 ] 2>/dev/null; then
        log "  Below 12 threshold. Waiting 30s and retrying..."
        sleep 30
        reset_locks

        docker run --rm \
            --network digiquarium_default \
            -e "TANK_NAME=$TANK_NAME" \
            -e "TANK_ID=$TANK_ID" \
            -e "GENDER=$GENDER" \
            -e "KIWIX_URL=$KIWIX_URL" \
            -e "WIKI_BASE=$WIKI_BASE" \
            -e "OLLAMA_URL=http://digiquarium-ollama:11434" \
            -e "OLLAMA_MODEL=llama3.2:latest" \
            -e "CEREBRAS_API_KEY=$CEREBRAS_KEY" \
            -e "CEREBRAS_MODEL=llama3.1-8b" \
            -e "TOGETHER_API_KEY=$TOGETHER_KEY" \
            -e "TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo" \
            -e "GROQ_API_KEY=$GROQ_KEY" \
            -e "GROQ_MODEL=llama-3.1-8b-instant" \
            -e "LOG_DIR=/logs" \
            -v "$(pwd)/src/explorer:/tank:ro" \
            -v "$(pwd)/config/tanks:/config:ro" \
            -v "$(pwd)/logs/$tank:/logs" \
            -v "$(pwd)/shared:/shared" \
            digiquarium-tank:latest \
            python3 -u /tank/baseline.py >> "$LOGFILE" 2>&1 || true

        if [ -f "logs/$tank/baseline_latest.json" ]; then
            substantial=$(python3 -c "
import json
d = json.load(open('logs/$tank/baseline_latest.json'))
print(sum(1 for r in d.get('responses', []) if len(r.get('response', '').strip()) > 10))
" 2>/dev/null || echo "0")
        fi
        log "  Retry result: $substantial/14 substantial"
    fi

    # Track result
    if [ "$substantial" -ge 12 ] 2>/dev/null; then
        PASSED=$((PASSED + 1))
        echo "$tank: $substantial/14 GOOD" >> "$RESULTS_FILE"
    else
        FAILED=$((FAILED + 1))
        echo "$tank: $substantial/14 POOR" >> "$RESULTS_FILE"
    fi
}

# Run original tanks
log ""
log "========== ORIGINAL TANKS (1-17) =========="
IDX=0
for tank in "${ORIGINAL_TANKS[@]}"; do
    IDX=$((IDX + 1))
    run_single_baseline "$tank" "$IDX" || true
done

# Run betaclone-redux tanks
log ""
log "========== BETACLONE-REDUX TANKS =========="
for tank in "${BETACLONE_TANKS[@]}"; do
    IDX=$((IDX + 1))
    run_single_baseline "$tank" "$IDX" || true
done

# ── Unpause all tanks ──
log ""
log "Unpausing all tanks..."
for tank in "${ALL_TANKS[@]}"; do
    docker unpause "$tank" >> "$LOGFILE" 2>&1 || true
done
log "All tanks unpaused."

# ── Update admin panel ──
log ""
log "Updating admin status panel..."
python3 /home/ijneb/digiquarium/scripts/update_admin_status.py >> "$LOGFILE" 2>&1 || log "WARN: Admin status update failed"

# ── FINAL REPORT ──
log ""
log "============================================================"
log "LIBRARIAN BASELINE — FINAL REPORT"
log "============================================================"
log "Total tanks: $TOTAL"
log "Passed (12+): $PASSED"
log "Failed (<12): $FAILED"
log ""
log "Individual results:"
cat "$RESULTS_FILE" | while read -r line; do
    log "  $line"
done
rm -f "$RESULTS_FILE"
log ""
log "============================================================"
log "ALL BASELINES COMPLETE at $(date '+%Y-%m-%d %H:%M:%S')"
log "============================================================"
