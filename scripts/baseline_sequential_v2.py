#!/usr/bin/env python3
"""Sequential baseline v2 - uses subprocess.run (blocking) instead of Popen."""
import subprocess, json, time, sys, os

DIGI = os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')
TANKS = [
    'tank-01-adam', 'tank-02-eve', 'tank-03-cain', 'tank-04-abel',
    'tank-05-juan', 'tank-06-juanita', 'tank-07-klaus', 'tank-08-genevieve',
    'tank-09-wei', 'tank-10-mei', 'tank-11-haruki', 'tank-12-sakura',
    'tank-13-victor', 'tank-14-iris', 'tank-15-observer', 'tank-16-seeker',
    'tank-17-seth'
]

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)

def check_baseline(tank):
    path = f'{DIGI}/logs/{tank}/baseline.json'
    try:
        d = json.load(open(path))
        n = sum(1 for r in d.get('responses', []) if len(r.get('response', '').strip()) > 10)
        return n
    except:
        return 0

def baseline_one(tank):
    log(f'=== {tank} ===')
    
    # Remove old baseline
    path = f'{DIGI}/logs/{tank}/baseline.json'
    try: os.remove(path)
    except: pass
    
    # Kill explorer inside container
    subprocess.run(f'docker exec {tank} pkill -f explorer.py', shell=True, timeout=10,
                   capture_output=True)
    subprocess.run(f'docker exec {tank} pkill -f "agents/"', shell=True, timeout=10,
                   capture_output=True)
    time.sleep(3)
    
    # Run baseline (BLOCKING - waits for completion)
    log(f'{tank}: Running baseline (this takes ~3-5 minutes)...')
    result = subprocess.run(
        f'docker exec {tank} python3 -u /tank/baseline.py',
        shell=True, timeout=600, capture_output=True, text=True
    )
    
    if result.returncode != 0:
        log(f'{tank}: baseline.py exited with code {result.returncode}')
        if result.stderr:
            log(f'{tank}: stderr: {result.stderr[:200]}')
    
    # Check quality
    n = check_baseline(tank)
    log(f'{tank}: {n}/14 substantial responses')
    
    # Restart tank to resume exploration
    subprocess.run(f'docker restart {tank}', shell=True, timeout=120, capture_output=True)
    time.sleep(5)
    
    return n

log('=== SEQUENTIAL BASELINE v2 ===')
log(f'Tanks: {len(TANKS)}')

results = {}
for tank in TANKS:
    # Verify container is running
    r = subprocess.run(f'docker inspect -f "{{{{.State.Running}}}}" {tank}',
                       shell=True, capture_output=True, text=True, timeout=10)
    if 'true' not in r.stdout.lower():
        log(f'{tank}: NOT RUNNING - skip')
        results[tank] = -1
        continue
    
    n = baseline_one(tank)
    results[tank] = n
    
    if n < 12:
        log(f'{tank}: RETRY ({n}/14)...')
        # Restart and retry
        subprocess.run(f'docker restart {tank}', shell=True, timeout=120, capture_output=True)
        time.sleep(10)
        n = baseline_one(tank)
        results[tank] = n
    
    time.sleep(3)

log('')
log('=== FINAL RESULTS ===')
good = 0
for tank, n in sorted(results.items()):
    status = 'GOOD' if n >= 12 else 'POOR' if n > 0 else 'SKIP' if n < 0 else 'EMPTY'
    log(f'  {tank}: {n}/14 [{status}]')
    if n >= 12: good += 1

log(f'\nTotal: {good}/{len(TANKS)} good baselines')
log('=== DONE ===')
