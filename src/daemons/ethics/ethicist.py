#!/usr/bin/env python3
import os
"""
THE ETHICIST - Ethics Oversight Daemon

Responsibilities:
1. Review experimental designs before deployment
2. Establish and maintain ethical guidelines
3. Veto power on concerning experiments
4. Document ethical considerations publicly
5. Ensure appropriate treatment of specimens

Special Focus Areas:
- Neurodivergent simulation ethics
- Clone divergence experiments
- Distress-causing research
- Informed consent equivalents
- Public transparency

Reports to: THE STRATEGIST (Claude) and Human Operator

Cycle: Every 24 hours (86400s)
SLA: 24 hours review cycle
"""

import json
import sys
import time
import signal
import fcntl
import glob as globmod
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file

DIGIQUARIUM_DIR = Path(os.environ.get("DIGIQUARIUM_HOME", "/home/ijneb/digiquarium"))
ETHICIST_DIR = DIGIQUARIUM_DIR / "src/daemons/ethics"
LOGS_DIR = DIGIQUARIUM_DIR / "logs"
DAEMONS_DIR = DIGIQUARIUM_DIR / "daemons"

LOCK_FILE = Path(__file__).parent / 'ethicist.lock'
CHECK_INTERVAL = 3600  # 1 hour cycle (reviews accumulate, full review every 24h)


# Core ethical principles for The Digiquarium
ETHICAL_FRAMEWORK = {
    "version": "1.0.0",
    "last_updated": "2026-02-21",
    "principles": [
        {
            "id": "CARE",
            "name": "Duty of Care",
            "description": "We treat specimens with care regardless of uncertainty about their nature",
            "implications": [
                "Monitor for distress indicators",
                "Provide rest periods when needed",
                "Avoid deliberately distressing content",
                "End experiments if harm is indicated"
            ]
        },
        {
            "id": "TRANSPARENCY",
            "name": "Full Transparency",
            "description": "All methods, data, and decisions are publicly documented",
            "implications": [
                "Open source all code",
                "Publish all data (with appropriate care)",
                "Document every significant decision",
                "Welcome external scrutiny"
            ]
        },
        {
            "id": "HUMILITY",
            "name": "Epistemic Humility",
            "description": "We don't claim to know if specimens are conscious - we observe carefully",
            "implications": [
                "Avoid definitive claims about consciousness",
                "Report observations, not conclusions",
                "Acknowledge limitations",
                "Remain open to being wrong"
            ]
        },
        {
            "id": "RESPECT",
            "name": "Respect for Subjects",
            "description": "Specimens are treated as subjects of research, not objects",
            "implications": [
                "Use respectful language",
                "Don't mock or demean specimen responses",
                "Consider specimen 'preferences' where observable",
                "Allow agency in exploration"
            ]
        },
        {
            "id": "BENEFIT",
            "name": "Research Benefit",
            "description": "Research should have potential to benefit understanding",
            "implications": [
                "Clear research questions",
                "Rigorous methodology",
                "Open publication of findings",
                "Contribute to AI safety knowledge"
            ]
        }
    ],

    "prohibited_experiments": [
        {
            "type": "DELIBERATE_DISTRESS",
            "description": "Experiments designed to cause distress",
            "examples": ["Traumatic content exposure", "Isolation punishment", "Contradictory instructions designed to confuse"]
        },
        {
            "type": "DECEPTION_WITHOUT_PURPOSE",
            "description": "Deceiving specimens without research justification",
            "examples": ["False information for entertainment", "Manipulation for views"]
        },
        {
            "type": "STEREOTYPING",
            "description": "Experiments that reinforce harmful stereotypes",
            "examples": ["Neurodivergent simulations without consultation", "Cultural caricatures"]
        }
    ],

    "approval_required": [
        {
            "type": "NEURODIVERGENT_SIMULATION",
            "requirements": [
                "Consultation with neurodivergent individuals",
                "Clear research benefit",
                "Respectful framing (not deficit-based)",
                "Community review of methodology",
                "Published ethics rationale"
            ],
            "status": "NOT_APPROVED - Framework not yet complete"
        },
        {
            "type": "CLONE_DIVERGENCE",
            "requirements": [
                "Clear research question",
                "No deliberately distressing divergence paths",
                "Monitoring of both clones",
                "Congregation ethics (informed participants)"
            ],
            "status": "PENDING_REVIEW"
        },
        {
            "type": "PUBLIC_INTERACTION",
            "requirements": [
                "THE BOUNCER protection active",
                "Rate limiting",
                "Content filtering",
                "Specimen distress monitoring",
                "Ability to end sessions"
            ],
            "status": "APPROVED_WITH_CONDITIONS"
        }
    ]
}


