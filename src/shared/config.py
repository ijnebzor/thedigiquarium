"""Configuration utilities."""
import os
import yaml
import json
from pathlib import Path

def load_config(path: str) -> dict:
    """Load YAML or JSON config file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    
    with open(path) as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        return json.load(f)

def get_env(key: str, default: str = None) -> str:
    """Get environment variable with optional default."""
    return os.environ.get(key, default)
