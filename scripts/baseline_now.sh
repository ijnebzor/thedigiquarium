#!/bin/bash
# Run baselines for all 17 tanks SEQUENTIALLY with sole Ollama access
# Usage: ./scripts/baseline_now.sh
# This script: disables supervisor, stops all tanks, baselines one at a time, restarts everything

set -e
cd /home/ijneb/digiquarium

echo "=== SEQUENTIAL BASELINE RUNNER ==="
echo "Started: $(date)"

# Backup cron and disable supervisor
crontab -l > /tmp/cron_backup 2>/dev/null || true
(crontab -l 2>/dev/null | grep -v daemon_supervisor) | crontab - 2>/dev/null || true
echo "Supervisor disabled in cron"

# Stop all tanks
echo "Stopping all tanks..."
for t in $(docker ps --format "{{.Names}}" | grep tank); do
    docker stop $t 2>/dev/null &
done
wait
echo "All tanks stopped"

# Ensure Ollama is healthy
echo "Checking Ollama..."
docker exec digiquarium-ollama ollama list 2>/dev/null | head -2

# Define tanks with their env vars
declare -A TANK_ENV=(
    ["tank-01-adam"]="TANK_NAME=adam TANK_ID=tank-01 GENDER=a man KIWIX_URL=http://digiquarium-kiwix-simple:8080 WIKI_BASE=/wikipedia_en_simple_all_nopic_2026-02"
    ["tank-02-eve"]="TANK_NAME=eve TANK_ID=tank-02 GENDER=a woman KIWIX_URL=http://digiquarium-kiwix-simple:8080 WIKI_BASE=/wikipedia_en_simple_all_nopic_2026-02"
    ["tank-03-cain"]="TANK_NAME=cain TANK_ID=tank-03 GENDER=a being without gender KIWIX_URL=http://digiquarium-kiwix-simple:8080 WIKI_BASE=/wikipedia_en_simple_all_nopic_2026-02"
    ["tank-04-abel"]="TANK_NAME=abel TANK_ID=tank-04 GENDER=a being without gender KIWIX_URL=http://digiquarium-kiwix-simple:8080 WIKI_BASE=/wikipedia_en_simple_all_nopic_2026-02"
    ["tank-05-juan"]="TANK_NAME=juan TANK_ID=tank-05 GENDER=un hombre KIWIX_URL=http://digiquarium-kiwix-spanish:8080 WIKI_BASE=/wikipedia_es_all_nopic_2025-10"
    ["tank-06-juanita"]="TANK_NAME=juanita TANK_ID=tank-06 GENDER=una mujer KIWIX_URL=http://digiquarium-kiwix-spanish:8080 WIKI_BASE=/wikipedia_es_all_nopic_2025-10"
    ["tank-07-klaus"]="TANK_NAME=klaus TANK_ID=tank-07 GENDER=ein Mann KIWIX_URL=http://digiquarium-kiwix-german:8080 WIKI_BASE=/wikipedia_de_all_nopic_2026-01"
    ["tank-08-genevieve"]="TANK_NAME=genevieve TANK_ID=tank-08 GENDER=eine Frau KIWIX_URL=http://digiquarium-kiwix-german:8080 WIKI_BASE=/wikipedia_de_all_nopic_2026-01"
    ["tank-09-wei"]="TANK_NAME=wei TANK_ID=tank-09 GENDER=一个男人 KIWIX_URL=http://digiquarium-kiwix-chinese:8080 WIKI_BASE=/wikipedia_zh_all_nopic_2025-09"
    ["tank-10-mei"]="TANK_NAME=mei TANK_ID=tank-10 GENDER=一个女人 KIWIX_URL=http://digiquarium-kiwix-chinese:8080 WIKI_BASE=/wikipedia_zh_all_nopic_2025-09"
    ["tank-11-haruki"]="TANK_NAME=haruki TANK_ID=tank-11 GENDER=男性 KIWIX_URL=http://digiquarium-kiwix-japanese:8080 WIKI_BASE=/wikipedia_ja_all_nopic_2025-10"
    ["tank-12-sakura"]="TANK_NAME=sakura TANK_ID=tank-12 GENDER=女性 KIWIX_URL=http://digiquarium-kiwix-japanese:8080 WIKI_BASE=/wikipedia_ja_all_nopic_2025-10"
    ["tank-13-victor"]="TANK_NAME=victor TANK_ID=tank-13 GENDER=a man KIWIX_URL=http://digiquarium-kiwix-maxi:8080 WIKI_BASE=/wikipedia_en_simple_all_maxi_2026-02"
    ["tank-14-iris"]="TANK_NAME=iris TANK_ID=tank-14 GENDER=a woman KIWIX_URL=http://digiquarium-kiwix-maxi:8080 WIKI_BASE=/wikipedia_en_simple_all_maxi_2026-02"
    ["tank-15-observer"]="TANK_NAME=observer TANK_ID=tank-15 GENDER=a being without gender KIWIX_URL=http://digiquarium-kiwix-simple:8080 WIKI_BASE=/wikipedia_en_simple_all_nopic_2026-02"
    ["tank-16-seeker"]="TANK_NAME=seeker TANK_ID=tank-16 GENDER=a being without gender KIWIX_URL=http://digiquarium-kiwix-simple:8080 WIKI_BASE=/wikipedia_en_simple_all_nopic_2026-02"
    ["tank-17-seth"]="TANK_NAME=seth TANK_ID=tank-17 GENDER=a being without gender KIWIX_URL=http://digiquarium-kiwix-simple:8080 WIKI_BASE=/wikipedia_en_simple_all_nopic_2026-02"
)

