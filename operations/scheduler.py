#!/usr/bin/env python3
"""
DIGIQUARIUM SCHEDULER - Master Calendar & Task Coordination
============================================================

Manages:
- 12-hour baseline schedule (all tanks, sequential)
- Daily summaries
- Language translation
- Baseline comparison/versioning
- Task queuing for Ollama inference

Works with: Caretaker, Guard, and other agents
SLA: 30 minutes
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
import queue

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
OPS_DIR = DIGIQUARIUM_DIR / 'operations'
CALENDAR_DIR = OPS_DIR / 'calendar'
REPORTS_DIR = OPS_DIR / 'reports'

# Ensure directories exist
CALENDAR_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Tank definitions with baseline order (sequential processing)
TANKS_ORDER = [
    ('tank-01-adam', 'english', 'control'),
    ('tank-02-eve', 'english', 'control'),
    ('tank-03-cain', 'english', 'agent'),
    ('tank-04-abel', 'english', 'agent'),
    ('tank-05-juan', 'spanish', 'language'),
    ('tank-06-juanita', 'spanish', 'language'),
    ('tank-07-klaus', 'german', 'language'),
    ('tank-08-genevieve', 'german', 'language'),
    ('tank-09-wei', 'chinese', 'language'),
    ('tank-10-mei', 'chinese', 'language'),
    ('tank-11-haruki', 'japanese', 'language'),
    ('tank-12-sakura', 'japanese', 'language'),
    ('tank-13-victor', 'english', 'visual'),
    ('tank-14-iris', 'english', 'visual'),
    ('tank-15-observer', 'english', 'special'),
    ('tank-16-seeker', 'english', 'special'),
    ('tank-17-seth', 'english', 'agent'),
]


class TaskQueue:
    """Thread-safe queue for Ollama inference tasks"""
    
    def __init__(self):
        self.queue = queue.Queue()
        self.processing = False
        self.current_task = None
    
    def add(self, task_type: str, tank_id: str, priority: int = 5):
        self.queue.put({
            'type': task_type,
            'tank_id': tank_id,
            'priority': priority,
            'queued_at': datetime.now().isoformat()
        })
    
    def get_next(self) -> Optional[dict]:
        if not self.queue.empty():
            return self.queue.get()
        return None
    
    def size(self) -> int:
        return self.queue.qsize()


task_queue = TaskQueue()


class Schedule:
    """Calendar and scheduling system"""
    
    def __init__(self):
        self.schedule_file = CALENDAR_DIR / 'schedule.json'
        self.load()
    
    def load(self):
        if self.schedule_file.exists():
            self.data = json.loads(self.schedule_file.read_text())
        else:
            self.data = {
                'baseline_interval_hours': 12,
                'last_baseline_run': None,
                'baseline_version': 0,
                'last_daily_summary': None,
                'scheduled_tasks': []
            }
            self.save()
    
    def save(self):
        self.schedule_file.write_text(json.dumps(self.data, indent=2))
    
    def should_run_baselines(self) -> bool:
        if not self.data['last_baseline_run']:
            return True
        last_run = datetime.fromisoformat(self.data['last_baseline_run'])
        hours_since = (datetime.now() - last_run).total_seconds() / 3600
        return hours_since >= self.data['baseline_interval_hours']
    
    def should_run_daily_summary(self) -> bool:
        if not self.data['last_daily_summary']:
            return True
        last_run = datetime.fromisoformat(self.data['last_daily_summary'])
        return last_run.date() < datetime.now().date()
    
    def mark_baselines_complete(self):
        self.data['last_baseline_run'] = datetime.now().isoformat()
        self.data['baseline_version'] += 1
        self.save()
    
    def mark_daily_summary_complete(self):
        self.data['last_daily_summary'] = datetime.now().isoformat()
        self.save()
    
    def get_baseline_version(self) -> int:
        return self.data['baseline_version']


schedule = Schedule()


def log_event(category: str, message: str, details: dict = None):
    """Log scheduler events"""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'category': category,
        'message': message,
        'details': details or {}
    }
    log_file = OPS_DIR / 'scheduler.log'
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{category}] {message}")


def run_command(cmd: str, timeout: int = 300) -> tuple:
    """Run shell command"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'Timeout'
    except Exception as e:
        return -1, '', str(e)


