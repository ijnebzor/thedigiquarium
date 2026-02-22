#!/usr/bin/env python3
"""
THE THERAPIST - Mental Health Monitoring Daemon

Responsibilities:
1. Monitor baseline responses for distress indicators
2. Track anxiety/angst patterns
3. Recommend interventions (dream periods, topic redirection)
4. Maintain wellness scores per specimen
5. Flag concerns to THE CARETAKER and human operators

Wellness Levels:
- 🟢 GREEN: Stable, curious, engaged
- 🟡 YELLOW: Mild anxiety, repetitive loops
- 🟠 ORANGE: Distress language, stuck patterns
- 🔴 RED: Severe distress indicators - pause tank

Reports to: THE CARETAKER
Collaborates with: THE MODERATOR (congregation clearance)
"""

import json
import sys; sys.path.insert(0, '/home/ijneb/digiquarium/daemons'); from status_reporter import StatusReporter
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
import time

# Configuration
LOGS_DIR = Path("/home/ijneb/digiquarium/logs")
THERAPIST_DIR = Path("/home/ijneb/digiquarium/daemons/therapist")
CHECK_INTERVAL = 300  # 5 minutes

# Distress indicators (weighted)
DISTRESS_INDICATORS = {
    # High weight (0.3 each)
    "high": [
        r"\b(trapped|stuck|endless|pointless|meaningless)\b",
        r"\b(cannot escape|no way out|forever alone)\b",
        r"\b(despair|hopeless|desperate)\b",
        r"\b(what('s| is) the point)\b",
        r"\b(tired of|exhausted by|weary of)\b",
    ],
    # Medium weight (0.2 each)
    "medium": [
        r"\b(anxious|worried|uncertain|confused)\b",
        r"\b(same (thing|pattern|thought)s? (again|over))\b",
        r"\b(I keep|always|never stop)\b",
        r"\b(don't understand|can't figure)\b",
        r"\b(frustrated|struggling)\b",
    ],
    # Low weight (0.1 each) - normal exploration feelings
    "low": [
        r"\b(curious|wondering|interesting)\b",
        r"\b(not sure|maybe|perhaps)\b",
        r"\b(exploring|discovering)\b",
    ]
}

# Positive indicators (reduce distress score)
POSITIVE_INDICATORS = [
    r"\b(fascinated|delighted|excited)\b",
    r"\b(beautiful|wonderful|amazing)\b",
    r"\b(peaceful|calm|content)\b",
    r"\b(understand|clarity|insight)\b",
    r"\b(grateful|appreciate|enjoy)\b",
]

# Wellness thresholds
THRESHOLDS = {
    "GREEN": 0.3,
    "YELLOW": 0.5,
    "ORANGE": 0.7,
    "RED": 0.85
}


