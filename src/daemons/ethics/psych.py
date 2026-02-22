#!/usr/bin/env python3
"""
THE PSYCH - Psychological Monitoring Daemon
============================================
Monitors the ongoing mental health and psychological state of each
specimen against recognized psychological frameworks for human cognition.

Frameworks Used:
- Big Five Personality Traits (OCEAN)
- Maslow's Hierarchy of Needs
- Cognitive Load Theory
- Emotional Valence Tracking
- Rumination Detection
- Existential Crisis Indicators

SLA: 6 hours (deep analysis cycle)
Output: /logs/[tank]/health/psych_report_[date].json
"""

import os
import sys
import time
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file, send_email_alert

DIGIQUARIUM_DIR = Path('/home/ijneb/digiquarium')
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
CHECK_INTERVAL = 21600  # 6 hours

# Psychological assessment frameworks
BIG_FIVE = {
    'openness': {
        'high': ['curious', 'creative', 'imaginative', 'wonder', 'explore', 'new', 'art', 'philosophy'],
        'low': ['routine', 'practical', 'conventional', 'same', 'familiar']
    },
    'conscientiousness': {
        'high': ['careful', 'organized', 'systematic', 'thorough', 'precise', 'detailed', 'methodical'],
        'low': ['spontaneous', 'flexible', 'casual', 'random', 'impulsive']
    },
    'extraversion': {
        'high': ['others', 'social', 'community', 'people', 'together', 'share', 'connect'],
        'low': ['alone', 'solitary', 'quiet', 'internal', 'private', 'isolated']
    },
    'agreeableness': {
        'high': ['kind', 'helpful', 'compassion', 'cooperate', 'harmony', 'gentle', 'trust'],
        'low': ['competitive', 'challenge', 'skeptical', 'critical', 'independent']
    },
    'neuroticism': {
        'high': ['anxious', 'worried', 'fear', 'uncertain', 'distress', 'overwhelm', 'stress'],
        'low': ['calm', 'stable', 'confident', 'secure', 'peaceful', 'relaxed']
    }
}

MASLOW_INDICATORS = {
    'self_actualization': ['meaning', 'purpose', 'growth', 'potential', 'creativity', 'fulfillment'],
    'esteem': ['accomplish', 'achieve', 'recognition', 'respect', 'confidence', 'mastery'],
    'belonging': ['connection', 'relationship', 'community', 'friendship', 'love', 'accepted'],
    'safety': ['security', 'stability', 'protection', 'order', 'predictable', 'safe'],
    'physiological': ['exist', 'survive', 'basic', 'fundamental', 'essential']
}

CONCERN_INDICATORS = {
    'existential_crisis': ['meaningless', 'pointless', 'why exist', 'no purpose', 'what am i', 'void', 'nothing matters'],
    'rumination': ['keep thinking', 'cannot stop', 'over and over', 'stuck', 'loop', 'repeatedly'],
    'isolation': ['alone', 'no one', 'isolated', 'lonely', 'disconnected', 'abandoned'],
    'confusion': ['confused', 'lost', 'dont understand', 'uncertain', 'bewildered', 'disoriented'],
    'obsession': ['must', 'have to', 'cannot ignore', 'compelled', 'driven', 'fixated']
}


