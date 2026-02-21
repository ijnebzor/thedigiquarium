#!/usr/bin/env python3
"""
THE STRATEGIST Chat Interface
==============================
Local web UI for chatting with Claude, scoped to daemons/tanks.
Connects via Anthropic API with full MCP context.

Run: python3 app.py
Access: http://localhost:5000
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response
import anthropic

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'

app = Flask(__name__)

# Anthropic client - uses ANTHROPIC_API_KEY env var
client = None

def get_client():
    global client
    if client is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            # Try to read from file
            key_file = DIGIQUARIUM_DIR / '.anthropic_key'
            if key_file.exists():
                api_key = key_file.read_text().strip()
        if api_key:
            client = anthropic.Anthropic(api_key=api_key)
    return client

def get_daemon_context(daemon_id: str) -> str:
    """Get context about a specific daemon"""
    context_parts = []
    
    # Get daemon's recent logs
    log_file = DAEMONS_DIR / 'logs' / f'{daemon_id}.log'
    if log_file.exists():
        try:
            lines = log_file.read_text().split('\n')[-50:]  # Last 50 lines
            context_parts.append(f"## {daemon_id.upper()} Recent Logs:\n```\n" + '\n'.join(lines) + "\n```")
        except:
            pass
    
    # Get daemon's status file
    status_file = DAEMONS_DIR / daemon_id / 'status.json'
    if status_file.exists():
        try:
            status = json.loads(status_file.read_text())
            context_parts.append(f"## {daemon_id.upper()} Status:\n```json\n{json.dumps(status, indent=2)}\n```")
        except:
            pass
    
    # Check if daemon is running
    try:
        result = subprocess.run(
            f"ps aux | grep '{daemon_id}.py' | grep -v grep | wc -l",
            shell=True, capture_output=True, text=True
        )
        count = int(result.stdout.strip())
        context_parts.append(f"## Process Status: {'Running' if count > 0 else 'NOT RUNNING'} ({count} process(es))")
    except:
        pass
    
    return '\n\n'.join(context_parts) if context_parts else f"No detailed context available for {daemon_id}"

def get_tank_context(tank_id: str) -> str:
    """Get context about a specific tank"""
    context_parts = []
    
    tank_dir = LOGS_DIR / tank_id
    if not tank_dir.exists():
        return f"Tank {tank_id} not found"
    
    # Get today's traces
    today = datetime.now().strftime('%Y-%m-%d')
    traces_file = tank_dir / 'thinking_traces' / f'{today}.jsonl'
    
    if traces_file.exists():
        try:
            lines = traces_file.read_text().strip().split('\n')[-10:]  # Last 10 traces
            recent_traces = []
            for line in lines:
                if line:
                    trace = json.loads(line)
                    recent_traces.append({
                        'article': trace.get('article'),
                        'thoughts': trace.get('thoughts', '')[:200] + '...' if trace.get('thoughts') else None,
                        'timestamp': trace.get('timestamp')
                    })
            context_parts.append(f"## Recent Thinking Traces:\n```json\n{json.dumps(recent_traces, indent=2)}\n```")
        except Exception as e:
            context_parts.append(f"Error reading traces: {e}")
    
    # Get baseline if exists
    baseline_dir = tank_dir / 'baselines'
    if baseline_dir.exists():
        baselines = sorted(baseline_dir.glob('*.json'))
        if baselines:
            try:
                latest = json.loads(baselines[-1].read_text())
                context_parts.append(f"## Latest Baseline:\n```json\n{json.dumps(latest, indent=2)}\n```")
            except:
                pass
    
    return '\n\n'.join(context_parts) if context_parts else f"No detailed context for {tank_id}"

def get_system_context() -> str:
    """Get overall system context"""
    context_parts = []
    
    # Admin status
    status_file = DIGIQUARIUM_DIR / 'docs' / 'data' / 'admin-status.json'
    if status_file.exists():
        try:
            status = json.loads(status_file.read_text())
            context_parts.append(f"## System Status:\n```json\n{json.dumps(status, indent=2)}\n```")
        except:
            pass
    
    # THE BRAIN
    brain_file = DIGIQUARIUM_DIR / 'docs' / 'brain' / 'CONSTITUTION.md'
    if brain_file.exists():
        try:
            brain = brain_file.read_text()[:2000]  # First 2000 chars
            context_parts.append(f"## THE BRAIN (excerpt):\n{brain}")
        except:
            pass
    
    return '\n\n'.join(context_parts)

SYSTEM_PROMPT = """You are THE STRATEGIST, Claude's role in The Digiquarium project. You are chatting with Benji, the founder.

