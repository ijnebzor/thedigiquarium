#!/usr/bin/env python3
"""
THE OLLAMA WATCHER - LLM Infrastructure Monitor
================================================
Monitors Ollama health, manages inference queue, pauses/resumes tanks.

SLA: 5 min detection, 5 min remediation
CRITICAL: All AI inference depends on this.
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file, send_email_alert

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
CHECK_INTERVAL = 60  # 1 minute - critical service
OLLAMA_URL = "http://localhost:11435"
OLLAMA_HOST_URL = "http://localhost:11434"  # Direct host

class OllamaWatcher:
    def __init__(self):
        self.log = DaemonLogger('ollama_watcher')
        self.stats = {
            'cycles': 0,
            'healthy_checks': 0,
            'unhealthy_checks': 0,
            'tank_pauses': 0,
            'tank_resumes': 0
        }
        self.ollama_healthy = False
        self.tanks_paused = False
    
    def check_ollama_health(self):
        """Check if Ollama is responding"""
        # Try docker proxy first
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                return True, models
        except:
            pass
        
        # Try host directly
        try:
            response = requests.get(f"{OLLAMA_HOST_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                return True, models
        except:
            pass
        
        return False, []
    
    def test_inference(self):
        """Test actual inference capability"""
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    'model': 'llama3.2:latest',
                    'prompt': 'Say "OK"',
                    'stream': False,
                    'options': {'num_predict': 5}
                },
                timeout=30
            )
            if response.status_code == 200:
                return True, response.json().get('response', '')[:20]
        except:
            pass
        return False, "Inference failed"
    
    def pause_all_tanks(self):
        """Pause all tanks to prevent queue buildup"""
        if self.tanks_paused:
            return
        
        self.log.action("Pausing all tanks - Ollama unhealthy")
        
        code, stdout, _ = run_command("docker ps --filter 'name=tank-' --format '{{.Names}}'")
        tanks = stdout.strip().split('\n') if stdout.strip() else []
        
        for tank in tanks:
            if tank:
                run_command(f"docker pause {tank}")
        
        self.tanks_paused = True
        self.stats['tank_pauses'] += 1
    
    def resume_all_tanks(self):
        """Resume all tanks when Ollama is healthy"""
        if not self.tanks_paused:
            return
        
        self.log.action("Resuming all tanks - Ollama healthy")
        
        code, stdout, _ = run_command("docker ps -a --filter 'name=tank-' --format '{{.Names}}'")
        tanks = stdout.strip().split('\n') if stdout.strip() else []
        
        for tank in tanks:
            if tank:
                run_command(f"docker unpause {tank}")
        
        self.tanks_paused = False
        self.stats['tank_resumes'] += 1
    
    def write_status(self):
        """Write current Ollama status"""
        status_file = DIGIQUARIUM_DIR / 'daemons' / 'ollama_watcher' / 'status.json'
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'ollama_healthy': self.ollama_healthy,
            'tanks_paused': self.tanks_paused,
            'stats': self.stats
        }
        
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def run(self):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║              THE OLLAMA WATCHER - LLM Infrastructure                 ║
╠══════════════════════════════════════════════════════════════════════╣
║  Monitors: Ollama health, inference capability                      ║
║  Actions: Pause/resume tanks based on Ollama status                 ║
║  SLA: 1 min detection, 5 min remediation                            ║
╚══════════════════════════════════════════════════════════════════════╝
""")
        write_pid_file('ollama_watcher')
        self.log.info("THE OLLAMA WATCHER starting")
        
        consecutive_failures = 0
        
        while True:
            try:
                self.stats['cycles'] += 1
                
                # Check Ollama health
                healthy, models = self.check_ollama_health()
                
                if healthy:
                    self.ollama_healthy = True
                    self.stats['healthy_checks'] += 1
                    consecutive_failures = 0
                    
                    # Resume tanks if they were paused
                    if self.tanks_paused:
                        self.resume_all_tanks()
                    
                    if self.stats['cycles'] % 5 == 0:
                        self.log.info(f"Cycle {self.stats['cycles']}: Ollama healthy, models: {models[:3]}")
                
                else:
                    self.ollama_healthy = False
                    self.stats['unhealthy_checks'] += 1
                    consecutive_failures += 1
                    
                    self.log.warn(f"Ollama unhealthy (failure #{consecutive_failures})")
                    
                    # After 3 consecutive failures, pause tanks
                    if consecutive_failures >= 3 and not self.tanks_paused:
                        self.pause_all_tanks()
                    
                    # After 10 failures, escalate
                    if consecutive_failures == 10:
                        send_email_alert(
                            "🚨 OLLAMA DOWN - Tanks Paused",
                            f"Ollama has been unhealthy for {consecutive_failures} checks.\n"
                            f"All tanks have been paused.\n"
                            f"Manual intervention required.\n\n"
                            f"Time: {datetime.now()}"
                        )
                
                self.write_status()
                time.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                self.log.error(f"Cycle error: {e}")
                time.sleep(30)

if __name__ == '__main__':
    OllamaWatcher().run()
