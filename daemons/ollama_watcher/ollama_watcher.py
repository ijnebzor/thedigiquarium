#!/usr/bin/env python3
"""
THE OLLAMA WATCHER v2.0 - LLM Infrastructure Monitor (Enhanced)
================================================================
Monitors Ollama service health and AUTO-RESTARTS on failure.

Post-incident upgrade (2026-02-21):
- Auto-restart after 3 consecutive failures
- Escalate to OVERSEER after 3 restart attempts
- Clear failure count on success

"Detection without action is worthless." - Incident Report
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'

class OllamaWatcher:
    def __init__(self):
        self.name = 'ollama_watcher'
        self.log_file = DAEMONS_DIR / 'logs' / 'ollama_watcher.log'
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.status_file = DAEMONS_DIR / 'ollama_watcher' / 'status.json'
        
        # Failure tracking
        self.consecutive_failures = 0
        self.restart_attempts = 0
        self.total_failures = 0
        
        # Thresholds
        self.AUTO_RESTART_THRESHOLD = 3  # Restart after this many consecutive failures
        self.ESCALATION_THRESHOLD = 3    # Escalate after this many restart attempts
        
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        icons = {'INFO': 'ℹ️', 'WARNING': '⚠️', 'ERROR': '❌', 'ACTION': '🔧', 'SUCCESS': '✅'}
        icon = icons.get(level, 'ℹ️')
        log_entry = f"{timestamp} {icon} [OLLAMA_WATCHER] {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        print(log_entry.strip())
    
    def run_command(self, cmd: list, timeout: int = 30) -> dict:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {'success': result.returncode == 0, 'stdout': result.stdout, 'stderr': result.stderr}
        except Exception as e:
            return {'success': False, 'stdout': '', 'stderr': str(e)}
    
    def check_health(self) -> bool:
        """Check if Ollama is responding"""
        result = self.run_command(['curl', '-s', '--max-time', '10', 'http://localhost:11434/api/tags'])
        return result['success'] and result['stdout'].strip() and 'models' in result['stdout']
    
    def restart_ollama(self) -> bool:
        """Restart the Ollama container"""
        self.log('ACTION', f'Auto-restarting Ollama (attempt {self.restart_attempts + 1})')
        
        result = self.run_command(['docker', 'restart', 'digiquarium-ollama'], timeout=60)
        
        if not result['success']:
            self.log('ERROR', f'Docker restart command failed: {result["stderr"]}')
            return False
        
        # Wait for startup
        self.log('INFO', 'Waiting 15 seconds for Ollama startup...')
        time.sleep(15)
        
        # Verify health
        if self.check_health():
            self.log('SUCCESS', 'Ollama restarted and healthy!')
            return True
        else:
            self.log('ERROR', 'Ollama restarted but still unhealthy')
            return False
    
    def escalate_to_overseer(self, message: str):
        """Send issue to THE OVERSEER"""
        overseer_inbox = DAEMONS_DIR / 'overseer' / 'inbox'
        overseer_inbox.mkdir(parents=True, exist_ok=True)
        
        issue = {
            'from': 'ollama_watcher',
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'severity': 'critical',
            'consecutive_failures': self.consecutive_failures,
            'restart_attempts': self.restart_attempts,
            'total_failures': self.total_failures
        }
        
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_ollama_watcher.json"
        (overseer_inbox / filename).write_text(json.dumps(issue, indent=2))
        
        self.log('WARNING', f'Escalated to OVERSEER: {message}')
    
    def update_status(self, healthy: bool):
        """Update status file"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'healthy': healthy,
            'consecutive_failures': self.consecutive_failures,
            'restart_attempts': self.restart_attempts,
            'total_failures': self.total_failures
        }
        
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        self.status_file.write_text(json.dumps(status, indent=2))
    
    def run_cycle(self):
        """Single monitoring cycle"""
        healthy = self.check_health()
        
        if healthy:
            # Success! Reset failure counters
            if self.consecutive_failures > 0:
                self.log('SUCCESS', f'Ollama recovered after {self.consecutive_failures} failures')
            self.consecutive_failures = 0
            self.restart_attempts = 0
            self.log('INFO', 'Ollama healthy')
        else:
            # Failure detected
            self.consecutive_failures += 1
            self.total_failures += 1
            self.log('WARNING', f'Ollama unhealthy (failure #{self.consecutive_failures}, total: {self.total_failures})')
            
            # Check if we should auto-restart
            if self.consecutive_failures >= self.AUTO_RESTART_THRESHOLD:
                if self.restart_attempts < self.ESCALATION_THRESHOLD:
                    # Attempt restart
                    self.restart_attempts += 1
                    success = self.restart_ollama()
                    
                    if success:
                        self.consecutive_failures = 0
                        self.restart_attempts = 0
                    elif self.restart_attempts >= self.ESCALATION_THRESHOLD:
                        # Escalate to OVERSEER
                        self.escalate_to_overseer(
                            f'Ollama unrecoverable after {self.ESCALATION_THRESHOLD} restart attempts. '
                            f'Total failures: {self.total_failures}. Requires human intervention.'
                        )
                else:
                    # Already escalated, just log
                    self.log('ERROR', f'Ollama still down, already escalated (failure #{self.total_failures})')
        
        self.update_status(healthy)
    
    def run(self):
        """Main daemon loop"""
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║        THE OLLAMA WATCHER v2.0 - LLM Infrastructure Monitor         ║")
        print("║        Now with AUTO-RESTART capability!                            ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        
        self.log('INFO', 'THE OLLAMA WATCHER v2.0 initialized')
        self.log('INFO', f'Auto-restart after {self.AUTO_RESTART_THRESHOLD} failures')
        self.log('INFO', f'Escalate after {self.ESCALATION_THRESHOLD} restart attempts')
        
        check_interval = 60  # 1 minute
        
        while True:
            try:
                self.run_cycle()
            except Exception as e:
                self.log('ERROR', f'Monitoring cycle failed: {e}')
            
            time.sleep(check_interval)


def main():
    watcher = OllamaWatcher()
    watcher.run()


if __name__ == '__main__':
    main()
