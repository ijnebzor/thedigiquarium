#!/bin/bash
cd /home/ijneb/digiquarium

wait_done() {
    local tank=$1
    local max=600
    local e=0
    while [ $e -lt $max ]; do
        sleep 15
        e=$((e + 15))
        if [ -f "logs/$tank/baseline.json" ]; then
            local c=$(python3 -c "import json;d=json.load(open('logs/$tank/baseline.json'));print(sum(1 for r in d.get('responses',[]) if len(r.get('response','').strip())>10))" 2>/dev/null)
            echo "$tank: $c/14 (${e}s)"
            if [ "$c" -ge 12 ] 2>/dev/null; then
                echo "$tank: COMPLETE"
                return 0
            fi
        else
            local q=$(docker logs --tail 3 $tank 2>&1 | grep -oP '\[\d+/14\]' | tail -1)
            echo "$tank: ${q:-waiting} (${e}s)"
        fi
    done
    echo "$tank: TIMEOUT"
    return 1
}

run_tank() {
    local tank=$1
    local profiles="$2"
    echo ""
    echo "======= BASELINE: $tank ======="
    rm -f logs/$tank/baseline.json
    docker compose $profiles up -d $tank 2>/dev/null
    sleep 3
    wait_done $tank
    docker stop $tank 2>/dev/null
}

# Cain is already running - wait for it
echo "=== Waiting for Cain (already started) ==="
wait_done tank-03-cain
docker stop tank-03-cain 2>/dev/null

# Abel
run_tank tank-04-abel "--profile agents"

# Spanish
docker compose --profile languages up -d kiwix-spanish 2>/dev/null
sleep 3
run_tank tank-05-juan "--profile languages"
run_tank tank-06-juanita "--profile languages"

# German
docker compose --profile languages up -d kiwix-german 2>/dev/null
sleep 3
run_tank tank-07-klaus "--profile languages"
run_tank tank-08-genevieve "--profile languages"

# Chinese
docker compose --profile languages up -d kiwix-chinese 2>/dev/null
sleep 3
run_tank tank-09-wei "--profile languages"
run_tank tank-10-mei "--profile languages"

# Japanese
docker compose --profile languages up -d kiwix-japanese 2>/dev/null
sleep 3
run_tank tank-11-haruki "--profile languages"
run_tank tank-12-sakura "--profile languages"

# Visual
docker compose --profile visual up -d kiwix-maxi 2>/dev/null
sleep 3
run_tank tank-13-victor "--profile visual"
run_tank tank-14-iris "--profile visual"

# Special
run_tank tank-15-observer "--profile special"
run_tank tank-16-seeker "--profile special"

# Seth
run_tank tank-17-seth "--profile agents"

echo ""
echo "=== ALL BASELINES COMPLETE ==="
echo ""
python3 -c "
import json, glob
for p in sorted(glob.glob('logs/tank-*/baseline.json')):
    t=p.split('/')[-2]
    d=json.load(open(p))
    n=sum(1 for r in d.get('responses',[]) if len(r.get('response','').strip())>10)
    print(f'{t}: {n}/14 substantial responses')
"

echo ""
echo "Starting all tanks for exploration..."
docker compose --profile languages --profile agents --profile visual --profile special up -d 2>/dev/null
echo "ALL TANKS LAUNCHED FOR EXPLORATION"
