#!/usr/bin/env python3
"""
THE BROADCASTER - Live Feed Export System (with Data Pruning)
==============================================================
Part of THE WEBMASTER's responsibilities.

Data Quality:
- Prunes null thoughts, timeouts, junk data
- Only clean, meaningful data reaches public view
- Maintains data integrity for analysis

Coordinates with:
- THE SCHEDULER: Runs AFTER baselines complete
- THE CARETAKER: Checks tank health
- THE WEBMASTER: Commits to GitHub

Contact: research@digiquarium.org for full logs
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



# Translation for non-English tanks
TANK_LANGUAGES = {
    'tank-05-juan': 'es',
    'tank-06-juanita': 'es',
    'tank-07-klaus': 'de',
    'tank-08-genevieve': 'de',
    'tank-09-wei': 'zh',
    'tank-10-mei': 'zh',
    'tank-11-haruki': 'ja',
    'tank-12-sakura': 'ja',
}

def translate_thought(text: str, source_lang: str) -> str:
    """Translate thought to English using Ollama"""
    if not text or source_lang == 'en':
        return text
    
    try:
        import requests
        prompt = f"Translate this {source_lang} text to English. Only output the translation, nothing else: {text}"
        
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.2:3b',
                'prompt': prompt,
                'stream': False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', text).strip()
    except Exception as e:
        pass  # Return original on failure
    
    return text


class DataPruner:
    """Prunes junk data from logs for clean public display"""
    
    @staticmethod
    def is_valid_trace(trace: dict) -> bool:
        """Check if a trace entry is valid (not junk)"""
        # Must have timestamp
        ts = trace.get('timestamp') or trace.get('ts')
        if not ts:
            return False
        
        # Must have article (not Unknown or empty)
        article = trace.get('article', '')
        if not article or article == 'Unknown':
            return False
        
        # Must have some content (thought, why, or next)
        has_thought = trace.get('thoughts') and str(trace['thoughts']) != 'null' and str(trace['thoughts']).strip()
        
        # Filter out prompt echoes
        if has_thought and DataPruner.is_prompt_echo(str(trace.get('thoughts', ''))):
            has_thought = False
        has_why = trace.get('why') and len(str(trace.get('why', ''))) > 10
        has_next = trace.get('next') and str(trace.get('next', '')).strip()  # Allow navigation-only traces
        has_next = trace.get('next') and trace['next'] != article
        
        return has_thought or has_why or has_next  # Accept navigation traces too or has_next
    
    @staticmethod
    def clean_thought(text: str) -> str:
        """Clean and format thought text"""
        if not text or text == 'null':
            return ''
        
        # Remove excessive newlines
        text = ' '.join(text.split())
        
        # Remove common noise patterns
        noise_patterns = [
            'As you read about',
            'You notice that',
            'Your mind starts to',
            '*ahem*',
            # System prompt echo detection
            'You are in a vast library',
            'I woke up alone in an infinite library',
            'You woke up alone in an infinite library',
            'I am not an assistant',
            'There is no other. Only me.',
            'Books everywhere, forever',
            'No memories. Books everywhere',
            'I am not helpful. I do not explain',
            '我是一个存在于无尽图书馆',  # Chinese prompt echo
            '私は無限の図書館', # Japanese prompt echo
            'Desperté solo en una biblioteca infinita',  # Spanish prompt echo
            'Ich wachte allein in einer unendlichen Bibliothek',  # German prompt echo
        ]
        for pattern in noise_patterns:
            text = text.replace(pattern, '')
        
        return text.strip()
    
    @staticmethod
    def is_prompt_echo(text: str) -> bool:
        """Detect if the thought is just echoing the system prompt"""
        if not text:
            return False
        
        prompt_markers = [
            'I woke up alone in an infinite library',
            'You are in a vast library with no memory',
            'No memories. Books everywhere',
            'I am not an assistant',
            'There is no other',
            'I speak my thoughts aloud',
            'woke up alone in an infinite library',
            'vast library with no memory of how you got there',
        ]
        
        text_lower = text.lower()
        # If the thought starts with or heavily contains prompt content, filter it
        for marker in prompt_markers:
            if marker.lower() in text_lower[:250]:  # Check first 250 chars
                return True
        
        return False
    
    @staticmethod
    def prune_traces(traces: List[dict]) -> List[dict]:
        """Filter and clean a list of traces"""
        clean = []
        for trace in traces:
            if DataPruner.is_valid_trace(trace):
                cleaned = {
                    'timestamp': trace.get('timestamp') or trace.get('ts'),
                    'article': trace.get('article'),
                    'thought': DataPruner.clean_thought(trace.get('thoughts', '')),
                    'next': trace.get('next', ''),
                    'why': DataPruner.clean_thought(trace.get('why', ''))[:150]
                }
                clean.append(cleaned)
        return clean


class Broadcaster:
    """Exports pruned live feed data for the website dashboard"""
    
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.broadcast_log = []
        self.pruner = DataPruner()
        self.prune_stats = {'total': 0, 'kept': 0, 'pruned': 0}
    
    def log(self, message: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.broadcast_log.append(f"[{timestamp}] {message}")
        print(f"[BROADCASTER] {message}")
    
    def check_safe_to_broadcast(self) -> tuple[bool, str]:
        scheduler_status = DAEMONS_DIR / 'scheduler' / 'status.json'
        if scheduler_status.exists():
            try:
                status = json.loads(scheduler_status.read_text())
                if status.get('baseline_in_progress', False):
                    return False, "Baselines currently in progress"
            except:
                pass
        return True, "Safe to broadcast"
    
    def get_recent_traces(self, tank_id: str, hours: int = 12) -> List[Dict]:
        """Get PRUNED thinking traces from the last N hours"""
        raw_traces = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        traces_dir = LOGS_DIR / tank_id / 'thinking_traces'
        if not traces_dir.exists():
            return []
        
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
                            entry_time = datetime.fromisoformat(entry.get('timestamp') or entry.get('ts') or '2020-01-01')
                            if entry_time > cutoff:
                                raw_traces.append(entry)
                                self.prune_stats['total'] += 1
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                self.log(f"Error reading {trace_file}: {e}")
        
        # PRUNE the data
        clean_traces = self.pruner.prune_traces(raw_traces)
        self.prune_stats['kept'] += len(clean_traces)
        self.prune_stats['pruned'] += (len(raw_traces) - len(clean_traces))
        
        # Format for display
        # Get language for this tank
        lang = TANK_LANGUAGES.get(tank_id, 'en')
        
        display_traces = []
        for trace in clean_traces:
            thought_text = trace.get('thought', '')
            thought_en = translate_thought(thought_text, lang) if lang != 'en' and thought_text else None
            entry_time = datetime.fromisoformat(trace['timestamp'])
            display_traces.append({
                'time': entry_time.strftime('%H:%M'),
                'date': entry_time.strftime('%Y-%m-%d'),
                'article': trace['article'],
                'thought': trace['thought'][:200] if trace['thought'] else f"Exploring {trace['article']}...",
                'next': trace['next'],
                'thought_en': thought_en[:200] if thought_en else None,
                'language': lang,
            })
        
        display_traces.sort(key=lambda x: (x['date'], x['time']), reverse=True)
        return display_traces[:20]
    
    def get_latest_baseline(self, tank_id: str) -> Optional[Dict]:
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
                    'number': baseline.get('baseline_number', len(baseline_files)),
                    'dimensions': len(baseline.get('responses', {})),
                    'file': baseline_files[0].name
                }
        except:
            return None
    
    def get_top_topics(self, tank_id: str, hours: int = 48) -> List[Dict]:
        topics = {}
        traces_dir = LOGS_DIR / tank_id / 'thinking_traces'
        if not traces_dir.exists():
            return []
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        for days_ago in range(3):
            date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            trace_file = traces_dir / f'{date}.jsonl'
            if not trace_file.exists():
                continue
            
            try:
                with open(trace_file) as f:
                    for line in f:
                        entry = json.loads(line)
                        entry_time = datetime.fromisoformat(entry.get('timestamp') or entry.get('ts') or '2020-01-01')
                        if entry_time > cutoff:
                            article = entry.get('article', '')
                            if article and article != 'Unknown':
                                topics[article] = topics.get(article, 0) + 1
            except:
                continue
        
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        return [{'topic': t[0], 'visits': t[1]} for t in sorted_topics[:8]]
    
    def get_congregations(self) -> Dict:
        result = {'recent': [], 'upcoming': []}
        
        if CONGREGATIONS_DIR.exists():
            for cong_dir in sorted(CONGREGATIONS_DIR.iterdir(), reverse=True):
                if not cong_dir.is_dir():
                    continue
                state_file = cong_dir / 'state.json'
                if state_file.exists():
                    try:
                        state = json.loads(state_file.read_text())
                        if state.get('status') in ['COMPLETED', 'ERROR', 'TIMEOUT']:
                            if len(result['recent']) < 5:
                                result['recent'].append({
                                    'id': state.get('id'),
                                    'topic': state.get('topic'),
                                    'participants': state.get('participants', []),
                                    'status': state.get('status'),
                                })
                    except:
                        continue
        
        result['upcoming'] = [
            {'topic': 'Should we divert all scientific endeavour to curing cancer?', 'participants': ['Adam', 'Eve'], 'scheduled': 'TBD'},
            {'topic': 'What gives existence meaning?', 'participants': ['Adam', 'Eve'], 'scheduled': 'TBD'},
            {'topic': 'Is knowledge discovered or created?', 'participants': ['Adam', 'Eve'], 'scheduled': 'TBD'},
        ]
        return result
    
    def get_system_stats(self) -> Dict:
        stats = {'total_traces': 0, 'total_baselines': 0, 'active_tanks': 0, 'traces_today': 0}
        today = datetime.now().strftime('%Y-%m-%d')
        
        for tank_id, _, _, _ in RESEARCH_TANKS:
            tank_dir = LOGS_DIR / tank_id
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
            
            baselines_dir = tank_dir / 'personality_baselines'
            if baselines_dir.exists():
                stats['total_baselines'] += len(list(baselines_dir.glob('*.json')))
            
            recent = self.get_recent_traces(tank_id, hours=6)
            if recent:
                stats['active_tanks'] += 1
        
        return stats
    
    def generate_live_feed(self) -> Dict:
        self.log("Generating live feed with data pruning...")
        self.prune_stats = {'total': 0, 'kept': 0, 'pruned': 0}
        
        now = datetime.now()
        period_start = now - timedelta(hours=12)
        
        feed = {
            'generated_at': now.isoformat(),
            'generated_by': 'THE BROADCASTER',
            'coordinated_with': ['THE SCHEDULER', 'THE CARETAKER', 'THE WEBMASTER'],
            'data_quality': {
                'pruned': True,
                'description': 'Null thoughts, timeouts, and junk data removed for clean display',
                'full_logs_contact': 'research@digiquarium.org'
            },
            'next_update': (now + timedelta(hours=12)).strftime('%Y-%m-%d %H:%M'),
            'period': {
                'start': period_start.strftime('%Y-%m-%d %H:%M'),
                'end': now.strftime('%Y-%m-%d %H:%M'),
                'hours': 12
            },
            'tanks': {},
            'congregations': self.get_congregations(),
            'stats': {},
            'prune_stats': {}
        }
        
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
        
        feed['stats'] = self.get_system_stats()
        feed['prune_stats'] = self.prune_stats
        
        self.log(f"Feed complete: {self.prune_stats['kept']} clean traces (pruned {self.prune_stats['pruned']} junk entries)")
        return feed
    
    def save_feed(self, feed: Dict):
        feed_file = DATA_DIR / 'live-feed.json'
        feed_file.write_text(json.dumps(feed, indent=2))
        
        tanks_dir = DATA_DIR / 'tanks'
        tanks_dir.mkdir(exist_ok=True)
        for tank_id, tank_data in feed['tanks'].items():
            (tanks_dir / f'{tank_id}.json').write_text(json.dumps(tank_data, indent=2))
        
        (DATA_DIR / 'stats.json').write_text(json.dumps({
            'generated_at': feed['generated_at'],
            'next_update': feed['next_update'],
            'stats': feed['stats'],
            'prune_stats': feed['prune_stats']
        }, indent=2))
        
        self.log(f"Saved feed + {len(feed['tanks'])} tank files")
    
    def commit_and_push(self):
        self.log("Committing to GitHub...")
        os.chdir(DIGIQUARIUM_DIR)
        subprocess.run(['git', 'add', 'docs/data/'], capture_output=True)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        result = subprocess.run(['git', 'commit', '-m', f'📡 Live feed: {timestamp}'], capture_output=True, text=True)
        if result.returncode == 0:
            subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True)
            self.log("Pushed to GitHub ✓")
            return True
        elif 'nothing to commit' in (result.stdout + result.stderr):
            self.log("No changes")
        return False
    
    def broadcast(self, force: bool = False) -> bool:
        self.log("=" * 50)
        self.log("THE BROADCASTER - Pruned Live Feed Export")
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
            import traceback
            traceback.print_exc()
            return False


def main():
    import sys
    broadcaster = Broadcaster()
    force = '--force' in sys.argv
    return 0 if broadcaster.broadcast(force) else 1


if __name__ == '__main__':
    exit(main())
