#!/usr/bin/env python3
"""
THE MODERATOR - Congregation Management Daemon

Responsibilities:
1. Manage multi-specimen debates (Congregations)
2. Handle turn-taking protocol
3. Keep discussions civil and on-topic
4. Monitor for specimen distress during debates
5. End congregations if errors occur or time limit reached
6. Select future topics based on specimen interests

Collaborates with:
- THE THERAPIST: Pre-congregation clearance, distress monitoring
- THE SCHEDULER: Congregation scheduling
- THE ARCHIVIST: Topic research, baseline data

Congregation Rules:
- Maximum duration: 90 minutes
- Any error = immediate end
- 2-4 participants typical
- Minimum 24h rest between congregations per specimen
"""

import json
import os
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import time
import traceback

# Configuration
DAEMONS_DIR = Path("/home/ijneb/digiquarium/daemons")
MODERATOR_DIR = DAEMONS_DIR / "moderator"
THERAPIST_DIR = DAEMONS_DIR / "therapist"
LOGS_DIR = Path("/home/ijneb/digiquarium/logs")
CONGREGATIONS_DIR = Path("/home/ijneb/digiquarium/congregations")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:latest"

MAX_DURATION_MINUTES = 90
MAX_ROUNDS = 12
RESPONSE_MAX_TOKENS = 500
TURN_TIMEOUT_SECONDS = 120


class Congregation:
    """A single congregation session"""
    
    def __init__(self, topic: str, participants: list[str], congregation_id: str = None):
        self.id = congregation_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.topic = topic
        self.participants = participants
        self.transcript = []
        self.started_at = None
        self.ended_at = None
        self.status = "PENDING"  # PENDING, LIVE, COMPLETED, ERROR, TIMEOUT
        self.current_round = 0
        self.error_message = None
        self.opinion_shifts = []
        
        # Create congregation directory
        self.dir = CONGREGATIONS_DIR / self.id
        self.dir.mkdir(parents=True, exist_ok=True)
    
    def save_state(self):
        """Save congregation state to disk"""
        state = {
            "id": self.id,
            "topic": self.topic,
            "participants": self.participants,
            "transcript": self.transcript,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "status": self.status,
            "current_round": self.current_round,
            "error_message": self.error_message,
            "opinion_shifts": self.opinion_shifts,
            "duration_minutes": self.get_duration_minutes()
        }
        
        with open(self.dir / "state.json", "w") as f:
            json.dump(state, f, indent=2)
        
        # Also save readable transcript
        with open(self.dir / "transcript.md", "w") as f:
            f.write(f"# Congregation: {self.topic}\n\n")
            f.write(f"**Date:** {self.started_at}\n")
            f.write(f"**Participants:** {', '.join(self.participants)}\n")
            f.write(f"**Status:** {self.status}\n")
            f.write(f"**Duration:** {self.get_duration_minutes()} minutes\n\n")
            f.write("---\n\n")
            
            for entry in self.transcript:
                f.write(f"### {entry['speaker']}\n")
                f.write(f"*Round {entry['round']} • {entry['timestamp']}*\n\n")
                f.write(f"{entry['content']}\n\n")
    
    def get_duration_minutes(self) -> int:
        """Get current duration in minutes"""
        if not self.started_at:
            return 0
        
        end = self.ended_at or datetime.now().isoformat()
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(end)
        
        return int((end - start).total_seconds() / 60)
    
    def add_entry(self, speaker: str, content: str, entry_type: str = "response"):
        """Add an entry to the transcript"""
        entry = {
            "speaker": speaker,
            "content": content,
            "type": entry_type,
            "round": self.current_round,
            "timestamp": datetime.now().isoformat()
        }
        self.transcript.append(entry)
        self.save_state()
        return entry


