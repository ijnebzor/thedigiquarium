#!/usr/bin/env python3
"""
Admin API - Wired Controls
==========================
Flask API that handles admin panel actions.
Run alongside the chat UI or standalone.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'

app = Flask(__name__)
CORS(app)  # Allow cross-origin from admin panel

def run_cmd(cmd, timeout=60):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, 
            text=True, timeout=timeout
        )
        return {
            'success': result.returncode == 0,
            'output': result.stdout + result.stderr
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'output': 'Command timed out'}
    except Exception as e:
        return {'success': False, 'output': str(e)}

@app.route('/api/action/<action>', methods=['POST'])
def execute_action(action):
    """Execute an admin action"""
    
    timestamp = datetime.now().isoformat()
    
    if action == 'audit':
        # Run system audit via OVERSEER
        result = run_cmd('python3 /home/ijneb/digiquarium/daemons/admin_status_generator.py')
        return jsonify({
            'action': 'audit',
            'timestamp': timestamp,
            'result': result,
            'message': 'System audit completed' if result['success'] else 'Audit failed'
        })
    
    elif action == 'prune_logs':
        # Run log pruning via WEBMASTER
        result = run_cmd('''python3 -c "
import sys
sys.path.insert(0, '/home/ijneb/digiquarium/daemons')
from webmaster.webmaster import Webmaster
w = Webmaster()
tanks, kept, pruned = w.prune_and_publish_logs()
print(f'Pruned {pruned} entries, kept {kept} from {tanks} tanks')
"''')
        return jsonify({
            'action': 'prune_logs',
            'timestamp': timestamp,
            'result': result,
            'message': 'Log pruning completed' if result['success'] else 'Prune failed'
        })
    
    elif action == 'push_github':
        # Git add, commit, push
        result = run_cmd('''cd /home/ijneb/digiquarium && \
            git add -A && \
            git commit -m "🤖 Auto-commit: Admin panel push $(date +%Y-%m-%d_%H:%M)" && \
            git push''')
        return jsonify({
            'action': 'push_github',
            'timestamp': timestamp,
            'result': result,
            'message': 'Pushed to GitHub' if result['success'] else 'Push failed'
        })
    
    elif action == 'restart_ollama':
        # Restart Ollama proxy container
        result = run_cmd('docker restart digiquarium-ollama')
        return jsonify({
            'action': 'restart_ollama',
            'timestamp': timestamp,
            'result': result,
            'message': 'Ollama restarted' if result['success'] else 'Restart failed'
        })
    
    elif action == 'chaos_enable':
        # Remove chaos kill file
        kill_file = DAEMONS_DIR / 'chaos_monkey' / 'DISABLE_CHAOS'
        if kill_file.exists():
            kill_file.unlink()
        return jsonify({
            'action': 'chaos_enable',
            'timestamp': timestamp,
            'result': {'success': True, 'output': 'Chaos enabled'},
            'message': 'Chaos Monkey enabled'
        })
    
    elif action == 'chaos_disable':
        # Create chaos kill file
        kill_file = DAEMONS_DIR / 'chaos_monkey' / 'DISABLE_CHAOS'
        kill_file.parent.mkdir(exist_ok=True)
        kill_file.touch()
        return jsonify({
            'action': 'chaos_disable',
            'timestamp': timestamp,
            'result': {'success': True, 'output': 'Chaos disabled'},
            'message': 'Chaos Monkey disabled'
        })
    
    elif action == 'chaos_trigger':
        # Manually trigger a chaos event
        result = run_cmd('''python3 -c "
import sys
sys.path.insert(0, '/home/ijneb/digiquarium/daemons')
from chaos_monkey.chaos_monkey import ChaosMonkey
m = ChaosMonkey()
m.execute_chaos()
"''')
        return jsonify({
            'action': 'chaos_trigger',
            'timestamp': timestamp,
            'result': result,
            'message': 'Chaos event triggered' if result['success'] else 'Trigger failed'
        })
    
    elif action == 'restart_daemon':
        daemon = request.json.get('daemon')
        if not daemon:
            return jsonify({'error': 'No daemon specified'}), 400
        
        # Kill and restart daemon
        result = run_cmd(f'''pkill -9 -f "{daemon}.py" 2>/dev/null; \
            sleep 2; \
            nohup python3 /home/ijneb/digiquarium/daemons/{daemon}/{daemon}.py \
            >> /home/ijneb/digiquarium/daemons/logs/{daemon}.log 2>&1 &''')
        return jsonify({
            'action': 'restart_daemon',
            'daemon': daemon,
            'timestamp': timestamp,
            'result': {'success': True, 'output': f'{daemon} restarted'},
            'message': f'{daemon} restarted'
        })
    
    else:
        return jsonify({'error': f'Unknown action: {action}'}), 400

@app.route('/api/status')
def get_status():
    """Get current system status"""
    status_file = DIGIQUARIUM_DIR / 'docs' / 'data' / 'admin-status.json'
    if status_file.exists():
        return jsonify(json.loads(status_file.read_text()))
    return jsonify({'error': 'Status file not found'}), 404

@app.route('/api/chaos/stats')
def get_chaos_stats():
    """Get Chaos Monkey statistics"""
    stats_file = DAEMONS_DIR / 'chaos_monkey' / 'stats.json'
    events_file = DAEMONS_DIR / 'chaos_monkey' / 'events.jsonl'
    kill_file = DAEMONS_DIR / 'chaos_monkey' / 'DISABLE_CHAOS'
    
    result = {
        'enabled': not kill_file.exists(),
        'stats': {},
        'recent_events': []
    }
    
    if stats_file.exists():
        result['stats'] = json.loads(stats_file.read_text())
    
    if events_file.exists():
        lines = events_file.read_text().strip().split('\n')[-10:]
        result['recent_events'] = [json.loads(l) for l in lines if l]
    
    return jsonify(result)

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║       Admin API - Wired Controls                                    ║")
    print("║       http://localhost:5001                                         ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    app.run(host='0.0.0.0', port=5001, debug=False)
