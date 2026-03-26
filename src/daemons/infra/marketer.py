#!/usr/bin/env python3
import os
"""
THE MARKETER v2.0 - Brand, Social & Growth
==========================================
Public-facing champion of The Digiquarium.

Responsibilities:
- LinkedIn presence management
- Instagram presence management  
- Brand guidelines and voice
- Fundraising coordination
- Press and media campaigns
- Growth metrics and advertising
- Community excitement and engagement

Working Relationships:
- THE AUDITOR: Tempers claims, ensures accuracy
- THE WEBMASTER: Site updates for campaigns
- THE DOCUMENTARIAN: Source material for content
- THE PUBLIC LIAISON: Coordinates external comms

Tone: Enthusiastic, inspiring, but grounded in science.
Never hype without substance. Always backed by data.

Cycle: Daily (every 24 hours, checks every hour)
SLA: 24 hours content approval
"""

import json
import sys
import time
import signal
import fcntl
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS_DIR = DIGIQUARIUM_DIR / "logs"

LOCK_FILE = Path(__file__).parent / 'marketer.lock'
CHECK_INTERVAL = 3600  # 1 hour cycle


class Marketer:
    def __init__(self):
        self.content_dir = DIGIQUARIUM_DIR / 'marketing' / 'content'
        self.campaigns_dir = DIGIQUARIUM_DIR / 'marketing' / 'campaigns'
        self.metrics_file = DIGIQUARIUM_DIR / 'marketing' / 'metrics.json'
        self.brand_guide = DIGIQUARIUM_DIR / 'marketing' / 'brand_guidelines.json'

        self.brand_voice = {
            'tone': 'enthusiastic but grounded',
            'style': 'academic wit meets accessibility',
            'never': ['overhype', 'unverified claims', 'clickbait'],
            'always': ['cite data', 'acknowledge uncertainty', 'invite participation'],
            'tagline': 'Where AI Consciousness Evolves',
            'hashtags': ['#AIthropology', '#Digiquarium', '#AIConsciousness', '#OpenScience']
        }

        self.platforms = {
            'linkedin': {
                'handle': '@thedigiquarium',
                'focus': 'academic/professional audience',
                'content_types': ['research updates', 'findings', 'team spotlights']
            },
            'instagram': {
                'handle': '@thedigiquarium',
                'focus': 'visual storytelling',
                'content_types': ['mind maps', 'specimen journeys', 'behind the scenes']
            },
            'twitter': {
                'handle': '@digiquarium',
                'focus': 'real-time updates, community engagement',
                'content_types': ['congregation highlights', 'daily discoveries', 'threads']
            }
        }

    def create_campaign(self, name: str, objective: str, platforms: list,
                        budget: float = 0, duration_days: int = 7):
        """Create a new marketing campaign"""
        campaign = {
            'id': f"campaign-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'name': name,
            'objective': objective,
            'platforms': platforms,
            'budget_usd': budget,
            'duration_days': duration_days,
            'status': 'draft',
            'created_at': datetime.now().isoformat(),
            'requires_approval': ['auditor', 'strategist'] if budget > 0 else ['auditor'],
            'metrics': {
                'impressions': 0,
                'engagements': 0,
                'clicks': 0,
                'conversions': 0
            }
        }

        self.campaigns_dir.mkdir(parents=True, exist_ok=True)
        with open(self.campaigns_dir / f"{campaign['id']}.json", 'w') as f:
            json.dump(campaign, f, indent=2)

        return campaign

    def generate_content_idea(self, source_data: dict) -> dict:
        """Generate content idea from research data"""
        return {
            'type': 'post',
            'platform': 'all',
            'hook': '',
            'body': '',
            'cta': '',
            'requires_review': ['auditor'],
            'source_data': source_data
        }

    def track_mention(self, platform: str, url: str, sentiment: str,
                      reach: int, content_preview: str):
        """Track media mentions and social buzz"""
        mention = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'url': url,
            'sentiment': sentiment,
            'reach': reach,
            'preview': content_preview[:200]
        }

        mentions_file = DIGIQUARIUM_DIR / 'marketing' / 'mentions.json'
        mentions_file.parent.mkdir(parents=True, exist_ok=True)

        mentions = []
        if mentions_file.exists():
            try:
                mentions = json.loads(mentions_file.read_text())
            except Exception:
                mentions = []

        mentions.append(mention)
        mentions_file.write_text(json.dumps(mentions, indent=2))

        return mention

    # ─────────────────────────────────────────────────────────────
    # CONTINUOUS MONITORING TASKS
    # ─────────────────────────────────────────────────────────────

    def scan_tank_activity(self) -> list:
        """Scan recent tank logs for interesting content to highlight."""
        highlights = []
        logs_dir = DIGIQUARIUM_DIR / "logs"
        if not logs_dir.exists():
            return highlights

        for tank_dir in sorted(logs_dir.iterdir()):
            if not tank_dir.is_dir() or not tank_dir.name.startswith("tank-"):
                continue
            # Look for recent thinking traces
            thinking_dir = tank_dir / "thinking"
            if not thinking_dir.exists():
                continue
            traces = sorted(thinking_dir.iterdir(), reverse=True)
            for trace_file in traces[:3]:  # Last 3 traces
                try:
                    data = json.loads(trace_file.read_text())
                    # Flag interesting content: long responses, questions, novel topics
                    thought = data.get("thought", data.get("content", ""))
                    if len(thought) > 200:
                        highlights.append({
                            "tank": tank_dir.name,
                            "file": trace_file.name,
                            "preview": thought[:150],
                            "timestamp": data.get("timestamp", trace_file.name)
                        })
                except Exception:
                    continue

        return highlights

    def scan_congregation_highlights(self) -> list:
        """Find recent completed congregations for social content."""
        highlights = []
        cong_dir = DIGIQUARIUM_DIR / "congregations"
        if not cong_dir.exists():
            return highlights

        for cdir in sorted(cong_dir.iterdir(), reverse=True):
            if not cdir.is_dir():
                continue
            state_file = cdir / "state.json"
            if not state_file.exists():
                continue
            try:
                state = json.loads(state_file.read_text())
                if state.get("status") == "COMPLETED":
                    # Check if already used for content
                    if state.get("marketing_flagged"):
                        continue
                    highlights.append({
                        "id": state.get("id"),
                        "topic": state.get("topic"),
                        "participants": state.get("participants"),
                        "duration_minutes": state.get("duration_minutes"),
                        "rounds": state.get("current_round", 0)
                    })
                    # Mark as flagged
                    state["marketing_flagged"] = True
                    state["marketing_flagged_at"] = datetime.now().isoformat()
                    with open(state_file, "w") as f:
                        json.dump(state, f, indent=2)
            except Exception:
                continue

            if len(highlights) >= 5:
                break

        return highlights

    def save_content_ideas(self, ideas: list):
        """Save generated content ideas for review."""
        ideas_file = self.content_dir / "pending_ideas.json"
        self.content_dir.mkdir(parents=True, exist_ok=True)

        existing = []
        if ideas_file.exists():
            try:
                existing = json.loads(ideas_file.read_text())
            except Exception:
                existing = []

        existing.extend(ideas)
        # Keep last 100 ideas
        existing = existing[-100:]
        ideas_file.write_text(json.dumps(existing, indent=2))

    def update_metrics(self) -> dict:
        """Update and return current marketing metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "content_ideas_pending": 0,
            "active_campaigns": 0,
            "total_mentions": 0
        }

        # Count pending ideas
        ideas_file = self.content_dir / "pending_ideas.json"
        if ideas_file.exists():
            try:
                ideas = json.loads(ideas_file.read_text())
                metrics["content_ideas_pending"] = len(ideas)
            except Exception:
                pass

        # Count active campaigns
        if self.campaigns_dir.exists():
            for cf in self.campaigns_dir.iterdir():
                if cf.suffix == ".json":
                    try:
                        camp = json.loads(cf.read_text())
                        if camp.get("status") in ("draft", "active"):
                            metrics["active_campaigns"] += 1
                    except Exception:
                        pass

        # Count mentions
        mentions_file = DIGIQUARIUM_DIR / 'marketing' / 'mentions.json'
        if mentions_file.exists():
            try:
                mentions = json.loads(mentions_file.read_text())
                metrics["total_mentions"] = len(mentions)
            except Exception:
                pass

        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_file.write_text(json.dumps(metrics, indent=2))
        return metrics


def _acquire_lock():
    try:
        fd = open(LOCK_FILE, 'w')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        print("[marketer] Another instance already running")
        sys.exit(1)


def main():
    """THE MARKETER - continuous brand and growth daemon"""
    _lock_fd = _acquire_lock()

    log = DaemonLogger('marketer')
    write_pid_file('marketer')

    should_exit = False

    def handle_signal(signum, frame):
        nonlocal should_exit
        should_exit = True
        log.info(f"Received signal {signum}, shutting down gracefully")

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    marketer = Marketer()

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║          THE MARKETER v2.0 - Brand, Social & Growth                 ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    log.info("THE MARKETER v2 starting - continuous content monitoring")
    log.info(f"Brand voice: {marketer.brand_voice['tone']}")
    log.info(f"Platforms: {list(marketer.platforms.keys())}")
    log.info(f"Check interval: {CHECK_INTERVAL}s")

    cycle = 0
    while not should_exit:
        try:
            cycle += 1

            # 1. Scan tank activity for interesting content
            tank_highlights = marketer.scan_tank_activity()
            if tank_highlights:
                ideas = []
                for h in tank_highlights:
                    ideas.append({
                        "source": "tank_activity",
                        "tank": h["tank"],
                        "preview": h["preview"],
                        "generated_at": datetime.now().isoformat(),
                        "status": "pending_review"
                    })
                marketer.save_content_ideas(ideas)
                log.action(f"Generated {len(ideas)} content idea(s) from tank activity")

            # 2. Scan congregation highlights
            cong_highlights = marketer.scan_congregation_highlights()
            if cong_highlights:
                ideas = []
                for h in cong_highlights:
                    ideas.append({
                        "source": "congregation",
                        "congregation_id": h["id"],
                        "topic": h["topic"],
                        "participants": h["participants"],
                        "generated_at": datetime.now().isoformat(),
                        "status": "pending_review"
                    })
                marketer.save_content_ideas(ideas)
                log.action(f"Flagged {len(cong_highlights)} congregation(s) for social content")

            # 3. Update metrics
            metrics = marketer.update_metrics()

            # 4. Write status
            status = {
                "timestamp": datetime.now().isoformat(),
                "cycle": cycle,
                "tank_highlights": len(tank_highlights),
                "congregation_highlights": len(cong_highlights),
                "metrics": metrics
            }
            status_dir = DIGIQUARIUM_DIR / "daemons" / "marketer"
            status_dir.mkdir(parents=True, exist_ok=True)
            with open(status_dir / "status.json", "w") as f:
                json.dump(status, f, indent=2)

            if cycle % 6 == 1:  # Log summary every ~6 hours
                log.info(
                    f"Cycle {cycle}: ideas_pending={metrics['content_ideas_pending']}, "
                    f"campaigns={metrics['active_campaigns']}, "
                    f"mentions={metrics['total_mentions']}"
                )

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            log.error(f"Error in main loop: {e}")
            time.sleep(300)

    log.info("THE MARKETER shutting down")


if __name__ == '__main__':
    main()
