#!/usr/bin/env python3
"""Sequential baseline runner - stops all exploration, baselines one tank at a time."""
import subprocess, json, time, sys, os

DIGI = os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')
TANKS = [
    'tank-01-adam', 'tank-02-eve', 'tank-03-cain', 'tank-04-abel',
    'tank-05-juan', 'tank-06-juanita', 'tank-07-klaus', 'tank-08-genevieve',
    'tank-09-wei', 'tank-10-mei', 'tank-11-haruki', 'tank-12-sakura',
    'tank-13-victor', 'tank-14-iris', 'tank-15-observer', 'tank-16-seeker',
    'tank-17-seth'
]

def run(cmd, timeout=60):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.returncode

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {msg}')

def check_baseline(tank):
    path = f'{DIGI}/logs/{tank}/baseline.json'
    try:
        d = json.load(open(path))
        n = sum(1 for r in d.get('responses', []) if len(r.get('response', '').strip()) > 10)
        return n
    except:
        return 0

def baseline_one_tank(tank):
    log(f'=== BASELINE: {tank} ===')
    
    # Clear old baseline
    path = f'{DIGI}/logs/{tank}/baseline.json'
    if os.path.exists(path):
        os.remove(path)
    
    # Kill the explorer process inside the container (baseline.py will run alongside)
    run(f'docker exec {tank} pkill -f explorer.py 2>/dev/null')
    run(f'docker exec {tank} pkill -f "agents/" 2>/dev/null')
    time.sleep(2)
    
    # Run baseline inside the container
    log(f'{tank}: Running baseline...')
    proc = subprocess.Popen(
        f'docker exec {tank} python3 -u /tank/baseline.py',
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    
    # Wait for completion (max 10 minutes)
    try:
        proc.wait(timeout=600)
    except subprocess.TimeoutExpired:
        proc.kill()
        log(f'{tank}: TIMEOUT')
        return 0
    
    # Check quality
    n = check_baseline(tank)
    log(f'{tank}: {n}/14 substantial responses')
    
    # Restart the explorer (the container's start.sh will handle it)
    run(f'docker restart {tank}')
    time.sleep(5)
    
    return n

def main():
    log('=== SEQUENTIAL BASELINE RUNNER ===')
    log(f'Tanks: {len(TANKS)}')
    
    results = {}
    for tank in TANKS:
        # Check container is running
        out, rc = run(f'docker inspect -f "{{{{.State.Running}}}}" {tank}')
        if 'true' not in out.lower():
            log(f'{tank}: NOT RUNNING - skipping')
            results[tank] = -1
            continue
        
        n = baseline_one_tank(tank)
        results[tank] = n
        
        # If failed, retry once
        if n < 12:
            log(f'{tank}: Retrying (got {n}/14)...')
            n = baseline_one_tank(tank)
            results[tank] = n
        
        time.sleep(5)  # Brief pause between tanks
    
    log('')
    log('=== RESULTS ===')
    good = 0
    for tank, n in sorted(results.items()):
        status = 'GOOD' if n >= 12 else 'POOR' if n > 0 else 'SKIP' if n == -1 else 'EMPTY'
        log(f'  {tank}: {n}/14 [{status}]')
        if n >= 12:
            good += 1
    
    log(f'')
    log(f'Total: {good}/{len(TANKS)} tanks with good baselines')
    log('=== DONE ===')

if __name__ == '__main__':
    main()