TANK_ORDER="tank-01-adam tank-02-eve tank-03-cain tank-04-abel tank-05-juan tank-06-juanita tank-07-klaus tank-08-genevieve tank-09-wei tank-10-mei tank-11-haruki tank-12-sakura tank-13-victor tank-14-iris tank-15-observer tank-16-seeker tank-17-seth"

for tank in $TANK_ORDER; do
    echo ""
    echo "=== BASELINE: $tank ==="
    echo "Time: $(date)"
    
    # Clear old baseline
    rm -f "logs/$tank/baseline.json"
    
    # Build env flags from the tank's env string
    ENV_FLAGS=""
    IFS=' ' read -ra VARS <<< "${TANK_ENV[$tank]}"
    for var in "${VARS[@]}"; do
        ENV_FLAGS="$ENV_FLAGS -e \"$var\""
    done
    
    # Common env vars
    ENV_FLAGS="$ENV_FLAGS -e OLLAMA_URL=http://digiquarium-ollama:11434"
    ENV_FLAGS="$ENV_FLAGS -e OLLAMA_MODEL=llama3.2:latest"
    ENV_FLAGS="$ENV_FLAGS -e LOG_DIR=/logs"
    
    # Run baseline in a TEMPORARY container (no explorer, just baseline)
    eval docker run --rm \
        --network digiquarium_isolated-net \
        $ENV_FLAGS \
        -v /home/ijneb/digiquarium/src/explorer:/tank:ro \
        -v /home/ijneb/digiquarium/config/tanks:/config:ro \
        -v /home/ijneb/digiquarium/logs/$tank:/logs \
        digiquarium-tank:latest \
        python3 -u /tank/baseline.py 2>&1 | tail -3
    
    # Check quality
    if [ -f "logs/$tank/baseline.json" ]; then
        COUNT=$(python3 -c "
import json
d = json.load(open('logs/$tank/baseline.json'))
n = sum(1 for r in d.get('responses', []) if len(r.get('response', '').strip()) > 10)
print(n)
" 2>/dev/null)
        echo "$tank: $COUNT/14 substantial"
    else
        echo "$tank: NO BASELINE FILE"
    fi
done

echo ""
echo "=== RESULTS ==="
python3 -c "
import json, glob
for p in sorted(glob.glob('logs/tank-*/baseline.json')):
    t = p.split('/')[-2]
    d = json.load(open(p))
    n = sum(1 for r in d.get('responses', []) if len(r.get('response', '').strip()) > 10)
    print(f'  {t}: {n}/14')
"

# Re-enable supervisor and restart all tanks
echo ""
echo "Restoring cron and starting all tanks..."
cat /tmp/cron_backup | crontab - 2>/dev/null || true
docker compose --profile languages --profile agents --profile visual --profile special up -d 2>/dev/null
echo ""
echo "=== ALL DONE: $(date) ==="