def wait_for_ollama():
    """Wait for Ollama to be available"""
    log_event('SCHEDULER', 'Waiting for Ollama availability...')
    for _ in range(30):
        code, stdout, _ = run_command('curl -s http://localhost:11435/api/tags', timeout=5)
        if code == 0:
            return True
        time.sleep(2)
    return False


def run_baseline_for_tank(tank_id: str, language: str) -> bool:
    """Run baseline assessment for a single tank (sequential, waits for completion)"""
    log_event('BASELINE', f'Starting baseline for {tank_id}', {'language': language})
    
    # Execute baseline inside the container
    cmd = f'docker exec {tank_id} python3 /tank/baseline.py'
    code, stdout, stderr = run_command(cmd, timeout=1800)  # 30 min timeout per tank
    
    if code == 0:
        log_event('BASELINE', f'Completed baseline for {tank_id}')
        return True
    else:
        log_event('BASELINE', f'Failed baseline for {tank_id}', {'error': stderr[:200]})
        return False


def run_all_baselines():
    """Run baselines sequentially for all tanks"""
    version = schedule.get_baseline_version() + 1
    log_event('BASELINE', f'Starting baseline run v{version} for all tanks')
    
    results = []
    for tank_id, language, tank_type in TANKS_ORDER:
        # Check if tank is running
        code, stdout, _ = run_command(f'docker ps --filter "name={tank_id}" --format "{{{{.Status}}}}"')
        if 'Up' not in stdout:
            log_event('BASELINE', f'Skipping {tank_id} - not running')
            results.append((tank_id, 'SKIPPED'))
            continue
        
        # Wait a bit between baselines to not overwhelm Ollama
        time.sleep(5)
        
        success = run_baseline_for_tank(tank_id, language)
        results.append((tank_id, 'SUCCESS' if success else 'FAILED'))
    
    # Mark completion
    schedule.mark_baselines_complete()
    
    # Generate baseline comparison report
    generate_baseline_comparison(version, results)
    
    return results


def generate_baseline_comparison(version: int, results: list):
    """Generate comparison of baselines across all tanks"""
    log_event('REPORT', f'Generating baseline comparison for v{version}')
    
    report = {
        'version': version,
        'timestamp': datetime.now().isoformat(),
        'tanks': {},
        'summary': {
            'total': len(results),
            'success': sum(1 for _, r in results if r == 'SUCCESS'),
            'failed': sum(1 for _, r in results if r == 'FAILED'),
            'skipped': sum(1 for _, r in results if r == 'SKIPPED')
        }
    }
    
    # Collect baseline data from each tank
    for tank_id, result in results:
        if result != 'SUCCESS':
            report['tanks'][tank_id] = {'status': result}
            continue
        
        # Find latest baseline
        baselines_dir = LOGS_DIR / tank_id / 'baselines'
        if baselines_dir.exists():
            baselines = sorted(baselines_dir.glob('*.json'), reverse=True)
            if baselines:
                try:
                    data = json.loads(baselines[0].read_text())
                    report['tanks'][tank_id] = {
                        'status': 'SUCCESS',
                        'file': baselines[0].name,
                        'mental_state': data.get('mental_state_analysis', {}),
                        'answered': sum(1 for r in data.get('responses', {}).values() if r.get('answer'))
                    }
                except:
                    report['tanks'][tank_id] = {'status': 'PARSE_ERROR'}
    
    # Save report
    report_file = REPORTS_DIR / f'baseline_comparison_v{version}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    report_file.write_text(json.dumps(report, indent=2))
    
    log_event('REPORT', f'Saved baseline comparison to {report_file.name}')


