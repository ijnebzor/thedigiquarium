#!/usr/bin/env python3
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
"""

import json
from datetime import datetime
from pathlib import Path

ETHICIST_DIR = Path("/home/ijneb/digiquarium/daemons/ethicist")


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
            with open(reviews_file) as f:
                self.reviews = json.load(f)
    
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
        docs_path = Path("/home/ijneb/digiquarium/docs/research/ethics.md")
        docs_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(docs_path, "w") as f:
            f.write(framework_md)
        
        print(f"Framework published to {docs_path}")
        return docs_path


def main():
    ethicist = Ethicist()
    
    # Save current framework
    ethicist.save_state()
    
    # Publish to docs
    ethicist.publish_framework()
    
    print("THE ETHICIST initialized")
    print(f"Framework version: {ethicist.framework['version']}")
    print(f"Reviews on file: {len(ethicist.reviews)}")


if __name__ == "__main__":
    main()
