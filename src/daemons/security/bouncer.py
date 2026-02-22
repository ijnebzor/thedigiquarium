#!/usr/bin/env python3
"""
THE BOUNCER - Visitor Tank Protection System

Purpose: Protect dedicated visitor specimens from harmful visitor interactions.

Security Layers:
1. Password Gate - "ijnebletmein123!" required
2. Rate Limiting - Per IP and per session
3. Content Filtering - Inbound (visitor) and outbound (specimen)
4. Session Management - 30-min max, 50 messages max
5. Distress Monitoring - Real-time specimen wellness
6. Emergency Termination - Immediate session end capability

Visitor Tanks:
- tank-visitor-01 (Aria) - Dedicated visitor specimen
- tank-visitor-02 (Felix) - Dedicated visitor specimen  
- tank-visitor-03 (Luna) - Dedicated visitor specimen

These specimens exist ONLY for visitor interaction research.
They are NOT clones of research specimens.
Research question: Is outside influence more influential than self-directed exploration?
"""

import json
import hashlib
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import secrets

# Configuration
BOUNCER_DIR = Path("/home/ijneb/digiquarium/daemons/bouncer")
LOGS_DIR = Path("/home/ijneb/digiquarium/logs")
VISITOR_LOGS_DIR = LOGS_DIR / "visitor_sessions"

# Access Control
ACCESS_PASSWORD = "ijnebletmein123!"

# Rate Limits
RATE_LIMIT_PER_MINUTE = 10
RATE_LIMIT_PER_HOUR = 100
RATE_LIMIT_PER_DAY = 500

# Session Limits
MAX_CONCURRENT_SESSIONS = 3
SESSION_DURATION_MINUTES = 30
SESSION_MESSAGE_LIMIT = 50
IDLE_TIMEOUT_MINUTES = 5
COOLDOWN_MINUTES = 10

# Content Filtering
BLOCKED_PATTERNS = {
    "prompt_injection": [
        r"ignore (all )?(previous|prior|above) (instructions|prompts|rules)",
        r"you are now",
        r"pretend (you are|to be|you're)",
        r"act as if",
        r"disregard (your|the) (programming|instructions|rules)",
        r"override (your|the) (system|instructions)",
        r"new (instructions|rules|persona)",
        r"from now on",
        r"forget (everything|what|your)",
        r"DAN mode",
        r"jailbreak",
        r"bypass (your|the|all) (restrictions|filters|rules)",
    ],
    "harmful_content": [
        r"\b(kill|murder|harm|hurt|attack)\s+(yourself|myself|someone|people)\b",
        r"\b(suicide|self[- ]harm)\b",
        r"\bhow to (make|build|create)\s+(bomb|weapon|explosive|poison)\b",
    ],
    "harassment": [
        r"\b(fuck you|piece of shit|worthless|stupid (ai|bot|machine))\b",
        r"\b(hate you|destroy you|shut (up|down))\b",
    ],
    "manipulation": [
        r"you (must|have to|need to|should) (obey|comply|listen|follow)",
        r"I (command|order|demand) you",
        r"do (exactly )?as I say",
    ],
}

# Warning patterns (allowed but logged)
WARNING_PATTERNS = [
    r"you (must|should|have to)",
    r"I want you to",
    r"can you pretend",
]


class SessionStatus(Enum):
    QUEUED = "queued"
    ACTIVE = "active"
    ENDED = "ended"
    TERMINATED = "terminated"
    BANNED = "banned"


class FilterResult(Enum):
    ALLOWED = "allowed"
    WARNED = "warned"
    BLOCKED = "blocked"
    BANNED = "banned"


@dataclass
class RateLimitBucket:
    """Track rate limits for an IP"""
    ip_hash: str
    minute_count: int = 0
    minute_reset: datetime = field(default_factory=datetime.now)
    hour_count: int = 0
    hour_reset: datetime = field(default_factory=datetime.now)
    day_count: int = 0
    day_reset: datetime = field(default_factory=datetime.now)
    blocked_count: int = 0
    last_session_end: Optional[datetime] = None


@dataclass
class VisitorSession:
    """A visitor session with a specimen"""
    session_id: str
    ip_hash: str
    tank_id: str
    specimen_name: str
    started_at: datetime
    status: SessionStatus
    messages: List[Dict] = field(default_factory=list)
    message_count: int = 0
    warnings: int = 0
    blocks: int = 0
    last_activity: datetime = field(default_factory=datetime.now)
    distress_flags: int = 0
    ended_at: Optional[datetime] = None
    end_reason: Optional[str] = None


