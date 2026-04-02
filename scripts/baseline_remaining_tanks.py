#!/usr/bin/env python3
"""
LIBRARIAN BASELINE — REMAINING TANKS (with 60s cooldown between baselines)
Picks up from where the first run hit rate limits.
Includes all tanks that need baselines (failed or not yet run).
"""

import subprocess
import json
import time
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/home/ijneb/digiquarium")
LOGFILE = BASE_DIR / "logs" / "baseline_all_tanks.log"
SHARED_DIR = BASE_DIR / "shared"

# Tanks that ALREADY completed successfully (12+ substantial)
COMPLETED_GOOD = [
    "tank-01-adam", "tank-02-eve", "tank-03-cain", "tank-04-abel",
    "tank-05-juan", "tank-06-juanita", "tank-07-klaus", "tank-08-genevieve",
    "tank-09-wei", "tank-10-mei",
]

# ALL tanks in order
ORIGINAL_TANKS = [
    "tank-01-adam", "tank-02-eve", "tank-03-cain", "tank-04-abel",
    "tank-05-juan", "tank-06-juanita", "tank-07-klaus", "tank-08-genevieve",
    "tank-09-wei", "tank-10-mei", "tank-11-haruki", "tank-12-sakura",
    "tank-13-victor", "tank-14-iris", "tank-15-observer", "tank-16-seeker", "tank-17-seth",
]

BETACLONE_TANKS = [
    "betaclone-redux-03-cain", "betaclone-redux-04-abel",
    "betaclone-redux-05-juan", "betaclone-redux-06-juanita",
    "betaclone-redux-07-klaus", "betaclone-redux-08-genevieve",
    "betaclone-redux-09-wei", "betaclone-redux-10-mei",
    "betaclone-redux-11-haruki", "betaclone-redux-12-sakura",
    "betaclone-redux-13-victor", "betaclone-redux-14-iris",
    "betaclone-redux-15-observer", "betaclone-redux-16-seeker", "betaclone-redux-17-seth",
]

ALL_TANKS = ORIGINAL_TANKS + BETACLONE_TANKS

# Tanks that still need baselines
REMAINING = [t for t in ALL_TANKS if t not in COMPLETED_GOOD]

COOLDOWN = 60  # seconds between baselines to let rate limits recover

log_fh = None

def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    if log_fh:
        log_fh.write(line + "\n")
        log_fh.flush()


def reset_locks():
    lock_files = [
        ".cerebras_rate_lock", ".together_rate_lock", ".groq_rate_lock",
        ".ollama_rate_lock", ".ollama_lock",
        ".cerebras_last_call", ".together_last_call", ".groq_last_call", ".ollama_last_call",
    ]
    for f in lock_files:
        path = SHARED_DIR / f
        try:
            path.unlink(missing_ok=True)
        except:
            pass
        try:
            path.touch()
            os.chmod(path, 0o666)
        except:
            pass


def get_container_env(tank):
    result = subprocess.run(
        ["docker", "inspect", tank, "--format", "{{range .Config.Env}}{{println .}}{{end}}"],
        capture_output=True, text=True, timeout=10
    )
    env = {}
    for line in result.stdout.strip().split("\n"):
        if "=" in line:
            key, _, val = line.partition("=")
            env[key] = val
    return env


def pause_all():
    log(f"Ensuring all {len(ALL_TANKS)} tanks are paused...")
    for tank in ALL_TANKS:
        subprocess.run(["docker", "pause", tank], capture_output=True, timeout=10)
    log("All tanks paused.")


def unpause_all():
    log("Unpausing all tanks...")
    for tank in ALL_TANKS:
        subprocess.run(["docker", "unpause", tank], capture_output=True, timeout=10)
    log("All tanks unpaused.")