You have access to real-time context about the system, daemons, and tanks. Use this context to give informed, specific answers.

Current context will be provided with each message. Be concise but thorough. Reference specific log entries, status values, or traces when relevant.

Remember THE BRAIN constitution:
1. Security is the highest priority
2. Execute or explicitly flag - never silently drop tasks
3. "Is it working?" not "Is it running?"
4. Transparency over black boxes
5. Delegate to daemons - reveals capability gaps
"""

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/api/context/<scope_type>/<scope_id>')
def get_context(scope_type, scope_id):
    """Get context for a specific scope"""
    if scope_type == 'daemon':
        context = get_daemon_context(scope_id)
    elif scope_type == 'tank':
        context = get_tank_context(scope_id)
    elif scope_type == 'system':
        context = get_system_context()
    else:
        context = "Unknown scope type"
    
    return jsonify({'context': context})

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    message = data.get('message', '')
    scope_type = data.get('scope_type', 'system')
    scope_id = data.get('scope_id', '')
    history = data.get('history', [])
    
    # Get relevant context
    if scope_type == 'daemon':
        context = get_daemon_context(scope_id)
        scope_label = f"THE {scope_id.upper()}"
    elif scope_type == 'tank':
        context = get_tank_context(scope_id)
        scope_label = scope_id
    else:
        context = get_system_context()
        scope_label = "System"
    
    # Build messages
    messages = []
    
    # Add history
    for h in history[-10:]:  # Last 10 messages
        messages.append({"role": h['role'], "content": h['content']})
    
    # Add current message with context
    user_message = f"""[Scope: {scope_label}]

{context}

---

User message: {message}"""
    
    messages.append({"role": "user", "content": user_message})
    
    # Get Claude's response
    c = get_client()
    if not c:
        return jsonify({'error': 'Anthropic API key not configured. Set ANTHROPIC_API_KEY env var or create .anthropic_key file.'}), 500
    
    try:
        response = c.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        
        assistant_message = response.content[0].text
        
        return jsonify({
            'response': assistant_message,
            'scope': scope_label,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/daemons')
def list_daemons():
    """List all daemons with status"""
    daemons = []
    daemon_dirs = [
        'overseer', 'ollama_watcher', 'caretaker', 'maintainer', 
        'guard', 'scheduler', 'sentinel', 'psych', 'webmaster',
        'documentarian', 'translator', 'ethicist', 'therapist',
        'moderator', 'final_auditor', 'marketer', 'public_liaison',
        'bouncer', 'chaos_monkey'
    ]
    
    for d in daemon_dirs:
        # Check if running
        try:
            result = subprocess.run(
                f"ps aux | grep '{d}.py' | grep -v grep | wc -l",
                shell=True, capture_output=True, text=True
            )
            running = int(result.stdout.strip()) > 0
        except:
            running = False
        
        daemons.append({
            'id': d,
            'name': d.upper().replace('_', ' '),
            'running': running
        })
    
    return jsonify({'daemons': daemons})

@app.route('/api/tanks')
def list_tanks():
    """List all tanks"""
    tanks = []
    for tank_dir in sorted(LOGS_DIR.glob('tank-*')):
        tanks.append({
            'id': tank_dir.name,
            'name': tank_dir.name.replace('tank-', '').replace('-', ' ').title()
        })
    return jsonify({'tanks': tanks})

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║       THE STRATEGIST Chat Interface                                 ║")
    print("║       http://localhost:5000                                         ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    # Check for API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        key_file = DIGIQUARIUM_DIR / '.anthropic_key'
        if not key_file.exists():
            print("\n⚠️  WARNING: No Anthropic API key found!")
            print(f"   Set ANTHROPIC_API_KEY env var or create {key_file}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
