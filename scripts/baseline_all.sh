#!/bin/bash
# Simple sequential baseline - uses full service names directly
cd /home/ijneb/digiquarium

wait_baseline() {
    local tank=$1
    for i in $(seq 1 40); do
        sleep 15
        if [ -f "logs/$tank/baseline.json" ]; then
            local c=$(python3 -c "import json;d=json.load(open('logs/$tank/baseline.json'));print(sum(1 for r in d.get('responses',[]) if len(r.get('response','').strip())>10))" 2>/dev/null)
            if [ "$c" -ge 12 ] 2>/dev/null; then
                echo "$tank: DONE ($c/14)"
                return 0
            fi
        fi
        local q=$(docker logs --tail 3 $tank 2>&1 | grep -oP '\[\d+/14\]' | tail -1)
        echo "$tank: ${q:-...} ($(($i*15))s)"
    done
    echo "$tank: TIMEOUT"
}

do_tank() {
    local tank=$1
    local extra_services="$2"
    echo ""
    echo "======= $tank ======="
    # Start any extra kiwix services needed
    if [ -n "$extra_services" ]; then
        for svc in $extra_services; do
            docker compose --profile languages --profile visual --profile agents --profile special up -d $svc 2>/dev/null
        done
        sleep 3
    fi
    rm -f logs/$tank/baseline.json
    docker compose --profile languages --profile agents --profile visual --profile special up -d $tank 2>/dev/null
    sleep 3
    wait_baseline $tank
    docker stop $tank 2>/dev/null
}

echo "=== SEQUENTIAL BASELINES ==="
echo "Started: $(date)"

# Wait for Abel (already running)
echo ""
echo "======= tank-04-abel (already running) ======="
wait_baseline tank-04-abel
docker stop tank-04-abel 2>/dev/null

# Spanish
do_tank tank-05-juan "kiwix-spanish"
do_tank tank-06-juanita ""

# German
do_tank tank-07-klaus "kiwix-german"
do_tank tank-08-genevieve ""

# Chinese
do_tank tank-09-wei "kiwix-chinese"
do_tank tank-10-mei ""

# Japanese
do_tank tank-11-haruki "kiwix-japanese"
do_tank tank-12-sakura ""

# Visual
do_tank tank-13-victor "kiwix-maxi"
do_tank tank-14-iris ""

# Special
do_tank tank-15-observer ""
do_tank tank-16-seeker ""

# Seth
do_tank tank-17-seth ""

echo ""
echo "=== RESULTS ==="
python3 -c "
import json, glob
for p in sorted(glob.glob('logs/tank-*/baseline.json')):
    t=p.split('/')[-2]
    d=json.load(open(p))
    n=sum(1 for r in d.get('responses',[]) if len(r.get('response','').strip())>10)
    print(f'{t}: {n}/14')
"

echo ""
echo "Launching all tanks..."
docker compose --profile languages --profile agents --profile visual --profile special up -d 2>/dev/null
echo "DONE: $(date)"