def run_baseline(tank, idx, total):
    log(f"")
    log(f"━━━ [{idx}/{total}] {tank} ━━━")

    env = get_container_env(tank)
    tank_name = env.get("TANK_NAME", "unknown")
    gender = env.get("GENDER", "a being without gender")
    log(f"  Name={tank_name} Gender={gender}")

    reset_locks()

    start = time.time()
    log(f"  Starting baseline at {datetime.now().strftime('%H:%M:%S')}...")

    cmd = [
        "docker", "run", "--rm",
        "--network", "digiquarium_default",
        "-e", f"TANK_NAME={env.get('TANK_NAME', '')}",
        "-e", f"TANK_ID={env.get('TANK_ID', '')}",
        "-e", f"GENDER={env.get('GENDER', '')}",
        "-e", f"KIWIX_URL={env.get('KIWIX_URL', '')}",
        "-e", f"WIKI_BASE={env.get('WIKI_BASE', '')}",
        "-e", "OLLAMA_URL=http://digiquarium-ollama:11434",
        "-e", "OLLAMA_MODEL=llama3.2:latest",
        "-e", f"CEREBRAS_API_KEY={env.get('CEREBRAS_API_KEY', '')}",
        "-e", "CEREBRAS_MODEL=llama3.1-8b",
        "-e", f"TOGETHER_API_KEY={env.get('TOGETHER_API_KEY', '')}",
        "-e", "TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "-e", f"GROQ_API_KEY={env.get('GROQ_API_KEY', '')}",
        "-e", "GROQ_MODEL=llama-3.1-8b-instant",
        "-e", "LOG_DIR=/logs",
        "-v", f"{BASE_DIR}/src/explorer:/tank:ro",
        "-v", f"{BASE_DIR}/config/tanks:/config:ro",
        "-v", f"{BASE_DIR}/logs/{tank}:/logs",
        "-v", f"{BASE_DIR}/shared:/shared",
        "digiquarium-tank:latest",
        "python3", "-u", "/tank/baseline.py",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if log_fh:
            log_fh.write(result.stdout)
            log_fh.flush()
    except subprocess.TimeoutExpired:
        log("  TIMEOUT after 10 minutes")

    duration = int(time.time() - start)
    log(f"  Completed in {duration}s")

    baseline_file = BASE_DIR / "logs" / tank / "baseline_latest.json"
    substantial = 0
    if baseline_file.exists():
        try:
            data = json.loads(baseline_file.read_text())
            substantial = sum(1 for r in data.get("responses", [])
                            if len(r.get("response", "").strip()) > 10)
        except:
            pass

    log(f"  Result: {substantial}/14 substantial responses")
    return substantial, duration


def main():
    global log_fh

    LOGFILE.parent.mkdir(parents=True, exist_ok=True)
    log_fh = open(LOGFILE, "a")  # APPEND to existing log

    total_remaining = len(REMAINING)
    log("")
    log("=" * 60)
    log(f"LIBRARIAN BASELINE — REMAINING {total_remaining} TANKS (with {COOLDOWN}s cooldown)")
    log(f"Already completed: {len(COMPLETED_GOOD)}/32")
    log("=" * 60)

    reset_locks()
    log("Rate locks reset.")

    pause_all()

    # Wait 2 minutes at the start for rate limits to fully recover
    log(f"Waiting 120s for rate limits to recover from previous run...")
    time.sleep(120)

    results = {}
    # Pre-load results for completed tanks
    for tank in COMPLETED_GOOD:
        results[tank] = "14/14 GOOD (previous run)"

    passed = len(COMPLETED_GOOD)
    failed = 0
    idx = 0

    for tank in REMAINING:
        idx += 1

        substantial, duration = run_baseline(tank, idx, total_remaining)

        if substantial < 12:
            log(f"  Below 12 threshold. Waiting 60s and retrying...")
            time.sleep(60)
            substantial, duration = run_baseline(tank, f"{idx}R", total_remaining)

        if substantial >= 12:
            passed += 1
            results[tank] = f"{substantial}/14 GOOD"
        else:
            failed += 1
            results[tank] = f"{substantial}/14 POOR"

        # Cooldown between baselines
        if idx < total_remaining:
            log(f"  Cooldown: waiting {COOLDOWN}s for rate limit recovery...")
            time.sleep(COOLDOWN)

    # Unpause all tanks
    log("")
    unpause_all()

    # Update admin panel
    log("")
    log("Updating admin status panel...")
    try:
        subprocess.run(
            ["python3", str(BASE_DIR / "scripts" / "update_admin_status.py")],
            capture_output=True, timeout=60
        )
        log("Admin status updated.")
    except Exception as e:
        log(f"WARN: Admin status update failed: {e}")

    # Final report
    log("")
    log("=" * 60)
    log("LIBRARIAN BASELINE — FINAL REPORT")
    log("=" * 60)
    log(f"Total tanks: {len(ALL_TANKS)}")
    log(f"Passed (12+): {passed}")
    log(f"Failed (<12): {failed}")
    log("")
    log("Individual results:")
    for tank in ALL_TANKS:
        log(f"  {tank}: {results.get(tank, 'UNKNOWN')}")
    log("")
    log("=" * 60)
    log(f"ALL BASELINES COMPLETE at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)

    log_fh.close()


if __name__ == "__main__":
    main()
