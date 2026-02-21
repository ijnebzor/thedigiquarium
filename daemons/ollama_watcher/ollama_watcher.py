#!/usr/bin/env python3
"""
THE OLLAMA WATCHER v3.0 - LLM Infrastructure Monitor (Fixed)
============================================================
Monitors Ollama service health and AUTO-RESTARTS on failure.

v3.0 Changes (2026-02-22):
- Check Windows host directly (192.168.50.94:11434)
- Check socat proxy container health
- Restart proxy container, not Ollama itself
- Proper escalation to OVERSEER
- PID file management for single instance

"Detection without action is worthless." - Incident Report
"""

import os
import sys
import json
import time
import signal
import subprocess
import fcntl
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'

# Ollama configuration
WINDOWS_HOST_OLLAMA = "http://192.168.50.94:11434"
PROXY_CONTAINER = "digiquarium-ollama"

class OllamaWatcher:
    def __init__(self):
        self.name = 'ollama_watcher'
        self.log_file = DAEMONS_DIR / 'logs' / 'ollama_watcher.log'
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.status_file = DAEMONS_DIR / 'ollama_watcher' / 'status.json'
        self.pid_file = DAEMONS_DIR / 'ollama_watcher' / 'ollama_watcher.pid'
        self.lock_file = DAEMONS_DIR / 'ollama_watcher' / 'ollama_watcher.lock'
        
        # Failure tracking
        self.consecutive_failures = 0
        self.restart_attempts = 0
        self.total_failures = 0
        
        # Thresholds
        self.AUTO_RESTART_THRESHOLD = 3
        self.ESCALATION_THRESHOLD = 3
        
        self.running = True
        
    def acquire_lock(self):
        """Ensure only one instance runs"""
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock_fd = open(self.lock_file, 'w')
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Write PID
            self.pid_file.write_text(str(os.getpid()))
            return True
        except IOError:
            self.log('ERROR', 'Another instance is already running')
            return False
    
    def release_lock(self):
        """Release lock on shutdown"""
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            self.lock_fd.close()
            self.pid_file.unlink(missing_ok=True)
            self.lock_file.unlink(missing_ok=True)
        except:
            pass
    
    def shutdown(self, signum, frame):
        """Graceful shutdown"""
        self.log('INFO', f'Received signal {signum}, shutting down')
        self.running = False
        self.release_lock()
        sys.exit(0)
        
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        icons = {'INFO': 'ℹ️', 'WARNING': '⚠️', 'ERROR': '❌', 'ACTION': '🔧', 'SUCCESS': '✅'}
        icon = icons.get(level, 'ℹ️')
        log_entry = f"{timestamp} {icon} [OLLAMA_WATCHER] {message}"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
        print(log_entry)
    
    def check_windows_ollama(self) -> bool:
        """Check if Ollama on Windows host is responding"""
        try:
            req = urllib.request.Request(f"{WINDOWS_HOST_OLLAMA}/api/tags", method='GET')
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                return 'models' in data and len(data['models']) > 0
        except Exception as e:
            self.log('WARNING', f'Windows Ollama check failed: {e}')
            return False
    
    def check_proxy_container(self) -> bool:
        """Check if socat proxy container is running"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={PROXY_CONTAINER}', '--format', '{{.Status}}'],
                capture_output=True, text=True, timeout=10
            )
            return 'Up' in result.stdout
        except Exception as e:
            self.log('WARNING', f'Proxy container check failed: {e}')
            return False
    
    def check_end_to_end(self) -> bool:
        """Check if a tank can actually reach Ollama through the proxy"""
        try:
            result = subprocess.run([
                'docker', 'exec', 'tank-01-adam', 'python3', '-c',
                '''
import urllib.request
import json
try:
    with urllib.request.urlopen("http://digiquarium-ollama:11434/api/tags", timeout=10) as r:
        data = json.loads(r.read())
        print("OK" if "models" in data else "FAIL")
except Exception as e:
    print(f"FAIL:{e}")
'''
            ], capture_output=True, text=True, timeout=30)
            return 'OK' in result.stdout
        except Exception as e:
            self.log('WARNING', f'End-to-end check failed: {e}')
            return False
    
    def restart_proxy(self) -> bool:
        """Restart the socat proxy container"""
        self.log('ACTION', f'Restarting proxy container (attempt {self.restart_attempts + 1})')
        
        try:
            # Stop and remove if exists
            subprocess.run(['docker', 'rm', '-f', PROXY_CONTAINER], 
                          capture_output=True, timeout=30)
            time.sleep(2)
            
            # Start via compose
            result = subprocess.run(
                ['docker', 'compose', 'up', '-d', 'ollama'],
                cwd=str(DIGIQUARIUM_DIR),
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode != 0:
                self.log('ERROR', f'Docker compose failed: {result.stderr}')
                return False
            
            time.sleep(10)
            
            # Verify
            if self.check_end_to_end():
                self.log('SUCCESS', 'Proxy container restarted and working')
                return True
            else:
                self.log('ERROR', 'Proxy restarted but end-to-end check failed')
                return False
                
        except Exception as e:
            self.log('ERROR', f'Restart failed: {e}')
            return False
    
    def escalate_to_overseer(self, message: str):
        """Send issue to THE OVERSEER"""
        overseer_inbox = DAEMONS_DIR / 'overseer' / 'inbox'
        overseer_inbox.mkdir(parents=True, exist_ok=True)
        
        issue = {
            'from': self.name,
            'timestamp': datetime.now().isoformat(),
            'severity': 'critical',
            'message': message,
            'consecutive_failures': self.consecutive_failures,
            'restart_attempts': self.restart_attempts,
            'total_failures': self.total_failures
        }
        
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.name}.json"
        (overseer_inbox / filename).write_text(json.dumps(issue, indent=2))
        self.log('WARNING', f'Escalated to OVERSEER: {message}')
    
    def update_status(self, windows_ok: bool, proxy_ok: bool, e2e_ok: bool):
        """Update status file"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'windows_ollama_healthy': windows_ok,
            'proxy_container_healthy': proxy_ok,
            'end_to_end_healthy': e2e_ok,
            'overall_healthy': windows_ok and proxy_ok and e2e_ok,
            'consecutive_failures': self.consecutive_failures,
            'restart_attempts': self.restart_attempts,
            'total_failures': self.total_failures
        }
        
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        self.status_file.write_text(json.dumps(status, indent=2))
    
    def run_cycle(self):
        """Single monitoring cycle"""
        # Check all three levels
        windows_ok = self.check_windows_ollama()
        proxy_ok = self.check_proxy_container()
        e2e_ok = self.check_end_to_end() if (windows_ok and proxy_ok) else False
        
        overall_healthy = windows_ok and proxy_ok and e2e_ok
        
        if overall_healthy:
            if self.consecutive_failures > 0:
                self.log('SUCCESS', f'Ollama recovered after {self.consecutive_failures} failures')
            self.consecutive_failures = 0
            self.restart_attempts = 0
            self.log('INFO', f'Ollama healthy (Windows: ✓, Proxy: ✓, E2E: ✓)')
        else:
            self.consecutive_failures += 1
            self.total_failures += 1
            
            status_str = f"Windows: {'✓' if windows_ok else '✗'}, Proxy: {'✓' if proxy_ok else '✗'}, E2E: {'✓' if e2e_ok else '✗'}"
            self.log('WARNING', f'Ollama unhealthy ({status_str}) - failure #{self.consecutive_failures}')
            
            # Diagnose the problem
            if not windows_ok:
                self.log('ERROR', 'Windows Ollama is down - requires manual intervention on Windows host')
                self.escalate_to_overseer('Windows Ollama is down. Check Windows host at 192.168.50.94')
            elif not proxy_ok:
                # Proxy issue - we can fix this
                if self.consecutive_failures >= self.AUTO_RESTART_THRESHOLD:
                    if self.restart_attempts < self.ESCALATION_THRESHOLD:
                        self.restart_attempts += 1
                        if self.restart_proxy():
                            self.consecutive_failures = 0
                            self.restart_attempts = 0
                    else:
                        self.escalate_to_overseer(
                            f'Proxy container unrecoverable after {self.ESCALATION_THRESHOLD} restart attempts'
                        )
            elif not e2e_ok:
                # Network issue
                self.log('ERROR', 'End-to-end connectivity failed despite healthy components')
                if self.consecutive_failures >= self.AUTO_RESTART_THRESHOLD:
                    self.escalate_to_overseer('End-to-end connectivity failed. Check Docker networking.')
        
        self.update_status(windows_ok, proxy_ok, e2e_ok)
    
    def run(self):
        """Main daemon loop"""
        # Ensure single instance
        if not self.acquire_lock():
            sys.exit(1)
        
        # Handle signals
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║   THE OLLAMA WATCHER v3.0 - LLM Infrastructure Monitor (Fixed)      ║")
        print("║   Now with: Single instance lock, E2E testing, Windows host check   ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        
        self.log('INFO', 'THE OLLAMA WATCHER v3.0 initialized')
        self.log('INFO', f'Windows host: {WINDOWS_HOST_OLLAMA}')
        self.log('INFO', f'Proxy container: {PROXY_CONTAINER}')
        
        check_interval = 60  # 1 minute
        
        while self.running:
            try:
                self.run_cycle()
            except Exception as e:
                self.log('ERROR', f'Monitoring cycle failed: {e}')
            
            time.sleep(check_interval)
        
        self.release_lock()


if __name__ == '__main__':
    watcher = OllamaWatcher()
    watcher.run()