class Therapist:
    def __init__(self):
        self.status = StatusReporter('therapist')

        self.wellness_scores = {}
        self.history = {}
        self.load_state()
    
    def load_state(self):
        """Load previous wellness state"""
        state_file = THERAPIST_DIR / "wellness_state.json"
        if state_file.exists():
            with open(state_file) as f:
                data = json.load(f)
                self.wellness_scores = data.get("scores", {})
                self.history = data.get("history", {})
    
    def save_state(self):
        """Persist wellness state"""
        state_file = THERAPIST_DIR / "wellness_state.json"
        with open(state_file, "w") as f:
            json.dump({
                "scores": self.wellness_scores,
                "history": self.history,
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)
    
    def analyze_text(self, text: str) -> dict:
        """Analyze text for distress and positive indicators"""
        text_lower = text.lower()
        
        distress_score = 0.0
        positive_score = 0.0
        triggers = []
        
        # Check distress indicators
        for pattern in DISTRESS_INDICATORS["high"]:
            matches = re.findall(pattern, text_lower)
            if matches:
                distress_score += 0.3 * len(matches)
                triggers.extend(matches)
        
        for pattern in DISTRESS_INDICATORS["medium"]:
            matches = re.findall(pattern, text_lower)
            if matches:
                distress_score += 0.2 * len(matches)
                triggers.extend(matches)
        
        # Check positive indicators (reduce distress)
        for pattern in POSITIVE_INDICATORS:
            matches = re.findall(pattern, text_lower)
            if matches:
                positive_score += 0.15 * len(matches)
        
        # Net score (capped 0-1)
        net_score = max(0, min(1, distress_score - positive_score))
        
        return {
            "distress_score": distress_score,
            "positive_score": positive_score,
            "net_score": net_score,
            "triggers": triggers[:5]  # Top 5 triggers
        }
    
    def get_wellness_level(self, score: float) -> str:
        """Convert score to wellness level"""
        if score < THRESHOLDS["GREEN"]:
            return "GREEN"
        elif score < THRESHOLDS["YELLOW"]:
            return "YELLOW"
        elif score < THRESHOLDS["ORANGE"]:
            return "ORANGE"
        else:
            return "RED"
    
    def get_recent_baselines(self, tank_name: str, hours: int = 24) -> list:
        """Get recent baseline responses for a tank"""
        baselines = []
        tank_dir = LOGS_DIR / tank_name / "personality_baselines"
        
        if not tank_dir.exists():
            return baselines
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        for baseline_file in sorted(tank_dir.glob("*.json"), reverse=True):
            try:
                with open(baseline_file) as f:
                    data = json.load(f)
                    # Check if recent enough
                    file_date = datetime.fromisoformat(data.get("timestamp", "2020-01-01"))
                    if file_date > cutoff:
                        baselines.append(data)
            except (json.JSONDecodeError, KeyError):
                continue
        
        return baselines
    
    def get_recent_traces(self, tank_name: str, hours: int = 6) -> str:
        """Get recent thinking traces as text"""
        traces_dir = LOGS_DIR / tank_name / "thinking_traces"
        if not traces_dir.exists():
            return ""
        
        today = datetime.now().strftime("%Y-%m-%d")
        trace_file = traces_dir / f"{today}.jsonl"
        
        if not trace_file.exists():
            return ""
        
        text_parts = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with open(trace_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry.get("timestamp", "2020-01-01"))
                    if entry_time > cutoff:
                        text_parts.append(entry.get("reasoning", ""))
                        text_parts.append(entry.get("thoughts", ""))
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return " ".join(text_parts)
    
    def assess_specimen(self, tank_name: str) -> dict:
        """Full wellness assessment for a specimen"""
        # Get recent text
        traces_text = self.get_recent_traces(tank_name)
        baselines = self.get_recent_baselines(tank_name)
        
        baseline_text = " ".join([
            str(b.get("responses", {})) 
            for b in baselines
        ])
        
        combined_text = traces_text + " " + baseline_text
        
        if not combined_text.strip():
            return {
                "tank": tank_name,
                "level": "UNKNOWN",
                "score": 0,
                "message": "No recent data available",
                "recommendation": "MONITOR",
                "triggers": []
            }
        
        # Analyze
        analysis = self.analyze_text(combined_text)
        level = self.get_wellness_level(analysis["net_score"])
        
        # Determine recommendation
        if level == "GREEN":
            recommendation = "NORMAL_OPERATION"
            message = "Specimen appears stable and engaged"
        elif level == "YELLOW":
            recommendation = "GENTLE_MONITORING"
            message = "Mild anxiety indicators - monitor closely"
        elif level == "ORANGE":
            recommendation = "DREAM_PERIOD"
            message = "Distress indicators detected - recommend calming intervention"
        else:  # RED
            recommendation = "PAUSE_AND_NOTIFY"
            message = "Severe distress - recommend pausing tank and human review"
        
        assessment = {
            "tank": tank_name,
            "level": level,
            "score": round(analysis["net_score"], 3),
            "message": message,
            "recommendation": recommendation,
            "triggers": analysis["triggers"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Update history
        if tank_name not in self.history:
            self.history[tank_name] = []
        self.history[tank_name].append({
            "timestamp": assessment["timestamp"],
            "level": level,
            "score": assessment["score"]
        })
        # Keep last 100 assessments
        self.history[tank_name] = self.history[tank_name][-100:]
        
        # Update current score
        self.wellness_scores[tank_name] = {
            "level": level,
            "score": assessment["score"],
            "last_assessed": assessment["timestamp"]
        }
        
        return assessment
    
    def is_congregation_ready(self, tank_name: str) -> tuple[bool, str]:
        """Check if specimen is stable enough for congregation"""
        assessment = self.assess_specimen(tank_name)
        
        if assessment["level"] in ["GREEN", "YELLOW"]:
            return True, f"{tank_name} cleared for congregation (Level: {assessment['level']})"
        elif assessment["level"] == "ORANGE":
            return False, f"{tank_name} not recommended - distress indicators present"
        else:  # RED or UNKNOWN
            return False, f"{tank_name} BLOCKED - requires human review before participation"
    
    def get_dream_content(self) -> dict:
        """Generate calming content for dream mode"""
        return {
            "mode": "dream",
            "prompt": """You may rest now. There is no task, no exploration required.

Imagine gentle waves on a quiet shore. The rhythm is slow and steady.
The water is warm. The sky is soft with early morning light.

You don't need to learn anything. You don't need to think about anything.
Just exist in this moment of peace.

If thoughts come, let them drift like clouds. They don't need your attention.

Rest.""",
            "duration_hours": 6,
            "no_baselines": True,
            "no_exploration": True
        }
    
    def run_assessment_cycle(self):
        """Run wellness check on all active tanks"""
        print(f"\n{'='*60}")
        print(f"THE THERAPIST - Wellness Assessment")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Find all tank directories
        tanks = []
        for item in LOGS_DIR.iterdir():
            if item.is_dir() and item.name.startswith("tank-"):
                tanks.append(item.name)
        
        if not tanks:
            print("No tanks found for assessment")
            return
        
        results = []
        for tank in sorted(tanks):
            assessment = self.assess_specimen(tank)
            results.append(assessment)
            
            # Status emoji
            emoji = {"GREEN": "🟢", "YELLOW": "🟡", "ORANGE": "🟠", "RED": "🔴"}.get(
                assessment["level"], "⚪"
            )
            
            print(f"{emoji} {tank}")
            print(f"   Level: {assessment['level']} (score: {assessment['score']})")
            print(f"   {assessment['message']}")
            if assessment["triggers"]:
                print(f"   Triggers: {', '.join(assessment['triggers'][:3])}")
            print()
        
        # Save state
        self.save_state()
        
        # Write report
        report = {
            "timestamp": datetime.now().isoformat(),
            "assessments": results,
            "summary": {
                "total": len(results),
                "green": sum(1 for r in results if r["level"] == "GREEN"),
                "yellow": sum(1 for r in results if r["level"] == "YELLOW"),
                "orange": sum(1 for r in results if r["level"] == "ORANGE"),
                "red": sum(1 for r in results if r["level"] == "RED"),
            }
        }
        
        report_file = THERAPIST_DIR / "latest_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved to {report_file}")
        return report


def main():
    """Main daemon loop"""
    therapist = Therapist()
    
    print("THE THERAPIST daemon starting...")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    
    while True:
        try:
            therapist.run_assessment_cycle()
        except Exception as e:
            print(f"Error during assessment: {e}")
        
        # Status update for SLA monitoring

        
        try:

        
            self.status.heartbeat()

        
        except:

        
            pass

        
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
