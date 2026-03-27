#!/bin/bash
# Sequential baseline runner - one tank at a time for clean Ollama responses
# This ensures each tank gets dedicated inference time

cd /home/ijneb/digiquarium

echo "=== SEQUENTIAL BASELINE RUNNER ==="
echo "Started: $(date)"
echo ""

# Start infrastructure only
echo "Starting infrastructure..."
docker compose up -d ollama kiwix-simple 2>/dev/null
sleep 5

# Verify Ollama is responding
echo "Verifying Ollama..."
docker exec digiquarium-ollama ollama list 2>/dev/null | head -3
echo ""

# All tanks in order - standard tanks use kiwix-simple
SIMPLE_TANKS="tank-01-adam tank-02-eve"
# These need their own kiwix servers started
LANG_TANKS_ES="tank-05-juan tank-06-juanita"
LANG_TANKS_DE="tank-07-klaus tank-08-genevieve"
LANG_TANKS_ZH="tank-09-wei tank-10-mei"
LANG_TANKS_JA="tank-11-haruki tank-12-sakura"
VISUAL_TANKS="tank-13-victor tank-14-iris"
SPECIAL_TANKS="tank-15-observer tank-16-seeker"
AGENT_TANKS="tank-03-cain tank-04-abel tank-17-seth"

run_baseline() {
    local tank=$1
    local compose_name=$(echo $tank | sed 's/tank-[0-9]*-//')
    
    echo "============================================"
    echo "BASELINE: $tank ($compose_name)"
    echo "Time: $(date)"
    echo "============================================"
    
    # Clear old baseline
    rm -f /home/ijneb/digiquarium/logs/$tank/baseline.json
    
    # Start just this tank
    docker compose --profile languages --profile agents --profile visual --profile special start $compose_name 2>/dev/null
    
    # Wait for baseline to complete (check every 10 seconds, max 10 minutes)
    local elapsed=0
    local max_wait=600
    while [ $elapsed -lt $max_wait ]; do
        sleep 10
        elapsed=$((elapsed + 10))
        
        # Check if baseline file exists and has content
        if [ -f "/home/ijneb/digiquarium/logs/$tank/baseline.json" ]; then
            local size=$(stat -f%z "/home/ijneb/digiquarium/logs/$tank/baseline.json" 2>/dev/null || stat -c%s "/home/ijneb/digiquarium/logs/$tank/baseline.json" 2>/dev/null)
            if [ "$size" -gt 500 ] 2>/dev/null; then
                # Check if all 14 questions answered
                local count=$(python3 -c "import json; d=json.load(open('/home/ijneb/digiquarium/logs/$tank/baseline.json')); print(len([r for r in d.get('responses',[]) if len(r.get('response','').strip()) > 10]))" 2>/dev/null)
                echo "  [$elapsed s] Baseline file: ${size} bytes, $count/14 substantial responses"
                if [ "$count" -ge 12 ]; then
                    echo "  COMPLETE - $count/14 substantial responses"
                    break
                fi
            fi
        else
            # Check progress from logs
            local qn=$(docker logs --tail 3 $tank 2>&1 | grep -oP '\[\d+/14\]' | tail -1)
            echo "  [$elapsed s] Progress: $qn"
        fi
    done
    
    # Stop the tank after baseline (it will be restarted for exploration later)
    docker compose --profile languages --profile agents --profile visual --profile special stop $compose_name 2>/dev/null
    
    echo "  Done with $tank"
    echo ""
}

# Run simple English tanks first
echo ""
echo "=== CONTROL GROUP (English Simple) ==="
for tank in $SIMPLE_TANKS; do run_baseline $tank; done

# Start Spanish kiwix, run Spanish tanks
echo "=== SPANISH GROUP ==="
docker compose --profile languages up -d kiwix-spanish 2>/dev/null
sleep 3
for tank in $LANG_TANKS_ES; do run_baseline $tank; done

# German
echo "=== GERMAN GROUP ==="
docker compose --profile languages up -d kiwix-german 2>/dev/null
sleep 3
for tank in $LANG_TANKS_DE; do run_baseline $tank; done

# Chinese
echo "=== CHINESE GROUP ==="
docker compose --profile languages up -d kiwix-chinese 2>/dev/null
sleep 3
for tank in $LANG_TANKS_ZH; do run_baseline $tank; done

# Japanese
echo "=== JAPANESE GROUP ==="
docker compose --profile languages up -d kiwix-japanese 2>/dev/null
sleep 3
for tank in $LANG_TANKS_JA; do run_baseline $tank; done

# Visual
echo "=== VISUAL GROUP ==="
docker compose --profile visual up -d kiwix-maxi 2>/dev/null
sleep 3
for tank in $VISUAL_TANKS; do run_baseline $tank; done

# Special
echo "=== SPECIAL GROUP ==="
for tank in $SPECIAL_TANKS; do run_baseline $tank; done

# Agents
echo "=== AGENT GROUP ==="
for tank in $AGENT_TANKS; do run_baseline $tank; done

echo ""
echo "=== ALL BASELINES COMPLETE ==="
echo "Finished: $(date)"
echo ""

# Print summary
echo "=== RESULTS SUMMARY ==="
python3 -c "
import json, glob
for path in sorted(glob.glob('/home/ijneb/digiquarium/logs/tank-*/baseline.json')):
    tank = path.split('/')[-2]
    try:
        data = json.load(open(path))
        responses = data.get('responses', [])
        substantial = sum(1 for r in responses if len(r.get('response','').strip()) > 10)
        print(f'{tank}: {substantial}/14 substantial responses')
    except:
        print(f'{tank}: ERROR reading baseline')
"

echo ""
echo "Starting all tanks for exploration..."
docker compose --profile languages --profile agents --profile visual --profile special up -d 2>/dev/null
echo "All tanks started. Exploration begins."
