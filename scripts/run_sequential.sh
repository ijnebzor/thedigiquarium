#!/bin/bash
cd /home/ijneb/digiquarium

wait_for_baseline() {
    local tank=$1
    local max=600
    local elapsed=0
    while [ $elapsed -lt $max ]; do
        sleep 15
        elapsed=$((elapsed + 15))
        if [ -f "logs/$tank/baseline.json" ]; then
            local count=$(python3 -c "import json; d=json.load(open('logs/$tank/baseline.json')); print(sum(1 for r in d.get('responses',[]) if len(r.get('response','').strip())>10))" 2>/dev/null)
            if [ "$count" -ge 12 ] 2>/dev/null; then
                echo "$tank: DONE ($count/14) in ${elapsed}s"
                return 0
            fi
        fi
        local qn=$(docker logs --tail 3 $tank 2>&1 | grep -oP '\[\d+/14\]' | tail -1)
        echo "$tank: ${qn:-starting} (${elapsed}s)"
    done
    echo "$tank: TIMEOUT after ${max}s"
    return 1
}

# Eve is already running - wait for it
echo "=== Waiting for Eve ==="
wait_for_baseline tank-02-eve
docker stop tank-02-eve 2>/dev/null

# Standard tanks needing kiwix-simple (already up)
for spec in "tank-03-cain:agents" "tank-04-abel:agents"; do
    tank=$(echo $spec | cut -d: -f1)
    name=$(echo $tank | sed 's/tank-[0-9]*-//')
    echo "=== Starting $tank ==="
    rm -f logs/$tank/baseline.json
    docker compose --profile agents up -d $name 2>/dev/null
    wait_for_baseline $tank
    docker stop $tank 2>/dev/null
done

# Spanish
docker compose --profile languages up -d kiwix-spanish 2>/dev/null
sleep 3
for tank in tank-05-juan tank-06-juanita; do
    name=$(echo $tank | sed 's/tank-[0-9]*-//')
    echo "=== Starting $tank ==="
    rm -f logs/$tank/baseline.json
    docker compose --profile languages up -d $name 2>/dev/null
    wait_for_baseline $tank
    docker stop $tank 2>/dev/null
done

# German
docker compose --profile languages up -d kiwix-german 2>/dev/null
sleep 3
for tank in tank-07-klaus tank-08-genevieve; do
    name=$(echo $tank | sed 's/tank-[0-9]*-//')
    echo "=== Starting $tank ==="
    rm -f logs/$tank/baseline.json
    docker compose --profile languages up -d $name 2>/dev/null
    wait_for_baseline $tank
    docker stop $tank 2>/dev/null
done

# Chinese
docker compose --profile languages up -d kiwix-chinese 2>/dev/null
sleep 3
for tank in tank-09-wei tank-10-mei; do
    name=$(echo $tank | sed 's/tank-[0-9]*-//')
    echo "=== Starting $tank ==="
    rm -f logs/$tank/baseline.json
    docker compose --profile languages up -d $name 2>/dev/null
    wait_for_baseline $tank
    docker stop $tank 2>/dev/null
done

# Japanese
docker compose --profile languages up -d kiwix-japanese 2>/dev/null
sleep 3
for tank in tank-11-haruki tank-12-sakura; do
    name=$(echo $tank | sed 's/tank-[0-9]*-//')
    echo "=== Starting $tank ==="
    rm -f logs/$tank/baseline.json
    docker compose --profile languages up -d $name 2>/dev/null
    wait_for_baseline $tank
    docker stop $tank 2>/dev/null
done

# Visual
docker compose --profile visual up -d kiwix-maxi 2>/dev/null
sleep 3
for tank in tank-13-victor tank-14-iris; do
    name=$(echo $tank | sed 's/tank-[0-9]*-//')
    echo "=== Starting $tank ==="
    rm -f logs/$tank/baseline.json
    docker compose --profile visual up -d $name 2>/dev/null
    wait_for_baseline $tank
    docker stop $tank 2>/dev/null
done

# Special + remaining agents
for tank in tank-15-observer tank-16-seeker; do
    name=$(echo $tank | sed 's/tank-[0-9]*-//')
    echo "=== Starting $tank ==="
    rm -f logs/$tank/baseline.json
    docker compose --profile special up -d $name 2>/dev/null
    wait_for_baseline $tank
    docker stop $tank 2>/dev/null
done

# Seth (agent)
echo "=== Starting tank-17-seth ==="
rm -f logs/tank-17-seth/baseline.json
docker compose --profile agents up -d seth 2>/dev/null
wait_for_baseline tank-17-seth
docker stop tank-17-seth 2>/dev/null

echo ""
echo "=== ALL BASELINES COMPLETE ==="
python3 -c "
import json, glob
for p in sorted(glob.glob('logs/tank-*/baseline.json')):
    t=p.split('/')[-2]
    d=json.load(open(p))
    n=sum(1 for r in d.get('responses',[]) if len(r.get('response','').strip())>10)
    print(f'{t}: {n}/14')
"

echo ""
echo "Starting all tanks for exploration..."
docker compose --profile languages --profile agents --profile visual --profile special up -d 2>/dev/null
echo "DONE"
