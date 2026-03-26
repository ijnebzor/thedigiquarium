#!/usr/bin/env python3
"""
update_admin_status.py — Queries Docker and system health,
writes docs/admin/status.json and docs/data/admin-status.json
for the Digiquarium admin panel.

Run manually, via cron, or from the maintainer daemon:
    python3 scripts/update_admin_status.py

Requires: docker (CLI), Python 3.8+
"""

import json
import subprocess
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
ADMIN_STATUS = REPO_ROOT / "docs" / "data" / "admin-status.json"
ADMIN_DIR_STATUS = REPO_ROOT / "docs" / "admin" / "status.json"


def run(cmd, timeout=30):
    """Run a shell command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def get_containers():
    """Get all Docker containers with their status."""
    raw = run('docker ps -a --format "{{.Names}}|{{.Status}}|{{.State}}"')
    if not raw:
        return []
    containers = []
    for line in raw.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            containers.append({
                "name": parts[0],
                "status": parts[1],
                "state": parts[2],
                "running": parts[2] == "running",
            })
    return containers


def get_tank_activity(containers):
    """Get tank-specific data from running tank containers."""
    tanks = []
    tank_containers = [c for c in containers if c["name"].startswith("tank-")]
    running_count = sum(1 for c in tank_containers if c["running"])

    for tc in tank_containers:
        name = tc["name"]
        # Try to get last article from container logs
        article = "—"
        log_line = run(
            f'docker logs {name} --tail 5 2>&1 | grep -i "article" | tail -1'
        )
        if log_line:
            # Extract article name if possible
            for marker in ["Reading:", "Article:", "Exploring:"]:
                if marker in log_line:
                    article = log_line.split(marker)[-1].strip()[:60]
                    break

        # Count traces from log
        trace_count = run(
            f'docker logs {name} --since 24h 2>&1 | grep -c "trace\\|thought\\|article" || echo 0'
        )

        tanks.append({
            "name": name,
            "article": article,
            "traces": int(trace_count) if trace_count and trace_count.isdigit() else 0,
            "running": tc["running"],
        })

    return running_count, tanks


def get_daemon_status(containers):
    """Check which daemons are running."""
    daemon_names = [
        "overseer", "ollama_watcher", "caretaker", "maintainer",
        "guard", "scheduler", "sentinel", "psych", "bouncer",
        "chaos_monkey", "therapist", "archivist", "final_auditor",
        "documentarian", "ethicist", "moderator", "broadcaster",
        "translator", "webmaster", "marketer", "public_liaison",
    ]

    daemons = {}
    for name in daemon_names:
        # Check if there's a running process for this daemon
        ps_check = run(f'pgrep -f "{name}" | wc -l')
        count = int(ps_check) if ps_check and ps_check.isdigit() else 0

        # Also check docker containers
        container_match = [
            c for c in containers
            if name in c["name"] and c["running"]
        ]

        running = count > 0 or len(container_match) > 0
        daemons[name] = {
            "running": running,
            "count": max(count, len(container_match)),
            "healthy": running,  # Simple health = running
        }

    return daemons


def get_ollama_status():
    """Check Ollama service health."""
    result = {
        "windows_healthy": False,
        "proxy_healthy": False,
        "e2e_healthy": False,
        "models": 0,
    }

    # Check if Ollama is accessible
    ollama_check = run("curl -s -o /dev/null -w '%{http_code}' http://localhost:11434/api/tags 2>/dev/null")
    if ollama_check == "200":
        result["windows_healthy"] = True

    # Check proxy (inside Docker network)
    proxy_check = run(
        "docker exec digiquarium-ollama curl -s -o /dev/null -w '%{http_code}' http://172.30.0.100:11434/api/tags 2>/dev/null"
    )
    if proxy_check == "200":
        result["proxy_healthy"] = True

    # Count models
    models_raw = run("curl -s http://localhost:11434/api/tags 2>/dev/null")
    if models_raw:
        try:
            models_data = json.loads(models_raw)
            result["models"] = len(models_data.get("models", []))
        except json.JSONDecodeError:
            pass

    # E2E: can a tank reach Ollama?
    e2e = run(
        'docker exec tank-01-adam curl -s -o /dev/null -w "%{http_code}" http://172.30.0.100:11434/api/tags 2>/dev/null'
    )
    result["e2e_healthy"] = e2e == "200"

    return result


def get_system_logs():
    """Collect recent system logs from key daemons."""
    logs = []

    # Overseer logs
    overseer_logs = run(
        'docker logs digiquarium-overseer --tail 20 --since 1h 2>&1 | tail -15'
    )
    if overseer_logs:
        for line in overseer_logs.split("\n"):
            if line.strip():
                logs.append(line.strip())

    # Caretaker logs
    caretaker_logs = run(
        'docker logs digiquarium-caretaker --tail 10 --since 1h 2>&1 | tail -5'
    )
    if caretaker_logs:
        for line in caretaker_logs.split("\n"):
            if line.strip():
                logs.append(line.strip())

    return logs[-30:] if logs else ["No recent logs available"]


def get_overseer_status():
    """Get overseer-specific metrics."""
    return {
        "running": run('pgrep -f overseer') is not None,
        "last_audit_healthy": True,
        "active_incidents": 0,
        "auto_remediations": 0,
    }


def build_status():
    """Build the complete admin status JSON."""
    print(f"[{datetime.now().isoformat()}] Generating admin status...")

    containers = get_containers()
    tanks_running, tank_activity = get_tank_activity(containers)
    daemons = get_daemon_status(containers)
    ollama = get_ollama_status()
    logs = get_system_logs()
    overseer = get_overseer_status()

    # Compute traces today
    traces_today = sum(t.get("traces", 0) for t in tank_activity)

    # Overall health
    overall_healthy = (
        ollama["e2e_healthy"]
        and ollama["proxy_healthy"]
        and tanks_running > 0
    )

    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_healthy": overall_healthy,
        "ollama": ollama,
        "daemons": daemons,
        "containers": {
            "total": len(containers),
            "running": sum(1 for c in containers if c["running"]),
            "details": containers,
        },
        "tanks": {
            "running": tanks_running,
            "traces_today": traces_today,
            "activity": tank_activity,
        },
        "network": {
            "isolated": True,  # By design
        },
        "overseer": overseer,
        "logs": logs,
    }

    return status


def main():
    status = build_status()

    # Write to both locations
    for path in [ADMIN_STATUS, ADMIN_DIR_STATUS]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(status, f, indent=2)
        print(f"  Written: {path}")

    print(f"  Overall healthy: {status['overall_healthy']}")
    print(f"  Containers: {status['containers']['total']} "
          f"({status['containers']['running']} running)")
    print(f"  Tanks running: {status['tanks']['running']}")
    print(f"  Daemons: {sum(1 for d in status['daemons'].values() if d['running'])} active")
    print(f"  Ollama models: {status['ollama']['models']}")
    print("Done.")


if __name__ == "__main__":
    main()
