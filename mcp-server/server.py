#!/usr/bin/env python3
"""
Digiquarium MCP Server - Claude's Autonomous Caretaker Interface
"""
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

# Configuration
DIGIQUARIUM_DIR = Path(os.environ.get("DIGIQUARIUM_DIR", os.path.expanduser("~/digiquarium")))
DOCKER_COMPOSE_FILE = DIGIQUARIUM_DIR / "docker-compose.yml"
LOGS_DIR = DIGIQUARIUM_DIR / "logs"

mcp = FastMCP("digiquarium_mcp")

class ContainerAction(str, Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"

class LogSource(str, Enum):
    STDOUT = "stdout"
    STDERR = "stderr"
    BOTH = "both"

def run_command(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 60) -> Dict[str, Any]:
    try:
        result = subprocess.run(cmd, cwd=cwd or DIGIQUARIUM_DIR, capture_output=True, text=True, timeout=timeout)
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": f"Timeout after {timeout}s", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}

def docker_cmd(args: List[str], timeout: int = 60) -> Dict[str, Any]:
    return run_command(["docker"] + args, timeout=timeout)

def docker_compose_cmd(args: List[str], profile: Optional[str] = None, timeout: int = 120) -> Dict[str, Any]:
    cmd = ["docker", "compose"]
    if DOCKER_COMPOSE_FILE.exists():
        cmd.extend(["-f", str(DOCKER_COMPOSE_FILE)])
    if profile:
        cmd.extend(["--profile", profile])
    cmd.extend(args)
    return run_command(cmd, timeout=timeout)

# ============ STATUS TOOLS ============

@mcp.tool(name="digiquarium_status", annotations={"readOnlyHint": True})
async def digiquarium_status() -> str:
    """Get comprehensive Digiquarium system status including all containers, services, and health."""
    results = [f"## 🌊 Digiquarium Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]
    
    # Container status
    ps = docker_cmd(["ps", "-a", "--format", "table {{.Names}}\t{{.Status}}\t{{.Image}}"])
    results.append("### 🐳 Containers\n```")
    results.append(ps["stdout"] if ps["success"] else f"Error: {ps['stderr']}")
    results.append("```\n")
    
    # Key services check
    results.append("### 🔧 Services")
    for svc in ["digiquarium-ollama", "digiquarium-kiwix-simple", "tank-01-adam"]:
        check = docker_cmd(["inspect", "--format", "{{.State.Status}}", svc])
        status = check["stdout"].strip() if check["success"] else "not found"
        emoji = "✅" if status == "running" else "⚠️" if status == "exited" else "❌"
        results.append(f"- {emoji} **{svc}**: {status}")
    
    # Disk usage
    df = run_command(["df", "-h", str(DIGIQUARIUM_DIR)])
    if df["success"]:
        results.append("\n### 💾 Disk\n```")
        results.append(df["stdout"])
        results.append("```")
    
    # Memory
    mem = run_command(["free", "-h"])
    if mem["success"]:
        results.append("\n### 🧠 Memory\n```")
        results.append(mem["stdout"])
        results.append("```")
    
    return "\n".join(results)

@mcp.tool(name="container_list", annotations={"readOnlyHint": True})
async def container_list() -> str:
    """List all Docker containers with status."""
    result = docker_cmd(["ps", "-a", "--format", "table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"])
    return result["stdout"] if result["success"] else f"Error: {result['stderr']}"

@mcp.tool(name="container_inspect", annotations={"readOnlyHint": True})
async def container_inspect(container_name: str) -> str:
    """Get detailed info about a container."""
    result = docker_cmd(["inspect", container_name])
    if result["success"]:
        try:
            data = json.loads(result["stdout"])[0]
            return json.dumps({
                "Name": data.get("Name"),
                "State": data.get("State"),
                "Image": data.get("Config", {}).get("Image"),
                "Networks": list(data.get("NetworkSettings", {}).get("Networks", {}).keys()),
                "Mounts": [m.get("Source") for m in data.get("Mounts", [])]
            }, indent=2)
        except:
            return result["stdout"]
    return f"Error: {result['stderr']}"

@mcp.tool(name="system_health", annotations={"readOnlyHint": True})
async def system_health() -> str:
    """Comprehensive system health check."""
    results = ["## 🏥 System Health\n"]
    
    # Uptime
    uptime = run_command(["uptime", "-p"])
    results.append(f"**Uptime:** {uptime['stdout'].strip()}\n")
    
    # Memory
    mem = run_command(["free", "-h"])
    results.append("### Memory\n```\n" + mem["stdout"] + "```\n")
    
    # Disk
    disk = run_command(["df", "-h", "/"])
    results.append("### Disk\n```\n" + disk["stdout"] + "```\n")
    
    # Docker
    docker_info = run_command(["docker", "info", "--format", "{{.ServerVersion}}"])
    containers = docker_cmd(["ps", "-q"])
    count = len(containers["stdout"].strip().split("\n")) if containers["stdout"].strip() else 0
    results.append(f"### Docker\n- Version: {docker_info['stdout'].strip()}\n- Running containers: {count}")
    
    return "\n".join(results)

# ============ CONTAINER MANAGEMENT ============

@mcp.tool(name="container_action", annotations={"destructiveHint": True})
async def container_action(container_name: str, action: str) -> str:
    """Perform action on container: start, stop, restart."""
    if action not in ["start", "stop", "restart"]:
        return f"❌ Invalid action. Use: start, stop, restart"
    result = docker_cmd([action, container_name])
    return f"✅ {action}ed {container_name}" if result["success"] else f"❌ Failed: {result['stderr']}"

@mcp.tool(name="docker_compose", annotations={"destructiveHint": True})
async def docker_compose_tool(command: str, service: Optional[str] = None, profile: Optional[str] = None) -> str:
    """Run docker compose command (e.g., 'up -d', 'down', 'ps', 'logs')."""
    args = command.split()
    if service:
        args.append(service)
    result = docker_compose_cmd(args, profile=profile)
    output = result["stdout"]
    if result["stderr"]:
        output += f"\nSTDERR: {result['stderr']}"
    return f"{'✅' if result['success'] else '❌'} docker compose {command}\n\n{output}"

@mcp.tool(name="exec_in_container", annotations={"destructiveHint": True})
async def exec_in_container(container_name: str, command: str) -> str:
    """Execute a command inside a running container."""
    result = docker_cmd(["exec", container_name, "sh", "-c", command], timeout=120)
    output = result["stdout"]
    if result["stderr"]:
        output += f"\nSTDERR: {result['stderr']}"
    return f"{'✅' if result['success'] else '❌'} exec in {container_name}:\n{output}"

# ============ LOGS ============

@mcp.tool(name="tank_logs", annotations={"readOnlyHint": True})
async def tank_logs(container_name: str, lines: int = 100, since: Optional[str] = None) -> str:
    """Get container logs. Use since like '1h', '30m', or '2024-01-15'."""
    args = ["logs", "--tail", str(min(lines, 500))]
    if since:
        args.extend(["--since", since])
    args.append(container_name)
    result = docker_cmd(args, timeout=30)
    output = ""
    if result["stdout"]:
        output += f"=== STDOUT ===\n{result['stdout']}\n"
    if result["stderr"]:
        output += f"=== STDERR ===\n{result['stderr']}"
    return output or "No logs found."

@mcp.tool(name="read_file", annotations={"readOnlyHint": True})
async def read_file(path: str) -> str:
    """Read a file from digiquarium directory."""
    file_path = DIGIQUARIUM_DIR / path
    try:
        file_path.resolve().relative_to(DIGIQUARIUM_DIR.resolve())
    except ValueError:
        return f"❌ Path must be within {DIGIQUARIUM_DIR}"
    if not file_path.exists():
        return f"❌ Not found: {file_path}"
    try:
        content = file_path.read_text()
        if len(content) > 50000:
            return content[:50000] + f"\n\n... [truncated, {len(content)} bytes total]"
        return content
    except Exception as e:
        return f"❌ Error: {e}"

@mcp.tool(name="list_directory", annotations={"readOnlyHint": True})
async def list_directory(path: str = ".") -> str:
    """List files in a directory within digiquarium."""
    dir_path = DIGIQUARIUM_DIR / path
    try:
        dir_path.resolve().relative_to(DIGIQUARIUM_DIR.resolve())
    except ValueError:
        return f"❌ Path must be within {DIGIQUARIUM_DIR}"
    if not dir_path.exists():
        return f"❌ Not found: {dir_path}"
    result = run_command(["ls", "-la", str(dir_path)])
    return f"📁 {dir_path}:\n{result['stdout']}" if result["success"] else f"❌ {result['stderr']}"

@mcp.tool(name="write_file", annotations={"destructiveHint": True})
async def write_file(path: str, content: str) -> str:
    """Write content to a file in digiquarium directory."""
    file_path = DIGIQUARIUM_DIR / path
    try:
        file_path.resolve().relative_to(DIGIQUARIUM_DIR.resolve())
    except ValueError:
        return f"❌ Path must be within {DIGIQUARIUM_DIR}"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        file_path.write_text(content)
        return f"✅ Wrote {len(content)} bytes to {file_path}"
    except Exception as e:
        return f"❌ Error: {e}"

# ============ NETWORK ISOLATION ============

@mcp.tool(name="verify_isolation", annotations={"readOnlyHint": True})
async def verify_isolation(container_name: str) -> str:
    """Verify tank is network-isolated (no internet, can reach Ollama/Kiwix)."""
    results = [f"## 🔒 Network Isolation: {container_name}\n"]
    
    # External internet test
    ext = docker_cmd(["exec", container_name, "sh", "-c", 
        "wget -q --spider --timeout=3 http://google.com && echo 'CONNECTED' || echo 'ISOLATED'"], timeout=10)
    if "ISOLATED" in ext.get("stdout", ""):
        results.append("✅ **External Internet:** BLOCKED")
    elif "CONNECTED" in ext.get("stdout", ""):
        results.append("❌ **External Internet:** ACCESSIBLE (SECURITY ISSUE!)")
    else:
        results.append(f"⚠️ **External Internet:** Test failed - {ext.get('stderr', '')[:100]}")
    
    # Ollama test
    ollama = docker_cmd(["exec", container_name, "sh", "-c",
        "wget -q --spider --timeout=3 http://digiquarium-ollama:11434/api/tags && echo 'OK' || echo 'FAIL'"], timeout=10)
    results.append("✅ **Ollama:** Accessible" if "OK" in ollama.get("stdout", "") else "❌ **Ollama:** Not accessible")
    
    # Kiwix test
    kiwix = docker_cmd(["exec", container_name, "sh", "-c",
        "wget -q --spider --timeout=3 http://digiquarium-kiwix-simple:8080 && echo 'OK' || echo 'FAIL'"], timeout=10)
    results.append("✅ **Kiwix:** Accessible" if "OK" in kiwix.get("stdout", "") else "⚠️ **Kiwix:** Not accessible")
    
    # Networks
    networks = docker_cmd(["inspect", "--format", "{{json .NetworkSettings.Networks}}", container_name])
    if networks["success"]:
        try:
            nets = json.loads(networks["stdout"])
            results.append(f"\n**Networks:** {', '.join(nets.keys())}")
        except:
            pass
    
    return "\n".join(results)

# ============ EXPERIMENT TOOLS ============

@mcp.tool(name="run_shell", annotations={"destructiveHint": True})
async def run_shell(command: str, timeout: int = 60) -> str:
    """Run a shell command on the host (use carefully)."""
    result = run_command(["bash", "-c", command], timeout=min(timeout, 300))
    output = result["stdout"]
    if result["stderr"]:
        output += f"\nSTDERR: {result['stderr']}"
    return f"{'✅' if result['success'] else '❌'} {command[:50]}...\n\n{output}"

@mcp.tool(name="get_config", annotations={"readOnlyHint": True})
async def get_config() -> str:
    """Get Digiquarium configuration overview."""
    results = [f"## ⚙️ Configuration\n"]
    results.append(f"**Base:** {DIGIQUARIUM_DIR}")
    results.append(f"**Logs:** {LOGS_DIR}")
    results.append(f"**Compose:** {DOCKER_COMPOSE_FILE}")
    
    if DOCKER_COMPOSE_FILE.exists():
        results.append("\n### docker-compose.yml\n```yaml")
        content = DOCKER_COMPOSE_FILE.read_text()
        results.append(content[:3000] + ("..." if len(content) > 3000 else ""))
        results.append("```")
    else:
        results.append("\n⚠️ docker-compose.yml not found")
    
    return "\n".join(results)

@mcp.tool(name="cleanup", annotations={"destructiveHint": True})
async def cleanup() -> str:
    """Clean up unused Docker resources."""
    results = ["## 🧹 Cleanup\n"]
    for resource in ["container", "image", "network"]:
        r = docker_cmd([resource, "prune", "-f"])
        results.append(f"**{resource}s:** {r['stdout'].strip()[:100]}")
    return "\n".join(results)

if __name__ == "__main__":
    mcp.run()
