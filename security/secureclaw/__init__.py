"""SecureClaw Security Module for Digiquarium Agent Tanks"""

from pathlib import Path

SKILL_PATH = Path(__file__).parent / "skill.txt"
PLUGIN_PATH = Path(__file__).parent / "plugin.py"

def get_skill_prompt():
    """Return the behavioral skill text to add to system prompts"""
    return SKILL_PATH.read_text()

def run_audit(tank_name: str, code_path: Path, log_dir: Path, system_prompt: str):
    """Run full security audit"""
    from .plugin import SecureClawAudit
    audit = SecureClawAudit(tank_name, log_dir)
    return audit.run_full_audit(code_path, system_prompt)
