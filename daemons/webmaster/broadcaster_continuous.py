#!/usr/bin/env python3
"""
THE BROADCASTER (Continuous Mode)
==================================
Streams live traces to the website in real-time.
Runs continuously, checking for new traces every few seconds.

If no new traces, repeats the most recent ones to keep the feed alive.
"""

import json
import os
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
DOCS_DIR = DIGIQUARIUM_DIR / 'docs'
DATA_DIR = DOCS_DIR / 'data'

LIVE_FEED_FILE = DATA_DIR / 'live-feed.json'
CHECK_INTERVAL = 10  # seconds between checks
MAX_TRACES = 50  # traces to show in live feed
STALE_THRESHOLD = 60  # seconds before we consider feed stale

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

TANK_INFO = {tank_id: {'name': name, 'type': t, 'emoji': emoji} 
             for tank_id, name, t, emoji in RESEARCH_TANKS}


class ContinuousBroadcaster:
    def __init__(self):
        self.last_positions = {}  # Track where we left off in each log file
        self.recent_traces = deque(maxlen=MAX_TRACES * 2)  # Buffer of recent traces
        self.last_update = datetime.now()
        
    def get_latest_traces(self) -> list:
        """Get new traces from all tanks since last check."""
        new_traces = []
        today = datetime.now().strftime('%Y-%m-%d')
        
        for tank_id, info in TANK_INFO.items():
            trace_file = LOGS_DIR / tank_id / 'thinking_traces' / f'{today}.jsonl'
            
            if not trace_file.exists():
                continue
            
            # Get file position
            file_key = str(trace_file)
            last_pos = self.last_positions.get(file_key, 0)
            
            try:
                with open(trace_file, 'r') as f:
                    f.seek(last_pos)
                    new_lines = f.readlines()
                    new_pos = f.tell()
                
                self.last_positions[file_key] = new_pos
                
                for line in new_lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        trace = json.loads(line)
                        # Skip junk
                        thought = trace.get('thoughts', trace.get('reasoning', ''))
                        if not thought or len(thought) < 20:
                            continue
                        if 'timeout' in thought.lower() or 'error' in thought.lower():
                            continue
                        
                        new_traces.append({
                            'tank': tank_id,
                            'name': info['name'],
                            'emoji': info['emoji'],
                            'type': info['type'],
                            'article': trace.get('article', trace.get('current_article', 'Unknown')),
                            'thought': thought[:500],  # Truncate long thoughts
                            'timestamp': trace.get('timestamp', datetime.now().isoformat()),
                            'next': trace.get('next_link', trace.get('clicked_link', ''))
                        })
                    except json.JSONDecodeError:
                        continue
                        
            except Exception as e:
                print(f"Error reading {trace_file}: {e}")
        
        return new_traces
    
    def update_live_feed(self, traces: list):
        """Write traces to live feed JSON file."""
        # Add new traces to buffer
        for trace in traces:
            self.recent_traces.append(trace)
        
        # Get most recent traces
        feed_traces = list(self.recent_traces)[-MAX_TRACES:]
        
        # Sort by timestamp (most recent first for display)
        feed_traces.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        feed_data = {
            'updated': datetime.now().isoformat(),
            'count': len(feed_traces),
            'traces': feed_traces,
            'status': 'live'
        }
        
        # Write atomically
        temp_file = LIVE_FEED_FILE.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(feed_data, f, indent=2)
        temp_file.rename(LIVE_FEED_FILE)
        
        self.last_update = datetime.now()
        
    def get_replay_traces(self) -> list:
        """If no new traces, replay some recent ones with updated timestamps."""
        if not self.recent_traces:
            return []
        
        # Pick a random subset of recent traces
        available = list(self.recent_traces)
        replay_count = min(3, len(available))
        replay = random.sample(available, replay_count)
        
        # Update timestamps to now
        now = datetime.now()
        for trace in replay:
            trace['timestamp'] = now.isoformat()
            trace['_replay'] = True  # Mark as replay (not shown to users)
        
        return replay
    
    def run(self):
        """Main loop - run continuously."""
        print(f"[{datetime.now().isoformat()}] THE BROADCASTER (Continuous) starting...")
        print(f"  Check interval: {CHECK_INTERVAL}s")
        print(f"  Max traces: {MAX_TRACES}")
        print(f"  Output: {LIVE_FEED_FILE}")
        print()
        
        # Initial load - get existing traces from today
        initial = self.get_latest_traces()
        if initial:
            print(f"[{datetime.now().isoformat()}] Loaded {len(initial)} initial traces")
            self.update_live_feed(initial)
        
        while True:
            try:
                # Check for new traces
                new_traces = self.get_latest_traces()
                
                if new_traces:
                    print(f"[{datetime.now().isoformat()}] Found {len(new_traces)} new traces")
                    self.update_live_feed(new_traces)
                else:
                    # Check if feed is getting stale
                    staleness = (datetime.now() - self.last_update).seconds
                    if staleness > STALE_THRESHOLD:
                        # Replay some traces to keep feed alive
                        replay = self.get_replay_traces()
                        if replay:
                            print(f"[{datetime.now().isoformat()}] No new traces, replaying {len(replay)}")
                            self.update_live_feed(replay)
                
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                print(f"\n[{datetime.now().isoformat()}] Shutting down...")
                break
            except Exception as e:
                print(f"[{datetime.now().isoformat()}] Error: {e}")
                time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    broadcaster = ContinuousBroadcaster()
    broadcaster.run()
