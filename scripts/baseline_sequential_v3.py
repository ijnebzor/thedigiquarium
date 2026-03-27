#!/usr/bin/env python3
"""Sequential baseline v3 - stops container, runs baseline as new command, restarts."""
import subprocess, json, time, sys, os

DIGI = os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')
TANKS = [
    'tank-01-adam', 'tank-02-eve', 'tank-03-cain', 'tank-04-abel',
    'tank-05-juan', 'tank-06-juanita', 'tank-07-klaus', 'tank-08-genevieve',
    'tank-09-wei', 'tank-10-mei', 'tank-11-haruki', 'tank-12-sakura',
    'tank-13-victor', 'tank-14-iris', 'tank-15-observer', 'tank-16-seeker',
    'tank-17-seth'
]

def run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', 1

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)

def check_baseline(tank):
    path = f'{DIGI}/logs/{tank}/baseline.json'
    try:
        d = json.load(open(path))
        n = sum(1 for r in d.get('responses', []) if len(r.get('response', '').strip()) > 10)
        return n, d.get('questions_answered', 0)
    except:
        return 0, 0

def baseline_one(tank):
    log(f'--- {tank} ---')
    
    # Clear old baseline
    path = f'{DIGI}/logs/{tank}/baseline.json'
    try: os.remove(path)
    except: pass
    
    # 1. Stop the container completely
    log(f'{tank}: Stopping container...')
    run(f'docker stop {tank}', timeout=30)
    time.sleep(2)
    
    # 2. Start container with baseline command instead of default explorer
    log(f'{tank}: Running baseline (solo Ollama access)...')
    out, rc = run(
        f'docker start {tank} && docker exec {tank} python3 -u /tank/baseline.py',
        timeout=600
    )
    
    if rc != 0:
        log(f'{tank}: baseline failed (rc={rc})')
        # Check if it's because the container's entrypoint is conflicting
        # Try alternative: use docker run with override
        log(f'{tank}: Trying docker run override...')
        # Get the container's image and env
        img_out, _ = run(f'docker inspect -f "{{{{.Config.Image}}}}" {tank}')
        env_out, _ = run(f'docker inspect -f "{{{{range .Config.Env}}}}{{{{.}}}} {{{{end}}}}" {tank}')
        
        # Build env flags
        env_flags = ' '.join(f'-e "{e}"' for e in env_out.split() if '=' in e)
        
        run(f'docker stop {tank}', timeout=30)
        out, rc = run(
            f'docker run --rm --network digiquarium_isolated-net '
            f'-v {DIGI}/src/explorer:/tank:ro '
            f'-v {DIGI}/config/tanks:/config:ro '
            f'-v {DIGI}/logs/{tank}:/logs '
            f'{env_flags} '
            f'{img_out} python3 -u /tank/baseline.py',
            timeout=600
        )
    
    # 3. Check quality
    n, total = check_baseline(tank)
    log(f'{tank}: {n}/{total} substantial responses')
    
    # 4. Restart container normally (will run explorer)
    log(f'{tank}: Restarting for exploration...')
    run(f'docker start {tank}', timeout=30)
    time.sleep(3)
    
    return n

log('=== SEQUENTIAL BASELINE v3 ===')
log(f'Tanks: {len(TANKS)}')
log(f'Strategy: stop container -> baseline solo -> restart for exploration')
log('')

results = {}
for tank in TANKS:
    n = baseline_one(tank)
    results[tank] = n
    
    if n < 12 and n >= 0:
        log(f'{tank}: RETRY ({n}/14)...')
        time.sleep(5)
        n = baseline_one(tank)
        results[tank] = n
    
    time.sleep(3)

log('')
log('=== FINAL RESULTS ===')
good = 0
for tank, n in sorted(results.items()):
    status = 'GOOD' if n >= 12 else 'POOR' if n > 0 else 'EMPTY'
    log(f'  {tank}: {n}/14 [{status}]')
    if n >= 12: good += 1

log(f'\nTotal: {good}/{len(TANKS)} good baselines')
log('=== DONE ===')
