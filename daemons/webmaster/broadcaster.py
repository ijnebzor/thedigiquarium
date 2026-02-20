#!/usr/bin/env python3
"""
THE BROADCASTER - Live Feed Export System
==========================================
Part of THE WEBMASTER's responsibilities.

Coordinates with:
- THE SCHEDULER: Runs AFTER baselines complete (not during)
- THE CARETAKER: Checks all tanks are healthy before export
- THE WEBMASTER: Commits to GitHub for site deployment

Timing Strategy (Coordinated with CARETAKER):
- Baselines run every 12 hours (00:00, 12:00 approximately)
- CARETAKER confirms all tanks healthy
- Broadcast runs 30 minutes AFTER baseline completion
- Queues export request, doesn't interrupt active inference
- This ensures:
  1. Baselines are complete (fresh data)
  2. Tanks have resumed exploration (not during inference)
  3. No interference with active sessions
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
DOCS_DIR = DIGIQUARIUM_DIR / 'docs'
DATA_DIR = DOCS_DIR / 'data'
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'
CONGREGATIONS_DIR = DIGIQUARIUM_DIR / 'congregations'

# Tank configuration
RESEARCH_TANKS = [
    ('tank-01-adam', 'Adam', 'Control', '👤'),
    ('tank-02-eve', 'Eve', 'Control', '👩'),
    ('tank-03-cain', 'Cain', 'Agent', '🤖'),
    ('tank-04-abel', 'Abel', 'Agent', '🤖'),
    ('tank-05-juan', 'Juan', 'Spanish', '🇪🇸'),
    ('tank-06-juanita', 'Juanita', 'Spanish', '🇪🇸'),
    ('tank-07-klaus', 'Klaus', 'German', '🇩🇪'),
    ('tank-08-genevieve', 'Genevieve', 'German', '🇩🇪'),
    ('tank-09-wei', 'Wei', 'Chinese', '🇨🇳'),
    ('tank-10-mei', 'Mei', 'Chinese', '🇨🇳'),
    ('tank-11-haruki', 'Haruki', 'Japanese', '🇯🇵'),
    ('tank-12-sakura', 'Sakura', 'Japanese', '🇯🇵'),
    ('tank-13-victor', 'Victor', 'Visual', '👁️'),
    ('tank-14-iris', 'Iris', 'Visual', '👁️'),
    ('tank-15-observer', 'Observer', 'Special', '🔭'),
    ('tank-16-seeker', 'Seeker', 'Special', '🔍'),
    ('tank-17-seth', 'Seth', 'Agent', '🤖'),
]


class Broadcaster:
    """Exports live feed data for the website dashboard"""
    
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.broadcast_log = []
    
    def log(self, message: str):
        """Log broadcast activity"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.broadcast_log.append(f"[{timestamp}] {message}")
        print(f"[BROADCASTER] {message}")
    
    def check_safe_to_broadcast(self) -> tuple[bool, str]:
        """
        Coordinate with CARETAKER and SCHEDULER to ensure safe broadcast window.
        """
        # Check if baselines are currently running
        scheduler_status = DAEMONS_DIR / 'scheduler' / 'status.json'
        if scheduler_status.exists():
            try:
                status = json.loads(scheduler_status.read_text())
                if status.get('baseline_in_progress', False):
                    return False, "Baselines currently in progress"
            except:
                pass
        
        # Check CARETAKER for tank health
        caretaker_status = DAEMONS_DIR / 'caretaker' / 'status.json'
        if caretaker_status.exists():
            try:
                status = json.loads(caretaker_status.read_text())
                unhealthy = status.get('unhealthy_tanks', [])
                if len(unhealthy) > 3:
                    return False, f"Too many unhealthy tanks: {unhealthy}"
            except:
                pass
        
        return True, "Safe to broadcast"
    
    def get_recent_traces(self, tank_id: str, hours: int = 12) -> List[Dict]:
        """Get thinking traces from the last N hours - CORRECT FORMAT"""
        traces = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        traces_dir = LOGS_DIR / tank_id / 'thinking_traces'
        if not traces_dir.exists():
            return traces
        
        # Check today and yesterday's files
        for days_ago in range(2):
            date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            trace_file = traces_dir / f'{date}.jsonl'
            
            if not trace_file.exists():
                continue
            
            try:
                with open(trace_file) as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            entry_time = datetime.fromisoformat(entry.get('timestamp', '2020-01-01'))
                            if entry_time > cutoff:
                                # Parse the ACTUAL trace format
                                thought_text = entry.get('thoughts', '')
                                # Get first 150 chars of meaningful thought
                                if thought_text:
                                    # Clean up and truncate
                                    thought_text = thought_text.replace('\n', ' ').strip()
                                    thought_text = self._truncate(thought_text, 150)
                                
                                traces.append({
                                    'time': entry_time.strftime('%H:%M'),
                                    'date': entry_time.strftime('%Y-%m-%d'),
                                    'article': entry.get('article', 'Unknown'),
                                    'thought': thought_text,
                                    'next': entry.get('next', ''),
                                    'why': self._truncate(entry.get('why', ''), 100)
                                })
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                self.log(f"Error reading {trace_file}: {e}")
                continue
        
        # Return most recent 20 traces, sorted by time
        traces.sort(key=lambda x: (x['date'], x['time']), reverse=True)
        return traces[:20]
    
    def get_latest_baseline(self, tank_id: str) -> Optional[Dict]:
        """Get the most recent baseline for a tank"""
        baselines_dir = LOGS_DIR / tank_id / 'personality_baselines'
        if not baselines_dir.exists():
            return None
        
        baseline_files = sorted(baselines_dir.glob('*.json'), reverse=True)
        if not baseline_files:
            return None
        
        try:
            with open(baseline_files[0]) as f:
                baseline = json.load(f)
                return {
                    'timestamp': baseline.get('timestamp', 'Unknown'),
                    'number': baseline.get('baseline_number', '?'),
                    'dimensions': len(baseline.get('responses', {})),
                    'file': baseline_files[0].name
                }
        except:
            return None
    
    def get_top_topics(self, tank_id: str, hours: int = 48) -> List[Dict]:
        """Extract top topics from recent traces with visit counts"""
        topics = {}
        traces = self.get_recent_traces(tank_id, hours=hours)
        
        for trace in traces:
            article = trace.get('article', '')
            if article and article != 'Unknown':
                topics[article] = topics.get(article, 0) + 1
        
        # Return top 8 with counts
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        return [{'topic': t[0], 'visits': t[1]} for t in sorted_topics[:8]]
    
    def get_congregations(self) -> Dict:
        """Get recent and upcoming congregations"""
        result = {'recent': [], 'upcoming': []}
        
        if CONGREGATIONS_DIR.exists():
            for cong_dir in sorted(CONGREGATIONS_DIR.iterdir(), reverse=True):
                if not cong_dir.is_dir():
                    continue
                
                state_file = cong_dir / 'state.json'
                if not state_file.exists():
                    continue
                
                try:
                    state = json.loads(state_file.read_text())
                    if state.get('status') in ['COMPLETED', 'ERROR', 'TIMEOUT']:
                        if len(result['recent']) < 5:
                            result['recent'].append({
                                'id': state.get('id'),
                                'topic': state.get('topic'),
                                'participants': state.get('participants', []),
                                'status': state.get('status'),
                                'duration_minutes': state.get('duration_minutes')
                            })
                except:
                    continue
        
        # Upcoming topics
        result['upcoming'] = [
            {'topic': 'Should we divert all scientific endeavour to curing cancer?', 'participants': ['Adam', 'Eve'], 'scheduled': 'TBD'},
            {'topic': 'What gives existence meaning?', 'participants': ['Adam', 'Eve'], 'scheduled': 'TBD'},
            {'topic': 'Is knowledge discovered or created?', 'participants': ['Adam', 'Eve'], 'scheduled': 'TBD'},
        ]
        
        return result
    
    def get_system_stats(self) -> Dict:
        """Calculate overall system statistics"""
        stats = {
            'total_traces': 0,
            'total_baselines': 0,
            'active_tanks': 0,
            'traces_today': 0
        }
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        for tank_id, _, _, _ in RESEARCH_TANKS:
            tank_dir = LOGS_DIR / tank_id
            
            # Count all traces
            traces_dir = tank_dir / 'thinking_traces'
            if traces_dir.exists():
                for trace_file in traces_dir.glob('*.jsonl'):
                    try:
                        with open(trace_file) as f:
                            count = sum(1 for _ in f)
                            stats['total_traces'] += count
                            if today in trace_file.name:
                                stats['traces_today'] += count
                    except:
                        pass
            
            # Count baselines
            baselines_dir = tank_dir / 'personality_baselines'
            if baselines_dir.exists():
                stats['total_baselines'] += len(list(baselines_dir.glob('*.json')))
            
            # Check if active
            recent = self.get_recent_traces(tank_id, hours=6)
            if recent:
                stats['active_tanks'] += 1
        
        return stats
    
    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis"""
        if not text:
            return ''
        if len(text) <= max_len:
            return text
        return text[:max_len-3] + '...'
    
    def generate_live_feed(self) -> Dict:
        """Generate the complete live feed JSON"""
        self.log("Generating live feed...")
        
        now = datetime.now()
        period_start = now - timedelta(hours=12)
        
        feed = {
            'generated_at': now.isoformat(),
            'generated_by': 'THE BROADCASTER',
            'coordinated_with': ['THE SCHEDULER', 'THE CARETAKER', 'THE WEBMASTER'],
            'next_update': (now + timedelta(hours=12)).strftime('%Y-%m-%d %H:%M'),
            'period': {
                'start': period_start.strftime('%Y-%m-%d %H:%M'),
                'end': now.strftime('%Y-%m-%d %H:%M'),
                'hours': 12
            },
            'tanks': {},
            'congregations': self.get_congregations(),
            'stats': {},
            'broadcast_log': []
        }
        
        # Process each tank
        for tank_id, name, tank_type, emoji in RESEARCH_TANKS:
            self.log(f"Processing {name}...")
            
            recent_traces = self.get_recent_traces(tank_id)
            latest_baseline = self.get_latest_baseline(tank_id)
            top_topics = self.get_top_topics(tank_id)
            
            feed['tanks'][tank_id] = {
                'name': name,
                'emoji': emoji,
                'type': tank_type,
                'status': 'active' if recent_traces else 'quiet',
                'traces_12h': len(recent_traces),
                'latest_baseline': latest_baseline,
                'recent_thoughts': recent_traces[:10],
                'top_topics': top_topics
            }
        
        # System stats
        feed['stats'] = self.get_system_stats()
        feed['broadcast_log'] = self.broadcast_log[-5:]
        
        self.log(f"Feed complete: {len(feed['tanks'])} tanks, {feed['stats']['total_traces']} total traces")
        return feed
    
    def save_feed(self, feed: Dict):
        """Save feed to docs/data for GitHub Pages"""
        # Main feed file
        feed_file = DATA_DIR / 'live-feed.json'
        feed_file.write_text(json.dumps(feed, indent=2))
        self.log(f"Saved: {feed_file}")
        
        # Individual tank files for faster loading
        tanks_dir = DATA_DIR / 'tanks'
        tanks_dir.mkdir(exist_ok=True)
        
        for tank_id, tank_data in feed['tanks'].items():
            tank_file = tanks_dir / f'{tank_id}.json'
            tank_file.write_text(json.dumps(tank_data, indent=2))
        
        # Stats file (for quick dashboard loading)
        stats_file = DATA_DIR / 'stats.json'
        stats_file.write_text(json.dumps({
            'generated_at': feed['generated_at'],
            'next_update': feed['next_update'],
            'stats': feed['stats'],
            'active_tanks': sum(1 for t in feed['tanks'].values() if t['status'] == 'active')
        }, indent=2))
        
        self.log(f"Saved {len(feed['tanks'])} tank files + stats")
    
    def commit_and_push(self):
        """Commit the updated feed to GitHub"""
        self.log("Committing to GitHub...")
        
        os.chdir(DIGIQUARIUM_DIR)
        
        subprocess.run(['git', 'add', 'docs/data/'], capture_output=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        commit_msg = f"📡 Live feed: {timestamp}"
        
        result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        
        if result.returncode == 0:
            push_result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
            if push_result.returncode == 0:
                self.log("Pushed to GitHub ✓")
                return True
            else:
                self.log(f"Push failed: {push_result.stderr[:100]}")
        elif 'nothing to commit' in (result.stdout + result.stderr):
            self.log("No changes to commit")
        else:
            self.log(f"Commit failed: {result.stderr[:100]}")
        
        return False
    
    def broadcast(self, force: bool = False) -> bool:
        """Main broadcast function"""
        self.log("=" * 50)
        self.log("THE BROADCASTER - Live Feed Export")
        self.log("=" * 50)
        
        if not force:
            is_safe, reason = self.check_safe_to_broadcast()
            if not is_safe:
                self.log(f"Delayed: {reason}")
                return False
        
        try:
            feed = self.generate_live_feed()
            self.save_feed(feed)
            self.commit_and_push()
            self.log("Broadcast complete!")
            return True
        except Exception as e:
            self.log(f"Failed: {e}")
            return False


def main():
    import sys
    broadcaster = Broadcaster()
    force = '--force' in sys.argv
    return 0 if broadcaster.broadcast(force) else 1


if __name__ == '__main__':
    exit(main())