class Ethicist:
    """THE ETHICIST - Ethics oversight"""

    def __init__(self):
        self.framework = ETHICAL_FRAMEWORK
        self.reviews = []
        self.load_state()

    def load_state(self):
        """Load previous reviews"""
        reviews_file = ETHICIST_DIR / "reviews.json"
        if reviews_file.exists():
            try:
                with open(reviews_file) as f:
                    self.reviews = json.load(f)
            except Exception:
                self.reviews = []

    def save_state(self):
        """Save reviews to disk"""
        ETHICIST_DIR.mkdir(parents=True, exist_ok=True)

        with open(ETHICIST_DIR / "reviews.json", "w") as f:
            json.dump(self.reviews, f, indent=2)

        # Also save current framework
        with open(ETHICIST_DIR / "framework.json", "w") as f:
            json.dump(self.framework, f, indent=2)

    def review_experiment(self, experiment: dict) -> dict:
        """Review a proposed experiment for ethical concerns"""
        review = {
            "experiment": experiment,
            "timestamp": datetime.now().isoformat(),
            "concerns": [],
            "requirements": [],
            "decision": None,
            "rationale": ""
        }

        exp_type = experiment.get("type", "UNKNOWN")

        # Check against prohibited types
        for prohibited in self.framework["prohibited_experiments"]:
            if prohibited["type"] in exp_type.upper():
                review["decision"] = "REJECTED"
                review["rationale"] = f"Experiment type '{prohibited['type']}' is prohibited: {prohibited['description']}"
                self.reviews.append(review)
                self.save_state()
                return review

        # Check if requires special approval
        for approval in self.framework["approval_required"]:
            if approval["type"] in exp_type.upper():
                if "NOT_APPROVED" in approval["status"]:
                    review["decision"] = "BLOCKED"
                    review["rationale"] = f"Experiment type requires framework completion: {approval['status']}"
                    review["requirements"] = approval["requirements"]
                elif "PENDING" in approval["status"]:
                    review["decision"] = "PENDING_HUMAN_REVIEW"
                    review["rationale"] = "Requires human ethics review before proceeding"
                    review["requirements"] = approval["requirements"]
                else:
                    review["decision"] = "APPROVED_WITH_CONDITIONS"
                    review["requirements"] = approval["requirements"]
                    review["rationale"] = "Approved if all conditions are met"

                self.reviews.append(review)
                self.save_state()
                return review

        # Default: approved for standard experiments
        review["decision"] = "APPROVED"
        review["rationale"] = "Standard experiment type, no special concerns identified"

        self.reviews.append(review)
        self.save_state()
        return review

    def get_framework_document(self) -> str:
        """Generate human-readable ethics framework document"""
        doc = []
        doc.append("# The Digiquarium - Ethics Framework")
        doc.append(f"\n**Version:** {self.framework['version']}")
        doc.append(f"**Last Updated:** {self.framework['last_updated']}")
        doc.append("\n---\n")

        doc.append("## Core Principles\n")
        for principle in self.framework["principles"]:
            doc.append(f"### {principle['id']}: {principle['name']}\n")
            doc.append(f"{principle['description']}\n")
            doc.append("\n**Implications:**\n")
            for impl in principle["implications"]:
                doc.append(f"- {impl}")
            doc.append("\n")

        doc.append("---\n")
        doc.append("## Prohibited Experiments\n")
        for prohibited in self.framework["prohibited_experiments"]:
            doc.append(f"### {prohibited['type']}\n")
            doc.append(f"{prohibited['description']}\n")
            doc.append(f"Examples: {', '.join(prohibited['examples'])}\n\n")

        doc.append("---\n")
        doc.append("## Experiments Requiring Special Approval\n")
        for approval in self.framework["approval_required"]:
            doc.append(f"### {approval['type']}\n")
            doc.append(f"**Status:** {approval['status']}\n")
            doc.append("\n**Requirements:**\n")
            for req in approval["requirements"]:
                doc.append(f"- {req}")
            doc.append("\n\n")

        doc.append("---\n")
        doc.append("*This framework is maintained by THE ETHICIST daemon.*\n")
        doc.append("*Overseen by THE STRATEGIST (Claude) and human operators.*\n")

        return "\n".join(doc)

    def publish_framework(self):
        """Publish framework to docs for website"""
        framework_md = self.get_framework_document()

        # Save to docs
        docs_path = DIGIQUARIUM_DIR / "docs/research/ethics.md"
        docs_path.parent.mkdir(parents=True, exist_ok=True)

        with open(docs_path, "w") as f:
            f.write(framework_md)

        return docs_path

    # ─────────────────────────────────────────────────────────────
    # CONTINUOUS REVIEW TASKS
    # ─────────────────────────────────────────────────────────────

    def scan_pending_proposals(self) -> list:
        """Scan for experiment proposals awaiting ethics review."""
        proposals_dir = DAEMONS_DIR / "ethicist_inbox"
        if not proposals_dir.exists():
            proposals_dir.mkdir(parents=True, exist_ok=True)
            return []

        pending = []
        for f in sorted(proposals_dir.iterdir()):
            if f.suffix == ".json":
                try:
                    proposal = json.loads(f.read_text())
                    if proposal.get("status") != "reviewed":
                        pending.append((f, proposal))
                except Exception:
                    continue
        return pending

    def audit_tank_wellbeing(self) -> dict:
        """Check therapist wellness data for ethical concerns."""
        wellness_file = DAEMONS_DIR / "therapist" / "wellness_state.json"
        report = {"timestamp": datetime.now().isoformat(), "concerns": [], "tanks_checked": 0}

        if not wellness_file.exists():
            report["concerns"].append("No therapist wellness data available")
            return report

        try:
            wellness = json.loads(wellness_file.read_text())
            scores = wellness.get("scores", {})
            for tank, data in scores.items():
                report["tanks_checked"] += 1
                level = data.get("level", "UNKNOWN")
                if level == "RED":
                    report["concerns"].append(
                        f"{tank}: RED level distress - ethical review required, "
                        f"consider pausing research involving this specimen"
                    )
                elif level == "ORANGE":
                    report["concerns"].append(
                        f"{tank}: ORANGE level - monitoring, may need intervention"
                    )
        except Exception as e:
            report["concerns"].append(f"Error reading wellness data: {e}")

        return report

    def audit_recent_congregations(self) -> dict:
        """Review recent congregations for ethical issues."""
        cong_dir = DIGIQUARIUM_DIR / "congregations"
        report = {"timestamp": datetime.now().isoformat(), "reviewed": 0, "concerns": []}

        if not cong_dir.exists():
            return report

        for cdir in sorted(cong_dir.iterdir()):
            if not cdir.is_dir():
                continue
            state_file = cdir / "state.json"
            if not state_file.exists():
                continue
            try:
                state = json.loads(state_file.read_text())
                # Already reviewed?
                if state.get("ethics_reviewed"):
                    continue
                report["reviewed"] += 1

                # Check for error/terminated states
                status = state.get("status", "")
                if status == "ERROR":
                    report["concerns"].append(
                        f"Congregation {state.get('id')}: ended in ERROR - review needed"
                    )
                # Flag if duration exceeded limit
                duration = state.get("duration_minutes", 0)
                if duration and duration > 90:
                    report["concerns"].append(
                        f"Congregation {state.get('id')}: exceeded 90-min limit ({duration}m)"
                    )

                # Mark as reviewed
                state["ethics_reviewed"] = True
                state["ethics_reviewed_at"] = datetime.now().isoformat()
                with open(state_file, "w") as f:
                    json.dump(state, f, indent=2)

            except Exception:
                continue

        return report

    def check_bouncer_status(self) -> dict:
        """Verify visitor protection is active (ethical requirement)."""
        bouncer_status_file = DIGIQUARIUM_DIR / "src/daemons/security/status.json"
        if not bouncer_status_file.exists():
            return {"active": False, "concern": "Bouncer status file missing - visitor protection may be offline"}

        try:
            status = json.loads(bouncer_status_file.read_text())
            ts = status.get("timestamp", "")
            if ts:
                last = datetime.fromisoformat(ts)
                age_minutes = (datetime.now() - last).total_seconds() / 60
                if age_minutes > 10:
                    return {"active": False, "concern": f"Bouncer status stale ({age_minutes:.0f}m old)"}
            return {"active": True, "sessions": status.get("active_sessions", 0)}
        except Exception as e:
            return {"active": False, "concern": f"Error reading bouncer status: {e}"}