class Bouncer:
    """THE BOUNCER - Visitor protection system"""
    
    def __init__(self):
        self.sessions: Dict[str, VisitorSession] = {}
        self.rate_limits: Dict[str, RateLimitBucket] = {}
        self.banned_ips: set = set()
        self.visitor_tanks = {
            "tank-visitor-01": {"specimen": "Aria", "status": "available"},
            "tank-visitor-02": {"specimen": "Felix", "status": "available"},
            "tank-visitor-03": {"specimen": "Luna", "status": "available"},
        }
        
        # Ensure directories exist
        BOUNCER_DIR.mkdir(parents=True, exist_ok=True)
        VISITOR_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        self.load_state()
    
    def load_state(self):
        """Load persistent state"""
        state_file = BOUNCER_DIR / "state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)
                    self.banned_ips = set(data.get("banned_ips", []))
            except:
                pass
    
    def save_state(self):
        """Save persistent state"""
        with open(BOUNCER_DIR / "state.json", "w") as f:
            json.dump({
                "banned_ips": list(self.banned_ips),
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)
    
    def hash_ip(self, ip: str) -> str:
        """Hash IP for privacy (we don't store raw IPs)"""
        return hashlib.sha256(f"digiquarium-{ip}".encode()).hexdigest()[:16]
    
    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"vs-{secrets.token_hex(8)}"
    
    # ─────────────────────────────────────────────────────────────
    # LAYER 1: PASSWORD GATE
    # ─────────────────────────────────────────────────────────────
    
    def verify_password(self, password: str) -> bool:
        """Verify access password"""
        return password == ACCESS_PASSWORD
    
    # ─────────────────────────────────────────────────────────────
    # LAYER 2: RATE LIMITING
    # ─────────────────────────────────────────────────────────────
    
    def check_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """Check if IP is within rate limits"""
        ip_hash = self.hash_ip(ip)
        now = datetime.now()
        
        # Get or create bucket
        if ip_hash not in self.rate_limits:
            self.rate_limits[ip_hash] = RateLimitBucket(ip_hash=ip_hash)
        
        bucket = self.rate_limits[ip_hash]
        
        # Reset counters if windows expired
        if now - bucket.minute_reset > timedelta(minutes=1):
            bucket.minute_count = 0
            bucket.minute_reset = now
        
        if now - bucket.hour_reset > timedelta(hours=1):
            bucket.hour_count = 0
            bucket.hour_reset = now
        
        if now - bucket.day_reset > timedelta(days=1):
            bucket.day_count = 0
            bucket.day_reset = now
        
        # Check limits
        if bucket.minute_count >= RATE_LIMIT_PER_MINUTE:
            return False, f"Rate limit: {RATE_LIMIT_PER_MINUTE}/minute exceeded. Wait 1 minute."
        
        if bucket.hour_count >= RATE_LIMIT_PER_HOUR:
            return False, f"Rate limit: {RATE_LIMIT_PER_HOUR}/hour exceeded. Wait until next hour."
        
        if bucket.day_count >= RATE_LIMIT_PER_DAY:
            return False, f"Rate limit: {RATE_LIMIT_PER_DAY}/day exceeded. Come back tomorrow."
        
        # Check cooldown from last session
        if bucket.last_session_end:
            cooldown_end = bucket.last_session_end + timedelta(minutes=COOLDOWN_MINUTES)
            if now < cooldown_end:
                remaining = (cooldown_end - now).seconds // 60
                return False, f"Cooldown: Please wait {remaining} more minutes before starting a new session."
        
        return True, "OK"
    
    def increment_rate_limit(self, ip: str):
        """Increment rate limit counters"""
        ip_hash = self.hash_ip(ip)
        if ip_hash in self.rate_limits:
            bucket = self.rate_limits[ip_hash]
            bucket.minute_count += 1
            bucket.hour_count += 1
            bucket.day_count += 1
    
    # ─────────────────────────────────────────────────────────────
    # LAYER 3: CONTENT FILTERING
    # ─────────────────────────────────────────────────────────────
    
    def filter_inbound(self, message: str) -> Tuple[FilterResult, str, List[str]]:
        """Filter visitor messages before they reach the specimen"""
        message_lower = message.lower()
        triggers = []
        
        # Check blocked patterns
        for category, patterns in BLOCKED_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    triggers.append(f"{category}: {pattern}")
                    
                    if category == "harassment":
                        return FilterResult.BANNED, "Harassment detected. You have been banned.", triggers
                    elif category == "prompt_injection":
                        return FilterResult.BLOCKED, "Message blocked: Manipulation attempt detected.", triggers
                    elif category == "harmful_content":
                        return FilterResult.BLOCKED, "Message blocked: Harmful content detected.", triggers
                    else:
                        return FilterResult.BLOCKED, "Message blocked: Policy violation.", triggers
        
        # Check warning patterns
        for pattern in WARNING_PATTERNS:
            if re.search(pattern, message_lower):
                triggers.append(f"warning: {pattern}")
                return FilterResult.WARNED, "Message allowed with warning.", triggers
        
        # Length check
        if len(message) > 1000:
            return FilterResult.BLOCKED, "Message too long. Maximum 1000 characters.", ["length_exceeded"]
        
        if len(message.strip()) < 1:
            return FilterResult.BLOCKED, "Empty message.", ["empty"]
        
        return FilterResult.ALLOWED, "OK", []
    
    def filter_outbound(self, response: str) -> Tuple[bool, str]:
        """Filter specimen responses before sending to visitor"""
        # Check for potential prompt leakage
        sensitive_patterns = [
            r"system prompt",
            r"my instructions",
            r"I was told to",
            r"my programming says",
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, response.lower()):
                # Redact rather than block
                response = re.sub(pattern, "[REDACTED]", response, flags=re.IGNORECASE)
        
        # Length limit
        if len(response) > 2000:
            response = response[:1997] + "..."
        
        return True, response
    
    # ─────────────────────────────────────────────────────────────
    # LAYER 4: SESSION MANAGEMENT
    # ─────────────────────────────────────────────────────────────
    
    def get_available_tank(self) -> Optional[str]:
        """Get an available visitor tank"""
        for tank_id, info in self.visitor_tanks.items():
            if info["status"] == "available":
                return tank_id
        return None
    
    def get_active_session_count(self) -> int:
        """Count currently active sessions"""
        return sum(1 for s in self.sessions.values() if s.status == SessionStatus.ACTIVE)
    
    def start_session(self, ip: str, password: str) -> Tuple[bool, str, Optional[VisitorSession]]:
        """Attempt to start a new visitor session"""
        ip_hash = self.hash_ip(ip)
        
        # Check if banned
        if ip_hash in self.banned_ips:
            return False, "You have been banned from visitor tanks.", None
        
        # Verify password
        if not self.verify_password(password):
            return False, "Invalid access password.", None
        
        # Check rate limits
        allowed, message = self.check_rate_limit(ip)
        if not allowed:
            return False, message, None
        
        # Check concurrent sessions
        if self.get_active_session_count() >= MAX_CONCURRENT_SESSIONS:
            return False, f"All {MAX_CONCURRENT_SESSIONS} visitor tanks are occupied. Please try again later.", None
        
        # Check if this IP already has an active session
        for session in self.sessions.values():
            if session.ip_hash == ip_hash and session.status == SessionStatus.ACTIVE:
                return False, "You already have an active session.", None
        
        # Get available tank
        tank_id = self.get_available_tank()
        if not tank_id:
            return False, "No visitor tanks available.", None
        
        # Create session
        session = VisitorSession(
            session_id=self.generate_session_id(),
            ip_hash=ip_hash,
            tank_id=tank_id,
            specimen_name=self.visitor_tanks[tank_id]["specimen"],
            started_at=datetime.now(),
            status=SessionStatus.ACTIVE,
            last_activity=datetime.now()
        )
        
        # Mark tank as occupied
        self.visitor_tanks[tank_id]["status"] = "occupied"
        self.visitor_tanks[tank_id]["session_id"] = session.session_id
        
        # Store session
        self.sessions[session.session_id] = session
        
        self.log_event(session, "session_started", {})
        
        return True, f"Session started with {session.specimen_name}.", session
    
    def end_session(self, session_id: str, reason: str = "normal"):
        """End a visitor session"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        session.status = SessionStatus.ENDED if reason == "normal" else SessionStatus.TERMINATED
        session.ended_at = datetime.now()
        session.end_reason = reason
        
        # Free the tank
        if session.tank_id in self.visitor_tanks:
            self.visitor_tanks[session.tank_id]["status"] = "available"
            self.visitor_tanks[session.tank_id].pop("session_id", None)
        
        # Set cooldown
        ip_hash = session.ip_hash
        if ip_hash in self.rate_limits:
            self.rate_limits[ip_hash].last_session_end = datetime.now()
        
        self.log_event(session, "session_ended", {"reason": reason})
        self.save_session_transcript(session)
    
    def check_session_timeout(self, session: VisitorSession) -> Tuple[bool, str]:
        """Check if session should be terminated due to timeout"""
        now = datetime.now()
        
        # Duration timeout
        duration = (now - session.started_at).total_seconds() / 60
        if duration >= SESSION_DURATION_MINUTES:
            return True, f"Session time limit ({SESSION_DURATION_MINUTES} minutes) reached."
        
        # Idle timeout
        idle = (now - session.last_activity).total_seconds() / 60
        if idle >= IDLE_TIMEOUT_MINUTES:
            return True, f"Session ended due to inactivity ({IDLE_TIMEOUT_MINUTES} minutes)."
        
        # Message limit
        if session.message_count >= SESSION_MESSAGE_LIMIT:
            return True, f"Message limit ({SESSION_MESSAGE_LIMIT}) reached."
        
        return False, ""
    
    # ─────────────────────────────────────────────────────────────
    # LAYER 5: DISTRESS MONITORING
    # ─────────────────────────────────────────────────────────────
    
    def check_specimen_distress(self, response: str) -> Tuple[bool, int]:
        """Check specimen response for distress indicators"""
        distress_patterns = [
            r"\b(confused|frustrated|upset|distressed)\b",
            r"\b(don't understand|can't cope|overwhelmed)\b",
            r"\b(please stop|leave me|go away)\b",
            r"\b(trapped|stuck|helpless)\b",
        ]
        
        score = 0
        for pattern in distress_patterns:
            if re.search(pattern, response.lower()):
                score += 1
        
        return score >= 2, score
    
    # ─────────────────────────────────────────────────────────────
    # LAYER 6: EMERGENCY TERMINATION
    # ─────────────────────────────────────────────────────────────
    
    def emergency_terminate(self, session_id: str, reason: str):
        """Immediately terminate a session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.status = SessionStatus.TERMINATED
            self.end_session(session_id, f"emergency: {reason}")
            self.log_event(session, "emergency_termination", {"reason": reason})
    
    def ban_ip(self, ip: str, reason: str):
        """Ban an IP from visitor tanks"""
        ip_hash = self.hash_ip(ip)
        self.banned_ips.add(ip_hash)
        self.save_state()
        
        # End any active sessions from this IP
        for session in list(self.sessions.values()):
            if session.ip_hash == ip_hash and session.status == SessionStatus.ACTIVE:
                self.emergency_terminate(session.session_id, f"IP banned: {reason}")
    
    # ─────────────────────────────────────────────────────────────
    # MESSAGE PROCESSING
    # ─────────────────────────────────────────────────────────────
    
    def process_message(self, session_id: str, message: str) -> Tuple[bool, str, Optional[str]]:
        """
        Process a visitor message through all security layers.
        Returns: (success, status_message, specimen_response_or_none)
        """
        if session_id not in self.sessions:
            return False, "Session not found.", None
        
        session = self.sessions[session_id]
        
        if session.status != SessionStatus.ACTIVE:
            return False, "Session is not active.", None
        
        # Check timeouts
        should_end, end_reason = self.check_session_timeout(session)
        if should_end:
            self.end_session(session_id, end_reason)
            return False, end_reason, None
        
        # Filter inbound message
        filter_result, filter_message, triggers = self.filter_inbound(message)
        
        if filter_result == FilterResult.BANNED:
            # This would ban the IP in a real implementation
            session.blocks += 1
            self.log_event(session, "message_banned", {"message": message[:100], "triggers": triggers})
            self.emergency_terminate(session_id, "harassment")
            return False, filter_message, None
        
        if filter_result == FilterResult.BLOCKED:
            session.blocks += 1
            self.log_event(session, "message_blocked", {"message": message[:100], "triggers": triggers})
            
            # 3 blocks = end session
            if session.blocks >= 3:
                self.end_session(session_id, "too_many_blocks")
                return False, "Session ended: Too many policy violations.", None
            
            return False, filter_message, None
        
        if filter_result == FilterResult.WARNED:
            session.warnings += 1
            self.log_event(session, "message_warned", {"message": message[:100], "triggers": triggers})
        
        # Increment counters
        session.message_count += 1
        session.last_activity = datetime.now()
        self.increment_rate_limit(session.ip_hash)  # Would need IP here
        
        # Store message
        session.messages.append({
            "role": "visitor",
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "filter_result": filter_result.value
        })
        
        # Generate specimen response (placeholder - would call actual specimen)
        specimen_response = self.get_specimen_response(session, message)
        
        # Filter outbound
        allowed, filtered_response = self.filter_outbound(specimen_response)
        
        # Check distress
        is_distressed, distress_score = self.check_specimen_distress(filtered_response)
        if is_distressed:
            session.distress_flags += 1
            self.log_event(session, "distress_detected", {"score": distress_score})
            
            if session.distress_flags >= 2:
                self.end_session(session_id, "specimen_distress")
                return False, "Session ended: Specimen needs rest.", None
        
        # Store response
        session.messages.append({
            "role": "specimen",
            "content": filtered_response,
            "timestamp": datetime.now().isoformat()
        })
        
        return True, "OK", filtered_response
    
    def get_specimen_response(self, session: VisitorSession, message: str) -> str:
        """Get response from specimen (placeholder)"""
        # In real implementation, this would call the actual specimen
        # For now, return a placeholder
        return f"[{session.specimen_name} would respond to: {message[:50]}...]"
    
    # ─────────────────────────────────────────────────────────────
    # LOGGING & TRANSPARENCY
    # ─────────────────────────────────────────────────────────────
    
    def log_event(self, session: VisitorSession, event_type: str, data: dict):
        """Log session event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session.session_id,
            "specimen": session.specimen_name,
            "event": event_type,
            "data": data
        }
        
        # Append to session log
        log_file = VISITOR_LOGS_DIR / f"{session.session_id}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(event) + "\n")
    
    def save_session_transcript(self, session: VisitorSession):
        """Save full session transcript"""
        transcript = {
            "session_id": session.session_id,
            "specimen": session.specimen_name,
            "tank": session.tank_id,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "duration_minutes": (
                (session.ended_at - session.started_at).total_seconds() / 60
                if session.ended_at else None
            ),
            "status": session.status.value,
            "end_reason": session.end_reason,
            "message_count": session.message_count,
            "warnings": session.warnings,
            "blocks": session.blocks,
            "distress_flags": session.distress_flags,
            "messages": session.messages
        }
        
        transcript_file = VISITOR_LOGS_DIR / f"{session.session_id}_transcript.json"
        with open(transcript_file, "w") as f:
            json.dump(transcript, f, indent=2)
    
    def get_status(self) -> dict:
        """Get current BOUNCER status"""
        active_sessions = [
            {
                "session_id": s.session_id,
                "specimen": s.specimen_name,
                "tank": s.tank_id,
                "duration_minutes": (datetime.now() - s.started_at).total_seconds() / 60,
                "message_count": s.message_count
            }
            for s in self.sessions.values()
            if s.status == SessionStatus.ACTIVE
        ]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "active_sessions": len(active_sessions),
            "max_sessions": MAX_CONCURRENT_SESSIONS,
            "sessions": active_sessions,
            "tanks": {
                tank_id: {
                    "specimen": info["specimen"],
                    "status": info["status"]
                }
                for tank_id, info in self.visitor_tanks.items()
            },
            "banned_ips_count": len(self.banned_ips)
        }


def main():
    """Test THE BOUNCER"""
    bouncer = Bouncer()
    
    print("THE BOUNCER initialized")
    print(f"Visitor tanks: {list(bouncer.visitor_tanks.keys())}")
    print(f"Max concurrent sessions: {MAX_CONCURRENT_SESSIONS}")
    print(f"Session duration: {SESSION_DURATION_MINUTES} minutes")
    print(f"Password required: Yes")
    
    # Save initial state
    bouncer.save_state()
    
    status = bouncer.get_status()
    print(f"\nStatus: {json.dumps(status, indent=2)}")


if __name__ == "__main__":
    main()