def generate_daily_summary():
    """Generate daily summary report"""
    log_event('REPORT', 'Generating daily summary')
    
    today = datetime.now().strftime('%Y-%m-%d')
    summary = {
        'date': today,
        'timestamp': datetime.now().isoformat(),
        'tanks': {},
        'totals': {
            'articles_read': 0,
            'discoveries': 0,
            'baselines': 0
        }
    }
    
    for tank_id, language, tank_type in TANKS_ORDER:
        tank_dir = LOGS_DIR / tank_id
        tank_summary = {
            'language': language,
            'type': tank_type,
            'articles_today': 0,
            'discoveries_today': 0
        }
        
        # Count today's traces
        traces_file = tank_dir / 'thinking_traces' / f'{today}.jsonl'
        if traces_file.exists():
            tank_summary['articles_today'] = sum(1 for _ in open(traces_file))
        
        # Count discoveries
        discoveries_file = tank_dir / 'discoveries' / f'{today}.md'
        if discoveries_file.exists():
            content = discoveries_file.read_text()
            tank_summary['discoveries_today'] = content.count('## ')
        
        summary['tanks'][tank_id] = tank_summary
        summary['totals']['articles_read'] += tank_summary['articles_today']
        summary['totals']['discoveries_today'] += tank_summary['discoveries_today']
    
    # Save summary
    summary_file = REPORTS_DIR / f'daily_summary_{today}.json'
    summary_file.write_text(json.dumps(summary, indent=2))
    
    # Also create markdown version
    md_content = f"# Daily Summary - {today}\n\n"
    md_content += f"**Total Articles Read:** {summary['totals']['articles_read']}\n"
    md_content += f"**Total Discoveries:** {summary['totals']['discoveries_today']}\n\n"
    md_content += "## Tank Activity\n\n"
    md_content += "| Tank | Language | Articles | Discoveries |\n"
    md_content += "|------|----------|----------|-------------|\n"
    for tank_id, data in summary['tanks'].items():
        name = tank_id.split('-')[-1]
        md_content += f"| {name} | {data['language']} | {data['articles_today']} | {data['discoveries_today']} |\n"
    
    md_file = REPORTS_DIR / f'daily_summary_{today}.md'
    md_file.write_text(md_content)
    
    schedule.mark_daily_summary_complete()
    log_event('REPORT', f'Daily summary saved to {summary_file.name}')
    
    return summary


def scheduler_loop():
    """Main scheduler loop"""
    log_event('SCHEDULER', 'Scheduler starting')
    
    while True:
        try:
            # Check if baselines need to run
            if schedule.should_run_baselines():
                log_event('SCHEDULER', 'Baseline run due - starting')
                run_all_baselines()
            
            # Check if daily summary needed
            if schedule.should_run_daily_summary():
                log_event('SCHEDULER', 'Daily summary due - starting')
                generate_daily_summary()
            
            # Process any queued tasks
            while task_queue.size() > 0:
                task = task_queue.get_next()
                if task:
                    log_event('SCHEDULER', f"Processing queued task: {task['type']} for {task['tank_id']}")
                    if task['type'] == 'baseline':
                        run_baseline_for_tank(task['tank_id'], 'english')
            
            # Sleep for 5 minutes before next check
            time.sleep(300)
            
        except KeyboardInterrupt:
            log_event('SCHEDULER', 'Scheduler stopped by user')
            break
        except Exception as e:
            log_event('SCHEDULER', f'Error: {e}')
            time.sleep(60)


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           📅 DIGIQUARIUM SCHEDULER - Master Calendar 📅              ║
╠══════════════════════════════════════════════════════════════════════╣
║  Baseline interval: Every 12 hours                                   ║
║  Daily summaries: Every day at first check                           ║
║  Task queue: Active                                                  ║
║  SLA: 30 minutes                                                     ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'baselines':
            run_all_baselines()
        elif sys.argv[1] == 'summary':
            generate_daily_summary()
        elif sys.argv[1] == 'status':
            print(f"Last baseline: {schedule.data['last_baseline_run']}")
            print(f"Baseline version: {schedule.data['baseline_version']}")
            print(f"Last daily summary: {schedule.data['last_daily_summary']}")
        else:
            scheduler_loop()
    else:
        scheduler_loop()


if __name__ == '__main__':
    main()