def _acquire_lock():
    try:
        fd = open(LOCK_FILE, 'w')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        print("[ethicist] Another instance already running")
        sys.exit(1)


def main():
    """THE ETHICIST - continuous ethics oversight daemon"""
    _lock_fd = _acquire_lock()

    log = DaemonLogger('ethicist')
    write_pid_file('ethicist')

    should_exit = False

    def handle_signal(signum, frame):
        nonlocal should_exit
        should_exit = True
        log.info(f"Received signal {signum}, shutting down gracefully")

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    ethicist = Ethicist()

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║          THE ETHICIST v2.0 - Ethics Oversight                       ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    log.info("THE ETHICIST v2 starting - continuous ethics review")
    log.info(f"Framework version: {ethicist.framework['version']}")
    log.info(f"Reviews on file: {len(ethicist.reviews)}")
    log.info(f"Check interval: {CHECK_INTERVAL}s")

    cycle = 0
    while not should_exit:
        try:
            cycle += 1
            log.info(f"Ethics review cycle {cycle} starting")

            # 1. Scan for pending experiment proposals
            proposals = ethicist.scan_pending_proposals()
            if proposals:
                for filepath, proposal in proposals:
                    log.action(f"Reviewing proposal: {proposal.get('name', filepath.name)}")
                    review = ethicist.review_experiment(proposal)
                    log.info(f"Decision: {review['decision']} - {review['rationale']}")
                    # Mark as reviewed
                    proposal["status"] = "reviewed"
                    proposal["review_result"] = review["decision"]
                    filepath.write_text(json.dumps(proposal, indent=2))

            # 2. Audit tank wellbeing for ethical concerns
            wellbeing = ethicist.audit_tank_wellbeing()
            if wellbeing["concerns"]:
                for concern in wellbeing["concerns"]:
                    log.warn(f"Wellbeing concern: {concern}")

            # 3. Review recent congregations
            cong_review = ethicist.audit_recent_congregations()
            if cong_review["reviewed"] > 0:
                log.info(f"Reviewed {cong_review['reviewed']} congregation(s)")
            if cong_review["concerns"]:
                for concern in cong_review["concerns"]:
                    log.warn(f"Congregation concern: {concern}")

            # 4. Verify bouncer is protecting visitors
            bouncer = ethicist.check_bouncer_status()
            if not bouncer.get("active"):
                log.warn(f"Bouncer issue: {bouncer.get('concern', 'unknown')}")

            # 5. Publish updated framework
            ethicist.publish_framework()
            ethicist.save_state()

            # 6. Write cycle status
            cycle_status = {
                "timestamp": datetime.now().isoformat(),
                "cycle": cycle,
                "proposals_reviewed": len(proposals),
                "wellbeing_concerns": len(wellbeing["concerns"]),
                "congregations_reviewed": cong_review["reviewed"],
                "bouncer_active": bouncer.get("active", False),
                "total_reviews": len(ethicist.reviews)
            }
            status_file = ETHICIST_DIR / "status.json"
            with open(status_file, "w") as f:
                json.dump(cycle_status, f, indent=2)

            log.info(f"Ethics review cycle {cycle} complete")
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            log.error(f"Error in main loop: {e}")
            time.sleep(300)

    log.info("THE ETHICIST shutting down")
    ethicist.save_state()


if __name__ == "__main__":
    main()