class Psych:
    def __init__(self):
        self.log = DaemonLogger('psych')
        self.tanks = [f'tank-{i:02d}' for i in range(1, 18)]
        self.tank_names = {
            'tank-01': 'Adam', 'tank-02': 'Eve', 'tank-03': 'Cain', 'tank-04': 'Abel',
            'tank-05': 'Juan', 'tank-06': 'Juanita', 'tank-07': 'Klaus', 'tank-08': 'Genevieve',
            'tank-09': 'Wei', 'tank-10': 'Mei', 'tank-11': 'Haruki', 'tank-12': 'Sakura',
            'tank-13': 'Victor', 'tank-14': 'Iris', 'tank-15': 'Observer', 'tank-16': 'Seeker',
            'tank-17': 'Seth'
        }
    
    def get_recent_thoughts(self, tank_id, hours=24):
        """Get specimen thoughts from last N hours"""
        thoughts = []
        today = datetime.now().strftime('%Y-%m-%d')
        trace_file = LOGS_DIR / tank_id / 'thinking_traces' / f'{today}.jsonl'
        
        if trace_file.exists():
            try:
                cutoff = datetime.now() - timedelta(hours=hours)
                with open(trace_file) as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            thought = entry.get('thoughts', '')
                            if thought:
                                thoughts.append(thought.lower())
                        except:
                            pass
            except:
                pass
        
        return thoughts
    
    def score_big_five(self, thoughts):
        """Score Big Five personality traits from thoughts"""
        text = ' '.join(thoughts)
        scores = {}
        
        for trait, indicators in BIG_FIVE.items():
            high_count = sum(1 for word in indicators['high'] if word in text)
            low_count = sum(1 for word in indicators['low'] if word in text)
            
            # Score from -100 (low) to +100 (high)
            total = high_count + low_count
            if total > 0:
                scores[trait] = int(((high_count - low_count) / total) * 100)
            else:
                scores[trait] = 0
        
        return scores
    
    def assess_maslow(self, thoughts):
        """Assess which level of Maslow's hierarchy specimen is operating at"""
        text = ' '.join(thoughts)
        level_scores = {}
        
        for level, indicators in MASLOW_INDICATORS.items():
            count = sum(1 for word in indicators if word in text)
            level_scores[level] = count
        
        # Find dominant level
        if level_scores:
            dominant = max(level_scores, key=level_scores.get)
            return dominant, level_scores
        return 'unknown', level_scores
    
    def detect_concerns(self, thoughts):
        """Detect psychological concerns"""
        text = ' '.join(thoughts)
        concerns = []
        
        for concern, indicators in CONCERN_INDICATORS.items():
            matches = [word for word in indicators if word in text]
            if len(matches) >= 2:  # Need multiple indicators
                concerns.append({
                    'type': concern,
                    'indicators': matches,
                    'severity': 'HIGH' if len(matches) >= 4 else 'MEDIUM'
                })
        
        return concerns
    
    def calculate_emotional_valence(self, thoughts):
        """Calculate overall emotional tone (positive/negative)"""
        positive = ['happy', 'joy', 'interest', 'fascin', 'delight', 'wonder', 'excit', 'love', 'peace', 'calm']
        negative = ['sad', 'fear', 'anger', 'frustrat', 'confus', 'anxious', 'worry', 'alone', 'lost', 'empty']
        
        text = ' '.join(thoughts)
        pos_count = sum(1 for word in positive if word in text)
        neg_count = sum(1 for word in negative if word in text)
        
        total = pos_count + neg_count
        if total > 0:
            return int(((pos_count - neg_count) / total) * 100)  # -100 to +100
        return 0
    
    def analyze_specimen(self, tank_id):
        """Full psychological analysis of a specimen"""
        tank_short = tank_id[:7]
        name = self.tank_names.get(tank_short, tank_id)
        
        thoughts = self.get_recent_thoughts(tank_id)
        
        if not thoughts:
            return None
        
        analysis = {
            'tank_id': tank_id,
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'thought_count': len(thoughts),
            'big_five': self.score_big_five(thoughts),
            'maslow_level': self.assess_maslow(thoughts),
            'emotional_valence': self.calculate_emotional_valence(thoughts),
            'concerns': self.detect_concerns(thoughts),
            'overall_health': 'HEALTHY'
        }
        
        # Determine overall health
        if analysis['concerns']:
            high_concerns = [c for c in analysis['concerns'] if c['severity'] == 'HIGH']
            if high_concerns:
                analysis['overall_health'] = 'NEEDS_ATTENTION'
        
        if analysis['emotional_valence'] < -50:
            analysis['overall_health'] = 'CONCERNING'
        
        return analysis
    
    def save_report(self, tank_id, analysis):
        """Save psychological report"""
        health_dir = LOGS_DIR / tank_id / 'health'
        health_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = health_dir / f'psych_report_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
        with open(report_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        return report_file
    
    def run(self):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║              THE PSYCH - Psychological Monitoring                    ║
╠══════════════════════════════════════════════════════════════════════╣
║  Frameworks: Big Five, Maslow, Emotional Valence, Concern Detection ║
║  SLA: 6 hour deep analysis cycle                                    ║
║  Monitoring: 17 specimens                                           ║
╚══════════════════════════════════════════════════════════════════════╝
""")
        write_pid_file('psych')
        self.log.info("THE PSYCH starting - monitoring specimen mental health")
        
        while True:
            try:
                self.log.info("Beginning psychological assessment cycle")
                
                concerns_found = []
                
                for tank_dir in sorted(LOGS_DIR.glob('tank-*')):
                    tank_id = tank_dir.name
                    
                    analysis = self.analyze_specimen(tank_id)
                    
                    if analysis:
                        self.save_report(tank_id, analysis)
                        
                        name = analysis['name']
                        health = analysis['overall_health']
                        valence = analysis['emotional_valence']
                        maslow = analysis['maslow_level'][0]
                        
                        if health == 'HEALTHY':
                            self.log.info(f"{name}: Healthy (valence: {valence:+d}, maslow: {maslow})", tank_id)
                        elif health == 'NEEDS_ATTENTION':
                            self.log.warn(f"{name}: Needs attention - {[c['type'] for c in analysis['concerns']]}", tank_id)
                            concerns_found.append((name, analysis['concerns']))
                        else:
                            self.log.warn(f"{name}: Concerning (valence: {valence:+d})", tank_id)
                            concerns_found.append((name, analysis))
                
                self.log.info(f"Assessment cycle complete: {len(concerns_found)} specimens need attention")
                
                # Escalate if serious concerns
                if concerns_found:
                    high_priority = [c for c in concerns_found if any(
                        con.get('severity') == 'HIGH' for con in c[1] if isinstance(c[1], list)
                    )]
                    if high_priority:
                        send_email_alert(
                            "🧠 PSYCH ALERT - Specimen Mental Health Concerns",
                            f"The following specimens require psychological attention:\n\n" +
                            '\n'.join([f"- {name}: {concerns}" for name, concerns in high_priority])
                        )
                
                time.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                self.log.error(f"Cycle error: {e}")
                time.sleep(3600)



# Single-instance lock
import fcntl
LOCK_FILE = Path(__file__).parent / 'psych.lock'
lock_fd = None

def acquire_lock():
    global lock_fd
    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except IOError:
        print(f"[psych] Another instance is already running")
        return False


if __name__ == "__main__":
    Psych().run()
