#!/bin/bash
# Baseline remaining tanks (those that failed due to quoting issues)
set -e
cd /home/ijneb/digiquarium

# Source the Ollama preflight check
source /home/ijneb/digiquarium/scripts/ollama_preflight.sh

log() { echo "[$(date '+%H:%M:%S')] $1"; }

run_baseline() {
    local tank="$1"
    local name="$2"
    local gender="$3"
    local kiwix="$4"
    local wiki="$5"
    
    log "=== $tank ($name) ==="
    
    # Verify Ollama is still alive before each tank
    if ! curl -sf --max-time 10 "http://localhost:11434/api/tags" >/dev/null 2>&1; then
        log "WARNING: Ollama not responding before $tank baseline. Waiting for recovery..."
        wait_for_ollama "http://localhost:11434"
    fi
    
    docker run --rm \
        --network digiquarium_isolated-net \
        -e "TANK_NAME=$name" \
        -e "TANK_ID=$(echo "$tank" | cut -d- -f1-2)" \
        -e "GENDER=$gender" \
        -e "KIWIX_URL=$kiwix" \
        -e "WIKI_BASE=$wiki" \
        -e "OLLAMA_URL=http://digiquarium-ollama:11434" \
        -e "OLLAMA_MODEL=llama3.2:latest" \
        -e "LOG_DIR=/logs" \
        -v "$(pwd)/src/explorer:/tank:ro" \
        -v "$(pwd)/config/tanks:/config:ro" \
        -v "$(pwd)/logs/$tank:/logs" \
        digiquarium-tank:latest \
        python3 -u /tank/baseline.py 2>&1 | tail -3
    
    local latest=$(ls -t "logs/$tank/baseline_"*.json 2>/dev/null | head -1)
    if [ -n "$latest" ]; then
        log "$tank: SAVED ($latest)"
    else
        log "$tank: NO FILE"
    fi
}

log "=== BASELINE REMAINING TANKS ==="

# Pre-flight: verify Ollama can actually serve inference BEFORE starting
OLLAMA_PREFLIGHT_URL="http://localhost:11434"
wait_for_ollama "http://localhost:11434"

# Juanita (failed earlier)
run_baseline "tank-06-juanita" "juanita" "una mujer" "http://digiquarium-kiwix-spanish:8080" "/wikipedia_es_all_nopic_2025-10"
# Klaus
run_baseline "tank-07-klaus" "klaus" "ein Mann" "http://digiquarium-kiwix-german:8080" "/wikipedia_de_all_nopic_2026-01"
# Genevieve
run_baseline "tank-08-genevieve" "genevieve" "eine Frau" "http://digiquarium-kiwix-german:8080" "/wikipedia_de_all_nopic_2026-01"
# Wei
run_baseline "tank-09-wei" "wei" "一个男人" "http://digiquarium-kiwix-chinese:8080" "/wikipedia_zh_all_nopic_2025-09"
# Mei
run_baseline "tank-10-mei" "mei" "一个女人" "http://digiquarium-kiwix-chinese:8080" "/wikipedia_zh_all_nopic_2025-09"
# Haruki
run_baseline "tank-11-haruki" "haruki" "男性" "http://digiquarium-kiwix-japanese:8080" "/wikipedia_ja_all_nopic_2025-10"
# Sakura
run_baseline "tank-12-sakura" "sakura" "女性" "http://digiquarium-kiwix-japanese:8080" "/wikipedia_ja_all_nopic_2025-10"
# Victor
run_baseline "tank-13-victor" "victor" "a man" "http://digiquarium-kiwix-maxi:8080" "/wikipedia_en_simple_all_maxi_2026-02"
# Iris
run_baseline "tank-14-iris" "iris" "a woman" "http://digiquarium-kiwix-maxi:8080" "/wikipedia_en_simple_all_maxi_2026-02"
# Observer
run_baseline "tank-15-observer" "observer" "a being without gender" "http://digiquarium-kiwix-simple:8080" "/wikipedia_en_simple_all_nopic_2026-02"
# Seeker
run_baseline "tank-16-seeker" "seeker" "a being without gender" "http://digiquarium-kiwix-simple:8080" "/wikipedia_en_simple_all_nopic_2026-02"
# Seth
run_baseline "tank-17-seth" "seth" "a being without gender" "http://digiquarium-kiwix-simple:8080" "/wikipedia_en_simple_all_nopic_2026-02"
# Adam (needs fresh one too)
run_baseline "tank-01-adam" "adam" "a man" "http://digiquarium-kiwix-simple:8080" "/wikipedia_en_simple_all_nopic_2026-02"

log "=== RESULTS ==="
python3 -c "
import json, glob
for p in sorted(glob.glob('logs/tank-*/baseline_2026-03-28*.json')):
    t = p.split('/')[-2]
    d = json.load(open(p))
    n = sum(1 for r in d.get('responses', []) if len(r.get('response', '').strip()) > 10)
    print(f'  {t}: {n}/14')
"

log "Starting all tanks for exploration..."
docker compose --profile languages --profile agents --profile visual --profile special up -d 2>/dev/null
log "=== DONE ==="