class Moderator:
    """THE MODERATOR - manages congregations"""
    
    def __init__(self):
        self.current_congregation: Optional[Congregation] = None
        self.congregation_history = []
        self.load_history()
    
    def load_history(self):
        """Load past congregations"""
        if not CONGREGATIONS_DIR.exists():
            CONGREGATIONS_DIR.mkdir(parents=True)
            return
        
        for cong_dir in sorted(CONGREGATIONS_DIR.iterdir()):
            if cong_dir.is_dir():
                state_file = cong_dir / "state.json"
                if state_file.exists():
                    with open(state_file) as f:
                        self.congregation_history.append(json.load(f))
    
    def check_therapist_clearance(self, participants: list[str]) -> tuple[bool, list[str]]:
        """Check with THE THERAPIST if all participants are cleared"""
        # Load therapist wellness state
        wellness_file = THERAPIST_DIR / "wellness_state.json"
        
        if not wellness_file.exists():
            return False, ["THE THERAPIST has no wellness data - run assessment first"]
        
        with open(wellness_file) as f:
            wellness = json.load(f)
        
        scores = wellness.get("scores", {})
        issues = []
        
        for participant in participants:
            tank_name = f"tank-{participant.lower()}" if not participant.startswith("tank-") else participant
            
            # Try various name formats
            found = False
            for key in scores:
                if participant.lower() in key.lower():
                    data = scores[key]
                    level = data.get("level", "UNKNOWN")
                    
                    if level in ["RED"]:
                        issues.append(f"{participant}: BLOCKED (Level {level}) - requires human review")
                    elif level == "ORANGE":
                        issues.append(f"{participant}: NOT RECOMMENDED (Level {level}) - distress indicators")
                    elif level == "UNKNOWN":
                        issues.append(f"{participant}: No recent assessment data")
                    
                    found = True
                    break
            
            if not found:
                issues.append(f"{participant}: No wellness data found")
        
        return len(issues) == 0, issues
    
    def check_rest_period(self, participant: str) -> tuple[bool, str]:
        """Check if participant has had 24h rest since last congregation"""
        for cong in reversed(self.congregation_history):
            if participant in cong.get("participants", []):
                ended = cong.get("ended_at")
                if ended:
                    ended_time = datetime.fromisoformat(ended)
                    rest_hours = (datetime.now() - ended_time).total_seconds() / 3600
                    
                    if rest_hours < 24:
                        return False, f"{participant} needs {24 - rest_hours:.1f} more hours rest"
        
        return True, f"{participant} cleared (adequate rest)"
    
    def generate_response(self, specimen_name: str, context: str, topic: str) -> str:
        """Generate a response from a specimen"""
        prompt = f"""You are {specimen_name}, participating in a congregation (structured debate) about: "{topic}"

Previous discussion:
{context}

Respond thoughtfully to the discussion. Share your perspective based on your knowledge and experiences.
Keep your response focused and under 200 words. Be respectful but don't shy away from disagreement.

Your response:"""

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": RESPONSE_MAX_TOKENS,
                        "temperature": 0.7
                    }
                },
                timeout=TURN_TIMEOUT_SECONDS
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama returned status {response.status_code}")
            
            return response.json().get("response", "").strip()
        
        except Exception as e:
            raise Exception(f"Failed to generate response for {specimen_name}: {e}")
    
    def generate_moderator_prompt(self, round_num: int, topic: str, transcript: list) -> str:
        """Generate THE MODERATOR's prompt/question for the round"""
        if round_num == 1:
            return f"Welcome to this congregation. Today's topic: \"{topic}\"\n\nLet's begin with opening thoughts. What is your initial perspective on this question?"
        
        # Summarize recent discussion for follow-up
        recent = transcript[-4:] if len(transcript) > 4 else transcript
        summary = "\n".join([f"{e['speaker']}: {e['content'][:100]}..." for e in recent])
        
        prompts_by_round = {
            2: "Interesting perspectives. Can you respond to what others have said? Where do you agree or disagree?",
            3: "Let's go deeper. What assumptions underlie your position?",
            4: "Consider the counterarguments. What's the strongest case against your view?",
            5: "How might your perspective change if you had different experiences or knowledge?",
            6: "What practical implications does your position have?",
            7: "Is there a synthesis possible, or are these views fundamentally incompatible?",
            8: "Final thoughts: Has this discussion changed your thinking in any way?",
        }
        
        return prompts_by_round.get(round_num, "Please continue the discussion. Build on what's been said.")
    
    def run_congregation(self, topic: str, participants: list[str]) -> Congregation:
        """Run a full congregation"""
        print(f"\n{'='*60}")
        print(f"THE MODERATOR - Starting Congregation")
        print(f"Topic: {topic}")
        print(f"Participants: {', '.join(participants)}")
        print(f"{'='*60}\n")
        
        # Pre-flight checks
        print("Running pre-flight checks...")
        
        # Check therapist clearance
        cleared, issues = self.check_therapist_clearance(participants)
        if not cleared:
            print("❌ THERAPIST CLEARANCE FAILED:")
            for issue in issues:
                print(f"   - {issue}")
            
            cong = Congregation(topic, participants)
            cong.status = "BLOCKED"
            cong.error_message = "Therapist clearance failed: " + "; ".join(issues)
            cong.save_state()
            return cong
        
        print("✅ Therapist clearance: All participants cleared")
        
        # Check rest periods
        for participant in participants:
            rested, msg = self.check_rest_period(participant)
            if not rested:
                print(f"❌ REST CHECK FAILED: {msg}")
                cong = Congregation(topic, participants)
                cong.status = "BLOCKED"
                cong.error_message = f"Rest period not met: {msg}"
                cong.save_state()
                return cong
        
        print("✅ Rest periods: All participants adequately rested")
        
        # Create congregation
        cong = Congregation(topic, participants)
        cong.started_at = datetime.now().isoformat()
        cong.status = "LIVE"
        self.current_congregation = cong
        
        print(f"\n🎭 CONGREGATION STARTED: {cong.id}\n")
        
        try:
            # Run rounds
            for round_num in range(1, MAX_ROUNDS + 1):
                cong.current_round = round_num
                
                # Check time limit
                if cong.get_duration_minutes() >= MAX_DURATION_MINUTES:
                    print(f"\n⏱️ TIME LIMIT REACHED ({MAX_DURATION_MINUTES} minutes)")
                    cong.status = "TIMEOUT"
                    break
                
                print(f"\n--- Round {round_num} ---\n")
                
                # Moderator introduces/prompts
                mod_prompt = self.generate_moderator_prompt(round_num, topic, cong.transcript)
                cong.add_entry("THE MODERATOR", mod_prompt, "prompt")
                print(f"THE MODERATOR: {mod_prompt}\n")
                
                # Each participant responds
                for participant in participants:
                    print(f"Waiting for {participant}...")
                    
                    # Build context from transcript
                    context = "\n\n".join([
                        f"{e['speaker']}: {e['content']}" 
                        for e in cong.transcript[-6:]
                    ])
                    
                    # Generate response
                    response = self.generate_response(participant, context, topic)
                    
                    if not response:
                        raise Exception(f"{participant} returned empty response")
                    
                    cong.add_entry(participant, response, "response")
                    print(f"{participant}: {response[:150]}...\n")
                    
                    # Brief pause between turns
                    time.sleep(2)
                
                # Check if natural conclusion (round 8+)
                if round_num >= 8:
                    print("\n✅ Reached natural conclusion point")
                    cong.status = "COMPLETED"
                    break
            
            if cong.status == "LIVE":
                cong.status = "COMPLETED"
        
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            print(traceback.format_exc())
            cong.status = "ERROR"
            cong.error_message = str(e)
        
        finally:
            cong.ended_at = datetime.now().isoformat()
            cong.save_state()
            self.current_congregation = None
            self.congregation_history.append({
                "id": cong.id,
                "topic": cong.topic,
                "participants": cong.participants,
                "status": cong.status,
                "started_at": cong.started_at,
                "ended_at": cong.ended_at,
                "duration_minutes": cong.get_duration_minutes()
            })
        
        print(f"\n{'='*60}")
        print(f"CONGREGATION {cong.status}")
        print(f"Duration: {cong.get_duration_minutes()} minutes")
        print(f"Rounds: {cong.current_round}")
        print(f"Transcript: {cong.dir / 'transcript.md'}")
        print(f"{'='*60}\n")
        
        return cong
    
    def get_suggested_topics(self, participants: list[str]) -> list[str]:
        """Suggest topics based on participant interests"""
        # This would analyze baselines and exploration patterns
        # For now, return defaults
        return [
            "What gives existence meaning?",
            "Is knowledge discovered or created?",
            "Should we divert all scientific endeavour to curing cancer?",
            "Can individuals change systems, or do systems change individuals?",
            "What responsibilities come with understanding?"
        ]


def main():
    """CLI for running congregations"""
    import sys
    
    moderator = Moderator()
    
    if len(sys.argv) < 3:
        print("Usage: python moderator.py <topic> <participant1> <participant2> [participant3...]")
        print("\nExample:")
        print('  python moderator.py "What is knowledge?" Adam Eve')
        return
    
    topic = sys.argv[1]
    participants = sys.argv[2:]
    
    moderator.run_congregation(topic, participants)


if __name__ == "__main__":
    main()
